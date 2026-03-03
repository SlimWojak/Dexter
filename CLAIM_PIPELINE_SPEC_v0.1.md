# CLAIM_PIPELINE_SPEC v0.1
## First CLAIM Producer for the a8ra Bead Field
## Draft for Joist Pattern Review

**Author:** COO (Claude Opus 4.6)
**Date:** 2026-03-03
**Status:** DRAFT — Pending Joist review (GPT lint + OWL audit + BOAR stress)
**Methodology Reference:** SYNTHETIC_OLYA_METHOD v0.4 (Olya-validated)
**Repo Head:** 2edf4da
**Constraint:** DEC-SUBSTRATE-FREEZE active (~21 days remaining) — ZERO schema mutations

---

## 1. CLAIM TYPE TAXONOMY

### 1.0 Schema Mapping Convention

All CLAIMs use the existing `ClaimContent` schema (frozen):

```yaml
ClaimContent:
  conclusion: str       # "{CLAIM_SUBTYPE}: {structured_summary}"
  reasoning_trace: str  # JSON string — full computational record (INV-LLM-REMOVAL-TEST)
  premises_ref: list[str]  # Bead IDs of input FACTs/CLAIMs
  confidence_basis: str    # "DETERMINISTIC" | "ALGORITHMIC" | "COMPOSITE"
  drawer: Drawer           # One of: HTF_BIAS, MARKET_STRUCTURE, PREMIUM_DISCOUNT, ENTRY_MODEL, CONFIRMATION
  icm_terms: list[str]     # ICT vocabulary tags for searchability
```

**Convention — NOT schema change:**
- `conclusion` follows template: `{TYPE}: {human_readable_summary}`
- `reasoning_trace` is a JSON string containing the full machine-parseable record. Fields vary by claim type but always include `claim_subtype`, `instrument`, and type-specific data. This satisfies INV-LLM-REMOVAL-TEST: any CLAIM is reconstructable from `reasoning_trace` without LLM reasoning.
- `confidence_basis` uses one of three values:
  - `DETERMINISTIC` — purely geometric, reproducible from input FACTs alone
  - `ALGORITHMIC` — parameterized algorithm, reproducible given parameters
  - `COMPOSITE` — derived from other CLAIMs, reproducible given inputs

### 1.1 SWING_POINT

```yaml
type: SWING_POINT
subtype: HH | HL | LH | LL
temporal_class: OBSERVATION
drawer: MARKET_STRUCTURE
input_beads: "N+1 FACT candles (N lookback + 1 pivot)"
timeframe: 1m (base), derived for 5m/15m/60m/4H/D via candle aggregation
methodology_ref: "v0.4 → framework.order_flow.determination.order_flow_read"
confidence_basis: DETERMINISTIC

reasoning_trace_schema:
  claim_subtype: "SWING_POINT"
  swing_type: "HH" | "HL" | "LH" | "LL"
  price: float          # Wick extreme of the pivot candle
  bar_time: str         # ISO timestamp of pivot candle
  lookback_bars: int    # N parameter (configurable, default 5)
  direction: "BULLISH" | "BEARISH" | null  # Derived: HH/HL=BULLISH, LH/LL=BEARISH
  prior_swing_ref: str | null  # bead_id of the previous swing this classifies against
  instrument: "EURUSD"
  source_timeframe: "1m" | "5m" | "15m" | "60m" | "4H" | "D"

detection_algorithm: |
  A bar at index i is a swing HIGH if:
    high[i] > max(high[i-N:i]) AND high[i] > max(high[i+1:i+N+1])
  A bar at index i is a swing LOW if:
    low[i] < min(low[i-N:i]) AND low[i] < min(low[i+1:i+N+1])
  Classification (HH/HL/LH/LL) requires comparing to the PREVIOUS swing
  of the same polarity (high-to-high, low-to-low).

expected_ratio: "~1 swing per 50-200 candles depending on timeframe and N"
```

### 1.2 FVG (Fair Value Gap)

```yaml
type: FVG
subtype: BULLISH_FVG | BEARISH_FVG
temporal_class: OBSERVATION
drawer: MARKET_STRUCTURE
input_beads: "Exactly 3 consecutive FACT candles (A, B, C)"
timeframe: 1m (base), derived for 5m/15m
methodology_ref: "v0.4 → lokz_manipulation.engine_event_detection.components.fvg"
confidence_basis: DETERMINISTIC

reasoning_trace_schema:
  claim_subtype: "FVG"
  fvg_direction: "BULLISH" | "BEARISH"
  gap_high: float       # Top boundary of the gap
  gap_low: float        # Bottom boundary of the gap
  gap_size_pips: float  # (gap_high - gap_low) / pip_unit
  candle_a_time: str    # ISO timestamp of Candle A
  candle_b_time: str    # ISO timestamp of Candle B (displacement candle)
  candle_c_time: str    # ISO timestamp of Candle C
  candle_a_id: str      # bead_id of Candle A FACT
  candle_b_id: str      # bead_id of Candle B FACT
  candle_c_id: str      # bead_id of Candle C FACT
  instrument: "EURUSD"
  pip_unit: float       # 0.0001 for EURUSD (configurable, not hardcoded)
  source_timeframe: str

detection_algorithm: |
  BULLISH_FVG: candle_A.high < candle_C.low
    gap_high = candle_C.low
    gap_low = candle_A.high
  BEARISH_FVG: candle_A.low > candle_C.high
    gap_high = candle_A.low
    gap_low = candle_C.high
  Per v0.4: wick-to-wick measurement.

expected_ratio: "~1 FVG per 20-50 candles in trending conditions"
```

### 1.3 VI (Volume Imbalance)

