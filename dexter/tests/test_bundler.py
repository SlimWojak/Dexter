"""Bundler tests — verify template filling and narrative bleed enforcement."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.bundler import (
    BundleError,
    check_narrative_bleed,
    generate_bundle,
)


def _make_valid_signatures():
    return [
        {
            "id": "S-001",
            "condition": "Price sweeps previous day low",
            "action": "Look for bullish displacement",
            "source_timestamp": "14:32",
        },
        {
            "id": "S-002",
            "condition": "FVG forms after displacement",
            "action": "Enter long at FVG midpoint",
            "source_timestamp": "27:15",
        },
    ]


def _make_auditor_summary():
    return {
        "total": 3,
        "rejected": 1,
        "passed": 2,
        "results": [
            {
                "verdict": "NO_FALSIFICATION_FOUND",
                "reason": "No falsification found after 3 attempts.",
                "citation": "All checks passed",
                "attempts": 3,
                "signature_id": "S-001",
                "auditor_model": "gemini-3-flash",
            },
            {
                "verdict": "NO_FALSIFICATION_FOUND",
                "reason": "No falsification found after 3 attempts.",
                "citation": "All checks passed",
                "attempts": 3,
                "signature_id": "S-002",
                "auditor_model": "gemini-3-flash",
            },
            {
                "verdict": "REJECT",
                "reason": "Missing provenance",
                "citation": "INV-SOURCE-PROVENANCE",
                "attempts": 1,
                "signature_id": "S-003",
                "auditor_model": "gemini-3-flash",
            },
        ],
    }


class TestNarrativeBleed(unittest.TestCase):
    """INV-NO-NARRATIVE enforcement."""

    def test_clean_text(self):
        violations = check_narrative_bleed("Price crossed above 50 EMA at 14:32.")
        self.assertEqual(len(violations), 0)

    def test_i_think(self):
        violations = check_narrative_bleed("I think this pattern is bullish.")
        self.assertIn("I think", violations)

    def test_suggests(self):
        violations = check_narrative_bleed("This suggests a reversal.")
        self.assertIn("this suggests", violations)

    def test_likely(self):
        violations = check_narrative_bleed("Price will likely move up.")
        self.assertIn("likely", violations)

    def test_multiple_violations(self):
        text = "I think this probably suggests a move."
        violations = check_narrative_bleed(text)
        self.assertTrue(len(violations) >= 2)


class TestBundleGeneration(unittest.TestCase):
    """Bundle generation from template."""

    def test_valid_bundle(self):
        bundle = generate_bundle(
            bundle_id="B-TEST-001",
            source_url="https://youtube.com/test",
            timestamp_range="0:00-30:00",
            validated_signatures=_make_valid_signatures(),
            rejected_signatures=[],
            auditor_summary=_make_auditor_summary(),
        )
        # Structure checks
        self.assertIn("# EVIDENCE BUNDLE: B-TEST-001", bundle)
        self.assertIn("### IF-THEN SIGNATURES", bundle)
        self.assertIn("### DELTA TO CANON", bundle)
        self.assertIn("### AUDITOR VERDICT", bundle)
        self.assertIn("### AUDITOR BACKTEST REVIEW", bundle)
        self.assertIn("### GATES PASSED", bundle)
        self.assertIn("### LOGIC DIFF", bundle)
        self.assertIn("### PROVENANCE", bundle)

    def test_signatures_in_table(self):
        bundle = generate_bundle(
            bundle_id="B-TEST-002",
            source_url="https://youtube.com/test",
            timestamp_range="0:00-30:00",
            validated_signatures=_make_valid_signatures(),
            rejected_signatures=[],
            auditor_summary=_make_auditor_summary(),
        )
        self.assertIn("S-001", bundle)
        self.assertIn("S-002", bundle)
        self.assertIn("14:32", bundle)

    def test_auditor_verdict_counts(self):
        bundle = generate_bundle(
            bundle_id="B-TEST-003",
            source_url="https://youtube.com/test",
            timestamp_range="0:00-30:00",
            validated_signatures=_make_valid_signatures(),
            rejected_signatures=[],
            auditor_summary=_make_auditor_summary(),
        )
        self.assertIn("Signatures validated: 2", bundle)
        self.assertIn("Signatures rejected: 1", bundle)

    def test_no_narrative_bleed(self):
        bundle = generate_bundle(
            bundle_id="B-TEST-004",
            source_url="https://youtube.com/test",
            timestamp_range="0:00-30:00",
            validated_signatures=_make_valid_signatures(),
            rejected_signatures=[],
            auditor_summary=_make_auditor_summary(),
        )
        violations = check_narrative_bleed(bundle)
        self.assertEqual(len(violations), 0, f"Narrative bleed in bundle: {violations}")

    def test_negative_beads_in_provenance(self):
        bundle = generate_bundle(
            bundle_id="B-TEST-005",
            source_url="https://youtube.com/test",
            timestamp_range="0:00-30:00",
            validated_signatures=_make_valid_signatures(),
            rejected_signatures=[],
            auditor_summary=_make_auditor_summary(),
            negative_beads=["N-001", "N-002"],
        )
        self.assertIn("N-001", bundle)
        self.assertIn("N-002", bundle)


class TestBundleRejection(unittest.TestCase):
    """Bundle fails if narrative violations sneak in template prose."""

    def test_narrative_in_quote_allowed(self):
        """Verbatim transcript quotes in table rows may contain speaker phrases."""
        sigs_with_speaker_phrase = [
            {
                "id": "S-QUOTE",
                "condition": "I think price will reverse at OB",
                "action": "enter long at FVG retracement",
                "source_timestamp": "5:00",
            },
        ]
        # Should NOT raise — "I think" is in a table row (verbatim quote)
        bundle = generate_bundle(
            bundle_id="B-QUOTE-001",
            source_url="https://youtube.com/test",
            timestamp_range="0:00-30:00",
            validated_signatures=sigs_with_speaker_phrase,
            rejected_signatures=[],
            auditor_summary={"total": 1, "rejected": 0, "passed": 1, "results": []},
        )
        self.assertIn("S-QUOTE", bundle)

    def test_narrative_bleed_without_exclude(self):
        """check_narrative_bleed without exclude_quotes still catches everything."""
        text = "| S-001 | I think price reverses | enter long | 5:00 |"
        violations = check_narrative_bleed(text, exclude_quotes=False)
        self.assertIn("I think", violations)

    def test_narrative_bleed_with_exclude(self):
        """check_narrative_bleed with exclude_quotes skips table rows."""
        text = "| S-001 | I think price reverses | enter long | 5:00 |"
        violations = check_narrative_bleed(text, exclude_quotes=True)
        self.assertEqual(len(violations), 0)


if __name__ == "__main__":
    unittest.main()
