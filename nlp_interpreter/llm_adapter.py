"""Optional boundary for future language-model interpretation providers.

No provider is configured by default. Any proposed data must be validated
through :class:`ConditionResult` and accepted only for a supported family.
"""

from __future__ import annotations

from typing import Any, Protocol

from .condition_schema import ConditionResult


class ConditionProposalProvider(Protocol):
    """Provider interface; implementations return data, never executable code."""

    def propose(self, text: str) -> dict[str, Any]:
        """Propose a normalized condition object for validation."""


def validate_proposal(proposal: dict[str, Any]) -> dict[str, Any]:
    """Validate provider output against the shared condition contract."""
    result = ConditionResult.model_validate(proposal)
    if result.family is None:
        raise ValueError("provider proposal must identify a supported condition family")
    return result.to_dict()
