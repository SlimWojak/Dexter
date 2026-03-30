"""Frontier model caller — unified interface to external LLM APIs.

Loads API keys from ~/lab/hermes/.env. Each provider has a convenience
function with sensible defaults for its intended use case.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import openai

_ENV_FILE = Path.home() / "lab" / "hermes" / ".env"
_loaded = False


def _ensure_keys():
    """Load API keys from lab env file if not already in environment."""
    global _loaded
    if _loaded:
        return
    if _ENV_FILE.exists():
        for line in _ENV_FILE.read_text().splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, val = line.split("=", 1)
                if val and key not in os.environ:
                    os.environ[key] = val
    _loaded = True


PROVIDERS = {
    "opus": {
        "module": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "env_key": "ANTHROPIC_API_KEY",
    },
    "gpt": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o",
        "env_key": "OPENAI_API_KEY",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
    },
    "perplexity": {
        "base_url": "https://api.perplexity.ai",
        "model": "sonar-pro",
        "env_key": "PERPLEXITY_API_KEY",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-2.0-flash",
        "env_key": "GEMINI_API_KEY",
    },
}


def ask_frontier(
    provider: str,
    prompt: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.3,
) -> str:
    """Call a frontier model. Returns the response text.

    Args:
        provider: One of: opus, gpt, deepseek, perplexity, gemini
        prompt: The user message
        system: Optional system prompt
        model: Override the default model for this provider
        max_tokens: Max response tokens
        temperature: Sampling temperature
    """
    _ensure_keys()

    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider '{provider}'. Use one of: {list(PROVIDERS.keys())}")

    cfg = PROVIDERS[provider]
    api_key = os.environ.get(cfg["env_key"], "")
    if not api_key:
        raise RuntimeError(f"API key not set for {provider} ({cfg['env_key']})")

    use_model = model or cfg["model"]

    # Anthropic uses its own SDK
    if provider == "opus":
        return _call_anthropic(api_key, use_model, prompt, system, max_tokens, temperature)

    # All others use OpenAI-compatible API
    client = openai.OpenAI(api_key=api_key, base_url=cfg["base_url"])
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = client.chat.completions.create(
        model=use_model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message.content


def _call_anthropic(
    api_key: str,
    model: str,
    prompt: str,
    system: Optional[str],
    max_tokens: int,
    temperature: float,
) -> str:
    """Call Anthropic API using their native SDK."""
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    resp = client.messages.create(**kwargs)
    return resp.content[0].text


def ask_opus(prompt: str, system: Optional[str] = None, model: str = "claude-sonnet-4-20250514", **kwargs) -> str:
    """Ask Claude for judgment, overfitting review, or architecture decisions."""
    return ask_frontier("opus", prompt, system=system, model=model, **kwargs)


def ask_gpt(prompt: str, system: Optional[str] = None, model: str = "gpt-4o", **kwargs) -> str:
    """Ask GPT for lateral perspective, pressure testing, or second opinions."""
    return ask_frontier("gpt", prompt, system=system, model=model, **kwargs)


def ask_deepseek(prompt: str, system: Optional[str] = None, model: str = "deepseek-chat", **kwargs) -> str:
    """Ask DeepSeek for coding tasks or computational donkey work."""
    return ask_frontier("deepseek", prompt, system=system, model=model, **kwargs)


def ask_perplexity(prompt: str, system: Optional[str] = None, model: str = "sonar-pro", **kwargs) -> str:
    """Ask Perplexity for research, ICT methodology scanning, academic study."""
    return ask_frontier("perplexity", prompt, system=system, model=model, **kwargs)


def ask_gemini(prompt: str, system: Optional[str] = None, model: str = "gemini-2.0-flash", **kwargs) -> str:
    """Ask Gemini for fast summarisation or bulk processing."""
    return ask_frontier("gemini", prompt, system=system, model=model, **kwargs)
