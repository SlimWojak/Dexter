#!/usr/bin/env python3
"""Reset ICT 2022 queue and run live Supadata extraction.

This script:
1. Resets the ICT 2022 queue status from DONE to QUEUED
2. Runs extraction with DEXTER_MOCK_MODE=false for live transcripts

Usage:
    python scripts/reset_and_extract_ict.py --reset-only  # Just reset queue
    python scripts/reset_and_extract_ict.py --extract     # Reset and extract
    python scripts/reset_and_extract_ict.py --limit 3     # Extract first 3 videos only
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env")

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ict_extract] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("dexter.ict_extract")

QUEUE_PATH = _PROJECT_ROOT / "corpus" / "ict_2022_mentorship_extraction_queue.yaml"


def reset_queue_status():
    """Reset all videos in ICT 2022 queue from DONE to QUEUED."""
    if not QUEUE_PATH.exists():
        logger.error("Queue file not found: %s", QUEUE_PATH)
        return False

    with open(QUEUE_PATH) as f:
        queue_data = yaml.safe_load(f)

    queue = queue_data.get("queue", [])
    reset_count = 0

    for video in queue:
        if video.get("status") == "DONE":
            video["status"] = "QUEUED"
            video["bundle_id"] = None  # Clear old bundle reference
            reset_count += 1

    # Write back
    with open(QUEUE_PATH, "w") as f:
        yaml.dump(queue_data, f, default_flow_style=False, sort_keys=False)

    logger.info("Reset %d videos from DONE to QUEUED", reset_count)
    return True


def check_supadata_key():
    """Verify Supadata API key is available."""
    key = os.getenv("SUPADATA_KEY") or os.getenv("SUPADATA_API_KEY")
    if not key:
        logger.error("SUPADATA_KEY not set in environment!")
        logger.error("Set SUPADATA_KEY in .env file for live extraction")
        return False
    logger.info("SUPADATA_KEY found (length=%d)", len(key))
    return True


def run_extraction(limit: int = 0):
    """Run ICT 2022 extraction with live Supadata transcripts."""
    # Force mock mode off
    os.environ["DEXTER_MOCK_MODE"] = "false"

    from scripts.run_source_extraction import process_youtube_queue

    logger.info("Starting ICT 2022 live extraction...")
    logger.info("DEXTER_MOCK_MODE=%s", os.environ.get("DEXTER_MOCK_MODE"))

    results = process_youtube_queue(
        queue_path=QUEUE_PATH,
        limit=limit,
        dry_run=False,
        delay_seconds=5.0,
        source_tier="CANON",  # CTO brief says ICT_LEARNING but queue has CANON
    )

    # Summary
    logger.info("=" * 60)
    logger.info("ICT 2022 LIVE EXTRACTION COMPLETE")
    logger.info("=" * 60)
    logger.info("Processed: %d", results.get("processed", 0))
    logger.info("Failed: %d", results.get("failed", 0))
    logger.info("Total signatures: %d", results.get("total_signatures", 0))
    logger.info("Validated: %d", results.get("total_validated", 0))
    logger.info("Rejected: %d", results.get("total_rejected", 0))

    total = results.get("total_validated", 0) + results.get("total_rejected", 0)
    if total > 0:
        rejection_rate = results.get("total_rejected", 0) / total * 100
        logger.info("Rejection rate: %.1f%%", rejection_rate)

    return results


def main():
    parser = argparse.ArgumentParser(description="Reset ICT 2022 queue and run live extraction")
    parser.add_argument("--reset-only", action="store_true", help="Only reset queue, don't extract")
    parser.add_argument("--extract", action="store_true", help="Reset queue and run extraction")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of videos to extract (0=all)")
    parser.add_argument("--skip-reset", action="store_true", help="Skip queue reset, just extract")
    args = parser.parse_args()

    # Check Supadata key first
    if not args.reset_only:
        if not check_supadata_key():
            sys.exit(1)

    # Reset queue
    if not args.skip_reset:
        if not reset_queue_status():
            sys.exit(1)

    if args.reset_only:
        logger.info("Queue reset complete (--reset-only mode)")
        return

    if args.extract or args.limit > 0:
        results = run_extraction(limit=args.limit)

        # Write results summary
        output_file = _PROJECT_ROOT / "bundles" / "ict_2022_live_extraction_results.yaml"
        with open(output_file, "w") as f:
            yaml.dump(results, f, default_flow_style=False)
        logger.info("Results written to: %s", output_file)
    else:
        logger.info("Queue reset. Use --extract to run extraction.")


if __name__ == "__main__":
    main()
