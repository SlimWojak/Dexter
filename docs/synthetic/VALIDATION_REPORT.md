# Synthetic Bead Field — Validation Report

**Date**: 2026-02-28
**Sprint**: S62
**Pipeline branch**: `feat/synthetic-bead-pipeline`
**Pipeline commit**: `2f9de34`
**Phoenix emitter provenance**: `phoenix@2ed5821` (`s62-governance-emitter`)
**Hardware**: Apple M4 Max Studio, 64GB RAM

---

## Summary

11,387,568 synthetic FACT beads generated from 1-minute Forex OHLCV data.
6 currency pairs, 5+ years of history (2021-2026), sourced from Dukascopy via RiverWriter.

All 6 pairs validated: hash chains verified, all beads signed, zero rejections.

---

## Per-Pair Results

| Pair   | Beads     | Time (min) | Rate (bps) | Hash Chain | Signatures | Rejections | DB Size |
|--------|-----------|------------|------------|------------|------------|------------|---------|
| EURUSD | 1,902,141 | 22.8       | 1,388      | VERIFIED   | ALL SIGNED | 0          | 11GB    |
| GBPUSD | 1,902,784 | 25.6       | 1,237      | VERIFIED   | ALL SIGNED | 0          | 11GB    |
| USDJPY | 1,897,869 | 25.6       | 1,234      | VERIFIED   | ALL SIGNED | 0          | 11GB    |
| USDCAD | 1,895,998 | 25.4       | 1,243      | VERIFIED   | ALL SIGNED | 0          | 11GB    |
| USDCHF | 1,889,777 | 25.3       | 1,243      | VERIFIED   | ALL SIGNED | 0          | 11GB    |
| AUDUSD | 1,898,999 | 25.5       | 1,241      | VERIFIED   | ALL SIGNED | 0          | 11GB    |
| **TOTAL** | **11,387,568** | | | | | **0** | **66GB** |

---

## Validation Checks (per pair)

1. **Bead Count** — DB row count matches pipeline ingestion count
2. **Sample Validation** — 10,000 random beads checked for schema compliance
3. **Hash Chain** — Full chain walk, every bead linked to predecessor
4. **Merkle Coverage** — Un-anchored beads within allowance
5. **Signature Check** — ECDSA signature present on all beads
6. **Progress Log** — Checkpoint JSON matches DB count (delta = 0)

All 6 checks passed for all 6 pairs.

---

## Execution Mode

- **EURUSD**: Canary run (solo, 22.8 min)
- **Remaining 5 pairs**: Parallel workers (1 per pair, separate DBs, ~25.5 min wall clock)
- **Dry-run throughput**: 44,418 beads/sec (transform only)
- **Live throughput**: ~1,240 beads/sec per worker (with signing + hash chain + SQLite)
- **Total wall clock**: ~48 min (canary + parallel batch)

---

## Data Source

```
Source: ~/RiverWriter/data/1m/
Origin: VPS (srv1353682.hstgr.cloud) via rsync
Provider: Dukascopy
Resolution: 1-minute bars
Columns: timestamp, open, high, low, close, volume, source, knowledge_time, bar_hash
Years: 2021-2026 (6 parquet files per pair)
Total source rows: 11,387,568
```

---

## Test Fix Applied

Pre-commit test failure in `test_synthetic_pipeline.py::TestTransformBar::test_valid_row_produces_correct_content`
was fixed during this session. Root cause: MagicMock auto-attribute creation for `BeadType.FACT` —
`from ... import` copies values at import time, so bead_field stubs must be fully configured
before importing the pipeline module. Fix applied to both `_import_transform` and `_import_batch`
fixtures. 23/23 unit tests passing, 3 integration tests skipped (require full bead_field).

---

## Artifacts (not committed — too large)

```
tools/synthetic/synthetic_beads.db           — EURUSD (11GB)
tools/synthetic/synthetic_beads_GBPUSD.db    — GBPUSD (11GB)
tools/synthetic/synthetic_beads_USDJPY.db    — USDJPY (11GB)
tools/synthetic/synthetic_beads_USDCAD.db    — USDCAD (11GB)
tools/synthetic/synthetic_beads_USDCHF.db    — USDCHF (11GB)
tools/synthetic/synthetic_beads_AUDUSD.db    — AUDUSD (11GB)
tools/synthetic/canary_run.log               — EURUSD canary log
tools/synthetic/canary_*.log                 — Per-pair run logs
```
