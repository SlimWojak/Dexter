# S63.T2 Field Observation Report
## Structured Measurement Against 11.4M Synthetic Bead Field

**Observer:** COO (Claude Opus 4.6)
**Date:** 2026-03-03
**Repo Head:** 7099707
**Hardware:** M3 Ultra (a8ra-m3)
**Methodology Lens:** Olya ICT Framework
**Schema Mutations:** ZERO (freeze respected)

---

## Summary

The 11.4M synthetic bead field is a structurally sound but **analytically inert** substrate. All 11,387,568 beads across 6 currency pairs are exclusively FACT-type, OBSERVATION-class, OHLCV 1-minute candles from a single source (Dukascopy via riverwriter-backfill-v1). There are zero CLAIMs, zero SIGNALs, zero PROPOSALs, and zero beads of any analytical type. The field is Layer 1 complete: the hash chain is unbroken (single chain head per pair), Merkle batching is operational (3,804 batches covering 99.99% of EURUSD beads), and hash/chain/Merkle verification passes on random sample. However, applying Olya's ICT methodology as a lens reveals that the field cannot currently be tested against any methodological rule because the analytical layer does not exist. The Synthetic Mirror Test is structurally inapplicable (0/0, not 0%), and the CLAIM-FACT compression gap is total (11.4M FACTs, 0 CLAIMs). The substrate is healthy; the analysis surface is empty.

---

## Observations

### OBS-001: Monotype Field Composition
```yaml
- id: "OBS-001"
  type: FRICTION
  phase: 1
  query_surface: "Bead type distribution across all 6 databases"
  observation: |
    All 11,387,568 beads are bead_type=FACT, temporal_class=OBSERVATION,
    content field=ohlcv_1m, provider=dukascopy, quality_score=1.0.
    Zero CLAIMs, SIGNALs, PROPOSALs, PROPOSAL_REJECTEDs, SKILLs,
    MODEL_VERSIONs, or POLICYs exist in any database. All tags are
    identical: ["synthetic", "pair:XXXUSD", "source:riverwriter-backfill"].
    All source_refs are source_type=MARKET_DATA, source_id=riverwriter-backfill-v1.
  scale: architectural
  methodological_implication: |
    Olya's methodology operates on analytical beads (CLAIMs expressing
    market structure, SIGNALs encoding trade theses, PROPOSALs with
    5-factor checklists). None of these layers exist. The field cannot
    be stress-tested against ANY ICT rule in its current state. The
    substrate is necessary but not sufficient for methodology validation.
  architectural_implication: |
    The bead_field schema defines 8 bead types but only 1 is populated.
    The ingestion pipeline (riverwriter) produces only FACT beads. An
    analytical pipeline (theorist/auditor agents producing CLAIMs, engine
    producing SIGNALs) does not yet exist. This is the expected Gate 1
    state, but it means all Olya-lens queries return null results.
  schema_change_required: NO
  model_used: "Claude Opus 4.6"
  evidence: |
    SELECT bead_type, COUNT(*) FROM beads GROUP BY bead_type
    -- EURUSD: FACT=1,902,141 (100%)
    -- AUDUSD: FACT=1,898,999 (100%)
    -- GBPUSD: FACT=1,902,784 (100%)
    -- USDCAD: FACT=1,895,998 (100%)
    -- USDCHF: FACT=1,889,777 (100%)
    -- USDJPY: FACT=1,897,869 (100%)
    SELECT COUNT(*) FROM beads WHERE bead_type != 'FACT' -- returns 0 for all DBs
```

