# DREAM CYCLE DESIGN INTENT

```yaml
document: DREAM_CYCLE_DESIGN_INTENT
version: 0.1
date: 2026-02-21
status: DESIGN_INTENT — approved concept, not build scope until Gate 5+
authors: G (Sovereign Operator) + CTO (Dexter) + GPT (Advisor) + Owl (Advisor)
purpose: |
  Capture the analytical lens the Dream Cycle will apply to the Bead Field.
  Prevents future sessions from baking scalar scoring into the substrate.
  Preserves the LeCun/JEPA conceptual alignment for when DGX build begins.
relationship:
  parent: a8ra_MASTER_PLAN_v0.1 (Section 4, Phase 3)
  sibling: BEAD_FIELD_SPEC_v0.3 (the data this analyzes)
  scope: Gate 5+ (Dream Cycle v1). NOT Gate 1 scope.
hardware: DGX Spark (Grace-Blackwell) — ARRIVED 2026-02-21, standing by
```

---

## 0. WHY THIS DOCUMENT EXISTS

```yaml
CONTEXT: |
  During Gate 1 planning, a "Data as Physics" concept surfaced:
  assign scalar Energy values (0.0-1.0) to beads based on logical tension,
  predictive drift, and lineage weakness. Store energy on beads. Use thresholds
  for automated promotion to Governance.
  
  Three-advisor pressure test produced unanimous verdict:
  - The physics framing is VALID (the architecture already has this shape)
  - Storing energy ON beads is REJECTED (violates INV-NO-GRADES, softens constitution)
  - Computing energy OVER beads in Dream Cycle is ACCEPTED (diagnostic, not doctrine)
  - Automated promotion from energy thresholds is REJECTED (violates INV-HUMAN-FRAMES)

DECISION: |
  DEC-ENERGY-NOT-STORED:
  "Energy/coherence is COMPUTED over the Bead Field by the Dream Cycle.
   It is NEVER stored as a bead attribute. The substrate remains hard,
   binary, signed, and immutable. The Dream Cycle is the scientist
   who studies the ledger; the ledger itself carries no opinions."

  This decision is CANONICAL. Future sessions must not add scalar scoring
  fields to the Bead Field schema without G approval and three-office review.
```

---

## 1. THE CONCEPTUAL ALIGNMENT

### 1.1 LeCun / JEPA Parallel

```yaml
THESIS: |
  Yann LeCun's core argument: generative models (predict tokens) are fragile.
  Energy-based models (score configurations) are robust. JEPA predicts
  latent world states, not surface observations. Model Predictive Control
  plans in latent space before acting.

  a8ra's architecture independently converged on the same shape:

ALIGNMENT_MAP:
  world_model: "Bead Field — bi-temporal state of all system knowledge"
  latent_state: "Bead configuration at any (WT, KT) slice"
  energy_landscape: "Rejection topology — the Shadow Field"
  jepa: "Dream Cycle predicts bead configurations, not price ticks"
  mpc: "Analytical economy simulates before Governance executes"
  regularization: "Shadow Field IS the negative space — structural, not constructed"

KEY_DISTINCTION: |
  LeCun's energy function scores configurations in a learned latent space.
  Our "energy" is computed from structured, signed, provenance-linked beads.
  We don't need learned embeddings to detect tension — we have explicit
  lineage chains, bi-temporal ranges, and categorical rejection reasons.
  
  The Bead Field gives us what embeddings approximate: structured relationships
  between knowledge units with verifiable provenance. This is stronger than
  latent space because it's auditable.
```

### 1.2 Why This Matters

```yaml
IMPLICATION: |
  The DGX Spark's primary value is NOT running LLMs.
  It is running structured simulation over the Bead Field:
  - Counterfactual replay of rejected proposals
  - Synthetic regime injection (noise, latency, liquidity perturbation)
  - Stability analysis across market conditions
  - Adversarial strategy testing (GALILEO)

  The Bead Field provides the substrate (hard, signed, immutable data).
  The DGX provides the compute (fluid, experimental, disposable analysis).
  
  This is the Two-Economy model applied to hardware:
  M3 Ultra = Knowledge (Economy 2 store, hard)
  DGX Spark = Compute (Economy 2 analysis, fluid)
```

---

## 2. THE LAW vs THE SCIENCE

