"""Application settings for the Fundamental Analyzer platform."""

from __future__ import annotations

import os
from pathlib import Path

APP_TITLE = "Fundamental Analyzer"

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"
DATA_DIR = BASE_DIR / "data"
COMPANY_HISTORY_DIR = DATA_DIR / "company_history"
EXAMPLES_DIR = DATA_DIR / "examples"


def _load_dotenv(dotenv_path: Path) -> None:
    """Load simple KEY=VALUE pairs from a local .env file if present."""
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(BASE_DIR / ".env")

DEFAULT_RULES_PATH = CONFIG_DIR / "default_rules.json"
USER_RULES_PATH = CONFIG_DIR / "user_rules.json"

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
AUTH_MIN_PASSWORD_LENGTH = int(os.getenv("AUTH_MIN_PASSWORD_LENGTH", "10"))
AUTH_LOCKOUT_ATTEMPTS = int(os.getenv("AUTH_LOCKOUT_ATTEMPTS", "5"))
AUTH_LOCKOUT_MINUTES = int(os.getenv("AUTH_LOCKOUT_MINUTES", "15"))
AUTH_SESSION_TIMEOUT_MINUTES = int(os.getenv("AUTH_SESSION_TIMEOUT_MINUTES", "30"))

SUPPORTED_FILE_EXTENSIONS = {".pdf"}
MAX_UPLOAD_SIZE_MB = 10
SUPPORTED_OPERATORS = [">", "<", ">=", "<=", "==", "industry_compare"]

MARKET_CAP_CATEGORIES = ["large_cap", "mid_cap", "small_cap", "micro_cap"]
