"""Test per-stream hash chain integrity (Phase B)."""

import pytest

from bead_field.schema.enums import BeadType, TemporalClass
from bead_field.schema.fact import FactBead
from bead_field.integrity.hashing import compute_hash
from bead_field.integrity.chain import (
    append_to_chain,
    verify_chain,
    verify_hash_self,
    HashChainError,
)

from bead_field.tests.conftest import make_core_fields, make_fact_content


def _make_raw_bead(**overrides):
    """Create a FactBead without hash fields set (pre-chain)."""
    return FactBead(**make_core_fields(BeadType.FACT), content=make_fact_content(), **overrides)


def _build_chain(length: int) -> list[FactBead]:
    """Build a chain of N linked beads."""
    chain = []
    for i in range(length):
        raw = _make_raw_bead()
        prev = chain[-1] if chain else None
        linked = append_to_chain(raw, prev)
        chain.append(linked)
    return chain


class TestAppendToChain:
    def test_first_bead_has_none_hash_prev(self):
        bead = append_to_chain(_make_raw_bead(), prev_bead=None)
        assert bead.hash_prev is None

    def test_first_bead_has_valid_hash_self(self):
        bead = append_to_chain(_make_raw_bead(), prev_bead=None)
        assert bead.hash_self
        assert len(bead.hash_self) == 64

    def test_second_bead_links_to_first(self):
        first = append_to_chain(_make_raw_bead(), prev_bead=None)
        second = append_to_chain(_make_raw_bead(), prev_bead=first)
        assert second.hash_prev == first.hash_self

    def test_hash_self_is_valid_after_append(self):
        bead = append_to_chain(_make_raw_bead(), prev_bead=None)
        assert verify_hash_self(bead)


class TestVerifyHashSelf:
    def test_valid_bead_passes(self):
        bead = append_to_chain(_make_raw_bead())
        assert verify_hash_self(bead) is True

    def test_tampered_content_fails(self):
        bead = append_to_chain(_make_raw_bead())
        tampered = bead.model_copy(
            update={"content": make_fact_content(symbol="TAMPERED")}
        )
        assert verify_hash_self(tampered) is False

    def test_tampered_tags_fails(self):
        bead = append_to_chain(_make_raw_bead())
        tampered = bead.model_copy(update={"tags": ["INJECTED"]})
        assert verify_hash_self(tampered) is False


class TestVerifyChain:
    def test_empty_chain_passes(self):
        assert verify_chain([]) is True

    def test_single_bead_passes(self):
        chain = _build_chain(1)
        assert verify_chain(chain) is True

    def test_chain_of_10_passes(self):
        chain = _build_chain(10)
        assert verify_chain(chain) is True

    def test_chain_of_10_linkage_correct(self):
        """Every bead's hash_prev matches the previous bead's hash_self."""
        chain = _build_chain(10)
        assert chain[0].hash_prev is None
        for i in range(1, len(chain)):
            assert chain[i].hash_prev == chain[i - 1].hash_self

    def test_tamper_middle_bead_detected(self):
        """Tampering a bead in the middle breaks the chain."""
        chain = _build_chain(5)
        tampered = chain[2].model_copy(update={"tags": ["TAMPERED"]})
        chain[2] = tampered
        with pytest.raises(HashChainError) as exc_info:
            verify_chain(chain)
        assert exc_info.value.bead_index == 2

    def test_tamper_hash_prev_detected(self):
        """Forging hash_prev breaks hash_self verification."""
        chain = _build_chain(5)
        forged = chain[3].model_copy(update={"hash_prev": "forged_link"})
        chain[3] = forged
        with pytest.raises(HashChainError) as exc_info:
            verify_chain(chain)
        assert exc_info.value.bead_index == 3

    def test_tamper_first_bead_detected(self):
        chain = _build_chain(3)
        tampered = chain[0].model_copy(update={"tags": ["TAMPERED"]})
        chain[0] = tampered
        with pytest.raises(HashChainError) as exc_info:
            verify_chain(chain)
        assert exc_info.value.bead_index == 0

    def test_swap_two_beads_detected(self):
        """Swapping bead order breaks chain linkage."""
        chain = _build_chain(4)
        chain[1], chain[2] = chain[2], chain[1]
        with pytest.raises(HashChainError):
            verify_chain(chain)


class TestRapidFireChain:
    def test_100_rapid_appends_maintain_integrity(self):
        """Rapid sequential writes must maintain hash chain invariants."""
        chain = _build_chain(100)
        assert verify_chain(chain) is True
        assert len(chain) == 100
        assert all(b.hash_self for b in chain)
        assert chain[0].hash_prev is None
        assert all(chain[i].hash_prev == chain[i - 1].hash_self for i in range(1, 100))


class TestHashChainError:
    def test_error_contains_bead_info(self):
        chain = _build_chain(3)
        tampered = chain[1].model_copy(update={"tags": ["BAD"]})
        chain[1] = tampered
        with pytest.raises(HashChainError) as exc_info:
            verify_chain(chain)
        err = exc_info.value
        assert err.bead_index == 1
        assert err.bead_id == chain[1].bead_id
