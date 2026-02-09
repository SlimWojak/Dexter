#!/usr/bin/env python3
"""
Taxonomy-Targeted Extraction Runner

Runs taxonomy-aware extraction that checks EACH concept in the reference taxonomy
and documents both FOUND and ABSENT concepts for coverage verification.

Usage:
    # Extract from a single document with taxonomy targeting
    python scripts/run_taxonomy_extraction.py --source /path/to/doc.pdf --source-tier BLESSED_TRADER

    # Extract specific drawer only
    python scripts/run_taxonomy_extraction.py --source /path/to/doc.pdf --drawer 3

    # Run full taxonomy pass on existing bundle
    python scripts/run_taxonomy_extraction.py --bundle B-20260209-091001 --taxonomy-pass

    # Batch process all documents in a source
    python scripts/run_taxonomy_extraction.py --batch --source-tier ICT_2022

Author: Dexter COO
Version: 1.0
"""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml


# Paths
PROJECT_ROOT = Path(__file__).parent.parent
TAXONOMY_PATH = PROJECT_ROOT / "data" / "taxonomy" / "reference_taxonomy.yaml"
COVERAGE_PATH = PROJECT_ROOT / "data" / "taxonomy" / "coverage_matrix.yaml"
THEORIST_PROMPT_PATH = PROJECT_ROOT / "roles" / "theorist_taxonomy.yaml"
BUNDLES_PATH = PROJECT_ROOT / "bundles"
OUTPUT_PATH = PROJECT_ROOT / "data" / "taxonomy" / "extraction_results"


