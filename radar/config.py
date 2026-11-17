"""Project-wide settings: paths, collection window and the fixed list of themes."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "posts.csv"
DIGEST_DIR = ROOT / "digests"

# Stories posted within this many hours before a run are collected (or refreshed).
# A digest covers one full UTC day, so this must stay well above 24 h: scheduled
# GitHub runs can start hours late, and a missed day can be rebuilt a day later.
COLLECT_WINDOW_HOURS = 72
# Number of stories in each daily digest.
DIGEST_SIZE = 10
# Upper bound on LLM classifications per run, to stay well inside the free tier.
MAX_CLASSIFICATIONS_PER_RUN = 200

# Fixed list of themes: slug -> display label. Order is the order used in digests.
THEMES = {
    "models": "Models",
    "agents": "Agents",
    "rag": "RAG",
    "dev-tools": "Dev tools",
    "security": "Security",
    "research": "Research",
    "business": "Business",
    "regulation": "Regulation",
    "other": "Other",
}
UNCLASSIFIED_LABEL = "Unclassified"
