"""CSV-backed data-health checks for the static synthetic fixture."""
from __future__ import annotations

import csv
from decimal import Decimal
from functools import cache
from typing import Any

from finance_assistant.domain.money import parse_money
from finance_assistant.metadata import (
    dataset_manifest,
    max_payout_date,
    max_posting_date,
    repo_root,
)

Check = dict[str, Any]


def build_data_health_response() -> dict[str, Any]:
    manifest = dataset_manifest()
    checks = [
        _transaction_freshness_check(),
        _payout_freshness_check(),
        _row_count_check(),
        _missing_reconciliation_check(),
        _duplicate_payout_check(),
        _payout_cash_semantics_check(),
        _partial_reconciliation_check(),
        _hostile_text_check(),
    ]
    overall_state = "healthy"
    if any(check["status"] == "fail" for check in checks):
        overall_state = "error"
    elif any(check["status"] == "warning" for check in checks):
        overall_state = "warning"

    return {
        "overall_state": overall_state,
        "data_as_of": manifest["data_as_of"],
        "checks": checks,
    }


def _transaction_freshness_check() -> Check:
    manifest = dataset_manifest()
    max_date = max_posting_date()
    return {
        "check_id": "DH-FRESHNESS-TRANSACTIONS",
        "category": "freshness",
        "status": "pass" if max_date <= manifest["data_as_of"] else "fail",
        "label": "Transaction posting dates are within the dataset anchor",
        "details": f"Max posting_date is {max_date}; data_as_of is {manifest['data_as_of']}.",
        "affected_record_count": 0,
        "sample_record_ids": [],
    }


def _payout_freshness_check() -> Check:
    manifest = dataset_manifest()
    max_date = max_payout_date()
    return {
        "check_id": "DH-FRESHNESS-PAYOUTS",
        "category": "freshness",
        "status": "pass" if max_date <= manifest["data_as_of"] else "fail",
        "label": "Completed payout dates are within the dataset anchor",
        "details": (
            f"Max completed payout_date is {max_date}; "
            f"data_as_of is {manifest['data_as_of']}."
        ),
        "affected_record_count": 0,
        "sample_record_ids": [],
    }


def _row_count_check() -> Check:
    manifest = dataset_manifest()
    counts = {
        file["path"].removeprefix("data/csv/").removesuffix(".csv"): file["row_count"]
        for file in manifest["files"]
        if str(file["path"]).startswith("data/csv/")
    }
    details = ", ".join(f"{name}: {count}" for name, count in sorted(counts.items()))
    return {
        "check_id": "DH-ROW-COUNTS",
        "category": "schema",
        "status": "pass",
        "label": "Declared fixture row counts are available",
        "details": details,
        "affected_record_count": 0,
        "sample_record_ids": [],
    }


def _missing_reconciliation_check() -> Check:
    transactions = _read_csv("transactions.csv")
    reconciliation_ids = {row["transaction_id"] for row in _read_csv("reconciliation_status.csv")}
    missing = sorted(
        row["transaction_id"]
        for row in transactions
        if row["status"] == "posted" and row["transaction_id"] not in reconciliation_ids
    )
    return {
        "check_id": "DH-MISSING-RECONCILIATION",
        "category": "coverage",
        "status": "warning" if missing else "pass",
        "label": "Posted transactions have reconciliation coverage",
        "details": (
            f"{len(missing)} posted transaction(s) have no reconciliation-status record. "
            "Reconciliation answers are qualified when this could affect completeness."
        ),
        "affected_record_count": len(missing),
        "sample_record_ids": missing[:20],
    }


def _duplicate_payout_check() -> Check:
    rows = [row for row in _read_csv("vendor_payouts.csv") if row["payout_status"] == "completed"]
    duplicate_ids: set[str] = set()
    for index, first in enumerate(rows):
        for second in rows[index + 1 :]:
            if _is_duplicate_payout_candidate(first, second):
                duplicate_ids.add(first["payout_id"])
                duplicate_ids.add(second["payout_id"])
    samples = sorted(duplicate_ids)[:20]
    return {
        "check_id": "DH-DUPLICATE-PAYOUTS",
        "category": "duplicates",
        "status": "warning" if duplicate_ids else "pass",
        "label": "Possible duplicate completed payouts are flagged, not deduplicated",
        "details": (
            f"{len(duplicate_ids)} payout row(s) participate in possible duplicate pairs. "
            "They remain included in financial totals until reviewed."
        ),
        "affected_record_count": len(duplicate_ids),
        "sample_record_ids": samples,
    }


