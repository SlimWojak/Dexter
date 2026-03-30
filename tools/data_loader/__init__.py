"""data_loader — Load RiverWriter 1m parquet data and aggregate to higher timeframes.

Usage:
    from tools.data_loader import load_pair, load_pair_tf, list_pairs, available_range

    # Load raw 1-minute bars
    df = load_pair("EURUSD")
    df = load_pair("EURUSD", start="2024-01-01", end="2024-12-31")

    # Load aggregated timeframe
    df_15m = load_pair_tf("EURUSD", "15m")
    df_4h  = load_pair_tf("EURUSD", "4h", start="2024-06-01")

    # Discovery
    pairs = list_pairs()
    info = available_range("EURUSD")
"""

from tools.data_loader.loader import (
    available_range,
    list_pairs,
    load_pair,
    load_pair_tf,
    SUPPORTED_TIMEFRAMES,
)

__all__ = [
    "load_pair",
    "load_pair_tf",
    "list_pairs",
    "available_range",
    "SUPPORTED_TIMEFRAMES",
]
