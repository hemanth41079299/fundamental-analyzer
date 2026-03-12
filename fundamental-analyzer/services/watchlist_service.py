"""Watchlist management services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from io import StringIO

import pandas as pd

from services.auth_service import require_current_user_id
from services.db import get_connection


@dataclass
class WatchlistInput:
    """Validated watchlist payload."""

    ticker: str
    company_name: str
    notes: str = ""


def _normalize_ticker(ticker: str) -> str:
    """Normalize ticker values."""
    return ticker.strip().upper()


def add_watchlist_item(payload: WatchlistInput) -> None:
    """Add a watchlist item, preventing duplicates."""
    user_id = require_current_user_id()
    ticker = _normalize_ticker(payload.ticker)
    if not ticker:
        raise ValueError("Ticker is required.")

    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM watchlist WHERE user_id = %s AND ticker = %s",
            (user_id, ticker),
        ).fetchone()
        if existing is not None:
            raise ValueError("This ticker already exists in the watchlist.")

        connection.execute(
            """
            INSERT INTO watchlist (user_id, ticker, company_name, added_on, notes)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, ticker, payload.company_name.strip(), date.today().isoformat(), payload.notes.strip()),
        )
        connection.commit()


def get_watchlist() -> pd.DataFrame:
    """Return watchlist items."""
    user_id = require_current_user_id()
    with get_connection() as connection:
        frame = pd.read_sql_query(
            "SELECT * FROM watchlist WHERE user_id = %s ORDER BY added_on DESC, id DESC",
            connection,
            params=(user_id,),
        )
    return frame


def remove_watchlist_item(watchlist_id: int) -> None:
    """Remove an item from the watchlist."""
    user_id = require_current_user_id()
    with get_connection() as connection:
        connection.execute("DELETE FROM watchlist WHERE user_id = %s AND id = %s", (user_id, watchlist_id))
        connection.commit()


def import_watchlist_csv(file) -> int:
    """Import watchlist rows from CSV."""
    try:
        frame = pd.read_csv(file)
    except Exception as exc:
        raise ValueError("Unable to read watchlist CSV.") from exc

    normalized_columns = {column: column.strip().lower() for column in frame.columns}
    frame = frame.rename(columns=normalized_columns)
    required_columns = {"ticker", "company_name", "notes"}
    missing = required_columns - set(frame.columns)
    if missing:
        raise ValueError(f"Watchlist CSV is missing required columns: {', '.join(sorted(missing))}")

    imported_count = 0
    for _, row in frame.iterrows():
        add_watchlist_item(
            WatchlistInput(
                ticker=str(row["ticker"]).strip(),
                company_name=str(row["company_name"]).strip(),
                notes="" if pd.isna(row["notes"]) else str(row["notes"]),
            )
        )
        imported_count += 1
    return imported_count


def export_watchlist_csv() -> str:
    """Export watchlist as CSV text."""
    frame = get_watchlist()
    buffer = StringIO()
    frame.to_csv(buffer, index=False)
    return buffer.getvalue()
