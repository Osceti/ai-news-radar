"""The three steps of a daily run: collect, classify, digest.

Each step reads and writes the CSV file, so they can also be run on their own.
External clients are passed in, which keeps the steps easy to test.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

from radar.config import DIGEST_SIZE, MAX_CLASSIFICATIONS_PER_RUN, WINDOW_HOURS
from radar.digest import recent_posts, render_digest, select_top
from radar.filters import match_ai_keywords
from radar.hn import created_at, is_live_story, to_record
from radar.storage import load_posts, merge_posts, save_posts

log = logging.getLogger(__name__)


def collect(data_path: Path, client, now: datetime, window_hours: int = WINDOW_HOURS) -> int:
    """Fetch recent AI stories from Hacker News and upsert them. Returns their count."""
    items = client.items(client.story_ids())
    cutoff = now - timedelta(hours=window_hours)
    records = []
    for item in items:
        if not is_live_story(item) or created_at(item) < cutoff:
            continue
        keywords = match_ai_keywords(item["title"])
        if keywords:
            records.append(to_record(item, keywords, now))

    posts = merge_posts(load_posts(data_path), records)
    save_posts(posts, data_path)
    log.info("Scanned %d stories: %d AI-related in the last %dh, %d stored in total",
             len(items), len(records), window_hours, len(posts))
    return len(records)


def classify(data_path: Path, classifier, limit: int = MAX_CLASSIFICATIONS_PER_RUN) -> tuple[int, int]:
    """Classify stories that have no theme yet, newest first.

    Returns ``(classified, pending)``. Unclassified stories are retried next run.
    """
    posts = load_posts(data_path)
    pending = posts[posts["theme"] == ""].sort_values("created_at", ascending=False).head(limit)
    if pending.empty:
        log.info("Nothing to classify")
        return 0, 0

    batch = [
        {"id": int(row.id), "title": row.title, "domain": row.domain}
        for row in pending.itertuples(index=False)
    ]
    results = classifier.classify(batch)
    for post_id, result in results.items():
        mask = posts["id"] == post_id
        posts.loc[mask, "theme"] = result["theme"]
        posts.loc[mask, "summary"] = result["summary"]
    save_posts(posts, data_path)
    log.info("Classified %d of %d pending stories", len(results), len(pending))
    return len(results), len(pending)


def make_digest(data_path: Path, digest_dir: Path, now: datetime,
                window_hours: int = WINDOW_HOURS, size: int = DIGEST_SIZE) -> Path:
    """Write ``digests/YYYY-MM-DD.md`` for the window ending at ``now``."""
    posts = load_posts(data_path)
    top = select_top(posts, now, window_hours, size)
    total = len(recent_posts(posts, now, window_hours))
    path = Path(digest_dir) / f"{now:%Y-%m-%d}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_digest(top, now, total, window_hours), encoding="utf-8")
    log.info("Wrote %s (%d stories)", path, len(top))
    return path