```yaml
type: VI
subtype: BULLISH_VI | BEARISH_VI
temporal_class: OBSERVATION
drawer: MARKET_STRUCTURE
input_beads: "Exactly 3 consecutive FACT candles (A, B, C)"
timeframe: 1m (base), derived for 5m/15m
methodology_ref: "v0.4 → lokz_manipulation.engine_event_detection.components.vi"
confidence_basis: DETERMINISTIC

reasoning_trace_schema:
  claim_subtype: "VI"
  vi_direction: "BULLISH" | "BEARISH"
  gap_high: float       # Top boundary (body edge)
  gap_low: float        # Bottom boundary (body edge)
  gap_size_pips: float
  candle_a_time: str
  candle_b_time: str
  candle_c_time: str
  candle_a_id: str
  candle_b_id: str
  candle_c_id: str
  has_wick_overlap: bool  # True if wicks overlap but bodies don't
  instrument: "EURUSD"
  pip_unit: float
  source_timeframe: str

detection_algorithm: |
  BULLISH_VI: max(candle_A.open, candle_A.close) < min(candle_C.open, candle_C.close)
    gap_high = min(candle_C.open, candle_C.close)  # body bottom of C
    gap_low = max(candle_A.open, candle_A.close)    # body top of A
  BEARISH_VI: min(candle_A.open, candle_A.close) > max(candle_C.open, candle_C.close)
    gap_high = min(candle_A.open, candle_A.close)   # body bottom of A
    gap_low = max(candle_C.open, candle_C.close)    # body top of C
  Per v0.4: body-to-body measurement. Wicks may overlap.

note: "Treated identically to FVG in all trading logic (v0.4 vi_treatment)"
expected_ratio: "~1.5-3x FVG count (body gaps are more common than wick gaps)"
```

### 1.4 SESSION_BOUNDARY

```yaml
type: SESSION_BOUNDARY
subtype: ASIA_OPEN | ASIA_CLOSE | LOKZ_OPEN | LOKZ_CLOSE | NYOKZ_OPEN | NYOKZ_CLOSE | DAY_OPEN | MIDNIGHT_OPEN
temporal_class: OBSERVATION
drawer: HTF_BIAS
input_beads: "1-2 FACT candles at boundary timestamps"
timeframe: 1m
methodology_ref: "v0.4 → chart_setup.sessions, session_monitoring.midnight_open"
confidence_basis: DETERMINISTIC

reasoning_trace_schema:
  claim_subtype: "SESSION_BOUNDARY"
  boundary_type: str    # ASIA_OPEN, etc.
  boundary_time_ny: str # NY local time (e.g., "19:00")
  boundary_time_utc: str  # Computed UTC equivalent (handles DST)
  price_at_boundary: float  # Close of the boundary candle
  instrument: "EURUSD"
  is_dst: bool          # Whether DST was active at this time
  trading_date: str     # The "forex day" this belongs to (17:00 NY boundary)

detection_algorithm: |
  For each trading day (17:00 NY to 17:00 NY next day):
    Find the candle closest to each session boundary time.
    NY to UTC conversion:
      EST (Nov-Mar): UTC-5 → Asia open 19:00 NY = 00:00 UTC next day
      EDT (Mar-Nov): UTC-4 → Asia open 19:00 NY = 23:00 UTC
    DST transitions handled via pytz/zoneinfo.

note: "Produces 8 CLAIMs per trading day. ~250 trading days/year = ~2,000/year"
expected_ratio: "8 per trading day, deterministic"
```

### 1.5 ASIA_RANGE

```yaml
type: ASIA_RANGE
subtype: VALID | EXCEEDED
temporal_class: OBSERVATION
drawer: HTF_BIAS
input_beads: "All FACT candles in 19:00-00:00 NY window + SESSION_BOUNDARY CLAIMs"
timeframe: 1m (computed from 1m candles in session window)
methodology_ref: "v0.4 → pre_session.asia_range_filter"
confidence_basis: DETERMINISTIC

reasoning_trace_schema:
  claim_subtype: "ASIA_RANGE"
  session_date: str     # Trading date
  high: float           # Session high (wick)
  low: float            # Session low (wick)
  range_pips: float     # (high - low) / pip_unit
  is_valid: bool        # range_pips <= 30
  candle_count: int     # Number of 1m candles in session
  high_candle_id: str   # bead_id of the candle with the high
  low_candle_id: str    # bead_id of the candle with the low
  instrument: "EURUSD"
  pip_unit: float

detection_algorithm: |
  Collect all FACT candles where bar_time falls within Asia session (19:00-00:00 NY).
  high = max(all candle highs)
  low = min(all candle lows)
  range_pips = (high - low) / pip_unit
  is_valid = range_pips <= 30

note: "One per trading day. Feeds into LOKZ skip decision."
expected_ratio: "1 per trading day"
```

### 1.6 PDH_PDL (Previous Day High/Low)

```yaml
type: PDH_PDL
temporal_class: OBSERVATION
drawer: HTF_BIAS
input_beads: "All FACT candles in previous forex day (17:00-17:00 NY)"
timeframe: Daily (computed from 1m candles)
methodology_ref: "v0.4 → pre_session.dealing_range_identification.pdh_pdl_definition"
confidence_basis: DETERMINISTIC

reasoning_trace_schema:
  claim_subtype: "PDH_PDL"
  trading_date: str     # The day these levels belong to
  previous_day_date: str  # The day these were computed from
  pdh: float            # Previous day high (WICK, not close — per v0.4)
  pdl: float            # Previous day low (WICK, not close — per v0.4)
  range_pips: float     # (pdh - pdl) / pip_unit
  pdh_candle_id: str    # bead_id of the candle with the high
  pdl_candle_id: str    # bead_id of the candle with the low
  day_boundary: str     # "17:00 NY" (per v0.4 pdh_pdl_definition)
  instrument: "EURUSD"
  pip_unit: float

note: "Forex day boundary is 17:00 NY, NOT midnight."
expected_ratio: "1 per trading day"
```

### 1.7 ORDER_FLOW (Phase 2 — Sketched)

```yaml
type: ORDER_FLOW
subtype: BULLISH | BEARISH | MIXED
temporal_class: OBSERVATION
drawer: HTF_BIAS
input_beads: "SWING_POINT CLAIMs from target timeframe"
timeframe: Daily, H4 (multi-timeframe)
methodology_ref: "v0.4 → framework.order_flow"
confidence_basis: ALGORITHMIC

reasoning_trace_schema:
  claim_subtype: "ORDER_FLOW"
  direction: "BULLISH" | "BEARISH" | "MIXED"
  pattern: "HH+HL" | "LH+LL" | "MIXED"
  swing_sequence: list   # Ordered list of swing CLAIMs used
  timeframe: str
  assessment_date: str
  instrument: "EURUSD"

note: |
  Phase 2 — requires SWING_POINT CLAIMs to exist first.
  "HH+HL = bullish, LH+LL = bearish, mixed = no trade" (v0.4)
  This is the Layer 1 gate. Gets everything.
```

