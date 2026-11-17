import math

import pandas as pd
import pytest
from conftest import NOW, make_item

from radar import __main__ as cli
from radar.evaluation import (
    NOT_AI,
    annotation_prompt,
    create_sample,
    draw_sample,
    evaluate,
    label_interactively,
    normalize_label,
    read_csv,
    render_report,
    wilson_interval,
)
from radar.hn import to_record
from radar.storage import empty_posts, merge_posts, save_posts


def classified_posts(n=30):
    themes = ["models", "agents", "dev-tools"]
    records = []
    for i in range(1, n + 1):
        rec = to_record(make_item(i, f"AI story {i}"), ["AI"], NOW)
        rec.update(theme=themes[i % 3], summary=f"Summary {i}.")
        records.append(rec)
    posts = merge_posts(empty_posts(), records)
    posts.loc[posts["id"] == 1, "theme"] = ""  # one unclassified story
    return posts


def test_draw_sample_is_reproducible_and_blind():
    posts = classified_posts()
    labels, predictions = draw_sample(posts, n=10, seed=1)
    again, _ = draw_sample(posts, n=10, seed=1)
    assert labels["id"].tolist() == again["id"].tolist()
    assert len(labels) == 10 and 1 not in labels["id"].tolist()
    assert "theme" not in labels.columns and "llm_theme" not in labels.columns
    assert (labels["human_theme"] == "").all()
    assert set(predictions.columns) == {"id", "llm_theme", "llm_summary"}


def test_create_sample_refuses_to_overwrite_labels(tmp_path):
    create_sample(classified_posts(), tmp_path, n=5)
    assert read_csv(tmp_path / "predictions.csv").shape[0] == 5
    with pytest.raises(FileExistsError):
        create_sample(classified_posts(), tmp_path, n=5)


def test_label_interactively_saves_progress(tmp_path):
    path = create_sample(classified_posts(), tmp_path, n=4)
    answers = iter(["9 opinion piece", "x", "1", "s", "q"])
    output = []
    assert label_interactively(path, input_fn=lambda _: next(answers),
                               print_fn=output.append) == 2
    labels = read_csv(path)
    assert labels["human_theme"].tolist() == ["other", "models", "", ""]
    assert labels.loc[0, "note"] == "opinion piece"
    assert any("Unknown answer" in line for line in output)

    # Resuming starts at the first unlabelled story; 0 means "not about AI".
    answers = iter(["0", "2"])
    assert label_interactively(path, input_fn=lambda _: next(answers),
                               print_fn=lambda *_: None) == 2
    assert read_csv(path)["human_theme"].tolist() == ["other", "models", NOT_AI, "agents"]


def test_label_interactively_stops_on_end_of_input(tmp_path):
    path = create_sample(classified_posts(), tmp_path, n=2)

    def closed(_):
        raise EOFError

    assert label_interactively(path, input_fn=closed, print_fn=lambda *_: None) == 0


@pytest.mark.parametrize("typed, expected", [
    ("4", "dev-tools"), ("0", NOT_AI), (" Models ", "models"), ("dev tools", "dev-tools"),
    ("not ai", NOT_AI), ("", ""), ("modles", None), ("10", None),
])
def test_normalize_label(typed, expected):
    assert normalize_label(typed) == expected


def test_read_csv_from_a_french_excel_export(tmp_path):
    path = tmp_path / "labels.csv"
    content = "id;title;domain;url;human_theme;note\n42;Café, IA et LLM;x.fr;u;7;levée\n"
    path.write_bytes(content.encode("cp1252"))
    df = read_csv(path)
    assert df.loc[0, "id"] == 42 and df.loc[0, "human_theme"] == "7"
    assert df.loc[0, "title"] == "Café, IA et LLM"

    path.write_bytes('id,title,domain,url,human_theme,note\n42,"Café, IA",x.fr,u,7,\n'
                     .encode("utf-8-sig"))  # Excel "CSV UTF-8" adds a BOM
    df = read_csv(path)
    assert df.columns[0] == "id" and df.loc[0, "title"] == "Café, IA"


