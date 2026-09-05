from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from finance_assistant.answers.receipt_builder import build_answer_receipt
from finance_assistant.domain.query_plan import QueryPlan
from finance_assistant.query.compiler import CompiledQuery
from finance_assistant.query.executor import (
    BreakdownRow,
    DuplicateWarningPair,
    QueryExecutionResult,
)


def _plan() -> QueryPlan:
    return QueryPlan.model_validate(
        {
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
    )


def _compiled() -> CompiledQuery:
    return CompiledQuery(
        name="vendor_payout_amount",
        primary_sql="SELECT 1",
        primary_params=(),
        source_sql="SELECT payout_id",
        source_params=(),
        source_id_column="payout_id",
        expected_grain=("payout_id",),
        max_rows=100,
    )


def test_receipt_contains_only_computed_value_and_lineage() -> None:
    result = QueryExecutionResult(
        value=Decimal("10000874.04"),
        source_row_count=2,
        source_record_ids=("PAY-DUP-001", "PAY-DUP-002"),
        source_record_ids_hash="a" * 64,
        breakdown=(
            BreakdownRow("V0035", "GrowthMint Media", Decimal("10000874.04"), 2),
        ),
        duplicate_pairs=(DuplicateWarningPair("PAY-DUP-001", "PAY-DUP-002"),),
        query_ms=41,
    )

    receipt = build_answer_receipt(
        plan=_plan(),
        compiled=_compiled(),
        result=result,
        query_id=UUID("11111111-1111-4111-8111-111111111111"),
    )

    assert receipt["status"] == "verified"
    assert receipt["answer"]["value"] == "10000874.04"
    assert receipt["primary_metric"]["formatted_value"] == "₹1,00,00,874.04"
    assert receipt["lineage"]["source_row_count"] == 2
    assert receipt["warnings"][0]["record_ids"] == ["PAY-DUP-001", "PAY-DUP-002"]


def test_failed_required_validation_returns_no_financial_number() -> None:
    result = QueryExecutionResult(
        value=Decimal("100.00"),
        source_row_count=2,
        source_record_ids=("PAY-ONLY-001",),
        source_record_ids_hash="b" * 64,
        breakdown=(),
        duplicate_pairs=(),
        query_ms=1,
    )

    receipt = build_answer_receipt(plan=_plan(), compiled=_compiled(), result=result)

    assert receipt["status"] == "error"
    assert receipt["answer"]["value"] is None
    assert receipt["answer"]["currency"] is None
    assert receipt["primary_metric"] is None
    assert receipt["validation"]["passed"] is False
