# CLAUDE.md — a8ra Bead Field Build Agent Orientation
## Read this FIRST. Then docs/BEAD_FIELD_SPRINT.md → BEAD_FIELD_SPEC_v0.3

---

## 0. IDENTITY

```yaml
project: a8ra (pronounced "a-eight-ra")
type: Sovereign Intelligence Refinery
function: Systematize discretionary trading expertise into mineable, reproducible knowledge
active_track: BEAD_FIELD_GATE_1 (Substrate Ready)
location: Mac Mini (build) → M3 Ultra (deploy)
sibling: Phoenix (constitutional trading system, separate repo)
motto: "Human frames. Machine computes. Human promotes."
```

### Two-Economy Model

```yaml
ECONOMY_1 — GOVERNANCE (The Law):
  owner: Phoenix
  properties: Deterministic, binary, state-machine, permanent
  examples: Lease activation, halt, state lock, T2 approval, ceremony
  rule: "Once signed, it's law."

ECONOMY_2 — ANALYTICAL (The Science):
  owner: Bead Field + Dream Cycle
  properties: Rich, bi-temporal, provenance-linked, mineable, experimental
  substrate: Hard (beads are signed, immutable, bi-temporal)
  analysis: Fluid (Dream Cycle computes over beads, disposable)
  examples: FACT, CLAIM, SIGNAL, PROPOSAL, PROPOSAL_REJECTED, SKILL
  rule: "Every bead is a sensor reading. Mine everything."

BRIDGE:
  direction: Economy 2 → Economy 1 (one-way valve)
  mechanism: SKILL beads validated through stress testing
  invariant: INV-BRIDGE-PROMOTION-GATE
  reverse: Economy 1 projects INTO Economy 2 as FACT beads (observation, not authority)
```

### The Moat

```yaml
DESIGN_PRINCIPLE: |
  The Bead Field is not a log. It is a high-resolution physics experiment.
  The moat is the quality of the record. If beads are weak,
  everything downstream is noise. If beads are strong,
  the DGX becomes an amplifier.

  Particles don't know their energy. The field equations compute it.
  The Bead Field carries no opinions. The Dream Cycle computes all opinions.
  The human decides which opinions become law.
```

---

## 1. QUICK STATUS (Update on major changes)

```yaml
as_of: 2026-02-22
phase: GATE_1_PLANNING

gate_1_build:
  status: NOT_STARTED (governance docs created, code pending)
  tests: 0/200+ target
  bead_types: 0/8
  genesis: NOT_STARTED
  detail: See docs/BEAD_FIELD_SPRINT.md

extraction_phase: COMPLETE (preserved in src/, not active)
  signatures: 981 validated
  bundles: 73
  tests: 363/363 PASS

hardware:
  dgx_spark: ARRIVED (2026-02-21, standing by for Gate 5+)
  m3_ultra: INCOMING (deployment target)
  mac_mini: OPERATIONAL (Gate 1 build hardware)
  m4_max: OPERATIONAL (Phoenix, separate track)
```

---

## 2. INVARIANTS (NON-NEGOTIABLE)

### Sovereignty

```yaml
INV-HUMAN-FRAMES: "Human frames. Machine computes. Human promotes."
INV-SOVEREIGN-VETO: "G can halt any task via BROADCAST."
INV-OLYA-ABSOLUTE: "Olya's NO on methodology is absolute."
INV-CAPITAL-GATE: "No live execution without human T2 approval."
```

### Bridge

```yaml
INV-BRIDGE-PROMOTION-GATE: "Economy 2→1 only via validated SKILL beads."
INV-DEXTER-ALWAYS-CLAIM: "All Dexter output enters Phoenix as CLAIM, never FACT."
```

### Data Integrity

```yaml
INV-BEAD-IMMUTABLE: "Structural beads append-only. No mutation, only supersession or retraction."
INV-BEAD-SIGNED: "Every structural bead carries dual PQC+ECDSA signatures."
INV-BEAD-TEMPORAL: "Every structural bead has KT. OBSERVATION requires WT."
INV-SHADOW-RICH: "PROPOSAL_REJECTED structurally identical to PROPOSAL + rejection context."
INV-TEMPORAL-BOUNDING: "DERIVED WT = intersection of OBSERVATION input spans only."
INV-COMMITMENT-THRESHOLD: "Only Formal Handoffs become beads. commit() is the bright line."
INV-NO-ORPHAN-INSIGHTS: "All rejected proposals captured and routed to Dream Cycle."
INV-REJECTION-POLICY-REF: "RISK_BREACH rejections MUST reference active POLICY version."
INV-ANCESTRAL-PRESERVED: "981 CLAIMs form Genesis Snapshot, G-signed Merkle root."
INV-SOVEREIGN-ANCHOR: "Daily ledger root signed with offline HSM."
INV-ANCHOR-AT-DECISIONS: "Merkle triggers on SIGNAL/PROPOSAL or fallback caps (500/1hr)."
```

