# DEXTER MANIFEST
## Sovereign Evidence Refinery

### STATUS
- Phase: 4A (Real Transcript Integration) — COMPLETE (awaiting first real run)
- Build Agent: Claude Code CLI (COO)
- Oversight: Claude Web (CTO) + Human (G)

### NEXT_ACTIONS
- [ ] Phase 4A: First real run — need ICT 2022 Mentorship Ep.1 video URL from G/Olya
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
- [x] Phase 4A: tests — 113/113 PASS (28 new: supadata API, jargon, normalization, runner gates)

### PHASE 4A EVIDENCE
- Supadata real API path: 200 response normalizes correctly (mocked HTTP): PASS
- Supadata async polling: 202 → poll → completed flow (mocked HTTP): PASS
- No API key raises ValueError with clear message: PASS
- Transcript normalization: plain text, timestamped chunks, empty, string lists: PASS
- Jargon checker finds 7/30 ICT terms in mock transcript: PASS
- Jargon checker detects "fairly value", "order blog", "liquidity sweet" errors: PASS
- Mock transcript jargon error rate 0.0% (< 5% gate): PASS
- Runner gates: 10 signatures, 20% rejection, 0% jargon error — ALL PASS
- Theorist YAML has 17-term ICT jargon reference block: PASS
- All 113 tests pass (85 prior + 28 new): PASS
- BLOCKER: Awaiting real YouTube URL for first live run

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
- Bundles produced: 1 (mock pipeline)
- Bundles promoted: 0
- MVP gate: 10-20 clean if-then signatures, <10min human review

### LINKS
- Roadmap: `docs/DEXTER_ROADMAP_v0.2.md`
- Sibling: https://github.com/SlimWojak/phoenix