def test_evaluate_reports_invalid_labels():
    labels, predictions = frames([(1, "7", "business"), (2, "modles", "models")])
    ev = evaluate(labels, predictions)
    assert (ev.correct, ev.total) == (1, 1)
    assert ev.invalid["id"].tolist() == [2]


def test_annotation_prompt_is_blind_and_complete():
    labels, predictions = draw_sample(classified_posts(), n=5)
    prompt = annotation_prompt(labels)
    assert all(f"{i} | AI story {i} | example.com" in prompt for i in labels["id"])
    assert "exactly 5 rows" in prompt and "not-ai" in prompt
    assert "Summary" not in prompt  # Gemini's output never reaches the annotator


def test_wilson_interval():
    low, high = wilson_interval(80, 100)
    assert low == pytest.approx(0.711, abs=1e-3)
    assert high == pytest.approx(0.867, abs=1e-3)
    assert all(math.isnan(v) for v in wilson_interval(0, 0))


def frames(rows):
    """rows: (id, human_theme, llm_theme)."""
    labels = pd.DataFrame([{"id": i, "title": f"t{i}", "domain": "", "url": f"u{i}",
                            "human_theme": h, "note": ""} for i, h, _ in rows])
    predictions = pd.DataFrame([{"id": i, "llm_theme": g, "llm_summary": ""} for i, _, g in rows])
    return labels, predictions


def test_evaluate_metrics():
    ev = evaluate(*frames([
        (1, "models", "models"),
        (2, "models", "dev-tools"),
        (3, "dev-tools", "dev-tools"),
        (4, "agents", "dev-tools"),
        (5, NOT_AI, "other"),
        (6, "", "models"),  # not labelled yet: ignored
    ]))
    assert (ev.labelled, len(ev.not_ai), ev.correct, ev.total) == (5, 1, 2, 4)
    assert ev.accuracy == 0.5
    per = ev.per_theme.set_index("theme")
    assert per.loc["models", "precision"] == 1.0 and per.loc["models", "recall"] == 0.5
    assert per.loc["dev-tools", "precision"] == pytest.approx(1 / 3)
    assert math.isnan(per.loc["rag", "precision"])
    assert ev.confusion.loc["models", "dev-tools"] == 1
    assert ev.errors["id"].tolist() == [2, 4]


def test_render_report():
    text = render_report(evaluate(*frames([
        (1, "models", "models"), (2, "agents", "dev-tools"), (3, NOT_AI, "other")])))
    assert "| Theme accuracy on AI stories | 50% (1/2) |" in text
    assert "| Keyword filter precision (stories really about AI) | 67% (2/3) |" in text
    assert "## Disagreements (1)" in text and "| [t2](u2) | agents | dev-tools |" in text
    assert "## Not about AI (1)" in text


def test_cli_evaluation_flow(tmp_path, capsys):
    data, eval_dir = tmp_path / "posts.csv", tmp_path / "eval"
    save_posts(classified_posts(), data)
    args = ["--data", str(data), "--eval-dir", str(eval_dir)]

    assert cli.main(["eval-report", *args]) == 1  # no sample yet
    assert cli.main(["eval-sample", *args]) == 0
    assert cli.main(["eval-sample", *args]) == 1  # never overwrites labels

    labels = read_csv(eval_dir / "labels.csv")
    predictions = read_csv(eval_dir / "predictions.csv")
    labels["human_theme"] = predictions["llm_theme"]
    labels.to_csv(eval_dir / "labels.csv", index=False)

    assert cli.main(["eval-report", *args]) == 0
    assert "Theme accuracy 100%" in capsys.readouterr().out
    assert (eval_dir / "report.md").exists()

    # An outside reference replaces the hand labels; it must cover the whole sample.
    reference = eval_dir / "judge.csv"
    rows = [f"{i},other," for i in predictions["id"]]
    reference.write_text("id,theme,note\n" + "\n".join(rows[1:]) + "\n")
    assert cli.main(["eval-report", *args, "--reference", str(reference)]) == 1
    reference.write_text("id,theme,note\n" + "\n".join(rows) + "\n")
    assert cli.main(["eval-report", *args, "--reference", str(reference),
                     "--annotator", "model X"]) == 0
    assert "labelled by model X" in (eval_dir / "report.md").read_text()