```yaml
THE_LAW (Governance Economy — Phoenix):
  properties: Deterministic, binary, state-machine
  decisions: ACTIVE or HALTED. PASS or FAIL. Signed or rejected.
  promotion: Human gate. Always. No exceptions.
  motto: "Once signed, it's law."

THE_SCIENCE (Analytical Economy — Bead Field + Dream Cycle):
  properties: Rich, mineable, experimental, allowed to be wrong
  substrate: Hard (beads are signed, immutable, bi-temporal)
  analysis: Fluid (Dream Cycle computes over beads, results are disposable)
  motto: "Every bead is a sensor reading. Mine everything."

THE_BOUNDARY: |
  The Bead Field is the HARD part of the Science.
  The Dream Cycle is the FLUID part of the Science.
  
  Beads are commitments (permanent record).
  Dream Cycle analytics are observations (disposable computation).
  
  Energy/tension/coherence lives in the fluid layer.
  The hard layer carries no opinions about its own contents.
  
  This is the same pattern as physics:
  Particles don't know their energy. Energy is a property of their
  configuration within a field. The field equations compute it.
  The particles just exist.
```

---

## 3. DIAGNOSTIC DIMENSIONS (Dream Cycle Analytical Lens)

These are the "forces" the Dream Cycle will compute over the Bead Field. They are NOT stored on beads. They are computed at query time during Dream Cycle sessions.

### 3.1 Logical Coherence (C_l)

```yaml
what: Binary contradiction detection within bi-temporal slices
method: |
  Rule-based, deterministic, enum-output.
  Query: "Are there CLAIM beads and FACT beads in the same WT window
  that assert contradictory states?"
examples:
  - CLAIM "HTF bias is bullish" + FACT "Weekly MSS broke bearish" in same session
  - CLAIM "Regime is trending" + FACT "ADX < 20" in same observation window
output: CONTRADICTION_DETECTED | COHERENT
action: CONTRADICTION_DETECTED → cluster flagged for forensic mining

NOT:
  - Not vector similarity
  - Not embedding distance
  - Not fuzzy matching
  - Not a scalar score
  
rationale: |
  Contradictions are structural, not probabilistic.
  Two signed beads either assert conflicting states or they don't.
  The answer is binary. The mining that follows is rich.
```

### 3.2 Predictive Fidelity (F_p)

```yaml
what: Delta between PROPOSAL expectations and actual outcomes
method: |
  Measurable, objective, quantifiable.
  Already mandated by INV-EXECUTION-FIDELITY.
  Compare: PROPOSAL.entry_price vs actual fill.
  Compare: SIGNAL predicted direction vs market outcome.
  Compare: SKILL predicted R:R vs realized R:R.
output: Structured delta record (not a score — the actual numbers)
action: High delta → triggers refinery recalibration analysis

safe_to_quantify: true
rationale: |
  This is measurement, not judgment. The delta between "what we predicted"
  and "what happened" is objective data. It feeds the Dream Cycle's
  counterfactual engine. It does NOT become a quality score on the bead.
  The bead records what was proposed. The Dream Cycle records what happened.
```

### 3.3 Veto Density (V_d)

```yaml
what: Frequency of human/governance rejection per pattern cluster
method: |
  Query PROPOSAL_REJECTED beads grouped by pattern type, concept cluster,
  regime context. Count rejections per cluster over time windows.
output: Density map (rejections per cluster per time window)
action: High density = unstable hypothesis → priority mining target

interpretation: |
  If Olya vetoes the same pattern type repeatedly, the system's understanding
  of that pattern is wrong. High veto density is the strongest signal
  that the Dream Cycle should investigate.
  
  Conversely, LOW veto density on a pattern that later fails is a
  calibration gap — the system was confident but wrong. Also high-value mining.
```

### 3.4 Regime Sensitivity (R_s)

```yaml
what: How much a SKILL's validity changes across regime transitions
method: |
  Counterfactual simulation on DGX.
  Take a validated SKILL. Replay it across:
  - Historical regime transitions (trending → ranging → volatile)
  - Synthetic perturbations (+200ms latency, -50% liquidity, ±spread widening)
  - Noise injection (random data corruption at various levels)
output: Robustness profile per SKILL (structured report, not a scalar)
action: |
  Regime-dependent SKILLs get tagged with regime constraints.
  Regime-robust SKILLs are higher-value for promotion consideration.
  
hardware: DGX Spark primary workload (Monte Carlo simulation at scale)
gate: Gate 5+ (requires sufficient SKILL volume + historical data)
```

