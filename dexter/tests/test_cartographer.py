"""Tests for Cartographer — corpus survey and mapping (Phase 5).

Tests cover:
- Video categorization by observable features
- Duration bucketing
- View tier classification
- Queue building and ordering (all strategies)
- Corpus map structure
- Clusters report generation
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

import yaml

os.environ.setdefault("DEXTER_MOCK_MODE", "true")

import core.cartographer as cartographer_mod
from core.cartographer import (
    categorize_video,
    build_corpus_map,
    build_extraction_queue,
    generate_clusters_report,
    CORPUS_DIR,
)


class _TempCorpusMixin:
    """Mixin that redirects cartographer output to temp dir during tests."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_corpus = cartographer_mod.CORPUS_DIR
        self._orig_map = cartographer_mod.CORPUS_MAP_FILE
        self._orig_queue = cartographer_mod.EXTRACTION_QUEUE_FILE
        self._orig_clusters = cartographer_mod.CLUSTERS_FILE
        cartographer_mod.CORPUS_DIR = Path(self._tmpdir)
        cartographer_mod.CORPUS_MAP_FILE = Path(self._tmpdir) / "corpus_map.yaml"
        cartographer_mod.EXTRACTION_QUEUE_FILE = Path(self._tmpdir) / "extraction_queue.yaml"
        cartographer_mod.CLUSTERS_FILE = Path(self._tmpdir) / "content_clusters.md"

    def tearDown(self):
        cartographer_mod.CORPUS_DIR = self._orig_corpus
        cartographer_mod.CORPUS_MAP_FILE = self._orig_map
        cartographer_mod.EXTRACTION_QUEUE_FILE = self._orig_queue
        cartographer_mod.CLUSTERS_FILE = self._orig_clusters
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)


def _make_video(title="Test Video", duration=1800, view_count=50000, upload_date="20240115", vid_id="abc123"):
    return {
        "id": vid_id,
        "title": title,
        "duration": duration,
        "view_count": view_count,
        "upload_date": upload_date,
        "description": "A test video",
        "url": f"https://www.youtube.com/watch?v={vid_id}",
    }


class TestCategorizeVideo(unittest.TestCase):
    """Test video categorization by observable features."""

    def test_mentorship_category(self):
        v = _make_video(title="ICT Mentorship 2024 - Lesson 1")
        result = categorize_video(v)
        self.assertEqual(result["category"], "MENTORSHIP")

    def test_live_session_category(self):
        v = _make_video(title="Live Trading Stream")
        result = categorize_video(v)
        self.assertEqual(result["category"], "LIVE_SESSION")

    def test_qa_category(self):
        v = _make_video(title="Q&A Session with Students")
        result = categorize_video(v)
        self.assertEqual(result["category"], "QA")

    def test_lecture_category(self):
        v = _make_video(title="Lecture on Market Structure")
        result = categorize_video(v)
        self.assertEqual(result["category"], "LECTURE")

    def test_review_category(self):
        v = _make_video(title="Weekly Market Review")
        result = categorize_video(v)
        self.assertEqual(result["category"], "REVIEW")

    def test_unknown_category(self):
        v = _make_video(title="Something Else Entirely")
        result = categorize_video(v)
        self.assertEqual(result["category"], "UNKNOWN")

    def test_case_insensitive(self):
        v = _make_video(title="MENTORSHIP LESSON")
        result = categorize_video(v)
        self.assertEqual(result["category"], "MENTORSHIP")


class TestDurationBucket(unittest.TestCase):
    """Test duration bucketing."""

    def test_short_under_10min(self):
        v = _make_video(duration=300)
        result = categorize_video(v)
        self.assertEqual(result["duration_bucket"], "SHORT")

    def test_medium_10_to_60min(self):
        v = _make_video(duration=1800)
        result = categorize_video(v)
        self.assertEqual(result["duration_bucket"], "MEDIUM")

    def test_long_over_60min(self):
        v = _make_video(duration=7200)
        result = categorize_video(v)
        self.assertEqual(result["duration_bucket"], "LONG")

    def test_zero_duration(self):
        v = _make_video(duration=0)
        result = categorize_video(v)
        self.assertEqual(result["duration_bucket"], "SHORT")


