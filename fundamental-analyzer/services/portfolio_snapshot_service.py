"""Portfolio snapshot services."""

from __future__ import annotations

from datetime import date
from io import StringIO

import pandas as pd

from services.audit_service import log_audit_event
from services.auth_service import require_current_user_id
from services.cash_service import get_cash_balance
from services.holdings_service import build_portfolio_summary, calculate_holdings
from services.portfolio_db import get_connection


def save_snapshot(snapshot_date: str | None = None) -> None:
    """Save a portfolio snapshot for a given date."""
    user_id = require_current_user_id()
    actual_date = snapshot_date or date.today().isoformat()
    holdings = calculate_holdings()
    cash_balance = get_cash_balance()
    summary = build_portfolio_summary(holdings, cash_balance)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO portfolio_snapshots (
                user_id, snapshot_date, invested_amount, portfolio_value, unrealized_pnl,
                realized_pnl, cash_balance, total_net_worth
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                actual_date,
                summary["invested_amount"],
                summary["portfolio_value"],
                summary["unrealized_pnl"],
                summary["realized_pnl"],
                summary["cash_balance"],
                summary["total_net_worth"],
            ),
        )
        connection.commit()
    log_audit_event(
        "save_snapshot",
        details={
            "snapshot_date": actual_date,
            "portfolio_value": summary["portfolio_value"],
            "total_net_worth": summary["total_net_worth"],
        },
        user_id=user_id,
    )


def save_snapshot_if_missing_today() -> None:
    """Save a daily snapshot only if today's snapshot does not already exist."""
    user_id = require_current_user_id()
    today = date.today().isoformat()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id FROM portfolio_snapshots WHERE user_id = ? AND snapshot_date = ?",
            (user_id, today),
        ).fetchone()
    if row is None:
        save_snapshot(today)


def get_snapshots() -> pd.DataFrame:
    """Return all portfolio snapshots."""
    user_id = require_current_user_id()
    with get_connection() as connection:
        frame = pd.read_sql_query(
            "SELECT * FROM portfolio_snapshots WHERE user_id = ? ORDER BY snapshot_date ASC, id ASC",
            connection,
            params=(user_id,),
        )
    return frame


def export_portfolio_summary_csv() -> str:
    """Export portfolio snapshots as CSV text."""
    frame = get_snapshots()
    buffer = StringIO()
    frame.to_csv(buffer, index=False)
    return buffer.getvalue()
