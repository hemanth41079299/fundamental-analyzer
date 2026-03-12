"""Best-effort PDF holdings parser."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

from services.csv_holdings_parser import NORMALIZED_HOLDINGS_COLUMNS, normalize_holdings_frame, safe_parse_number

try:  # pragma: no cover - depends on local environment
    import fitz
except ModuleNotFoundError:  # pragma: no cover - depends on local environment
    fitz = None  # type: ignore[assignment]

_TICKER_PATTERN = re.compile(r"\b[A-Z0-9][A-Z0-9.\-]{1,20}\b")


def _require_pymupdf() -> None:
    """Ensure PyMuPDF is installed before parsing PDFs."""
    if fitz is None:
        raise ValueError("PyMuPDF is not installed. Run: pip install -r requirements.txt")


def _read_pdf_bytes(file_or_path: Any) -> bytes:
    """Return raw PDF bytes from a path or file-like object."""
    if isinstance(file_or_path, (str, Path)):
        return Path(file_or_path).read_bytes()
    if hasattr(file_or_path, "getvalue"):
        return bytes(file_or_path.getvalue())
    if hasattr(file_or_path, "read"):
        if hasattr(file_or_path, "seek"):
            file_or_path.seek(0)
        payload = file_or_path.read()
        if hasattr(file_or_path, "seek"):
            file_or_path.seek(0)
        return bytes(payload)
    raise ValueError("Unsupported PDF input.")


def _extract_pdf_lines(file_or_path: Any) -> list[str]:
    """Extract cleaned text lines from a PDF."""
    _require_pymupdf()
    payload = _read_pdf_bytes(file_or_path)
    document = fitz.open(stream=payload, filetype="pdf")
    lines: list[str] = []
    for page in document:
        text = page.get_text("text")
        for raw_line in text.splitlines():
            cleaned = re.sub(r"\s+", " ", raw_line).strip()
            if cleaned:
                lines.append(cleaned)
    return lines


def _split_line_to_fields(line: str) -> list[str]:
    """Split a PDF line using common table delimiters."""
    fields = [field.strip() for field in re.split(r"\s{2,}|\t|\|", line) if field.strip()]
    if len(fields) > 1:
        return fields
    return line.split()


def _extract_ticker_and_name(fields: list[str]) -> tuple[str | None, str | None, int]:
    """Extract ticker and company tokens from the start of a PDF row."""
    numeric_index = next((index for index, value in enumerate(fields) if safe_parse_number(value) is not None), len(fields))
    prefix = fields[:numeric_index]
    ticker = None
    for token in reversed(prefix):
        if _TICKER_PATTERN.fullmatch(token.upper()):
            ticker = token.upper()
            break

    company_tokens = [token for token in prefix if token.upper() != ticker]
    company_name = " ".join(company_tokens).strip() or None
    return ticker, company_name, numeric_index


def _build_row_from_numeric_fields(ticker: str | None, company_name: str | None, numeric_fields: list[str]) -> dict[str, Any] | None:
    """Map trailing numeric fields to the normalized schema."""
    numbers = [safe_parse_number(field) for field in numeric_fields]
    numbers = [value for value in numbers if value is not None]
    if len(numbers) < 2:
        return None

    row: dict[str, Any] = {column: None for column in NORMALIZED_HOLDINGS_COLUMNS}
    row["ticker"] = ticker
    row["company_name"] = company_name

    if len(numbers) >= 7:
        row["quantity"], row["avg_buy"], row["buy_value"], row["ltp"], row["present_value"], row["pnl"], row["pnl_pct"] = numbers[:7]
    elif len(numbers) == 6:
        row["quantity"], row["avg_buy"], row["buy_value"], row["ltp"], row["present_value"], row["pnl"] = numbers
    elif len(numbers) == 5:
        row["quantity"], row["avg_buy"], row["ltp"], row["present_value"], row["pnl"] = numbers
    elif len(numbers) == 4:
        row["quantity"], row["avg_buy"], row["ltp"], row["present_value"] = numbers
    else:
        row["quantity"], row["ltp"] = numbers[:2]

    return row


def _parse_table_like_lines(lines: list[str]) -> pd.DataFrame:
    """Parse holdings rows from text lines that resemble portfolio tables."""
    rows: list[dict[str, Any]] = []
    for line in lines:
        lowered = line.lower()
        if "holding" in lowered and "quantity" in lowered:
            continue
        if "total" in lowered and "value" in lowered:
            continue

        fields = _split_line_to_fields(line)
        ticker, company_name, numeric_start = _extract_ticker_and_name(fields)
        numeric_fields = fields[numeric_start:]
        row = _build_row_from_numeric_fields(ticker, company_name, numeric_fields)
        if row is None:
            continue
        rows.append(row)

    if not rows:
        return pd.DataFrame(columns=NORMALIZED_HOLDINGS_COLUMNS)
    return pd.DataFrame(rows)


def parse_holdings_pdf(file_or_path: Any) -> pd.DataFrame:
    """Parse a holdings-style PDF using a best-effort text/table strategy."""
    lines = _extract_pdf_lines(file_or_path)
    if not lines:
        raise ValueError("The PDF does not contain readable text.")

    parsed = _parse_table_like_lines(lines)
    if parsed.empty:
        raise ValueError("Unable to identify holdings rows in the PDF.")

    normalized = normalize_holdings_frame(parsed)
    if normalized.empty:
        raise ValueError("The PDF could not be normalized into holdings data.")
    return normalized
