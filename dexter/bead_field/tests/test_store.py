"""Test bi-temporal store: CRUD, immutability, unsigned rejection, migrations (Phase E)."""

import pytest
import sqlite3

from bead_field.schema.enums import BeadType, BeadStatus, TemporalClass
from bead_field.schema.fact import FactBead
from bead_field.schema.claim import ClaimBead
from bead_field.integrity.chain import append_to_chain
from bead_field.integrity.signing import KeyManager, sign_hash
from bead_field.store.bitemporal import (
    BeadStore,
    DuplicateBeadError,
    UnsignedBeadError,
)
from bead_field.store.migrations import get_current_version, rollback_last

from bead_field.tests.conftest import (
    make_core_fields, make_fact_content, make_claim_content,
    make_attestation,
)


@pytest.fixture
def keys():
    return KeyManager.generate()


def _make_signed_fact(keys, **overrides):
    """Create a fully signed FactBead ready for store insertion."""
    bead = FactBead(
        **make_core_fields(BeadType.FACT),
        content=make_fact_content(**overrides),
    )
    linked = append_to_chain(bead)
    ecdsa_sig, pqc_sig = sign_hash(linked.hash_self, keys)
    return linked.model_copy(
        update={"attestation": linked.attestation.model_copy(
            update={"ecdsa_sig": ecdsa_sig, "pqc_sig": pqc_sig}
        )}
    )


def _make_signed_claim(keys, **overrides):
    bead = ClaimBead(
        **make_core_fields(BeadType.CLAIM, TemporalClass.PATTERN),
        content=make_claim_content(**overrides),
    )
    linked = append_to_chain(bead)
    ecdsa_sig, pqc_sig = sign_hash(linked.hash_self, keys)
    return linked.model_copy(
        update={"attestation": linked.attestation.model_copy(
            update={"ecdsa_sig": ecdsa_sig, "pqc_sig": pqc_sig}
        )}
    )


@pytest.fixture
def store():
    s = BeadStore(":memory:")
    yield s
    s.close()


class TestInsertAndRetrieve:
    def test_insert_and_get(self, store, keys):
        bead = _make_signed_fact(keys)
        store.insert(bead)
        retrieved = store.get(bead.bead_id)
        assert retrieved is not None
        assert retrieved.bead_id == bead.bead_id
        assert retrieved.bead_type == BeadType.FACT
        assert retrieved.content.symbol == "EURUSD"

    def test_get_nonexistent_returns_none(self, store):
        assert store.get("nonexistent-id") is None

    def test_count_empty(self, store):
        assert store.count() == 0

    def test_count_after_inserts(self, store, keys):
        store.insert(_make_signed_fact(keys))
        store.insert(_make_signed_fact(keys, symbol="GBPUSD"))
        assert store.count() == 2

    def test_count_by_type(self, store, keys):
        store.insert(_make_signed_fact(keys))
        store.insert(_make_signed_claim(keys))
        assert store.count("FACT") == 1
        assert store.count("CLAIM") == 1

    def test_round_trip_preserves_content(self, store, keys):
        bead = _make_signed_fact(keys, symbol="USDJPY", value=149.85)
        store.insert(bead)
        retrieved = store.get(bead.bead_id)
        assert retrieved.content.symbol == "USDJPY"
        assert retrieved.content.value == 149.85

    def test_round_trip_preserves_temporal(self, store, keys):
        bead = _make_signed_fact(keys)
        store.insert(bead)
        retrieved = store.get(bead.bead_id)
        assert retrieved.temporal_class == TemporalClass.OBSERVATION
        assert retrieved.world_time_valid_from is not None

    def test_round_trip_preserves_hash(self, store, keys):
        bead = _make_signed_fact(keys)
        store.insert(bead)
        retrieved = store.get(bead.bead_id)
        assert retrieved.hash_self == bead.hash_self

    def test_round_trip_preserves_attestation(self, store, keys):
        bead = _make_signed_fact(keys)
        store.insert(bead)
        retrieved = store.get(bead.bead_id)
        assert retrieved.attestation.ecdsa_sig == bead.attestation.ecdsa_sig
        assert retrieved.attestation.pqc_sig == bead.attestation.pqc_sig

    def test_round_trip_preserves_lineage(self, store, keys):
        bead = _make_signed_fact(keys)
        bead_with_lineage = bead.model_copy(update={"lineage": ["ancestor-1", "ancestor-2"]})
        linked = append_to_chain(bead_with_lineage)
        ecdsa_sig, pqc_sig = sign_hash(linked.hash_self, keys)
        signed = linked.model_copy(
            update={"attestation": linked.attestation.model_copy(
                update={"ecdsa_sig": ecdsa_sig, "pqc_sig": pqc_sig}
            )}
        )
        store.insert(signed)
        retrieved = store.get(signed.bead_id)
        assert retrieved.lineage == ["ancestor-1", "ancestor-2"]