class TestViewTier(unittest.TestCase):
    """Test view tier classification."""

    def test_viral_over_1m(self):
        v = _make_video(view_count=2_000_000)
        result = categorize_video(v)
        self.assertEqual(result["view_tier"], "VIRAL")

    def test_high_over_100k(self):
        v = _make_video(view_count=500_000)
        result = categorize_video(v)
        self.assertEqual(result["view_tier"], "HIGH")

    def test_medium_over_10k(self):
        v = _make_video(view_count=50_000)
        result = categorize_video(v)
        self.assertEqual(result["view_tier"], "MEDIUM")

    def test_low_under_10k(self):
        v = _make_video(view_count=5_000)
        result = categorize_video(v)
        self.assertEqual(result["view_tier"], "LOW")

    def test_zero_views(self):
        v = _make_video(view_count=0)
        result = categorize_video(v)
        self.assertEqual(result["view_tier"], "LOW")


class TestBuildCorpusMap(_TempCorpusMixin, unittest.TestCase):
    """Test corpus map building."""

    def test_corpus_map_structure(self):
        videos = [
            _make_video(title="Mentorship 1", vid_id="v1"),
            _make_video(title="Live Stream", vid_id="v2"),
            _make_video(title="Q&A Session", vid_id="v3"),
        ]
        result = build_corpus_map(videos)
        self.assertEqual(result["total_videos"], 3)
        self.assertIn("categories", result)
        self.assertIn("videos", result)
        self.assertIn("generated", result)

    def test_categories_counted(self):
        videos = [
            _make_video(title="Mentorship 1", vid_id="v1"),
            _make_video(title="Mentorship 2", vid_id="v2"),
            _make_video(title="Live Stream", vid_id="v3"),
        ]
        result = build_corpus_map(videos)
        self.assertEqual(result["categories"]["MENTORSHIP"], 2)
        self.assertEqual(result["categories"]["LIVE_SESSION"], 1)

    def test_videos_have_status(self):
        videos = [_make_video()]
        result = build_corpus_map(videos)
        self.assertEqual(result["videos"][0]["status"], "QUEUED")


class TestBuildExtractionQueue(_TempCorpusMixin, unittest.TestCase):
    """Test queue building with different strategies."""

    def _make_corpus_map(self):
        videos = [
            {**_make_video(title="Mentorship 1", view_count=10000, vid_id="v1"), "category": "MENTORSHIP", "status": "QUEUED"},
            {**_make_video(title="Live Stream", view_count=500000, vid_id="v2"), "category": "LIVE_SESSION", "status": "QUEUED"},
            {**_make_video(title="Lecture A", view_count=200000, vid_id="v3"), "category": "LECTURE", "status": "QUEUED"},
        ]
        return {"videos": videos}

    def test_mentorship_first_strategy(self):
        queue = build_extraction_queue(self._make_corpus_map(), "mentorship_first")
        self.assertEqual(queue[0]["category"], "MENTORSHIP")
        self.assertEqual(queue[1]["category"], "LECTURE")

    def test_views_strategy(self):
        queue = build_extraction_queue(self._make_corpus_map(), "views")
        self.assertEqual(queue[0]["view_count"], 500000)

    def test_chronological_strategy(self):
        videos = {
            "videos": [
                {**_make_video(upload_date="20240301", vid_id="v1"), "category": "X", "status": "QUEUED"},
                {**_make_video(upload_date="20240101", vid_id="v2"), "category": "X", "status": "QUEUED"},
            ]
        }
        queue = build_extraction_queue(videos, "chronological")
        self.assertEqual(queue[0]["upload_date"], "20240101")

    def test_queue_ordering_preserved(self):
        """Queue returns correct number of items in order."""
        queue = build_extraction_queue(self._make_corpus_map(), "mentorship_first")
        self.assertEqual(len(queue), 3)
        # First item should be MENTORSHIP (highest priority)
        self.assertEqual(queue[0]["category"], "MENTORSHIP")

    def test_empty_corpus(self):
        queue = build_extraction_queue({"videos": []}, "mentorship_first")
        self.assertEqual(len(queue), 0)


class TestClustersReport(_TempCorpusMixin, unittest.TestCase):
    """Test markdown clusters report generation."""

    def test_report_has_header(self):
        corpus = build_corpus_map([_make_video()])
        report = generate_clusters_report(corpus)
        self.assertIn("# ICT Content Clusters", report)

    def test_report_has_categories(self):
        videos = [
            _make_video(title="Mentorship 1", vid_id="v1"),
            _make_video(title="Live Stream", vid_id="v2"),
        ]
        corpus = build_corpus_map(videos)
        report = generate_clusters_report(corpus)
        self.assertIn("MENTORSHIP", report)
        self.assertIn("LIVE_SESSION", report)

    def test_report_includes_video_count(self):
        videos = [_make_video(title="Test", vid_id=f"v{i}") for i in range(5)]
        corpus = build_corpus_map(videos)
        report = generate_clusters_report(corpus)
        self.assertIn("Total Videos: 5", report)


if __name__ == "__main__":
    unittest.main()
