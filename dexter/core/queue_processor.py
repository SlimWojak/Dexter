"""Queue Processor: batch extraction from extraction_queue.yaml.

Reads the Cartographer-generated queue, processes transcripts sequentially,
updates status per video. Supports dry_run and limit controls.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger("dexter.queue_processor")

CORPUS_DIR = Path(__file__).resolve().parent.parent / "corpus"
EXTRACTION_QUEUE_FILE = CORPUS_DIR / "extraction_queue.yaml"


def load_queue(queue_path: Optional[Path] = None) -> Dict:
    """Load extraction queue from YAML file."""
    path = queue_path or EXTRACTION_QUEUE_FILE
    if not path.exists():
        raise FileNotFoundError(f"Extraction queue not found: {path}")
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    return data


def save_queue(data: Dict, queue_path: Optional[Path] = None) -> None:
    """Save updated queue back to YAML file with atomic write.

    Uses write-tmp + rename pattern for crash safety:
    1. Write to .tmp file
    2. Flush + fsync to ensure data on disk
    3. Atomic rename (os.replace is atomic on POSIX)

    Crash at any point = either old file or new file, never partial.
    """
    import os

    path = queue_path or EXTRACTION_QUEUE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temporary file first
    tmp_path = path.with_suffix(path.suffix + ".tmp")

    with open(tmp_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        f.flush()
        os.fsync(f.fileno())  # Ensure data is written to disk

    # Atomic rename (POSIX guarantees this is atomic)
    os.replace(tmp_path, path)

    logger.info("Queue saved (atomic): %s", path)


def get_pending_videos(queue_data: Dict) -> List[Dict]:
    """Get all videos with status QUEUED (not yet processed)."""
    return [
        v for v in queue_data.get("queue", [])
        if v.get("status") == "QUEUED"
    ]


def update_video_status(
    queue_data: Dict,
    video_id: str,
    status: str,
    *,
    bundle_id: Optional[str] = None,
    error: Optional[str] = None,
) -> None:
    """Update a video's status in the queue data (in-memory)."""
    for v in queue_data.get("queue", []):
        if v.get("id") == video_id:
            v["status"] = status
            if bundle_id:
                v["bundle_id"] = bundle_id
            if error:
                v["error"] = error
            break


def process_queue(
    *,
    queue_path: Optional[Path] = None,
    limit: int = 0,
    dry_run: bool = False,
    delay_seconds: float = 5.0,
) -> Dict:
    """Process extraction queue — fetch transcripts and run pipeline.

    Args:
        queue_path: Path to extraction_queue.yaml (default: corpus/extraction_queue.yaml)
        limit: Max videos to process (0 = all pending)
        dry_run: If True, log what would be processed without running
        delay_seconds: Pause between videos (rate limiting)

    Returns:
        Summary dict with processed/skipped/failed counts.
    """
    queue_data = load_queue(queue_path)
    pending = get_pending_videos(queue_data)

    if limit > 0:
        pending = pending[:limit]

    logger.info(
        "Queue: %d total, %d pending, processing %d (dry_run=%s)",
        len(queue_data.get("queue", [])),
        len(get_pending_videos(queue_data)),
        len(pending),
        dry_run,
    )

    processed = 0
    failed = 0
    skipped = 0
    results = []

    for video in pending:
        video_id = video.get("id", "?")
        title = video.get("title", "?")[:60]
        url = video.get("url", "")

        if not url:
            logger.warning("Skipping %s: no URL", video_id)
            skipped += 1
            continue

        if dry_run:
            logger.info("[DRY RUN] Would process: %s — %s", video_id, title)
            results.append({"video_id": video_id, "title": title, "action": "dry_run"})
            continue

        logger.info("Processing [%d/%d]: %s — %s", processed + 1, len(pending), video_id, title)
        update_video_status(queue_data, video_id, "PROCESSING")
        save_queue(queue_data, queue_path)

        try:
            from core.loop import process_transcript
            summary = process_transcript(url)
            update_video_status(
                queue_data,
                video_id,
                "DONE",
                bundle_id=summary.get("bundle_id"),
            )
            processed += 1
            results.append({
                "video_id": video_id,
                "title": title,
                "status": "DONE",
                "bundle_id": summary.get("bundle_id"),
                "validated": summary.get("validated", 0),
                "rejected": summary.get("rejected", 0),
            })
            logger.info(
                "Completed %s: %d validated, %d rejected, bundle=%s",
                video_id,
                summary.get("validated", 0),
                summary.get("rejected", 0),
                summary.get("bundle_id"),
            )
        except Exception as e:
            logger.exception("Failed processing %s: %s", video_id, e)
            update_video_status(queue_data, video_id, "FAILED", error=str(e)[:200])
            failed += 1
            results.append({
                "video_id": video_id,
                "title": title,
                "status": "FAILED",
                "error": str(e)[:200],
            })

        save_queue(queue_data, queue_path)

        if delay_seconds > 0 and not dry_run:
            time.sleep(delay_seconds)

    summary = {
        "total_pending": len(get_pending_videos(load_queue(queue_path))) if not dry_run else len(pending),
        "processed": processed,
        "failed": failed,
        "skipped": skipped,
        "dry_run": dry_run,
        "results": results,
    }

    logger.info(
        "Queue processing complete: %d processed, %d failed, %d skipped",
        processed, failed, skipped,
    )

    return summary
