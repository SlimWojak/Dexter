"""Back-propagation seam tests — verify rejection → NEGATIVE_BEAD → Theorist flow."""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.context import (
    append_negative_bead,
    read_negative_beads,
    BEADS_DIR,
)


def _make_claim_bead(sig_id: str, condition: str, action: str, drawer: int, bundle_id: str) -> dict:
    """Create a mock CLAIM_BEAD."""
    return {
        "bead_type": "CLAIM",
        "source_system": "DEXTER",
        "source_video": "https://www.youtube.com/watch?v=test",
        "source_timestamp": "100s",
        "source_quote": "test quote",
        "signature": {
            "id": sig_id,
            "condition": condition,
            "action": action,
            "drawer": drawer,
            "drawer_confidence": "explicit",
            "drawer_basis": "test basis",
        },
        "extraction_meta": {
            "theorist_model": "deepseek/deepseek-chat",
            "auditor_model": "google/gemini-2.0-flash-exp",
            "auditor_verdict": "SURVIVED",
            "extraction_date": "2026-02-03T15:00:00.000000+00:00",
            "bundle_id": bundle_id,
        },
        "phoenix_meta": {
            "status": "UNVALIDATED",
            "promoted_by": None,
            "promoted_date": None,
            "cso_validation": None,
        },
    }


class TestNegativeBeadSchema(unittest.TestCase):
    """Test NEGATIVE_BEAD schema with P2 enhancements."""

    def setUp(self):
        """Create temp directory for beads."""
        self.temp_dir = tempfile.mkdtemp()
        self.beads_dir = Path(self.temp_dir) / "beads"
        self.beads_dir.mkdir()
        self.patcher = patch("core.context.BEADS_DIR", self.beads_dir)
        self.patcher.start()

    def tearDown(self):
        """Clean up."""
        self.patcher.stop()
        shutil.rmtree(self.temp_dir)

    def test_negative_bead_has_required_fields(self):
        """NEGATIVE_BEAD should have all required fields."""
        bead = append_negative_bead(
            reason="Test rejection",
            source_signature="S-001",
            source_bundle="B-TEST",
            source_claim_id="B-TEST:S-001",
            drawer=3,
            rejected_by="human",
        )

        self.assertIn("id", bead)
        self.assertEqual(bead["type"], "NEGATIVE")
        self.assertIn("reason", bead)
        self.assertIn("source_signature", bead)
        self.assertIn("source_bundle", bead)
        self.assertIn("source_claim_id", bead)
        self.assertIn("drawer", bead)
        self.assertIn("rejected_by", bead)
        self.assertIn("timestamp", bead)
        self.assertIn("metadata", bead)

    def test_negative_bead_id_format(self):
        """NEGATIVE_BEAD ID should follow N-XXX format."""
        bead = append_negative_bead(
            reason="Test",
            source_signature="S-001",
        )
        self.assertTrue(bead["id"].startswith("N-"))
        self.assertRegex(bead["id"], r"N-\d{3}")

    def test_negative_bead_preserves_drawer(self):
        """Drawer should be preserved from original claim."""
        bead = append_negative_bead(
            reason="OTE doesn't apply",
            source_signature="S-007",
            drawer=4,
        )
        self.assertEqual(bead["drawer"], 4)

    def test_negative_bead_rejected_by_field(self):
        """rejected_by field should indicate who rejected."""
        bead = append_negative_bead(
            reason="Test",
            source_signature="S-001",
            rejected_by="olya",
        )
        self.assertEqual(bead["rejected_by"], "olya")

    def test_negative_bead_defaults_rejected_by_auditor(self):
        """Default rejected_by should be 'auditor'."""
        bead = append_negative_bead(
            reason="Test",
            source_signature="S-001",
        )
        self.assertEqual(bead["rejected_by"], "auditor")

    def test_negative_bead_stored_in_beads_dir(self):
        """NEGATIVE_BEAD should be stored in beads directory."""
        append_negative_bead(
            reason="Test",
            source_signature="S-001",
        )
        session_files = list(self.beads_dir.glob("session_*.jsonl"))
        self.assertEqual(len(session_files), 1)

        with open(session_files[0]) as f:
            content = f.read()
            self.assertIn("NEGATIVE", content)

    def test_negative_bead_read_back(self):
        """NEGATIVE_BEADs should be readable via read_negative_beads()."""
        append_negative_bead(
            reason="First rejection",
            source_signature="S-001",
            rejected_by="human",
        )
        append_negative_bead(
            reason="Second rejection",
            source_signature="S-002",
            rejected_by="olya",
        )

        negatives = read_negative_beads(limit=10)
        self.assertEqual(len(negatives), 2)
        self.assertEqual(negatives[0]["source_signature"], "S-001")
        self.assertEqual(negatives[1]["source_signature"], "S-002")


