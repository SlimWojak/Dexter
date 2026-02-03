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
