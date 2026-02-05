"""Tests for tier-based model routing (P3.4).

Tests:
- Tier model config selection
- Anthropic vs OpenRouter provider routing
- Drawer reference context loading
- Source tier in CLAIM_BEADs
"""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.llm_client import (
    TIER_MODEL_ROUTING,
    MODEL_ROUTING,
    get_model_config,
    get_tier_model_config,
    load_drawer_reference_context,
    clear_drawer_context_cache,
    _parse_anthropic_response,
)


class TestTierModelRouting(unittest.TestCase):
    """Test tier-based model configuration."""

    def test_olya_primary_uses_opus(self):
        """OLYA_PRIMARY tier should use Opus for Theorist."""
        config = get_tier_model_config("theorist", "OLYA_PRIMARY")
        self.assertEqual(config["model"], "claude-opus-4-5-20251101")
        self.assertEqual(config["provider"], "anthropic")
        self.assertEqual(config["family"], "anthropic")

    def test_canon_uses_sonnet(self):
        """CANON tier should use Sonnet for Theorist."""
        config = get_tier_model_config("theorist", "CANON")
        self.assertEqual(config["model"], "claude-sonnet-4-5-20250929")
        self.assertEqual(config["provider"], "anthropic")
        self.assertEqual(config["family"], "anthropic")

    def test_lateral_uses_deepseek(self):
        """LATERAL tier should use DeepSeek for Theorist."""
        config = get_tier_model_config("theorist", "LATERAL")
        self.assertEqual(config["model"], "deepseek/deepseek-chat")
        self.assertEqual(config["provider"], "openrouter")
        self.assertEqual(config["family"], "deepseek")

    def test_ict_learning_uses_deepseek(self):
        """ICT_LEARNING tier should use DeepSeek for Theorist."""
        config = get_tier_model_config("theorist", "ICT_LEARNING")
        self.assertEqual(config["model"], "deepseek/deepseek-chat")
        self.assertEqual(config["provider"], "openrouter")

    def test_auditor_unchanged_across_tiers(self):
        """Auditor should use same model regardless of tier."""
        for tier in ["OLYA_PRIMARY", "CANON", "LATERAL", "ICT_LEARNING"]:
            config = get_tier_model_config("auditor", tier)
            self.assertEqual(config["model"], "google/gemini-2.0-flash-exp")
            self.assertEqual(config["family"], "google")

    def test_bundler_unchanged_across_tiers(self):
        """Bundler should use same model regardless of tier."""
        for tier in ["OLYA_PRIMARY", "CANON", "LATERAL", "ICT_LEARNING"]:
            config = get_tier_model_config("bundler", tier)
            self.assertEqual(config["model"], "deepseek/deepseek-chat")

    def test_no_tier_falls_back_to_default(self):
        """No tier should fall back to default MODEL_ROUTING."""
        config = get_tier_model_config("theorist", None)
        default_config = get_model_config("theorist")
        self.assertEqual(config["model"], default_config["model"])

    def test_unknown_tier_falls_back_to_default(self):
        """Unknown tier should fall back to default MODEL_ROUTING."""
        config = get_tier_model_config("theorist", "UNKNOWN_TIER")
        default_config = get_model_config("theorist")
        self.assertEqual(config["model"], default_config["model"])

    def test_config_is_copy(self):
        """Config returned should be a copy to prevent mutation."""
        config1 = get_tier_model_config("theorist", "OLYA_PRIMARY")
        config1["model"] = "mutated"
        config2 = get_tier_model_config("theorist", "OLYA_PRIMARY")
        self.assertEqual(config2["model"], "claude-opus-4-5-20251101")


