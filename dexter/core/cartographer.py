"""Cartographer: Corpus survey and mapping agent.

Enumerates content from YouTube channels/playlists, categorizes videos,
builds extraction queues. Uses yt-dlp for metadata (no video download).
"""

from __future__ import annotations

import json
import logging
import re
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

# Known playlist IDs and their metadata
KNOWN_PLAYLISTS = {
    "PLVgHx4Z63paah1dHyad1OMJQJdm6iP2Yn": {
        "name": "ICT 2022 Mentorship",
        "category_override": "MENTORSHIP_2022",
        "source_tier": "CANON",
    },
}

# Topic detection patterns for finer categorization
TOPIC_PATTERNS = {
    "KILLZONE": r"killzone|kill zone|asian range|london open|new york open",
    "MARKET_STRUCTURE": r"market structure|structure shift|bos|choch|swing",
    "LIQUIDITY": r"liquidity|sweep|raid|stop hunt|buy side|sell side",
    "PREMIUM_DISCOUNT": r"premium|discount|equilibrium|fair value|fvg|gap",
    "ORDER_BLOCKS": r"order block|breaker|mitigation|ob\b",
    "TIME_PRICE": r"time and price|time & price|time theory|power of 3",
    "OTE": r"optimal trade entry|ote\b|fibonacci",
    "BIAS": r"daily bias|weekly bias|htf bias|higher time",
    "PSYCHOLOGY": r"psychology|journaling|mindset|discipline",
    "RISK": r"risk management|money management|position siz",
}


def extract_playlist_id(url: str) -> Optional[str]:
    """Extract playlist ID from YouTube URL."""
    match = re.search(r"list=([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else None


def survey_channel(channel_url: str) -> tuple[List[Dict], Optional[Dict]]:
    """Enumerate all videos from a YouTube channel/playlist via yt-dlp.

    Returns tuple of (video list, playlist metadata if known).
    """
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    # Check if this is a known playlist
    playlist_id = extract_playlist_id(channel_url)
    playlist_meta = KNOWN_PLAYLISTS.get(playlist_id) if playlist_id else None

    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        "--no-download",
        channel_url,
    ]

    logger.info("Surveying channel: %s", channel_url)
    if playlist_meta:
        logger.info("Recognized playlist: %s", playlist_meta.get("name"))

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
                "source_url": channel_url,
                "playlist_id": playlist_id,
            })
        except json.JSONDecodeError:
            continue

    logger.info("Surveyed %d videos from %s", len(videos), channel_url)
    return videos, playlist_meta


def detect_topics(video: Dict) -> List[str]:
    """Detect topic tags from video title and description."""
    text = f"{video.get('title', '')} {video.get('description', '')}".lower()
    topics = []
    for topic, pattern in TOPIC_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            topics.append(topic)
    return topics


def categorize_video(video: Dict, playlist_meta: Optional[Dict] = None) -> Dict:
    """Categorize video by observable features. No quality judgments."""
    title_lower = (video.get("title") or "").lower()
    duration = video.get("duration") or 0
    views = video.get("view_count") or 0

    # Category detection (observable, not qualitative)
    # Playlist override takes precedence
    if playlist_meta and playlist_meta.get("category_override"):
        category = playlist_meta["category_override"]
    elif "mentorship" in title_lower:
        category = "MENTORSHIP"
    elif "live" in title_lower or "stream" in title_lower:
        category = "LIVE_SESSION"
    elif "q&a" in title_lower or "question" in title_lower:
        category = "QA"
    elif "lecture" in title_lower or "lesson" in title_lower:
        category = "LECTURE"
    elif "review" in title_lower:
        category = "REVIEW"
    else:
        category = "UNKNOWN"

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

    # Detect topic tags
    topics = detect_topics(video)

    # Source tier from playlist metadata
    source_tier = playlist_meta.get("source_tier", "ICT_LEARNING") if playlist_meta else "ICT_LEARNING"

    return {
        **video,
        "category": category,
        "duration_bucket": duration_bucket,
        "view_tier": view_tier,
        "topics": topics,
        "source_tier": source_tier,
        "status": "QUEUED",
    }


def build_corpus_map(
    videos: List[Dict],
    playlist_meta: Optional[Dict] = None,
    output_prefix: Optional[str] = None,
) -> Dict:
    """Build full corpus map with categorization."""
    categorized = [categorize_video(v, playlist_meta) for v in videos]

    categories: Dict[str, int] = {}
    topics_count: Dict[str, int] = {}
    for v in categorized:
        cat = v["category"]
        categories[cat] = categories.get(cat, 0) + 1
        for topic in v.get("topics", []):
            topics_count[topic] = topics_count.get(topic, 0) + 1

    corpus_map = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "total_videos": len(categorized),
        "categories": categories,
        "topics": topics_count,
        "playlist_name": playlist_meta.get("name") if playlist_meta else None,
        "source_tier": playlist_meta.get("source_tier") if playlist_meta else None,
        "videos": categorized,
    }

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = CORPUS_DIR / f"{output_prefix}_corpus_map.yaml" if output_prefix else CORPUS_MAP_FILE
    with open(output_file, "w") as f:
        yaml.dump(corpus_map, f, default_flow_style=False, allow_unicode=True)

    logger.info("Corpus map saved: %s (%d videos)", output_file, len(categorized))
    return corpus_map