### 1.8 MSS (Market Structure Shift — Phase 2 — Sketched)

```yaml
type: MSS
subtype: BULLISH_MSS | BEARISH_MSS
temporal_class: OBSERVATION
drawer: MARKET_STRUCTURE
input_beads: "SWING_POINT CLAIMs + FVG/VI CLAIMs + FACT candles"
timeframe: 15m, 60m, Daily
methodology_ref: "v0.4 → lokz_manipulation.engine_event_detection.components.mss"
confidence_basis: COMPOSITE

reasoning_trace_schema:
  claim_subtype: "MSS"
  mss_direction: "BULLISH" | "BEARISH"
  broken_swing_ref: str    # bead_id of the SWING_POINT CLAIM that was broken
  broken_swing_price: float
  displacement_present: bool
  displacement_factors:    # Binary checklist — NOT scored
    forceful_exit: bool
    structure_removed: bool
    fvg_left: bool
    one_sided: bool
    no_rotation: bool
  fvg_or_vi_ref: str | null  # bead_id of the FVG/VI CLAIM created
  instrument: "EURUSD"

note: |
  Phase 2 — requires SWING_POINT + FVG/VI CLAIMs.
  Displacement is a 5-component binary checklist, NOT a pip threshold (v0.4).
  This avoids ScalarBan while maintaining the qualitative nature of Olya's definition.
  The 5 displacement factors are machine-evaluable binary checks:
    1. forceful_exit: Close of displacement candle > 2x median candle body size
    2. structure_removed: Prior swing broken on close (not just wick)
    3. fvg_left: FVG or VI exists in the displacement sequence
    4. one_sided: >80% of candle bodies in displacement direction
    5. no_rotation: No opposing swing within displacement sequence
  ALL 5 must be TRUE for displacement = TRUE.
  Joist review needed: Are these 5 checks faithful to Olya's qualitative intent?
```

### 1.9 DEALING_RANGE (Phase 2 — Sketched)

```yaml
type: DEALING_RANGE
temporal_class: OBSERVATION
drawer: PREMIUM_DISCOUNT
input_beads: "SWING_POINT CLAIMs + MSS CLAIMs"
timeframe: Daily, H4
methodology_ref: "v0.4 → pre_session.dealing_range_identification"
confidence_basis: COMPOSITE

reasoning_trace_schema:
  claim_subtype: "DEALING_RANGE"
  range_high: float
  range_low: float
  equilibrium: float    # (range_high + range_low) / 2
  range_pips: float
  boundary_type_high: str  # "EQUAL_HIGHS" | "PDH" | "MSS_SWING" | "VALIDATED_SWING"
  boundary_type_low: str
  high_ref: str         # bead_id of the boundary CLAIM
  low_ref: str
  instrument: "EURUSD"

note: "Phase 2. Boundaries follow v0.4 priority: Equal H/L > PDH/PDL > MSS Swings > Validated Swings"
```

### 1.10 OTE_ZONE (Phase 2 — Sketched)

```yaml
type: OTE_ZONE
temporal_class: OBSERVATION
drawer: ENTRY_MODEL
input_beads: "DEALING_RANGE CLAIM + SWING_POINT CLAIMs"
methodology_ref: "v0.4 → entry_execution.ote_confirmation"
confidence_basis: DETERMINISTIC

reasoning_trace_schema:
  claim_subtype: "OTE_ZONE"
  ote_high: float       # 61.8% retracement level
  ote_low: float        # 79% retracement level
  range_ref: str        # bead_id of DEALING_RANGE CLAIM
  fib_anchor_high: float
  fib_anchor_low: float
  instrument: "EURUSD"

note: "Phase 2. Deterministic once DEALING_RANGE exists. fib_range: [0.618, 0.79] per v0.4"
```

### Taxonomy Summary Table

```
| # | CLAIM Type       | Drawer            | Temporal Class | Phase | Confidence     | Inputs              |
|---|------------------|-------------------|----------------|-------|----------------|----------------------|
| 1 | SWING_POINT      | MARKET_STRUCTURE  | OBSERVATION    | 1     | DETERMINISTIC  | N+1 FACT candles     |
| 2 | FVG              | MARKET_STRUCTURE  | OBSERVATION    | 1     | DETERMINISTIC  | 3 FACT candles       |
| 3 | VI               | MARKET_STRUCTURE  | OBSERVATION    | 1     | DETERMINISTIC  | 3 FACT candles       |
| 4 | SESSION_BOUNDARY | HTF_BIAS          | OBSERVATION    | 1     | DETERMINISTIC  | 1-2 FACT candles     |
| 5 | ASIA_RANGE       | HTF_BIAS          | OBSERVATION    | 1     | DETERMINISTIC  | FACT window + SB     |
| 6 | PDH_PDL          | HTF_BIAS          | OBSERVATION    | 1     | DETERMINISTIC  | FACT day window      |
| 7 | ORDER_FLOW       | HTF_BIAS          | OBSERVATION    | 2     | ALGORITHMIC    | SWING_POINT CLAIMs   |
| 8 | MSS              | MARKET_STRUCTURE  | OBSERVATION    | 2     | COMPOSITE      | SWING + FVG/VI + FACT|
| 9 | DEALING_RANGE    | PREMIUM_DISCOUNT  | OBSERVATION    | 2     | COMPOSITE      | SWING + MSS CLAIMs   |
|10 | OTE_ZONE         | ENTRY_MODEL       | OBSERVATION    | 2     | DETERMINISTIC  | DEALING_RANGE CLAIM  |
```

---

## 2. PIPELINE ARCHITECTURE

### 2.1 Chosen Approach: TIERED (Option C)

**Rationale:** The ICT methodology has a natural dependency hierarchy — you need swings before you can detect MSS, you need MSS before you can determine order flow, you need dealing ranges before you can compute OTE zones. A tiered architecture mirrors this dependency structure directly.

