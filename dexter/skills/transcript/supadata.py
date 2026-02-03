"""Supadata transcript API wrapper.

Phase 3: Mock data for testing.
Phase 4A: Real API integration with jargon accuracy checking.

API docs: https://docs.supadata.ai/get-transcript
Endpoint: GET https://api.supadata.ai/v1/transcript?url=<video_url>
Auth: x-api-key header
"""

from __future__ import annotations

import logging
import os
import time
from typing import Dict, List, Optional

import requests

logger = logging.getLogger("dexter.supadata")

SUPADATA_BASE_URL = "https://api.supadata.ai/v1"

# ICT jargon reference for accuracy checking
ICT_TERMS = [
    "FVG", "fair value gap", "order block", "breaker", "mitigation",
    "liquidity", "sweep", "raid", "displacement", "imbalance",
    "market structure shift", "MSS", "change of character", "CHOCH",
    "optimal trade entry", "OTE", "silver bullet", "killzone",
    "power of three", "accumulation", "manipulation", "distribution",
    "dealing range", "premium", "discount", "equilibrium",
    "institutional order flow", "smart money", "SMT", "divergence",
]

# Common transcription errors for ICT content
JARGON_ERROR_PATTERNS = [
    ("fairly value", "fair value"),
    ("order blog", "order block"),
    ("liquidity sweet", "liquidity sweep"),
    ("break her", "breaker"),
    ("kill zone", "killzone"),
    ("fair valley", "fair value"),
    ("order black", "order block"),
    ("displacement", "displacement"),  # correct — baseline
]


def _get_api_key() -> Optional[str]:
    """Get Supadata API key from environment."""
    return os.getenv("SUPADATA_KEY") or os.getenv("SUPADATA_API_KEY")


def _is_mock_mode() -> bool:
    return os.getenv("DEXTER_MOCK_MODE", "true").lower() == "true"


def fetch_transcript(video_url: str) -> Dict:
    """Fetch transcript from Supadata API or mock.

    Returns: {"video_id": str, "title": str, "segments": [{"start": float, "text": str}]}
    """
    # Mock mode
    if "mock" in video_url or _is_mock_mode():
        logger.info("Using mock transcript (DEXTER_MOCK_MODE=true or mock URL)")
        return _mock_ict_transcript()

    api_key = _get_api_key()
    if not api_key:
        raise ValueError(
            "SUPADATA_KEY not set in environment. "
            "Set DEXTER_MOCK_MODE=true for testing or provide API key."
        )

    return _fetch_real_transcript(video_url, api_key)


def _fetch_real_transcript(video_url: str, api_key: str) -> Dict:
    """Fetch transcript from Supadata API with job polling support."""
    logger.info("Fetching transcript from Supadata: %s", video_url)

    resp = requests.get(
        f"{SUPADATA_BASE_URL}/transcript",
        params={"url": video_url},
        headers={"x-api-key": api_key},
        timeout=60,
    )

    if resp.status_code == 202:
        # Async job — poll for results
        job_data = resp.json()
        job_id = job_data.get("jobId") or job_data.get("id")
        if not job_id:
            raise RuntimeError(f"Supadata returned 202 but no jobId: {resp.text[:200]}")
        logger.info("Async job started: %s. Polling...", job_id)
        return _poll_job(job_id, api_key)

    resp.raise_for_status()
    data = resp.json()
    return _normalize_transcript(data, video_url)


