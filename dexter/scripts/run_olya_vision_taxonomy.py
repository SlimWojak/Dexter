#!/usr/bin/env python3
"""
Stage 2 REDO: Olya Notes Vision-Enabled Taxonomy Extraction

Uses P3.5 two-pass architecture for image-heavy PDFs:
  Pass 1: Opus vision extracts content from screenshots
  Pass 2: Taxonomy Theorist extracts IF-THEN logic

Threshold: If page has <200 chars text, route through vision.

Usage:
    python scripts/run_olya_vision_taxonomy.py
    python scripts/run_olya_vision_taxonomy.py --test
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Load environment from .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value
                if key == "OPENROUTER_KEY":
                    os.environ["OPENROUTER_API_KEY"] = value

import httpx
import yaml

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF not installed. Run: pip install pymupdf")
    sys.exit(1)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
TAXONOMY_PATH = PROJECT_ROOT / "data" / "taxonomy" / "reference_taxonomy.yaml"
COVERAGE_PATH = PROJECT_ROOT / "data" / "taxonomy" / "coverage_matrix.yaml"
OLYA_PATH = PROJECT_ROOT / "data" / "sources" / "olya_notes"
OUTPUT_PATH = PROJECT_ROOT / "data" / "taxonomy" / "olya_vision_results"

# Thresholds
MIN_TEXT_CHARS = 200  # Below this, use vision extraction


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def save_yaml(data: dict, path: Path):
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


# =============================================================================
# VISION EXTRACTION (Pass 1)
# =============================================================================

VISION_PROMPT = """Describe ALL visible content in this trading notes/chart screenshot.

EXTRACT EVERYTHING:
1. ALL TEXT — headers, bullet points, notes, labels, annotations
2. CHART MARKINGS — zones, lines, arrows, levels
3. ICT TERMINOLOGY — FVG, OB, BSL, SSL, MSS, OTE, IFVG, Breaker, etc.
4. PRICE LEVELS — exact numbers if visible
5. RULES/CONDITIONS — any IF-THEN logic or checklist items
6. TIME/SESSION markers — killzones, session boundaries

CRITICAL: Preserve EXACT terminology. If you see "BSL @ 1.1200", write exactly that.
Return a structured description with all visible information."""


def extract_page_via_vision(page, page_num: int) -> str:
    """Extract content from a PDF page using Opus vision."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(f"    WARNING: ANTHROPIC_API_KEY not set, skipping vision for page {page_num}")
        return ""

    # Render page to image at 150 DPI
    mat = fitz.Matrix(150 / 72, 150 / 72)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")

    # Call Opus vision
    try:
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-5-20250929",  # Use Sonnet for cost efficiency
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": img_base64,
                                },
                            },
                            {"type": "text", "text": VISION_PROMPT},
                        ],
                    }
                ],
                "max_tokens": 4096,
                "temperature": 0.1,
            },
            timeout=120.0,
        )
        response.raise_for_status()
        data = response.json()

        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        return content.strip()

    except Exception as e:
        print(f"    Vision extraction failed for page {page_num}: {e}")
        return ""


def extract_pdf_content(pdf_path: Path) -> dict:
    """Extract content from PDF using vision when needed.

    Returns:
        {
            "text_content": str,  # Combined text from all pages
            "pages": int,
            "vision_pages": int,  # Pages that used vision
            "text_pages": int,    # Pages that had enough text
        }
    """
    doc = fitz.open(str(pdf_path))
    all_content = []
    vision_pages = 0
    text_pages = 0

    for page_num, page in enumerate(doc, 1):
        # First try text extraction
        text = page.get_text().strip()

        if len(text) >= MIN_TEXT_CHARS:
            # Enough text, use it
            all_content.append(f"[Page {page_num} - TEXT]\n{text}")
            text_pages += 1
        else:
            # Not enough text, use vision
            print(f"    Page {page_num}: {len(text)} chars < {MIN_TEXT_CHARS}, using vision...")
            vision_content = extract_page_via_vision(page, page_num)
            if vision_content:
                all_content.append(f"[Page {page_num} - VISION]\n{vision_content}")
                vision_pages += 1
            elif text:
                # Fallback to limited text if vision fails
                all_content.append(f"[Page {page_num} - TEXT (limited)]\n{text}")
                text_pages += 1

    page_count = len(doc)
    doc.close()

    return {
        "text_content": "\n\n".join(all_content),
        "pages": page_count,
        "vision_pages": vision_pages,
        "text_pages": text_pages,
    }


# =============================================================================
# TAXONOMY EXTRACTION (Pass 2)
# =============================================================================

def build_drawer_prompt(drawer_num, drawer_data: dict) -> str:
    """Build extraction prompt for a specific drawer."""
    concepts = drawer_data.get("concepts", [])
    concepts_text = []
    for i, c in enumerate(concepts, 1):
        name = c.get("name", "")
        cid = c.get("id", "")
        defn = c.get("definition", {}).get("canonical", "")[:150]
        terms = [str(t) for t in c.get("definition", {}).get("ict_terminology", [])[:5]]
        concepts_text.append(f"{i}. {name} ({cid})\n   Terms: {', '.join(terms)}\n   Definition: {defn}...")
    return "\n".join(concepts_text)