```yaml
architecture: TIERED
tiers:
  tier_1_structural:
    name: "Structural Primitives"
    producers: [SWING_POINT, FVG, VI, SESSION_BOUNDARY, ASIA_RANGE, PDH_PDL]
    reads: "FACT beads only (direct SQLite query)"
    writes: "CLAIM beads via IngestionPipeline"
    dependency: "None — runs on raw FACT field"
    parallelism: "SWING_POINT, FVG, VI can run in parallel on same candle stream"

  tier_2_composite:
    name: "Composite Analysis"
    producers: [ORDER_FLOW, MSS, DEALING_RANGE, OTE_ZONE]
    reads: "FACT beads + Tier 1 CLAIMs"
    writes: "CLAIM beads via IngestionPipeline"
    dependency: "Tier 1 must complete for the relevant time window"
```

### 2.2 Read Path

```yaml
read_strategy: "Direct SQLite via FieldQuery API"
rationale: |
  The FieldQuery API is tested and performant (2.3ms for 6-pair queries, OBS-010).
  CLAIM producers read FACTs in chronological order via:
    SELECT * FROM beads
    WHERE bead_type = 'FACT'
      AND world_time_valid_from >= ?
      AND world_time_valid_from < ?
    ORDER BY world_time_valid_from

  Tier 2 producers additionally query CLAIMs:
    SELECT * FROM beads
    WHERE bead_type = 'CLAIM'
      AND json_extract(content, '$.claim_subtype') = 'SWING_POINT'
      AND world_time_valid_from >= ?
      AND world_time_valid_from < ?

windowing: |
  Producers process data in DAY windows (17:00 NY to 17:00 NY per v0.4 day boundary).
  Each window overlaps by the lookback period (e.g., N bars for swing detection).
  This bounds memory usage and enables parallel processing of different days.

database: "EURUSD only — synthetic_beads.db (1,902,141 FACTs)"
```

### 2.3 Write Path

```yaml
write_strategy: "Standard IngestionPipeline"
rationale: |
  All CLAIMs go through the existing IngestionPipeline (pipeline.py).
  This ensures:
    - Schema validation via Pydantic (ClaimBead model)
    - UUID v7 assignment
    - HLC timestamp for KT
    - Hash chain linking (single chain, SPF-001 architecture)
    - Dual PQC+ECDSA signing
    - Store insertion with immutability trigger
    - Merkle batch recording

  No direct store access. No bypass. INV-BEAD-SIGNED enforced.

pipeline_configuration:
  air_node_id: "claim-pipeline-v1"
  code_hash: "{git_commit_hash}"    # Tracks which code produced the CLAIMs
  source_ref:
    source_type: AGENT              # CLAIMs are agent-produced
    source_id: "claim-producer-v1"
    source_version: "0.1.0"
```

### 2.4 Hash Chain Integrity

```yaml
chain_strategy: "Single pipeline instance per production run"
rationale: |
  Per SPF-001, the pipeline uses a single hash chain. All CLAIMs link into
  the same chain as existing FACTs. This is correct for sequential production.

  For Tier 1 parallel producers (SWING_POINT, FVG, VI running simultaneously):
    Option A: Serialize outputs through a single pipeline instance (queue)
    Option B: Each producer gets its own pipeline instance (separate chains)

  CHOSEN: Option A — serialize through single pipeline.
  Rationale: Maintains single chain. Simpler verification. Parallel computation,
  serial ingestion. The bottleneck is computation, not ingestion.

chain_ordering: |
  Within a day window, CLAIMs are ingested in chronological order of their
  world_time (the market time of the pattern, not the detection time).
  When multiple CLAIMs have the same WT (e.g., FVG and VI from the same
  3 candles), order is: SWING_POINT → FVG → VI (deterministic tiebreak).
```

### 2.5 Lineage (input_bead_ids)

```yaml
lineage_strategy: "Explicit bead_id references in both lineage and premises_ref"

lineage_field: |
  BeadCore.lineage (list[str]) carries the UUIDs of ALL input beads.
  This is the machine-traversable provenance chain.

premises_ref_field: |
  ClaimContent.premises_ref (list[str]) carries the same UUIDs.
  This is the claim-level reference for reasoning inspection.

  Both fields carry the SAME values. Redundancy is intentional:
  lineage is on BeadCore (universal), premises_ref is on ClaimContent (semantic).

verification: |
  Per SPF-012 recommendation: lineage validation should be enabled for
  production ingestion. Each referenced bead_id must exist in the store.
  Validate before ingestion, fail loudly on phantom references.
```

### 2.6 KT Handling (OBS-002)

```yaml
kt_strategy: "CLAIM KT = detection time (HLC tick), WT = market time of pattern"
rationale: |
  Per bead spec: KT is when the system LEARNED about the pattern.
  For batch backfill of historical CLAIMs, KT will cluster near the
  production run time (same issue as OBS-002 for FACTs).

  This is acceptable for Phase 1 (batch historical analysis).
  When live ingestion begins, CLAIMs will have KT near their WT
  (detecting swings as they form), creating natural KT spread.

  WT is the market time of the pattern:
    SWING_POINT WT = time of the pivot candle
    FVG/VI WT = time of Candle C (the candle that creates the gap)
    SESSION_BOUNDARY WT = the boundary timestamp
    ASIA_RANGE WT from = session start, WT to = session end
```

---

## 3. LINEAGE MODEL

### 3.1 Input Counts Per Type

```yaml
SWING_POINT:
  fact_inputs: "2*N+1 FACT candles (N lookback on each side + pivot)"
  claim_inputs: "0 (Tier 1 — no CLAIM dependencies)"
  typical: "11 FACTs for N=5"

FVG:
  fact_inputs: "Exactly 3 FACT candles"
  claim_inputs: "0"

VI:
  fact_inputs: "Exactly 3 FACT candles"
  claim_inputs: "0"

SESSION_BOUNDARY:
  fact_inputs: "1-2 FACT candles (at boundary time)"
  claim_inputs: "0"

ASIA_RANGE:
  fact_inputs: "~300 FACT candles (5 hours × ~60 bars/hour)"
  claim_inputs: "2 SESSION_BOUNDARY CLAIMs (ASIA_OPEN, ASIA_CLOSE)"

PDH_PDL:
  fact_inputs: "~1300 FACT candles (full forex day)"
  claim_inputs: "2 SESSION_BOUNDARY CLAIMs (DAY_OPEN boundaries)"

ORDER_FLOW (Phase 2):
  fact_inputs: "0 (reads CLAIMs only)"
  claim_inputs: "4+ SWING_POINT CLAIMs (minimum 2 highs + 2 lows for pattern)"

MSS (Phase 2):
  fact_inputs: "Displacement candle sequence (3-10 FACTs)"
  claim_inputs: "1 SWING_POINT (broken swing) + 1 FVG or VI (displacement evidence)"

DEALING_RANGE (Phase 2):
  fact_inputs: "0"
  claim_inputs: "2+ SWING_POINT/MSS CLAIMs (range boundaries)"

OTE_ZONE (Phase 2):
  fact_inputs: "0"
  claim_inputs: "1 DEALING_RANGE CLAIM"
```

