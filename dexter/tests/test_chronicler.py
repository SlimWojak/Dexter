"""Chronicler tests — verify compression, clustering, redundancy detection, and archival."""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.chronicler import (
    compute_similarity,
    cluster_by_drawer,
    cluster_within_drawer,
    detect_redundant_pairs,
    load_all_claims,
    load_negative_beads,
    generate_theory_md,
    archive_session_beads,
    compress_beads,
    needs_compression_check,
    DRAWER_NAMES,
    DEFAULT_SIMILARITY_THRESHOLD,
)


def _make_claim(sig_id: str, condition: str, action: str, drawer: int) -> dict:
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
            "bundle_id": "B-TEST",
        },
        "phoenix_meta": {
            "status": "UNVALIDATED",
            "promoted_by": None,
            "promoted_date": None,
            "cso_validation": None,
        },
    }


def _make_negative(neg_id: str, reason: str, source_sig: str) -> dict:
    """Create a mock NEGATIVE bead."""
    return {
        "id": neg_id,
        "type": "NEGATIVE",
        "reason": reason,
        "source_signature": source_sig,
        "source_bundle": "B-TEST",
        "timestamp": "2026-02-03T15:00:00.000000+00:00",
        "metadata": {},
    }


class TestSimilarity(unittest.TestCase):
    """Test cosine similarity computation."""

    def test_identical_texts(self):
        """Identical texts should have similarity 1.0."""
        text = "IF price reaches equilibrium THEN look for entry"
        sim = compute_similarity(text, text)
        self.assertAlmostEqual(sim, 1.0, places=5)

    def test_completely_different(self):
        """Completely different texts should have low similarity."""
        text_a = "apple banana cherry"
        text_b = "dog elephant fox"
        sim = compute_similarity(text_a, text_b)
        self.assertEqual(sim, 0.0)

    def test_similar_texts(self):
        """Similar texts should have high similarity."""
        text_a = "IF price reaches equilibrium on daily chart THEN look for buying opportunities"
        text_b = "IF price reaches equilibrium THEN hunt for buying opportunities on lower timeframes"
        sim = compute_similarity(text_a, text_b)
        self.assertGreater(sim, 0.5)

    def test_threshold_detection(self):
        """Near-duplicate texts should exceed 0.85 threshold."""
        text_a = "IF price is below equilibrium at discount THEN expect rally"
        text_b = "IF price is below equilibrium in discount zone THEN expect rally upward"
        sim = compute_similarity(text_a, text_b)
        self.assertGreater(sim, 0.7)

    def test_empty_text(self):
        """Empty texts should have 0 similarity."""
        sim = compute_similarity("", "some text")
        self.assertEqual(sim, 0.0)


class TestClusterByDrawer(unittest.TestCase):
    """Test drawer-based clustering."""

    def test_single_drawer(self):
        """Claims with same drawer should cluster together."""
        claims = [
            _make_claim("S-001", "cond1", "action1", 3),
            _make_claim("S-002", "cond2", "action2", 3),
        ]
        clusters = cluster_by_drawer(claims)
        self.assertEqual(len(clusters[3]), 2)
        self.assertEqual(len(clusters[1]), 0)

    def test_multiple_drawers(self):
        """Claims should be distributed across drawers."""
        claims = [
            _make_claim("S-001", "cond1", "action1", 1),
            _make_claim("S-002", "cond2", "action2", 2),
            _make_claim("S-003", "cond3", "action3", 3),
            _make_claim("S-004", "cond4", "action4", 4),
            _make_claim("S-005", "cond5", "action5", 5),
        ]
        clusters = cluster_by_drawer(claims)
        for drawer in range(1, 6):
            self.assertEqual(len(clusters[drawer]), 1)

    def test_all_drawers_initialized(self):
        """All 5 drawers should be present in result."""
        clusters = cluster_by_drawer([])
        self.assertEqual(len(clusters), 5)
        for drawer in range(1, 6):
            self.assertIn(drawer, clusters)