### 3.5 Lineage Integrity (L_i)

```yaml
what: Provenance chain verification depth and completeness
method: |
  Binary pass/fail on chain verification (INV-BEAD-SIGNED, INV-BEAD-IMMUTABLE).
  But DEPTH of verified chain is informative for mining priority.
output: VERIFIED (depth N) | BROKEN (at bead X)
action: |
  Broken lineage → invariant failure → bead flagged (not scored)
  Shallow lineage (verified but short) → lower mining priority
  Deep lineage (verified, many ancestors) → higher mining value
  
NOT_A_SCORE: |
  Lineage either verifies or it doesn't. Binary.
  Depth is a count, not a quality score.
  A bead with lineage depth 2 is not "worse" than depth 10.
  It just has less analytical surface for the Dream Cycle to mine.
```

---

## 4. WHAT THE DGX ACTUALLY DOES (Gate 5+ Vision)

```yaml
DREAM_CYCLE_PIPELINE:
  
  phase_1_load:
    action: "Librarian loads PROPOSAL_REJECTED beads + full lineage context"
    source: Bead Field on M3 Ultra (read replica on DGX)
    scope: Shadow Field (all rejections) + success trajectories (executed proposals)
    
  phase_2_diagnose:
    action: "Compute diagnostic dimensions over loaded bead clusters"
    dimensions: [logical_coherence, predictive_fidelity, veto_density, regime_sensitivity]
    output: Diagnostic report per cluster (structured, not scalar)
    hardware: DGX Spark
    
  phase_3_simulate:
    action: "Counterfactual replay — 'In what universe would this have been correct?'"
    method: |
      For each high-tension cluster:
      - Replay with original conditions → confirm failure
      - Replay with perturbed conditions → find stability boundaries
      - Replay with synthetic regimes → test generalization
      - Replay with noise injection → test robustness
    scale: "10,000 simulations per cluster (DGX PFLOP earns its keep here)"
    hardware: DGX Spark (primary compute workload)
    
  phase_4_distill:
    action: "SkillRL — distill failure trajectories into SKILL candidates"
    method: |
      Identify the minimal adjustment to system parameters that would have
      converted a high-tension failure into a low-tension success.
      Express as structured IF-THEN SKILL bead.
    output: SKILL beads with validation_status = CANDIDATE
    
  phase_5_validate:
    action: "Human validates SKILL candidates"
    gate: Olya reviews. Her NO is absolute. INV-OLYA-ABSOLUTE.
    promotion: CANDIDATE → VALIDATED (human gate, never automated)
    
  phase_6_condition:
    action: "Validated SKILLs condition future agent behavior"
    bridge: Economy 2 → Economy 1 via INV-BRIDGE-PROMOTION-GATE
    constraint: "SKILL.validation_status must be VALIDATED before conditioning"

JEPA_ALIGNMENT: |
  The DGX predicts "what bead configuration would result from this action"
  NOT "what price will EURUSD be tomorrow."
  
  This is world modeling over signed, structured data.
  Not generative prediction over noisy token streams.
  
  The DGX asks: "If I propose a short at this level, given this bead state,
  what is the likely rejection category?" That's JEPA-like prediction
  in the bead configuration space.
```

---

## 5. ANTI-PATTERNS (What This Is NOT)

```yaml
ANTI_PATTERN_1:
  name: "Energy Score on Beads"
  description: "Store a 0.0-1.0 scalar on every bead"
  why_rejected: |
    Violates INV-NO-GRADES. Turns the ledger into a "maybe-ledger."
    Beads are commitments, not hypotheses with confidence intervals.
    
ANTI_PATTERN_2:
  name: "Automated Promotion via Energy Threshold"
  description: "If Energy < 0.2, auto-promote to Governance"
  why_rejected: |
    Violates INV-HUMAN-FRAMES and INV-BRIDGE-PROMOTION-GATE.
    Replaces Olya with a formula. The human gate is the moat, not overhead.
    
ANTI_PATTERN_3:
  name: "Fuzzy Contradiction Detection"
  description: "Use embedding similarity to detect 'soft' contradictions"
  why_rejected: |
    Contradictions in signed, structured data are deterministic.
    Two beads either assert conflicting states or they don't.
    Embedding similarity introduces false positives and unauditable reasoning.
    
ANTI_PATTERN_4:
  name: "Lineage Quality Score"
  description: "Score provenance chains on a continuous scale"
  why_rejected: |
    Lineage verifies or it doesn't. Binary invariant (INV-BEAD-SIGNED).
    Depth is a count, useful for mining priority. Not a quality judgment.
    
ANTI_PATTERN_5:
  name: "Dream Cycle Writes Energy to Bead Field"
  description: "Store Dream Cycle analytics as bead attributes"
  why_rejected: |
    Dream Cycle output is SKILL beads (structural, signed, permanent).
    Analytics/diagnostics are ephemeral computation, not commitments.
    The Three-Layer Model is clear: analytics = Layer 1 (Ephemeral).
    Only SKILL candidates cross to Layer 2 (Structural) via commit().
```

