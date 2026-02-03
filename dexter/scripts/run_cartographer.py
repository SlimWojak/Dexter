#!/usr/bin/env python3
"""Run Cartographer to survey ICT channel and build extraction queue.

Usage:
    python scripts/run_cartographer.py <channel_url>
    python scripts/run_cartographer.py <channel_url> --strategy views
    python scripts/run_cartographer.py <channel_url> --strategy chronological
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Add project root to path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env")

from core.cartographer import run_cartographer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [cartographer] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)


def main():
    parser = argparse.ArgumentParser(
        description="Survey ICT channel and build extraction queue"
    )
    parser.add_argument("channel_url", help="YouTube channel or playlist URL")
    parser.add_argument(
        "--strategy",
        default="mentorship_first",
        choices=["mentorship_first", "chronological", "views"],
        help="Queue prioritization strategy (default: mentorship_first)",
    )
    args = parser.parse_args()

    print(f"Surveying: {args.channel_url}")
    print(f"Strategy: {args.strategy}")
    print("=" * 60)

    result = run_cartographer(args.channel_url, args.strategy)

    print(f"\nVideos found: {result['videos_found']}")
    print(f"Corpus map: {result['corpus_map']}")
    print(f"Extraction queue: {result['extraction_queue']}")
    print(f"Clusters report: {result['clusters_report']}")

    if result.get("categories"):
        print("\nCategories:")
        for cat, count in sorted(result["categories"].items()):
            print(f"  {cat}: {count}")

    if result.get("top_5_queue"):
        print("\nTop 5 in queue:")
        for i, title in enumerate(result["top_5_queue"], 1):
            print(f"  {i}. {title[:70]}")

    print("\nReview queue before running Theorist.")
    print("=" * 60)


if __name__ == "__main__":
    main()
