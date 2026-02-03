#!/usr/bin/env python3
"""Real transcript runner — Phase 4A.

Fetches a real transcript via Supadata, runs jargon check,
then runs the full Dexter extraction pipeline.

Usage:
    python scripts/run_real_transcript.py <youtube_url>
    python scripts/run_real_transcript.py <youtube_url> --mock   # force mock mode
    python scripts/run_real_transcript.py <youtube_url> --jargon-only  # jargon check only
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skills.transcript.supadata import (
    fetch_transcript,
    check_ict_jargon,
    format_for_theorist,
)
from core.loop import process_transcript

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [runner] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("dexter.runner")

# Phase 4A gates
GATE_MIN_SIGNATURES = 10
GATE_MAX_JARGON_ERROR_RATE = 0.05  # 5%
GATE_REJECTION_RATE_MIN = 0.10     # 10%
GATE_REJECTION_RATE_MAX = 0.30     # 30%


def run_jargon_check(video_url: str) -> dict:
    """Fetch transcript and run jargon accuracy check."""
    logger.info("Fetching transcript for jargon check: %s", video_url)
    transcript = fetch_transcript(video_url)

    logger.info(
        "Transcript: '%s' — %d segments",
        transcript.get("title", "?"),
        len(transcript.get("segments", [])),
    )

    jargon = check_ict_jargon(transcript)

    print("\n" + "=" * 60)
    print("ICT JARGON ACCURACY CHECK")
    print("=" * 60)
    print(f"Terms found:      {jargon['terms_found']} / {jargon['terms_checked']}")
    print(f"Error rate:       {jargon['error_rate'] * 100:.1f}%")

    if jargon["found_terms"]:
        print(f"\nFound terms: {', '.join(jargon['found_terms'])}")

    if jargon["potential_errors"]:
        print("\nPotential transcription errors:")
        for err in jargon["potential_errors"]:
            print(f"  - '{err['found']}' → should be '{err['expected']}'")

    # Gate check
    if jargon["error_rate"] > GATE_MAX_JARGON_ERROR_RATE:
        print(f"\n** FAIL: Jargon error rate {jargon['error_rate']*100:.1f}% "
              f"> {GATE_MAX_JARGON_ERROR_RATE*100:.0f}% gate")
        print("** ESCALATE: Consider pivot to Sonix or manual review")
    else:
        print(f"\n** PASS: Jargon error rate within {GATE_MAX_JARGON_ERROR_RATE*100:.0f}% gate")

    print("=" * 60)
    return jargon


def run_full_pipeline(video_url: str) -> dict:
    """Run full extraction pipeline with gate validation."""
    # Step 1: Jargon check
    jargon = run_jargon_check(video_url)

    if jargon["error_rate"] > GATE_MAX_JARGON_ERROR_RATE:
        logger.warning(
            "Jargon error rate %.1f%% exceeds gate. Proceeding with caution.",
            jargon["error_rate"] * 100,
        )

    # Step 2: Full pipeline
    print("\n" + "=" * 60)
    print("RUNNING FULL EXTRACTION PIPELINE")
    print("=" * 60)

    summary = process_transcript(video_url)

    # Step 3: Gate validation
    print("\n" + "=" * 60)
    print("PHASE 4A GATE VALIDATION")
    print("=" * 60)

    total = summary.get("total_extracted", 0)
    validated = summary.get("validated", 0)
    rejected = summary.get("rejected", 0)
    rejection_rate = rejected / max(total, 1)

    print(f"Total extracted:  {total}")
    print(f"Validated:        {validated}")
    print(f"Rejected:         {rejected}")
    print(f"Rejection rate:   {rejection_rate * 100:.1f}%")
    print(f"Bundle:           {summary.get('bundle_id', 'none')}")
    print(f"Jargon error:     {jargon['error_rate'] * 100:.1f}%")

    gates = []

    # Gate 1: Minimum signatures
    if total >= GATE_MIN_SIGNATURES:
        gates.append(("Signatures >= 10", "PASS"))
    else:
        gates.append(("Signatures >= 10", f"FAIL ({total})"))

    # Gate 2: Rejection rate in range
    if GATE_REJECTION_RATE_MIN <= rejection_rate <= GATE_REJECTION_RATE_MAX:
        gates.append(("Rejection 10-30%", "PASS"))
    else:
        gates.append(("Rejection 10-30%", f"FAIL ({rejection_rate*100:.0f}%)"))

    # Gate 3: Jargon accuracy
    if jargon["error_rate"] <= GATE_MAX_JARGON_ERROR_RATE:
        gates.append(("Jargon error < 5%", "PASS"))
    else:
        gates.append(("Jargon error < 5%", f"FAIL ({jargon['error_rate']*100:.1f}%)"))

    print("\nGates:")
    all_pass = True
    for name, status in gates:
        marker = "PASS" if status == "PASS" else "FAIL"
        print(f"  [{marker}] {name}: {status}")
        if status != "PASS":
            all_pass = False

    if all_pass:
        print("\n** ALL GATES PASS — Ready for human review **")
    else:
        print("\n** SOME GATES FAILED — Review before promoting **")

    print("=" * 60)

    return {
        "summary": summary,
        "jargon": jargon,
        "gates": dict(gates),
        "all_gates_pass": all_pass,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Dexter Real Transcript Runner (Phase 4A)"
    )
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "--mock", action="store_true",
        help="Force mock mode (DEXTER_MOCK_MODE=true)",
    )
    parser.add_argument(
        "--jargon-only", action="store_true",
        help="Run jargon check only, skip full pipeline",
    )
    args = parser.parse_args()

    if args.mock:
        os.environ["DEXTER_MOCK_MODE"] = "true"
        logger.info("Mock mode forced via --mock flag")

    if args.jargon_only:
        result = run_jargon_check(args.url)
        print(f"\nJSON: {json.dumps(result, indent=2)}")
    else:
        result = run_full_pipeline(args.url)
        print(f"\nJSON summary: {json.dumps(result['summary'], indent=2)}")


if __name__ == "__main__":
    main()
