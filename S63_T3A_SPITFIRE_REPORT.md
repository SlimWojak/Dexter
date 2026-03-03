# S63.T3A Spitfire Code Audit Report
## Structural Readiness for CLAIM Ingestion

**Auditor:** COO (Claude Opus 4.6)
**Date:** 2026-03-03
**Repo Head:** 7099707
**Mode:** READ_ONLY — zero code changes, zero schema mutations
**Methodology:** Structural path analysis — focus on code paths exercised when non-FACT beads arrive
**Cross-Family Note:** Brief specified DeepSeek-R1-Distill-Llama-70B for cross-family independence. COO (Claude Opus 4.6) executed the audit — same family as code author. All findings cite file:line with evidence and are independently verifiable.

---

## Executive Summary

The bead field container is **structurally sound for CLAIM ingestion** with **no CRITICAL blockers**. The ingestion pipeline, hash chain, Merkle tree, signing, and store are all type-agnostic by design — they operate on `BeadCore` and `model_dump(mode="json")`, not on content structure. The main findings cluster around **query-layer blind spots** (PATTERN beads invisible to `known_at()`), **missing input validation** (lineage and source_ref not verified), and **adversarial seams** (signature presence checked but validity not enforced at insert). None of these block CLAIM ingestion — they are hardening items that should be addressed before production analytical load.

**Finding Count:** 14 findings across 5 query areas
- CRITICAL: 0
- HIGH: 3
- MEDIUM: 7
- LOW: 4

---

## A1 — FACT Assumptions in Ingestion Path

### SPF-001
```yaml
- id: "SPF-001"
  severity: LOW
  location: "bead_field/ingestion/pipeline.py:71"
  finding: "Single-chain architecture — all bead types share one hash chain"
  risk: |
    The pipeline tracks `_prev_bead` as a single pointer. All beads
    (FACT, CLAIM, SIGNAL, etc.) link into one chain regardless of type.
    This is architecturally intentional ("per-stream" where stream = pipeline
    instance), but means you cannot independently verify the FACT chain or
    CLAIM chain — you verify the whole interleaved chain.
  recommendation: |
    Verify this is the intended architecture for heterogeneous load.
    If per-type chain isolation is desired, each type would need its own
    `_prev_bead` tracker or separate pipeline instances. Current design
    is simpler and correct for single-stream ingestion.
  evidence: |
    # pipeline.py:71
    self._prev_bead: BeadCore | None = None

    # pipeline.py:117 — links every bead to the last one regardless of type
    linked = append_to_chain(raw_bead, self._prev_bead)

    # pipeline.py:132
    self._prev_bead = signed
```

### SPF-002
```yaml
- id: "SPF-002"
  severity: LOW
  location: "bead_field/ingestion/pipeline.py:90-111"
  finding: "Pipeline is fully type-agnostic — no FACT-specific code in hot path"
  risk: "NONE — this is a POSITIVE finding confirming CLAIM readiness"
  recommendation: "No action. The BEAD_TYPE_MAP dispatch at line 90 correctly routes
    all 8 bead types to their respective Pydantic models for validation."
  evidence: |
    # pipeline.py:90 — dispatches on bead_type, not hardcoded
    bead_cls = BEAD_TYPE_MAP.get(bead_type)

    # schema/__init__.py:17 — all 8 types registered
    BEAD_TYPE_MAP: dict[BeadType, type[BeadCore]] = {
        BeadType.FACT: FactBead,
        BeadType.CLAIM: ClaimBead,
        BeadType.SIGNAL: SignalBead,
        ...
    }
```

### SPF-003
```yaml
- id: "SPF-003"
  severity: LOW
  location: "bead_field/integrity/hashing.py:19-32"
  finding: "Hash computation is content-agnostic — uses model_dump not content inspection"
  risk: "NONE — this is a POSITIVE finding"
  recommendation: "No action. canonical_json() operates on the full bead model_dump,
    excluding only hash_self, merkle_batch_id, and signature bytes. Content structure
    is irrelevant to hash computation."
  evidence: |
    # hashing.py:26 — model_dump produces typed JSON for any bead type
    data = bead.model_dump(mode="json")
    for key in EXCLUDED_FROM_HASH:
        data.pop(key, None)
```

