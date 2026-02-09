#!/usr/bin/env python3
"""
Stage 1: Blessed Trader Taxonomy Extraction

Runs taxonomy-targeted extraction on all 18 Blessed Trader PDFs.
Updates coverage matrix and generates report after each batch.

Usage:
    python scripts/run_blessed_taxonomy.py
    python scripts/run_blessed_taxonomy.py --test  # Single PDF test
    python scripts/run_blessed_taxonomy.py --drawer 3  # Specific drawer only
"""

import argparse
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
                # Map OPENROUTER_KEY to OPENROUTER_API_KEY
                if key == "OPENROUTER_KEY":
                    os.environ["OPENROUTER_API_KEY"] = value

import httpx
import yaml

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
TAXONOMY_PATH = PROJECT_ROOT / "data" / "taxonomy" / "reference_taxonomy.yaml"
COVERAGE_PATH = PROJECT_ROOT / "data" / "taxonomy" / "coverage_matrix.yaml"
BLESSED_PATH = PROJECT_ROOT / "data" / "sources" / "blessed_training"
OUTPUT_PATH = PROJECT_ROOT / "data" / "taxonomy" / "blessed_results"
REPORT_PATH = PROJECT_ROOT / "bundles" / "COVERAGE_REPORT.md"


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def save_yaml(data: dict, path: Path):
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from PDF using PyMuPDF."""
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except ImportError:
        print("ERROR: PyMuPDF (fitz) not installed. Run: pip install pymupdf")
        sys.exit(1)


def build_drawer_prompt(drawer_num: int, drawer_data: dict) -> str:
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

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 4000,
    }

    response = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=120.0,
    )
    response.raise_for_status()

    result = response.json()
    return result["choices"][0]["message"]["content"]


def extract_taxonomy_for_drawer(content: str, drawer_num: int, taxonomy: dict) -> list:
    """Extract taxonomy concepts for a specific drawer."""

    # Map drawer numbers to taxonomy keys
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

IMPORTANT: Output EVERY concept - do not skip any."""

    user_prompt = f"""SOURCE CONTENT:
{content[:12000]}

CONCEPTS TO CHECK (Drawer {drawer_num}):
{concepts_prompt}

Check EACH concept above and output one JSON per line."""

    try:
        response = call_llm(system_prompt, user_prompt)

        # Parse JSONL response
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


def update_coverage_matrix(results: list, source: str = "BLESSED_TRADER"):
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

        # FOUND takes precedence
        if status == "FOUND" or (status in ["PARTIAL", "ABSENT"] and current_status == "PENDING"):
            source_entry["status"] = status

        # Add evidence if FOUND
        if status == "FOUND":
            if source_entry.get("evidence") is None:
                source_entry["evidence"] = {"signature_ids": [], "documents": []}

            sig = item.get("signature", "")
            if sig:
                sig_id = f"BT-{concept_id}-{len(source_entry['evidence']['signature_ids']) + 1}"
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


def process_pdf(pdf_path: Path, taxonomy: dict, drawers: list = None) -> dict:
    """Process a single PDF through taxonomy extraction."""
    print(f"\nProcessing: {pdf_path.name}")

    # Extract text
    content = extract_pdf_text(pdf_path)
    if not content.strip():
        print("  WARNING: Empty content")
        return {"file": pdf_path.name, "error": "Empty content"}

    print(f"  Content: {len(content)} chars")

    # Process each drawer
    if drawers is None:
        drawers = [1, 2, 3, 4, 5]  # Skip olya for Blessed

    all_results = []
    for drawer in drawers:
        print(f"  Drawer {drawer}...", end=" ", flush=True)
        results = extract_taxonomy_for_drawer(content, drawer, taxonomy)

        # Add source document to results
        for r in results:
            r["source_document"] = pdf_path.name

        found = sum(1 for r in results if r.get("status") == "FOUND")
        partial = sum(1 for r in results if r.get("status") == "PARTIAL")
        absent = sum(1 for r in results if r.get("status") == "ABSENT")

        print(f"FOUND:{found} PARTIAL:{partial} ABSENT:{absent}")
        all_results.extend(results)

    return {
        "file": pdf_path.name,
        "total_concepts_checked": len(all_results),
        "found": sum(1 for r in all_results if r.get("status") == "FOUND"),
        "partial": sum(1 for r in all_results if r.get("status") == "PARTIAL"),
        "absent": sum(1 for r in all_results if r.get("status") == "ABSENT"),
        "results": all_results,
    }


def main():
    parser = argparse.ArgumentParser(description="Blessed Trader taxonomy extraction")
    parser.add_argument("--test", action="store_true", help="Test with single PDF")
    parser.add_argument("--drawer", type=int, help="Process specific drawer only")
    parser.add_argument("--file", type=str, help="Process specific file")
    args = parser.parse_args()

    # Load taxonomy
    taxonomy = load_yaml(TAXONOMY_PATH)
    print(f"Loaded taxonomy: {TAXONOMY_PATH}")

    # Get PDFs
    pdfs = sorted(BLESSED_PATH.glob("*.pdf"))
    print(f"Found {len(pdfs)} Blessed Trader PDFs")

    if args.test:
        pdfs = pdfs[:1]
        print("TEST MODE: Processing 1 PDF only")

    if args.file:
        pdfs = [p for p in pdfs if args.file in p.name]
        if not pdfs:
            print(f"ERROR: No PDF matching '{args.file}'")
            return

    drawers = [args.drawer] if args.drawer else None

    # Ensure output directory
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    # Process PDFs
    all_file_results = []
    total_found = 0
    total_partial = 0
    total_absent = 0

    for pdf in pdfs:
        result = process_pdf(pdf, taxonomy, drawers)
        all_file_results.append(result)

        if "error" not in result:
            total_found += result.get("found", 0)
            total_partial += result.get("partial", 0)
            total_absent += result.get("absent", 0)

            # Update coverage matrix after each file
            update_coverage_matrix(result.get("results", []))

    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    results_file = OUTPUT_PATH / f"blessed_taxonomy_{timestamp}.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pdfs_processed": len(pdfs),
            "total_found": total_found,
            "total_partial": total_partial,
            "total_absent": total_absent,
            "files": all_file_results,
        }, f, indent=2)

    print(f"\n{'='*60}")
    print("STAGE 1 BLESSED TRADER TAXONOMY EXTRACTION COMPLETE")
    print(f"{'='*60}")
    print(f"PDFs processed: {len(pdfs)}")
    print(f"FOUND: {total_found}")
    print(f"PARTIAL: {total_partial}")
    print(f"ABSENT: {total_absent}")
    print(f"Results: {results_file}")

    # Generate coverage report
    print("\nGenerating coverage report...")
    os.system(f"python3 {PROJECT_ROOT}/scripts/generate_coverage_report.py")


if __name__ == "__main__":
    main()
