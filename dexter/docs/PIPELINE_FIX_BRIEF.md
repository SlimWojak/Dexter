# Pipeline Fix Brief — Content Loss Diagnostic

```yaml
date: 2026-02-09
priority: P0 (blocks taxonomy build)
estimated_time: 1-2 hours
gate: 10 zero-signature PDFs must yield signatures after fix
```

---

## Context

Theorist diagnostic confirmed: Direct API calls extract 1-2 signatures from Liquidity PDF content, but full pipeline returns 0. Content is lost somewhere between vision extraction and Theorist invocation.

**Evidence:**
- Liquidity PDF p12 via direct API: DeepSeek=1, Sonnet=2 signatures
- Liquidity PDF via full pipeline: 0 signatures
- Same vision description, different results

---

## Objective

Find and fix the content loss point in the extraction pipeline.

---

## Step 1: Add Pipeline Telemetry

### 1.1 Identify instrumentation points

```
PDF → Vision Extraction → [POINT A] → Chunking → [POINT B] → Theorist → [POINT C] → Output
```

Add logging at:
- **POINT A**: Raw vision description (post-extraction, pre-chunking)
- **POINT B**: Chunked content sent to Theorist (exact API payload)
- **POINT C**: Theorist raw response (before parsing)

### 1.2 Files to instrument

| File | Purpose | Add |
|------|---------|-----|
| `skills/document/pdf_ingester.py` | PDF → chunks | Log chunk boundaries + content |
| `skills/extraction/theorist.py` | Chunks → API | Log exact payload sent to model |
| `scripts/run_source_extraction.py` | Orchestrator | Log vision description pre-chunking |

### 1.3 Telemetry format

```python
# Add to each instrumentation point
import json
from pathlib import Path

def log_pipeline_stage(stage: str, source: str, content: str, metadata: dict = None):
    """Log content at pipeline stage for debugging."""
    log_dir = Path("data/audit/pipeline_telemetry")
    log_dir.mkdir(parents=True, exist_ok=True)

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "stage": stage,
        "source": source,
        "content_chars": len(content),
        "content_preview": content[:500],
        "content_full": content,
        "metadata": metadata or {}
    }

    log_file = log_dir / f"{source.replace('/', '_')}_{stage}.json"
    with open(log_file, "w") as f:
        json.dump(log_entry, f, indent=2)
```

---

## Step 2: Re-extract Liquidity PDF with Logging

### 2.1 Run single PDF with telemetry enabled

```bash
# Set debug flag
export DEXTER_PIPELINE_DEBUG=true

# Run single PDF extraction
python scripts/run_source_extraction.py \
  --source "data/sources/blessed_trader/Liquidity_PDF_Blessed_TRD.pdf" \
  --tier LATERAL \
  --vision-extract
```

### 2.2 Compare telemetry to direct test

| Check | Direct Test | Pipeline | Delta |
|-------|-------------|----------|-------|
| Vision chars | 2218 | ? | Should match |
| Content to Theorist | 2218 | ? | If < 2218, found the loss |
| Chunks created | 1 | ? | If > 1, chunking is splitting |

---

## Step 3: Identify and Fix Content Loss

### Hypothesis A: Chunking splits IF-THEN content

**Symptom:** Multiple chunks created, each too small for extraction
**Fix:** Set minimum chunk size or disable chunking for vision-extracted content

```python
# In pdf_ingester.py
if vision_extracted:
    # Don't chunk vision descriptions — they're already atomic
    return [full_vision_content]
```

### Hypothesis B: Vision description truncated

**Symptom:** Content at POINT A is shorter than expected
**Fix:** Increase token limit in vision extraction call

### Hypothesis C: Formatting stripped

**Symptom:** Content chars match but structure lost (newlines, etc.)
**Fix:** Preserve original formatting through pipeline

### Hypothesis D: Wrong content passed to Theorist

**Symptom:** Theorist receives different content than vision output
**Fix:** Trace data flow, fix handoff

---

## Step 4: Re-run Zero-Signature PDFs

### 4.1 Target list (10 PDFs)

```yaml
zero_signature_pdfs:
  # High-priority (should have content based on topics)
  - Liquidity_PDF_Blessed_TRD (4).pdf        # LITMUS TEST — vision showed IF-THEN
  - Orderblock_Propulsion_Block_Breaker (3).pdf  # Core ICT concepts
  - Weekly__Daily_Structure___Price_Delivery (2).pdf  # Structural methodology

  # Medium-priority (Theorist returned 2 tokens — likely `[]`)
  - Lesson_11_PDF_-_M (6).pdf   # 24 pages, CBDR/Sessions
  - Lesson_15_PDF (3).pdf       # 26 pages
  - Lesson_16_PDF (3).pdf       # 25 pages
  - Lesson_17_PDF (2).pdf       # 36 pages
  - Lesson_20_PDF (4).pdf       # 42 pages
  - Lesson_5_PDF (2).pdf        # 20 pages

  # Lower priority
  - EU_DXY_SMT_Divergence. (1).pdf  # May be concept-only, no IF-THEN
```

### 4.2 Validation criteria

| PDF | Stage 2 Sigs | Post-Fix Sigs | Status |
|-----|--------------|---------------|--------|
| Liquidity | 0 | ≥1 | MUST PASS |
| Orderblock | 0 | ≥0 | May be genuinely thin |
| Others | 0 | ≥0 | Check for improvement |

**Gate:** At least 3 of the 10 must yield signatures after fix. Liquidity is the litmus test.

---

## Step 5: Commit and Document

### 5.1 Commit sequence

```bash
# After telemetry added
git commit -m "[Pipeline] Add extraction telemetry for debugging"

# After fix identified
git commit -m "[Pipeline] Fix content loss in <location>"

# After re-extraction validated
git commit -m "[Pipeline] Blessed re-extraction — N PDFs now yield signatures"
```

### 5.2 Update DEXTER_MANIFEST

```yaml
pipeline_fix:
  issue: Content lost between vision and Theorist
  root_cause: <discovered during fix>
  fix: <applied fix>
  validation: N/10 zero-sig PDFs now yield signatures
```

---

## Done Criteria

- [ ] Telemetry added at 3 pipeline points
- [ ] Liquidity PDF re-extracted with logging
- [ ] Content loss point identified
- [ ] Fix applied
- [ ] 10 zero-signature PDFs re-extracted
- [ ] At least 3/10 now yield signatures (Liquidity must pass)
- [ ] Committed and pushed
- [ ] DEXTER_MANIFEST updated

---

## Then: Taxonomy Build

Once pipeline fix validated, proceed to taxonomy implementation (Phases 1-4 from taxonomy brief). No model routing changes needed — pipeline now delivers full content.

---

*Surgical fix. Find the leak. Patch it. Move on.*
