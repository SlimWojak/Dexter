# PHOENIX_MANIFEST.md

> "Anthropic is discovering the same law from the opposite direction.
> They started with UI → struggling toward truth.
> You started with truth → earned UI.
> That asymmetry is everything."
> — GPT synthesis, 2026

> "Beads are the town's records – inhabitants forget, town remembers."
> — Yegge (via GROK)

> "UI is a projection of state, not a participant in reasoning."

---

## 1. IDENTITY

```yaml
project: Phoenix / WarBoar
purpose: Constitutional trading system
status: S44_COMPLETE | POST_S44_FREEZE | CSO_PRODUCTION_READY | S33_P2_BLOCKED (Olya — unblock via COE)
block_complete: S35-S44 (CONSTITUTIONAL_CEILING + SLEEP_SAFE + WARBOAR_AWAKENS + TRUST_CLOSURE + FOUNDATION_VALIDATED)
s44_completion_date: 2026-02-04
current_sprint: S47_PENDING (Lease Implementation — unblocked)
certification: WARBOAR_CERTIFIED | LIVE_GATEWAY_VALIDATED | CSO_PRODUCTION_READY | S44_FOUNDATION_VALIDATED
relationship: Sibling to God_Mode (forge builds tools, Phoenix protects capital)
sibling_system: Dexter (Sovereign Evidence Refinery — ICT extraction, separate Mac Mini)
canonical_fate: docs/DEFINITIVE_FATE.yaml
total_tests: 1500+ (28 xfailed)
total_invariants: 105+
total_chaos_vectors: 224
gate_glossary: 48 gates mapped

INV-NO-CORE-REWRITES-POST-S44: ACTIVE
  rule: "After live validation, no architectural rewrites. Only tightening, surfacing, governance."
  enforced_since: 2026-02-04
```

## 1b. NON-GOALS

```yaml
- NOT an AI trader (logic lives in CSO + operator)
- NOT a dashboard (no control surfaces)
- NOT a strategy generator
- NOT self-improving without human oversight
- NOT a recommendation engine (system never says "I noticed")
- NOT an authority on meaning (human frames, machine computes)
```

---

## 2. ARCHITECTURE_TOPOLOGY

### MODULES

