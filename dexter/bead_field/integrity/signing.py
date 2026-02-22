"""Dual PQC (ML-DSA-65 / Dilithium3) + ECDSA (secp256r1) signing (Spec Section 5.3).

Phase 0 finding: pqcrypto.sign.ml_dsa_65.verify() returns bool, does NOT raise.
ECDSA's VerifyingKey.verify() DOES raise on failure.
This module normalises both to return bool for consistent API.

Either signature alone is sufficient for validation (per spec).
Both present = optimal sovereignty health.
ECDSA-only = valid but flags degraded sovereignty (Owl advisory).
"""

import hashlib
from base64 import b64decode, b64encode
from pathlib import Path

from ecdsa import NIST256p, SigningKey as EcdsaSigningKey, VerifyingKey as EcdsaVerifyingKey
from pqcrypto.sign.ml_dsa_65 import generate_keypair as pqc_generate_keypair
from pqcrypto.sign.ml_dsa_65 import sign as pqc_sign
from pqcrypto.sign.ml_dsa_65 import verify as pqc_verify

PQC_STUB = False


class KeyPair:
    """Holds ECDSA + PQC key material."""

    def __init__(
        self,
        ecdsa_sk: EcdsaSigningKey,
        ecdsa_vk: EcdsaVerifyingKey,
        pqc_pk: bytes,
        pqc_sk: bytes,
    ):
        self.ecdsa_sk = ecdsa_sk
        self.ecdsa_vk = ecdsa_vk
        self.pqc_pk = pqc_pk
        self.pqc_sk = pqc_sk


class KeyManager:
    """Generates and manages ECDSA + PQC key pairs.

    File-based storage for Mac Mini; HSM-aware interface for future.
    """

    @staticmethod
    def generate() -> KeyPair:
        ecdsa_sk = EcdsaSigningKey.generate(curve=NIST256p)
        ecdsa_vk = ecdsa_sk.get_verifying_key()
        pqc_pk, pqc_sk = pqc_generate_keypair()
        return KeyPair(ecdsa_sk=ecdsa_sk, ecdsa_vk=ecdsa_vk, pqc_pk=pqc_pk, pqc_sk=pqc_sk)

    @staticmethod
    def save(keys: KeyPair, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "ecdsa_sk.pem").write_bytes(keys.ecdsa_sk.to_pem())
        (directory / "ecdsa_vk.pem").write_bytes(keys.ecdsa_vk.to_pem())
        (directory / "pqc_pk.bin").write_bytes(keys.pqc_pk)
        (directory / "pqc_sk.bin").write_bytes(keys.pqc_sk)

    @staticmethod
    def load(directory: Path) -> KeyPair:
        ecdsa_sk = EcdsaSigningKey.from_pem(
            (directory / "ecdsa_sk.pem").read_bytes()
        )
        ecdsa_vk = EcdsaVerifyingKey.from_pem(
            (directory / "ecdsa_vk.pem").read_bytes()
        )
        pqc_pk = (directory / "pqc_pk.bin").read_bytes()
        pqc_sk = (directory / "pqc_sk.bin").read_bytes()
        return KeyPair(ecdsa_sk=ecdsa_sk, ecdsa_vk=ecdsa_vk, pqc_pk=pqc_pk, pqc_sk=pqc_sk)


def sign_hash(hash_hex: str, keys: KeyPair) -> tuple[str, str]:
    """Sign a hex-encoded hash with both ECDSA and PQC.

    Returns (ecdsa_sig_b64, pqc_sig_b64) — base64-encoded signatures.
    """
    hash_bytes = bytes.fromhex(hash_hex)

    ecdsa_sig = keys.ecdsa_sk.sign(hash_bytes, hashfunc=hashlib.sha256)
    pqc_sig = pqc_sign(keys.pqc_sk, hash_bytes)

    return b64encode(ecdsa_sig).decode(), b64encode(pqc_sig).decode()


def verify_ecdsa(hash_hex: str, sig_b64: str, vk: EcdsaVerifyingKey) -> bool:
    """Verify ECDSA signature. Returns bool (normalised from raise-on-fail API)."""
    if not sig_b64:
        return False
    try:
        hash_bytes = bytes.fromhex(hash_hex)
        sig_bytes = b64decode(sig_b64)
        vk.verify(sig_bytes, hash_bytes, hashfunc=hashlib.sha256)
        return True
    except Exception:
        return False


def verify_pqc(hash_hex: str, sig_b64: str, pk: bytes) -> bool:
    """Verify PQC (ML-DSA-65) signature. Returns bool (already bool from pqcrypto)."""
    if not sig_b64:
        return False
    try:
        hash_bytes = bytes.fromhex(hash_hex)
        sig_bytes = b64decode(sig_b64)
        return pqc_verify(pk, hash_bytes, sig_bytes)
    except Exception:
        return False


class SignatureVerification:
    """Result of dual signature verification."""

    def __init__(self, ecdsa_valid: bool, pqc_valid: bool):
        self.ecdsa_valid = ecdsa_valid
        self.pqc_valid = pqc_valid

    @property
    def valid(self) -> bool:
        """Either signature alone is sufficient (per spec)."""
        return self.ecdsa_valid or self.pqc_valid

    @property
    def optimal(self) -> bool:
        """Both signatures present and valid = full sovereignty."""
        return self.ecdsa_valid and self.pqc_valid

    @property
    def degraded(self) -> bool:
        """Valid but not optimal — Owl advisory: flag degraded sovereignty."""
        return self.valid and not self.optimal


def verify_dual(
    hash_hex: str,
    ecdsa_sig_b64: str,
    pqc_sig_b64: str,
    ecdsa_vk: EcdsaVerifyingKey,
    pqc_pk: bytes,
) -> SignatureVerification:
    """Verify both signatures and return structured result."""
    return SignatureVerification(
        ecdsa_valid=verify_ecdsa(hash_hex, ecdsa_sig_b64, ecdsa_vk),
        pqc_valid=verify_pqc(hash_hex, pqc_sig_b64, pqc_pk),
    )
