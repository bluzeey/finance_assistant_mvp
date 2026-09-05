"""Pydantic QueryPlan contract models.

These models mirror the closed JSON contract and provide canonical hashing. They
carry resolved enums/IDs only; they never carry SQL.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date
from enum import StrEnum
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Intent(StrEnum):
    AGGREGATE = "aggregate"
    COMPARE = "compare"
    RANK = "rank"
    LIST = "list"
    DRILLDOWN = "drilldown"
    DETECT = "detect"
    METADATA = "metadata"
    CLARIFY = "clarify"
    REFUSE = "refuse"
    CORRECT = "correct"
    RESET = "reset"


class Metric(StrEnum):
    VENDOR_PAYOUT_AMOUNT = "vendor_payout_amount"
    NET_CASH_OUTFLOW = "net_cash_outflow"
    VENDOR_SPEND = "vendor_spend"
    UNRECONCILED_AMOUNT = "unreconciled_amount"
    UNRECONCILED_COUNT = "unreconciled_count"
    POSSIBLE_DUPLICATE_PAYOUTS = "possible_duplicate_payouts"
    VENDOR_PAYOUT_ANOMALY = "vendor_payout_anomaly"
    DATA_FRESHNESS = "data_freshness"


class DateField(StrEnum):
    PAYOUT_DATE = "payout_date"
    POSTING_DATE = "posting_date"
    TRANSACTION_DATE = "transaction_date"
    DOCUMENT_DATE = "document_date"
    DUE_DATE = "due_date"
    SCHEDULED_DATE = "scheduled_date"
    MATCHED_ON = "matched_on"
    LAST_REVIEWED_AT = "last_reviewed_at"


class CalendarBasis(StrEnum):
    EXPLICIT = "explicit"
    CALENDAR = "calendar"
    FISCAL = "fiscal"
    ROLLING = "rolling"


class Dimension(StrEnum):
    VENDOR_ID = "vendor_id"
    VENDOR_CATEGORY = "vendor_category"
    ACCOUNT_CODE = "account_code"
    DEPARTMENT = "department"
    COST_CENTER = "cost_center"
    PROJECT_CODE = "project_code"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    STATUS = "status"
    REASON_CODE = "reason_code"
    PAYMENT_METHOD = "payment_method"


class SortField(StrEnum):
    VALUE = "value"
    DATE = "date"
    VENDOR_NAME = "vendor_name"
    UNRECONCILED_AMOUNT = "unreconciled_amount"
    SOURCE_ROW_COUNT = "source_row_count"


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class PayoutStatus(StrEnum):
    COMPLETED = "completed"
    PENDING = "pending"
    FAILED = "failed"
    REVERSED = "reversed"


class TransactionStatus(StrEnum):
    POSTED = "posted"
    VOIDED = "voided"
    DRAFT = "draft"


class ReconciliationStatus(StrEnum):
    RECONCILED = "reconciled"
    UNRECONCILED = "unreconciled"
    PARTIALLY_RECONCILED = "partially_reconciled"
    DISPUTED = "disputed"


class Department(StrEnum):
    ENGINEERING = "Engineering"
    PRODUCT = "Product"
    DESIGN = "Design"
    FINANCE = "Finance"
    OPERATIONS = "Operations"
    SALES = "Sales"
    MARKETING = "Marketing"
    PEOPLE = "People"
    LEADERSHIP = "Leadership"


class AmountOperator(StrEnum):
    EQ = "eq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    BETWEEN = "between"


class ComparisonMode(StrEnum):
    PREVIOUS_PERIOD = "previous_period"
    EXPLICIT_PERIOD = "explicit_period"
    YEAR_OVER_YEAR = "year_over_year"


class DateRange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    start: date
    end_exclusive: date
    date_field: DateField
    source_phrase: str = Field(max_length=120)
    anchor_date: date
    calendar_basis: CalendarBasis

    @model_validator(mode="after")
    def check_half_open_range(self) -> Self:
        if self.start >= self.end_exclusive:
            raise ValueError("date_range.start must be before end_exclusive")
        return self


class AmountFilter(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operator: AmountOperator
    value: str | tuple[str, str]


class QueryFilters(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    vendor_ids: tuple[str, ...] = ()
    vendor_categories: tuple[str, ...] = ()
    account_codes: tuple[str, ...] = ()
    departments: tuple[Department, ...] = ()
    cost_centers: tuple[str, ...] = ()
    project_codes: tuple[str, ...] = ()
    transaction_ids: tuple[str, ...] = ()
    payout_ids: tuple[str, ...] = ()
    transaction_status: tuple[TransactionStatus, ...] = ()
    payout_status: tuple[PayoutStatus, ...] = ()
    reconciliation_status: tuple[ReconciliationStatus, ...] = ()
    reason_codes: tuple[str, ...] = ()
    payment_methods: tuple[str, ...] = ()
    amount: AmountFilter | None = None

    @field_validator(
        "vendor_ids",
        "vendor_categories",
        "account_codes",
        "departments",
        "cost_centers",
        "project_codes",
        "transaction_ids",
        "payout_ids",
        "transaction_status",
        "payout_status",
        "reconciliation_status",
        "reason_codes",
        "payment_methods",
        mode="after",
    )
    @classmethod
    def sort_unique(cls, values: tuple[Any, ...]) -> tuple[Any, ...]:
        return tuple(sorted(set(values), key=str))

    def non_empty_dict(self) -> dict[str, Any]:
        raw = self.model_dump(mode="json", exclude_none=True)
        return {key: value for key, value in raw.items() if value not in ([], (), None)}


class SortSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    field: SortField
    direction: SortDirection


class Comparison(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: ComparisonMode
    start: date
    end_exclusive: date

    @model_validator(mode="after")
    def check_range(self) -> Self:
        if self.start >= self.end_exclusive:
            raise ValueError("comparison.start must be before end_exclusive")
        return self


class Ambiguity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    field: str
    reason: str = Field(max_length=240)
    choices: tuple[dict[str, Any], ...]
    blocks_execution: Literal[True]


class QueryPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0.0"] = "1.0.0"
    intent: Intent
    metric: Metric | None
    date_range: DateRange | None
    filters: QueryFilters = Field(default_factory=QueryFilters)
    group_by: tuple[Dimension, ...] = ()
    sort: tuple[SortSpec, ...] = ()
    limit: int = Field(default=100, ge=1, le=500)
    comparison: Comparison | None = None
    ambiguities: tuple[Ambiguity, ...] = ()
    unsupported_fields: tuple[str, ...] = ()
    user_requested_explanation: bool = False
    user_requested_export: Literal["csv", "xlsx"] | None = None

    @field_validator("group_by", mode="after")
    @classmethod
    def sort_group_by(cls, values: tuple[Dimension, ...]) -> tuple[Dimension, ...]:
        return tuple(sorted(set(values), key=str))

    @field_validator("unsupported_fields", mode="after")
    @classmethod
    def sort_unsupported_fields(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(values)))

    @model_validator(mode="after")
    def check_metric_required_for_executable_intents(self) -> Self:
        blocked_intents = {Intent.CLARIFY, Intent.REFUSE, Intent.RESET}
        if self.intent not in blocked_intents and self.metric is None:
            raise ValueError("metric is required for executable QueryPlan intents")
        return self

    def canonical_payload(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json", exclude_none=False)
        payload["filters"] = self.filters.non_empty_dict()
        return payload

    def canonical_json(self) -> str:
        return json.dumps(self.canonical_payload(), sort_keys=True, separators=(",", ":"))

    def query_plan_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()