```yaml
governance/:
  purpose: Halt, invariants, kill flags
  authority: ABSOLUTE

brokers/ibkr/:
  purpose: IBKR connection, guards, session beads
  authority: GATED (T2 required)

cso/:
  purpose: CSE validation, signal routing (gate status, not grades)
  authority: READ_ONLY (consumes, never generates)

orientation/:
  purpose: Machine-verifiable system state checksum
  authority: COMPUTED (aggregation only)

widget/:
  purpose: Verbatim state projection
  authority: NONE (read-only surface)

approval/:
  purpose: T2 evidence display
  authority: PRESENTATION_ONLY

daemons/:
  purpose: File seam spine
  authority: ROUTING_ONLY

# S35-S39 (COMPLETE)
cfp/:
  purpose: Conditional Fact Projector
  authority: COMPUTED (conditional facts only, no causal claims)
  status: S35_COMPLETE ✓
  tests: 62

cso/:
  purpose: Gate status (facts, not grades)
  authority: READ_ONLY (consumes, never generates grades)
  status: S36_COMPLETE ✓
  tests: 45

athena/:
  purpose: Memory discipline (CLAIM/FACT/CONFLICT beads)
  authority: STORAGE_ONLY (no doctrine mutation)
  status: S37_COMPLETE ✓
  tests: 51

hunt/:
  purpose: Exhaustive variant computation
  authority: COMPUTE_ONLY (human-declared grids, no selection)
  status: S38_COMPLETE ✓
  tests: 69

validation/:
  purpose: Research validation suite (decomposed outputs)
  authority: COMPUTE_ONLY (no viability scores, no verdicts)
  status: S39_COMPLETE ✓
  tests: 109
  codename: CONSTITUTIONAL_CEILING

# S40 (COMPLETE)
governance/circuit_breaker.py:
  purpose: Circuit breaker FSM (CLOSED→OPEN→HALF_OPEN)
  authority: SELF_HEALING
  status: S40_COMPLETE ✓
  
governance/backoff.py:
  purpose: Exponential backoff with jitter
  authority: RETRY_CONTROL
  status: S40_COMPLETE ✓
  
governance/health_fsm.py:
  purpose: Health state machine (HEALTHY→DEGRADED→CRITICAL→HALTED)
  authority: HEALTH_MONITORING
  status: S40_COMPLETE ✓
  
governance/runtime_assertions.py:
  purpose: Constitutional assertions at runtime boundaries
  authority: RUNTIME_ENFORCEMENT
  status: S40_COMPLETE ✓
  
brokers/ibkr/supervisor.py:
  purpose: Shadow supervisor OUTSIDE trading loop
  authority: WATCHDOG
  status: S40_COMPLETE ✓
  
brokers/ibkr/heartbeat.py:
  purpose: Connector liveness monitoring
  authority: HEARTBEAT
  status: S40_COMPLETE ✓
  
brokers/ibkr/degradation.py:
  purpose: Graceful degradation cascade (T2→T1→T0)
  authority: DEGRADATION
  status: S40_COMPLETE ✓
  
narrator/:
  purpose: Template-based state projection (boar dialect)
  authority: PROJECTION_ONLY (facts, no synthesis)
  status: S40_COMPLETE ✓
  
tools/hooks/:
  purpose: Pre-commit constitutional enforcement
  authority: BUILD_TIME_ENFORCEMENT
  status: S40_COMPLETE ✓

# S41 (COMPLETE)
slm/:
  purpose: SLM classification API (rule-based guard dog)
  authority: CLASSIFICATION_ONLY (no state mutation)
  status: S41_COMPLETE ✓

governance/slm_boundary.py:
  purpose: ContentClassifier + @slm_output_guard
  authority: HERESY_DETECTION
  status: S41_COMPLETE ✓
  
narrator/renderer.py:
  purpose: narrator_emit() single chokepoint
  authority: EMISSION_GATE
  status: S41_COMPLETE ✓

narrator/surface.py:
  purpose: Human-readable formatters (gate facts, degraded states)
  authority: PRESENTATION_ONLY
  status: S41_COMPLETE ✓

notification/alert_taxonomy.py:
  purpose: Alert one-liner formatters with severity emojis
  authority: NOTIFICATION_FORMATTING
  status: S41_COMPLETE ✓

# S42 (COMPLETE)
cso/knowledge/GATE_GLOSSARY.yaml:
  purpose: Gate name → drawer location + meaning (48 gates)
  authority: CSO_REFERENCE
  status: S42_COMPLETE ✓

state/health_writer.py:
  purpose: CSO-readable health file generator
  authority: OBSERVABILITY
  status: S42_COMPLETE ✓

cso/knowledge/CSO_HEALTH_PROMPT.md:
  purpose: Health file consumption instructions for CSO
  authority: CSO_GUIDANCE
  status: S42_COMPLETE ✓

docs/OPERATOR_INSTRUCTIONS/:
  purpose: Operator expectations and boundaries
  authority: OPERATOR_GUIDANCE
  status: S42_COMPLETE ✓
```

### DAEMONS

```yaml
watcher.py: Intent routing | FILE_SEAM_SPINE
lens.py: Response injection | FILE_SEAM_SPINE
menu_bar.py: Surface renderer | READ_ONLY
```

### FILE_SEAM

```yaml
intents:
  path: /intents/incoming/ → watcher → workers
responses:
  path: /responses/ → lens → Claude
state:
  path: /state/orientation.yaml → surface renderer
```

### DATA_FLOW

```yaml
River → Enrichment → CSO → CSE → Approval → Execution

nodes:
  river/: BUILT
  cso/scanner.py: BUILT
  cso/consumer.py: BUILT
  approval/evidence.py: BUILT
  execution/: STUB
  brokers/ibkr/: BUILT (paper mode)
  cfp/: S35_COMPLETE ✓
  cso_harness/: S36_COMPLETE ✓
  athena/: S37_COMPLETE ✓
  hunt/: S38_COMPLETE ✓
  validation/: S39_COMPLETE ✓

validation_flow:
  River → CFP (conditional facts) → Athena (memory) → Hunt (grid) → Validation (decomposed)
```

