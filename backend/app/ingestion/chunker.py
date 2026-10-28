"""Structure-aware chunking that respects document boundaries."""

from __future__ import annotations

import hashlib
import uuid

import tiktoken

from app.config import get_settings
from app.schemas import ChunkData, ParsedElement


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """Count tokens in text using tiktoken."""
    try:
        enc = tiktoken.get_encoding(model)
    except Exception:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def generate_chunk_id(content: str, source: str, index: int) -> str:
    """Generate a deterministic chunk ID from content hash."""
    hash_input = f"{source}::{index}::{content[:200]}"
    return hashlib.sha256(hash_input.encode()).hexdigest()[:16]


async def chunk_elements(
    elements: list[ParsedElement],
    source_file: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[ChunkData]:
    """
    Perform structure-aware chunking on parsed document elements.

    Strategy:
    1. Group elements under their nearest heading (section-aware).
    2. Within each section, accumulate text until the token limit.
    3. Headings are always prepended to their body chunks for context.
    4. Tables, code blocks, and lists are kept intact when possible.

    Args:
        elements: Parsed document elements from the parser.
        source_file: Original filename.
        chunk_size: Max tokens per chunk (default from settings).
        chunk_overlap: Token overlap between chunks (default from settings).

    Returns:
        List of ChunkData objects ready for enrichment.
    """
    settings = get_settings()
    max_tokens = chunk_size or settings.chunk_size
    overlap = chunk_overlap or settings.chunk_overlap

    # Phase 1: Group elements into sections
    sections = _group_into_sections(elements)

    # Phase 2: Chunk each section
    chunks: list[ChunkData] = []
    chunk_index = 0

    for section_header, section_elements in sections:
        section_chunks = _chunk_section(
            section_header=section_header,
            elements=section_elements,
            max_tokens=max_tokens,
            overlap=overlap,
        )

        for chunk_text in section_chunks:
            chunk_id = generate_chunk_id(chunk_text, source_file, chunk_index)
            chunks.append(ChunkData(
                chunk_id=chunk_id,
                content=chunk_text,
                chunk_index=chunk_index,
                source_file=source_file,
                section_header=section_header,
                token_count=count_tokens(chunk_text),
            ))
            chunk_index += 1

    return chunks


def _group_into_sections(elements: list[ParsedElement]) -> list[tuple[str | None, list[ParsedElement]]]:
    """Group elements under their nearest heading."""
    sections: list[tuple[str | None, list[ParsedElement]]] = []
    current_header: str | None = None
    current_elements: list[ParsedElement] = []

    for el in elements:
        if el.element_type == "heading":
            # Start a new section
            if current_elements:
                sections.append((current_header, current_elements))
            current_header = el.content
            current_elements = []
        else:
            current_elements.append(el)

    # Don't forget the last section
    if current_elements:
        sections.append((current_header, current_elements))

    # If no sections were created (no headings), create one from all elements
    if not sections and elements:
        sections = [(None, elements)]

    return sections


def _chunk_section(
    section_header: str | None,
    elements: list[ParsedElement],
    max_tokens: int,
    overlap: int,
) -> list[str]:
    """
    Chunk a section's elements, keeping the header prepended for context.

    Special elements (tables, code) are kept whole if they fit; otherwise,
    they're split by lines.
    """
    header_prefix = f"## {section_header}\n\n" if section_header else ""
    header_tokens = count_tokens(header_prefix) if header_prefix else 0
    available_tokens = max_tokens - header_tokens

    chunks: list[str] = []
    current_texts: list[str] = []
    current_tokens = 0

    for el in elements:
        el_text = el.content.strip()
        if not el_text:
            continue

        el_tokens = count_tokens(el_text)

        # If a single element exceeds the limit, split it
        if el_tokens > available_tokens:
            # Flush current accumulation
            if current_texts:
                chunk_body = "\n\n".join(current_texts)
                chunks.append(f"{header_prefix}{chunk_body}")
                current_texts = []
                current_tokens = 0

            # Split large element by lines
            sub_chunks = _split_large_text(el_text, available_tokens, overlap)
            for sc in sub_chunks:
                chunks.append(f"{header_prefix}{sc}")
            continue

        # Check if adding this element would exceed the limit
        if current_tokens + el_tokens > available_tokens:
            # Flush and start new chunk
            chunk_body = "\n\n".join(current_texts)
            chunks.append(f"{header_prefix}{chunk_body}")

            # Calculate overlap: keep last N tokens worth of text
            overlap_text = _get_overlap_text(current_texts, overlap)
            current_texts = [overlap_text] if overlap_text else []
            current_tokens = count_tokens(overlap_text) if overlap_text else 0

        current_texts.append(el_text)
        current_tokens += el_tokens

    # Flush remaining
    if current_texts:
        chunk_body = "\n\n".join(current_texts)
        chunks.append(f"{header_prefix}{chunk_body}")

    return chunks


def _split_large_text(text: str, max_tokens: int, overlap: int) -> list[str]:
    """Split text that exceeds max_tokens by sentences/lines."""
    lines = text.split("\n")
    chunks: list[str] = []
    current_lines: list[str] = []
    current_tokens = 0

    for line in lines:
        line_tokens = count_tokens(line)
        if current_tokens + line_tokens > max_tokens and current_lines:
            chunks.append("\n".join(current_lines))
            # Keep overlap
            overlap_lines = []
            overlap_tokens = 0
            for prev_line in reversed(current_lines):
                lt = count_tokens(prev_line)
                if overlap_tokens + lt > overlap:
                    break
                overlap_lines.insert(0, prev_line)
                overlap_tokens += lt
            current_lines = overlap_lines
            current_tokens = overlap_tokens
        current_lines.append(line)
        current_tokens += line_tokens

    if current_lines:
        chunks.append("\n".join(current_lines))

    return chunks


def _get_overlap_text(texts: list[str], overlap_tokens: int) -> str:
    """Get the tail of accumulated texts to use as overlap."""
    if not texts or overlap_tokens <= 0:
        return ""

    result_parts: list[str] = []
    total = 0
    for text in reversed(texts):
        tokens = count_tokens(text)
        if total + tokens > overlap_tokens:
            break
        result_parts.insert(0, text)
        total += tokens

    return "\n\n".join(result_parts)
