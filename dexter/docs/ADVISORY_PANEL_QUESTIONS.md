# DEXTER ADVISORY PANEL — Day 2 Review
## Questions for Lateral Check

### For Grok (Frontier Scout / Trench Warrior)

```yaml
QUERY_1_HARDENING:
  context: "DEXTER MVP running on Mac Mini, Docker isolation (--network none), supervisor.py for crash recovery with exponential backoff (1s-60s). Currently using TMUX + Amphetamine for persistence."
  question: "What are the best-practice 24/7 daemon patterns for Python agents on macOS in Feb 2026? launchd vs supervisord vs Docker-native? Any OpenClaw community learnings on long-running stability?"

QUERY_2_SECURITY:
  context: "4-layer injection guard (HTML/JS strip, regex pattern match, TF-IDF cosine similarity @ 0.85 threshold, halt). Pure stdlib — no external embedders. Attack vectors stored in data/attack_vectors.jsonl."
  question: "Latest injection attack patterns against LLM agents (Feb 2026)? Any new vectors we should add to attack_vectors.jsonl? Community recommendations for agent security hardening? Are there multi-turn or indirect injection patterns we should test?"

QUERY_3_COST_OPTIMIZATION:
  context: "Currently ~$0.003/video. Theorist: deepseek/deepseek-chat via OpenRouter. Auditor: google/gemini-2.0-flash-exp. Rate limit fallback: 429 -> 5s sleep + default model."
  question: "Any new ultra-cheap models on OpenRouter suitable for extraction/audit roles? Free tier options that maintain quality? Cost benchmarks from similar agent deployments? Any models that excel at structured JSON extraction?"

QUERY_4_MEMORY_PATTERNS:
  context: "Bead-chain JSONL (append-only, per-calendar-day files) + THEORY.md recursive summarization (planned, Chronicler not yet implemented). Compression threshold: 25 beads / 750 tokens."
  question: "Best practices for long-running agent memory in 2026? Any improvements on bead-chain pattern? Vector DB vs flat file for 1000+ video corpus? How do production agents handle context window management at scale?"
```

### For Gemini (Wise Owl / Lateral Thinker)

```yaml
QUERY_1_ARCHITECTURE:
  context: "DEXTER = 5 roles (Theorist, Auditor, Bundler, Chronicler, Cartographer) with cross-family model diversity enforced. Pipeline: transcript -> chunked windows -> LLM extraction -> adversarial audit -> evidence bundle. 6,000 LOC Python, 208 tests."
  question: "Any architectural blind spots? Roles we're missing? Potential failure modes in the adversarial loop we haven't considered? Should there be a 'Reconciler' role that cross-references signatures across videos?"

QUERY_2_PHOENIX_SYNERGY:
  context: "DEXTER outputs CLAIM_BEADs (always CLAIM, never FACT — invariant enforced). Phoenix CSO validates to FACT_BEADs. Drawer tagging: HTF_BIAS, MARKET_STRUCTURE, PREMIUM_DISCOUNT, ENTRY_MODEL, CONFIRMATION."
  question: "Is the CLAIM->FACT bridge the right abstraction? Any risk of semantic drift between systems? Should there be a shared ontology or schema validation layer? How should contradictions between videos be surfaced?"

QUERY_3_INSIGHT_EXTRACTION:
  context: "Currently extracting IF-THEN signatures with 5-drawer classification. Theorist uses 100+ line ICT jargon system prompt. Deduplication by if|then key across overlapping windows."
  question: "What other insight types should DEXTER extract beyond IF-THEN? Relationships between concepts? Contradictions in ICT teaching across time periods? Meta-patterns across videos? Should we extract 'context dependencies' (IF X, but only when Y)?"

QUERY_4_SCALING:
  context: "790 videos mapped (286 mentorship). Currently processing top 5 mentorship. Extraction queue: YAML-based with status tracking. Batch processor: sequential, configurable delay."
  question: "At what point does volume become noise? Should there be a 'saturation detector' that flags diminishing returns per drawer? How do we know when we've extracted enough from a topic cluster? Is there a quality-over-quantity threshold?"
```

### For Phoenix CTO (Sibling System Architect)

