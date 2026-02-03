"""Full loop integration test — mock transcript through complete pipeline."""

import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.context import BEADS_DIR, _session_file, read_beads, read_negative_beads
from core.loop import process_transcript
from core.bundler import check_narrative_bleed


BUNDLES_DIR = Path(__file__).resolve().parent.parent / "bundles"


class TestFullLoop(unittest.TestCase):
    """End-to-end: mock transcript → Theorist → Auditor → Bundler."""

    @classmethod
    def setUpClass(cls):
        """Run full pipeline once, store results."""
        # Ensure clean state
        BEADS_DIR.mkdir(parents=True, exist_ok=True)
        sf = _session_file()
        if sf.exists():
            os.remove(sf)

        # Set mock mode
        os.environ["DEXTER_MOCK_MODE"] = "true"

        cls.summary = process_transcript("mock://ict_2022_mentorship_01")

    def test_01_signatures_extracted(self):
        """Theorist extracts at least 5 signatures."""
        self.assertGreaterEqual(
            self.summary["total_extracted"], 5,
            f"Only extracted {self.summary['total_extracted']}",
        )

    def test_02_some_validated(self):
        """At least 1 signature survives audit."""
        self.assertGreater(
            self.summary["validated"], 0,
            "No signatures survived audit",
        )

    def test_03_some_rejected(self):
        """At least 1 signature rejected (proves adversarial stance)."""
        self.assertGreater(
            self.summary["rejected"], 0,
            "No signatures rejected — Auditor may not be adversarial enough",
        )

    def test_04_bundle_created(self):
        """Bundle file exists in bundles/ directory."""
        bundle_id = self.summary["bundle_id"]
        self.assertIsNotNone(bundle_id, "No bundle created")

        bundle_path = BUNDLES_DIR / f"{bundle_id}.md"
        self.assertTrue(
            bundle_path.exists(),
            f"Bundle file not found: {bundle_path}",
        )

    def test_05_bundle_no_narrative_bleed(self):
        """Bundle passes INV-NO-NARRATIVE check."""
        bundle_id = self.summary["bundle_id"]
        if not bundle_id:
            self.skipTest("No bundle created")

        bundle_path = BUNDLES_DIR / f"{bundle_id}.md"
        with open(bundle_path) as f:
            content = f.read()

        violations = check_narrative_bleed(content)
        self.assertEqual(
            len(violations), 0,
            f"Narrative bleed in bundle: {violations}",
        )

    def test_06_negative_beads_created(self):
        """Negative beads exist for rejected signatures."""
        negatives = read_negative_beads(limit=50)
        self.assertGreater(
            len(negatives), 0,
            "No negative beads created for rejections",
        )

    def test_07_beads_written(self):
        """Session beads file contains pipeline activity."""
        all_beads = read_beads()
        bead_types = {b["type"] for b in all_beads}
        self.assertIn("TRANSCRIPT_FETCH", bead_types)
        self.assertIn("EXTRACTION", bead_types)

    def test_08_bundle_bead_logged(self):
        """BUNDLE bead written to session."""
        all_beads = read_beads()
        bundle_beads = [b for b in all_beads if b["type"] == "BUNDLE"]
        self.assertGreater(len(bundle_beads), 0, "No BUNDLE bead logged")


class TestFullLoopIdempotent(unittest.TestCase):
    """Second run still works (no state corruption)."""

    def test_second_run_succeeds(self):
        os.environ["DEXTER_MOCK_MODE"] = "true"
        summary = process_transcript("mock://ict_second_run")
        self.assertGreater(summary["total_extracted"], 0)


if __name__ == "__main__":
    unittest.main()
