#!/usr/bin/env python3
"""
Stage 3: ICT 2022 Mentorship Taxonomy Extraction

Fetches transcripts from Supadata API and extracts taxonomy concepts.
Uses the same drawer-by-drawer approach as Blessed and Olya extraction.

Usage:
    python scripts/run_ict2022_taxonomy.py
    python scripts/run_ict2022_taxonomy.py --test        # Single video test
    python scripts/run_ict2022_taxonomy.py --limit 5    # Process 5 videos
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Load environment from .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value
                if key == "OPENROUTER_KEY":
                    os.environ["OPENROUTER_API_KEY"] = value

# Disable mock mode for real transcripts
os.environ["DEXTER_MOCK_MODE"] = "false"

import httpx
import yaml

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from skills.transcript.supadata import fetch_transcript

# Paths
TAXONOMY_PATH = PROJECT_ROOT / "data" / "taxonomy" / "reference_taxonomy.yaml"
COVERAGE_PATH = PROJECT_ROOT / "data" / "taxonomy" / "coverage_matrix.yaml"
QUEUE_PATH = PROJECT_ROOT / "corpus" / "ict_2022_mentorship_extraction_queue.yaml"
OUTPUT_PATH = PROJECT_ROOT / "data" / "taxonomy" / "ict2022_results"

# Ensure output dir exists
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

# OpenRouter config
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_KEY")
THEORIST_MODEL = "deepseek/deepseek-chat"


def load_taxonomy() -> dict:
    """Load reference taxonomy."""
    with open(TAXONOMY_PATH) as f:
        return yaml.safe_load(f)


def load_coverage_matrix() -> dict:
    """Load coverage matrix."""
    with open(COVERAGE_PATH) as f:
        return yaml.safe_load(f)


def save_coverage_matrix(matrix: dict):
    """Save coverage matrix."""
    matrix["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(COVERAGE_PATH, "w") as f:
        yaml.dump(matrix, f, default_flow_style=False, allow_unicode=True, width=120)


def load_queue() -> list:
    """Load ICT 2022 extraction queue."""
    with open(QUEUE_PATH) as f:
        data = yaml.safe_load(f)
    return data.get("queue", [])


def get_transcript_content(video: dict) -> str:
    """Fetch and format transcript for a video."""
    url = video.get("url")
    if not url:
        return ""

    print(f"  Fetching transcript from Supadata...")
    try:
        transcript = fetch_transcript(url)
        segments = transcript.get("segments", [])

        # Combine all segments with timestamps
        content_parts = []
        for seg in segments:
            start = seg.get("start", 0)
            text = seg.get("text", "").strip()
            if text:
                # Format: [MM:SS] text
                mins = int(start // 60)
                secs = int(start % 60)
                content_parts.append(f"[{mins:02d}:{secs:02d}] {text}")

        content = "\n".join(content_parts)
        print(f"  Got {len(content)} chars ({len(segments)} segments)")
        return content
    except Exception as e:
        print(f"  ERROR fetching transcript: {e}")
        return ""


def build_drawer_prompt(drawer: dict, content: str, video_title: str) -> str:
    """Build taxonomy extraction prompt for a specific drawer."""
    concepts = drawer.get("concepts", [])
    drawer_name = drawer.get("name", "Unknown")

    concept_list = []
    for c in concepts:
        con_id = c.get("id", "")
        name = c.get("name", "")
        defn = c.get("definition", {})
        if_clause = defn.get("if", "")
        then_clause = defn.get("then", "")
        terms = [str(t) for t in defn.get("ict_terminology", [])[:5]]

        concept_list.append(f"""
Concept: {con_id} - {name}
IF: {if_clause}
THEN: {then_clause}
ICT Terms: {', '.join(terms) if terms else 'N/A'}
""")

    return f"""You are a taxonomy extraction specialist analyzing ICT 2022 Mentorship content.

VIDEO: {video_title}

TRANSCRIPT CONTENT:
{content[:15000]}

DRAWER: {drawer_name}

CONCEPTS TO CHECK:
{''.join(concept_list)}

TASK: For each concept, determine if ICT explicitly teaches this concept in this video.

For each concept, respond with ONE of:
- FOUND: ICT explicitly teaches this concept with clear IF-THEN logic
- PARTIAL: ICT mentions related terms but doesn't give complete IF-THEN rule
- ABSENT: Concept not taught in this video

