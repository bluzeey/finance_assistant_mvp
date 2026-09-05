from __future__ import annotations

from typing import cast

import pytest

from finance_assistant.domain.query_plan import QueryPlan
from finance_assistant.query.compiler import UnsupportedQueryPlan, compile_query_plan


def _payout_plan(**overrides: object) -> QueryPlan:
    raw: dict[str, object] = {
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
        "group_by": ["vendor_id"],
        "sort": [],
        "limit": 100,
        "comparison": None,
        "ambiguities": [],
        "unsupported_fields": [],
    }
    raw.update(overrides)
    return QueryPlan.model_validate(raw)


def test_completed_payout_compiler_uses_bound_params_and_hardcoded_status() -> None:
    compiled = compile_query_plan(_payout_plan(), company_id="CMP-NL-001")

    assert compiled.name == "vendor_payout_amount"
    assert compiled.source_id_column == "payout_id"
    assert "p.payout_status = 'completed'" in compiled.primary_sql
    assert "2026-08-01" not in compiled.primary_sql
    assert compiled.primary_params[0] == "CMP-NL-001"
    assert len(compiled.primary_params) == 3
    assert compiled.breakdown_sql is not None


def test_vendor_filter_is_bound_as_value_not_spliced_into_sql() -> None:
    compiled = compile_query_plan(
        _payout_plan(filters={"payout_status": ["completed"], "vendor_ids": ["V0003"]}),
        company_id="CMP-NL-001",
    )

    bound_vendor_ids = cast(list[str], compiled.primary_params[-1])
    assert "V0003" not in compiled.primary_sql
    assert bound_vendor_ids == ["V0003"]
    assert "p.vendor_id = ANY(%s::text[])" in compiled.primary_sql


def test_non_completed_status_cannot_reach_database() -> None:
    plan = _payout_plan(filters={"payout_status": ["pending"]})

    with pytest.raises(UnsupportedQueryPlan):
        compile_query_plan(plan, company_id="CMP-NL-001")


def test_wrong_date_field_cannot_reach_database() -> None:
    raw_date_range = {
        "start": "2026-08-01",
        "end_exclusive": "2026-09-01",
        "date_field": "posting_date",
        "source_phrase": "last month",
        "anchor_date": "2026-09-03",
        "calendar_basis": "calendar",
    }
    plan = _payout_plan(date_range=raw_date_range)

    with pytest.raises(UnsupportedQueryPlan):
        compile_query_plan(plan, company_id="CMP-NL-001")


def test_unsupported_metric_cannot_reach_database() -> None:
    plan = _payout_plan(metric="vendor_spend")

    with pytest.raises(UnsupportedQueryPlan):
        compile_query_plan(plan, company_id="CMP-NL-001")
