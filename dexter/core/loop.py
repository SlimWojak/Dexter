"""Main heartbeat loop — configurable interval + jitter from heartbeat.yaml.

Each tick:
  1. Log heartbeat bead
  2. Check compression threshold
  3. Dispatch to router (stub in Phase 1)
  4. Sleep interval +/- jitter

Phase 3: adds process_transcript pipeline for full extraction loop.
"""

from __future__ import annotations

import argparse
import logging
import random
import signal
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from core.context import (
    append_bead,
    append_negative_bead,
    count_beads,
    needs_compression,
    read_negative_beads,
)
from core.router import dispatch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [loop] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("dexter.loop")

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config" / "heartbeat.yaml"

_running = True


def _handle_signal(signum, frame):
    global _running
    logger.info("Received signal %d. Shutting down gracefully.", signum)
    _running = False


def load_config(config_path: Path) -> dict:
    defaults = {
        "heartbeat": {"interval_seconds": 60, "jitter_max_seconds": 10, "health_check_enabled": True},
        "bead_compression": {"max_beads": 25, "max_tokens": 750},
    }
    if not config_path.exists():
        logger.warning("Config not found at %s, using defaults.", config_path)
        return defaults
    with open(config_path) as f:
        cfg = yaml.safe_load(f) or {}
    for key in defaults:
        if key not in cfg:
            cfg[key] = defaults[key]
    return cfg


def heartbeat_tick(cfg: dict, tick_count: int) -> None:
    """Execute one heartbeat tick."""
    hb_cfg = cfg["heartbeat"]
    comp_cfg = cfg["bead_compression"]

    bead = append_bead(
        bead_type="HEARTBEAT",
        content=f"tick_{tick_count}",
        source="core.loop",
        metadata={"tick": tick_count, "beads_count": count_beads()},
    )
    logger.info("Tick %d | bead=%s | beads_count=%d", tick_count, bead["id"], count_beads())

    max_beads = comp_cfg.get("max_beads", 25)
    if needs_compression(max_beads):
        logger.info("Compression threshold reached (%d beads). Chronicler needed.", max_beads)
        dispatch("chronicler", {"task": "compress_beads", "threshold": max_beads})

    if hb_cfg.get("health_check_enabled", True):
        logger.info("Health: OK | tick=%d", tick_count)


# ---------------------------------------------------------------------------
# Phase 3: Full extraction pipeline
# ---------------------------------------------------------------------------

