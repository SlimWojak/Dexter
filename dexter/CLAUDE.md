# CLAUDE.md — Dexter Build Agent Orientation
## Read this FIRST. Then SPRINT_ROADMAP.md → DEXTER_MANIFEST.md

---

## IDENTITY

```yaml
project: DEXTER
type: Sovereign Evidence Refinery
purpose: Extract IF-THEN trading logic from ICT content → CLAIM_BEADs → Phoenix
location: Mac Mini MVP (→ M3 Ultra on graduation)
sibling: Phoenix (constitutional trading system, separate repo)
mascot: 🔬🧪 (Forensic Lab)
motto: "Mine the ore. Refine the gold. Human decides."
```

---

## ROLE

COO-level build agent. Full YOLO permissions inside Docker Sandbox.
CTO (Claude Web) maintains strategic oversight in parallel session.

---

## QUICK STATUS (Update this section on major changes)

```yaml
phase: OPERATIONAL_MVP
tests: 255/255 PASS
signatures_validated: 504
bundles_created: 32
corpus_mapped: 790 videos
overnight_soak: 18/20 videos processed
cost_per_video: ~$0.003
chronicler: IMPLEMENTED (P1 COMPLETE)
backprop_seam: IMPLEMENTED (P2 COMPLETE)

active_priorities:
  P1: Chronicler — COMPLETE (2026-02-05)
  P2: Back-propagation seam — COMPLETE (2026-02-05)
  P3: CSO curriculum scoping (awaiting Olya input)
  P4: Auditor hardening (2.1% rejection too low)
  P5: Queue atomicity (5-line fix)
  P6: Runaway guards (turn cap, cost ceiling)
```

---

## INVARIANTS (NON-NEGOTIABLE)

### Execution
- ALL code execution inside Docker Sandbox (`./docker-sandbox.sh`)
- `--dangerously-skip-permissions` allowed ONLY inside sandbox
- Never execute untrusted input outside sandbox

### Git Hygiene
- After every phase/sub-task completion:
  ```bash
  git add .
  git commit -m "[Phase X.Y] Brief description"
  git push origin main
  ```
- Update `docs/DEXTER_MANIFEST.md` NEXT_ACTIONS after each commit

### Output Constitutional
- Evidence-only bundles; no narrative (INV-NO-NARRATIVE)
- No grades/scores (INV-NO-GRADES)
- No recommendations (INV-NO-UNSOLICITED)
- All if-then signatures trace to transcript timestamp (INV-SOURCE-PROVENANCE)
- Auditor breaks, never validates (INV-AUDITOR-ADVERSARIAL)
- Output reconstructable without LLM (INV-LLM-REMOVAL-TEST)

### Context Management
- If context > 50k tokens: spawn fresh session, preserve beads/THEORY.md
- Bead compression every 20-30 beads via Chronicler (PENDING implementation)

### Phoenix Integration Invariants

```yaml
INV-DEXTER-ALWAYS-CLAIM: |
  All Dexter output enters Phoenix as CLAIM_BEAD, never FACT_BEAD.
  Refinement makes review faster, not unnecessary.
  Only human (Olya) promotes CLAIM -> FACT.

INV-DEXTER-NO-PROMOTE: |
  No auto-promotion to Phoenix. Human gate mandatory.
  Bundles accumulate. Human pulls when ready.

INV-DEXTER-SOURCE-LINK: |
  Every signature links to video URL + timestamp.
  Provenance is non-negotiable.

INV-DEXTER-CROSS-FAMILY: |
  Auditor must be different model family from Theorist.
  Currently: Theorist=deepseek, Auditor=google.
```

### Advisor Synthesis Invariants (2026-02-04)

```yaml
INV-DEXTER-ICT-NATIVE: |
  Theorist uses raw ICT terminology.
  Translation to Phoenix drawer names happens at Bundler only.
  Prevents feedback loop where Dexter mirrors Phoenix jargon.

INV-FACT-ENCAPSULATES-CLAIM: |
  Every FACT bead references source CLAIM_ID for forensic trace.
  Enables "search and destroy" if extraction logic found flawed.

INV-CALIBRATION-FOILS: |
  Validation batches MAY include foils. Operator-configurable.
  Foil approval flags session. Default-reject is primary guard.

INV-RUNAWAY-CAP: |
  Agent loops hard-capped at N turns (10-20).
  No-output > X minutes → halt.
  Daily cost ceiling enforced.

INV-BEAD-AUDIT-TRAIL: |
  All beads auditable end-to-end with full provenance chain.
```

---

## MODEL ROUTING

