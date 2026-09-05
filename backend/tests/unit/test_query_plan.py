from __future__ import annotations

from typing import Any, cast

import pytest
from pydantic import ValidationError

from finance_assistant.domain.query_plan import QueryPlan


def _base_plan() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "intent": "aggregate",
        "metric": "vendor_payout_amount",
        "date_range": {
            "start": "2026-08-01",
            "end_exclusive": "2026-09-01",
            "date_field": "payout_date",
            "source_phrase": "last month",
            "anchor_date": "2026-09-03",
            "calendar_basis": "calendar",
        },
        "filters": {"payout_status": ["completed"]},
        "group_by": [],
        "sort": [],
        "limit": 100,
        "comparison": None,
        "ambiguities": [],
        "unsupported_fields": [],
    }


def test_query_plan_rejects_unknown_fields_and_enums() -> None:
    raw = _base_plan()
    raw["sql"] = "select * from vendor_payouts"
    with pytest.raises(ValidationError):
        QueryPlan.model_validate(raw)

    bad_dimension = _base_plan()
    bad_dimension["group_by"] = ["raw_sql_table"]
    with pytest.raises(ValidationError):
        QueryPlan.model_validate(bad_dimension)


def test_query_plan_requires_metric_for_executable_intents() -> None:
    raw = _base_plan()
    raw["metric"] = None
    with pytest.raises(ValidationError):
        QueryPlan.model_validate(raw)

    clarification = _base_plan()
    clarification["intent"] = "clarify"
    clarification["metric"] = None
    QueryPlan.model_validate(clarification)


def test_query_plan_rejects_invalid_date_ranges() -> None:
    raw = _base_plan()
    date_range = dict(cast(dict[str, Any], raw["date_range"]))
    date_range["end_exclusive"] = "2026-08-01"
    raw["date_range"] = date_range

    with pytest.raises(ValidationError):
        QueryPlan.model_validate(raw)


def test_query_plan_hash_is_stable_for_equivalent_filter_order() -> None:
    first = _base_plan()
    first["filters"] = {"vendor_ids": ["V0003", "V0001"], "payout_status": ["completed"]}

    second = _base_plan()
    second["filters"] = {"payout_status": ["completed"], "vendor_ids": ["V0001", "V0003"]}

    first_plan = QueryPlan.model_validate(first)
    second_plan = QueryPlan.model_validate(second)

    assert first_plan.filters.vendor_ids == ("V0001", "V0003")
    assert first_plan.query_plan_hash() == second_plan.query_plan_hash()
