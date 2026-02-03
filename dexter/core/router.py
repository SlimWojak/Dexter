"""Role dispatch — routes tasks to role handlers.

Phase 2: adds negative bead prepend for Theorist, model diversity logging.
Phase 3: will route to actual LLM call via OpenRouter.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

import yaml

from core.context import read_negative_beads

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
        }
        logger.info("Prepended %d negative beads to Theorist context", len(negatives))
    return payload


def dispatch(role: str, payload: Dict) -> Dict:
    """Dispatch a task to a role handler.

    Phase 2: logs model diversity, prepends negatives for Theorist.
    Phase 3: will route to actual LLM call via OpenRouter.
    """
    manifest = _load_role(role)

    # Model diversity logging
    model = manifest.get("model", "unknown")
    family = manifest.get("family", "unknown")
    logger.info(
        "Dispatch to [%s]: %s | model=%s family=%s",
        role, payload.get("task", "unknown"), model, family,
    )

    # Prepend negative beads for Theorist role
    if role == "theorist":
        payload = _prepend_negative_context(payload)

    return {
        "role": role,
        "status": "stub",
        "manifest_loaded": manifest.get("name", role),
        "model": model,
        "family": family,
        "payload_received": True,
        "negative_context_prepended": role == "theorist",
    }
