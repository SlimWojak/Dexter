# Theorist Diagnostic Report

```yaml
date: 2026-02-09
issue: 10 of 18 Blessed PDFs returned 0 signatures in Stage 2
hypothesis: MODEL_ROUTING | PROMPT_ISSUE | CONTENT_THIN
method: Direct API comparison (DeepSeek vs Sonnet) on same vision content
```

---

## Executive Summary

**Diagnosis: PIPELINE_INTEGRATION (not MODEL_ROUTING)**

Direct API calls to both DeepSeek and Sonnet successfully extract signatures from the same vision content that returned 0 in the full pipeline. This indicates the issue is NOT with model capability, but with how content flows through the extraction pipeline.

---

## Test Results

### Test 1: Liquidity_PDF_Blessed_TRD (Page 12)

**Vision Content Quality**: EXCELLENT
- Clear IF-THEN statement in source:
  > "WHEN THE PRICE IS GOING SIDEWAYS (CONSOLIDATING) THE LIQUIDITY (RETAIL STOPS) ARE BUILDING ABOVE & BELOW IT, AND IN MOST CASES PRICE WILL WANT TO SWEEP BOTH SIDES BEFORE PICKING A DIRECTION."

| Model | Signatures | Response Size | Quality |
|-------|------------|---------------|---------|
| DeepSeek (deepseek/deepseek-chat) | 1 | 416 chars | Good - combined into single rule |
| Sonnet (claude-sonnet-4-5-20250929) | 2 | 601 chars | Better - split into atomic rules |

**DeepSeek Output:**
```json
[
  {
    "id": "S-001",
    "if": "price is going sideways (consolidating)",
    "then": "price will sweep both buy-side and sell-side liquidity zones before picking a direction",
    "source_quote": "WHEN THE PRICE IS GOING SIDEWAYS...",
    "drawer": 2
  }
]
```

**Sonnet Output:**
```json
[
  {
    "id": "S-001",
    "if": "price is going sideways (consolidating)",
    "then": "liquidity (retail stops) are building above & below it",
    "source_quote": "WHEN THE PRICE IS GOING SIDEWAYS...",
    "drawer": 2
  },
  {
    "id": "S-002",
    "if": "price is consolidating with liquidity above and below",
    "then": "price will want to sweep both sides before picking a direction",
    "source_quote": "IN MOST CASES PRICE WILL WANT TO SWEEP BOTH SIDES...",
    "drawer": 1
  }
]
```

**Verdict**: Both models succeed. Sonnet produces more atomic signatures (better for validation).

---

### Test 2: Orderblock_Propulsion_Block_Breaker (Pages 3-4)

**Vision Content Quality**: TITLE SLIDE (no methodology content)
- Page 3: Educational title "ORDERBLOCK / PROPULSION BLOCK / BREAKER" with branding
- Page 4: Similar structural content without IF-THEN rules

| Model | Signatures | Notes |
|-------|------------|-------|
| DeepSeek | 0 | Correctly returned [] |
| Sonnet | 0 | Correctly returned [] |

**Verdict**: Both models correctly return empty arrays for content-thin pages. The Orderblock PDF may have methodology on later pages, but pages 3-4 are legitimately empty of extractable rules.

---

## Root Cause Analysis

### Why Full Pipeline Returned 0 When Direct API Succeeds

The discrepancy reveals a **pipeline integration issue**, not a model issue:

1. **Chunking Boundaries**: The full pipeline chunks documents before extraction. The IF-THEN content may be split across chunk boundaries, making individual chunks appear content-thin.

2. **Vision Description Format**: The full pipeline may format vision descriptions differently than the direct test, potentially stripping key context.

3. **Processing Path**: The Liquidity PDF was processed in Stage 2 (confirmed in inventory), but returned 0 signatures. Yet the same vision content extracts 1-2 signatures via direct API.

4. **Possible Token Truncation**: If vision descriptions exceed token limits, the IF-THEN content may be truncated before reaching Theorist.

---

## Diagnosis Matrix

| Hypothesis | Evidence | Verdict |
|------------|----------|---------|
| MODEL_ROUTING | Both models extract when given good content | RULED OUT |
| PROMPT_ISSUE | Same prompt works in direct test | RULED OUT |
| CONTENT_THIN | Orderblock pages 3-4 are thin, but Liquidity p12 is rich | PARTIAL (some PDFs genuinely thin) |
| PIPELINE_INTEGRATION | Direct API succeeds where pipeline fails | **CONFIRMED** |

---

## Recommendations

### Immediate (P0)
1. **Audit chunking logic** in `skills/document/pdf_ingester.py` - verify IF-THEN statements aren't split across chunks
2. **Log vision descriptions** at extraction time to verify they match direct test format
3. **Verify token limits** - ensure vision descriptions aren't truncated before Theorist

### Short-term (P1)
1. **Re-extract Liquidity PDF** with debug logging to capture exact content sent to Theorist
2. **Add pipeline telemetry** - log chunk boundaries, token counts, and raw API inputs
3. **Consider Sonnet for LATERAL tier** - produces more atomic signatures (2 vs 1)

### Long-term (P2)
1. **Page-level extraction** for image-heavy PDFs (bypass chunking entirely)
2. **Vision-aware chunking** - chunk after vision extraction, not before
3. **Quality gate on vision output** - flag pages with <500 chars for manual review

---

## Test Artifacts

| File | Purpose |
|------|---------|
| `data/audit/theorist_diagnostic_results.json` | Raw API response comparison |
| `data/audit/liquidity_p12_vision.txt` | Vision description used for testing |
| `data/audit/orderblock_p3_vision.txt` | Title page vision (expected empty) |

---

## Conclusion

The 0-signature issue is NOT a model capability problem. Both DeepSeek and Sonnet successfully extract when given properly formatted vision content. The root cause is in the pipeline layer - likely chunking or formatting differences between full run and direct API.

**Next Step**: Audit the extraction pipeline to identify where content is lost between vision extraction and Theorist invocation.

---

*Diagnostic complete. Pipeline audit recommended.*
