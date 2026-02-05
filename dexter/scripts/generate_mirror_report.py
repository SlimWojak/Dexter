#!/usr/bin/env python3
"""Mirror Report Generator — Olya review artifact.

Synthesizes CLAIM_BEADs from all tiers into a readable report
for CSO (Olya) validation. Uses Claude Opus for synthesis.

Output: bundles/MIRROR_REPORT.md

Usage:
    python scripts/generate_mirror_report.py
    python scripts/generate_mirror_report.py --output /path/to/report.md
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [mirror] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("dexter.mirror_report")

BUNDLES_DIR = _PROJECT_ROOT / "bundles"

# Drawer name translations for human-readable output
DRAWER_NAMES = {
    1: "Higher Timeframe Direction",
    2: "Market Structure",
    3: "Premium & Discount Zones",
    4: "Entry Patterns",
    5: "Confirmation Signals",
}

# Tier display names
TIER_NAMES = {
    "OLYA_PRIMARY": "Your Notes",
    "ICT_LEARNING": "ICT 2022 Mentorship",
    "CANON": "ICT 2022 Mentorship",
    "LATERAL": "Blessed Trader",
}

SYNTHESIS_PROMPT = '''You are synthesising extracted trading logic claims for expert review.

The expert (Olya) is a practicing trader. She will read this report to recognise her own methodology — or correct where extraction missed.

Write in clear, readable prose. She is reviewing over coffee, not debugging JSONL.

Structure the report as follows:

## Section 1: What We Found In Your Notes

Synthesise OLYA_PRIMARY claims. Group by drawer (Higher Timeframe Direction, Market Structure, Premium & Discount Zones, Entry Patterns, Confirmation Signals).

Use her terminology naturally. Show the patterns that repeat across multiple notes. Highlight where her logic is most precise.

## Section 2: What ICT 2022 Mentorship Teaches

Synthesise ICT_LEARNING/CANON claims. Group by drawer. Focus on the core methodology as extracted from the playlist.

## Section 3: What Blessed Trader Emphasises

Synthesise LATERAL claims. Brief — only {lateral_count} signatures. Note that most content was visual examples.

## Section 4: Where Your Practice Differs From The Teaching

THIS IS THE KEY SECTION. Present as a table:

| Topic | ICT Teaching | Your Applied Logic | Delta |
|-------|--------------|-------------------|-------|

Identify where Olya's notes show different emphasis, additional conditions, stricter filters, or different execution logic compared to ICT source material. These deltas ARE her edge.

## Section 5: Patterns That Repeat Across Your Notes

Claims that appear in 3+ of her notes in different contexts. These are her core beliefs — the logic she returns to consistently.

## Section 6: Open Questions

Claims that seem incomplete, contradictory across notes, or where the extraction may have missed nuance. Flag for her review.

For each claim referenced, include the source file in parentheses so she can trace back to her original note if needed.

---

INPUT DATA:

OLYA_PRIMARY CLAIMS ({olya_count} total):
{olya_claims}

ICT_LEARNING/CANON CLAIMS ({ict_count} total):
{ict_claims}

LATERAL CLAIMS ({lateral_count} total):
{lateral_claims}

---

Generate the Mirror Report now. Be thorough in Section 4 (deltas) — this is the highest value section.
'''


def load_all_claims() -> Dict[str, List[Dict]]:
    """Load all CLAIM_BEADs from bundles directory, grouped by tier."""
    claims_by_tier = defaultdict(list)

    claim_files = list(BUNDLES_DIR.glob("*_claims.jsonl"))
    logger.info("Found %d CLAIM_BEAD files", len(claim_files))

    for claim_file in claim_files:
        try:
            with open(claim_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    claim = json.loads(line)
                    tier = claim.get("extraction_meta", {}).get("source_tier")

                    # Normalize tier names
                    if tier == "CANON":
                        tier = "ICT_LEARNING"
                    # Handle missing tiers - older soak claims are from ICT videos
                    elif tier is None or tier == "UNKNOWN" or tier == "":
                        # Check source_file to infer tier
                        source_file = claim.get("signature", {}).get("source_file") or ""
                        source_file_upper = source_file.upper() if source_file else ""
                        if "OLYA" in source_file_upper:
                            tier = "OLYA_PRIMARY"
                        elif "Lesson" in source_file or "Blessed" in source_file_upper:
                            tier = "LATERAL"
                        else:
                            # Default older claims to ICT_LEARNING (overnight soak)
                            tier = "ICT_LEARNING"

                    claims_by_tier[tier].append(claim)
        except Exception as e:
            logger.warning("Error reading %s: %s", claim_file.name, e)

    # Log tier counts
    for tier, claims in claims_by_tier.items():
        logger.info("Tier %s: %d claims", tier, len(claims))

    return dict(claims_by_tier)


def format_claims_for_prompt(claims: List[Dict], max_claims: int = 200) -> str:
    """Format claims for inclusion in synthesis prompt."""
    if not claims:
        return "(no claims)"

    # Sort by drawer for organization
    claims_by_drawer = defaultdict(list)
    for claim in claims:
        drawer = claim.get("signature", {}).get("drawer") or 0
        claims_by_drawer[drawer].append(claim)

    lines = []
    total_included = 0

    for drawer in sorted(claims_by_drawer.keys()):
        drawer_name = DRAWER_NAMES.get(drawer, f"Drawer {drawer}")
        drawer_claims = claims_by_drawer[drawer]

        lines.append(f"\n### {drawer_name} ({len(drawer_claims)} claims)")

        for claim in drawer_claims:
            if total_included >= max_claims:
                lines.append(f"\n... and {len(claims) - total_included} more claims truncated")
                break

            sig = claim.get("signature", {})
            source_file = sig.get("source_file", "unknown")
            condition = sig.get("condition", "")
            action = sig.get("action", "")

            lines.append(f"- IF {condition} → THEN {action} ({source_file})")
            total_included += 1

        if total_included >= max_claims:
            break

    return "\n".join(lines)


def call_opus_synthesis(prompt: str) -> str:
    """Call Claude Opus for report synthesis."""
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in environment")

    client = anthropic.Anthropic(api_key=api_key)

    logger.info("Calling Claude Opus for synthesis...")

    response = client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=8000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # Extract text from response
    content = response.content[0].text if response.content else ""

    # Log cost
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    # Opus pricing: $15/1M input, $75/1M output
    cost = (input_tokens * 15 / 1_000_000) + (output_tokens * 75 / 1_000_000)
    logger.info("[OPUS COST] in=%d out=%d cost=$%.4f", input_tokens, output_tokens, cost)

    return content


def generate_report_header() -> str:
    """Generate report header with metadata."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""# Mirror Report — Trading Logic Synthesis

