"""Tests for envelope constructor — BRIDGE_SPEC_v0.2 Section 2.1."""

from __future__ import annotations

import secrets

import pytest

from bridge.envelope import EnvelopeConstructor, load_or_create_bridge_key
from bridge.tests.conftest import FakeGovernanceLog
from bridge.reader import GovernanceLogReader
from bridge.types import BRIDGE_VERSION, VerifiedEntry
from pathlib import Path


@pytest.fixture()
def bridge_key() -> bytes:
    return secrets.token_bytes(32)


@pytest.fixture()
def constructor(bridge_key: bytes) -> EnvelopeConstructor:
    return EnvelopeConstructor(bridge_key=bridge_key)


def _read_entries(
    fake_log: FakeGovernanceLog,
    phoenix_key: bytes,
    state_dir: Path,
) -> list[VerifiedEntry]:
    reader = GovernanceLogReader(fake_log.log_path, state_dir, phoenix_key)
    result = reader.poll()
    return list(result.entries)


class TestEnvelopeConstruction:
    def test_seal_populates_all_fields(
        self, constructor: EnvelopeConstructor, populated_log: FakeGovernanceLog,
        phoenix_key: bytes, state_dir: Path,
    ) -> None:
        entries = _read_entries(populated_log, phoenix_key, state_dir)
        env = constructor.seal(entries[0])

        assert env.version == BRIDGE_VERSION
        assert len(env.event_id) == 64
        assert env.event_type == "LEASE_ACTIVATION"
        assert env.payload == entries[0].payload
        assert env.gt_timestamp == entries[0].timestamp
        assert env.athena_ref["athena_hash"] == entries[0].athena_hash
        assert env.athena_ref["athena_index"] == entries[0].athena_index
        assert env.source_signature == entries[0].source_signature
        assert env.replay_guard == entries[0].seq
        assert env.bridge_seal["bridge_key_id"] == "bridge-notary-v1"
        assert env.bridge_seal["bridge_version"] == BRIDGE_VERSION

    def test_event_id_is_deterministic(
        self, bridge_key: bytes, populated_log: FakeGovernanceLog,
        phoenix_key: bytes, state_dir: Path,
    ) -> None:
        """Same payload → same event_id."""
        entries = _read_entries(populated_log, phoenix_key, state_dir)
        c1 = EnvelopeConstructor(bridge_key=bridge_key)
        c2 = EnvelopeConstructor(bridge_key=bridge_key)

        env1 = c1.seal(entries[0])
        env2 = c2.seal(entries[0])
        assert env1.event_id == env2.event_id


class TestBridgeSeal:
    def test_seal_verifies(
        self, constructor: EnvelopeConstructor, populated_log: FakeGovernanceLog,
        phoenix_key: bytes, state_dir: Path,
    ) -> None:
        entries = _read_entries(populated_log, phoenix_key, state_dir)
        env = constructor.seal(entries[0])
        assert constructor.verify_seal(env)

    def test_tampered_envelope_fails_verification(
        self, constructor: EnvelopeConstructor, populated_log: FakeGovernanceLog,
        phoenix_key: bytes, state_dir: Path,
    ) -> None:
        entries = _read_entries(populated_log, phoenix_key, state_dir)
        env = constructor.seal(entries[0])
        env.payload = {"tampered": True}
        assert not constructor.verify_seal(env)

    def test_wrong_key_fails_verification(
        self, populated_log: FakeGovernanceLog, phoenix_key: bytes, state_dir: Path,
    ) -> None:
        entries = _read_entries(populated_log, phoenix_key, state_dir)
        c1 = EnvelopeConstructor(bridge_key=secrets.token_bytes(32))
        c2 = EnvelopeConstructor(bridge_key=secrets.token_bytes(32))

        env = c1.seal(entries[0])
        assert not c2.verify_seal(env)


class TestKeyIsolation:
    """INV-BRIDGE-KEY-ISOLATION: Bridge key ≠ Phoenix key."""

    def test_bridge_key_distinct_from_phoenix_key(
        self, bridge_key: bytes, phoenix_key: bytes,
    ) -> None:
        assert bridge_key != phoenix_key

    def test_key_persistence(self, tmp_path: Path) -> None:
        key1 = load_or_create_bridge_key(tmp_path, "test-key")
        key2 = load_or_create_bridge_key(tmp_path, "test-key")
        assert key1 == key2
        assert len(key1) == 32


class TestSigChain:
    """INV-BRIDGE-SIG-CHAIN: Two signatures on every envelope."""

    def test_both_signatures_present(
        self, constructor: EnvelopeConstructor, populated_log: FakeGovernanceLog,
        phoenix_key: bytes, state_dir: Path,
    ) -> None:
        entries = _read_entries(populated_log, phoenix_key, state_dir)
        env = constructor.seal(entries[0])

        assert env.source_signature.get("sig"), "Phoenix signature missing"
        assert env.source_signature.get("algorithm"), "Phoenix algorithm missing"
        assert env.bridge_seal.get("bridge_sig"), "Bridge signature missing"
        assert env.bridge_seal.get("bridge_key_id"), "Bridge key_id missing"

    def test_signatures_are_independent(
        self, constructor: EnvelopeConstructor, populated_log: FakeGovernanceLog,
        phoenix_key: bytes, state_dir: Path,
    ) -> None:
        entries = _read_entries(populated_log, phoenix_key, state_dir)
        env = constructor.seal(entries[0])
        assert env.source_signature["sig"] != env.bridge_seal["bridge_sig"]
