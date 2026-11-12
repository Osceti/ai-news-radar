from datetime import timedelta

from conftest import NOW, FakeClassifier, FakeHNClient, make_item

from radar import __main__ as cli
from radar.pipeline import classify, collect, make_digest
from radar.storage import load_posts

ITEMS = [
    make_item(1, "OpenAI releases a new model", hours_ago=2, score=400, comments=120),
    make_item(2, "Show HN: A RAG toolkit in Rust", hours_ago=5, score=80, comments=20),
    make_item(3, "A history of the bicycle", hours_ago=1, score=500, comments=300),
    make_item(4, "LLM benchmarks from last week", hours_ago=48, score=900, comments=400),
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

    path = make_digest(data, digests, NOW)
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


def test_cli_skips_classification_without_key(tmp_path, monkeypatch, caplog):
    data = tmp_path / "posts.csv"
    collect(data, FakeHNClient(ITEMS), NOW)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    cli.run_classification(data)
    assert "GEMINI_API_KEY is not set" in caplog.text
    assert (load_posts(data)["theme"] == "").all()
