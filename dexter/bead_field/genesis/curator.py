"""Genesis curation — map extraction-phase CLAIMs against v0.3 taxonomy.

Categorizes every CLAIM into:
  GENESIS_INCLUDE: Maps to validated methodology concepts
  GENESIS_EXCLUDE_CONTRADICTION: Contradicted by v0.3 corrections
  GENESIS_EXCLUDE_ARTIFACT: Test/pipeline artifacts, not methodology

HALT after curation report generated — G reviews before proceeding.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


REMOVED_CONCEPTS_V03 = {
    "CBDR",
    "cbdr",
    "Central Bank Dealers Range",
    "SMT",
    "smt",
    "Smart Money Technique divergence",
    "time stop",
    "time-stop",
    "structure break exit",
    "structure-break exit",
}

CONTRADICTION_PATTERNS = [
    (re.compile(r"\bcbdr\b", re.IGNORECASE), "CBDR removed in v0.3 correction #2"),
    (re.compile(r"\bsmt\b", re.IGNORECASE), "SMT removed in v0.3 correction #7"),
    (re.compile(r"\btime.?stop\b", re.IGNORECASE), "Time stop removed in v0.3 correction #10"),
    (re.compile(r"\bstructure.?break.?exit\b", re.IGNORECASE), "Structure break exit removed in v0.3 correction #11"),
]

ARTIFACT_INDICATORS = [
    "(MOCK)",
    "mock://",
    "test_",
    "pipeline_test",
]


class CurationCategory:
    INCLUDE = "GENESIS_INCLUDE"
    EXCLUDE_CONTRADICTION = "GENESIS_EXCLUDE_CONTRADICTION"
    EXCLUDE_ARTIFACT = "GENESIS_EXCLUDE_ARTIFACT"


class CuratedClaim:
    def __init__(self, claim: dict, category: str, reason: str = ""):
        self.claim = claim
        self.category = category
        self.reason = reason

    @property
    def signature_id(self) -> str:
        return self.claim.get("signature", {}).get("id", "UNKNOWN")

    @property
    def condition(self) -> str:
        return self.claim.get("signature", {}).get("condition", "")

    @property
    def action(self) -> str:
        return self.claim.get("signature", {}).get("action", "")

    @property
    def source(self) -> str:
        return self.claim.get("source_video", "UNKNOWN")

    @property
    def bundle_id(self) -> str:
        return self.claim.get("extraction_meta", {}).get("bundle_id", "UNKNOWN")


def load_claims(bundles_dir: Path) -> list[dict]:
    """Load all CLAIMs from JSONL files in bundles directory."""
    claims = []
    for jsonl_path in sorted(bundles_dir.glob("*_claims.jsonl")):
        with open(jsonl_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    claims.append(json.loads(line))
    return claims


def load_taxonomy(taxonomy_path: Path) -> dict:
    """Load the v0.3 methodology taxonomy."""
    with open(taxonomy_path) as f:
        return yaml.safe_load(f)


def _is_artifact(claim: dict) -> str | None:
    """Check if a CLAIM is a test/pipeline artifact."""
    source = claim.get("source_video", "")
    source_url = claim.get("source_url", "")
    for indicator in ARTIFACT_INDICATORS:
        if indicator in source or indicator in source_url:
            return f"Artifact: source contains '{indicator}'"
    return None


def _is_contradiction(claim: dict) -> str | None:
    """Check if a CLAIM references concepts removed in v0.3."""
    sig = claim.get("signature", {})
    condition = sig.get("condition", "")
    action = sig.get("action", "")
    text = f"{condition} {action}"

    for pattern, reason in CONTRADICTION_PATTERNS:
        if pattern.search(text):
            return reason
    return None


def curate(claims: list[dict]) -> list[CuratedClaim]:
    """Categorize each CLAIM for Genesis inclusion/exclusion."""
    results = []
    for claim in claims:
        artifact_reason = _is_artifact(claim)
        if artifact_reason:
            results.append(CuratedClaim(claim, CurationCategory.EXCLUDE_ARTIFACT, artifact_reason))
            continue

        contradiction_reason = _is_contradiction(claim)
        if contradiction_reason:
            results.append(CuratedClaim(claim, CurationCategory.EXCLUDE_CONTRADICTION, contradiction_reason))
            continue

        results.append(CuratedClaim(claim, CurationCategory.INCLUDE))

    return results


def generate_curation_report(curated: list[CuratedClaim], output_path: Path) -> dict:
    """Generate CURATION_REPORT.md and return summary stats."""
    included = [c for c in curated if c.category == CurationCategory.INCLUDE]
    contradictions = [c for c in curated if c.category == CurationCategory.EXCLUDE_CONTRADICTION]
    artifacts = [c for c in curated if c.category == CurationCategory.EXCLUDE_ARTIFACT]

    summary = {
        "total": len(curated),
        "genesis_include": len(included),
        "exclude_contradiction": len(contradictions),
        "exclude_artifact": len(artifacts),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    lines = [
        "# GENESIS CURATION REPORT",
        "",
        "```yaml",
        f"date: {summary['timestamp']}",
        f"total_claims: {summary['total']}",
        f"genesis_include: {summary['genesis_include']}",
        f"exclude_contradiction: {summary['exclude_contradiction']}",
        f"exclude_artifact: {summary['exclude_artifact']}",
        "taxonomy: SYNTHETIC_OLYA_METHOD_v0.3",
        "status: AWAITING_G_REVIEW",
        "```",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"- **{summary['genesis_include']}** CLAIMs included in Genesis Snapshot",
        f"- **{summary['exclude_contradiction']}** excluded (contradicted by v0.3 corrections)",
        f"- **{summary['exclude_artifact']}** excluded (test/pipeline artifacts)",
        "",
        "---",
        "",
    ]

    if contradictions:
        lines.append("## Excluded: Contradictions (v0.3 Corrections)")
        lines.append("")
        lines.append("| # | Signature | Condition | Reason | Source |")
        lines.append("|---|-----------|-----------|--------|--------|")
        for i, c in enumerate(contradictions, 1):
            cond = c.condition[:60] + "..." if len(c.condition) > 60 else c.condition
            lines.append(f"| {i} | {c.signature_id} | {cond} | {c.reason} | {c.bundle_id} |")
        lines.append("")
        lines.append("---")
        lines.append("")

    if artifacts:
        lines.append("## Excluded: Artifacts")
        lines.append("")
        lines.append(f"**{len(artifacts)}** CLAIMs from mock/test sources excluded from permanent record.")
        lines.append("")
        sources = set()
        for c in artifacts:
            sources.add(c.source)
        lines.append("Artifact sources:")
        for src in sorted(sources):
            count = sum(1 for c in artifacts if c.source == src)
            lines.append(f"- `{src}` ({count} CLAIMs)")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Genesis Include: Source Distribution")
    lines.append("")
    source_counts: dict[str, int] = {}
    for c in included:
        src = c.source or "UNKNOWN"
        source_counts[src] = source_counts.get(src, 0) + 1
    lines.append("| Source | CLAIMs |")
    lines.append("|--------|--------|")
    for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        display = src[:70] + "..." if len(src) > 70 else src
        lines.append(f"| {display} | {count} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**HALT: G must review and approve before Genesis Snapshot proceeds.**")
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines))

    return summary
