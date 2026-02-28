"""Post-run integrity validation for synthetic bead field.

Checks schema compliance, hash chain integrity, Merkle coverage,
value structure, and tag correctness on the sandboxed SQLite DB.

CTO requirement: sample 10K random beads per pair.
"""

import argparse
import json
import logging
import math
import random
import sqlite3
import sys
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

REQUIRED_VALUE_KEYS = frozenset({"open", "high", "low", "close", "volume"})
REQUIRED_TAGS = {"synthetic", "source:riverwriter-backfill"}


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def check_counts(conn: sqlite3.Connection, expected: int | None) -> tuple[bool, str]:
    """Check total bead count and optionally compare to expected."""
    row = conn.execute("SELECT COUNT(*) FROM beads WHERE bead_type = 'FACT'").fetchone()
    total = row[0]
    if expected is not None and total != expected:
        return False, f"Count mismatch: got {total}, expected {expected}"
    return True, f"Total FACT beads: {total}"


def check_sample(conn: sqlite3.Connection, pair: str, sample_size: int = 10000) -> list[str]:
    """Sample N beads for a pair and validate structure."""
    errors = []

    rows = conn.execute(
        """SELECT bead_id, bead_type, content, temporal_class, tags,
                  world_time_valid_from, world_time_valid_to, attestation,
                  hash_self
           FROM beads
           WHERE tags LIKE ?
           ORDER BY RANDOM() LIMIT ?""",
        (f'%"pair:{pair}"%', sample_size),
    ).fetchall()

    if not rows:
        errors.append(f"{pair}: no beads found")
        return errors

    logger.info("  %s: sampling %d of %d+ beads", pair, len(rows), len(rows))

    for row in rows:
        bid = row["bead_id"]

        # bead_type
        if row["bead_type"] != "FACT":
            errors.append(f"{bid}: bead_type={row['bead_type']}, expected FACT")

        # temporal_class
        if row["temporal_class"] != "OBSERVATION":
            errors.append(f"{bid}: temporal_class={row['temporal_class']}")

        # content structure
        try:
            content = json.loads(row["content"])
            value = content.get("value")
            if not isinstance(value, dict):
                errors.append(f"{bid}: value is {type(value).__name__}, expected dict")
            elif set(value.keys()) != REQUIRED_VALUE_KEYS:
                errors.append(f"{bid}: value keys={set(value.keys())}")
            else:
                for k, v in value.items():
                    if not isinstance(v, (int, float)):
                        errors.append(f"{bid}: value.{k} is {type(v).__name__}")
                    elif v != v:  # NaN check
                        errors.append(f"{bid}: value.{k} is NaN")
                    elif v == float("inf") or v == float("-inf"):
                        errors.append(f"{bid}: value.{k} is Inf")
        except json.JSONDecodeError as e:
            errors.append(f"{bid}: content JSON parse error: {e}")

        # world_time span = 60 seconds
        wt_from = row["world_time_valid_from"]
        wt_to = row["world_time_valid_to"]
        if wt_from is None or wt_to is None:
            errors.append(f"{bid}: missing world_time")
        else:
            try:
                dt_from = datetime.fromisoformat(wt_from)
                dt_to = datetime.fromisoformat(wt_to)
                delta = (dt_to - dt_from).total_seconds()
                if abs(delta - 60.0) > 0.001:
                    errors.append(f"{bid}: WT span={delta}s, expected 60s")
            except ValueError as e:
                errors.append(f"{bid}: WT parse error: {e}")

        # tags
        try:
            tags = set(json.loads(row["tags"]))
            if "synthetic" not in tags:
                errors.append(f"{bid}: missing 'synthetic' tag")
            if f"pair:{pair}" not in tags:
                errors.append(f"{bid}: missing 'pair:{pair}' tag")
            if "source:riverwriter-backfill" not in tags:
                errors.append(f"{bid}: missing 'source:riverwriter-backfill' tag")
        except json.JSONDecodeError:
            errors.append(f"{bid}: tags JSON parse error")

        # hash_self is non-empty
        if not row["hash_self"]:
            errors.append(f"{bid}: empty hash_self")

        # attestation has signatures
        try:
            att = json.loads(row["attestation"])
            if not att.get("ecdsa_sig"):
                errors.append(f"{bid}: missing ecdsa_sig")
        except json.JSONDecodeError:
            errors.append(f"{bid}: attestation JSON parse error")

    return errors


def check_hash_chain(conn: sqlite3.Connection, pair: str, limit: int = 0) -> list[str]:
    """Walk the hash chain for a pair and verify hash_prev linkage.

    Beads are ordered by knowledge_time (ingestion order = chain order).
    If limit > 0, only check first N beads (for speed on large datasets).
    """
    errors = []

    sql = """SELECT bead_id, hash_self, hash_prev, knowledge_time_recorded_at
             FROM beads
             WHERE tags LIKE ?
             ORDER BY knowledge_time_recorded_at ASC"""
    params: list = [f'%"pair:{pair}"%']

    if limit > 0:
        sql += " LIMIT ?"
        params.append(limit)

    rows = conn.execute(sql, params).fetchall()

    if not rows:
        errors.append(f"{pair}: no beads for chain check")
        return errors

    # First bead in chain: hash_prev must be None
    first = rows[0]
    if first["hash_prev"] is not None:
        errors.append(
            f"{pair}: first bead {first['bead_id']} has hash_prev="
            f"{first['hash_prev']}, expected None"
        )

    # Walk chain: each bead's hash_prev must equal previous bead's hash_self
    for i in range(1, len(rows)):
        prev_hash = rows[i - 1]["hash_self"]
        curr = rows[i]
        if curr["hash_prev"] != prev_hash:
            errors.append(
                f"{pair}: chain break at bead {curr['bead_id']} "
                f"(hash_prev={curr['hash_prev']}, expected={prev_hash})"
            )
            break  # Stop at first break — downstream is meaningless

    logger.info("  %s: chain verified for %d beads", pair, len(rows))
    return errors


