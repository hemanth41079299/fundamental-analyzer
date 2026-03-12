"""PostgreSQL connection and schema bootstrap helpers."""

from __future__ import annotations

from typing import Any

from config.settings import DATABASE_URL

try:  # pragma: no cover - depends on local environment
    import psycopg
    from psycopg.rows import dict_row
except ModuleNotFoundError:  # pragma: no cover - depends on local environment
    psycopg = None  # type: ignore[assignment]
    dict_row = None  # type: ignore[assignment]


def _require_database_url() -> str:
    """Return the configured database URL or raise a clear error."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not configured. Create a .env file or export DATABASE_URL before starting the app.")
    return DATABASE_URL


def _require_psycopg() -> Any:
    """Ensure the PostgreSQL driver is installed."""
    if psycopg is None or dict_row is None:
        raise ValueError("psycopg is not installed. Run: pip install -r requirements.txt")
    return psycopg


def get_connection():
    """Return a PostgreSQL connection with dict-like row access."""
    psycopg_module = _require_psycopg()
    return psycopg_module.connect(
        _require_database_url(),
        row_factory=dict_row,
    )


def _ensure_users_table(connection) -> None:
    """Create and align the users table."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id BIGSERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            approval_status TEXT NOT NULL DEFAULT 'approved',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            approval_note TEXT,
            failed_login_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until TEXT,
            last_login_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS approval_status TEXT NOT NULL DEFAULT 'approved'"
    )
    connection.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE"
    )
    connection.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS approval_note TEXT")
    connection.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER NOT NULL DEFAULT 0"
    )
    connection.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TEXT")
    connection.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TEXT")


def _ensure_transactions_table(connection) -> None:
    """Create the transactions table and indexes."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            date TEXT NOT NULL,
            ticker TEXT NOT NULL,
            company_name TEXT,
            transaction_type TEXT NOT NULL CHECK (transaction_type IN ('BUY', 'SELL')),
            quantity DOUBLE PRECISION NOT NULL,
            price DOUBLE PRECISION NOT NULL,
            charges DOUBLE PRECISION NOT NULL DEFAULT 0,
            notes TEXT
        )
        """
    )
    connection.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, date, id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user_ticker ON transactions(user_id, ticker)")


def _ensure_watchlist_table(connection) -> None:
    """Create the watchlist table and indexes."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS watchlist (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            ticker TEXT NOT NULL,
            company_name TEXT,
            added_on TEXT NOT NULL,
            notes TEXT
        )
        """
    )
    connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_watchlist_user_ticker ON watchlist(user_id, ticker)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_user_added_on ON watchlist(user_id, added_on, id)")


def _ensure_cash_ledger_table(connection) -> None:
    """Create the cash ledger table and indexes."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS cash_ledger (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            date TEXT NOT NULL,
            entry_type TEXT NOT NULL CHECK (entry_type IN ('DEPOSIT', 'WITHDRAWAL')),
            amount DOUBLE PRECISION NOT NULL,
            notes TEXT
        )
        """
    )
    connection.execute("CREATE INDEX IF NOT EXISTS idx_cash_ledger_user_date ON cash_ledger(user_id, date, id)")


def _ensure_portfolio_snapshots_table(connection) -> None:
    """Create the portfolio snapshot table and indexes."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS portfolio_snapshots (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            snapshot_date TEXT NOT NULL,
            invested_amount DOUBLE PRECISION NOT NULL,
            portfolio_value DOUBLE PRECISION NOT NULL,
            unrealized_pnl DOUBLE PRECISION NOT NULL,
            realized_pnl DOUBLE PRECISION NOT NULL,
            cash_balance DOUBLE PRECISION NOT NULL,
            total_net_worth DOUBLE PRECISION NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_snapshots_user_date ON portfolio_snapshots(user_id, snapshot_date)"
    )


def _ensure_company_history_table(connection) -> None:
    """Create the company history table and indexes."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS company_history (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            timestamp TEXT NOT NULL,
            company_name TEXT NOT NULL,
            source_file TEXT,
            metrics_json TEXT NOT NULL,
            score DOUBLE PRECISION NOT NULL,
            total_score DOUBLE PRECISION NOT NULL,
            verdict TEXT NOT NULL,
            narration TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_company_history_user_company_time ON company_history(user_id, company_name, timestamp)"
    )


def _ensure_custom_rules_table(connection) -> None:
    """Create the user custom rules table and indexes."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS custom_rules (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            category TEXT NOT NULL,
            rules_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_custom_rules_user_category ON custom_rules(user_id, category)"
    )


def _ensure_audit_logs_table(connection) -> None:
    """Create the audit log table and indexes."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            action TEXT NOT NULL,
            details_json TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_created_at ON audit_logs(user_id, created_at, id)"
    )


def init_db() -> None:
    """Create and align the PostgreSQL schema used by the app."""
    with get_connection() as connection:
        _ensure_users_table(connection)
        _ensure_transactions_table(connection)
        _ensure_watchlist_table(connection)
        _ensure_cash_ledger_table(connection)
        _ensure_portfolio_snapshots_table(connection)
        _ensure_company_history_table(connection)
        _ensure_custom_rules_table(connection)
        _ensure_audit_logs_table(connection)
        connection.commit()


def init_portfolio_db() -> None:
    """Backward-compatible alias for the old SQLite bootstrap name."""
    init_db()