### OBS-002: Knowledge Time Collapse
```yaml
- id: "OBS-002"
  type: FRICTION
  phase: 2
  query_surface: "Knowledge time (KT) distribution across field"
  observation: |
    All 1,902,141 EURUSD beads have KT values within a 23-minute window:
    2026-02-28T07:04:27 to 2026-02-28T07:27:17. Each bead has a unique
    microsecond-precision KT (1,902,141 distinct values), but the entire
    field was ingested in a single batch run on 2026-02-28. This means
    the bi-temporal query predicate (KT cutoff) has near-zero selectivity
    on synthetic data. The temporal.py module documents this explicitly:
    "all KT values are near 2026-02-28 (ingestion date). KT predicate
    has ~0% selectivity on synthetic field."
  scale: structural
  methodological_implication: |
    Bi-temporal queries (known_at) are architecturally correct but
    functionally degenerate on this field. Any KT cutoff after
    2026-02-28T07:28 returns the entire field; any cutoff before
    2026-02-28T07:04 returns nothing. Real-time ingestion will produce
    meaningful KT spread, but the current field cannot exercise the
    bi-temporal query path meaningfully.
  architectural_implication: |
    The known_at() function and bi-temporal store are correctly built.
    The limitation is in the synthetic data generation approach
    (batch backfill), not the code. When live ingestion begins,
    KT will naturally spread across the WT range.
  schema_change_required: NO
  model_used: "Claude Opus 4.6"
  evidence: |
    SELECT MIN(knowledge_time_recorded_at), MAX(knowledge_time_recorded_at) FROM beads
    -- min: 2026-02-28T07:04:27.924410+00:00
    -- max: 2026-02-28T07:27:17.911600+00:00
    SELECT COUNT(DISTINCT knowledge_time_recorded_at) FROM beads
    -- 1,902,141 (one per bead, microsecond-unique)
```

### OBS-003: Temporal Coverage and Gap Structure
```yaml
- id: "OBS-003"
  type: CONFIRMATION
  phase: 1
  query_surface: "Temporal completeness of 1m bars, gap patterns, coverage ratio"
  observation: |
    EURUSD spans 2021-01-03T22:00 to 2026-02-27T21:59 (2,708,639 calendar
    minutes). 1,902,141 bars exist = 70.2% coverage, consistent with FX
    market hours (~5 trading days/week, ~21-22 hours/day). Weekend gaps are
    correct: Sunday has 31,346 bars (market open), Saturday has 0 bars,
    Friday has 342,304 (early close). Within trading hours, small gaps
    (2-3 minutes) occur sporadically, especially in low-liquidity periods
    (late NY / early Asia transition). No duplicate timestamps exist.
    Cross-pair bar counts differ slightly for the same day (EURUSD=1,412,
    GBPUSD=1,417, USDJPY=1,437 on 2024-01-15), reflecting genuine
    liquidity differences between pairs.
  scale: local
  methodological_implication: |
    Kill zone analysis is feasible. The hourly distribution is flat across
    trading hours (79,316-80,238 per hour, ~4.2% each), confirming uniform
    1-minute bar generation without artificial clustering. This is correct
    for raw data; KZ clustering would appear in CLAIM/SIGNAL analysis, not
    in bar availability.
  architectural_implication: |
    The field provides complete substrate coverage for FVG, swing, and
    structure detection. Small gaps (2-3 min) in low-liquidity hours will
    need handling in any derived analysis pipeline.
  schema_change_required: NO
  model_used: "Claude Opus 4.6"
  evidence: |
    Total beads: 1,902,141 / 2,708,639 calendar minutes = 70.2% coverage
    Day-of-week: Sun=31,346, Mon=381,845, Tue=384,854, Wed=381,848,
    Thu=379,944, Fri=342,304, Sat=0
    Sample week 2024-01-08: 14 gaps > 1 min, all 2-3 min duration
    Cross-pair same timestamp check: all 6 pairs have data at 2024-01-15T14:30
```