**Generated:** {now}
**Purpose:** CSO (Olya) review of extracted methodology
**Source:** Dexter Evidence Refinery

---

*This report synthesizes IF-THEN trading logic extracted from your notes, ICT 2022 Mentorship, and supplementary materials. Review for accuracy — your corrections will improve the extraction.*

---

"""


def generate_mirror_report(output_path: Optional[Path] = None) -> str:
    """Generate the full Mirror Report."""

    # Load all claims
    claims_by_tier = load_all_claims()

    olya_claims = claims_by_tier.get("OLYA_PRIMARY", [])
    ict_claims = claims_by_tier.get("ICT_LEARNING", [])
    lateral_claims = claims_by_tier.get("LATERAL", [])

    total_claims = len(olya_claims) + len(ict_claims) + len(lateral_claims)
    logger.info("Total claims to synthesize: %d", total_claims)

    if total_claims == 0:
        logger.warning("No claims found to synthesize")
        return "# Mirror Report\n\nNo claims found for synthesis."

    # Format claims for prompt
    olya_formatted = format_claims_for_prompt(olya_claims, max_claims=150)
    ict_formatted = format_claims_for_prompt(ict_claims, max_claims=150)
    lateral_formatted = format_claims_for_prompt(lateral_claims, max_claims=50)

    # Build synthesis prompt
    prompt = SYNTHESIS_PROMPT.format(
        olya_count=len(olya_claims),
        ict_count=len(ict_claims),
        lateral_count=len(lateral_claims),
        olya_claims=olya_formatted,
        ict_claims=ict_formatted,
        lateral_claims=lateral_formatted,
    )

    # Call Opus for synthesis
    synthesis = call_opus_synthesis(prompt)

    # Combine header and synthesis
    report = generate_report_header() + synthesis

    # Add footer
    report += f"""

---

## Report Metadata

| Tier | Claims Included |
|------|-----------------|
| Your Notes (OLYA_PRIMARY) | {len(olya_claims)} |
| ICT 2022 Mentorship | {len(ict_claims)} |
| Blessed Trader (LATERAL) | {len(lateral_claims)} |
| **Total** | **{total_claims}** |

*Generated by Dexter Mirror Report Generator v1.0*
"""

    # Write to file
    if output_path is None:
        output_path = BUNDLES_DIR / "MIRROR_REPORT.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(report)

    logger.info("Mirror Report written to: %s", output_path)

    return report


def main():
    parser = argparse.ArgumentParser(description="Generate Mirror Report for Olya review")
    parser.add_argument("--output", "-o", type=str, help="Output path (default: bundles/MIRROR_REPORT.md)")
    parser.add_argument("--dry-run", action="store_true", help="Show claim counts without generating report")
    args = parser.parse_args()

    if args.dry_run:
        claims_by_tier = load_all_claims()
        print("\nClaim counts by tier:")
        for tier, claims in claims_by_tier.items():
            print(f"  {tier}: {len(claims)}")
        print(f"\nTotal: {sum(len(c) for c in claims_by_tier.values())}")
        return

    output_path = Path(args.output) if args.output else None

    try:
        report = generate_mirror_report(output_path)
        print(f"\nMirror Report generated successfully!")
        print(f"Output: {output_path or BUNDLES_DIR / 'MIRROR_REPORT.md'}")
    except Exception as e:
        logger.exception("Failed to generate Mirror Report: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
