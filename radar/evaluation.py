"""Evaluation of the Gemini classifier against hand labels.

1. ``draw_sample`` picks a random sample of classified stories. The stories go to
   ``eval/labels.csv`` *without* Gemini's answer, so labelling is blind; Gemini's
   theme and summary are frozen separately in ``eval/predictions.csv``.
2. ``label_interactively`` shows each story in the terminal and records a theme,
   or ``not-ai`` when the keyword filter let through a story that is not about AI.
3. ``evaluate`` compares the two files and ``render_report`` writes the results.
"""

import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from radar.classifier import THEME_GUIDE
from radar.config import ROOT, THEMES

EVAL_DIR = ROOT / "eval"
LABELS_NAME = "labels.csv"
PREDICTIONS_NAME = "predictions.csv"
REPORT_NAME = "report.md"

NOT_AI = "not-ai"
# Keys typed while labelling: 1-9 for the themes, 0 for "not about AI".
KEYS = {str(i): theme for i, theme in enumerate(THEMES, start=1)} | {"0": NOT_AI}
SAMPLE_SIZE = 100
SEED = 42


# --- Sampling -----------------------------------------------------------------

def draw_sample(posts: pd.DataFrame, n: int = SAMPLE_SIZE,
                seed: int = SEED) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Random sample of classified stories: ``(labels to fill, frozen predictions)``."""
    classified = posts[posts["theme"] != ""]
    sample = classified.sample(n=min(n, len(classified)), random_state=seed).sort_values("id")
    labels = sample[["id", "title", "domain", "url"]].assign(human_theme="", note="")
    predictions = sample[["id", "theme", "summary"]].rename(
        columns={"theme": "llm_theme", "summary": "llm_summary"})
    return labels.reset_index(drop=True), predictions.reset_index(drop=True)


def create_sample(posts: pd.DataFrame, eval_dir: Path, n: int = SAMPLE_SIZE,
                  seed: int = SEED) -> Path:
    eval_dir = Path(eval_dir)
    labels_path = eval_dir / LABELS_NAME
    if labels_path.exists():
        raise FileExistsError(f"{labels_path} already exists; delete it to draw a new sample")
    labels, predictions = draw_sample(posts, n, seed)
    eval_dir.mkdir(parents=True, exist_ok=True)
    labels.to_csv(labels_path, index=False)
    predictions.to_csv(eval_dir / PREDICTIONS_NAME, index=False)
    return labels_path


def read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df["id"] = df["id"].astype("int64")
    return df


# --- Labelling ----------------------------------------------------------------

def theme_menu() -> str:
    lines = ["Themes:"]
    lines += [f"  {key}  {theme:<10} {THEME_GUIDE.get(theme, 'the keyword filter was wrong')}"
              for key, theme in sorted(KEYS.items(), key=lambda kv: kv[0] == "0")]
    return "\n".join(lines)


def label_interactively(labels_path: Path, input_fn=input, print_fn=print) -> int:
    """Ask for a theme for every unlabelled story. Saves after each answer.

    Answer with a key, optionally followed by a note (``"3 about embeddings"``),
    ``s`` to skip or ``q`` to quit. Returns the number of stories labelled.
    """
    labels = read_csv(labels_path)
    todo = list(labels.index[labels["human_theme"] == ""])
    print_fn(theme_menu())
    labelled = 0
    for idx in todo:
        row = labels.loc[idx]
        position = int((labels["human_theme"] != "").sum()) + 1
        print_fn(f"\n[{position}/{len(labels)}] {row['title']}\n"
                 f"    {row['domain'] or 'news.ycombinator.com'} | {row['url']}")
        while True:
            try:
                answer = input_fn("Theme (1-9, 0 = not AI, s = skip, q = quit): ").strip()
            except EOFError:
                answer = "q"
            key, _, note = answer.partition(" ")
            if key.lower() == "q":
                return labelled
            if key.lower() == "s":
                break
            if key in KEYS:
                labels.at[idx, "human_theme"] = KEYS[key]
                labels.at[idx, "note"] = note.strip()
                labels.to_csv(labels_path, index=False)
                labelled += 1
                break
            print_fn("  Unknown answer, try again.")
    return labelled


# --- Metrics ------------------------------------------------------------------

def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% confidence interval of a proportion (Wilson score)."""
    if n == 0:
        return (math.nan, math.nan)
    p = successes / n
    denominator = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denominator
    return (max(0.0, centre - half), min(1.0, centre + half))