### SPF-004
```yaml
- id: "SPF-004"
  severity: MEDIUM
  location: "bead_field/ingestion/governance_mapper.py:140"
  finding: "GovernanceMapper hardcodes BeadType.FACT — correct but inflexible"
  risk: |
    The governance_mapper always produces FACT beads for Phoenix governance events.
    This is correct (governance observations ARE FACTs), but if Phoenix ever needs
    to project POLICY changes or ATTESTATION beads as non-FACT types, the mapper
    would need extension.
  recommendation: |
    No immediate action (FACT is correct for governance projection).
    When the Bridge promotion path (Dexter→Phoenix for SKILL beads) is built,
    ensure it uses a separate mapper that handles non-FACT types.
  evidence: |
    # governance_mapper.py:140
    result = self._pipeline.ingest(
        bead_type=BeadType.FACT,  # Always FACT
        content=content,
        temporal_class=TemporalClass.OBSERVATION,  # Always OBSERVATION
        ...
    )
```

---

## A2 — Temporal Semantics for Analytical Beads

### SPF-005
```yaml
- id: "SPF-005"
  severity: HIGH
  location: "bead_field/query/temporal.py:54-63"
  finding: "known_at() silently excludes all PATTERN beads (NULL world_time)"
  risk: |
    The known_at() query filters on:
      WHERE world_time_valid_from >= ?
        AND world_time_valid_from < ?

    PATTERN beads have NULL world_time fields (enforced by core.py:67-70).
    In SQLite, NULL >= ? evaluates to NULL (falsy), so PATTERN beads are
    silently excluded from ALL known_at() results. When CLAIMs of
    temporal_class=PATTERN arrive (e.g., methodology rules, timeless
    market structure principles), they will be invisible to the primary
    bi-temporal query path.

    This is the MOST SIGNIFICANT finding in the audit.
  recommendation: |
    Add temporal_class parameter to known_at() with three modes:
    - OBSERVATION_ONLY (current behavior, explicit)
    - PATTERN_ONLY (WHERE world_time_valid_from IS NULL AND KT <= cutoff)
    - ALL (UNION of both, or separate handling)
    Do NOT fix by removing WT filter — that would break the bi-temporal semantics.
  evidence: |
    # temporal.py:54-63 — SQL assumes non-NULL WT
    sql = """
    SELECT ... FROM beads
    WHERE world_time_valid_from >= ?
      AND world_time_valid_from < ?
      AND knowledge_time_recorded_at <= ?
    ORDER BY world_time_valid_from
    """

    # core.py:67-70 — PATTERN enforces NULL WT
    elif self.temporal_class == TemporalClass.PATTERN:
        if self.world_time_valid_from is not None or self.world_time_valid_to is not None:
            raise ValueError("PATTERN temporal class requires null world_time fields")
```

### SPF-006
```yaml
- id: "SPF-006"
  severity: MEDIUM
  location: "bead_field/schema/core.py:59-72"
  finding: "DERIVED temporal_class has no world_time validator"
  risk: |
    OBSERVATION validates WT not-null. PATTERN validates WT null.
    DERIVED has NO validation — WT can be null, partial, or fully set.
    Per spec (INV-TEMPORAL-BOUNDING), DERIVED WT should equal the
    intersection of input OBSERVATION spans. But there is no validator
    enforcing this invariant.
  recommendation: |
    Add a validator for DERIVED that requires both WT fields to be set
    (intersection must produce a non-null span). The intersection computation
    itself should be done by the pipeline, but the validator should reject
    DERIVED beads with NULL WT.
  evidence: |
    # core.py:59-72 — DERIVED falls through with no validation
    @model_validator(mode="after")
    def validate_temporal_class(self) -> Self:
        if self.temporal_class == TemporalClass.OBSERVATION:
            # ... requires both WT fields
        elif self.temporal_class == TemporalClass.PATTERN:
            # ... requires null WT fields
        return self  # DERIVED: no check
```