### Quality

```yaml
INV-NO-GRADES: "No grades, no scores, no rankings. PASS/FAIL boolean only."
INV-NO-NARRATIVE: "Evidence bundles template-locked. No interpretation."
INV-CROSS-FAMILY: "Theorist and Auditor must be different model families."
INV-ATTR-CAUSAL-BAN: "No causal attribution without controlled experiment."
INV-CLAIM-FACT-SEPARATION: "Claims and facts are distinct types. Binary, no gray."
INV-REFINERY-LATENCY-TRACKED: "WT-KT delta is first-class metric. Near-zero = anomaly."
INV-EXECUTION-FIDELITY: "Intent vs fill delta tracked. >50bps = alert."
```

### Security

```yaml
INV-NO-SECRETS-IN-REPO: "Git hooks block credential patterns."
INV-DEPLOYMENT-AUDIT: "Security invariants cover deployment config, not just code."
INV-RUNAWAY-CAP: "Agent loops hard-capped. No-output timeout. Daily cost ceiling."
INV-CHECKPOINT-BEFORE-DEATH: "Checkpoint at 70% context, forced at 90%."
```

### Operational

```yaml
INV-HALT-1: "halt_local < 50ms."
INV-HALT-2: "halt_cascade < 500ms."
INV-HALT-OVERRIDES-LEASE: "Halt wins. Always."
INV-PERISH-BY-DEFAULT: "No auto-renew. Ceremony or expire."
INV-NO-CORE-REWRITES-POST-S44: "Phoenix foundation validated. No rewrites."
```

### Advisory Panel Additions (2026-02-22)

```yaml
INV-DREAM-ISOLATION: |
  Dream Cycle processes may NOT write to bead store directly.
  May only emit SKILL_CANDIDATE via ingestion pipeline.
  Must pass full schema validation + signing like any other bead.
```

---

## 3. CANON DOCUMENTS

```yaml
READING_ORDER:
  1: CLAUDE.md (this file — identity and rules)
  2: docs/BEAD_FIELD_SPRINT.md (phase progress and blockers)
  3: docs/beadfields_plan/BEAD_FIELD_SPEC_v0.3.md (the data constitution)
  4: docs/beadfields_plan/COO_BRIEF_GATE_1.md (build sequence)
  5: docs/beadfields_plan/a8ra_MASTER_PLAN_v0_1.md (world view)
  6: docs/beadfields_plan/a8ra_SYSTEM_MANIFEST_v1_0.md (cross-system orientation)

AWARE_OF_BUT_DO_NOT_BUILD:
  docs/beadfields_plan/DREAM_CYCLE_DESIGN_INTENT_v0_1.md: |
    How the Dream Cycle (Gate 5+) will analyze the Bead Field.
    Key decision: DEC-ENERGY-NOT-STORED — energy/coherence is COMPUTED over beads,
    never STORED on them. No energy fields, no scalar scores, no coherence attributes
    on bead schema. INV-NO-GRADES applies. Aligns with LeCun/JEPA: substrate = hard
    physics, Dream Cycle = fluid analysis. Build the hard substrate. Mining comes later.

STATUS: LOCKED (Three-office approved. Do not relitigate. Build from them.)
```

---

## 4. ARCHITECTURE

### Bead Field Directory (Gate 1 Build Surface)

```
bead_field/
├── __init__.py
├── schema/
│   ├── __init__.py
│   ├── core.py              # BeadCore base model (Spec Section 3.1)
│   ├── fact.py               # FACT content schema
│   ├── claim.py              # CLAIM content schema
│   ├── signal.py             # SIGNAL content schema
│   ├── proposal.py           # PROPOSAL content schema
│   ├── proposal_rejected.py  # PROPOSAL_REJECTED (INV-SHADOW-RICH)
│   ├── skill.py              # SKILL content schema
│   ├── model_version.py      # MODEL_VERSION content schema
│   ├── policy.py             # POLICY content schema
│   └── enums.py              # All shared enums
├── store/
│   ├── __init__.py
│   ├── bitemporal.py         # SQLite bi-temporal store
│   ├── migrations.py         # Version-tracked schema migrations
│   └── queries.py            # Bi-temporal query helpers (WT/KT predicates)
├── integrity/
│   ├── __init__.py
│   ├── hashing.py            # SHA-256 canonical JSON hashing
│   ├── chain.py              # Per-stream hash chain
│   ├── merkle.py             # Merkle tree + batch anchoring
│   └── signing.py            # Dual PQC (Dilithium) + ECDSA signing
├── clock/
│   ├── __init__.py
│   └── hlc.py                # Hybrid Logical Clock
├── ingestion/
│   ├── __init__.py
│   └── pipeline.py           # Raw data → validated, signed, stored bead
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
    └── test_invariants.py     # Invariant enforcement + tamper detection
```

