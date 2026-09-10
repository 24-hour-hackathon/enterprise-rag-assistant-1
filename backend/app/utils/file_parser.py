import os
import re
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class ExtractedBlock:
    text: str
    page_number: Optional[int] = 1
    section: Optional[str] = "General"


@dataclass
class ExtractedPage:
    page_number: int
    text: str
    sections: List[ExtractedBlock] = field(default_factory=list)


@dataclass
class ExtractedDocument:
    filename: str
    file_type: str
    blocks: List[ExtractedBlock] = field(default_factory=list)
    raw_text: str = ""
    total_pages: int = 1


def _extract_pdf(file_path: str, filename: str) -> ExtractedDocument:
    """Extract text from PDF while preserving page numbers and section headers."""
    import fitz  # PyMuPDF

    doc = fitz.open(file_path)
    blocks: List[ExtractedBlock] = []
    full_text_list: List[str] = []
    total_pages = len(doc)

    for page_idx in range(total_pages):
        page = doc[page_idx]
        page_num = page_idx + 1
        page_text = page.get_text("text").strip()

        if not page_text:
            continue

        full_text_list.append(f"--- Page {page_num} ---\n{page_text}")

        # Attempt to split into paragraphs/blocks and infer section header
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", page_text) if p.strip()]
        current_section = f"Page {page_num}"

        for p in paragraphs:
            # Check if this paragraph looks like a header (short, capitalized or title case, no ending period)
            lines = [line.strip() for line in p.split("\n") if line.strip()]
            if lines and len(lines[0]) < 80 and not lines[0].endswith(".") and (lines[0].isupper() or lines[0].istitle() or lines[0].startswith("#")):
                current_section = lines[0].lstrip("#").strip()

            blocks.append(ExtractedBlock(
                text=p,
                page_number=page_num,
                section=current_section
            ))

    doc.close()

    return ExtractedDocument(
        filename=filename,
        file_type="pdf",
        blocks=blocks,
        raw_text="\n\n".join(full_text_list),
        total_pages=max(1, total_pages)
    )


def _extract_docx(file_path: str, filename: str) -> ExtractedDocument:
    """Extract text from DOCX while preserving section headings."""
    import docx

    doc = docx.Document(file_path)
    blocks: List[ExtractedBlock] = []
    full_text_list: List[str] = []
    current_section = "Introduction"
    current_page = 1
    word_count = 0

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue

        # Check for heading style
        style_name = paragraph.style.name.lower() if paragraph.style else ""
        if "heading" in style_name or "title" in style_name:
            current_section = text
        elif len(text) < 80 and (text.isupper() or text.startswith("#")):
            current_section = text.lstrip("#").strip()

        # Rough page estimate for Word docs (~500 words per page)
        words_in_para = len(text.split())
        word_count += words_in_para
        estimated_page = max(1, (word_count // 450) + 1)

        blocks.append(ExtractedBlock(
            text=text,
            page_number=estimated_page,
            section=current_section
        ))
        full_text_list.append(text)

    # Also extract tables if present
    for table in doc.tables:
        table_rows = []
        for row in table.rows:
            row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_text:
                table_rows.append(" | ".join(row_text))
        if table_rows:
            table_text = "\n".join(table_rows)
            blocks.append(ExtractedBlock(
                text=f"[Table Data]\n{table_text}",
                page_number=current_page,
                section=f"{current_section} - Table"
            ))
            full_text_list.append(table_text)

    return ExtractedDocument(
        filename=filename,
        file_type="docx",
        blocks=blocks,
        raw_text="\n\n".join(full_text_list),
        total_pages=max(1, (word_count // 450) + 1)
    )


def _extract_txt(file_path: str, filename: str) -> ExtractedDocument:
    """Extract text from TXT with multiple encoding fallbacks."""
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    content = None

    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, OSError):
            continue

    if content is None:
        with open(file_path, "rb") as f:
            content = f.read().decode("utf-8", errors="replace")

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]
    blocks: List[ExtractedBlock] = []
    current_section = "General"
    word_count = 0

    for p in paragraphs:
        lines = [l.strip() for l in p.split("\n") if l.strip()]
        if lines and len(lines[0]) < 80 and (lines[0].startswith("#") or lines[0].isupper() or lines[0].istitle() and not lines[0].endswith(".")):
            current_section = lines[0].lstrip("#").strip()

        words_in_p = len(p.split())
        word_count += words_in_p
        estimated_page = max(1, (word_count // 450) + 1)

        blocks.append(ExtractedBlock(
            text=p,
            page_number=estimated_page,
            section=current_section
        ))

    return ExtractedDocument(
        filename=filename,
        file_type="txt",
        blocks=blocks,
        raw_text=content,
        total_pages=max(1, (word_count // 450) + 1)
    )


def parse_file(file_path: str, original_filename: Optional[str] = None) -> ExtractedDocument:
    """Parse document based on its extension."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    path_obj = Path(file_path)
    extension = path_obj.suffix.lower()
    filename = original_filename if original_filename else path_obj.name

    if extension == ".pdf":
        return _extract_pdf(file_path, filename)
    elif extension in [".docx", ".doc"]:
        return _extract_docx(file_path, filename)
    elif extension in [".txt", ".md", ".text"]:
        return _extract_txt(file_path, filename)
    else:
        raise ValueError(f"Unsupported file format: {extension}. Supported formats: PDF, DOCX, TXT.")
