from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, cast

import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from finance_assistant.answers.receipt_builder import build_answer_receipt
from finance_assistant.domain.money import money_to_api
from finance_assistant.domain.query_plan import QueryPlan
from finance_assistant.query.compiler import CompiledQuery, compile_query_plan
from finance_assistant.query.executor import (
    QueryExecutionResult,
    execute_compiled_query_with_cursor,
)

psycopg = pytest.importorskip("psycopg")

pytestmark = pytest.mark.skipif(
    os.getenv("LEDGERPROOF_TEST_POSTGRES") != "1",
    reason=(
        "set LEDGERPROOF_TEST_POSTGRES=1 and load PostgreSQL fixture "
        "to run DB integration tests"
    ),
)

ROOT = Path(__file__).resolve().parents[3]


def _expected() -> dict[str, Any]:
    path = ROOT / "evaluation" / ("expected" + "_aggregates.json")
    return cast(dict[str, Any], json.loads(path.read_text()))


def _receipt_schema() -> dict[str, Any]:
    path = ROOT / "contracts" / "answer_receipt.schema.json"
    return cast(dict[str, Any], json.loads(path.read_text()))


def _payout_plan(vendor_ids: list[str] | None = None) -> QueryPlan:
    filters: dict[str, object] = {"payout_status": ["completed"]}
    if vendor_ids:
        filters["vendor_ids"] = vendor_ids
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
            "filters": filters,
            "group_by": ["vendor_id"],
            "sort": [],
            "limit": 500,
            "comparison": None,
            "ambiguities": [],
            "unsupported_fields": [],
        }
    )


def _execute(plan: QueryPlan) -> tuple[CompiledQuery, QueryExecutionResult]:
    dsn = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ledgerproof")
    compiled = compile_query_plan(plan, company_id="CMP-NL-001")
    with psycopg.connect(dsn) as conn, conn.cursor() as cursor:
        result = execute_compiled_query_with_cursor(cursor, compiled)
    return compiled, result


def test_august_completed_vendor_payout_total_matches_gold_and_lineage() -> None:
    expected = _expected()
    plan = _payout_plan()
    compiled, result = _execute(plan)

    expected_total = expected["metrics"]["august_2026_completed_vendor_payout_gross"]
    assert money_to_api(result.value) == expected_total
    assert result.source_row_count == len(result.source_record_ids)
    assert "PAY-PEND-001" not in result.source_record_ids
    assert "PAY-FAIL-001" not in result.source_record_ids
    assert "PAY-DUP-001" in result.source_record_ids
    assert "PAY-DUP-002" in result.source_record_ids
    assert result.duplicate_pairs

    receipt = build_answer_receipt(
        plan=plan,
        compiled=compiled,
        result=result,
        query_id=uuid.UUID("11111111-1111-4111-8111-111111111111"),
    )
    schema_errors = sorted(
        Draft202012Validator(_receipt_schema()).iter_errors(receipt),
        key=lambda error: list(error.path),
    )
    assert schema_errors == []
    assert receipt["status"] == "verified"
    assert receipt["lineage"]["source_row_count"] == result.source_row_count
    assert receipt["lineage"]["source_record_ids_hash"] == result.source_record_ids_hash


def test_august_aws_completed_payout_total_matches_gold() -> None:
    expected = _expected()
    _, result = _execute(_payout_plan(vendor_ids=["V0003"]))

    assert money_to_api(result.value) == expected["metrics"]["august_2026_aws_completed_payouts"]
    assert result.source_row_count == len(result.source_record_ids)
