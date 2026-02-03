"""LLM-Removal Test — INV-LLM-REMOVAL-TEST enforcement.

Verifies that all if-then signatures in generated bundles are
extractable as structured data without LLM interpretation.
Parse 5 test bundles and assert structured extraction.
"""

import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.bundler import generate_bundle


def _make_test_bundle(idx):
    """Generate a test bundle with known signatures."""
    sigs = [
        {
            "id": f"S-{idx:03d}-01",
            "condition": f"Test condition {idx}.1",
            "action": f"Test action {idx}.1",
            "source_timestamp": f"{idx}:00",
        },
        {
            "id": f"S-{idx:03d}-02",
            "condition": f"Test condition {idx}.2",
            "action": f"Test action {idx}.2",
            "source_timestamp": f"{idx}:30",
        },
    ]
    summary = {
        "total": 2, "rejected": 0, "passed": 2,
        "results": [
            {"verdict": "NO_FALSIFICATION_FOUND", "reason": "passed",
             "citation": "n/a", "attempts": 3, "signature_id": s["id"],
             "auditor_model": "gemini-3-flash"}
            for s in sigs
        ],
    }
    return generate_bundle(
        bundle_id=f"B-LM-{idx:03d}",
        source_url=f"https://youtube.com/test{idx}",
        timestamp_range=f"0:00-{idx}0:00",
        validated_signatures=sigs,
        rejected_signatures=[],
        auditor_summary=summary,
    ), sigs


def extract_signatures_from_bundle(bundle_text):
    """Extract if-then signatures from bundle markdown table.

    This is the LLM-removal test: can we reconstruct structured data
    from the bundle output without needing an LLM to interpret prose?
    """
    # Find the signatures table
    table_re = re.compile(
        r"\|\s*ID\s*\|\s*Condition \(IF\)\s*\|\s*Action \(THEN\)\s*\|\s*Source Timestamp\s*\|"
        r"\s*\n\|[-\s|]+\|\s*\n((?:\|[^\n]+\|\s*\n)+)",
        re.MULTILINE,
    )
    match = table_re.search(bundle_text)
    if not match:
        return []

    rows_text = match.group(1)
    signatures = []
    for row in rows_text.strip().split("\n"):
        cells = [c.strip() for c in row.split("|") if c.strip()]
        if len(cells) >= 4 and cells[0] != "—":
            signatures.append({
                "id": cells[0],
                "condition": cells[1],
                "action": cells[2],
                "source_timestamp": cells[3],
            })
    return signatures


def extract_auditor_counts(bundle_text):
    """Extract auditor verdict counts from bundle without LLM."""
    validated_re = re.compile(r"Signatures validated:\s*(\d+)")
    rejected_re = re.compile(r"Signatures rejected:\s*(\d+)")
    v = validated_re.search(bundle_text)
    r = rejected_re.search(bundle_text)
    return {
        "validated": int(v.group(1)) if v else None,
        "rejected": int(r.group(1)) if r else None,
    }


class TestLLMRemoval(unittest.TestCase):
    """All bundle data must be extractable without LLM interpretation."""

    def test_5_bundles_signatures_extractable(self):
        """Generate 5 bundles and verify all signatures can be parsed."""
        for i in range(1, 6):
            bundle_text, original_sigs = _make_test_bundle(i)
            extracted = extract_signatures_from_bundle(bundle_text)

            self.assertEqual(
                len(extracted), len(original_sigs),
                f"Bundle {i}: expected {len(original_sigs)} sigs, got {len(extracted)}",
            )

            for orig, ext in zip(original_sigs, extracted):
                self.assertEqual(ext["id"], orig["id"],
                                 f"Bundle {i}: ID mismatch")
                self.assertEqual(ext["condition"], orig["condition"],
                                 f"Bundle {i}: condition mismatch")
                self.assertEqual(ext["action"], orig["action"],
                                 f"Bundle {i}: action mismatch")
                self.assertEqual(ext["source_timestamp"], orig["source_timestamp"],
                                 f"Bundle {i}: timestamp mismatch")

    def test_auditor_counts_extractable(self):
        """Auditor verdict counts must be parseable."""
        for i in range(1, 6):
            bundle_text, _ = _make_test_bundle(i)
            counts = extract_auditor_counts(bundle_text)
            self.assertEqual(counts["validated"], 2)
            self.assertEqual(counts["rejected"], 0)

    def test_bundle_id_extractable(self):
        """Bundle ID must appear in predictable location."""
        for i in range(1, 6):
            bundle_text, _ = _make_test_bundle(i)
            id_re = re.compile(r"# EVIDENCE BUNDLE: (B-LM-\d{3})")
            match = id_re.search(bundle_text)
            self.assertIsNotNone(match, f"Bundle {i}: ID not extractable")
            self.assertEqual(match.group(1), f"B-LM-{i:03d}")

    def test_provenance_extractable(self):
        """Provenance section must contain parseable fields."""
        bundle_text, _ = _make_test_bundle(1)
        self.assertIn("Transcript method:", bundle_text)
        self.assertIn("Theorist model:", bundle_text)
        self.assertIn("Auditor model:", bundle_text)
        self.assertIn("Chronicler incorporated:", bundle_text)
        self.assertIn("Negative beads considered:", bundle_text)


if __name__ == "__main__":
    unittest.main()
