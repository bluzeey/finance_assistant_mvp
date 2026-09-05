"""Execute compiled finance queries and collect typed result facts."""
from __future__ import annotations

import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol

from django.db import connection, transaction

from finance_assistant.domain.money import money_to_api, parse_money
from finance_assistant.query.compiler import CompiledQuery
from finance_assistant.query.lineage import source_ids_hash


class CursorLike(Protocol):
    def execute(self, query: str, params: tuple[Any, ...] | None = None) -> Any: ...
    def fetchone(self) -> tuple[Any, ...] | None: ...
    def fetchall(self) -> list[tuple[Any, ...]]: ...


@dataclass(frozen=True, slots=True)
class BreakdownRow:
    vendor_id: str
    vendor: str
    amount: Decimal
    source_row_count: int

    def to_receipt_row(self) -> dict[str, str | int]:
        return {
            "vendor_id": self.vendor_id,
            "vendor": self.vendor,
            "amount": money_to_api(self.amount),
            "source_row_count": self.source_row_count,
        }


@dataclass(frozen=True, slots=True)
class DuplicateWarningPair:
    payout_id_a: str
    payout_id_b: str


@dataclass(frozen=True, slots=True)
class QueryExecutionResult:
    value: Decimal
    source_row_count: int
    source_record_ids: tuple[str, ...]
    source_record_ids_hash: str
    breakdown: tuple[BreakdownRow, ...]
    duplicate_pairs: tuple[DuplicateWarningPair, ...]
    query_ms: int


def execute_compiled_query(compiled: CompiledQuery) -> QueryExecutionResult:
    """Execute a compiled query using Django's configured PostgreSQL connection."""
    with transaction.atomic(), connection.cursor() as cursor:
        return execute_compiled_query_with_cursor(cursor, compiled, configure_read_only=True)


def execute_compiled_query_with_cursor(
    cursor: CursorLike,
    compiled: CompiledQuery,
    *,
    configure_read_only: bool = False,
) -> QueryExecutionResult:
    start = time.perf_counter()
    if configure_read_only:
        _configure_read_only(cursor)

    cursor.execute(compiled.primary_sql, compiled.primary_params)
    primary_row = cursor.fetchone()
    if primary_row is None:
        value = Decimal("0.00")
        source_row_count = 0
    else:
        value = parse_money(primary_row[0])
        source_row_count = int(primary_row[1])

    cursor.execute(compiled.source_sql, compiled.source_params)
    source_ids = tuple(str(row[0]) for row in cursor.fetchall())

    breakdown_rows: tuple[BreakdownRow, ...] = ()
    if compiled.breakdown_sql is not None:
        cursor.execute(compiled.breakdown_sql, compiled.breakdown_params)
        breakdown_rows = tuple(
            BreakdownRow(
                vendor_id=str(row[0]),
                vendor=str(row[1]),
                amount=parse_money(row[2]),
                source_row_count=int(row[3]),
            )
            for row in cursor.fetchall()
        )

    duplicate_pairs: tuple[DuplicateWarningPair, ...] = ()
    if compiled.duplicate_warning_sql is not None:
        cursor.execute(compiled.duplicate_warning_sql, compiled.duplicate_warning_params)
        duplicate_pairs = tuple(
            DuplicateWarningPair(payout_id_a=str(row[0]), payout_id_b=str(row[1]))
            for row in cursor.fetchall()
        )

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    return QueryExecutionResult(
        value=value,
        source_row_count=source_row_count,
        source_record_ids=source_ids,
        source_record_ids_hash=source_ids_hash(compiled.source_id_column, source_ids),
        breakdown=breakdown_rows,
        duplicate_pairs=duplicate_pairs,
        query_ms=elapsed_ms,
    )


def _configure_read_only(cursor: CursorLike) -> None:
    # SET LOCAL is supported in PostgreSQL and is scoped to the current transaction.
    cursor.execute("SET TRANSACTION READ ONLY")
    cursor.execute("SET LOCAL statement_timeout = '3000ms'")
    cursor.execute("SET LOCAL idle_in_transaction_session_timeout = '5000ms'")
