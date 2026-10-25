"""City Council Minutes pipeline CLI.

Subcommands (each stage is idempotent and resumable):
  discover   walk Laserfiche Signed Minutes → data/original/laserfiche/inventory.csv
  sample     choose one meeting per (year, quarter) → data/lookups/sample_quarterly.csv
  fetch      download PDFs (sample or all) → data/original/laserfiche/pdf/
  convert    Datalab OCR → data/interim/datalab/markdown/
  extract    Datalab structured extraction → data/interim/datalab/extract/
  tidy       extraction JSON → data/processed/*.csv + meetings.json
  score      compare against the hand-transcribed 2021–22 meetings
  audit      coverage, NA rates, cost so far + projection → data/audit/
  run        fetch → convert → extract → tidy → score → audit

Run as `uv run python -m scripts <subcommand>`.
"""

from __future__ import annotations

import argparse
import logging
import sys


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="city-council-minutes", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("discover", help="Walk the Laserfiche folder tree")
    d.add_argument("--refresh", action="store_true", help="Re-list folders already cached")
    d.add_argument("--years", type=int, nargs="*", help="Limit to these year folders")

    s = sub.add_parser("sample", help="Pick one meeting per quarter per year")
    s.add_argument("--seed", type=int, default=20261025)

    for name in ("fetch", "convert", "extract", "run"):
        sp = sub.add_parser(name)
        sp.add_argument("--scope", choices=["sample", "gold", "all"], default="sample",
                        help="sample = quarterly sample; gold = the 41 hand-transcribed meetings")
        sp.add_argument("--limit", type=int, help="Process at most N documents (for testing)")
        sp.add_argument("--entry-ids", type=int, nargs="*", help="Only these entry ids")
        sp.add_argument("--mode", choices=["fast", "balanced", "accurate"], default="balanced",
                        help="Datalab extraction mode (extract/run only)")

    t = sub.add_parser("tidy")
    t.add_argument("--mode", choices=["fast", "balanced", "accurate"], default="balanced")
    sub.add_parser("score")
    sub.add_parser("audit")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        level=logging.DEBUG if args.verbose else logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    if args.cmd == "discover":
        from scripts.discover import discover
        discover(refresh=args.refresh, years=set(args.years) if args.years else None)
        return 0
    if args.cmd == "sample":
        from scripts.sample import build_sample
        build_sample(seed=args.seed)
        return 0
    if args.cmd in ("fetch", "run"):
        from scripts.fetch import fetch
        rc = fetch(scope=args.scope, limit=args.limit, entry_ids=args.entry_ids)
        if args.cmd == "fetch":
            return rc
    if args.cmd in ("convert", "run"):
        from scripts.datalab import convert_all
        rc = convert_all(scope=args.scope, limit=args.limit, entry_ids=args.entry_ids)
        if args.cmd == "convert":
            return rc
    if args.cmd in ("extract", "run"):
        from scripts.datalab import extract_all
        rc = extract_all(scope=args.scope, limit=args.limit, entry_ids=args.entry_ids,
                         mode=args.mode)
        if args.cmd == "extract":
            return rc
    if args.cmd in ("tidy", "run"):
        from scripts.tidy import tidy_all
        tidy_all(mode=getattr(args, "mode", "balanced"))
    if args.cmd in ("score", "run"):
        from scripts.score import score
        score()
    if args.cmd in ("audit", "run"):
        from scripts.audit import audit
        audit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
