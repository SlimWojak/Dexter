# Dexter Coverage Report

*Generated: 2026-02-09T11:28:05.792135+00:00*

> "Show me you looked, not just what you found." - Olya

---

## Executive Summary

**Total Concepts:** 66
**Total Coverage Cells:** 198 (concepts x sources)

### Coverage Status

| Status | Count | Percentage |
|--------|-------|------------|
| FOUND | 40 | 20.2% |
| PARTIAL | 1 | 0.5% |
| ABSENT | 17 | 8.6% |
| PENDING | 140 | 70.7% |

**Effective Coverage:** 20.7% (FOUND + PARTIAL)

---

## Coverage by Source

| Source | FOUND | Total | Coverage |
|--------|-------|-------|----------|
| ICT_2022 | 0 | 66 | 0.0% |
| BLESSED_TRADER | 40 | 66 | 60.6% |
| OLYA_NOTES | 0 | 66 | 0.0% |

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
| HTF Bullish Bias | ... | FOUND | ... |
| HTF Bearish Bias | ... | FOUND | ... |
| Draw on Liquidity - Buy-side | ... | FOUND | ... |
| Draw on Liquidity - Sell-side | ... | FOUND | ... |
| Internal Liquidity Objective - Bull | ... | --- | ... |
| Internal Liquidity Objective - Bear | ... | --- | ... |
| External Liquidity Objective - Bull | ... | FOUND | ... |
| External Liquidity Objective - Bear | ... | --- | ... |
| Dealing Range - Bullish Context | ... | FOUND | ... |
| Dealing Range - Bearish Context | ... | FOUND | ... |
| Three Questions Framework - Locatio | ... | FOUND | ... |
| Three Questions Framework - Objecti | ... | FOUND | ... |


### Time & Session

| Concept | ICT 2022 | Blessed | Olya Notes |
|---------|----------|---------|------------|
| Asia Session - Liquidity Build | ... | FOUND | ... |
| Midnight Open Reference | ... | FOUND | ... |
| Midnight Open as PD Reference | ... | FOUND | ... |
| London Killzone - Session Highs/Low | ... | FOUND | ... |
| London Killzone - Sweep Condition | ... | FOUND | ... |
| NY 08:30 Open Reference | ... | FOUND | ... |
| Pre-08:30 Judas/Manipulation | ... | FOUND | ... |
| 08:30+ Delivery Window | ... | --- | ... |
| NY AM Killzone | ... | FOUND | ... |
| Lunch Hours - Reduced Activity | ... | --- | ... |
| PM Session Disable | ... | --- | ... |
| London Setup via Asia Range Sweep | ... | FOUND | ... |


### Structure & Displacement

| Concept | ICT 2022 | Blessed | Olya Notes |
|---------|----------|---------|------------|
| Swing High Definition | ... | FOUND | ... |
| Swing Low Definition | ... | FOUND | ... |
| Liquidity Sweep - Bullish | ... | FOUND | ... |
| Liquidity Sweep - Bearish | ... | FOUND | ... |
| Market Structure Shift - Bearish | ... | FOUND | ... |
| Market Structure Shift - Bullish | ... | FOUND | ... |
| MSS Invalidation | ... | FOUND | ... |
| Bullish FVG Definition | ... | FOUND | ... |
| Bearish FVG Definition | ... | FOUND | ... |
| Displacement - TRUE | ... | FOUND | ... |
| Displacement - FALSE | ... | FOUND | ... |
| Core 2022 Engine Event | ... | FOUND | ... |


### Execution

| Concept | ICT 2022 | Blessed | Olya Notes |
|---------|----------|---------|------------|
| Intraday Dealing Range Definition | ... | FOUND | ... |
| Premium/Discount Zones - Bullish | ... | FOUND | ... |
| Premium/Discount Zones - Bearish | ... | FOUND | ... |
| OTE Buy Zone | ... | FOUND | ... |
| OTE Sell Zone | ... | PART | ... |
| FVG Confirmation - Short | ... | FOUND | ... |
| FVG Confirmation - Long | ... | FOUND | ... |
| FVG Retrace Entry - Short | ... | FOUND | ... |
| FVG Retrace Entry - Long | ... | FOUND | ... |
| Limit Order - Short | ... | --- | ... |
| Limit Order - Long | ... | FOUND | ... |
| 2022 Model Setup VALID | ... | FOUND | ... |