---

## 6. RELATIONSHIP TO GATE 1

```yaml
GATE_1_IMPACT: ZERO

The COO brief for Gate 1 is correct as written:
- 8 bead type schemas (no energy fields)
- SQLite bi-temporal store (no scoring columns)
- Hash chain + Merkle + dual signing
- Genesis Snapshot ceremony
- 200+ tests

This document captures DESIGN INTENT for Gate 5+.
It does NOT add scope to Gate 1.
It prevents future scope creep by documenting the decision boundary.

WHAT_GATE_1_BUILDS_THAT_ENABLES_THIS:
  - Rich PROPOSAL_REJECTED schema → Dream Cycle fuel
  - Bi-temporal queries → temporal slice analysis
  - Lineage chains → provenance walks for mining
  - Merkle proofs → integrity verification at scale
  - Tags array → flexible clustering for diagnostic grouping

The substrate is built for mining. The mining comes later.
```

---

## 7. DECISION LOG

```yaml
- date: 2026-02-21
  decision: DEC-ENERGY-NOT-STORED
  ruling: |
    Energy/coherence is COMPUTED over the Bead Field by the Dream Cycle.
    Never STORED as a bead attribute. Substrate remains hard, binary, signed.
  advisors: GPT (proposed boundary), Owl (refined landing), CTO (synthesis)
  approved_by: G
  
- date: 2026-02-21
  decision: DEC-JEPA-ALIGNMENT
  ruling: |
    Dream Cycle predicts bead configurations, not price ticks.
    This is world modeling over structured data, not generative prediction.
    LeCun/JEPA framing validated as conceptual alignment, not implementation spec.
  advisors: G (insight originator), GPT (validation), Owl (physics parallel)
  approved_by: G
  
- date: 2026-02-21
  decision: DEC-DIAGNOSTICS-EPHEMERAL
  ruling: |
    Dream Cycle diagnostic outputs (coherence, fidelity, veto density,
    regime sensitivity) are ephemeral computation. Only SKILL candidates
    cross the Commitment Threshold to become structural beads.
  source: Three-Layer Model (BEAD_FIELD_SPEC_v0.3 Section 2)
  approved_by: G

- date: 2026-02-21
  note: DGX Spark (Grace-Blackwell) arrived. Standing by for Gate 5+ compute role.
```

---

## 8. CANONICAL DOCUMENT SET (Updated)

```yaml
STRATEGIC:
  a8ra_MASTER_PLAN_v0.1: World view, Two-Economy model, Pulse, Bridge
  DREAM_CYCLE_DESIGN_INTENT_v0.1: THIS FILE — what the DGX does with the data

TECHNICAL:
  BEAD_FIELD_SPEC_v0.3: Data constitution (bead schema, invariants)
  
OPERATIONAL:
  a8ra_SYSTEM_MANIFEST_v1.0: Cross-system orientation
  COO_BRIEF_GATE_1.md: Build instructions for substrate

FUTURE (planned):
  BRIDGE_SPEC.md: Governance↔Analytical projection contract
  REFINERY_CONTRACT.yaml: Production data philosophy
  DREAM_CYCLE_SPEC.md: Full Gate 5 implementation spec (extends this document)
```

---

```yaml
DESIGN_PRINCIPLE: |
  The Bead Field is the hard ledger. The Dream Cycle is the scientist.
  The ledger carries no opinions. The scientist computes all opinions.
  The human decides which opinions become law.
  
  Keep Governance crisp. Let Analytical be fluid.
  That tension is the edge.
```

*Particles don't know their energy. The field equations compute it.* 🔬⚡
