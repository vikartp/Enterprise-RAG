"""Tests for the ingestion pipeline — parser, chunker, enricher."""

from __future__ import annotations

import pytest

from app.ingestion.chunker import chunk_elements, count_tokens
from app.ingestion.parser import parse_file
from app.schemas import ParsedElement


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

class TestParser:
    """Tests for layout-aware document parsing."""

    @pytest.mark.asyncio
    async def test_parse_markdown_headings(self):
        """Markdown parser should extract headings as separate elements."""
        content = b"# Title\n\nSome body text.\n\n## Section 2\n\nMore text here."
        elements = await parse_file(content, "test.md")

        headings = [e for e in elements if e.element_type == "heading"]
        assert len(headings) >= 2
        assert headings[0].content == "Title"
        assert headings[1].content == "Section 2"

    @pytest.mark.asyncio
    async def test_parse_markdown_code_blocks(self):
        """Markdown parser should preserve code blocks."""
        content = b"# Code Example\n\n```python\nprint('hello')\n```\n\nEnd."
        elements = await parse_file(content, "test.md")

        code_blocks = [e for e in elements if e.element_type == "code"]
        assert len(code_blocks) >= 1
        assert "print('hello')" in code_blocks[0].content

    @pytest.mark.asyncio
    async def test_parse_text_file(self):
        """Plain text parser should split on double newlines."""
        content = b"First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        elements = await parse_file(content, "test.txt")

        assert len(elements) == 3
        assert elements[0].content == "First paragraph."

    @pytest.mark.asyncio
    async def test_parse_csv(self):
        """CSV parser should create a table element."""
        content = b"name,age,city\nAlice,30,NYC\nBob,25,LA"
        elements = await parse_file(content, "test.csv")

        assert len(elements) == 1
        assert elements[0].element_type == "table"

    @pytest.mark.asyncio
    async def test_unsupported_file_type(self):
        """Parser should reject unsupported file types."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            await parse_file(b"data", "test.docx")


# ---------------------------------------------------------------------------
# Chunker tests
# ---------------------------------------------------------------------------

class TestChunker:
    """Tests for structure-aware chunking."""

    @pytest.mark.asyncio
    async def test_basic_chunking(self):
        """Chunker should create chunks from parsed elements."""
        elements = [
            ParsedElement(element_type="heading", content="Section A", metadata={}),
            ParsedElement(element_type="paragraph", content="Body text for section A.", metadata={}),
        ]
        chunks = await chunk_elements(elements, "test.md")
        assert len(chunks) >= 1
        assert chunks[0].source_file == "test.md"
        assert chunks[0].section_header == "Section A"

    @pytest.mark.asyncio
    async def test_chunk_preserves_headers(self):
        """Chunks should include their section header for context."""
        elements = [
            ParsedElement(element_type="heading", content="API Reference", metadata={}),
            ParsedElement(element_type="paragraph", content="The API supports REST endpoints.", metadata={}),
        ]
        chunks = await chunk_elements(elements, "docs.md")

        assert any("API Reference" in c.content for c in chunks)

    @pytest.mark.asyncio
    async def test_chunk_ids_are_deterministic(self):
        """Same input should produce same chunk IDs."""
        elements = [
            ParsedElement(element_type="paragraph", content="Deterministic content.", metadata={}),
        ]
        chunks1 = await chunk_elements(elements, "test.md")
        chunks2 = await chunk_elements(elements, "test.md")
        assert chunks1[0].chunk_id == chunks2[0].chunk_id

    def test_token_counting(self):
        """Token counter should return reasonable counts."""
        count = count_tokens("Hello, world!")
        assert count > 0
        assert count < 10


# ---------------------------------------------------------------------------
# Enricher tests (mocked — requires OpenAI API key)
# ---------------------------------------------------------------------------

class TestEnricher:
    """Tests for chunk enrichment (structure only, LLM calls mocked)."""

    @pytest.mark.asyncio
    async def test_enriched_chunk_structure(self):
        """EnrichedChunk should have all required fields."""
        from app.schemas import EnrichedChunk

        chunk = EnrichedChunk(
            chunk_id="test-123",
            content="Test content",
            chunk_index=0,
            source_file="test.md",
            summary="A test chunk",
            keywords=["test", "content"],
            hypothetical_questions=["What is this?"],
        )

        assert chunk.chunk_id == "test-123"
        assert len(chunk.keywords) == 2
        assert len(chunk.hypothetical_questions) == 1
