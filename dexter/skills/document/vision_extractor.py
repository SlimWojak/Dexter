"""Vision Extraction Skill — Extract trading logic from annotated charts.

P3.5: Two-pass architecture for visual content extraction.

Pass 1 — Vision Description:
  - Input: Chart screenshot with annotations
  - Model: Claude Opus via Anthropic direct (vision capable)
  - Output: Structured text description of all visual elements

Pass 2 — Theorist Extraction:
  - Input: Vision description + any surrounding text
  - Model: Standard tier routing
  - Output: IF-THEN signatures with source_type: VISUAL

This enables Dexter to extract trading rules from:
- Annotated TradingView screenshots
- Olya's note PDFs with chart images
- Blessed Trader chart examples
- Any visual trading content
"""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger("dexter.vision_extractor")

# =============================================================================
# VISION DESCRIPTION PROMPTS (Pass 1)
# =============================================================================

CHART_DESCRIPTION_PROMPT = """Describe everything visible on this trading chart screenshot.

EXTRACT AND DESCRIBE:
1. DRAWN ZONES & RECTANGLES:
   - Any highlighted areas, boxes, or shaded zones
   - Color and position (e.g., "blue rectangle at price level X-Y")

2. LABELED PRICE LEVELS:
   - Exact text of any price labels (e.g., "BSL @ 1.12020")
   - Horizontal lines with annotations
   - Support/resistance markings

3. TEXT ANNOTATIONS & NOTES:
   - All text boxes, comments, or explanatory notes
   - Any checklist items visible
   - Handwritten or typed annotations

4. ICT CONCEPT MARKERS:
   - Order blocks (+OB, -OB, bullish OB, bearish OB)
   - Fair Value Gaps (FVG, IFVG, BISI, SIBI)
   - Liquidity markers (BSL, SSL, buy-side, sell-side)
   - Breakers, mitigation blocks
   - MSS (Market Structure Shift) markers
   - Midpoints, equilibrium lines

5. FIBONACCI LEVELS:
   - Any fib retracement or extension levels
   - OTE zones (0.62-0.79 area)
   - Specific fib values shown

6. ARROWS & DIRECTIONAL INDICATORS:
   - Entry/exit arrows
   - Predicted price movement paths
   - Directional bias indicators

7. TIME/SESSION MARKERS:
   - Killzone boundaries (Asia, London, NY)
   - Time labels on chart
   - Session separators

8. STRUCTURAL ELEMENTS:
   - Highs and lows marked (HH, HL, LH, LL)
   - Swing points
   - Range boundaries

CRITICAL RULES:
- Use EXACT terminology as written on the chart — do NOT translate or interpret
- If you see "+OB", write "+OB", not "positive order block"
- If you see "BSL @ 1.12020", preserve that exact format
- Include ALL text, even if partially visible
- For numbered lists or checklists, preserve the structure

Return a structured description with sections for each category above.
If a category has no relevant content, skip it."""


TRADING_NOTES_PROMPT = """Describe all visible content in this trading notes screenshot.

EXTRACT:
1. ALL TEXT:
   - Headers, titles, and section names
   - Bullet points and numbered lists
   - Explanatory paragraphs
   - Checklists with check/uncheck states

2. CHART CONTENT (if present):
   - Use the same extraction rules as for charts
   - Price levels, annotations, markers

3. TABLES OR STRUCTURED DATA:
   - Preserve table structure
   - Column headers and values

4. RULES OR CONDITIONS:
   - Any IF-THEN style statements
   - Entry/exit criteria
   - Validation/invalidation conditions

5. TERMINOLOGY:
   - ICT-specific terms (preserve exact spelling)
   - Abbreviations and acronyms
   - Custom notation

CRITICAL:
- Preserve EXACT text as written
- Include checklist item states (checked/unchecked)
- Maintain list numbering and hierarchy
- Do not interpret — transcribe faithfully"""


