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
phase: OPERATIONAL_MVP
signatures_validated: 504
bundles_created: 32
corpus_mapped: 790 videos
tests: 208/208 PASS
cost: $0.003/video
overnight_soak: 18/20 videos, 424 validated
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
| **P1** | Chronicler implementation | HIGH (memory unbounded) | URGENT |
| **P2** | Back-propagation seam | HIGH (no learning without this) | PENDING |
| **P3** | CSO curriculum scoping | MEDIUM (unbounded extraction) | BLOCKED (awaiting Olya) |
| **P4** | Auditor hardening | MEDIUM (2.1% rejection too low) | PENDING |
| **P5** | Queue atomicity | MEDIUM (crash corruption) | PENDING (5-line fix) |
| **P6** | Runaway guards | MEDIUM (token burn) | PENDING |

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
  chronicler: google/gemini-2.0-flash-exp (summarization — NOT IMPLEMENTED)
  cartographer: google/gemini-2.0-flash-exp (corpus mapping)

memory:
  beads: Append-only JSONL per day
  theory_md: Recursive summary (PENDING — Chronicler P1)
  
bridge:
  format: CLAIM_BEAD JSONL with 5-drawer tags
  files: bundles/{id}_claims.jsonl
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
  - Chronicler not implemented (beads growing unbounded)
  - Queue writes non-atomic (crash = corruption)
  - Auditor too lenient (2.1% rejection, target 10%)

operational:
  - 2 injection false positives (ICT speech patterns)
  - No daemon mode (manual TMUX + Amphetamine)
  - Sync pipeline won't scale past 100+ videos
```

---

## Security Stack

```yaml
L1: Docker --network none (containment)
L2: 4-layer injection guard (input sanitization)
L3: Turn cap + cost ceiling (PENDING — P6)
L4: No-output watchdog (PENDING — P6)
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

# Test health
pytest tests/ -v                  # Should be 208/208 PASS
```

---

## Key Contacts

- **CTO (Claude Web):** Strategic oversight, lateral checks
- **Human (G):** Final authority, capital decisions
- **CSO (Olya):** Curriculum, validation, promotion authority

---

*Human frames. Machine computes. Human promotes.* 🔬🧪
