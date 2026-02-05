"""Chronicler role — recursive summarization to THEORY.md.

Compresses bead chain, clusters signatures by drawer + semantic similarity,
flags redundant signatures, archives processed beads. Different model family
(google) for fresh perspective on summaries.

Phase P1 deliverable — prevents memory bloat.
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("dexter.chronicler")

# Paths
MEMORY_DIR = Path(__file__).resolve().parent.parent / "memory"
BEADS_DIR = MEMORY_DIR / "beads"
ARCHIVE_DIR = MEMORY_DIR / "archive"
THEORY_PATH = MEMORY_DIR / "THEORY.md"
BUNDLES_DIR = Path(__file__).resolve().parent.parent / "bundles"

# Thresholds from chronicler.yaml
DEFAULT_MAX_BEADS = 25
DEFAULT_SIMILARITY_THRESHOLD = 0.85

# 5-Drawer system
DRAWER_NAMES = {
    1: "HTF_BIAS",
    2: "MARKET_STRUCTURE",
    3: "PREMIUM_DISCOUNT",
    4: "ENTRY_MODEL",
    5: "CONFIRMATION",
}


# ---------------------------------------------------------------------------
# Similarity (stdlib TF-IDF cosine — same approach as injection_guard.py)
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase words."""
    return re.findall(r"\b\w+\b", text.lower())


def _cosine_similarity(a: Counter, b: Counter) -> float:
    """Cosine similarity between two term-frequency counters."""
    common = set(a) & set(b)
    if not common:
        return 0.0
    dot = sum(a[k] * b[k] for k in common)
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def compute_similarity(text_a: str, text_b: str) -> float:
    """Compute cosine similarity between two text strings."""
    tokens_a = Counter(_tokenize(text_a))
    tokens_b = Counter(_tokenize(text_b))
    return _cosine_similarity(tokens_a, tokens_b)


# ---------------------------------------------------------------------------
# CLAIM_BEAD loading
# ---------------------------------------------------------------------------

def load_all_claims() -> List[Dict]:
    """Load all CLAIM_BEADs from bundles directory."""
    claims = []
    if not BUNDLES_DIR.exists():
        return claims

    for path in sorted(BUNDLES_DIR.glob("*_claims.jsonl")):
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        claim = json.loads(line)
                        # Add source file for provenance
                        claim["_source_file"] = path.name
                        claims.append(claim)
        except Exception as e:
            logger.warning("Failed to load claims from %s: %s", path, e)

    return claims


def load_negative_beads() -> List[Dict]:
    """Load all NEGATIVE beads from session files."""
    negatives = []
    if not BEADS_DIR.exists():
        return negatives

    for path in sorted(BEADS_DIR.glob("session_*.jsonl")):
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        bead = json.loads(line)
                        if bead.get("type") == "NEGATIVE":
                            bead["_source_file"] = path.name
                            negatives.append(bead)
        except Exception as e:
            logger.warning("Failed to load beads from %s: %s", path, e)

    return negatives


# ---------------------------------------------------------------------------
# Clustering
# ---------------------------------------------------------------------------

def cluster_by_drawer(claims: List[Dict]) -> Dict[int, List[Dict]]:
    """Group claims by drawer number (1-5)."""
    clusters: Dict[int, List[Dict]] = {i: [] for i in range(1, 6)}

    for claim in claims:
        sig = claim.get("signature", {})
        drawer = sig.get("drawer", 0)
        if drawer in clusters:
            clusters[drawer].append(claim)
        else:
            # Unknown drawer — log but don't lose
            logger.warning("Claim %s has unknown drawer %s", sig.get("id"), drawer)
            clusters[1].append(claim)  # Default to HTF_BIAS

    return clusters


