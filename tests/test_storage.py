from conftest import NOW, make_item

from radar.hn import to_record
from radar.storage import empty_posts, load_posts, merge_posts, save_posts


def record(item_id, score=10, title="AI story"):
    return to_record(make_item(item_id, title, score=score), ["AI"], NOW)


def test_load_missing_file_returns_empty(tmp_path):
    df = load_posts(tmp_path / "nope.csv")
    assert df.empty
    assert "theme" in df.columns


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "data" / "posts.csv"
    df = merge_posts(empty_posts(), [record(2), record(1)])
    save_posts(df, path)
    loaded = load_posts(path)
    assert loaded["id"].tolist() == [1, 2]
    assert loaded["score"].dtype == "int64"
    assert loaded.loc[0, "theme"] == ""


def test_merge_updates_metrics_and_keeps_classification():
    existing = merge_posts(empty_posts(), [record(1, score=10), record(2, score=5)])
    existing.loc[existing["id"] == 1, ["theme", "summary"]] = ["models", "A model release."]

    merged = merge_posts(existing, [record(1, score=300, title="AI story (updated)"), record(3)])

    assert merged["id"].tolist() == [1, 2, 3]
    row = merged[merged["id"] == 1].iloc[0]
    assert row["score"] == 300
    assert row["title"] == "AI story (updated)"
    assert (row["theme"], row["summary"]) == ("models", "A model release.")
    assert merged[merged["id"] == 3].iloc[0]["theme"] == ""


def test_merge_never_duplicates():
    df = merge_posts(empty_posts(), [record(1), record(1, score=99)])
    df = merge_posts(df, [record(1), record(1)])
    assert df["id"].tolist() == [1]


def test_merge_with_no_records_is_a_noop():
    existing = merge_posts(empty_posts(), [record(1)])
    assert merge_posts(existing, []).equals(existing)
