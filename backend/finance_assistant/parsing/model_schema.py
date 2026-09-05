"""Pydantic model for InterpretationDraft structured model output."""
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class DraftIntent(StrEnum):
    AGGREGATE = "aggregate"
    COMPARE = "compare"
    RANK = "rank"
    LIST = "list"
    LOOKUP = "lookup"
    AGEING = "ageing"
    DATA_HEALTH = "data_health"
    ANOMALY = "anomaly"
    DEFINITION = "definition"
    EXPORT = "export"


class DraftEntityType(StrEnum):
    VENDOR = "vendor"
    ACCOUNT = "account"
    DEPARTMENT = "department"
    COST_CENTER = "cost_center"
    PROJECT = "project"
    TRANSACTION = "transaction"
    PAYOUT = "payout"
    STATUS = "status"


class DraftPeriodRole(StrEnum):
    PRIMARY = "primary"
    COMPARISON = "comparison"
    AGE_ANCHOR = "age_anchor"


class DraftCorrectionOperation(StrEnum):
    SET = "SET"
    REPLACE = "REPLACE"
    ADD = "ADD"
    REMOVE = "REMOVE"
    CLEAR = "CLEAR"
    RESET = "RESET"
    REFER_TO_RESULT = "REFER_TO_RESULT"


class DraftEntity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    type: DraftEntityType
    text: str = Field(min_length=1, max_length=200)


class DraftPeriod(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str = Field(min_length=1, max_length=100)
    role: DraftPeriodRole


class DraftCorrection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation: DraftCorrectionOperation
    field: str = Field(max_length=100)
    value_text: str | None = Field(default=None, max_length=500)


class InterpretationDraft(BaseModel):
    """Closed schema returned by the language model before deterministic resolution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    intent: DraftIntent | None
    metric_candidate: str | None = Field(max_length=100)
    entities: tuple[DraftEntity, ...] = Field(max_length=20)
    periods: tuple[DraftPeriod, ...] = Field(max_length=4)
    dimensions: tuple[str, ...] = Field(max_length=5)
    statuses: tuple[str, ...] = Field(max_length=10)
    correction_operations: tuple[DraftCorrection, ...] = Field(max_length=10)
    unsupported_concepts: tuple[str, ...] = Field(max_length=10)
    ambiguity_notes: tuple[str, ...] = Field(max_length=10)


def empty_interpretation_draft() -> InterpretationDraft:
    return InterpretationDraft(
        intent=None,
        metric_candidate=None,
        entities=(),
        periods=(),
        dimensions=(),
        statuses=(),
        correction_operations=(),
        unsupported_concepts=(),
        ambiguity_notes=(),
    )


def interpretation_draft_json_schema() -> dict[str, object]:
    """Return a Sarvam Structured Outputs-compatible JSON Schema."""
    schema = InterpretationDraft.model_json_schema(mode="validation")
    schema["additionalProperties"] = False
    return schema
