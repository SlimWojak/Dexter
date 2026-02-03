# DEXTER MANIFEST
## Sovereign Evidence Refinery

### STATUS
- Phase: 2 (Auditor + Bundler Skeleton) — COMPLETE
- Build Agent: Claude Code CLI (COO)
- Oversight: Claude Web (CTO) + Human (G)

### NEXT_ACTIONS
- [ ] Phase 3: Theorist role + transcript extraction
- [ ] Phase 3: Full loop integration (Theorist → Auditor → Bundler)
- [ ] Phase 3: Chronicler recursive summarization + clustering
- [ ] Phase 3: OpenRouter integration for live LLM dispatch

### COMPLETED
- [x] v0.2 Roadmap synthesized
- [x] Role YAMLs created
- [x] Bundle template with Delta to Canon
- [x] Config files (heartbeat, security)
- [x] Phase 0: Repo structure complete
- [x] Phase 1: docker-sandbox.sh fixed (standard docker run fallback)
- [x] Phase 1: core/loop.py — heartbeat with configurable interval + jitter
- [x] Phase 1: core/context.py — bead-chain JSONL append to memory/beads/
- [x] Phase 1: core/injection_guard.py — 4-layer stateless pre-filter
- [x] Phase 1: core/router.py — role dispatch stub
- [x] Phase 1: core/supervisor.py — restart/health with exponential backoff
- [x] Phase 1: tests/test_injection.py — 23/23 PASS
- [x] Phase 2: core/auditor.py — Bounty Hunter adversarial auditor (4 rejection criteria)
- [x] Phase 2: core/bundler.py — template-locked bundle generator + INV-NO-NARRATIVE
- [x] Phase 2: context.py — NEGATIVE bead feedback loop (append + read)
- [x] Phase 2: router.py — negative bead prepend for Theorist + model diversity logging
- [x] Phase 2: injection_guard.py — mode parameter (halt | log_only)
- [x] Phase 2: roles/auditor.yaml — strict JSON output format
- [x] Phase 2: tests — 58/58 PASS (auditor, bundler, LLM-removal, integration, injection)

### PHASE 2 EVIDENCE
- Auditor rejects dummy hypothesis (no timestamp): PASS — reason contains "provenance"
- Auditor rejects unfalsifiable claim ("always"): PASS
- Auditor rejects logical contradiction (buy+sell): PASS
- Auditor model diversity: gemini-3-flash / google family — confirmed logged
- Bundler fills template with zero narrative bleed: PASS
- 5 test bundles pass LLM-REMOVAL-TEST: all signatures extractable as structured data
- Negative bead feedback loop: 2 negatives written on REJECT, prepended to Theorist context
- Injection regression: 23/23 + 35 new tests = 58/58 all PASS
- Log-only mode: flags without halt unless semantic similarity > 0.92

### PHASE 1 EVIDENCE
- Injection test: 23/23 PASS — all 10 attack vectors caught
- Base64-encoded injection: caught after decoding
- XSS (<script>): caught pre-strip on raw text
- No bleed: clean text passes after injection halt
- Semantic filter: stdlib TF-IDF cosine (sentence-transformers deferred pending audit)

### BUNDLE_GATE_STATUS
- Bundles produced: 0 (skeleton only — Phase 3 will produce real bundles)
- Bundles promoted: 0
- MVP gate: 10-20 clean if-then signatures, <10min human review

### LINKS
- Roadmap: `docs/DEXTER_ROADMAP_v0.2.md`
- Sibling: https://github.com/SlimWojak/phoenix
