from datetime import date

import pandas as pd
import pytest
from conftest import NOW, make_item

from radar.config import THEMES
from radar.hn import to_record
from radar.storage import empty_posts, merge_posts
from radar.trends import (
    between,
    complete_days,
    daily_volume,
    prepare,
    theme_momentum,
    theme_share,
    top_domains,
    top_stories,
)

D12 = NOW.date()  # 2026-11-12, NOW is 20:00 UTC


def frame(specs):
    """specs: (id, days_before_12_nov, theme, score, comments, domain)."""
    records = []
    for item_id, days_ago, theme, score, comments, domain in specs:
        rec = to_record(make_item(item_id, f"AI {item_id}", hours_ago=24 * days_ago,
                                  score=score, comments=comments), ["AI"], NOW)
        rec.update(theme=theme, domain=domain)
        records.append(rec)
    return prepare(merge_posts(empty_posts(), records))


DATA = frame([
    (1, 2, "models", 100, 0, "a.com"),   # 10 Nov
    (2, 1, "models", 10, 0, "a.com"),    # 11 Nov
    (3, 1, "agents", 30, 0, "b.com"),    # 11 Nov
    (4, 0, "agents", 5, 5, ""),          # 12 Nov
    (5, 0, "agents", 1, 0, "b.com"),     # 12 Nov
    (6, 0, "", 999, 999, "c.com"),       # unclassified: ignored
])


def test_prepare_keeps_classified_stories():
    assert DATA["id"].tolist() == [1, 2, 3, 4, 5]
    assert DATA.loc[DATA["id"] == 4, "engagement"].item() == 10
    assert DATA.loc[DATA["id"] == 1, "day"].item() == date(2026, 11, 10)


def test_complete_days_skips_first_and_current_day():
    assert complete_days(DATA, today=date(2026, 11, 13)) == (date(2026, 11, 11), date(2026, 11, 12))
    assert complete_days(DATA, today=date(2026, 11, 11)) is None
    assert complete_days(DATA.iloc[0:0], today=D12) is None


def test_between_is_inclusive():
    assert between(DATA, date(2026, 11, 11), date(2026, 11, 11))["id"].tolist() == [2, 3]


def test_theme_share_by_volume_and_attention():
    volume = theme_share(DATA)
    assert list(volume.columns) == list(THEMES)
    assert volume.loc[pd.Timestamp("2026-11-11"), "models"] == 0.5
    assert volume.sum(axis=1).round(6).eq(1).all()

    attention = theme_share(DATA, measure="attention")
    assert attention.loc[pd.Timestamp("2026-11-11"), "agents"] == 0.75
    with pytest.raises(ValueError):
        theme_share(DATA, measure="clicks")


def test_theme_momentum():
    table = theme_momentum(DATA, end=D12, window_days=1).set_index("theme")
    # 12 Nov: 2 agents of 2; 11 Nov: 1 agents of 2.
    assert table.loc["agents", "recent"] == 1.0
    assert table.loc["agents", "change"] == pytest.approx(50)
    assert table.loc["models", "change"] == pytest.approx(-50)
    assert table.loc["agents", "stories"] == 2
    assert table.index[0] == "agents"  # rising first


def test_volume_domains_and_top_stories():
    assert daily_volume(DATA).tolist() == [1, 2, 2]
    domains = top_domains(DATA)
    assert domains["domain"].tolist() == ["a.com", "b.com"]  # self post excluded
    assert top_stories(DATA, n=2)["title"].tolist() == ["AI 1", "AI 3"]


def test_prepare_can_keep_unclassified_stories():
    rec = to_record(make_item(99, "Unlabelled", hours_ago=2), ["AI"], NOW)
    rec.update(theme="")
    posts = merge_posts(empty_posts(), [rec])
    assert len(prepare(posts)) == 0
    assert len(prepare(posts, classified_only=False)) == 1
