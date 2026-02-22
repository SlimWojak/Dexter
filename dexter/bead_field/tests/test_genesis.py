"""Test genesis machinery: curation, delta, snapshot (Phase H).

Tests use synthetic CLAIMs to verify the machinery works correctly.
Actual curation of 981 CLAIMs is a separate step with HALT gate.
"""

import json
import pytest
from pathlib import Path

from bead_field.schema.enums import BeadType, TemporalClass, PolicyType
from bead_field.integrity.chain import verify_chain, verify_hash_self
from bead_field.integrity.merkle import MerkleTree
from bead_field.integrity.signing import KeyManager, verify_dual
from bead_field.store.bitemporal import BeadStore
from bead_field.store.queries import query_pattern_beads

from bead_field.genesis.curator import (
    curate, CurationCategory, CuratedClaim,
    load_claims, generate_curation_report,
)
from bead_field.genesis.delta import build_delta_content, OLYA_CORRECTIONS_V03
from bead_field.genesis.snapshot import (
    build_genesis_beads, build_genesis_snapshot, _extraction_claim_to_bead_content,
)


@pytest.fixture
def keys():
    return KeyManager.generate()


@pytest.fixture
def store():
    s = BeadStore(":memory:")
    yield s
    s.close()


def _make_claim(sig_id="S-001", condition="IF price enters FVG", action="THEN look for displacement",
                source_video="https://youtube.com/test", drawer=1, mock=False):
    source = "ICT 2022 Mentorship - Episode 1 (MOCK)" if mock else source_video
    return {
        "bead_type": "CLAIM",
        "source_system": "DEXTER",
        "source_video": source,
        "source_url": source,
        "source_timestamp": "0:14",
        "source_quote": "test quote",
        "signature": {
            "id": sig_id,
            "condition": condition,
            "action": action,
            "drawer": drawer,
            "drawer_confidence": "inferred",
            "drawer_basis": "test",
        },
        "extraction_meta": {
            "theorist_model": "deepseek-v3.2",
            "auditor_model": "gemini-2.0-flash",
            "auditor_verdict": "SURVIVED",
            "extraction_date": "2026-02-03T14:37:26+00:00",
            "bundle_id": "B-TEST",
        },
        "phoenix_meta": {"status": "UNVALIDATED"},
    }


# --- Curation ---

class TestCuration:
    def test_valid_claim_included(self):
        claims = [_make_claim()]
        curated = curate(claims)
        assert len(curated) == 1
        assert curated[0].category == CurationCategory.INCLUDE

    def test_mock_claim_excluded_as_artifact(self):
        claims = [_make_claim(mock=True)]
        curated = curate(claims)
        assert curated[0].category == CurationCategory.EXCLUDE_ARTIFACT

    def test_cbdr_claim_excluded_as_contradiction(self):
        claims = [_make_claim(condition="IF CBDR range is defined")]
        curated = curate(claims)
        assert curated[0].category == CurationCategory.EXCLUDE_CONTRADICTION
        assert "CBDR" in curated[0].reason

    def test_smt_claim_excluded_as_contradiction(self):
        claims = [_make_claim(condition="IF SMT divergence detected")]
        curated = curate(claims)
        assert curated[0].category == CurationCategory.EXCLUDE_CONTRADICTION

    def test_time_stop_excluded(self):
        claims = [_make_claim(action="THEN apply time stop at 30 min")]
        curated = curate(claims)
        assert curated[0].category == CurationCategory.EXCLUDE_CONTRADICTION

    def test_structure_break_exit_excluded(self):
        claims = [_make_claim(action="THEN use structure break exit")]
        curated = curate(claims)
        assert curated[0].category == CurationCategory.EXCLUDE_CONTRADICTION

    def test_mixed_batch_categories(self):
        claims = [
            _make_claim(sig_id="S-OK"),
            _make_claim(sig_id="S-MOCK", mock=True),
            _make_claim(sig_id="S-CBDR", condition="IF CBDR indicates range"),
            _make_claim(sig_id="S-OK2", condition="IF OTE level reached"),
        ]
        curated = curate(claims)
        categories = {c.signature_id: c.category for c in curated}
        assert categories["S-OK"] == CurationCategory.INCLUDE
        assert categories["S-MOCK"] == CurationCategory.EXCLUDE_ARTIFACT
        assert categories["S-CBDR"] == CurationCategory.EXCLUDE_CONTRADICTION
        assert categories["S-OK2"] == CurationCategory.INCLUDE

    def test_curated_claim_properties(self):
        claims = [_make_claim(sig_id="S-042")]
        curated = curate(claims)
        assert curated[0].signature_id == "S-042"
        assert curated[0].source
        assert curated[0].bundle_id == "B-TEST"


class TestCurationReport:
    def test_report_generated(self, tmp_path):
        claims = [_make_claim(), _make_claim(mock=True), _make_claim(condition="IF CBDR range")]
        curated = curate(claims)
        report_path = tmp_path / "CURATION_REPORT.md"
        summary = generate_curation_report(curated, report_path)

        assert report_path.exists()
        assert summary["total"] == 3
        assert summary["genesis_include"] == 1
        assert summary["exclude_artifact"] == 1
        assert summary["exclude_contradiction"] == 1

    def test_report_contains_halt_notice(self, tmp_path):
        curated = curate([_make_claim()])
        report_path = tmp_path / "CURATION_REPORT.md"
        generate_curation_report(curated, report_path)
        content = report_path.read_text()
        assert "HALT" in content
        assert "G must review" in content


# --- Delta ---

