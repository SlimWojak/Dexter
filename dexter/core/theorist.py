"""Theorist — Forensic Extractor for ICT methodology.

Extracts if-then signatures from transcript segments.
Phase 3: mock mode extraction via pattern matching.
Phase 5: real LLM extraction via OpenRouter (deepseek-v3.2).
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger("dexter.theorist")

ROLES_DIR = Path(__file__).resolve().parent.parent / "roles"


def _load_manifest() -> Dict:
    path = ROLES_DIR / "theorist.yaml"
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------------------------
# Mock extraction (Phase 3) — pattern-based, no LLM
# ---------------------------------------------------------------------------

# Patterns that indicate if-then logic in ICT transcripts
_IF_THEN_PATTERNS = [
    # "if X, Y" / "if X then Y" / "when X, Y"
    re.compile(
        r"(?:if|when)\s+(.+?)(?:,\s*|\s+then\s+)(.+?)(?:\.|$)",
        re.IGNORECASE,
    ),
    # "X is your Y" (signal pattern)
    re.compile(
        r"(.+?)\s+(?:is your|that'?s your)\s+(.+?)(?:\.|$)",
        re.IGNORECASE,
    ),
]

# Patterns that indicate absolute/unfalsifiable claims
_ABSOLUTE_MARKERS = {"always", "never", "guaranteed", "100%", "every time"}


def _timestamp_to_str(seconds: float) -> str:
    """Convert seconds to MM:SS format."""
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"


def _extract_from_segment(
    segment: Dict, sig_counter: int, negative_patterns: List[str]
) -> List[Dict]:
    """Extract if-then signatures from a single transcript segment."""
    text = segment.get("text", "")
    timestamp = _timestamp_to_str(segment.get("start", 0))
    signatures = []

    for pattern in _IF_THEN_PATTERNS:
        for match in pattern.finditer(text):
            condition = match.group(1).strip()
            action = match.group(2).strip()

            # Skip if matches negative bead pattern
            skip = False
            for neg in negative_patterns:
                if neg.lower() in condition.lower() or neg.lower() in action.lower():
                    logger.info("Skipping signature — matches negative pattern: %s", neg)
                    skip = True
                    break
            if skip:
                continue

            # Determine confidence
            confidence = "EXPLICIT"
            text_lower = text.lower()
            if any(m in text_lower for m in _ABSOLUTE_MARKERS):
                confidence = "INFERRED"

            sig_counter += 1
            signatures.append({
                "id": f"S-{sig_counter:03d}",
                "condition": f"IF {condition}",
                "action": f"THEN {action}",
                "source_timestamp": timestamp,
                "source_quote": text[:200],
                "confidence": confidence,
                "source": segment.get("source", ""),
            })

    return signatures


def extract_signatures(
    transcript: Dict,
    *,
    negative_beads: Optional[List[Dict]] = None,
) -> List[Dict]:
    """Extract if-then signatures from a transcript.

    Args:
        transcript: dict with "segments" list and "title"
        negative_beads: recent NEGATIVE beads to avoid repeating patterns

    Returns:
        List of signature dicts matching Theorist output format.
    """
    manifest = _load_manifest()
    model = manifest.get("model", "unknown")
    family = manifest.get("family", "unknown")

    logger.info(
        "Theorist extracting from '%s' | model=%s family=%s",
        transcript.get("title", "?"), model, family,
    )

    # Build negative pattern list for avoidance
    negative_patterns = []
    if negative_beads:
        for nb in negative_beads:
            reason = nb.get("reason", "")
            # Extract key phrases from rejection reasons
            negative_patterns.append(reason)
        logger.info("Avoiding %d negative patterns", len(negative_patterns))

    segments = transcript.get("segments", [])
    all_signatures = []
    sig_counter = 0

    for seg in segments:
        # Add source info to segment
        seg["source"] = transcript.get("title", "unknown")
        extracted = _extract_from_segment(seg, sig_counter, negative_patterns)
        sig_counter += len(extracted)
        all_signatures.extend(extracted)

    logger.info(
        "Extracted %d signatures from %d segments",
        len(all_signatures), len(segments),
    )

    return all_signatures
