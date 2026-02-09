# Dexter Coverage Report

*Generated: 2026-02-09T13:14:16.661103+00:00*

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
| ICT_2022 | 0 | 66 | 0.0% |
| BLESSED_TRADER | 40 | 66 | 60.6% |
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
| HTF Bullish Bias | ... | FOUND | FOUND |
| HTF Bearish Bias | ... | FOUND | FOUND |
| Draw on Liquidity - Buy-side | ... | FOUND | --- |
| Draw on Liquidity - Sell-side | ... | FOUND | --- |
| Internal Liquidity Objective - Bull | ... | --- | --- |
| Internal Liquidity Objective - Bear | ... | --- | --- |
| External Liquidity Objective - Bull | ... | FOUND | --- |
| External Liquidity Objective - Bear | ... | --- | --- |
| Dealing Range - Bullish Context | ... | FOUND | --- |
| Dealing Range - Bearish Context | ... | FOUND | --- |
| Three Questions Framework - Locatio | ... | FOUND | PART |
| Three Questions Framework - Objecti | ... | FOUND | PART |


### Time & Session

| Concept | ICT 2022 | Blessed | Olya Notes |
|---------|----------|---------|------------|
| Asia Session - Liquidity Build | ... | FOUND | --- |
| Midnight Open Reference | ... | FOUND | FOUND |
| Midnight Open as PD Reference | ... | FOUND | --- |
| London Killzone - Session Highs/Low | ... | FOUND | FOUND |
| London Killzone - Sweep Condition | ... | FOUND | --- |
| NY 08:30 Open Reference | ... | FOUND | --- |
| Pre-08:30 Judas/Manipulation | ... | FOUND | --- |
| 08:30+ Delivery Window | ... | --- | --- |
| NY AM Killzone | ... | FOUND | --- |
| Lunch Hours - Reduced Activity | ... | --- | --- |
| PM Session Disable | ... | --- | --- |
| London Setup via Asia Range Sweep | ... | FOUND | --- |


### Structure & Displacement

| Concept | ICT 2022 | Blessed | Olya Notes |
|---------|----------|---------|------------|
| Swing High Definition | ... | FOUND | FOUND |
| Swing Low Definition | ... | FOUND | FOUND |
| Liquidity Sweep - Bullish | ... | FOUND | FOUND |
| Liquidity Sweep - Bearish | ... | FOUND | FOUND |
| Market Structure Shift - Bearish | ... | FOUND | FOUND |
| Market Structure Shift - Bullish | ... | FOUND | FOUND |
| MSS Invalidation | ... | FOUND | FOUND |
| Bullish FVG Definition | ... | FOUND | FOUND |
| Bearish FVG Definition | ... | FOUND | FOUND |
| Displacement - TRUE | ... | FOUND | FOUND |
| Displacement - FALSE | ... | FOUND | FOUND |
| Core 2022 Engine Event | ... | FOUND | FOUND |


### Execution

| Concept | ICT 2022 | Blessed | Olya Notes |
|---------|----------|---------|------------|
| Intraday Dealing Range Definition | ... | FOUND | FOUND |
| Premium/Discount Zones - Bullish | ... | FOUND | FOUND |
| Premium/Discount Zones - Bearish | ... | FOUND | FOUND |
| OTE Buy Zone | ... | FOUND | FOUND |
| OTE Sell Zone | ... | PART | FOUND |
| FVG Confirmation - Short | ... | FOUND | FOUND |
| FVG Confirmation - Long | ... | FOUND | FOUND |
| FVG Retrace Entry - Short | ... | FOUND | FOUND |
| FVG Retrace Entry - Long | ... | FOUND | FOUND |
| Limit Order - Short | ... | --- | FOUND |
| Limit Order - Long | ... | FOUND | FOUND |
| 2022 Model Setup VALID | ... | FOUND | PART |


### Protection & Risk

| Concept | ICT 2022 | Blessed | Olya Notes |
|---------|----------|---------|------------|
| Stop Loss - Short | ... | --- | FOUND |
| Stop Loss - Long | ... | --- | FOUND |
| Nested SL Anchor | ... | --- | FOUND |
| Max Risk Rejection | ... | --- | FOUND |
| TP1 - Short | ... | --- | FOUND |
| TP1 - Long | ... | --- | FOUND |
| Runner Target | ... | --- | FOUND |
| Close on Structure Break Against | ... | --- | FOUND |
| Breakeven at 1:1 RR | ... | --- | FOUND |
| Daily Loss Limit | ... | --- | FOUND |


### Olya Extensions

| Concept | ICT 2022 | Blessed | Olya Notes |
|---------|----------|---------|------------|
| PDA Registry Pattern | ... | ... | --- |
| State Machine Warmup | ... | ... | --- |
| 3Q Ownership Boundary | ... | ... | --- |
| No Partial Exits | ... | ... | --- |
| No Re-entry Same Narrative | ... | ... | --- |
| No Position Scaling | ... | ... | --- |
| Fixed 1% Risk | ... | ... | --- |
| Breakeven-Only Trailing | ... | ... | --- |


---

## Coverage Gaps Analysis

### Concepts with No Evidence (All Sources ABSENT/PENDING)

- **CON-D1-INTLQ-01**: Internal Liquidity Objective - Bullish
- **CON-D1-INTLQ-02**: Internal Liquidity Objective - Bearish
- **CON-D1-EXTLQ-02**: External Liquidity Objective - Bearish
- **CON-D2-TIME-08**: 08:30+ Delivery Window
- **CON-D2-TIME-10**: Lunch Hours - Reduced Activity
- **CON-D2-TIME-11**: PM Session Disable
- **CON-OX-PDA-REGISTRY**: PDA Registry Pattern
- **CON-OX-WARMUP**: State Machine Warmup
- **CON-OX-BLUR-001**: 3Q Ownership Boundary
- **CON-OX-NO-PARTIALS**: No Partial Exits
- **CON-OX-NO-REENTRY**: No Re-entry Same Narrative
- **CON-OX-NO-SCALING**: No Position Scaling
- **CON-OX-FIXED-RISK**: Fixed 1% Risk
- **CON-OX-BE-ONLY**: Breakeven-Only Trailing


### Concepts with Partial Evidence Only

*No concepts with only partial evidence.*

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
- **Coverage Gaps**: 14 concepts have no evidence from any source. Review source selection or extraction quality.

---

## Report Metadata

- **Generated:** 2026-02-09T13:14:16.661103+00:00
- **Taxonomy Version:** 1.0
- **Coverage Matrix Version:** 1.0
- **Last Matrix Update:** 2026-02-09T13:13:48.555229+00:00

---

*Generated by Dexter Coverage Report Generator*