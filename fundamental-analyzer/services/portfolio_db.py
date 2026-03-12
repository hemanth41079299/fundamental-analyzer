"""SQLite helper and migrations for the portfolio management layer."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from config.settings import DATA_DIR

PORTFOLIO_DB_PATH = Path(DATA_DIR) / "portfolio.db"


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection configured for dict-like row access."""
    PORTFOLIO_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(PORTFOLIO_DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    """Check whether a table exists."""
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _get_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    """Return column names for a table."""
    if not _table_exists(connection, table_name):
        return set()
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row["name"]) for row in rows}


def _get_create_sql(connection: sqlite3.Connection, table_name: str) -> str:
    """Return the CREATE TABLE SQL for a table."""
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    if row is None or row["sql"] is None:
        return ""
    return str(row["sql"])


def _resolve_legacy_user_id(connection: sqlite3.Connection) -> int | None:
    """Assign legacy shared data only when there is exactly one user."""
    row = connection.execute("SELECT COUNT(*) AS user_count FROM users").fetchone()
    user_count = int(row["user_count"]) if row is not None else 0
    if user_count != 1:
        return None

    user_row = connection.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1").fetchone()
    if user_row is None:
        return None
    return int(user_row["id"])


def _ensure_users_table(connection: sqlite3.Connection) -> None:
    """Create the users table."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )


def _migrate_transactions_table(connection: sqlite3.Connection) -> None:
    """Ensure transactions include user_id and user-scoped indexes."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT NOT NULL,
            ticker TEXT NOT NULL,
            company_name TEXT,
            transaction_type TEXT NOT NULL CHECK (transaction_type IN ('BUY', 'SELL')),
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            charges REAL NOT NULL DEFAULT 0,
            notes TEXT
        )
        """
    )
    if "user_id" not in _get_columns(connection, "transactions"):
        connection.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER")
        legacy_user_id = _resolve_legacy_user_id(connection)
        if legacy_user_id is not None:
            connection.execute(
                "UPDATE transactions SET user_id = ? WHERE user_id IS NULL",
                (legacy_user_id,),
            )

    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, date, id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_user_ticker ON transactions(user_id, ticker)"
    )


def _migrate_watchlist_table(connection: sqlite3.Connection) -> None:
    """Ensure watchlist uniqueness is scoped by user_id."""
    desired_sql = """
        CREATE TABLE watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ticker TEXT NOT NULL,
            company_name TEXT,
            added_on TEXT NOT NULL,
            notes TEXT
        )
    """
    if not _table_exists(connection, "watchlist"):
        connection.execute(desired_sql)
    else:
        columns = _get_columns(connection, "watchlist")
        create_sql = _get_create_sql(connection, "watchlist").upper()
        needs_rebuild = "user_id" not in columns or "TICKER TEXT NOT NULL UNIQUE" in create_sql
        if needs_rebuild:
            legacy_user_id = _resolve_legacy_user_id(connection)
            connection.execute("ALTER TABLE watchlist RENAME TO watchlist_legacy")
            connection.execute(desired_sql)
            connection.execute(
                """
                INSERT INTO watchlist (id, user_id, ticker, company_name, added_on, notes)
                SELECT id, ?, ticker, company_name, added_on, notes
                FROM watchlist_legacy
                """,
                (legacy_user_id,),
            )
            connection.execute("DROP TABLE watchlist_legacy")

    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_watchlist_user_ticker ON watchlist(user_id, ticker)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_watchlist_user_added_on ON watchlist(user_id, added_on, id)"
    )


def _migrate_cash_ledger_table(connection: sqlite3.Connection) -> None:
    """Ensure cash ledger includes user_id."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS cash_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT NOT NULL,
            entry_type TEXT NOT NULL CHECK (entry_type IN ('DEPOSIT', 'WITHDRAWAL')),
            amount REAL NOT NULL,
            notes TEXT
        )
        """
    )
    if "user_id" not in _get_columns(connection, "cash_ledger"):
        connection.execute("ALTER TABLE cash_ledger ADD COLUMN user_id INTEGER")
        legacy_user_id = _resolve_legacy_user_id(connection)
        if legacy_user_id is not None:
            connection.execute(
                "UPDATE cash_ledger SET user_id = ? WHERE user_id IS NULL",
                (legacy_user_id,),
            )

    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_cash_ledger_user_date ON cash_ledger(user_id, date, id)"
    )


def _migrate_portfolio_snapshots_table(connection: sqlite3.Connection) -> None:
    """Ensure snapshots are unique per user, not globally."""
    desired_sql = """
        CREATE TABLE portfolio_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            snapshot_date TEXT NOT NULL,
            invested_amount REAL NOT NULL,
            portfolio_value REAL NOT NULL,
            unrealized_pnl REAL NOT NULL,
            realized_pnl REAL NOT NULL,
            cash_balance REAL NOT NULL,
            total_net_worth REAL NOT NULL
        )
    """
    if not _table_exists(connection, "portfolio_snapshots"):
        connection.execute(desired_sql)
    else:
        columns = _get_columns(connection, "portfolio_snapshots")
        create_sql = _get_create_sql(connection, "portfolio_snapshots").upper()
        needs_rebuild = "user_id" not in columns or "SNAPSHOT_DATE TEXT NOT NULL UNIQUE" in create_sql
        if needs_rebuild:
            legacy_user_id = _resolve_legacy_user_id(connection)
            connection.execute("ALTER TABLE portfolio_snapshots RENAME TO portfolio_snapshots_legacy")
            connection.execute(desired_sql)
            connection.execute(
                """
                INSERT INTO portfolio_snapshots (
                    id, user_id, snapshot_date, invested_amount, portfolio_value,
                    unrealized_pnl, realized_pnl, cash_balance, total_net_worth
                )
                SELECT
                    id, ?, snapshot_date, invested_amount, portfolio_value,
                    unrealized_pnl, realized_pnl, cash_balance, total_net_worth
                FROM portfolio_snapshots_legacy
                """,
                (legacy_user_id,),
            )
            connection.execute("DROP TABLE portfolio_snapshots_legacy")

    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_snapshots_user_date ON portfolio_snapshots(user_id, snapshot_date)"
    )


def _ensure_company_history_table(connection: sqlite3.Connection) -> None:
    """Create the company history table."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS company_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            timestamp TEXT NOT NULL,
            company_name TEXT NOT NULL,
            source_file TEXT,
            metrics_json TEXT NOT NULL,
            score REAL NOT NULL,
            total_score REAL NOT NULL,
            verdict TEXT NOT NULL,
            narration TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_company_history_user_company_time ON company_history(user_id, company_name, timestamp)"
    )


def _ensure_custom_rules_table(connection: sqlite3.Connection) -> None:
    """Create the custom rules table."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS custom_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT NOT NULL,
            rules_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_custom_rules_user_category ON custom_rules(user_id, category)"
    )


def _ensure_audit_logs_table(connection: sqlite3.Connection) -> None:
    """Create the audit log table."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details_json TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_created_at ON audit_logs(user_id, created_at, id)"
    )


def init_portfolio_db() -> None:
    """Create and migrate all local SQLite tables."""
    with get_connection() as connection:
        _ensure_users_table(connection)
        _migrate_transactions_table(connection)
        _migrate_watchlist_table(connection)
        _migrate_cash_ledger_table(connection)
        _migrate_portfolio_snapshots_table(connection)
        _ensure_company_history_table(connection)
        _ensure_custom_rules_table(connection)
        _ensure_audit_logs_table(connection)
        connection.commit()
