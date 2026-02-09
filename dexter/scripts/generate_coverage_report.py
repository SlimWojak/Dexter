#!/usr/bin/env python3
"""
Coverage Report Generator for Dexter Taxonomy System

Generates a human-readable coverage report (bundles/COVERAGE_REPORT.md) showing:
1. Overall coverage statistics
2. Per-drawer coverage breakdown
3. Per-source coverage breakdown
4. Detailed concept matrix with evidence status
5. Gaps and recommendations

Usage:
    python scripts/generate_coverage_report.py
    python scripts/generate_coverage_report.py --output /custom/path/report.md
    python scripts/generate_coverage_report.py --format markdown|html|json

Author: Dexter COO
Version: 1.0
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml


# Paths
PROJECT_ROOT = Path(__file__).parent.parent
TAXONOMY_PATH = PROJECT_ROOT / "data" / "taxonomy" / "reference_taxonomy.yaml"
COVERAGE_PATH = PROJECT_ROOT / "data" / "taxonomy" / "coverage_matrix.yaml"
DEFAULT_OUTPUT = PROJECT_ROOT / "bundles" / "COVERAGE_REPORT.md"


def load_yaml(path: Path) -> dict:
    """Load YAML file."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def status_symbol(status: str) -> str:
    """Convert status to display symbol."""
    symbols = {
        "FOUND": "Y",
        "PARTIAL": "~",
        "ABSENT": "-",
        "PENDING": ".",
        "NOT_APPLICABLE": "N/A",
    }
    return symbols.get(status, "?")


def status_emoji(status: str) -> str:
    """Convert status to emoji for markdown."""
    emojis = {
        "FOUND": "FOUND",
        "PARTIAL": "PART",
        "ABSENT": "---",
        "PENDING": "...",
        "NOT_APPLICABLE": "N/A",
    }
    return emojis.get(status, "?")


