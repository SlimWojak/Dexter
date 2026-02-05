# DEXTER SPRINT ROADMAP
## Sovereign Evidence Refinery — ICT Forensic Extraction
## Updated: 2026-02-04 (Post-Advisor Synthesis)

---

## CURRENT STATUS

```yaml
phase: OPERATIONAL_MVP
soak_complete: true
signatures_validated: 504
bundles_created: 32
corpus_mapped: 790 videos
tests: 255/255 PASS
phoenix_integration: BRIDGE_SPEC_COMPLETE
chronicler: IMPLEMENTED (P1 COMPLETE)
backprop_seam: IMPLEMENTED (P2 COMPLETE)
```

---

## COMPLETED PHASES

| Phase | Description | Status | Date |
|-------|-------------|--------|------|
| 0 | Scaffold + repo structure | ✅ COMPLETE | 2026-02-03 |
| 1 | Core loop + injection guard | ✅ COMPLETE | 2026-02-03 |
| 2 | Auditor + Bundler skeleton | ✅ COMPLETE | 2026-02-03 |
| 3 | Theorist + full loop | ✅ COMPLETE | 2026-02-03 |
| 4A | Real transcripts (Supadata) | ✅ COMPLETE | 2026-02-03 |
| 5 | LLM Theorist + Cartographer + operational | ✅ COMPLETE | 2026-02-03 |
| Integration | Phoenix CLAIM_BEAD bridge | ✅ SPEC_COMPLETE | 2026-02-03 |
| Soak | Overnight extraction (20 videos) | ✅ COMPLETE | 2026-02-04 |
| P1 | Chronicler (recursive summarization) | ✅ COMPLETE | 2026-02-05 |
| P2 | Back-propagation seam (learning loop) | ✅ COMPLETE | 2026-02-05 |

---

## ACTIVE PRIORITIES (Post-Advisor Synthesis)

### P1: CHRONICLER IMPLEMENTATION — COMPLETE
```yaml
status: COMPLETE
risk: MITIGATED (memory bloat addressed)
description: |
  Implemented recursive summarization with clustering.
  THEORY.md generated with 5-drawer organization + index.
  Archive flow working (session beads → archive/).
  NEGATIVE section preserved.
  Redundancy detection: 75 pairs flagged (cosine >= 0.85).
owner: Dexter COO
completed: 2026-02-05
evidence:
  - core/chronicler.py (compress_beads, cluster_by_drawer, detect_redundant_pairs)
  - tests/test_chronicler.py (25 tests)
  - memory/THEORY.md (424 claims → 389 clusters)
  - memory/archive/ (session archival working)
```

### P2: BACK-PROPAGATION SEAM — COMPLETE
```yaml
status: COMPLETE
risk: MITIGATED (learning loop now operational)
description: |
  Olya rejection → NEGATIVE_BEAD → feeds back to Theorist context.
  RLHF analogy: Olya = Reward Model, Dexter = Policy.
  This is the seam that makes the refinery LEARN.
source: OWL advisor
owner: Dexter COO
completed: 2026-02-05
evidence:
  - Enhanced NEGATIVE_BEAD schema (source_claim_id, drawer, rejected_by)
  - scripts/record_rejection.py (CLI for human rejection)
  - tests/test_backprop.py (22 tests)
  - Theorist context injection verified
  - Chronicler integration verified
```

### P3: SCOPE CONSTRAINT — AWAITING CSO CURRICULUM
```yaml
status: BLOCKED (awaiting CSO input)
risk: MEDIUM (unbounded extraction dilutes signal)
description: |
  CSO providing curated curriculum (24-48h).
  Bound Dexter extraction to specified videos/modules.
  "Forensic surgeon, not morgue consumer" (Olya).
  Depth over breadth: 1-3 core setups at exhaustive depth first.
source: CSO strategic input
owner: G + CSO Team
```

### P4: AUDITOR PROMPT HARDENING
```yaml
status: PENDING
risk: MEDIUM (2.1% rejection rate too low)
description: |
  Harden Auditor prompt before adding third family.
  Target: 10% rejection floor (BOAR health metric).
  Sequence: Prompt hardening → monitor → third family if <5%.
source: Advisor synthesis
owner: Dexter COO
```

