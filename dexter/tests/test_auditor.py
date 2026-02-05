"""Auditor tests — verify rejection criteria and Bounty Hunter behavior."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.auditor import audit_signature, audit_batch


class TestProvenanceRejection(unittest.TestCase):
    """Auditor rejects signatures missing provenance."""

    def test_no_timestamp_no_source(self):
        sig = {"id": "S-001", "condition": "price > MA", "action": "buy"}
        result = audit_signature(sig)
        self.assertEqual(result["verdict"], "REJECT")
        self.assertIn("provenance", result["reason"].lower())

    def test_no_timestamp_with_source(self):
        sig = {"id": "S-002", "condition": "price > MA", "action": "buy", "source": "ICT video"}
        result = audit_signature(sig)
        self.assertEqual(result["verdict"], "REJECT")
        self.assertIn("timestamp", result["reason"].lower())

    def test_valid_provenance_passes(self):
        sig = {
            "id": "S-003",
            "condition": "price crosses above 50 EMA",
            "action": "enter long",
            "source_timestamp": "14:32",
            "source": "ICT 2022 Mentorship Ep.1",
        }
        result = audit_signature(sig)
        self.assertNotEqual(result["verdict"], "REJECT")


class TestFalsifiabilityRejection(unittest.TestCase):
    """Auditor rejects unfalsifiable claims."""

    def test_always_marker(self):
        sig = {
            "id": "S-010",
            "condition": "price always reverses at OB",
            "action": "enter long",
            "source_timestamp": "5:00",
            "source": "video",
        }
        result = audit_signature(sig)
        self.assertEqual(result["verdict"], "REJECT")
        self.assertIn("unfalsifiable", result["reason"].lower())

    def test_guaranteed_marker(self):
        sig = {
            "id": "S-011",
            "condition": "FVG fill is guaranteed",
            "action": "enter trade",
            "source_timestamp": "10:00",
            "source": "video",
        }
        result = audit_signature(sig)
        self.assertEqual(result["verdict"], "REJECT")

    def test_testable_claim_passes(self):
        sig = {
            "id": "S-012",
            "condition": "price sweeps previous day low",
            "action": "look for bullish displacement",
            "source_timestamp": "22:15",
            "source": "video",
        }
        result = audit_signature(sig)
        self.assertNotEqual(result["verdict"], "REJECT")


class TestLogicalConsistency(unittest.TestCase):
    """Auditor rejects logical contradictions."""

    def test_buy_and_sell(self):
        sig = {
            "id": "S-020",
            "condition": "price breaks structure",
            "action": "buy and sell simultaneously",
            "source_timestamp": "1:00",
            "source": "video",
        }
        result = audit_signature(sig)
        self.assertEqual(result["verdict"], "REJECT")
        self.assertIn("contradiction", result["reason"].lower())

    def test_empty_condition(self):
        sig = {
            "id": "S-021",
            "condition": "",
            "action": "enter long",
            "source_timestamp": "1:00",
            "source": "video",
        }
        result = audit_signature(sig)
        self.assertEqual(result["verdict"], "REJECT")
        self.assertIn("incomplete", result["reason"].lower())


class TestTautologyRejection(unittest.TestCase):
    """Auditor rejects tautological signatures (v0.3 hardening)."""

    def test_price_up_increases(self):
        sig = {
            "id": "S-030",
            "condition": "price goes up",
            "action": "price increases",
            "source_timestamp": "1:00",
            "source": "video",
        }
        result = audit_signature(sig)
        self.assertEqual(result["verdict"], "REJECT")
        self.assertIn("tautology", result["reason"].lower())

    def test_bullish_expect_bullishness(self):
        sig = {
            "id": "S-031",
            "condition": "market is bullish",
            "action": "expect bullishness in price",
            "source_timestamp": "2:00",
            "source": "video",
        }
        result = audit_signature(sig)
        self.assertEqual(result["verdict"], "REJECT")
        self.assertIn("tautology", result["reason"].lower())

    def test_high_word_overlap(self):
        sig = {
            "id": "S-032",
            "condition": "price breaks above resistance level strongly",
            "action": "price breaks resistance level upward strongly",
            "source_timestamp": "3:00",
            "source": "video",
        }
        result = audit_signature(sig)
        self.assertEqual(result["verdict"], "REJECT")
        self.assertIn("tautology", result["reason"].lower())

    def test_non_tautology_passes(self):
        sig = {
            "id": "S-033",
            "condition": "price sweeps previous day low in London session",
            "action": "look for bullish displacement and enter long",
            "source_timestamp": "4:00",
            "source": "video",
        }
        result = audit_signature(sig)
        self.assertNotEqual(result["verdict"], "REJECT")


class TestAmbiguityRejection(unittest.TestCase):
    """Auditor rejects ambiguous/subjective signatures (v0.3 hardening)."""

    def test_looks_good(self):
        sig = {
            "id": "S-040",
            "condition": "price looks good at this level",
            "action": "enter long",
            "source_timestamp": "1:00",
            "source": "video",
        }
        result = audit_signature(sig)
        self.assertEqual(result["verdict"], "REJECT")
        self.assertIn("ambiguity", result["reason"].lower())

    def test_feels_heavy(self):
        sig = {
            "id": "S-041",
            "condition": "market feels heavy",
            "action": "sell",
            "source_timestamp": "2:00",
            "source": "video",
        }
        result = audit_signature(sig)
        self.assertEqual(result["verdict"], "REJECT")
        self.assertIn("ambiguity", result["reason"].lower())

    def test_seems_weak(self):
        sig = {
            "id": "S-042",
            "condition": "price action seems weak",
            "action": "avoid longs",
            "source_timestamp": "3:00",
            "source": "video",
        }
        result = audit_signature(sig)
        self.assertEqual(result["verdict"], "REJECT")
        self.assertIn("ambiguity", result["reason"].lower())

    def test_might_be(self):
        sig = {
            "id": "S-043",
            "condition": "this might be a reversal zone",
            "action": "enter trade",
            "source_timestamp": "4:00",
            "source": "video",
        }
        result = audit_signature(sig)
        self.assertEqual(result["verdict"], "REJECT")
        self.assertIn("ambiguity", result["reason"].lower())

    def test_objective_condition_passes(self):
        sig = {
            "id": "S-044",
            "condition": "price crosses above 50 EMA with volume above average",
            "action": "enter long with stop below swing low",
            "source_timestamp": "5:00",
            "source": "video",
        }
        result = audit_signature(sig)
        self.assertNotEqual(result["verdict"], "REJECT")


class TestBatchAudit(unittest.TestCase):
    """Batch audit returns proper summary."""

    def test_mixed_batch(self):
        sigs = [
            {"id": "S-100", "condition": "price > MA", "action": "buy"},  # no provenance
            {
                "id": "S-101",
                "condition": "price sweeps low",
                "action": "look for displacement",
                "source_timestamp": "14:00",
                "source": "video",
            },  # valid
            {
                "id": "S-102",
                "condition": "this always works",
                "action": "enter",
                "source_timestamp": "2:00",
                "source": "video",
            },  # unfalsifiable
        ]
        summary = audit_batch(sigs)
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["rejected"], 2)
        self.assertEqual(summary["passed"], 1)


class TestRejectionRateTracking(unittest.TestCase):
    """v0.3 Bounty Hunter: rejection rate tracking."""

    def _make_valid_sig(self, sig_id):
        return {
            "id": sig_id,
            "condition": "price crosses above 50 EMA in London session",
            "action": "enter long with stop below swing low",
            "source_timestamp": "14:32",
            "source": "ICT Mentorship",
        }

    def _make_invalid_sig(self, sig_id):
        return {"id": sig_id, "condition": "always works", "action": "buy", "source_timestamp": "1:00", "source": "x"}

    def test_rejection_rate_calculated(self):
        sigs = [self._make_valid_sig("S-110"), self._make_invalid_sig("S-111")]
        summary = audit_batch(sigs)
        self.assertIn("rejection_rate", summary)
        self.assertAlmostEqual(summary["rejection_rate"], 0.5, places=2)
        self.assertEqual(summary["rejection_rate_pct"], 50.0)

    def test_rate_status_ok(self):
        # 2/10 rejected = 20% > 10% target
        sigs = [self._make_invalid_sig(f"S-{i}") for i in range(2)]
        sigs += [self._make_valid_sig(f"S-{i+2}") for i in range(8)]
        summary = audit_batch(sigs)
        self.assertEqual(summary["rate_status"], "OK")

    def test_rate_status_below_target(self):
        # 1/20 rejected = 5% < 10% target
        sigs = [self._make_invalid_sig("S-130")]
        sigs += [self._make_valid_sig(f"S-{i+131}") for i in range(19)]
        summary = audit_batch(sigs)
        self.assertIn(summary["rate_status"], ["BELOW_TARGET", "CRITICAL_LOW"])

    def test_rate_status_critical_low(self):
        # 0/10 rejected = 0% (rubber stamp)
        sigs = [self._make_valid_sig(f"S-{i}") for i in range(10)]
        summary = audit_batch(sigs)
        self.assertEqual(summary["rate_status"], "RUBBER_STAMP")

    def test_rejection_reasons_tracked(self):
        sigs = [
            {"id": "S-150", "condition": "always wins", "action": "buy", "source_timestamp": "1:00", "source": "x"},  # falsifiability
            {"id": "S-151", "condition": "price > MA", "action": "sell"},  # provenance
        ]
        summary = audit_batch(sigs)
        self.assertIn("rejection_reasons", summary)
        self.assertIn("falsifiability", summary["rejection_reasons"])
        self.assertIn("provenance", summary["rejection_reasons"])

    def test_small_batch_no_rate_status(self):
        # Batches < 5 don't get flagged
        sigs = [self._make_valid_sig(f"S-{i}") for i in range(3)]
        summary = audit_batch(sigs)
        # rate_status should be OK for small batches (no flag)
        self.assertEqual(summary["rate_status"], "OK")


class TestAuditorOutput(unittest.TestCase):
    """Verify output format matches spec."""

    def test_output_keys(self):
        sig = {"id": "S-200", "condition": "test", "action": "test"}
        result = audit_signature(sig)
        self.assertIn("verdict", result)
        self.assertIn("reason", result)
        self.assertIn("citation", result)
        self.assertIn("attempts", result)

    def test_no_falsification_statement(self):
        sig = {
            "id": "S-201",
            "condition": "price crosses 50 EMA in London session",
            "action": "enter long with 1R stop below swing low",
            "source_timestamp": "14:32",
            "source": "ICT Mentorship Ep.3",
        }
        result = audit_signature(sig)
        self.assertEqual(result["verdict"], "NO_FALSIFICATION_FOUND")
        self.assertIn("No falsification found after 3 attempts", result["reason"])

    def test_model_diversity_logged(self):
        sig = {
            "id": "S-202",
            "condition": "test",
            "action": "test",
            "source_timestamp": "1:00",
            "source": "x",
        }
        result = audit_signature(sig)
        self.assertEqual(result["auditor_model"], "gemini-3-flash")
        self.assertEqual(result["auditor_family"], "google")


if __name__ == "__main__":
    unittest.main()
