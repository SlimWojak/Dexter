# BEAD FIELD SPRINT — Gate 1 Substrate

```yaml
document: BEAD_FIELD_SPRINT
version: 1.0
date: 2026-02-22
status: ACTIVE — governing Gate 1 substrate build
purpose: Phase tracker, advisory synthesis, risk log, running score
owner: G (Sovereign Operator)
executor: COO (Cursor Agent, Mac Mini)
spec: BEAD_FIELD_SPEC_v0.3 (CANONICAL — do not deviate)
brief: COO_BRIEF_GATE_1.md (execution sequence)
```

---

## 0. SPRINT IDENTITY

```yaml
GOAL: |
  Stand up the immutable bi-temporal substrate.
  Produce the Genesis Snapshot (981 CLAIMs → Bead Zero).
  Pass Gate 1 exit criteria (200+ tests, 8 bead types, signed Genesis).

NON_GOALS:
  - No Dream Cycle code (Gate 5+)
  - No energy computation, no scalar scoring (DEC-ENERGY-NOT-STORED)
  - No auto-promotion logic (INV-HUMAN-FRAMES)
  - No schema experimentation (spec is canon)
  - No DGX code (standing by for Gate 5+)
  - No throughput optimization (prove correctness first)

HARDWARE:
  build: Mac Mini (COO runs here)
  deploy: M3 Ultra (when arrives — tested code deploys in hours)
  standing_by: DGX Spark (arrived 2026-02-21, Gate 5+ compute role)

CODEBASE:
  active: bead_field/ (NEW — Gate 1 build surface)
  preserved: src/ (extraction pipeline, COMPLETE, do not modify)
  genesis_source: bundles/ (981 CLAIMs in JSONL)
  spec: docs/beadfields_plan/BEAD_FIELD_SPEC_v0.3.md
```

---

## 1. ADVISORY SYNTHESIS

Three advisors pressure-tested the COO Brief and Dream Cycle Design Intent (2026-02-22).

### Adopted

| Source | Recommendation | Decision ID | Impact |
|--------|---------------|-------------|--------|
| Owl | Phase I: forensic integrity stress test — manual tamper detection proves integrity catches corruption | — | Added as Phase I |
| Owl | PQC degraded sovereignty alert — ECDSA-only is valid but system flags degraded state | — | Phase D signing logic |
| Owl | Test migration tooling before Genesis load — verify plumbing while tank is empty | — | Phase E pre-check |
| Architect | 30-day schema freeze after Gate 1 PASS | DEC-SUBSTRATE-FREEZE | Post-Gate-1 rule |
| Architect | Dream Cycle may NOT write to bead store directly | INV-DREAM-ISOLATION | Future invariant, documented now |
| Architect | Basic field health observability before Dream Cycle | — | Phase G counters |
| Boar | Reinforce DEC-ENERGY-NOT-STORED in scope fence | — | Section 0 non-goals |

### Documented (Intent Only, Gate 5+ Scope)

| Source | Recommendation | Decision ID |
|--------|---------------|-------------|
| Architect | Simulation determinism contract (seed, snapshot hash, model, params logged) | DEC-SIMULATION-REPRODUCIBILITY |

### Parked

| Source | Recommendation | Rationale |
|--------|---------------|-----------|
| Boar | DGX prototype ephemeral energy script | Scope creep. DGX irrelevant to Gate 1 substrate. |
| Boar | ChadBoar 5000/day volume stress sim | Gate 2 scope. Gate 1 proves correctness, not throughput. |

---

## 2. NEW DECISIONS

```yaml
DEC-SUBSTRATE-FREEZE:
  ruling: |
    After Gate 1 PASS:
    - No schema field additions for 30 days
    - No new bead types
    - No invariant changes
    - Only bug fixes allowed
  source: Architect (Advisory Panel, 2026-02-22)
  rationale: First 30 days expose edge cases. Reactive modification corrupts field stability.
  approved_by: G

INV-DREAM-ISOLATION:
  ruling: |
    Dream Cycle processes:
    - May NOT write to bead store directly
    - May only emit SKILL_CANDIDATE via ingestion pipeline
    - Must pass full schema validation + signing like any other bead
  source: Architect (Advisory Panel, 2026-02-22)
  rationale: Scientists go through the same constitutional door as everyone else.
  enforcement: Gate 5+ (documented now, enforced when Dream Cycle builds)

DEC-SIMULATION-REPRODUCIBILITY:
  ruling: |
    Every Dream Cycle session logs:
    - Random seed
    - Input bead snapshot hash
    - model_version bead reference
    - Simulation parameters
  source: Architect (Advisory Panel, 2026-02-22)
  scope: Gate 5+ ONLY. Documented intent, not Gate 1 build scope.
```