class TestRejectionIngestion(unittest.TestCase):
    """Test rejection ingestion pathway."""

    def setUp(self):
        """Create temp directories for beads and bundles."""
        self.temp_dir = tempfile.mkdtemp()
        self.beads_dir = Path(self.temp_dir) / "beads"
        self.bundles_dir = Path(self.temp_dir) / "bundles"
        self.beads_dir.mkdir()
        self.bundles_dir.mkdir()

        # Create a test bundle with claims
        self.bundle_id = "B-20260203-150140"
        claims = [
            _make_claim_bead("S-001", "IF price below equilibrium", "THEN buy", 3, self.bundle_id),
            _make_claim_bead("S-002", "IF price above premium", "THEN sell", 3, self.bundle_id),
            _make_claim_bead("S-003", "IF HTF bias bullish", "THEN look long", 1, self.bundle_id),
        ]
        claims_file = self.bundles_dir / f"{self.bundle_id}_claims.jsonl"
        with open(claims_file, "w") as f:
            for claim in claims:
                f.write(json.dumps(claim) + "\n")

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)

    def test_find_claim_in_bundle(self):
        """Should find a claim by ID in a bundle."""
        # Import here to use patched paths
        import scripts.record_rejection as rr

        with patch.object(rr, "BUNDLES_DIR", self.bundles_dir):
            claim, full_id = rr.find_claim("S-001", self.bundle_id)

        self.assertIsNotNone(claim)
        self.assertEqual(claim["signature"]["id"], "S-001")
        self.assertEqual(full_id, f"{self.bundle_id}:S-001")

    def test_find_claim_with_colon_format(self):
        """Should parse 'B-XXX:S-YYY' format."""
        import scripts.record_rejection as rr

        with patch.object(rr, "BUNDLES_DIR", self.bundles_dir):
            claim, full_id = rr.find_claim(f"{self.bundle_id}:S-002")

        self.assertIsNotNone(claim)
        self.assertEqual(claim["signature"]["id"], "S-002")

    def test_find_nonexistent_claim(self):
        """Should return None for nonexistent claim."""
        import scripts.record_rejection as rr

        with patch.object(rr, "BUNDLES_DIR", self.bundles_dir):
            claim, full_id = rr.find_claim("S-999", self.bundle_id)

        self.assertIsNone(claim)

    def test_record_rejection_creates_negative(self):
        """record_rejection should create a NEGATIVE_BEAD."""
        import scripts.record_rejection as rr

        with patch.object(rr, "BUNDLES_DIR", self.bundles_dir), \
             patch("core.context.BEADS_DIR", self.beads_dir):

            negative = rr.record_rejection(
                claim_spec=f"{self.bundle_id}:S-001",
                reason="OTE doesn't apply here",
                rejected_by="olya",
            )

        self.assertEqual(negative["type"], "NEGATIVE")
        self.assertIn("OTE doesn't apply here", negative["reason"])
        self.assertEqual(negative["source_signature"], "S-001")
        self.assertEqual(negative["drawer"], 3)
        self.assertEqual(negative["rejected_by"], "olya")

    def test_record_rejection_preserves_provenance(self):
        """Rejection should include full provenance chain."""
        import scripts.record_rejection as rr

        with patch.object(rr, "BUNDLES_DIR", self.bundles_dir), \
             patch("core.context.BEADS_DIR", self.beads_dir):

            negative = rr.record_rejection(
                claim_spec="S-003",
                reason="Missing context",
                bundle_id=self.bundle_id,
            )

        self.assertEqual(negative["source_claim_id"], f"{self.bundle_id}:S-003")
        self.assertEqual(negative["source_bundle"], self.bundle_id)
        self.assertEqual(negative["drawer"], 1)  # HTF_BIAS

    def test_record_rejection_handles_missing_claim(self):
        """Should still record rejection even if claim not found."""
        import scripts.record_rejection as rr

        with patch.object(rr, "BUNDLES_DIR", self.bundles_dir), \
             patch("core.context.BEADS_DIR", self.beads_dir):

            # This should not raise
            negative = rr.record_rejection(
                claim_spec="S-999",
                reason="Invalid claim",
                bundle_id=self.bundle_id,
            )

        self.assertEqual(negative["type"], "NEGATIVE")
        self.assertEqual(negative["source_signature"], "S-999")


