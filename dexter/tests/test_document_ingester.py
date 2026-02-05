"""Tests for Document Ingestion (P3.1).

Tests cover:
- PDF text extraction
- PDF chunking
- Markdown parsing and chunking
- Source tier detection
- Theorist formatting
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skills.document.md_ingester import (
    parse_markdown_sections,
    chunk_markdown,
    ingest_markdown,
    determine_source_tier as md_determine_tier,
    format_chunks_for_theorist as md_format,
)


class TestMarkdownParsing(unittest.TestCase):
    """Markdown section parsing tests."""

    def test_parse_single_section(self):
        content = "# Title\n\nSome content here."
        sections = parse_markdown_sections(content)
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0]["title"], "Title")
        self.assertEqual(sections[0]["level"], 1)
        self.assertIn("Some content", sections[0]["content"])

    def test_parse_multiple_sections(self):
        content = """# First
Content 1

## Second
Content 2

### Third
Content 3
"""
        sections = parse_markdown_sections(content)
        self.assertEqual(len(sections), 3)
        self.assertEqual(sections[0]["title"], "First")
        self.assertEqual(sections[1]["title"], "Second")
        self.assertEqual(sections[2]["title"], "Third")
        self.assertEqual(sections[0]["level"], 1)
        self.assertEqual(sections[1]["level"], 2)
        self.assertEqual(sections[2]["level"], 3)

    def test_parse_no_headers(self):
        content = "Just plain text without any headers."
        sections = parse_markdown_sections(content)
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0]["level"], 0)

    def test_nested_content_preserved(self):
        content = """# Main

Some intro.

## Sub

- List item 1
- List item 2

```python
code here
```
"""
        sections = parse_markdown_sections(content)
        self.assertEqual(len(sections), 2)
        self.assertIn("List item 1", sections[1]["content"])
        self.assertIn("code here", sections[1]["content"])


class TestMarkdownChunking(unittest.TestCase):
    """Markdown chunking tests."""

    def test_small_content_single_chunk(self):
        content = "# Title\n\nShort content."
        chunks = chunk_markdown(content, chunk_size=1000)
        self.assertEqual(len(chunks), 1)

    def test_large_content_multiple_chunks(self):
        # P3.4d: With section-based chunking, need paragraphs for splits
        # Create content with multiple paragraphs that exceed MAX_SECTION_SIZE
        content = "# Title\n\n" + "\n\n".join([f"Paragraph {i}. " + "A" * 1000 for i in range(25)])
        chunks = chunk_markdown(content, chunk_size=8000, overlap=100)
        self.assertGreater(len(chunks), 1)

    def test_sections_preserved(self):
        content = """# Section 1
Short content.

