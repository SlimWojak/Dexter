"""Theorist — Forensic Extractor for ICT methodology.

Extracts if-then signatures from transcript segments.
Phase 3: mock mode extraction via pattern matching (per-segment).
Phase 4A: sliding window extraction for real transcripts (auto-caption chunks).
Phase 5: LLM extraction via OpenRouter (deepseek/deepseek-chat).
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

# OpenRouter model for LLM extraction
THEORIST_MODEL = "deepseek/deepseek-chat"

# System prompt for LLM Theorist
THEORIST_SYSTEM_PROMPT = """You are a FORENSIC EXTRACTOR for ICT (Inner Circle Trader) methodology.

ICT JARGON REFERENCE (use these exact terms):
- FVG = Fair Value Gap (imbalance in price)
- OB = Order Block (institutional candle)
- MSS = Market Structure Shift
- CHOCH = Change of Character
- OTE = Optimal Trade Entry (61.8-78.6% fib)
- SMT = Smart Money Technique (divergence between correlated assets)
- Killzone = High-probability trading window (London/NY open)
- Displacement = Strong directional move creating imbalance
- Liquidity = Resting orders (stops, equal highs/lows)
- Sweep/Raid = Taking liquidity before reversal
- Breaker = Failed order block that becomes support/resistance
- Mitigation = Price returning to fill an imbalance
- Power of Three = Accumulation → Manipulation → Distribution
- Dealing Range = High-to-low range containing current price action
- Silver Bullet = Specific FVG entry during killzone windows
- Draw on Liquidity = Target that price is moving toward

YOUR ONLY JOB: Extract if-then logical statements from the transcript.

RULES:
- Extract ONLY explicit if-then trading logic
- Every signature MUST include approximate timestamp (from segment markers)
- NO interpretation, NO inference, NO "what he probably means"
- Use canonical ICT terms even if transcript uses informal language
- If a claim is vague or motivational (not actionable), SKIP IT
- Deduplicate: if same logic appears twice, keep first occurrence only
- Skip channel promotion, personal anecdotes, non-trading content

DRAWER CLASSIFICATION:
For each signature, classify into one of 5 drawers:

Drawer 1 - HTF BIAS: Higher timeframe directional context
  Examples: Weekly bias, daily trend, institutional positioning

Drawer 2 - MARKET STRUCTURE: Structural breaks and formations
  Examples: MSS, CHoCH, BOS, swing points, equal highs/lows

Drawer 3 - PREMIUM/DISCOUNT: Price relative to range
  Examples: Above/below 50% fib, dealing range position, equilibrium

Drawer 4 - ENTRY MODEL: Specific entry patterns
  Examples: FVG entry, order block, liquidity sweep trigger

Drawer 5 - CONFIRMATION: Additional validation
  Examples: SMT divergence, volume, time/session, displacement

OUTPUT FORMAT (strict JSON array, nothing else):
[
  {
    "id": "S-001",
    "if": "price sweeps liquidity below equal lows during London killzone",
    "then": "look for displacement and FVG formation for long entry",
    "timestamp": "14:32",
    "source_quote": "verbatim quote, max 30 words",
    "confidence": "EXPLICIT",
    "drawer": 4,
    "drawer_confidence": "explicit",
    "drawer_basis": "ICT explicitly taught this as entry model pattern"
  }
]

confidence values: EXPLICIT (directly stated), INFERRED (implied by context), UNCLEAR (ambiguous)
drawer_confidence values: explicit (ICT named the category), inferred (clear from context)

If no clear if-then logic in this segment, return: []

AVOID PATTERNS SIMILAR TO THESE REJECTED SIGNATURES:
{negative_context}

