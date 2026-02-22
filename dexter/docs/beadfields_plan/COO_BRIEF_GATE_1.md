# COO BUILD BRIEF — BEAD FIELD GATE 1

```yaml
from: CTO (Dexter)
to: COO (Claude Code CLI, Mac Mini)
date: 2026-02-20
classification: BUILD_BRIEF — execute in order
purpose: Stand up Bead Field substrate, curate Genesis Snapshot, pass Gate 1
spec: BEAD_FIELD_SPEC_v0.3 (CANONICAL — do not deviate)
repo: Same repo as Dexter extraction pipeline
codebase: NEW directory bead_field/ (do not modify src/)
```

---

## 0. BEFORE YOU WRITE CODE

```yaml
READ_THESE_FIRST:
  1: docs/BEAD_FIELD_SPEC_v0_3.md (the constitution — every schema, every invariant)
  2: CLAUDE.md (build invariants, commit discipline)
  3: This brief (execution sequence)

AWARE_OF_BUT_DO_NOT_BUILD:
  DREAM_CYCLE_DESIGN_INTENT_v0.1.md: |
    Documents how the Dream Cycle (Gate 5+) will analyze the Bead Field.
    Key decision: Energy/coherence is COMPUTED over beads, never STORED on them.
    No energy fields, no scalar scores, no coherence attributes on bead schema.
    INV-NO-GRADES applies. Build the hard substrate. Mining comes later.

UNDERSTAND:
  - bead_field/ is a NEW codebase alongside existing src/ (extraction pipeline)
  - src/ is COMPLETED, preserved, not active. Do not modify.
  - bundles/ contains the 981 CLAIMs from extraction phase
  - Gate 1 runs on Mac Mini now, deploys to M3 Ultra later
  - SQLite is the bi-temporal proxy (swappable to XTDB on M3)
  - Python 3.11+, Pydantic v2, pytest
```

---

## 1. DIRECTORY STRUCTURE

Create this layout in repo root:

```
bead_field/
├── __init__.py
├── schema/
│   ├── __init__.py
│   ├── core.py              # BeadCore base model (Section 3.1)
│   ├── fact.py               # FACT content schema
│   ├── claim.py              # CLAIM content schema
│   ├── signal.py             # SIGNAL content schema
│   ├── proposal.py           # PROPOSAL content schema
│   ├── proposal_rejected.py  # PROPOSAL_REJECTED content schema
│   ├── skill.py              # SKILL content schema
│   ├── model_version.py      # MODEL_VERSION content schema
│   ├── policy.py             # POLICY content schema
│   └── enums.py              # All enums (shared)
├── store/
│   ├── __init__.py
│   ├── bitemporal.py         # SQLite bi-temporal store
│   ├── migrations.py         # Schema migration tooling (from day 1)
│   └── queries.py            # Bi-temporal query helpers (WT/KT predicates)
├── integrity/
│   ├── __init__.py
│   ├── hashing.py            # SHA-256 hash computation (canonical JSON)
│   ├── chain.py              # Per-stream hash chain
│   ├── merkle.py             # Merkle tree + batch anchoring
│   └── signing.py            # Dual PQC (Dilithium) + ECDSA signing
├── clock/
│   ├── __init__.py
│   └── hlc.py                # Hybrid Logical Clock
├── ingestion/
│   ├── __init__.py
│   └── pipeline.py           # Data → validated bead → store
├── genesis/
│   ├── __init__.py
│   ├── curator.py            # Map 981 CLAIMs against v0.3 taxonomy
│   ├── snapshot.py           # Genesis Merkle tree + signing ceremony
│   └── delta.py              # METHODOLOGY_DELTA bead builder
└── tests/
    ├── __init__.py
    ├── conftest.py            # Shared fixtures (temp DB, test beads, test keys)
    ├── test_schema.py         # All 8 bead types validate correctly
    ├── test_enums.py          # Enum completeness
    ├── test_store.py          # Bi-temporal CRUD + range queries
    ├── test_hashing.py        # Deterministic hash, canonical JSON
    ├── test_chain.py          # Hash chain walk + tamper detection
    ├── test_merkle.py         # Merkle tree build, proof, verify
    ├── test_signing.py        # PQC + ECDSA sign/verify round-trip
    ├── test_hlc.py            # HLC monotonicity, tick, merge
    ├── test_ingestion.py      # Pipeline: raw data → stored bead
    ├── test_genesis.py        # Curation, snapshot, delta bead
    ├── test_queries.py        # Bi-temporal query correctness
    └── test_invariants.py     # Invariant enforcement (immutability, unsigned rejection, etc.)
```

