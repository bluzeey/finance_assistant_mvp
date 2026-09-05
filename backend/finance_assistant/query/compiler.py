"""Allow-listed SQL compiler registry.

The compiler dispatches only on trusted QueryPlan enums. SQL templates are owned
by application code; user/model text can only become bound parameter values.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from finance_assistant.domain.query_plan import (
    DateField,
    Dimension,
    Intent,
    Metric,
    PayoutStatus,
    QueryPlan,
)

type DbScalar = str | int | date | Decimal
type DbParams = tuple[DbScalar | list[str], ...]


class UnsupportedQueryPlan(ValueError):
    """Raised before database access when a plan is outside the allow-list."""


@dataclass(frozen=True, slots=True)
class CompiledQuery:
    name: str
    primary_sql: str
    primary_params: DbParams
    source_sql: str
    source_params: DbParams
    source_id_column: str
    expected_grain: tuple[str, ...]
    max_rows: int
    breakdown_sql: str | None = None
    breakdown_params: DbParams = ()
    duplicate_warning_sql: str | None = None
    duplicate_warning_params: DbParams = ()


COMPILER_KEYS = frozenset({(Intent.AGGREGATE, Metric.VENDOR_PAYOUT_AMOUNT)})


def compile_query_plan(plan: QueryPlan, company_id: str) -> CompiledQuery:
    """Compile a canonical QueryPlan into one of the named read-only SQL shapes."""
    key = (plan.intent, plan.metric)
    if key == (Intent.AGGREGATE, Metric.VENDOR_PAYOUT_AMOUNT):
        return compile_completed_payout_total(plan, company_id)
    raise UnsupportedQueryPlan(f"Unsupported compiler key: {plan.intent}/{plan.metric}")


def compile_completed_payout_total(plan: QueryPlan, company_id: str) -> CompiledQuery:
    if plan.date_range is None:
        raise UnsupportedQueryPlan("vendor_payout_amount requires a date_range")
    if plan.metric != Metric.VENDOR_PAYOUT_AMOUNT or plan.intent != Intent.AGGREGATE:
        raise UnsupportedQueryPlan("plan is not a completed payout aggregate")
    if plan.date_range.date_field != DateField.PAYOUT_DATE:
        raise UnsupportedQueryPlan("vendor_payout_amount must use payout_date")

    requested_statuses = set(plan.filters.payout_status)
    if requested_statuses and requested_statuses != {PayoutStatus.COMPLETED}:
        raise UnsupportedQueryPlan("completed payout amount cannot include non-completed statuses")

    where_sql, where_params = _completed_payout_where_clause(plan, company_id)
    primary_sql = f"""
        SELECT coalesce(sum(p.gross_amount), 0)::numeric(18,2) AS value,
               count(*)::integer AS source_row_count
        FROM vendor_payouts p
        {where_sql}
    """
    source_sql = f"""
        SELECT p.payout_id
        FROM vendor_payouts p
        {where_sql}
        ORDER BY p.payout_date ASC, p.payout_id ASC
    """
    breakdown_sql = f"""
        SELECT p.vendor_id,
               v.display_name AS vendor,
               sum(p.gross_amount)::numeric(18,2) AS amount,
               count(*)::integer AS source_row_count
        FROM vendor_payouts p
        JOIN vendors v USING (vendor_id)
        {where_sql}
        GROUP BY p.vendor_id, v.display_name
        ORDER BY amount DESC, vendor ASC, p.vendor_id ASC
        LIMIT %s
    """
    duplicate_sql = f"""
        SELECT p1.payout_id AS payout_id_a, p2.payout_id AS payout_id_b
        FROM vendor_payouts p1
        JOIN vendor_payouts p2
          ON p1.company_id = p2.company_id
         AND p1.vendor_id = p2.vendor_id
         AND p1.payout_date = p2.payout_date
         AND p1.gross_amount = p2.gross_amount
         AND p1.payout_id < p2.payout_id
         AND (
           (p1.bank_reference IS NOT NULL AND p1.bank_reference = p2.bank_reference)
           OR p1.invoice_reference = p2.invoice_reference
         )
        WHERE p1.company_id = %s
          AND p1.payout_status = 'completed'
          AND p2.payout_status = 'completed'
          AND p1.payout_date >= %s
          AND p1.payout_date < %s
        {_vendor_filter_sql('p1', plan)}
        ORDER BY p1.payout_id ASC, p2.payout_id ASC
    """
    duplicate_params = _duplicate_params(plan, company_id)

    return CompiledQuery(
        name="vendor_payout_amount",
        primary_sql=primary_sql,
        primary_params=where_params,
        source_sql=source_sql,
        source_params=where_params,
        source_id_column="payout_id",
        expected_grain=("payout_id",),
        max_rows=plan.limit,
        breakdown_sql=breakdown_sql,
        breakdown_params=(*where_params, min(plan.limit, 500)),
        duplicate_warning_sql=duplicate_sql,
        duplicate_warning_params=duplicate_params,
    )


def _completed_payout_where_clause(plan: QueryPlan, company_id: str) -> tuple[str, DbParams]:
    if plan.date_range is None:
        raise UnsupportedQueryPlan("date_range required")
    clauses = [
        "p.company_id = %s",
        "p.payout_status = 'completed'",
        "p.payout_date >= %s",
        "p.payout_date < %s",
    ]
    params: list[DbScalar | list[str]] = [
        company_id,
        plan.date_range.start,
        plan.date_range.end_exclusive,
    ]
    vendor_ids = list(plan.filters.vendor_ids)
    if vendor_ids:
        clauses.append("p.vendor_id = ANY(%s::text[])")
        params.append(vendor_ids)

    unsupported_group_by = set(plan.group_by) - {Dimension.VENDOR_ID}
    if unsupported_group_by:
        raise UnsupportedQueryPlan("unsupported group_by for completed payout total")

    return "WHERE " + "\n          AND ".join(clauses), tuple(params)


def _vendor_filter_sql(alias: str, plan: QueryPlan) -> str:
    if not plan.filters.vendor_ids:
        return ""
    return f"AND {alias}.vendor_id = ANY(%s::text[])"


def _duplicate_params(plan: QueryPlan, company_id: str) -> DbParams:
    if plan.date_range is None:
        raise UnsupportedQueryPlan("date_range required")
    params: list[DbScalar | list[str]] = [
        company_id,
        plan.date_range.start,
        plan.date_range.end_exclusive,
    ]
    if plan.filters.vendor_ids:
        params.append(list(plan.filters.vendor_ids))
    return tuple(params)
