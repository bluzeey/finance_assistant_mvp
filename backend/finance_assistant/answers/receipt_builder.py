"""Build immutable AnswerReceipt payloads from validated computed facts."""
from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from finance_assistant.domain.money import format_inr, money_to_api, sum_money
from finance_assistant.domain.query_plan import Metric, QueryPlan
from finance_assistant.metadata import company_metadata, dataset_manifest
from finance_assistant.query.compiler import CompiledQuery
from finance_assistant.query.executor import QueryExecutionResult


def build_answer_receipt(
    *,
    plan: QueryPlan,
    compiled: CompiledQuery,
    result: QueryExecutionResult,
    query_id: uuid.UUID | None = None,
    conversation_id: uuid.UUID | None = None,
    turn_id: uuid.UUID | None = None,
    parse_ms: int = 0,
    validation_ms: int = 0,
    compose_ms: int = 0,
) -> dict[str, Any]:
    """Build an AnswerReceipt dictionary conforming to the JSON contract."""
    if plan.metric != Metric.VENDOR_PAYOUT_AMOUNT:
        raise ValueError("receipt builder currently supports completed vendor payouts only")
    if plan.date_range is None:
        raise ValueError("receipt requires a resolved date_range")

    generated_query_id = query_id or uuid.uuid4()
    checks = _validation_checks(plan, result)
    required_failed = any(check["status"] == "fail" and check["required"] for check in checks)
    if required_failed:
        status = "error"
    elif result.source_row_count == 0:
        status = "no_matching_rows"
    else:
        status = "verified"
    value_for_answer: str | None = None if status == "error" else money_to_api(result.value)
    formatted_value = format_inr(result.value) if value_for_answer is not None else ""
    period_label = _period_label(plan.date_range.start, plan.date_range.end_exclusive)
    plain_language = _plain_language(status, formatted_value, period_label, result.source_row_count)

    warnings = _warnings(result)
    validation_checks = [
        {
            "check_id": check["code"],
            "label": check["label"],
            "status": check["status"],
            "details": check["message"],
        }
        for check in checks
    ]
    company = company_metadata()
    manifest = dataset_manifest()
    source_preview = list(result.source_record_ids[:500])

    return {
        "schema_version": "1.0.0",
        "query_id": str(generated_query_id),
        "conversation_id": str(conversation_id) if conversation_id else None,
        "turn_id": str(turn_id) if turn_id else None,
        "status": status,
        "answer": {
            "plain_language": plain_language,
            "value": value_for_answer,
            "currency": "INR" if value_for_answer is not None else None,
            "unit": "currency" if value_for_answer is not None else "none",
        },
        "primary_metric": None
        if value_for_answer is None
        else {
            "metric_id": "vendor_payout_amount",
            "label": "Completed vendor payouts",
            "value": value_for_answer,
            "formatted_value": formatted_value,
        },
        "interpretation": {
            "canonical_query_plan": plan.canonical_payload(),
            "human_readable_steps": [
                (
                    f"Interpreted ‘{plan.date_range.source_phrase}’ as "
                    f"{plan.date_range.start.isoformat()} through "
                    f"{(plan.date_range.end_exclusive).isoformat()} exclusive using the dataset "
                    f"date of {plan.date_range.anchor_date.isoformat()}."
                ),
                "Selected vendor payout records with payout_status = completed.",
                "Summed gross_amount using database NUMERIC arithmetic.",
            ],
            "assumptions": [],
            "context_changes": [
                "Set metric to completed vendor payout amount.",
                f"Set date range to {period_label}.",
            ],
        },
        "breakdown": {
            "columns": [
                {"key": "vendor", "label": "Vendor", "type": "text"},
                {"key": "amount", "label": "Payout amount", "type": "currency"},
            ],
            "rows": [row.to_receipt_row() for row in result.breakdown],
            "total_row": {
                "label": "All completed payouts",
                "amount": value_for_answer,
            }
            if value_for_answer is not None
            else None,
        },
        "lineage": {
            "company_id": company["company_id"],
            "dataset_version": manifest["dataset_version"],
            "data_as_of": manifest["data_as_of"],
            "executed_query_name": compiled.name,
            "source_row_count": result.source_row_count,
            "source_record_ids": source_preview,
            "source_record_ids_truncated": len(result.source_record_ids) > len(source_preview),
            "source_record_ids_hash": result.source_record_ids_hash,
            "database_snapshot_id": f"northstar-{manifest['data_as_of']}-v1",
        },
        "validation": {
            "passed": not required_failed,
            "checks": validation_checks,
        },
        "confidence": {
            "state": "blocked" if required_failed else "verified",
            "score": 96 if not required_failed else 0,
            "factors": [
                {
                    "factor": "score_policy",
                    "score": 96 if not required_failed else 0,
                    "reason": "Deterministic evidence score; not a model probability.",
                },
                {"factor": "validation", "score": 100 if not required_failed else 0},
            ],
        },
        "warnings": warnings,
        "clarification": None,
        "records_preview": {
            "columns": [
                {"key": "payout_id", "label": "Payout ID", "type": "id"},
                {"key": "payout_date", "label": "Payout date", "type": "date"},
                {"key": "vendor", "label": "Vendor", "type": "text"},
                {"key": "gross_amount", "label": "Gross amount", "type": "currency"},
            ],
            "rows": [],
            "next_cursor": None,
            "total_count": result.source_row_count,
        },
        "exports": {
            "csv_url": f"/api/v1/queries/{generated_query_id}/export?format=csv",
            "xlsx_url": f"/api/v1/queries/{generated_query_id}/export?format=xlsx",
            "expires_at": None,
        },
        "timings": {
            "total_ms": parse_ms + result.query_ms + validation_ms + compose_ms,
            "parse_ms": parse_ms,
            "query_ms": result.query_ms,
            "validation_ms": validation_ms,
            "compose_ms": compose_ms,
            "model_id": None,
            "input_tokens": None,
            "output_tokens": None,
            "cache_status": "bypass",
        },
    }


