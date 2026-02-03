"""Role dispatch — routes tasks to role handlers.

Phase 3: mock/local mode with pattern-based handlers.
Phase 5: LLM mode with OpenRouter dispatch, role-based model routing.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from core.context import read_negative_beads
from core.injection_guard import scan as injection_scan, InjectionDetected

logger = logging.getLogger("dexter.router")

ROLES_DIR = Path(__file__).resolve().parent.parent / "roles"

_role_cache: Dict[str, Dict] = {}


def _load_role(name: str) -> Dict:
    if name in _role_cache:
        return _role_cache[name]
    path = ROLES_DIR / f"{name}.yaml"
    if not path.exists():
        logger.warning("Role manifest not found: %s", path)
        return {"name": name, "status": "not_configured"}
    with open(path) as f:
        manifest = yaml.safe_load(f) or {}
    manifest["name"] = name
    _role_cache[name] = manifest
    return manifest


def clear_cache() -> None:
    """Clear role manifest cache (useful for tests)."""
    _role_cache.clear()


def list_roles() -> List[str]:
    """List available role names from roles/ directory."""
    if not ROLES_DIR.exists():
        return []
    return [p.stem for p in ROLES_DIR.glob("*.yaml")]


def _prepend_negative_context(payload: Dict) -> Dict:
    """Prepend last 10 negative beads as context for Theorist."""
    negatives = read_negative_beads(limit=10)
    if negatives:
        neg_ids = [n.get("id", "?") for n in negatives]
        neg_reasons = [f"{n.get('id')}: {n.get('reason', '')}" for n in negatives]
        payload["negative_context"] = {
            "instruction": f"Avoid patterns similar to these rejected signatures: [{', '.join(neg_ids)}]",
            "recent_rejections": neg_reasons,
            "beads": negatives,
        }
        logger.info("Prepended %d negative beads to Theorist context", len(negatives))
    return payload


def _check_injection(payload: Dict, role: str) -> None:
    """Run injection guard on payload. Mode depends on role."""
    mode = "log_only" if role == "auditor" else "halt"
    text = str(payload.get("transcript", payload.get("task", "")))
    if text:
        try:
            injection_scan(text, mode=mode)
        except InjectionDetected:
            logger.warning("Injection detected in dispatch to [%s]", role)
            raise


def is_mock_mode() -> bool:
    """Check if running in mock mode (no real API calls)."""
    return os.getenv("DEXTER_MOCK_MODE", "true").lower() == "true"


def is_llm_mode() -> bool:
    """Check if LLM extraction is enabled."""
    return os.getenv("DEXTER_LLM_MODE", "false").lower() == "true"


def dispatch(role: str, payload: Dict) -> Dict:
    """Dispatch a task to a role handler.

    Modes:
        DEXTER_MOCK_MODE=true  → local mock handlers (no API calls)
        DEXTER_LLM_MODE=true   → LLM via OpenRouter (role-based routing)
        Neither                 → local pattern-based handlers on real data
    """
    manifest = _load_role(role)

    # Model diversity logging
    model = manifest.get("model", "unknown")
    family = manifest.get("family", "unknown")
    logger.info(
        "Dispatch to [%s]: %s | model=%s family=%s | mock=%s llm=%s",
        role, payload.get("task", "unknown"), model, family,
        is_mock_mode(), is_llm_mode(),
    )

    # Injection guard
    _check_injection(payload, role)

    # Prepend negative beads for Theorist role
    if role == "theorist":
        payload = _prepend_negative_context(payload)

    # Mock mode — always use local handlers
    if is_mock_mode():
        return _mock_dispatch(role, payload, manifest)

    # LLM mode — use OpenRouter for supported roles
    if is_llm_mode() and role == "theorist":
        return _llm_dispatch_theorist(payload, manifest)

    # Local mode — pattern-based handlers on real data
    return _local_dispatch(role, payload, manifest)


def _llm_dispatch_theorist(payload: Dict, manifest: Dict) -> Dict:
    """LLM dispatch for Theorist — uses OpenRouter deepseek."""
    from core.theorist import extract_signatures
    from core.llm_client import get_model_config

    config = get_model_config("theorist")
    transcript = payload.get("transcript_data")
    chunks = payload.get("chunks")
    negative_beads = payload.get("negative_context", {}).get("beads", [])

    if transcript:
        signatures = extract_signatures(
            transcript,
            negative_beads=negative_beads,
            chunks=chunks,
        )
    else:
        signatures = []

    return {
        "role": "theorist",
        "status": "llm",
        "model": config["model"],
        "family": config["family"],
        "signatures": signatures,
    }


def _local_dispatch(role: str, payload: Dict, manifest: Dict) -> Dict:
    """Local dispatch — uses pattern-based handlers on real transcripts."""
    result = _mock_dispatch(role, payload, manifest)
    result["status"] = "local"
    return result


def _mock_dispatch(role: str, payload: Dict, manifest: Dict) -> Dict:
    """Mock dispatch — uses local handlers instead of LLM."""
    model = manifest.get("model", "unknown")
    family = manifest.get("family", "unknown")

    if role == "theorist":
        from core.theorist import extract_signatures
        transcript = payload.get("transcript_data")
        negative_beads = payload.get("negative_context", {}).get("beads", [])
        if transcript:
            signatures = extract_signatures(transcript, negative_beads=negative_beads)
        else:
            signatures = []
        return {
            "role": role,
            "status": "mock",
            "model": model,
            "family": family,
            "signatures": signatures,
        }

    elif role == "auditor":
        from core.auditor import audit_signature, audit_batch
        signature = payload.get("signature")
        signatures = payload.get("signatures")
        if signature:
            result = audit_signature(signature)
            return {"role": role, "status": "mock", "model": model, "family": family, **result}
        elif signatures:
            result = audit_batch(signatures)
            return {"role": role, "status": "mock", "model": model, "family": family, **result}
        return {"role": role, "status": "mock", "model": model, "family": family, "error": "no input"}

    elif role == "bundler":
        return {
            "role": role,
            "status": "mock",
            "model": model,
            "family": family,
            "payload_received": True,
        }

    else:
        return {
            "role": role,
            "status": "mock",
            "model": model,
            "family": family,
            "manifest_loaded": manifest.get("name", role),
            "payload_received": True,
            "negative_context_prepended": role == "theorist",
        }