---

## 3. PHASE CHECKLIST

### Phase 0: Dependency Validation

```yaml
description: Smoke-test all dependencies on ARM Mac Mini before writing code
status: COMPLETE
tasks:
  - Install pydantic>=2.0, uuid6, pytest, pytest-cov, pyyaml — DONE
  - Install ecdsa (secp256r1) — DONE (sign/verify round-trip confirmed)
  - Install PQC — DONE (pqcrypto 0.4.0, ML-DSA-65 aka Dilithium3)
  - Verify each import works in Python 3.14.2 — DONE (all pass)
  - Record PQC outcome in risk log (R1) — DONE (resolved)
results:
  python: 3.14.2 (Homebrew, ARM64)
  pydantic: 2.12.5
  uuid6: 2025.0.1
  ecdsa: 0.19.1 (secp256r1 / NIST P-256)
  pqc: pqcrypto 0.4.0 (ML-DSA-65 = Dilithium3, native ARM wheel)
  pqc_stub: false (real Dilithium, no stub needed)
  sqlite3: 3.51.2 (stdlib)
  pqc_note: |
    liboqs-python FAILED (Homebrew builds static only, Python wrapper needs .dylib).
    pqcrypto worked first try with pre-built ARM64 wheel.
    verify() returns bool (not raise) — code must check return value.
sign_off: 2026-02-22
blockers: NONE
```

### Phase A: Schema

```yaml
description: Pydantic v2 models for all 8 bead types + enums
source: BEAD_FIELD_SPEC_v0.3 Section 3 (verbatim — do not invent fields)
status: COMPLETE
target_tests: 40+
actual_tests: 79 (27 enum + 52 schema)
deliverables:
  - bead_field/schema/*.py (core, fact, claim, signal, proposal, proposal_rejected, skill, model_version, policy, enums)
  - bead_field/tests/test_schema.py, test_enums.py
notes:
  - Include 1000-rapid-insert test verifying UUID v7 monotonic ordering (R5 mitigation)
  - Threading/concurrency stress tests are Gate 2+ scope (single-node Mini for now)
sign_off: —
blockers: —
```

### Phase B: Hashing + Hash Chain

```yaml
description: Deterministic SHA-256 hashing and per-stream chain
source: BEAD_FIELD_SPEC_v0.3 Section 5.1
status: COMPLETE
target_tests: 15+
actual_tests: 31 (14 hashing + 17 chain)
deliverables:
  - bead_field/integrity/hashing.py, chain.py
  - bead_field/tests/test_hashing.py, test_chain.py
sign_off: 2026-02-22
blockers: NONE
```

### Phase C: HLC

```yaml
description: Hybrid Logical Clock for knowledge_time
source: BEAD_FIELD_SPEC_v0.3 Section 3.1 + 4.1
status: PENDING
target_tests: 8+
deliverables:
  - bead_field/clock/hlc.py
  - bead_field/tests/test_hlc.py
notes:
  - Include 1000-rapid-tick test verifying HLC non-regression (no backward time)
  - Include rapid-fire hash chain append test verifying hash_prev linkage holds under fast sequential writes
  - True multi-thread/multi-process concurrency testing is Gate 2+ (M3 Ultra, multiple agents)
sign_off: —
blockers: —
```

### Phase D: Signing

```yaml
description: Dual PQC (Dilithium) + ECDSA signing
source: BEAD_FIELD_SPEC_v0.3 Section 5.3
status: PENDING
target_tests: 10+
deliverables:
  - bead_field/integrity/signing.py
  - bead_field/tests/test_signing.py
notes:
  - Integration tests on ACTUAL library API (ChadBoar learning #1)
  - If PQC stubbed: flag PQC_STUB=True, log degraded sovereignty alert (Owl)
  - Either signature alone sufficient for validation, both required for optimal health
sign_off: —
blockers: —
```