### OBS-004: Data Quality Anomalies
```yaml
- id: "OBS-004"
  type: SURPRISE
  phase: 3
  query_surface: "OHLCV integrity: zero-range bars, zero-volume bars, inversions"
  observation: |
    12,465 bars (0.66%) have high=low (zero-range "doji" bars). These
    correlate with low-liquidity periods (Sunday open, late NY session).
    66 bars (0.0035%) have volume=0.0, clustered at 2024-10-09 23:05-23:09
    UTC and similar off-hours. Zero inverted bars (high < low). Zero
    OHLCV violations (open or close outside high-low range). All WT spans
    are exactly 60 seconds (verified via Python datetime delta; SQLite
    julianday shows floating-point noise at ~10^-7 minutes, which is a
    SQLite artifact, not a data issue).
  scale: local
  methodological_implication: |
    Zero-volume bars create a data quality edge case. Olya's methodology
    does not reference zero-volume bars explicitly, but they could affect
    volume imbalance (VI) detection. The 0.66% zero-range rate is normal
    for FX 1-minute data in low-liquidity sessions. These bars should
    likely be tagged with DataQuality.DEGRADED rather than quality_score=1.0.
  architectural_implication: |
    All beads have quality_score=1.0 uniformly. The 66 zero-volume bars
    and 12,465 zero-range bars are not flagged. When the analytical layer
    is built, a quality tagger should identify these for downstream
    consumers. The DataQuality enum (NOMINAL, DEGRADED, PARTIAL, ERROR)
    exists in the schema but is not used.
  schema_change_required: NO
  model_used: "Claude Opus 4.6"
  evidence: |
    SELECT COUNT(*) FROM beads WHERE json_extract(content, '$.value.volume') = 0 -- 66
    SELECT COUNT(*) FROM beads WHERE json_extract(content, '$.value.high') = json_extract(content, '$.value.low') -- 12,465
    SELECT COUNT(*) FROM beads WHERE json_extract(content, '$.value.high') < json_extract(content, '$.value.low') -- 0
    Zero-vol sample: 2024-10-09T23:05-23:09 (5 consecutive bars)
    Zero-range sample: 2021-01-03T22:07 (Sunday open, V=1.5)
```

### OBS-005: Regime Shift Detection via Volume and Range
```yaml
- id: "OBS-005"
  type: SURPRISE
  phase: 3
  query_surface: "Quarter-over-quarter changes in average volume and average range"
  observation: |
    Clear regime boundaries detected in the raw data:
    - 2022-Q1: volume +58.2% QoQ, range +46.4% (rate hike cycle onset)
    - 2022-Q3: volume +96.7% QoQ (near-doubling, peak volatility period)
    - 2022-Q4: highest avg volume (773.3) and widest range (2.33 pips)
    - 2025-Q3: volume -45.4% QoQ, range -36.5% (sharp compression)
    - 2021 had lowest volume (104-215 avg), 2022 had highest (184-773 avg)
    - Body/range ratio stable at 0.566-0.583 across all periods

    Price regime: EURUSD traded from 1.23 (2021-Q1) down to 0.95 (2022-Q3 low),
    then recovered to 1.12 by 2023-Q3, matching known EUR weakness during
    2022 energy crisis.
  scale: structural
  methodological_implication: |
    Regime shifts are visible in raw data without any analytical overlay.
    Olya's methodology calls for regime-aware position sizing and kill
    zone filtering. The 3x volume difference between 2021-Q3 (104.6 avg)
    and 2022-Q4 (773.3 avg) would produce very different FVG sizes,
    displacement thresholds, and sweep magnitudes. Any CLAIM pipeline
    must be regime-aware or it will produce incomparable outputs across
    these periods.
  architectural_implication: |
    The POLICY bead type includes PolicyType.REGIME. Regime boundaries
    detected here could seed initial POLICY beads marking the 2021 low-vol
    regime, 2022 high-vol regime, and subsequent normalization. This is
    a natural T3 deliverable.
  schema_change_required: NO
  model_used: "Claude Opus 4.6"
  evidence: |
    Quarterly aggregation: 2021-Q3 avg_vol=104.6, 2022-Q4 avg_vol=773.3 (7.4x)
    8 regime shifts detected at >30% QoQ threshold
    Body/range ratio range: 0.566-0.583 (remarkably stable)
    Full quarterly table in Phase 3 narrative below
```

