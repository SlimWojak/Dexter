"""PDF Ingester — Extract text from PDF documents.

P3: Source Ingestion Pipeline

Extracts text from PDFs, handles mixed content (text + images),
chunks for Theorist processing with source tier tagging.

Dependencies: PyMuPDF (fitz)
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("dexter.pdf_ingester")

# Source tier definitions
SOURCE_TIERS = {
    "CANON": "Canon source (5-drawer YAMLs, Layer 0)",
    "OLYA_PRIMARY": "Olya's primary notes and analysis",
    "LATERAL": "Lateral education sources (Blessed Trader, etc.)",
    "ICT_LEARNING": "ICT YouTube content",
}

# Minimum text threshold for a page to be considered "text-heavy"
MIN_TEXT_CHARS_PER_PAGE = 100

# Chunk settings (match supadata chunking pattern)
DEFAULT_CHUNK_SIZE = 2000  # characters (rough equivalent of 5min transcript)
DEFAULT_OVERLAP = 400  # characters (~1min overlap equivalent)


def _load_fitz():
    """Lazy-load PyMuPDF to allow graceful fallback."""
    try:
        import fitz
        return fitz
    except ImportError:
        raise ImportError(
            "PyMuPDF not installed. Run: pip install PyMuPDF\n"
            "Or add to requirements.txt and reinstall."
        )


def extract_text_from_pdf(
    pdf_path: Path,
    *,
    min_text_chars: int = MIN_TEXT_CHARS_PER_PAGE,
) -> Dict:
    """Extract text from a PDF file.

    Args:
        pdf_path: Path to PDF file
        min_text_chars: Minimum chars for page to be considered text-heavy

    Returns:
        {
            "file_path": str,
            "file_name": str,
            "total_pages": int,
            "text_pages": int,
            "image_heavy_pages": list[int],  # Page numbers with mostly images
            "pages": [{"page_num": int, "text": str, "char_count": int}],
            "full_text": str,  # All text concatenated
        }
    """
    fitz = _load_fitz()

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    logger.info("Extracting text from PDF: %s", pdf_path.name)

    doc = fitz.open(pdf_path)
    pages = []
    image_heavy_pages = []
    all_text = []

    total_pages = len(doc)

    for page_num in range(total_pages):
        page = doc[page_num]
        text = page.get_text()
        char_count = len(text.strip())

        pages.append({
            "page_num": page_num + 1,  # 1-indexed for human readability
            "text": text.strip(),
            "char_count": char_count,
        })

        if char_count >= min_text_chars:
            all_text.append(text.strip())
        else:
            # Log as image-heavy (mostly charts/screenshots)
            image_heavy_pages.append(page_num + 1)
            logger.debug("Page %d is image-heavy (%d chars)", page_num + 1, char_count)

    doc.close()

    text_pages = total_pages - len(image_heavy_pages)
    full_text = "\n\n".join(all_text)

    logger.info(
        "Extracted %d pages (%d text, %d image-heavy) from %s",
        total_pages, text_pages, len(image_heavy_pages), pdf_path.name,
    )

    return {
        "file_path": str(pdf_path),
        "file_name": pdf_path.name,
        "total_pages": total_pages,
        "text_pages": text_pages,
        "image_heavy_pages": image_heavy_pages,
        "pages": pages,
        "full_text": full_text,
    }


def chunk_pdf_text(
    extracted: Dict,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> List[Dict]:
    """Chunk extracted PDF text into overlapping windows.

    Similar to supadata chunk_transcript() but uses character-based windows
    instead of time-based.

    Args:
        extracted: Output from extract_text_from_pdf()
        chunk_size: Target chunk size in characters
        overlap: Overlap between chunks in characters

    Returns:
        List of {"chunk_num": int, "text": str, "source_page_start": int, "source_page_end": int}
    """
    full_text = extracted.get("full_text", "")
    if not full_text:
        return []

    chunks = []
    start = 0
    chunk_num = 1

    while start < len(full_text):
        end = min(start + chunk_size, len(full_text))

        # Try to break at word boundary
        if end < len(full_text):
            # Look for space/newline near end
            for i in range(end, max(start, end - 100), -1):
                if full_text[i] in " \n":
                    end = i + 1
                    break

        chunk_text = full_text[start:end].strip()

        if chunk_text:
            chunks.append({
                "chunk_num": chunk_num,
                "text": chunk_text,
                "char_start": start,
                "char_end": end,
            })
            chunk_num += 1

        # Move start with overlap
        start = max(start + 1, end - overlap)

    logger.info("Chunked %d chars into %d chunks (%d char windows, %d overlap)",
                len(full_text), len(chunks), chunk_size, overlap)

    return chunks


def determine_source_tier(file_path: Path) -> str:
    """Determine source tier based on file path.

    Args:
        file_path: Path to source file

    Returns:
        One of: CANON, OLYA_PRIMARY, LATERAL, ICT_LEARNING
    """
    path_str = str(file_path).lower()

    if "5_drawer" in path_str or "layer_0" in path_str:
        return "CANON"
    elif "olya_notes" in path_str or "olya" in path_str:
        return "OLYA_PRIMARY"
    elif "blessed" in path_str:
        return "LATERAL"
    else:
        return "LATERAL"  # Default for PDFs


def ingest_pdf(
    pdf_path: Path,
    *,
    source_tier: Optional[str] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> Dict:
    """Full PDF ingestion: extract, chunk, and add metadata.

    Args:
        pdf_path: Path to PDF file
        source_tier: Override tier (auto-detected if None)
        chunk_size: Chunk size in characters
        overlap: Overlap in characters

    Returns:
        {
            "source_file": str,
            "source_type": "pdf",
            "source_tier": str,
            "total_pages": int,
            "text_pages": int,
            "image_heavy_pages": list[int],
            "chunks": [{
                "chunk_num": int,
                "text": str,
                "source_file": str,
                "source_type": "pdf",
                "source_tier": str,
                "provenance": str,  # "page X-Y" or "chars X-Y"
            }],
        }
    """
    pdf_path = Path(pdf_path)
    tier = source_tier or determine_source_tier(pdf_path)

    # Extract
    extracted = extract_text_from_pdf(pdf_path)

    # Chunk
    raw_chunks = chunk_pdf_text(extracted, chunk_size=chunk_size, overlap=overlap)

    # Add metadata to each chunk
    chunks = []
    for chunk in raw_chunks:
        chunks.append({
            "chunk_num": chunk["chunk_num"],
            "text": chunk["text"],
            "source_file": pdf_path.name,
            "source_type": "pdf",
            "source_tier": tier,
            "provenance": f"chars {chunk['char_start']}-{chunk['char_end']}",
        })

    logger.info(
        "Ingested PDF: %s | tier=%s | %d chunks | %d text pages | %d image-heavy pages",
        pdf_path.name, tier, len(chunks),
        extracted["text_pages"], len(extracted["image_heavy_pages"]),
    )

    return {
        "source_file": str(pdf_path),
        "source_type": "pdf",
        "source_tier": tier,
        "total_pages": extracted["total_pages"],
        "text_pages": extracted["text_pages"],
        "image_heavy_pages": extracted["image_heavy_pages"],
        "chunks": chunks,
    }


def ingest_pdf_directory(
    dir_path: Path,
    *,
    source_tier: Optional[str] = None,
    recursive: bool = False,
) -> List[Dict]:
    """Ingest all PDFs in a directory.

    Args:
        dir_path: Directory containing PDFs
        source_tier: Override tier for all files
        recursive: Search subdirectories

    Returns:
        List of ingestion results (one per PDF)
    """
    dir_path = Path(dir_path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    pattern = "**/*.pdf" if recursive else "*.pdf"
    pdf_files = sorted(dir_path.glob(pattern))

    logger.info("Found %d PDFs in %s", len(pdf_files), dir_path)

    results = []
    for pdf_path in pdf_files:
        try:
            result = ingest_pdf(pdf_path, source_tier=source_tier)
            results.append(result)
        except Exception as e:
            logger.error("Failed to ingest %s: %s", pdf_path.name, e)
            results.append({
                "source_file": str(pdf_path),
                "source_type": "pdf",
                "source_tier": source_tier or "unknown",
                "error": str(e),
                "chunks": [],
            })

    return results


def format_chunks_for_theorist(chunks: List[Dict]) -> str:
    """Format chunks for Theorist input (similar to transcript format).

    Args:
        chunks: List of chunk dicts from ingest_pdf()

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
        lines.append("")  # Blank line between chunks

    return "\n".join(lines)
