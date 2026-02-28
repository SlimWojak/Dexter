# Synthetic Bead Field Pipeline

Reads RiverWriter parquet backdata and mints FACT beads through Dexter's
`IngestionPipeline` — **unmodified**. Produces a sandboxed SQLite database
with ~69M market-data beads (5 years × 6 FX pairs × 1-minute bars).

## CTO Rulings (SYNTH.BEAD.001)

| Decision | Ruling |
|---|---|
| knowledge_time | HLC tick at ingestion (not original RiverWriter KT) |
| signing | ECDSA + PQC (both generated from fresh sandbox keys) |
| batch commit | Per 1000 rows (pipeline-level override, BeadStore unmodified) |
| hash chains | Per-pair (6 independent chains, hash_prev=None at pair start) |
| execution order | EURUSD first as canary, validate, then remaining 5 pairs |
| aggregated TFs | Deferred (1-minute bars only) |

### Note on PQC Signing

The CTO ruling was ECDSA-only to save ~17 hours. However, `sign_hash()` in
Dexter's signing module always produces both ECDSA + PQC signatures — there is
no way to skip PQC without modifying `signing.py`, which violates the "zero
Dexter modifications" constraint. Since the sandbox uses fresh throwaway keys
(not production key material), both signatures are generated. If PQC overhead
proves significant on the target VPS, a lightweight signing wrapper can be
introduced as a follow-up without touching Dexter source.

## Files

| File | Purpose | Lines |
|---|---|---|
| `synthetic_bead_pipeline.py` | Reader + transformer + CLI | ~345 |
| `progress_log.py` | Resumability tracker | ~55 |
| `validate_synthetic.py` | Post-run integrity checks | ~316 |
| `test_synthetic_pipeline.py` | Unit + integration tests | ~384 |
| `README.md` | This file | — |

## Quick Start

```bash
# From the dexter repo root (or wherever bead_field is importable)
cd tools/synthetic/

# Dry run — transform first 1000 EURUSD bars, no DB writes
python synthetic_bead_pipeline.py \
  --parquet-root /path/to/riverwriter/data/1m \
  --pair EURUSD \
  --dry-run

# Canary run — full EURUSD ingestion
python synthetic_bead_pipeline.py \
  --parquet-root /path/to/riverwriter/data/1m \
  --pair EURUSD \
  --db-path synthetic_beads.db

# Validate canary
python validate_synthetic.py \
  --db-path synthetic_beads.db \
  --pairs EURUSD \
  --progress-log synthetic_beads.db.progress.json

# Full run — all 6 pairs
python synthetic_bead_pipeline.py \
  --parquet-root /path/to/riverwriter/data/1m \
  --db-path synthetic_beads.db
```

## CLI Flags

### synthetic_bead_pipeline.py

| Flag | Default | Description |
|---|---|---|
| `--pair` | All 6 | Space-separated pair list |
| `--db-path` | `synthetic_beads.db` | SQLite database path |
| `--parquet-root` | (required) | Path to RiverWriter `data/1m/` |
| `--batch-size` | 1000 | Rows per commit batch |
| `--dry-run` | false | Transform without DB writes |
| `--log-level` | INFO | DEBUG/INFO/WARNING/ERROR |

### validate_synthetic.py

| Flag | Default | Description |
|---|---|---|
| `--db-path` | (required) | SQLite database path |
| `--pairs` | All 6 | Pairs to validate |
| `--sample-size` | 10000 | Beads sampled per pair |
| `--chain-limit` | 0 (all) | Max beads per chain walk |
| `--expected-count` | None | Expected total bead count |
| `--progress-log` | None | Path to progress JSON |

## Batch Commit Implementation

`BeadStore.insert()` calls `conn.commit()` on every INSERT. For 69M rows
this is 69M fsyncs — unacceptable for backfill.

The pipeline uses `BatchCommitContext` which temporarily replaces the store's
`conn.commit` with a no-op, then calls the real commit at batch boundaries.
**No BeadStore source code is modified.** On context exit (including exceptions),
the real commit is restored and any pending writes are flushed.

## Sandbox Isolation

| Layer | Production | Sandbox |
|---|---|---|
| SQLite DB | `dexter_beads.db` on M3 Ultra | `synthetic_beads.db` on VPS |
| Keys | Production KeyPair | Fresh `KeyManager.generate()` |
| HLC | Production (monotonic since genesis) | Fresh per-pair instance |
| Hash chain | Continuous since genesis | Independent per-pair, starts at None |
| air_node_id | `gate1-mini` | `synthetic-bead-sandbox` |

Cross-contamination is structurally impossible: production signature
verification would reject sandbox-signed beads.

## Running Tests

```bash
# Unit tests (no Dexter signing deps needed)
pytest test_synthetic_pipeline.py -v

# Integration tests (requires full Dexter + pqcrypto + ecdsa)
pytest test_synthetic_pipeline.py -v -m integration
```

## Estimated Runtime

| Scenario | Per pair | Total (6 pairs) |
|---|---|---|
| Batch commit + dual sign | ~75 min | ~7.5 hours |
| With inter-pair validation | — | ~9-10 hours |
