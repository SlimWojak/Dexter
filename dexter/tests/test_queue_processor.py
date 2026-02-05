"""Tests for Queue Processor (Phase 5).

Tests cover:
- Queue loading and saving
- Pending video filtering
- Status updates
- Dry run mode
- Limit control
- Error handling during processing
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import yaml

os.environ.setdefault("DEXTER_MOCK_MODE", "true")

from core.queue_processor import (
    load_queue,
    save_queue,
    get_pending_videos,
    update_video_status,
    process_queue,
)


def _make_queue_data(n=3, status="QUEUED"):
    return {
        "generated": "2024-01-01T00:00:00+00:00",
        "strategy": "mentorship_first",
        "total": n,
        "queue": [
            {
                "id": f"vid{i}",
                "title": f"Test Video {i}",
                "url": f"https://www.youtube.com/watch?v=vid{i}",
                "category": "MENTORSHIP",
                "status": status,
                "position": i + 1,
            }
            for i in range(n)
        ],
    }


def _write_queue_file(data):
    """Write queue data to a temp file and return path."""
    fd, path = tempfile.mkstemp(suffix=".yaml")
    os.close(fd)
    with open(path, "w") as f:
        yaml.dump(data, f)
    return Path(path)


class TestLoadQueue(unittest.TestCase):

    def test_load_existing_queue(self):
        path = _write_queue_file(_make_queue_data())
        try:
            data = load_queue(path)
            self.assertEqual(data["total"], 3)
            self.assertEqual(len(data["queue"]), 3)
        finally:
            path.unlink()

    def test_load_nonexistent_raises(self):
        with self.assertRaises(FileNotFoundError):
            load_queue(Path("/tmp/nonexistent_queue_12345.yaml"))


class TestSaveQueue(unittest.TestCase):

    def test_save_and_reload(self):
        data = _make_queue_data()
        fd, path_str = tempfile.mkstemp(suffix=".yaml")
        os.close(fd)
        path = Path(path_str)
        try:
            save_queue(data, path)
            reloaded = load_queue(path)
            self.assertEqual(reloaded["total"], 3)
        finally:
            path.unlink()

    def test_atomic_write_no_tmp_left(self):
        """After successful save, .tmp file should not exist."""
        data = _make_queue_data()
        fd, path_str = tempfile.mkstemp(suffix=".yaml")
        os.close(fd)
        path = Path(path_str)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        try:
            save_queue(data, path)
            # .tmp file should be gone after atomic rename
            self.assertFalse(tmp_path.exists())
            # Main file should exist with correct content
            self.assertTrue(path.exists())
            reloaded = load_queue(path)
            self.assertEqual(reloaded["total"], 3)
        finally:
            if path.exists():
                path.unlink()
            if tmp_path.exists():
                tmp_path.unlink()

    def test_atomic_write_creates_parent_dirs(self):
        """save_queue should create parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "subdir" / "queue.yaml"
            data = _make_queue_data()
            save_queue(data, path)
            self.assertTrue(path.exists())
            reloaded = load_queue(path)
            self.assertEqual(reloaded["total"], 3)

    def test_atomic_write_integrity(self):
        """File should have complete content after atomic write."""
        data = _make_queue_data(10)  # More data to verify integrity
        fd, path_str = tempfile.mkstemp(suffix=".yaml")
        os.close(fd)
        path = Path(path_str)
        try:
            save_queue(data, path)
            reloaded = load_queue(path)
            # All 10 videos should be present
            self.assertEqual(len(reloaded["queue"]), 10)
            for i, v in enumerate(reloaded["queue"]):
                self.assertEqual(v["id"], f"vid{i}")
        finally:
            path.unlink()


class TestGetPendingVideos(unittest.TestCase):

    def test_all_queued(self):
        data = _make_queue_data(5)
        pending = get_pending_videos(data)
        self.assertEqual(len(pending), 5)

    def test_mixed_statuses(self):
        data = _make_queue_data(3)
        data["queue"][0]["status"] = "DONE"
        data["queue"][1]["status"] = "FAILED"
        pending = get_pending_videos(data)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["id"], "vid2")

    def test_empty_queue(self):
        data = {"queue": []}
        self.assertEqual(len(get_pending_videos(data)), 0)


class TestUpdateVideoStatus(unittest.TestCase):

    def test_update_status(self):
        data = _make_queue_data()
        update_video_status(data, "vid0", "DONE")
        self.assertEqual(data["queue"][0]["status"], "DONE")

    def test_update_with_bundle_id(self):
        data = _make_queue_data()
        update_video_status(data, "vid1", "DONE", bundle_id="B-20260203-120000")
        self.assertEqual(data["queue"][1]["bundle_id"], "B-20260203-120000")

    def test_update_with_error(self):
        data = _make_queue_data()
        update_video_status(data, "vid2", "FAILED", error="API timeout")
        self.assertEqual(data["queue"][2]["error"], "API timeout")

    def test_update_nonexistent_video(self):
        data = _make_queue_data()
        # Should not crash
        update_video_status(data, "nonexistent", "DONE")
        # Original statuses unchanged
        for v in data["queue"]:
            self.assertEqual(v["status"], "QUEUED")