Extract facts. Not meaning. Not motivation."""


def _load_manifest() -> Dict:
    path = ROLES_DIR / "theorist.yaml"
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _is_llm_mode() -> bool:
    """Check if LLM extraction is enabled."""
    return os.getenv("DEXTER_LLM_MODE", "false").lower() == "true"


# ---------------------------------------------------------------------------
# LLM extraction (Phase 5)
# ---------------------------------------------------------------------------

def _parse_llm_json(content: str) -> List[Dict]:
    """Parse JSON array from LLM response, handling markdown code blocks."""
    text = content.strip()
    # Handle ```json ... ``` blocks
    if text.startswith("```"):
        lines = text.split("\n")
        # Find the content between ``` markers
        inside = []
        in_block = False
        for line in lines:
            if line.strip().startswith("```") and not in_block:
                in_block = True
                continue
            elif line.strip() == "```" and in_block:
                break
            elif in_block:
                inside.append(line)
        text = "\n".join(inside)

    # Try parsing
    result = json.loads(text)
    if isinstance(result, list):
        return result
    return []


def _extract_llm(
    chunks: List[Dict],
    negative_beads: Optional[List[Dict]],
    source_title: str,
) -> List[Dict]:
    """Extract signatures using LLM via OpenRouter.

    Processes transcript chunks through deepseek, deduplicates results.
    """
    from core.llm_client import call_llm

    # Format negative context
    neg_context = "None yet."
    if negative_beads:
        neg_lines = [
            f"- {nb.get('id', '?')}: {nb.get('reason', '')}"
            for nb in negative_beads[:10]
        ]
        neg_context = "\n".join(neg_lines)

    system_prompt = THEORIST_SYSTEM_PROMPT.replace("{negative_context}", neg_context)

    all_signatures: List[Dict] = []
    seen_logic: set = set()

    for chunk_idx, chunk in enumerate(chunks):
        user_content = (
            f"TRANSCRIPT SEGMENT [{chunk['start']:.0f}s - {chunk['end']:.0f}s]:\n\n"
            f"{chunk['text']}\n\n"
            f"Extract all if-then trading logic from this segment. Return JSON array only."
        )

        try:
            result = call_llm(
                model=THEORIST_MODEL,
                system_prompt=system_prompt,
                user_content=user_content,
                temperature=0.2,
            )

            signatures = _parse_llm_json(result["content"])

            for sig in signatures:
                # Normalize for dedup
                if_clause = sig.get("if", "")
                then_clause = sig.get("then", "")
                logic_key = f"{if_clause.lower().strip()}|{then_clause.lower().strip()}"

                if logic_key in seen_logic:
                    continue
                seen_logic.add(logic_key)

                sig_id = f"S-{len(all_signatures) + 1:03d}"
                all_signatures.append({
                    "id": sig_id,
                    "condition": f"IF {if_clause}",
                    "action": f"THEN {then_clause}",
                    "source_timestamp": sig.get("timestamp", _timestamp_to_str(chunk["start"])),
                    "source_quote": sig.get("source_quote", "")[:200],
                    "confidence": sig.get("confidence", "EXPLICIT"),
                    "source": source_title,
                    "drawer": sig.get("drawer"),
                    "drawer_confidence": sig.get("drawer_confidence", "inferred"),
                    "drawer_basis": sig.get("drawer_basis", ""),
                })

            logger.info(
                "[LLM] Chunk %d/%d: %d signatures (total unique: %d)",
                chunk_idx + 1, len(chunks), len(signatures), len(all_signatures),
            )

        except json.JSONDecodeError as e:
            logger.warning("[LLM] JSON parse error on chunk %d: %s", chunk_idx + 1, e)
            continue
        except Exception as e:
            logger.error("[LLM] Extraction error on chunk %d: %s", chunk_idx + 1, e)
            continue

    return all_signatures


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
    """Sliding window extraction for real transcripts with auto-caption chunks."""
    if not segments:
        return []

    seen_conditions: Dict[str, int] = {}
    raw_matches: List[Tuple[int, str, str, str, str]] = []

    for window_size in _WINDOW_SIZES:
        for i in range(len(segments) - window_size + 1):
            window_segs = segments[i:i + window_size]
            window_text = " ".join(s.get("text", "") for s in window_segs)
            timestamp = _timestamp_to_str(window_segs[0].get("start", 0))

            for pattern in _IF_THEN_PATTERNS:
                for match in pattern.finditer(window_text):
                    condition = match.group(1).strip()
                    action = match.group(2).strip()

                    if len(condition) < _MIN_PHRASE_LEN or len(action) < _MIN_PHRASE_LEN:
                        continue

                    norm_cond = _normalize_text(condition)
                    if norm_cond in seen_conditions:
                        prev_idx = seen_conditions[norm_cond]
                        prev = raw_matches[prev_idx]
                        if len(action) > len(prev[3]):
                            raw_matches[prev_idx] = (i, timestamp, condition, action, window_text[:200])
                        continue

                    seen_conditions[norm_cond] = len(raw_matches)
                    raw_matches.append((i, timestamp, condition, action, window_text[:200]))

    signatures = []
    sig_counter = 0

    for seg_idx, timestamp, condition, action, quote in raw_matches:
        skip = False
        for neg in negative_patterns:
            if neg.lower() in condition.lower() or neg.lower() in action.lower():
                logger.info("Skipping windowed signature — matches negative pattern: %s", neg)
                skip = True
                break
        if skip:
            continue

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
    sample = segments[:min(50, len(segments))]
    avg_len = sum(len(s.get("text", "")) for s in sample) / max(len(sample), 1)
    return avg_len < 60


def extract_signatures(
    transcript: Dict,
    *,
    negative_beads: Optional[List[Dict]] = None,
    chunks: Optional[List[Dict]] = None,
) -> List[Dict]:
    """Extract if-then signatures from a transcript.

    Args:
        transcript: dict with "segments" list and "title"
        negative_beads: recent NEGATIVE beads to avoid repeating patterns
        chunks: pre-built chunks for LLM mode (from chunk_transcript)

    Returns:
        List of signature dicts matching Theorist output format.
    """
    manifest = _load_manifest()
    model = manifest.get("model", "unknown")
    family = manifest.get("family", "unknown")
    source_title = transcript.get("title", "unknown")

    logger.info(
        "Theorist extracting from '%s' | model=%s family=%s | llm_mode=%s",
        source_title, model, family, _is_llm_mode(),
    )

    # LLM extraction mode (Phase 5)
    if _is_llm_mode() and chunks:
        logger.info("Using LLM extraction (%s) on %d chunks", THEORIST_MODEL, len(chunks))
        return _extract_llm(chunks, negative_beads, source_title)

    # Build negative pattern list for pattern-based extraction
    negative_patterns = []
    if negative_beads:
        for nb in negative_beads:
            reason = nb.get("reason", "")
            negative_patterns.append(reason)
        logger.info("Avoiding %d negative patterns", len(negative_patterns))

    segments = transcript.get("segments", [])

    # Choose extraction strategy based on segment characteristics
    if _needs_windowed_extraction(segments):
        logger.info(
            "Using windowed extraction (auto-caption chunks detected, %d segments)",
            len(segments),
        )
        all_signatures = _extract_windowed(segments, negative_patterns, source_title)
    else:
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