class TestImmutability:
    def test_inv_bead_immutable_no_content_update(self, store, keys):
        """INV-BEAD-IMMUTABLE: content UPDATE must not be possible via store API."""
        bead = _make_signed_fact(keys)
        store.insert(bead)
        with pytest.raises(sqlite3.IntegrityError, match="INV-BEAD-IMMUTABLE"):
            store.connection.execute(
                "UPDATE beads SET content = ? WHERE bead_id = ?",
                ('{"tampered": true}', bead.bead_id),
            )

    def test_status_update_allowed(self, store, keys):
        bead = _make_signed_fact(keys)
        store.insert(bead)
        store.update_status(bead.bead_id, "SUPERSEDED", superseded_by="new-bead-id")
        retrieved = store.get(bead.bead_id)
        assert retrieved.status == BeadStatus.SUPERSEDED
        assert retrieved.superseded_by == "new-bead-id"

    def test_merkle_batch_id_update_allowed(self, store, keys):
        bead = _make_signed_fact(keys)
        store.insert(bead)
        store.set_merkle_batch_id(bead.bead_id, "batch-001")
        retrieved = store.get(bead.bead_id)
        assert retrieved.merkle_batch_id == "batch-001"

    def test_duplicate_bead_rejected(self, store, keys):
        bead = _make_signed_fact(keys)
        store.insert(bead)
        with pytest.raises(DuplicateBeadError):
            store.insert(bead)


class TestUnsignedRejection:
    def test_unsigned_bead_rejected(self, store):
        bead = FactBead(
            **make_core_fields(BeadType.FACT, attestation=make_attestation(ecdsa_sig="", pqc_sig="")),
            content=make_fact_content(),
        )
        linked = append_to_chain(bead)
        with pytest.raises(UnsignedBeadError):
            store.insert(linked)

    def test_ecdsa_only_accepted(self, store, keys):
        bead = _make_signed_fact(keys)
        ecdsa_only = bead.model_copy(
            update={"attestation": bead.attestation.model_copy(update={"pqc_sig": ""})}
        )
        store.insert(ecdsa_only)
        assert store.get(ecdsa_only.bead_id) is not None


class TestMigrations:
    def test_fresh_db_has_current_version(self, store):
        version = get_current_version(store.connection)
        assert version == 1

    def test_rollback_and_reapply(self):
        store = BeadStore(":memory:")
        assert get_current_version(store.connection) == 1
        new_version = rollback_last(store.connection)
        assert new_version == 0
        from bead_field.store.migrations import apply_migrations
        applied = apply_migrations(store.connection)
        assert applied == 1
        assert get_current_version(store.connection) == 1
        store.close()

    def test_beads_table_exists(self, store):
        rows = store.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='beads'"
        ).fetchall()
        assert len(rows) == 1

    def test_indexes_exist(self, store):
        rows = store.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_beads_%'"
        ).fetchall()
        assert len(rows) == 7