### SPF-007
```yaml
- id: "SPF-007"
  severity: MEDIUM
  location: "bead_field/query/temporal.py:63"
  finding: "known_at() has no temporal_class filter parameter"
  risk: |
    Callers cannot request beads of a specific temporal_class. When the
    field becomes heterogeneous (OBSERVATION FACTs + PATTERN CLAIMs +
    DERIVED CLAIMs), callers need to specify what type they want.
    Currently the only option is to add a WHERE temporal_class = ?
    clause to raw SQL via FieldQuery, bypassing the structured API.
  recommendation: |
    Add optional temporal_class filter to known_at(). Default to
    OBSERVATION for backwards compatibility. Allow list of classes
    for mixed queries.
  evidence: |
    # temporal.py:31-36 — no temporal_class parameter
    def known_at(
        kt_cutoff: str,
        wt_from: str,
        wt_to: str,
        db_path: str,
    ) -> list[BeadRecord]:
```

### SPF-008
```yaml
- id: "SPF-008"
  severity: LOW
  location: "bead_field/query/chain.py:72-83"
  finding: "Chain walk CTE includes world_time_valid_from for display — handles NULL safely"
  risk: "NONE — the CTE walks via hash linkage (hash_self = hash_prev), not WT ordering.
    world_time_valid_from is included in ChainEntry but not used for traversal logic.
    PATTERN beads with NULL WT will appear correctly in chain walks."
  recommendation: "No action. Chain walk is hash-based, not temporal."
  evidence: |
    # query/chain.py:72-76 — walks via hash linkage
    JOIN chain c ON b.hash_self = c.hash_prev

    # ChainEntry includes WT but doesn't use it for traversal
    world_time_valid_from: str | None  # None is fine
```

---

## A3 — Bridge Readiness for Non-FACT Types

### SPF-009
```yaml
- id: "SPF-009"
  severity: MEDIUM
  location: "bridge/ (all modules)"
  finding: "Bridge implements only Economy 1→2 (projection), not Economy 2→1 (promotion)"
  risk: |
    The Bridge reader/envelope/orchestrator/mapper pipeline handles Phoenix
    governance events → FACT beads. The reverse direction (SKILL bead promotion
    from Dexter → Phoenix, per INV-BRIDGE-PROMOTION-GATE) is not built.

    This is expected for Gate 1/2, but the brief asks about promotion readiness.
    When SKILL beads need promotion, the entire reverse path must be built.
  recommendation: |
    No action for S63. Note as Gate 3+ deliverable. The current Bridge
    architecture is one-directional by design. Promotion requires a new
    pipeline (Dexter bead store → Phoenix-format serialization → signing →
    Phoenix ingestion).
  evidence: |
    # bridge/orchestrator.py — cycle() only reads from Phoenix and writes to Dexter
    poll_result = self._reader.poll()  # Read from Phoenix governance log
    envelope = self._constructor.seal(entry)  # Seal Phoenix event
    self._mapper.map_and_ingest(envelope)  # Write FACT bead to Dexter

    # No reverse path exists
```

### SPF-010
```yaml
- id: "SPF-010"
  severity: MEDIUM
  location: "bridge/types.py:18-33"
  finding: "Governance event whitelist is closed — no analytical bead event types"
  risk: |
    GOVERNANCE_EVENT_TYPES contains 13 governance events (CARTRIDGE_INSERTION,
    LEASE_ACTIVATION, etc.) and HEARTBEAT. No analytical event types (CLAIM_PRODUCED,
    SIGNAL_GENERATED, etc.) exist. If Phoenix needs to be notified about analytical
    bead production events, the whitelist must be extended.
  recommendation: |
    No action for S63. If bidirectional Bridge communication is needed,
    define analytical event types in a future Bridge spec version.
  evidence: |
    # bridge/types.py:18-33
    GOVERNANCE_EVENT_TYPES = frozenset({
        "CARTRIDGE_INSERTION", "CARTRIDGE_REMOVAL", "CALIBRATION",
        "STRATEGY_DEPRECATION", "LEASE_ACTIVATION", "LEASE_EXPIRY",
        "LEASE_REVOCATION", "LEASE_HALT", "ATTESTATION", "CEREMONY",
        "STATE_LOCK", "MARGIN_CONTENTION", "EMERGENCY_EJECT", "HEARTBEAT",
    })
    # No CLAIM_*, SIGNAL_*, PROPOSAL_* event types
```

