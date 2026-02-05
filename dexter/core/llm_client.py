"""LLM client with tier-based model routing.

Supports:
- OpenRouter for commodity tiers (LATERAL, ICT_LEARNING)
- Anthropic direct API for premium tiers (OLYA_PRIMARY, CANON)
- Per-role model selection with cross-family diversity
- Rate-limit fallback, per-call cost logging
- Source tier awareness for extraction quality routing
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger("dexter.llm_client")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"

# =============================================================================
# TIER-BASED MODEL ROUTING (P3.4)
# =============================================================================
# Source tier determines extraction quality model:
# - OLYA_PRIMARY: Opus (highest quality for Olya's personal notes)
# - CANON: Sonnet (high quality for canonical methodology)
# - LATERAL/ICT_LEARNING: DeepSeek (cost-effective for bulk)
#
# Auditor and Bundler use same models across all tiers (cross-family check)

TIER_MODEL_ROUTING: Dict[str, Dict] = {
    "OLYA_PRIMARY": {
        "theorist": {
            "model": "claude-opus-4-5-20251101",
            "provider": "anthropic",
            "family": "anthropic",
            "temperature": 0.2,
            "max_tokens": 4096,
        },
    },
    "CANON": {
        "theorist": {
            "model": "claude-sonnet-4-5-20250929",
            "provider": "anthropic",
            "family": "anthropic",
            "temperature": 0.2,
            "max_tokens": 4096,
        },
    },
    "LATERAL": {
        "theorist": {
            "model": "deepseek/deepseek-chat",
            "provider": "openrouter",
            "family": "deepseek",
            "temperature": 0.2,
            "max_tokens": 4096,
        },
    },
    "ICT_LEARNING": {
        "theorist": {
            "model": "deepseek/deepseek-chat",
            "provider": "openrouter",
            "family": "deepseek",
            "temperature": 0.2,
            "max_tokens": 4096,
        },
    },
}

# Default routing for non-tier-aware calls (auditor, bundler, etc.)
MODEL_ROUTING: Dict[str, Dict] = {
    "theorist": {
        "model": "deepseek/deepseek-chat",
        "provider": "openrouter",
        "family": "deepseek",
        "temperature": 0.2,
        "max_tokens": 4096,
    },
    "auditor": {
        "model": "google/gemini-2.0-flash-exp",
        "provider": "openrouter",
        "family": "google",
        "temperature": 0.1,
        "max_tokens": 2048,
    },
    "bundler": {
        "model": "deepseek/deepseek-chat",
        "provider": "openrouter",
        "family": "deepseek",
        "temperature": 0.0,
        "max_tokens": 4096,
    },
    "chronicler": {
        "model": "google/gemini-2.0-flash-exp",
        "provider": "openrouter",
        "family": "google",
        "temperature": 0.3,
        "max_tokens": 4096,
    },
    "cartographer": {
        "model": "google/gemini-2.0-flash-exp",
        "provider": "openrouter",
        "family": "google",
        "temperature": 0.1,
        "max_tokens": 2048,
    },
    "vision_extract": {
        "model": "google/gemini-2.0-flash-exp",
        "provider": "openrouter",
        "family": "google",
        "temperature": 0.0,  # Deterministic for OCR
        "max_tokens": 4096,
    },
    "default": {
        "model": "deepseek/deepseek-chat",
        "provider": "openrouter",
        "family": "deepseek",
        "temperature": 0.3,
        "max_tokens": 2048,
    },
}

# Approximate cost per 1M tokens (USD) — Feb 2026
MODEL_COSTS: Dict[str, Dict[str, float]] = {
    "deepseek/deepseek-chat": {"input": 0.14, "output": 0.28},
    "google/gemini-2.0-flash-exp": {"input": 0.10, "output": 0.40},
    "claude-opus-4-5-20251101": {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},
}


def _get_openrouter_key() -> Optional[str]:
    """Get OpenRouter API key from environment."""
    return os.getenv("OPENROUTER_KEY") or os.getenv("OPENROUTER_API_KEY")


def _get_anthropic_key() -> Optional[str]:
    """Get Anthropic API key from environment."""
    return os.getenv("ANTHROPIC_API_KEY")


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
    """Log estimated cost for a call and record to guard manager."""
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

    # Record cost to guard manager (P6 cost ceiling)
    try:
        from core.loop import record_llm_cost
        record_llm_cost(cost, model)
    except ImportError:
        pass  # Guard integration not available (e.g., in tests)


def _make_openrouter_request(
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


def _make_anthropic_request(
    client: httpx.Client,
    model: str,
    system_prompt: str,
    user_content: str,
    temperature: float,
    max_tokens: int,
    api_key: str,
) -> httpx.Response:
    """Make a single Anthropic direct API request."""
    return client.post(
        ANTHROPIC_BASE_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_API_VERSION,
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_content},
            ],
        },
    )


def _parse_anthropic_response(data: Dict) -> tuple[str, Dict]:
    """Parse Anthropic API response into content and usage.

    Returns:
        (content_text, usage_dict)
    """
    content_blocks = data.get("content", [])
    content = ""
    for block in content_blocks:
        if block.get("type") == "text":
            content += block.get("text", "")

    usage = data.get("usage", {})
    # Anthropic uses input_tokens/output_tokens, normalize to OpenRouter format
    normalized_usage = {
        "prompt_tokens": usage.get("input_tokens", 0),
        "completion_tokens": usage.get("output_tokens", 0),
    }

    return content, normalized_usage


def call_llm(
    model: str,
    system_prompt: str,
    user_content: str,
    *,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    timeout: float = 120.0,
    provider: str = "openrouter",
) -> Dict:
    """Call LLM API with specified model and provider.

    Args:
        model: Model identifier
        system_prompt: System prompt
        user_content: User message content
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        timeout: Request timeout in seconds
        provider: "openrouter" or "anthropic"

    Returns:
        {"content": str, "usage": dict, "model": str, "provider": str}
    """
    if provider == "anthropic":
        return _call_anthropic(
            model, system_prompt, user_content,
            temperature=temperature, max_tokens=max_tokens, timeout=timeout,
        )
    else:
        return _call_openrouter(
            model, system_prompt, user_content,
            temperature=temperature, max_tokens=max_tokens, timeout=timeout,
        )


def _call_openrouter(
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
    """
    api_key = _get_openrouter_key()
    if not api_key:
        raise ValueError(
            "OPENROUTER_KEY not set in environment. "
            "Set DEXTER_LLM_MODE=false for local pattern extraction."
        )

    with httpx.Client(timeout=timeout) as client:
        response = _make_openrouter_request(
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
            response = _make_openrouter_request(
                client, fallback_model, system_prompt, user_content,
                temperature, max_tokens, api_key,
            )
            model = fallback_model

        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        usage = data.get("usage", {})
        logger.info(
            "[LLM] provider=openrouter model=%s tokens_in=%s tokens_out=%s",
            model,
            usage.get("prompt_tokens"),
            usage.get("completion_tokens"),
        )
        _log_cost(model, usage)

        return {"content": content, "usage": usage, "model": model, "provider": "openrouter"}


def _call_anthropic(
    model: str,
    system_prompt: str,
    user_content: str,
    *,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    timeout: float = 120.0,
) -> Dict:
    """Call Anthropic direct API with specified model.

    No fallback — for premium tiers, quality > completion.
    """
    api_key = _get_anthropic_key()
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not set in environment. "
            "Required for OLYA_PRIMARY and CANON tier extraction."
        )

    with httpx.Client(timeout=timeout) as client:
        response = _make_anthropic_request(
            client, model, system_prompt, user_content,
            temperature, max_tokens, api_key,
        )

        # No fallback for Anthropic — quality matters more than completion
        if response.status_code == 429:
            logger.error(
                "[LLM] 429 rate limit on Anthropic %s. No fallback for premium tiers.",
                model,
            )
            raise RuntimeError(f"Anthropic rate limit on {model}. Wait and retry.")

        response.raise_for_status()

        data = response.json()
        content, usage = _parse_anthropic_response(data)

        logger.info(
            "[LLM] provider=anthropic model=%s tokens_in=%s tokens_out=%s",
            model,
            usage.get("prompt_tokens"),
            usage.get("completion_tokens"),
        )
        _log_cost(model, usage)

        return {"content": content, "usage": usage, "model": model, "provider": "anthropic"}