### P5: QUEUE ATOMICITY
```yaml
status: PENDING
risk: MEDIUM (state corruption on crash)
description: |
  save_queue() does full YAML rewrite.
  Fix: write-tmp + rename pattern (5 lines).
  Ship before scaling past current batch sizes.
source: COO codebase notes
owner: Dexter COO
```

### P6: RUNAWAY GUARDS — NEW
```yaml
status: PENDING
risk: MEDIUM (token burn, stall detection)
description: |
  - Hard turn cap (10-20 turns per agent loop)
  - Daily cost ceiling
  - No-output watchdog (halt if no output > X minutes)
source: GPT advisor
owner: Dexter COO
```

---

## LOWER PRIORITY (Queue for Later)

### Injection Filter Tuning
```yaml
status: PENDING
risk: LOW (2/20 videos affected)
description: Whitelist common ICT speech patterns (false positives).
```

### Researcher Role (Perplexity)
```yaml
status: SCOPED_NOT_BUILT
description: |
  Perplexity as R&D layer (microstructure, regime, execution research).
  Defer until core extraction stable + CSO curriculum defined.
```

### Hardening (Daemon Mode)
```yaml
status: SCOPED_NOT_BUILT
description: |
  - launchd for auto-start on boot
  - Structured logging + rotation
  - Error alerting (Matrix push)
  - Bundle content hashing
```

---

## NEW INVARIANTS (From Advisor Synthesis)

```yaml
INV-DEXTER-ICT-NATIVE:
  source: OWL
  rule: "Theorist uses raw ICT terminology. Translation at Bundler only."
  enforcement: Theorist prompt

INV-FACT-ENCAPSULATES-CLAIM:
  source: OWL (adopted)
  rule: "Every FACT bead references source CLAIM_ID for forensic trace."
  enforcement: Bridge contract spec

INV-CALIBRATION-FOILS:
  source: OWL (modified per CSO)
  rule: "Validation batches MAY include foils. Operator-configurable."
  enforcement: Calibration protocol

INV-RUNAWAY-CAP:
  source: GPT
  rule: "Agent loops hard-capped at N turns. No-output > X min → halt."
  enforcement: Loop implementation

INV-BEAD-AUDIT-TRAIL:
  source: BOAR
  rule: "All beads auditable end-to-end with full provenance chain."
  enforcement: Bead schema
```

---

## CSO STRATEGIC INPUTS (Accepted)

```yaml
1_curated_curriculum:
  request: Bound extraction to CSO-provided video list
  status: ACCEPTED — awaiting curriculum (24-48h)
  
2_depth_over_breadth:
  request: Phase 1 = 1-3 core setups at exhaustive depth
  status: ACCEPTED — routes to extraction scope
  
3_foils_configurable:
  request: Foil injection optional, not mandatory
  status: ACCEPTED — default-reject is primary guard
  
4_lateral_sources:
  request: Accommodate sources beyond ICT YouTube
  status: NOTED — curriculum spec will define
```

---

## PHOENIX INTEGRATION STATUS

```yaml
bridge: CLAIM_BEAD file-based export
format: JSONL with drawer tags + provenance
invariant: INV-DEXTER-ALWAYS-CLAIM (never auto-promote)
integration_timing: AFTER both sides stable
phoenix_next: S47 Lease Implementation (separate track)
```

---

## ORIENTATION FOR NEXT SESSION

```yaml
bootstrap_sequence:
  1: cat docs/SPRINT_ROADMAP.md (this file)
  2: cat docs/DEXTER_MANIFEST.md (system status)
  3: Check bundles/index.jsonl (extraction state)
  4: Confirm CSO curriculum received (if ready)

context_in_30_seconds:
  - Overnight soak: 504 signatures, 32 bundles
  - Advisor synthesis complete: 4 new invariants
  - CSO input: Depth > breadth, curated curriculum coming
  - P1: Chronicler (memory). P2: Back-propagation seam.
  - Phoenix S47 is separate track. Dexter operates independently.
```