def detect_redundant_pairs(
    claims: List[Dict],
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> List[Tuple[Dict, Dict, float]]:
    """Find pairs of claims with similarity above threshold.

    Returns list of (claim_a, claim_b, similarity) tuples.
    """
    redundant = []

    for i, claim_a in enumerate(claims):
        sig_a = claim_a.get("signature", {})
        text_a = f"{sig_a.get('condition', '')} {sig_a.get('action', '')}"

        for claim_b in claims[i + 1:]:
            sig_b = claim_b.get("signature", {})
            text_b = f"{sig_b.get('condition', '')} {sig_b.get('action', '')}"

            sim = compute_similarity(text_a, text_b)
            if sim >= threshold:
                redundant.append((claim_a, claim_b, sim))

    return redundant


def cluster_within_drawer(
    claims: List[Dict],
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> List[List[Dict]]:
    """Cluster claims within a drawer by semantic similarity.

    Uses simple greedy clustering: each claim joins the first cluster
    where it has similarity >= threshold with any member.
    """
    if not claims:
        return []

    clusters: List[List[Dict]] = []

    for claim in claims:
        sig = claim.get("signature", {})
        text = f"{sig.get('condition', '')} {sig.get('action', '')}"

        # Find best matching cluster
        best_cluster_idx = -1
        best_sim = 0.0

        for idx, cluster in enumerate(clusters):
            for existing in cluster:
                existing_sig = existing.get("signature", {})
                existing_text = f"{existing_sig.get('condition', '')} {existing_sig.get('action', '')}"
                sim = compute_similarity(text, existing_text)
                if sim > best_sim:
                    best_sim = sim
                    best_cluster_idx = idx

        # Join cluster or create new one
        if best_sim >= threshold and best_cluster_idx >= 0:
            clusters[best_cluster_idx].append(claim)
        else:
            clusters.append([claim])

    return clusters


# ---------------------------------------------------------------------------
# LLM Summarization
# ---------------------------------------------------------------------------

def _get_cluster_topic(claims: List[Dict]) -> str:
    """Generate a topic label for a cluster based on common patterns."""
    # Extract key terms from conditions
    all_conditions = []
    for claim in claims:
        sig = claim.get("signature", {})
        cond = sig.get("condition", "")
        all_conditions.append(cond)

    # Find common terms (simple heuristic)
    all_tokens = []
    for cond in all_conditions:
        all_tokens.extend(_tokenize(cond))

    token_counts = Counter(all_tokens)
    # Remove common stopwords
    stopwords = {"if", "the", "a", "an", "and", "or", "to", "of", "in", "at", "is", "then"}
    for sw in stopwords:
        token_counts.pop(sw, None)

    # Top 3 terms as topic
    top_terms = [term for term, _ in token_counts.most_common(3)]
    if top_terms:
        return "_".join(top_terms).upper()
    return "GENERAL"


def summarize_cluster_with_llm(
    claims: List[Dict],
    drawer_name: str,
) -> Dict:
    """Use LLM to generate cluster summary.

    Returns:
        {
            "topic": str,
            "summary": str,
            "entry_ids": List[str],
            "entry_count": int,
            "key_patterns": List[str],
        }
    """
    # Check if LLM mode is enabled
    llm_mode = os.environ.get("DEXTER_LLM_MODE", "true").lower() == "true"

    entry_ids = [c.get("signature", {}).get("id", "?") for c in claims]
    topic = _get_cluster_topic(claims)

    if not llm_mode or len(claims) == 0:
        # Mock mode or empty — return heuristic summary
        return {
            "topic": topic,
            "summary": f"Cluster of {len(claims)} signatures in {drawer_name}",
            "entry_ids": entry_ids,
            "entry_count": len(claims),
            "key_patterns": [topic],
        }

    # Build prompt for LLM
    conditions = []
    actions = []
    for claim in claims[:10]:  # Limit to first 10 for context
        sig = claim.get("signature", {})
        conditions.append(sig.get("condition", ""))
        actions.append(sig.get("action", ""))

    system_prompt = """You are a trading knowledge summarizer. Your task is to:
1. Identify the common pattern across these IF-THEN trading signatures
2. Summarize in 1-2 sentences what the cluster represents
3. List 2-3 key patterns/concepts

RULES:
- Use raw ICT terminology (do not translate to other frameworks)
- Never interpret — only summarize what is explicitly stated
- Never add commentary or recommendations
- Preserve source provenance (reference signature IDs when relevant)

Output JSON only:
{"summary": "...", "key_patterns": ["...", "..."]}"""

    user_content = f"""Drawer: {drawer_name}
Signatures ({len(claims)} total, showing first {min(len(claims), 10)}):

CONDITIONS:
{chr(10).join(f'- {c}' for c in conditions)}

ACTIONS:
{chr(10).join(f'- {a}' for a in actions)}"""

    try:
        from core.llm_client import call_llm_for_role

        result = call_llm_for_role(
            role="chronicler",
            system_prompt=system_prompt,
            user_content=user_content,
        )

        content = result.get("content", "{}")
        # Parse JSON from response
        # Handle markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        parsed = json.loads(content.strip())

        return {
            "topic": topic,
            "summary": parsed.get("summary", f"Cluster of {len(claims)} signatures"),
            "entry_ids": entry_ids,
            "entry_count": len(claims),
            "key_patterns": parsed.get("key_patterns", [topic]),
        }

    except Exception as e:
        logger.warning("LLM summarization failed: %s", e)
        return {
            "topic": topic,
            "summary": f"Cluster of {len(claims)} signatures in {drawer_name}",
            "entry_ids": entry_ids,
            "entry_count": len(claims),
            "key_patterns": [topic],
        }


# ---------------------------------------------------------------------------
# THEORY.md Generation
# ---------------------------------------------------------------------------

def generate_theory_md(
    drawer_clusters: Dict[int, List[List[Dict]]],
    redundant_pairs: List[Tuple[Dict, Dict, float]],
    negatives: List[Dict],
) -> str:
    """Generate THEORY.md content from clusters and negatives."""
    lines = [
        "# THEORY.md — Recursive Summary (Standard Meter)",
        "# Populated by Chronicler; do not edit by hand.",
        "# v0.2: Clustering pattern enabled — redundancy detection active",
        "",
        "---",
        "",
        "## INDEX",
        "",
    ]

    # Build index
    total_entries = 0
    total_clusters = 0

    for drawer_num in range(1, 6):
        drawer_name = DRAWER_NAMES[drawer_num]
        clusters = drawer_clusters.get(drawer_num, [])
        if clusters:
            for cluster in clusters:
                entry_ids = [c.get("signature", {}).get("id", "?") for c in cluster]
                if entry_ids:
                    total_clusters += 1
                    total_entries += len(entry_ids)
                    topic = _get_cluster_topic(cluster)
                    lines.append(f"- **{drawer_name}** | CLUSTER: {topic} | Entries: {', '.join(entry_ids[:5])}{'...' if len(entry_ids) > 5 else ''}")

    if total_entries == 0:
        lines.append("*No entries yet. Awaiting Theorist output.*")

    lines.extend([
        "",
        "---",
        "",
        "## CLUSTERS",
        "",
    ])

    # Drawer sections
    for drawer_num in range(1, 6):
        drawer_name = DRAWER_NAMES[drawer_num]
        clusters = drawer_clusters.get(drawer_num, [])

        lines.append(f"### Drawer {drawer_num}: {drawer_name}")
        lines.append("")

        if not clusters:
            lines.append("*No signatures yet.*")
            lines.append("")
            continue

        for cluster in clusters:
            if not cluster:
                continue

            summary = summarize_cluster_with_llm(cluster, drawer_name)
            entry_ids = summary["entry_ids"]

            lines.append(f"#### CLUSTER: {summary['topic']} | Entries: {len(entry_ids)}")
            lines.append("")
            lines.append(f"**Summary:** {summary['summary']}")
            lines.append("")
            lines.append(f"**Entry IDs:** {', '.join(entry_ids[:10])}{'...' if len(entry_ids) > 10 else ''}")
            lines.append("")
            if summary["key_patterns"]:
                lines.append(f"**Key Patterns:** {', '.join(summary['key_patterns'])}")
                lines.append("")

        lines.append("")

    # Redundancy section
    if redundant_pairs:
        lines.extend([
            "---",
            "",
            "## REDUNDANT SIGNATURES (Flagged)",
            "",
            "<!-- Pairs with cosine similarity > 0.85 -->",
            "",
        ])

        for claim_a, claim_b, sim in redundant_pairs[:20]:  # Limit display
            sig_a = claim_a.get("signature", {})
            sig_b = claim_b.get("signature", {})
            lines.append(f"- **{sig_a.get('id', '?')}** ↔ **{sig_b.get('id', '?')}** (sim: {sim:.2f})")
            lines.append(f"  - REDUNDANT — See {sig_a.get('id', '?')}")

        lines.append("")

    # Negative section
    lines.extend([
        "---",
        "",
        "## NEGATIVE PATTERNS (Failure Mining)",
        "",
        "<!-- Recent rejected signatures to avoid re-discovery -->",
        "<!-- Format: N-XXX | Reason | Source Bundle -->",
        "",
    ])

    if negatives:
        for neg in negatives[-20:]:  # Show last 20
            neg_id = neg.get("id", "?")
            reason = neg.get("reason", "Unknown")
            source = neg.get("source_bundle", neg.get("source_signature", ""))
            lines.append(f"- **{neg_id}** | {reason} | Source: {source}")
        lines.append("")
    else:
        lines.append("*No negative patterns yet. Awaiting Auditor rejections.*")
        lines.append("")

    # Footer
    timestamp = datetime.now(timezone.utc).isoformat()
    lines.extend([
        "---",
        "",
        f"*Last updated: {timestamp}*",
        f"*Entries: {total_entries} | Clusters: {total_clusters} | Negatives: {len(negatives)}*",
        "",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Archive
# ---------------------------------------------------------------------------

def archive_session_beads(session_file: Path) -> Optional[Path]:
    """Move a session bead file to archive.

    Returns the archive path if successful, None otherwise.
    """
    if not session_file.exists():
        return None

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    # Generate archive filename with date range
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    archive_name = f"archive_{session_file.stem}_{timestamp}.jsonl"
    archive_path = ARCHIVE_DIR / archive_name

    try:
        shutil.move(str(session_file), str(archive_path))
        logger.info("Archived %s to %s", session_file.name, archive_path.name)
        return archive_path
    except Exception as e:
        logger.error("Failed to archive %s: %s", session_file.name, e)
        return None


def archive_old_sessions(keep_days: int = 1) -> List[Path]:
    """Archive session files older than keep_days.

    Returns list of archived paths.
    """
    archived = []
    if not BEADS_DIR.exists():
        return archived

    today = datetime.now(timezone.utc).date()

    for path in sorted(BEADS_DIR.glob("session_*.jsonl")):
        # Extract date from filename
        try:
            date_str = path.stem.replace("session_", "")
            file_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            days_old = (today - file_date).days
            if days_old >= keep_days:
                result = archive_session_beads(path)
                if result:
                    archived.append(result)
        except ValueError:
            continue

    return archived


# ---------------------------------------------------------------------------
# Main Compression Entry Point
# ---------------------------------------------------------------------------

def compress_beads(
    max_beads: int = DEFAULT_MAX_BEADS,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    archive_days: int = 1,
) -> Dict:
    """Main entry point for bead compression.

    Triggers when bead count exceeds threshold. Performs:
    1. Load all CLAIM_BEADs from bundles
    2. Cluster by drawer + semantic similarity
    3. Detect redundant pairs
    4. Generate THEORY.md
    5. Archive old session beads

    Returns:
        {
            "compressed": bool,
            "total_claims": int,
            "clusters_by_drawer": Dict[int, int],
            "redundant_pairs": int,
            "archived_files": List[str],
            "theory_path": str,
        }
    """
    logger.info("Starting bead compression (threshold=%d)", max_beads)

    # Load data
    claims = load_all_claims()
    negatives = load_negative_beads()

    logger.info("Loaded %d CLAIM_BEADs, %d NEGATIVE beads", len(claims), len(negatives))

    if not claims:
        logger.info("No claims to compress")
        return {
            "compressed": False,
            "total_claims": 0,
            "clusters_by_drawer": {},
            "redundant_pairs": 0,
            "archived_files": [],
            "theory_path": str(THEORY_PATH),
        }

    # Cluster by drawer
    by_drawer = cluster_by_drawer(claims)

    # Cluster within each drawer
    drawer_clusters: Dict[int, List[List[Dict]]] = {}
    for drawer_num, drawer_claims in by_drawer.items():
        if drawer_claims:
            clusters = cluster_within_drawer(drawer_claims, similarity_threshold)
            drawer_clusters[drawer_num] = clusters
            logger.info("Drawer %d (%s): %d claims → %d clusters",
                       drawer_num, DRAWER_NAMES[drawer_num],
                       len(drawer_claims), len(clusters))

    # Detect redundant pairs across all claims
    redundant = detect_redundant_pairs(claims, similarity_threshold)
    logger.info("Found %d redundant pairs (sim >= %.2f)", len(redundant), similarity_threshold)

    # Generate THEORY.md
    theory_content = generate_theory_md(drawer_clusters, redundant, negatives)

    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    with open(THEORY_PATH, "w") as f:
        f.write(theory_content)
    logger.info("Updated THEORY.md at %s", THEORY_PATH)

    # Archive old sessions
    archived = archive_old_sessions(keep_days=archive_days)

    return {
        "compressed": True,
        "total_claims": len(claims),
        "clusters_by_drawer": {d: len(c) for d, c in drawer_clusters.items()},
        "redundant_pairs": len(redundant),
        "archived_files": [str(p) for p in archived],
        "theory_path": str(THEORY_PATH),
    }


def needs_compression_check(max_beads: int = DEFAULT_MAX_BEADS) -> bool:
    """Check if compression is needed based on bead count.

    This wraps context.needs_compression for the Chronicler interface.
    """
    from core.context import needs_compression
    return needs_compression(max_beads)


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(description="Run Chronicler compression")
    parser.add_argument("--max-beads", type=int, default=DEFAULT_MAX_BEADS,
                       help="Bead count threshold for compression")
    parser.add_argument("--similarity", type=float, default=DEFAULT_SIMILARITY_THRESHOLD,
                       help="Cosine similarity threshold for redundancy")
    parser.add_argument("--archive-days", type=int, default=1,
                       help="Archive sessions older than N days")
    parser.add_argument("--force", action="store_true",
                       help="Force compression even if below threshold")

    args = parser.parse_args()

    if not args.force and not needs_compression_check(args.max_beads):
        print(f"Bead count below threshold ({args.max_beads}). Use --force to compress anyway.")
    else:
        result = compress_beads(
            max_beads=args.max_beads,
            similarity_threshold=args.similarity,
            archive_days=args.archive_days,
        )
        print(json.dumps(result, indent=2))
