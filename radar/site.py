"""Static HTML dashboard: ``docs/index.html``, rebuilt every day and served by GitHub Pages.

All numbers are computed here, with the tested functions of ``radar.trends``; the page
only draws them. The data is embedded in the page as JSON, so it needs no server.
"""

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from radar import trends
from radar.config import ROOT, THEMES
from radar.storage import load_posts

SITE_DIR = ROOT / "docs"
TEMPLATE = Path(__file__).with_name("dashboard.html")
REPO_URL = "https://github.com/Osceti/ai-news-radar"
# Bright fills that read well with black text and black outlines (brutalist palette).
THEME_COLORS = {
    "models": "#60A5FA", "agents": "#FB923C", "rag": "#4ADE80", "dev-tools": "#A78BFA",
    "security": "#F87171", "research": "#22D3EE", "business": "#FACC15",
    "regulation": "#F472B6", "other": "#A1A1AA",
}
TOP_STORIES = 60


def _evaluation_accuracy(eval_dir: Path) -> dict | None:
    """Accuracy of the current prompt on the held-out sample, if the files exist."""
    from radar.classifier import PROMPT_VERSION
    from radar.evaluation import evaluate, load_reference, read_csv

    labels, judge = eval_dir / "labels.csv", eval_dir / "judge_labels.csv"
    predictions = eval_dir / f"predictions_v{PROMPT_VERSION}.csv"
    if not (labels.exists() and judge.exists() and predictions.exists()):
        return None
    ev = evaluate(load_reference(labels, judge), read_csv(predictions))
    return {"accuracy": round(ev.accuracy, 3), "stories": ev.total}


def _shares(table: pd.DataFrame, days: list) -> dict[str, list[float]]:
    table = table.reindex([pd.Timestamp(d) for d in days], fill_value=0)
    return {slug: [round(v, 4) for v in table[slug]] for slug in THEMES}


def build_payload(posts: pd.DataFrame, today: date, eval_dir: Path | None = None) -> dict | None:
    """Everything the page shows, as plain JSON-serialisable data."""
    df_all = trends.prepare(posts)
    days_range = trends.complete_days(df_all, today)
    if days_range is None:
        return None
    start, end = days_range
    df = trends.between(df_all, start, end)
    days = [start + pd.Timedelta(days=i) for i in range((end - start).days + 1)]
    window = max(1, min(7, len(days) // 2))

    totals = pd.DataFrame({
        "stories": df["theme"].value_counts(),
        "engagement": df.groupby("theme")["engagement"].sum(),
    }).reindex(list(THEMES), fill_value=0)

    def momentum(measure: str) -> list[dict]:
        table = trends.theme_momentum(df_all, end=end, window_days=window, measure=measure)
        return [{"theme": r.theme, "recent": round(r.recent, 4), "previous": round(r.previous, 4),
                 "change": round(r.change, 2), "stories": int(r.stories)}
                for r in table.itertuples(index=False)]

    top = trends.top_stories(df, n=TOP_STORIES)
    volume = trends.daily_volume(df).reindex(days, fill_value=0)

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "days": [d.isoformat() for d in days],
        "total": int(len(df)),
        "themes": [{"slug": s, "label": label, "color": THEME_COLORS[s]} for s, label in THEMES.items()],
        "volume": [int(v) for v in volume],
        "share": {"volume": _shares(trends.theme_share(df, "volume"), days),
                  "attention": _shares(trends.theme_share(df, "attention"), days)},
        "totals": [{"theme": s, "stories": int(r.stories), "engagement": int(r.engagement)}
                   for s, r in totals.iterrows()],
        "window": window,
        "momentum": {"volume": momentum("volume"), "attention": momentum("attention")},
        "stories": [{"day": r.day.isoformat(), "theme": r.theme, "title": r.title, "url": r.url,
                     "hn_url": r.hn_url, "domain": r.domain, "score": int(r.score),
                     "comments": int(r.num_comments)} for r in top.itertuples(index=False)],
        "domains": trends.top_domains(df, n=10).to_dict("records"),
        "latest_digest": f"{REPO_URL}/blob/main/digests/{end.isoformat()}.md",
        "evaluation": _evaluation_accuracy(eval_dir) if eval_dir else None,
        "repo": REPO_URL,
    }


def render(payload: dict) -> str:
    # "</" is escaped so that a story title can never close the <script> tag.
    data = json.dumps(payload, ensure_ascii=False, default=int).replace("</", "<\\/")
    return TEMPLATE.read_text(encoding="utf-8").replace("__RADAR_DATA__", data)


def write_site(data_path: Path, out_dir: Path, today: date, eval_dir: Path | None = None) -> Path | None:
    payload = build_payload(load_posts(data_path), today, eval_dir)
    if payload is None:
        return None
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "index.html"
    path.write_text(render(payload), encoding="utf-8")
    (out_dir / ".nojekyll").touch()  # serve the file as is on GitHub Pages
    return path
