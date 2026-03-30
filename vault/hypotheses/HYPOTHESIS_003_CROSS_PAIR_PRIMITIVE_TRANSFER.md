---
track: TRACK_2_ROBUSTNESS_TESTING
status: ACTIVE
priority: P2
question: How do vLOCK primitives behave on GBPUSD and USDJPY compared to EURUSD?
  Which primitives transfer cleanly, which need recalibration?
time_budget: 1 overnight session
deliverable: vault/findings/CROSS_PAIR_TRANSFER_MATRIX.yaml
success_criteria:
- Transferability matrix produced for all primitives x 2 pairs
- At least one primitive category identified as GREEN across all 3 pairs
- Any RED primitives flagged with specific behavioural difference
created_at: '2026-03-30T10:23:11.998613+00:00'
updated_at: '2026-03-30T10:23:11.998615+00:00'
---

## Method

1. Run detect_runner on GBPUSD and USDJPY (2024 full year, once data available)
2. Compare per-primitive: detection count, average size, temporal distribution
3. Build transferability matrix:
   - GREEN: similar distribution to EURUSD (transfers cleanly)
   - AMBER: different scale but same pattern (needs parameter adjustment)
   - RED: fundamentally different behaviour (may not apply)
4. Focus on: FVG, BOS, CHoCH, OTE, Sweep (the chain-critical primitives)

## Constitution Grounding

- vLOCK.yaml: All 13 locked L1 primitives with EURUSD baseline parameters

## Data Dependency

Requires RiverWriter to have fetched GBPUSD + USDJPY back to at least 2024-01-01.
Can run partial analysis on whatever data is available.

