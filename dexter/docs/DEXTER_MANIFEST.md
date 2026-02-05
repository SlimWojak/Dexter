# DEXTER MANIFEST
## Sovereign Evidence Refinery

### STATUS
- Phase: 5+ (Phoenix Integration Established) — OPERATIONAL
- Build Agent: Claude Code CLI (COO)
- Oversight: Claude Web (CTO) + Human (G)
- Phoenix CTO: Reviewed and approved architecture

### PHOENIX INTEGRATION
- Status: BRIDGE ESTABLISHED
- Format: CLAIM_BEAD spec implemented
- Drawer tagging: Active (5-drawer system)
- Human gate: Mandatory (INV-DEXTER-ALWAYS-CLAIM)
- Phoenix CTO: Reviewed and approved architecture
- Data flow: DEXTER -> CLAIM_BEADs -> Human review -> Phoenix FACT_BEADs

### NEXT_ACTIONS (Post-Advisor Synthesis 2026-02-04)

**P1 — CHRONICLER (COMPLETE):**
- [x] Implement recursive summarization every 20-30 beads
- [x] Produce THEORY.md summary + index
- [x] Archive raw beads to archive/
- [x] Preserve negatives in dedicated section

**P2 — BACK-PROPAGATION SEAM (COMPLETE):**
- [x] Design Olya rejection → NEGATIVE_BEAD flow
- [x] Feed NEGATIVE_BEADs back to Theorist context
- [x] Document seam in ROLE_CONTRACTS.md

**P3 — SCOPE CONSTRAINT:**
- [ ] BLOCKED: Awaiting CSO curriculum (24-48h from 2026-02-04)
- [ ] Bound extraction to CSO-provided video list when received

**P4 — AUDITOR HARDENING (COMPLETE):**
- [x] Harden Auditor prompt with v0.3 Bounty Hunter pattern
- [x] Add 6 mandatory falsification attacks (provenance, falsifiability, logical, tautology, ambiguity, canon)
- [x] Add rejection rate tracking with flags (RUBBER_STAMP, CRITICAL_LOW, BELOW_TARGET)
- [ ] Monitor rejection rate post-hardening (operational)
- [ ] Third family (Llama/Qwen) if still <5% (future if needed)

**P5 — QUEUE ATOMICITY (COMPLETE):**
- [x] Fix save_queue() with write-tmp + rename pattern
- [x] Ship before scaling past current batch sizes

**P6 — RUNAWAY GUARDS (COMPLETE):**
- [x] Hard turn cap (20 turns default, configurable)
- [x] Daily cost ceiling ($1.00/day default)
- [x] Session cost ceiling ($0.50/session default)
- [x] No-output watchdog (5 min timeout default)
- [x] GuardManager for unified guard orchestration

**LOWER PRIORITY:**
- [ ] Injection guard tuning (whitelist ICT speech patterns — 2/20 affected)
- [ ] Researcher role (Perplexity) — defer until CSO curriculum defined
- [ ] Daemon mode (launchd, logging, Matrix alerts)

### COMPLETED
- [x] v0.2 Roadmap synthesized
- [x] Role YAMLs created
- [x] Bundle template with Delta to Canon
- [x] Config files (heartbeat, security)
- [x] Phase 0: Repo structure complete
- [x] Phase 1: Core loop + injection guard + hardening — 23/23 PASS
- [x] Phase 2: Auditor + Bundler skeleton — 58/58 PASS
- [x] Phase 3: core/theorist.py — forensic extractor (pattern-based mock, deepseek family)
- [x] Phase 3: skills/transcript/supadata.py — mock ICT transcript (10 segments)
- [x] Phase 3: core/router.py — mock dispatch, injection guard integration, DEXTER_MOCK_MODE
- [x] Phase 3: core/loop.py — process_transcript() pipeline (fetch→extract→audit→bundle)
- [x] Phase 3: roles/theorist.yaml — full prompt contract, deepseek family
- [x] Phase 3: Full loop verified — 10 extracted, 2 rejected, 8 validated, bundle created
- [x] Phase 3: tests — 85/85 PASS (theorist, full loop, model diversity, + all Phase 1-2)

- [x] Phase 4A: skills/transcript/supadata.py — real Supadata API + async polling + jargon checker
- [x] Phase 4A: roles/theorist.yaml — ICT jargon reference prefix (17 terms)
- [x] Phase 4A: scripts/run_real_transcript.py — CLI runner with gate validation
- [x] Phase 4A: tests — 115/115 PASS (30 new: supadata API, jargon, normalization, runner gates, bundler quote exclusion)
- [x] Phase 4A: Theorist windowed extraction for auto-caption chunks
- [x] Phase 4A: Router local dispatch (pattern-based handlers on real data)
- [x] Phase 4A: Bundler narrative bleed — exclude verbatim transcript quotes in table rows
- [x] Phase 4A: First real run — youtube.com/watch?v=tmeCWULSTHc (ICT 2024 Mentorship Ep1)

