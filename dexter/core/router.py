"""Role dispatch — routes tasks to role handlers.

Phase 3: adds mock/real mode, injection guard integration, role-specific handlers.
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


def dispatch(role: str, payload: Dict) -> Dict:
    """Dispatch a task to a role handler.

    Phase 3: mock mode uses local handlers, logs model diversity.
    """
    manifest = _load_role(role)

    # Model diversity logging
    model = manifest.get("model", "unknown")
    family = manifest.get("family", "unknown")
    logger.info(
        "Dispatch to [%s]: %s | model=%s family=%s | mock=%s",
        role, payload.get("task", "unknown"), model, family, is_mock_mode(),
    )

    # Injection guard
    _check_injection(payload, role)

    # Prepend negative beads for Theorist role
    if role == "theorist":
        payload = _prepend_negative_context(payload)

    # Role-specific dispatch
    # Phase 4A: local handlers work on real transcripts (pattern-based extraction)
    # Phase 5: will add OpenRouter LLM dispatch as an upgrade path
    if is_mock_mode():
        return _mock_dispatch(role, payload, manifest)

    # Real mode — use local handlers (same as mock, but flagged as "local")
    # Pattern-based Theorist and rule-based Auditor work on real data
    return _local_dispatch(role, payload, manifest)


def _local_dispatch(role: str, payload: Dict, manifest: Dict) -> Dict:
    """Local dispatch — uses pattern-based handlers on real transcripts."""
    result = _mock_dispatch(role, payload, manifest)
    result["status"] = "local"  # distinguish from mock
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
        # Bundler handled externally via core.bundler.generate_bundle
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
