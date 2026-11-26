"""Typed data structures used by the rule parser and validator."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Transition:
    """One deterministic Turing Machine transition."""

    current_state: str
    read_symbol: str
    next_state: str
    write_symbol: str
    direction: str

    def to_dict(self) -> dict[str, str]:
        """Return the transition in the shared JSON-friendly representation."""
        return asdict(self)


def transition_from_mapping(data: dict[str, Any]) -> Transition:
    """Build a Transition from a mapping, rejecting missing fields."""
    required = (
        "current_state", "read_symbol", "next_state", "write_symbol", "direction"
    )
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"Transition is missing required field(s): {', '.join(missing)}")
    return Transition(**{key: data[key] for key in required})
