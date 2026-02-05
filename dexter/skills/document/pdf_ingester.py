"""PDF Ingester — Extract text from PDF documents.

P3: Source Ingestion Pipeline

Extracts text from PDFs, handles mixed content (text + images),
chunks for Theorist processing with source tier tagging.

P3.4-fix: Image-heavy pages extracted via Gemini Vision OCR.

Dependencies: PyMuPDF (fitz)
"""

from __future__ import annotations

import base64
import io
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

# Chunk settings for PDFs (optimized for documents, not transcripts)
# P3.4d: Increased chunk size to reduce API calls with expensive models
DEFAULT_CHUNK_SIZE = 12000  # characters (target: 5-20 chunks per document)
DEFAULT_OVERLAP = 200  # minimal overlap for document continuity
MIN_CHUNK_SIZE = 8000  # minimum chunk before combining with next page
MAX_CHUNK_SIZE = 16000  # maximum before splitting


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


# Vision extraction prompt for image-heavy PDF pages (legacy, kept for compatibility)
VISION_EXTRACT_PROMPT = """Extract all visible text, annotations, labels, and structured content from this image.

IMPORTANT:
- Preserve any trading terminology, price levels, and chart annotations exactly as written
- Include all text boxes, labels, headers, and captions
- For tables or structured content, preserve the structure
- If there are bullet points or numbered lists, maintain the format
- Include any handwritten annotations if readable
- For charts: extract axis labels, data labels, annotations, but do NOT interpret price action

Return ONLY the extracted text, no commentary or analysis."""


def _extract_page_image_text(
    page,
    page_num: int,
    fitz,
    *,
    source_tier: str = "LATERAL",
    use_trading_vision: bool = True,
) -> str:
    """Extract text from an image-heavy page using vision API.

    P3.5: Uses the enhanced vision extractor for trading content.

    Args:
        page: PyMuPDF page object
        page_num: Page number (1-indexed)
        fitz: PyMuPDF module
        source_tier: Source tier for model selection
        use_trading_vision: If True, use enhanced trading chart extraction

    Returns:
        Extracted text from the page image
    """
    # Check if vision extraction is enabled
    if os.getenv("DEXTER_VISION_EXTRACT", "false").lower() != "true":
        logger.debug("Vision extract disabled for page %d (set DEXTER_VISION_EXTRACT=true)", page_num)
        return ""

    # Render page to image
    mat = fitz.Matrix(150 / 72, 150 / 72)  # 150 DPI
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")

    # P3.5: Use enhanced trading vision extraction
    if use_trading_vision:
        try:
            from skills.document.vision_extractor import extract_chart_description, extract_notes_description

            # Use Opus for OLYA_PRIMARY, Sonnet for others
            use_opus = source_tier in ("OLYA_PRIMARY", "CANON")

            # Try notes extraction (better for text-heavy content with charts)
            result = extract_notes_description(
                img_base64,
                source_tier=source_tier,
                use_opus=use_opus,
            )
            extracted_text = result.get("description", "").strip()

            if extracted_text:
                logger.info("[VISION P3.5] Page %d: extracted %d chars via trading vision",
                           page_num, len(extracted_text))
                return extracted_text

        except ImportError:
            logger.debug("Enhanced vision extractor not available, falling back to basic OCR")
        except Exception as e:
            logger.warning("[VISION P3.5] Page %d trading extraction failed: %s, trying basic OCR",
                          page_num, e)

    # Fallback to basic OCR via llm_client
    try:
        from core.llm_client import call_vision_extract

        result = call_vision_extract(img_base64, VISION_EXTRACT_PROMPT)
        extracted_text = result.get("content", "").strip()

        if extracted_text:
            logger.info("[VISION] Page %d: extracted %d chars via basic OCR", page_num, len(extracted_text))
            return extracted_text
        else:
            logger.debug("[VISION] Page %d: no text extracted", page_num)
            return ""

    except ImportError:
        logger.warning("Vision extraction unavailable (llm_client not found)")
        return ""
    except Exception as e:
        logger.warning("[VISION] Page %d extraction failed: %s", page_num, e)
        return ""


