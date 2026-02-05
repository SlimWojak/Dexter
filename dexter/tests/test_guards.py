"""Tests for Runaway Guards (P6).

Tests cover:
- Turn cap enforcement
- Cost ceiling tracking
- Stall watchdog detection
- Guard manager integration
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.guards import (
    TurnCapGuard,
    CostCeilingGuard,
    StallWatchdogGuard,
    GuardManager,
)


class TestTurnCapGuard(unittest.TestCase):
    """Turn cap enforcement tests."""

    def test_basic_counting(self):
        guard = TurnCapGuard(max_turns=5, warn_at=3)
        self.assertEqual(guard.current_turn, 0)
        guard.increment()
        self.assertEqual(guard.current_turn, 1)
        guard.increment()
        self.assertEqual(guard.current_turn, 2)

    def test_can_continue_before_cap(self):
        guard = TurnCapGuard(max_turns=3)
        self.assertTrue(guard.can_continue())
        guard.increment()
        self.assertTrue(guard.can_continue())
        guard.increment()
        self.assertTrue(guard.can_continue())

    def test_halt_at_cap(self):
        guard = TurnCapGuard(max_turns=3, action="halt")
        guard.increment()  # 1
        guard.increment()  # 2
        guard.increment()  # 3 - hits cap
        self.assertFalse(guard.can_continue())

    def test_warn_at_threshold(self):
        guard = TurnCapGuard(max_turns=10, warn_at=8)
        for _ in range(7):
            guard.increment()
        self.assertTrue(guard.can_continue())
        # Turn 8 should trigger warning (in logs)
        guard.increment()
        self.assertTrue(guard.can_continue())

    def test_reset(self):
        guard = TurnCapGuard(max_turns=3)
        guard.increment()
        guard.increment()
        guard.increment()
        self.assertFalse(guard.can_continue())
        guard.reset()
        self.assertTrue(guard.can_continue())
        self.assertEqual(guard.current_turn, 0)

    def test_status(self):
        guard = TurnCapGuard(max_turns=10)
        guard.increment()
        guard.increment()
        status = guard.status()
        self.assertEqual(status["current_turn"], 2)
        self.assertEqual(status["max_turns"], 10)
        self.assertEqual(status["remaining"], 8)
        self.assertFalse(status["halted"])

    def test_warn_and_continue_action(self):
        guard = TurnCapGuard(max_turns=2, action="warn_and_continue")
        guard.increment()
        guard.increment()  # Hits cap
        # With warn_and_continue, should NOT halt
        self.assertTrue(guard.can_continue())


class TestCostCeilingGuard(unittest.TestCase):
    """Cost ceiling tracking tests."""

    def setUp(self):
        # Use temp file for cost log to avoid polluting real data
        self.temp_dir = tempfile.mkdtemp()
        self.cost_log_path = Path(self.temp_dir) / "cost_log.jsonl"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_basic_cost_tracking(self):
        guard = CostCeilingGuard(daily_limit_usd=1.0, session_limit_usd=0.5)
        guard.session_cost = 0  # Reset
        guard.daily_cost = 0
        guard.add_cost(0.001)
        self.assertAlmostEqual(guard.session_cost, 0.001, places=6)

    def test_session_limit_halt(self):
        guard = CostCeilingGuard(session_limit_usd=0.01, daily_limit_usd=1.0, action="halt")
        guard.session_cost = 0
        guard.daily_cost = 0
        guard.add_cost(0.015)  # Exceeds session limit
        self.assertTrue(guard.is_exceeded())
        self.assertFalse(guard.can_continue())

    def test_daily_limit_halt(self):
        guard = CostCeilingGuard(session_limit_usd=1.0, daily_limit_usd=0.01, action="halt")
        guard.session_cost = 0
        guard.daily_cost = 0
        guard.add_cost(0.015)  # Exceeds daily limit
        self.assertTrue(guard.is_exceeded())

    def test_within_limits(self):
        guard = CostCeilingGuard(session_limit_usd=1.0, daily_limit_usd=10.0)
        guard.session_cost = 0
        guard.daily_cost = 0
        guard.add_cost(0.001)
        self.assertTrue(guard.can_continue())

    def test_status(self):
        guard = CostCeilingGuard(session_limit_usd=0.5, daily_limit_usd=1.0)
        guard.session_cost = 0.1
        guard.daily_cost = 0.2
        status = guard.status()
        self.assertAlmostEqual(status["session_cost"], 0.1, places=4)
        self.assertEqual(status["session_limit"], 0.5)
        self.assertAlmostEqual(status["session_remaining"], 0.4, places=4)


class TestStallWatchdogGuard(unittest.TestCase):
    """Stall watchdog tests."""

    def test_heartbeat_resets_timer(self):
        guard = StallWatchdogGuard(timeout_minutes=1)
        initial = guard.last_activity
        time.sleep(0.01)  # Small delay
        guard.heartbeat()
        self.assertGreater(guard.last_activity, initial)

    def test_no_stall_immediately(self):
        guard = StallWatchdogGuard(timeout_minutes=1)
        self.assertFalse(guard.is_stalled())
        self.assertTrue(guard.can_continue())

    def test_stall_detection(self):
        # Use very short timeout for testing
        guard = StallWatchdogGuard(timeout_minutes=0.001, action="halt")  # 0.06 seconds
        time.sleep(0.1)  # Wait longer than timeout
        self.assertTrue(guard.is_stalled())
        self.assertFalse(guard.can_continue())

    def test_status(self):
        guard = StallWatchdogGuard(timeout_minutes=5)
        guard.heartbeat()
        status = guard.status()
        self.assertIn("seconds_since_activity", status)
        self.assertEqual(status["timeout_seconds"], 300)
        self.assertFalse(status["halted"])


class TestGuardManager(unittest.TestCase):
    """Guard manager integration tests."""

    def test_from_config_defaults(self):
        manager = GuardManager.from_config()
        self.assertIsNotNone(manager.turn_cap)
        self.assertIsNotNone(manager.cost_ceiling)
        self.assertIsNotNone(manager.stall_watchdog)

    def test_can_continue_all_ok(self):
        manager = GuardManager(
            turn_cap=TurnCapGuard(max_turns=10),
            cost_ceiling=CostCeilingGuard(session_limit_usd=1.0),
            stall_watchdog=StallWatchdogGuard(timeout_minutes=5),
        )
        self.assertTrue(manager.can_continue())

    def test_halt_on_turn_cap(self):
        manager = GuardManager(
            turn_cap=TurnCapGuard(max_turns=2),
        )
        manager.on_turn()  # 1
        manager.on_turn()  # 2 - hits cap
        self.assertFalse(manager.can_continue())

    def test_on_cost_tracks(self):
        guard = CostCeilingGuard(session_limit_usd=1.0, daily_limit_usd=10.0)
        guard.session_cost = 0
        guard.daily_cost = 0
        manager = GuardManager(cost_ceiling=guard)
        manager.on_cost(0.01, model="test")
        self.assertAlmostEqual(guard.session_cost, 0.01, places=4)

    def test_on_output_resets_watchdog(self):
        watchdog = StallWatchdogGuard(timeout_minutes=1)
        manager = GuardManager(stall_watchdog=watchdog)
        initial = watchdog.last_activity
        time.sleep(0.01)
        manager.on_output()
        self.assertGreater(watchdog.last_activity, initial)

    def test_status_combined(self):
        manager = GuardManager(
            turn_cap=TurnCapGuard(max_turns=10),
            cost_ceiling=CostCeilingGuard(session_limit_usd=1.0),
        )
        status = manager.status()
        self.assertIn("can_continue", status)
        self.assertIn("turn_cap", status)
        self.assertIn("cost_ceiling", status)

    def test_empty_manager(self):
        manager = GuardManager()
        self.assertTrue(manager.can_continue())
        manager.on_turn()  # Should not crash
        manager.on_cost(0.01)
        manager.on_output()


class TestGuardConfigLoading(unittest.TestCase):
    """Test loading guards from config file."""

    def test_custom_config(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
runaway_guards:
  enabled: true
  turn_cap:
    enabled: true
    max_turns: 50
    warn_at: 40
  cost_ceiling:
    enabled: false
  stall_watchdog:
    enabled: true
    timeout_minutes: 10
""")
            f.flush()

            try:
                manager = GuardManager.from_config(Path(f.name))
                self.assertIsNotNone(manager.turn_cap)
                self.assertEqual(manager.turn_cap.max_turns, 50)
                self.assertIsNone(manager.cost_ceiling)  # Disabled
                self.assertIsNotNone(manager.stall_watchdog)
                self.assertEqual(manager.stall_watchdog.timeout_seconds, 600)  # 10 min
            finally:
                os.unlink(f.name)

    def test_guards_disabled(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
runaway_guards:
  enabled: false
""")
            f.flush()

            try:
                manager = GuardManager.from_config(Path(f.name))
                self.assertIsNone(manager.turn_cap)
                self.assertIsNone(manager.cost_ceiling)
                self.assertIsNone(manager.stall_watchdog)
                self.assertTrue(manager.can_continue())  # Empty manager always continues
            finally:
                os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
