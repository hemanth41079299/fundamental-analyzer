"""Application settings for the Fundamental Analyzer platform."""

from __future__ import annotations

import os
from pathlib import Path

try:  # pragma: no cover - depends on Streamlit runtime
    import streamlit as st
except ModuleNotFoundError:  # pragma: no cover - non-Streamlit execution
    st = None  # type: ignore[assignment]

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


def _get_config_value(key: str, default: str = "") -> str:
    """Read configuration from Streamlit secrets first, then environment variables."""
    if st is not None:
        try:
            value = st.secrets.get(key)
        except Exception:
            value = None
        if value is not None:
            return str(value).strip()
    return os.getenv(key, default).strip()

DEFAULT_RULES_PATH = CONFIG_DIR / "default_rules.json"
USER_RULES_PATH = CONFIG_DIR / "user_rules.json"

DATABASE_URL = _get_config_value("DATABASE_URL")
AUTH_MIN_PASSWORD_LENGTH = int(_get_config_value("AUTH_MIN_PASSWORD_LENGTH", "10"))
AUTH_LOCKOUT_ATTEMPTS = int(_get_config_value("AUTH_LOCKOUT_ATTEMPTS", "5"))
AUTH_LOCKOUT_MINUTES = int(_get_config_value("AUTH_LOCKOUT_MINUTES", "15"))
AUTH_SESSION_TIMEOUT_MINUTES = int(_get_config_value("AUTH_SESSION_TIMEOUT_MINUTES", "30"))

SUPPORTED_FILE_EXTENSIONS = {".pdf"}
MAX_UPLOAD_SIZE_MB = 10
SUPPORTED_OPERATORS = [">", "<", ">=", "<=", "==", "industry_compare"]

MARKET_CAP_CATEGORIES = ["large_cap", "mid_cap", "small_cap", "micro_cap"]