---

## 2. EXECUTION SEQUENCE

**Do these in order. Each phase completes before the next starts.**

### Phase A: Schema (Day 1 morning)

```yaml
task: Implement Pydantic v2 models for all 8 bead types
source: BEAD_FIELD_SPEC_v0.3 Section 3 (verbatim — do not invent fields)
output: bead_field/schema/*.py + bead_field/tests/test_schema.py

enums_to_define:
  BeadType: [FACT, CLAIM, SIGNAL, PROPOSAL, PROPOSAL_REJECTED, SKILL, MODEL_VERSION, POLICY]
  TemporalClass: [OBSERVATION, PATTERN, DERIVED]
  BeadStatus: [ACTIVE, SUPERSEDED, RETRACTED]
  SourceType: [MARKET_DATA, AGENT, HUMAN, EXTRACTION, SIMULATION, OPEN_SOURCE]
  Direction: [LONG, SHORT, NEUTRAL]
  ProposalAction: [ENTER_LONG, ENTER_SHORT, EXIT, ADJUST, HEDGE]
  RejectionSource: [AUDITOR, RISK_ENGINE, HUMAN, DREAM_CYCLE]
  RejectionCategory: [PROVENANCE_FAILURE, LOGICAL_CONTRADICTION, REGIME_MISMATCH, RISK_BREACH, STALE_DATA, FALSIFICATION_FAILED, HUMAN_OVERRIDE, DREAM_CYCLE_FAILURE]
  SkillType: [AVOIDANCE, RECOGNITION, TIMING, SIZING, REGIME]
  SkillValidation: [CANDIDATE, VALIDATED, PROMOTED, DEPRECATED]
  DeploymentStatus: [CANDIDATE, STAGING, PRODUCTION, RETIRED]
  PolicyType: [RISK, EXECUTION, REGIME, OPERATIONAL]
  Drawer: [HTF_BIAS, MARKET_STRUCTURE, PREMIUM_DISCOUNT, ENTRY_MODEL, CONFIRMATION]
  PositionSizeUnit: [LOTS, CONTRACTS, USD, PCT_EQUITY]
  DataQuality: [NOMINAL, DEGRADED, PARTIAL, ERROR]  # ChadBoar learning

key_schema_rules:
  - BeadCore is the base model. All 8 types extend it with type-specific content.
  - bead_id is UUID v7 (use uuid7 library or uuid6 — time-ordered)
  - world_time fields are Optional[datetime] (null for PATTERN class)
  - knowledge_time_recorded_at is required datetime (never null)
  - lineage is list[str] (list of bead_id references, empty for root beads)
  - hash_self computed AFTER all other fields set (exclude hash_self and merkle_batch_id from hash input)
  - attestation is a nested model (AttestationEnvelope)
  - PROPOSAL_REJECTED MUST include full proposal fields + rejection context (INV-SHADOW-RICH)
  - RISK_BREACH rejection MUST have rejection_policy_ref (INV-REJECTION-POLICY-REF)
  - fact_content.quality_score is Optional[float] with ge=0.0, le=1.0 — this is DATA quality, not analytical

validation_rules:
  - If temporal_class == OBSERVATION: world_time_valid_from and world_time_valid_to MUST be set
  - If temporal_class == PATTERN: world_time_valid_from and world_time_valid_to MUST be None
  - If temporal_class == DERIVED: world_time inherited (validation deferred to ingestion)
  - If bead_type == PROPOSAL_REJECTED and rejection_category == RISK_BREACH: rejection_policy_ref MUST NOT be None

tests:
  - Each bead type constructs successfully with valid data
  - Each bead type rejects invalid data (missing required fields, wrong types)
  - Temporal class validation enforced
  - RISK_BREACH without policy ref rejected
  - PROPOSAL_REJECTED without full proposal fields rejected
  - Round-trip JSON serialization (model → JSON → model)
  - Target: 40+ schema tests
```

