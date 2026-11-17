"""Command line entry point.

Daily pipeline: ``python -m radar {collect,classify,digest,run}``.
Classifier evaluation: ``python -m radar {eval-sample,eval-label,eval-report}``.
"""

import argparse
import logging
import os
from datetime import date, datetime, timezone
from pathlib import Path

from radar.classifier import DEFAULT_MODEL, GeminiClassifier
from radar.config import COLLECT_WINDOW_HOURS, DATA_FILE, DIGEST_DIR
from radar import evaluation
from radar.digest import previous_day
from radar.hn import HackerNewsClient
from radar.pipeline import classify, collect, make_digest
from radar.storage import load_posts

PIPELINE_COMMANDS = ["collect", "classify", "digest", "run"]
EVAL_COMMANDS = ["eval-sample", "eval-label", "eval-report"]

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


def run_evaluation(command: str, data_path: Path, eval_dir: Path) -> int:
    labels_path = eval_dir / evaluation.LABELS_NAME
    if command == "eval-sample":
        try:
            path = evaluation.create_sample(load_posts(data_path), eval_dir)
        except FileExistsError as exc:
            log.error("%s", exc)
            return 1
        print(f"Sample written to {path}. Label it with: python -m radar eval-label")
        return 0
    if not labels_path.exists():
        log.error("No sample yet: run python -m radar eval-sample first")
        return 1
    if command == "eval-label":
        count = evaluation.label_interactively(labels_path)
        print(f"\n{count} stories labelled this session; progress saved to {labels_path}")
        return 0

    ev = evaluation.evaluate(evaluation.read_csv(labels_path),
                             evaluation.read_csv(eval_dir / evaluation.PREDICTIONS_NAME))
    for row in ev.invalid.itertuples(index=False):
        warn(f"Unknown label {row.human_theme!r} for story {row.id} ({row.title[:60]}): "
             f"use 0-9 or one of {', '.join(evaluation.KEYS.values())}. Ignored.")
    report_path = eval_dir / evaluation.REPORT_NAME
    report_path.write_text(evaluation.render_report(ev), encoding="utf-8")
    low, high = ev.interval
    print(f"{ev.labelled} labelled, {len(ev.not_ai)} not about AI. "
          f"Theme accuracy {ev.accuracy:.0%} ({ev.correct}/{ev.total}), "
          f"95% CI {low:.0%}-{high:.0%}. Report: {report_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m radar", description=__doc__)
    parser.add_argument("command", choices=PIPELINE_COMMANDS + EVAL_COMMANDS,
                        help="'run' chains collect, classify and digest")
    parser.add_argument("--data", type=Path, default=DATA_FILE, help="posts CSV file")
    parser.add_argument("--digests", type=Path, default=DIGEST_DIR, help="digest directory")
    parser.add_argument("--window-hours", type=int, default=COLLECT_WINDOW_HOURS,
                        help="collect stories posted in the last N hours (default: %(default)s)")
    parser.add_argument("--date", type=date.fromisoformat, default=None,
                        help="UTC day of the digest, YYYY-MM-DD (default: yesterday)")
    parser.add_argument("--eval-dir", type=Path, default=evaluation.EVAL_DIR,
                        help="directory of the evaluation files")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if args.command in EVAL_COMMANDS:
        return run_evaluation(args.command, args.data, args.eval_dir)

    now = datetime.now(timezone.utc).replace(microsecond=0)
    day = args.date or previous_day(now)
    if args.command in ("digest", "run") and day >= now.date():
        warn(f"{day} is not over yet (UTC): its digest will be incomplete.")

    if args.command in ("collect", "run"):
        collect(args.data, HackerNewsClient(), now, args.window_hours)
    if args.command in ("classify", "run"):
        run_classification(args.data)
    if args.command in ("digest", "run"):
        print(make_digest(args.data, args.digests, day))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
