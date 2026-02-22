"""Test dual PQC + ECDSA signing on ACTUAL library APIs (Phase D).

ChadBoar learning #1: integration tests must cover actual signing library API.
Phase 0 finding: pqcrypto verify() returns bool, ecdsa verify() raises.
"""

import pytest
from pathlib import Path

from bead_field.integrity.signing import (
    KeyManager,
    KeyPair,
    sign_hash,
    verify_ecdsa,
    verify_pqc,
    verify_dual,
    SignatureVerification,
    PQC_STUB,
)
from bead_field.integrity.hashing import compute_hash
from bead_field.integrity.chain import append_to_chain
from bead_field.schema.enums import BeadType
from bead_field.schema.fact import FactBead

from bead_field.tests.conftest import make_core_fields, make_fact_content


TEST_HASH = "a1b2c3d4e5f6" + "0" * 52  # 64-char hex


@pytest.fixture
def keys():
    return KeyManager.generate()


@pytest.fixture
def signed_pair(keys):
    ecdsa_sig, pqc_sig = sign_hash(TEST_HASH, keys)
    return ecdsa_sig, pqc_sig


class TestKeyManager:
    def test_generate_returns_keypair(self, keys):
        assert isinstance(keys, KeyPair)
        assert keys.ecdsa_sk is not None
        assert keys.ecdsa_vk is not None
        assert len(keys.pqc_pk) > 0
        assert len(keys.pqc_sk) > 0

    def test_save_and_load_round_trip(self, keys, tmp_path):
        key_dir = tmp_path / "test_keys"
        KeyManager.save(keys, key_dir)

        loaded = KeyManager.load(key_dir)

        test_hash = "ab" * 32
        sig_orig_ecdsa, sig_orig_pqc = sign_hash(test_hash, keys)
        assert verify_ecdsa(test_hash, sig_orig_ecdsa, loaded.ecdsa_vk)
        assert verify_pqc(test_hash, sig_orig_pqc, loaded.pqc_pk)

    def test_saved_files_exist(self, keys, tmp_path):
        key_dir = tmp_path / "test_keys"
        KeyManager.save(keys, key_dir)
        assert (key_dir / "ecdsa_sk.pem").exists()
        assert (key_dir / "ecdsa_vk.pem").exists()
        assert (key_dir / "pqc_pk.bin").exists()
        assert (key_dir / "pqc_sk.bin").exists()


class TestSignAndVerify:
    def test_ecdsa_sign_verify_round_trip(self, keys):
        ecdsa_sig, _ = sign_hash(TEST_HASH, keys)
        assert verify_ecdsa(TEST_HASH, ecdsa_sig, keys.ecdsa_vk) is True

    def test_pqc_sign_verify_round_trip(self, keys):
        _, pqc_sig = sign_hash(TEST_HASH, keys)
        assert verify_pqc(TEST_HASH, pqc_sig, keys.pqc_pk) is True

    def test_dual_sign_verify_round_trip(self, keys, signed_pair):
        ecdsa_sig, pqc_sig = signed_pair
        result = verify_dual(TEST_HASH, ecdsa_sig, pqc_sig, keys.ecdsa_vk, keys.pqc_pk)
        assert result.valid is True
        assert result.optimal is True
        assert result.degraded is False

    def test_signatures_are_base64_strings(self, keys, signed_pair):
        ecdsa_sig, pqc_sig = signed_pair
        assert isinstance(ecdsa_sig, str)
        assert isinstance(pqc_sig, str)
        from base64 import b64decode
        b64decode(ecdsa_sig)
        b64decode(pqc_sig)


class TestTamperDetection:
    def test_ecdsa_rejects_tampered_hash(self, keys, signed_pair):
        ecdsa_sig, _ = signed_pair
        tampered = "ff" * 32
        assert verify_ecdsa(tampered, ecdsa_sig, keys.ecdsa_vk) is False

    def test_pqc_rejects_tampered_hash(self, keys, signed_pair):
        _, pqc_sig = signed_pair
        tampered = "ff" * 32
        assert verify_pqc(tampered, pqc_sig, keys.pqc_pk) is False

    def test_ecdsa_rejects_wrong_key(self, keys, signed_pair):
        ecdsa_sig, _ = signed_pair
        other_keys = KeyManager.generate()
        assert verify_ecdsa(TEST_HASH, ecdsa_sig, other_keys.ecdsa_vk) is False

    def test_pqc_rejects_wrong_key(self, keys, signed_pair):
        _, pqc_sig = signed_pair
        other_keys = KeyManager.generate()
        assert verify_pqc(TEST_HASH, pqc_sig, other_keys.pqc_pk) is False


class TestEitherSigSufficient:
    """Per spec: either signature alone is sufficient for validation."""

    def test_ecdsa_only_is_valid(self, keys):
        ecdsa_sig, _ = sign_hash(TEST_HASH, keys)
        result = verify_dual(TEST_HASH, ecdsa_sig, "", keys.ecdsa_vk, keys.pqc_pk)
        assert result.valid is True
        assert result.ecdsa_valid is True
        assert result.pqc_valid is False

    def test_pqc_only_is_valid(self, keys):
        _, pqc_sig = sign_hash(TEST_HASH, keys)
        result = verify_dual(TEST_HASH, "", pqc_sig, keys.ecdsa_vk, keys.pqc_pk)
        assert result.valid is True
        assert result.pqc_valid is True
        assert result.ecdsa_valid is False

    def test_neither_sig_is_invalid(self, keys):
        result = verify_dual(TEST_HASH, "", "", keys.ecdsa_vk, keys.pqc_pk)
        assert result.valid is False


class TestDegradedSovereignty:
    """Owl advisory: ECDSA-only valid but flags degraded state."""

    def test_ecdsa_only_is_degraded(self, keys):
        ecdsa_sig, _ = sign_hash(TEST_HASH, keys)
        result = verify_dual(TEST_HASH, ecdsa_sig, "", keys.ecdsa_vk, keys.pqc_pk)
        assert result.degraded is True

    def test_pqc_only_is_degraded(self, keys):
        _, pqc_sig = sign_hash(TEST_HASH, keys)
        result = verify_dual(TEST_HASH, "", pqc_sig, keys.ecdsa_vk, keys.pqc_pk)
        assert result.degraded is True

    def test_both_valid_not_degraded(self, keys, signed_pair):
        ecdsa_sig, pqc_sig = signed_pair
        result = verify_dual(TEST_HASH, ecdsa_sig, pqc_sig, keys.ecdsa_vk, keys.pqc_pk)
        assert result.degraded is False


class TestPqcStubFlag:
    def test_pqc_stub_is_false(self):
        """Real Dilithium via pqcrypto, no stub needed (Phase 0 validated)."""
        assert PQC_STUB is False


class TestEndToEndWithBead:
    """Sign a real bead's hash — full pipeline integration."""

    def test_sign_real_bead_hash(self, keys):
        bead = FactBead(
            **make_core_fields(BeadType.FACT),
            content=make_fact_content(),
        )
        linked = append_to_chain(bead)
        ecdsa_sig, pqc_sig = sign_hash(linked.hash_self, keys)
        result = verify_dual(linked.hash_self, ecdsa_sig, pqc_sig, keys.ecdsa_vk, keys.pqc_pk)
        assert result.valid is True
        assert result.optimal is True