### 3.2 Verification Rules

```yaml
rules:
  - name: "EXISTENCE_CHECK"
    description: "Every bead_id in lineage must exist in the store"
    enforcement: "Pre-ingestion query: SELECT COUNT(*) FROM beads WHERE bead_id IN (?...)"
    on_failure: "Reject CLAIM — do not ingest phantom lineage"

  - name: "TYPE_CHECK"
    description: "Lineage bead types must match expected inputs for the CLAIM subtype"
    enforcement: |
      FVG lineage must contain exactly 3 FACT beads.
      ORDER_FLOW lineage must contain only CLAIM beads with subtype SWING_POINT.
    on_failure: "Reject CLAIM — type mismatch in lineage"

  - name: "TEMPORAL_ORDER"
    description: "Input FACTs must be in chronological order"
    enforcement: "Verify world_time_valid_from is monotonically increasing in lineage"
    on_failure: "Reject CLAIM — temporal disorder in inputs"

  - name: "CONTIGUITY_CHECK"
    description: "For FVG/VI, the 3 input candles must be consecutive (no gaps > 1 bar)"
    enforcement: "Verify bar timestamps are sequential (allowing for market gaps)"
    on_failure: "Reject CLAIM — input candles not contiguous"
```

### 3.3 Chain Walk Compatibility

```yaml
compatibility: |
  The chain walk API (query/chain.py) traverses via hash_prev linkage,
  not lineage. CLAIMs appear in the chain alongside FACTs.

  Lineage traversal is SEPARATE from chain walk:
  - Chain walk: temporal/insertion order traversal (backward via hash_prev)
  - Lineage walk: semantic dependency traversal (CLAIM → source FACTs/CLAIMs)

  To traverse lineage, query by bead_id from the CLAIM's lineage list.
  This is a different access pattern than chain walk and may benefit from
  a dedicated lineage_walk() function in the query layer (Phase 2 scope).

depth: |
  Maximum lineage depth for Phase 1: 2 levels (CLAIM → FACT)
  Maximum lineage depth for Phase 2: 3 levels (COMPOSITE → CLAIM → FACT)
  Example: OTE_ZONE → DEALING_RANGE → SWING_POINT → FACT candles
```

---

## 4. VALIDATION STRATEGY

### 4.1 Ground Truth Per CLAIM Type

```yaml
DETERMINISTIC_TYPES:
  description: "Purely geometric/algorithmic. Ground truth is recomputation."
  types: [SWING_POINT, FVG, VI, SESSION_BOUNDARY, ASIA_RANGE, PDH_PDL, OTE_ZONE]
  validation: |
    Given the same input FACTs and parameters, the CLAIM MUST produce
    identical output. Test by:
    1. Run producer on known candle sequence
    2. Verify output matches hand-computed expected values
    3. Re-run — output must be bitwise identical
  ground_truth: "Mathematical recomputation from input candles"
  mirror_risk: NONE — no LLM judgment involved

ALGORITHMIC_TYPES:
  description: "Parameterized algorithm. Ground truth is parameter sensitivity analysis."
  types: [ORDER_FLOW]
  validation: |
    Given a known swing sequence (HH, HL, HH, HL), ORDER_FLOW must output BULLISH.
    Given (LH, LL, LH, LL), must output BEARISH.
    Given (HH, LL), must output MIXED.
  ground_truth: "Pattern matching on swing sequence — deterministic given swings"
  mirror_risk: LOW — depends on SWING_POINT quality, not LLM judgment

COMPOSITE_TYPES:
  description: "Multi-input analysis. Ground truth requires staged validation."
  types: [MSS, DEALING_RANGE]
  validation: |
    MSS validation requires:
    1. Verify the broken swing exists and was actually broken (close beyond swing price)
    2. Verify displacement factors are correctly evaluated (5 binary checks)
    3. Verify FVG/VI exists in the displacement sequence

    DEALING_RANGE validation requires:
    1. Verify boundary selection follows v0.4 priority order
    2. Verify equilibrium = (high + low) / 2
  ground_truth: "Staged recomputation — each factor independently verifiable"
  mirror_risk: MEDIUM — displacement factors involve judgment thresholds
```

### 4.2 Test Approach

```yaml
test_suite_structure:
  unit_tests:
    description: "Per-producer, per-CLAIM-type, known-input/known-output"
    count_estimate: "~50 tests per CLAIM type × 6 Phase 1 types = ~300 tests"
    examples:
      - "test_swing_point_hh: Known 11-candle sequence → expect HH at index 5"
      - "test_fvg_bullish: 3 candles where A.high < C.low → expect BULLISH_FVG"
      - "test_vi_bullish: 3 candles where A.body_top < C.body_bottom → expect BULLISH_VI"
      - "test_no_fvg: 3 candles where A.high >= C.low → expect no CLAIM produced"
      - "test_asia_range_exceeded: Asia range = 35 pips → expect EXCEEDED subtype"

  integration_tests:
    description: "Full pipeline: FACT candles → IngestionPipeline → stored CLAIMs → verify"
    count_estimate: "~20 integration tests"
    examples:
      - "test_fvg_round_trip: Ingest 3 FACTs → produce FVG CLAIM → verify in store → verify hash"
      - "test_lineage_validation: Ingest CLAIM with phantom lineage → expect rejection"

  regression_tests:
    description: "Run on known historical windows, compare against hand-labeled ground truth"
    approach: |
      Select 5-10 historical day windows from the synthetic field.
      Hand-label: swing points, FVGs, VIs, session boundaries.
      Run producer. Compare output to hand labels.
      Any discrepancy is a bug in the producer, not the test.
    golden_windows:
      - "2024-01-15 (normal trading day, well-studied in T2)"
      - "2024-06-12 (FOMC day — high volatility, OBS-006)"
      - "2021-01-04 (low volatility period, OBS-005)"
      - "2022-09-15 (peak volatility regime, OBS-005)"
      - "2024-10-09 (zero-volume bar cluster, OBS-004)"
```

