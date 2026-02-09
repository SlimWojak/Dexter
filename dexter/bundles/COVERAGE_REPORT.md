# Dexter Coverage Report

*Generated: 2026-02-09T14:11:55.847822+00:00*

> "Show me you looked, not just what you found." - Olya

---

## Executive Summary

**Total Concepts:** 66
**Total Coverage Cells:** 198 (concepts x sources)

### Coverage Status

| Status | Count | Percentage |
|--------|-------|------------|
| FOUND | 77 | 38.9% |
| PARTIAL | 4 | 2.0% |
| ABSENT | 43 | 21.7% |
| PENDING | 74 | 37.4% |

**Effective Coverage:** 40.9% (FOUND + PARTIAL)

---

## Coverage by Source

| Source | FOUND | Total | Coverage |
|--------|-------|-------|----------|
| BLESSED_TRADER | 40 | 66 | 60.6% |
| ICT_2022 | 0 | 66 | 0.0% |
| OLYA_NOTES | 37 | 66 | 56.1% |

---

## Coverage by Drawer

| Drawer | Name | FOUND | Total | Coverage |
|--------|------|-------|-------|----------|
| drawer_1 | HTF Bias & Liquidity | 0 | 36 | 0.0% |
| drawer_2 | Time & Session | 0 | 36 | 0.0% |
| drawer_3 | Structure & Displacement | 0 | 36 | 0.0% |
| drawer_4 | Execution | 0 | 36 | 0.0% |
| drawer_5 | Protection & Risk | 0 | 30 | 0.0% |
| olya | Olya Extensions | 0 | 24 | 0.0% |

---

## Detailed Coverage Matrix

Legend: FOUND = extracted with evidence, PART = mentioned but incomplete, --- = not found, ... = not yet checked

### HTF Bias & Liquidity

| Concept | ICT 2022 | Blessed | Olya Notes |
|---------|----------|---------|------------|
| Three Questions Framework - Locatio | PART | FOUND | PART |
| Three Questions Framework - Objecti | PART | FOUND | PART |
| HTF Bullish Bias | FOUND | FOUND | FOUND |
| HTF Bearish Bias | FOUND | FOUND | FOUND |
| Dealing Range - Bullish Context | --- | FOUND | --- |
| Dealing Range - Bearish Context | --- | FOUND | --- |
| Draw on Liquidity - Buy-side | PART | FOUND | --- |
| Draw on Liquidity - Sell-side | PART | FOUND | --- |
| External Liquidity Objective - Bull | PART | FOUND | --- |
| External Liquidity Objective - Bear | PART | --- | --- |
| Internal Liquidity Objective - Bull | --- | --- | --- |
| Internal Liquidity Objective - Bear | --- | --- | --- |


### Time & Session

| Concept | ICT 2022 | Blessed | Olya Notes |
|---------|----------|---------|------------|
| Asia Session - Liquidity Build | FOUND | FOUND | --- |
| Midnight Open Reference | FOUND | FOUND | FOUND |
| Midnight Open as PD Reference | PART | FOUND | --- |
| London Killzone - Session Highs/Low | FOUND | FOUND | FOUND |
| London Killzone - Sweep Condition | FOUND | FOUND | --- |
| NY 08:30 Open Reference | PART | FOUND | --- |
| Pre-08:30 Judas/Manipulation | FOUND | FOUND | --- |
| 08:30+ Delivery Window | PART | --- | --- |
| NY AM Killzone | PART | FOUND | --- |
| Lunch Hours - Reduced Activity | PART | --- | --- |
| PM Session Disable | --- | --- | --- |
| London Setup via Asia Range Sweep | FOUND | FOUND | --- |


### Structure & Displacement

| Concept | ICT 2022 | Blessed | Olya Notes |
|---------|----------|---------|------------|
| Displacement - TRUE | PART | FOUND | FOUND |
| Displacement - FALSE | PART | FOUND | FOUND |
| Core 2022 Engine Event | PART | FOUND | FOUND |
| Bullish FVG Definition | --- | FOUND | FOUND |
| Bearish FVG Definition | --- | FOUND | FOUND |
| Market Structure Shift - Bearish | PART | FOUND | FOUND |
| Market Structure Shift - Bullish | PART | FOUND | FOUND |
| MSS Invalidation | PART | FOUND | FOUND |
| Liquidity Sweep - Bullish | FOUND | FOUND | FOUND |
| Liquidity Sweep - Bearish | FOUND | FOUND | FOUND |
| Swing High Definition | FOUND | FOUND | FOUND |
| Swing Low Definition | FOUND | FOUND | FOUND |