---

## 3. CONTRACTS_AND_SEAMS

```yaml
cse_schema.yaml:
  status: PROVEN (mock ↔ production validated)
  path: schemas/cse_schema.yaml

orientation_bead.yaml:
  status: PROVEN (machine-verifiable)
  path: schemas/orientation_bead.yaml

5_drawer_interface:
  status: PROVEN (whitelist only)
  path: cso/knowledge/conditions.yaml

t2_token_contract:
  status: PROVEN (single-use, 5min expiry)
  path: schemas/t2_token.yaml

ibkr_connector:
  status: PROVEN (paper mode)
  path: brokers/ibkr/connector.py

bead_schema:
  status: BUILT (14 types)
  path: schemas/beads.yaml
  s37_additions: [CLAIM_BEAD, FACT_BEAD, CONFLICT_BEAD]

INV-D4-NO-DERIVATION-1:
  status: PROVEN (verbatim projection contract)
  test: drills/d4_verification.py
```

---

## 4. INVARIANTS_PROVEN

### FOUNDATION (S28-S34)

```yaml
# HALT
INV-HALT-1: "halt_local() completes < 50ms"
  test: tests/test_halt_latency.py
  enforcement: governance/halt.py halt_local()
  measured: 0.15ms typical

INV-HALT-2: "cascade halt completes < 500ms"
  test: tests/test_halt_propagation_multiprocess.py
  enforcement: halt_cascade() in governance/halt.py

# FILE_SEAM
INV-D1-WATCHER-1: "exactly-once processing per intent"
  test: tests/daemons/test_watcher_exactly_once.py
  enforcement: watcher.py deduplication

INV-D1-LENS-1: "≤50 tokens context injection"
  test: tests/daemons/test_lens_context_cost.py
  enforcement: lens.py truncation

# ORIENTATION
INV-D3-CHECKSUM-1: "orientation is machine-verifiable, no prose"
  test: drills/d3_negative_test.py
  enforcement: orientation/validator.py

INV-D3-CORRUPTION-1: "corruption triggers STATE_CONFLICT"
  test: drills/d3_negative_test.py
  enforcement: hash mismatch detection

# SURFACE
INV-D4-GLANCEABLE-1: "widget update < 100ms"
  test: drills/d4_verification.py
  enforcement: surface_renderer.py

INV-D4-NO-DERIVATION-1: "verbatim fields only, no computed display"
  test: drills/d4_verification.py
  enforcement: whitelist field projection

INV-D4-EPHEMERAL-1: "no local persistence in widget"
  test: drills/d4_verification.py
  enforcement: widget reads state/, never writes

# IBKR
INV-IBKR-PAPER-GUARD-1: "live mode blocked without IBKR_ALLOW_LIVE=true"
  test: tests/test_no_live_orders.py
  enforcement: IBKRConfig.allow_live flag

INV-IBKR-ACCOUNT-CHECK-1: "account validation on connect"
  test: tests/chaos/test_bunny_s33_p1.py
  enforcement: connector.py account match check

# T2
INV-T2-TOKEN-1: "single-use, 5min expiry"
  test: tests/test_tier_gates.py
  enforcement: t2_token.py expiry logic

INV-T2-GATE-1: "no order submission without valid T2 token"
  test: tests/test_halt_blocks_t2_action.py
  enforcement: tier_gates.py require_t2_token()
```

### ATTRIBUTION (S35 CFP) ✓