# Section 2
More content.
"""
        chunks = chunk_markdown(content, chunk_size=5000, preserve_sections=True)
        # With high chunk size, should be single chunk
        self.assertGreaterEqual(len(chunks), 1)


class TestMarkdownIngestion(unittest.TestCase):
    """Full markdown ingestion tests."""

    def test_ingest_creates_chunks(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test Doc\n\nThis is test content for ingestion.")
            f.flush()

            try:
                result = ingest_markdown(Path(f.name))
                self.assertEqual(result["source_type"], "markdown")
                self.assertGreater(len(result["chunks"]), 0)
                self.assertIn("source_tier", result)
            finally:
                os.unlink(f.name)

    def test_chunks_have_metadata(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Header\n\nContent here.")
            f.flush()

            try:
                result = ingest_markdown(Path(f.name), source_tier="CANON")
                chunk = result["chunks"][0]
                self.assertEqual(chunk["source_type"], "markdown")
                self.assertEqual(chunk["source_tier"], "CANON")
                self.assertIn("text", chunk)
                self.assertIn("provenance", chunk)
            finally:
                os.unlink(f.name)


class TestSourceTierDetection(unittest.TestCase):
    """Source tier detection tests."""

    def test_layer_0_is_canon(self):
        path = Path("/data/sources/layer_0/doc.md")
        self.assertEqual(md_determine_tier(path), "CANON")

    def test_5_drawer_is_canon(self):
        path = Path("/data/sources/5_drawer_YAML_files/foundation.yaml")
        self.assertEqual(md_determine_tier(path), "CANON")

    def test_olya_notes_is_primary(self):
        path = Path("/data/sources/olya_notes/note.pdf")
        self.assertEqual(md_determine_tier(path), "OLYA_PRIMARY")

    def test_blessed_is_lateral(self):
        path = Path("/data/sources/blessed_training/lesson.pdf")
        # blessed_training not in md_determine_tier, so LATERAL
        # (pdf_ingester has more specific detection)
        self.assertIn(md_determine_tier(path), ["LATERAL", "CANON"])


class TestTheoristFormatting(unittest.TestCase):
    """Theorist formatting tests."""

    def test_format_includes_provenance(self):
        chunks = [
            {
                "chunk_num": 1,
                "text": "Test content",
                "source_file": "test.md",
                "source_tier": "CANON",
                "provenance": "section: Intro",
            }
        ]
        formatted = md_format(chunks)
        self.assertIn("[section: Intro]", formatted)
        self.assertIn("[CANON]", formatted)
        self.assertIn("test.md", formatted)
        self.assertIn("Test content", formatted)

    def test_format_multiple_chunks(self):
        chunks = [
            {"chunk_num": 1, "text": "First", "source_file": "a.md", "source_tier": "CANON", "provenance": "chunk 1"},
            {"chunk_num": 2, "text": "Second", "source_file": "a.md", "source_tier": "CANON", "provenance": "chunk 2"},
        ]
        formatted = md_format(chunks)
        self.assertIn("First", formatted)
        self.assertIn("Second", formatted)


class TestPDFIngester(unittest.TestCase):
    """PDF ingester tests (require PyMuPDF)."""

    @classmethod
    def setUpClass(cls):
        """Check if PyMuPDF is available."""
        try:
            import fitz
            cls.fitz_available = True
        except ImportError:
            cls.fitz_available = False

    def test_pdf_tier_detection(self):
        if not self.fitz_available:
            self.skipTest("PyMuPDF not installed")

        from skills.document.pdf_ingester import determine_source_tier

        # Test olya_notes detection
        path = Path("/data/sources/olya_notes/note.pdf")
        self.assertEqual(determine_source_tier(path), "OLYA_PRIMARY")

        # Test blessed detection
        path = Path("/data/sources/blessed_training/lesson.pdf")
        self.assertEqual(determine_source_tier(path), "LATERAL")

    def test_chunk_pdf_text(self):
        if not self.fitz_available:
            self.skipTest("PyMuPDF not installed")

        from skills.document.pdf_ingester import chunk_pdf_text

        # P3.4d: Page-based chunking requires pages data
        pages = [
            {"page_num": 1, "text": "A" * 5000, "char_count": 5000},
            {"page_num": 2, "text": "B" * 5000, "char_count": 5000},
            {"page_num": 3, "text": "C" * 5000, "char_count": 5000},
        ]
        extracted = {
            "full_text": "".join(p["text"] for p in pages),
            "pages": pages,
        }
        chunks = chunk_pdf_text(extracted)
        self.assertGreater(len(chunks), 0)
        self.assertIn("text", chunks[0])
        self.assertIn("chunk_num", chunks[0])


class TestRealSourceFiles(unittest.TestCase):
    """Test against actual source files if available."""

    SOURCES_DIR = Path(__file__).resolve().parent.parent / "data" / "sources"

    def test_layer_0_ingestion(self):
        layer_0_dir = self.SOURCES_DIR / "layer_0"
        if not layer_0_dir.exists():
            self.skipTest("layer_0 directory not found")

        md_files = list(layer_0_dir.glob("*.md"))
        if not md_files:
            self.skipTest("No MD files in layer_0")

        result = ingest_markdown(md_files[0])
        self.assertEqual(result["source_tier"], "CANON")
        self.assertGreater(len(result["chunks"]), 0)
        # Layer 0 is large, should have multiple chunks
        self.assertGreater(len(result["chunks"]), 5)

    def test_blessed_pdf_ingestion(self):
        try:
            import fitz
        except ImportError:
            self.skipTest("PyMuPDF not installed")

        from skills.document.pdf_ingester import ingest_pdf

        blessed_dir = self.SOURCES_DIR / "blessed_training"
        if not blessed_dir.exists():
            self.skipTest("blessed_training directory not found")

        pdf_files = list(blessed_dir.glob("*.pdf"))
        if not pdf_files:
            self.skipTest("No PDF files in blessed_training")

        result = ingest_pdf(pdf_files[0])
        self.assertEqual(result["source_tier"], "LATERAL")
        self.assertIn("chunks", result)
        self.assertIn("total_pages", result)

    def test_olya_notes_ingestion(self):
        try:
            import fitz
        except ImportError:
            self.skipTest("PyMuPDF not installed")

        from skills.document.pdf_ingester import ingest_pdf

        olya_dir = self.SOURCES_DIR / "olya_notes"
        if not olya_dir.exists():
            self.skipTest("olya_notes directory not found")

        pdf_files = list(olya_dir.glob("*.pdf"))
        if not pdf_files:
            self.skipTest("No PDF files in olya_notes")

        result = ingest_pdf(pdf_files[0])
        self.assertEqual(result["source_tier"], "OLYA_PRIMARY")
        self.assertIn("image_heavy_pages", result)


class TestP34dChunkingOptimization(unittest.TestCase):
    """P3.4d: Test chunking produces fewer, larger chunks for documents."""

    def test_pdf_page_based_chunking_fewer_chunks(self):
        """PDF page-based chunking should produce fewer chunks than char-based."""
        try:
            import fitz
        except ImportError:
            self.skipTest("PyMuPDF not installed")

        from skills.document.pdf_ingester import chunk_pdf_text

        # Simulate a 20-page document with 500 chars per page
        pages = [{"page_num": i + 1, "text": f"Page {i + 1} content. " * 30, "char_count": 500}
                 for i in range(20)]
        extracted = {
            "full_text": "\n\n".join(p["text"] for p in pages),
            "pages": pages,
        }

        # Page-based chunking (default)
        page_chunks = chunk_pdf_text(extracted, use_page_chunking=True)

        # Legacy char-based chunking (2000 char, 400 overlap)
        legacy_chunks = chunk_pdf_text(extracted, chunk_size=2000, overlap=400, use_page_chunking=False)

        # Page-based should produce FEWER chunks
        self.assertLess(
            len(page_chunks), len(legacy_chunks),
            f"Page-based ({len(page_chunks)}) should produce fewer chunks than legacy ({len(legacy_chunks)})"
        )

        # Page-based chunks should be LARGER on average
        avg_page = sum(len(c["text"]) for c in page_chunks) / len(page_chunks) if page_chunks else 0
        avg_legacy = sum(len(c["text"]) for c in legacy_chunks) / len(legacy_chunks) if legacy_chunks else 0
        self.assertGreater(avg_page, avg_legacy)

    def test_pdf_chunk_size_in_expected_range(self):
        """PDF chunks should be in 8-16k char range."""
        try:
            import fitz
        except ImportError:
            self.skipTest("PyMuPDF not installed")

        from skills.document.pdf_ingester import chunk_pdf_by_pages, MIN_CHUNK_SIZE, MAX_CHUNK_SIZE

        # Simulate a document with varying page sizes
        pages = [
            {"page_num": 1, "text": "A" * 3000, "char_count": 3000},
            {"page_num": 2, "text": "B" * 4000, "char_count": 4000},
            {"page_num": 3, "text": "C" * 5000, "char_count": 5000},
            {"page_num": 4, "text": "D" * 2000, "char_count": 2000},
        ]
        extracted = {"pages": pages}

        chunks = chunk_pdf_by_pages(extracted)

        # All chunks should be within bounds (except maybe last one)
        for chunk in chunks[:-1]:
            chunk_size = len(chunk["text"])
            self.assertGreaterEqual(chunk_size, MIN_CHUNK_SIZE * 0.5,
                                   f"Chunk too small: {chunk_size} < {MIN_CHUNK_SIZE * 0.5}")

    def test_markdown_section_based_chunking(self):
        """Markdown should chunk by sections, not arbitrary char windows."""
        content = """# Introduction
