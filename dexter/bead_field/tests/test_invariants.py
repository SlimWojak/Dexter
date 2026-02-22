"""Forensic Integrity Stress Test — prove the substrate catches corruption (Phase I).

Steps 1-5: Manual tamper detection (Owl advisory)
Step 6: LLM Removal Test (CTO advisory, INV-LLM-REMOVAL-TEST)

Proving code works is Phases A-H.
Proving integrity works is steps 1-5.
Proving the system is sovereign (no LLM dependency in the record) is step 6.
"""

import json
import sqlite3
import pytest
from datetime import datetime, timezone

from bead_field.schema.enums import BeadType, TemporalClass, BeadStatus
from bead_field.schema.fact import FactBead
from bead_field.schema.claim import ClaimBead
from bead_field.schema.signal import SignalBead
from bead_field.schema.proposal import ProposalBead
from bead_field.schema.proposal_rejected import ProposalRejectedBead
from bead_field.schema.skill import SkillBead
from bead_field.schema.model_version import ModelVersionBead
from bead_field.schema.policy import PolicyBead
from bead_field.schema import parse_bead, BEAD_TYPE_MAP
from bead_field.integrity.chain import verify_chain, verify_hash_self, HashChainError
from bead_field.integrity.hashing import compute_hash
from bead_field.integrity.merkle import MerkleTree
from bead_field.integrity.signing import KeyManager, sign_hash, verify_dual
from bead_field.store.bitemporal import BeadStore
from bead_field.ingestion.pipeline import IngestionPipeline

from bead_field.tests.conftest import (
    make_core_fields, make_source_ref, make_fact_content, make_claim_content,
    make_signal_content, make_proposal_content, make_proposal_rejected_content,
    make_skill_content, make_model_version_content, make_policy_content, ts,
)


@pytest.fixture
def keys():
    return KeyManager.generate()


@pytest.fixture
def populated_store(keys):
    """A store with 5 signed beads for tamper testing."""
    store = BeadStore(":memory:")
    pipeline = IngestionPipeline(store, keys)
    now = ts()

    beads = []
    for i in range(5):
        result = pipeline.ingest(
            bead_type=BeadType.FACT,
            content=make_fact_content(symbol=f"PAIR{i}"),
            temporal_class=TemporalClass.OBSERVATION,
            source_ref=make_source_ref(),
            world_time_valid_from=now,
            world_time_valid_to=now,
        )
        assert result.success
        beads.append(result.bead)

    yield store, beads, keys
    store.close()


# --- Step 1: Tamper content blob in SQLite ---

class TestStep1TamperContent:
    def test_direct_content_update_blocked_by_trigger(self, populated_store):
        """Manually edit a single byte in SQLite content blob -> trigger fires."""
        store, beads, _ = populated_store
        target = beads[2]

        with pytest.raises(sqlite3.IntegrityError, match="INV-BEAD-IMMUTABLE"):
            store.connection.execute(
                "UPDATE beads SET content = ? WHERE bead_id = ?",
                ('{"tampered": true}', target.bead_id),
            )

    def test_tampered_content_fails_hash_verification(self, populated_store):
        """Even if trigger were bypassed, hash_self would not match."""
        store, beads, _ = populated_store
        target = beads[2]
        tampered = target.model_copy(
            update={"content": make_fact_content(symbol="TAMPERED")}
        )
        assert not verify_hash_self(tampered)


# --- Step 2: Tamper knowledge_time in SQLite ---

class TestStep2TamperKnowledgeTime:
    def test_direct_kt_update_blocked_by_trigger(self, populated_store):
        """Manually change a knowledge_time stamp -> trigger fires."""
        store, beads, _ = populated_store
        target = beads[1]

        with pytest.raises(sqlite3.IntegrityError, match="INV-BEAD-IMMUTABLE"):
            store.connection.execute(
                "UPDATE beads SET knowledge_time_recorded_at = ? WHERE bead_id = ?",
                ("2020-01-01T00:00:00+00:00", target.bead_id),
            )

    def test_tampered_kt_fails_hash_verification(self, populated_store):
        """Knowledge time is in the hash input — changing it breaks hash_self."""
        _, beads, _ = populated_store
        target = beads[1]
        tampered = target.model_copy(
            update={"knowledge_time_recorded_at": datetime(2020, 1, 1, tzinfo=timezone.utc)}
        )
        assert not verify_hash_self(tampered)


# --- Step 3: Hash chain walk triggers HARD_FAIL ---