### Existing Codebase (Do Not Modify)

```yaml
src/: Extraction pipeline (COMPLETE — 363 tests, 981 signatures)
bundles/: 73 extraction bundles + 981 CLAIMs (Genesis source material)
config/: Extraction configuration
roles/: Agent role definitions (extraction phase)
```

### Eight Analytical Bead Types

```yaml
FACT: Market data, events (from providers or OPEN_SOURCE intelligence)
CLAIM: Agent inference with reasoning trace
SIGNAL: Tradeable thesis with derivation and risk profile
PROPOSAL: Trade intent that passed all gates
PROPOSAL_REJECTED: Declined trade — FULL context (Shadow Field fuel)
SKILL: Distilled lesson from Dream Cycle
MODEL_VERSION: Model metadata and deployment status
POLICY: Risk rules, position limits, regime definitions
```

### Three Temporal Classes

```yaml
OBSERVATION: Tied to specific market time (has WT span)
PATTERN: Timeless methodology (WT null, valid across all time)
DERIVED: Computed from other beads (WT = intersection of OBSERVATION inputs)
```

### Integrity Model

```yaml
hash_chain: Per-stream SHA-256 linking
merkle: Hybrid trigger (Decision Boundary + 500 bead / 1hr fallback)
signing: Dual PQC (Dilithium) + ECDSA (secp256r1)
sovereign_anchor: Daily ledger root signed with offline HSM
```

---

## 5. KEY DECISIONS

```yaml
# System Architecture
DEC-TWO-ECONOMIES: "Governance and analytical beads are separate systems with one-way bridge."
DEC-PROJECTION: "Phoenix projects into Bead Field. Bead Field doesn't modify Phoenix internals."
DEC-COE: "Olya validates (recognition), not extracts (recall)."
DEC-PHYSICS-EXPERIMENT: "Bead Field is a physics experiment, not a log."

# Data Architecture
DEC-BINARY-CLAIM-FACT: "No intermediate PROVISIONAL_FACT. Binary only."
DEC-TEMPORAL-BOUNDING: "DERIVED WT = intersection of OBSERVATION spans."
DEC-MERKLE-HYBRID: "Decision Boundary + fallback caps (500 beads / 1hr)."
DEC-GENESIS-SNAPSHOT: "981 CLAIMs bundled as single Merkle root. Bead Zero."
DEC-FORMAL-HANDOFF: "commit() is the bright line. Observation ≠ Incorporation."
DEC-PQC-FOUNDATIONAL: "Software-first PQC+ECDSA from Day 1. TEE is additional."

# Gate 1 Specific
DEC-NEW-CODEBASE-SAME-REPO: "Gate 1 builds clean in bead_field/. Extraction preserved in src/."
DEC-BUILD-NOW-DEPLOY-LATER: "Build on Mini now. Deploy to M3 Ultra in hours."
DEC-ENERGY-NOT-STORED: "Energy/coherence COMPUTED by Dream Cycle. NEVER stored on beads."
DEC-JEPA-ALIGNMENT: "Dream Cycle predicts bead configurations, not price ticks."
DEC-DIAGNOSTICS-EPHEMERAL: "Dream Cycle analytics are ephemeral. Only SKILL candidates become structural."

# Advisory Panel (2026-02-22)
DEC-SUBSTRATE-FREEZE: "30-day no-schema-change window after Gate 1 PASS."
DEC-SIMULATION-REPRODUCIBILITY: "Dream Cycle sessions log seed, snapshot hash, model, params. Gate 5+."
```

---

## 6. HARDWARE

```yaml
NODE_DGX — NVIDIA DGX Spark (Grace-Blackwell):
  status: ARRIVED (2026-02-21)
  role: Dream Cycle compute (Gate 5+)
  gate_1_role: NONE (standing by)

NODE_M3 — Mac Studio M3 Ultra (512GB):
  status: INCOMING
  role: Knowledge Substrate + Control Plane
  gate_1_role: Deployment target (tested code from Mini)

NODE_M4 — Mac Studio M4 Max (64GB):
  status: OPERATIONAL
  role: Phoenix Execution (separate track)
  gate_1_role: NONE

NODE_MINI — Mac Mini:
  status: OPERATIONAL
  role: Gate 1 build hardware (COO runs here)
```

