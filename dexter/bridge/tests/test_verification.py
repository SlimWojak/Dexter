"""
Tests for Bridge verification whitelist — BRIDGE_SPEC_v0.2 Section 2.2.

Covers:
  - Algorithm-dispatched signature verification (CTO key instruction)
  - Hash chain verification
  - Replay check with gap semantics
  - GT monotonic enforcement
  - Version and event_type whitelist checks
  - Full pipeline verify_entry
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bridge.tests.conftest import FakeGovernanceLog
from bridge.types import FailureType, VerifyOutcome
from bridge.verification import (
    _VERIFIERS,
    compute_entry_hash,
    event_type_check,
    gt_monotonic_check,
    hash_verify,
    register_verifier,
    replay_check,
    sig_verify,
    verify_entry,
    version_check,
)

GENESIS_HASH = "0" * 64


class TestSigVerifyDispatch:
    """CTO: Reader MUST dispatch on algorithm field."""

    def test_hmac_sha256_valid(
        self, fake_log: FakeGovernanceLog, phoenix_key: bytes
    ) -> None:
        entry = fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        outcome, failure = sig_verify(entry, phoenix_key)
        assert outcome == VerifyOutcome.PASS
        assert failure is None

    def test_hmac_sha256_wrong_key_rejects(
        self, fake_log: FakeGovernanceLog
    ) -> None:
        entry = fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        outcome, failure = sig_verify(entry, b"wrong_key_" * 3)
        assert outcome == VerifyOutcome.FAIL
        assert failure is not None
        assert failure.failure_type == FailureType.SIG_INVALID

    def test_unknown_algorithm_rejects(
        self, fake_log: FakeGovernanceLog, phoenix_key: bytes
    ) -> None:
        entry = fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        entry["source_signature"]["algorithm"] = "rsa-4096"
        outcome, failure = sig_verify(entry, phoenix_key)
        assert outcome == VerifyOutcome.FAIL
        assert failure is not None
        assert failure.failure_type == FailureType.ALGORITHM_UNKNOWN
        assert "rsa-4096" in failure.detail

    def test_register_custom_verifier(
        self, fake_log: FakeGovernanceLog, phoenix_key: bytes
    ) -> None:
        """ECDSA drops in later via register_verifier."""
        calls: list[tuple[bytes, str, str]] = []

        def fake_ecdsa(key: bytes, hash_hex: str, sig: str) -> bool:
            calls.append((key, hash_hex, sig))
            return True

        register_verifier("ecdsa-test", fake_ecdsa)
        try:
            entry = fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
            entry["source_signature"]["algorithm"] = "ecdsa-test"

            outcome, failure = sig_verify(entry, phoenix_key)
            assert outcome == VerifyOutcome.PASS
            assert len(calls) == 1
        finally:
            del _VERIFIERS["ecdsa-test"]

    def test_tampered_payload_fails_sig(
        self, fake_log: FakeGovernanceLog, phoenix_key: bytes
    ) -> None:
        entry = fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        entry["payload"]["lease_id"] = "TAMPERED"
        outcome, failure = sig_verify(entry, phoenix_key)
        assert outcome == VerifyOutcome.FAIL
        assert failure is not None
        assert failure.failure_type == FailureType.SIG_INVALID


class TestHashVerify:
    def test_valid_chain(
        self, fake_log: FakeGovernanceLog
    ) -> None:
        e1 = fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        e2 = fake_log.append("LEASE_EXPIRY", {"lease_id": "l1", "final_stats": {}})

        outcome1, _ = hash_verify(e1, GENESIS_HASH)
        assert outcome1 == VerifyOutcome.PASS

        hash_e1 = compute_entry_hash(e1)
        outcome2, _ = hash_verify(e2, hash_e1)
        assert outcome2 == VerifyOutcome.PASS

    def test_broken_chain_rejects(
        self, fake_log: FakeGovernanceLog
    ) -> None:
        entry = fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        outcome, failure = hash_verify(entry, "wrong_hash" * 6)
        assert outcome == VerifyOutcome.FAIL
        assert failure is not None
        assert failure.failure_type == FailureType.HASH_CHAIN_BREAK

    def test_tampered_athena_hash_rejects(
        self, fake_log: FakeGovernanceLog
    ) -> None:
        entry = fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        entry["athena_hash"] = "f" * 64
        outcome, failure = hash_verify(entry, GENESIS_HASH)
        assert outcome == VerifyOutcome.FAIL
        assert failure is not None
        assert failure.failure_type == FailureType.HASH_MISMATCH


class TestReplayCheck:
    def test_normal_sequential(self) -> None:
        outcome, _ = replay_check({"seq": 1}, 0)
        assert outcome == VerifyOutcome.PASS

    def test_duplicate_rejects(self) -> None:
        outcome, failure = replay_check({"seq": 3}, 3)
        assert outcome == VerifyOutcome.FAIL
        assert failure is not None
        assert failure.failure_type == FailureType.REPLAY_DUPLICATE

    def test_backwards_rejects(self) -> None:
        outcome, failure = replay_check({"seq": 2}, 5)
        assert outcome == VerifyOutcome.FAIL
        assert failure.failure_type == FailureType.REPLAY_DUPLICATE

    def test_gap_one_warns(self) -> None:
        outcome, failure = replay_check({"seq": 3}, 1)
        assert outcome == VerifyOutcome.WARN
        assert failure is not None
        assert failure.failure_type == FailureType.SEQ_GAP

    def test_gap_gt_one_halts(self) -> None:
        outcome, failure = replay_check({"seq": 10}, 1)
        assert outcome == VerifyOutcome.HALT
        assert failure is not None
        assert failure.failure_type == FailureType.SEQ_GAP
        assert "Multi-step" in failure.detail


class TestGtMonotonicCheck:
    def test_increasing_passes(self) -> None:
        outcome, _ = gt_monotonic_check(
            {"timestamp": "2026-02-28T12:00:01"}, "2026-02-28T12:00:00"
        )
        assert outcome == VerifyOutcome.PASS

    def test_equal_passes(self) -> None:
        outcome, _ = gt_monotonic_check(
            {"timestamp": "2026-02-28T12:00:00"}, "2026-02-28T12:00:00"
        )
        assert outcome == VerifyOutcome.PASS

    def test_decreasing_rejects(self) -> None:
        outcome, failure = gt_monotonic_check(
            {"timestamp": "2026-02-28T11:00:00"}, "2026-02-28T12:00:00"
        )
        assert outcome == VerifyOutcome.FAIL
        assert failure is not None
        assert failure.failure_type == FailureType.GT_NON_MONOTONIC

    def test_first_entry_no_prior(self) -> None:
        outcome, _ = gt_monotonic_check({"timestamp": "2026-02-28T12:00:00"}, None)
        assert outcome == VerifyOutcome.PASS


class TestVersionCheck:
    def test_supported_version(self) -> None:
        outcome, _ = version_check("0.1.0")
        assert outcome == VerifyOutcome.PASS

    def test_unknown_version_rejects(self) -> None:
        outcome, failure = version_check("99.0.0")
        assert outcome == VerifyOutcome.FAIL
        assert failure is not None
        assert failure.failure_type == FailureType.VERSION_UNKNOWN


class TestEventTypeCheck:
    def test_all_13_governance_events(self) -> None:
        from bridge.types import PHOENIX_GOVERNANCE_EVENTS
        for et in PHOENIX_GOVERNANCE_EVENTS:
            outcome, _ = event_type_check(et)
            assert outcome == VerifyOutcome.PASS, f"{et} should pass"

    def test_heartbeat_accepted(self) -> None:
        outcome, _ = event_type_check("HEARTBEAT")
        assert outcome == VerifyOutcome.PASS

    def test_unknown_type_rejects(self) -> None:
        outcome, failure = event_type_check("INVENTED_TYPE")
        assert outcome == VerifyOutcome.FAIL
        assert failure.failure_type == FailureType.EVENT_TYPE_UNKNOWN


class TestVerifyEntryPipeline:
    """Full verification pipeline — all checks in sequence."""

    def test_valid_entry_passes_all(
        self, fake_log: FakeGovernanceLog, phoenix_key: bytes
    ) -> None:
        entry = fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        outcome, failures = verify_entry(
            entry=entry,
            phoenix_key=phoenix_key,
            last_seen_seq=0,
            last_seen_gt=None,
            expected_hash_prev=GENESIS_HASH,
        )
        assert outcome == VerifyOutcome.PASS
        assert failures == []

    def test_bad_sig_fails_before_replay(
        self, fake_log: FakeGovernanceLog
    ) -> None:
        entry = fake_log.append("LEASE_ACTIVATION", {"lease_id": "l1"})
        outcome, failures = verify_entry(
            entry=entry,
            phoenix_key=b"wrong",
            last_seen_seq=0,
            last_seen_gt=None,
            expected_hash_prev=GENESIS_HASH,
        )
        assert outcome == VerifyOutcome.FAIL
        assert len(failures) == 1
        assert failures[0].failure_type == FailureType.SIG_INVALID

    def test_multi_entry_sequence(
        self, populated_log: FakeGovernanceLog, phoenix_key: bytes
    ) -> None:
        """5 entries, all should pass sequentially."""
        import json

        entries: list[dict] = []
        with open(populated_log.log_path) as f:
            for line in f:
                s = line.strip()
                if s:
                    entries.append(json.loads(s))

        assert len(entries) == 5

        prev_hash = GENESIS_HASH
        prev_seq = 0
        prev_gt = None

        for entry in entries:
            outcome, failures = verify_entry(
                entry=entry,
                phoenix_key=phoenix_key,
                last_seen_seq=prev_seq,
                last_seen_gt=prev_gt,
                expected_hash_prev=prev_hash,
            )
            assert outcome == VerifyOutcome.PASS, (
                f"Entry seq={entry['seq']} failed: {failures}"
            )
            prev_hash = compute_entry_hash(entry)
            prev_seq = entry["seq"]
            prev_gt = entry["timestamp"]
