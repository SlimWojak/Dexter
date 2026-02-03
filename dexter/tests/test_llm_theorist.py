"""Tests for LLM Theorist extraction (Phase 5).

Tests cover:
- JSON parsing from LLM responses (plain, code-block wrapped)
- Deduplication across chunks
- Negative context prepending
- Signature format validation
- Error handling (bad JSON, API errors)
"""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch, MagicMock

# Ensure mock mode for tests
os.environ.setdefault("DEXTER_MOCK_MODE", "true")

from core.theorist import (
    _parse_llm_json,
    _extract_llm,
    _is_llm_mode,
    THEORIST_SYSTEM_PROMPT,
    THEORIST_MODEL,
)


class TestParseLlmJson(unittest.TestCase):
    """Test JSON parsing from LLM responses."""

    def test_plain_json_array(self):
        content = '[{"if": "price breaks", "then": "enter long"}]'
        result = _parse_llm_json(content)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["if"], "price breaks")

    def test_json_in_code_block(self):
        content = '```json\n[{"if": "FVG forms", "then": "wait for retest"}]\n```'
        result = _parse_llm_json(content)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["if"], "FVG forms")

    def test_empty_array(self):
        result = _parse_llm_json("[]")
        self.assertEqual(result, [])

    def test_code_block_with_language_tag(self):
        content = '```json\n[\n  {"if": "OB forms", "then": "mark level"}\n]\n```'
        result = _parse_llm_json(content)
        self.assertEqual(len(result), 1)

    def test_non_array_returns_empty(self):
        content = '{"if": "single object, not array"}'
        result = _parse_llm_json(content)
        self.assertEqual(result, [])

    def test_invalid_json_raises(self):
        with self.assertRaises(json.JSONDecodeError):
            _parse_llm_json("not json at all")

    def test_whitespace_handling(self):
        content = '  \n  [{"if": "a", "then": "b"}]  \n  '
        result = _parse_llm_json(content)
        self.assertEqual(len(result), 1)


class TestExtractLlm(unittest.TestCase):
    """Test LLM extraction pipeline (mocked API)."""

    def _mock_chunks(self, n=2):
        return [
            {"start": i * 300.0, "end": (i + 1) * 300.0, "text": f"Chunk {i} text"}
            for i in range(n)
        ]

    def _mock_llm_response(self, signatures):
        return {
            "content": json.dumps(signatures),
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
            "model": "deepseek/deepseek-chat",
        }

    @patch("core.llm_client.call_llm")
    def test_basic_extraction(self, mock_call):
        sigs = [{"if": "price sweeps lows", "then": "look for FVG", "timestamp": "5:00", "confidence": "EXPLICIT"}]
        mock_call.return_value = self._mock_llm_response(sigs)

        result = _extract_llm(self._mock_chunks(1), None, "Test Video")
        self.assertEqual(len(result), 1)
        self.assertIn("IF", result[0]["condition"])
        self.assertIn("THEN", result[0]["action"])

    @patch("core.llm_client.call_llm")
    def test_dedup_across_chunks(self, mock_call):
        """Same logic in two chunks should be deduplicated."""
        sigs = [{"if": "price breaks above", "then": "go long", "timestamp": "1:00"}]
        mock_call.return_value = self._mock_llm_response(sigs)

        result = _extract_llm(self._mock_chunks(3), None, "Test Video")
        # Same signature repeated 3 times but dedup should keep only 1
        self.assertEqual(len(result), 1)

    @patch("core.llm_client.call_llm")
    def test_unique_signatures_preserved(self, mock_call):
        responses = [
            self._mock_llm_response([{"if": "FVG forms", "then": "enter", "timestamp": "1:00"}]),
            self._mock_llm_response([{"if": "OB holds", "then": "scale in", "timestamp": "6:00"}]),
        ]
        mock_call.side_effect = responses

        result = _extract_llm(self._mock_chunks(2), None, "Test Video")
        self.assertEqual(len(result), 2)

    @patch("core.llm_client.call_llm")
    def test_signature_id_format(self, mock_call):
        sigs = [{"if": "a", "then": "b", "timestamp": "1:00"}]
        mock_call.return_value = self._mock_llm_response(sigs)

        result = _extract_llm(self._mock_chunks(1), None, "Test")
        self.assertTrue(result[0]["id"].startswith("S-"))

    @patch("core.llm_client.call_llm")
    def test_negative_context_passed(self, mock_call):
        sigs = [{"if": "x", "then": "y", "timestamp": "0:00"}]
        mock_call.return_value = self._mock_llm_response(sigs)

        negatives = [
            {"id": "NB-001", "reason": "unfalsifiable absolute claim"},
        ]
        _extract_llm(self._mock_chunks(1), negatives, "Test")

        # Verify call_llm was called — the negative context is embedded in system_prompt
        # inside _extract_llm, so we check the system_prompt arg
        call_args = mock_call.call_args
        system_prompt = call_args.kwargs.get("system_prompt", "")
        self.assertIn("unfalsifiable", system_prompt)

    @patch("core.llm_client.call_llm")
    def test_bad_json_skips_chunk(self, mock_call):
        """Chunk with bad JSON response should be skipped, not crash."""
        mock_call.return_value = {"content": "not valid json", "usage": {}, "model": "test"}
        result = _extract_llm(self._mock_chunks(1), None, "Test")
        self.assertEqual(len(result), 0)

    @patch("core.llm_client.call_llm")
    def test_api_error_skips_chunk(self, mock_call):
        """API error should skip chunk, not crash."""
        mock_call.side_effect = Exception("Connection error")
        result = _extract_llm(self._mock_chunks(1), None, "Test")
        self.assertEqual(len(result), 0)

    @patch("core.llm_client.call_llm")
    def test_source_quote_truncated(self, mock_call):
        long_quote = "x" * 500
        sigs = [{"if": "a", "then": "b", "source_quote": long_quote, "timestamp": "0:00"}]
        mock_call.return_value = self._mock_llm_response(sigs)

        result = _extract_llm(self._mock_chunks(1), None, "Test")
        self.assertLessEqual(len(result[0]["source_quote"]), 200)


class TestLlmMode(unittest.TestCase):
    """Test LLM mode detection."""

    @patch.dict(os.environ, {"DEXTER_LLM_MODE": "false"})
    def test_llm_mode_false(self):
        self.assertFalse(_is_llm_mode())

    @patch.dict(os.environ, {"DEXTER_LLM_MODE": "true"})
    def test_llm_mode_true(self):
        self.assertTrue(_is_llm_mode())

    @patch.dict(os.environ, {}, clear=True)
    def test_llm_mode_default_false(self):
        # Remove the key entirely
        os.environ.pop("DEXTER_LLM_MODE", None)
        self.assertFalse(_is_llm_mode())


class TestTheoristSystemPrompt(unittest.TestCase):
    """Test system prompt content."""

    def test_contains_negative_context_placeholder(self):
        self.assertIn("{negative_context}", THEORIST_SYSTEM_PROMPT)

    def test_contains_ict_jargon(self):
        for term in ["FVG", "OB", "MSS", "Killzone", "OTE"]:
            self.assertIn(term, THEORIST_SYSTEM_PROMPT)

    def test_contains_json_format_spec(self):
        self.assertIn("JSON", THEORIST_SYSTEM_PROMPT)

    def test_model_is_deepseek(self):
        self.assertIn("deepseek", THEORIST_MODEL)


if __name__ == "__main__":
    unittest.main()
