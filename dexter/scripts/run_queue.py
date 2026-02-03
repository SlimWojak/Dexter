#!/usr/bin/env python3
"""Run Queue Processor — batch extraction from Cartographer queue.

Usage:
    python scripts/run_queue.py                    # dry run (default)
    python scripts/run_queue.py --execute          # real processing
    python scripts/run_queue.py --execute --limit 3  # process first 3
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env")

from core.queue_processor import process_queue

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [queue] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)


def main():
    parser = argparse.ArgumentParser(
        description="Process extraction queue (Cartographer → Theorist pipeline)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually process (default is dry run)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max videos to process (0 = all pending)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=5.0,
        help="Seconds between videos (default: 5)",
    )
    parser.add_argument(
        "--queue",
        type=str,
        default=None,
        help="Path to extraction_queue.yaml (default: corpus/extraction_queue.yaml)",
    )
    args = parser.parse_args()

    dry_run = not args.execute
    queue_path = Path(args.queue) if args.queue else None

    if dry_run:
        print("DRY RUN — use --execute to actually process")
    print("=" * 60)

    result = process_queue(
        queue_path=queue_path,
        limit=args.limit,
        dry_run=dry_run,
        delay_seconds=args.delay,
    )

    print(f"\nProcessed: {result['processed']}")
    print(f"Failed: {result['failed']}")
    print(f"Skipped: {result['skipped']}")

    if result.get("results"):
        print("\nResults:")
        for r in result["results"]:
            status = r.get("status") or r.get("action", "?")
            print(f"  {r['video_id']}: {status} — {r['title']}")

    print("=" * 60)


if __name__ == "__main__":
    main()