---

## SEED IDEAS (Vision, Not Sprint Scope)

```yaml
HIGHEST_ALPHA — OLYA_MANIFEST:
  concept: |
    Dexter extracts from Olya's OWN content (journals, notes, trade logs).
    Three ore sources converge:
      - ICT content (tradition — what's taught)
      - Lateral educators (Blessed Trader PDFs, etc.)
      - Olya's cognitive exhaust (practice — what she actually does)
    The delta between teaching and practice IS the edge.
  phase: 6+ ("Oracle's Archive")

PARALLEL_SYNTHETIC_PHOENIX:
  concept: Dexter agents test hypotheses on Phoenix sim with 5yr backdata.
  prerequisite: Phoenix sim environment must exist
  phase: 8+ (Carpark)

FLYWHEEL_AMP:
  concept: Continuous mining + journal ingestion + rejection tuning + dynasty memory.
  prerequisite: P1 Chronicler must ship first
  phase: 6-7

RESEARCHER_ROLE:
  concept: Perplexity as R&D layer (microstructure, regime, execution research).
  status: SCOPED_NOT_BUILT — defer until curriculum defined
  
SELF_UPGRADING_META:
  classification: CARPARK (constitutional muzzle stays tight)
  risk: Highest authority drift risk — park until trust earned
```

---

## ADVISOR RULINGS (2026-02-04)

```yaml
promotion_states:
  ruling: Binary CLAIM/FACT (GPT wins, rich metadata on FACT)
  rejected: OWL's PROVISIONAL_FACT (gray authority risk)
  adopted: OWL's provenance chain (FACT encapsulates CLAIM_ID)

calibration_protocol:
  default_reject: Approval requires explicit action
  delta_input: Edit ≥1 parameter per 5 signatures
  view_separation: Dexter vs Perplexity shown separately
  foils: Optional, operator-configurable

auditor_sequence: Prompt harden → monitor → third family if <5%

atom_budget: 32-48 features across 5 drawers
```

---

## KNOWN GAPS

```yaml
critical:
  chronicler: Not implemented (beads unbounded — P1 URGENT)
  queue_atomicity: save_queue() does full YAML rewrite (crash corruption risk)
  auditor_leniency: 2.1% rejection rate too low (target 10%)

operational:
  injection_false_positives: 2/20 videos (Ep13 "pretend to be", Ep19 "you are now")
  matrix_alerts: Cosmetic warning (non-blocking)
  sync_pipeline: Won't scale past 100+ videos
  daemon_mode: Not configured (manual TMUX + Amphetamine)

pending:
  runaway_guards: P6 (turn cap, cost ceiling, watchdog)
  researcher_role: Perplexity (defer until curriculum)
  developer_role: Backtest code generation (far horizon)
```

---

## SECURITY STACK

```yaml
L1_containment: Docker --network none
L2_input_sanitization: 4-layer injection guard
L3_runaway_prevention: Turn cap + cost ceiling (PENDING)
L4_stall_detection: No-output watchdog (PENDING)
L5_credentials: Composio auth (FUTURE)
```

---

## RELATED DOCUMENTS

| Document | Location | Purpose |
|----------|----------|---------|
| `COLD_START.md` | `docs/` | Quick orientation for new CTO |
| `DEXTER_MANIFEST.md` | `docs/` | Operational status + evidence |
| `DEXTER_ROADMAP_v0.2.md` | `docs/` | Build history (phases 0-5) |
| `PHOENIX_MANIFEST.md` | `docs/` | Phoenix system reference |
| `POST_S44_SYNTHESIS_v0.1.md` | `docs/` | Advisor synthesis source |
| `addendum_from_CTO_Opus_Review.md` | `docs/` | Seed ideas (Olya_Manifest) |
| `ROLE_CONTRACTS.md` | `docs/` | Role boundaries |
| `CLAUDE.md` | root | Build agent orientation |

---

**OINK OINK.** 🐗🔬
