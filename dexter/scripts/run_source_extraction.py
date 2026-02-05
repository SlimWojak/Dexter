#!/usr/bin/env python3
"""Unified Source Extraction Runner — multi-source extraction orchestrator.

Processes extraction sources from multiple types:
- YouTube videos (from Cartographer queues)
- PDF documents (from data/sources/)
- Markdown files (from data/sources/)

Routes to appropriate extractor and applies source tier tags.

Usage:
    # Process all sources (dry run)
    python scripts/run_source_extraction.py

    # Process ICT 2022 playlist only
    python scripts/run_source_extraction.py --source ict_2022_mentorship --execute

    # Process PDF sources only
    python scripts/run_source_extraction.py --type pdf --execute --limit 5

    # Process specific queue file
    python scripts/run_source_extraction.py --queue corpus/ict_2022_mentorship_extraction_queue.yaml --execute
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env")

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [extractor] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("dexter.source_extractor")

# Directories
CORPUS_DIR = _PROJECT_ROOT / "corpus"
SOURCES_DIR = _PROJECT_ROOT / "data" / "sources"

# Source configurations
SOURCE_CONFIGS = {
    "ict_2022_mentorship": {
        "type": "youtube",
        "queue_file": "ict_2022_mentorship_extraction_queue.yaml",
        "source_tier": "CANON",
        "description": "ICT 2022 Mentorship playlist (24 videos)",
    },
    "blessed_trader": {
        "type": "pdf",
        "source_dir": "blessed_training",
        "source_tier": "LATERAL",
        "description": "Blessed Trader PDF course materials",
    },
    "olya_notes": {
        "type": "pdf",
        "source_dir": "olya_notes",
        "source_tier": "OLYA_PRIMARY",
        "description": "Olya's personal trading notes",
    },
    "layer_0": {
        "type": "markdown",
        "source_dir": "layer_0",
        "source_tier": "OLYA_PRIMARY",
        "description": "Layer 0 foundational context",
    },
    "full_channel": {
        "type": "youtube",
        "queue_file": "extraction_queue.yaml",
        "source_tier": "ICT_LEARNING",
        "description": "Full ICT channel (790 videos)",
    },
}


def discover_sources() -> Dict[str, Dict]:
    """Discover available sources and their status."""
    sources = {}

    for name, config in SOURCE_CONFIGS.items():
        source_info = {
            **config,
            "name": name,
            "available": False,
            "item_count": 0,
            "pending_count": 0,
        }

        if config["type"] == "youtube":
            queue_path = CORPUS_DIR / config["queue_file"]
            if queue_path.exists():
                with open(queue_path) as f:
                    queue_data = yaml.safe_load(f) or {}
                queue = queue_data.get("queue", [])
                pending = [v for v in queue if v.get("status") == "QUEUED"]
                source_info["available"] = True
                source_info["item_count"] = len(queue)
                source_info["pending_count"] = len(pending)
                source_info["queue_path"] = str(queue_path)

        elif config["type"] == "pdf":
            source_dir = SOURCES_DIR / config["source_dir"]
            if source_dir.exists():
                pdfs = list(source_dir.glob("*.pdf"))
                source_info["available"] = True
                source_info["item_count"] = len(pdfs)
                source_info["pending_count"] = len(pdfs)  # All pending until tracked
                source_info["source_path"] = str(source_dir)

        elif config["type"] == "markdown":
            source_dir = SOURCES_DIR / config["source_dir"]
            if source_dir.exists():
                mds = list(source_dir.glob("*.md"))
                source_info["available"] = True
                source_info["item_count"] = len(mds)
                source_info["pending_count"] = len(mds)
                source_info["source_path"] = str(source_dir)

        sources[name] = source_info

    return sources


def process_youtube_queue(
    queue_path: Path,
    *,
    limit: int = 0,
    dry_run: bool = False,
    delay_seconds: float = 5.0,
    source_tier: str = "ICT_LEARNING",
) -> Dict:
    """Process YouTube video queue."""
    from core.queue_processor import process_queue

    # Set source tier in environment for pipeline to use
    os.environ["DEXTER_SOURCE_TIER"] = source_tier

    return process_queue(
        queue_path=queue_path,
        limit=limit,
        dry_run=dry_run,
        delay_seconds=delay_seconds,
    )


def process_pdf_source(
    source_dir: Path,
    *,
    limit: int = 0,
    dry_run: bool = False,
    source_tier: str = "LATERAL",
) -> Dict:
    """Process PDF documents from a source directory."""
    from skills.document.pdf_ingester import ingest_pdf

    pdfs = sorted(source_dir.glob("*.pdf"))
    if limit > 0:
        pdfs = pdfs[:limit]

    logger.info("Processing %d PDFs from %s (tier=%s)", len(pdfs), source_dir.name, source_tier)

    results = []
    processed = 0
    failed = 0
    total_chunks = 0

    for pdf in pdfs:
        if dry_run:
            logger.info("[DRY RUN] Would process: %s", pdf.name)
            results.append({"file": pdf.name, "action": "dry_run"})
            continue

        try:
            logger.info("Ingesting: %s", pdf.name)
            ingested = ingest_pdf(pdf)
            chunks = ingested.get("chunks", [])

            # Override source tier
            for chunk in chunks:
                chunk["source_tier"] = source_tier

            total_chunks += len(chunks)
            processed += 1
            results.append({
                "file": pdf.name,
                "status": "DONE",
                "chunks": len(chunks),
                "pages": ingested.get("total_pages", 0),
            })
            logger.info("Ingested %s: %d chunks from %d pages",
                       pdf.name, len(chunks), ingested.get("total_pages", 0))

        except Exception as e:
            logger.exception("Failed processing %s: %s", pdf.name, e)
            failed += 1
            results.append({
                "file": pdf.name,
                "status": "FAILED",
                "error": str(e)[:200],
            })

    return {
        "processed": processed,
        "failed": failed,
        "total_chunks": total_chunks,
        "dry_run": dry_run,
        "results": results,
    }


def process_markdown_source(
    source_dir: Path,
    *,
    limit: int = 0,
    dry_run: bool = False,
    source_tier: str = "OLYA_PRIMARY",
) -> Dict:
    """Process Markdown files from a source directory."""
    from skills.document.md_ingester import ingest_markdown

    mds = sorted(source_dir.glob("*.md"))
    if limit > 0:
        mds = mds[:limit]

    logger.info("Processing %d MDs from %s (tier=%s)", len(mds), source_dir.name, source_tier)

    results = []
    processed = 0
    failed = 0
    total_chunks = 0

    for md in mds:
        if dry_run:
            logger.info("[DRY RUN] Would process: %s", md.name)
            results.append({"file": md.name, "action": "dry_run"})
            continue

        try:
            logger.info("Ingesting: %s", md.name)
            ingested = ingest_markdown(md)
            chunks = ingested.get("chunks", [])

            # Override source tier
            for chunk in chunks:
                chunk["source_tier"] = source_tier

            total_chunks += len(chunks)
            processed += 1
            results.append({
                "file": md.name,
                "status": "DONE",
                "chunks": len(chunks),
                "sections": ingested.get("total_sections", 0),
            })
            logger.info("Ingested %s: %d chunks from %d sections",
                       md.name, len(chunks), ingested.get("total_sections", 0))

        except Exception as e:
            logger.exception("Failed processing %s: %s", md.name, e)
            failed += 1
            results.append({
                "file": md.name,
                "status": "FAILED",
                "error": str(e)[:200],
            })

    return {
        "processed": processed,
        "failed": failed,
        "total_chunks": total_chunks,
        "dry_run": dry_run,
        "results": results,
    }


def run_extraction(
    *,
    source_name: Optional[str] = None,
    source_type: Optional[str] = None,
    queue_path: Optional[Path] = None,
    limit: int = 0,
    dry_run: bool = False,
    delay_seconds: float = 5.0,
) -> Dict:
    """Run extraction for specified sources.

    Args:
        source_name: Specific source to process (e.g., "ict_2022_mentorship")
        source_type: Filter by type ("youtube", "pdf", "markdown")
        queue_path: Override queue file path (for YouTube sources)
        limit: Max items to process per source
        dry_run: If True, log without processing
        delay_seconds: Pause between items (for YouTube)

    Returns:
        Summary dict with results per source.
    """
    sources = discover_sources()
    all_results = {}

    # Filter sources
    if source_name:
        if source_name not in sources:
            raise ValueError(f"Unknown source: {source_name}. Available: {list(sources.keys())}")
        sources = {source_name: sources[source_name]}

    if source_type:
        sources = {k: v for k, v in sources.items() if v["type"] == source_type}

    # Process each source
    for name, config in sources.items():
        if not config["available"]:
            logger.info("Skipping %s: not available", name)
            continue

        if config["pending_count"] == 0:
            logger.info("Skipping %s: no pending items", name)
            continue

        logger.info("=" * 60)
        logger.info("Processing source: %s (%s)", name, config["description"])
        logger.info("Type: %s, Tier: %s, Items: %d pending",
                   config["type"], config["source_tier"], config["pending_count"])
        logger.info("=" * 60)

        if config["type"] == "youtube":
            q_path = queue_path or Path(config.get("queue_path", ""))
            result = process_youtube_queue(
                q_path,
                limit=limit,
                dry_run=dry_run,
                delay_seconds=delay_seconds,
                source_tier=config["source_tier"],
            )
        elif config["type"] == "pdf":
            result = process_pdf_source(
                Path(config["source_path"]),
                limit=limit,
                dry_run=dry_run,
                source_tier=config["source_tier"],
            )
        elif config["type"] == "markdown":
            result = process_markdown_source(
                Path(config["source_path"]),
                limit=limit,
                dry_run=dry_run,
                source_tier=config["source_tier"],
            )
        else:
            logger.warning("Unknown source type: %s", config["type"])
            continue

        all_results[name] = result

    return all_results


def print_status():
    """Print status of all known sources."""
    sources = discover_sources()

    print("\n" + "=" * 70)
    print("DEXTER SOURCE STATUS")
    print("=" * 70)

    for name, config in sources.items():
        status = "" if config["available"] else "[NOT FOUND]"
        print(f"\n{name}: {config['description']} {status}")
        if config["available"]:
            print(f"  Type: {config['type']}, Tier: {config['source_tier']}")
            print(f"  Items: {config['item_count']} total, {config['pending_count']} pending")
        else:
            print(f"  Expected at: {config.get('source_path', config.get('queue_file', '?'))}")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Unified source extraction runner"
    )
    parser.add_argument(
        "--source",
        choices=list(SOURCE_CONFIGS.keys()),
        help="Specific source to process",
    )
    parser.add_argument(
        "--type",
        choices=["youtube", "pdf", "markdown"],
        help="Filter by source type",
    )
    parser.add_argument(
        "--queue",
        type=str,
        help="Override queue file path (for YouTube sources)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max items to process per source (0 = all)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually process (default is dry run)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=5.0,
        help="Seconds between YouTube videos (default: 5)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show source status and exit",
    )
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    dry_run = not args.execute
    queue_path = Path(args.queue) if args.queue else None

    if dry_run:
        print("\nDRY RUN — use --execute to actually process")

    results = run_extraction(
        source_name=args.source,
        source_type=args.type,
        queue_path=queue_path,
        limit=args.limit,
        dry_run=dry_run,
        delay_seconds=args.delay,
    )

    # Summary
    print("\n" + "=" * 70)
    print("EXTRACTION SUMMARY")
    print("=" * 70)

    for name, result in results.items():
        processed = result.get("processed", 0)
        failed = result.get("failed", 0)
        print(f"\n{name}:")
        print(f"  Processed: {processed}")
        print(f"  Failed: {failed}")
        if "total_chunks" in result:
            print(f"  Chunks: {result['total_chunks']}")

    if dry_run:
        print("\n[DRY RUN] No actual processing performed.")

    print("=" * 70)


if __name__ == "__main__":
    main()
