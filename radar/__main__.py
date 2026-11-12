"""Command line entry point: ``python -m radar {collect,classify,digest,run}``."""

import argparse
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from radar.classifier import DEFAULT_MODEL, GeminiClassifier
from radar.config import DATA_FILE, DIGEST_DIR, WINDOW_HOURS
from radar.hn import HackerNewsClient
from radar.pipeline import classify, collect, make_digest

log = logging.getLogger("radar")


def warn(message: str) -> None:
    """Log a warning, also surfaced as an annotation when running in GitHub Actions."""
    log.warning(message)
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::warning::{message}")


def run_classification(data_path: Path) -> None:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        warn("GEMINI_API_KEY is not set: stories are stored unclassified and will be "
             "classified on the next run that has a key.")
        return
    model = os.environ.get("GEMINI_MODEL", "").strip() or DEFAULT_MODEL
    log.info("Classifying with %s", model)
    classified, pending = classify(data_path, GeminiClassifier(api_key, model=model))
    if classified < pending:
        warn(f"Only {classified} of {pending} stories were classified; "
             "the rest will be retried on the next run.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m radar", description=__doc__)
    parser.add_argument("command", choices=["collect", "classify", "digest", "run"],
                        help="'run' chains collect, classify and digest")
    parser.add_argument("--data", type=Path, default=DATA_FILE, help="posts CSV file")
    parser.add_argument("--digests", type=Path, default=DIGEST_DIR, help="digest directory")
    parser.add_argument("--window-hours", type=int, default=WINDOW_HOURS,
                        help="collect and rank stories posted in the last N hours")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    now = datetime.now(timezone.utc).replace(microsecond=0)

    if args.command in ("collect", "run"):
        collect(args.data, HackerNewsClient(), now, args.window_hours)
    if args.command in ("classify", "run"):
        run_classification(args.data)
    if args.command in ("digest", "run"):
        print(make_digest(args.data, args.digests, now, args.window_hours))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
