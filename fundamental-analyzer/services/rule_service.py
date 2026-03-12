"""Rule configuration load/save services."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from config.settings import DEFAULT_RULES_PATH, SUPPORTED_OPERATORS, USER_RULES_PATH
from models.rule_model import Rule
from services.audit_service import log_audit_event
from services.auth_service import require_current_user_id
from services.db import get_connection


class RuleService:
    """Manage default and user-defined rule sets."""

    def __init__(
        self,
        default_rules_path: Path = DEFAULT_RULES_PATH,
        user_rules_path: Path = USER_RULES_PATH,
    ) -> None:
        self.default_rules_path = Path(default_rules_path)
        self.user_rules_path = Path(user_rules_path)

    def _load_json(self, path: Path) -> dict[str, list[dict[str, object]]]:
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _load_custom_rules(self, user_id: int) -> dict[str, list[dict[str, object]]]:
        """Load custom rules for the authenticated user from PostgreSQL."""
        with get_connection() as connection:
            rows = connection.execute(
                "SELECT category, rules_json FROM custom_rules WHERE user_id = %s",
                (user_id,),
            ).fetchall()

        payload: dict[str, list[dict[str, object]]] = {}
        for row in rows:
            try:
                payload[str(row["category"])] = json.loads(str(row["rules_json"]))
            except json.JSONDecodeError:
                payload[str(row["category"])] = []
        return payload

    def _coerce_rules(self, raw_rules: list[dict[str, object]]) -> list[Rule]:
        """Normalize raw JSON rules into ``Rule`` objects."""
        normalized_rules: list[Rule] = []
        for raw_rule in raw_rules:
            normalized_rules.append(
                Rule(
                    category=str(raw_rule.get("category")).strip() if raw_rule.get("category") else None,
                    parameter=str(raw_rule.get("parameter", "")).strip(),
                    label=str(raw_rule.get("label")).strip() if raw_rule.get("label") else None,
                    operator=str(raw_rule.get("operator", "")).strip(),
                    value=float(raw_rule.get("value", 0)),
                    rationale=str(raw_rule.get("rationale", "")).strip(),
                )
            )
        return normalized_rules

    def validate_rule_payload(self, payload: Any) -> tuple[bool, str, list[Rule]]:
        """Validate imported JSON payload and convert it to ``Rule`` objects."""
        if isinstance(payload, dict):
            if len(payload) != 1:
                return False, "Imported JSON object must contain exactly one market-cap bucket.", []
            _, raw_rules = next(iter(payload.items()))
        else:
            raw_rules = payload

        if not isinstance(raw_rules, list):
            return False, "Imported JSON must be a list of rules or a single-bucket object.", []

        validated_rules: list[Rule] = []
        required_fields = {"parameter", "operator", "value", "rationale"}

        for index, item in enumerate(raw_rules, start=1):
            if not isinstance(item, dict):
                return False, f"Rule #{index} must be a JSON object.", []

            missing_fields = sorted(required_fields - set(item.keys()))
            if missing_fields:
                return False, f"Rule #{index} is missing required fields: {', '.join(missing_fields)}.", []

            operator = str(item.get("operator", "")).strip()
            if operator not in SUPPORTED_OPERATORS:
                return False, f"Rule #{index} uses unsupported operator: {operator}.", []

            parameter = str(item.get("parameter", "")).strip()
            rationale = str(item.get("rationale", "")).strip()
            if not parameter:
                return False, f"Rule #{index} has an empty parameter.", []
            if not rationale:
                return False, f"Rule #{index} has an empty rationale.", []

            try:
                value = float(item.get("value"))
            except (TypeError, ValueError):
                return False, f"Rule #{index} has a non-numeric value.", []

            validated_rules.append(
                Rule(
                    parameter=parameter,
                    operator=operator,
                    value=value,
                    rationale=rationale,
                    category=str(item.get("category")).strip() if item.get("category") else None,
                    label=str(item.get("label")).strip() if item.get("label") else None,
                )
            )

        return True, "", validated_rules

    def get_rule_source(self, category: str, user_id: int | None = None) -> str:
        """Return the active rule source for a market-cap bucket."""
        resolved_user_id = user_id if user_id is not None else require_current_user_id()
        user_rules = self._load_custom_rules(resolved_user_id)
        if category in user_rules and user_rules[category]:
            return "custom"
        return "default"

    def get_rules(self, category: str, user_id: int | None = None) -> list[Rule]:
        """Return user rules if present, otherwise default rules."""
        rules, _ = self.get_rules_with_source(category, user_id=user_id)
        return rules

    def get_rules_with_source(self, category: str, user_id: int | None = None) -> tuple[list[Rule], str]:
        """Return active rules and whether they came from custom or default config."""
        resolved_user_id = user_id if user_id is not None else require_current_user_id()
        user_rules = self._load_custom_rules(resolved_user_id)
        if category in user_rules and user_rules[category]:
            return self._coerce_rules(user_rules[category]), "custom"
        default_rules = self._load_json(self.default_rules_path)
        return self._coerce_rules(default_rules.get(category, [])), "default"

    def save_rules(self, category: str, rules: list[Rule]) -> None:
        """Persist edited custom rules for the authenticated user."""
        user_id = require_current_user_id()
        payload = json.dumps([rule.to_dict() for rule in rules], indent=2)
        updated_at = datetime.utcnow().isoformat(timespec="seconds")
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO custom_rules (user_id, category, rules_json, updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, category)
                DO UPDATE SET rules_json = excluded.rules_json, updated_at = excluded.updated_at
                """,
                (user_id, category, payload, updated_at),
            )
            connection.commit()
        log_audit_event(
            "save_rules",
            details={"category": category, "rule_count": len(rules)},
            user_id=user_id,
        )

    def export_rules_json(self, category: str) -> str:
        """Return the active rules for a bucket as formatted JSON."""
        rules = self.get_rules(category)
        return json.dumps([rule.to_dict() for rule in rules], indent=2)

    def validate_operator(self, operator: str) -> bool:
        """Check whether an operator is supported."""
        return operator in SUPPORTED_OPERATORS