class TestStep3HashChainDetection:
    def test_tampered_bead_breaks_chain_walk(self, populated_store):
        """chain.py walk detects tampered bead in the middle."""
        _, beads, _ = populated_store
        chain = list(beads)
        chain[2] = chain[2].model_copy(update={"tags": ["INJECTED"]})

        with pytest.raises(HashChainError) as exc_info:
            verify_chain(chain)
        assert exc_info.value.bead_index == 2

    def test_forged_hash_prev_breaks_chain(self, populated_store):
        """Forging hash_prev to skip a bead -> chain break detected."""
        _, beads, _ = populated_store
        chain = list(beads)
        chain[3] = chain[3].model_copy(update={"hash_prev": "forged_link_00000"})

        with pytest.raises(HashChainError) as exc_info:
            verify_chain(chain)
        assert exc_info.value.bead_index == 3


# --- Step 4: Merkle proof verification fails on tamper ---

class TestStep4MerkleProofDetection:
    def test_tampered_leaf_fails_merkle_proof(self, populated_store):
        """Merkle proof for a tampered bead does not verify."""
        _, beads, _ = populated_store
        leaves = [b.hash_self for b in beads]
        tree = MerkleTree(leaves)

        proof = tree.proof(2)
        assert MerkleTree.verify_proof(leaves[2], proof, tree.root)
        assert not MerkleTree.verify_proof("tampered_hash_value", proof, tree.root)

    def test_removed_bead_breaks_merkle_root(self, populated_store):
        """Removing a bead changes the Merkle root."""
        _, beads, _ = populated_store
        full_leaves = [b.hash_self for b in beads]
        partial_leaves = [b.hash_self for b in beads[:4]]

        full_tree = MerkleTree(full_leaves)
        partial_tree = MerkleTree(partial_leaves)

        assert full_tree.root != partial_tree.root


# --- Step 5: Signing verification fails on tamper ---

class TestStep5SigningDetection:
    def test_tampered_hash_fails_signature_verification(self, populated_store):
        """Signature was over original hash — tampered hash won't verify."""
        _, beads, keys = populated_store
        target = beads[0]

        result = verify_dual(
            target.hash_self,
            target.attestation.ecdsa_sig,
            target.attestation.pqc_sig,
            keys.ecdsa_vk,
            keys.pqc_pk,
        )
        assert result.optimal

        tampered_hash = "ff" * 32
        result_bad = verify_dual(
            tampered_hash,
            target.attestation.ecdsa_sig,
            target.attestation.pqc_sig,
            keys.ecdsa_vk,
            keys.pqc_pk,
        )
        assert not result_bad.valid

    def test_wrong_keys_fail_verification(self, populated_store):
        """Bead signed with ceremony keys, verified with different keys -> fail."""
        _, beads, _ = populated_store
        other_keys = KeyManager.generate()
        target = beads[0]

        result = verify_dual(
            target.hash_self,
            target.attestation.ecdsa_sig,
            target.attestation.pqc_sig,
            other_keys.ecdsa_vk,
            other_keys.pqc_pk,
        )
        assert not result.valid


# --- Step 6: LLM Removal Test (INV-LLM-REMOVAL-TEST) ---

