"""Theorist — Forensic Extractor for ICT methodology.

Extracts if-then signatures from transcript segments.
Phase 3: mock mode extraction via pattern matching (per-segment).
Phase 4A: sliding window extraction for real transcripts (auto-caption chunks).
Phase 5: real LLM extraction via OpenRouter (deepseek-v3.2).
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
# Pattern-based extraction (Phase 3 + Phase 4A windowed)
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

# Minimum length for condition and action to be considered meaningful
_MIN_PHRASE_LEN = 15

# Window sizes for joining auto-caption chunks
_WINDOW_SIZES = [3, 5, 7]


def _timestamp_to_str(seconds: float) -> str:
    """Convert seconds to MM:SS format."""
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"


def _normalize_text(text: str) -> str:
    """Normalize text for deduplication comparison."""
    return re.sub(r"\s+", " ", text.lower().strip())[:80]


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


def _extract_windowed(
    segments: List[Dict],
    negative_patterns: List[str],
    source_title: str,
) -> List[Dict]:
    """Sliding window extraction for real transcripts with auto-caption chunks.

    Joins consecutive segments into windows of varying sizes, runs pattern
    matching on joined text, deduplicates by normalized condition text.
    """
    if not segments:
        return []

    # Track seen conditions to deduplicate overlapping windows
    seen_conditions: Dict[str, int] = {}  # normalized_condition → first segment index
    raw_matches: List[Tuple[int, str, str, str, str]] = []  # (seg_idx, timestamp, condition, action, quote)

    for window_size in _WINDOW_SIZES:
        for i in range(len(segments) - window_size + 1):
            window_segs = segments[i:i + window_size]
            window_text = " ".join(s.get("text", "") for s in window_segs)
            timestamp = _timestamp_to_str(window_segs[0].get("start", 0))

            for pattern in _IF_THEN_PATTERNS:
                for match in pattern.finditer(window_text):
                    condition = match.group(1).strip()
                    action = match.group(2).strip()

                    # Skip short/trivial matches
                    if len(condition) < _MIN_PHRASE_LEN or len(action) < _MIN_PHRASE_LEN:
                        continue

                    # Deduplicate by normalized condition
                    norm_cond = _normalize_text(condition)
                    if norm_cond in seen_conditions:
                        # Keep the longer action if same condition seen before
                        prev_idx = seen_conditions[norm_cond]
                        prev = raw_matches[prev_idx]
                        if len(action) > len(prev[3]):
                            raw_matches[prev_idx] = (i, timestamp, condition, action, window_text[:200])
                        continue

                    seen_conditions[norm_cond] = len(raw_matches)
                    raw_matches.append((i, timestamp, condition, action, window_text[:200]))

    # Filter negative patterns and build signatures
    signatures = []
    sig_counter = 0

    for seg_idx, timestamp, condition, action, quote in raw_matches:
        # Skip negative patterns
        skip = False
        for neg in negative_patterns:
            if neg.lower() in condition.lower() or neg.lower() in action.lower():
                logger.info("Skipping windowed signature — matches negative pattern: %s", neg)
                skip = True
                break
        if skip:
            continue

        # Determine confidence
        combined_lower = (condition + " " + action).lower()
        confidence = "EXPLICIT"
        if any(m in combined_lower for m in _ABSOLUTE_MARKERS):
            confidence = "INFERRED"

        sig_counter += 1
        signatures.append({
            "id": f"S-{sig_counter:03d}",
            "condition": f"IF {condition}",
            "action": f"THEN {action}",
            "source_timestamp": timestamp,
            "source_quote": quote,
            "confidence": confidence,
            "source": source_title,
        })

    return signatures


def _needs_windowed_extraction(segments: List[Dict]) -> bool:
    """Detect if transcript has short auto-caption chunks needing windowed extraction."""
    if len(segments) < 20:
        return False
    # Sample average segment length
    sample = segments[:min(50, len(segments))]
    avg_len = sum(len(s.get("text", "")) for s in sample) / max(len(sample), 1)
    # Auto-captions typically have very short chunks (< 60 chars avg)
    return avg_len < 60


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
            negative_patterns.append(reason)
        logger.info("Avoiding %d negative patterns", len(negative_patterns))

    segments = transcript.get("segments", [])
    source_title = transcript.get("title", "unknown")

    # Choose extraction strategy based on segment characteristics
    if _needs_windowed_extraction(segments):
        logger.info(
            "Using windowed extraction (auto-caption chunks detected, %d segments)",
            len(segments),
        )
        all_signatures = _extract_windowed(segments, negative_patterns, source_title)
    else:
        # Per-segment extraction (works for mock and pre-joined transcripts)
        all_signatures = []
        sig_counter = 0
        for seg in segments:
            seg["source"] = source_title
            extracted = _extract_from_segment(seg, sig_counter, negative_patterns)
            sig_counter += len(extracted)
            all_signatures.extend(extracted)

    logger.info(
        "Extracted %d signatures from %d segments",
        len(all_signatures), len(segments),
    )

    return all_signatures