def generate_markdown_report(coverage: dict, taxonomy: dict) -> str:
    """Generate markdown coverage report."""

    lines = []
    now = datetime.now(timezone.utc).isoformat()

    # Header
    lines.extend([
        "# Dexter Coverage Report",
        "",
        f"*Generated: {now}*",
        "",
        "> \"Show me you looked, not just what you found.\" - Olya",
        "",
        "---",
        "",
    ])

    # Executive Summary
    summary = coverage.get("summary", {})
    by_status = summary.get("by_status", {})

    total = sum(by_status.values())
    found = by_status.get("FOUND", 0)
    partial = by_status.get("PARTIAL", 0)
    absent = by_status.get("ABSENT", 0)
    pending = by_status.get("PENDING", 0)

    found_pct = (100 * found / total) if total else 0
    coverage_pct = (100 * (found + partial) / total) if total else 0

    lines.extend([
        "## Executive Summary",
        "",
        f"**Total Concepts:** {coverage.get('summary', {}).get('total_concepts', 66)}",
        f"**Total Coverage Cells:** {total} (concepts x sources)",
        "",
        "### Coverage Status",
        "",
        f"| Status | Count | Percentage |",
        f"|--------|-------|------------|",
        f"| FOUND | {found} | {found_pct:.1f}% |",
        f"| PARTIAL | {partial} | {100*partial/total:.1f}% |" if total else "| PARTIAL | 0 | 0% |",
        f"| ABSENT | {absent} | {100*absent/total:.1f}% |" if total else "| ABSENT | 0 | 0% |",
        f"| PENDING | {pending} | {100*pending/total:.1f}% |" if total else "| PENDING | 0 | 0% |",
        "",
        f"**Effective Coverage:** {coverage_pct:.1f}% (FOUND + PARTIAL)",
        "",
        "---",
        "",
    ])

    # Coverage by Source
    by_source = summary.get("by_source", {})
    lines.extend([
        "## Coverage by Source",
        "",
        "| Source | FOUND | Total | Coverage |",
        "|--------|-------|-------|----------|",
    ])

    for source, stats in by_source.items():
        found = stats.get("found", 0)
        total = stats.get("total", 0)
        pct = (100 * found / total) if total else 0
        lines.append(f"| {source} | {found} | {total} | {pct:.1f}% |")

    lines.extend(["", "---", ""])

    # Coverage by Drawer
    by_drawer = summary.get("by_drawer", {})
    drawer_names = {
        "drawer_1": "HTF Bias & Liquidity",
        "drawer_2": "Time & Session",
        "drawer_3": "Structure & Displacement",
        "drawer_4": "Execution",
        "drawer_5": "Protection & Risk",
        "olya": "Olya Extensions",
    }

    lines.extend([
        "## Coverage by Drawer",
        "",
        "| Drawer | Name | FOUND | Total | Coverage |",
        "|--------|------|-------|-------|----------|",
    ])

    for drawer, stats in by_drawer.items():
        found = stats.get("found", 0)
        total = stats.get("total", 0)
        pct = (100 * found / total) if total else 0
        name = drawer_names.get(drawer, drawer)
        lines.append(f"| {drawer} | {name} | {found} | {total} | {pct:.1f}% |")

    lines.extend(["", "---", ""])

    # Detailed Coverage Matrix
    lines.extend([
        "## Detailed Coverage Matrix",
        "",
        "Legend: FOUND = extracted with evidence, PART = mentioned but incomplete, --- = not found, ... = not yet checked",
        "",
    ])

    # Group by drawer
    drawer_concepts = {}
    for concept_id, concept in coverage.get("coverage", {}).items():
        drawer = concept.get("drawer", 0)
        if drawer not in drawer_concepts:
            drawer_concepts[drawer] = []
        drawer_concepts[drawer].append((concept_id, concept))

    for drawer in sorted(drawer_concepts.keys(), key=lambda x: str(x)):
        drawer_name = drawer_names.get(f"drawer_{drawer}", f"Drawer {drawer}")
        if drawer == "OLYA":
            drawer_name = "Olya Extensions"

        lines.extend([
            f"### {drawer_name}",
            "",
            "| Concept | ICT 2022 | Blessed | Olya Notes |",
            "|---------|----------|---------|------------|",
        ])

        for concept_id, concept in drawer_concepts[drawer]:
            name = concept.get("name", concept_id)[:35]

            sources = concept.get("sources", {})
            ict = status_emoji(sources.get("ICT_2022", {}).get("status", "?"))
            blessed = status_emoji(sources.get("BLESSED_TRADER", {}).get("status", "?"))
            olya = status_emoji(sources.get("OLYA_NOTES", {}).get("status", "?"))

            lines.append(f"| {name} | {ict} | {blessed} | {olya} |")

        lines.extend(["", ""])

    lines.append("---")
    lines.append("")

    # Gaps Analysis
    lines.extend([
        "## Coverage Gaps Analysis",
        "",
        "### Concepts with No Evidence (All Sources ABSENT/PENDING)",
        "",
    ])

    no_evidence = []
    for concept_id, concept in coverage.get("coverage", {}).items():
        sources = concept.get("sources", {})
        all_absent = all(
            sources.get(s, {}).get("status") in ["ABSENT", "PENDING", None]
            for s in ["ICT_2022", "BLESSED_TRADER", "OLYA_NOTES"]
        )
        if all_absent:
            no_evidence.append((concept_id, concept.get("name", "")))

    if no_evidence:
        for cid, name in no_evidence:
            lines.append(f"- **{cid}**: {name}")
    else:
        lines.append("*No gaps found - all concepts have at least one source with evidence.*")

    lines.extend(["", ""])

    # Partial Evidence
    lines.extend([
        "### Concepts with Partial Evidence Only",
        "",
    ])

    partial_only = []
    for concept_id, concept in coverage.get("coverage", {}).items():
        sources = concept.get("sources", {})
        statuses = [sources.get(s, {}).get("status") for s in ["ICT_2022", "BLESSED_TRADER", "OLYA_NOTES"]]
        if "PARTIAL" in statuses and "FOUND" not in statuses:
            partial_only.append((concept_id, concept.get("name", "")))

    if partial_only:
        for cid, name in partial_only:
            lines.append(f"- **{cid}**: {name}")
    else:
        lines.append("*No concepts with only partial evidence.*")

    lines.extend(["", "---", ""])

    # Evidence Grade Distribution
    lines.extend([
        "## Evidence Grade Distribution",
        "",
        "Based on reference taxonomy evidence grades:",
        "",
    ])

    # Count grades from taxonomy
    grade_counts = {}
    taxonomy_data = taxonomy

    for drawer_key in ["drawer_1_htf_bias", "drawer_2_time_session", "drawer_3_structure",
                       "drawer_4_execution", "drawer_5_protection", "olya_extensions"]:
        if drawer_key in taxonomy_data:
            for concept in taxonomy_data[drawer_key].get("concepts", []):
                grade = concept.get("evidence_grade", "UNKNOWN")
                grade_counts[grade] = grade_counts.get(grade, 0) + 1

    lines.append("| Grade | Count | Description |")
    lines.append("|-------|-------|-------------|")
    grade_descriptions = {
        "STRONG_EVIDENCE": "Academic/peer-reviewed backing",
        "MODERATE_EVIDENCE": "Practitioner-backed, needs testing",
        "PRACTITIONER_LORE": "Widely taught, limited empirical backing",
        "UNIQUE": "Olya-specific codification",
    }
    for grade, count in sorted(grade_counts.items()):
        desc = grade_descriptions.get(grade, "")
        lines.append(f"| {grade} | {count} | {desc} |")

    lines.extend(["", "---", ""])

    # Recommendations
    lines.extend([
        "## Recommendations",
        "",
    ])

    recommendations = []

    # Check for low coverage sources
    for source, stats in by_source.items():
        found = stats.get("found", 0)
        total = stats.get("total", 0)
        pct = (100 * found / total) if total else 0
        if pct < 20:
            recommendations.append(f"- **{source}**: Only {pct:.1f}% coverage. Run taxonomy-targeted extraction on remaining documents.")

    # Check for pending items
    if pending > total * 0.5:
        recommendations.append(f"- **High Pending Rate**: {100*pending/total:.0f}% of cells still pending. Run `--scan-all` to process existing bundles.")

    # Check for no-evidence concepts
    if len(no_evidence) > 10:
        recommendations.append(f"- **Coverage Gaps**: {len(no_evidence)} concepts have no evidence from any source. Review source selection or extraction quality.")

    if recommendations:
        for rec in recommendations:
            lines.append(rec)
    else:
        lines.append("*Coverage is healthy. No immediate actions required.*")

    lines.extend(["", "---", ""])

    # Footer
    lines.extend([
        "## Report Metadata",
        "",
        f"- **Generated:** {now}",
        f"- **Taxonomy Version:** {taxonomy.get('version', 'unknown')}",
        f"- **Coverage Matrix Version:** {coverage.get('version', 'unknown')}",
        f"- **Last Matrix Update:** {coverage.get('last_updated', 'never')}",
        "",
        "---",
        "",
        "*Generated by Dexter Coverage Report Generator*",
    ])

    return "\n".join(lines)