class TestTheoristContextInjection(unittest.TestCase):
    """Test that Theorist receives negative context."""

    def setUp(self):
        """Create temp directory for beads."""
        self.temp_dir = tempfile.mkdtemp()
        self.beads_dir = Path(self.temp_dir) / "beads"
        self.beads_dir.mkdir()

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)

    def test_router_prepends_negatives(self):
        """Router should prepend negative beads to Theorist payload."""
        from core.router import _prepend_negative_context

        with patch("core.context.BEADS_DIR", self.beads_dir):
            # Create some negative beads
            append_negative_bead(
                reason="Missing provenance",
                source_signature="S-001",
                rejected_by="auditor",
            )
            append_negative_bead(
                reason="OTE doesn't apply",
                source_signature="S-002",
                rejected_by="human",
            )

            payload = {"task": "extract", "transcript": "test"}
            result = _prepend_negative_context(payload)

        self.assertIn("negative_context", result)
        self.assertIn("instruction", result["negative_context"])
        self.assertIn("N-", result["negative_context"]["instruction"])
        self.assertEqual(len(result["negative_context"]["beads"]), 2)

    def test_theorist_receives_negative_context(self):
        """Theorist should format negatives in system prompt."""
        from core.theorist import THEORIST_SYSTEM_PROMPT

        # The system prompt should have placeholder for negatives
        self.assertIn("{negative_context}", THEORIST_SYSTEM_PROMPT)
        self.assertIn("AVOID PATTERNS", THEORIST_SYSTEM_PROMPT)

    def test_negative_context_formatted_for_llm(self):
        """Negative context should be formatted for LLM consumption."""
        from core.router import _prepend_negative_context

        with patch("core.context.BEADS_DIR", self.beads_dir):
            append_negative_bead(
                reason="OTE doesn't work this way | Original: IF at 62% THEN buy",
                source_signature="S-005",
                drawer=4,
                rejected_by="olya",
            )

            payload = {}
            result = _prepend_negative_context(payload)

        # Check format
        context = result["negative_context"]
        self.assertIn("Avoid patterns similar to", context["instruction"])
        self.assertTrue(any("N-" in r for r in context["recent_rejections"]))