### Phase B: Hashing + Hash Chain (Day 1 afternoon)

```yaml
task: Deterministic SHA-256 hashing and per-stream chain
source: BEAD_FIELD_SPEC_v0.3 Section 5.1

hashing_rules:
  - Canonical JSON serialization (sorted keys, no whitespace, UTF-8)
  - Input: ALL fields EXCEPT hash_self and merkle_batch_id
  - Output: hex-encoded SHA-256
  - CRITICAL: Same inputs MUST produce same hash. Test this explicitly.
  - Use json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

chain_rules:
  - Each bead in a stream points to previous bead via hash_prev
  - First bead in stream: hash_prev = None
  - Verification: walk chain backward, verify hash_prev matches prior hash_self
  - Tamper detection: if any hash doesn't match, chain is broken

tests:
  - Same bead data → same hash (determinism)
  - Different data → different hash
  - Chain of 10 beads → walk backward verifies
  - Tamper one bead in middle → detection fires
  - hash_self and merkle_batch_id excluded from hash input
  - Target: 15+ tests
```

### Phase C: HLC (Day 1 afternoon)

```yaml
task: Hybrid Logical Clock for knowledge_time
source: BEAD_FIELD_SPEC_v0.3 Section 3.1 + 4.1

hlc_rules:
  - Single-node simplified (full distributed HLC when M3 arrives)
  - Monotonically increasing: each tick > previous tick
  - Merge operation: max(local, remote) + 1 (for future multi-node)
  - Resolution: microsecond precision
  - Format: ISO 8601 with microsecond precision

implementation:
  - HLC class with tick() and merge(remote_time) methods
  - tick() returns datetime guaranteed > previous
  - If wall clock has advanced: use wall clock + counter reset
  - If wall clock hasn't advanced: increment counter
  - Thread-safe (Lock or atomic operations)

tests:
  - Monotonicity: 1000 rapid ticks all increasing
  - Merge: merging a future time advances the clock
  - Merge: merging a past time doesn't regress
  - Target: 8+ tests
```

### Phase D: Signing (Day 2 morning)

```yaml
task: Dual PQC (Dilithium) + ECDSA signing
source: BEAD_FIELD_SPEC_v0.3 Section 5.3

dependencies:
  ecdsa: pip install ecdsa (secp256r1 / NIST P-256)
  pqc: pip install liboqs-python (or oqs — for CRYSTALS-Dilithium)
  fallback: If liboqs unavailable on Mini, use pqcrypto or dilithium-py
  CRITICAL: Integration tests must cover ACTUAL library API (ChadBoar learning #1)

implementation:
  - KeyManager class: generates and stores ECDSA + Dilithium key pairs
  - sign(hash_self) → returns (ecdsa_sig, pqc_sig)
  - verify(hash_self, ecdsa_sig, pqc_sig) → bool
  - Either signature alone sufficient for validation (per spec)
  - Key storage: file-based for Mini, HSM-aware interface for future

tests:
  - Sign + verify round-trip (both algorithms)
  - Tampered data → verification fails
  - Either signature alone verifies
  - Key generation determinism with seed
  - Target: 10+ tests

NOTE_ON_PQC_AVAILABILITY:
  If liboqs-python won't install cleanly on Mac Mini ARM:
  1. Try: pip install oqs
  2. Try: pip install pqcrypto
  3. Fallback: Stub PQC with Ed25519 + flag PQC_STUB=True
  4. Report blocker to CTO — do NOT skip PQC entirely
```

### Phase E: SQLite Bi-Temporal Store (Day 2)

