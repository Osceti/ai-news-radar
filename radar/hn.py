"""Minimal client for the official Hacker News API (https://github.com/HackerNews/API).

The API has no search endpoint, so we read the ids of the current top, new and
best stories, fetch each item concurrently and keep the recent ones.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)

API_BASE = "https://hacker-news.firebaseio.com/v0"
DISCUSSION_URL = "https://news.ycombinator.com/item?id={id}"
FEEDS = ("topstories", "newstories", "beststories")


def make_session() -> requests.Session:
    """HTTP session with connection pooling and retries on transient errors."""
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504))
    session.mount("https://", HTTPAdapter(max_retries=retry, pool_maxsize=32))
    session.headers["User-Agent"] = "ai-news-radar/0.1"
    return session


class HackerNewsClient:
    def __init__(self, session=None, base_url: str = API_BASE, timeout: float = 10.0,
                 max_workers: int = 16):
        self.session = session or make_session()
        self.base_url = base_url
        self.timeout = timeout
        self.max_workers = max_workers

    def _get(self, path: str):
        response = self.session.get(f"{self.base_url}/{path}.json", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def story_ids(self, feeds: tuple[str, ...] = FEEDS) -> list[int]:
        """Union of the ids listed in ``feeds``, without duplicates, in feed order."""
        ids: dict[int, None] = {}
        for feed in feeds:
            for item_id in self._get(feed) or []:
                ids.setdefault(item_id, None)
        return list(ids)

    def item(self, item_id: int) -> dict | None:
        try:
            return self._get(f"item/{item_id}")
        except requests.RequestException as exc:
            log.warning("Could not fetch item %s: %s", item_id, exc)
            return None

    def items(self, ids: list[int]) -> list[dict]:
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            return [item for item in pool.map(self.item, ids) if item]


def is_live_story(item: dict) -> bool:
    """True for stories (including Ask/Show HN) that are neither deleted nor dead."""
    return (
        item.get("type") == "story"
        and not item.get("deleted")
        and not item.get("dead")
        and bool(item.get("title"))
        and "time" in item
    )


def created_at(item: dict) -> datetime:
    return datetime.fromtimestamp(item["time"], tz=timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_record(item: dict, keywords: list[str], collected_at: datetime) -> dict:
    """Flatten an HN item into a row of the posts table."""
    discussion = DISCUSSION_URL.format(id=item["id"])
    url = item.get("url") or discussion  # Ask HN posts have no external link
    domain = urlparse(item["url"]).netloc.removeprefix("www.") if item.get("url") else ""
    return {
        "id": int(item["id"]),
        "created_at": iso(created_at(item)),
        "title": item["title"].strip(),
        "url": url,
        "domain": domain,
        "hn_url": discussion,
        "score": int(item.get("score", 0)),
        "num_comments": int(item.get("descendants", 0)),
        "author": item.get("by", ""),
        "keywords": ";".join(keywords),
        "theme": "",
        "summary": "",
        "collected_at": iso(collected_at),
    }
