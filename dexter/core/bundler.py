"""Template-locked Evidence Bundler — zero narrative, facts only.

Reads bundles/BUNDLE_TEMPLATE.md, fills slots from validated signatures
and auditor verdicts. Enforces INV-NO-NARRATIVE via bleed checker.
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("dexter.bundler")

BUNDLES_DIR = Path(__file__).resolve().parent.parent / "bundles"
TEMPLATE_PATH = BUNDLES_DIR / "BUNDLE_TEMPLATE.md"

# INV-NO-NARRATIVE enforcement
NARRATIVE_VIOLATIONS = [
    "I think",
    "this suggests",
    "likely",
    "probably",
    "seems to",
    "appears to",
    "in my opinion",
    "I believe",
    "it looks like",
    "might be",
    "could mean",
    "I feel",
]


def check_narrative_bleed(text: str, *, exclude_quotes: bool = False) -> List[str]:
    """Check for narrative violations. Returns list of found violations.

    Args:
        text: full bundle text to check
        exclude_quotes: if True, strip table rows (verbatim transcript quotes)
            before checking. Use for bundles with real transcript content.
    """
    check_text = text
    if exclude_quotes:
        # Remove markdown table rows (contain verbatim transcript quotes)
        lines = text.split("\n")
        check_text = "\n".join(
            line for line in lines
            if not line.strip().startswith("|") or line.strip().startswith("|-")
        )
    check_lower = check_text.lower()
    found = []
    for phrase in NARRATIVE_VIOLATIONS:
        if phrase.lower() in check_lower:
            found.append(phrase)
    return found


class BundleError(Exception):
    """Raised when bundle generation fails validation."""
    pass


def _format_signatures_table(signatures: List[Dict]) -> str:
    """Format signatures as markdown table rows."""
    rows = []
    for sig in signatures:
        sid = sig.get("id", "?")
        condition = sig.get("condition", "")
        action = sig.get("action", "")
        ts = sig.get("source_timestamp", "")
        rows.append(f"| {sid} | {condition} | {action} | {ts} |")
    return "\n".join(rows) if rows else "| — | No validated signatures | — | — |"


def _format_delta_table(deltas: List[Dict]) -> str:
    """Format delta-to-canon as markdown table rows."""
    rows = []
    for d in deltas:
        param = d.get("parameter", "")
        current = d.get("current_value", "—")
        new_val = d.get("bundle_value", "—")
        change = d.get("change_type", "NEW")
        rows.append(f"| {param} | {current} | {new_val} | {change} |")
    return "\n".join(rows) if rows else "| — | — | — | — |"


def _format_gates_table(gates: Dict) -> str:
    """Format gates as markdown table rows."""
    rows = []
    for gate_name, gate_data in gates.items():
        status = gate_data.get("status", "PENDING")
        notes = gate_data.get("notes", "")
        rows.append(f"| {gate_name.upper()} | {status} | {notes} |")
    return "\n".join(rows) if rows else "| — | PENDING | — |"


def generate_bundle(
    bundle_id: str,
    source_url: str,
    timestamp_range: str,
    validated_signatures: List[Dict],
    rejected_signatures: List[Dict],
    auditor_summary: Dict,
    *,
    deltas: Optional[List[Dict]] = None,
    gates: Optional[Dict] = None,
    logic_diff: str = "# No code generated yet",
    provenance: Optional[Dict] = None,
    negative_beads: Optional[List[str]] = None,
) -> str:
    """Generate a complete evidence bundle from template.

    Raises BundleError if narrative bleed detected.
    """
    now = datetime.now(timezone.utc).isoformat()
    deltas = deltas or []
    gates = gates or {"TEMPORAL": {"status": "PENDING"}, "STRUCTURAL": {"status": "PENDING"}, "RISK": {"status": "PENDING"}}
    provenance = provenance or {}
    negative_beads = negative_beads or []

    novel_count = sum(1 for d in deltas if d.get("change_type") == "NEW")

    auditor_model = auditor_summary.get("results", [{}])[0].get("auditor_model", "gemini-3-flash") if auditor_summary.get("results") else "gemini-3-flash"

    # Build rejection reasons list
    rejection_reasons = []
    for r in auditor_summary.get("results", []):
        if r.get("verdict") == "REJECT":
            rejection_reasons.append(f"- {r.get('signature_id', '?')}: {r.get('reason', '')}")
    rejection_str = "\n".join(rejection_reasons) if rejection_reasons else "- None"

    bundle = f"""# EVIDENCE BUNDLE: {bundle_id}
## Generated: {now}
## Source: {source_url} @ {timestamp_range}

### IF-THEN SIGNATURES
| ID | Condition (IF) | Action (THEN) | Source Timestamp |
|----|----------------|---------------|------------------|
{_format_signatures_table(validated_signatures)}

### DELTA TO CANON (v0.2)
| Parameter | Current Phoenix Value | This Bundle Value | Change Type |
|-----------|----------------------|-------------------|-------------|
{_format_delta_table(deltas)}

**Novelty Statement:** "This bundle introduces {novel_count} net-new parameters not present in Phoenix canon."

### AUDITOR VERDICT
- Signatures validated: {auditor_summary.get("passed", 0)}
- Signatures rejected: {auditor_summary.get("rejected", 0)}
- Rejection reasons:
{rejection_str}
- Falsification attempts: {MAX_ATTEMPTS}
- Statement: "{_auditor_statement(auditor_summary)}"

### AUDITOR BACKTEST REVIEW (v0.2)
- Data leakage check: PENDING
- Curve fitting check: PENDING
- Logic match check: PENDING
- Reviewer model: [{auditor_model}]
- Line citations: [pending Phase 4]

### GATES PASSED (Phoenix Format)
| Gate | Status | Notes |
|------|--------|-------|
{_format_gates_table(gates)}

### LOGIC DIFF (Developer Output)
```python
{logic_diff}
```

### PROVENANCE
- Transcript method: [{provenance.get("transcript_method", "pending")}]
- Theorist model: [{provenance.get("theorist_model", "pending")}]
- Auditor model: [{auditor_model}]
- Chronicler incorporated: [{provenance.get("chronicler", "N")}]
- Negative beads considered: [{", ".join(negative_beads) if negative_beads else "none"}]
"""

    # INV-NO-NARRATIVE enforcement (exclude table rows with verbatim quotes)
    violations = check_narrative_bleed(bundle, exclude_quotes=True)
    if violations:
        logger.warning("NARRATIVE BLEED in bundle %s: %s", bundle_id, violations)
        raise BundleError(
            f"INV-NO-NARRATIVE violation in bundle {bundle_id}: {violations}"
        )

    return bundle


MAX_ATTEMPTS = 3


def _auditor_statement(summary: Dict) -> str:
    rejected = summary.get("rejected", 0)
    if rejected > 0:
        return f"{rejected} signatures rejected"
    return f"No falsification found after {MAX_ATTEMPTS} attempts"


def save_bundle(bundle_id: str, content: str) -> Path:
    """Save bundle to bundles/ directory. Returns file path."""
    BUNDLES_DIR.mkdir(parents=True, exist_ok=True)
    path = BUNDLES_DIR / f"{bundle_id}.md"
    with open(path, "w") as f:
        f.write(content)
    logger.info("Bundle saved: %s", path)
    return path