def load_yaml(path: Path) -> dict:
    """Load YAML file."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_taxonomy_concepts() -> dict:
    """Load and structure taxonomy concepts by drawer."""
    taxonomy = load_yaml(TAXONOMY_PATH)

    drawers = {}
    drawer_mapping = {
        "drawer_1_htf_bias": 1,
        "drawer_2_time_session": 2,
        "drawer_3_structure": 3,
        "drawer_4_execution": 4,
        "drawer_5_protection": 5,
        "olya_extensions": "olya",
    }

    for yaml_key, drawer_num in drawer_mapping.items():
        if yaml_key in taxonomy:
            drawer = taxonomy[yaml_key]
            concepts = []
            for concept in drawer.get("concepts", []):
                concepts.append({
                    "id": concept["id"],
                    "name": concept["name"],
                    "definition": concept.get("definition", {}).get("canonical", ""),
                    "terminology": concept.get("definition", {}).get("ict_terminology", []),
                })
            drawers[drawer_num] = {
                "name": drawer.get("name", yaml_key),
                "concepts": concepts,
            }

    return drawers


def build_taxonomy_prompt(drawer_num: int | str, drawers: dict) -> str:
    """Build the taxonomy extraction prompt for a specific drawer."""
    prompt_config = load_yaml(THEORIST_PROMPT_PATH)

    drawer = drawers.get(drawer_num, {})
    if not drawer:
        raise ValueError(f"Unknown drawer: {drawer_num}")

    # Build concepts list
    concepts_text = []
    for i, concept in enumerate(drawer["concepts"], 1):
        term_str = ", ".join(concept["terminology"][:5]) if concept["terminology"] else ""
        concepts_text.append(
            f"{i}. {concept['name']} ({concept['id']})\n"
            f"   Definition: {concept['definition'][:200]}...\n"
            f"   Key terms: {term_str}"
        )

    concepts_list = "\n".join(concepts_text)

    # Get drawer name
    drawer_key = f"drawer_{drawer_num}" if isinstance(drawer_num, int) else "olya_extensions"
    drawer_config = prompt_config.get("drawer_prompts", {}).get(drawer_key, {})

    return prompt_config["extraction_prompt_template"].format(
        source_content="{content}",  # Will be filled later
        drawer_number=drawer_num,
        drawer_name=drawer_config.get("name", drawer["name"]),
        concepts_list=concepts_list,
    )


def extract_with_taxonomy(
    content: str,
    drawer_num: int | str,
    drawers: dict,
    model: str = "deepseek/deepseek-chat",
    api_key: Optional[str] = None,
) -> list:
    """
    Run taxonomy-targeted extraction on content for a specific drawer.

    Returns list of extraction results with status for each concept.
    """
    import httpx

    # Build prompt
    prompt_template = build_taxonomy_prompt(drawer_num, drawers)
    full_prompt = prompt_template.replace("{content}", content[:15000])  # Limit content size

    # Load theorist config
    prompt_config = load_yaml(THEORIST_PROMPT_PATH)
    system_prompt = prompt_config.get("system_prompt", "")

    # API call
    api_key = api_key or os.getenv("OPENROUTER_API_KEY")
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
            {"role": "user", "content": full_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 8000,
    }

    response = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=120.0,
    )
    response.raise_for_status()

    result = response.json()
    content = result["choices"][0]["message"]["content"]

    # Parse JSONL output
    extractions = []
    for line in content.strip().split("\n"):
        line = line.strip()
        if line.startswith("{"):
            try:
                obj = json.loads(line)
                extractions.append(obj)
            except json.JSONDecodeError:
                continue

    return extractions


def process_document(
    doc_path: Path,
    source_tier: str,
    drawers: Optional[list] = None,
    model: str = "deepseek/deepseek-chat",
) -> dict:
    """
    Process a document through taxonomy-targeted extraction.

    Args:
        doc_path: Path to document (PDF or MD)
        source_tier: Source tier (ICT_2022, BLESSED_TRADER, OLYA_NOTES)
        drawers: List of drawer numbers to process (default: all)
        model: Model to use for extraction

    Returns:
        Extraction results by drawer
    """
    # Load document content
    if doc_path.suffix.lower() == ".pdf":
        # Use PDF ingestion
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(doc_path))
            content = ""
            for page in doc:
                content += page.get_text()
            doc.close()
        except ImportError:
            raise ImportError("PyMuPDF (fitz) required for PDF extraction")
    elif doc_path.suffix.lower() in [".md", ".txt"]:
        content = doc_path.read_text()
    else:
        raise ValueError(f"Unsupported file type: {doc_path.suffix}")

    if not content.strip():
        return {"error": "Empty document content"}

    # Load taxonomy
    taxonomy_drawers = load_taxonomy_concepts()

    # Determine which drawers to process
    if drawers is None:
        drawers = [1, 2, 3, 4, 5, "olya"]

    # Process each drawer
    results = {
        "document": str(doc_path),
        "source_tier": source_tier,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "drawers": {},
    }

    for drawer_num in drawers:
        print(f"  Processing drawer {drawer_num}...")
        try:
            extractions = extract_with_taxonomy(
                content, drawer_num, taxonomy_drawers, model
            )

            # Summarize
            found = sum(1 for e in extractions if e.get("status") == "FOUND")
            partial = sum(1 for e in extractions if e.get("status") == "PARTIAL")
            absent = sum(1 for e in extractions if e.get("status") == "ABSENT")

            results["drawers"][drawer_num] = {
                "found": found,
                "partial": partial,
                "absent": absent,
                "total": len(extractions),
                "extractions": extractions,
            }

            print(f"    FOUND: {found}, PARTIAL: {partial}, ABSENT: {absent}")

        except Exception as e:
            results["drawers"][drawer_num] = {"error": str(e)}
            print(f"    ERROR: {e}")

    return results


def update_coverage_from_results(results: dict) -> None:
    """Update coverage matrix from extraction results."""
    from update_coverage_matrix import (
        load_coverage_matrix,
        save_yaml,
        update_summary,
    )

    coverage = load_coverage_matrix()
    source = results.get("source_tier", "")

    # Map tier to coverage source
    tier_map = {
        "ICT_2022": "ICT_2022",
        "CANON": "ICT_2022",
        "BLESSED_TRADER": "BLESSED_TRADER",
        "LATERAL": "BLESSED_TRADER",
        "OLYA_NOTES": "OLYA_NOTES",
        "OLYA_PRIMARY": "OLYA_NOTES",
    }
    coverage_source = tier_map.get(source.upper())
    if not coverage_source:
        print(f"Unknown source tier: {source}")
        return

    now = datetime.now(timezone.utc).isoformat()

    # Update coverage for each extraction
    for drawer_num, drawer_results in results.get("drawers", {}).items():
        if "error" in drawer_results:
            continue

        for extraction in drawer_results.get("extractions", []):
            concept_id = extraction.get("concept_id")
            status = extraction.get("status", "").upper()

            if not concept_id or concept_id not in coverage.get("coverage", {}):
                continue

            concept = coverage["coverage"][concept_id]
            if coverage_source not in concept.get("sources", {}):
                continue

            source_entry = concept["sources"][coverage_source]

            # Update status (FOUND takes precedence)
            current = source_entry.get("status", "PENDING")
            if status == "FOUND" or (status in ["PARTIAL", "ABSENT"] and current == "PENDING"):
                source_entry["status"] = status

            # Update evidence if FOUND
            if status == "FOUND":
                if source_entry.get("evidence") is None:
                    source_entry["evidence"] = {
                        "signature_ids": [],
                        "bundles": [],
                        "documents": [],
                    }

                doc = results.get("document", "")
                if doc and doc not in source_entry["evidence"]["documents"]:
                    source_entry["evidence"]["documents"].append(doc)

                # Add signature
                sig = extraction.get("signature", "")
                if sig:
                    sig_id = f"TAX-{concept_id}-{len(source_entry['evidence']['signature_ids']) + 1}"
                    source_entry["evidence"]["signature_ids"].append(sig_id)

            # Update timestamp
            source_entry["last_checked"] = now

    # Update summary
    coverage = update_summary(coverage)
    coverage["last_updated"] = now

    save_yaml(coverage, COVERAGE_PATH)
    print(f"Updated coverage matrix: {COVERAGE_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Taxonomy-targeted extraction")
    parser.add_argument("--source", type=Path, help="Source document path")
    parser.add_argument("--source-tier", help="Source tier (ICT_2022, BLESSED_TRADER, OLYA_NOTES)")
    parser.add_argument("--drawer", type=int, help="Process specific drawer only")
    parser.add_argument("--bundle", help="Process existing bundle")
    parser.add_argument("--taxonomy-pass", action="store_true", help="Run taxonomy pass on bundle")
    parser.add_argument("--batch", action="store_true", help="Batch process all documents")
    parser.add_argument("--model", default="deepseek/deepseek-chat", help="Model to use")
    parser.add_argument("--update-coverage", action="store_true", help="Update coverage matrix")
    parser.add_argument("--output", type=Path, help="Output path for results")

    args = parser.parse_args()

    # Ensure output directory exists
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    if args.source and args.source_tier:
        # Single document processing
        print(f"Processing: {args.source}")
        print(f"Source tier: {args.source_tier}")

        drawers = [args.drawer] if args.drawer else None

        results = process_document(
            args.source,
            args.source_tier,
            drawers=drawers,
            model=args.model,
        )

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_file = args.output or (OUTPUT_PATH / f"taxonomy_{args.source.stem}_{timestamp}.json")

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to: {output_file}")

        # Update coverage if requested
        if args.update_coverage:
            update_coverage_from_results(results)

        # Summary
        total_found = sum(d.get("found", 0) for d in results.get("drawers", {}).values() if isinstance(d, dict))
        total_partial = sum(d.get("partial", 0) for d in results.get("drawers", {}).values() if isinstance(d, dict))
        total_absent = sum(d.get("absent", 0) for d in results.get("drawers", {}).values() if isinstance(d, dict))

        print(f"\n=== SUMMARY ===")
        print(f"FOUND: {total_found}")
        print(f"PARTIAL: {total_partial}")
        print(f"ABSENT: {total_absent}")

    elif args.batch:
        print("Batch mode not yet implemented - use single document mode")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