### 4.3 Mirror Risk Mitigation

```yaml
owl_warning: |
  "If an LLM reads candles and produces CLAIMs, and another LLM reads
  CLAIMs and validates them, we're back in the mirror."

mitigation:
  phase_1: |
    ALL Phase 1 CLAIM types are DETERMINISTIC. No LLM judgment.
    Producers are pure algorithms: candle data in, CLAIM out.
    Validation is recomputation: same inputs → same outputs.
    Mirror risk is ZERO for Phase 1.

  phase_2: |
    MSS displacement factors involve judgment-like thresholds:
    - "forceful_exit: Close > 2x median candle body" — this IS a threshold
    - Olya says "qualitative — no pip thresholds" but we need machine evaluation

    Options for Joist review:
    A) Accept threshold-based binary checks as operational approximation
       (each factor is binary PASS/FAIL, not scored)
    B) Flag MSS CLAIMs as requiring human validation (INV-HUMAN-FRAMES)
    C) Use cross-family model to evaluate displacement (INV-CROSS-FAMILY)

    Recommendation: Option A for initial pipeline, with Option B as
    audit overlay. Human (Olya) validates a sample of MSS CLAIMs to
    calibrate threshold fidelity.

  inv_human_frames: |
    "Human frames. Machine computes. Human promotes."
    The CLAIM pipeline COMPUTES structural analysis.
    The CLAIM taxonomy was FRAMED by humans (Olya v0.4 methodology).
    CLAIMs are NOT promoted to FACT — they remain CLAIMs (INV-CLAIM-FACT-SEPARATION).
    Human validates CLAIM quality through sampling, not wholesale review.
```

---

## 5. T2 INTEGRATION

### 5.1 KT Handling (OBS-002)

```yaml
issue: "All 11.4M FACT beads have KT within 23-minute window (batch ingestion)"
impact_on_claims: |
  CLAIM KT will also cluster if produced in batch backfill.
  This is acceptable — KT represents when the system DETECTED the pattern,
  not when the pattern OCCURRED (that's WT).

  For historical backfill: KT ≈ production run time (clustered)
  For live operation: KT ≈ WT + processing latency (spread naturally)

design_response: |
  No special handling needed. The HLC tick in IngestionPipeline
  produces unique microsecond-precision KT values (same as FACTs).
  Bi-temporal queries on CLAIMs should primarily use WT predicates.
  KT predicates become meaningful only in live operation.
```

### 5.2 Zero-Bar Handling (OBS-004)

```yaml
issue: "12,465 zero-range bars (0.66%) and 66 zero-volume bars (0.0035%)"

design_response:
  swing_detection: |
    INCLUDE zero-range bars. A bar with high=low IS a valid price observation.
    It cannot be a swing high or low (high == low means it's never the
    local maximum or minimum unless ALL surrounding bars are also zero-range).
    Natural handling, no special case needed.

  fvg_detection: |
    INCLUDE zero-range bars. A zero-range bar CAN participate in an FVG:
    if Candle B is zero-range but A.high < C.low, the FVG is valid.
    The gap exists regardless of Candle B's range.

  vi_detection: |
    INCLUDE zero-range bars. A zero-range bar has body_top == body_bottom
    (open == close). This can still produce a body-to-body gap if A.close < C.open.

  zero_volume_bars: |
    INCLUDE but TAG. The 66 zero-volume bars should produce CLAIMs that include
    a quality note in the reasoning_trace:
      "quality_note": "includes_zero_volume_bar"
    This uses the existing string field, not a new schema field.
    Tag the CLAIM: tags = [..., "data_quality:degraded_input"]

  recommendation_for_gate3: |
    When DataQuality tagging is implemented (T2 recommendation #3),
    update FACT beads for the 66 zero-volume bars to quality=DEGRADED.
    CLAIMs built on DEGRADED FACTs should inherit a degraded tag.
```

### 5.3 Regime Awareness (OBS-005)

```yaml
issue: "8 regime shifts detected. 3x volume difference 2021 vs 2022."

design_response: |
  CLAIMs are NOT regime-normalized. Raw values are stored.
  Rationale:
    - Normalization would introduce a score/transform (ScalarBan risk)
    - Different FVG sizes across regimes are FACTS, not problems
    - Regime context should be carried as metadata, not baked into values

  Tagging approach:
    - Phase 1 CLAIMs carry a regime tag in their tags list
    - Tags use the format: "regime:{regime_id}" where regime_id references
      a POLICY bead (when they exist) or a provisional label
    - Provisional labels: "regime:low_vol_2021", "regime:high_vol_2022", etc.

  POLICY bead production (separate from CLAIM pipeline):
    - T2 recommendation #4: Regime boundaries → POLICY beads of type REGIME
    - These are POLICY beads, not CLAIMs — different pipeline
    - CLAIM pipeline reads active POLICY bead for regime tagging

  FVG/VI size interpretation:
    - A 2-pip FVG in 2021 (low vol) is contextually different from a 2-pip FVG in 2022 (high vol)
    - The CLAIM records the raw gap_size_pips
    - Regime-aware interpretation is a Phase 3 concern (SIGNAL production)
```

### 5.4 Pip Convention (OBS-010)

```yaml
issue: "USDJPY range is 150x larger due to JPY quoting convention"

design_response: |
  Phase 1 scope: EURUSD only (v0.4 instrument_scope).
  JPY quoting is NOT relevant yet.

  Design principle: pip_unit is a PARAMETER, not a constant.
    EURUSD: pip_unit = 0.0001
    USDJPY: pip_unit = 0.01

  Every CLAIM that reports pip values includes pip_unit in reasoning_trace.
  No hardcoded 0.0001 anywhere in the pipeline code.

  When expanding to other pairs:
    - pip_unit loaded from instrument configuration (not code)
    - All pip calculations use: pip_count = price_diff / pip_unit
    - Cross-pair comparisons must account for pip_unit differences
```

