"""Validation helpers for uploaded PDF files and extracted text."""

from __future__ import annotations

from pathlib import Path

from config.settings import SUPPORTED_FILE_EXTENSIONS


def validate_pdf_file(filename: str) -> tuple[bool, str]:
    """Validate upload file extension."""
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_FILE_EXTENSIONS:
        return False, "Unsupported file type. Please upload a PDF file."
    return True, ""


def validate_pdf_text(text: str) -> tuple[bool, str]:
    """Validate that the extracted PDF text is usable for analysis."""
    stripped = text.strip()
    if not stripped:
        return False, "The PDF appears unreadable or contains no extractable text."
    if len(stripped) < 50:
        return False, "The PDF text is too limited for analysis. It may be a scanned image PDF."
    return True, ""
