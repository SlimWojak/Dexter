"""Supadata transcript API wrapper.

Phase 3: Stub with mock data for testing.
Phase 5: Real API integration.
"""

from __future__ import annotations

import os
from typing import Dict, List

SUPADATA_API_KEY = os.getenv("SUPADATA_API_KEY")


def fetch_transcript(video_url: str) -> Dict:
    """Fetch transcript from Supadata API.

    Returns: {"video_id": str, "title": str, "segments": [{"start": float, "text": str}]}
    """
    if "mock" in video_url or not SUPADATA_API_KEY:
        return _mock_ict_transcript()

    # Phase 5: Real API call
    raise NotImplementedError("Real Supadata integration in Phase 5")


def _mock_ict_transcript() -> Dict:
    """Mock ICT-style transcript for loop testing.

    Contains patterns that should trigger both extractions AND rejections:
    - Explicit if-then statements (extractable)
    - Absolute claims ("always") that Auditor should reject
    - Clean conditions that should pass audit
    """
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


def format_for_theorist(transcript: Dict) -> str:
    """Format transcript segments for Theorist input."""
    lines = [
        f"[{seg['start']:.1f}s] {seg['text']}"
        for seg in transcript.get("segments", [])
    ]
    return f"VIDEO: {transcript.get('title', 'unknown')}\n\n" + "\n".join(lines)
