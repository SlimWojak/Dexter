# Document ingestion skills — P3 Source Ingestion Pipeline

from skills.document.pdf_ingester import (
    ingest_pdf,
    ingest_pdf_directory,
    extract_text_from_pdf,
    chunk_pdf_text,
    determine_source_tier as pdf_determine_source_tier,
)

from skills.document.md_ingester import (
    ingest_markdown,
    parse_markdown_sections,
    chunk_markdown,
    determine_source_tier as md_determine_source_tier,
)

from skills.document.vision_extractor import (
    extract_chart_description,
    extract_notes_description,
    extract_from_image_file,
    extract_from_pdf_page,
    extract_all_visual_pages,
    format_vision_for_theorist,
    batch_format_for_theorist,
)

__all__ = [
    # PDF
    "ingest_pdf",
    "ingest_pdf_directory",
    "extract_text_from_pdf",
    "chunk_pdf_text",
    "pdf_determine_source_tier",
    # Markdown
    "ingest_markdown",
    "parse_markdown_sections",
    "chunk_markdown",
    "md_determine_source_tier",
    # Vision (P3.5)
    "extract_chart_description",
    "extract_notes_description",
    "extract_from_image_file",
    "extract_from_pdf_page",
    "extract_all_visual_pages",
    "format_vision_for_theorist",
    "batch_format_for_theorist",
]
