"""Genesis Snapshot — build Merkle tree over curated CLAIMs, sign with sovereign key.

The Genesis Snapshot is the cryptographic origin of the entire refinery.
Every future bead traces lineage back to this root.

HALT after snapshot built — G signs with sovereign key.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from uuid6 import uuid7

from bead_field.clock.hlc import HLC
from bead_field.integrity.chain import append_to_chain
from bead_field.integrity.hashing import compute_hash
from bead_field.integrity.merkle import MerkleTree
from bead_field.integrity.signing import KeyPair, sign_hash
from bead_field.schema.core import AttestationEnvelope, BeadCore, SourceRef
from bead_field.schema.claim import ClaimBead
from bead_field.schema.policy import PolicyBead
from bead_field.schema.enums import (
    BeadType, Drawer, PolicyType, SourceType, TemporalClass,
)
from bead_field.store.bitemporal import BeadStore
from .curator import CuratedClaim, CurationCategory
from .delta import build_delta_content

DRAWER_MAP = {
    1: Drawer.HTF_BIAS,
    2: Drawer.MARKET_STRUCTURE,
    3: Drawer.PREMIUM_DISCOUNT,
    4: Drawer.ENTRY_MODEL,
    5: Drawer.CONFIRMATION,
}


def _extraction_claim_to_bead_content(claim: dict) -> dict:
    """Convert an extraction-phase CLAIM to Bead Field ClaimContent."""
    sig = claim.get("signature", {})
    raw_drawer = sig.get("drawer")

    if isinstance(raw_drawer, int):
        drawer = DRAWER_MAP.get(raw_drawer, Drawer.HTF_BIAS).value
    elif isinstance(raw_drawer, str) and raw_drawer in {d.value for d in Drawer}:
        drawer = raw_drawer
    else:
        drawer = Drawer.HTF_BIAS.value

    condition = sig.get("condition", "")
    action = sig.get("action", "")

    icm_terms = []
    for term in ["FVG", "OB", "OTE", "MSS", "MMM", "MMXM", "BOS", "CHOCH",
                  "IPDA", "HTF", "LTF", "BSL", "SSL", "EQH", "EQL"]:
        if term.lower() in condition.lower() or term.lower() in action.lower():
            icm_terms.append(term)

    source_ref_id = claim.get("extraction_meta", {}).get("bundle_id", "unknown")
    source_quote = claim.get("source_quote", "")

    return {
        "conclusion": f"{condition} → {action}",
        "reasoning_trace": f"Source: {source_quote}" if source_quote else "Extraction-phase signature",
        "premises_ref": [],
        "confidence_basis": f"Extraction-phase auditor: {claim.get('extraction_meta', {}).get('auditor_verdict', 'UNKNOWN')}",
        "drawer": drawer,
        "icm_terms": icm_terms,
    }


def build_genesis_beads(
    curated: list[CuratedClaim],
    keys: KeyPair,
    hlc: HLC | None = None,
) -> list[BeadCore]:
    """Convert curated CLAIMs to signed PATTERN-class Bead Field beads."""
    hlc = hlc or HLC()
    beads: list[BeadCore] = []
    prev_bead: BeadCore | None = None

    included = [c for c in curated if c.category == CurationCategory.INCLUDE]

    for curated_claim in included:
        content = _extraction_claim_to_bead_content(curated_claim.claim)
        source_bundle = curated_claim.claim.get("extraction_meta", {}).get("bundle_id", "unknown")

        bead = ClaimBead(
            bead_id=str(uuid7()),
            bead_type=BeadType.CLAIM,
            content=content,
            temporal_class=TemporalClass.PATTERN,
            knowledge_time_recorded_at=hlc.tick(),
            source_ref=SourceRef(
                source_type=SourceType.EXTRACTION,
                source_id=source_bundle,
                source_version="extraction-phase-v1",
            ),
            lineage=[],
            tags=["ANCESTRAL", "EXTRACTION_PHASE", f"bundle:{source_bundle}"],
            attestation=AttestationEnvelope(
                air_node_id="genesis-ceremony",
                code_hash="gate1-genesis",
            ),
        )

        linked = append_to_chain(bead, prev_bead)
        ecdsa_sig, pqc_sig = sign_hash(linked.hash_self, keys)
        signed = linked.model_copy(
            update={"attestation": linked.attestation.model_copy(
                update={"ecdsa_sig": ecdsa_sig, "pqc_sig": pqc_sig}
            )}
        )

        beads.append(signed)
        prev_bead = signed

    delta_content = build_delta_content()
    delta_bead = PolicyBead(
        bead_id=str(uuid7()),
        bead_type=BeadType.POLICY,
        content=delta_content,
        temporal_class=TemporalClass.PATTERN,
        knowledge_time_recorded_at=hlc.tick(),
        source_ref=SourceRef(
            source_type=SourceType.HUMAN,
            source_id="olya",
            source_version="v0.3-validation",
        ),
        lineage=[],
        tags=["ANCESTRAL", "METHODOLOGY_DELTA", "v0.1_to_v0.3"],
        attestation=AttestationEnvelope(
            air_node_id="genesis-ceremony",
            code_hash="gate1-genesis",
        ),
    )

    linked_delta = append_to_chain(delta_bead, prev_bead)
    ecdsa_sig, pqc_sig = sign_hash(linked_delta.hash_self, keys)
    signed_delta = linked_delta.model_copy(
        update={"attestation": linked_delta.attestation.model_copy(
            update={"ecdsa_sig": ecdsa_sig, "pqc_sig": pqc_sig}
        )}
    )
    beads.append(signed_delta)

    return beads


def build_genesis_snapshot(
    beads: list[BeadCore],
    keys: KeyPair,
    store: BeadStore,
    hlc: HLC | None = None,
) -> dict:
    """Build the Genesis Merkle tree and GENESIS_ANCHOR policy bead.

    Returns snapshot metadata. Does NOT sign with sovereign key — that's G's job.
    """
    hlc = hlc or HLC()

    for bead in beads:
        store.insert(bead)

    leaves = [b.hash_self for b in beads]
    tree = MerkleTree(leaves)
    batch_id = str(uuid7())

    anchor_content = {
        "policy_name": "GENESIS_ANCHOR",
        "policy_type": PolicyType.OPERATIONAL.value,
        "rules": {
            "merkle_root": tree.root,
            "bead_count": tree.leaf_count,
            "signed_by": "G (AWAITING)",
            "description": "Cryptographic origin of the a8ra Bead Field. Bead Zero.",
        },
        "effective_from": datetime.now(timezone.utc).isoformat(),
        "effective_to": None,
        "supersedes": None,
        "authority": "G",
    }

    anchor_bead = PolicyBead(
        bead_id=str(uuid7()),
        bead_type=BeadType.POLICY,
        content=anchor_content,
        temporal_class=TemporalClass.PATTERN,
        knowledge_time_recorded_at=hlc.tick(),
        source_ref=SourceRef(
            source_type=SourceType.HUMAN,
            source_id="G",
            source_version="genesis-ceremony",
        ),
        lineage=[],
        tags=["GENESIS_ANCHOR", "BEAD_ZERO"],
        attestation=AttestationEnvelope(
            air_node_id="genesis-ceremony",
            code_hash="gate1-genesis",
        ),
    )

    linked_anchor = append_to_chain(anchor_bead, beads[-1])
    ecdsa_sig, pqc_sig = sign_hash(linked_anchor.hash_self, keys)
    signed_anchor = linked_anchor.model_copy(
        update={"attestation": linked_anchor.attestation.model_copy(
            update={"ecdsa_sig": ecdsa_sig, "pqc_sig": pqc_sig}
        )}
    )
    store.insert(signed_anchor)

    store.connection.execute(
        """INSERT INTO merkle_batches (batch_id, merkle_root, bead_count, timestamp, trigger_bead_id)
           VALUES (?, ?, ?, ?, ?)""",
        (batch_id, tree.root, tree.leaf_count,
         datetime.now(timezone.utc).isoformat(), signed_anchor.bead_id),
    )

    for bead in beads:
        store.set_merkle_batch_id(bead.bead_id, batch_id)
    store.set_merkle_batch_id(signed_anchor.bead_id, batch_id)
    store.connection.commit()

    return {
        "merkle_root": tree.root,
        "bead_count": tree.leaf_count,
        "batch_id": batch_id,
        "anchor_bead_id": signed_anchor.bead_id,
        "tree": tree,
    }
