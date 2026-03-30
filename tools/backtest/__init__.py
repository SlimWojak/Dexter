"""backtest — Walk-forward validation harness.

Enforces mandatory train/validation split:
    Train:    2021-01-01 to 2024-12-31
    Validate: 2025-01-01 to current

INV-WALK-FORWARD-MANDATORY: Every quantitative claim needs walk-forward validation.

Usage:
    from tools.backtest import WalkForwardHarness

    harness = WalkForwardHarness()
    result = harness.run(
        strategy_fn=my_strategy,
        pair="EURUSD",
        timeframe="15m",
    )
    print(result.summary())
"""

from tools.backtest.harness import WalkForwardHarness, BacktestResult

__all__ = ["WalkForwardHarness", "BacktestResult"]
