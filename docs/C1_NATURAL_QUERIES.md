# C1 — Natural Researcher Queries
# Written BEFORE any CP1 SQL execution
# Timestamp: 2026-02-28T16:05:00Z (pre-CP1)
# Author: Fresh Opus (Dexter Phase 1 Observation)

These are the first 10 queries I naturally reach for as a researcher
opening a 66GB, 11.4M-bead synthetic FACT field for the first time.

## Q-NAT-1: What is the temporal extent of the field?
"What are the earliest and latest world_time_valid_from across the entire EURUSD DB?"
Why: First thing any researcher asks — what's my date range?

## Q-NAT-2: How are beads distributed across pairs?
"Row count per DB. Are all pairs roughly equal or are some sparser?"
Why: Sanity check on pipeline uniformity.

## Q-NAT-3: Are there temporal gaps?
"Count beads per calendar day for EURUSD. Show me weekends, holidays, gaps."
Why: Time series completeness is the first data quality check.

## Q-NAT-4: What does the content JSON actually contain?
"Show me 5 sample content blobs from different time periods."
Why: Need to understand the actual data shape — brief says per-field beads,
reality shows ohlcv_1m composite. Which is it everywhere?

## Q-NAT-5: Can I filter by pair without parsing JSON?
"Query beads using the tags array — does tag:pair:EURUSD work efficiently?"
Why: If every query requires json_extract on content.symbol, that's a
full-scan cost I need to quantify.

## Q-NAT-6: Walk the hash chain — does it hold?
"Pick a bead in the middle of EURUSD. Walk hash_prev backward 100 steps.
Verify hash_self at each step."
Why: Chain integrity at scale is THE moat claim. Need to verify it.

## Q-NAT-7: How many Merkle batches? What size?
"Count merkle_batches rows. Show batch_size distribution (min/max/avg/p50/p95)."
Why: Merkle anchoring is the second integrity claim. Batch sizes reveal
the trigger cadence (should be ~500 beads or 1hr, per spec).

## Q-NAT-8: Can I cross-query pairs at the same timestamp?
"Given a specific minute (e.g. 2023-06-15T14:30:00Z), get all 6 pairs' bars."
Why: Multi-pair analysis is the fundamental use case. If this requires
ATTACH + 6 JOINs, the ergonomics are painful and Track B needs to know.

## Q-NAT-9: What is the KT-WT delta?
"For 100 random beads, compute knowledge_time - world_time. What's the spread?"
Why: Synthetic pipeline means KT should be far after WT (years gap for
historical data). But the HLC ordering within a batch matters.

## Q-NAT-10: Are there any data anomalies?
"Find beads where close=0, volume=0, or high < low in the content JSON."
Why: 11.4M beads from Dukascopy over 5 years — there will be
holiday stubs, zero-volume bars, or Sunday open anomalies. Finding them
tells me what the field's noise floor looks like.

---
# LOCKED — No edits after this point. CP1 execution follows.
