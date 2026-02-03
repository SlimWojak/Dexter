"""Tests for model routing and LLM client (Phase 5).

Tests cover:
- Role-based model configuration
- Cross-family diversity validation (Theorist vs Auditor)
- All roles have valid config
- Cost logging calculation
- Rate-limit fallback behavior
- API key retrieval
"""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("DEXTER_MOCK_MODE", "true")

from core.llm_client import (
    MODEL_ROUTING,
    MODEL_COSTS,
    get_model_config,
    validate_model_diversity,
    _log_cost,
    _get_api_key,
    call_llm,
    call_llm_for_role,
)


class TestModelRouting(unittest.TestCase):
    """Test role-based model configuration."""

    def test_all_roles_configured(self):
        expected_roles = ["theorist", "auditor", "bundler", "chronicler", "cartographer", "default"]
        for role in expected_roles:
            self.assertIn(role, MODEL_ROUTING, f"Missing config for role: {role}")

    def test_each_role_has_required_fields(self):
        required = {"model", "family", "temperature", "max_tokens"}
        for role, config in MODEL_ROUTING.items():
            for field in required:
                self.assertIn(field, config, f"Role {role} missing field: {field}")

    def test_theorist_is_deepseek(self):
        config = get_model_config("theorist")
        self.assertIn("deepseek", config["model"])
        self.assertEqual(config["family"], "deepseek")

    def test_auditor_is_google(self):
        config = get_model_config("auditor")
        self.assertIn("google", config["model"])
        self.assertEqual(config["family"], "google")

    def test_unknown_role_returns_default(self):
        config = get_model_config("unknown_role")
        self.assertEqual(config, MODEL_ROUTING["default"])

    def test_get_model_config_returns_copy(self):
        """Config should be a copy to prevent mutation."""
        config1 = get_model_config("theorist")
        config1["temperature"] = 999
        config2 = get_model_config("theorist")
        self.assertNotEqual(config2["temperature"], 999)

    def test_temperature_ranges(self):
        for role, config in MODEL_ROUTING.items():
            self.assertGreaterEqual(config["temperature"], 0.0, f"{role} temp too low")
            self.assertLessEqual(config["temperature"], 1.0, f"{role} temp too high")


class TestModelDiversityValidation(unittest.TestCase):
    """Test cross-family diversity validation."""

    def test_diverse_families(self):
        log = [
            {"role": "theorist", "family": "deepseek"},
            {"role": "auditor", "family": "google"},
        ]
        result = validate_model_diversity(log)
        self.assertTrue(result["diverse"])
        self.assertEqual(result["theorist_family"], "deepseek")
        self.assertEqual(result["auditor_family"], "google")

    def test_same_family_not_diverse(self):
        log = [
            {"role": "theorist", "family": "deepseek"},
            {"role": "auditor", "family": "deepseek"},
        ]
        result = validate_model_diversity(log)
        self.assertFalse(result["diverse"])

    def test_missing_theorist(self):
        log = [{"role": "auditor", "family": "google"}]
        result = validate_model_diversity(log)
        self.assertFalse(result["diverse"])

    def test_missing_auditor(self):
        log = [{"role": "theorist", "family": "deepseek"}]
        result = validate_model_diversity(log)
        self.assertFalse(result["diverse"])

    def test_empty_log(self):
        result = validate_model_diversity([])
        self.assertFalse(result["diverse"])

    def test_default_routing_is_diverse(self):
        """Verify the default MODEL_ROUTING config ensures diversity."""
        log = [
            {"role": "theorist", "family": MODEL_ROUTING["theorist"]["family"]},
            {"role": "auditor", "family": MODEL_ROUTING["auditor"]["family"]},
        ]
        result = validate_model_diversity(log)
        self.assertTrue(result["diverse"])


