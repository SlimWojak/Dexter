"""
Structure Detector — ICT Market Structure Detection
====================================================

Converts River bars into detected market structures.
Implements: FVG, BOS, CHoCH, OTE, Liquidity Sweep

INVARIANT: INV-STRUCTURE-DET-1 "Deterministic detection"
Same bars → same output (no randomness)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import pandas as pd  # type: ignore[import-untyped]  # pandas has no py.typed

# =============================================================================
# ENUMS
# =============================================================================


class Direction(str, Enum):
    """Market direction."""

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class StructureType(str, Enum):
    """ICT structure types."""

    FVG = "FVG"
    BOS = "BOS"
    CHOCH = "CHoCH"
    OTE = "OTE"
    LIQUIDITY_SWEEP = "LIQUIDITY_SWEEP"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class FVG:
    """Fair Value Gap structure."""

    direction: Direction
    gap_high: float
    gap_low: float
    gap_size_pips: float
    fill_percent: float
    age_bars: int
    candle_indices: list[int]
    detected_at_time: datetime
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "structure_type": "FVG",
            "direction": self.direction.value,
            "gap_high": self.gap_high,
            "gap_low": self.gap_low,
            "gap_size_pips": self.gap_size_pips,
            "fill_percent": self.fill_percent,
            "age_bars": self.age_bars,
            "candle_indices": self.candle_indices,
            "detected_at_time": self.detected_at_time.isoformat(),
            "confidence": self.confidence,
        }


@dataclass
class BOS:
    """Break of Structure."""

    direction: Direction
    swing_level: float
    break_candle_index: int
    break_strength: float
    confirmation_bars: int
    detected_at_time: datetime
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "structure_type": "BOS",
            "direction": self.direction.value,
            "swing_level": self.swing_level,
            "break_candle_index": self.break_candle_index,
            "break_strength": self.break_strength,
            "confirmation_bars": self.confirmation_bars,
            "detected_at_time": self.detected_at_time.isoformat(),
            "confidence": self.confidence,
        }


@dataclass
class CHoCH:
    """Change of Character."""

    direction: Direction
    prior_trend: Direction
    reversal_level: float
    reversal_strength: float
    candle_index: int
    detected_at_time: datetime
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "structure_type": "CHoCH",
            "direction": self.direction.value,
            "prior_trend": self.prior_trend.value,
            "reversal_level": self.reversal_level,
            "reversal_strength": self.reversal_strength,
            "candle_index": self.candle_index,
            "detected_at_time": self.detected_at_time.isoformat(),
            "confidence": self.confidence,
        }


@dataclass
class OTE:
    """Optimal Trade Entry zone."""

    direction: Direction
    range_high: float
    range_low: float
    ote_high: float
    ote_low: float
    current_in_zone: bool
    related_bos_index: int
    detected_at_time: datetime
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "structure_type": "OTE",
            "direction": self.direction.value,
            "range_high": self.range_high,
            "range_low": self.range_low,
            "ote_high": self.ote_high,
            "ote_low": self.ote_low,
            "current_in_zone": self.current_in_zone,
            "related_bos_index": self.related_bos_index,
            "detected_at_time": self.detected_at_time.isoformat(),
            "confidence": self.confidence,
        }


@dataclass
class LiquiditySweep:
    """Liquidity Sweep structure."""

    direction: Direction
    level_swept: float
    sweep_depth_pips: float
    sweep_candle_index: int
    close_respected: bool
    detected_at_time: datetime
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "structure_type": "LIQUIDITY_SWEEP",
            "direction": self.direction.value,
            "level_swept": self.level_swept,
            "sweep_depth_pips": self.sweep_depth_pips,
            "sweep_candle_index": self.sweep_candle_index,
            "close_respected": self.close_respected,
            "detected_at_time": self.detected_at_time.isoformat(),
            "confidence": self.confidence,
        }


@dataclass
class StructureOutput:
    """Output from structure detection."""

    pair: str
    timeframe: str
    analysis_timestamp: datetime
    bars_analyzed: int
    structures: list[FVG | BOS | CHoCH | OTE | LiquiditySweep]
    htf_bias: Direction
    swing_highs: list[float] = field(default_factory=list)
    swing_lows: list[float] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pair": self.pair,
            "timeframe": self.timeframe,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "bars_analyzed": self.bars_analyzed,
            "structures": [s.to_dict() for s in self.structures],
            "htf_bias": self.htf_bias.value,
        }


# =============================================================================
# STRUCTURE DETECTOR
# =============================================================================


class StructureDetector:
    """
    Detects ICT market structures from price bars.

    INVARIANT: INV-STRUCTURE-DET-1
    Deterministic: same bars → same output
    """

    def __init__(self, pip_value: float = 0.0001) -> None:
        """
        Initialize detector.

        Args:
            pip_value: Pip value for the pair (0.0001 for most, 0.01 for JPY)
        """
        self._pip_value = pip_value

    def detect_all(
        self,
        bars: pd.DataFrame,
        pair: str,
        timeframe: str,
    ) -> StructureOutput:
        """
        Detect all structures in bars.

        Args:
            bars: DataFrame with columns [timestamp, open, high, low, close, volume]
            pair: Currency pair
            timeframe: Timeframe string

        Returns:
            StructureOutput with all detected structures
        """
        if bars.empty:
            return StructureOutput(
                pair=pair,
                timeframe=timeframe,
                analysis_timestamp=datetime.now(UTC),
                bars_analyzed=0,
                structures=[],
                htf_bias=Direction.NEUTRAL,
            )

        structures: list[FVG | BOS | CHoCH | OTE | LiquiditySweep] = []

        # Detect swing points first (needed for BOS, CHoCH)
        swing_highs, swing_lows = self._detect_swing_points(bars)

        # Detect each structure type
        fvgs = self.detect_fvg(bars)
        structures.extend(fvgs)

        bos_list = self.detect_bos(bars, swing_highs, swing_lows)
        structures.extend(bos_list)

        choch_list = self.detect_choch(bars, swing_highs, swing_lows)
        structures.extend(choch_list)

        # OTE zones from recent BOS
        for bos in bos_list[-3:]:  # Last 3 BOS
            ote = self.detect_ote(bars, bos)
            if ote:
                structures.append(ote)

        sweeps = self.detect_liquidity_sweep(bars, swing_highs, swing_lows)
        structures.extend(sweeps)

        # Determine HTF bias from structure
        htf_bias = self._determine_bias(bos_list, choch_list)

        return StructureOutput(
            pair=pair,
            timeframe=timeframe,
            analysis_timestamp=datetime.now(UTC),
            bars_analyzed=len(bars),
            structures=structures,
            htf_bias=htf_bias,
            swing_highs=swing_highs,
            swing_lows=swing_lows,
        )

    def detect_fvg(self, bars: pd.DataFrame) -> list[FVG]:
        """
        Detect Fair Value Gaps.

        FVG Definition:
        - Bullish: bar[n].low > bar[n-2].high (gap above)
        - Bearish: bar[n].high < bar[n-2].low (gap below)
        """
        fvgs: list[FVG] = []

        if len(bars) < 3:
            return fvgs

        for i in range(2, len(bars)):
            bar_0 = bars.iloc[i - 2]  # First candle
            bar_2 = bars.iloc[i]  # Third candle
            timestamp = self._get_timestamp(bars, i)

            # Bullish FVG: gap above
            if bar_2["low"] > bar_0["high"]:
                gap_high = bar_2["low"]
                gap_low = bar_0["high"]
                gap_size = (gap_high - gap_low) / self._pip_value

                # Check fill (has price come back into gap?)
                fill_percent = self._calculate_fvg_fill(bars, i, gap_high, gap_low)

                fvgs.append(
                    FVG(
                        direction=Direction.BULLISH,
                        gap_high=gap_high,
                        gap_low=gap_low,
                        gap_size_pips=gap_size,
                        fill_percent=fill_percent,
                        age_bars=len(bars) - i - 1,
                        candle_indices=[i - 2, i - 1, i],
                        detected_at_time=timestamp,
                    )
                )

            # Bearish FVG: gap below
            elif bar_2["high"] < bar_0["low"]:
                gap_high = bar_0["low"]
                gap_low = bar_2["high"]
                gap_size = (gap_high - gap_low) / self._pip_value

                fill_percent = self._calculate_fvg_fill(bars, i, gap_high, gap_low)

                fvgs.append(
                    FVG(
                        direction=Direction.BEARISH,
                        gap_high=gap_high,
                        gap_low=gap_low,
                        gap_size_pips=gap_size,
                        fill_percent=fill_percent,
                        age_bars=len(bars) - i - 1,
                        candle_indices=[i - 2, i - 1, i],
                        detected_at_time=timestamp,
                    )
                )

        return fvgs

    def detect_bos(
        self,
        bars: pd.DataFrame,
        swing_highs: list[float],
        swing_lows: list[float],
    ) -> list[BOS]:
        """
        Detect Break of Structure.

        BOS Definition:
        - Bullish: Close above previous swing high
        - Bearish: Close below previous swing low
        """
        bos_list: list[BOS] = []

        if len(bars) < 5 or not swing_highs or not swing_lows:
            return bos_list

        # Track highest/lowest seen
        highest_swing = max(swing_highs) if swing_highs else bars["high"].max()
        lowest_swing = min(swing_lows) if swing_lows else bars["low"].min()

        for i in range(4, len(bars)):
            bar = bars.iloc[i]
            timestamp = self._get_timestamp(bars, i)

            # Bullish BOS: close above swing high
            if bar["close"] > highest_swing:
                break_strength = (bar["close"] - highest_swing) / self._pip_value
                bos_list.append(
                    BOS(
                        direction=Direction.BULLISH,
                        swing_level=highest_swing,
                        break_candle_index=i,
                        break_strength=break_strength,
                        confirmation_bars=len(bars) - i - 1,
                        detected_at_time=timestamp,
                    )
                )
                highest_swing = bar["high"]  # Update for next iteration

            # Bearish BOS: close below swing low
            elif bar["close"] < lowest_swing:
                break_strength = (lowest_swing - bar["close"]) / self._pip_value
                bos_list.append(
                    BOS(
                        direction=Direction.BEARISH,
                        swing_level=lowest_swing,
                        break_candle_index=i,
                        break_strength=break_strength,
                        confirmation_bars=len(bars) - i - 1,
                        detected_at_time=timestamp,
                    )
                )
                lowest_swing = bar["low"]

        return bos_list

    def detect_choch(
        self,
        bars: pd.DataFrame,
        swing_highs: list[float],
        swing_lows: list[float],
    ) -> list[CHoCH]:
        """
        Detect Change of Character.

        CHoCH Definition:
        BOS in opposite direction to prior trend.
        """
        choch_list: list[CHoCH] = []

        # First detect BOS
        bos_list = self.detect_bos(bars, swing_highs, swing_lows)

        if len(bos_list) < 2:
            return choch_list

        # Look for direction changes
        for i in range(1, len(bos_list)):
            prev_bos = bos_list[i - 1]
            curr_bos = bos_list[i]

            if prev_bos.direction != curr_bos.direction:
                choch_list.append(
                    CHoCH(
                        direction=curr_bos.direction,
                        prior_trend=prev_bos.direction,
                        reversal_level=curr_bos.swing_level,
                        reversal_strength=curr_bos.break_strength,
                        candle_index=curr_bos.break_candle_index,
                        detected_at_time=curr_bos.detected_at_time,
                    )
                )

        return choch_list

    def detect_ote(self, bars: pd.DataFrame, bos: BOS) -> OTE | None:
        """
        Detect OTE zone after BOS.

        OTE Definition:
        Price in 0.62-0.79 Fibonacci zone of range after BOS.
        """
        if bos.break_candle_index >= len(bars) - 1:
            return None

        # Get range from BOS to current
        range_bars = bars.iloc[bos.break_candle_index :]
        if len(range_bars) < 2:
            return None

        range_high = range_bars["high"].max()
        range_low = range_bars["low"].min()
        range_size = range_high - range_low

        if range_size < self._pip_value * 10:  # Min 10 pips
            return None

        # Calculate OTE zone (0.62-0.79 fib)
        if bos.direction == Direction.BULLISH:
            # Bullish: OTE is below current price
            ote_high = range_high - (range_size * 0.62)
            ote_low = range_high - (range_size * 0.79)
        else:
            # Bearish: OTE is above current price
            ote_low = range_low + (range_size * 0.62)
            ote_high = range_low + (range_size * 0.79)

        current_price = bars.iloc[-1]["close"]
        in_zone = ote_low <= current_price <= ote_high

        return OTE(
            direction=bos.direction,
            range_high=range_high,
            range_low=range_low,
            ote_high=ote_high,
            ote_low=ote_low,
            current_in_zone=in_zone,
            related_bos_index=bos.break_candle_index,
            detected_at_time=self._get_timestamp(bars, len(bars) - 1),
        )

    def detect_liquidity_sweep(
        self,
        bars: pd.DataFrame,
        swing_highs: list[float],
        swing_lows: list[float],
    ) -> list[LiquiditySweep]:
        """
        Detect Liquidity Sweeps.

        Sweep Definition:
        Wick pierces beyond equal highs/lows, but close respects level.
        """
        sweeps: list[LiquiditySweep] = []

        if len(bars) < 5:
            return sweeps

        for i in range(4, len(bars)):
            bar = bars.iloc[i]
            timestamp = self._get_timestamp(bars, i)

            # Check for sweep of recent highs
            for level in swing_highs[-3:]:  # Last 3 swing highs
                if bar["high"] > level and bar["close"] < level:
                    sweep_depth = (bar["high"] - level) / self._pip_value
                    if sweep_depth > 2:  # Min 2 pips sweep
                        sweeps.append(
                            LiquiditySweep(
                                direction=Direction.BEARISH,  # Expect down after sweep
                                level_swept=level,
                                sweep_depth_pips=sweep_depth,
                                sweep_candle_index=i,
                                close_respected=True,
                                detected_at_time=timestamp,
                            )
                        )

            # Check for sweep of recent lows
            for level in swing_lows[-3:]:
                if bar["low"] < level and bar["close"] > level:
                    sweep_depth = (level - bar["low"]) / self._pip_value
                    if sweep_depth > 2:
                        sweeps.append(
                            LiquiditySweep(
                                direction=Direction.BULLISH,
                                level_swept=level,
                                sweep_depth_pips=sweep_depth,
                                sweep_candle_index=i,
                                close_respected=True,
                                detected_at_time=timestamp,
                            )
                        )

        return sweeps

    def _detect_swing_points(
        self,
        bars: pd.DataFrame,
        lookback: int = 3,
    ) -> tuple[list[float], list[float]]:
        """Detect swing highs and lows."""
        swing_highs: list[float] = []
        swing_lows: list[float] = []

        if len(bars) < lookback * 2 + 1:
            return swing_highs, swing_lows

        for i in range(lookback, len(bars) - lookback):
            # Check for swing high
            is_high = True
            for j in range(1, lookback + 1):
                if bars.iloc[i]["high"] <= bars.iloc[i - j]["high"]:
                    is_high = False
                    break
                if bars.iloc[i]["high"] <= bars.iloc[i + j]["high"]:
                    is_high = False
                    break
            if is_high:
                swing_highs.append(bars.iloc[i]["high"])

            # Check for swing low
            is_low = True
            for j in range(1, lookback + 1):
                if bars.iloc[i]["low"] >= bars.iloc[i - j]["low"]:
                    is_low = False
                    break
                if bars.iloc[i]["low"] >= bars.iloc[i + j]["low"]:
                    is_low = False
                    break
            if is_low:
                swing_lows.append(bars.iloc[i]["low"])

        return swing_highs, swing_lows

    def _calculate_fvg_fill(
        self,
        bars: pd.DataFrame,
        fvg_index: int,
        gap_high: float,
        gap_low: float,
    ) -> float:
        """Calculate how much of FVG has been filled."""
        if fvg_index >= len(bars) - 1:
            return 0.0

        subsequent_bars = bars.iloc[fvg_index + 1 :]
        if subsequent_bars.empty:
            return 0.0

        gap_size = gap_high - gap_low
        if gap_size <= 0:
            return 0.0

        # Check how much price has come back into gap
        max_intrusion = 0.0
        for _, bar in subsequent_bars.iterrows():
            if bar["low"] < gap_high and bar["high"] > gap_low:
                intrusion = min(gap_high, bar["high"]) - max(gap_low, bar["low"])
                max_intrusion = max(max_intrusion, intrusion)

        return min(1.0, max_intrusion / gap_size)

    def _determine_bias(
        self,
        bos_list: list[BOS],
        choch_list: list[CHoCH],
    ) -> Direction:
        """Determine HTF bias from structures."""
        if not bos_list:
            return Direction.NEUTRAL

        # Recent BOS determines bias
        recent_bos = bos_list[-1]

        # But if there's a recent CHoCH, that takes precedence
        if choch_list:
            recent_choch = choch_list[-1]
            # CHoCH within last 10 bars of most recent BOS
            if abs(recent_choch.candle_index - recent_bos.break_candle_index) < 10:
                return recent_choch.direction

        return recent_bos.direction

    def _get_timestamp(self, bars: pd.DataFrame, index: int) -> datetime:
        """Get timestamp from bars at index."""
        ts = bars.iloc[index].get("timestamp")
        if ts is None:
            return datetime.now(UTC)
        if isinstance(ts, str):
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if isinstance(ts, datetime):
            return ts
        return datetime.now(UTC)
