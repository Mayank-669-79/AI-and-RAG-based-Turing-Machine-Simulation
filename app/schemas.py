"""Shared API schemas. Keep these contracts aligned with the root README."""

from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class ConditionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    condition: str = Field(min_length=1, description="Natural-language language condition")
    alphabet: list[str] = Field(default_factory=lambda: ["0", "1"])


class RunRequest(ConditionRequest):
    input_string: str = ""
    max_steps: int = Field(default=1000, ge=1, le=100_000)


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ApiErrorResponse(BaseModel):
    success: Literal[False] = False
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
