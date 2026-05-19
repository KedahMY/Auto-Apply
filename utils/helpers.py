import re
import os
from docx import Document


_UNSAFE_CHARS = r'/\\:?*|<>"'


def sanitize_filename(s: str) -> str:
    for ch in _UNSAFE_CHARS:
        s = s.replace(ch, "_")
    return s.strip()


def extract_docx_text(path: str) -> str:
    """Return the full text of a DOCX file with basic structure preserved."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"CV file not found: {path}")
    doc = Document(path)
    lines = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            lines.append(text)
    return "\n".join(lines)


def read_text_file(path: str) -> str:
    """Read a plain-text or markdown file and return its contents."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data lake file not found: {path}")
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def clean_text(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).replace("\xa0", " ").strip()


def parse_page_input(page_input: str) -> list[int]:
    """Parse a page string like '3' or '1-5' into a list of page numbers."""
    page_input = page_input.strip()
    if "-" in page_input:
        start_str, end_str = page_input.split("-", 1)
        start, end = int(start_str.strip()), int(end_str.strip())
        if start < 1:
            raise ValueError("Start page must be at least 1.")
        if start > end:
            raise ValueError("Start page must be <= end page.")
        return list(range(start, end + 1))
    else:
        n = int(page_input)
        if n < 1:
            raise ValueError("Page number must be at least 1.")
        return [n]
