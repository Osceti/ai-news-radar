from datetime import timedelta

from conftest import NOW, FakeClassifier, FakeHNClient, make_item

from radar import __main__ as cli
from radar.pipeline import classify, collect, make_digest
from radar.storage import load_posts

ITEMS = [
    make_item(1, "OpenAI releases a new model", hours_ago=2, score=400, comments=120),
    make_item(2, "Show HN: A RAG toolkit in Rust", hours_ago=5, score=80, comments=20),
    make_item(3, "A history of the bicycle", hours_ago=1, score=500, comments=300),
    make_item(4, "LLM benchmarks from last week", hours_ago=80, score=900, comments=400),
    make_item(5, "Hiring: ML engineer", hours_ago=1, type="job"),
]


def test_collect_keeps_recent_ai_stories_only(tmp_path):
    data = tmp_path / "posts.csv"
    assert collect(data, FakeHNClient(ITEMS), NOW) == 2
    assert load_posts(data)["id"].tolist() == [1, 2]


def test_full_run_and_rerun(tmp_path):
    data, digests = tmp_path / "posts.csv", tmp_path / "digests"
    collect(data, FakeHNClient(ITEMS), NOW)

    classifier = FakeClassifier(theme="models")
    assert classify(data, classifier) == (2, 2)
    assert [p["id"] for p in classifier.calls[0]] == [1, 2]  # newest first

    path = make_digest(data, digests, NOW.date())
    assert path.name == "2026-11-12.md"
    text = path.read_text()
    assert "OpenAI releases a new model" in text and "About OpenAI releases a new model." in text
    assert "bicycle" not in text

    # A later run sees updated scores: no duplicates, classification kept, no new LLM call.
    later = NOW + timedelta(hours=1)
    updated = [make_item(1, "OpenAI releases a new model", hours_ago=3, score=650, comments=200, now=later)]
    collect(data, FakeHNClient(updated), later)
    posts = load_posts(data)
    assert posts["id"].tolist() == [1, 2]
    assert posts.loc[posts["id"] == 1, "score"].item() == 650
    assert posts.loc[posts["id"] == 1, "theme"].item() == "models"
    assert classify(data, classifier) == (0, 0)


def test_classify_relabels_stories_from_an_older_prompt(tmp_path):
    from radar.classifier import PROMPT_VERSION

    data = tmp_path / "posts.csv"
    collect(data, FakeHNClient(ITEMS), NOW)
    classify(data, FakeClassifier(theme="models"))
    posts = load_posts(data)
    assert (posts["prompt_version"] == PROMPT_VERSION).all()

    # Story 2 was labelled by an older prompt and story 6 is new: the new one goes first.
    posts.loc[posts["id"] == 2, "prompt_version"] = PROMPT_VERSION - 1
    posts.to_csv(data, index=False)
    collect(data, FakeHNClient(ITEMS + [make_item(6, "New LLM story", hours_ago=10)]), NOW)
    classifier = FakeClassifier(theme="agents")
    assert classify(data, classifier) == (2, 2)
    assert [p["id"] for p in classifier.calls[0]] == [6, 2]
    posts = load_posts(data).set_index("id")
    assert posts.loc[1, "theme"] == "models"  # up to date: untouched
    assert posts.loc[2, "theme"] == "agents" and posts.loc[2, "prompt_version"] == PROMPT_VERSION


def test_load_posts_without_prompt_version_column(tmp_path):
    data = tmp_path / "posts.csv"
    collect(data, FakeHNClient(ITEMS), NOW)
    classify(data, FakeClassifier(theme="models"))
    legacy = load_posts(data).drop(columns="prompt_version")
    legacy.loc[legacy["id"] == 2, "theme"] = ""
    legacy.to_csv(data, index=False)
    assert load_posts(data).set_index("id")["prompt_version"].to_dict() == {1: 1, 2: 0}


def test_cli_digest_for_a_given_date(tmp_path, capsys):
    data, digests = tmp_path / "posts.csv", tmp_path / "digests"
    collect(data, FakeHNClient(ITEMS), NOW)
    assert cli.main(["digest", "--data", str(data), "--digests", str(digests),
                     "--date", "2026-11-12"]) == 0
    text = (digests / "2026-11-12.md").read_text()
    assert "Top 2 of 2 AI-related stories" in text
    assert capsys.readouterr().out.strip().endswith("2026-11-12.md")


def test_cli_skips_classification_without_key(tmp_path, monkeypatch, caplog):
    data = tmp_path / "posts.csv"
    collect(data, FakeHNClient(ITEMS), NOW)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    cli.run_classification(data)
    assert "GEMINI_API_KEY is not set" in caplog.text
    assert (load_posts(data)["theme"] == "").all()
