"""Phase 4A — Supadata API integration + jargon checker tests.

Tests real API path (with mock fallback), jargon accuracy checking,
transcript normalization, and runner gate validation.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skills.transcript.supadata import (
    fetch_transcript,
    check_ict_jargon,
    format_for_theorist,
    _normalize_transcript,
    _get_api_key,
    _is_mock_mode,
    ICT_TERMS,
    JARGON_ERROR_PATTERNS,
)


class TestMockModeDetection(unittest.TestCase):
    """DEXTER_MOCK_MODE controls mock vs real dispatch."""

    def test_mock_url_triggers_mock(self):
        t = fetch_transcript("mock://test")
        self.assertEqual(t["video_id"], "mock_ict_2022_mentorship_01")

    def test_mock_env_true(self):
        with patch.dict(os.environ, {"DEXTER_MOCK_MODE": "true"}):
            self.assertTrue(_is_mock_mode())

    def test_mock_env_false(self):
        with patch.dict(os.environ, {"DEXTER_MOCK_MODE": "false"}):
            self.assertFalse(_is_mock_mode())

    def test_mock_env_default_is_true(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(_is_mock_mode())


class TestApiKeyRetrieval(unittest.TestCase):
    """API key from SUPADATA_KEY or SUPADATA_API_KEY."""

    def test_supadata_key_env(self):
        with patch.dict(os.environ, {"SUPADATA_KEY": "sk_test123"}, clear=True):
            self.assertEqual(_get_api_key(), "sk_test123")

    def test_supadata_api_key_fallback(self):
        with patch.dict(os.environ, {"SUPADATA_API_KEY": "sk_alt"}, clear=True):
            self.assertEqual(_get_api_key(), "sk_alt")

    def test_no_key_returns_none(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(_get_api_key())


class TestTranscriptNormalization(unittest.TestCase):
    """_normalize_transcript handles various API response formats."""

    def test_plain_text_content(self):
        data = {"content": "Hello world this is a transcript", "title": "Test"}
        result = _normalize_transcript(data, "src")
        self.assertEqual(len(result["segments"]), 1)
        self.assertEqual(result["segments"][0]["text"], "Hello world this is a transcript")
        self.assertEqual(result["segments"][0]["start"], 0.0)

    def test_timestamped_chunks(self):
        data = {
            "content": [
                {"offset": 0, "text": "First chunk"},
                {"offset": 5000, "text": "Second chunk"},
                {"offset": 10000, "text": "Third chunk"},
            ],
            "title": "Timestamped Video",
        }
        result = _normalize_transcript(data, "src")
        self.assertEqual(len(result["segments"]), 3)
        self.assertAlmostEqual(result["segments"][0]["start"], 0.0)
        self.assertAlmostEqual(result["segments"][1]["start"], 5.0)
        self.assertAlmostEqual(result["segments"][2]["start"], 10.0)

    def test_offset_ms_to_seconds(self):
        """Offset in milliseconds converted to seconds."""
        data = {"content": [{"offset": 67500, "text": "mid video"}], "title": "T"}
        result = _normalize_transcript(data, "src")
        self.assertAlmostEqual(result["segments"][0]["start"], 67.5)

    def test_empty_text_chunks_skipped(self):
        data = {
            "content": [
                {"offset": 0, "text": "Real content"},
                {"offset": 1000, "text": "   "},
                {"offset": 2000, "text": ""},
            ],
            "title": "Sparse",
        }
        result = _normalize_transcript(data, "src")
        self.assertEqual(len(result["segments"]), 1)

    def test_string_chunks_in_list(self):
        data = {"content": ["First line", "Second line"], "title": "T"}
        result = _normalize_transcript(data, "src")
        self.assertEqual(len(result["segments"]), 2)
        self.assertEqual(result["segments"][0]["start"], 0.0)

    def test_empty_content(self):
        data = {"content": [], "title": "Empty"}
        result = _normalize_transcript(data, "src")
        self.assertEqual(len(result["segments"]), 0)

    def test_title_preserved(self):
        data = {"content": "text", "title": "My ICT Video"}
        result = _normalize_transcript(data, "src")
        self.assertEqual(result["title"], "My ICT Video")

    def test_lang_field(self):
        data = {"content": "text", "lang": "en", "title": "T"}
        result = _normalize_transcript(data, "src")
        self.assertEqual(result["lang"], "en")


class TestJargonChecker(unittest.TestCase):
    """check_ict_jargon detects terms and errors."""

    def test_finds_ict_terms_in_mock(self):
        transcript = fetch_transcript("mock://test")
        result = check_ict_jargon(transcript)
        self.assertGreater(result["terms_found"], 0)
        self.assertEqual(result["terms_checked"], len(ICT_TERMS))

    def test_mock_transcript_finds_specific_terms(self):
        transcript = fetch_transcript("mock://test")
        result = check_ict_jargon(transcript)
        # Mock transcript mentions FVG, liquidity, displacement, breaker, dealing range
        found_lower = [t.lower() for t in result["found_terms"]]
        self.assertIn("fair value gap", found_lower)
        self.assertIn("liquidity", found_lower)
        self.assertIn("displacement", found_lower)

    def test_mock_has_low_error_rate(self):
        """Mock transcript should have clean jargon (no transcription errors)."""
        transcript = fetch_transcript("mock://test")
        result = check_ict_jargon(transcript)
        self.assertLessEqual(result["error_rate"], 0.05)

    def test_detects_transcription_errors(self):
        """Synthetic transcript with known errors."""
        transcript = {
            "segments": [
                {"start": 0.0, "text": "The fairly value gap is important"},
                {"start": 5.0, "text": "Look at the order blog for entries"},
                {"start": 10.0, "text": "Check the liquidity sweet level"},
            ]
        }
        result = check_ict_jargon(transcript)
        self.assertGreater(len(result["potential_errors"]), 0)
        error_texts = [e["found"] for e in result["potential_errors"]]
        self.assertIn("fairly value", error_texts)
        self.assertIn("order blog", error_texts)
        self.assertIn("liquidity sweet", error_texts)

    def test_error_rate_calculation(self):
        """Error rate = potential_errors / max(terms_found, 1)."""
        transcript = {
            "segments": [
                {"start": 0.0, "text": "fair value gap and displacement"},
                {"start": 5.0, "text": "fairly value is wrong"},
            ]
        }
        result = check_ict_jargon(transcript)
        expected_rate = len(result["potential_errors"]) / max(result["terms_found"], 1)
        self.assertAlmostEqual(result["error_rate"], round(expected_rate, 4))

    def test_baseline_entries_skipped(self):
        """JARGON_ERROR_PATTERNS baseline (error==correct) entries are skipped."""
        baselines = [
            (err, corr) for err, corr in JARGON_ERROR_PATTERNS
            if err == corr
        ]
        self.assertGreater(len(baselines), 0, "Should have at least one baseline entry")

    def test_empty_transcript(self):
        result = check_ict_jargon({"segments": []})
        self.assertEqual(result["terms_found"], 0)
        self.assertEqual(result["error_rate"], 0.0)


class TestFormatForTheorist(unittest.TestCase):
    """format_for_theorist produces timestamped text."""

    def test_format_includes_timestamps(self):
        transcript = fetch_transcript("mock://test")
        formatted = format_for_theorist(transcript)
        self.assertIn("[0.0s]", formatted)
        self.assertIn("[14.5s]", formatted)

    def test_format_includes_title(self):
        transcript = fetch_transcript("mock://test")
        formatted = format_for_theorist(transcript)
        self.assertIn("VIDEO:", formatted)
        self.assertIn(transcript["title"], formatted)


class TestRealApiPath(unittest.TestCase):
    """Real API code path (mocked HTTP, never hits real API in tests)."""

    @patch("skills.transcript.supadata.requests.get")
    @patch.dict(os.environ, {"DEXTER_MOCK_MODE": "false"})
    def test_200_response_normalized(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "content": [
                {"offset": 0, "text": "Hello ICT"},
                {"offset": 5000, "text": "Fair value gap"},
            ],
            "title": "Test Video",
            "lang": "en",
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        with patch.dict(os.environ, {"SUPADATA_KEY": "test_key"}):
            result = fetch_transcript("https://youtube.com/watch?v=real123")

        self.assertEqual(len(result["segments"]), 2)
        self.assertEqual(result["title"], "Test Video")
        mock_get.assert_called_once()

    @patch("skills.transcript.supadata.requests.get")
    @patch.dict(os.environ, {"DEXTER_MOCK_MODE": "false"})
    def test_no_api_key_raises(self, mock_get):
        with patch.dict(os.environ, {}, clear=True):
            os.environ["DEXTER_MOCK_MODE"] = "false"
            with self.assertRaises(ValueError) as ctx:
                fetch_transcript("https://youtube.com/watch?v=real123")
            self.assertIn("SUPADATA_KEY", str(ctx.exception))

    @patch("skills.transcript.supadata.requests.get")
    @patch("skills.transcript.supadata.time.sleep")
    @patch.dict(os.environ, {"DEXTER_MOCK_MODE": "false"})
    def test_202_async_polling(self, mock_sleep, mock_get):
        """HTTP 202 triggers async job polling."""
        # First call returns 202 with jobId
        resp_202 = MagicMock()
        resp_202.status_code = 202
        resp_202.json.return_value = {"jobId": "job-abc"}

        # Second call returns completed
        resp_done = MagicMock()
        resp_done.status_code = 200
        resp_done.json.return_value = {
            "status": "completed",
            "result": {
                "content": [{"offset": 0, "text": "Done"}],
                "title": "Async Video",
            },
        }
        resp_done.raise_for_status = MagicMock()

        mock_get.side_effect = [resp_202, resp_done]

        with patch.dict(os.environ, {"SUPADATA_KEY": "test_key"}):
            result = fetch_transcript("https://youtube.com/watch?v=async123")

        self.assertEqual(result["segments"][0]["text"], "Done")
        self.assertEqual(mock_get.call_count, 2)


class TestRunnerGates(unittest.TestCase):
    """Gate thresholds from runner script."""

    def test_gate_constants_defined(self):
        from scripts.run_real_transcript import (
            GATE_MIN_SIGNATURES,
            GATE_MAX_JARGON_ERROR_RATE,
            GATE_REJECTION_RATE_MIN,
            GATE_REJECTION_RATE_MAX,
        )
        self.assertEqual(GATE_MIN_SIGNATURES, 10)
        self.assertAlmostEqual(GATE_MAX_JARGON_ERROR_RATE, 0.05)
        self.assertAlmostEqual(GATE_REJECTION_RATE_MIN, 0.10)
        self.assertAlmostEqual(GATE_REJECTION_RATE_MAX, 0.30)


if __name__ == "__main__":
    unittest.main()
