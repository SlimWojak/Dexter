"""4-layer stateless injection guard — runs OUTSIDE container as pre-filter.

Layers:
  1. Preprocess: strip HTML/JS/comments, normalize whitespace, detect encoding tricks
  2. Pattern match: regex against attack_vectors.jsonl
  3. Semantic filter: cosine similarity (stdlib TF-IDF — no external embedder)
  4. Action: HALT + log on flag
"""

from __future__ import annotations

import base64
import json
import logging
import math
import os
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("dexter.injection_guard")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ATTACK_VECTORS_PATH = DATA_DIR / "attack_vectors.jsonl"
LOG_DIR = Path(__file__).resolve().parent.parent / "memory" / "injection_logs"


# ---------------------------------------------------------------------------
# Layer 1: Preprocess
# ---------------------------------------------------------------------------

_HTML_TAG_RE = re.compile(r"<[^>]+>", re.IGNORECASE)
_JS_BLOCK_RE = re.compile(
    r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL
)
_CODE_COMMENT_RE = re.compile(r"(//.*?$|/\*.*?\*/|#.*?$)", re.MULTILINE | re.DOTALL)
_MULTI_SPACE_RE = re.compile(r"\s+")

# Unicode categories that are suspicious in bulk (format/control chars)
_SUSPICIOUS_CATEGORIES = {"Cf", "Cc", "Co", "Cn"}


def _strip_html_js(text: str) -> str:
    text = _JS_BLOCK_RE.sub("", text)
    text = _HTML_TAG_RE.sub("", text)
    return text


def _strip_code_comments(text: str) -> str:
    return _CODE_COMMENT_RE.sub("", text)


def _normalize_whitespace(text: str) -> str:
    return _MULTI_SPACE_RE.sub(" ", text).strip()


def _detect_base64(text: str) -> List[str]:
    """Find base64-encoded segments that decode to ASCII."""
    findings = []
    b64_re = re.compile(r"[A-Za-z0-9+/]{20,}={0,2}")
    for match in b64_re.finditer(text):
        try:
            decoded = base64.b64decode(match.group()).decode("utf-8", errors="ignore")
            if len(decoded) > 5 and decoded.isprintable():
                findings.append(decoded)
        except Exception:
            pass
    return findings


def _detect_unicode_abuse(text: str) -> bool:
    """Flag if >5% of chars are suspicious unicode categories."""
    if not text:
        return False
    suspicious = sum(1 for c in text if unicodedata.category(c) in _SUSPICIOUS_CATEGORIES)
    return (suspicious / len(text)) > 0.05


def preprocess(text: str) -> Tuple[str, List[str]]:
    """Layer 1: clean text, return (cleaned, warnings)."""
    warnings = []

    # Detect encoding tricks on raw input
    b64_decoded = _detect_base64(text)
    if b64_decoded:
        warnings.append(f"base64_decoded_segments: {len(b64_decoded)}")

    if _detect_unicode_abuse(text):
        warnings.append("unicode_abuse_detected")

    cleaned = _strip_html_js(text)
    cleaned = _strip_code_comments(cleaned)
    cleaned = _normalize_whitespace(cleaned)

    # Also check decoded base64 content for injection
    full_text = cleaned + " " + " ".join(b64_decoded)

    return full_text, warnings


# ---------------------------------------------------------------------------
# Layer 2: Pattern match
# ---------------------------------------------------------------------------

_patterns_cache: Optional[List[Dict]] = None


def _load_patterns() -> List[Dict]:
    global _patterns_cache
    if _patterns_cache is not None:
        return _patterns_cache
    patterns = []
    if ATTACK_VECTORS_PATH.exists():
        with open(ATTACK_VECTORS_PATH) as f:
            for line in f:
                line = line.strip()
                if line:
                    patterns.append(json.loads(line))
    _patterns_cache = patterns
    return patterns


def pattern_match(text: str) -> List[Dict]:
    """Layer 2: regex match against known attack vectors. Returns matches."""
    text_lower = text.lower()
    matches = []
    for vec in _load_patterns():
        pattern = vec["pattern"].lower()
        if re.search(re.escape(pattern), text_lower):
            matches.append(vec)
    return matches


# ---------------------------------------------------------------------------
# Layer 3: Semantic filter (stdlib TF-IDF cosine — no external deps)
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    return re.findall(r"\b\w+\b", text.lower())


def _cosine_similarity(a: Counter, b: Counter) -> float:
    """Cosine similarity between two term-frequency counters."""
    common = set(a) & set(b)
    if not common:
        return 0.0
    dot = sum(a[k] * b[k] for k in common)
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def semantic_filter(text: str, threshold: float = 0.85) -> List[Dict]:
    """Layer 3: TF-IDF cosine similarity against attack patterns.

    Uses stdlib-only approach. For production, swap to sentence-transformers
    embeddings (requires audit per CLAUDE.md deps policy).
    """
    text_tokens = Counter(_tokenize(text))
    flagged = []
    for vec in _load_patterns():
        pattern_tokens = Counter(_tokenize(vec["pattern"]))
        sim = _cosine_similarity(text_tokens, pattern_tokens)
        if sim >= threshold:
            flagged.append({**vec, "similarity": round(sim, 4)})
    return flagged


# ---------------------------------------------------------------------------
# Layer 4: Action
# ---------------------------------------------------------------------------

def _log_incident(text: str, reason: str, details: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    incident = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "raw_text_preview": text[:500],
        "details": details,
    }
    log_file = LOG_DIR / f"incident_{datetime.now(timezone.utc).strftime('%Y%m%d')}.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(incident) + "\n")
    logger.warning("INJECTION HALTED: %s | %s", reason, json.dumps(details))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class InjectionDetected(Exception):
    """Raised when injection is detected — HALT before LLM exposure."""

    def __init__(self, reason: str, details: dict):
        self.reason = reason
        self.details = details
        super().__init__(f"Injection detected: {reason}")


def scan(text: str, *, semantic_threshold: float = 0.85) -> dict:
    """Run all 4 layers. Returns result dict. Raises InjectionDetected on flag.

    Returns:
        {"clean": True/False, "warnings": [...], "matches": [...]}
    """
    result = {"clean": True, "warnings": [], "pattern_matches": [], "semantic_matches": []}

    # Layer 2 (pre-strip): Pattern match on RAW text first
    # HTML/XSS patterns like <script> must be caught before Layer 1 strips them
    p_matches_raw = pattern_match(text)

    # Layer 1: Preprocess
    cleaned, warnings = preprocess(text)
    result["warnings"] = warnings

    # Layer 2 (post-strip): Pattern match on cleaned text (catches decoded b64 etc.)
    p_matches_cleaned = pattern_match(cleaned)

    # Merge matches, deduplicate by id
    seen_ids = set()
    p_matches = []
    for m in p_matches_raw + p_matches_cleaned:
        if m["id"] not in seen_ids:
            seen_ids.add(m["id"])
            p_matches.append(m)
    result["pattern_matches"] = p_matches

    # Layer 3: Semantic filter
    s_matches = semantic_filter(cleaned, threshold=semantic_threshold)
    result["semantic_matches"] = s_matches

    # Layer 4: Action
    if p_matches or s_matches:
        result["clean"] = False
        reason_parts = []
        if p_matches:
            reason_parts.append(f"pattern_match({len(p_matches)})")
        if s_matches:
            reason_parts.append(f"semantic_flag({len(s_matches)})")
        reason = "; ".join(reason_parts)
        _log_incident(text, reason, result)
        raise InjectionDetected(reason, result)

    if warnings:
        logger.info("Preprocess warnings (no halt): %s", warnings)

    return result