```yaml
task: Bi-temporal storage with WT/KT range queries
source: BEAD_FIELD_SPEC_v0.3 Section 4 + Gate 1 exit criteria

schema_migration_from_day_1:
  - Version-tracked migrations (not CREATE IF NOT EXISTS — ChadBoar learning #2)
  - Migration table tracks applied versions
  - Each migration is a numbered .sql or Python function
  - Rollback support (down migration)

table_design:
  beads:
    bead_id: TEXT PRIMARY KEY
    bead_type: TEXT NOT NULL
    content: TEXT NOT NULL (JSON)
    world_time_valid_from: TEXT (ISO 8601, nullable)
    world_time_valid_to: TEXT (ISO 8601, nullable)
    knowledge_time_recorded_at: TEXT NOT NULL (ISO 8601)
    temporal_class: TEXT NOT NULL
    source_ref: TEXT NOT NULL (JSON)
    lineage: TEXT NOT NULL (JSON array)
    hash_self: TEXT NOT NULL
    hash_prev: TEXT (nullable)
    merkle_batch_id: TEXT (nullable)
    attestation: TEXT NOT NULL (JSON)
    status: TEXT NOT NULL DEFAULT 'ACTIVE'
    superseded_by: TEXT (nullable)
    retraction_reason: TEXT (nullable)
    tags: TEXT NOT NULL (JSON array)

  merkle_batches:
    batch_id: TEXT PRIMARY KEY
    merkle_root: TEXT NOT NULL
    bead_count: INTEGER NOT NULL
    timestamp: TEXT NOT NULL
    trigger_bead_id: TEXT (nullable)

  migrations:
    version: INTEGER PRIMARY KEY
    applied_at: TEXT NOT NULL
    description: TEXT

indexes:
  - idx_beads_type ON beads(bead_type)
  - idx_beads_wt_from ON beads(world_time_valid_from)
  - idx_beads_wt_to ON beads(world_time_valid_to)
  - idx_beads_kt ON beads(knowledge_time_recorded_at)
  - idx_beads_temporal_class ON beads(temporal_class)
  - idx_beads_status ON beads(status)
  - idx_beads_merkle ON beads(merkle_batch_id)

store_invariants:
  - INSERT only (no UPDATE on bead content — INV-BEAD-IMMUTABLE)
  - UPDATE allowed ONLY on: status, superseded_by, retraction_reason, merkle_batch_id
  - Reject any unsigned bead at ingestion (attestation must be populated)
  - Reject beads with duplicate bead_id

query_helpers:
  - query_by_wt_range(from, to) → beads with overlapping world_time
  - query_by_kt_asof(asof_time) → beads known at a specific knowledge time
  - query_by_type_and_wt(bead_type, wt_from, wt_to) → filtered range
  - query_by_lineage(bead_id) → all beads that reference this bead in lineage
  - refinery_latency(bead_id) → KT - WT_end delta

tests:
  - Insert + retrieve round-trip
  - Bi-temporal query: "what did we know on date X about period Y" (Gate 1 exit criterion)
  - Immutability: attempted content UPDATE raises error
  - Status update: ACTIVE → SUPERSEDED works
  - Duplicate bead_id rejected
  - Unsigned bead rejected
  - Range queries return correct results
  - Empty DB queries return empty results (not errors)
  - Migration applies cleanly on fresh DB
  - Target: 30+ tests
```

### Phase F: Merkle Anchoring (Day 2 afternoon)

```yaml
task: Merkle tree + batch anchoring with hybrid trigger
source: BEAD_FIELD_SPEC_v0.3 Section 5.2

implementation:
  - MerkleTree class: build from list of hash_self values
  - Proof generation: given a leaf, produce proof path to root
  - Proof verification: given leaf + proof + root, verify membership
  - Batch anchoring: collect beads since last anchor, build tree, store root
  - Backfill: set merkle_batch_id on all beads in the batch

trigger_logic:
  - Primary: SIGNAL or PROPOSAL bead committed → anchor
  - Fallback 1: 500 beads since last anchor → anchor (configurable)
  - Fallback 2: 1 hour since last anchor → anchor (configurable)
  - First trigger wins

tests:
  - Build tree from known leaves → known root
  - Proof for any leaf verifies
  - Tampered leaf → proof fails
  - Batch anchor stores correct root + bead count
  - Backfill sets merkle_batch_id on all batch beads
  - Trigger: SIGNAL bead → anchor fires
  - Trigger: 500 beads → fallback fires
  - Trigger: 1 hour → time fallback fires
  - Empty batch → no anchor (edge case)
  - Target: 15+ tests
```

### Phase G: Ingestion Pipeline (Day 3 morning)

