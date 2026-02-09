#!/usr/bin/env python3
"""Debug extraction — trace content flow through pipeline.

Runs single PDF with telemetry at each stage to identify content loss point.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env")

TELEMETRY_DIR = _PROJECT_ROOT / "data" / "audit" / "pipeline_telemetry"
TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)


def log_stage(stage: str, source: str, content: str, metadata: dict = None):
    """Log content at pipeline stage."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "stage": stage,
        "source": source,
        "content_chars": len(content),
        "content_preview": content[:1000] if content else "",
        "content_full": content,
        "metadata": metadata or {},
    }

    safe_name = source.replace("/", "_").replace(" ", "_").replace("(", "").replace(")", "")
    log_file = TELEMETRY_DIR / f"{safe_name}_{stage}.json"
    with open(log_file, "w") as f:
        json.dump(log_entry, f, indent=2)

    print(f"[{stage}] {source}: {len(content)} chars")
    return log_entry


def run_debug_extraction(pdf_path: str):
    """Run extraction with telemetry at each stage."""
    from skills.document.pdf_ingester import ingest_pdf, extract_text_from_pdf

    pdf_path = Path(pdf_path)
    source_name = pdf_path.name
    source_tier = "LATERAL"

    print(f"\n{'='*60}")
    print(f"DEBUG EXTRACTION: {source_name}")
    print(f"{'='*60}\n")

    # Stage A: Raw PDF extraction (pre-chunking)
    print("[STAGE A] Extracting from PDF...")
    extracted = extract_text_from_pdf(pdf_path, source_tier=source_tier)

    # Log each page's text
    for page in extracted.get("pages", []):
        page_num = page.get("page_num", 0)
        page_text = page.get("text", "")
        method = page.get("extraction_method", "unknown")
        log_stage(
            f"A_page_{page_num:02d}_{method}",
            source_name,
            page_text,
            {"page_num": page_num, "method": method, "chars": len(page_text)}
        )

    full_text = extracted.get("full_text", "")
    log_stage("A_full_text", source_name, full_text, {
        "total_pages": extracted.get("total_pages"),
        "text_pages": extracted.get("text_pages"),
        "image_heavy_pages": extracted.get("image_heavy_pages"),
    })

    # Stage B: Chunking
    print("\n[STAGE B] Chunking...")
    ingested = ingest_pdf(pdf_path, source_tier=source_tier)
    chunks = ingested.get("chunks", [])

    for chunk in chunks:
        chunk_num = chunk.get("chunk_num", 0)
        chunk_text = chunk.get("text", "")
        log_stage(
            f"B_chunk_{chunk_num:02d}",
            source_name,
            chunk_text,
            {
                "chunk_num": chunk_num,
                "provenance": chunk.get("provenance"),
                "source_type": chunk.get("source_type"),
            }
        )

    # Stage C: What gets sent to Theorist
    print("\n[STAGE C] Building Theorist input...")

    # Simulate what _extract_llm does
    for chunk_idx, chunk in enumerate(chunks):
        # This is the EXACT logic from theorist.py _extract_llm
        if "start" in chunk and "end" in chunk:
            # Transcript chunk (shouldn't hit this for PDFs)
            user_content = (
                f"TRANSCRIPT SEGMENT [{chunk['start']:.0f}s - {chunk['end']:.0f}s]:\n\n"
                f"{chunk['text']}\n\n"
                f"Extract all if-then trading logic from this segment. Return JSON array only."
            )
        else:
            # Document chunk (PDF/MD)
            section_info = chunk.get("section_title", "")
            section_prefix = f"[Section: {section_info}]\n\n" if section_info else ""
            user_content = (
                f"DOCUMENT EXCERPT:\n\n"
                f"{section_prefix}{chunk.get('text', chunk.get('content', ''))}\n\n"
                f"Extract all if-then trading logic from this excerpt. Return JSON array only."
            )

        log_stage(
            f"C_theorist_input_{chunk_idx:02d}",
            source_name,
            user_content,
            {"chunk_idx": chunk_idx, "source_tier": source_tier}
        )

    # Stage D: Actually call Theorist (if LLM mode enabled)
    if os.getenv("DEXTER_LLM_MODE", "false").lower() == "true":
        print("\n[STAGE D] Calling Theorist (LLM mode)...")
        from core.theorist import extract_signatures

        transcript = {"title": source_name, "segments": []}
        signatures = extract_signatures(
            transcript,
            chunks=chunks,
            source_tier=source_tier,
            source_file=source_name,
        )

        log_stage(
            "D_theorist_output",
            source_name,
            json.dumps(signatures, indent=2),
            {"signature_count": len(signatures)}
        )

        print(f"\n[RESULT] Extracted {len(signatures)} signatures")
        for sig in signatures:
            print(f"  - {sig.get('id')}: IF {sig.get('condition', '')[:50]}...")
    else:
        print("\n[STAGE D] Skipped - LLM mode disabled (set DEXTER_LLM_MODE=true)")

    # Summary
    print(f"\n{'='*60}")
    print("TELEMETRY SUMMARY")
    print(f"{'='*60}")
    print(f"Stage A (raw): {len(full_text)} chars from {extracted.get('total_pages')} pages")
    print(f"Stage B (chunks): {len(chunks)} chunks")
    total_chunk_chars = sum(len(c.get('text', '')) for c in chunks)
    print(f"Stage B (total chunk chars): {total_chunk_chars}")
    print(f"Telemetry saved to: {TELEMETRY_DIR}")

    # Check for content loss
    if total_chunk_chars < len(full_text) * 0.8:
        print(f"\n[WARNING] Content loss detected!")
        print(f"  Full text: {len(full_text)} chars")
        print(f"  Chunk text: {total_chunk_chars} chars")
        print(f"  Loss: {len(full_text) - total_chunk_chars} chars ({100*(1-total_chunk_chars/max(1,len(full_text))):.1f}%)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default to Liquidity PDF
        pdf = _PROJECT_ROOT / "data" / "sources" / "blessed_training" / "Liquidity_PDF_Blessed_TRD (4).pdf"
    else:
        pdf = Path(sys.argv[1])

    if not pdf.exists():
        print(f"Error: PDF not found: {pdf}")
        sys.exit(1)

    run_debug_extraction(str(pdf))
