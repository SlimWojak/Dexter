"""Test deterministic hashing and canonical JSON (Phase B)."""

import json
import pytest

from bead_field.schema.enums import BeadType, TemporalClass
from bead_field.schema.fact import FactBead
from bead_field.schema.claim import ClaimBead
from bead_field.integrity.hashing import compute_hash, canonical_json, EXCLUDED_FROM_HASH, EXCLUDED_ATTESTATION_FIELDS

from bead_field.tests.conftest import (
    make_core_fields, make_fact_content, make_claim_content,
)


def _make_fact_bead(**overrides):
    return FactBead(**make_core_fields(BeadType.FACT), content=make_fact_content(), **overrides)


class TestDeterminism:
    def test_same_bead_same_hash(self):
        """Identical bead data must produce identical hash."""
        bead = _make_fact_bead()
        h1 = compute_hash(bead)
        h2 = compute_hash(bead)
        assert h1 == h2

    def test_different_data_different_hash(self):
        """Different content must produce different hash."""
        bead_a = _make_fact_bead()
        bead_b = FactBead(
            **make_core_fields(BeadType.FACT),
            content=make_fact_content(symbol="GBPUSD", value=1.2650),
        )
        assert compute_hash(bead_a) != compute_hash(bead_b)

    def test_hash_is_hex_sha256(self):
        """Hash must be 64-char hex-encoded SHA-256."""
        bead = _make_fact_bead()
        h = compute_hash(bead)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_round_trip_determinism(self):
        """Serialize to JSON and back, hash must be identical."""
        bead = _make_fact_bead()
        h_before = compute_hash(bead)
        json_str = bead.model_dump_json()
        restored = FactBead.model_validate_json(json_str)
        h_after = compute_hash(restored)
        assert h_before == h_after


class TestExclusionRules:
    def test_hash_self_excluded(self):
        """Changing hash_self must NOT change the computed hash."""
        bead = _make_fact_bead()
        h1 = compute_hash(bead)
        modified = bead.model_copy(update={"hash_self": "some_different_value"})
        h2 = compute_hash(modified)
        assert h1 == h2

    def test_merkle_batch_id_excluded(self):
        """Changing merkle_batch_id must NOT change the computed hash."""
        bead = _make_fact_bead()
        h1 = compute_hash(bead)
        modified = bead.model_copy(update={"merkle_batch_id": "batch-999"})
        h2 = compute_hash(modified)
        assert h1 == h2

    def test_other_fields_included(self):
        """Changing any non-excluded field MUST change the hash."""
        bead = _make_fact_bead()
        h_original = compute_hash(bead)

        modified = bead.model_copy(update={"tags": ["TAMPERED"]})
        assert compute_hash(modified) != h_original

    def test_hash_prev_is_included(self):
        """hash_prev IS in the hash input (creates chain linkage)."""
        bead = _make_fact_bead()
        h1 = compute_hash(bead)
        modified = bead.model_copy(update={"hash_prev": "abc123"})
        h2 = compute_hash(modified)
        assert h1 != h2

    def test_excluded_set_is_correct(self):
        assert EXCLUDED_FROM_HASH == {"hash_self", "merkle_batch_id"}

    def test_attestation_sigs_excluded(self):
        """Signatures are computed FROM the hash — including them would be circular."""
        bead = _make_fact_bead()
        h1 = compute_hash(bead)
        modified = bead.model_copy(
            update={"attestation": bead.attestation.model_copy(
                update={"ecdsa_sig": "different_sig", "pqc_sig": "another_sig"}
            )}
        )
        h2 = compute_hash(modified)
        assert h1 == h2

    def test_attestation_metadata_included(self):
        """Node ID, code hash ARE in the hash (non-circular attestation metadata)."""
        bead = _make_fact_bead()
        h1 = compute_hash(bead)
        modified = bead.model_copy(
            update={"attestation": bead.attestation.model_copy(
                update={"air_node_id": "different-node"}
            )}
        )
        h2 = compute_hash(modified)
        assert h1 != h2


class TestCanonicalJson:
    def test_sorted_keys(self):
        bead = _make_fact_bead()
        cj = canonical_json(bead)
        data = json.loads(cj)
        keys = list(data.keys())
        assert keys == sorted(keys)

    def test_no_whitespace(self):
        """Canonical JSON must have no spaces or newlines."""
        bead = _make_fact_bead()
        cj = canonical_json(bead)
        assert " " not in cj.replace('" ', '"').replace(' "', '"')
        assert "\n" not in cj

    def test_no_excluded_fields_in_output(self):
        bead = _make_fact_bead(hash_self="should_be_removed", merkle_batch_id="also_removed")
        cj = canonical_json(bead)
        data = json.loads(cj)
        assert "hash_self" not in data
        assert "merkle_batch_id" not in data

    def test_utf8_encoding(self):
        """Non-ASCII content must be preserved (not escaped)."""
        bead = FactBead(
            **make_core_fields(BeadType.FACT),
            content=make_fact_content(symbol="EUR/USD", value="Résistance"),
        )
        cj = canonical_json(bead)
        assert "Résistance" in cj

    def test_nested_dicts_sorted(self):
        """Nested dict keys must also be sorted."""
        bead = _make_fact_bead()
        cj = canonical_json(bead)
        parsed = json.loads(cj)
        att = parsed["attestation"]
        assert list(att.keys()) == sorted(att.keys())