def generate_json_report(coverage: dict, taxonomy: dict) -> str:
    """Generate JSON coverage report."""
    report = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "summary": coverage.get("summary", {}),
        "coverage": coverage.get("coverage", {}),
        "taxonomy_version": taxonomy.get("version"),
    }
    return json.dumps(report, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Generate coverage report")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output path")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")

    args = parser.parse_args()

    # Load data
    coverage = load_yaml(COVERAGE_PATH)
    taxonomy = load_yaml(TAXONOMY_PATH)

    print(f"Loaded coverage matrix: {COVERAGE_PATH}")
    print(f"Loaded taxonomy: {TAXONOMY_PATH}")

    # Generate report
    if args.format == "markdown":
        report = generate_markdown_report(coverage, taxonomy)
    elif args.format == "json":
        report = generate_json_report(coverage, taxonomy)
    else:
        report = generate_markdown_report(coverage, taxonomy)

    # Save report
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        f.write(report)

    print(f"Report saved to: {args.output}")

    # Print summary
    summary = coverage.get("summary", {})
    by_status = summary.get("by_status", {})
    total = sum(by_status.values())
    found = by_status.get("FOUND", 0)
    pending = by_status.get("PENDING", 0)

    print(f"\n=== Quick Summary ===")
    print(f"FOUND: {found}/{total} ({100*found/total:.1f}%)" if total else "FOUND: 0")
    print(f"PENDING: {pending}/{total}" if total else "PENDING: 0")


if __name__ == "__main__":
    main()