class TestChroniclerIntegration(unittest.TestCase):
    """Test that Chronicler handles new NEGATIVE_BEADs correctly."""

    def setUp(self):
        """Create temp directories."""
        self.temp_dir = tempfile.mkdtemp()
        self.beads_dir = Path(self.temp_dir) / "beads"
        self.bundles_dir = Path(self.temp_dir) / "bundles"
        self.memory_dir = Path(self.temp_dir) / "memory"
        self.beads_dir.mkdir()
        self.bundles_dir.mkdir()
        self.memory_dir.mkdir()

        os.environ["DEXTER_LLM_MODE"] = "false"

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
        os.environ.pop("DEXTER_LLM_MODE", None)

    def test_chronicler_preserves_enhanced_negatives(self):
        """Chronicler should preserve negatives with enhanced schema."""
        from core.chronicler import load_negative_beads, generate_theory_md

        with patch("core.context.BEADS_DIR", self.beads_dir), \
             patch("core.chronicler.BEADS_DIR", self.beads_dir):

            # Create enhanced negative beads
            append_negative_bead(
                reason="OTE doesn't apply",
                source_signature="S-007",
                source_claim_id="B-TEST:S-007",
                drawer=4,
                rejected_by="olya",
            )
            append_negative_bead(
                reason="Missing context",
                source_signature="S-003",
                source_claim_id="B-TEST:S-003",
                drawer=1,
                rejected_by="human",
            )

            negatives = load_negative_beads()
            content = generate_theory_md({1: [], 2: [], 3: [], 4: [], 5: []}, [], negatives)

        # Negatives should appear in THEORY.md
        self.assertIn("N-", content)
        self.assertIn("OTE doesn't apply", content)
        self.assertIn("Missing context", content)

    def test_chronicler_no_regression(self):
        """Chronicler should still work with old-format negatives."""
        from core.chronicler import load_negative_beads

        # Create a session file with old-format negative
        session_file = self.beads_dir / "session_2026-02-03.jsonl"
        old_negative = {
            "id": "N-001",
            "type": "NEGATIVE",
            "reason": "Old format rejection",
            "source_signature": "S-001",
            "source_bundle": "B-TEST",
            "timestamp": "2026-02-03T15:00:00.000000+00:00",
            "metadata": {},
        }
        with open(session_file, "w") as f:
            f.write(json.dumps(old_negative) + "\n")

        with patch("core.chronicler.BEADS_DIR", self.beads_dir):
            negatives = load_negative_beads()

        self.assertEqual(len(negatives), 1)
        self.assertEqual(negatives[0]["id"], "N-001")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases in rejection flow."""

    def setUp(self):
        """Create temp directories."""
        self.temp_dir = tempfile.mkdtemp()
        self.beads_dir = Path(self.temp_dir) / "beads"
        self.bundles_dir = Path(self.temp_dir) / "bundles"
        self.beads_dir.mkdir()
        self.bundles_dir.mkdir()

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)

    def test_empty_reason(self):
        """Should handle empty reason string."""
        with patch("core.context.BEADS_DIR", self.beads_dir):
            bead = append_negative_bead(
                reason="",
                source_signature="S-001",
            )
        self.assertEqual(bead["reason"], "")

    def test_very_long_reason(self):
        """Should handle very long reason strings."""
        long_reason = "x" * 1000
        with patch("core.context.BEADS_DIR", self.beads_dir):
            bead = append_negative_bead(
                reason=long_reason,
                source_signature="S-001",
            )
        self.assertEqual(len(bead["reason"]), 1000)

    def test_duplicate_rejection(self):
        """Should allow duplicate rejections (different timestamps)."""
        with patch("core.context.BEADS_DIR", self.beads_dir):
            bead1 = append_negative_bead(
                reason="First rejection",
                source_signature="S-001",
            )
            bead2 = append_negative_bead(
                reason="Second rejection",
                source_signature="S-001",
            )

        self.assertNotEqual(bead1["id"], bead2["id"])

    def test_null_drawer(self):
        """Should handle None drawer value."""
        with patch("core.context.BEADS_DIR", self.beads_dir):
            bead = append_negative_bead(
                reason="Test",
                source_signature="S-001",
                drawer=None,
            )
        self.assertIsNone(bead["drawer"])


if __name__ == "__main__":
    unittest.main()
