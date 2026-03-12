"""Transaction persistence and validation services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from io import StringIO

import pandas as pd

from services.audit_service import log_audit_event
from services.auth_service import require_current_user_id
from services.portfolio_db import get_connection


@dataclass
class TransactionInput:
    """Validated transaction payload."""

    date: str
    ticker: str
    company_name: str
    transaction_type: str
    quantity: float
    price: float
    charges: float = 0.0
    notes: str = ""


def _normalize_ticker(ticker: str) -> str:
    """Normalize a ticker symbol."""
    return ticker.strip().upper()


def get_transactions() -> pd.DataFrame:
    """Return all stored transactions ordered by date and id."""
    user_id = require_current_user_id()
    with get_connection() as connection:
        frame = pd.read_sql_query(
            "SELECT * FROM transactions WHERE user_id = ? ORDER BY date ASC, id ASC",
            connection,
            params=(user_id,),
        )
    return frame


def _available_quantity(ticker: str) -> float:
    """Return currently available quantity for a ticker from transactions."""
    user_id = require_current_user_id()
    normalized_ticker = _normalize_ticker(ticker)
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT COALESCE(SUM(
                CASE
                    WHEN transaction_type = 'BUY' THEN quantity
                    WHEN transaction_type = 'SELL' THEN -quantity
                    ELSE 0
                END
            ), 0) AS net_quantity
            FROM transactions
            WHERE user_id = ? AND ticker = ?
            """,
            (user_id, normalized_ticker),
        ).fetchone()
    return float(row["net_quantity"]) if row is not None else 0.0


def validate_transaction_input(payload: TransactionInput) -> None:
    """Validate a transaction before insert."""
    if not payload.date:
        raise ValueError("Transaction date is required.")
    if not payload.ticker.strip():
        raise ValueError("Ticker is required.")
    if payload.quantity <= 0:
        raise ValueError("Quantity must be greater than 0.")
    if payload.price <= 0:
        raise ValueError("Price must be greater than 0.")
    if payload.charges < 0:
        raise ValueError("Charges cannot be negative.")
    if payload.transaction_type not in {"BUY", "SELL"}:
        raise ValueError("Transaction type must be BUY or SELL.")
    if payload.transaction_type == "SELL":
        available = _available_quantity(payload.ticker)
        if payload.quantity > available:
            raise ValueError("SELL quantity cannot exceed available holdings.")


def add_transaction(payload: TransactionInput) -> None:
    """Insert a validated transaction into the database."""
    user_id = require_current_user_id()
    normalized_payload = TransactionInput(
        date=payload.date,
        ticker=_normalize_ticker(payload.ticker),
        company_name=payload.company_name.strip(),
        transaction_type=payload.transaction_type,
        quantity=float(payload.quantity),
        price=float(payload.price),
        charges=float(payload.charges),
        notes=payload.notes.strip(),
    )
    validate_transaction_input(normalized_payload)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO transactions (
                user_id, date, ticker, company_name, transaction_type, quantity, price, charges, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                normalized_payload.date,
                normalized_payload.ticker,
                normalized_payload.company_name,
                normalized_payload.transaction_type,
                normalized_payload.quantity,
                normalized_payload.price,
                normalized_payload.charges,
                normalized_payload.notes,
            ),
        )
        connection.commit()
    log_audit_event(
        "add_transaction",
        details={
            "ticker": normalized_payload.ticker,
            "transaction_type": normalized_payload.transaction_type,
            "quantity": normalized_payload.quantity,
            "price": normalized_payload.price,
        },
        user_id=user_id,
    )


def import_transactions_csv(file) -> int:
    """Import transactions from CSV after row-by-row validation."""
    try:
        frame = pd.read_csv(file)
    except Exception as exc:
        raise ValueError("Unable to read transactions CSV.") from exc

    normalized_columns = {column: column.strip().lower() for column in frame.columns}
    frame = frame.rename(columns=normalized_columns)
    required_columns = {
        "date",
        "ticker",
        "company_name",
        "transaction_type",
        "quantity",
        "price",
        "charges",
        "notes",
    }
    missing = required_columns - set(frame.columns)
    if missing:
        raise ValueError(f"Transactions CSV is missing required columns: {', '.join(sorted(missing))}")

    imported_count = 0
    for _, row in frame.iterrows():
        payload = TransactionInput(
            date=str(row["date"]).strip(),
            ticker=str(row["ticker"]).strip(),
            company_name=str(row["company_name"]).strip(),
            transaction_type=str(row["transaction_type"]).strip().upper(),
            quantity=float(row["quantity"]),
            price=float(row["price"]),
            charges=float(row["charges"]),
            notes="" if pd.isna(row["notes"]) else str(row["notes"]),
        )
        add_transaction(payload)
        imported_count += 1

    return imported_count


def export_transactions_csv() -> str:
    """Export all transactions as CSV text."""
    frame = get_transactions()
    buffer = StringIO()
    frame.to_csv(buffer, index=False)
    return buffer.getvalue()


def transaction_form_defaults() -> dict[str, object]:
    """Return starter values for the transaction form."""
    return {
        "date": date.today(),
        "ticker": "",
        "company_name": "",
        "transaction_type": "BUY",
        "quantity": 0.0,
        "price": 0.0,
        "charges": 0.0,
        "notes": "",
    }
