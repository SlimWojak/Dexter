"""Role dispatch stub — routes tasks to role handlers.

Phase 1: stub that logs dispatch. Full implementation in Phase 3.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

import yaml

logger = logging.getLogger("dexter.router")

ROLES_DIR = Path(__file__).resolve().parent.parent / "roles"

_role_cache: Dict[str, Dict] = {}


def _load_role(name: str) -> dict:
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


def dispatch(role: str, payload: dict) -> dict:
    """Dispatch a task to a role handler.

    Phase 1: logs and returns stub response.
    Phase 3: will route to actual LLM call via OpenRouter.
    """
    manifest = _load_role(role)
    logger.info("Dispatch to [%s]: %s", role, payload.get("task", "unknown"))

    return {
        "role": role,
        "status": "stub",
        "manifest_loaded": manifest.get("name", role),
        "payload_received": True,
    }
