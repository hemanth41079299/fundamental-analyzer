"""Starter report service."""

from __future__ import annotations

import json
from pathlib import Path
from time import strftime

from models.company_data import CompanyData
from models.result_model import AnalysisResult


def save_analysis_output(
    output_dir: Path,
    company_data: CompanyData,
    analysis_result: AnalysisResult,
    narration: str,
) -> Path:
    """Save starter analysis output as JSON in the outputs folder."""
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = (company_data.company_name or "company").replace(" ", "_").lower()
    timestamp = strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"{safe_name}_{timestamp}.json"
    payload = {
        "company_data": company_data.to_dict(),
        "analysis_result": analysis_result.to_dict(),
        "narration": narration,
    }
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)
    return output_path
