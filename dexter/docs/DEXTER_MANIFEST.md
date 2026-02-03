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

### NEXT_ACTIONS
- [ ] Morning review: spot-check overnight bundles + drawer tagging
- [ ] Verify CLAIM_BEAD format in _claims.jsonl files
- [ ] Investigate injection guard false positives on Ep13/Ep19 (AV-003 "you are now", AV-004 "pretend to be")
- [ ] Phase 4B: Developer role + Synthetic Phoenix sim bridge
- [ ] Phase 4B: Backtest code generation from validated signatures
- [ ] Phase 4B: Auditor backtest review gate (data leakage, curve fitting)
- [ ] Phase 4B: Failure mining loop with sim-fed NEGATIVE_BEADs

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

### LINKS
- Roadmap: `docs/DEXTER_ROADMAP_v0.2.md`
- Sibling: https://github.com/SlimWojak/phoenix