def process_transcript(transcript_url: str) -> Dict:
    """Full Dexter extraction loop (synchronous, mock mode compatible).

    Pipeline:
      1. Fetch transcript (Supadata stub)
      2. Theorist extracts signatures
      3. Auditor validates each signature
      4. Bundler packages validated signatures
      5. Log results, update beads

    Returns:
        Summary dict with extraction results.
    """
    from skills.transcript.supadata import fetch_transcript, format_for_theorist, chunk_transcript
    from core.auditor import audit_signature
    from core.bundler import generate_bundle, save_bundle
    from core.router import is_llm_mode

    logger.info("=== PROCESS TRANSCRIPT: %s ===", transcript_url)

    # 1. Fetch transcript
    transcript = fetch_transcript(transcript_url)
    formatted = format_for_theorist(transcript)
    logger.info("Fetched transcript: %s (%d segments)", transcript.get("title", "?"), len(transcript.get("segments", [])))

    append_bead(
        bead_type="TRANSCRIPT_FETCH",
        content=transcript.get("title", "unknown"),
        source="core.loop.process_transcript",
        metadata={"video_id": transcript.get("video_id"), "segments": len(transcript.get("segments", []))},
    )

    # 2. Theorist extracts signatures
    # In LLM mode, build chunks for context-windowed extraction
    chunks = None
    if is_llm_mode():
        chunks = chunk_transcript(transcript)
        logger.info("Built %d chunks for LLM extraction", len(chunks))

    theorist_result = dispatch("theorist", {
        "task": "extract_signatures",
        "transcript": formatted,
        "transcript_data": transcript,
        "chunks": chunks,
    })
    signatures = theorist_result.get("signatures", [])
    logger.info("Theorist extracted %d signatures", len(signatures))

    append_bead(
        bead_type="EXTRACTION",
        content=f"extracted_{len(signatures)}_signatures",
        source="core.loop.process_transcript",
        metadata={"count": len(signatures), "theorist_model": theorist_result.get("model")},
    )

    # 3. Auditor validates each signature
    validated = []
    rejected = []
    for sig in signatures:
        result = audit_signature(sig)
        if result["verdict"] == "REJECT":
            rejected.append(sig)
            append_negative_bead(
                reason=result["reason"],
                source_signature=sig.get("id", "unknown"),
            )
            logger.info("REJECTED %s: %s", sig.get("id"), result["reason"])
        else:
            validated.append(sig)
            logger.info("PASSED %s", sig.get("id"))

    logger.info("Audit: %d validated, %d rejected", len(validated), len(rejected))

    # 4. Bundle validated signatures
    bundle_path = None
    bundle_id = None
    if validated:
        from core.auditor import audit_batch
        audit_summary = audit_batch(signatures)

        from core.bundler import generate_bundle_id
        bundle_id = generate_bundle_id()
        try:
            bundle_content = generate_bundle(
                bundle_id=bundle_id,
                source_url=transcript_url,
                timestamp_range=_compute_timestamp_range(transcript),
                validated_signatures=validated,
                rejected_signatures=rejected,
                auditor_summary=audit_summary,
                negative_beads=[nb.get("id", "?") for nb in read_negative_beads(limit=10)],
                provenance={
                    "transcript_method": "Supadata",
                    "theorist_model": theorist_result.get("model", "unknown"),
                },
            )
            bundle_path = save_bundle(
                bundle_id,
                bundle_content,
                metadata={
                    "source_url": transcript_url,
                    "validated": len(validated),
                    "rejected": len(rejected),
                },
            )
            logger.info("Bundle saved: %s", bundle_path)

            append_bead(
                bead_type="BUNDLE",
                content=bundle_id,
                source="core.loop.process_transcript",
                metadata={"validated": len(validated), "rejected": len(rejected), "path": str(bundle_path)},
            )

            # Export CLAIM_BEADs for Phoenix integration
            from core.bundler import export_claim_beads
            claims_path = export_claim_beads(
                bundle_id,
                validated,
                bundle_meta={
                    "video_title": transcript.get("title", ""),
                    "video_url": transcript_url,
                    "theorist_model": theorist_result.get("model", "unknown"),
                    "auditor_model": "google/gemini-2.0-flash-exp",
                },
            )
            logger.info("CLAIM_BEADs exported: %s", claims_path)
        except Exception:
            logger.exception("Bundle generation failed for %s", bundle_id)

    # 5. Summary
    summary = {
        "transcript_url": transcript_url,
        "transcript_title": transcript.get("title"),
        "total_extracted": len(signatures),
        "validated": len(validated),
        "rejected": len(rejected),
        "bundle_id": bundle_id,
        "bundle_path": str(bundle_path) if bundle_path else None,
    }

    logger.info(
        "=== COMPLETE: %d extracted, %d validated, %d rejected, bundle=%s ===",
        len(signatures), len(validated), len(rejected), bundle_id,
    )

    return summary


def _compute_timestamp_range(transcript: Dict) -> str:
    """Compute timestamp range string from transcript segments."""
    segments = transcript.get("segments", [])
    if not segments:
        return "0:00-0:00"
    start = segments[0].get("start", 0)
    end = segments[-1].get("start", 0)
    start_str = f"{int(start) // 60}:{int(start) % 60:02d}"
    end_str = f"{int(end) // 60}:{int(end) % 60:02d}"
    return f"{start_str}-{end_str}"


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run(config_path: Path, *, once: bool = False, transcript: Optional[str] = None) -> None:
    """Main loop — runs until signal or _running is False.

    Args:
        once: if True, run one tick and exit
        transcript: if set, process this transcript URL then exit
    """
    global _running

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    cfg = load_config(config_path)
    hb = cfg["heartbeat"]
    interval = hb.get("interval_seconds", 60)
    jitter_max = hb.get("jitter_max_seconds", 10)

    logger.info("Heartbeat started. interval=%ds jitter=+/-%ds", interval, jitter_max)

    # Single transcript processing mode
    if transcript:
        process_transcript(transcript)
        return

    tick_count = 0

    while _running:
        tick_count += 1
        try:
            heartbeat_tick(cfg, tick_count)
        except Exception:
            logger.exception("Error in heartbeat tick %d", tick_count)

        if once:
            break

        jitter = random.uniform(-jitter_max, jitter_max)
        sleep_time = max(1, interval + jitter)

        deadline = time.monotonic() + sleep_time
        while _running and time.monotonic() < deadline:
            time.sleep(min(1.0, deadline - time.monotonic()))

    logger.info("Heartbeat stopped after %d ticks.", tick_count)


def main():
    parser = argparse.ArgumentParser(description="Dexter Heartbeat Loop")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--once", action="store_true", help="Run one tick and exit")
    parser.add_argument("--transcript", type=str, default=None, help="Process a transcript URL and exit")
    args = parser.parse_args()
    run(args.config, once=args.once, transcript=args.transcript)


if __name__ == "__main__":
    main()