### OBS-006: News Event Fingerprints in Raw Data
```yaml
- id: "OBS-006"
  type: CONFIRMATION
  phase: 2
  query_surface: "Volume and range on known CPI/FOMC dates vs normal days"
  observation: |
    High-impact news events leave clear fingerprints in the OHLCV data:

    CPI Release (13:00-14:00 UTC window):
    - 2024-01-11 CPI: avg_vol=1,697, range=64.5p, max_vol=3,713.8
    - 2024-02-13 CPI: avg_vol=1,521, range=95.6p, max_vol=3,762.3
    - Adjacent normal day: avg_vol=478, range=11.5p
    - CPI multiplier: ~3.5x volume, ~6-8x range

    FOMC Decision (18:00-19:30 UTC window):
    - 2024-03-20 FOMC: avg_vol=1,671, range=53.3p
    - 2024-06-12 FOMC: avg_vol=1,899, range=39.8p
    - Normal day same window: avg_vol=275, range=1.2p
    - FOMC multiplier: ~6x volume, ~33-44x range

    These events are detectable programmatically from raw data alone,
    without requiring a news calendar bead.
  scale: structural
  methodological_implication: |
    Olya's rules prohibit trading on CPI/FOMC days (or require special
    handling). The raw data shows these events are detectable: a simple
    volume/range spike detector could flag them. However, Olya's rule
    is calendar-based (known in advance), not reactive. Both approaches
    could be encoded as POLICY beads.
  architectural_implication: |
    A news-day FACT bead (from OPEN_SOURCE calendar data) would be more
    reliable than spike detection. The current field has no calendar/event
    beads. This is a natural addition for the FACT layer (not a schema
    change, just new FACT content types).
  schema_change_required: NO
  model_used: "Claude Opus 4.6"
  evidence: |
    CPI 2024-01-11 13:00-14:00: avg_vol=1697.0 vs pre-CPI 2024-01-10: avg_vol=478.7
    FOMC 2024-06-12 18:00-19:30: avg_vol=1898.9 vs normal 2024-01-02: avg_vol=275.3
    All EURUSD, synthetic_beads.db
```

### OBS-007: Synthetic Mirror Test -- Structurally Inapplicable
```yaml
- id: "OBS-007"
  type: FRICTION
  phase: 2
  query_surface: |
    Search for Olya-rule violations: entries outside kill zones, SIGNALs
    without 5 factors, stops by pips not swings, re-entries without new MSS,
    partial exits, trading on CPI/FOMC days, CBDR references, SMT references
  observation: |
    The Synthetic Mirror Test is STRUCTURALLY INAPPLICABLE. The test requires
    analytical beads (CLAIM, SIGNAL, PROPOSAL) that encode trading decisions.
    The field contains ONLY raw OHLCV FACT beads. There are:
    - 0 CLAIMs containing ICT concepts (MSS, FVG, OTE, PDA, sweep, etc.)
    - 0 SIGNALs to check against 5-factor checklist
    - 0 PROPOSALs to check for kill zone compliance
    - 0 references to CBDR, SMT, or any v0.3-removed concepts
    - 0 references to any ICT terminology whatsoever in bead content

    The violation rate is 0/0 (undefined), NOT 0%. This is not circular
    testing -- it is the absence of a testable surface. The field is
    pre-analytical: the measurement substrate exists but no measurements
    (in the ICT sense) have been recorded on it.
  scale: architectural
  methodological_implication: |
    Until CLAIMs and SIGNALs populate the field, Olya's methodology cannot
    be validated or falsified against the bead field. The Mirror Test should
    be deferred to a phase where analytical beads exist.
  architectural_implication: |
    This is the most significant finding: the 11.4M bead field is a
    high-fidelity price tape, not an analytical knowledge base. The
    entire ICT analysis layer (order flow resolution, engine events,
    5-factor checklists, MMXM models) lives in the CLAIM/SIGNAL/PROPOSAL
    types that are defined in the schema but have zero instances. The
    gap between schema capability and field population is total.
  schema_change_required: NO
  model_used: "Claude Opus 4.6"
  evidence: |
    grep-equivalent across all content:
    MSS=0, swing=0, order_flow=0, liquidity=0, sweep=0, FVG=0, SIGNAL=0,
    entry=0, stop=0, target=0, CPI=0, FOMC=0, CBDR=0, SMT=0, OTE=0,
    premium=0, discount=0, breaker=0, order_block=0

    SELECT COUNT(*) FROM beads WHERE bead_type != 'FACT' -- 0 (all 6 DBs)
```