```yaml
QUERY_1_INTEGRATION:
  context: "CLAIM_BEAD format: bead_type=CLAIM, source_system=DEXTER, drawer (1-5), status=UNVALIDATED, promoted_by=None. Exported as per-bundle JSONL files."
  question: "Any refinements to the format after seeing overnight soak output? Additional metadata Phoenix CSO would find useful? Should CLAIM_BEADs carry confidence scores or extraction difficulty ratings?"

QUERY_2_OPERATING_RHYTHM:
  context: "Bundles accumulate in bundles/ directory. Human pulls when ready. Matrix alerts on creation. Commands: APPROVE/REJECT/REVIEW."
  question: "What's the ideal review cadence for Olya? Daily digest? Weekly batch? How does this fit Phoenix's existing rhythm? Should there be auto-aging (bundles older than N days get flagged)?"

QUERY_3_INVARIANT_COVERAGE:
  context: "Active invariants: INV-DEXTER-ALWAYS-CLAIM, INV-DEXTER-NO-PROMOTE, INV-DEXTER-SOURCE-LINK, INV-DEXTER-CROSS-FAMILY, INV-NO-NARRATIVE, INV-NO-GRADES, INV-NO-UNSOLICITED."
  question: "Any Phoenix invariants we should inherit that we missed? Any DEXTER-specific invariants that should propagate back to Phoenix? Should there be an INV-DEXTER-NO-DUPLICATE (reject signatures already in Phoenix canon)?"
```

### For COO (Codebase Perspective)

```yaml
QUERY_1_TECHNICAL_DEBT:
  context: "Built in 1 day, 208 tests, 6,000 LOC. Zero TODO/FIXME/HACK comments found. Clean error handling throughout. pydantic imported but unused."
  question: "What technical debt did you accumulate? Any shortcuts that need addressing? Code areas that feel fragile? Is the synchronous pipeline a scaling limitation?"

QUERY_2_EXPANSION_IDEAS:
  context: "Current: transcript extraction only. Architecture: modular roles + skills. Existing stubs: perplexity.py (research), exa.py (research)."
  question: "What capabilities would be easy to add given current architecture? What would require significant refactoring? Any low-hanging fruit in the skills/ directory?"

QUERY_3_PERFORMANCE:
  context: "Processing ~5 videos in batch run. Sequential with configurable delay. Single-threaded. YAML queue with full-file rewrite."
  question: "Any bottlenecks observed? Rate limits hit? Memory issues? Recommendations for scaling to 100+ video batches? Should we add concurrent extraction (asyncio.gather)?"
```

---

## EXPANDED SCOPE: Researcher Role + Architecture Research

### Context

Perplexity's alpha extends beyond ICT extraction corroboration:

| Use Case | Perplexity Role | Value |
|----------|-----------------|-------|
| ICT extraction | Corroboration | "Is this real?" |
| Pattern validation | Microstructure research | "Why does it work?" |
| Regime awareness | Condition research | "When does it work?" |
| Execution optimization | Quant research | "How to best execute?" |
| Architecture decisions | Systems research | "What's the best model?" |
| Cross-methodology | Synthesis research | "What else maps to this?" |

### Proposed: "Researcher" Role

```yaml
role: researcher
purpose: "Bridge extracted patterns to broader market knowledge"
model: perplexity/deep-research (async, heavy queries)
trigger: "Hypothesis formed OR architecture question OR pattern validation needed"

query_types:
  microstructure:
    prompt: "Does [ICT concept] map to known market mechanics?"
    output: { academic_support: bool, papers: [], mechanism: str }

  regime:
    prompt: "Under what conditions does [pattern] succeed/fail?"
    output: { favorable: [], unfavorable: [], evidence: [] }

  execution:
    prompt: "What's optimal execution for [setup type]?"
    output: { recommendations: [], sources: [], tradeoffs: [] }

  architecture:
    prompt: "What models exist for [market structure detection]?"
    output: { approaches: [], pros_cons: [], implementations: [] }

  synthesis:
    prompt: "How does [ICT concept] relate to [other methodology]?"
    output: { mappings: [], conflicts: [], combined_insight: str }
```

---

### Advisory Questions: Researcher Role

#### For Grok (Frontier Scout)

```yaml
QUERY_5_PERPLEXITY_PATTERNS:
  context: "Planning to use Perplexity as R&D research layer, not just corroboration"
  question: |
    Best practices for using Perplexity Deep Research in agent workflows (Feb 2026)?
    - Async patterns that don't block heartbeat?
    - Cost optimization (when Search API vs Deep Research)?
    - Any OpenClaw community integrations to learn from?
    - Rate limits / quotas to watch for?

QUERY_6_ACADEMIC_SOURCES:
  context: "Want to validate ICT patterns against market microstructure research"
  question: |
    Best sources for academic trading/microstructure research accessible via Perplexity?
    - SSRN, arXiv quant-ph, Journal of Finance?
    - Any APIs for direct academic paper access?
    - How reliable is Perplexity for citing actual papers vs hallucinating?
```

