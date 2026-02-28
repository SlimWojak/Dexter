"""Resumability tracker for synthetic bead pipeline.

Stores (pair, year, rows_ingested) checkpoints as JSON.
On restart, pipeline resumes from last committed offset.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ProgressLog:
    """Track ingestion progress per (pair, year) for crash recovery."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._state: dict[str, int] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                self._state = json.loads(self._path.read_text())
                logger.info("Loaded progress: %d checkpoints", len(self._state))
            except (json.JSONDecodeError, OSError) as e:
                raise RuntimeError(
                    f"Corrupt progress log at {self._path}: {e}"
                ) from e
        else:
            self._state = {}

    @staticmethod
    def _key(pair: str, year: str) -> str:
        return f"{pair}:{year}"

    def get_offset(self, pair: str, year: str) -> int:
        """Return the number of rows already ingested for (pair, year)."""
        return self._state.get(self._key(pair, year), 0)

    def update(self, pair: str, year: str, rows_ingested: int) -> None:
        """Persist a checkpoint after a batch completes."""
        self._state[self._key(pair, year)] = rows_ingested
        self._save()

    def _save(self) -> None:
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._state, indent=2))
        tmp.rename(self._path)

    @property
    def state(self) -> dict[str, int]:
        return dict(self._state)
