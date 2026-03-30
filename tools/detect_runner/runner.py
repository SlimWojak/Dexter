"""Detection runner — wires data_loader to structure_detector.

Loads market data from RiverWriter parquet files and runs ICT structure
detection using the vendored StructureDetector from Phoenix/en1gma.
"""

from __future__ import annotations

from typing import Optional

from tools.data_loader import load_pair_tf
from tools.detect_runner.structure_detector import StructureDetector, StructureOutput

PIP_VALUES = {
    "EURUSD": 0.0001,
    "GBPUSD": 0.0001,
    "AUDUSD": 0.0001,
    "USDCAD": 0.0001,
    "USDCHF": 0.0001,
    "USDJPY": 0.01,
}


def run_detection(
    pair: str,
    timeframe: str = "15m",
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> StructureOutput:
    """Run structure detection on a pair at a given timeframe.

    Args:
        pair: Currency pair (e.g. "EURUSD")
        timeframe: One of: 1m, 5m, 15m, 30m, 1h, 4h, 1d
        start: Start date filter (e.g. "2024-01-01")
        end: End date filter (e.g. "2024-12-31")

    Returns:
        StructureOutput with all detected structures
    """
    pair = pair.upper()
    pip_value = PIP_VALUES.get(pair, 0.0001)

    bars = load_pair_tf(pair, timeframe, start=start, end=end)
    detector = StructureDetector(pip_value=pip_value)
    return detector.detect_all(bars, pair, timeframe)


def run_multi_tf(
    pair: str,
    timeframes: list[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> dict[str, StructureOutput]:
    """Run detection across multiple timeframes for confluence analysis.

    Args:
        pair: Currency pair
        timeframes: List of timeframes (default: ["15m", "1h", "4h"])
        start: Start date filter
        end: End date filter

    Returns:
        Dict mapping timeframe -> StructureOutput
    """
    if timeframes is None:
        timeframes = ["15m", "1h", "4h"]

    results = {}
    for tf in timeframes:
        results[tf] = run_detection(pair, tf, start=start, end=end)
    return results