### Phase E: SQLite Bi-Temporal Store

```yaml
description: Bi-temporal storage with WT/KT range queries + version-tracked migrations
source: BEAD_FIELD_SPEC_v0.3 Section 4 + Gate 1 exit criteria
status: PENDING
target_tests: 30+
deliverables:
  - bead_field/store/bitemporal.py, migrations.py, queries.py
  - bead_field/tests/test_store.py, test_queries.py
notes:
  - Version-tracked migrations from day 1 (ChadBoar learning #2)
  - Test migration with dummy schema change BEFORE Genesis load (Owl)
sign_off: —
blockers: —
```

### Phase F: Merkle Anchoring

```yaml
description: Merkle tree + batch anchoring with hybrid trigger
source: BEAD_FIELD_SPEC_v0.3 Section 5.2
status: PENDING
target_tests: 15+
deliverables:
  - bead_field/integrity/merkle.py
  - bead_field/tests/test_merkle.py
sign_off: —
blockers: —
```

### Phase G: Ingestion Pipeline

```yaml
description: End-to-end pipeline — raw data → validated, signed, stored bead
source: BEAD_FIELD_SPEC_v0.3 Sections 2.2, 3, 5
status: PENDING
target_tests: 15+
deliverables:
  - bead_field/ingestion/pipeline.py
  - bead_field/tests/test_ingestion.py
notes:
  - Basic observability counters (beads ingested by type, rejections by reason)
sign_off: —
blockers: —
```

### Phase H: Genesis Curation + Snapshot

```yaml
description: Curate 981 CLAIMs, build Genesis Merkle tree, sign with sovereign key
source: BEAD_FIELD_SPEC_v0.3 Section 6 + COO Brief Phase H
status: PENDING
target_tests: 15+
deliverables:
  - bead_field/genesis/curator.py, snapshot.py, delta.py
  - bead_field/tests/test_genesis.py
  - bead_field/genesis/CURATION_REPORT.md
  - bead_field/genesis/GENESIS_VERIFICATION_REPORT.md
risk: HIGH — most consequential single task. Cryptographic origin of entire refinery.
halt_points:
  - HALT 1: After curation report generated. G reviews before proceeding.
  - HALT 2: After Genesis Merkle tree built. G signs with sovereign key.
sign_off: —
blockers: —
```

### Phase I: Forensic Integrity Stress Test

```yaml
description: Manual tamper detection + structural integrity — prove the system catches corruption and stands without LLM
source: Owl (Advisory Panel, 2026-02-22) + CTO (LLM Removal Test, 2026-02-22)
status: PENDING
target_tests: 8+
procedure:
  1: Manually edit a single byte in SQLite content blob of a FACT bead
  2: Manually change a knowledge_time stamp in the DB
  3: Verify chain.py hash walk triggers HARD_FAIL
  4: Verify merkle.py proof verification fails
  5: Verify signing verification fails on tampered bead
  6: LLM Removal Test — load any bead from store, reconstruct full object from stored fields
     only. No LLM call, no prose interpretation. If any field requires inference to parse,
     that is a structural failure (INV-LLM-REMOVAL-TEST).
deliverables:
  - bead_field/tests/test_invariants.py (tamper detection + LLM removal suite)
rationale: |
  Proving code works is Phases A-H. Proving integrity works is steps 1-5.
  Proving the system is sovereign (no LLM dependency in the record) is step 6.
sign_off: —
blockers: —
```

---

## 4. RISK LOG

