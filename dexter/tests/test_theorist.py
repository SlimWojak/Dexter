"""Theorist tests — mock transcript extraction and output validation."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.theorist import extract_signatures
from skills.transcript.supadata import fetch_transcript


class TestTheoristExtraction(unittest.TestCase):
    """Theorist extracts signatures from mock transcript."""

    @classmethod
    def setUpClass(cls):
        cls.transcript = fetch_transcript("mock://ict_test")
        cls.signatures = extract_signatures(cls.transcript)

    def test_extracts_5_plus_signatures(self):
        """Must extract at least 5 signatures from mock transcript."""
        self.assertGreaterEqual(
            len(self.signatures), 5,
            f"Only extracted {len(self.signatures)} signatures, expected >= 5",
        )

    def test_each_has_required_fields(self):
        """Every signature must have id, condition, action, timestamp, quote."""
        required = {"id", "condition", "action", "source_timestamp", "source_quote"}
        for sig in self.signatures:
            for field in required:
                self.assertIn(
                    field, sig,
                    f"Signature {sig.get('id', '?')} missing field: {field}",
                )

    def test_each_has_confidence(self):
        """Confidence field must be EXPLICIT, INFERRED, or UNCLEAR."""
        valid = {"EXPLICIT", "INFERRED", "UNCLEAR"}
        for sig in self.signatures:
            self.assertIn(
                sig.get("confidence"), valid,
                f"Signature {sig['id']} has invalid confidence: {sig.get('confidence')}",
            )

    def test_timestamps_present(self):
        """Every signature must have a non-empty timestamp."""
        for sig in self.signatures:
            self.assertTrue(
                sig["source_timestamp"],
                f"Signature {sig['id']} has empty timestamp",
            )

    def test_quotes_present(self):
        """Every signature must have a non-empty source quote."""
        for sig in self.signatures:
            self.assertTrue(
                sig["source_quote"],
                f"Signature {sig['id']} has empty quote",
            )

    def test_conditions_start_with_if(self):
        """Conditions should start with IF (Theorist format)."""
        for sig in self.signatures:
            self.assertTrue(
                sig["condition"].startswith("IF "),
                f"Signature {sig['id']} condition doesn't start with IF: {sig['condition'][:50]}",
            )

    def test_actions_start_with_then(self):
        """Actions should start with THEN (Theorist format)."""
        for sig in self.signatures:
            self.assertTrue(
                sig["action"].startswith("THEN "),
                f"Signature {sig['id']} action doesn't start with THEN: {sig['action'][:50]}",
            )


class TestTheoristNegativeAvoidance(unittest.TestCase):
    """Theorist respects negative bead patterns."""

    def test_avoids_negative_patterns(self):
        transcript = fetch_transcript("mock://ict_test")
        negative_beads = [
            {"id": "N-001", "reason": "liquidity"},
        ]
        sigs_with_neg = extract_signatures(transcript, negative_beads=negative_beads)
        sigs_without = extract_signatures(transcript)

        # With negative beads, should have fewer or equal signatures
        # (some containing "liquidity" should be skipped)
        self.assertLessEqual(len(sigs_with_neg), len(sigs_without))


class TestMockTranscript(unittest.TestCase):
    """Validate mock transcript structure."""

    def test_transcript_has_segments(self):
        t = fetch_transcript("mock://test")
        self.assertIn("segments", t)
        self.assertGreater(len(t["segments"]), 0)

    def test_each_segment_has_start_and_text(self):
        t = fetch_transcript("mock://test")
        for seg in t["segments"]:
            self.assertIn("start", seg)
            self.assertIn("text", seg)

    def test_transcript_has_title(self):
        t = fetch_transcript("mock://test")
        self.assertIn("title", t)
        self.assertTrue(t["title"])


if __name__ == "__main__":
    unittest.main()
