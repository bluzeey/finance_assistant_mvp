#!/usr/bin/env python3
"""Development-only deterministic evaluator for the synthetic Tiby finance fixture.

This module is an oracle for fixture generation and tests. Production application code
must implement the same semantic contract independently and must never read gold files
from ``evaluation/``.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable, Mapping, Sequence

MONEY_QUANT = Decimal("0.01")


def money(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def money_str(value: Decimal) -> str:
    return format(value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP), "f")


def parse_timestamp(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")


@dataclass(frozen=True)
class Fixture:
    banks: Sequence[Mapping[str, str]]
    accounts: Sequence[Mapping[str, str]]
    transactions: Sequence[Mapping[str, str]]

    @property
    def account_by_id(self) -> dict[str, Mapping[str, str]]:
        return {row["account_id"]: row for row in self.accounts}

    @property
    def bank_by_code(self) -> dict[str, Mapping[str, str]]:
        return {row["bank_code"]: row for row in self.banks}


def filter_transactions(
    fixture: Fixture,
    *,
    start: str | None = None,
    end: str | None = None,
    transaction_types: Iterable[str] | None = None,
    bank_codes: Iterable[str] | None = None,
    account_ids: Iterable[str] | None = None,
    entity_ids: Iterable[str] | None = None,
    program_ids: Iterable[int | str] | None = None,
    description_contains: str | None = None,
    transaction_reference_id: str | None = None,
    transaction_id: str | None = None,
) -> list[Mapping[str, str]]:
    """Apply the same predicates expected from the allow-listed query compiler.

    Date intervals are half-open: start inclusive, end exclusive. Reference matching is
    exact and case-sensitive. Description matching is a case-insensitive literal
    substring search and must be labelled as unstructured/qualified in user answers.
    """
    start_dt = parse_timestamp(start) if start else None
    end_dt = parse_timestamp(end) if end else None
    type_set = set(transaction_types or [])
    bank_set = set(bank_codes or [])
    account_set = set(account_ids or [])
    entity_set = set(entity_ids or [])
    program_set = {str(int(x)) for x in (program_ids or [])}
    needle = description_contains.casefold() if description_contains else None
    accounts = fixture.account_by_id

    result: list[Mapping[str, str]] = []
    for row in fixture.transactions:
        account = accounts[row["account_id"]]
        stamp = parse_timestamp(row["transaction_date"])
        if start_dt is not None and stamp < start_dt:
            continue
        if end_dt is not None and stamp >= end_dt:
            continue
        if type_set and row["transaction_type"] not in type_set:
            continue
        if bank_set and account["bank_code"] not in bank_set:
            continue
        if account_set and row["account_id"] not in account_set:
            continue
        if entity_set and account["entity_id"] not in entity_set:
            continue
        if program_set and str(int(account["program_id"])) not in program_set:
            continue
        if needle is not None and needle not in (row.get("description") or "").casefold():
            continue
        if transaction_reference_id is not None and row.get("transaction_reference_id") != transaction_reference_id:
            continue
        if transaction_id is not None and row["transaction_id"] != transaction_id:
            continue
        result.append(row)
    return result


def aggregate_metric(metric: str, rows: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    amounts = [money(row["transaction_amount"]) for row in rows]
    debits = [money(row["transaction_amount"]) for row in rows if row["transaction_type"] == "debit"]
    credits = [money(row["transaction_amount"]) for row in rows if row["transaction_type"] == "credit"]

    if metric == "debit_total":
        return {"value": money_str(sum(debits, Decimal("0.00"))), "unit": "INR", "record_count": len(debits)}
    if metric == "credit_total":
        return {"value": money_str(sum(credits, Decimal("0.00"))), "unit": "INR", "record_count": len(credits)}
    if metric == "net_cash_flow":
        value = sum(credits, Decimal("0.00")) - sum(debits, Decimal("0.00"))
        return {"value": money_str(value), "unit": "INR", "record_count": len(rows)}
    if metric == "transaction_count":
        return {"value": str(len(rows)), "unit": "records", "record_count": len(rows)}
    if metric == "average_transaction_amount":
        value = Decimal("0.00") if not amounts else sum(amounts, Decimal("0.00")) / Decimal(len(amounts))
        return {"value": money_str(value), "unit": "INR", "record_count": len(rows)}
    if metric == "largest_transaction":
        if not rows:
            return {"value": None, "unit": "INR", "record_count": 0, "record": None}
        largest = max(rows, key=lambda row: (money(row["transaction_amount"]), row["transaction_id"]))
        return {
            "value": money_str(money(largest["transaction_amount"])),
            "unit": "INR",
            "record_count": len(rows),
            "record": dict(largest),
        }
    raise ValueError(f"Unsupported transaction metric: {metric}")


def current_balance(
    fixture: Fixture,
    *,
    bank_codes: Iterable[str] | None = None,
    account_ids: Iterable[str] | None = None,
    entity_ids: Iterable[str] | None = None,
    program_ids: Iterable[int | str] | None = None,
) -> dict[str, Any]:
    bank_set = set(bank_codes or [])
    account_set = set(account_ids or [])
    entity_set = set(entity_ids or [])
    program_set = {str(int(x)) for x in (program_ids or [])}
    rows = []
    for row in fixture.accounts:
        if bank_set and row["bank_code"] not in bank_set:
            continue
        if account_set and row["account_id"] not in account_set:
            continue
        if entity_set and row["entity_id"] not in entity_set:
            continue
        if program_set and str(int(row["program_id"])) not in program_set:
            continue
        rows.append(row)
    value = sum((money(row["available_balance"]) for row in rows), Decimal("0.00"))
    return {"value": money_str(value), "unit": "INR", "record_count": len(rows), "records": rows}


def group_transactions(
    fixture: Fixture,
    rows: Sequence[Mapping[str, str]],
    *,
    metric: str,
    dimension: str,
) -> list[dict[str, Any]]:
    accounts = fixture.account_by_id
    banks = fixture.bank_by_code
    groups: dict[str, list[Mapping[str, str]]] = {}
    for row in rows:
        account = accounts[row["account_id"]]
        stamp = parse_timestamp(row["transaction_date"])
        if dimension == "bank_code":
            key = account["bank_code"]
        elif dimension == "bank_name":
            key = banks[account["bank_code"]]["bank_name"]
        elif dimension == "account_id":
            key = row["account_id"]
        elif dimension == "entity_id":
            key = account["entity_id"]
        elif dimension == "program_id":
            key = str(int(account["program_id"]))
        elif dimension == "transaction_type":
            key = row["transaction_type"]
        elif dimension == "day":
            key = stamp.strftime("%Y-%m-%d")
        elif dimension == "month":
            key = stamp.strftime("%Y-%m")
        else:
            raise ValueError(f"Unsupported group dimension: {dimension}")
        groups.setdefault(key, []).append(row)

    output: list[dict[str, Any]] = []
    for key, group_rows in groups.items():
        aggregate = aggregate_metric(metric, group_rows)
        output.append({"key": key, **aggregate})
    output.sort(key=lambda item: (Decimal(item["value"]) if item["unit"] == "INR" and item["value"] is not None else Decimal(item["record_count"])), reverse=True)
    return output
