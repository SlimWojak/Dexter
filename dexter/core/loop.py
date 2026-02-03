"""Main heartbeat loop — configurable interval + jitter from heartbeat.yaml.

Each tick:
  1. Log heartbeat bead
  2. Check compression threshold
  3. Dispatch to router (stub in Phase 1)
  4. Sleep interval +/- jitter
"""

import argparse
import logging
import random
import signal
import sys
import time
from pathlib import Path

import yaml

from core.context import append_bead, count_beads, needs_compression
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
    # Merge with defaults
    for key in defaults:
        if key not in cfg:
            cfg[key] = defaults[key]
    return cfg


def heartbeat_tick(cfg: dict, tick_count: int) -> None:
    """Execute one heartbeat tick."""
    hb_cfg = cfg["heartbeat"]
    comp_cfg = cfg["bead_compression"]

    # Write heartbeat bead
    bead = append_bead(
        bead_type="HEARTBEAT",
        content=f"tick_{tick_count}",
        source="core.loop",
        metadata={"tick": tick_count, "beads_count": count_beads()},
    )
    logger.info("Tick %d | bead=%s | beads_count=%d", tick_count, bead["id"], count_beads())

    # Check compression threshold
    max_beads = comp_cfg.get("max_beads", 25)
    if needs_compression(max_beads):
        logger.info("Compression threshold reached (%d beads). Chronicler needed.", max_beads)
        # Phase 3: trigger chronicler via router
        dispatch("chronicler", {"task": "compress_beads", "threshold": max_beads})

    # Health check beacon (Phase 1: just log)
    if hb_cfg.get("health_check_enabled", True):
        logger.info("Health: OK | tick=%d", tick_count)


def run(config_path: Path) -> None:
    """Main loop — runs until signal or _running is False."""
    global _running

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    cfg = load_config(config_path)
    hb = cfg["heartbeat"]
    interval = hb.get("interval_seconds", 60)
    jitter_max = hb.get("jitter_max_seconds", 10)

    logger.info("Heartbeat started. interval=%ds jitter=+/-%ds", interval, jitter_max)

    tick_count = 0

    while _running:
        tick_count += 1
        try:
            heartbeat_tick(cfg, tick_count)
        except Exception:
            logger.exception("Error in heartbeat tick %d", tick_count)

        # Sleep with jitter
        jitter = random.uniform(-jitter_max, jitter_max)
        sleep_time = max(1, interval + jitter)
        logger.debug("Sleeping %.1fs (interval=%d, jitter=%.1f)", sleep_time, interval, jitter)

        # Interruptible sleep
        deadline = time.monotonic() + sleep_time
        while _running and time.monotonic() < deadline:
            time.sleep(min(1.0, deadline - time.monotonic()))

    logger.info("Heartbeat stopped after %d ticks.", tick_count)


def main():
    parser = argparse.ArgumentParser(description="Dexter Heartbeat Loop")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