class TestProcessQueue(unittest.TestCase):

    def test_dry_run(self):
        path = _write_queue_file(_make_queue_data(3))
        try:
            result = process_queue(queue_path=path, dry_run=True)
            self.assertTrue(result["dry_run"])
            self.assertEqual(result["processed"], 0)
            self.assertEqual(len(result["results"]), 3)
            for r in result["results"]:
                self.assertEqual(r["action"], "dry_run")
        finally:
            path.unlink()

    def test_dry_run_with_limit(self):
        path = _write_queue_file(_make_queue_data(5))
        try:
            result = process_queue(queue_path=path, dry_run=True, limit=2)
            self.assertEqual(len(result["results"]), 2)
        finally:
            path.unlink()

    @patch("core.loop.process_transcript")
    def test_execute_success(self, mock_process):
        mock_process.return_value = {
            "bundle_id": "B-20260203-120000",
            "validated": 5,
            "rejected": 1,
        }
        path = _write_queue_file(_make_queue_data(1))
        try:
            result = process_queue(queue_path=path, limit=1, delay_seconds=0)
            self.assertEqual(result["processed"], 1)
            self.assertEqual(result["failed"], 0)
            self.assertEqual(result["results"][0]["bundle_id"], "B-20260203-120000")

            # Verify status was updated in file
            data = load_queue(path)
            self.assertEqual(data["queue"][0]["status"], "DONE")
        finally:
            path.unlink()

    @patch("core.loop.process_transcript")
    def test_execute_failure(self, mock_process):
        mock_process.side_effect = Exception("Transcript fetch failed")
        path = _write_queue_file(_make_queue_data(1))
        try:
            result = process_queue(queue_path=path, limit=1, delay_seconds=0)
            self.assertEqual(result["processed"], 0)
            self.assertEqual(result["failed"], 1)
            self.assertEqual(result["results"][0]["status"], "FAILED")

            data = load_queue(path)
            self.assertEqual(data["queue"][0]["status"], "FAILED")
        finally:
            path.unlink()

    def test_skip_no_url(self):
        data = _make_queue_data(1)
        data["queue"][0]["url"] = ""
        path = _write_queue_file(data)
        try:
            result = process_queue(queue_path=path, dry_run=False, delay_seconds=0)
            self.assertEqual(result["skipped"], 1)
            self.assertEqual(result["processed"], 0)
        finally:
            path.unlink()

    def test_already_done_skipped(self):
        data = _make_queue_data(2)
        data["queue"][0]["status"] = "DONE"
        path = _write_queue_file(data)
        try:
            result = process_queue(queue_path=path, dry_run=True)
            # Only 1 pending (vid1), vid0 is DONE
            self.assertEqual(len(result["results"]), 1)
        finally:
            path.unlink()


class TestBundleVersioning(unittest.TestCase):
    """Test the new B-YYYYMMDD-HHMMSS bundle ID format."""

    def test_bundle_id_format(self):
        from core.bundler import generate_bundle_id
        bid = generate_bundle_id()
        self.assertTrue(bid.startswith("B-"))
        self.assertEqual(len(bid), 17)
        # Verify YYYYMMDD-HHMMSS pattern
        parts = bid[2:].split("-")
        self.assertEqual(len(parts), 2)
        self.assertEqual(len(parts[0]), 8)  # YYYYMMDD
        self.assertEqual(len(parts[1]), 6)  # HHMMSS

    def test_bundle_index_write_and_read(self):
        from core.bundler import save_bundle, read_bundle_index, INDEX_FILE, BUNDLES_DIR
        import tempfile

        # Use a temp directory to avoid polluting real bundles
        original_dir = BUNDLES_DIR
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                # Monkey-patch for test
                import core.bundler as bundler_mod
                bundler_mod.BUNDLES_DIR = tmp_path
                bundler_mod.INDEX_FILE = tmp_path / "index.jsonl"

                path = save_bundle(
                    "B-20260203-120000",
                    "# Test Bundle",
                    metadata={"source_url": "http://test.com", "validated": 5, "rejected": 1},
                )
                self.assertTrue(path.exists())

                entries = read_bundle_index()
                self.assertEqual(len(entries), 1)
                self.assertEqual(entries[0]["bundle_id"], "B-20260203-120000")
                self.assertEqual(entries[0]["validated"], 5)
        finally:
            bundler_mod.BUNDLES_DIR = original_dir
            bundler_mod.INDEX_FILE = original_dir / "index.jsonl"


if __name__ == "__main__":
    unittest.main()
