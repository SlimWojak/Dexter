"""OpenRouter LLM client with role-based model routing.

Phase 5: synchronous httpx client for compatibility with existing pipeline.
Supports per-role model selection, cross-family diversity validation,
rate-limit fallback, and per-call cost logging.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger("dexter.llm_client")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Role-based model routing — v0.2 spec
# Temperature rationale:
#   theorist  0.2 — slight creativity for edge-case if-then capture
#   auditor   0.1 — very low for deterministic falsification
#   bundler   0.0 — zero variance on template fill
#   chronicler 0.3 — enough diversity for summarization without drift
#   cartographer 0.1 — metadata categorization, cheap/fast
MODEL_ROUTING: Dict[str, Dict] = {
    "theorist": {
        "model": "deepseek/deepseek-chat",
        "family": "deepseek",
        "temperature": 0.2,
        "max_tokens": 4096,
    },
    "auditor": {
        "model": "google/gemini-2.0-flash-exp",
        "family": "google",
        "temperature": 0.1,
        "max_tokens": 2048,
    },
    "bundler": {
        "model": "deepseek/deepseek-chat",
        "family": "deepseek",
        "temperature": 0.0,
        "max_tokens": 4096,
    },
    "chronicler": {
        "model": "google/gemini-2.0-flash-exp",
        "family": "google",
        "temperature": 0.3,
        "max_tokens": 4096,
    },
    "cartographer": {
        "model": "google/gemini-2.0-flash-exp",
        "family": "google",
        "temperature": 0.1,
        "max_tokens": 2048,
    },
    "default": {
        "model": "deepseek/deepseek-chat",
        "family": "deepseek",
        "temperature": 0.3,
        "max_tokens": 2048,
    },
}

# Approximate cost per 1M tokens (USD) — Feb 2026
MODEL_COSTS: Dict[str, Dict[str, float]] = {
    "deepseek/deepseek-chat": {"input": 0.14, "output": 0.28},
    "google/gemini-2.0-flash-exp": {"input": 0.10, "output": 0.40},
}


def _get_api_key() -> Optional[str]:
    """Get OpenRouter API key from environment."""
    return os.getenv("OPENROUTER_KEY") or os.getenv("OPENROUTER_API_KEY")


def get_model_config(role: str) -> Dict:
    """Get model configuration for a role."""
    config = MODEL_ROUTING.get(role, MODEL_ROUTING["default"])
    return dict(config)  # copy to prevent mutation


def validate_model_diversity(dispatch_log: List[Dict]) -> Dict:
    """Validate Theorist and Auditor use different model families."""
    theorist_family = None
    auditor_family = None

    for entry in dispatch_log:
        if entry.get("role") == "theorist":
            theorist_family = entry.get("family")
        elif entry.get("role") == "auditor":
            auditor_family = entry.get("family")

    diverse = (
        theorist_family is not None
        and auditor_family is not None
        and theorist_family != auditor_family
    )

    return {
        "diverse": diverse,
        "theorist_family": theorist_family,
        "auditor_family": auditor_family,
    }


def _log_cost(model: str, usage: Dict) -> None:
    """Log estimated cost for a call."""
    costs = MODEL_COSTS.get(model)
    if not costs:
        return
    input_tokens = usage.get("prompt_tokens", 0) or 0
    output_tokens = usage.get("completion_tokens", 0) or 0
    cost = (
        (input_tokens / 1_000_000 * costs["input"])
        + (output_tokens / 1_000_000 * costs["output"])
    )
    logger.info("[COST] model=%s cost=$%.6f (in=%d out=%d)", model, cost, input_tokens, output_tokens)


def _make_request(
    client: httpx.Client,
    model: str,
    system_prompt: str,
    user_content: str,
    temperature: float,
    max_tokens: int,
    api_key: str,
) -> httpx.Response:
    """Make a single OpenRouter API request."""
    return client.post(
        OPENROUTER_BASE_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/SlimWojak/Dexter",
            "X-Title": "Dexter Evidence Refinery",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
    )


def call_llm(
    model: str,
    system_prompt: str,
    user_content: str,
    *,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    timeout: float = 120.0,
) -> Dict:
    """Call OpenRouter API with specified model.

    Includes rate-limit fallback: on 429, waits 5s and retries with default model.

    Returns:
        {"content": str, "usage": dict, "model": str}
    """
    api_key = _get_api_key()
    if not api_key:
        raise ValueError(
            "OPENROUTER_KEY not set in environment. "
            "Set DEXTER_LLM_MODE=false for local pattern extraction."
        )

    with httpx.Client(timeout=timeout) as client:
        response = _make_request(
            client, model, system_prompt, user_content,
            temperature, max_tokens, api_key,
        )

        # Rate-limit fallback
        if response.status_code == 429:
            fallback_model = MODEL_ROUTING["default"]["model"]
            logger.warning(
                "[LLM] 429 rate limit on %s. Retrying with %s after 5s.",
                model, fallback_model,
            )
            time.sleep(5)
            response = _make_request(
                client, fallback_model, system_prompt, user_content,
                temperature, max_tokens, api_key,
            )
            model = fallback_model

        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        usage = data.get("usage", {})
        logger.info(
            "[LLM] model=%s tokens_in=%s tokens_out=%s",
            model,
            usage.get("prompt_tokens"),
            usage.get("completion_tokens"),
        )
        _log_cost(model, usage)

        return {"content": content, "usage": usage, "model": model}


def call_llm_for_role(
    role: str,
    system_prompt: str,
    user_content: str,
    *,
    override_model: Optional[str] = None,
    timeout: float = 120.0,
) -> Dict:
    """Call LLM with role-based model routing.

    Selects model/temperature/max_tokens from MODEL_ROUTING based on role.

    Returns:
        {"content": str, "usage": dict, "model": str, "family": str, "role": str}
    """
    config = get_model_config(role)
    model = override_model or config["model"]

    result = call_llm(
        model=model,
        system_prompt=system_prompt,
        user_content=user_content,
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
        timeout=timeout,
    )

    result["family"] = config["family"]
    result["role"] = role

    logger.info(
        "[ROUTING] role=%s model=%s family=%s",
        role, model, config["family"],
    )

    return result