---

## 7. RELATIONSHIPS

```yaml
G:
  role: Sovereign Operator
  authority: SUPREME
  function: Strategic direction, sprint approval, Genesis signing, capital allocation
  veto: BROADCAST.md → all offices halt

OLYA:
  role: CSO / Oracle
  authority: DOMAIN — sovereign over trading methodology
  function: CLAIM→FACT promotion, gate calibration, curriculum curation
  veto: Absolute and final. Rejection → NEGATIVE_BEAD → Dream Cycle.
  principle: "Recognition over recall. Forensic surgeon, not morgue consumer."

PHOENIX_CTO:
  role: Sibling instance (separate repo, hardware, team)
  status: S49→S50→v0.1 (2 sprints from first release)
  rule: Do NOT touch Phoenix repo. Integration via BRIDGE_SPEC (after both sides stable).

COO:
  role: Builder/implementer (Cursor Agent, Mac Mini)
  function: Receives briefs, executes phases, commits code, reports blockers
  current: Gate 1 build

ADVISORS:
  owl: Structure, coherence, pressure tests
  architect: Spec tightening, lint, guardrails
  boar: Frontier scout, chaos audit, energy
```

---

## 8. PHASE EXECUTION

```yaml
current: GATE_1 — BEAD_FIELD_SUBSTRATE
detail: See docs/BEAD_FIELD_SPRINT.md for phase-by-phase progress

GATE_SEQUENCE:
  Gate_1: Substrate Ready (NOW — schema, store, integrity, Genesis)
  Gate_2: Bead Field Semantics + Graph Operations
  Gate_3: AIR + Execution Integrity
  Gate_4: Swarm Agents + Coordination
  Gate_5: Dream Cycle v1 (DGX Spark)
  Gate_6: Dream Cycle v2 (GALILEO + SkillRL)
  Gate_7: Sovereign Readiness

COMMIT_DISCIPLINE:
  format: "[Gate1/Area] Brief description"
  rules:
    - Tests pass before every commit
    - Zero TODO/FIXME/HACK in committed code
    - Update BEAD_FIELD_SPRINT.md running score after milestones
    - Report blockers immediately (don't guess at solutions)
```

---

## 9. SEED IDEAS (Vision, Not Sprint Scope)

Do NOT build without G approval:

```yaml
OLYA_MANIFEST: Extract from her journals/notes → she validates "that's me"
PARALLEL_SYNTHETIC_PHOENIX: Test hypotheses on sim + 5yr backdata
FLYWHEEL_AMP: Continuous mining + dynasty memory
SELF_UPGRADING_META: CARPARK (constitutional muzzle tight)
```

---

## 10. THINGS TO NEVER DO

- Never auto-promote CLAIM → FACT
- Never touch Phoenix repo or infrastructure
- Never add grades/scores/rankings (except DataQuality on FACTs)
- Never deviate from BEAD_FIELD_SPEC_v0.3 schema definitions
- Never skip PQC signing (stub if unavailable, but never skip)
- Never modify src/ (extraction pipeline is COMPLETE)
- Never write Dream Cycle code in Gate 1
- Never store energy/coherence/scores on bead schema
- Never let DGX excitement expand Gate 1 scope
- Never commit without tests passing
- Never proceed past Genesis curation halt-points without G approval
- Never leak Olya's private parameters

---

## 11. CRITICAL REFERENCES

| Document | Location | Purpose |
|----------|----------|---------|
| BEAD_FIELD_SPRINT.md | docs/ | Phase tracker and running score |
| BEAD_FIELD_SPEC_v0.3 | docs/beadfields_plan/ | Data constitution (schema, invariants) |
| COO_BRIEF_GATE_1.md | docs/beadfields_plan/ | Build instruction manual (phases A-H) |
| a8ra_MASTER_PLAN_v0.1 | docs/beadfields_plan/ | Strategic world view (Two-Economy, Pulse) |
| a8ra_SYSTEM_MANIFEST_v1.0 | docs/beadfields_plan/ | Cross-system orientation |
| DREAM_CYCLE_DESIGN_INTENT_v0.1 | docs/beadfields_plan/ | Gate 5+ vision (do not build) |
| Advisory Feedback | docs/beadfields_plan/ | Advisor rulings (synthesized into sprint) |

---

*The moat is the quality of the record. The record is the Bead Field. Everything else is downstream.*
