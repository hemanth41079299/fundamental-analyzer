"""Backward-compatible database wrapper.

The application now uses PostgreSQL through ``services.db``.
"""

from __future__ import annotations

from services.db import get_connection, init_db, init_portfolio_db

__all__ = ["get_connection", "init_db", "init_portfolio_db"]