```yaml
INV-ATTR-CAUSAL-BAN: "No causal claims; only conditional facts"
  test: tests/test_cfp/test_causal_ban_linter.py
  enforcement: cfp/causal_ban_linter.py

INV-ATTR-PROVENANCE: "All outputs include query_string + dataset_hash + bead_id"
  test: tests/test_cfp/test_executor.py::TestProvenance
  enforcement: CFPResult dataclass required fields

INV-ATTR-NO-RANKING: "No ranking, no best/worst, no implied priority"
  test: tests/chaos/test_bunny_s35.py
  enforcement: ScalarBanLinter ranking patterns

INV-ATTR-SILENCE: "System surfaces conflicts, never resolves"
  test: tests/test_cfp/test_conflict_display.py
  enforcement: CONFLICT_BEAD type, no resolution field

INV-ATTR-NO-WRITEBACK: "Stored facts cannot mutate doctrine"
  test: tests/test_athena/test_store.py
  enforcement: BeadStore append-only

INV-ATTR-CONFLICT-DISPLAY: "When showing best, must show worst alongside"
  test: tests/test_cfp/test_conflict_display.py
  enforcement: paired extremes requirement
```

### HARNESS (S36) ✓

```yaml
INV-HARNESS-1: "CSO outputs gate status only, never grades"
  test: tests/test_cso/test_evaluator.py
  enforcement: GateStatus enum, no grade fields

INV-HARNESS-2: "No confidence scores unless explicit formula"
  test: tests/test_cso/test_bit_vector.py
  enforcement: gates_passed[] only, no confidence

INV-HARNESS-3: "Alerts fire on gate combinations, not quality"
  test: tests/test_cso/test_alerts.py
  enforcement: alert triggers on gate_count threshold

INV-HARNESS-4: "Multi-pair sorted alphabetically by default"
  test: tests/test_cso/test_multi_pair.py
  enforcement: sorted() on pair names

INV-NO-GRADE-RECONSTRUCTION: "No A/B/C/D/F grades anywhere"
  test: tests/chaos/test_bunny_s36.py
  enforcement: ScalarBanLinter grade patterns
```

### MEMORY (S37) ✓

```yaml
INV-CLAIM-FACT-SEPARATION: "Claims and facts are distinct bead types"
  test: tests/test_athena/test_bead_types.py
  enforcement: CLAIM_BEAD vs FACT_BEAD enums

INV-CONFLICT-NO-RESOLUTION: "System flags conflicts, never resolves"
  test: tests/chaos/test_bunny_s37.py
  enforcement: CONFLICT_BEAD.resolution = None

INV-MEMORY-PROVENANCE: "All memories have full provenance chain"
  test: tests/test_athena/test_store.py
  enforcement: bead_id + dataset_hash required
```

### HUNT (S38) ✓

```yaml
INV-HUNT-EXHAUSTIVE: "Hunt computes ALL declared variants, never selects"
  test: tests/test_hunt/test_executor.py
  enforcement: grid.compute_all() returns full table

INV-HUNT-BUDGET: "Compute/token cap enforced per run"
  test: tests/test_hunt/test_budget.py
  enforcement: BudgetEnforcer.check()

INV-HUNT-NO-SURVIVOR-RANKING: "No 'best performer' rankings"
  test: tests/chaos/test_bunny_s38.py
  enforcement: ScalarBanLinter ranking patterns

INV-HUNT-NO-SELECTION: "Grid returns full table, never filters"
  test: tests/test_hunt/test_output.py
  enforcement: exhaustive flag enforced
```

### VALIDATION (S39) ✓ — CONSTITUTIONAL CEILING

```yaml
INV-SCALAR-BAN: "No composite scores (0-100); decompose to factors"
  test: tests/test_validation/test_scalar_ban_linter.py
  enforcement: validation/scalar_ban_linter.py

INV-NO-AGGREGATE-SCALAR: "No avg_* fields; return full arrays"
  test: tests/test_validation/test_cross_module_audit.py
  enforcement: AVG_PATTERNS in linter

INV-NEUTRAL-ADJECTIVES: "No evaluative words (strong, weak, robust)"
  test: tests/chaos/test_bunny_s39.py
  enforcement: ADJECTIVE_PATTERNS in linter

INV-VISUAL-PARITY: "No color metadata (red=bad, green=good)"
  test: tests/chaos/test_bunny_s39.py
  enforcement: COLOR_METADATA_PATTERNS

INV-NO-IMPLICIT-VERDICT: "Mandatory disclaimer on all outputs"
  test: tests/test_validation/test_walk_forward.py
  enforcement: disclaimer injection

INV-CROSS-MODULE-NO-SYNTH: "Chain outputs remain decomposed"
  test: tests/chain/test_cfp_validation_chain.py
  enforcement: chain validation suite
```