def _poll_job(job_id: str, api_key: str, max_wait: int = 300) -> Dict:
    """Poll Supadata async job until complete."""
    start = time.monotonic()
    poll_interval = 5

    while time.monotonic() - start < max_wait:
        resp = requests.get(
            f"{SUPADATA_BASE_URL}/transcript/{job_id}",
            headers={"x-api-key": api_key},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        status = data.get("status", "unknown")
        if status == "completed":
            result = data.get("result", data)
            return _normalize_transcript(result, job_id)
        elif status == "failed":
            error = data.get("error", "unknown error")
            raise RuntimeError(f"Supadata job {job_id} failed: {error}")

        logger.info("Job %s status: %s. Polling in %ds...", job_id, status, poll_interval)
        time.sleep(poll_interval)
        poll_interval = min(poll_interval * 1.5, 30)

    raise TimeoutError(f"Supadata job {job_id} timed out after {max_wait}s")


def _normalize_transcript(data: Dict, source: str) -> Dict:
    """Normalize Supadata response to internal format."""
    content = data.get("content", [])

    # Handle plain text response (no timestamps)
    if isinstance(content, str):
        return {
            "video_id": source,
            "title": data.get("title", source),
            "segments": [{"start": 0.0, "text": content}],
            "lang": data.get("lang", "en"),
        }

    # Handle timestamped chunks
    segments = []
    for chunk in content:
        if isinstance(chunk, dict):
            start_ms = chunk.get("offset", 0)
            text = chunk.get("text", "")
            if text.strip():
                segments.append({
                    "start": start_ms / 1000.0,  # ms → seconds
                    "text": text.strip(),
                })
        elif isinstance(chunk, str):
            segments.append({"start": 0.0, "text": chunk.strip()})

    return {
        "video_id": source,
        "title": data.get("title", source),
        "segments": segments,
        "lang": data.get("lang", "en"),
    }


def check_ict_jargon(transcript: Dict) -> Dict:
    """Check for ICT jargon accuracy in transcript.

    Returns: {"terms_found": int, "terms_checked": int,
              "potential_errors": [...], "error_rate": float}
    """
    full_text = " ".join(
        seg.get("text", "") for seg in transcript.get("segments", [])
    )
    full_text_lower = full_text.lower()

    found = []
    for term in ICT_TERMS:
        if term.lower() in full_text_lower:
            found.append(term)

    potential_errors = []
    for error_text, correct_text in JARGON_ERROR_PATTERNS:
        if error_text == correct_text:
            continue  # skip baseline entries
        if error_text.lower() in full_text_lower:
            potential_errors.append({"found": error_text, "expected": correct_text})

    error_rate = len(potential_errors) / max(len(found), 1)

    result = {
        "terms_found": len(found),
        "terms_checked": len(ICT_TERMS),
        "found_terms": found,
        "potential_errors": potential_errors,
        "error_rate": round(error_rate, 4),
    }

    logger.info(
        "Jargon check: %d/%d terms found, %d errors (rate=%.1f%%)",
        len(found), len(ICT_TERMS), len(potential_errors), error_rate * 100,
    )

    return result


def format_for_theorist(transcript: Dict) -> str:
    """Format transcript segments for Theorist input."""
    lines = [
        f"[{seg['start']:.1f}s] {seg['text']}"
        for seg in transcript.get("segments", [])
    ]
    return f"VIDEO: {transcript.get('title', 'unknown')}\n\n" + "\n".join(lines)


def chunk_transcript(
    transcript: Dict,
    chunk_duration: int = 300,
    overlap: int = 60,
) -> List[Dict]:
    """Split transcript into overlapping chunks for LLM processing.

    Args:
        transcript: Full transcript with segments
        chunk_duration: Target chunk size in seconds (default 5 min)
        overlap: Overlap between chunks in seconds (default 1 min)

    Returns:
        List of {"start": float, "end": float, "text": str}
    """
    segments = transcript.get("segments", [])
    if not segments:
        return []

    chunks = []
    current_start = segments[0].get("start", 0)
    current_texts: List[str] = []
    current_end = current_start

    for seg in segments:
        seg_start = seg.get("start", 0)
        seg_text = seg.get("text", "")

        # Start new chunk if we exceed duration
        if seg_start - current_start > chunk_duration and current_texts:
            chunks.append({
                "start": current_start,
                "end": current_end,
                "text": " ".join(current_texts),
            })
            # Start new chunk with overlap
            overlap_start = max(0, seg_start - overlap)
            # Gather overlap segments
            current_start = overlap_start
            current_texts = []
            # Re-add recent segments that fall within overlap window
            for prev_seg in segments:
                ps = prev_seg.get("start", 0)
                if overlap_start <= ps < seg_start:
                    current_texts.append(prev_seg.get("text", ""))

        current_texts.append(seg_text)
        current_end = seg_start

    # Last chunk
    if current_texts:
        chunks.append({
            "start": current_start,
            "end": current_end,
            "text": " ".join(current_texts),
        })

    logger.info("Chunked %d segments into %d chunks (%ds windows, %ds overlap)",
                len(segments), len(chunks), chunk_duration, overlap)
    return chunks


# ---------------------------------------------------------------------------
# Mock transcript (preserved from Phase 3)
# ---------------------------------------------------------------------------

def _mock_ict_transcript() -> Dict:
    """Mock ICT-style transcript for loop testing."""
    return {
        "video_id": "mock_ict_2022_mentorship_01",
        "title": "ICT 2022 Mentorship - Episode 1 (MOCK)",
        "segments": [
            {
                "start": 0.0,
                "text": "Welcome to the mentorship. Today we cover fair value gaps and market structure.",
            },
            {
                "start": 14.5,
                "text": "When price trades into a fair value gap during the London session, we look for displacement.",
            },
            {
                "start": 32.0,
                "text": "If you see a market structure shift after sweeping liquidity, that's your entry signal.",
            },
            {
                "start": 48.0,
                "text": "If a fair value gap forms, it always fills completely, then you enter at the retracement.",
            },
            {
                "start": 67.0,
                "text": "If price is above the 50 percent of the dealing range during New York AM session, then bias is bullish.",
            },
            {
                "start": 89.0,
                "text": "If you cannot identify the draw on liquidity first, then do not enter a trade.",
            },
            {
                "start": 112.0,
                "text": "If the weekly candle has a long wick into a breaker block, then expect reversal.",
            },
            {
                "start": 134.0,
                "text": "When there is a gap between the bodies of consecutive candles, if price returns to fill it, then look for continuation in the original direction.",
            },
            {
                "start": 156.0,
                "text": "If the Asian session high is swept during London open, then look for a reversal to the downside.",
            },
            {
                "start": 178.0,
                "text": "When this setup has confluence with higher timeframe order flow, it is guaranteed to work then take the trade.",
            },
        ],
    }