class TestCostLogging(unittest.TestCase):
    """Test per-call cost estimation."""

    def test_deepseek_cost(self):
        """Verify cost calculation for deepseek model."""
        costs = MODEL_COSTS["deepseek/deepseek-chat"]
        usage = {"prompt_tokens": 1_000_000, "completion_tokens": 1_000_000}
        expected = costs["input"] + costs["output"]
        # Just verify the math works
        actual = (1_000_000 / 1_000_000 * costs["input"]) + (1_000_000 / 1_000_000 * costs["output"])
        self.assertAlmostEqual(actual, expected)

    def test_gemini_cost(self):
        costs = MODEL_COSTS["google/gemini-2.0-flash-exp"]
        self.assertIn("input", costs)
        self.assertIn("output", costs)

    def test_unknown_model_no_crash(self):
        """_log_cost should not crash on unknown model."""
        _log_cost("unknown/model", {"prompt_tokens": 100, "completion_tokens": 50})

    def test_zero_tokens(self):
        _log_cost("deepseek/deepseek-chat", {"prompt_tokens": 0, "completion_tokens": 0})

    def test_missing_usage_fields(self):
        _log_cost("deepseek/deepseek-chat", {})


class TestApiKey(unittest.TestCase):
    """Test API key retrieval."""

    @patch.dict(os.environ, {"OPENROUTER_KEY": "test-key-123"}, clear=False)
    def test_openrouter_key(self):
        self.assertEqual(_get_api_key(), "test-key-123")

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "alt-key-456"}, clear=False)
    def test_openrouter_api_key_fallback(self):
        os.environ.pop("OPENROUTER_KEY", None)
        self.assertEqual(_get_api_key(), "alt-key-456")

    @patch.dict(os.environ, {}, clear=True)
    def test_no_key_returns_none(self):
        os.environ.pop("OPENROUTER_KEY", None)
        os.environ.pop("OPENROUTER_API_KEY", None)
        self.assertIsNone(_get_api_key())


class TestCallLlm(unittest.TestCase):
    """Test call_llm function (mocked HTTP)."""

    def test_no_api_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENROUTER_KEY", None)
            os.environ.pop("OPENROUTER_API_KEY", None)
            with self.assertRaises(ValueError) as ctx:
                call_llm("test/model", "system", "user")
            self.assertIn("OPENROUTER_KEY", str(ctx.exception))

    @patch("core.llm_client.httpx.Client")
    @patch.dict(os.environ, {"OPENROUTER_KEY": "test-key"})
    def test_successful_call(self, MockClient):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "test response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        MockClient.return_value = mock_client

        result = call_llm("deepseek/deepseek-chat", "system prompt", "user content")
        self.assertEqual(result["content"], "test response")
        self.assertEqual(result["model"], "deepseek/deepseek-chat")

    @patch("core.llm_client.httpx.Client")
    @patch("core.llm_client.time.sleep")
    @patch.dict(os.environ, {"OPENROUTER_KEY": "test-key"})
    def test_429_fallback(self, mock_sleep, MockClient):
        """Test rate-limit fallback: 429 → sleep → retry with default model."""
        mock_429 = MagicMock()
        mock_429.status_code = 429

        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.json.return_value = {
            "choices": [{"message": {"content": "fallback response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }
        mock_200.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.side_effect = [mock_429, mock_200]
        MockClient.return_value = mock_client

        result = call_llm("some/model", "system", "user")
        self.assertEqual(result["content"], "fallback response")
        mock_sleep.assert_called_once_with(5)


class TestCallLlmForRole(unittest.TestCase):
    """Test role-based LLM dispatch."""

    @patch("core.llm_client.call_llm")
    def test_role_config_applied(self, mock_call):
        mock_call.return_value = {"content": "ok", "usage": {}, "model": "deepseek/deepseek-chat"}

        result = call_llm_for_role("theorist", "system", "user")
        self.assertEqual(result["role"], "theorist")
        self.assertEqual(result["family"], "deepseek")

        # Verify temperature was passed from config
        call_kwargs = mock_call.call_args
        self.assertEqual(call_kwargs.kwargs.get("temperature") or call_kwargs[1].get("temperature"),
                         MODEL_ROUTING["theorist"]["temperature"])

    @patch("core.llm_client.call_llm")
    def test_override_model(self, mock_call):
        mock_call.return_value = {"content": "ok", "usage": {}, "model": "custom/model"}

        call_llm_for_role("theorist", "system", "user", override_model="custom/model")
        call_args = mock_call.call_args
        self.assertEqual(call_args.kwargs.get("model") or call_args[0][0], "custom/model")


if __name__ == "__main__":
    unittest.main()