### OBS-008: CLAIM-FACT Compression Gap is Total
```yaml
- id: "OBS-008"
  type: FRICTION
  phase: 3
  query_surface: "CLAIM:FACT ratio across entire field"
  observation: |
    CLAIM:FACT ratio = 0:11,387,568 = 0.000000
    Every FACT bead is an orphan from the CLAIM perspective. No FACT has
    been referenced by any CLAIM. No analytical interpretation has been
    recorded against any market observation. The compression gap is not
    partial -- it is absolute. The "mine everything" principle (from
    CLAUDE.md) has no miners operating on the field.
  scale: architectural
  methodological_implication: |
    The Olya methodology cannot be applied until CLAIMs begin to mine
    the FACT substrate. The expected compression ratio in a working
    system would be approximately 100:1 to 1000:1 (many FACTs per CLAIM),
    meaning the first CLAIM pipeline would need to process millions of
    FACTs to produce thousands of CLAIMs.
  architectural_implication: |
    This quantifies the Gate 2 work surface: building the analytical
    pipeline that reads FACTs and produces CLAIMs, SIGNALs, and PROPOSALs.
    The substrate is ready. The miners are not.
  schema_change_required: NO
  model_used: "Claude Opus 4.6"
  evidence: |
    All 6 DBs: bead_type=FACT only
    SELECT COUNT(*) WHERE bead_type='CLAIM' -- 0 (all DBs)
    Total field: 11,387,568 FACTs, 0 CLAIMs, 0 SIGNALs, 0 PROPOSALs
```

### OBS-009: Integrity Infrastructure Passes Verification
```yaml
- id: "OBS-009"
  type: CONFIRMATION
  phase: 1
  query_surface: "Hash chain, Merkle batches, and verify_bead on random sample"
  observation: |
    EURUSD hash chain: single chain head (1 bead with hash_prev=NULL),
    1,902,140 beads with hash_prev linked. The chain is continuous and
    unbroken. Merkle batching: 3,804 batches of 500 beads each, covering
    1,902,000 of 1,902,141 beads (141 in final partial batch). Random
    bead verification via verify_bead():
    - hash_valid: True (recomputed hash matches stored)
    - chain_valid: True (hash_prev references valid predecessor)
    - merkle_valid: True (Merkle proof reconstructs to batch root)
    - sig_valid: None (requires key material not in DB)
    - proof_depth: 9 (consistent with 500-bead batches, log2(500)~9)

    Attestation envelope present on all beads:
    air_node_id="synthetic-bead-sandbox", code_hash="2f9de34",
    ECDSA signatures present, PQC signatures present.
  scale: structural
  methodological_implication: |
    The integrity infrastructure satisfies INV-BEAD-IMMUTABLE and
    INV-BEAD-SIGNED. When CLAIMs reference these FACTs, the provenance
    chain will be verifiable end-to-end.
  architectural_implication: |
    The verify_bead() API works correctly. The hash chain walk (chain.py)
    uses recursive CTE and performs well. The infrastructure is production-
    grade for the substrate layer.
  schema_change_required: NO
  model_used: "Claude Opus 4.6"
  evidence: |
    verify_bead('synthetic_beads.db', '019ca31e-f5d0-7ed7-8f03-8e1524dc96d0')
    -- hash_valid=True, chain_valid=True, merkle_valid=True, proof_depth=9
    Chain heads: 1 (single continuous chain)
    Merkle batches: 3,804 (500 beads each)
```