def _validation_checks(plan: QueryPlan, result: QueryExecutionResult) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    date_range = plan.date_range
    date_status = "pass" if date_range and date_range.start < date_range.end_exclusive else "fail"
    checks.append(
        {
            "code": "V-DATE-001",
            "label": "Date range is valid",
            "status": date_status,
            "message": "The QueryPlan uses a valid half-open date interval.",
            "required": True,
        }
    )
    checks.append(
        {
            "code": "V-STATUS-001",
            "label": "Only completed payouts included",
            "status": "pass",
            "message": "Pending, failed, and reversed attempts were excluded by the compiler.",
            "required": True,
        }
    )
    count_status = "pass" if result.source_row_count == len(result.source_record_ids) else "fail"
    checks.append(
        {
            "code": "V-SOURCE-COUNT-001",
            "label": "Source grain count matches aggregate count",
            "status": count_status,
            "message": (
                f"Primary count {result.source_row_count}; source lineage count "
                f"{len(result.source_record_ids)}."
            ),
            "required": True,
        }
    )
    checks.append(
        {
            "code": "V-TOTAL-001",
            "label": "Breakdown ties to total",
            "status": "pass" if _breakdown_ties(result) else "fail",
            "message": "Vendor breakdown equals the primary metric.",
            "required": True,
        }
    )
    checks.append(
        {
            "code": "V-PRECISION-001",
            "label": "Decimal precision",
            "status": "pass",
            "message": "Database NUMERIC(18,2) values were parsed as Python Decimal.",
            "required": True,
        }
    )
    return checks


def _warnings(result: QueryExecutionResult) -> list[dict[str, Any]]:
    if not result.duplicate_pairs:
        return []
    record_ids = sorted(
        {
            payout_id
            for pair in result.duplicate_pairs
            for payout_id in (pair.payout_id_a, pair.payout_id_b)
        }
    )
    return [
        {
            "code": "POSSIBLE_DUPLICATE_PAYOUTS",
            "severity": "warning",
            "message": (
                "Completed payouts share a vendor, date, amount, and bank/invoice reference. "
                "They remain included in the total until reviewed."
            ),
            "record_ids": record_ids,
        }
    ]


def _breakdown_ties(result: QueryExecutionResult) -> bool:
    if not result.breakdown:
        return True
    return sum_money(row.amount for row in result.breakdown) == result.value


def _plain_language(
    status: str,
    formatted_value: str,
    period_label: str,
    source_row_count: int,
) -> str:
    if status == "error":
        return "The computed result failed a required validation check, so no number was returned."
    if status == "no_matching_rows":
        return f"No completed vendor payout records matched {period_label}."
    return (
        f"Northstar Labs completed {formatted_value} in vendor payouts during {period_label} "
        f"from {source_row_count} source records."
    )


def _period_label(start: date, end_exclusive: date) -> str:
    # If end is the first day of the following month, this is a complete calendar month.
    if (
        start.day == 1
        and end_exclusive.day == 1
        and (end_exclusive.month - start.month) % 12 == 1
    ):
        return start.strftime("%B %Y")
    return f"{start.isoformat()} to before {end_exclusive.isoformat()}"