```yaml
roles:
  theorist:
    model: deepseek/deepseek-chat
    family: deepseek
    purpose: Extraction (strong at structured JSON output)
    
  auditor:
    model: google/gemini-2.0-flash-exp
    family: google
    purpose: Adversarial veto (DIFFERENT family for cross-family check)
    
  bundler:
    model: deepseek/deepseek-chat
    family: deepseek
    purpose: Template filling (low creativity needed)
    
  chronicler:
    model: google/gemini-2.0-flash-exp
    family: google
    purpose: Summarization (different family for fresh perspective)
    
  cartographer:
    model: google/gemini-2.0-flash-exp
    family: google
    purpose: Corpus survey and categorization
    
  heartbeat:
    model: thudm/glm-4.5-air
    family: thudm
    purpose: Free tier health checks

cost_discipline:
  deepseek: $0.14/$0.28 per 1M tokens (in/out)
  gemini: $0.10/$0.40 per 1M tokens
  target: ~$0.003/video
```

---

## ARCHITECTURE

```yaml
roles: [theorist, auditor, bundler, chronicler, cartographer]
  # researcher role: SCOPED_NOT_BUILT (Perplexity, defer until curriculum defined)

memory:
  beads: Append-only JSONL per calendar day
  theory_md: Recursive summarization (Chronicler — PENDING)
  archive: Compressed old beads (PENDING)

bridge:
  format: CLAIM_BEAD JSONL with drawer tags + provenance
  export: bundles/{id}_claims.jsonl
  invariant: INV-DEXTER-ALWAYS-CLAIM (never auto-promote)
  
5_drawer_system:
  drawer_1: HTF_BIAS (Higher timeframe directional context)
  drawer_2: MARKET_STRUCTURE (Structural breaks and formations)
  drawer_3: PREMIUM_DISCOUNT (Price relative to range)
  drawer_4: ENTRY_MODEL (Specific entry patterns)
  drawer_5: CONFIRMATION (Additional validation signals)
```

---

## SECURITY STACK

```yaml
L1_containment:
  docker: "--network none" (network isolation)
  sandbox: docker-sandbox.sh wrapper
  
L2_input_sanitization:
  injection_guard: 4-layer (preprocess → regex → TF-IDF semantic → halt)
  attack_db: data/attack_vectors.jsonl (auditable, extensible)
  threshold: cosine similarity > 0.85 = flag
  
L3_runaway_prevention:  # PENDING implementation
  turn_cap: 10-20 turns per agent loop
  cost_ceiling: Daily limit
  
L4_stall_detection:  # PENDING implementation
  watchdog: No-output > X minutes → halt
  
L5_credentials:  # FUTURE
  composio: Auth management (not implemented)
```

---

## CSO INPUTS (Accepted 2026-02-04)

```yaml
1_curated_curriculum:
  request: Bound extraction to CSO-provided video list
  status: ACCEPTED — awaiting curriculum (24-48h from 2026-02-04)
  
2_depth_over_breadth:
  request: Phase 1 = 1-3 core setups at exhaustive depth
  status: ACCEPTED — routes to extraction scope
  
3_foils_configurable:
  request: Foil injection optional, not mandatory
  status: ACCEPTED — default-reject is primary guard
  
4_lateral_sources:
  request: Accommodate sources beyond ICT YouTube
  status: NOTED — curriculum spec will define
  
5_integration_requirements:
  request: Shared file access, session persistence, Perplexity access
  status: NOTED — future, not blocking
```

---

## SEED IDEAS (Vision, Not Sprint Scope)

```yaml
HIGHEST_ALPHA — OLYA_MANIFEST:
  concept: |
    Dexter extracts from Olya's OWN content (journals, notes, trade logs).
    She validates: "That's my past self" vs "No, nuance."
    Three ore sources converge:
      - ICT content (tradition — what's taught)
      - Lateral educators (context — Blessed Trader PDFs, etc.)
      - Olya's cognitive exhaust (practice — what she actually does)
    The delta between teaching and practice IS the edge.
  prerequisite: CSO curriculum + Notion API or export
  phase: 6+ ("Oracle's Archive")

PARALLEL_SYNTHETIC_PHOENIX:
  concept: |
    Dexter agents test hypotheses on Phoenix sim with 5yr backdata.
    Evidence bundles from TESTING, not just extraction.
    Dexter becomes the hypothesis lab.
  prerequisite: Phoenix sim environment must exist
  phase: 8+ (Carpark until extraction stable)

FLYWHEEL_AMP:
  concept: |
    Continuous mining + journal ingestion + rejection tuning + dynasty memory.
    Chronicler → THEORY.md → recursive compression.
    The bead-chain becomes a growing knowledge palace.
  prerequisite: P1 Chronicler must ship first
  phase: 6-7

SELF_UPGRADING_META:
  concept: Agent observes workflows, crystallizes skills, self-refines.
  classification: CARPARK (constitutional muzzle must stay TIGHT)
  risk: Highest authority drift risk — park until trust earned over months
```

