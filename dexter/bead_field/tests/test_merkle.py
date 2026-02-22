"""Test Merkle tree, proof verification, and batch anchoring (Phase F)."""

import pytest
import time
from datetime import datetime, timezone, timedelta

from bead_field.schema.enums import BeadType, TemporalClass
from bead_field.schema.fact import FactBead
from bead_field.schema.signal import SignalBead
from bead_field.integrity.chain import append_to_chain
from bead_field.integrity.signing import KeyManager, sign_hash
from bead_field.integrity.merkle import (
    MerkleTree,
    BatchAnchor,
    AnchorConfig,
    DECISION_BOUNDARY_TYPES,
)
from bead_field.store.bitemporal import BeadStore

from bead_field.tests.conftest import (
    make_core_fields, make_fact_content, make_signal_content,
)


@pytest.fixture
def keys():
    return KeyManager.generate()


@pytest.fixture
def store():
    s = BeadStore(":memory:")
    yield s
    s.close()


def _make_signed_bead(keys, bead_type=BeadType.FACT, tc=TemporalClass.OBSERVATION, content_fn=None, **overrides):
    if content_fn is None:
        content_fn = make_fact_content
    if bead_type == BeadType.SIGNAL:
        content_fn = make_signal_content
        cls = SignalBead
    else:
        cls = FactBead
    bead = cls(**make_core_fields(bead_type, tc), content=content_fn(), **overrides)
    linked = append_to_chain(bead)
    ecdsa_sig, pqc_sig = sign_hash(linked.hash_self, keys)
    return linked.model_copy(
        update={"attestation": linked.attestation.model_copy(
            update={"ecdsa_sig": ecdsa_sig, "pqc_sig": pqc_sig}
        )}
    )


# --- MerkleTree ---

class TestMerkleTree:
    def test_build_from_known_leaves(self):
        leaves = ["aaa", "bbb", "ccc", "ddd"]
        tree = MerkleTree(leaves)
        assert tree.root
        assert len(tree.root) == 64
        assert tree.leaf_count == 4

    def test_single_leaf(self):
        tree = MerkleTree(["abc123"])
        assert tree.root
        assert tree.leaf_count == 1

    def test_odd_leaf_count(self):
        tree = MerkleTree(["a", "b", "c"])
        assert tree.root
        assert tree.leaf_count == 3

    def test_same_leaves_same_root(self):
        leaves = ["x", "y", "z"]
        t1 = MerkleTree(leaves)
        t2 = MerkleTree(leaves)
        assert t1.root == t2.root

    def test_different_leaves_different_root(self):
        t1 = MerkleTree(["a", "b"])
        t2 = MerkleTree(["a", "c"])
        assert t1.root != t2.root

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            MerkleTree([])


class TestMerkleProof:
    def test_proof_verifies_for_any_leaf(self):
        leaves = ["aaa", "bbb", "ccc", "ddd"]
        tree = MerkleTree(leaves)
        for i, leaf in enumerate(leaves):
            proof = tree.proof(i)
            assert MerkleTree.verify_proof(leaf, proof, tree.root)

    def test_proof_verifies_single_leaf(self):
        tree = MerkleTree(["only"])
        proof = tree.proof(0)
        assert MerkleTree.verify_proof("only", proof, tree.root)

    def test_proof_verifies_odd_count(self):
        leaves = ["a", "b", "c", "d", "e"]
        tree = MerkleTree(leaves)
        for i, leaf in enumerate(leaves):
            proof = tree.proof(i)
            assert MerkleTree.verify_proof(leaf, proof, tree.root)

    def test_tampered_leaf_fails_proof(self):
        leaves = ["aaa", "bbb", "ccc", "ddd"]
        tree = MerkleTree(leaves)
        proof = tree.proof(1)
        assert not MerkleTree.verify_proof("TAMPERED", proof, tree.root)

    def test_wrong_root_fails_proof(self):
        tree = MerkleTree(["a", "b", "c"])
        proof = tree.proof(0)
        assert not MerkleTree.verify_proof("a", proof, "wrong_root_hash")

    def test_proof_index_out_of_range(self):
        tree = MerkleTree(["a", "b"])
        with pytest.raises(IndexError):
            tree.proof(5)

    def test_large_tree_proof(self):
        leaves = [f"leaf_{i}" for i in range(100)]
        tree = MerkleTree(leaves)
        for i in [0, 49, 99]:
            proof = tree.proof(i)
            assert MerkleTree.verify_proof(leaves[i], proof, tree.root)


# --- BatchAnchor trigger logic ---

class TestBatchAnchorTriggers:
    def test_signal_triggers_anchor(self, store, keys):
        anchor = BatchAnchor(store)
        fact = _make_signed_bead(keys, BeadType.FACT)
        store.insert(fact)
        assert anchor.record(fact) is None

        signal = _make_signed_bead(keys, BeadType.SIGNAL)
        store.insert(signal)
        batch_id = anchor.record(signal)
        assert batch_id is not None

    def test_max_beads_triggers_anchor(self, store, keys):
        config = AnchorConfig(max_beads=5, max_time_seconds=99999)
        anchor = BatchAnchor(store, config)

        for i in range(4):
            bead = _make_signed_bead(keys)
            store.insert(bead)
            assert anchor.record(bead) is None

        fifth = _make_signed_bead(keys)
        store.insert(fifth)
        batch_id = anchor.record(fifth)
        assert batch_id is not None

    def test_time_trigger(self, store, keys):
        config = AnchorConfig(max_beads=99999, max_time_seconds=0)
        anchor = BatchAnchor(store, config)
        bead = _make_signed_bead(keys)
        store.insert(bead)
        anchor.record(bead)

        anchor._last_anchor_time = datetime.now(timezone.utc) - timedelta(hours=2)
        batch_id = anchor.check_time_trigger()
        assert batch_id is not None

    def test_empty_time_trigger_no_anchor(self, store, keys):
        config = AnchorConfig(max_beads=99999, max_time_seconds=0)
        anchor = BatchAnchor(store, config)
        assert anchor.check_time_trigger() is None

    def test_decision_boundary_types(self):
        assert BeadType.SIGNAL in DECISION_BOUNDARY_TYPES
        assert BeadType.PROPOSAL in DECISION_BOUNDARY_TYPES
        assert BeadType.FACT not in DECISION_BOUNDARY_TYPES


class TestBatchAnchorBackfill:
    def test_backfill_sets_merkle_batch_id(self, store, keys):
        config = AnchorConfig(max_beads=3)
        anchor = BatchAnchor(store, config)

        beads = []
        for _ in range(3):
            bead = _make_signed_bead(keys)
            store.insert(bead)
            beads.append(bead)
            anchor.record(bead)

        for b in beads:
            retrieved = store.get(b.bead_id)
            assert retrieved.merkle_batch_id is not None

    def test_batch_stored_in_merkle_batches_table(self, store, keys):
        anchor = BatchAnchor(store)
        signal = _make_signed_bead(keys, BeadType.SIGNAL)
        store.insert(signal)
        batch_id = anchor.record(signal)

        batch = anchor.get_batch(batch_id)
        assert batch is not None
        assert batch["merkle_root"]
        assert batch["bead_count"] == 1

    def test_pending_cleared_after_anchor(self, store, keys):
        anchor = BatchAnchor(store)
        signal = _make_signed_bead(keys, BeadType.SIGNAL)
        store.insert(signal)
        anchor.record(signal)
        assert anchor.pending_count == 0