@dataclass
class Evaluation:
    labelled: int
    not_ai: pd.DataFrame
    correct: int
    total: int
    per_theme: pd.DataFrame
    confusion: pd.DataFrame
    errors: pd.DataFrame

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else math.nan

    @property
    def interval(self) -> tuple[float, float]:
        return wilson_interval(self.correct, self.total)


def evaluate(labels: pd.DataFrame, predictions: pd.DataFrame) -> Evaluation:
    done = labels[labels["human_theme"] != ""].merge(predictions, on="id", how="inner")
    not_ai = done[done["human_theme"] == NOT_AI]
    ai = done[done["human_theme"] != NOT_AI]
    hit = ai["human_theme"] == ai["llm_theme"]

    rows = []
    for theme in THEMES:
        support = int((ai["human_theme"] == theme).sum())
        predicted = int((ai["llm_theme"] == theme).sum())
        true_pos = int(((ai["human_theme"] == theme) & hit).sum())
        rows.append({
            "theme": theme,
            "support": support,
            "predicted": predicted,
            "precision": true_pos / predicted if predicted else math.nan,
            "recall": true_pos / support if support else math.nan,
        })
    confusion = (pd.crosstab(ai["human_theme"], ai["llm_theme"])
                 .reindex(index=list(THEMES), columns=list(THEMES), fill_value=0))
    return Evaluation(
        labelled=len(done),
        not_ai=not_ai,
        correct=int(hit.sum()),
        total=len(ai),
        per_theme=pd.DataFrame(rows),
        confusion=confusion,
        errors=ai[~hit],
    )


# --- Report -------------------------------------------------------------------

def _pct(value: float) -> str:
    return "–" if math.isnan(value) else f"{value:.0%}"


def render_report(ev: Evaluation) -> str:
    low, high = ev.interval
    lines = [
        "# Classifier evaluation",
        "",
        f"{ev.labelled} stories labelled by hand, blind to Gemini's answer.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Keyword filter precision (stories really about AI) | "
        f"{_pct((ev.labelled - len(ev.not_ai)) / ev.labelled if ev.labelled else math.nan)} "
        f"({ev.labelled - len(ev.not_ai)}/{ev.labelled}) |",
        f"| Theme accuracy on AI stories | {_pct(ev.accuracy)} ({ev.correct}/{ev.total}) |",
        f"| 95% confidence interval (Wilson) | {_pct(low)} – {_pct(high)} |",
        "",
        "## Per theme",
        "",
        "| Theme | Human labels | Gemini labels | Precision | Recall |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in ev.per_theme.itertuples(index=False):
        lines.append(f"| {row.theme} | {row.support} | {row.predicted} | "
                     f"{_pct(row.precision)} | {_pct(row.recall)} |")

    lines += ["", "## Confusion matrix", "",
              "Rows: human label. Columns: Gemini's label.", "",
              "| | " + " | ".join(THEMES) + " |",
              "| --- |" + " ---: |" * len(THEMES)]
    for theme, counts in ev.confusion.iterrows():
        lines.append(f"| **{theme}** | " + " | ".join(
            f"**{c}**" if col == theme and c else str(c) for col, c in counts.items()) + " |")

    lines += ["", f"## Disagreements ({len(ev.errors)})", "",
              "| Story | Human | Gemini | Note |", "| --- | --- | --- | --- |"]
    for row in ev.errors.sort_values(["human_theme", "llm_theme"]).itertuples(index=False):
        lines.append(f"| [{_cell(row.title)}]({row.url}) | {row.human_theme} | "
                     f"{row.llm_theme} | {_cell(row.note)} |")

    if len(ev.not_ai):
        lines += ["", f"## Not about AI ({len(ev.not_ai)})", "",
                  "Stories the keyword filter let through.", ""]
        lines += [f"- [{_cell(row.title)}]({row.url}) (Gemini: {row.llm_theme})"
                  for row in ev.not_ai.itertuples(index=False)]
    lines.append("")
    return "\n".join(lines)


def _cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