def build_extraction_queue(
    corpus_map: Dict,
    strategy: str = "mentorship_first",
    output_prefix: Optional[str] = None,
) -> List[Dict]:
    """Build prioritized extraction queue. Strategy is human-provided."""
    videos = corpus_map.get("videos", [])

    if strategy == "mentorship_first":
        priority_order = ["MENTORSHIP_2022", "MENTORSHIP", "LECTURE", "REVIEW", "LIVE_SESSION", "QA", "UNKNOWN"]

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
        "playlist_name": corpus_map.get("playlist_name"),
        "source_tier": corpus_map.get("source_tier"),
        "total": len(queue),
        "queue": [{**v, "position": i + 1} for i, v in enumerate(queue)],
    }

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = CORPUS_DIR / f"{output_prefix}_extraction_queue.yaml" if output_prefix else EXTRACTION_QUEUE_FILE
    with open(output_file, "w") as f:
        yaml.dump(extraction_queue, f, default_flow_style=False, allow_unicode=True)

    logger.info("Extraction queue saved: %s (strategy=%s, %d videos)",
                output_file, strategy, len(queue))
    return queue


def generate_clusters_report(corpus_map: Dict, output_prefix: Optional[str] = None) -> str:
    """Generate markdown report of content clusters."""
    videos = corpus_map.get("videos", [])
    playlist_name = corpus_map.get("playlist_name") or "ICT Content"
    source_tier = corpus_map.get("source_tier") or "UNKNOWN"

    lines = [
        f"# {playlist_name} Clusters",
        f"\nGenerated: {datetime.now(timezone.utc).isoformat()}",
        f"\nSource Tier: {source_tier}",
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
            topics = v.get("topics", [])
            topic_str = f" [{', '.join(topics)}]" if topics else ""
            lines.append(f"- [{title}]({url}) — {views:,} views, {duration}min{topic_str}")
        lines.append("")

    # Topic summary
    topics_count = corpus_map.get("topics", {})
    if topics_count:
        lines.append("## By Topic\n")
        for topic, count in sorted(topics_count.items(), key=lambda x: -x[1]):
            lines.append(f"- {topic}: {count} videos")
        lines.append("")

    report = "\n".join(lines)

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = CORPUS_DIR / f"{output_prefix}_clusters.md" if output_prefix else CLUSTERS_FILE
    with open(output_file, "w") as f:
        f.write(report)

    logger.info("Clusters report saved: %s", output_file)
    return report


def run_cartographer(
    channel_url: str,
    strategy: str = "mentorship_first",
    output_prefix: Optional[str] = None,
) -> Dict:
    """Full Cartographer pipeline: survey → categorize → map → queue → report.

    Args:
        channel_url: YouTube channel or playlist URL
        strategy: Queue prioritization strategy
        output_prefix: Optional prefix for output files (e.g., "ict_2022" -> "ict_2022_corpus_map.yaml")
    """
    logger.info("=== CARTOGRAPHER: %s ===", channel_url)

    videos, playlist_meta = survey_channel(channel_url)

    # Auto-generate prefix from playlist name if not provided
    if not output_prefix and playlist_meta:
        output_prefix = playlist_meta.get("name", "").lower().replace(" ", "_").replace("-", "_")

    corpus_map = build_corpus_map(videos, playlist_meta, output_prefix)
    queue = build_extraction_queue(corpus_map, strategy, output_prefix)
    report = generate_clusters_report(corpus_map, output_prefix)

    # Determine output file paths
    if output_prefix:
        corpus_file = CORPUS_DIR / f"{output_prefix}_corpus_map.yaml"
        queue_file = CORPUS_DIR / f"{output_prefix}_extraction_queue.yaml"
        clusters_file = CORPUS_DIR / f"{output_prefix}_clusters.md"
    else:
        corpus_file = CORPUS_MAP_FILE
        queue_file = EXTRACTION_QUEUE_FILE
        clusters_file = CLUSTERS_FILE

    result = {
        "videos_found": len(videos),
        "corpus_map": str(corpus_file),
        "extraction_queue": str(queue_file),
        "clusters_report": str(clusters_file),
        "categories": corpus_map.get("categories", {}),
        "topics": corpus_map.get("topics", {}),
        "playlist_name": playlist_meta.get("name") if playlist_meta else None,
        "source_tier": playlist_meta.get("source_tier") if playlist_meta else None,
        "top_5_queue": [q.get("title", "?") for q in queue[:5]],
    }

    logger.info("=== CARTOGRAPHER COMPLETE: %d videos mapped ===", len(videos))
    return result
