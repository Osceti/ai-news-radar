"""Trend analysis over the collected stories, shared by the notebook and the dashboard.

Two ways to measure how much a theme matters on a given day:
- volume: the share of AI stories that belong to the theme;
- attention: the theme's share of points + comments, i.e. what readers engaged with.
"""

from datetime import date, timedelta

import pandas as pd

from radar.config import THEMES
from radar.github import parse_repo


def prepare(posts: pd.DataFrame) -> pd.DataFrame:
    """Classified stories with ``day`` (UTC date) and ``engagement`` columns."""
    df = posts[posts["theme"].isin(list(THEMES))].copy()
    df["day"] = pd.to_datetime(df["created_at"], utc=True).dt.date
    df["engagement"] = df["score"] + df["num_comments"]
    return df


def complete_days(df: pd.DataFrame, today: date) -> tuple[date, date] | None:
    """First and last days fully covered by the data.

    The first day of data is partial (collection started during it), and so is
    ``today``. Returns ``None`` when no complete day is available yet.
    """
    if df.empty:
        return None
    first, last = min(df["day"]) + timedelta(days=1), today - timedelta(days=1)
    return (first, last) if first <= last else None


def between(df: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    """Stories posted from ``start`` to ``end`` included."""
    return df[(df["day"] >= start) & (df["day"] <= end)]


def theme_share(df: pd.DataFrame, measure: str = "volume", freq: str = "D") -> pd.DataFrame:
    """Share of each theme per period: rows are periods, columns are themes, rows sum to 1.

    ``measure`` is ``volume`` (story counts) or ``attention`` (points + comments);
    ``freq`` is a pandas period alias such as ``D`` (day) or ``W`` (week).
    """
    if measure not in ("volume", "attention"):
        raise ValueError("measure must be 'volume' or 'attention'")
    values = "id" if measure == "volume" else "engagement"
    period = pd.to_datetime(df["day"]).dt.to_period(freq).dt.start_time
    table = df.assign(period=period).pivot_table(
        index="period", columns="theme", values=values,
        aggfunc="count" if measure == "volume" else "sum", fill_value=0)
    table = table.reindex(columns=list(THEMES), fill_value=0)
    totals = table.sum(axis=1).replace(0, float("nan"))
    return table.div(totals, axis=0).fillna(0.0)


def theme_momentum(df: pd.DataFrame, end: date, window_days: int = 7,
                   measure: str = "volume") -> pd.DataFrame:
    """Compare each theme's share in the last ``window_days`` days to the window before.

    Returns one row per theme with ``recent`` and ``previous`` shares, their
    ``change`` in percentage points and the number of stories, rising themes first.
    """
    recent = between(df, end - timedelta(days=window_days - 1), end)
    previous = between(df, end - timedelta(days=2 * window_days - 1),
                       end - timedelta(days=window_days))

    def shares(part: pd.DataFrame) -> pd.Series:
        weights = part.groupby("theme")["id" if measure == "volume" else "engagement"]
        totals = weights.count() if measure == "volume" else weights.sum()
        totals = totals.reindex(list(THEMES), fill_value=0)
        return totals / totals.sum() if totals.sum() else totals.astype(float)

    result = pd.DataFrame({
        "recent": shares(recent),
        "previous": shares(previous),
        "stories": recent.groupby("theme").size().reindex(list(THEMES), fill_value=0),
    })
    result["change"] = (result["recent"] - result["previous"]) * 100
    result.index.name = "theme"
    return result.sort_values("change", ascending=False).reset_index()


def daily_volume(df: pd.DataFrame) -> pd.Series:
    """Number of AI stories per day."""
    return df.groupby("day").size().rename("stories")


def top_domains(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Most frequent link domains (self posts excluded), with their total engagement."""
    linked = df[df["domain"] != ""]
    table = linked.groupby("domain").agg(stories=("id", "size"), engagement=("engagement", "sum"))
    return table.sort_values(["stories", "engagement"], ascending=False).head(n).reset_index()


def top_github_repos(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """GitHub repositories linked from the stories, ranked by points + comments.

    A repository posted several times adds up its stories; the best one is kept as
    the discussion to link to.
    """
    columns = ["repo", "stories", "engagement", "score", "num_comments", "title", "hn_url", "day"]
    linked = df.assign(repo=df["url"].map(parse_repo)).dropna(subset=["repo"])
    if linked.empty:
        return pd.DataFrame(columns=columns)
    best = linked.sort_values("engagement", ascending=False).drop_duplicates("repo")
    totals = linked.groupby("repo").agg(stories=("id", "size"), engagement=("engagement", "sum"),
                                        score=("score", "sum"), num_comments=("num_comments", "sum"))
    table = best[["repo", "title", "hn_url", "day"]].merge(totals, on="repo")
    return table.sort_values(["engagement", "repo"], ascending=[False, True]).head(n)[columns].reset_index(drop=True)


def top_stories(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Stories with the most points + comments."""
    columns = ["day", "theme", "title", "url", "domain", "hn_url", "score", "num_comments",
               "engagement"]
    return df.sort_values("engagement", ascending=False).head(n)[columns].reset_index(drop=True)
