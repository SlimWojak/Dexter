# DEXTER SPRINT ROADMAP
## Sovereign Evidence Refinery — ICT Forensic Extraction
## Updated: 2026-02-04 (Post-Advisor Synthesis)

---

## CURRENT STATUS

```yaml
phase: EXTRACTION_READY
soak_complete: true
signatures_validated: 504
bundles_created: 32
corpus_mapped: 790 videos (full) + 24 videos (ICT 2022)
tests: 322/322 PASS
phoenix_integration: BRIDGE_SPEC_COMPLETE

# Core priorities (all complete)
chronicler: IMPLEMENTED (P1 COMPLETE)
backprop_seam: IMPLEMENTED (P2 COMPLETE)
queue_atomicity: IMPLEMENTED (P5 COMPLETE)
auditor_hardening: IMPLEMENTED (P4 COMPLETE)
runaway_guards: IMPLEMENTED (P6 COMPLETE)

# Source ingestion (in progress)
source_pipeline: OPERATIONAL
  pdf_ingester: IMPLEMENTED (P3.1)
  md_ingester: IMPLEMENTED (P3.1)
  unified_runner: IMPLEMENTED (P3.3)
  ict_2022_survey: COMPLETE (P3.2)
  extraction_run: PENDING (P3.4)

sources_registered:
  ict_2022_mentorship: 24 videos (CANON)
  blessed_trader: 18 PDFs (LATERAL)
  olya_notes: 22 PDFs (OLYA_PRIMARY)
  layer_0: 1 MD (OLYA_PRIMARY)
  full_channel: 790 videos (ICT_LEARNING)
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
| P5 | Queue atomicity (crash-safe writes) | ✅ COMPLETE | 2026-02-05 |
| P4 | Auditor hardening (v0.3 Bounty Hunter) | ✅ COMPLETE | 2026-02-05 |
| P6 | Runaway guards (turn cap, cost, watchdog) | ✅ COMPLETE | 2026-02-05 |
| P6.1 | Guard integration into main loop | ✅ COMPLETE | 2026-02-05 |

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

### P3: SOURCE INGESTION PIPELINE — IN PROGRESS
```yaml
status: IN_PROGRESS (P3.1-P3.3 COMPLETE, P3.4 PENDING)
risk: LOW (infrastructure ready, extraction run pending)
description: |
  Multi-source extraction capability: YouTube, PDF, Markdown.
  Source tier tagging: CANON, OLYA_PRIMARY, LATERAL, ICT_LEARNING.
  Unified orchestration via scripts/run_source_extraction.py.
source: CSO strategic input + lateral source requirement
owner: Dexter COO
completed_sub_tasks:
  P3.1: PDF + MD ingesters (skills/document/)
  P3.2: ICT 2022 Mentorship playlist survey (24 videos, CANON)
  P3.3: Unified extraction runner (5 sources registered)
pending:
  P3.4: First multi-source extraction run
evidence:
  - skills/document/pdf_ingester.py (PyMuPDF extraction)
  - skills/document/md_ingester.py (section preservation)
  - scripts/run_source_extraction.py (multi-source orchestrator)
  - corpus/ict_2022_mentorship_*.yaml (playlist survey)
  - tests: 322/322 PASS (20 new document ingester tests)
```

### P4: AUDITOR PROMPT HARDENING — COMPLETE
```yaml
status: COMPLETE
risk: MITIGATED (hardened v0.3 Bounty Hunter pattern)
description: |
  Hardened Auditor with 6 mandatory falsification attacks.
  Added tautology and ambiguity detection.
  Rejection rate tracking with flags (RUBBER_STAMP, CRITICAL_LOW, BELOW_TARGET).
  Target: 10% rejection floor.
source: Advisor synthesis
owner: Dexter COO
completed: 2026-02-05
evidence:
  - roles/auditor.yaml v0.3 (Bounty Hunter framing)
  - core/auditor.py (6 falsification checks + rate tracking)
  - tests/test_auditor.py (27 tests, including tautology, ambiguity, rate tracking)
```

### P5: QUEUE ATOMICITY — COMPLETE
```yaml
status: COMPLETE
risk: MITIGATED (crash-safe writes)
description: |
  save_queue() now uses write-tmp + atomic rename.
  Crash at any point = old file or new file, never partial.