Short intro.

## Section A
This is section A with moderate content.
It has multiple paragraphs.

And some more text here.

## Section B
Section B content is also here.

## Section C
Final section.
"""
        from skills.document.md_ingester import chunk_markdown

        chunks = chunk_markdown(content, chunk_size=12000, preserve_sections=True)

        # With large chunk size, small sections should combine
        # Should produce 1-2 chunks, not many small ones
        self.assertLessEqual(len(chunks), 2, f"Too many chunks: {len(chunks)}")

        # Each chunk should have section info
        for chunk in chunks:
            self.assertIn("section", chunk)

    def test_large_section_gets_split(self):
        """Very large sections should be split at paragraphs."""
        # Create a section with 20k chars
        large_content = """# Large Section

""" + "\n\n".join([f"Paragraph {i}. " + "X" * 800 for i in range(25)])

        from skills.document.md_ingester import chunk_markdown, MAX_SECTION_SIZE

        chunks = chunk_markdown(large_content, chunk_size=MAX_SECTION_SIZE)

        # Should produce multiple chunks
        self.assertGreater(len(chunks), 1, "Large section should be split")

        # Each chunk should be under max
        for chunk in chunks:
            self.assertLessEqual(len(chunk["text"]), MAX_SECTION_SIZE * 1.2,
                                f"Chunk too large: {len(chunk['text'])}")

    def test_layer_0_reference_not_in_pending(self):
        """Layer 0 should be marked as REFERENCE with 0 pending."""
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

        # Import after path fix
        from run_source_extraction import SOURCE_CONFIGS

        layer_0_config = SOURCE_CONFIGS.get("layer_0", {})
        self.assertEqual(layer_0_config.get("type"), "reference")
        self.assertEqual(layer_0_config.get("role"), "REFERENCE")


if __name__ == "__main__":
    unittest.main()