class TestDelta:
    def test_13_corrections(self):
        assert len(OLYA_CORRECTIONS_V03) == 13

    def test_delta_content_structure(self):
        content = build_delta_content()
        assert content["policy_name"] == "METHODOLOGY_DELTA_v0.1_to_v0.3"
        assert content["authority"] == "Olya"
        assert len(content["rules"]["corrections"]) == 13

    def test_removed_concepts_listed(self):
        content = build_delta_content()
        removed = content["rules"]["removed_concepts"]
        assert "CBDR" in removed
        assert "SMT" in removed


# --- Snapshot ---

class TestClaimConversion:
    def test_extraction_claim_to_bead_content(self):
        claim = _make_claim(condition="IF FVG on HTF", action="THEN enter at OTE", drawer=4)
        content = _extraction_claim_to_bead_content(claim)
        assert "FVG" in content["conclusion"]
        assert content["drawer"] == "ENTRY_MODEL"
        assert "FVG" in content["icm_terms"]
        assert "HTF" in content["icm_terms"]
        assert "OTE" in content["icm_terms"]

    def test_null_drawer_defaults_to_htf_bias(self):
        claim = _make_claim(drawer=None)
        content = _extraction_claim_to_bead_content(claim)
        assert content["drawer"] == "HTF_BIAS"


class TestBuildGenesisBeads:
    def test_builds_correct_count(self, keys):
        curated = curate([_make_claim(sig_id=f"S-{i}") for i in range(5)])
        beads = build_genesis_beads(curated, keys)
        assert len(beads) == 6  # 5 CLAIMs + 1 METHODOLOGY_DELTA

    def test_all_beads_are_pattern_class(self, keys):
        curated = curate([_make_claim()])
        beads = build_genesis_beads(curated, keys)
        for bead in beads:
            assert bead.temporal_class == TemporalClass.PATTERN

    def test_all_beads_have_ancestral_tag(self, keys):
        curated = curate([_make_claim()])
        beads = build_genesis_beads(curated, keys)
        for bead in beads:
            assert "ANCESTRAL" in bead.tags

    def test_all_beads_have_valid_hash(self, keys):
        curated = curate([_make_claim(), _make_claim(sig_id="S-2")])
        beads = build_genesis_beads(curated, keys)
        for bead in beads:
            assert verify_hash_self(bead)

    def test_beads_form_hash_chain(self, keys):
        curated = curate([_make_claim(sig_id=f"S-{i}") for i in range(5)])
        beads = build_genesis_beads(curated, keys)
        verify_chain(beads)

    def test_last_bead_is_delta(self, keys):
        curated = curate([_make_claim()])
        beads = build_genesis_beads(curated, keys)
        assert beads[-1].bead_type == BeadType.POLICY
        assert "METHODOLOGY_DELTA" in beads[-1].tags

    def test_excludes_artifacts(self, keys):
        curated = curate([_make_claim(), _make_claim(mock=True)])
        beads = build_genesis_beads(curated, keys)
        assert len(beads) == 2  # 1 included CLAIM + 1 DELTA (mock excluded)


class TestBuildGenesisSnapshot:
    def test_snapshot_creates_merkle_tree(self, keys, store):
        curated = curate([_make_claim(sig_id=f"S-{i}") for i in range(3)])
        beads = build_genesis_beads(curated, keys)
        snapshot = build_genesis_snapshot(beads, keys, store)

        assert snapshot["merkle_root"]
        assert len(snapshot["merkle_root"]) == 64
        assert snapshot["bead_count"] == 4  # 3 CLAIMs + 1 DELTA

    def test_all_beads_stored(self, keys, store):
        curated = curate([_make_claim(sig_id=f"S-{i}") for i in range(3)])
        beads = build_genesis_beads(curated, keys)
        build_genesis_snapshot(beads, keys, store)

        assert store.count() == 5  # 3 CLAIMs + 1 DELTA + 1 GENESIS_ANCHOR

    def test_all_beads_have_merkle_batch_id(self, keys, store):
        curated = curate([_make_claim()])
        beads = build_genesis_beads(curated, keys)
        snapshot = build_genesis_snapshot(beads, keys, store)

        for bead in beads:
            retrieved = store.get(bead.bead_id)
            assert retrieved.merkle_batch_id == snapshot["batch_id"]

    def test_genesis_anchor_exists(self, keys, store):
        curated = curate([_make_claim()])
        beads = build_genesis_beads(curated, keys)
        snapshot = build_genesis_snapshot(beads, keys, store)

        anchor = store.get(snapshot["anchor_bead_id"])
        assert anchor is not None
        assert anchor.bead_type == BeadType.POLICY
        assert "GENESIS_ANCHOR" in anchor.tags

    def test_merkle_proof_for_any_genesis_bead(self, keys, store):
        curated = curate([_make_claim(sig_id=f"S-{i}") for i in range(5)])
        beads = build_genesis_beads(curated, keys)
        snapshot = build_genesis_snapshot(beads, keys, store)

        tree = snapshot["tree"]
        for i, bead in enumerate(beads):
            proof = tree.proof(i)
            assert MerkleTree.verify_proof(bead.hash_self, proof, snapshot["merkle_root"])

    def test_genesis_beads_queryable_as_pattern(self, keys, store):
        """EC3: Ancestral CLAIMs queryable as PATTERN-class beads."""
        curated = curate([_make_claim(sig_id=f"S-{i}") for i in range(3)])
        beads = build_genesis_beads(curated, keys)
        build_genesis_snapshot(beads, keys, store)

        pattern_beads = query_pattern_beads(store.connection, bead_type="CLAIM")
        assert len(pattern_beads) == 3
        for pb in pattern_beads:
            assert pb.temporal_class == TemporalClass.PATTERN
            assert "ANCESTRAL" in pb.tags