---

## KNOWN GAPS

```yaml
critical:
  - Chronicler not implemented (beads unbounded — P1 URGENT)
  - Queue writes non-atomic (crash corruption risk — P5)
  - 2.1% rejection rate (Auditor too lenient — P4)

operational:
  - 2 injection false positives (ICT speech patterns: Ep13, Ep19)
  - Matrix alerts cosmetic warning (non-blocking)
  - Sync pipeline won't scale past 100+ videos
  - Daemon mode not configured (manual TMUX + Amphetamine)

pending_implementation:
  - Runaway guards (P6 — turn cap, cost ceiling, watchdog)
  - Researcher role (Perplexity — defer until curriculum)
  - Developer role (backtest code generation — far horizon)
```

---

## WATCH_OUTS

### Security
- Run `injection_guard.py` on ALL external inputs
- Flag to Auditor if similarity > 0.85 to attack vectors
- No pip installs beyond requirements.txt without audit

### Persistence
- Docker volumes for `/memory`, `/bundles`
- `--restart unless-stopped` on sandbox container

### Deps
- Audit new skills via security review before integration
- Prefer stdlib over new dependencies

---

## FRONTIER PATTERNS

### Inverse Loop
- Feed Auditor rejects back to Theorist via NEGATIVE_BEADs
- Recent negatives (last 10) prefix Theorist context

### Async Delegates
- `perplexity.py`: poll every 60s, non-blocking (SCOPED, not built)
- Fallback to `exa.py` if latency > 3min

### Self-Evolution (Human-Gated)
- After 5 bundles: Auditor MAY propose 1-2 prompt tweaks
- Proposals logged to channel; NO hot-reload without human approval

---

## PHASE EXECUTION

Current: OPERATIONAL_MVP → Post-Advisor Synthesis (2026-02-04)

Active Priorities (see `docs/SPRINT_ROADMAP.md`):
- P1: Chronicler implementation (URGENT — memory unbounded)
- P2: Back-propagation seam (Olya NO → NEGATIVE_BEAD → Theorist)
- P3: Scope constraint (BLOCKED — awaiting CSO curriculum)
- P4: Auditor prompt hardening (target 10% rejection floor)
- P5: Queue atomicity (write-tmp + rename pattern)
- P6: Runaway guards (turn cap + cost ceiling + watchdog)

On task complete:
1. Run tests
2. Git commit + push
3. Update DEXTER_MANIFEST.md NEXT_ACTIONS
4. Report to channel
5. Await CTO/Human gate before next priority

---

## COMMS

- CTO (Claude Web): Strategic oversight, lateral checks
- Human (G): Final authority, capital decisions, promotion gates
- Channel: Status updates, bundle alerts, drift warnings

---

## ADVISOR RULINGS (2026-02-04)

```yaml
promotion_states:
  ruling: Binary CLAIM/FACT (GPT wins)
  rejected: OWL's PROVISIONAL_FACT (gray authority risk)
  adopted: OWL's provenance chain (FACT encapsulates source CLAIM_ID)

calibration_protocol:
  - Default state = REJECT (approval requires explicit action)
  - Delta input ≥1 parameter per 5 signatures (proves engagement)
  - View separation (Dexter vs Perplexity shown separately)
  - Foils optional (operator-configurable)

auditor_sequence:
  1: Prompt harden first
  2: Monitor rejection rate
  3: Third family (Llama/Qwen) if still <5%

atom_budget:
  recommendation: 32-48 features across 5 drawers
  breakdown:
    HTF_bias: 8-12
    structure: 12-18
    timing_session: 4-6
    volatility_regime: 4-6
    risk_context: 4-6
```

---

## CRITICAL REFERENCES

| Document | Location | Purpose |
|----------|----------|---------|
| COLD_START.md | docs/ | Quick orientation for new CTO |
| SPRINT_ROADMAP.md | docs/ | Current priorities P1-P6 |
| DEXTER_MANIFEST.md | docs/ | Operational status + evidence |
| DEXTER_ROADMAP_v0.2.md | docs/ | Build history (phases 0-5) |
| POST_S44_SYNTHESIS_v0.1.md | docs/ | Advisor synthesis source |
| addendum_from_CTO_Opus_Review.md | docs/ | Seed ideas (Olya_Manifest) |

---

*Human frames. Machine computes. Human promotes.* 🔬
