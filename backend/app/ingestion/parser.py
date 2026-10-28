"""Layout-aware document parser for PDFs, Markdown, TXT, and CSV files."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import BinaryIO

from app.schemas import ParsedElement


async def parse_file(file_content: bytes, filename: str) -> list[ParsedElement]:
    """
    Parse an uploaded file into structured elements, preserving layout.

    Supports: PDF, Markdown (.md), plain text (.txt), CSV (.csv)
    Uses the `unstructured` library for layout-aware extraction that preserves
    headings, tables, code blocks, and list structures.

    Args:
        file_content: Raw bytes of the uploaded file.
        filename: Original filename (used to determine file type).

    Returns:
        List of ParsedElement objects with type and content.
    """
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return await _parse_pdf(file_content, filename)
    elif ext == ".md":
        return await _parse_markdown(file_content, filename)
    elif ext == ".txt":
        return await _parse_text(file_content, filename)
    elif ext == ".csv":
        return await _parse_csv(file_content, filename)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: .pdf, .md, .txt, .csv")


async def _parse_pdf(content: bytes, filename: str) -> list[ParsedElement]:
    """Parse PDF using unstructured with layout preservation."""
    try:
        from unstructured.partition.pdf import partition_pdf

        # Write to temp file (unstructured requires file path)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            elements = partition_pdf(
                filename=tmp_path,
                strategy="auto",  # Uses OCR fallback if needed
                include_page_breaks=True,
            )
            return _convert_unstructured_elements(elements, filename)
        finally:
            os.unlink(tmp_path)

    except ImportError:
        # Fallback: treat as raw text extraction
        text = content.decode("utf-8", errors="ignore")
        return [ParsedElement(element_type="paragraph", content=text, metadata={"source": filename})]


async def _parse_markdown(content: bytes, filename: str) -> list[ParsedElement]:
    """Parse Markdown preserving heading hierarchy, code blocks, and lists."""
    text = content.decode("utf-8", errors="ignore")
    elements: list[ParsedElement] = []
    current_block: list[str] = []
    current_type = "paragraph"
    in_code_block = False
    code_lang = ""

    for line in text.split("\n"):
        # Toggle code block
        if line.strip().startswith("```"):
            if in_code_block:
                # End code block
                elements.append(ParsedElement(
                    element_type="code",
                    content="\n".join(current_block),
                    metadata={"source": filename, "language": code_lang},
                ))
                current_block = []
                in_code_block = False
                current_type = "paragraph"
            else:
                # Flush current block
                if current_block:
                    elements.append(ParsedElement(
                        element_type=current_type,
                        content="\n".join(current_block).strip(),
                        metadata={"source": filename},
                    ))
                    current_block = []
                in_code_block = True
                code_lang = line.strip().removeprefix("```").strip()
            continue

        if in_code_block:
            current_block.append(line)
            continue

        # Detect headings
        if line.startswith("#"):
            # Flush previous block
            if current_block:
                elements.append(ParsedElement(
                    element_type=current_type,
                    content="\n".join(current_block).strip(),
                    metadata={"source": filename},
                ))
                current_block = []

            level = len(line) - len(line.lstrip("#"))
            heading_text = line.lstrip("#").strip()
            elements.append(ParsedElement(
                element_type="heading",
                content=heading_text,
                metadata={"source": filename, "level": level},
            ))
            current_type = "paragraph"
            continue

        # Detect tables (lines with |)
        if "|" in line and line.strip().startswith("|"):
            if current_type != "table":
                if current_block:
                    elements.append(ParsedElement(
                        element_type=current_type,
                        content="\n".join(current_block).strip(),
                        metadata={"source": filename},
                    ))
                    current_block = []
                current_type = "table"
            current_block.append(line)
            continue

        # Detect list items
        stripped = line.strip()
        if stripped and (stripped[0] in "-*+" or (stripped[0].isdigit() and ". " in stripped[:4])):
            if current_type != "list":
                if current_block:
                    elements.append(ParsedElement(
                        element_type=current_type,
                        content="\n".join(current_block).strip(),
                        metadata={"source": filename},
                    ))
                    current_block = []
                current_type = "list"
            current_block.append(line)
            continue

        # Empty line = paragraph break
        if not stripped:
            if current_block:
                elements.append(ParsedElement(
                    element_type=current_type,
                    content="\n".join(current_block).strip(),
                    metadata={"source": filename},
                ))
                current_block = []
                current_type = "paragraph"
            continue

        # Default: paragraph text
        if current_type != "paragraph" and current_block:
            elements.append(ParsedElement(
                element_type=current_type,
                content="\n".join(current_block).strip(),
                metadata={"source": filename},
            ))
            current_block = []
            current_type = "paragraph"
        current_block.append(line)

    # Flush remaining
    if current_block:
        elements.append(ParsedElement(
            element_type=current_type,
            content="\n".join(current_block).strip(),
            metadata={"source": filename},
        ))

    return [e for e in elements if e.content.strip()]


async def _parse_text(content: bytes, filename: str) -> list[ParsedElement]:
    """Parse plain text, splitting on double newlines into paragraphs."""
    text = content.decode("utf-8", errors="ignore")
    paragraphs = text.split("\n\n")
    return [
        ParsedElement(
            element_type="paragraph",
            content=p.strip(),
            metadata={"source": filename},
        )
        for p in paragraphs
        if p.strip()
    ]


async def _parse_csv(content: bytes, filename: str) -> list[ParsedElement]:
    """Parse CSV into a table element with row-based content."""
    import csv
    import io

    text = content.decode("utf-8", errors="ignore")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)

    if not rows:
        return []

    # Convert to a readable table format
    table_content = "\n".join([", ".join(row) for row in rows])
    return [
        ParsedElement(
            element_type="table",
            content=table_content,
            metadata={
                "source": filename,
                "row_count": len(rows),
                "columns": rows[0] if rows else [],
            },
        )
    ]


def _convert_unstructured_elements(elements: list, filename: str) -> list[ParsedElement]:
    """Convert unstructured library elements to our ParsedElement schema."""
    TYPE_MAP = {
        "Title": "heading",
        "Header": "heading",
        "NarrativeText": "paragraph",
        "UncategorizedText": "paragraph",
        "ListItem": "list",
        "Table": "table",
        "FigureCaption": "paragraph",
        "PageBreak": "paragraph",
    }

    result = []
    for el in elements:
        el_type = type(el).__name__
        mapped_type = TYPE_MAP.get(el_type, "paragraph")
        text = str(el).strip()
        if text:
            metadata = {"source": filename}
            if hasattr(el, "metadata") and el.metadata:
                if hasattr(el.metadata, "page_number"):
                    metadata["page_number"] = el.metadata.page_number
            result.append(ParsedElement(
                element_type=mapped_type,
                content=text,
                metadata=metadata,
            ))

    return result
