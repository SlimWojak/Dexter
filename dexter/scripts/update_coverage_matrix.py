#!/usr/bin/env python3
"""
Coverage Matrix Updater for Dexter Taxonomy System

Updates the coverage matrix (data/taxonomy/coverage_matrix.yaml) based on:
1. Extraction results from bundles/
2. Taxonomy-targeted extraction output

Usage:
    python scripts/update_coverage_matrix.py --source ICT_2022 --bundle B-20260209-091001
    python scripts/update_coverage_matrix.py --scan-all
    python scripts/update_coverage_matrix.py --report

Author: Dexter COO
Version: 1.0
"""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml


# Paths
PROJECT_ROOT = Path(__file__).parent.parent
TAXONOMY_PATH = PROJECT_ROOT / "data" / "taxonomy" / "reference_taxonomy.yaml"
COVERAGE_PATH = PROJECT_ROOT / "data" / "taxonomy" / "coverage_matrix.yaml"
BUNDLES_PATH = PROJECT_ROOT / "bundles"
INDEX_PATH = BUNDLES_PATH / "index.jsonl"


def load_yaml(path: Path) -> dict:
    """Load YAML file."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def save_yaml(data: dict, path: Path) -> None:
    """Save YAML file with proper formatting."""
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def load_taxonomy() -> dict:
    """Load reference taxonomy and build concept lookup."""
    taxonomy = load_yaml(TAXONOMY_PATH)

    # Build flat concept lookup
    concepts = {}

    for drawer_key in ["drawer_1_htf_bias", "drawer_2_time_session", "drawer_3_structure",
                       "drawer_4_execution", "drawer_5_protection", "olya_extensions"]:
        if drawer_key in taxonomy:
            drawer = taxonomy[drawer_key]
            for concept in drawer.get("concepts", []):
                concepts[concept["id"]] = {
                    "name": concept["name"],
                    "category": concept.get("category", ""),
                    "ict_terminology": concept.get("definition", {}).get("ict_terminology", []),
                    "drawer": drawer.get("name", drawer_key),
                }

    return concepts


def load_coverage_matrix() -> dict:
    """Load coverage matrix."""
    return load_yaml(COVERAGE_PATH)


def load_bundle_claims(bundle_id: str) -> list:
    """Load claims from a bundle's claims file."""
    claims_path = BUNDLES_PATH / f"{bundle_id}_claims.jsonl"
    if not claims_path.exists():
        return []

    claims = []
    with open(claims_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    claims.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return claims


def match_signature_to_concepts(signature: dict, concepts: dict) -> list:
    """
    Match a signature to taxonomy concepts based on:
    1. Direct concept_id if present
    2. Drawer assignment + terminology matching
    3. ICT terminology keyword matching

    Returns list of matched concept IDs.
    """
    matched = []

    # Check for direct concept_id assignment (from taxonomy-targeted extraction)
    if "concept_id" in signature:
        if signature["concept_id"] in concepts:
            return [signature["concept_id"]]

    # Get signature text for matching
    sig_text = signature.get("signature", "").lower()
    condition = signature.get("condition", "").lower()
    action = signature.get("action", "").lower()
    full_text = f"{sig_text} {condition} {action}"

    # Get drawer from signature
    sig_drawer = signature.get("drawer", "").upper()

    # Match based on terminology
    for concept_id, concept in concepts.items():
        score = 0

        # Check ICT terminology matches
        for term in concept.get("ict_terminology", []):
            term_lower = term.lower()
            if term_lower in full_text:
                score += 1

        # Bonus for drawer match
        concept_drawer = concept.get("drawer", "")
        if sig_drawer and concept_drawer:
            if sig_drawer in concept_drawer.upper() or concept_drawer.upper() in sig_drawer:
                score += 2

        # Threshold for match
        if score >= 2:  # At least 2 terminology matches or drawer match + 1 term
            matched.append((concept_id, score))

    # Return top matches (sorted by score)
    matched.sort(key=lambda x: x[1], reverse=True)
    return [m[0] for m in matched[:3]]  # Top 3 matches max


def determine_source_from_bundle(bundle_id: str, index_entries: list) -> Optional[str]:
    """Determine source tier from bundle metadata."""
    for entry in index_entries:
        if entry.get("bundle_id") == bundle_id:
            source_tier = entry.get("source_tier", "").upper()

            # Map tiers to coverage matrix sources
            tier_map = {
                "CANON": "ICT_2022",
                "ICT_2022": "ICT_2022",
                "LATERAL": "BLESSED_TRADER",
                "BLESSED_TRADER": "BLESSED_TRADER",
                "OLYA_PRIMARY": "OLYA_NOTES",
                "OLYA_NOTES": "OLYA_NOTES",
            }
            return tier_map.get(source_tier)

    return None


def load_index() -> list:
    """Load bundle index."""
    if not INDEX_PATH.exists():
        return []

    entries = []
    with open(INDEX_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def update_coverage_for_bundle(
    coverage: dict,
    concepts: dict,
    bundle_id: str,
    source: str,
    claims: list
) -> dict:
    """Update coverage matrix for a specific bundle's claims."""

    now = datetime.now(timezone.utc).isoformat()

    for claim in claims:
        # Match claim to concepts
        matched_concepts = match_signature_to_concepts(claim, concepts)

        for concept_id in matched_concepts:
            if concept_id not in coverage["coverage"]:
                continue

            concept_entry = coverage["coverage"][concept_id]
            if source not in concept_entry["sources"]:
                continue

            source_entry = concept_entry["sources"][source]

            # Update status
            current_status = source_entry.get("status", "PENDING")

            # FOUND takes precedence over PENDING/PARTIAL
            if current_status != "FOUND":
                source_entry["status"] = "FOUND"

            # Update evidence
            if source_entry.get("evidence") is None:
                source_entry["evidence"] = {
                    "signature_ids": [],
                    "bundles": [],
                    "documents": [],
                }

            # Add signature reference
            sig_id = claim.get("id", claim.get("signature_id", ""))
            if sig_id and sig_id not in source_entry["evidence"]["signature_ids"]:
                source_entry["evidence"]["signature_ids"].append(sig_id)

            # Add bundle reference
            if bundle_id not in source_entry["evidence"]["bundles"]:
                source_entry["evidence"]["bundles"].append(bundle_id)

            # Add document reference
            doc = claim.get("source_document", claim.get("source", ""))
            if doc and doc not in source_entry["evidence"]["documents"]:
                source_entry["evidence"]["documents"].append(doc)

            # Update timestamp
            source_entry["last_checked"] = now

    return coverage


def update_summary(coverage: dict) -> dict:
    """Recalculate summary statistics."""

    stats = {
        "FOUND": 0,
        "ABSENT": 0,
        "PARTIAL": 0,
        "PENDING": 0,
        "NOT_APPLICABLE": 0,
    }

    drawer_stats = {
        "drawer_1": {"found": 0, "total": 0},
        "drawer_2": {"found": 0, "total": 0},
        "drawer_3": {"found": 0, "total": 0},
        "drawer_4": {"found": 0, "total": 0},
        "drawer_5": {"found": 0, "total": 0},
        "olya": {"found": 0, "total": 0},
    }

    source_stats = {
        "ICT_2022": {"found": 0, "total": 0},
        "BLESSED_TRADER": {"found": 0, "total": 0},
        "OLYA_NOTES": {"found": 0, "total": 0},
    }

    for concept_id, concept in coverage.get("coverage", {}).items():
        # Determine drawer
        drawer = concept.get("drawer", 0)
        if isinstance(drawer, int):
            drawer_key = f"drawer_{drawer}" if drawer <= 5 else "olya"
        else:
            drawer_key = "olya"

        for source, entry in concept.get("sources", {}).items():
            status = entry.get("status", "PENDING")

            # Update global stats
            if status in stats:
                stats[status] += 1

            # Update drawer stats
            if drawer_key in drawer_stats:
                drawer_stats[drawer_key]["total"] += 1
                if status == "FOUND":
                    drawer_stats[drawer_key]["found"] += 1

            # Update source stats
            if source in source_stats:
                source_stats[source]["total"] += 1
                if status == "FOUND":
                    source_stats[source]["found"] += 1

    # Update coverage summary
    coverage["summary"]["by_status"] = stats
    coverage["summary"]["by_drawer"] = drawer_stats
    coverage["summary"]["by_source"] = source_stats
    coverage["summary"]["total_coverage_cells"] = sum(stats.values())

    return coverage


def scan_all_bundles(coverage: dict, concepts: dict) -> dict:
    """Scan all bundles and update coverage matrix."""

    index_entries = load_index()

    # Process each bundle
    for entry in index_entries:
        bundle_id = entry.get("bundle_id")
        if not bundle_id:
            continue

        # Determine source
        source = determine_source_from_bundle(bundle_id, index_entries)
        if not source:
            # Try to infer from bundle metadata
            source_tier = entry.get("source_tier", "").upper()
            if "ICT" in source_tier or "2022" in source_tier:
                source = "ICT_2022"
            elif "BLESSED" in source_tier or "LATERAL" in source_tier:
                source = "BLESSED_TRADER"
            elif "OLYA" in source_tier:
                source = "OLYA_NOTES"
            else:
                continue

        # Load claims
        claims = load_bundle_claims(bundle_id)
        if not claims:
            continue

        print(f"Processing {bundle_id} ({source}): {len(claims)} claims")

        # Update coverage
        coverage = update_coverage_for_bundle(coverage, concepts, bundle_id, source, claims)

    # Update summary
    coverage = update_summary(coverage)
    coverage["last_updated"] = datetime.now(timezone.utc).isoformat()

    return coverage


def generate_report(coverage: dict) -> str:
    """Generate human-readable coverage report."""

    lines = [
        "# Coverage Matrix Report",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Summary",
        "",
    ]

    summary = coverage.get("summary", {})
    by_status = summary.get("by_status", {})

    total = sum(by_status.values())
    found = by_status.get("FOUND", 0)
    pending = by_status.get("PENDING", 0)
    absent = by_status.get("ABSENT", 0)
    partial = by_status.get("PARTIAL", 0)

    lines.append(f"Total coverage cells: {total}")
    lines.append(f"- FOUND: {found} ({100*found/total:.1f}%)" if total else "- FOUND: 0")
    lines.append(f"- PENDING: {pending}")
    lines.append(f"- ABSENT: {absent}")
    lines.append(f"- PARTIAL: {partial}")
    lines.append("")

    # By source
    lines.append("## Coverage by Source")
    lines.append("")
    by_source = summary.get("by_source", {})
    for source, stats in by_source.items():
        found = stats.get("found", 0)
        total = stats.get("total", 0)
        pct = 100 * found / total if total else 0
        lines.append(f"- {source}: {found}/{total} ({pct:.1f}%)")
    lines.append("")

    # By drawer
    lines.append("## Coverage by Drawer")
    lines.append("")
    by_drawer = summary.get("by_drawer", {})
    for drawer, stats in by_drawer.items():
        found = stats.get("found", 0)
        total = stats.get("total", 0)
        pct = 100 * found / total if total else 0
        lines.append(f"- {drawer}: {found}/{total} ({pct:.1f}%)")
    lines.append("")

    # Detailed matrix (top-level view)
    lines.append("## Concept Status Matrix")
    lines.append("")
    lines.append("```")
    lines.append(f"{'CONCEPT':<45} | {'ICT_2022':<10} | {'BLESSED':<10} | {'OLYA':<10}")
    lines.append("-" * 85)

    for concept_id, concept in coverage.get("coverage", {}).items():
        name = concept.get("name", concept_id)[:42]

        statuses = []
        for source in ["ICT_2022", "BLESSED_TRADER", "OLYA_NOTES"]:
            entry = concept.get("sources", {}).get(source, {})
            status = entry.get("status", "?")

            # Symbol conversion
            symbol_map = {
                "FOUND": "FOUND",
                "ABSENT": "---",
                "PARTIAL": "PART",
                "PENDING": "...",
                "NOT_APPLICABLE": "N/A",
            }
            statuses.append(symbol_map.get(status, "?")[:10])

        lines.append(f"{name:<45} | {statuses[0]:<10} | {statuses[1]:<10} | {statuses[2]:<10}")

    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Update coverage matrix")
    parser.add_argument("--source", help="Source to update (ICT_2022, BLESSED_TRADER, OLYA_NOTES)")
    parser.add_argument("--bundle", help="Bundle ID to process")
    parser.add_argument("--scan-all", action="store_true", help="Scan all bundles")
    parser.add_argument("--report", action="store_true", help="Generate coverage report")
    parser.add_argument("--output", help="Output path for report")

    args = parser.parse_args()

    # Load data
    concepts = load_taxonomy()
    coverage = load_coverage_matrix()

    print(f"Loaded {len(concepts)} concepts from taxonomy")

    if args.scan_all:
        print("Scanning all bundles...")
        coverage = scan_all_bundles(coverage, concepts)
        save_yaml(coverage, COVERAGE_PATH)
        print(f"Updated coverage matrix: {COVERAGE_PATH}")

    elif args.bundle and args.source:
        print(f"Processing bundle {args.bundle} for source {args.source}")
        claims = load_bundle_claims(args.bundle)
        if claims:
            coverage = update_coverage_for_bundle(coverage, concepts, args.bundle, args.source, claims)
            coverage = update_summary(coverage)
            coverage["last_updated"] = datetime.now(timezone.utc).isoformat()
            save_yaml(coverage, COVERAGE_PATH)
            print(f"Processed {len(claims)} claims")
        else:
            print("No claims found in bundle")

    if args.report:
        report = generate_report(coverage)

        if args.output:
            output_path = Path(args.output)
            with open(output_path, "w") as f:
                f.write(report)
            print(f"Report saved to: {output_path}")
        else:
            print(report)


if __name__ == "__main__":
    main()
