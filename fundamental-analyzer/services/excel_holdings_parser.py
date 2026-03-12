"""Excel holdings parser with normalized output columns."""

from __future__ import annotations

import pandas as pd

from services.csv_holdings_parser import normalize_holdings_frame


def parse_holdings_excel(file, sheet_name: str | int | None = 0) -> pd.DataFrame:
    """Read and normalize an Excel holdings file."""
    try:
        frame = pd.read_excel(file, sheet_name=sheet_name)
    except ImportError as exc:
        raise ValueError("Excel parsing requires openpyxl. Install dependencies from requirements.txt.") from exc
    except Exception as exc:
        raise ValueError("Unable to read the holdings Excel file.") from exc

    if isinstance(frame, dict):
        if not frame:
            raise ValueError("The Excel file does not contain any readable sheets.")
        frame = next(iter(frame.values()))

    return normalize_holdings_frame(frame)
