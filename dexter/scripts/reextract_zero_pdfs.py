#!/usr/bin/env python3
"""Re-extract the 10 zero-signature PDFs after pipeline fix."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env")

# The 10 PDFs that returned 0 signatures in Stage 2
ZERO_SIGNATURE_PDFS = [
    "Liquidity_PDF_Blessed_TRD (4).pdf",
    "Orderblock_Propulsion_Block_Breaker (3).pdf",
    "Weekly__Daily_Structure___Price_Delivery (2).pdf",
    "Lesson_11_PDF_-_M (6).pdf",
    "Lesson_15_PDF (3).pdf",
    "Lesson_16_PDF (3).pdf",
    "Lesson_17_PDF (2).pdf",
    "Lesson_20_PDF (4).pdf",
    "Lesson_5_PDF (2).pdf",
    "EU_DXY_SMT_Divergence. (1).pdf",
]

BLESSED_DIR = _PROJECT_ROOT / "data" / "sources" / "blessed_training"


def main():
    from core.loop import process_document

    print(f"\n{'='*70}")
    print("PIPELINE FIX VALIDATION — RE-EXTRACTING 10 ZERO-SIGNATURE PDFs")
    print(f"{'='*70}\n")

    results = []
    total_extracted = 0
    total_validated = 0
    pdfs_with_sigs = 0

    for i, pdf_name in enumerate(ZERO_SIGNATURE_PDFS, 1):
        pdf_path = BLESSED_DIR / pdf_name
        if not pdf_path.exists():
            print(f"[{i}/10] SKIP: {pdf_name} (not found)")
            results.append({"file": pdf_name, "status": "NOT_FOUND"})
            continue

        print(f"\n[{i}/10] Processing: {pdf_name}")
        print("-" * 50)

        try:
            result = process_document(
                str(pdf_path),
                source_tier="LATERAL",
                source_type="pdf",
            )

            extracted = result.get("total_extracted", 0)
            validated = result.get("validated", 0)
            rejected = result.get("rejected", 0)
            bundle_id = result.get("bundle_id")

            total_extracted += extracted
            total_validated += validated
            if validated > 0:
                pdfs_with_sigs += 1

            results.append({
                "file": pdf_name,
                "status": "DONE",
                "extracted": extracted,
                "validated": validated,
                "rejected": rejected,
                "bundle_id": bundle_id,
            })

            print(f"  Extracted: {extracted}, Validated: {validated}, Rejected: {rejected}")
            if bundle_id:
                print(f"  Bundle: {bundle_id}")

        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({"file": pdf_name, "status": "ERROR", "error": str(e)[:200]})

    # Summary
    print(f"\n{'='*70}")
    print("RE-EXTRACTION SUMMARY")
    print(f"{'='*70}")
    print(f"PDFs processed: {len(results)}")
    print(f"PDFs with signatures: {pdfs_with_sigs}")
    print(f"Total extracted: {total_extracted}")
    print(f"Total validated: {total_validated}")

    # Per-PDF table
    print(f"\n{'PDF':<50} {'Extracted':>10} {'Validated':>10}")
    print("-" * 72)
    for r in results:
        if r["status"] == "DONE":
            print(f"{r['file']:<50} {r.get('extracted', 0):>10} {r.get('validated', 0):>10}")
        else:
            print(f"{r['file']:<50} {'—':>10} {r['status']:>10}")

    # Validation check
    print(f"\n{'='*70}")
    if pdfs_with_sigs >= 3:
        print("VALIDATION: PASSED — At least 3 PDFs now yield signatures")
    else:
        print(f"VALIDATION: FAILED — Only {pdfs_with_sigs}/3 required PDFs yield signatures")
    print(f"{'='*70}\n")

    # Save results
    results_file = _PROJECT_ROOT / "data" / "audit" / "pipeline_fix_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "pdfs_processed": len(results),
            "pdfs_with_signatures": pdfs_with_sigs,
            "total_extracted": total_extracted,
            "total_validated": total_validated,
            "results": results,
        }, f, indent=2)
    print(f"Results saved to: {results_file}")


if __name__ == "__main__":
    main()
