"""Cross-pair query abstraction for the bead field.

FieldQuery is the ONE supported path for multi-pair queries.
It fans out to all pair DBs via ThreadPoolExecutor, merges
results with a pair label, and normalizes timestamps automatically.

No ATTACH. Parallel sequential is the architecture.
(Observation: ATTACH adds 0.9ms overhead, no speed win, more complexity.)
"""

import os
import re
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

from .timestamps import normalize_params


_PAIR_FROM_FILENAME = re.compile(r"synthetic_beads(?:_(\w+))?\.db$")

DEFAULT_DB_DIR = os.path.expanduser("~/dexter/tools/synthetic")


@dataclass
class QueryResult:
    """Result from a single pair's query execution."""
    pair: str
    rows: list[dict]
    row_count: int
    wall_time_ms: float


@dataclass
class FieldQueryResult:
    """Merged results from all pairs."""
    results: list[QueryResult] = field(default_factory=list)

    @property
    def total_rows(self) -> int:
        return sum(r.row_count for r in self.results)

    @property
    def all_rows(self) -> list[dict]:
        merged = []
        for r in self.results:
            for row in r.rows:
                row["_pair"] = r.pair
            merged.extend(r.rows)
        return merged

    @property
    def total_time_ms(self) -> float:
        return max((r.wall_time_ms for r in self.results), default=0.0)


class FieldQuery:
    """Cross-pair query interface.

    Usage:
        fq = FieldQuery.from_data_dir("~/dexter/tools/synthetic")
        result = fq.execute("SELECT bead_id, content FROM beads WHERE world_time_valid_from = ?",
                           ("2024-01-15T14:30:00",))
    """

    def __init__(self, db_paths: dict[str, str]) -> None:
        """Initialize with explicit pair→path mapping.

        Args:
            db_paths: Dict mapping pair name (e.g. 'EURUSD') to DB file path.
        """
        if not db_paths:
            raise ValueError("db_paths cannot be empty")
        for pair, path in db_paths.items():
            if not os.path.exists(path):
                raise FileNotFoundError(f"DB not found for {pair}: {path}")
        self._db_paths = dict(db_paths)

    @classmethod
    def from_data_dir(cls, directory: str) -> "FieldQuery":
        """Auto-discover pair DBs from a directory.

        Expects files named synthetic_beads.db (EURUSD) and
        synthetic_beads_{PAIR}.db for other pairs.
        """
        dirpath = Path(os.path.expanduser(directory))
        if not dirpath.is_dir():
            raise FileNotFoundError(f"Directory not found: {dirpath}")

        db_paths: dict[str, str] = {}
        for f in sorted(dirpath.glob("synthetic_beads*.db")):
            m = _PAIR_FROM_FILENAME.search(f.name)
            if m:
                pair = m.group(1) or "EURUSD"
                db_paths[pair] = str(f)

        if not db_paths:
            raise FileNotFoundError(f"No synthetic_beads*.db files in {dirpath}")

        return cls(db_paths)

    @property
    def pairs(self) -> list[str]:
        return sorted(self._db_paths.keys())

    def execute(
        self,
        sql: str,
        params: tuple | list = (),
        parallel: bool = True,
    ) -> FieldQueryResult:
        """Execute SQL against all pair DBs and merge results.

        Timestamps in params are automatically normalized to canonical
        UTC form before hitting SQLite.

        Args:
            sql: SQL query template. Executed against each pair's beads table.
            params: Query parameters. Timestamps are auto-normalized.
            parallel: If True, query all DBs concurrently via ThreadPoolExecutor.

        Returns:
            FieldQueryResult with merged results from all pairs.
        """
        norm_params = normalize_params(params)

        if parallel:
            return self._execute_parallel(sql, norm_params)
        return self._execute_sequential(sql, norm_params)

    def _query_one(self, pair: str, db_path: str, sql: str, params: tuple | list) -> QueryResult:
        import time
        t0 = time.monotonic()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            raw_rows = cur.fetchall()
            rows = [dict(r) for r in raw_rows]
            wall_ms = (time.monotonic() - t0) * 1000
            return QueryResult(
                pair=pair,
                rows=rows,
                row_count=len(rows),
                wall_time_ms=wall_ms,
            )
        finally:
            conn.close()

    def _execute_parallel(self, sql: str, params: tuple | list) -> FieldQueryResult:
        result = FieldQueryResult()
        with ThreadPoolExecutor(max_workers=len(self._db_paths)) as executor:
            futures = {
                executor.submit(self._query_one, pair, path, sql, params): pair
                for pair, path in self._db_paths.items()
            }
            for future in as_completed(futures):
                qr = future.result()
                result.results.append(qr)
        result.results.sort(key=lambda r: r.pair)
        return result

    def _execute_sequential(self, sql: str, params: tuple | list) -> FieldQueryResult:
        result = FieldQueryResult()
        for pair, path in sorted(self._db_paths.items()):
            qr = self._query_one(pair, path, sql, params)
            result.results.append(qr)
        return result