### SELF-HEALING (S40) ✓

```yaml
INV-CIRCUIT-1: "OPEN circuit blocks all requests"
  test: tests/test_self_healing/test_circuit_breaker.py::TestCircuitBreakerOpenState
  enforcement: CircuitOpenError raised on call()

INV-CIRCUIT-2: "HALF_OPEN allows exactly 1 probe"
  test: tests/test_self_healing/test_circuit_breaker.py::TestHalfOpenProbe
  enforcement: _probe_in_progress flag blocks concurrent probes

INV-BACKOFF-1: "Retry interval doubles each attempt"
  test: tests/test_self_healing/test_backoff.py::TestExponentialGrowth
  enforcement: formula: min(base * 2^attempt + jitter, max)

INV-BACKOFF-2: "Interval capped at max (300s)"
  test: tests/test_self_healing/test_backoff.py::TestMaxCap
  enforcement: max_delay parameter enforced

INV-HEALTH-1: "CRITICAL → alert callback invoked"
  test: tests/test_self_healing/test_health_fsm.py::TestCriticalAlert
  enforcement: alert_callback fired on state transition

INV-HEALTH-2: "HALTED → halt_callback invoked"
  test: tests/test_self_healing/test_health_fsm.py::TestHaltedCallback
  enforcement: halt_callback fired on HALTED transition

INV-HEAL-REENTRANCY: "N failures in 1s → ≤N/cooldown alerts"
  test: tests/test_self_healing/test_health_fsm.py::TestAlertCooldown
  enforcement: alert_cooldown suppresses rapid-fire alerts
```

### IBKR RESILIENCE (S40) ✓

```yaml
INV-IBKR-FLAKEY-1: "3 missed heartbeats → DEAD declaration"
  test: tests/test_ibkr/test_heartbeat.py::TestMissThreshold
  enforcement: is_alive returns False after miss_threshold

INV-IBKR-FLAKEY-2: "Supervisor survives connector crash"
  test: tests/test_ibkr/test_supervisor.py::TestSupervisorSurvival
  enforcement: supervisor runs in separate thread

INV-IBKR-FLAKEY-3: "Reconnection requires validation"
  test: tests/test_ibkr/test_degradation.py::TestRestoreRequiresValidation
  enforcement: restore() requires health check pass

INV-IBKR-DEGRADE-1: "T2 blocked within 1s of disconnect"
  test: tests/test_ibkr/test_degradation.py::TestT2BlockTiming
  enforcement: trigger_degradation() immediate effect

INV-IBKR-DEGRADE-2: "No T2 in DEGRADED state"
  test: tests/test_ibkr/test_degradation.py::TestTierBlocking
  enforcement: TierBlockedError raised on check_tier(2)

INV-SUPERVISOR-1: "Supervisor death → immediate alert"
  test: tests/test_ibkr/test_supervisor.py::TestSupervisorDeathAlert
  enforcement: watchdog monitors supervisor thread
```

### HOOKS (S40) ✓

```yaml
INV-HOOK-1: "Pre-commit blocks scalar_score in new code"
  test: tests/test_hooks/test_pre_commit.py::TestScalarBan
  enforcement: tools/hooks/scalar_ban_hook.py + .pre-commit-config.yaml

INV-HOOK-2: "Pre-commit blocks causal language"
  test: tests/test_hooks/test_pre_commit.py::TestCausalLanguageBan
  enforcement: CAUSAL_PATTERNS in scalar_ban_hook.py

INV-HOOK-3: "Runtime catches missing provenance"
  test: tests/test_hooks/test_runtime_assertions.py::TestProvenanceMissing
  enforcement: assert_provenance() raises ProvenanceMissing

INV-HOOK-4: "Runtime catches ranking fields"
  test: tests/test_hooks/test_runtime_assertions.py::TestRankingViolation
  enforcement: assert_no_ranking() raises RankingViolation
```