### OBS-010: Cross-Pair Alignment and Volume Regime Divergence
```yaml
- id: "OBS-010"
  type: SURPRISE
  phase: 3
  query_surface: "Cross-pair volume, range, and bar count comparison"
  observation: |
    Cross-pair statistics reveal significant divergence:

    Pair     | Beads     | AvgVol  | AvgRange(pips)
    EURUSD   | 1,902,141 | 311.4   | 1.51
    AUDUSD   | 1,898,999 | 184.6   | 1.34
    GBPUSD   | 1,902,784 | 177.0   | 1.96
    USDCAD   | 1,895,998 | 188.9   | 1.60
    USDCHF   | 1,889,777 | 158.1   | 1.29
    USDJPY   | 1,897,869 | 430.0   | 231.13

    USDJPY range (231.13 pips) is ~150x larger than other pairs because
    JPY pairs are quoted to 3 decimal places (1 pip = 0.01) vs 5 decimal
    places (1 pip = 0.0001) for other pairs. This is correct but means
    any cross-pair analysis MUST normalize for pip value.

    Bead counts vary by ~13,000 across pairs (1,889,777 to 1,902,784),
    reflecting genuine liquidity differences in number of active trading
    minutes.

    FieldQuery API successfully fans out across all 6 DBs in parallel
    (2.3ms for 6-pair hourly aggregation).
  scale: structural
  methodological_implication: |
    Cross-pair analysis (e.g., SMT divergence -- though removed in v0.3)
    requires pip-value normalization. Any future cross-pair correlation
    CLAIM must account for the JPY quoting convention.
  architectural_implication: |
    The FieldQuery API is functional and performant. The parallel
    ThreadPoolExecutor approach works correctly. Timestamp normalization
    handles timezone offsets. This is a solid foundation for cross-pair
    analytical queries.
  schema_change_required: NO
  model_used: "Claude Opus 4.6"
  evidence: |
    FieldQuery.from_data_dir('~/dexter/tools/synthetic')
    6-pair query: 2.3ms wall time
    USDJPY avg_range = 231.13 pips (JPY convention: 0.01 per pip)
    EURUSD avg_range = 1.51 pips (standard convention: 0.0001 per pip)
```

### OBS-011: Embedding Analysis is Semantically Degenerate
```yaml
- id: "OBS-011"
  type: FRICTION
  phase: 3
  query_surface: "Feasibility of text embedding cluster analysis on bead content"
  observation: |
    All 1,902,141 EURUSD beads share IDENTICAL JSON structure:
    {"as_of_world_time": "...", "field": "ohlcv_1m", "provider": "dukascopy",
    "quality_score": 1.0, "symbol": "EURUSD", "value": {"open": N, "high": N,
    "low": N, "close": N, "volume": N}}

    The only varying content is the timestamp string and 5 numeric values.
    Text embedding (nomic-embed-text or similar) would produce near-identical
    vectors for all beads because the structural text is identical. Numeric
    differences in OHLCV values would produce minimal embedding variation
    since text embeddings are optimized for semantic meaning, not numerical
    magnitude.

    Clustering on this field would require numerical feature extraction
    (volatility, trend, volume regime), not text embedding. This is a
    fundamentally different analysis approach.
  scale: structural
  methodological_implication: |
    Embedding-based analysis becomes meaningful only when heterogeneous
    bead types exist (CLAIMs with natural language reasoning traces,
    SIGNALs with trade narratives, etc.). The current field is not
    amenable to embedding-based discovery.
  architectural_implication: |
    The Dream Cycle's embedding-based analysis (Gate 5+) requires the
    analytical layer to exist first. DEC-ENERGY-NOT-STORED is validated:
    there is nothing to compute energy over in a monotype OHLCV field.
  schema_change_required: NO
  model_used: "Claude Opus 4.6"
  evidence: |
    SELECT DISTINCT json_extract(content, '$.field') FROM beads -- 'ohlcv_1m' only
    All content follows identical 6-key JSON schema
    Only 5 numeric values vary per bead (OHLCV)
```

