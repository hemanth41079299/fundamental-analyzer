"""Application settings for the starter scaffold."""

from __future__ import annotations

from pathlib import Path

APP_TITLE = "Fundamental Analyzer"

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"
DATA_DIR = BASE_DIR / "data"
COMPANY_HISTORY_DIR = DATA_DIR / "company_history"
EXAMPLES_DIR = DATA_DIR / "examples"

DEFAULT_RULES_PATH = CONFIG_DIR / "default_rules.json"
USER_RULES_PATH = CONFIG_DIR / "user_rules.json"

SUPPORTED_FILE_EXTENSIONS = {".pdf"}
MAX_UPLOAD_SIZE_MB = 10
SUPPORTED_OPERATORS = [">", "<", ">=", "<=", "==", "industry_compare"]

MARKET_CAP_CATEGORIES = ["large_cap", "mid_cap", "small_cap", "micro_cap"]
