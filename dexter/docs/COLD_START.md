# DEXTER COLD START — Read This First

> For a fresh Claude CTO session with ZERO prior context.

---

## What Is Dexter?

**Sovereign Evidence Refinery.** Extracts IF-THEN trading logic from ICT content.

- Sibling to Phoenix (constitutional trading system)
- Separate repo, hardware, CTO
- Built in 1 day, iterated over 2 sessions
- Mascot: 🔬🧪 (Forensic Lab)

**Core principle:**
```
Transcripts → If-Then Signatures → Evidence Bundles → Human Review → Phoenix Canon

The swarm extracts. The swarm audits. The swarm bundles.
The swarm NEVER recommends. The swarm NEVER interprets.
Human frames. Machine computes. Human promotes.
```

---

## Quick Status

```yaml
phase: STAGE_3_COMPLETE
signatures_validated: 981 (504 soak + 331 stage2 + 146 stage3)
bundles_created: 73
corpus_mapped: 790 videos (full) + 24 videos (ICT 2022)
tests: 363/363 PASS
cost: $0.003/video
overnight_soak: 18/20 videos, 424 validated
document_pipeline: OPERATIONAL
vision_extraction: OPERATIONAL
mirror_report: bundles/MIRROR_REPORT.md

stage_3_extraction:
  ict_2022_live: 21 → 146 validated (14.6% rejected)
  mirror_report: Generated with Opus ($0.42)
  auditor_status: HEALTHY (above 10% floor)

sources_registered:
  ict_2022_mentorship: 24 videos (CANON)
  blessed_trader: 18 PDFs (LATERAL)
  olya_notes: 22 PDFs (OLYA_PRIMARY)
  layer_0: 1 MD (REFERENCE)
  full_channel: 790 videos (ICT_LEARNING)
```

---

## Read Order

1. **This file** (COLD_START.md) — 2 min orientation
2. **CLAUDE.md** (root) — invariants, execution protocol, model routing
3. **docs/SPRINT_ROADMAP.md** — current priorities P1-P6
4. **docs/DEXTER_MANIFEST.md** — operational status + evidence

If exploring further:
- `docs/DEXTER_ROADMAP_v0.2.md` — build history (phases 0-5)
- `docs/POST_S44_SYNTHESIS_v0.1.md` — advisor synthesis
- `docs/addendum_from_CTO_Opus_Review.md` — seed ideas (Olya_Manifest)

---

## Current Priorities (P1-P6)

| Priority | Task | Risk | Status |
|----------|------|------|--------|
| **P1** | Chronicler implementation | MITIGATED | COMPLETE |
| **P2** | Back-propagation seam | MITIGATED | COMPLETE |
| **P3** | Source ingestion pipeline | MITIGATED | COMPLETE |
| **P3.5** | Vision extraction skill | MITIGATED | COMPLETE |
| **P4** | Auditor hardening | MITIGATED | COMPLETE |
| **P5** | Queue atomicity | MITIGATED | COMPLETE |
| **P6** | Runaway guards | MITIGATED | COMPLETE |
| **Stage 2** | Full corpus extraction | MITIGATED | COMPLETE |
| **Stage 3** | Live ICT + Mirror Report | MITIGATED | COMPLETE |

---

## Key Invariant

```yaml
INV-DEXTER-ALWAYS-CLAIM: |
  All Dexter output = CLAIM. Never FACT.
  Human (Olya) promotes. Always.
  Refinement makes review faster, not unnecessary.
```

---

## Architecture at a Glance

```yaml
roles:
  theorist: deepseek/deepseek-chat (extraction)
  auditor: google/gemini-2.0-flash-exp (adversarial veto — DIFFERENT family)
  bundler: deepseek/deepseek-chat (template filling)
  chronicler: google/gemini-2.0-flash-exp (summarization — IMPLEMENTED)
  cartographer: google/gemini-2.0-flash-exp (corpus mapping)

memory:
  beads: Append-only JSONL per day
  theory_md: Recursive summary (IMPLEMENTED — Chronicler P1)
  archive: Session bead archival (IMPLEMENTED)

bridge:
  format: CLAIM_BEAD JSONL with 5-drawer tags
  files: bundles/{id}_claims.jsonl

source_pipeline:
  pdf_ingester: skills/document/pdf_ingester.py
  md_ingester: skills/document/md_ingester.py
  unified_runner: scripts/run_source_extraction.py
  tiers: [CANON, OLYA_PRIMARY, LATERAL, ICT_LEARNING]
```

---

## 5-Drawer System

```yaml
Drawer 1 - HTF_BIAS: Higher timeframe directional context
Drawer 2 - MARKET_STRUCTURE: Structural breaks and formations
Drawer 3 - PREMIUM_DISCOUNT: Price relative to range
Drawer 4 - ENTRY_MODEL: Specific entry patterns
Drawer 5 - CONFIRMATION: Additional validation signals
```

---

## Phoenix Relationship

- **Zero shared code** — separate repos, separate CTOs
- **Bridge:** CLAIM_BEAD JSONL files with drawer tags
- **Human gate mandatory** — Olya reviews, promotes to FACT
- **Phoenix status:** S47 Lease Implementation (separate track)
- **Integration timing:** AFTER both sides stable

---

## Seed Ideas (Vision, Not Sprint)

```yaml
HIGHEST_ALPHA — OLYA_MANIFEST:
  - Extract from HER journals/notes/trade logs
  - She validates: "That's my past self" vs "No, nuance"
  - ICT (tradition) + Lateral (context) + Olya (practice) → edge

OTHERS:
  - Parallel Synthetic Phoenix (test on sim — Phase 8+)
  - Researcher role (Perplexity — defer until curriculum)
  - Flywheel Amp (continuous mining — needs Chronicler first)
```

---

## Known Gaps

```yaml
critical:
  - ALL MITIGATED (P1-P6 + Stage 2 COMPLETE)

operational:
  - 2 injection false positives (ICT speech patterns)
  - No daemon mode (manual TMUX + Amphetamine)
  - Sync pipeline won't scale past 100+ videos
  - Auditor rejection rate 1.8% (below 10% target)

pending:
  - Live transcript integration (mock transcripts for ICT 2022)
  - Human review of Stage 2 output
```

---

## Security Stack

```yaml
L1: Docker --network none (containment)
L2: 4-layer injection guard (input sanitization)
L3: Turn cap + cost ceiling (IMPLEMENTED — P6)
L4: No-output watchdog (IMPLEMENTED — P6)
L5: Composio auth (FUTURE)
```

---

## Bootstrap Commands

```bash
# Quick status check
cat docs/COLD_START.md           # This file
cat CLAUDE.md                     # Invariants + model routing
cat docs/SPRINT_ROADMAP.md       # Current priorities

# Operational state
cat docs/DEXTER_MANIFEST.md      # Evidence + status
cat bundles/index.jsonl | tail   # Recent bundles

# Source inventory
python3 scripts/run_source_extraction.py --status

# Test health
pytest tests/ -v                  # Should be 322/322 PASS
```

---

## Key Contacts

- **CTO (Claude Web):** Strategic oversight, lateral checks
- **Human (G):** Final authority, capital decisions
- **CSO (Olya):** Curriculum, validation, promotion authority

---

*Human frames. Machine computes. Human promotes.* 🔬🧪