- [x] Phase 5: core/llm_client.py — OpenRouter client with role-based MODEL_ROUTING
- [x] Phase 5: Model routing — per-role model/family/temperature/max_tokens config
- [x] Phase 5: Cross-family diversity validation (Theorist=deepseek, Auditor=google)
- [x] Phase 5: Rate-limit fallback (429 → sleep 5s → retry with default model)
- [x] Phase 5: Per-call cost logging (MODEL_COSTS lookup, $/1M tokens)
- [x] Phase 5: core/theorist.py — LLM extraction via OpenRouter deepseek (THEORIST_SYSTEM_PROMPT)
- [x] Phase 5: LLM JSON parsing (plain + ```json code blocks), dedup by if|then key
- [x] Phase 5: skills/transcript/supadata.py — chunk_transcript() (5min overlapping windows)
- [x] Phase 5: core/router.py — LLM dispatch path + is_llm_mode()
- [x] Phase 5: core/cartographer.py — corpus survey via yt-dlp, categorization, queue strategies
- [x] Phase 5: roles/cartographer.yaml — INV-NO-RECOMMEND, INV-NO-INTERPRET, INV-HUMAN-QUEUE
- [x] Phase 5: scripts/run_cartographer.py — CLI for channel survey
- [x] Phase 5: core/bundler.py — B-YYYYMMDD-HHMMSS bundle IDs + index.jsonl tracking
- [x] Phase 5: core/queue_processor.py — batch extraction from extraction_queue.yaml
- [x] Phase 5: scripts/run_queue.py — CLI for queue processing (dry_run/execute/limit)
- [x] Phase 5: tests — 208/208 PASS (93 new: LLM theorist, cartographer, model routing, queue processor)

- [x] Pipeline A: Cartographer surveyed @InnerCircleTrader (790 videos, 286 mentorship)
- [x] Pipeline B: LLM Theorist quality test — 13 sigs from Ep2, canonical ICT terminology
- [x] Pipeline C: Batch processing top 5 mentorship — 43 sigs, 4 bundles, 0 failures
- [x] Integration: CLAUDE.md Phoenix invariants (ALWAYS-CLAIM, NO-PROMOTE, SOURCE-LINK, CROSS-FAMILY)
- [x] Integration: CLAIM_BEAD export (generate_claim_bead, export_claim_beads, _claims.jsonl)
- [x] Integration: 5-drawer pre-tagging in Theorist (HTF_BIAS, MARKET_STRUCTURE, PREMIUM_DISCOUNT, ENTRY_MODEL, CONFIRMATION)
- [x] Integration: Roadmap updated with Phoenix integration section
- [x] Overnight soak: 20 videos queued, 18 DONE, 2 FAILED (injection guard false positives)
- [x] Soak results: 424 validated, 9 rejected (2.1% rejection rate), 20 CLAIM_BEAD files (408 beads)
- [x] Drawer tagging verified: drawers 1-5 active, confidence + basis fields populated

- [x] P1 Chronicler: core/chronicler.py — recursive summarization + clustering
- [x] P1 Chronicler: memory/THEORY.md — generated from 424 CLAIM_BEADs
- [x] P1 Chronicler: memory/archive/ — session bead archival working
- [x] P1 Chronicler: NEGATIVE section preserved in THEORY.md
- [x] P1 Chronicler: Redundancy detection (cosine > 0.85) — 75 pairs flagged
- [x] P1 Chronicler: Drawer clustering (5-drawer system) — all drawers populated
- [x] P1 Chronicler: tests — 25 new tests, 233/233 PASS total

- [x] P2 Back-propagation: Enhanced NEGATIVE_BEAD schema (source_claim_id, drawer, rejected_by)
- [x] P2 Back-propagation: scripts/record_rejection.py — CLI for human rejection
- [x] P2 Back-propagation: Theorist context injection verified
- [x] P2 Back-propagation: Chronicler integration verified (no regression)
- [x] P2 Back-propagation: tests — 22 new tests, 255/255 PASS total
- [x] P2 Back-propagation: ROLE_CONTRACTS.md updated with seam documentation

- [x] P5 Queue atomicity: save_queue() now uses write-tmp + atomic rename
- [x] P5 Queue atomicity: tests — 3 new tests, 258/258 PASS total

- [x] P4 Auditor hardening: roles/auditor.yaml v0.3 Bounty Hunter pattern
- [x] P4 Auditor hardening: 6 mandatory falsification attacks (+ tautology, ambiguity)
- [x] P4 Auditor hardening: Rejection rate tracking (RUBBER_STAMP/CRITICAL_LOW/BELOW_TARGET flags)
- [x] P4 Auditor hardening: tests — 12 new tests (tautology, ambiguity, rate tracking)

- [x] P6 Runaway guards: config/guards.yaml configuration file
- [x] P6 Runaway guards: core/guards.py (TurnCapGuard, CostCeilingGuard, StallWatchdogGuard)
- [x] P6 Runaway guards: GuardManager for unified orchestration
- [x] P6 Runaway guards: tests — 25 new tests, 298/298 PASS total

### PIPELINE EVIDENCE
- Cartographer: 790 videos surveyed, 286 MENTORSHIP, 80 LECTURE, 64 LIVE, 53 REVIEW: PASS
- LLM Ep2: 13 unique signatures, canonical ICT terms (FVG, MSS, killzone, OTE): PASS
- Batch top 5: 5 processed, 0 failures, 4 bundles (43 sigs total): PASS
- CLAIM_BEAD format: bead_type=CLAIM, status=UNVALIDATED, promoted_by=None: PASS
- Drawer tagging: 5-drawer system in THEORIST_SYSTEM_PROMPT: PASS
- Index tracking: bundles/index.jsonl with 32 entries: PASS
- Total API cost (all runs): ~$0.05
- Overnight soak: 18/20 DONE, 424 validated, 9 rejected, 408 CLAIM_BEADs: PASS
- Soak failures: 2 injection guard false positives (Ep13 "pretend to be", Ep19 "you are now"): KNOWN
- Drawer spot-check: drawer=2 (MARKET_STRUCTURE), drawer=4 (ENTRY_MODEL), drawer=1 (HTF_BIAS): PASS

### PHASE 5 EVIDENCE
- All roles configured in MODEL_ROUTING (theorist, auditor, bundler, chronicler, cartographer, default): PASS
- Theorist=deepseek family, Auditor=google family (cross-family veto): PASS
- Rate-limit fallback: 429 triggers 5s sleep + retry with default model (mocked): PASS
- Cost logging: deepseek ($0.14/$0.28 per 1M in/out), gemini ($0.10/$0.40): PASS
- LLM JSON parsing handles plain arrays and ```json code blocks: PASS
- LLM dedup: same if|then across chunks kept only once: PASS
- Negative context prepended to system prompt for LLM extraction: PASS
- Bad JSON / API errors skip chunk without crash: PASS
- Cartographer categorization: MENTORSHIP, LECTURE, LIVE_SESSION, QA, REVIEW, UNKNOWN: PASS
- Duration buckets: SHORT (<10min), MEDIUM (10-60min), LONG (>60min): PASS
- View tiers: VIRAL (>1M), HIGH (>100K), MEDIUM (>10K), LOW: PASS
- Queue strategies: mentorship_first, chronological, views: PASS
- Bundle ID format B-YYYYMMDD-HHMMSS (17 chars, UTC): PASS
- index.jsonl write + read round-trip: PASS
- Queue processor: dry_run, limit, execute, failure handling: PASS
- All 208 tests pass: PASS

### P2 BACK-PROPAGATION EVIDENCE
- Enhanced NEGATIVE_BEAD schema: source_claim_id, drawer, rejected_by fields: PASS
- scripts/record_rejection.py CLI works (--claim-id, --reason, --list-claims): PASS
- Rejection round-trip: claim lookup → NEGATIVE_BEAD creation → provenance preserved: PASS
- Theorist context injection: _prepend_negative_context() formats negatives: PASS
- THEORIST_SYSTEM_PROMPT contains {negative_context} placeholder: PASS
- Chronicler handles enhanced negatives (no regression): PASS
- 22 new tests (schema, ingestion, injection, integration, edge cases): PASS
- All 255 tests pass (233 prior + 22 new): PASS
- Learning loop operational: Human → NEGATIVE_BEAD → Theorist avoidance: PASS

### P1 CHRONICLER EVIDENCE
- core/chronicler.py created with compress_beads(), cluster_by_drawer(), detect_redundant_pairs(): PASS
- THEORY.md generated with INDEX, CLUSTERS (5 drawers), REDUNDANT, NEGATIVE sections: PASS
- Clustering: 424 claims → 389 clusters across 5 drawers: PASS
- Redundancy: 75 pairs flagged (cosine >= 0.85): PASS
- Archive: session_2026-02-03.jsonl → archive/archive_session_2026-02-03_*.jsonl: PASS
- NEGATIVE beads preserved (4 negatives in THEORY.md): PASS
- LLM summarization via chronicler role (google/gemini-2.0-flash-exp, temp=0.3): PASS
- 25 new tests (similarity, clustering, redundancy, archive, integration): PASS
- All 233 tests pass (208 prior + 25 new): PASS
- Memory bloat risk mitigated: PASS

### PHASE 4A EVIDENCE
- Supadata real API path: 200 response normalizes correctly (mocked HTTP): PASS
- Supadata async polling: 202 → poll → completed flow (mocked HTTP): PASS
- No API key raises ValueError with clear message: PASS
- Transcript normalization: plain text, timestamped chunks, empty, string lists: PASS
- Jargon checker finds 7/30 ICT terms in mock transcript: PASS
- Jargon checker detects "fairly value", "order blog", "liquidity sweet" errors: PASS
- Mock transcript jargon error rate 0.0% (< 5% gate): PASS
- Runner gates (mock): 10 signatures, 20% rejection, 0% jargon error — ALL PASS
- Theorist YAML has 17-term ICT jargon reference block: PASS
- All 115 tests pass (85 prior + 30 new): PASS
- FIRST REAL RUN (tmeCWULSTHc):
  - 1244 segments fetched from Supadata API: PASS
  - 7/30 ICT terms detected (FVG, liquidity, imbalance, OTE, premium, discount, smart money): PASS
  - Jargon error rate 0.0%: PASS (gate: <5%)
  - 36 signatures extracted via windowed extraction: PASS (gate: >=10)
  - 1 rejected (S-005: buy/sell logical contradiction): PARTIAL (gate: 10-30%, actual: 2.8%)
  - Bundle B-1770122781 created: PASS
  - KNOWN ISSUE: regex deduplication too loose — near-duplicate conditions from overlapping windows
  - KNOWN ISSUE: rejection rate 2.8% < 10% gate floor — expected with regex extraction (no LLM)
  - Phase 5 LLM extraction will address both issues

### PHASE 3 EVIDENCE
- Theorist extracts 10 signatures from mock transcript: PASS (gate: 5+)
- Each signature has timestamp + verbatim quote: PASS
- Auditor rejects 2 signatures (S-004 "always", S-010 "guaranteed"): PASS (proves adversarial)
- Bundler creates bundle from 8 survivors: PASS
- Negative beads created for 2 rejections: PASS
- Second run: Theorist receives negative bead context (2 beads prepended): PASS
- Negative avoidance: "liquidity" pattern skips 3 signatures: PASS
- Model diversity: Theorist=deepseek, Auditor=google (different families): PASS
- Full loop runs without crash in mock mode: PASS
- All 85 tests pass: PASS
- No new pip installs required

### PHASE 2 EVIDENCE
- Auditor rejects missing provenance: PASS
- Bundler zero narrative bleed: PASS
- 5 bundles pass LLM-REMOVAL-TEST: PASS
- Injection regression: 23/23 still PASS

### PHASE 1 EVIDENCE
- Injection test: 23/23 PASS
- Semantic filter: stdlib TF-IDF cosine (sentence-transformers deferred)

### BUNDLE_GATE_STATUS
- Bundles produced: 32 (3 mock, 4 pre-soak LLM, 3 batch top-5, 22 overnight soak)
- Bundles promoted: 0
- Total validated signatures: 504
- Total rejected: 12 (2.3% rejection rate)
- Total CLAIM_BEADs exported: 408
- Largest bundle: B-20260203-150140 (49 validated)
- Bundle ID format: B-YYYYMMDD-HHMMSS
- Index tracking: bundles/index.jsonl (32 entries)
- CLAIM_BEAD export: bundles/{id}_claims.jsonl (20 files)
- MVP gate: 10-20 clean if-then signatures, <10min human review

### NEW INVARIANTS (Advisor Synthesis 2026-02-04)
```yaml
INV-DEXTER-ICT-NATIVE: "Theorist uses raw ICT terminology. Translation at Bundler only."
INV-FACT-ENCAPSULATES-CLAIM: "Every FACT bead references source CLAIM_ID for forensic trace."
INV-CALIBRATION-FOILS: "Validation batches MAY include foils. Operator-configurable."
INV-RUNAWAY-CAP: "Agent loops hard-capped at N turns. No-output > X min → halt."
INV-BEAD-AUDIT-TRAIL: "All beads auditable end-to-end with full provenance chain."
```

### LINKS
- Sprint Roadmap: `docs/SPRINT_ROADMAP.md` (current priorities)
- Build History: `docs/DEXTER_ROADMAP_v0.2.md` (phases 0-5)
- Phoenix Manifest: `docs/PHOENIX_MANIFEST.md` (sibling system)
- Advisor Synthesis: `docs/POST_S44_SYNTHESIS_v0.1.md`
- Sibling Repo: https://github.com/SlimWojak/phoenix