#### For Gemini (Wise Owl)

```yaml
QUERY_5_RESEARCH_INTEGRATION:
  context: "Researcher role adds microstructure/regime/execution context to bundles"
  question: |
    How should research context integrate with CLAIM_BEADs?
    - Separate "RESEARCH_BEAD" type?
    - Embedded in signature metadata?
    - Risk of research context biasing Olya's review?
    - Should research be visible during promotion decision or after?

QUERY_6_ARCHITECTURE_RESEARCH:
  context: "Questioning whether MSS state machine is optimal for Phoenix market structure detection"
  question: |
    Is using Perplexity to research architecture alternatives a good pattern?
    - Risk of "shiny object" distraction from working system?
    - How to evaluate research suggestions vs proven implementation?
    - Should architecture research be separate workstream from DEXTER?
```

#### For Phoenix CTO

```yaml
QUERY_4_MICROSTRUCTURE_LAYER:
  context: "Perplexity could add 'why it works' context to ICT patterns"
  question: |
    Should Phoenix CSO receive microstructure context alongside CLAIM_BEADs?
    - Does "academic support" change how CSO validates?
    - Risk of over-weighting researched claims vs experiential ones?
    - How does this fit the CLAIM -> FACT promotion flow?

QUERY_5_STATE_MACHINE_REVIEW:
  context: "CTO raised question: Is MSS state machine the right model for Phoenix?"
  question: |
    Should we use Perplexity to research alternative market structure models?
    - Hidden Markov Models?
    - Order flow state detection?
    - ML classifiers?
    Or is this premature optimization given current Phoenix state?
```

---

### Advisory Questions: Architecture Research

#### For All Advisors

```yaml
META_QUESTION_ARCHITECTURE:
  context: |
    Phoenix currently uses enrichment + MSS state machine for market structure.
    Perplexity could research alternatives (HMM, order flow, ML classifiers).

  questions:
    1. "Is architecture research a valid use of DEXTER/Perplexity, or scope creep?"
    2. "If valid, should it be separate workstream or integrated with extraction?"
    3. "How do we evaluate 'better' architecture without rebuilding Phoenix?"
    4. "What's the threshold for 'worth investigating' vs 'distraction'?"

  desired_output: |
    Clear recommendation on whether/how to pursue architecture research.
    If yes: Proposed process for research -> evaluation -> decision.
    If no: Rationale for staying with current approach.
```

---

### Example Perplexity Research Queries (For Tomorrow's Testing)

```yaml
TEST_QUERY_1_MICROSTRUCTURE:
  query: |
    Academic research on stop-loss clustering and price reversals.
    Do institutional order flows actually target retail stop levels?
    Cite quantitative finance papers, not trading blogs.
  purpose: "Validate ICT 'liquidity sweep' concept"

TEST_QUERY_2_REGIME:
  query: |
    How do fair value gap strategies perform in high volatility vs low volatility?
    Any quantitative backtests comparing VIX levels to FVG fill rates?
  purpose: "Understand regime sensitivity"

TEST_QUERY_3_ARCHITECTURE:
  query: |
    Compare state machine approaches for market structure detection:
    Rule-based swing points vs Hidden Markov Models vs Order flow states.
    Which do quantitative trading firms prefer for intraday forex/indices?
  purpose: "Evaluate Phoenix architecture alternatives"

TEST_QUERY_4_SYNTHESIS:
  query: |
    How do ICT/SMC concepts map to Wyckoff methodology?
    Is 'liquidity sweep' equivalent to 'spring'?
    Academic or serious practitioner analysis only.
  purpose: "Cross-methodology synthesis"
```

---

## Review Protocol (Tomorrow)

1. **Morning check**: Review overnight soak results (20 videos queued)
2. **Hardening review**: Walk through HARDENING_ROADMAP.md gaps
3. **Advisory panel**: Route questions to Grok/Gemini/Phoenix CTO
4. **Synthesis**: Incorporate feedback into v0.3 roadmap
5. **Test Perplexity**: Run example research queries, evaluate quality
6. **Prioritize**: What's Phase 6? Hardening or features or Researcher role?
