"""Versioned QueryState and deterministic state operations."""
from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from finance_assistant.domain.query_plan import (
    Comparison,
    DateRange,
    Dimension,
    Metric,
    QueryFilters,
    SortSpec,
)


class StateOperationType(StrEnum):
    SET = "SET"
    REPLACE = "REPLACE"
    ADD = "ADD"
    REMOVE = "REMOVE"
    CLEAR = "CLEAR"
    RESET_ALL = "RESET_ALL"


class StateField(StrEnum):
    METRIC = "metric"
    DATE_RANGE = "date_range"
    FILTERS = "filters"
    GROUP_BY = "group_by"
    SORT = "sort"
    COMPARISON = "comparison"
    REFERENCED_QUERY_IDS = "referenced_query_ids"
    PENDING_CLARIFICATION = "pending_clarification"


class PendingClarification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    field: str
    phrase: str
    choices: tuple[dict[str, Any], ...]


class QueryState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    context_version: int = Field(ge=0)
    metric: Metric | None = None
    date_range: DateRange | None = None
    filters: QueryFilters = Field(default_factory=QueryFilters)
    group_by: tuple[Dimension, ...] = ()
    sort: tuple[SortSpec, ...] = ()
    comparison: Comparison | None = None
    referenced_query_ids: tuple[UUID, ...] = Field(default_factory=tuple, max_length=10)
    pending_clarification: PendingClarification | None = None

    @field_validator("group_by", mode="after")
    @classmethod
    def sort_group_by(cls, values: tuple[Dimension, ...]) -> tuple[Dimension, ...]:
        return tuple(sorted(set(values), key=str))

    @field_validator("referenced_query_ids", mode="after")
    @classmethod
    def sort_referenced_query_ids(cls, values: tuple[UUID, ...]) -> tuple[UUID, ...]:
        return tuple(sorted(set(values), key=str))

    def bump_version(self) -> QueryState:
        return self.model_copy(update={"context_version": self.context_version + 1})


class StateOperation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation: StateOperationType
    field: StateField | None = None
    value: Any = None
    filter_key: Literal["vendor_ids", "account_codes", "departments", "payout_status"] | None = None

    @model_validator(mode="after")
    def validate_operation_shape(self) -> Self:
        if self.operation != StateOperationType.RESET_ALL and self.field is None:
            raise ValueError("field is required unless operation is RESET_ALL")
        mutates_filter = self.operation in {StateOperationType.ADD, StateOperationType.REMOVE}
        if mutates_filter and not self.filter_key:
            raise ValueError("filter_key is required for ADD/REMOVE")
        return self


def apply_state_operation(state: QueryState, operation: StateOperation) -> QueryState:
    """Apply one deterministic operation without reading raw chat history."""
    if operation.operation == StateOperationType.RESET_ALL:
        return QueryState(context_version=state.context_version + 1)
    if operation.field is None:
        raise ValueError("field is required")

    if operation.operation in {StateOperationType.SET, StateOperationType.REPLACE}:
        return _replace_field(state, operation.field, operation.value).bump_version()

    if operation.operation == StateOperationType.CLEAR:
        return _clear_field(state, operation.field).bump_version()

    if operation.operation in {StateOperationType.ADD, StateOperationType.REMOVE}:
        return _mutate_filter(state, operation).bump_version()

    raise ValueError(f"Unsupported state operation {operation.operation}")


def _replace_field(state: QueryState, field: StateField, value: Any) -> QueryState:
    if field == StateField.METRIC:
        return state.model_copy(update={"metric": Metric(value) if value is not None else None})
    if field == StateField.DATE_RANGE:
        return state.model_copy(
            update={"date_range": DateRange.model_validate(value) if value is not None else None}
        )
    if field == StateField.FILTERS:
        return state.model_copy(update={"filters": QueryFilters.model_validate(value or {})})
    if field == StateField.GROUP_BY:
        return state.model_copy(update={"group_by": tuple(Dimension(item) for item in value or [])})
    if field == StateField.SORT:
        sort = tuple(SortSpec.model_validate(item) for item in value or [])
        return state.model_copy(update={"sort": sort})
    if field == StateField.COMPARISON:
        return state.model_copy(
            update={"comparison": Comparison.model_validate(value) if value is not None else None}
        )
    if field == StateField.REFERENCED_QUERY_IDS:
        referenced_query_ids = tuple(UUID(str(item)) for item in value or [])
        return state.model_copy(update={"referenced_query_ids": referenced_query_ids})
    if field == StateField.PENDING_CLARIFICATION:
        pending = PendingClarification.model_validate(value) if value is not None else None
        return state.model_copy(update={"pending_clarification": pending})
    raise ValueError(f"Unsupported field {field}")


def _clear_field(state: QueryState, field: StateField) -> QueryState:
    defaults = {
        StateField.METRIC: None,
        StateField.DATE_RANGE: None,
        StateField.FILTERS: QueryFilters(),
        StateField.GROUP_BY: (),
        StateField.SORT: (),
        StateField.COMPARISON: None,
        StateField.REFERENCED_QUERY_IDS: (),
        StateField.PENDING_CLARIFICATION: None,
    }
    return state.model_copy(update={field.value: defaults[field]})


def _mutate_filter(state: QueryState, operation: StateOperation) -> QueryState:
    if operation.filter_key is None:
        raise ValueError("filter_key is required")
    raw_filters = state.filters.model_dump(mode="json", exclude_none=True)
    existing = list(raw_filters.get(operation.filter_key) or [])
    if isinstance(operation.value, str):
        incoming = [operation.value]
    else:
        incoming = list(operation.value or [])

    if operation.operation == StateOperationType.ADD:
        merged = sorted({*existing, *incoming}, key=str)
    else:
        to_remove = {str(item) for item in incoming}
        merged = [item for item in existing if str(item) not in to_remove]

    raw_filters[operation.filter_key] = merged
    return state.model_copy(update={"filters": QueryFilters.model_validate(raw_filters)})
