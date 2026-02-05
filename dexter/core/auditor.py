"""Adversarial Auditor — Bounty Hunter pattern.

Evaluates if-then signatures for falsifiability, provenance, logical
consistency, and canon conflicts. Rejects aggressively. Phase 2 runs
locally without LLM; Phase 3 will route through OpenRouter to gemini-3-flash.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger("dexter.auditor")

ROLES_DIR = Path(__file__).resolve().parent.parent / "roles"
THEORY_PATH = Path(__file__).resolve().parent.parent / "memory" / "THEORY.md"

MAX_ATTEMPTS = 3


def _load_manifest() -> Dict:
    path = ROLES_DIR / "auditor.yaml"
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _load_theory() -> str:
    if THEORY_PATH.exists():
        with open(THEORY_PATH) as f:
            return f.read()
    return ""


# ---------------------------------------------------------------------------
# Rejection criteria (stateless, no LLM needed for Phase 2)
# ---------------------------------------------------------------------------

def _check_provenance(signature: Dict) -> Optional[Dict]:
    """REJECT if no timestamp or source provenance."""
    has_timestamp = bool(signature.get("source_timestamp") or signature.get("timestamp"))
    has_source = bool(signature.get("source") or signature.get("source_url"))
    if not has_timestamp and not has_source:
        return {
            "verdict": "REJECT",
            "reason": "Missing provenance — no timestamp or source attribution",
            "citation": "INV-SOURCE-PROVENANCE: Every if-then traces to transcript timestamp",
            "attempts": 1,
        }
    if not has_timestamp:
        return {
            "verdict": "REJECT",
            "reason": "Missing timestamp — source exists but no temporal reference",
            "citation": "INV-SOURCE-PROVENANCE",
            "attempts": 1,
        }
    return None


def _check_falsifiability(signature: Dict) -> Optional[Dict]:
    """REJECT if the claim cannot be tested."""
    condition = str(signature.get("condition", "")).lower()
    action = str(signature.get("action", "")).lower()

    unfalsifiable_markers = [
        "always", "never", "every time", "guaranteed",
        "100%", "certainly", "without exception",
    ]
    for marker in unfalsifiable_markers:
        if marker in condition or marker in action:
            return {
                "verdict": "REJECT",
                "reason": f"Unfalsifiable claim — contains absolute marker: '{marker}'",
                "citation": "Claims with absolute quantifiers cannot be empirically tested",
                "attempts": 1,
            }
    return None


def _check_logical_consistency(signature: Dict) -> Optional[Dict]:
    """REJECT if condition and action are logically contradictory."""
    condition = str(signature.get("condition", "")).lower()
    action = str(signature.get("action", "")).lower()

    # Basic contradiction: buy+sell in same statement
    if ("buy" in action and "sell" in action) and "or" not in action:
        return {
            "verdict": "REJECT",
            "reason": "Logical contradiction — action contains both buy and sell without alternative",
            "citation": "Mutually exclusive actions in single signature",
            "attempts": 1,
        }

    # Empty condition or action
    if not condition.strip() or not action.strip():
        return {
            "verdict": "REJECT",
            "reason": "Incomplete signature — empty condition or action",
            "citation": "If-then signature requires both IF and THEN clauses",
            "attempts": 1,
        }
    return None


def _check_tautology(signature: Dict) -> Optional[Dict]:
    """REJECT if condition restates or implies the action (circular logic)."""
    condition = str(signature.get("condition", "")).lower()
    action = str(signature.get("action", "")).lower()

    # Normalize for comparison
    cond_words = set(condition.split())
    action_words = set(action.split())

    # Direct tautology patterns
    tautology_pairs = [
        ("price goes up", "price increases"),
        ("price goes down", "price decreases"),
        ("bullish", "expect bullishness"),
        ("bearish", "expect bearishness"),
        ("price rises", "price moves up"),
        ("price falls", "price moves down"),
    ]

    for cond_pattern, action_pattern in tautology_pairs:
        if cond_pattern in condition and action_pattern in action:
            return {
                "verdict": "REJECT",
                "reason": f"Tautology — condition '{cond_pattern}' restates action '{action_pattern}'",
                "citation": "Circular logic: condition implies action by definition",
                "attempts": 1,
            }

    # High overlap detection (>70% word overlap = suspicious)
    if len(cond_words) >= 3 and len(action_words) >= 3:
        overlap = cond_words & action_words
        overlap_ratio = len(overlap) / min(len(cond_words), len(action_words))
        if overlap_ratio > 0.7:
            return {
                "verdict": "REJECT",
                "reason": f"Tautology suspected — {len(overlap)} words overlap between condition and action",
                "citation": "High word overlap suggests circular reasoning",
                "attempts": 1,
            }
    return None


def _check_ambiguity(signature: Dict) -> Optional[Dict]:
    """REJECT if condition is not actionable without subjective interpretation."""
    condition = str(signature.get("condition", "")).lower()
    action = str(signature.get("action", "")).lower()

    # Ambiguous/subjective markers
    ambiguous_markers = [
        "looks", "feels", "seems", "appears", "might",
        "could be", "probably", "maybe", "sort of", "kind of",
        "looks good", "looks bad", "looks weak", "looks strong",
        "feels heavy", "feels light", "feels right",
    ]

    for marker in ambiguous_markers:
        if marker in condition:
            return {
                "verdict": "REJECT",
                "reason": f"Ambiguity — condition contains subjective marker: '{marker}'",
                "citation": "Conditions must be objectively testable without interpretation",
                "attempts": 1,
            }
        if marker in action:
            return {
                "verdict": "REJECT",
                "reason": f"Ambiguity — action contains subjective marker: '{marker}'",
                "citation": "Actions must be concrete and executable",
                "attempts": 1,
            }
    return None


def _check_canon_conflict(signature: Dict, theory_text: str) -> Optional[Dict]:
    """REJECT if signature contradicts existing THEORY.md canon."""
    if not theory_text:
        return None

    condition = str(signature.get("condition", "")).lower()

    # Check for direct contradictions with existing theory entries
    # Phase 2: simple keyword overlap check
    # Phase 3: semantic similarity via LLM
    theory_lower = theory_text.lower()
    contradiction_pairs = [
        ("bullish", "bearish"),
        ("long", "short"),
        ("buy", "sell"),
        ("support", "resistance"),
    ]
    for term_a, term_b in contradiction_pairs:
        if term_a in condition:
            # Check if theory says opposite about similar context
            # Simplified: look for the opposite term near similar keywords
            condition_words = set(condition.split())
            for line in theory_lower.split("\n"):
                if term_b in line:
                    overlap = condition_words & set(line.split())
                    if len(overlap) >= 3:
                        return {
                            "verdict": "REJECT",
                            "reason": f"Conflicts with canon — condition uses '{term_a}' but THEORY.md contains '{term_b}' in similar context",
                            "citation": f"THEORY.md line containing: '{line.strip()[:80]}'",
                            "attempts": 2,
                        }
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def audit_signature(signature: Dict) -> Dict:
    """Run all rejection criteria against a single if-then signature.

    Args:
        signature: dict with keys: id, condition, action, source_timestamp, source

    Returns:
        Auditor verdict dict: {verdict, reason, citation, attempts}
    """
    manifest = _load_manifest()
    model_family = manifest.get("family", "unknown")
    model = manifest.get("model", "unknown")

    logger.info(
        "Auditing signature %s | model=%s family=%s",
        signature.get("id", "?"), model, model_family,
    )

    # Run rejection criteria in order (fail fast)
    # 6 mandatory falsification attacks per v0.3 Bounty Hunter spec
    checks = [
        ("provenance", lambda s: _check_provenance(s)),
        ("falsifiability", lambda s: _check_falsifiability(s)),
        ("logical_consistency", lambda s: _check_logical_consistency(s)),
        ("tautology", lambda s: _check_tautology(s)),
        ("ambiguity", lambda s: _check_ambiguity(s)),
        ("canon_conflict", lambda s: _check_canon_conflict(s, _load_theory())),
    ]

    attempt_count = 0
    for check_name, check_fn in checks:
        attempt_count += 1
        result = check_fn(signature)
        if result is not None:
            result["attempts"] = min(attempt_count, MAX_ATTEMPTS)
            result["auditor_model"] = model
            result["auditor_family"] = model_family
            result["check_failed"] = check_name
            logger.info(
                "REJECT %s: %s (%s)", signature.get("id", "?"), result["reason"], check_name
            )
            return result

    # All checks passed — no falsification found
    return {
        "verdict": "NO_FALSIFICATION_FOUND",
        "reason": f"No falsification found after {MAX_ATTEMPTS} attempts. Flagging for human review.",
        "citation": "All automated checks passed — manual review recommended",
        "attempts": MAX_ATTEMPTS,
        "auditor_model": model,
        "auditor_family": model_family,
    }


def audit_batch(signatures: List[Dict]) -> Dict:
    """Audit a batch of signatures. Returns summary with per-signature results.

    v0.3 Bounty Hunter: Tracks rejection rate and flags low-rejection batches.
    Target: 10% rejection floor. <5% triggers warning.
    """
    results = []
    rejected = 0
    passed = 0
    rejection_reasons: Dict[str, int] = {}

    for sig in signatures:
        result = audit_signature(sig)
        result["signature_id"] = sig.get("id", "unknown")
        results.append(result)
        if result["verdict"] == "REJECT":
            rejected += 1
            # Track rejection reasons for analysis
            check_failed = result.get("check_failed", "unknown")
            rejection_reasons[check_failed] = rejection_reasons.get(check_failed, 0) + 1
        else:
            passed += 1

    # Calculate rejection rate
    total = len(signatures)
    rejection_rate = rejected / total if total > 0 else 0.0

    # v0.3 Bounty Hunter: Flag low rejection rates
    # Target floor: 10%. Warning at <5%. 0% = rubber stamp.
    rate_status = "OK"
    if total >= 5:  # Only flag on meaningful batches
        if rejection_rate == 0.0:
            rate_status = "RUBBER_STAMP"
            logger.error(
                "[AUDITOR] RUBBER STAMP ALERT: 0%% rejection on batch of %d. "
                "Auditor may have failed. Manual review required.",
                total,
            )
        elif rejection_rate < 0.05:
            rate_status = "CRITICAL_LOW"
            logger.warning(
                "[AUDITOR] CRITICAL: Rejection rate %.1f%% < 5%% floor. "
                "Batch may be rubber-stamped. Total=%d, Rejected=%d",
                rejection_rate * 100, total, rejected,
            )
        elif rejection_rate < 0.10:
            rate_status = "BELOW_TARGET"
            logger.warning(
                "[AUDITOR] WARNING: Rejection rate %.1f%% below 10%% target. "
                "Total=%d, Rejected=%d",
                rejection_rate * 100, total, rejected,
            )

    logger.info(
        "[AUDITOR] Batch complete: %d total, %d rejected (%.1f%%), status=%s",
        total, rejected, rejection_rate * 100, rate_status,
    )

    return {
        "total": total,
        "rejected": rejected,
        "passed": passed,
        "rejection_rate": rejection_rate,
        "rejection_rate_pct": round(rejection_rate * 100, 1),
        "rate_status": rate_status,
        "rejection_reasons": rejection_reasons,
        "results": results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