### Execution

| Concept | ICT 2022 | Blessed | Olya Notes |
|---------|----------|---------|------------|
| 2022 Model Setup VALID | PART | FOUND | PART |
| Limit Order - Short | PART | --- | FOUND |
| Limit Order - Long | PART | FOUND | FOUND |
| FVG Confirmation - Short | --- | FOUND | FOUND |
| FVG Confirmation - Long | --- | FOUND | FOUND |
| FVG Retrace Entry - Short | --- | FOUND | FOUND |
| FVG Retrace Entry - Long | --- | FOUND | FOUND |
| OTE Buy Zone | FOUND | FOUND | FOUND |
| OTE Sell Zone | FOUND | PART | FOUND |
| Premium/Discount Zones - Bullish | PART | FOUND | FOUND |
| Premium/Discount Zones - Bearish | PART | FOUND | FOUND |
| Intraday Dealing Range Definition | FOUND | FOUND | FOUND |


### Protection & Risk

| Concept | ICT 2022 | Blessed | Olya Notes |
|---------|----------|---------|------------|
| Breakeven at 1:1 RR | --- | --- | FOUND |
| Daily Loss Limit | PART | --- | FOUND |
| Stop Loss - Short | FOUND | --- | FOUND |
| Stop Loss - Long | FOUND | --- | FOUND |
| Nested SL Anchor | PART | --- | FOUND |
| Max Risk Rejection | FOUND | --- | FOUND |
| TP1 - Short | FOUND | --- | FOUND |
| TP1 - Long | FOUND | --- | FOUND |
| Runner Target | PART | --- | FOUND |
| Close on Structure Break Against | PART | --- | FOUND |


### Olya Extensions

| Concept | ICT 2022 | Blessed | Olya Notes |
|---------|----------|---------|------------|
| Breakeven-Only Trailing | PART | ... | --- |
| 3Q Ownership Boundary | --- | ... | --- |
| Fixed 1% Risk | PART | ... | --- |
| No Partial Exits | PART | ... | --- |
| No Re-entry Same Narrative | PART | ... | --- |
| No Position Scaling | PART | ... | --- |
| PDA Registry Pattern | --- | ... | --- |
| State Machine Warmup | --- | ... | --- |


---

## Coverage Gaps Analysis

### Concepts with No Evidence (All Sources ABSENT/PENDING)

- **CON-D1-INTLQ-01**: Internal Liquidity Objective - Bullish
- **CON-D1-INTLQ-02**: Internal Liquidity Objective - Bearish
- **CON-D2-TIME-11**: PM Session Disable
- **CON-OX-BLUR-001**: 3Q Ownership Boundary
- **CON-OX-PDA-REGISTRY**: PDA Registry Pattern
- **CON-OX-WARMUP**: State Machine Warmup


### Concepts with Partial Evidence Only

- **CON-D1-EXTLQ-02**: External Liquidity Objective - Bearish
- **CON-D2-TIME-08**: 08:30+ Delivery Window
- **CON-D2-TIME-10**: Lunch Hours - Reduced Activity
- **CON-OX-BE-ONLY**: Breakeven-Only Trailing
- **CON-OX-FIXED-RISK**: Fixed 1% Risk
- **CON-OX-NO-PARTIALS**: No Partial Exits
- **CON-OX-NO-REENTRY**: No Re-entry Same Narrative
- **CON-OX-NO-SCALING**: No Position Scaling

---

## Evidence Grade Distribution

Based on reference taxonomy evidence grades:

| Grade | Count | Description |
|-------|-------|-------------|
| MODERATE_EVIDENCE | 40 | Practitioner-backed, needs testing |
| PRACTITIONER_LORE | 1 | Widely taught, limited empirical backing |
| STRONG_EVIDENCE | 15 | Academic/peer-reviewed backing |
| UNIQUE | 10 | Olya-specific codification |

---

## Recommendations

- **ICT_2022**: Only 0.0% coverage. Run taxonomy-targeted extraction on remaining documents.
- **High Pending Rate**: 112% of cells still pending. Run `--scan-all` to process existing bundles.

---

## Report Metadata

- **Generated:** 2026-02-09T14:11:55.847822+00:00
- **Taxonomy Version:** 1.0
- **Coverage Matrix Version:** 1.0
- **Last Matrix Update:** 2026-02-09T14:11:55.640947+00:00

---

*Generated by Dexter Coverage Report Generator*