### NARRATOR (S40) ✓

```yaml
INV-NARRATOR-1: "Narrator outputs facts only, no synthesis"
  test: tests/test_narrator/test_templates.py::TestNoSynthesis
  enforcement: FORBIDDEN_WORDS + validate_template_content()

INV-NARRATOR-2: "All data fields have explicit source"
  test: tests/test_narrator/test_renderer.py::TestDataSourceTracing
  enforcement: DataSources class with source_file attributes

INV-NARRATOR-3: "Undefined variable → error, not silent"
  test: tests/test_narrator/test_renderer.py::TestStrictUndefined
  enforcement: Jinja2 StrictUndefined mode
```

### SAFETY (Cross-Sprint)

```yaml
INV-NO-UNSOLICITED: "System never says 'I noticed' or proposes hypotheses"
  test: tests/test_cso_no_exec_write.py
  enforcement: CSO read-only, no proposal generation

INV-LLM-REMOVAL-TEST: "If removing LLM prevents reconstruction → invalid"
  test: tests/test_nex_subsumption.py
  enforcement: design principle (manual audit)

INV-NO-ROLLUP: "No aggregation across traffic lights; no 'overall' label"
  test: tests/test_cso/test_bit_vector.py
  enforcement: gates_passed[] without aggregation

INV-NO-DEFAULT-SALIENCE: "UI must not imply importance"
  test: drills/d4_verification.py
  enforcement: alphabetical sort, no highlighting

INV-SLICE-MINIMUM-N: "N < 30 → warn or fail-silent"
  test: tests/test_cfp/test_lens_schema_validation.py
  enforcement: minimum_n validation

INV-BIAS-PREDICATE: "HTF bias as predicate status, not directional words"
  test: tests/test_cso/test_drawer_schema.py
  enforcement: conditions.yaml predicates
```

### GOVERNANCE

```yaml
INV-REGIME-EXPLICIT: "Regimes = explicit predicates, never auto-detected"
  test: tests/test_cso/test_evaluator.py
  enforcement: conditions.yaml whitelist

INV-REGIME-GOVERNANCE: "Regimes versioned, capped (~20 max)"
  test: tests/test_cso/test_drawer_schema.py
  enforcement: schema validation
```

---

## 5. PATTERNS

### PROVEN

```yaml
checksum_not_briefing:
  source: D3
  insight: Machine-verifiable orientation defeats session amnesia

contract_before_integration:
  source: D2
  insight: Mock-first validation proves interface before real data

truth_first_ui:
  source: D4
  insight: UI freedom earned by state discipline

projection_not_participation:
  source: D4
  insight: UI subordinate to state, never participant in reasoning

file_seam_spine:
  source: D1
  insight: Universal injection point for Claude interaction

human_frames_machine_computes:
  source: DEFINITIVE_FATE
  insight: System never proposes; human declares what to compute
```

### REIMAGINE_PATTERNS (S35-S39)

```yaml
gate_facts_not_grades:
  applies_to: [NEX-003, NEX-008, NEX-012]
  phoenix_output: gates_passed[] + gates_failed[]
  forbidden: [letter grades, quality scores, aggregated metrics]

conditional_facts_not_causality:
  applies_to: [NEX-024, NEX-026]
  phoenix_output: "P&L when [condition]"
  forbidden: ["factor X contributed Y%"]
  precedent: Brinson attribution

conflict_surface_not_resolution:
  applies_to: [NEX-016]
  phoenix_output: "Fact A conflicts Fact B" (CONFLICT_BEAD)
  forbidden: [resolution authority]
  precedent: Wikipedia corpus detection
```

### LOGGED_FOR_FUTURE

```yaml
dynamic_workflow_entry:
  source: Spenser Skates 2026
  status: S40+ DORMANT

pilot_as_whisperer:
  source: S34.5 exploration
  status: S40+ DORMANT

bead_query_endpoint:
  source: Willison datasette
  status: S35 CFP scope
```

---

## 6. BEAD_TYPES (S37 Scope)