---

## 6. PHASING

### 6.1 Phase 1 — Minimum Viable CLAIM Set

```yaml
scope: "6 CLAIM types, EURUSD only, deterministic producers"
types: [SWING_POINT, FVG, VI, SESSION_BOUNDARY, ASIA_RANGE, PDH_PDL]
timeframes: [1m, 5m, 15m]  # Swing detection at multiple TFs

estimated_output:
  SWING_POINT: "~10,000-50,000 CLAIMs (varies by lookback N and timeframe)"
  FVG: "~20,000-100,000 CLAIMs (depends on trend conditions)"
  VI: "~30,000-150,000 CLAIMs (more common than FVG)"
  SESSION_BOUNDARY: "~10,000 CLAIMs (8 per day × ~1,250 trading days)"
  ASIA_RANGE: "~1,250 CLAIMs (1 per trading day)"
  PDH_PDL: "~1,250 CLAIMs (1 per trading day)"
  TOTAL_ESTIMATE: "~70,000-300,000 Phase 1 CLAIMs"

what_this_enables:
  - "Swing sequence verification (are swings correctly classified?)"
  - "FVG/VI detection verification (are gaps correctly identified?)"
  - "Session structure verification (are boundaries correctly placed?)"
  - "Asia Range filter verification (are ranges correctly computed?)"
  - "PDH/PDL level verification (are levels correctly measured?)"
  - "Foundation for Phase 2 composite analysis"

what_this_does_NOT_enable:
  - "Mirror Test (needs MSS, ORDER_FLOW, SIGNAL types)"
  - "5-factor checklist testing (needs SIGNAL/PROPOSAL)"
  - "Kill zone compliance testing (needs PROPOSAL with entry times)"

exit_criteria:
  - "All 6 CLAIM types produce valid CLAIMs on EURUSD field"
  - "300+ unit tests, all PASS"
  - "Regression tests on 5 golden windows match hand-labeled ground truth"
  - "Lineage validation enabled and passing"
  - "Hash chain and Merkle verification pass on mixed FACT+CLAIM field"
  - "CLAIM:FACT ratio within expected bounds (Phase 1: ~0.01-0.03)"
```

### 6.2 Phase 2 — Interpretive CLAIMs (Sketched)

```yaml
scope: "4 CLAIM types, EURUSD only, composite producers"
types: [ORDER_FLOW, MSS, DEALING_RANGE, OTE_ZONE]
depends_on: "Phase 1 complete"

what_this_enables:
  - "Directional read verification (ORDER_FLOW matches manual analysis)"
  - "MSS detection verification (structural shifts correctly identified)"
  - "Dealing range boundary verification"
  - "OTE zone computation verification"
  - "Partial Mirror Test: can check if CLAIMs encode ICT concepts correctly"

key_risks:
  - "MSS displacement factors require threshold calibration (Joist review)"
  - "ORDER_FLOW depends on SWING_POINT quality (cascading error)"
  - "DEALING_RANGE boundary selection involves priority ordering (v0.4 hierarchy)"

estimated_additional: "~5,000-20,000 Phase 2 CLAIMs"
```

### 6.3 Phase 3 — Composite SIGNALs (Sketched)

```yaml
scope: "SIGNAL and ENGINE_EVENT production"
types: |
  ENGINE_EVENT (composite: sweep + MSS + FVG/VI — per v0.4 engine_event_detection)
  FIVE_FACTOR_CHECK (binary: all 5 factors evaluated)
  These are SIGNAL beads, not CLAIMs — different bead type.
depends_on: "Phase 2 complete"

what_this_enables:
  - "Full Mirror Test (OBS-007 re-execution)"
  - "5-factor checklist validation"
  - "Kill zone compliance checking"
  - "Engine event detection verification"

note: "Phase 3 design is out of scope for this spec. Sketched for context only."
```

---

## 7. OPEN QUESTIONS

### For Joist Review (Advisor Input)

```yaml
Q1_DISPLACEMENT_THRESHOLDS:
  question: |
    MSS displacement is "qualitative — no pip thresholds" per Olya.
    The spec proposes 5 binary checks with operational thresholds
    (e.g., "close > 2x median candle body"). Is this a faithful
    operationalization or a departure from the method?
  who_decides: "Olya (CSO) + OWL audit"
  impact: "Phase 2 MSS detection accuracy"

Q2_SWING_LOOKBACK_N:
  question: |
    Swing detection uses lookback parameter N. What value(s)?
    N=5 is standard but produces many swings.
    N=10 is more selective.
    Should we produce CLAIMs at multiple N values?
  who_decides: "CTO + Olya"
  impact: "Phase 1 SWING_POINT count and quality"

Q3_MULTI_TIMEFRAME_APPROACH:
  question: |
    FVG/VI detection on 5m/15m requires candle aggregation from 1m FACTs.
    Should we: (A) Aggregate 1m FACTs into 5m/15m "virtual candles" on the fly,
    or (B) Ingest pre-aggregated 5m/15m FACTs from a separate data source?
    Option A maintains single-source purity. Option B requires new FACT ingestion.
  who_decides: "CTO"
  impact: "Data pipeline complexity"

Q4_REASONING_TRACE_FORMAT:
  question: |
    The spec proposes JSON-in-string for reasoning_trace to carry structured
    data within the frozen schema. Is this acceptable, or should we explore
    alternatives (e.g., using the tags field for structured metadata)?
  who_decides: "OWL + CTO"
  impact: "Query ergonomics and data access patterns"

Q5_STRATEGY_ARCHITECTURE:
  question: |
    Olya's PROPOSAL_STRATEGY_ARCHITECTURE.md proposes a 5-drawer framework
    with "strategy cartridges." The Drawer enum in the schema (HTF_BIAS,
    MARKET_STRUCTURE, PREMIUM_DISCOUNT, ENTRY_MODEL, CONFIRMATION) already
    maps to this. Should the CLAIM pipeline support multiple strategy
    cartridges from the start, or focus on ICT Directional only?
  who_decides: "G + Olya"
  impact: "Phase 1 scope — adding Asia Range Scalp strategy increases scope"
```