### Protection & Risk

| Concept | ICT 2022 | Blessed | Olya Notes |
|---------|----------|---------|------------|
| Stop Loss - Short | ... | --- | ... |
| Stop Loss - Long | ... | --- | ... |
| Nested SL Anchor | ... | --- | ... |
| Max Risk Rejection | ... | --- | ... |
| TP1 - Short | ... | --- | ... |
| TP1 - Long | ... | --- | ... |
| Runner Target | ... | --- | ... |
| Close on Structure Break Against | ... | --- | ... |
| Breakeven at 1:1 RR | ... | --- | ... |
| Daily Loss Limit | ... | --- | ... |


### Olya Extensions

| Concept | ICT 2022 | Blessed | Olya Notes |
|---------|----------|---------|------------|
| PDA Registry Pattern | ... | ... | ... |
| State Machine Warmup | ... | ... | ... |
| 3Q Ownership Boundary | ... | ... | ... |
| No Partial Exits | ... | ... | ... |
| No Re-entry Same Narrative | ... | ... | ... |
| No Position Scaling | ... | ... | ... |
| Fixed 1% Risk | ... | ... | ... |
| Breakeven-Only Trailing | ... | ... | ... |


---

## Coverage Gaps Analysis

### Concepts with No Evidence (All Sources ABSENT/PENDING)

- **CON-D1-INTLQ-01**: Internal Liquidity Objective - Bullish
- **CON-D1-INTLQ-02**: Internal Liquidity Objective - Bearish
- **CON-D1-EXTLQ-02**: External Liquidity Objective - Bearish
- **CON-D2-TIME-08**: 08:30+ Delivery Window
- **CON-D2-TIME-10**: Lunch Hours - Reduced Activity
- **CON-D2-TIME-11**: PM Session Disable
- **CON-D4-ENTRY-01**: Limit Order - Short
- **CON-D5-RISK-01**: Stop Loss - Short
- **CON-D5-RISK-02**: Stop Loss - Long
- **CON-D5-RISK-03**: Nested SL Anchor
- **CON-D5-RISK-04**: Max Risk Rejection
- **CON-D5-TP-01**: TP1 - Short
- **CON-D5-TP-02**: TP1 - Long
- **CON-D5-TP-03**: Runner Target
- **CON-D5-TP-04**: Close on Structure Break Against
- **CON-D5-MGMT-01**: Breakeven at 1:1 RR
- **CON-D5-MGMT-02**: Daily Loss Limit
- **CON-OX-PDA-REGISTRY**: PDA Registry Pattern
- **CON-OX-WARMUP**: State Machine Warmup
- **CON-OX-BLUR-001**: 3Q Ownership Boundary
- **CON-OX-NO-PARTIALS**: No Partial Exits
- **CON-OX-NO-REENTRY**: No Re-entry Same Narrative
- **CON-OX-NO-SCALING**: No Position Scaling
- **CON-OX-FIXED-RISK**: Fixed 1% Risk
- **CON-OX-BE-ONLY**: Breakeven-Only Trailing


### Concepts with Partial Evidence Only

- **CON-D4-OTE-02**: OTE Sell Zone

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
- **OLYA_NOTES**: Only 0.0% coverage. Run taxonomy-targeted extraction on remaining documents.
- **High Pending Rate**: 212% of cells still pending. Run `--scan-all` to process existing bundles.
- **Coverage Gaps**: 25 concepts have no evidence from any source. Review source selection or extraction quality.

---

## Report Metadata

- **Generated:** 2026-02-09T11:28:05.792135+00:00
- **Taxonomy Version:** 1.0
- **Coverage Matrix Version:** 1.0
- **Last Matrix Update:** 2026-02-09T11:28:05.630916+00:00

---

*Generated by Dexter Coverage Report Generator*