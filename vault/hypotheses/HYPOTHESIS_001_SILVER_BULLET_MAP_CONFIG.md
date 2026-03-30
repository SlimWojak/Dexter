---
track: TRACK_1_STRATEGY_SCOUTING
status: ACTIVE
priority: P1
question: Can ICT Silver Bullet be expressed as a Map configuration using existing
  vLOCK primitives? Does it produce valid setups on EURUSD?
time_budget: 2 overnight sessions
deliverable: vault/proposals/SILVER_BULLET.yaml
success_criteria:
- 'Map config expressed in terms of existing primitives: YES/NO'
- 'If YES: precision/recall against manual Silver Bullet identification'
- 'Walk-forward positive: YES/NO'
- 'Cross-pair transfer (GBPUSD at minimum): YES/NO'
created_at: '2026-03-30T10:23:11.997861+00:00'
updated_at: '2026-03-30T10:23:11.997869+00:00'
---

## Background

Silver Bullet is an ICT concept Olya has identified as a future strategy candidate.
The Lab scouts it before she needs to invest time. Core pattern: 15m FVG formed
between 10:00-11:00 NY in the direction of daily bias, used as an entry mechanism.

## Method

1. Research ICT Silver Bullet methodology (variants, rules, exceptions)
2. Translate into Map configuration language:
   - regime: daily direction from Map (existing)
   - pda: 15m FVG (existing primitive, time-windowed to 10:00-11:00 NY)
   - gate: time window + regime alignment
3. Run detect.py on EURUSD 2021-2024 with 15m FVG detection
4. Filter for FVGs inside 10:00-11:00 NY window + regime alignment
5. Walk-forward validate on 2025-current
6. Overfitting review (frontier model when available)

## Constitution Grounding

- vLOCK.yaml: FVG primitive (L1)
- HTF_MAP_SPEC_v0_1.yaml: Map regime/direction
- ARS_CANON_v1_3.md: Kill zone time windows

