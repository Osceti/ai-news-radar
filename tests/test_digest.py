from conftest import NOW, make_item

from radar.digest import escape_md, render_digest, select_top
from radar.hn import to_record
from radar.storage import empty_posts, merge_posts


def posts_frame(specs):
    """specs: (id, title, hours_ago, score, comments, theme, summary)."""
    records = []
    for item_id, title, hours_ago, score, comments, theme, summary in specs:
        rec = to_record(make_item(item_id, title, hours_ago, score, comments), ["AI"], NOW)
        rec.update(theme=theme, summary=summary)
        records.append(rec)
    return merge_posts(empty_posts(), records)


def test_select_top_ranks_recent_posts_by_engagement():
    df = posts_frame([
        (1, "old but huge", 30, 900, 500, "models", ""),
        (2, "quiet", 2, 5, 0, "models", ""),
        (3, "popular", 3, 200, 100, "agents", ""),
        (4, "discussed", 5, 50, 400, "business", ""),
    ])
    top = select_top(df, NOW, window_hours=24, limit=2)
    assert top["id"].tolist() == [4, 3]


def test_render_groups_by_theme_in_fixed_order():
    df = posts_frame([
        (1, "Agent framework", 1, 100, 10, "agents", "A new agent framework."),
        (2, "New model [beta]", 1, 300, 50, "models", "A model release."),
        (3, "Mystery post", 1, 20, 1, "", ""),
    ])
    text = render_digest(select_top(df, NOW), NOW, total=7)

    assert text.startswith("# AI News Radar — 2026-11-12")
    assert "Top 3 of 7 AI-related stories" in text
    assert text.index("## Models") < text.index("## Agents") < text.index("## Unclassified")
    assert "**[New model \\[beta\\]](https://www.example.com/2)** (example.com)\\" in text
    assert "  A model release.\\" in text
    assert "300 points · 50 comments · [discussion](https://news.ycombinator.com/item?id=2)" in text
    assert "## RAG" not in text  # empty themes are omitted


def test_render_empty_day():
    text = render_digest(posts_frame([]), NOW, total=0)
    assert "No AI-related stories" in text


def test_escape_md():
    assert escape_md("a *b* [c] `d` <e>") == "a \\*b\\* \\[c\\] \\`d\\` \\<e\\>"
