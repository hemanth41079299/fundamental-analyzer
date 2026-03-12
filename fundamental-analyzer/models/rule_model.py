"""Rule model definitions for the starter scaffold."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class Rule:
    """Rule definition loaded from JSON."""

    parameter: str
    operator: str
    value: float
    rationale: str
    category: str | None = None
    label: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Convert rule to a dictionary."""
        return asdict(self)