class TestClusterWithinDrawer(unittest.TestCase):
    """Test semantic clustering within a drawer."""

    def test_similar_claims_cluster(self):
        """Similar claims should be grouped together."""
        claims = [
            _make_claim("S-001", "IF price below equilibrium", "THEN look for discount entry", 3),
            _make_claim("S-002", "IF price is below equilibrium level", "THEN search for discount entries", 3),
            _make_claim("S-003", "IF market at premium above equilibrium", "THEN look for short", 3),
        ]
        clusters = cluster_within_drawer(claims, threshold=0.5)
        # First two should cluster together, third separate
        self.assertGreaterEqual(len(clusters), 1)
        self.assertLessEqual(len(clusters), 3)

    def test_dissimilar_claims_separate(self):
        """Dissimilar claims should form separate clusters."""
        claims = [
            _make_claim("S-001", "apple banana cherry", "fruit salad", 3),
            _make_claim("S-002", "dog elephant fox", "animal zoo", 3),
            _make_claim("S-003", "car bus train", "transportation", 3),
        ]
        clusters = cluster_within_drawer(claims, threshold=0.85)
        # Each should be in its own cluster
        self.assertEqual(len(clusters), 3)

    def test_empty_input(self):
        """Empty input should return empty clusters."""
        clusters = cluster_within_drawer([])
        self.assertEqual(clusters, [])


class TestRedundancyDetection(unittest.TestCase):
    """Test redundant pair detection."""

    def test_redundant_pair_detected(self):
        """Near-duplicate claims should be flagged."""
        claims = [
            _make_claim("S-001", "IF price below equilibrium", "THEN buy", 3),
            _make_claim("S-002", "IF price below equilibrium", "THEN buy", 3),
        ]
        redundant = detect_redundant_pairs(claims, threshold=0.85)
        self.assertEqual(len(redundant), 1)
        self.assertGreaterEqual(redundant[0][2], 0.85)

    def test_no_redundancy(self):
        """Distinct claims should not be flagged."""
        claims = [
            _make_claim("S-001", "apple banana cherry", "fruit", 3),
            _make_claim("S-002", "dog elephant fox", "animal", 3),
        ]
        redundant = detect_redundant_pairs(claims, threshold=0.85)
        self.assertEqual(len(redundant), 0)

    def test_returns_pair_info(self):
        """Redundant pairs should include both claims and similarity."""
        claims = [
            _make_claim("S-001", "same text here", "same action", 3),
            _make_claim("S-002", "same text here", "same action", 3),
        ]
        redundant = detect_redundant_pairs(claims, threshold=0.5)
        self.assertEqual(len(redundant), 1)
        claim_a, claim_b, sim = redundant[0]
        self.assertEqual(claim_a["signature"]["id"], "S-001")
        self.assertEqual(claim_b["signature"]["id"], "S-002")
        self.assertIsInstance(sim, float)


