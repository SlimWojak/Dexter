"""Walk-forward validation harness with mandatory train/val split.

Enforces INV-WALK-FORWARD-MANDATORY and INV-NO-PARAM-HUNTING.

The harness splits data into train and validation periods, runs a strategy
function on both, and reports metrics separately. The strategy function
should NOT be tuned to validation data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

import pandas as pd

from tools.data_loader import load_pair_tf

TRAIN_START = "2021-01-01"
TRAIN_END = "2024-12-31"
VALIDATION_START = "2025-01-01"


@dataclass
class TradeSignal:
    """A trade signal produced by a strategy."""
    timestamp: datetime
    direction: str  # "LONG" or "SHORT"
    entry_price: float
    stop_loss: float
    take_profit: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestMetrics:
    """Metrics for a single period (train or validation)."""
    period: str
    start_date: str
    end_date: str
    total_bars: int
    total_signals: int
    trades_won: int
    trades_lost: int
    win_rate: float
    avg_rr: float
    total_pips: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "period": self.period,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "total_bars": self.total_bars,
            "total_signals": self.total_signals,
            "trades_won": self.trades_won,
            "trades_lost": self.trades_lost,
            "win_rate": self.win_rate,
            "avg_rr": self.avg_rr,
            "total_pips": self.total_pips,
        }


@dataclass
class BacktestResult:
    """Result of a walk-forward backtest."""
    pair: str
    timeframe: str
    strategy_name: str
    train_metrics: BacktestMetrics
    validation_metrics: Optional[BacktestMetrics]
    walk_forward_pass: bool
    signals_train: list[TradeSignal] = field(default_factory=list)
    signals_validation: list[TradeSignal] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"=== Walk-Forward Result: {self.strategy_name} ===",
            f"Pair: {self.pair} | TF: {self.timeframe}",
            f"",
            f"TRAIN ({self.train_metrics.start_date} to {self.train_metrics.end_date}):",
            f"  Signals: {self.train_metrics.total_signals} | "
            f"Win Rate: {self.train_metrics.win_rate:.1%} | "
            f"Avg R:R: {self.train_metrics.avg_rr:.2f} | "
            f"Pips: {self.train_metrics.total_pips:.1f}",
        ]
        if self.validation_metrics:
            vm = self.validation_metrics
            lines.extend([
                f"",
                f"VALIDATION ({vm.start_date} to {vm.end_date}):",
                f"  Signals: {vm.total_signals} | "
                f"Win Rate: {vm.win_rate:.1%} | "
                f"Avg R:R: {vm.avg_rr:.2f} | "
                f"Pips: {vm.total_pips:.1f}",
            ])
        lines.append(f"")
        lines.append(f"Walk-Forward: {'PASS' if self.walk_forward_pass else 'FAIL'}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pair": self.pair,
            "timeframe": self.timeframe,
            "strategy_name": self.strategy_name,
            "train": self.train_metrics.to_dict(),
            "validation": self.validation_metrics.to_dict() if self.validation_metrics else None,
            "walk_forward_pass": self.walk_forward_pass,
        }


# Strategy function signature:
#   def strategy(bars: pd.DataFrame, pair: str, timeframe: str) -> list[TradeSignal]
StrategyFn = Callable[[pd.DataFrame, str, str], list[TradeSignal]]


class WalkForwardHarness:
    """Walk-forward validation harness.

    Enforces train/validation split. The strategy function receives bars
    and returns trade signals. The harness evaluates signals mechanically.
    """

    def __init__(
        self,
        train_start: str = TRAIN_START,
        train_end: str = TRAIN_END,
        validation_start: str = VALIDATION_START,
        pip_value: float = 0.0001,
    ):
        self.train_start = train_start
        self.train_end = train_end
        self.validation_start = validation_start
        self.pip_value = pip_value

    def run(
        self,
        strategy_fn: StrategyFn,
        pair: str,
        timeframe: str = "15m",
        strategy_name: str = "unnamed",
        min_validation_signals: int = 5,
    ) -> BacktestResult:
        """Run walk-forward validation.

        Args:
            strategy_fn: Function that takes (bars, pair, tf) -> list[TradeSignal]
            pair: Currency pair
            timeframe: Timeframe
            strategy_name: Name for logging
            min_validation_signals: Minimum validation signals for a PASS
        """
        pair = pair.upper()
        if pair == "USDJPY":
            self.pip_value = 0.01

        # Load train data
        try:
            train_bars = load_pair_tf(pair, timeframe, start=self.train_start, end=self.train_end)
        except FileNotFoundError:
            train_bars = pd.DataFrame()

        # Load validation data
        try:
            val_bars = load_pair_tf(pair, timeframe, start=self.validation_start)
        except FileNotFoundError:
            val_bars = pd.DataFrame()

        # Run strategy on train
        train_signals = strategy_fn(train_bars, pair, timeframe) if not train_bars.empty else []
        train_metrics = self._evaluate_signals(
            train_signals, train_bars, "train", self.train_start, self.train_end
        )

        # Run strategy on validation
        val_signals = strategy_fn(val_bars, pair, timeframe) if not val_bars.empty else []
        val_metrics = self._evaluate_signals(
            val_signals, val_bars, "validation", self.validation_start, "current"
        ) if val_signals else None

        # Walk-forward pass criteria
        walk_forward_pass = (
            val_metrics is not None
            and val_metrics.total_signals >= min_validation_signals
            and val_metrics.win_rate >= train_metrics.win_rate * 0.7  # Allow 30% degradation
            and val_metrics.avg_rr >= train_metrics.avg_rr * 0.5  # Allow 50% RR degradation
        )

        return BacktestResult(
            pair=pair,
            timeframe=timeframe,
            strategy_name=strategy_name,
            train_metrics=train_metrics,
            validation_metrics=val_metrics,
            walk_forward_pass=walk_forward_pass,
            signals_train=train_signals,
            signals_validation=val_signals,
        )

    def _evaluate_signals(
        self,
        signals: list[TradeSignal],
        bars: pd.DataFrame,
        period: str,
        start_date: str,
        end_date: str,
    ) -> BacktestMetrics:
        """Mechanically evaluate trade signals against price data."""
        won = 0
        lost = 0
        total_pips = 0.0
        rr_values = []

        for signal in signals:
            result = self._evaluate_single_trade(signal, bars)
            if result is None:
                continue
            if result > 0:
                won += 1
            else:
                lost += 1
            total_pips += result
            sl_distance = abs(signal.entry_price - signal.stop_loss) / self.pip_value
            if sl_distance > 0:
                rr_values.append(result / sl_distance)

        total = won + lost
        return BacktestMetrics(
            period=period,
            start_date=start_date,
            end_date=end_date,
            total_bars=len(bars),
            total_signals=len(signals),
            trades_won=won,
            trades_lost=lost,
            win_rate=won / total if total > 0 else 0.0,
            avg_rr=sum(rr_values) / len(rr_values) if rr_values else 0.0,
            total_pips=total_pips,
        )

    def _evaluate_single_trade(
        self,
        signal: TradeSignal,
        bars: pd.DataFrame,
    ) -> Optional[float]:
        """Evaluate a single trade signal. Returns pips gained/lost or None."""
        if bars.empty:
            return None

        # Find bars after signal timestamp
        mask = bars["timestamp"] >= pd.Timestamp(signal.timestamp)
        subsequent = bars[mask]

        if subsequent.empty:
            return None

        for _, bar in subsequent.iterrows():
            if signal.direction == "LONG":
                if bar["low"] <= signal.stop_loss:
                    return -(signal.entry_price - signal.stop_loss) / self.pip_value
                if bar["high"] >= signal.take_profit:
                    return (signal.take_profit - signal.entry_price) / self.pip_value
            else:  # SHORT
                if bar["high"] >= signal.stop_loss:
                    return -(signal.stop_loss - signal.entry_price) / self.pip_value
                if bar["low"] <= signal.take_profit:
                    return (signal.entry_price - signal.take_profit) / self.pip_value

        return None  # Trade still open