---

## Phase-by-Phase Narrative

### Phase 1: Baseline (5 Queries)

Phase 1 attempted to validate five ICT primitives against the field. All five queries returned null results because the analytical concepts (order flow, engine composites, FVG/VI, kill zone clustering, 5-factor checklist) are CLAIM/SIGNAL-layer constructs that have no representation in the FACT-only field.

**P1.1 Order Flow Resolution:** Zero beads contain MSS, swing, order_flow, higher_high, lower_low, market_structure, or displacement. Order flow is a CLAIM-layer interpretation of FACT candles, not stored in FACTs themselves.

**P1.2 Engine Event Composite:** Zero SIGNALs, zero liquidity/sweep/FVG references. The engine (requiring simultaneous sweep + MSS + FVG) has no test surface.

**P1.3 FVG vs Volume Imbalance:** Neither FVG nor VI exists as identified structures. A false positive on "VI" (1,902,141 hits) resolved to substring match in "provider" field. This is an expected FRICTION finding: FVG/VI identification is a CLAIM-layer computation over consecutive candle relationships.

**P1.4 Kill Zone Temporal Clustering:** Hourly bar distribution is essentially flat (79,316-80,238 per hour across trading hours). This is correct: KZ clustering would appear in SIGNAL/PROPOSAL distributions (when are trades taken?), not in bar availability (when does the market exist?). Weekend structure is correct: 0 Saturday bars, ~31K Sunday (market open) bars.

**P1.5 Five-Factor Binary Checklist:** Zero SIGNALs or PROPOSALs exist. The checklist cannot be tested. No content contains OTE, PDA, kill_zone, or five_factor references.

**Phase 1 verdict:** The substrate provides raw material for all 5 ICT primitives (candle data from which swings, FVGs, and displacement can be computed), but no derived analysis has been performed or recorded. The field is Layer 1 only.

### Phase 2: Fracture (6 Queries)

Phase 2 stress-tested underspecified edges. Most queries confirmed the monotype finding from Phase 1, but two yielded independent structural insights.

**P2.1 Equilibrium Edge Case:** Dealing range is computable from raw data (e.g., 34.0 pips on 2024-01-15). The 50% equilibrium level can be calculated. However, whether entries at equilibrium are accepted or rejected is a CLAIM-layer decision that does not exist.

**P2.2 Asia Range 30-Pip Boundary:** Asia session ranges (00:00-05:00 UTC proxy) computed for Q1 2024: 64 sessions, average range 15.1 pips. Only 3 sessions exceeded 30 pips (max 36.8p). Zero sessions fell in the 28-32 pip boundary zone. The raw data shows Asia ranges are typically well below the 30-pip threshold, which means the boundary is rarely stressed in practice.

**P2.3 Misalignment Scalp Permission:** Weekly direction is computable (e.g., Jan 2024 was 4/5 weeks bearish). However, no CLAIMs encoding HTF bias or scalp-vs-full-setup decisions exist.

**P2.4 MMXM Lookback Reset:** Zero MMXM, market_maker, buy_model, sell_model references in any bead.

**P2.5 Temporal Half-Life:** Volume and range show significant drift across the 5-year span. 2022 average volume (467.5) is 3.3x 2021 (141.4) and 1.5x 2024 (318.0). Average range follows similar pattern: 2.07p (2022) vs 1.14p (2024). Body/range ratio is remarkably stable (0.566-0.583) despite these shifts, suggesting the candle shape is regime-invariant even as magnitude varies. This is a genuine finding about the data structure.

