---
track: TRACK_4_MAP_DYNAMICS_LAB
status: ACTIVE
priority: P2
question: How stable is the Map over a 2-year EURUSD horizon? Does it produce sensible
  regime durations, or does it oscillate excessively?
time_budget: 1 overnight session
deliverable: vault/findings/MAP_STABILITY_2023_2025.yaml
success_criteria:
- Regime durations cluster in sensible ranges (not single-day oscillation)
- Dealing range extremes show reasonable spread
- PDA count stays bounded (not unbounded accumulation over months)
- Any period with >3 regime changes per week flagged as instability
created_at: '2026-03-30T10:23:11.998313+00:00'
updated_at: '2026-03-30T10:23:11.998316+00:00'
---

## Method

1. Load EURUSD daily + 4H data from RiverWriter (once 2023-2025 data available)
2. Run structure detection daily to produce displacement/MSS events
3. Feed events into Map engine day-by-day (simulating real-time)
4. Record: regime at each point, dealing range boundaries, PDA count
5. Measure:
   - Regime flip frequency (expect: <2 per month in trending, more in ranging)
   - Dealing range duration (expect: days to weeks, not hours)
   - PDA accumulation rate (expect: manageable, not explosion)
   - Any period with >3 regime changes per week (flag as instability)

## Constitution Grounding

- HTF_MAP_SPEC_v0_1.yaml: Map architecture, regime definitions
- STATE_DETECTION_v2.yaml: State/regime classification logic
- vLOCK.yaml: Displacement, MSS primitives

## Data Dependency

Requires RiverWriter to have fetched back to at least 2023-01-01.
Currently fetching -- check with: cd ~/lab/data/river && python3 run.py --status

