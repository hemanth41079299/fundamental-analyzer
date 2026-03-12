"""Company analysis history persistence services."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from models.company_data import CompanyData
from models.result_model import AnalysisResult
from services.auth_service import require_current_user_id
from services.portfolio_db import PORTFOLIO_DB_PATH, get_connection


def load_company_history(company_name: str) -> list[dict[str, Any]]:
    """Load prior user-scoped analysis history for a company."""
    user_id = require_current_user_id()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT timestamp, company_name, source_file, metrics_json, score, total_score, verdict, narration
            FROM company_history
            WHERE user_id = ? AND company_name = ?
            ORDER BY timestamp ASC, id ASC
            """,
            (user_id, company_name),
        ).fetchall()

    history_rows: list[dict[str, Any]] = []
    for row in rows:
        try:
            metrics = json.loads(str(row["metrics_json"]))
        except json.JSONDecodeError:
            metrics = {}
        history_rows.append(
            {
                "timestamp": row["timestamp"],
                "company_name": row["company_name"],
                "source_file": row["source_file"],
                "metrics": metrics,
                "score": row["score"],
                "total_score": row["total_score"],
                "verdict": row["verdict"],
                "narration": row["narration"],
            }
        )
    return history_rows


def save_company_history(
    company_data: CompanyData,
    analysis_result: AnalysisResult,
    narration: str,
) -> Path:
    """Append a user-scoped company analysis entry to SQLite."""
    user_id = require_current_user_id()
    company_name = company_data.company_name or "Unknown Company"
    timestamp = datetime.now().isoformat(timespec="seconds")
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO company_history (
                user_id, timestamp, company_name, source_file, metrics_json,
                score, total_score, verdict, narration
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                timestamp,
                company_name,
                company_data.source_file,
                json.dumps(company_data.to_dict()),
                analysis_result.score.percentage,
                analysis_result.scorecard.total_score,
                analysis_result.final_verdict,
                narration,
            ),
        )
        connection.commit()
    return PORTFOLIO_DB_PATH
