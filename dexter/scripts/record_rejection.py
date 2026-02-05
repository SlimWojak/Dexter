#!/usr/bin/env python3
"""Record human rejection of a CLAIM_BEAD → creates NEGATIVE_BEAD.

This is the back-propagation seam. When Olya (or G) rejects a claim,
run this script to record the rejection. The NEGATIVE_BEAD will then
feed back into the Theorist's context, preventing similar extractions.

Usage:
    python scripts/record_rejection.py --claim-id B-20260203-150140:S-007 --reason "OTE doesn't work this way"
    python scripts/record_rejection.py --claim-id S-007 --bundle B-20260203-150140 --reason "Missing context"
    python scripts/record_rejection.py --list-claims B-20260203-150140  # Show claims in bundle

The rejection flows:
    1. Human runs this script with claim ID + reason
    2. Script looks up original CLAIM_BEAD
    3. Creates NEGATIVE_BEAD with full provenance
    4. Chronicler preserves in THEORY.md (P1)
    5. Theorist receives in context (avoidance pattern)
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.context import append_negative_bead

logger = logging.getLogger("dexter.record_rejection")

BUNDLES_DIR = Path(__file__).resolve().parent.parent / "bundles"


def load_claims_from_bundle(bundle_id: str) -> List[Dict]:
    """Load all CLAIM_BEADs from a specific bundle.

    Args:
        bundle_id: Bundle ID like B-20260203-150140

    Returns:
        List of claim dicts
    """
    claims_file = BUNDLES_DIR / f"{bundle_id}_claims.jsonl"

    if not claims_file.exists():
        return []

    claims = []
    with open(claims_file) as f:
        for line in f:
            line = line.strip()
            if line:
                claims.append(json.loads(line))

    return claims


def find_claim(claim_spec: str, bundle_id: Optional[str] = None) -> Tuple[Optional[Dict], str]:
    """Find a CLAIM_BEAD by ID.

    Args:
        claim_spec: Either "B-20260203-150140:S-007" or just "S-007"
        bundle_id: Optional bundle ID if not in claim_spec

    Returns:
        (claim_dict or None, full_claim_id)
    """
    # Parse claim_spec
    if ":" in claim_spec:
        bundle_id, sig_id = claim_spec.split(":", 1)
    else:
        sig_id = claim_spec

    if not bundle_id:
        # Search all bundles
        for claims_file in sorted(BUNDLES_DIR.glob("*_claims.jsonl"), reverse=True):
            bundle = claims_file.stem.replace("_claims", "")
            claims = load_claims_from_bundle(bundle)
            for claim in claims:
                if claim.get("signature", {}).get("id") == sig_id:
                    full_id = f"{bundle}:{sig_id}"
                    return claim, full_id
        return None, claim_spec

    # Search specific bundle
    claims = load_claims_from_bundle(bundle_id)
    for claim in claims:
        if claim.get("signature", {}).get("id") == sig_id:
            full_id = f"{bundle_id}:{sig_id}"
            return claim, full_id

    return None, f"{bundle_id}:{sig_id}"


def list_claims_in_bundle(bundle_id: str) -> None:
    """Print all claims in a bundle for human review."""
    claims = load_claims_from_bundle(bundle_id)

    if not claims:
        print(f"No claims found in bundle {bundle_id}")
        return

    print(f"\n=== Claims in {bundle_id} ({len(claims)} total) ===\n")

    for claim in claims:
        sig = claim.get("signature", {})
        print(f"  {sig.get('id', '?'):6} | D{sig.get('drawer', '?')} | {sig.get('condition', '')[:60]}...")
        print(f"         | {sig.get('action', '')[:60]}...")
        print()


def record_rejection(
    claim_spec: str,
    reason: str,
    bundle_id: Optional[str] = None,
    rejected_by: str = "human",
) -> Dict:
    """Record a human rejection of a CLAIM_BEAD.

    Args:
        claim_spec: Claim ID like "B-20260203-150140:S-007" or "S-007"
        reason: Why it was rejected (even 2 words is signal)
        bundle_id: Optional bundle ID if not in claim_spec
        rejected_by: Who rejected ("human", "olya", "auditor")

    Returns:
        The created NEGATIVE_BEAD
    """
    # Find the original claim
    claim, full_claim_id = find_claim(claim_spec, bundle_id)

    if claim:
        sig = claim.get("signature", {})
        source_signature = sig.get("id", "")
        source_bundle = claim.get("extraction_meta", {}).get("bundle_id", "")
        drawer = sig.get("drawer")

        # Build enhanced reason with context
        condition = sig.get("condition", "")
        action = sig.get("action", "")
        enhanced_reason = f"{reason} | Original: {condition} → {action}"[:500]
    else:
        # Claim not found - still record rejection with what we have
        logger.warning("Claim not found: %s. Recording rejection anyway.", claim_spec)
        source_signature = claim_spec.split(":")[-1] if ":" in claim_spec else claim_spec
        source_bundle = bundle_id or (claim_spec.split(":")[0] if ":" in claim_spec else "")
        drawer = None
        enhanced_reason = reason

    # Create the NEGATIVE_BEAD
    negative = append_negative_bead(
        reason=enhanced_reason,
        source_signature=source_signature,
        source_bundle=source_bundle,
        source_claim_id=full_claim_id,
        drawer=drawer,
        rejected_by=rejected_by,
        metadata={
            "original_reason": reason,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    return negative


def main():
    parser = argparse.ArgumentParser(
        description="Record human rejection of a CLAIM_BEAD",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --claim-id B-20260203-150140:S-007 --reason "OTE doesn't apply here"
  %(prog)s --claim-id S-007 --bundle B-20260203-150140 --reason "Missing context"
  %(prog)s --list-claims B-20260203-150140

The rejection will create a NEGATIVE_BEAD that feeds back to Theorist.
"""
    )

    parser.add_argument(
        "--claim-id",
        help="Claim ID to reject (e.g., B-20260203-150140:S-007 or just S-007)",
    )
    parser.add_argument(
        "--bundle",
        help="Bundle ID if not included in claim-id",
    )
    parser.add_argument(
        "--reason",
        help="Why the claim is being rejected (even 2 words is useful)",
    )
    parser.add_argument(
        "--rejected-by",
        default="human",
        help="Who is rejecting (human, olya, auditor). Default: human",
    )
    parser.add_argument(
        "--list-claims",
        metavar="BUNDLE_ID",
        help="List all claims in a bundle for review",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    # List mode
    if args.list_claims:
        list_claims_in_bundle(args.list_claims)
        return 0

    # Rejection mode
    if not args.claim_id or not args.reason:
        parser.error("--claim-id and --reason are required for recording a rejection")

    negative = record_rejection(
        claim_spec=args.claim_id,
        reason=args.reason,
        bundle_id=args.bundle,
        rejected_by=args.rejected_by,
    )

    print(f"\nNEGATIVE_BEAD created:")
    print(f"  ID:              {negative['id']}")
    print(f"  Source Claim:    {negative['source_claim_id']}")
    print(f"  Source Sig:      {negative['source_signature']}")
    print(f"  Drawer:          {negative['drawer']}")
    print(f"  Rejected By:     {negative['rejected_by']}")
    print(f"  Reason:          {negative['reason'][:100]}...")
    print(f"  Timestamp:       {negative['timestamp']}")
    print()
    print("This rejection will feed back to Theorist on next extraction.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