def get_tier_model_config(role: str, source_tier: Optional[str] = None) -> Dict:
    """Get model configuration for role, optionally adjusted by source tier.

    For Theorist role, source tier determines model quality:
    - OLYA_PRIMARY → Opus (highest quality)
    - CANON → Sonnet (high quality)
    - LATERAL/ICT_LEARNING → DeepSeek (cost-effective)

    Other roles (Auditor, Bundler, etc.) use default routing regardless of tier.
    """
    # Check if tier-specific routing applies for this role
    if source_tier and source_tier in TIER_MODEL_ROUTING:
        tier_config = TIER_MODEL_ROUTING[source_tier]
        if role in tier_config:
            return dict(tier_config[role])  # copy to prevent mutation

    # Fall back to default role-based routing
    return get_model_config(role)


def call_llm_for_role(
    role: str,
    system_prompt: str,
    user_content: str,
    *,
    override_model: Optional[str] = None,
    source_tier: Optional[str] = None,
    timeout: float = 120.0,
) -> Dict:
    """Call LLM with role-based model routing, optionally tier-aware.

    Args:
        role: Role name (theorist, auditor, bundler, etc.)
        system_prompt: System prompt
        user_content: User message content
        override_model: Override model selection
        source_tier: Source tier for tier-aware routing (OLYA_PRIMARY, CANON, etc.)
        timeout: Request timeout

    Returns:
        {"content": str, "usage": dict, "model": str, "family": str, "role": str,
         "provider": str, "source_tier": str|None}
    """
    config = get_tier_model_config(role, source_tier)
    model = override_model or config["model"]
    provider = config.get("provider", "openrouter")

    result = call_llm(
        model=model,
        system_prompt=system_prompt,
        user_content=user_content,
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
        timeout=timeout,
        provider=provider,
    )

    result["family"] = config["family"]
    result["role"] = role
    result["source_tier"] = source_tier

    logger.info(
        "[ROUTING] role=%s tier=%s model=%s family=%s provider=%s",
        role, source_tier or "default", model, config["family"], provider,
    )

    return result