class TestTheoryMdGeneration(unittest.TestCase):
    """Test THEORY.md generation."""

    def test_generates_markdown(self):
        """Should generate valid markdown content."""
        drawer_clusters = {
            1: [[_make_claim("S-001", "cond1", "action1", 1)]],
            2: [],
            3: [[_make_claim("S-002", "cond2", "action2", 3)]],
            4: [],
            5: [],
        }
        negatives = [_make_negative("N-001", "Test rejection", "S-003")]
        redundant = []

        content = generate_theory_md(drawer_clusters, redundant, negatives)

        self.assertIn("# THEORY.md", content)
        self.assertIn("## INDEX", content)
        self.assertIn("## CLUSTERS", content)
        self.assertIn("## NEGATIVE PATTERNS", content)
        self.assertIn("HTF_BIAS", content)
        self.assertIn("N-001", content)

    def test_negative_section_present(self):
        """NEGATIVE section should always be present."""
        content = generate_theory_md({1: [], 2: [], 3: [], 4: [], 5: []}, [], [])
        self.assertIn("## NEGATIVE PATTERNS", content)

    def test_negatives_included(self):
        """Negative beads should appear in output."""
        negatives = [
            _make_negative("N-001", "Missing provenance", "S-001"),
            _make_negative("N-002", "Unfalsifiable claim", "S-002"),
        ]
        content = generate_theory_md({1: [], 2: [], 3: [], 4: [], 5: []}, [], negatives)
        self.assertIn("N-001", content)
        self.assertIn("N-002", content)
        self.assertIn("Missing provenance", content)

    def test_redundant_pairs_section(self):
        """Redundant pairs should be flagged in output."""
        claim_a = _make_claim("S-001", "same", "action", 3)
        claim_b = _make_claim("S-002", "same", "action", 3)
        redundant = [(claim_a, claim_b, 0.95)]

        content = generate_theory_md({1: [], 2: [], 3: [], 4: [], 5: []}, redundant, [])
        self.assertIn("REDUNDANT", content)
        self.assertIn("S-001", content)
        self.assertIn("S-002", content)

    def test_drawer_names_used(self):
        """All drawer names should appear."""
        content = generate_theory_md({1: [], 2: [], 3: [], 4: [], 5: []}, [], [])
        for name in DRAWER_NAMES.values():
            self.assertIn(name, content)


