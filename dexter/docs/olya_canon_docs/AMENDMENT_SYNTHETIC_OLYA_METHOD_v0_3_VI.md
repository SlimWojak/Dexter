# AMENDMENT REQUEST
## File: `SYNTHETIC_OLYA_METHOD_final_v0_3.yaml`
## Subject: Volume Imbalance (VI) — New Concept Addition
## Date: 2026-02-24
## Requested by: Olya (CSO)
## Version bump: v0.3 → v0.4

---

## DECISION

Volume Imbalance (VI) is to be treated as equal to FVG in all trading logic.

Both types must be **detected separately** and **named separately** in system outputs, but handled identically in entry, management, and exit logic.

**Why this is needed:** Interactive Brokers data feed sometimes produces body-to-body gaps (VI) where Forex.com would show a wick-to-wick gap (FVG). Both are valid reaction zones.

---

## DEFINITIONS

| Concept | Definition |
|---------|-----------|
| **FVG (Fair Value Gap)** | Three-candle imbalance. Candle A wick high < Candle C wick low (bullish), or Candle A wick low > Candle C wick high (bearish). Wick-to-wick gap. |
| **VI (Volume Imbalance)** | Three-candle imbalance. Candle A body top < Candle C body bottom (bullish), or Candle A body bottom > Candle C body top (bearish). Body-to-body gap. Wicks may overlap. |

**Respect rule (applies to both):**
Candle BODIES must stay inside the zone boundaries. Wicks can breach, but bodies must remain within.

---

## AMENDMENTS REQUIRED

### AMENDMENT 1 — Engine Event Detection: FVG definition
**Location:** `engine_event_detection` → `components` → `fvg`

**Current:**
```yaml
fvg: "Three-candle imbalance: Candle A high < Candle C low (bullish) or A low > C high (bearish)"
```

**Replace with:**
```yaml
fvg: "Three-candle imbalance (wick-to-wick). Candle A wick high < Candle C wick low (bullish) or Candle A wick low > Candle C wick high (bearish)."
vi: "Three-candle imbalance (body-to-body). Candle A body top < Candle C body bottom (bullish) or Candle A body bottom > Candle C body top (bearish). Wicks may overlap."
vi_treatment: "Treated identically to FVG in all trading logic. Detected and labeled separately in system outputs."
```

---

### AMENDMENT 2 — Engine Event Detection: Respect definition
**Location:** `engine_event_detection` → `fvg_respect_definition`

**Current:**
```yaml
fvg_respect_definition:
  description: >
    FVG "respected" means candle BODIES stay inside the FVG boundaries.
    Wicks can break the FVG, but bodies must remain within.
  rule: "Candle BODIES must stay inside the FVG — wicks can break it, but bodies must remain within"
  source: [olya_feedback_v0.3]
```

**Replace with:**
```yaml
zone_respect_definition:
  applies_to: "FVG and VI equally"
  description: >
    A zone is "respected" when candle BODIES stay inside the zone boundaries.
    Wicks can breach the zone, but bodies must remain within.
  rule: "Candle BODIES must stay inside the zone — wicks can breach it, but bodies must remain within"
  source: [olya_feedback_v0.3, olya_feedback_v0.4]
```

---

### AMENDMENT 3 — Five Factor Checklist
**Location:** `entry_execution` → `five_factor_checklist` → `factors`

**Current:**
```yaml
factors:
  2: "PDA engaged (OB, FVG, or Breaker in correct zone)"
  3: "MSS confirmed (with displacement + FVG)"
  5: "LTF PDA available for entry (5min OB or FVG for precise entry)"
```

**Replace with:**
```yaml
factors:
  2: "PDA engaged (OB, FVG, VI, or Breaker in correct zone)"
  3: "MSS confirmed (with displacement + FVG or VI)"
  5: "LTF PDA available for entry (5min OB, FVG, or VI for precise entry)"
```

---

### AMENDMENT 4 — Entry Types: Add VI retrace alongside FVG retrace
**Location:** `entry_execution` → `entry_types`

**Current:**
```yaml
fvg_retrace:
  description: "Price retraces into FVG created by displacement"
  where: "FVG in Discount (longs) or Premium (shorts), within OTE zone"
  entry_price: "FVG boundary or CE (50% of FVG)"
  quality: "Fresh FVG (untouched or single-tap) preferred"
  source: [lesson_6_fvg_bisi_sibi]
```

**Add directly after `fvg_retrace` block:**
```yaml
vi_retrace:
  description: "Price retraces into Volume Imbalance created by displacement"
  where: "VI in Discount (longs) or Premium (shorts), within OTE zone"
  entry_price: "VI body boundary or CE (50% of VI)"
  quality: "Fresh VI (untouched or single-tap) preferred"
  treatment: "Identical to FVG retrace in all logic"
  source: [olya_feedback_v0.4]
```

---

### AMENDMENT 5 — Limit Order Placement
**Location:** `entry_execution` → `limit_order_placement` → `order_types`

**Current:**
```yaml
order_types:
  - "Limit at FVG boundary or CE"
  - "Limit at OB body or MT"
```

**Replace with:**
```yaml
order_types:
  - "Limit at FVG boundary or CE"
  - "Limit at VI body boundary or CE"
  - "Limit at OB body or MT"
```

---

### AMENDMENT 6 — Metadata: Version and changelog
**Location:** `metadata`

**Update version:**
```yaml
version: "0.4"
date: "2026-02-24"
```

**Add to changelog:**
```yaml
v0.4: |
  Volume Imbalance (VI) added as equal concept to FVG.
  VI defined as body-to-body gap (wicks may overlap).
  Both FVG and VI detected and named separately in system outputs.
  Both treated identically in all trading logic.
  Amendments: engine_event_detection, five_factor_checklist, entry_types, limit_order_placement.
  Source: Olya decision 2026-02-24.
```

---

### AMENDMENT 7 — Known Gaps: Add resolution entry
**Location:** `known_gaps` → `resolved_in_v0_3` (rename section to `resolved`)

**Add the following entry:**
```yaml
- concept: "Volume Imbalance vs FVG"
  resolution: "VI (body-to-body gap) added as equal concept to FVG (wick-to-wick gap). Both detected and named separately. Both treated identically in all trading logic."
  source: olya_feedback_v0.4
```

---

## SUMMARY OF CHANGES

| Amendment | Section | Type |
|-----------|---------|------|
| 1 | engine_event_detection → components | Add VI definition alongside FVG |
| 2 | engine_event_detection → fvg_respect_definition | Expand to cover both FVG and VI |
| 3 | five_factor_checklist → factors | Add VI alongside FVG in factors 2, 3, 5 |
| 4 | entry_types | Add vi_retrace entry type |
| 5 | limit_order_placement → order_types | Add VI limit order type |
| 6 | metadata | Version bump to v0.4, changelog entry |
| 7 | known_gaps | Add resolution entry for VI |

---

## IMPORTANT NOTE FOR TEAM

Where FVG appears in **conceptual references** (e.g. MSS narrative descriptions, weekly context, consequence types) — these do **not** need updating. The definition amendments above mean FVG-or-VI is now implicit wherever the method refers to imbalances.

Only the sections listed above require explicit amendment.

---

**END OF AMENDMENT REQUEST**
