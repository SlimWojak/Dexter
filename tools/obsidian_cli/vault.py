"""Vault operations — structured YAML frontmatter + markdown documents."""

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional

import yaml

VAULT_DIR = Path.home() / "lab" / "vault"

VALID_SECTIONS = [
    "hypotheses",
    "experiments",
    "findings",
    "dead_ends",
    "proposals",
    "weekly_reviews",
]


def vault_write(
    section: str,
    name: str,
    frontmatter: dict[str, Any],
    body: str = "",
    overwrite: bool = False,
) -> Path:
    """Write a structured document to the vault.

    Args:
        section: One of: hypotheses, experiments, findings, dead_ends, proposals, weekly_reviews
        name: Document name (without extension)
        frontmatter: YAML frontmatter dict (metadata)
        body: Markdown body content
        overwrite: If False, raises if file exists

    Returns:
        Path to the written file
    """
    _validate_section(section)
    section_dir = VAULT_DIR / section
    section_dir.mkdir(parents=True, exist_ok=True)

    filepath = section_dir / f"{name}.md"
    if filepath.exists() and not overwrite:
        raise FileExistsError(f"Document already exists: {filepath}. Use overwrite=True to replace.")

    # Add timestamp if not present
    if "created_at" not in frontmatter and not filepath.exists():
        frontmatter["created_at"] = datetime.now(timezone.utc).isoformat()
    if "updated_at" not in frontmatter:
        frontmatter["updated_at"] = datetime.now(timezone.utc).isoformat()

    content = _format_document(frontmatter, body)
    filepath.write_text(content, encoding="utf-8")
    return filepath


def vault_read(section: str, name: str) -> dict[str, Any]:
    """Read a vault document, returning frontmatter and body.

    Returns:
        Dict with keys: "frontmatter" (dict), "body" (str), "path" (str)
    """
    _validate_section(section)
    filepath = VAULT_DIR / section / f"{name}.md"
    if not filepath.exists():
        raise FileNotFoundError(f"Document not found: {filepath}")

    content = filepath.read_text(encoding="utf-8")
    frontmatter, body = _parse_document(content)
    return {
        "frontmatter": frontmatter,
        "body": body,
        "path": str(filepath),
    }


def vault_list(section: str) -> list[dict[str, Any]]:
    """List all documents in a vault section.

    Returns:
        List of dicts with keys: name, path, frontmatter (dict)
    """
    _validate_section(section)
    section_dir = VAULT_DIR / section
    if not section_dir.exists():
        return []

    results = []
    for f in sorted(section_dir.glob("*.md")):
        content = f.read_text(encoding="utf-8")
        frontmatter, _ = _parse_document(content)
        results.append({
            "name": f.stem,
            "path": str(f),
            "frontmatter": frontmatter,
        })
    return results


def vault_list_all() -> dict[str, int]:
    """Return document counts per section."""
    counts = {}
    for section in VALID_SECTIONS:
        section_dir = VAULT_DIR / section
        if section_dir.exists():
            counts[section] = len(list(section_dir.glob("*.md")))
        else:
            counts[section] = 0
    return counts


def _validate_section(section: str) -> None:
    if section not in VALID_SECTIONS:
        raise ValueError(f"Invalid section '{section}'. Must be one of: {VALID_SECTIONS}")


def _format_document(frontmatter: dict[str, Any], body: str) -> str:
    """Format a document with YAML frontmatter."""
    fm_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True)
    parts = ["---", fm_str.rstrip(), "---"]
    if body:
        parts.append("")
        parts.append(body)
    return "\n".join(parts) + "\n"


def _parse_document(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter and body from a markdown document."""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    try:
        frontmatter = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        frontmatter = {}

    body = parts[2].strip()
    return frontmatter, body
