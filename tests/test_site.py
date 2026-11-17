import json
import re
from datetime import date

from conftest import NOW, make_item

from radar.config import THEMES
from radar.hn import to_record
from radar.site import build_payload, render, write_site
from radar.storage import empty_posts, merge_posts, save_posts

TODAY = date(2026, 11, 13)  # 12 Nov is the only complete day (11 Nov is the first, partial)


def posts():
    specs = [  # (id, hours before 12 Nov 20:00, theme, score, comments, title)
        (1, 30, "models", 50, 5, "Day one"),
        (2, 2, "agents", 300, 100, "Agents </script><b>win</b>"),
        (3, 5, "agents", 10, 1, "Small agent news"),
        (4, 8, "business", 120, 80, "Funding round"),
    ]
    records = []
    for item_id, hours, theme, score, comments, title in specs:
        rec = to_record(make_item(item_id, title, hours_ago=hours, score=score, comments=comments),
                        ["AI"], NOW)
        rec.update(theme=theme)
        records.append(rec)
    return merge_posts(empty_posts(), records)


def test_payload_covers_complete_days_only():
    payload = build_payload(posts(), TODAY)
    assert payload["days"] == ["2026-11-12"]
    assert payload["total"] == 3  # story 1 was posted on the partial first day
    assert [t["slug"] for t in payload["themes"]] == list(THEMES)
    assert payload["share"]["volume"]["agents"] == [round(2 / 3, 4)]
    assert payload["stories"][0]["title"].startswith("Agents")
    assert payload["latest_digest"].endswith("/digests/2026-11-12.md")
    assert payload["evaluation"] is None


def test_payload_is_none_without_a_complete_day():
    assert build_payload(posts(), date(2026, 11, 12)) is None


def test_render_embeds_data_safely():
    html = render(build_payload(posts(), TODAY))
    assert "__RADAR_DATA__" not in html
    data = re.search(r'<script id="radar-data" type="application/json">(.*?)</script>', html, re.S)
    assert "</script><b>" not in data.group(1)  # a title cannot close the script tag
    assert json.loads(data.group(1))["total"] == 3


def test_write_site(tmp_path):
    data = tmp_path / "posts.csv"
    save_posts(posts(), data)
    path = write_site(data, tmp_path / "docs", TODAY)
    assert path.name == "index.html" and (tmp_path / "docs" / ".nojekyll").exists()
    assert write_site(data, tmp_path / "empty", date(2026, 11, 12)) is None