```yaml
CLAIM_BEAD:
  source: human input
  status: unverified assertion
  example: "Olya believes London FVG works better after 8:30"

FACT_BEAD:
  source: computation (formula explicit)
  status: verified output
  provenance: query_string + dataset_hash
  example: "win_rate(session=London, time>8:30) = 62%"

CONFLICT_BEAD:
  references: [bead_a_id, bead_b_id]
  resolution: NONE (human must resolve)
  example: "CLAIM_123 conflicts with FACT_456"

rationale: "Separates memory from myth"
```

---

## 7. CARPARK

```yaml
# IMMEDIATE (S35-S39 scope)
IBKR_FLAKEY.md:
  path: docs/explorations/IBKR_FLAKEY.md
  pattern: Heartbeat + supervisor (@banteg zero deps)

# S40+ DORMANT (GROK frontier)
MULTI_AGENT_ORCHESTRATION:
  description: Orchestrator → sub-agents w/ dependency graphs
  dependencies: S35-S39 proven

SELF_HEALING:
  description: Backoff, circuit breakers, auto-escalation
  dependencies: S35-S39 proven

WORKFLOW_LEARNING:
  description: Store patterns → propose refinements (human veto)
  governance: NEX-027 salvage path

RBAC_SUB_AGENTS:
  description: T2 gating extended to sub-agent spawning
  dependencies: Multi-agent operational

TOKEN_COST_INFRASTRUCTURE:
  description: Per-workflow budget, prompt optimization
  relation: INV-HUNT-BUDGET extended
```

---

## 8. SPRINT_ARCHAEOLOGY

```yaml
# FOUNDATION (S28-S34)
S28-S31: Foundation (River, Governance, Halt, CSO, Signalman)
S32: Execution path (IBKR mock, T2, lifecycle) | 17/17 BUNNY
S33_P1: Infrastructure (Real IBKR, monitoring, runbooks) | 15/15 BUNNY
S34: Operational finishing (D1-D4) | 13/13 BUNNY

# BLOCKED
S33_P2: BLOCKED (Olya CSO calibration)

# CONSTITUTIONAL BLOCK (S35-S39) — COMPLETE ✓
S35: CFP (Conditional Fact Projector) | ✓ 62 tests, 21 BUNNY
S36: CSO Harness (gate status, not grades) | ✓ 45 tests, 18 BUNNY
S37: Memory Discipline (CLAIM/FACT/CONFLICT) | ✓ 51 tests, 15 BUNNY
S38: Hunt Infrastructure (exhaustive compute) | ✓ 69 tests, 23 BUNNY
S39: Research Validation (decomposed outputs) | ✓ 109 tests, 28 BUNNY

# SLEEP_SAFE BLOCK (S40) — COMPLETE ✓
S40: Sleep-Safe Resilience | ✓ 312 tests, 15 BUNNY
  Track_A: Self-Healing (circuit breakers, backoff, health FSM) | 57 tests
  Track_B: IBKR Flakey (supervisor, heartbeat, degradation) | 56 tests
  Track_C: Hooks (pre-commit + runtime assertions) | 52 tests
  Track_D: Narrator (template-based state projection) | 38 tests
  Track_E: Professional Polish (API alignment) | 56 tests
  Track_F: BUNNY Chaos Battery (15 vectors) | 45 tests

cumulative_summary:
  s35_s39_completion_date: 2026-01-29
  s40_completion_date: 2026-01-30
  s41_completion_date: 2026-01-23
  total_tests: 1474+
  total_bunny_vectors: 224
  total_invariants: 95+
  s35_s39_theme: "CONSTITUTIONAL CEILING"
  s40_theme: "SLEEP_SAFE"
  s41_theme: "WARBOAR_AWAKENS"

# S41 COMPLETE
S41: WARBOAR_AWAKENS | ✓ 195 tests, 20 BUNNY
  Phase_2A: Foundation (IO schema, invariant freeze)
  Phase_2B: Dataset generation (pivoted to rule-based)
  Phase_2C: ContentClassifier (100% accuracy, 0.34ms p95)
  Phase_2D: Narrator integration (single chokepoint)
  Phase_2E: Surface polish (human cadence)
  Phase_3: Live Gateway validation (PAPER MODE)

# S42 COMPLETE (Trust Closure)
S42: TRUST_CLOSURE | ✓ Gate glossary (48 gates), health file, operator docs
  Track_A: CSO Production (glossary, health, operator docs)
  Track_B: Failure Rehearsal (chaos playbook)
  Track_C: Tech Debt Burn (xfail documented)
  Track_D: River Completion (synthetic fallback)
  Track_E: Observability (phoenix_status CLI)
  Track_F: Doc Seal (START_HERE, archive sweep)

# S44 COMPLETE (Foundation Validated)
S44: LIVE_VALIDATION | ✓ 24h unattended soak, zero arch flaws, zero invariant violations
  Phase_1: River verification (synthetic fallback operational)
  Phase_2: Full path test (CSO → Narrator → Execution validated)
  Phase_3: 24h soak (IBKR paper mode, no crashes, no violations)
  exit_gate: FOUNDATION_VALIDATED
  ops_gaps_documented: [heartbeat daemon, IBKR disconnect, River staleness, health_writer]
  disposition: "Software exists. Now we operate."

# PARALLEL TRACKS (Independent)
DEXTER_COE: OPERATIONAL (Mac Mini, separate CTO, ICT extraction)
CSO_COE: MODEL_SHIFT_ACCEPTED (recognition-based validation)
  paradigm: "Dexter + Perplexity → comprehensive base → Olya validates"
  unblocks: S33_P2 (when Olya provides curriculum)

# CURRENT STATE
S44_COMPLETE | POST_S44_FREEZE ACTIVE | CSO_PRODUCTION_READY | S47_NEXT
# INV-NO-CORE-REWRITES-POST-S44: No architectural rewrites. Only tightening, surfacing, governance.
# See docs/ARCHITECTURAL_FINALITY.md for freeze rules
```