class TestStep6LlmRemovalTest:
    """Can we reconstruct a bead entirely from stored fields without any LLM reasoning?
    Does any logic depend on prose interpretation? If yes -> structural failure."""

    CONTENT_FACTORIES = {
        BeadType.FACT: (FactBead, TemporalClass.OBSERVATION, make_fact_content),
        BeadType.CLAIM: (ClaimBead, TemporalClass.PATTERN, make_claim_content),
        BeadType.SIGNAL: (SignalBead, TemporalClass.OBSERVATION, make_signal_content),
        BeadType.PROPOSAL: (ProposalBead, TemporalClass.OBSERVATION, make_proposal_content),
        BeadType.PROPOSAL_REJECTED: (ProposalRejectedBead, TemporalClass.OBSERVATION, make_proposal_rejected_content),
        BeadType.SKILL: (SkillBead, TemporalClass.PATTERN, make_skill_content),
        BeadType.MODEL_VERSION: (ModelVersionBead, TemporalClass.PATTERN, make_model_version_content),
        BeadType.POLICY: (PolicyBead, TemporalClass.PATTERN, make_policy_content),
    }

    @pytest.mark.parametrize("bead_type", list(CONTENT_FACTORIES.keys()),
                             ids=[bt.value for bt in CONTENT_FACTORIES.keys()])
    def test_bead_reconstructable_from_stored_fields(self, bead_type, keys):
        """For every bead type: store -> retrieve -> reconstruct without LLM."""
        bead_cls, tc, content_fn = self.CONTENT_FACTORIES[bead_type]
        store = BeadStore(":memory:")
        pipeline = IngestionPipeline(store, keys)
        now = ts()

        kwargs = {}
        if tc == TemporalClass.OBSERVATION:
            kwargs["world_time_valid_from"] = now
            kwargs["world_time_valid_to"] = now

        result = pipeline.ingest(
            bead_type=bead_type,
            content=content_fn(),
            temporal_class=tc,
            source_ref=make_source_ref(),
            **kwargs,
        )
        assert result.success

        retrieved = store.get(result.bead.bead_id)
        assert retrieved is not None

        dumped = retrieved.model_dump(mode="json")
        assert isinstance(dumped["bead_id"], str)
        assert isinstance(dumped["bead_type"], str)
        assert isinstance(dumped["content"], dict)
        assert isinstance(dumped["knowledge_time_recorded_at"], str)
        assert isinstance(dumped["attestation"], dict)

        reconstructed = parse_bead(dumped)
        assert reconstructed.bead_id == retrieved.bead_id
        assert reconstructed.bead_type == retrieved.bead_type
        assert reconstructed.content == retrieved.content

        store.close()

    def test_no_field_requires_prose_interpretation(self, keys):
        """Every field in every bead type is machine-parseable from its stored value."""
        store = BeadStore(":memory:")
        pipeline = IngestionPipeline(store, keys)
        now = ts()

        result = pipeline.ingest(
            bead_type=BeadType.FACT,
            content=make_fact_content(),
            temporal_class=TemporalClass.OBSERVATION,
            source_ref=make_source_ref(),
            world_time_valid_from=now,
            world_time_valid_to=now,
        )

        row = store.connection.execute(
            "SELECT * FROM beads WHERE bead_id = ?", (result.bead.bead_id,)
        ).fetchone()

        for key in row.keys():
            value = row[key]
            if value is None:
                continue
            if key in ("content", "source_ref", "lineage", "attestation", "tags"):
                parsed = json.loads(value)
                assert isinstance(parsed, (dict, list)), f"Field {key} not machine-parseable"
            else:
                assert isinstance(value, (str, int, float)), f"Field {key} type {type(value)} not primitive"

        store.close()


# --- Compound: full corruption scenario ---

class TestCompoundCorruptionScenario:
    def test_insert_corrupt_retrieve_detect(self, keys):
        """End-to-end: ingest valid bead, corrupt in DB (bypassing trigger via
        direct SQLite without trigger), detect via hash verification."""
        store = BeadStore(":memory:")
        pipeline = IngestionPipeline(store, keys)
        now = ts()

        result = pipeline.ingest(
            bead_type=BeadType.FACT,
            content=make_fact_content(symbol="PRISTINE"),
            temporal_class=TemporalClass.OBSERVATION,
            source_ref=make_source_ref(),
            world_time_valid_from=now,
            world_time_valid_to=now,
        )
        assert result.success

        store.connection.execute("DROP TRIGGER trg_bead_immutable")
        store.connection.execute(
            "UPDATE beads SET tags = ? WHERE bead_id = ?",
            ('["CORRUPTED"]', result.bead.bead_id),
        )
        store.connection.commit()
        store.connection.execute("""
            CREATE TRIGGER trg_bead_immutable
            BEFORE UPDATE ON beads
            WHEN OLD.content != NEW.content
              OR OLD.bead_type != NEW.bead_type
              OR OLD.temporal_class != NEW.temporal_class
              OR OLD.source_ref != NEW.source_ref
              OR OLD.lineage != NEW.lineage
              OR OLD.hash_self != NEW.hash_self
              OR OLD.hash_prev != NEW.hash_prev
              OR OLD.knowledge_time_recorded_at != NEW.knowledge_time_recorded_at
              OR OLD.world_time_valid_from IS NOT NEW.world_time_valid_from
              OR OLD.world_time_valid_to IS NOT NEW.world_time_valid_to
              OR OLD.attestation != NEW.attestation
            BEGIN
              SELECT RAISE(ABORT, 'INV-BEAD-IMMUTABLE: cannot modify structural bead fields');
            END
        """)

        corrupted = store.get(result.bead.bead_id)
        assert corrupted.tags == ["CORRUPTED"]
        assert not verify_hash_self(corrupted)

        store.close()