def extract_text_from_pdf(
    pdf_path: Path,
    *,
    min_text_chars: int = MIN_TEXT_CHARS_PER_PAGE,
    source_tier: Optional[str] = None,
) -> Dict:
    """Extract text from a PDF file.

    P3.5: Now uses enhanced trading vision extraction for image-heavy pages.

    Args:
        pdf_path: Path to PDF file
        min_text_chars: Minimum chars for page to be considered text-heavy
        source_tier: Source tier for vision model selection

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

    # Auto-detect source tier if not provided
    if source_tier is None:
        source_tier = determine_source_tier(pdf_path)

    logger.info("Extracting text from PDF: %s (tier=%s)", pdf_path.name, source_tier)

    doc = fitz.open(pdf_path)
    pages = []
    image_heavy_pages = []
    all_text = []

    total_pages = len(doc)

    for page_num in range(total_pages):
        page = doc[page_num]
        text = page.get_text()
        char_count = len(text.strip())

        if char_count >= min_text_chars:
            # Text-heavy page — use extracted text
            pages.append({
                "page_num": page_num + 1,
                "text": text.strip(),
                "char_count": char_count,
                "extraction_method": "text",
            })
            all_text.append(text.strip())
        else:
            # Image-heavy page — try vision extraction (P3.5 enhanced)
            image_heavy_pages.append(page_num + 1)
            logger.debug("Page %d is image-heavy (%d chars), trying vision...", page_num + 1, char_count)

            vision_text = _extract_page_image_text(
                page, page_num + 1, fitz,
                source_tier=source_tier,
                use_trading_vision=True,
            )
            if vision_text:
                pages.append({
                    "page_num": page_num + 1,
                    "text": vision_text,
                    "char_count": len(vision_text),
                    "extraction_method": "vision",
                })
                all_text.append(vision_text)
            else:
                # No text extracted from either method
                pages.append({
                    "page_num": page_num + 1,
                    "text": text.strip(),  # Keep any minimal text
                    "char_count": char_count,
                    "extraction_method": "text_minimal",
                })
                if text.strip():
                    all_text.append(text.strip())

    doc.close()

    text_pages = total_pages - len(image_heavy_pages)
    vision_pages = sum(1 for p in pages if p.get("extraction_method") == "vision")
    full_text = "\n\n".join(all_text)

    logger.info(
        "Extracted %d pages (%d text, %d image-heavy, %d via vision) from %s",
        total_pages, text_pages, len(image_heavy_pages), vision_pages, pdf_path.name,
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


def chunk_pdf_by_pages(
    extracted: Dict,
    *,
    min_chunk_size: int = MIN_CHUNK_SIZE,
    max_chunk_size: int = MAX_CHUNK_SIZE,
) -> List[Dict]:
    """Chunk PDF by page boundaries (P3.4d optimization).

    Uses natural page breaks to create larger, coherent chunks.
    Combines small pages, splits very large pages.

    Args:
        extracted: Output from extract_text_from_pdf()
        min_chunk_size: Minimum chars before combining with next page
        max_chunk_size: Maximum chars before splitting

    Returns:
        List of {"chunk_num": int, "text": str, "page_start": int, "page_end": int}
    """
    pages = extracted.get("pages", [])
    if not pages:
        return []

    chunks = []
    chunk_num = 1
    current_text = []
    current_char_count = 0
    current_page_start = 1

    for page in pages:
        page_text = page.get("text", "").strip()
        page_num = page.get("page_num", 0)
        page_chars = len(page_text)

        if not page_text:
            continue

        # If this page alone exceeds max, split it
        if page_chars > max_chunk_size:
            # Save current accumulated chunk first
            if current_text:
                chunks.append({
                    "chunk_num": chunk_num,
                    "text": "\n\n".join(current_text),
                    "page_start": current_page_start,
                    "page_end": page_num - 1,
                })
                chunk_num += 1
                current_text = []
                current_char_count = 0

            # Split the large page at paragraph breaks
            sub_chunks = _split_large_text(page_text, max_chunk_size)
            for i, sub_text in enumerate(sub_chunks):
                chunks.append({
                    "chunk_num": chunk_num,
                    "text": sub_text,
                    "page_start": page_num,
                    "page_end": page_num,
                    "sub_chunk": i + 1,
                })
                chunk_num += 1
            current_page_start = page_num + 1
            continue

        # If adding this page would exceed max, save current and start new
        if current_char_count + page_chars > max_chunk_size and current_text:
            chunks.append({
                "chunk_num": chunk_num,
                "text": "\n\n".join(current_text),
                "page_start": current_page_start,
                "page_end": page_num - 1,
            })
            chunk_num += 1
            current_text = []
            current_char_count = 0
            current_page_start = page_num

        # Add page to current chunk
        current_text.append(page_text)
        current_char_count += page_chars

        # If we've reached minimum size and next page would likely exceed max,
        # close the chunk (but don't close if we haven't reached min yet)
        if current_char_count >= min_chunk_size:
            # Check if this is a good place to break
            # (We'll continue accumulating if still under max)
            pass

    # Save remaining
    if current_text:
        last_page = pages[-1].get("page_num", len(pages))
        chunks.append({
            "chunk_num": chunk_num,
            "text": "\n\n".join(current_text),
            "page_start": current_page_start,
            "page_end": last_page,
        })

    logger.info(
        "Chunked %d pages into %d chunks (page-based, %d-%d char targets)",
        len(pages), len(chunks), min_chunk_size, max_chunk_size,
    )

    return chunks


def _split_large_text(text: str, max_size: int) -> List[str]:
    """Split large text at paragraph boundaries."""
    paragraphs = text.split("\n\n")
    chunks = []
    current = []
    current_size = 0

    for para in paragraphs:
        para_size = len(para)

        if current_size + para_size > max_size and current:
            chunks.append("\n\n".join(current))
            current = []
            current_size = 0

        current.append(para)
        current_size += para_size

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def chunk_pdf_text(
    extracted: Dict,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    use_page_chunking: bool = True,
) -> List[Dict]:
    """Chunk extracted PDF text.

    P3.4d: Default to page-based chunking for better document coherence.

    Args:
        extracted: Output from extract_text_from_pdf()
        chunk_size: Target chunk size in characters (for legacy mode)
        overlap: Overlap between chunks in characters (for legacy mode)
        use_page_chunking: If True, use page-based chunking (default)

    Returns:
        List of chunk dicts
    """
    # P3.4d: Use page-based chunking by default
    if use_page_chunking:
        page_chunks = chunk_pdf_by_pages(extracted)
        # Convert to standard format
        return [
            {
                "chunk_num": c["chunk_num"],
                "text": c["text"],
                "char_start": 0,  # Not applicable for page chunking
                "char_end": len(c["text"]),
                "page_start": c.get("page_start"),
                "page_end": c.get("page_end"),
            }
            for c in page_chunks
        ]

    # Legacy character-based chunking (for transcripts or special cases)
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

    # Extract (P3.5: pass tier for vision model selection)
    extracted = extract_text_from_pdf(pdf_path, source_tier=tier)

    # Build set of vision-extracted pages for source_type tagging
    vision_pages = set()
    for page in extracted.get("pages", []):
        if page.get("extraction_method") == "vision":
            vision_pages.add(page.get("page_num"))

    # Chunk (P3.4d: page-based by default)
    raw_chunks = chunk_pdf_text(extracted, chunk_size=chunk_size, overlap=overlap)

    # Add metadata to each chunk
    chunks = []
    for chunk in raw_chunks:
        # Use page provenance if available, else char range
        if chunk.get("page_start") and chunk.get("page_end"):
            if chunk["page_start"] == chunk["page_end"]:
                provenance = f"page {chunk['page_start']}"
            else:
                provenance = f"pages {chunk['page_start']}-{chunk['page_end']}"

            # P3.5: Check if chunk is from vision-extracted pages
            chunk_pages = range(chunk["page_start"], chunk["page_end"] + 1)
            has_vision = any(p in vision_pages for p in chunk_pages)
        else:
            provenance = f"chars {chunk['char_start']}-{chunk['char_end']}"
            has_vision = False

        # P3.5: Set source_type based on extraction method
        source_type = "VISUAL" if has_vision else "DOCUMENT"

        chunks.append({
            "chunk_num": chunk["chunk_num"],
            "text": chunk["text"],
            "source_file": pdf_path.name,
            "source_type": source_type,
            "source_tier": tier,
            "provenance": provenance,
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
