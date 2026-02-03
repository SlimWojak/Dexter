"""Cartographer: Corpus survey and mapping agent.

Enumerates content from YouTube channels/playlists, categorizes videos,
builds extraction queues. Uses yt-dlp for metadata (no video download).
"""

from __future__ import annotations

import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger("dexter.cartographer")

CORPUS_DIR = Path(__file__).resolve().parent.parent / "corpus"
CORPUS_MAP_FILE = CORPUS_DIR / "corpus_map.yaml"
EXTRACTION_QUEUE_FILE = CORPUS_DIR / "extraction_queue.yaml"
CLUSTERS_FILE = CORPUS_DIR / "content_clusters.md"


def survey_channel(channel_url: str) -> List[Dict]:
    """Enumerate all videos from a YouTube channel/playlist via yt-dlp.

    Returns list of video metadata dicts (no download).
    """
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        "--no-download",
        channel_url,
    ]

    logger.info("Surveying channel: %s", channel_url)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        logger.error("yt-dlp error: %s", result.stderr[:500])
        raise RuntimeError(f"yt-dlp failed: {result.stderr[:200]}")

    videos = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            videos.append({
                "id": data.get("id"),
                "title": data.get("title", ""),
                "duration": data.get("duration"),
                "view_count": data.get("view_count", 0),
                "upload_date": data.get("upload_date", ""),
                "description": (data.get("description") or "")[:500],
                "url": f"https://www.youtube.com/watch?v={data.get('id')}",
            })
        except json.JSONDecodeError:
            continue

    logger.info("Surveyed %d videos from %s", len(videos), channel_url)
    return videos


def categorize_video(video: Dict) -> Dict:
    """Categorize video by observable features. No quality judgments."""
    title_lower = (video.get("title") or "").lower()
    duration = video.get("duration") or 0
    views = video.get("view_count") or 0

    # Category detection (observable, not qualitative)
    category = "UNKNOWN"
    if "mentorship" in title_lower:
        category = "MENTORSHIP"
    elif "live" in title_lower or "stream" in title_lower:
        category = "LIVE_SESSION"
    elif "q&a" in title_lower or "question" in title_lower:
        category = "QA"
    elif "lecture" in title_lower or "lesson" in title_lower:
        category = "LECTURE"
    elif "review" in title_lower:
        category = "REVIEW"

    # Duration bucket
    if duration < 600:
        duration_bucket = "SHORT"
    elif duration < 3600:
        duration_bucket = "MEDIUM"
    else:
        duration_bucket = "LONG"

    # View tier
    if views > 1_000_000:
        view_tier = "VIRAL"
    elif views > 100_000:
        view_tier = "HIGH"
    elif views > 10_000:
        view_tier = "MEDIUM"
    else:
        view_tier = "LOW"

    return {
        **video,
        "category": category,
        "duration_bucket": duration_bucket,
        "view_tier": view_tier,
        "status": "QUEUED",
    }


def build_corpus_map(videos: List[Dict]) -> Dict:
    """Build full corpus map with categorization."""
    categorized = [categorize_video(v) for v in videos]

    categories: Dict[str, int] = {}
    for v in categorized:
        cat = v["category"]
        categories[cat] = categories.get(cat, 0) + 1

    corpus_map = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "total_videos": len(categorized),
        "categories": categories,
        "videos": categorized,
    }

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    with open(CORPUS_MAP_FILE, "w") as f:
        yaml.dump(corpus_map, f, default_flow_style=False, allow_unicode=True)

    logger.info("Corpus map saved: %s (%d videos)", CORPUS_MAP_FILE, len(categorized))
    return corpus_map


def build_extraction_queue(
    corpus_map: Dict,
    strategy: str = "mentorship_first",
) -> List[Dict]:
    """Build prioritized extraction queue. Strategy is human-provided."""
    videos = corpus_map.get("videos", [])

    if strategy == "mentorship_first":
        priority_order = ["MENTORSHIP", "LECTURE", "REVIEW", "LIVE_SESSION", "QA", "UNKNOWN"]

        def sort_key(v: Dict) -> tuple:
            cat = v.get("category", "UNKNOWN")
            cat_priority = priority_order.index(cat) if cat in priority_order else 99
            view_priority = -(v.get("view_count") or 0)
            return (cat_priority, view_priority)

        queue = sorted(videos, key=sort_key)

    elif strategy == "chronological":
        queue = sorted(videos, key=lambda v: v.get("upload_date", ""))

    elif strategy == "views":
        queue = sorted(videos, key=lambda v: -(v.get("view_count") or 0))

    else:
        queue = list(videos)

    extraction_queue = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "strategy": strategy,
        "total": len(queue),
        "queue": [{**v, "position": i + 1} for i, v in enumerate(queue)],
    }

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    with open(EXTRACTION_QUEUE_FILE, "w") as f:
        yaml.dump(extraction_queue, f, default_flow_style=False, allow_unicode=True)

    logger.info("Extraction queue saved: %s (strategy=%s, %d videos)",
                EXTRACTION_QUEUE_FILE, strategy, len(queue))
    return queue


def generate_clusters_report(corpus_map: Dict) -> str:
    """Generate markdown report of content clusters."""
    videos = corpus_map.get("videos", [])

    lines = [
        "# ICT Content Clusters",
        f"\nGenerated: {datetime.now(timezone.utc).isoformat()}",
        f"\nTotal Videos: {len(videos)}",
        "\n## By Category\n",
    ]

    by_category: Dict[str, List[Dict]] = {}
    for v in videos:
        cat = v.get("category", "UNKNOWN")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(v)

    for cat, vids in sorted(by_category.items()):
        lines.append(f"### {cat} ({len(vids)} videos)\n")
        top5 = sorted(vids, key=lambda x: -(x.get("view_count") or 0))[:5]
        for v in top5:
            views = v.get("view_count") or 0
            duration = (v.get("duration") or 0) // 60
            title = (v.get("title") or "?")[:60]
            url = v.get("url", "")
            lines.append(f"- [{title}]({url}) — {views:,} views, {duration}min")
        lines.append("")

    report = "\n".join(lines)

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    with open(CLUSTERS_FILE, "w") as f:
        f.write(report)

    logger.info("Clusters report saved: %s", CLUSTERS_FILE)
    return report


def run_cartographer(
    channel_url: str,
    strategy: str = "mentorship_first",
) -> Dict:
    """Full Cartographer pipeline: survey → categorize → map → queue → report."""
    logger.info("=== CARTOGRAPHER: %s ===", channel_url)

    videos = survey_channel(channel_url)
    corpus_map = build_corpus_map(videos)
    queue = build_extraction_queue(corpus_map, strategy)
    report = generate_clusters_report(corpus_map)

    result = {
        "videos_found": len(videos),
        "corpus_map": str(CORPUS_MAP_FILE),
        "extraction_queue": str(EXTRACTION_QUEUE_FILE),
        "clusters_report": str(CLUSTERS_FILE),
        "categories": corpus_map.get("categories", {}),
        "top_5_queue": [q.get("title", "?") for q in queue[:5]],
    }

    logger.info("=== CARTOGRAPHER COMPLETE: %d videos mapped ===", len(videos))
    return result