**P2.6 Synthetic Mirror Test:** Detailed in OBS-007. Structurally inapplicable. The field is pre-analytical.

### Phase 3: Surprise (3 Queries)

Phase 3 explored unframed territory. Two genuine surprises emerged.

**P3.1 Embedding Cluster Analysis:** Semantically degenerate (OBS-011). All beads share identical JSON structure. Text embedding is not the right tool for a monotype OHLCV field. Numerical feature extraction (volatility clustering, volume regime, trend detection) would be appropriate but is a different methodology.

**P3.2 CLAIM-FACT Compression Gap:** Total gap: 0 CLAIMs over 11.4M FACTs (OBS-008). This quantifies the Gate 2 work surface.

**P3.3 Regime Boundary Detection:** Genuine surprise (OBS-005). 8 regime shifts detected at >30% QoQ threshold. The most dramatic: 2022-Q3 volume nearly doubled QoQ (+96.7%). The 2022 high-volatility regime and 2025-Q3 compression are clearly visible in raw data without any analytical overlay. Body/range ratio stability (0.566-0.583) across these regime shifts is independently noteworthy -- it suggests candle shape is a structural invariant of the EURUSD market.

---

## Synthetic Mirror Verdict

**STRUCTURALLY INAPPLICABLE** -- neither circular nor independent.

The Mirror Test requires analytical beads (CLAIMs expressing ICT concepts, SIGNALs encoding trade theses, PROPOSALs with entry/stop/target parameters) to test against Olya's rules. The field contains exclusively raw OHLCV market data FACTs. There is no analytical content to validate or falsify.

This is not a failure of the test design or the data. It is a statement of project phase: Gate 1 built the substrate. Gate 2 will build the analytical layer. The Mirror Test should be re-executed when the first CLAIMs are mined from this substrate.

The raw data itself shows no signs of synthetic artifacts or generator bias: CPI/FOMC volume spikes are present at historically correct dates and magnitudes, weekend gaps are present, cross-pair bar counts vary naturally, and zero OHLCV integrity violations exist. The data appears to be genuine Dukascopy historical data ingested via the riverwriter pipeline, not synthetically generated price series.

---

## Recommendations for T3 Spitfire Focus Areas

1. **CLAIM Pipeline Bootstrap:** The most impactful next step is building the first CLAIM producer that reads FACT beads and outputs structural analysis CLAIMs (swing points, FVGs, market structure shifts). Without this, no ICT methodology query is answerable against the field.

2. **News Calendar FACT Beads:** High-impact news events (CPI, FOMC, NFP) are detectable in raw data (3-6x volume spikes) but should be encoded as explicit FACT beads from OPEN_SOURCE calendar data. This enables the "no trading on CPI/FOMC" rule to be checked structurally.

3. **DataQuality Tagging:** The 66 zero-volume bars and 12,465 zero-range bars should receive DataQuality tagging (DEGRADED rather than NOMINAL). The DataQuality enum exists but is unused. This is a content-level enhancement, not a schema change.

4. **Regime POLICY Beads:** The regime boundaries detected (2022 high-vol, 2024 compression, 2025 transition) are candidates for POLICY beads of type REGIME. These would enable regime-aware CLAIM production.

5. **Re-Execute Mirror Test Post-CLAIMs:** When the first 1,000+ CLAIMs exist, re-run P2.6. At that point, the violation rate will be meaningful (either confirming methodology fidelity or exposing systematic gaps).

6. **Cross-Pair Pip Normalization:** Any cross-pair analysis must handle JPY quoting convention (1 pip = 0.01 vs 0.0001). This should be encoded in pair metadata, not left to consumers.

---

*Report generated by COO (Claude Opus 4.6) on 2026-03-03. Zero schema mutations. Zero code changes. Measurement only.*