source: COO codebase notes
owner: Dexter COO
completed: 2026-02-05
evidence:
  - core/queue_processor.py: save_queue() with fsync + os.replace
  - tests: 3 new atomic write tests
```

### P6: RUNAWAY GUARDS — COMPLETE
```yaml
status: COMPLETE
risk: MITIGATED (guards implemented)
description: |
  - Hard turn cap (20 turns default, configurable)
  - Daily cost ceiling ($1.00/day default)
  - Session cost ceiling ($0.50/session default)
  - No-output watchdog (5 min timeout default)
  - GuardManager for unified guard orchestration
source: GPT advisor
owner: Dexter COO
completed: 2026-02-05
evidence:
  - config/guards.yaml (configuration)
  - core/guards.py (TurnCapGuard, CostCeilingGuard, StallWatchdogGuard, GuardManager)
  - tests/test_guards.py (25 tests)
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
  1: cat docs/COLD_START.md (quick orientation)
  2: cat docs/SPRINT_ROADMAP.md (this file)
  3: cat docs/DEXTER_MANIFEST.md (system status)
  4: python3 scripts/run_source_extraction.py --status (source inventory)
  5: Check bundles/index.jsonl (extraction state)

context_in_30_seconds:
  - P1-P6 ALL COMPLETE: Chronicler, backprop, auditor, queue, guards
  - P3 IN_PROGRESS: Source pipeline operational, extraction run pending
  - 5 sources registered: ICT 2022 (24), Blessed (18), Olya (22), Layer0 (1), Full (790)
  - Tests: 322/322 PASS
  - Next action: P3.4 multi-source extraction run
  - Phoenix S47 is separate track. Dexter operates independently.
```

---

## EXTRACTION CAMPAIGN (Upcoming)

```yaml
phase: P3.4 — First Multi-Source Extraction Run
status: READY_TO_EXECUTE

sources_ready:
  ict_2022_mentorship:
    type: youtube
    count: 24 videos
    tier: CANON
    topics: [KILLZONE, MARKET_STRUCTURE, BIAS, RISK, TIME_PRICE, OTE, PSYCHOLOGY]
    command: "python3 scripts/run_source_extraction.py --source ict_2022_mentorship --execute"

  blessed_trader:
    type: pdf
    count: 18 documents
    tier: LATERAL
    command: "python3 scripts/run_source_extraction.py --source blessed_trader --execute"

  olya_notes:
    type: pdf
    count: 22 documents
    tier: OLYA_PRIMARY
    command: "python3 scripts/run_source_extraction.py --source olya_notes --execute"

recommended_sequence:
  1: ICT 2022 first 3 videos (test run, verify output quality)
  2: Blessed Trader PDFs (lateral context)
  3: Olya notes (highest alpha source)
  4: ICT 2022 remaining 21 videos

guards_active:
  turn_cap: 20 per loop
  cost_ceiling: $1.00/day, $0.50/session
  watchdog: 5 min no-output halt

human_gate: Required before each batch
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
  chronicler: MITIGATED (P1 COMPLETE — recursive summarization + archival)
  queue_atomicity: MITIGATED (P5 COMPLETE — atomic write pattern)
  auditor_leniency: MITIGATED (P4 COMPLETE — hardened to v0.3, rate tracking)
  runaway_guards: MITIGATED (P6 COMPLETE — turn cap, cost ceiling, watchdog)

operational:
  injection_false_positives: 2/20 videos (Ep13 "pretend to be", Ep19 "you are now")
  matrix_alerts: Cosmetic warning (non-blocking)
  sync_pipeline: Won't scale past 100+ videos
  daemon_mode: Not configured (manual TMUX + Amphetamine)

pending:
  researcher_role: Perplexity (defer until curriculum)
  developer_role: Backtest code generation (far horizon)
```

---

## SECURITY STACK

```yaml
L1_containment: Docker --network none
L2_input_sanitization: 4-layer injection guard
L3_runaway_prevention: Turn cap + cost ceiling (IMPLEMENTED — P6)
L4_stall_detection: No-output watchdog (IMPLEMENTED — P6)
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
