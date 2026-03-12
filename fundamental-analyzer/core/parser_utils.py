"""Utilities for cleaning PDF text and extracting label-based values."""

from __future__ import annotations

import re
from typing import Iterable


def clean_text(text: str) -> str:
    """Normalize extracted PDF text while preserving line boundaries."""
    compact = text.replace("\u00a0", " ").replace("\t", " ")
    compact = re.sub(r"[|]+", " ", compact)
    compact = compact.replace("\r\n", "\n").replace("\r", "\n")
    cleaned_lines = [re.sub(r"\s+", " ", line).strip() for line in compact.splitlines()]
    return "\n".join(line for line in cleaned_lines if line)


def normalize_label(label: str) -> str:
    """Normalize label text for robust pattern building."""
    normalized = label.lower().strip()
    normalized = normalized.replace("%", " percent ")
    normalized = normalized.replace("/", " ")
    normalized = re.sub(r"[^a-z0-9 ]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def parse_numeric_value(raw_value: str | None) -> float | None:
    """Parse a numeric value from messy PDF text."""
    if raw_value is None:
        return None

    cleaned = raw_value.strip().lower()
    if cleaned in {"", "na", "n/a", "none", "-", "--", "not available"}:
        return None

    negative = cleaned.startswith("(") and cleaned.endswith(")")
    if negative:
        cleaned = cleaned[1:-1]

    cleaned = cleaned.replace(",", "")
    cleaned = cleaned.replace("rs.", "").replace("rs", "")
    cleaned = cleaned.replace("crore", "").replace("cr", "")
    cleaned = cleaned.replace("%", "")
    cleaned = cleaned.strip()

    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None

    value = float(match.group(0))
    return -value if negative else value


def extract_labeled_value(text: str, labels: Iterable[str], window: int = 80) -> str | None:
    """Extract the text immediately following a known label."""
    for label in labels:
        normalized_label = normalize_label(label)
        if not normalized_label:
            continue

        words = normalized_label.split()
        label_pattern = r"\b" + r"\W*".join(re.escape(word) for word in words) + r"\b"
        pattern = rf"(?im){label_pattern}\s*[:\-]?\s*([^\n]{{1,{window}}})"
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None


def extract_company_name(text: str) -> str | None:
    """Extract a company name using a label-first strategy."""
    patterns = [
        r"(?im)company name\s*[:\-]?\s*([A-Za-z0-9&.,()\- ]{3,80})$",
        r"(?im)name of company\s*[:\-]?\s*([A-Za-z0-9&.,()\- ]{3,80})$",
        r"(?im)^([A-Za-z0-9&.,()\- ]{3,80})\s+company overview$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip(" -:")
    return None
