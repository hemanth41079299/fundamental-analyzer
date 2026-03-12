"""Secure file upload validation and persistence helpers."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from config.settings import MAX_UPLOAD_SIZE_MB, SUPPORTED_FILE_EXTENSIONS, UPLOADS_DIR
from services.audit_service import log_audit_event
from services.auth_service import require_current_user_id

SAFE_FILENAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def _get_upload_size(uploaded_file) -> int:
    """Return file size in bytes."""
    size = getattr(uploaded_file, "size", None)
    if isinstance(size, int):
        return size
    return len(uploaded_file.getbuffer())


def validate_uploaded_file(uploaded_file) -> None:
    """Validate file extension, size, and filename safety."""
    filename = str(getattr(uploaded_file, "name", "")).strip()
    if not filename:
        raise ValueError("Uploaded file must have a valid filename.")

    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_FILE_EXTENSIONS:
        raise ValueError("Unsupported file type. Please upload a PDF file.")

    if "/" in filename or "\\" in filename or ".." in filename:
        raise ValueError("Unsafe filename detected.")

    if not SAFE_FILENAME_PATTERN.fullmatch(filename):
        raise ValueError("Filename contains unsupported characters.")

    max_size_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    file_size = _get_upload_size(uploaded_file)
    if file_size > max_size_bytes:
        raise ValueError(f"File is too large. Maximum allowed size is {MAX_UPLOAD_SIZE_MB} MB.")


def build_user_upload_path(uploaded_file) -> Path:
    """Build a user-specific target path for an uploaded file."""
    user_id = require_current_user_id()
    filename = Path(str(uploaded_file.name).strip()).name
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    safe_name = f"{timestamp}_{filename}"
    user_dir = Path(UPLOADS_DIR) / f"user_{user_id}"
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir / safe_name


def save_secure_uploaded_file(uploaded_file) -> Path:
    """Validate and save an uploaded file into a user-specific folder."""
    user_id = require_current_user_id()
    validate_uploaded_file(uploaded_file)
    output_path = build_user_upload_path(uploaded_file)
    output_path.write_bytes(uploaded_file.getbuffer())
    log_audit_event(
        "upload",
        details={
            "filename": uploaded_file.name,
            "saved_path": str(output_path),
            "size_bytes": _get_upload_size(uploaded_file),
        },
        user_id=user_id,
    )
    return output_path