IMPORTANT:
- Only mark FOUND if ICT gives explicit trading rules matching the IF-THEN structure
- Look for timestamps like [MM:SS] to cite exact video locations
- Be conservative - ABSENT is correct if concept isn't clearly taught

Respond in JSON format:
{{
  "drawer": "{drawer_name}",
  "results": [
    {{"concept_id": "CON-XX-YY", "status": "FOUND|PARTIAL|ABSENT", "evidence": "quote or null", "timestamp": "MM:SS or null"}}
  ]
}}
"""


def call_theorist(prompt: str) -> dict:
    """Call DeepSeek Theorist via OpenRouter."""
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set")

    response = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": THEORIST_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 4000,
        },
        timeout=120.0,
    )
    response.raise_for_status()

    data = response.json()
    content = data["choices"][0]["message"]["content"]

    # Parse JSON from response
    try:
        # Handle markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content.strip())
    except json.JSONDecodeError:
        return {"error": "Failed to parse response", "raw": content[:500]}


def get_drawers_from_taxonomy(taxonomy: dict) -> list:
    """Extract drawer definitions from taxonomy."""
    drawer_keys = [
        ("drawer_1_htf_bias", "1", "HTF Bias & Liquidity"),
        ("drawer_2_time_session", "2", "Time & Session"),
        ("drawer_3_structure", "3", "Structure & Displacement"),
        ("drawer_4_execution", "4", "Execution"),
        ("drawer_5_protection", "5", "Protection & Risk"),
        ("olya_extensions", "olya", "Olya Extensions"),
    ]

    drawers = []
    for key, drawer_id, name in drawer_keys:
        if key in taxonomy:
            drawer_data = taxonomy[key]
            concepts = drawer_data.get("concepts", [])
            drawers.append({
                "id": drawer_id,
                "name": name,
                "concepts": concepts
            })
    return drawers


def process_video(video: dict, taxonomy: dict) -> dict:
    """Process a single video through taxonomy extraction."""
    title = video.get("title", "Unknown")
    video_id = video.get("id", "unknown")

    print(f"\nProcessing: {title}")

    # Get transcript
    content = get_transcript_content(video)
    if not content or len(content) < 100:
        print(f"  WARNING: Insufficient transcript content ({len(content)} chars)")
        return {"video_id": video_id, "title": title, "error": "insufficient_content", "drawers": {}}

    results = {"video_id": video_id, "title": title, "drawers": {}, "content_length": len(content)}

    # Process each drawer
    drawers = get_drawers_from_taxonomy(taxonomy)
    for drawer in drawers:
        drawer_id = drawer.get("id", "unknown")
        drawer_name = drawer.get("name", "Unknown")

        print(f"  Drawer {drawer_id}...", end=" ", flush=True)

        prompt = build_drawer_prompt(drawer, content, title)

        try:
            response = call_theorist(prompt)

            if "error" in response:
                print(f"ERROR: {response.get('error', 'unknown')}")
                results["drawers"][drawer_id] = {"error": response.get("error")}
                continue

            drawer_results = response.get("results", [])

            # Count statuses
            found = sum(1 for r in drawer_results if r.get("status") == "FOUND")
            partial = sum(1 for r in drawer_results if r.get("status") == "PARTIAL")
            absent = sum(1 for r in drawer_results if r.get("status") == "ABSENT")

            print(f"FOUND:{found} PARTIAL:{partial} ABSENT:{absent}")

            results["drawers"][drawer_id] = {
                "name": drawer_name,
                "results": drawer_results,
                "summary": {"found": found, "partial": partial, "absent": absent}
            }

            # Rate limit between drawers
            time.sleep(1)

        except Exception as e:
            print(f"ERROR: {e}")
            results["drawers"][drawer_id] = {"error": str(e)}

    return results


def update_coverage_from_results(results: dict, matrix: dict):
    """Update coverage matrix from extraction results."""
    video_title = results.get("title", "Unknown")

    for drawer_id, drawer_data in results.get("drawers", {}).items():
        if "error" in drawer_data:
            continue

        for concept_result in drawer_data.get("results", []):
            concept_id = concept_result.get("concept_id")
            status = concept_result.get("status", "").upper()
            evidence = concept_result.get("evidence")
            timestamp = concept_result.get("timestamp")

            if not concept_id or concept_id not in matrix.get("coverage", {}):
                continue

            # Map status
            if status == "FOUND":
                new_status = "FOUND"
            elif status == "PARTIAL":
                new_status = "PARTIAL"
            else:
                new_status = "ABSENT"

            # Get current ICT_2022 entry
            concept_coverage = matrix["coverage"][concept_id]
            ict_entry = concept_coverage.get("sources", {}).get("ICT_2022", {}) or {}
            current_status = ict_entry.get("status", "PENDING")

            # Only upgrade status (PENDING -> ABSENT -> PARTIAL -> FOUND)
            status_rank = {"PENDING": 0, "ABSENT": 1, "PARTIAL": 2, "FOUND": 3}
            if status_rank.get(new_status, 0) > status_rank.get(current_status, 0):
                # Create signature ID
                evidence = ict_entry.get("evidence") or {}
                existing_sigs = evidence.get("signature_ids") or []
                sig_count = len(existing_sigs) + 1
                sig_id = f"ICT-{concept_id}-{sig_count}"

                if new_status == "FOUND" or new_status == "PARTIAL":
                    existing_docs = evidence.get("documents") or []
                    concept_coverage["sources"]["ICT_2022"] = {
                        "status": new_status,
                        "evidence": {
                            "signature_ids": existing_sigs + [sig_id],
                            "documents": list(set(existing_docs + [video_title])),
                            "timestamps": [timestamp] if timestamp else None,
                        },
                        "last_checked": datetime.now(timezone.utc).isoformat(),
                    }
                else:
                    concept_coverage["sources"]["ICT_2022"] = {
                        "status": new_status,
                        "evidence": None,
                        "last_checked": datetime.now(timezone.utc).isoformat(),
                    }


def main():
    parser = argparse.ArgumentParser(description="ICT 2022 Taxonomy Extraction")
    parser.add_argument("--test", action="store_true", help="Process single video for testing")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of videos to process")
    args = parser.parse_args()

    # Load taxonomy and queue
    taxonomy = load_taxonomy()
    matrix = load_coverage_matrix()
    queue = load_queue()

    print(f"Loaded taxonomy: {TAXONOMY_PATH}")
    print(f"Found {len(queue)} ICT 2022 videos")

    # Reset ICT_2022 coverage to PENDING if doing full run
    if not args.test:
        print("Reset ICT 2022 coverage to PENDING")
        for concept_id, concept_data in matrix.get("coverage", {}).items():
            if "ICT_2022" in concept_data.get("sources", {}):
                concept_data["sources"]["ICT_2022"] = {
                    "status": "PENDING",
                    "evidence": None,
                    "last_checked": None,
                }

    # Determine videos to process
    if args.test:
        # Process first video with DONE status
        videos = [v for v in queue if v.get("status") == "DONE"][:1]
        print(f"TEST MODE: Processing {videos[0].get('title', 'Unknown') if videos else 'none'}")
    elif args.limit > 0:
        videos = [v for v in queue if v.get("status") == "DONE"][:args.limit]
    else:
        videos = [v for v in queue if v.get("status") == "DONE"]

    # Track results
    all_results = []
    totals = {"found": 0, "partial": 0, "absent": 0}

    for video in videos:
        results = process_video(video, taxonomy)
        all_results.append(results)

        # Update totals
        for drawer_data in results.get("drawers", {}).values():
            if "summary" in drawer_data:
                totals["found"] += drawer_data["summary"].get("found", 0)
                totals["partial"] += drawer_data["summary"].get("partial", 0)
                totals["absent"] += drawer_data["summary"].get("absent", 0)

        # Update coverage matrix
        update_coverage_from_results(results, matrix)

        # Rate limit between videos
        time.sleep(2)

    # Save results
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output_file = OUTPUT_PATH / f"ict2022_taxonomy_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)

    # Save updated matrix
    save_coverage_matrix(matrix)

    # Summary
    print("\n" + "=" * 60)
    print("STAGE 3 ICT 2022 TAXONOMY EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"Videos processed: {len(videos)}")
    print(f"FOUND: {totals['found']}")
    print(f"PARTIAL: {totals['partial']}")
    print(f"ABSENT: {totals['absent']}")
    print(f"Results: {output_file}")

    # Regenerate coverage report
    print("\nGenerating coverage report...")
    os.system(f"python3 {PROJECT_ROOT}/scripts/generate_coverage_report.py")


if __name__ == "__main__":
    main()
