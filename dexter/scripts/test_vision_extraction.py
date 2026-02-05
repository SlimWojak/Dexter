#!/usr/bin/env python3
"""P3.5 Vision Extraction Test Script.

Stage A: Proof of concept with EURUSD PDF
Stage B: Blessed Trader PDFs rerun
Stage C: Olya chart note extraction

Usage:
    python scripts/test_vision_extraction.py --stage A
    python scripts/test_vision_extraction.py --stage B
    python scripts/test_vision_extraction.py --stage C
    python scripts/test_vision_extraction.py --all
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skills.document.vision_extractor import (
    extract_from_pdf_page,
    extract_all_visual_pages,
    format_vision_for_theorist,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("vision_test")


# =============================================================================
# TEST SOURCES
# =============================================================================

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "sources"

STAGE_A_SOURCE = DATA_DIR / "olya_notes" / "OLYA 10 📍✅5min liquidity scalps.pdf"

STAGE_B_SOURCES = [
    DATA_DIR / "blessed_training" / "Lesson_11_PDF_-_M (6).pdf",
    DATA_DIR / "blessed_training" / "Liquidity_PDF_Blessed_TRD (4).pdf",
]

# Best sources for visual extraction (user recommended)
STAGE_C_SOURCE = DATA_DIR / "olya_notes" / "OLYA 7 ✅ A+ SETUPS.pdf"  # 11 pages, 7 image-heavy


# =============================================================================
# STAGE A: EURUSD Proof of Concept
# =============================================================================

def run_stage_a():
    """Stage A: Test vision extraction on EURUSD PDF.

    Expected elements to capture:
    - +OB markers
    - BSL @ price levels
    - W/D Overlap zones
    - 3-question framework text
    - HTF Direction annotations
    """
    logger.info("=" * 60)
    logger.info("STAGE A: EURUSD 5MIN ENTRIES EXAMPLES")
    logger.info("=" * 60)

    if not STAGE_A_SOURCE.exists():
        logger.error("Source not found: %s", STAGE_A_SOURCE)
        return None

    # Extract first visual page
    logger.info("Extracting visual content from: %s", STAGE_A_SOURCE.name)

    # Test single page extraction (page 1)
    result = extract_from_pdf_page(
        STAGE_A_SOURCE,
        page_num=1,
        source_tier="OLYA_PRIMARY",
        content_type="chart",
        use_opus=True,  # Premium quality for proof of concept
    )

    logger.info("\n--- VISION DESCRIPTION (Page 1) ---")
    print(result.get("description", ""))

    # Check for expected ICT elements
    description = result.get("description", "").lower()
    expected_terms = [
        "ob",  # Order block
        "fvg",  # Fair Value Gap
        "liquidity",
        "bsl",  # Buy-side liquidity
        "ssl",  # Sell-side liquidity
    ]

    found_terms = [t for t in expected_terms if t in description]
    logger.info("\n--- ICT TERMS FOUND ---")
    logger.info("Found %d/%d expected terms: %s", len(found_terms), len(expected_terms), found_terms)

    # Format for Theorist
    formatted = format_vision_for_theorist(result)
    logger.info("\n--- FORMATTED FOR THEORIST (first 500 chars) ---")
    print(formatted[:500] + "..." if len(formatted) > 500 else formatted)

    # Save result
    output_dir = Path(__file__).resolve().parent.parent / "memory" / "vision_tests"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"stage_a_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump({
            "stage": "A",
            "source": str(STAGE_A_SOURCE),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "result": result,
            "formatted_length": len(formatted),
            "terms_found": found_terms,
        }, f, indent=2)

    logger.info("\nResult saved to: %s", output_file)

    return result


# =============================================================================
# STAGE B: Blessed Trader PDFs
# =============================================================================

def run_stage_b():
    """Stage B: Rerun Blessed Trader PDFs with vision extraction.

    Previous extraction yielded 0 signatures (visual-only content).
    With vision extraction, we should find chart annotation logic.
    """
    logger.info("=" * 60)
    logger.info("STAGE B: BLESSED TRADER PDFs (Vision Extraction)")
    logger.info("=" * 60)

    all_results = []

    for pdf_path in STAGE_B_SOURCES:
        if not pdf_path.exists():
            logger.warning("Source not found: %s", pdf_path)
            continue

        logger.info("\nProcessing: %s", pdf_path.name)

        # Extract all visual pages
        results = extract_all_visual_pages(
            pdf_path,
            source_tier="LATERAL",
            min_text_chars=100,
            use_opus=False,  # Use Sonnet for lateral sources (cost)
        )

        logger.info("Extracted %d visual pages", len(results))

        for result in results:
            if result.get("description"):
                all_results.append({
                    "source": pdf_path.name,
                    "page": result.get("page_num"),
                    "description_length": len(result.get("description", "")),
                    "model": result.get("model"),
                })

                # Show snippet
                desc = result.get("description", "")[:300]
                logger.info("  Page %d: %d chars - %s...",
                           result.get("page_num"), len(result.get("description", "")), desc[:100])

    # Save results
    output_dir = Path(__file__).resolve().parent.parent / "memory" / "vision_tests"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"stage_b_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump({
            "stage": "B",
            "sources": [str(p) for p in STAGE_B_SOURCES],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results_summary": all_results,
        }, f, indent=2)

    logger.info("\nStage B complete. %d visual pages extracted.", len(all_results))
    logger.info("Result saved to: %s", output_file)

    return all_results


# =============================================================================
# STAGE C: Olya Chart Note
# =============================================================================

def run_stage_c():
    """Stage C: Full pipeline test with Olya chart notes.

    This is the highest-value test:
    PDF → Vision Extraction → Theorist → Auditor → Bundle

    Expected: IF-THEN signatures from annotated chart examples.
    """
    logger.info("=" * 60)
    logger.info("STAGE C: OLYA CHART NOTES (Full Pipeline)")
    logger.info("=" * 60)

    if not STAGE_C_SOURCE.exists():
        logger.error("Source not found: %s", STAGE_C_SOURCE)
        return None

    logger.info("Processing: %s", STAGE_C_SOURCE.name)

    # First, get all visual pages
    visual_results = extract_all_visual_pages(
        STAGE_C_SOURCE,
        source_tier="OLYA_PRIMARY",
        min_text_chars=100,
        use_opus=True,  # Premium quality for Olya's notes
    )

    logger.info("Extracted %d visual pages", len(visual_results))

    # Format for Theorist
    all_formatted = []
    for result in visual_results:
        if result.get("description"):
            formatted = format_vision_for_theorist(result)
            all_formatted.append(formatted)

            logger.info("Page %d: %d chars formatted for Theorist",
                       result.get("page_num"), len(formatted))

    combined = "\n---\n\n".join(all_formatted)

    # Save intermediate result
    output_dir = Path(__file__).resolve().parent.parent / "memory" / "vision_tests"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"stage_c_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump({
            "stage": "C",
            "source": str(STAGE_C_SOURCE),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "visual_pages_count": len(visual_results),
            "formatted_for_theorist_length": len(combined),
            "pages": [
                {
                    "page_num": r.get("page_num"),
                    "description_length": len(r.get("description", "")),
                    "model": r.get("model"),
                }
                for r in visual_results
            ],
        }, f, indent=2)

    # Save the formatted content for manual review
    content_file = output_dir / f"stage_c_content_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.txt"
    with open(content_file, "w") as f:
        f.write(combined)

    logger.info("\nStage C complete.")
    logger.info("Metadata saved to: %s", output_file)
    logger.info("Formatted content saved to: %s", content_file)
    logger.info("Total content: %d chars ready for Theorist", len(combined))

    return {
        "visual_results": visual_results,
        "formatted_content": combined,
    }


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="P3.5 Vision Extraction Tests")
    parser.add_argument(
        "--stage",
        choices=["A", "B", "C"],
        help="Run specific stage (A=EURUSD, B=Blessed, C=Olya)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all stages",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check sources exist without API calls",
    )

    args = parser.parse_args()

    if args.dry_run:
        logger.info("DRY RUN: Checking sources...")
        sources = [STAGE_A_SOURCE] + STAGE_B_SOURCES + [STAGE_C_SOURCE]
        for src in sources:
            status = "OK" if src.exists() else "MISSING"
            logger.info("  [%s] %s", status, src.name)
        return

    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY not set. Required for vision extraction.")
        sys.exit(1)

    if args.all:
        run_stage_a()
        print("\n" + "=" * 60 + "\n")
        run_stage_b()
        print("\n" + "=" * 60 + "\n")
        run_stage_c()
    elif args.stage == "A":
        run_stage_a()
    elif args.stage == "B":
        run_stage_b()
    elif args.stage == "C":
        run_stage_c()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
