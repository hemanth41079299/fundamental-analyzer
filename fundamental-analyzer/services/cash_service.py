"""Cash ledger services."""

from __future__ import annotations

from dataclasses import dataclass
from io import StringIO

import pandas as pd

from services.auth_service import require_current_user_id
from services.db import get_connection


@dataclass
class CashEntryInput:
    """Validated cash ledger payload."""

    date: str
    entry_type: str
    amount: float
    notes: str = ""


def validate_cash_entry(payload: CashEntryInput) -> None:
    """Validate a cash ledger entry."""
    if not payload.date:
        raise ValueError("Cash entry date is required.")
    if payload.entry_type not in {"DEPOSIT", "WITHDRAWAL"}:
        raise ValueError("Entry type must be DEPOSIT or WITHDRAWAL.")
    if payload.amount <= 0:
        raise ValueError("Amount must be greater than 0.")


def add_cash_entry(payload: CashEntryInput) -> None:
    """Insert a cash ledger entry."""
    user_id = require_current_user_id()
    validate_cash_entry(payload)
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO cash_ledger (user_id, date, entry_type, amount, notes)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, payload.date, payload.entry_type, payload.amount, payload.notes.strip()),
        )
        connection.commit()


def get_cash_entries() -> pd.DataFrame:
    """Return all cash ledger entries."""
    user_id = require_current_user_id()
    with get_connection() as connection:
        frame = pd.read_sql_query(
            "SELECT * FROM cash_ledger WHERE user_id = %s ORDER BY date DESC, id DESC",
            connection,
            params=(user_id,),
        )
    return frame


def get_cash_balance() -> float:
    """Calculate cash balance from deposits and withdrawals."""
    user_id = require_current_user_id()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT COALESCE(SUM(
                CASE
                    WHEN entry_type = 'DEPOSIT' THEN amount
                    WHEN entry_type = 'WITHDRAWAL' THEN -amount
                    ELSE 0
                END
            ), 0) AS cash_balance
            FROM cash_ledger
            WHERE user_id = %s
            """,
            (user_id,),
        ).fetchone()
    return float(row["cash_balance"]) if row is not None else 0.0


def export_cash_entries_csv() -> str:
    """Export cash ledger as CSV text."""
    frame = get_cash_entries()
    buffer = StringIO()
    frame.to_csv(buffer, index=False)
    return buffer.getvalue()
