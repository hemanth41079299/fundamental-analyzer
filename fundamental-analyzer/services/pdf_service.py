"""PDF file persistence and text extraction services."""

from __future__ import annotations

from pathlib import Path

import fitz

from core.validators import validate_pdf_text
from services.upload_security_service import save_secure_uploaded_file


def save_uploaded_file(uploaded_file) -> Path:
    """Persist an uploaded PDF using secure user-scoped storage."""
    return save_secure_uploaded_file(uploaded_file)


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from a PDF using PyMuPDF."""
    try:
        document = fitz.open(pdf_path)
    except Exception as exc:  # pragma: no cover - library specific
        raise ValueError("Unable to read the uploaded PDF file.") from exc

    text_parts: list[str] = []
    with document:
        for page in document:
            text_parts.append(page.get_text("text"))

    extracted_text = "\n".join(text_parts)
    is_valid, message = validate_pdf_text(extracted_text)
    if not is_valid:
        raise ValueError(message)
    return extracted_text
