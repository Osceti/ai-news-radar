from datetime import datetime, timedelta, timezone

import pytest
import requests

NOW = datetime(2026, 11, 12, 20, 0, tzinfo=timezone.utc)


def make_item(item_id, title, hours_ago=1.0, score=10, comments=5, now=NOW, **extra):
    """An HN API item as returned by /v0/item/<id>.json."""
    item = {
        "id": item_id,
        "type": "story",
        "by": "someone",
        "title": title,
        "time": int((now - timedelta(hours=hours_ago)).timestamp()),
        "score": score,
        "descendants": comments,
        "url": f"https://www.example.com/{item_id}",
    }
    item.update(extra)
    return item


class FakeResponse:
    def __init__(self, data=None, status_code=200, text=""):
        self._data = data
        self.status_code = status_code
        self.text = text

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeHNClient:
    """Stands in for HackerNewsClient in pipeline tests."""

    def __init__(self, items):
        self._items = {item["id"]: item for item in items}

    def story_ids(self):
        return list(self._items)

    def items(self, ids):
        return [self._items[i] for i in ids]


class FakeClassifier:
    def __init__(self, theme="models"):
        self.theme = theme
        self.calls = []

    def classify(self, posts):
        self.calls.append(posts)
        return {p["id"]: {"theme": self.theme, "summary": f"About {p['title']}."} for p in posts}


@pytest.fixture
def now():
    return NOW