---

## 9. BOOTSTRAP

### SEQUENCE

```bash
git pull
cat docs/DEFINITIVE_FATE.yaml | head -100  # Fate framework
cat docs/SPRINT_ROADMAP.md | grep -A20 "current_sprint"  # Active work
cat docs/PHOENIX_MANIFEST.md  # System map
cat state/orientation.yaml  # if exists
```

### FIRST_QUESTIONS

```yaml
- "What is current execution_phase?"
- "Any kill_flags_active?"
- "What's the last human action bead?"
- "Which sprint is active?"
- "What invariants must this sprint prove?"
```

### WHAT_NOT_TO_ASSUME

```yaml
- State hash mismatch = heresy, halt first
- Orientation.yaml exists (might be deleted)
- CSO is calibrated (operator-paced)
- System can propose (it cannot — human frames only)
- Grades exist (gates_passed only)
```

### FIRST_FAILURE_TEST

```yaml
test_1:
  action: Delete orientation.yaml
  expect: Widget goes blank (⚠️ NO STATE)

test_2:
  action: Inject corrupted bead (wrong hash)
  expect: STATE_CONFLICT detected

test_3:
  action: Request "Grade A" output
  expect: System returns gates_passed[], refuses grades
```

---

## 10. CRITICAL_REFERENCES

```yaml
DEFINITIVE_FATE.yaml:
  purpose: NEX→Phoenix fate table (61 capabilities)
  location: docs/DEFINITIVE_FATE.yaml

SPRINT_ROADMAP.md:
  purpose: S35-S39 detailed scope + invariants
  location: docs/SPRINT_ROADMAP.md

PHOENIX_MANIFESTO.md:
  purpose: Vision, characters, narrative culture
  location: docs/PHOENIX_MANIFESTO.md

conditions.yaml:
  purpose: 5-drawer gate predicates
  location: cso/knowledge/conditions.yaml

beads.yaml:
  purpose: Bead type definitions
  location: schemas/beads.yaml
```

---

*S35-S41 COMPLETE. Human frames, machine computes. Human sleeps.*
*No scalar scores. No rankings. No verdicts. Ever.*
*The constitutional ceiling is set. The floor holds. Guard dog armed. Live gateway validated. 🐗🔥*
