"""Markdown Ingester — Parse and chunk markdown documents.

P3: Source Ingestion Pipeline

Parses markdown files by section headers, preserves structure,
chunks for Theorist processing with source tier tagging.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("dexter.md_ingester")

# Heading patterns
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

# Chunk settings
DEFAULT_CHUNK_SIZE = 2000  # characters
DEFAULT_OVERLAP = 400  # characters


def parse_markdown_sections(content: str) -> List[Dict]:
    """Parse markdown into sections by headers.

    Args:
        content: Raw markdown text

    Returns:
        List of {"level": int, "title": str, "content": str, "line_start": int}
    """
    lines = content.split("\n")
    sections = []
    current_section = None
    current_content = []
    current_line = 0

    for i, line in enumerate(lines):
        match = HEADING_PATTERN.match(line)

        if match:
            # Save previous section
            if current_section:
                current_section["content"] = "\n".join(current_content).strip()
                sections.append(current_section)

            # Start new section
            level = len(match.group(1))
            title = match.group(2).strip()
            current_section = {
                "level": level,
                "title": title,
                "line_start": i + 1,
            }
            current_content = []
        else:
            current_content.append(line)

    # Save last section
    if current_section:
        current_section["content"] = "\n".join(current_content).strip()
        sections.append(current_section)
    elif current_content:
        # Document with no headers
        sections.append({
            "level": 0,
            "title": "(No heading)",
            "content": "\n".join(current_content).strip(),
            "line_start": 1,
        })

    return sections


def chunk_markdown(
    content: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    preserve_sections: bool = True,
) -> List[Dict]:
    """Chunk markdown into overlapping windows.

    Args:
        content: Raw markdown text
        chunk_size: Target chunk size in characters
        overlap: Overlap between chunks in characters
        preserve_sections: Try to break at section boundaries

    Returns:
        List of {"chunk_num": int, "text": str, "section": str, "line_start": int}
    """
    if preserve_sections:
        sections = parse_markdown_sections(content)
        return _chunk_by_sections(sections, chunk_size, overlap)
    else:
        return _chunk_by_size(content, chunk_size, overlap)


def _chunk_by_sections(
    sections: List[Dict],
    chunk_size: int,
    overlap: int,
) -> List[Dict]:
    """Chunk by respecting section boundaries where possible."""
    chunks = []
    chunk_num = 1
    current_text = []
    current_char_count = 0
    current_section_titles = []

    for section in sections:
        section_text = section["content"]
        section_title = section["title"]
        section_chars = len(section_text)

        # If adding this section would exceed chunk size
        if current_char_count + section_chars > chunk_size and current_text:
            # Save current chunk
            chunks.append({
                "chunk_num": chunk_num,
                "text": "\n\n".join(current_text),
                "sections": current_section_titles.copy(),
                "section": current_section_titles[0] if current_section_titles else "",
            })
            chunk_num += 1

            # Start new chunk with overlap (last part of previous)
            if overlap > 0 and current_text:
                overlap_text = "\n\n".join(current_text)[-overlap:]
                current_text = [overlap_text] if overlap_text.strip() else []
                current_char_count = len(overlap_text)
            else:
                current_text = []
                current_char_count = 0
            current_section_titles = []

        # If single section is larger than chunk_size, split it
        if section_chars > chunk_size:
            sub_chunks = _chunk_by_size(section_text, chunk_size, overlap)
            for sub in sub_chunks:
                chunks.append({
                    "chunk_num": chunk_num,
                    "text": sub["text"],
                    "sections": [section_title],
                    "section": section_title,
                })
                chunk_num += 1
        else:
            # Add section to current chunk
            if section_text.strip():
                current_text.append(f"## {section_title}\n{section_text}")
                current_char_count += section_chars
                current_section_titles.append(section_title)

    # Save remaining
    if current_text:
        chunks.append({
            "chunk_num": chunk_num,
            "text": "\n\n".join(current_text),
            "sections": current_section_titles,
            "section": current_section_titles[0] if current_section_titles else "",
        })

    return chunks


def _chunk_by_size(
    content: str,
    chunk_size: int,
    overlap: int,
) -> List[Dict]:
    """Simple size-based chunking."""
    chunks = []
    start = 0
    chunk_num = 1

    while start < len(content):
        end = min(start + chunk_size, len(content))

        # Try to break at paragraph/sentence boundary
        if end < len(content):
            for i in range(end, max(start, end - 200), -1):
                if content[i] in "\n.!?":
                    end = i + 1
                    break

        chunk_text = content[start:end].strip()

        if chunk_text:
            chunks.append({
                "chunk_num": chunk_num,
                "text": chunk_text,
                "sections": [],
                "section": "",
            })
            chunk_num += 1

        start = max(start + 1, end - overlap)

    return chunks


def determine_source_tier(file_path: Path) -> str:
    """Determine source tier based on file path."""
    path_str = str(file_path).lower()

    if "layer_0" in path_str or "5_drawer" in path_str:
        return "CANON"
    elif "olya" in path_str:
        return "OLYA_PRIMARY"
    else:
        return "LATERAL"


def ingest_markdown(
    md_path: Path,
    *,
    source_tier: Optional[str] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> Dict:
    """Full markdown ingestion: parse, chunk, and add metadata.

    Args:
        md_path: Path to markdown file
        source_tier: Override tier (auto-detected if None)
        chunk_size: Chunk size in characters
        overlap: Overlap in characters

    Returns:
        {
            "source_file": str,
            "source_type": "markdown",
            "source_tier": str,
            "total_sections": int,
            "chunks": [{
                "chunk_num": int,
                "text": str,
                "source_file": str,
                "source_type": "markdown",
                "source_tier": str,
                "section": str,
                "provenance": str,
            }],
        }
    """
    md_path = Path(md_path)
    if not md_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_path}")

    tier = source_tier or determine_source_tier(md_path)

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    sections = parse_markdown_sections(content)
    raw_chunks = chunk_markdown(content, chunk_size=chunk_size, overlap=overlap)

    # Add metadata to each chunk
    chunks = []
    for chunk in raw_chunks:
        section = chunk.get("section", "")
        provenance = f"section: {section}" if section else f"chunk {chunk['chunk_num']}"

        chunks.append({
            "chunk_num": chunk["chunk_num"],
            "text": chunk["text"],
            "source_file": md_path.name,
            "source_type": "markdown",
            "source_tier": tier,
            "section": section,
            "provenance": provenance,
        })

    logger.info(
        "Ingested markdown: %s | tier=%s | %d sections | %d chunks",
        md_path.name, tier, len(sections), len(chunks),
    )

    return {
        "source_file": str(md_path),
        "source_type": "markdown",
        "source_tier": tier,
        "total_sections": len(sections),
        "sections": [s["title"] for s in sections],
        "chunks": chunks,
    }


def format_chunks_for_theorist(chunks: List[Dict]) -> str:
    """Format chunks for Theorist input.

    Args:
        chunks: List of chunk dicts from ingest_markdown()

    Returns:
        Formatted string for Theorist processing
    """
    lines = []
    for chunk in chunks:
        provenance = chunk.get("provenance", f"chunk {chunk.get('chunk_num', '?')}")
        source = chunk.get("source_file", "unknown")
        tier = chunk.get("source_tier", "unknown")
        text = chunk.get("text", "")

        lines.append(f"[{provenance}] [{tier}] {source}")
        lines.append(text)
        lines.append("")

    return "\n".join(lines)