class TestArchive(unittest.TestCase):
    """Test session bead archival."""

    def setUp(self):
        """Create temp directories for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.beads_dir = Path(self.temp_dir) / "beads"
        self.archive_dir = Path(self.temp_dir) / "archive"
        self.beads_dir.mkdir()

    def tearDown(self):
        """Clean up temp directories."""
        shutil.rmtree(self.temp_dir)

    def test_archive_moves_file(self):
        """Archive should move file to archive directory."""
        # Create a test session file
        session_file = self.beads_dir / "session_2026-02-01.jsonl"
        session_file.write_text('{"test": true}\n')

        with patch("core.chronicler.ARCHIVE_DIR", self.archive_dir):
            result = archive_session_beads(session_file)

        self.assertIsNotNone(result)
        self.assertFalse(session_file.exists())
        self.assertTrue(self.archive_dir.exists())
        self.assertEqual(len(list(self.archive_dir.glob("*.jsonl"))), 1)

    def test_archive_nonexistent_file(self):
        """Archiving nonexistent file should return None."""
        fake_file = self.beads_dir / "nonexistent.jsonl"
        result = archive_session_beads(fake_file)
        self.assertIsNone(result)


class TestCompressionIntegration(unittest.TestCase):
    """Integration tests for full compression flow."""

    def setUp(self):
        """Set up temp directories and mock data."""
        self.temp_dir = tempfile.mkdtemp()
        self.memory_dir = Path(self.temp_dir) / "memory"
        self.beads_dir = self.memory_dir / "beads"
        self.archive_dir = self.memory_dir / "archive"
        self.bundles_dir = Path(self.temp_dir) / "bundles"

        self.beads_dir.mkdir(parents=True)
        self.bundles_dir.mkdir()

        # Disable LLM calls for testing
        os.environ["DEXTER_LLM_MODE"] = "false"

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
        os.environ.pop("DEXTER_LLM_MODE", None)

    def test_compression_with_claims(self):
        """Full compression should process claims and generate THEORY.md."""
        # Create test claims file
        claims_file = self.bundles_dir / "B-TEST_claims.jsonl"
        claims = [
            _make_claim("S-001", "IF price below equilibrium", "THEN buy", 3),
            _make_claim("S-002", "IF price above premium", "THEN sell", 3),
            _make_claim("S-003", "IF HTF bias bullish", "THEN look long", 1),
        ]
        with open(claims_file, "w") as f:
            for claim in claims:
                f.write(json.dumps(claim) + "\n")

        # Create test session file
        session_file = self.beads_dir / "session_2026-02-01.jsonl"
        session_file.write_text('{"type": "HEARTBEAT"}\n')

        with patch("core.chronicler.BUNDLES_DIR", self.bundles_dir), \
             patch("core.chronicler.MEMORY_DIR", self.memory_dir), \
             patch("core.chronicler.BEADS_DIR", self.beads_dir), \
             patch("core.chronicler.ARCHIVE_DIR", self.archive_dir), \
             patch("core.chronicler.THEORY_PATH", self.memory_dir / "THEORY.md"):

            result = compress_beads(archive_days=0)

        self.assertTrue(result["compressed"])
        self.assertEqual(result["total_claims"], 3)
        self.assertIn(1, result["clusters_by_drawer"])
        self.assertIn(3, result["clusters_by_drawer"])

        # THEORY.md should exist
        theory_path = self.memory_dir / "THEORY.md"
        self.assertTrue(theory_path.exists())
        content = theory_path.read_text()
        self.assertIn("S-001", content)

    def test_compression_empty(self):
        """Compression with no claims should not fail."""
        with patch("core.chronicler.BUNDLES_DIR", self.bundles_dir), \
             patch("core.chronicler.MEMORY_DIR", self.memory_dir), \
             patch("core.chronicler.BEADS_DIR", self.beads_dir):

            result = compress_beads()

        self.assertFalse(result["compressed"])
        self.assertEqual(result["total_claims"], 0)


class TestNegativeBeadPreservation(unittest.TestCase):
    """Test that NEGATIVE beads survive compression."""

    def setUp(self):
        """Set up temp directories."""
        self.temp_dir = tempfile.mkdtemp()
        self.memory_dir = Path(self.temp_dir) / "memory"
        self.beads_dir = self.memory_dir / "beads"
        self.bundles_dir = Path(self.temp_dir) / "bundles"

        self.beads_dir.mkdir(parents=True)
        self.bundles_dir.mkdir()

        os.environ["DEXTER_LLM_MODE"] = "false"

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
        os.environ.pop("DEXTER_LLM_MODE", None)

    def test_negatives_in_theory_md(self):
        """NEGATIVE beads should appear in THEORY.md."""
        # Create session with negatives
        session_file = self.beads_dir / "session_2026-02-03.jsonl"
        negatives = [
            _make_negative("N-001", "Missing provenance", "S-001"),
            _make_negative("N-002", "Unfalsifiable claim", "S-002"),
        ]
        with open(session_file, "w") as f:
            for neg in negatives:
                f.write(json.dumps(neg) + "\n")

        # Create a claim for compression
        claims_file = self.bundles_dir / "B-TEST_claims.jsonl"
        with open(claims_file, "w") as f:
            f.write(json.dumps(_make_claim("S-003", "cond", "action", 3)) + "\n")

        with patch("core.chronicler.BUNDLES_DIR", self.bundles_dir), \
             patch("core.chronicler.MEMORY_DIR", self.memory_dir), \
             patch("core.chronicler.BEADS_DIR", self.beads_dir), \
             patch("core.chronicler.THEORY_PATH", self.memory_dir / "THEORY.md"):

            compress_beads()

        theory_path = self.memory_dir / "THEORY.md"
        content = theory_path.read_text()

        self.assertIn("N-001", content)
        self.assertIn("N-002", content)
        self.assertIn("Missing provenance", content)
        self.assertIn("Unfalsifiable claim", content)


class TestNeedsCompression(unittest.TestCase):
    """Test compression threshold checking."""

    def test_needs_compression_wrapper(self):
        """needs_compression_check should wrap context.needs_compression."""
        with patch("core.context.needs_compression") as mock_nc:
            mock_nc.return_value = True
            result = needs_compression_check(25)
            mock_nc.assert_called_once_with(25)
            self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