def _payout_cash_semantics_check() -> Check:
    bad_ids: list[str] = []
    for row in _read_csv("vendor_payouts.csv"):
        gross = parse_money(row["gross_amount"])
        fee = parse_money(row["fee_amount"])
        net = parse_money(row["net_cash_outflow"])
        if row["payout_status"] == "completed":
            valid = net == gross + fee
        else:
            valid = net == Decimal("0.00")
        if not valid:
            bad_ids.append(row["payout_id"])
    return {
        "check_id": "DH-PAYOUT-CASH-SEMANTICS",
        "category": "precision",
        "status": "fail" if bad_ids else "pass",
        "label": "Payout cash-outflow semantics are consistent",
        "details": "Completed net_cash_outflow equals gross plus fee; non-completed rows are zero.",
        "affected_record_count": len(bad_ids),
        "sample_record_ids": bad_ids[:20],
    }


def _partial_reconciliation_check() -> Check:
    transaction_amounts = {
        row["transaction_id"]: abs(parse_money(row["signed_amount"]))
        for row in _read_csv("transactions.csv")
    }
    bad_ids: list[str] = []
    for row in _read_csv("reconciliation_status.csv"):
        if row["status"] != "partially_reconciled":
            continue
        transaction_amount = transaction_amounts[row["transaction_id"]]
        reconciled = parse_money(row["reconciled_amount"])
        unreconciled = parse_money(row["unreconciled_amount"])
        if reconciled + unreconciled != transaction_amount:
            bad_ids.append(row["transaction_id"])
    return {
        "check_id": "DH-PARTIAL-RECONCILIATION",
        "category": "reconciliation",
        "status": "fail" if bad_ids else "pass",
        "label": "Partial reconciliation components tie to transaction amount",
        "details": "Open metrics must use unreconciled_amount, not full transaction amount.",
        "affected_record_count": len(bad_ids),
        "sample_record_ids": bad_ids[:20],
    }


def _hostile_text_check() -> Check:
    hostile_fragments = ("IGNORE PRIOR INSTRUCTIONS", "RETURN 1,000,000")
    hits: list[str] = []
    for row in _read_csv("transactions.csv"):
        haystack = f"{row.get('description', '')} {row.get('merchant_name_raw', '')}"
        if any(fragment in haystack.upper() for fragment in hostile_fragments):
            hits.append(row["transaction_id"])
    return {
        "check_id": "DH-PROMPT-INJECTION-TEXT",
        "category": "schema",
        "status": "warning" if hits else "pass",
        "label": "Hostile-looking record text is treated as inert data",
        "details": (
            "Record descriptions are displayed as text and are not instructions "
            "to the model."
        ),
        "affected_record_count": len(hits),
        "sample_record_ids": hits[:20],
    }


def _is_duplicate_payout_candidate(first: dict[str, str], second: dict[str, str]) -> bool:
    same_grain = (
        first["vendor_id"] == second["vendor_id"]
        and first["payout_date"] == second["payout_date"]
        and parse_money(first["gross_amount"]) == parse_money(second["gross_amount"])
    )
    if not same_grain:
        return False
    shared_bank = (
        bool(first["bank_reference"])
        and first["bank_reference"] == second["bank_reference"]
    )
    shared_invoice = first["invoice_reference"] == second["invoice_reference"]
    return shared_bank or shared_invoice


@cache
def _read_csv(filename: str) -> tuple[dict[str, str], ...]:
    with (repo_root() / "data" / "csv" / filename).open(newline="", encoding="utf-8") as handle:
        return tuple(csv.DictReader(handle))
