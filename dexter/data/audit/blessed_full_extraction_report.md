# Blessed Trader Full Extraction Report

```yaml
extraction_date: 2026-02-09
source: blessed_training (18 PDFs)
tier: LATERAL
vision_model: claude-sonnet-4-5-20250929
theorist_model: deepseek/deepseek-chat
auditor_model: gemini-3-flash
```

---

## Executive Summary

| Metric | Stage 2 | Full Rerun | Change |
|--------|---------|------------|--------|
| PDFs processed | 2 | 18 | +16 |
| Signatures extracted | 10 | 55 | +45 |
| Signatures validated | 10 | 53 | +43 |
| Signatures rejected | 0 | 2 | +2 |
| Bundles created | 2 | 8 | +6 |
| Rejection rate | 0% | 3.6% | +3.6% |

**Outcome:** 5.3x increase in validated signatures compared to Stage 2.

---

## Per-PDF Results

| Filename | Pages | Extracted | Validated | Rejected | Bundle |
|----------|-------|-----------|-----------|----------|--------|
| EU_DXY_SMT_Divergence. (1).pdf | 11 | 0 | 0 | 0 | - |
| Lesson_10_PDF (2).pdf | 40 | 10 | 10 | 0 | B-20260209-074215 |
| Lesson_11_PDF_-_M (6).pdf | 24 | 0 | 0 | 0 | - |
| Lesson_12_PDF (1).pdf | 29 | 6 | 5 | 1 | B-20260209-074500 |
| Lesson_15_PDF (3).pdf | 26 | 0 | 0 | 0 | - |
| Lesson_16_PDF (3).pdf | 25 | 0 | 0 | 0 | - |
| Lesson_17_PDF (2).pdf | 36 | 0 | 0 | 0 | - |
| Lesson_18_PDF (4).pdf | 20 | 8 | 8 | 0 | B-20260209-075814 |
| Lesson_19_PDF (4).pdf | 16 | 10 | 10 | 0 | B-20260209-075919 |
| Lesson_20_PDF (4).pdf | 42 | 0 | 0 | 0 | - |
| Lesson_21_PDF (3).pdf | 22 | 5 | 4 | 1 | B-20260209-080419 |
| Lesson_5_PDF (2).pdf | 20 | 0 | 0 | 0 | - |
| Lesson_6_PDF (3).pdf | 21 | 6 | 6 | 0 | B-20260209-080901 |
| Lesson_7_PDF (3).pdf | 53 | 5 | 5 | 0 | B-20260209-081742 |
| Lesson_8_PDF (3).pdf | 27 | 5 | 5 | 0 | B-20260209-081956 |
| Liquidity_PDF_Blessed_TRD (4).pdf | 25 | 0 | 0 | 0 | - |
| Orderblock_Propulsion_Block_Breaker (3).pdf | 16 | 0 | 0 | 0 | - |
| Weekly__Daily_Structure___Price_Delivery (2).pdf | 12 | 0 | 0 | 0 | - |

**Total:** 465 pages, 55 extracted, 53 validated, 2 rejected

---

## Bundles Created

| Bundle ID | Source PDF | Validated | Rejected |
|-----------|------------|-----------|----------|
| B-20260209-074215 | Lesson_10_PDF (2).pdf | 10 | 0 |
| B-20260209-074500 | Lesson_12_PDF (1).pdf | 5 | 1 |
| B-20260209-075814 | Lesson_18_PDF (4).pdf | 8 | 0 |
| B-20260209-075919 | Lesson_19_PDF (4).pdf | 10 | 0 |
| B-20260209-080419 | Lesson_21_PDF (3).pdf | 4 | 1 |
| B-20260209-080901 | Lesson_6_PDF (3).pdf | 6 | 0 |
| B-20260209-081742 | Lesson_7_PDF (3).pdf | 5 | 0 |
| B-20260209-081956 | Lesson_8_PDF (3).pdf | 5 | 0 |

---

## PDFs with Zero Signatures (10 of 18)

| PDF | Pages | Possible Reason |
|-----|-------|-----------------|
| EU_DXY_SMT_Divergence | 11 | Concept-focused, may lack explicit IF-THEN rules |
| Lesson_11_PDF_-_M | 24 | Theorist returned 2 tokens — possible prompt issue |
| Lesson_15 | 26 | Theorist returned 2 tokens |
| Lesson_16 | 25 | Theorist returned 2 tokens |
| Lesson_17 | 36 | Theorist returned 2 tokens |
| Lesson_20 | 42 | Theorist returned 2 tokens |
| Lesson_5 | 20 | Theorist returned 2 tokens |
| Liquidity_PDF_Blessed_TRD | 25 | **UNEXPECTED** — Vision audit showed rich IF-THEN content |
| Orderblock_Propulsion_Block | 16 | **UNEXPECTED** — Core ICT concepts |
| Weekly__Daily_Structure | 12 | **UNEXPECTED** — Structural methodology |

**Concern:** Three PDFs (Liquidity, Orderblock, Weekly_Daily) should have IF-THEN content based on their topics but returned 0 signatures. DeepSeek Theorist may be failing on certain content patterns.

---

## Analysis

### What Worked
1. Vision extraction successfully processed 465 pages
2. 8 PDFs produced meaningful signature counts
3. Auditor rejected 2 signatures (3.6% rate — healthy)
4. 5.3x improvement over Stage 2

### What Needs Investigation
1. **10 PDFs returned 0 signatures** — Some expected:
   - SMT_Divergence: Concept explanation, not IF-THEN rules
   - Some lessons may be examples without explicit rules

2. **DeepSeek short responses** — Many chunks returned only 1-2 tokens:
   - Possible prompt issue
   - Model may not understand extraction format
   - Need to check actual LLM responses

3. **Liquidity PDF gap** — Vision audit showed:
   - "BUY-SIDE LIQUIDITY", "SELL-SIDE LIQUIDITY" detected
   - "PRICE WILL WANT TO SWEEP BOTH SIDES BEFORE PICKING A DIRECTION"
   - This IS IF-THEN content but Theorist returned 0

### Recommendations
1. **Investigate Theorist prompt** — Why is DeepSeek returning 1-2 tokens on some content?
2. **Manual review of Liquidity PDF** — Confirm if extractable content exists
3. **Consider Theorist model change** — Test Sonnet for LATERAL tier if DeepSeek underperforms
4. **Taxonomy-targeted extraction** — May help force extraction from concept-rich PDFs

---

## Cost Summary

| Component | Estimated Cost |
|-----------|----------------|
| Vision (Sonnet, ~300 pages) | ~$3.50 |
| Theorist (DeepSeek, 18 PDFs) | ~$0.02 |
| Auditor (Gemini Flash) | ~$0.01 |
| **Total** | ~$3.53 |

---

## Comparison to Brief Expectations

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| Signatures from 18 PDFs | 30-50 | 53 | EXCEEDED |
| PDFs producing signatures | 12-15 | 8 | BELOW |
| Bundles created | 10+ | 8 | CLOSE |

**Assessment:** Total signature count exceeded expectations (53 vs 30-50), but fewer PDFs contributed than expected. The yield is concentrated in 8 PDFs with 10 producing nothing.

---

## Next Steps

1. Create Task 3 commit
2. Proceed to Task 4: Concept Mapping
3. Flag Theorist underperformance to CTO for potential prompt tuning

---

*Full extraction complete. Vision skill validated. Theorist behavior requires investigation.* 🔬