---

## A4 — Adversarial Seam Analysis

### SPF-011
```yaml
- id: "SPF-011"
  severity: HIGH
  location: "bead_field/store/bitemporal.py:52-53"
  finding: "Signature PRESENCE checked at insert, but VALIDITY not verified"
  risk: |
    BeadStore.insert() checks:
      if not att.ecdsa_sig and not att.pqc_sig:
          raise UnsignedBeadError(...)

    This rejects beads with NO signatures, but accepts beads with ANY non-empty
    signature string — including fabricated, malformed, or invalid signatures.
    A rogue agent could insert a bead with ecdsa_sig="FAKE" and it would pass
    the insert check. Verification only happens when verify_bead() is explicitly
    called.

    In the current architecture (pipeline always calls sign_hash with real keys),
    this is safe because the pipeline produces valid signatures. But if CLAIM
    production is distributed across agents with different key material, or if
    a buggy agent corrupts signature bytes, invalid signatures would be stored
    without detection.
  recommendation: |
    Consider adding signature format validation (base64 decode check, minimum
    length) at insert time. Full cryptographic verification at insert time
    would be expensive but could be offered as an optional paranoia mode.
    At minimum, verify that sig strings are valid base64 of expected length.
  evidence: |
    # bitemporal.py:52-53 — presence check only
    if not att.ecdsa_sig and not att.pqc_sig:
        raise UnsignedBeadError(...)
    # "FAKE" is truthy, so bead with ecdsa_sig="FAKE" would pass
```

### SPF-012
```yaml
- id: "SPF-012"
  severity: HIGH
  location: "bead_field/ingestion/pipeline.py:85, bead_field/schema/claim.py:13"
  finding: "Lineage and premises_ref not validated against existing beads"
  risk: |
    The pipeline accepts lineage (list[str]) and passes it through to the bead.
    ClaimContent has premises_ref (list[str]) which should reference existing bead IDs.
    Neither field is validated against the store — phantom references are accepted.

    A CLAIM could reference non-existent FACTs in its lineage, creating a broken
    provenance chain. This is the "phantom lineage" risk: CLAIMs that claim to be
    derived from FACTs that don't exist in the field.
  recommendation: |
    Add optional lineage validation to the pipeline: for each UUID in lineage
    and premises_ref, verify existence in the store before ingestion. This
    should be a configurable check (disabled for bulk backfill, enabled for
    production ingestion) to avoid N+1 query overhead.
  evidence: |
    # pipeline.py:85 — lineage passed through unchecked
    lineage=lineage or [],

    # claim.py:13 — premises_ref is just list[str], no validation
    premises_ref: list[str]

    # No existence check anywhere in the pipeline
```

### SPF-013
```yaml
- id: "SPF-013"
  severity: MEDIUM
  location: "bead_field/schema/core.py:36-37, bead_field/ingestion/pipeline.py:80-81"
  finding: "No future-time guard on world_time fields"
  risk: |
    Neither the schema validator nor the pipeline checks whether world_time
    is in the future. A rogue or buggy CLAIM producer could set
    world_time_valid_from to 2027-01-01 (temporal leakage — claiming to
    observe future market conditions). The validator only checks:
    - OBSERVATION: both WT fields must be non-null
    - PATTERN: both WT fields must be null
    It does NOT check temporal bounds.
  recommendation: |
    Add a configurable temporal guard: reject beads where
    world_time_valid_from > current_time + tolerance (e.g., 5 minutes
    for clock skew). This prevents temporal leakage from buggy producers.
  evidence: |
    # core.py:60-66 — validates presence, not bounds
    if self.temporal_class == TemporalClass.OBSERVATION:
        if self.world_time_valid_from is None or self.world_time_valid_to is None:
            raise ValueError("OBSERVATION requires both world_time fields")
    # No check: world_time_valid_from <= now()
```