| ID | Risk | Severity | Mitigation | Status |
|----|------|----------|------------|--------|
| R1 | PQC (Dilithium) unavailable on ARM Mac Mini | HIGH | ~~Fallback chain needed~~ RESOLVED: pqcrypto 0.4.0 with native ARM wheel. ML-DSA-65 (Dilithium3). No stub. | RESOLVED (Phase 0) |
| R2 | Canonical JSON non-determinism | MEDIUM | Explicit `json.dumps(sort_keys=True, separators=(',', ':'), ensure_ascii=False)`. Round-trip determinism tested. | RESOLVED (Phase B) |
| R3 | Genesis curation misclassification | HIGH | Halt-and-review protocol. G approves before snapshot. Curation report preserved. | PENDING (Phase H) |
| R4 | SQLite datetime precision edge cases | LOW | ISO 8601 with microsecond precision. Test boundary cases explicitly. | PENDING (Phase E) |
| R5 | UUID v7 ordering under rapid insertion | LOW | uuid6 library handles monotonicity. Test 1000 rapid creates. | PENDING (Phase A) |
| R6 | Migration version drift on multi-session builds | MEDIUM | Numbered migrations with rollback. Test dummy migration before Genesis load. | PENDING (Phase E) |

---

## 5. GATE 1 EXIT CRITERIA

From BEAD_FIELD_SPEC_v0.3 Section 10 + COO_BRIEF_GATE_1.md Section 6:

```yaml
EC1: "Show all FACT beads about EURUSD that we knew on Jan 1 about Q4 2025" → correct results
EC2: Merkle proof for any bead reconstructable and verifiable
EC3: Ancestral CLAIMs queryable as PATTERN-class beads with intact lineage
EC4: All 8 bead types validate and store correctly
EC5: Hash chain tamper detection works
EC6: Dual signing works (PQC + ECDSA)
EC7: Genesis Snapshot signed and verifiable
EC8: 200+ tests passing
```

---

## 6. RUNNING SCORE

```yaml
as_of: 2026-02-22
phase: Phase B COMPLETE — ready for Phase C (HLC)
tests_passing: 110
bead_types_implemented: 8/8
invariants_proven: 3 (INV-SHADOW-RICH, INV-REJECTION-POLICY-REF, temporal class validation)
genesis_status: NOT_STARTED
blockers: NONE
```

---

## 7. ANOMALY / BLOCKER LOG

```yaml
# Timestamped entries. Future sessions learn from past pain.
# Format: - date: YYYY-MM-DD | phase: X | issue: description | resolution: description

entries:
  - date: 2026-02-22
    phase: "0"
    issue: |
      liboqs-python 0.14.1 fails on ARM Mac Mini. The Python wrapper tries to
      auto-install liboqs C library from source (cloning git branch 0.14.1) but
      the branch doesn't exist. Homebrew's liboqs 0.15.0 only builds static (.a),
      not shared (.dylib), so the Python wrapper can't load it.
    resolution: |
      Used pqcrypto 0.4.0 instead. Has pre-built ARM64 wheel with ML-DSA-65
      (NIST-standardized Dilithium3). verify() returns bool, not raise.
      No PQC stub needed.
```

---

## 8. POST-GATE-1

```yaml
SUBSTRATE_ASSERTION:
  description: |
    Cryptographic ceremony after Gate 1 PASS, before freeze begins.
    G signs the exact constitution the refinery began with.
    The Genesis Snapshot signs the data. This assertion signs the system
    that produced the data.
  G_signs:
    - schema_hash: SHA-256 of all Pydantic model definitions (bead_field/schema/)
    - migration_version: Current migration version number
    - invariant_set_hash: SHA-256 of the invariant set enforced by test suite
    - test_count: Total passing tests at Gate 1 PASS
    - genesis_merkle_root: Root hash of the Genesis Snapshot
  output: SUBSTRATE_ASSERTION POLICY bead (signed, stored, permanent)
  rationale: |
    Six months from now, diff against this assertion to know exactly
    what changed. Institutional systems document their baseline.

DEC-SUBSTRATE-FREEZE:
  trigger: Gate 1 PASS + Substrate Assertion signed
  duration: 30 days
  allowed: Bug fixes only
  prohibited: Schema field additions, new bead types, invariant changes

OBSERVABILITY_BEFORE_INTELLIGENCE:
  required_before_gate_5:
    - Beads per day by type
    - Rejection completeness % (shadow richness)
    - WT/KT delta distribution
    - Merkle batch frequency
    - Lineage depth distribution

DGX_READINESS:
  hardware: ARRIVED (2026-02-21)
  role: Gate 5+ compute (Dream Cycle, SkillRL, adversarial simulation)
  gate_1_role: NONE
```

---

*Every phase complete. Every sign-off earned. Every bead a commitment.*