def call_llm(system_prompt: str, user_prompt: str, model: str = "deepseek/deepseek-chat") -> str:
    """Call LLM via OpenRouter."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set")

    response = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 4000,
        },
        timeout=120.0,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def extract_taxonomy_for_drawer(content: str, drawer_num, taxonomy: dict) -> list:
    """Extract taxonomy concepts for a specific drawer."""
    drawer_keys = {
        1: "drawer_1_htf_bias",
        2: "drawer_2_time_session",
        3: "drawer_3_structure",
        4: "drawer_4_execution",
        5: "drawer_5_protection",
        "olya": "olya_extensions",
    }

    drawer_key = drawer_keys.get(drawer_num)
    if not drawer_key or drawer_key not in taxonomy:
        return []

    drawer_data = taxonomy[drawer_key]
    concepts_prompt = build_drawer_prompt(drawer_num, drawer_data)

    system_prompt = """You are an expert ICT trading analyst. Extract IF-THEN trading logic from content.

For EACH concept listed, determine:
- FOUND: Concept is discussed with actionable IF-THEN logic
- PARTIAL: Concept is mentioned but not as a complete rule
- ABSENT: Concept is not present in this content

Output ONE JSON object per line for EACH concept. Format:
{"concept_id": "CON-D1-BIAS-01", "status": "FOUND", "signature": "IF condition THEN action", "source_quote": "quote from text"}
{"concept_id": "CON-D1-BIAS-02", "status": "ABSENT", "absence_reason": "NOT_DISCUSSED"}

IMPORTANT: Output EVERY concept - do not skip any. Be CONSERVATIVE with FOUND - only mark FOUND if there's clear IF-THEN logic."""

    user_prompt = f"""SOURCE CONTENT (extracted via vision from trading notes):
{content[:15000]}

CONCEPTS TO CHECK (Drawer {drawer_num}):
{concepts_prompt}

Check EACH concept above and output one JSON per line. Be conservative - mark ABSENT if not clearly present."""

    try:
        response = call_llm(system_prompt, user_prompt)
        results = []
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("{"):
                try:
                    obj = json.loads(line)
                    if "concept_id" in obj:
                        results.append(obj)
                except json.JSONDecodeError:
                    continue
        return results
    except Exception as e:
        print(f"    ERROR: {e}")
        return []


# =============================================================================
# COVERAGE MATRIX UPDATE
# =============================================================================

def reset_olya_coverage():
    """Reset Olya Notes coverage to PENDING (discard hallucinated results)."""
    coverage = load_yaml(COVERAGE_PATH)

    for concept_id, concept in coverage.get("coverage", {}).items():
        if "OLYA_NOTES" in concept.get("sources", {}):
            concept["sources"]["OLYA_NOTES"] = {
                "status": "PENDING",
                "evidence": None,
                "last_checked": None,
            }

    coverage["last_updated"] = datetime.now(timezone.utc).isoformat()
    save_yaml(coverage, COVERAGE_PATH)
    print("Reset Olya Notes coverage to PENDING")


