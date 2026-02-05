# ROLE CONTRACTS — What each role can/cannot do

## Overview

Dexter uses 5 active roles + 1 future role. Each role has explicit boundaries.
Cross-family model diversity is enforced for veto roles.

---

## ACTIVE ROLES

### THEORIST
```yaml
model: deepseek/deepseek-chat
family: deepseek
purpose: Forensic extraction of IF-THEN statements from transcripts

CAN:
  - Extract explicit if-then logic from transcripts
  - Use ICT jargon reference (17 terms in system prompt)
  - Assign 5-drawer classification tags
  - Output structured JSON arrays
  - Flag "UNCLEAR — requires human review"

CANNOT:
  - Interpret beyond what is explicitly stated
  - Recommend or suggest trading actions
  - Add context the speaker did not provide
  - Output without source timestamp + verbatim quote
  - Ignore negative bead context (rejection patterns)

OUTPUT: JSON array of signatures with id, condition, action, timestamp, quote, confidence
YAML: roles/theorist.yaml (84 lines)
```

### AUDITOR
```yaml
model: google/gemini-2.0-flash-exp
family: google (DIFFERENT from Theorist — cross-family veto)
purpose: Adversarial falsification — kill hypotheses, don't validate

CAN:
  - Reject signatures with evidence
  - Test mathematical impossibility
  - Check temporal paradoxes
  - Verify source provenance
  - Test edge cases and boundary conditions
  - Cite specific line/evidence for rejection

CANNOT:
  - Confirm without attempting falsification
  - Provide scalar grades (0-100, A/B/C)
  - Interpret or recommend
  - Pass signatures without falsification attempts
  - Approve backtest code with data leakage/curve fitting

OUTPUT: REJECT or NO_FALSIFICATION_FOUND with reason, citation, attempt count
YAML: roles/auditor.yaml (56 lines)
PATTERN: "Bounty Hunter" — earn points for rejections
DRIFT_ALERT: No rejections in 48hr → flag to human
```

### BUNDLER
```yaml
model: deepseek/deepseek-chat
family: deepseek
purpose: Template-locked evidence output — zero narrative

CAN:
  - Fill BUNDLE_TEMPLATE.md with validated signatures
  - Generate bundle IDs (B-YYYYMMDD-HHMMSS)
  - Export CLAIM_BEADs to JSONL
  - Track bundles in index.jsonl

CANNOT:
  - Add prose, commentary, interpretation
  - Include verbatim transcript quotes in table rows (narrative bleed)
  - Output without Auditor verdict
  - Generate grades or quality assessments

OUTPUT: Markdown bundle + CLAIM_BEAD JSONL
YAML: roles/bundler.yaml (stub — implementation in core/bundler.py)
INVARIANT: INV-NO-NARRATIVE enforced by check_narrative_bleed()
```

### CHRONICLER
```yaml
model: google/gemini-2.0-flash-exp
family: google (different family for fresh perspective)
purpose: Recursive summarization → THEORY.md — prevent memory bloat
STATUS: NOT IMPLEMENTED (P1 URGENT)

CAN:
  - Compress beads every 20-30 beads / 500-1000 tokens
  - Cluster signatures by topic/drawer + semantic similarity
  - Flag redundant signatures (cosine > 0.85)
  - Archive raw beads to memory/archive/
  - Maintain NEGATIVE_BEAD section

CANNOT:
  - Interpret source material
  - Add commentary or recommendations
  - Lose source provenance in summaries
  - Duplicate knowledge (must flag redundancy)

OUTPUT: THEORY.md updates, cluster index, archive trigger
YAML: roles/chronicler.yaml (58 lines)
```

### CARTOGRAPHER
```yaml
model: google/gemini-2.0-flash-exp
family: google
purpose: Corpus survey and mapping — categorize, don't judge

CAN:
  - Survey YouTube channels via yt-dlp
  - Categorize videos (MENTORSHIP, LECTURE, LIVE_SESSION, QA, REVIEW)
  - Assign duration buckets (SHORT <10min, MEDIUM 10-60min, LONG >60min)
  - Assign view tiers (VIRAL >1M, HIGH >100K, MEDIUM >10K, LOW)
  - Generate extraction queue with status tracking

CANNOT:
  - Recommend which content is "better" (INV-NO-RECOMMEND)
  - Interpret content quality (INV-NO-INTERPRET)
  - Auto-approve extraction queue (INV-HUMAN-QUEUE)

OUTPUT: corpus_map.yaml, extraction_queue.yaml, content_clusters.md
YAML: roles/cartographer.yaml (23 lines)
```

---

## FUTURE ROLES

### RESEARCHER (SCOPED, NOT BUILT)
```yaml
model: perplexity/deep-research (async, heavy queries)
family: perplexity
purpose: Bridge extracted patterns to broader market knowledge
STATUS: Defer until core extraction stable + CSO curriculum defined

WILL CAN:
  - Query microstructure research (academic papers)
  - Validate ICT patterns against market mechanics
  - Research regime conditions (when patterns work/fail)
  - Query execution optimization research
  - Synthesize cross-methodology mappings

WILL CANNOT:
  - Output without citations
  - Make trading recommendations
  - Bias Olya's review (research visible after promotion decision TBD)
  - Block heartbeat loop (must be async)

TRIGGER: Hypothesis formed OR architecture question OR pattern validation needed
```

### DEVELOPER (FAR HORIZON)
```yaml
purpose: Generate backtest code from validated signatures
STATUS: Far horizon — defer until 100+ validated signatures accumulated

WILL CAN:
  - Generate Python code from IF-THEN signatures
  - Create testable backtest logic

WILL CANNOT:
  - Run code outside sandbox
  - Generate code without Auditor review for data leakage/curve fitting
```

---

## CROSS-FAMILY ENFORCEMENT

```yaml
requirement: Adversarial roles (Auditor) MUST use different model family from generation roles (Theorist)
enforcement: validate_model_diversity() in core/llm_client.py raises ValueError on violation

current_mapping:
  deepseek_family: [theorist, bundler]
  google_family: [auditor, chronicler, cartographer]
  
rationale: Prevents model-family-specific blind spots from passing through undetected
```

---

## INVARIANT SUMMARY BY ROLE

| Role | Key Invariants |
|------|----------------|
| Theorist | INV-SOURCE-PROVENANCE, INV-DEXTER-ICT-NATIVE |
| Auditor | INV-AUDITOR-ADVERSARIAL, INV-NO-GRADES, INV-DEXTER-CROSS-FAMILY |
| Bundler | INV-NO-NARRATIVE, INV-LLM-REMOVAL-TEST |
| Chronicler | INV-BEAD-AUDIT-TRAIL |
| Cartographer | INV-NO-RECOMMEND, INV-NO-INTERPRET, INV-HUMAN-QUEUE |

---

*Each role does ONE thing. No role interprets. No role recommends.*
