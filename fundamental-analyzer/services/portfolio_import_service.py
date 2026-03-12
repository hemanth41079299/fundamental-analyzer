"""Portfolio holdings import workflow services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path

import pandas as pd

from services.audit_service import log_audit_event
from services.auth_service import require_current_user_id
from services.csv_holdings_parser import normalize_holdings_frame, parse_holdings_csv
from services.excel_holdings_parser import parse_holdings_excel
from services.pdf_holdings_parser import parse_holdings_pdf
from services.transaction_service import TransactionInput, add_transaction

IMPORT_MODE_LABELS = {
    "buy_transactions": "Convert holdings to BUY transactions",
}


@dataclass
class PortfolioImportPreview:
    """Preview payload for a holdings import file."""

    file_name: str
    holdings: pd.DataFrame
    import_ready: pd.DataFrame


def _get_file_name(file) -> str:
    """Return a safe display file name."""
    file_name = getattr(file, "name", "") or "uploaded_file"
    return Path(str(file_name)).name


def _get_file_suffix(file) -> str:
    """Return the lower-case file suffix for an uploaded file."""
    return Path(_get_file_name(file)).suffix.lower()


def parse_holdings_file(file) -> pd.DataFrame:
    """Parse a holdings file based on its extension."""
    suffix = _get_file_suffix(file)
    if suffix == ".csv":
        return parse_holdings_csv(file)
    if suffix in {".xlsx", ".xls"}:
        return parse_holdings_excel(file)
    if suffix == ".pdf":
        return parse_holdings_pdf(file)
    raise ValueError("Unsupported holdings file. Use CSV, Excel, or PDF.")


def _build_import_ready_frame(holdings: pd.DataFrame) -> pd.DataFrame:
    """Build a transaction-oriented preview from normalized holdings."""
    if holdings.empty:
        return pd.DataFrame(columns=["ticker", "company_name", "quantity", "price", "buy_value", "ltp", "present_value"])

    frame = normalize_holdings_frame(holdings)
    import_frame = frame.copy()
    import_frame["price"] = import_frame["avg_buy"]

    derived_price_mask = import_frame["price"].isna() & import_frame["buy_value"].notna() & import_frame["quantity"].notna() & (import_frame["quantity"] != 0)
    import_frame.loc[derived_price_mask, "price"] = (
        import_frame.loc[derived_price_mask, "buy_value"] / import_frame.loc[derived_price_mask, "quantity"]
    )

    import_frame["validation_status"] = "Ready"
    missing_ticker = import_frame["ticker"].isna()
    missing_quantity = import_frame["quantity"].isna() | (import_frame["quantity"] <= 0)
    missing_price = import_frame["price"].isna() | (import_frame["price"] <= 0)

    import_frame.loc[missing_ticker, "validation_status"] = "Missing ticker"
    import_frame.loc[missing_quantity, "validation_status"] = "Invalid quantity"
    import_frame.loc[missing_price, "validation_status"] = "Missing avg buy"

    return import_frame[["ticker", "company_name", "quantity", "price", "buy_value", "ltp", "present_value", "validation_status"]]


def build_portfolio_import_preview(file) -> PortfolioImportPreview:
    """Parse a holdings file and prepare a preview dataframe."""
    holdings = parse_holdings_file(file)
    import_ready = _build_import_ready_frame(holdings)
    return PortfolioImportPreview(
        file_name=_get_file_name(file),
        holdings=holdings,
        import_ready=import_ready,
    )


def _prepare_buy_transactions(import_frame: pd.DataFrame, import_date: str, import_note: str = "") -> list[TransactionInput]:
    """Validate parsed holdings and convert them to BUY transactions."""
    transactions: list[TransactionInput] = []
    errors: list[str] = []

    for index, row in import_frame.reset_index(drop=True).iterrows():
        ticker = "" if pd.isna(row["ticker"]) else str(row["ticker"]).strip().upper()
        company_name = "" if pd.isna(row["company_name"]) else str(row["company_name"]).strip()
        quantity = None if pd.isna(row["quantity"]) else float(row["quantity"])
        price = None if pd.isna(row["price"]) else float(row["price"])
        imported_ltp = None if pd.isna(row.get("ltp")) else float(row["ltp"])
        imported_present_value = None if pd.isna(row.get("present_value")) else float(row["present_value"])

        if not ticker:
            errors.append(f"Row {index + 1}: ticker is required.")
            continue
        if quantity is None or quantity <= 0:
            errors.append(f"Row {index + 1}: quantity must be greater than 0.")
            continue
        if price is None or price <= 0:
            errors.append(f"Row {index + 1}: avg buy or derived buy price is required.")
            continue

        note_parts = ["Imported from holdings file"]
        if import_note.strip():
            note_parts.append(import_note.strip())
        metadata = {
            "source": "holdings_import",
            "imported_ltp": imported_ltp,
            "imported_present_value": imported_present_value,
        }
        note_parts.append(f"[import_meta]{json.dumps(metadata, separators=(',', ':'))}")

        transactions.append(
            TransactionInput(
                date=import_date,
                ticker=ticker,
                company_name=company_name,
                transaction_type="BUY",
                quantity=quantity,
                price=price,
                charges=0.0,
                notes=" | ".join(note_parts),
            )
        )

    if errors:
        raise ValueError("Holdings import validation failed:\n" + "\n".join(errors))
    return transactions


def import_portfolio_holdings(
    holdings: pd.DataFrame,
    import_mode: str = "buy_transactions",
    import_date: str | None = None,
    import_note: str = "",
) -> int:
    """Import parsed holdings into the portfolio ledger."""
    if import_mode not in IMPORT_MODE_LABELS:
        raise ValueError("Unsupported import mode.")

    normalized_holdings = normalize_holdings_frame(holdings)
    if normalized_holdings.empty:
        raise ValueError("No holdings rows were available for import.")

    actual_date = import_date or date.today().isoformat()
    import_ready = _build_import_ready_frame(normalized_holdings)
    transactions = _prepare_buy_transactions(import_ready, actual_date, import_note)

    for payload in transactions:
        add_transaction(payload)

    user_id = require_current_user_id()
    log_audit_event(
        "import_holdings",
        details={
            "import_mode": import_mode,
            "rows_imported": len(transactions),
            "import_date": actual_date,
        },
        user_id=user_id,
    )
    return len(transactions)
