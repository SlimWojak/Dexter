"""Bead-chain context management — append-only JSONL to memory/beads/."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


BEADS_DIR = Path(__file__).resolve().parent.parent / "memory" / "beads"


def _session_file() -> Path:
    """One JSONL file per calendar day."""
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return BEADS_DIR / f"session_{date_str}.jsonl"


def append_bead(
    bead_type: str,
    content: str,
    *,
    source: str = "",
    metadata: Optional[Dict] = None,
) -> Dict:
    """Append a bead to the current session's JSONL file.

    Returns the bead dict that was written.
    """
    BEADS_DIR.mkdir(parents=True, exist_ok=True)

    bead = {
        "id": f"B-{int(time.time() * 1000)}",
        "type": bead_type,
        "content": content,
        "source": source,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata or {},
    }

    with open(_session_file(), "a") as f:
        f.write(json.dumps(bead) + "\n")

    return bead


def read_beads(limit: int = 0) -> List[Dict]:
    """Read beads from the current session file. 0 = all."""
    path = _session_file()
    if not path.exists():
        return []
    beads = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                beads.append(json.loads(line))
    if limit > 0:
        beads = beads[-limit:]
    return beads


def count_beads() -> int:
    """Count beads in current session file."""
    path = _session_file()
    if not path.exists():
        return 0
    count = 0
    with open(path) as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def needs_compression(max_beads: int = 25) -> bool:
    """Check if bead count exceeds compression threshold."""
    return count_beads() >= max_beads


# ---------------------------------------------------------------------------
# Negative bead support (Phase 2: failure feedback loop)
# ---------------------------------------------------------------------------

_negative_counter = 0


def append_negative_bead(
    reason: str,
    source_signature: str,
    *,
    source_bundle: str = "",
    metadata: Optional[Dict] = None,
) -> Dict:
    """Append a NEGATIVE bead on Auditor REJECT.

    Returns the bead dict that was written.
    """
    global _negative_counter
    _negative_counter += 1

    BEADS_DIR.mkdir(parents=True, exist_ok=True)

    bead = {
        "id": f"N-{_negative_counter:03d}",
        "type": "NEGATIVE",
        "reason": reason,
        "source_signature": source_signature,
        "source_bundle": source_bundle,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata or {},
    }

    with open(_session_file(), "a") as f:
        f.write(json.dumps(bead) + "\n")

    return bead


def read_negative_beads(limit: int = 10) -> List[Dict]:
    """Read the most recent NEGATIVE beads from current session.

    Args:
        limit: max number to return (default 10, per roadmap spec)
    """
    all_beads = read_beads()
    negatives = [b for b in all_beads if b.get("type") == "NEGATIVE"]
    if limit > 0:
        negatives = negatives[-limit:]
    return negatives