### For G/Olya Decision

```yaml
Q6_CLAIM_PRODUCTION_MODEL:
  question: |
    The brief asks "don't assume specific model for CLAIM production."
    Phase 1 CLAIMs are DETERMINISTIC (no model needed — pure algorithm).
    Phase 2 MSS displacement evaluation may benefit from model judgment.
    Does G/Olya want Phase 2 to use LLM judgment, or should displacement
    be operationalized as binary algorithmic checks?
  who_decides: "G + Olya"
  impact: "Mirror risk level for Phase 2"

Q7_HUMAN_VALIDATION_CADENCE:
  question: |
    INV-HUMAN-FRAMES requires human validation. What is the cadence?
    Options:
    A) Olya validates a random sample of Phase 1 CLAIMs (e.g., 100 FVGs, 100 swings)
    B) Olya validates all CLAIMs on 5 golden windows
    C) Olya validates only Phase 2+ CLAIMs (Phase 1 is deterministic, less risk)
  who_decides: "Olya"
  impact: "CSO time commitment and CLAIM quality assurance"
```

---

## Appendix A: CLAIM Content Examples

### Example: SWING_POINT CLAIM

```json
{
  "bead_type": "CLAIM",
  "temporal_class": "OBSERVATION",
  "world_time_valid_from": "2024-01-15T14:25:00+00:00",
  "world_time_valid_to": "2024-01-15T14:35:00+00:00",
  "content": {
    "conclusion": "SWING_POINT: Higher High at 1.08542 on EURUSD 1m",
    "reasoning_trace": "{\"claim_subtype\":\"SWING_POINT\",\"swing_type\":\"HH\",\"price\":1.08542,\"bar_time\":\"2024-01-15T14:30:00+00:00\",\"lookback_bars\":5,\"direction\":\"BULLISH\",\"prior_swing_ref\":\"019ca31e-xxxx\",\"instrument\":\"EURUSD\",\"source_timeframe\":\"1m\"}",
    "premises_ref": ["019ca31e-a001", "019ca31e-a002", "019ca31e-a003", "019ca31e-a004", "019ca31e-a005", "019ca31e-a006", "019ca31e-a007", "019ca31e-a008", "019ca31e-a009", "019ca31e-a010", "019ca31e-a011"],
    "confidence_basis": "DETERMINISTIC — swing detection N=5 lookback, both sides confirmed",
    "drawer": "MARKET_STRUCTURE",
    "icm_terms": ["swing_point", "higher_high", "market_structure", "order_flow"]
  },
  "source_ref": {
    "source_type": "AGENT",
    "source_id": "claim-producer-v1",
    "source_version": "0.1.0"
  },
  "lineage": ["019ca31e-a001", "019ca31e-a002", "..."],
  "tags": ["instrument:EURUSD", "claim_type:SWING_POINT", "timeframe:1m"]
}
```

### Example: FVG CLAIM

```json
{
  "bead_type": "CLAIM",
  "temporal_class": "OBSERVATION",
  "world_time_valid_from": "2024-01-15T14:28:00+00:00",
  "world_time_valid_to": "2024-01-15T14:31:00+00:00",
  "content": {
    "conclusion": "FVG: Bullish Fair Value Gap 1.08510-1.08525 (1.5 pips) on EURUSD 1m",
    "reasoning_trace": "{\"claim_subtype\":\"FVG\",\"fvg_direction\":\"BULLISH\",\"gap_high\":1.08525,\"gap_low\":1.08510,\"gap_size_pips\":1.5,\"candle_a_time\":\"2024-01-15T14:28:00+00:00\",\"candle_b_time\":\"2024-01-15T14:29:00+00:00\",\"candle_c_time\":\"2024-01-15T14:30:00+00:00\",\"candle_a_id\":\"019ca31e-a003\",\"candle_b_id\":\"019ca31e-a004\",\"candle_c_id\":\"019ca31e-a005\",\"instrument\":\"EURUSD\",\"pip_unit\":0.0001,\"source_timeframe\":\"1m\"}",
    "premises_ref": ["019ca31e-a003", "019ca31e-a004", "019ca31e-a005"],
    "confidence_basis": "DETERMINISTIC — wick-to-wick gap: candle_A.high(1.08510) < candle_C.low(1.08525)",
    "drawer": "MARKET_STRUCTURE",
    "icm_terms": ["fair_value_gap", "fvg", "imbalance", "bullish"]
  },
  "source_ref": {
    "source_type": "AGENT",
    "source_id": "claim-producer-v1",
    "source_version": "0.1.0"
  },
  "lineage": ["019ca31e-a003", "019ca31e-a004", "019ca31e-a005"],
  "tags": ["instrument:EURUSD", "claim_type:FVG", "timeframe:1m"]
}
```

---

## Appendix B: Methodology Mapping

```yaml
# How SYNTHETIC_OLYA_METHOD v0.4 sections map to CLAIM types

v0.4_section → claim_type:
  framework.order_flow → ORDER_FLOW (Phase 2)
  framework.three_questions → ORDER_FLOW + DEALING_RANGE (Phase 2)
  pre_session.weekly_context → SWING_POINT at Weekly TF (Phase 2+)
  pre_session.daily_bias_determination → ORDER_FLOW (Phase 2)
  pre_session.dealing_range_identification → DEALING_RANGE (Phase 2)
  pre_session.draw_on_liquidity → Phase 3 (SIGNAL scope)
  pre_session.asia_range_filter → ASIA_RANGE (Phase 1)
  session_monitoring.midnight_open → SESSION_BOUNDARY:MIDNIGHT_OPEN (Phase 1)
  session_monitoring.asia_liquidity_build → ASIA_RANGE (Phase 1)
  lokz_manipulation.liquidity_sweep → Phase 3 (ENGINE_EVENT scope)
  lokz_manipulation.engine_event_detection → Phase 3 (SIGNAL scope)
  entry_execution.five_factor_checklist → Phase 3 (SIGNAL scope)
  entry_execution.ote_confirmation → OTE_ZONE (Phase 2)
```

---

*Spec produced by COO (Claude Opus 4.6) on 2026-03-03. Zero code changes. Zero schema mutations. Design only.*