class TestAnthropicResponseParsing(unittest.TestCase):
    """Test Anthropic API response parsing."""

    def test_parse_text_content(self):
        """Parse simple text content from Anthropic response."""
        data = {
            "content": [
                {"type": "text", "text": "Hello world"}
            ],
            "usage": {"input_tokens": 10, "output_tokens": 5}
        }
        content, usage = _parse_anthropic_response(data)
        self.assertEqual(content, "Hello world")
        self.assertEqual(usage["prompt_tokens"], 10)
        self.assertEqual(usage["completion_tokens"], 5)

    def test_parse_multiple_text_blocks(self):
        """Parse multiple text blocks from Anthropic response."""
        data = {
            "content": [
                {"type": "text", "text": "First "},
                {"type": "text", "text": "Second"}
            ],
            "usage": {"input_tokens": 20, "output_tokens": 10}
        }
        content, usage = _parse_anthropic_response(data)
        self.assertEqual(content, "First Second")

    def test_parse_empty_content(self):
        """Parse empty content list."""
        data = {"content": [], "usage": {}}
        content, usage = _parse_anthropic_response(data)
        self.assertEqual(content, "")
        self.assertEqual(usage["prompt_tokens"], 0)
        self.assertEqual(usage["completion_tokens"], 0)

    def test_parse_missing_usage(self):
        """Handle missing usage field."""
        data = {"content": [{"type": "text", "text": "test"}]}
        content, usage = _parse_anthropic_response(data)
        self.assertEqual(content, "test")
        self.assertEqual(usage["prompt_tokens"], 0)


class TestDrawerReferenceContext(unittest.TestCase):
    """Test 5-drawer reference context loading."""

    def setUp(self):
        clear_drawer_context_cache()

    def tearDown(self):
        clear_drawer_context_cache()

    def test_loads_drawer_context(self):
        """Should load drawer taxonomy from index.yaml."""
        context = load_drawer_reference_context()
        # Should have loaded something
        self.assertGreater(len(context), 0)
        # Should contain drawer references
        self.assertIn("DRAWER", context)
        self.assertIn("TAXONOMY", context)

    def test_caches_context(self):
        """Should cache context after first load."""
        context1 = load_drawer_reference_context()
        context2 = load_drawer_reference_context()
        self.assertEqual(context1, context2)

    def test_respects_max_chars(self):
        """Should truncate if over max_chars."""
        context = load_drawer_reference_context(max_chars=100)
        self.assertLessEqual(len(context), 120)  # Allow for truncation marker

    def test_clear_cache(self):
        """Should clear cache when requested."""
        _ = load_drawer_reference_context()
        clear_drawer_context_cache()
        # Should reload on next call (no error)
        context = load_drawer_reference_context()
        self.assertIsInstance(context, str)


class TestProviderSelection(unittest.TestCase):
    """Test provider selection based on tier."""

    def test_anthropic_provider_for_olya(self):
        """OLYA_PRIMARY should select anthropic provider."""
        config = get_tier_model_config("theorist", "OLYA_PRIMARY")
        self.assertEqual(config["provider"], "anthropic")

    def test_anthropic_provider_for_canon(self):
        """CANON should select anthropic provider."""
        config = get_tier_model_config("theorist", "CANON")
        self.assertEqual(config["provider"], "anthropic")

    def test_openrouter_provider_for_lateral(self):
        """LATERAL should select openrouter provider."""
        config = get_tier_model_config("theorist", "LATERAL")
        self.assertEqual(config["provider"], "openrouter")

    def test_openrouter_provider_for_ict_learning(self):
        """ICT_LEARNING should select openrouter provider."""
        config = get_tier_model_config("theorist", "ICT_LEARNING")
        self.assertEqual(config["provider"], "openrouter")


class TestCrossFamilyDiversity(unittest.TestCase):
    """Test that Theorist and Auditor use different families."""

    def test_olya_tier_maintains_diversity(self):
        """Even with Opus Theorist, Auditor should be different family."""
        theorist = get_tier_model_config("theorist", "OLYA_PRIMARY")
        auditor = get_tier_model_config("auditor", "OLYA_PRIMARY")
        self.assertNotEqual(theorist["family"], auditor["family"])

    def test_canon_tier_maintains_diversity(self):
        """Sonnet Theorist + Google Auditor = different families."""
        theorist = get_tier_model_config("theorist", "CANON")
        auditor = get_tier_model_config("auditor", "CANON")
        self.assertNotEqual(theorist["family"], auditor["family"])

    def test_lateral_tier_maintains_diversity(self):
        """DeepSeek Theorist + Google Auditor = different families."""
        theorist = get_tier_model_config("theorist", "LATERAL")
        auditor = get_tier_model_config("auditor", "LATERAL")
        self.assertNotEqual(theorist["family"], auditor["family"])


if __name__ == "__main__":
    unittest.main()