def check_merkle_coverage(conn: sqlite3.Connection) -> list[str]:
    """Every bead should have a merkle_batch_id assigned."""
    errors = []
    row = conn.execute(
        "SELECT COUNT(*) FROM beads WHERE merkle_batch_id IS NULL"
    ).fetchone()
    orphans = row[0]
    if orphans > 0:
        # The last batch may not have been anchored if it didn't hit
        # the 500-bead trigger. Allow up to 499 un-anchored beads per pair.
        pair_count = conn.execute(
            "SELECT COUNT(DISTINCT json_extract(tags, '$[1]')) FROM beads"
        ).fetchone()[0]
        max_allowed = 499 * max(pair_count, 1)
        if orphans > max_allowed:
            errors.append(
                f"Merkle: {orphans} beads without batch_id "
                f"(allowed up to {max_allowed} for {pair_count} pairs)"
            )
        else:
            logger.info(
                "  Merkle: %d un-anchored beads (within allowance for %d pairs)",
                orphans, pair_count,
            )
    else:
        logger.info("  Merkle: all beads have batch_id")
    return errors


def check_no_unsigned(conn: sqlite3.Connection) -> list[str]:
    """Verify no beads have empty signatures."""
    errors = []
    rows = conn.execute(
        """SELECT bead_id, attestation FROM beads
           WHERE json_extract(attestation, '$.ecdsa_sig') = ''
             AND json_extract(attestation, '$.pqc_sig') = ''"""
    ).fetchall()
    if rows:
        errors.append(f"Unsigned beads: {len(rows)} found")
    else:
        logger.info("  Signatures: all beads signed")
    return errors


def check_progress_log(progress_path: str, conn: sqlite3.Connection) -> list[str]:
    """Cross-check progress log against actual DB counts."""
    import json as _json
    from pathlib import Path

    errors = []
    p = Path(progress_path)
    if not p.exists():
        errors.append(f"Progress log not found: {progress_path}")
        return errors

    state = _json.loads(p.read_text())
    total_logged = sum(state.values())
    total_db = conn.execute("SELECT COUNT(*) FROM beads").fetchone()[0]

    # Allow for rejections: logged rows >= DB beads
    if total_logged < total_db:
        errors.append(
            f"Progress log ({total_logged}) < DB count ({total_db})"
        )
    else:
        logger.info(
            "  Progress: logged=%d, DB=%d (delta=%d rejections)",
            total_logged, total_db, total_logged - total_db,
        )
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate synthetic bead field integrity",
    )
    parser.add_argument("--db-path", required=True, help="Path to synthetic_beads.db")
    parser.add_argument(
        "--pairs", nargs="+", default=["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "USDCHF"],
    )
    parser.add_argument("--sample-size", type=int, default=10000)
    parser.add_argument("--chain-limit", type=int, default=0, help="Limit chain check per pair (0=all)")
    parser.add_argument("--expected-count", type=int, default=None, help="Expected total bead count")
    parser.add_argument("--progress-log", default=None, help="Path to progress JSON")
    parser.add_argument("--log-level", default="INFO")

    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    conn = connect(args.db_path)
    all_errors: list[str] = []

    logger.info("=== Bead Count ===")
    ok, msg = check_counts(conn, args.expected_count)
    logger.info("  %s", msg)
    if not ok:
        all_errors.append(msg)

    logger.info("=== Sample Validation ===")
    for pair in args.pairs:
        errs = check_sample(conn, pair, args.sample_size)
        all_errors.extend(errs)

    logger.info("=== Hash Chain ===")
    for pair in args.pairs:
        errs = check_hash_chain(conn, pair, limit=args.chain_limit)
        all_errors.extend(errs)

    logger.info("=== Merkle Coverage ===")
    all_errors.extend(check_merkle_coverage(conn))

    logger.info("=== Signature Check ===")
    all_errors.extend(check_no_unsigned(conn))

    if args.progress_log:
        logger.info("=== Progress Log ===")
        all_errors.extend(check_progress_log(args.progress_log, conn))

    conn.close()

    print(f"\n=== VALIDATION {'PASS' if not all_errors else 'FAIL'} ===")
    if all_errors:
        print(f"\n{len(all_errors)} errors:")
        for e in all_errors[:50]:  # Cap output
            print(f"  ✗ {e}")
        if len(all_errors) > 50:
            print(f"  ... and {len(all_errors) - 50} more")
        sys.exit(1)
    else:
        print("All checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