```yaml
task: End-to-end pipeline: raw data → validated, signed, stored bead
source: BEAD_FIELD_SPEC_v0.3 Sections 2.2, 3, 5

pipeline_steps:
  1: Validate input data against type-specific schema
  2: Assign bead_id (UUID v7)
  3: Set knowledge_time via HLC tick
  4: Compute hash_self
  5: Link hash_prev (get latest bead in stream)
  6: Sign (dual PQC + ECDSA)
  7: Validate attestation populated
  8: Insert into store
  9: Check Merkle trigger conditions
  10: If triggered, build Merkle batch

rejection_at_ingestion:
  - Missing required fields → reject
  - Temporal class mismatch (OBSERVATION without WT) → reject
  - Unsigned bead → reject
  - Duplicate bead_id → reject
  - RISK_BREACH without policy ref → reject

tests:
  - Happy path: FACT bead ingested, stored, retrievable
  - Happy path: CLAIM bead with lineage references
  - Rejection: bad schema → ingestion fails gracefully
  - Rejection: unsigned → ingestion fails
  - Pipeline respects immutability (can't re-ingest same bead_id)
  - Merkle trigger fires on SIGNAL ingestion
  - Target: 15+ tests
```

### Phase H: Genesis Curation + Snapshot (Day 3)

```yaml
task: Curate the 981 CLAIMs, build Genesis Merkle tree, sign
source: BEAD_FIELD_SPEC_v0.3 Section 6 + CTO handoff (curation approach)

CRITICAL_NOTE: |
  This is the most consequential task. The Genesis Snapshot is the
  cryptographic origin of the entire refinery. Get it right.

step_1_curation:
  input: bundles/ directory (981 CLAIMs in JSONL format)
  action: Load all 981 CLAIMs
  action: Load SYNTHETIC_OLYA_METHOD_v0.3.yaml (the taxonomy)
  action: Map each CLAIM against the v0.3 taxonomy concepts
  output: Curation report with three categories:
    GENESIS_INCLUDE: CLAIMs that map to validated methodology concepts
    GENESIS_EXCLUDE_CONTRADICTION: CLAIMs contradicted by v0.3 corrections
    GENESIS_EXCLUDE_ARTIFACT: CLAIMs that are test/pipeline artifacts, not methodology
  output: Save report as bead_field/genesis/CURATION_REPORT.md
  STOP: Report to CTO. G reviews before proceeding.

step_2_delta_bead:
  after: G approves curation report
  action: Build METHODOLOGY_DELTA bead recording v0.1→v0.3 corrections
  content: Each of Olya's 13 corrections as structured entries
  bead_type: POLICY (methodology change record)
  temporal_class: PATTERN (timeless — methodology, not market observation)

step_3_snapshot:
  after: G approves curation + delta bead
  action: Convert curated CLAIMs to Bead Field schema (CLAIM type, PATTERN class)
  action: Include METHODOLOGY_DELTA bead in Genesis set
  action: Hash all Genesis beads
  action: Build Merkle tree over all Genesis hash_self values
  action: Create GENESIS_ANCHOR POLICY bead:
    policy_name: "GENESIS_ANCHOR"
    content: { merkle_root: <root>, bead_count: <N>, signed_by: "G" }
  action: Set merkle_batch_id on all Genesis beads
  STOP: Report to CTO. G signs with sovereign key.

step_4_verification:
  action: Verify every Genesis bead traces to signed root
  action: Verify Merkle proof for random sample of Genesis beads
  action: Verify hash chain integrity
  output: GENESIS_VERIFICATION_REPORT.md

tests:
  - Curation loads all 981 CLAIMs from bundles/
  - Curation maps against taxonomy concepts
  - Excluded CLAIMs include known removals (CBDR, SMT, time stop)
  - Genesis beads are PATTERN temporal class
  - Genesis beads have empty lineage (root beads)
  - Merkle tree builds correctly
  - Proof verification works for any Genesis bead
  - GENESIS_ANCHOR bead validates against POLICY schema
  - Target: 15+ tests
```

---

## 3. DEPENDENCIES

```bash
# Core
pip install pydantic>=2.0 --break-system-packages
pip install uuid6 --break-system-packages           # UUID v7 support
pip install pytest pytest-cov --break-system-packages

# Signing
pip install ecdsa --break-system-packages             # ECDSA secp256r1
pip install liboqs-python --break-system-packages     # PQC Dilithium (try first)
# If liboqs fails on ARM: pip install pqcrypto or pip install dilithium-py
# If ALL PQC fails: stub with Ed25519, flag PQC_STUB=True, report blocker

# Data
pip install pyyaml --break-system-packages            # For loading v0.3 taxonomy

# Already available
# sqlite3 (stdlib)
# hashlib (stdlib)
# json (stdlib)
```

