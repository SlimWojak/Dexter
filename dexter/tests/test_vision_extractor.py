"""Tests for P3.5 Vision Extraction Skill."""

import base64
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skills.document.vision_extractor import (
    CHART_DESCRIPTION_PROMPT,
    TRADING_NOTES_PROMPT,
    extract_chart_description,
    extract_notes_description,
    format_vision_for_theorist,
    batch_format_for_theorist,
    load_image_as_base64,
)


class TestVisionPrompts(unittest.TestCase):
    """Test that vision prompts contain expected ICT terminology."""

    def test_chart_prompt_contains_ict_terms(self):
        """Chart prompt should guide extraction of ICT concepts."""
        ict_terms = ["order block", "FVG", "liquidity", "MSS", "fibonacci", "OTE"]
        prompt_lower = CHART_DESCRIPTION_PROMPT.lower()
        for term in ict_terms:
            self.assertIn(term.lower(), prompt_lower,
                         f"Chart prompt should mention {term}")

    def test_notes_prompt_preserves_terminology(self):
        """Notes prompt should preserve exact terminology."""
        self.assertIn("ICT", TRADING_NOTES_PROMPT)
        self.assertIn("preserve", TRADING_NOTES_PROMPT.lower())

    def test_chart_prompt_emphasizes_no_interpretation(self):
        """Chart prompt should not interpret, only describe."""
        self.assertIn("EXACT", CHART_DESCRIPTION_PROMPT.upper())


class TestVisionExtraction(unittest.TestCase):
    """Test vision extraction functions with mocked API."""

    @patch("skills.document.vision_extractor._get_anthropic_key")
    @patch("httpx.Client")
    def test_extract_chart_description_calls_opus_for_olya(
        self, mock_client_class, mock_get_key
    ):
        """OLYA_PRIMARY tier should use Opus model."""
        mock_get_key.return_value = "test-key"

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "Test chart description"}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = extract_chart_description(
            "base64_image_data",
            source_tier="OLYA_PRIMARY",
            use_opus=True,
        )

        # Verify Opus was used
        call_args = mock_client.post.call_args
        request_json = call_args.kwargs.get("json") or call_args[1].get("json")
        self.assertEqual(request_json["model"], "claude-opus-4-5-20251101")
        self.assertEqual(result["source_type"], "VISUAL")

    @patch("skills.document.vision_extractor._get_anthropic_key")
    @patch("httpx.Client")
    def test_extract_chart_description_uses_sonnet_for_lateral(
        self, mock_client_class, mock_get_key
    ):
        """LATERAL tier with use_opus=False should use Sonnet."""
        mock_get_key.return_value = "test-key"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "Chart description"}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = extract_chart_description(
            "base64_image_data",
            source_tier="LATERAL",
            use_opus=False,
        )

        call_args = mock_client.post.call_args
        request_json = call_args.kwargs.get("json") or call_args[1].get("json")
        self.assertEqual(request_json["model"], "claude-sonnet-4-5-20250929")

    @patch("skills.document.vision_extractor._get_anthropic_key")
    def test_extract_chart_raises_without_api_key(self, mock_get_key):
        """Should raise ValueError without API key."""
        mock_get_key.return_value = None

        with self.assertRaises(ValueError) as ctx:
            extract_chart_description("base64_data")

        self.assertIn("ANTHROPIC_API_KEY", str(ctx.exception))


class TestFormatForTheorist(unittest.TestCase):
    """Test formatting vision results for Theorist processing."""

    def test_format_includes_provenance(self):
        """Formatted output should include source provenance."""
        vision_result = {
            "description": "Test chart with +OB marker at 1.1200",
            "source_file": "test.pdf",
            "page_num": 3,
            "source_type": "VISUAL",
        }

        formatted = format_vision_for_theorist(vision_result)

        self.assertIn("[VISUAL CONTENT:", formatted)
        self.assertIn("test.pdf", formatted)
        self.assertIn("page 3", formatted)
        self.assertIn("+OB marker", formatted)

    def test_format_includes_surrounding_text(self):
        """Surrounding text should be included if provided."""
        vision_result = {
            "description": "Chart showing FVG formation",
            "source_file": "notes.pdf",
            "page_num": 1,
        }
        surrounding = "This is the setup checklist:"

        formatted = format_vision_for_theorist(vision_result, surrounding)

        self.assertIn("PAGE TEXT", formatted)
        self.assertIn("checklist", formatted)
        self.assertIn("FVG formation", formatted)

    def test_batch_format_joins_sections(self):
        """Batch formatting should join multiple results."""
        results = [
            {"description": "Chart 1", "page_num": 1, "source_file": "test.pdf"},
            {"description": "Chart 2", "page_num": 2, "source_file": "test.pdf"},
        ]

        formatted = batch_format_for_theorist(results)

        self.assertIn("Chart 1", formatted)
        self.assertIn("Chart 2", formatted)
        self.assertIn("---", formatted)  # Section separator


class TestImageLoading(unittest.TestCase):
    """Test image loading utilities."""

    def test_load_image_raises_for_missing_file(self):
        """Should raise FileNotFoundError for missing file."""
        with self.assertRaises(FileNotFoundError):
            load_image_as_base64(Path("/nonexistent/image.png"))


class TestSourceTypeTagging(unittest.TestCase):
    """Test that source_type: VISUAL flows through correctly."""

    def test_vision_result_has_visual_source_type(self):
        """Vision extraction should tag output as VISUAL."""
        # This is tested in the extraction tests above
        pass

    @patch("skills.document.vision_extractor._get_anthropic_key")
    @patch("httpx.Client")
    def test_notes_extraction_returns_visual_type(
        self, mock_client_class, mock_get_key
    ):
        """Notes extraction should also return VISUAL source_type."""
        mock_get_key.return_value = "test-key"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "Notes content"}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = extract_notes_description("base64_data", source_tier="OLYA_PRIMARY")

        self.assertEqual(result["source_type"], "VISUAL")


if __name__ == "__main__":
    unittest.main()