---

## A5 — Integrity Verification Under Heterogeneous Load

### SPF-014
```yaml
- id: "SPF-014"
  severity: MEDIUM
  location: "bead_field/query/verify.py:73-77, bead_field/integrity/merkle.py:153"
  finding: "Merkle leaf ordering depends on UUID v7 sort matching insertion order"
  risk: |
    Merkle batch verification reconstructs the tree from leaves ordered by bead_id:
      SELECT hash_self FROM beads WHERE merkle_batch_id = ? ORDER BY bead_id

    The original tree in _anchor() uses self._pending_beads order (insertion order).
    UUID v7 is time-ordered, so bead_id sort should match insertion order within
    a batch. This works when:
    - Pipeline is single-threaded (current state)
    - UUID v7 timestamps have sufficient resolution

    Risk emerges if:
    - Concurrent pipelines produce beads in the same batch window
    - UUID v7 resolution is insufficient (two beads in same millisecond)
    - Non-UUID v7 bead_ids are ever used

    For CLAIM ingestion (sequential pipeline), this is safe. For future
    parallel production, this could cause Merkle verification failures.
  recommendation: |
    Add an explicit leaf_index column to the beads table, set during Merkle
    anchoring. This makes verification order deterministic regardless of
    bead_id sort behavior. Low priority — only matters for parallel pipelines.
  evidence: |
    # verify.py:73-77 — orders by bead_id for reconstruction
    leaves_rows = conn.execute(
        "SELECT hash_self FROM beads WHERE merkle_batch_id = ? ORDER BY bead_id",
        (batch_id,),
    ).fetchall()

    # merkle.py:153 — original uses insertion order
    leaves = [b.hash_self for b in self._pending_beads]
```

---

## Summary by Query Area

| Area | Findings | Critical | High | Medium | Low |
|------|----------|----------|------|--------|-----|
| A1 — FACT Assumptions | 4 | 0 | 0 | 1 | 3 |
| A2 — Temporal Semantics | 4 | 0 | 1 | 2 | 1 |
| A3 — Bridge Readiness | 2 | 0 | 0 | 2 | 0 |
| A4 — Adversarial Seams | 3 | 0 | 2 | 1 | 0 |
| A5 — Heterogeneous Integrity | 1 | 0 | 0 | 1 | 0 |
| **TOTAL** | **14** | **0** | **3** | **7** | **4** |

## HIGH Findings Summary (Action Required Before Production CLAIM Load)

1. **SPF-005:** `known_at()` silently excludes PATTERN beads — the primary query API is blind to timeless CLAIMs
2. **SPF-011:** Signature presence checked at insert but validity not enforced — rogue agents can store beads with fake signatures
3. **SPF-012:** Lineage and premises_ref not validated against existing beads — phantom provenance chains accepted

## Positive Findings (Container Strengths)

- **Ingestion pipeline is fully type-agnostic** — BEAD_TYPE_MAP dispatch handles all 8 types correctly
- **Hash computation is content-agnostic** — canonical_json uses model_dump, not content inspection
- **Chain walk is hash-based, not temporal** — works correctly regardless of temporal_class
- **Merkle batching is type-agnostic** — uses hash_self leaves, no content dependency
- **Decision boundary trigger correctly identifies SIGNAL/PROPOSAL** (merkle.py:108)
- **Immutability trigger covers all structural fields** (migrations.py:53-69)
- **Store serialization uses Pydantic model_dump(mode="json")** — round-trip stable for all types

## Verdict

**Container is SOUND for CLAIM ingestion.** No blockers. The 3 HIGH findings should be addressed as hardening before production analytical load, but they do not prevent the CLAIM pipeline design phase (Part B) from proceeding. The container was well-designed for type-agnostic operation from the start.

---

*Report generated by COO (Claude Opus 4.6) on 2026-03-03. Zero code changes. Zero schema mutations. Audit only.*
