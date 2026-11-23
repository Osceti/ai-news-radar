from datetime import date, datetime, timezone

from conftest import NOW, make_item

from radar.digest import escape_md, posts_on, previous_day, render_digest, select_top
from radar.hn import to_record
from radar.storage import empty_posts, merge_posts

DAY = NOW.date()  # 2026-11-12; NOW is 20:00 UTC that day


def posts_frame(specs):
    """specs: (id, title, hours_ago, score, comments, theme, summary)."""
    records = []
    for item_id, title, hours_ago, score, comments, theme, summary in specs:
        rec = to_record(make_item(item_id, title, hours_ago, score, comments), ["AI"], NOW)
        rec.update(theme=theme, summary=summary)
        records.append(rec)
    return merge_posts(empty_posts(), records)


def test_previous_day_is_last_complete_utc_day():
    assert previous_day(datetime(2026, 11, 13, 0, 55, tzinfo=timezone.utc)) == date(2026, 11, 12)
    assert previous_day(datetime(2026, 11, 13, 23, 41, tzinfo=timezone.utc)) == date(2026, 11, 12)


def test_posts_on_uses_utc_day_boundaries():
    df = posts_frame([
        (1, "first second of the day", 20, 1, 0, "", ""),       # 00:00:00
        (2, "last minute of the day", -3.99, 1, 0, "", ""),     # 23:59:24
        (3, "previous day", 20.01, 1, 0, "", ""),               # 11 Nov 23:59
        (4, "next day", -4, 1, 0, "", ""),                      # 13 Nov 00:00
    ])
    assert sorted(posts_on(df, DAY)["id"]) == [1, 2]


def test_select_top_ranks_the_day_by_engagement():
    df = posts_frame([
        (1, "previous day but huge", 30, 900, 500, "models", ""),
        (2, "quiet", 2, 5, 0, "models", ""),
        (3, "popular", 3, 200, 100, "agents", ""),
        (4, "discussed", 5, 50, 400, "business", ""),
    ])
    top = select_top(df, DAY, limit=2)
    assert top["id"].tolist() == [4, 3]


def test_render_groups_by_theme_in_fixed_order():
    df = posts_frame([
        (1, "Agent framework", 1, 100, 10, "agents", "A new agent framework."),
        (2, "New model [beta]", 1, 300, 50, "models", "A model release."),
        (3, "Mystery post", 1, 20, 1, "", ""),
    ])
    text = render_digest(select_top(df, DAY), DAY, total=7)

    assert text.startswith("# AI News Radar — 2026-11-12")
    assert "Top 3 of 7 AI-related stories posted on Hacker News on Thursday 12 November 2026 (UTC)" in text
    assert text.index("## Models") < text.index("## Agents") < text.index("## Unclassified")
    assert "**[New model \\[beta\\]](https://www.example.com/2)** (example.com)\\" in text
    assert "  A model release.\\" in text
    assert "300 points · 50 comments · [discussion](https://news.ycombinator.com/item?id=2)" in text
    assert "## RAG" not in text  # empty themes are omitted


def test_render_escapes_parentheses_in_urls():
    rec = to_record(
        make_item(1, "Foo", 1, 10, 2, url="https://en.wikipedia.org/wiki/Foo_(bar)"), ["AI"], NOW
    )
    rec.update(theme="models", summary="")
    df = merge_posts(empty_posts(), [rec])
    text = render_digest(select_top(df, DAY), DAY, total=1)

    assert "- **[Foo](https://en.wikipedia.org/wiki/Foo_\\(bar\\))** (en.wikipedia.org)\\" in text
    assert "(https://en.wikipedia.org/wiki/Foo_(bar))" not in text


def test_render_empty_day():
    text = render_digest(posts_frame([]), DAY, total=0)
    assert "No AI-related stories" in text


def test_escape_md():
    assert escape_md("a *b* [c] `d` <e>") == "a \\*b\\* \\[c\\] \\`d\\` \\<e\\>"
