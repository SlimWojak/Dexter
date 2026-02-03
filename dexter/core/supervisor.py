"""Supervisor — restart/health wrapper for loop.py.

Handles crash recovery with exponential backoff per heartbeat.yaml config.
Runs as the container entrypoint; manages loop.py as a subprocess.
"""

import argparse
import logging
import subprocess
import sys
import time
from pathlib import Path

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [supervisor] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("dexter.supervisor")

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config" / "heartbeat.yaml"


def load_backoff_config(config_path: Path) -> dict:
    defaults = {"initial_seconds": 1, "multiplier": 2, "max_seconds": 60}
    if not config_path.exists():
        return defaults
    with open(config_path) as f:
        cfg = yaml.safe_load(f) or {}
    backoff = cfg.get("supervisor", {}).get("restart_backoff", {})
    return {
        "initial_seconds": backoff.get("initial_seconds", defaults["initial_seconds"]),
        "multiplier": backoff.get("multiplier", defaults["multiplier"]),
        "max_seconds": backoff.get("max_seconds", defaults["max_seconds"]),
    }


def run_loop(config_path: Path) -> int:
    """Run loop.py as subprocess, return exit code."""
    cmd = [
        sys.executable, "-u",
        str(Path(__file__).resolve().parent / "loop.py"),
        "--config", str(config_path),
    ]
    logger.info("Starting loop: %s", " ".join(cmd))
    proc = subprocess.run(cmd)
    return proc.returncode


def main():
    parser = argparse.ArgumentParser(description="Dexter Supervisor")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()

    backoff_cfg = load_backoff_config(args.config)
    delay = backoff_cfg["initial_seconds"]
    multiplier = backoff_cfg["multiplier"]
    max_delay = backoff_cfg["max_seconds"]

    logger.info("Supervisor started. Backoff: %s", backoff_cfg)

    consecutive_failures = 0

    while True:
        exit_code = run_loop(args.config)

        if exit_code == 0:
            logger.info("Loop exited cleanly (code 0). Restarting.")
            delay = backoff_cfg["initial_seconds"]
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            logger.warning(
                "Loop crashed (code %d). Failure #%d. Restart in %ds.",
                exit_code, consecutive_failures, delay,
            )
            time.sleep(delay)
            delay = min(delay * multiplier, max_delay)


if __name__ == "__main__":
    main()