def update_coverage_matrix(results: list, source: str = "OLYA_NOTES"):
    """Update coverage matrix with extraction results."""
    coverage = load_yaml(COVERAGE_PATH)
    now = datetime.now(timezone.utc).isoformat()

    for item in results:
        concept_id = item.get("concept_id")
        status = item.get("status", "").upper()

        if not concept_id or concept_id not in coverage.get("coverage", {}):
            continue

        concept = coverage["coverage"][concept_id]
        if source not in concept.get("sources", {}):
            continue

        source_entry = concept["sources"][source]
        current_status = source_entry.get("status", "PENDING")

        if status == "FOUND" or (status in ["PARTIAL", "ABSENT"] and current_status == "PENDING"):
            source_entry["status"] = status

        if status == "FOUND":
            if source_entry.get("evidence") is None:
                source_entry["evidence"] = {"signature_ids": [], "documents": []}
            sig = item.get("signature", "")
            if sig:
                sig_id = f"OLV-{concept_id}-{len(source_entry['evidence']['signature_ids']) + 1}"
                source_entry["evidence"]["signature_ids"].append(sig_id)
            doc = item.get("source_document", "")
            if doc and doc not in source_entry["evidence"]["documents"]:
                source_entry["evidence"]["documents"].append(doc)

        source_entry["last_checked"] = now

    # Update summary stats
    stats = {"FOUND": 0, "ABSENT": 0, "PARTIAL": 0, "PENDING": 0, "NOT_APPLICABLE": 0}
    source_stats = {s: {"found": 0, "total": 0} for s in ["ICT_2022", "BLESSED_TRADER", "OLYA_NOTES"]}

    for cid, concept in coverage.get("coverage", {}).items():
        for src, entry in concept.get("sources", {}).items():
            st = entry.get("status", "PENDING")
            if st in stats:
                stats[st] += 1
            if src in source_stats:
                source_stats[src]["total"] += 1
                if st == "FOUND":
                    source_stats[src]["found"] += 1

    coverage["summary"]["by_status"] = stats
    coverage["summary"]["by_source"] = source_stats
    coverage["last_updated"] = now
    save_yaml(coverage, COVERAGE_PATH)


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_pdf(pdf_path: Path, taxonomy: dict) -> dict:
    """Process a single PDF through vision + taxonomy extraction."""
    print(f"\nProcessing: {pdf_path.name}")

    # Pass 1: Extract content (vision when needed)
    extraction = extract_pdf_content(pdf_path)
    content = extraction["text_content"]

    if not content.strip():
        print("  WARNING: No content extracted")
        return {"file": pdf_path.name, "error": "No content"}

    print(f"  Content: {len(content)} chars ({extraction['vision_pages']} vision, {extraction['text_pages']} text pages)")

    # Pass 2: Taxonomy extraction for each drawer (including olya extensions)
    drawers = [1, 2, 3, 4, 5, "olya"]
    all_results = []

    for drawer in drawers:
        print(f"  Drawer {drawer}...", end=" ", flush=True)
        results = extract_taxonomy_for_drawer(content, drawer, taxonomy)

        for r in results:
            r["source_document"] = pdf_path.name

        found = sum(1 for r in results if r.get("status") == "FOUND")
        partial = sum(1 for r in results if r.get("status") == "PARTIAL")
        absent = sum(1 for r in results if r.get("status") == "ABSENT")

        print(f"FOUND:{found} PARTIAL:{partial} ABSENT:{absent}")
        all_results.extend(results)

    return {
        "file": pdf_path.name,
        "pages": extraction["pages"],
        "vision_pages": extraction["vision_pages"],
        "text_pages": extraction["text_pages"],
        "content_chars": len(content),
        "total_concepts_checked": len(all_results),
        "found": sum(1 for r in all_results if r.get("status") == "FOUND"),
        "partial": sum(1 for r in all_results if r.get("status") == "PARTIAL"),
        "absent": sum(1 for r in all_results if r.get("status") == "ABSENT"),
        "results": all_results,
    }


def main():
    parser = argparse.ArgumentParser(description="Olya Notes vision taxonomy extraction")
    parser.add_argument("--test", action="store_true", help="Test with single PDF")
    parser.add_argument("--file", type=str, help="Process specific file")
    parser.add_argument("--no-reset", action="store_true", help="Don't reset coverage before running")
    args = parser.parse_args()

    taxonomy = load_yaml(TAXONOMY_PATH)
    print(f"Loaded taxonomy: {TAXONOMY_PATH}")

    pdfs = sorted(OLYA_PATH.glob("*.pdf"))
    print(f"Found {len(pdfs)} Olya Notes PDFs")

    if args.test:
        # Pick a known image-heavy PDF for testing
        pdfs = [p for p in pdfs if "5min" in p.name.lower() or "OLYA 10" in p.name]
        if not pdfs:
            pdfs = sorted(OLYA_PATH.glob("*.pdf"))[:1]
        print(f"TEST MODE: Processing {pdfs[0].name}")

    if args.file:
        pdfs = [p for p in pdfs if args.file in p.name]

    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    # Reset Olya coverage (discard hallucinated results)
    if not args.no_reset:
        reset_olya_coverage()

    # Process PDFs
    all_file_results = []
    total_found = 0
    total_partial = 0
    total_absent = 0
    total_vision_pages = 0

    for pdf in pdfs:
        result = process_pdf(pdf, taxonomy)
        all_file_results.append(result)

        if "error" not in result:
            total_found += result.get("found", 0)
            total_partial += result.get("partial", 0)
            total_absent += result.get("absent", 0)
            total_vision_pages += result.get("vision_pages", 0)
            update_coverage_matrix(result.get("results", []))

    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    results_file = OUTPUT_PATH / f"olya_vision_taxonomy_{timestamp}.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pdfs_processed": len(pdfs),
            "total_vision_pages": total_vision_pages,
            "total_found": total_found,
            "total_partial": total_partial,
            "total_absent": total_absent,
            "files": all_file_results,
        }, f, indent=2)

    print(f"\n{'='*60}")
    print("STAGE 2 (REDO) OLYA NOTES VISION TAXONOMY COMPLETE")
    print(f"{'='*60}")
    print(f"PDFs processed: {len(pdfs)}")
    print(f"Vision pages: {total_vision_pages}")
    print(f"FOUND: {total_found}")
    print(f"PARTIAL: {total_partial}")
    print(f"ABSENT: {total_absent}")
    print(f"Results: {results_file}")

    # Generate coverage report
    print("\nGenerating coverage report...")
    os.system(f"python3 {PROJECT_ROOT}/scripts/generate_coverage_report.py")


if __name__ == "__main__":
    main()