# =============================================================================
# VISION EXTRACTION FUNCTIONS
# =============================================================================

def _get_anthropic_key() -> Optional[str]:
    """Get Anthropic API key from environment."""
    return os.getenv("ANTHROPIC_API_KEY")


def extract_chart_description(
    image_base64: str,
    *,
    source_tier: str = "OLYA_PRIMARY",
    timeout: float = 120.0,
    use_opus: bool = True,
) -> Dict:
    """Pass 1: Extract structured description from a chart image.

    Args:
        image_base64: Base64-encoded image data (PNG or JPEG)
        source_tier: Source tier for model selection
        timeout: Request timeout in seconds
        use_opus: If True, use Opus for highest quality (default for OLYA_PRIMARY)

    Returns:
        {
            "description": str,  # Structured text description
            "model": str,
            "usage": dict,
            "source_type": "VISUAL",
        }
    """
    api_key = _get_anthropic_key()
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set for vision extraction")

    # Model selection based on tier and quality flag
    if use_opus and source_tier in ("OLYA_PRIMARY", "CANON"):
        model = "claude-opus-4-5-20251101"
    else:
        model = "claude-sonnet-4-5-20250929"

    # Determine media type (assume PNG if not obvious)
    # Base64 doesn't carry format info, but most screenshots are PNG
    media_type = "image/png"

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_base64,
                    },
                },
                {
                    "type": "text",
                    "text": CHART_DESCRIPTION_PROMPT,
                },
            ],
        }
    ]

    with httpx.Client(timeout=timeout) as client:
        response = client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": 4096,
                "temperature": 0.1,  # Low temp for accurate description
            },
        )

        if response.status_code == 429:
            logger.warning("[VISION] Rate limited on %s, waiting 10s...", model)
            import time
            time.sleep(10)
            response = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 4096,
                    "temperature": 0.1,
                },
            )

        response.raise_for_status()
        data = response.json()

        # Parse response
        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        usage = data.get("usage", {})
        normalized_usage = {
            "prompt_tokens": usage.get("input_tokens", 0),
            "completion_tokens": usage.get("output_tokens", 0),
        }

        # Log cost
        _log_vision_cost(model, normalized_usage)

        logger.info(
            "[VISION] Chart description extracted: model=%s, tokens_in=%d, tokens_out=%d, chars=%d",
            model,
            normalized_usage.get("prompt_tokens", 0),
            normalized_usage.get("completion_tokens", 0),
            len(content),
        )

        return {
            "description": content,
            "model": model,
            "usage": normalized_usage,
            "source_type": "VISUAL",
        }


def extract_notes_description(
    image_base64: str,
    *,
    source_tier: str = "OLYA_PRIMARY",
    timeout: float = 120.0,
    use_opus: bool = True,
) -> Dict:
    """Pass 1: Extract structured description from trading notes image.

    Similar to extract_chart_description but optimized for note-style content.
    """
    api_key = _get_anthropic_key()
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set for vision extraction")

    if use_opus and source_tier in ("OLYA_PRIMARY", "CANON"):
        model = "claude-opus-4-5-20251101"
    else:
        model = "claude-sonnet-4-5-20250929"

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_base64,
                    },
                },
                {
                    "type": "text",
                    "text": TRADING_NOTES_PROMPT,
                },
            ],
        }
    ]

    with httpx.Client(timeout=timeout) as client:
        response = client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": 4096,
                "temperature": 0.1,
            },
        )

        if response.status_code == 429:
            logger.warning("[VISION] Rate limited on %s, waiting 10s...", model)
            import time
            time.sleep(10)
            response = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 4096,
                    "temperature": 0.1,
                },
            )

        response.raise_for_status()
        data = response.json()

        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        usage = data.get("usage", {})
        normalized_usage = {
            "prompt_tokens": usage.get("input_tokens", 0),
            "completion_tokens": usage.get("output_tokens", 0),
        }

        _log_vision_cost(model, normalized_usage)

        logger.info(
            "[VISION] Notes description extracted: model=%s, chars=%d",
            model, len(content),
        )

        return {
            "description": content,
            "model": model,
            "usage": normalized_usage,
            "source_type": "VISUAL",
        }


