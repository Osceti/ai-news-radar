"""CSV storage of collected posts, one row per Hacker News story id."""

from pathlib import Path

import pandas as pd

COLUMNS = [
    "id",
    "created_at",
    "title",
    "url",
    "domain",
    "hn_url",
    "score",
    "num_comments",
    "author",
    "keywords",
    "theme",
    "summary",
    "prompt_version",
    "collected_at",
]
INT_COLUMNS = ("id", "score", "num_comments", "prompt_version")
# Columns produced by the classifier, kept when a story is collected again.
# prompt_version is the classifier prompt that produced the theme (0: not classified).
CLASSIFICATION_COLUMNS = ("theme", "summary", "prompt_version")


def empty_posts() -> pd.DataFrame:
    return pd.DataFrame(
        {col: pd.Series(dtype="int64" if col in INT_COLUMNS else "object") for col in COLUMNS}
    )


def load_posts(path: Path) -> pd.DataFrame:
    if not Path(path).exists():
        return empty_posts()
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    if "prompt_version" not in df:  # files written before versions were tracked: v1
        df["prompt_version"] = (df["theme"] != "").astype(int).astype(str)
    df["prompt_version"] = df["prompt_version"].replace("", "0")
    for col in INT_COLUMNS:
        df[col] = df[col].astype("int64")
    return df[COLUMNS]


def save_posts(df: pd.DataFrame, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df[COLUMNS].sort_values("id").to_csv(path, index=False)


def merge_posts(existing: pd.DataFrame, records: list[dict]) -> pd.DataFrame:
    """Upsert freshly collected ``records`` into ``existing``.

    A story seen again gets its latest title, score and comment count, while its
    theme and summary are carried over so it is never classified twice.
    """
    fresh = pd.DataFrame(records, columns=COLUMNS).drop_duplicates("id", keep="last")
    if fresh.empty:
        return existing
    fresh = fresh.astype({col: "int64" for col in INT_COLUMNS})
    if existing.empty:
        return fresh.sort_values("id").reset_index(drop=True)

    previous = existing.set_index("id")
    for col in CLASSIFICATION_COLUMNS:
        fresh[col] = fresh["id"].map(previous[col]).fillna(fresh[col])
    fresh = fresh.astype({col: "int64" for col in INT_COLUMNS})

    kept = existing[~existing["id"].isin(fresh["id"])]
    merged = pd.concat([kept, fresh], ignore_index=True)
    return merged.sort_values("id").reset_index(drop=True)
