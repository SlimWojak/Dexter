"""Runaway Guards — P6 implementation.

Prevents token burn, infinite loops, and stalled agents.

Guards:
- Turn cap: Hard limit on agent loop iterations
- Cost ceiling: Daily/session spend limits
- Stall watchdog: Halt on no-output timeout

INV-RUNAWAY-CAP: Agent loops hard-capped at N turns. No-output > X min → halt.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

import yaml

logger = logging.getLogger("dexter.guards")

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "guards.yaml"
COST_LOG_PATH = Path(__file__).resolve().parent.parent / "memory" / "cost_log.jsonl"


def _load_config() -> Dict:
    """Load guards configuration."""
    if not CONFIG_PATH.exists():
        logger.warning("Guards config not found at %s, using defaults.", CONFIG_PATH)
        return _default_config()
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f) or _default_config()


def _default_config() -> Dict:
    """Default guard configuration."""
    return {
        "runaway_guards": {
            "enabled": True,
            "turn_cap": {
                "enabled": True,
                "max_turns": 20,
                "warn_at": 15,
                "action": "halt",
            },
            "cost_ceiling": {
                "enabled": True,
                "daily_limit_usd": 1.00,
                "session_limit_usd": 0.50,
                "action": "halt",
                "reset_hour_utc": 0,
            },
            "stall_watchdog": {
                "enabled": True,
                "timeout_minutes": 5,
                "check_interval_seconds": 30,
                "action": "halt",
            },
        },
        "alerts": {
            "log_every_turn": True,
            "log_cost_per_call": True,
            "warn_threshold_turns": 0.75,
            "warn_threshold_cost": 0.80,
        },
    }


# ---------------------------------------------------------------------------
# Turn Cap Guard
# ---------------------------------------------------------------------------

class TurnCapGuard:
    """Tracks and enforces turn limits per agent loop.

    Usage:
        guard = TurnCapGuard(max_turns=20)
        while guard.can_continue():
            # do work
            guard.increment()
    """

    def __init__(self, max_turns: int = 20, warn_at: int = 15, action: str = "halt"):
        self.max_turns = max_turns
        self.warn_at = warn_at
        self.action = action
        self.current_turn = 0
        self._halted = False

    def increment(self) -> int:
        """Increment turn counter. Returns new count."""
        self.current_turn += 1
        logger.info("[GUARD] Turn %d/%d", self.current_turn, self.max_turns)

        if self.current_turn >= self.warn_at:
            logger.warning(
                "[GUARD] Approaching turn cap: %d/%d (%.0f%%)",
                self.current_turn, self.max_turns,
                (self.current_turn / self.max_turns) * 100,
            )

        if self.current_turn >= self.max_turns:
            if self.action == "halt":
                logger.error(
                    "[GUARD] TURN CAP REACHED: %d turns. Halting.",
                    self.max_turns,
                )
                self._halted = True
            else:
                logger.warning(
                    "[GUARD] TURN CAP REACHED: %d turns. Continuing (action=%s).",
                    self.max_turns, self.action,
                )
                # Note: _halted stays False for warn_and_continue

        return self.current_turn

    def can_continue(self) -> bool:
        """Check if loop can continue."""
        if self._halted:
            return False
        # For "halt" action, we halt at max. For "warn_and_continue", we continue.
        if self.action != "halt":
            return True  # Warn mode always continues
        return self.current_turn < self.max_turns

    def reset(self) -> None:
        """Reset turn counter."""
        self.current_turn = 0
        self._halted = False

    def status(self) -> Dict:
        """Return current status."""
        return {
            "current_turn": self.current_turn,
            "max_turns": self.max_turns,
            "remaining": max(0, self.max_turns - self.current_turn),
            "halted": self._halted,
            "pct_used": round((self.current_turn / self.max_turns) * 100, 1) if self.max_turns > 0 else 0,
        }


# ---------------------------------------------------------------------------
# Cost Ceiling Guard
# ---------------------------------------------------------------------------

class CostCeilingGuard:
    """Tracks and enforces cost limits (daily and session).

    Usage:
        guard = CostCeilingGuard(daily_limit=1.0, session_limit=0.5)
        guard.add_cost(0.001)  # After each LLM call
        if guard.is_exceeded():
            break
    """

    def __init__(
        self,
        daily_limit_usd: float = 1.00,
        session_limit_usd: float = 0.50,
        action: str = "halt",
    ):
        self.daily_limit = daily_limit_usd
        self.session_limit = session_limit_usd
        self.action = action
        self.session_cost = 0.0
        self.daily_cost = self._load_daily_cost()
        self._halted = False
        self._session_start = datetime.now(timezone.utc)

    def _load_daily_cost(self) -> float:
        """Load accumulated daily cost from log file."""
        if not COST_LOG_PATH.exists():
            return 0.0

        today = datetime.now(timezone.utc).date()
        daily_total = 0.0

        try:
            import json
            with open(COST_LOG_PATH) as f:
                for line in f:
                    if not line.strip():
                        continue
                    entry = json.loads(line)
                    entry_date = datetime.fromisoformat(entry.get("timestamp", "")).date()
                    if entry_date == today:
                        daily_total += entry.get("cost_usd", 0.0)
        except Exception as e:
            logger.warning("Failed to load daily cost: %s", e)
            return 0.0

        return daily_total

    def _log_cost(self, cost: float, model: str = "unknown") -> None:
        """Append cost entry to log file."""
        import json
        COST_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cost_usd": cost,
            "model": model,
            "session_total": self.session_cost,
            "daily_total": self.daily_cost,
        }
        with open(COST_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def add_cost(self, cost_usd: float, model: str = "unknown") -> None:
        """Record a cost expenditure."""
        self.session_cost += cost_usd
        self.daily_cost += cost_usd

        logger.info(
            "[COST] +$%.6f | session=$%.4f/%s | daily=$%.4f/%s",
            cost_usd,
            self.session_cost, self.session_limit,
            self.daily_cost, self.daily_limit,
        )

        self._log_cost(cost_usd, model)

        # Check limits
        if self.session_cost >= self.session_limit:
            if self.action == "halt":
                logger.error(
                    "[GUARD] SESSION COST CEILING: $%.4f >= $%.4f. Halting.",
                    self.session_cost, self.session_limit,
                )
                self._halted = True
            else:
                logger.warning(
                    "[GUARD] SESSION COST CEILING: $%.4f >= $%.4f. Continuing.",
                    self.session_cost, self.session_limit,
                )

        if self.daily_cost >= self.daily_limit:
            if self.action == "halt":
                logger.error(
                    "[GUARD] DAILY COST CEILING: $%.4f >= $%.4f. Halting.",
                    self.daily_cost, self.daily_limit,
                )
                self._halted = True
            else:
                logger.warning(
                    "[GUARD] DAILY COST CEILING: $%.4f >= $%.4f. Continuing.",
                    self.daily_cost, self.daily_limit,
                )

    def is_exceeded(self) -> bool:
        """Check if any cost limit is exceeded."""
        return self._halted

    def can_continue(self) -> bool:
        """Check if loop can continue within cost limits."""
        return not self._halted

    def status(self) -> Dict:
        """Return current cost status."""
        return {
            "session_cost": round(self.session_cost, 6),
            "session_limit": self.session_limit,
            "session_remaining": round(max(0, self.session_limit - self.session_cost), 6),
            "daily_cost": round(self.daily_cost, 6),
            "daily_limit": self.daily_limit,
            "daily_remaining": round(max(0, self.daily_limit - self.daily_cost), 6),
            "halted": self._halted,
        }


# ---------------------------------------------------------------------------
# Stall Watchdog Guard
# ---------------------------------------------------------------------------

class StallWatchdogGuard:
    """Detects and halts on stalled agent loops (no output for X minutes).

    Usage:
        guard = StallWatchdogGuard(timeout_minutes=5)
        while running:
            guard.heartbeat()  # Call after each meaningful output
            if guard.is_stalled():
                break
    """

    def __init__(self, timeout_minutes: float = 5.0, action: str = "halt"):
        self.timeout_seconds = timeout_minutes * 60
        self.action = action
        self.last_activity = time.monotonic()
        self._halted = False

    def heartbeat(self) -> None:
        """Record activity timestamp."""
        self.last_activity = time.monotonic()
        logger.debug("[WATCHDOG] Heartbeat recorded")

    def check(self) -> bool:
        """Check for stall condition. Returns True if stalled."""
        elapsed = time.monotonic() - self.last_activity
        if elapsed >= self.timeout_seconds:
            if self.action == "halt":
                logger.error(
                    "[GUARD] STALL DETECTED: No activity for %.1f minutes. Halting.",
                    elapsed / 60,
                )
                self._halted = True
            else:
                logger.warning(
                    "[GUARD] STALL DETECTED: No activity for %.1f minutes. Continuing.",
                    elapsed / 60,
                )
            return True
        return False

    def is_stalled(self) -> bool:
        """Check stall status (runs check internally)."""
        self.check()
        return self._halted

    def can_continue(self) -> bool:
        """Check if loop can continue (not stalled)."""
        return not self.is_stalled()

    def status(self) -> Dict:
        """Return current watchdog status."""
        elapsed = time.monotonic() - self.last_activity
        return {
            "seconds_since_activity": round(elapsed, 1),
            "timeout_seconds": self.timeout_seconds,
            "remaining_seconds": round(max(0, self.timeout_seconds - elapsed), 1),
            "halted": self._halted,
        }


# ---------------------------------------------------------------------------
# Combined Guard Manager
# ---------------------------------------------------------------------------

class GuardManager:
    """Manages all runaway guards in a unified interface.

    Usage:
        guards = GuardManager.from_config()
        while guards.can_continue():
            # Do work
            guards.on_turn()
            guards.on_cost(0.001)
            guards.on_output()
    """

    def __init__(
        self,
        turn_cap: Optional[TurnCapGuard] = None,
        cost_ceiling: Optional[CostCeilingGuard] = None,
        stall_watchdog: Optional[StallWatchdogGuard] = None,
    ):
        self.turn_cap = turn_cap
        self.cost_ceiling = cost_ceiling
        self.stall_watchdog = stall_watchdog

    @classmethod
    def from_config(cls, config_path: Optional[Path] = None) -> "GuardManager":
        """Create GuardManager from configuration file."""
        if config_path:
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
        else:
            config = _load_config()

        guards_cfg = config.get("runaway_guards", {})
        if not guards_cfg.get("enabled", True):
            logger.info("[GUARD] Guards disabled in config")
            return cls()

        turn_cap = None
        cost_ceiling = None
        stall_watchdog = None

        # Turn cap
        tc_cfg = guards_cfg.get("turn_cap", {})
        if tc_cfg.get("enabled", True):
            turn_cap = TurnCapGuard(
                max_turns=tc_cfg.get("max_turns", 20),
                warn_at=tc_cfg.get("warn_at", 15),
                action=tc_cfg.get("action", "halt"),
            )

        # Cost ceiling
        cc_cfg = guards_cfg.get("cost_ceiling", {})
        if cc_cfg.get("enabled", True):
            cost_ceiling = CostCeilingGuard(
                daily_limit_usd=cc_cfg.get("daily_limit_usd", 1.00),
                session_limit_usd=cc_cfg.get("session_limit_usd", 0.50),
                action=cc_cfg.get("action", "halt"),
            )

        # Stall watchdog
        sw_cfg = guards_cfg.get("stall_watchdog", {})
        if sw_cfg.get("enabled", True):
            stall_watchdog = StallWatchdogGuard(
                timeout_minutes=sw_cfg.get("timeout_minutes", 5.0),
                action=sw_cfg.get("action", "halt"),
            )

        logger.info(
            "[GUARD] Guards initialized: turn_cap=%s, cost=%s, watchdog=%s",
            turn_cap is not None,
            cost_ceiling is not None,
            stall_watchdog is not None,
        )

        return cls(turn_cap, cost_ceiling, stall_watchdog)

    def on_turn(self) -> None:
        """Record a turn (call at start of each loop iteration)."""
        if self.turn_cap:
            self.turn_cap.increment()
        if self.stall_watchdog:
            self.stall_watchdog.heartbeat()

    def on_cost(self, cost_usd: float, model: str = "unknown") -> None:
        """Record a cost expenditure."""
        if self.cost_ceiling:
            self.cost_ceiling.add_cost(cost_usd, model)
        if self.stall_watchdog:
            self.stall_watchdog.heartbeat()

    def on_output(self) -> None:
        """Record meaningful output (resets stall timer)."""
        if self.stall_watchdog:
            self.stall_watchdog.heartbeat()

    def can_continue(self) -> bool:
        """Check if all guards allow continuation."""
        if self.turn_cap and not self.turn_cap.can_continue():
            return False
        if self.cost_ceiling and not self.cost_ceiling.can_continue():
            return False
        if self.stall_watchdog and not self.stall_watchdog.can_continue():
            return False
        return True

    def status(self) -> Dict:
        """Return combined status of all guards."""
        return {
            "can_continue": self.can_continue(),
            "turn_cap": self.turn_cap.status() if self.turn_cap else None,
            "cost_ceiling": self.cost_ceiling.status() if self.cost_ceiling else None,
            "stall_watchdog": self.stall_watchdog.status() if self.stall_watchdog else None,
        }