def call_vision_extract(
    image_base64: str,
    prompt: str,
    *,
    timeout: float = 60.0,
) -> Dict:
    """Call Claude Vision for image text extraction (OCR).

    Uses Claude Sonnet via Anthropic direct API with image input.
    Fast and cost-effective for OCR tasks.

    Args:
        image_base64: Base64-encoded image data (PNG or JPEG)
        prompt: Extraction prompt
        timeout: Request timeout

    Returns:
        {"content": str, "usage": dict, "model": str}
    """
    api_key = _get_anthropic_key()
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set for vision extraction")

    # Use Sonnet for vision (good quality, lower cost than Opus)
    model = "claude-sonnet-4-5-20250929"

    # Build Anthropic-format message with image
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_base64,
                    },
                },
                {
                    "type": "text",
                    "text": prompt,
                },
            ],
        }
    ]

    with httpx.Client(timeout=timeout) as client:
        response = client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": 4096,
            },
        )

        if response.status_code == 429:
            logger.warning("[VISION] Rate limited, waiting 5s...")
            import time
            time.sleep(5)
            response = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 4096,
                },
            )

        response.raise_for_status()
        data = response.json()

        # Parse Anthropic response format
        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        usage = data.get("usage", {})
        normalized_usage = {
            "prompt_tokens": usage.get("input_tokens", 0),
            "completion_tokens": usage.get("output_tokens", 0),
        }

        _log_cost(model, normalized_usage)

        logger.info(
            "[VISION] model=%s tokens_in=%s tokens_out=%s",
            model, normalized_usage.get("prompt_tokens", "?"),
            normalized_usage.get("completion_tokens", "?"),
        )

        return {
            "content": content,
            "usage": normalized_usage,
            "model": model,
        }


# =============================================================================
# 5-DRAWER REFERENCE CONTEXT LOADER
# =============================================================================

_DRAWER_YAML_DIR = Path(__file__).resolve().parent.parent / "data" / "sources" / "5_drawer_YAML_files"
_DRAWER_CONTEXT_CACHE: Optional[str] = None


def load_drawer_reference_context(max_chars: int = 8000) -> str:
    """Load 5-drawer YAMLs as Theorist reference context.

    Returns a condensed summary of the drawer taxonomy for the Theorist
    to understand drawer classification. Does NOT include full YAML contents
    (would blow context limits).

    Args:
        max_chars: Maximum characters for the context block

    Returns:
        Drawer reference context string for system prompt injection
    """
    global _DRAWER_CONTEXT_CACHE

    if _DRAWER_CONTEXT_CACHE is not None:
        return _DRAWER_CONTEXT_CACHE

    if not _DRAWER_YAML_DIR.exists():
        logger.warning("[DRAWER] 5-drawer YAML dir not found: %s", _DRAWER_YAML_DIR)
        _DRAWER_CONTEXT_CACHE = ""
        return ""

    # Build condensed reference from index.yaml
    index_file = _DRAWER_YAML_DIR / "index.yaml"
    if not index_file.exists():
        logger.warning("[DRAWER] index.yaml not found")
        _DRAWER_CONTEXT_CACHE = ""
        return ""

    try:
        import yaml
        with open(index_file) as f:
            index = yaml.safe_load(f)

        drawers = index.get("drawers", [])

        lines = [
            "## 5-DRAWER TAXONOMY REFERENCE",
            "When classifying extracted IF-THEN signatures, use these drawer categories:",
            "",
        ]

        for d in drawers:
            drawer_num = d.get("drawer", "?")
            name = d.get("name", "?").upper()
            question = d.get("question", "?")
            contains = d.get("contains", [])

            lines.append(f"### DRAWER {drawer_num}: {name}")
            lines.append(f"Question: {question}")
            if contains:
                lines.append("Contains: " + ", ".join(str(c)[:50] for c in contains[:5]))
            lines.append("")

        context = "\n".join(lines)

        # Truncate if needed
        if len(context) > max_chars:
            context = context[:max_chars] + "\n[TRUNCATED]"

        _DRAWER_CONTEXT_CACHE = context
        logger.info("[DRAWER] Loaded reference context: %d chars", len(context))
        return context

    except Exception as e:
        logger.exception("[DRAWER] Failed to load reference context: %s", e)
        _DRAWER_CONTEXT_CACHE = ""
        return ""


def clear_drawer_context_cache() -> None:
    """Clear the cached drawer context (for testing)."""
    global _DRAWER_CONTEXT_CACHE
    _DRAWER_CONTEXT_CACHE = None