---

## 4. INVARIANTS TO ENFORCE IN CODE

```yaml
# These are non-negotiable. Tests MUST verify each one.

INV-BEAD-IMMUTABLE: No UPDATE on bead content after INSERT
INV-BEAD-SIGNED: Every stored bead has both ecdsa_sig and pqc_sig populated
INV-BEAD-TEMPORAL: OBSERVATION has WT, PATTERN has null WT, KT always set
INV-SHADOW-RICH: PROPOSAL_REJECTED has full proposal fields (not a stub)
INV-REJECTION-POLICY-REF: RISK_BREACH requires policy ref
INV-COMMITMENT-THRESHOLD: Only committed beads enter store (no drafts)
INV-ANCESTRAL-PRESERVED: Genesis CLAIMs are PATTERN class, root lineage
INV-TEMPORAL-BOUNDING: DERIVED WT = intersection of OBSERVATION inputs
INV-ANCHOR-AT-DECISIONS: Merkle triggers on SIGNAL/PROPOSAL or fallback caps
INV-NO-GRADES: No scores/grades anywhere except fact_content.quality_score (data quality only)
```

---

## 5. COMMIT DISCIPLINE

```yaml
commit_format: "[Gate1/Area] Brief description"
examples:
  - "[Gate1/Schema] Implement 8 bead type Pydantic models"
  - "[Gate1/Store] SQLite bi-temporal proxy with migrations"
  - "[Gate1/Integrity] Hash chain + Merkle anchoring"
  - "[Gate1/Signing] Dual PQC + ECDSA signing"
  - "[Gate1/Genesis] Curation report for 981 CLAIMs"
  - "[Gate1/Tests] Full invariant enforcement suite"

rules:
  - Tests pass before every commit
  - Zero TODO/FIXME/HACK in committed code
  - Update test count in commit message if significant
  - Report blockers immediately (don't guess at solutions)
```

---

## 6. GATE 1 EXIT CRITERIA (from spec)

```yaml
PASS_WHEN:
  1: "Show all FACT beads about EURUSD that we knew on Jan 1 about Q4 2025" → correct results
  2: Merkle proof for any bead reconstructable and verifiable
  3: Ancestral CLAIMs queryable as PATTERN-class beads with intact lineage
  4: All 8 bead types validate and store correctly
  5: Hash chain tamper detection works
  6: Dual signing works (PQC + ECDSA)
  7: Genesis Snapshot signed and verifiable
  8: 200+ tests passing
```

---

## 7. CHADBOAR LEARNINGS (Apply These)

```yaml
1: Integration tests MUST cover actual signing library API (not mocked interfaces)
2: Schema migration tooling from day 1 (versioned migrations, not CREATE IF NOT EXISTS)
3: FACT beads need DataQuality enum (NOMINAL/DEGRADED/PARTIAL/ERROR)
4: Refinery Latency (WT-KT delta) doubles as hallucination detector
5: Deployment config audited separately from code (INV-DEPLOYMENT-AUDIT)
```

---

## 8. REPORTING

```yaml
after_each_phase:
  report: "Phase X complete. Y tests passing. Blockers: [none | description]."
  
after_curation (Phase H step 1):
  STOP: Full curation report to CTO. Do NOT proceed until G approves.

after_genesis_build (Phase H step 3):
  STOP: Genesis ready for signing. Report to CTO. G signs.

final_report:
  format: |
    GATE 1 STATUS: PASS/FAIL
    Tests: N/N passing
    Bead types implemented: 8/8
    Store: operational (SQLite bi-temporal)
    Integrity: hash chain + Merkle + dual signing
    Genesis: N curated CLAIMs signed as Bead Zero
    Blockers: [none | list]
```

---

```yaml
SOVEREIGN_DIRECTIVE:
  The spec is canon. Build the substrate. Report blockers, don't guess.
  signed: CTO (Dexter)
  date: 2026-02-20
```

*Every bead is a commitment. Every commitment is signed. Every signature is sovereign.* 🔬🧪