def _log_vision_cost(model: str, usage: Dict) -> None:
    """Log vision API cost."""
    # Cost per 1M tokens (Feb 2026)
    costs = {
        "claude-opus-4-5-20251101": {"input": 15.00, "output": 75.00},
        "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},
    }

    model_costs = costs.get(model)
    if not model_costs:
        return

    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    cost = (
        (input_tokens / 1_000_000 * model_costs["input"])
        + (output_tokens / 1_000_000 * model_costs["output"])
    )

    logger.info("[VISION COST] model=%s cost=$%.4f (in=%d out=%d)",
                model, cost, input_tokens, output_tokens)

    # Record to guard manager
    try:
        from core.loop import record_llm_cost
        record_llm_cost(cost, model)
    except ImportError:
        pass


# =============================================================================
# IMAGE LOADING UTILITIES
# =============================================================================

def load_image_as_base64(image_path: Path) -> str:
    """Load an image file and encode as base64.

    Args:
        image_path: Path to PNG, JPEG, or other image file

    Returns:
        Base64-encoded string
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def extract_pdf_page_as_image(pdf_path: Path, page_num: int) -> str:
    """Extract a PDF page as a base64-encoded PNG image.

    Args:
        pdf_path: Path to PDF file
        page_num: Page number (1-indexed)

    Returns:
        Base64-encoded PNG image
    """
    try:
        import fitz
    except ImportError:
        raise ImportError("PyMuPDF required: pip install PyMuPDF")

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    if page_num < 1 or page_num > total_pages:
        doc.close()
        raise ValueError(f"Page {page_num} out of range (1-{total_pages})")

    page = doc[page_num - 1]

    # Render at 150 DPI for good quality without huge size
    mat = fitz.Matrix(150 / 72, 150 / 72)
    pix = page.get_pixmap(matrix=mat)

    img_bytes = pix.tobytes("png")
    doc.close()

    return base64.b64encode(img_bytes).decode("utf-8")


# =============================================================================
# HIGH-LEVEL EXTRACTION FUNCTIONS
# =============================================================================

def extract_from_image_file(
    image_path: Path,
    *,
    source_tier: str = "OLYA_PRIMARY",
    content_type: str = "chart",  # "chart" or "notes"
    use_opus: bool = True,
) -> Dict:
    """Extract description from an image file.

    Args:
        image_path: Path to image file
        source_tier: Source tier for model selection
        content_type: "chart" for chart screenshots, "notes" for text-heavy notes
        use_opus: Use Opus model (default True for OLYA_PRIMARY)

    Returns:
        Vision extraction result dict
    """
    image_base64 = load_image_as_base64(image_path)

    if content_type == "notes":
        return extract_notes_description(
            image_base64,
            source_tier=source_tier,
            use_opus=use_opus,
        )
    else:
        return extract_chart_description(
            image_base64,
            source_tier=source_tier,
            use_opus=use_opus,
        )


def extract_from_pdf_page(
    pdf_path: Path,
    page_num: int,
    *,
    source_tier: str = "OLYA_PRIMARY",
    content_type: str = "auto",  # "chart", "notes", or "auto"
    use_opus: bool = True,
) -> Dict:
    """Extract description from a specific PDF page.

    Args:
        pdf_path: Path to PDF file
        page_num: Page number (1-indexed)
        source_tier: Source tier
        content_type: Content type hint ("auto" detects from page)
        use_opus: Use Opus model

    Returns:
        Vision extraction result with page provenance
    """
    image_base64 = extract_pdf_page_as_image(pdf_path, page_num)

    # Auto-detect content type based on source tier
    if content_type == "auto":
        if "notes" in str(pdf_path).lower() or "olya" in str(pdf_path).lower():
            content_type = "notes"
        else:
            content_type = "chart"

    if content_type == "notes":
        result = extract_notes_description(
            image_base64,
            source_tier=source_tier,
            use_opus=use_opus,
        )
    else:
        result = extract_chart_description(
            image_base64,
            source_tier=source_tier,
            use_opus=use_opus,
        )

    # Add provenance
    result["source_file"] = Path(pdf_path).name
    result["page_num"] = page_num
    result["provenance"] = f"page {page_num} (vision)"

    return result


def extract_all_visual_pages(
    pdf_path: Path,
    *,
    source_tier: str = "OLYA_PRIMARY",
    min_text_chars: int = 100,
    use_opus: bool = True,
) -> List[Dict]:
    """Extract descriptions from all image-heavy pages in a PDF.

    Args:
        pdf_path: Path to PDF file
        source_tier: Source tier
        min_text_chars: Threshold below which page is considered image-heavy
        use_opus: Use Opus model

    Returns:
        List of vision extraction results, one per visual page
    """
    try:
        import fitz
    except ImportError:
        raise ImportError("PyMuPDF required: pip install PyMuPDF")

    pdf_path = Path(pdf_path)
    doc = fitz.open(pdf_path)
    results = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text().strip()

        # Only process image-heavy pages
        if len(text) < min_text_chars:
            logger.info("[VISION] Processing image-heavy page %d of %s",
                       page_num + 1, pdf_path.name)
            try:
                result = extract_from_pdf_page(
                    pdf_path,
                    page_num + 1,
                    source_tier=source_tier,
                    use_opus=use_opus,
                )
                results.append(result)
            except Exception as e:
                logger.warning("[VISION] Failed to extract page %d: %s",
                              page_num + 1, e)
                results.append({
                    "description": "",
                    "source_file": pdf_path.name,
                    "page_num": page_num + 1,
                    "error": str(e),
                    "source_type": "VISUAL",
                })

    doc.close()

    logger.info("[VISION] Extracted %d visual pages from %s",
               len(results), pdf_path.name)

    return results


# =============================================================================
# THEORIST INTEGRATION (Pass 2 prep)
# =============================================================================

def format_vision_for_theorist(
    vision_result: Dict,
    surrounding_text: str = "",
) -> str:
    """Format vision extraction result for Theorist processing.

    Args:
        vision_result: Output from extract_chart_description or similar
        surrounding_text: Any text from the same page/context

    Returns:
        Formatted string ready for Theorist extraction
    """
    description = vision_result.get("description", "")
    source_file = vision_result.get("source_file", "unknown")
    page_num = vision_result.get("page_num")

    lines = []

    # Add provenance header
    if page_num:
        lines.append(f"[VISUAL CONTENT: {source_file} page {page_num}]")
    else:
        lines.append(f"[VISUAL CONTENT: {source_file}]")

    lines.append("")

    # Add surrounding text if present
    if surrounding_text.strip():
        lines.append("=== PAGE TEXT ===")
        lines.append(surrounding_text.strip())
        lines.append("")

    # Add vision description
    lines.append("=== CHART/IMAGE CONTENT ===")
    lines.append(description)
    lines.append("")

    return "\n".join(lines)


def batch_format_for_theorist(
    vision_results: List[Dict],
    page_texts: Optional[Dict[int, str]] = None,
) -> str:
    """Format multiple vision results for batch Theorist processing.

    Args:
        vision_results: List of vision extraction results
        page_texts: Optional mapping of page_num -> text content

    Returns:
        Combined formatted string
    """
    page_texts = page_texts or {}
    sections = []

    for result in vision_results:
        page_num = result.get("page_num", 0)
        surrounding_text = page_texts.get(page_num, "")
        formatted = format_vision_for_theorist(result, surrounding_text)
        sections.append(formatted)

    return "\n---\n\n".join(sections)
