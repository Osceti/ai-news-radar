from conftest import NOW, FakeResponse, make_item

from radar.hn import HackerNewsClient, is_live_story, to_record


class FakeSession:
    def __init__(self, feeds, items, failing=()):
        self.feeds = feeds
        self.items = items
        self.failing = set(failing)

    def get(self, url, timeout=None):
        path = url.split("/v0/", 1)[1].removesuffix(".json")
        if path.startswith("item/"):
            item_id = int(path.removeprefix("item/"))
            if item_id in self.failing:
                return FakeResponse(status_code=500)
            return FakeResponse(self.items.get(item_id))
        return FakeResponse(self.feeds.get(path, []))


def test_story_ids_union_without_duplicates():
    session = FakeSession({"topstories": [3, 1], "newstories": [5, 3], "beststories": [1, 7]}, {})
    assert HackerNewsClient(session=session).story_ids() == [3, 1, 5, 7]


def test_items_skips_missing_and_failing_items():
    items = {1: make_item(1, "a"), 2: make_item(2, "b")}
    session = FakeSession({}, items, failing={2})
    fetched = HackerNewsClient(session=session, max_workers=2).items([1, 2, 3])
    assert [item["id"] for item in fetched] == [1]


def test_is_live_story():
    assert is_live_story(make_item(1, "AI news"))
    assert not is_live_story(make_item(1, "AI news", type="job"))
    assert not is_live_story(make_item(1, "AI news", dead=True))
    assert not is_live_story({"id": 1, "type": "story", "deleted": True, "time": 0})


def test_to_record_fields():
    item = make_item(42, " LLM news ", score=120, comments=33, url="https://www.example.org/post")
    record = to_record(item, ["LLM"], NOW)
    assert record["id"] == 42
    assert record["title"] == "LLM news"
    assert record["domain"] == "example.org"
    assert record["hn_url"] == "https://news.ycombinator.com/item?id=42"
    assert (record["score"], record["num_comments"]) == (120, 33)
    assert record["created_at"] == "2026-11-12T19:00:00Z"
    assert record["collected_at"] == "2026-11-12T20:00:00Z"
    assert record["theme"] == ""


def test_to_record_ask_hn_links_to_discussion():
    item = make_item(7, "Ask HN: Which LLM do you use?")
    del item["url"]
    del item["descendants"]
    record = to_record(item, ["LLM"], NOW)
    assert record["url"] == "https://news.ycombinator.com/item?id=7"
    assert record["domain"] == ""
    assert record["num_comments"] == 0
