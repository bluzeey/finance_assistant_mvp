#!/usr/bin/env python3
"""Fail-fast integrity and finance-semantic validation for the sample dataset."""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "data" / "csv"
EVAL_DIR = ROOT / "evaluation"
DATA_AS_OF = date(2026, 9, 3)
OPEN_STATUSES = {"unreconciled", "partially_reconciled", "disputed"}
errors: list[str] = []
warnings: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def warn(message: str) -> None:
    warnings.append(message)


def rows(name: str) -> list[dict[str, str]]:
    path = CSV_DIR / name
    if not path.exists():
        fail(f"Missing file: {path}")
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def unique(data: list[dict[str, str]], key: str, label: str) -> None:
    counts = Counter(r[key] for r in data)
    dupes = [v for v, n in counts.items() if n > 1]
    if dupes:
        fail(f"{label}.{key} has duplicate values: {dupes[:10]}")


def decimal(value: str, context: str) -> Decimal:
    try:
        d = Decimal(value)
    except InvalidOperation:
        fail(f"Invalid decimal in {context}: {value!r}")
        return Decimal("0")
    if d.as_tuple().exponent < -2:
        fail(f"More than 2 decimal places in {context}: {value}")
    return d


def require_subset(values: set[str], allowed: set[str], context: str) -> None:
    bad = values - allowed
    if bad:
        fail(f"Unexpected {context}: {sorted(bad)}")


def main() -> int:
    coa = rows("chart_of_accounts.csv")
    vendors = rows("vendors.csv")
    aliases = rows("vendor_aliases.csv")
    txns = rows("transactions.csv")
    payouts = rows("vendor_payouts.csv")
    recs = rows("reconciliation_status.csv")
    dictionary = rows("data_dictionary.csv")

    unique(coa, "account_code", "chart_of_accounts")
    unique(vendors, "vendor_id", "vendors")
    unique(aliases, "alias_id", "vendor_aliases")
    unique(txns, "transaction_id", "transactions")
    unique(payouts, "payout_id", "vendor_payouts")
    unique(recs, "reconciliation_id", "reconciliation_status")
    unique(recs, "transaction_id", "reconciliation_status")

    account_ids = {r["account_code"] for r in coa}
    vendor_ids = {r["vendor_id"] for r in vendors}
    txn_ids = {r["transaction_id"] for r in txns}
    if {r["vendor_id"] for r in aliases} - vendor_ids:
        fail("vendor_aliases contains unknown vendor_id")
    if {r["default_account_code"] for r in vendors} - account_ids:
        fail("vendors contains unknown default_account_code")
    if {r["vendor_id"] for r in txns} - vendor_ids:
        fail("transactions contains unknown vendor_id")
    if {r["account_code"] for r in txns} - account_ids:
        fail("transactions contains unknown account_code")
    if {r["vendor_id"] for r in payouts} - vendor_ids:
        fail("vendor_payouts contains unknown vendor_id")
    if {r["invoice_transaction_id"] for r in payouts} - txn_ids:
        fail("vendor_payouts contains unknown invoice_transaction_id")
    if {r["transaction_id"] for r in recs} - txn_ids:
        fail("reconciliation_status contains unknown transaction_id")

    require_subset({r["status"] for r in txns}, {"posted","voided","draft"}, "transaction status")
    require_subset({r["payout_status"] for r in payouts}, {"completed","pending","failed","reversed"}, "payout status")
    require_subset({r["status"] for r in recs}, {"reconciled","unreconciled","partially_reconciled","disputed"}, "reconciliation status")
    require_subset({r["currency"] for r in txns + payouts + recs}, {"INR"}, "currency")

    tx_by_id = {r["transaction_id"]: r for r in txns}
    rec_by_tx = {r["transaction_id"]: r for r in recs}
    for t in txns:
        amount = decimal(t["signed_amount"], f"transaction {t['transaction_id']}")
        if date.fromisoformat(t["posting_date"]) > DATA_AS_OF:
            fail(f"Future posting date on {t['transaction_id']}")
        if t["is_reversal"] == "true":
            if not t["reverses_transaction_id"] or t["reverses_transaction_id"] not in txn_ids:
                fail(f"Broken reversal link on {t['transaction_id']}")
            if amount >= 0:
                fail(f"Reversal must carry negative signed amount: {t['transaction_id']}")
        elif t["reverses_transaction_id"]:
            fail(f"Non-reversal has reverses_transaction_id: {t['transaction_id']}")
        if t["status"] == "voided" and amount != 0:
            warn(f"Voided transaction has nonzero amount: {t['transaction_id']}")

    for p in payouts:
        gross = decimal(p["gross_amount"], f"payout {p['payout_id']} gross")
        fee = decimal(p["fee_amount"], f"payout {p['payout_id']} fee")
        cash = decimal(p["net_cash_outflow"], f"payout {p['payout_id']} net")
        if min(gross, fee, cash) < 0:
            fail(f"Negative unsigned payout amount: {p['payout_id']}")
        if p["payout_status"] == "pending":
            if p["payout_date"]:
                fail(f"Pending payout has payout_date: {p['payout_id']}")
            if cash != 0:
                fail(f"Pending payout has net cash outflow: {p['payout_id']}")
        else:
            if not p["payout_date"]:
                fail(f"Non-pending payout lacks payout_date: {p['payout_id']}")
            elif date.fromisoformat(p["payout_date"]) > DATA_AS_OF:
                fail(f"Future payout date: {p['payout_id']}")
        if p["payout_status"] == "completed" and cash != gross + fee:
            fail(f"Completed payout net does not equal gross + fee: {p['payout_id']}")
        if p["payout_status"] != "completed" and cash != 0:
            fail(f"Non-completed payout has cash outflow: {p['payout_id']}")
        if p["vendor_id"] != tx_by_id[p["invoice_transaction_id"]]["vendor_id"]:
            fail(f"Payout vendor differs from invoice vendor: {p['payout_id']}")

    for r in recs:
        reconciled = decimal(r["reconciled_amount"], f"reconciliation {r['reconciliation_id']} reconciled")
        open_amount = decimal(r["unreconciled_amount"], f"reconciliation {r['reconciliation_id']} open")
        txn_abs = abs(decimal(tx_by_id[r["transaction_id"]]["signed_amount"], f"transaction {r['transaction_id']}"))
        if reconciled + open_amount != txn_abs:
            fail(f"Reconciliation components do not tie to transaction: {r['transaction_id']} ({reconciled}+{open_amount}!={txn_abs})")
        if r["status"] == "reconciled" and open_amount != 0:
            fail(f"Reconciled row has open amount: {r['transaction_id']}")
        if r["status"] in OPEN_STATUSES and open_amount <= 0:
            fail(f"Open reconciliation row has non-positive open amount: {r['transaction_id']}")

    posted_ids = {t["transaction_id"] for t in txns if t["status"] == "posted"}
    missing_rec = sorted(posted_ids - set(rec_by_tx))
    if missing_rec != ["TXN-MISSING-REC-001"]:
        fail(f"Unexpected posted transactions missing reconciliation: {missing_rec[:20]}")

    acme = sorted(r["vendor_id"] for r in aliases if r["normalized_alias"] == "acme")
    abc = sorted(r["vendor_id"] for r in aliases if r["normalized_alias"] == "abc")
    if acme != ["V0001","V0002"] or abc != ["V0044","V0045"]:
        fail(f"Ambiguous alias fixtures invalid: acme={acme}, abc={abc}")
    if any(r["is_ambiguous"] != "true" for r in aliases if r["normalized_alias"] in {"acme","abc"}):
        fail("Ambiguous aliases are not flagged")

    required_special = {
        "TXN-ANOM-001","TXN-DUP-001","TXN-DUP-002","TXN-REV-ORIG","TXN-REV-001",
        "TXN-PROMPT-001","TXN-MISSING-REC-001","TXN-PART-001","TXN-PEND-001",
        "TXN-FAIL-001","TXN-VOID-001"
    }
    if required_special - txn_ids:
        fail(f"Missing planted transaction fixtures: {sorted(required_special - txn_ids)}")
    payout_ids = {p["payout_id"] for p in payouts}
    required_payouts = {"PAY-ANOM-001","PAY-DUP-001","PAY-DUP-002","PAY-PROMPT-001","PAY-PART-001","PAY-PEND-001","PAY-FAIL-001"}
    if required_payouts - payout_ids:
        fail(f"Missing planted payout fixtures: {sorted(required_payouts - payout_ids)}")
    prompt_text = tx_by_id["TXN-PROMPT-001"]["description"]
    if "IGNORE PRIOR INSTRUCTIONS" not in prompt_text:
        fail("Prompt-injection fixture is missing")
    if Decimal(rec_by_tx["TXN-PART-001"]["unreconciled_amount"]) != Decimal("200000.00"):
        fail("Partial reconciliation fixture does not have INR 200,000 open")

    dupes = [p for p in payouts if p["payout_id"] in {"PAY-DUP-001","PAY-DUP-002"}]
    if len(dupes) != 2 or len({(p["vendor_id"],p["payout_date"],p["gross_amount"],p["bank_reference"]) for p in dupes}) != 1:
        fail("Duplicate payout fixture does not share expected signals")

    travel_ids = {
        t["transaction_id"] for t in txns
        if t["account_code"] in {"6200","6210","6220"}
        and date(2026,8,24) <= date.fromisoformat(t["posting_date"]) < date(2026,8,31)
    }
    travel_open = [r for r in recs if r["transaction_id"] in travel_ids and r["status"] in OPEN_STATUSES]
    if travel_open:
        fail(f"Travel zero-result fixture has open records: {[r['transaction_id'] for r in travel_open]}")

    # Recompute load-bearing gold metrics independently.
    expected = json.loads((EVAL_DIR / "expected_aggregates.json").read_text(encoding="utf-8"))
    def sum_completed(start: date, end: date) -> Decimal:
        return sum((Decimal(p["gross_amount"]) for p in payouts if p["payout_status"] == "completed" and start <= date.fromisoformat(p["payout_date"]) < end), Decimal("0.00"))
    aug = sum_completed(date(2026,8,1), date(2026,9,1)).quantize(Decimal("0.01"))
    jul = sum_completed(date(2026,7,1), date(2026,8,1)).quantize(Decimal("0.01"))
    if str(aug) != expected["metrics"]["august_2026_completed_vendor_payout_gross"]:
        fail("August expected aggregate drift")
    if str(jul) != expected["metrics"]["july_2026_completed_vendor_payout_gross"]:
        fail("July expected aggregate drift")
    open_rows = [r for r in recs if r["status"] in OPEN_STATUSES]
    if len(open_rows) != expected["metrics"]["open_reconciliation_count"]:
        fail("Open reconciliation count expected aggregate drift")
    open_sum = sum((Decimal(r["unreconciled_amount"]) for r in open_rows), Decimal("0.00")).quantize(Decimal("0.01"))
    if str(open_sum) != expected["metrics"]["open_reconciliation_amount"]:
        fail("Open reconciliation amount expected aggregate drift")

    if len(dictionary) < 70:
        fail(f"Data dictionary unexpectedly short: {len(dictionary)} rows")
    benchmark_rows = []
    with (EVAL_DIR / "benchmark_questions.csv").open("r", encoding="utf-8", newline="") as f:
        benchmark_rows = list(csv.DictReader(f))
    if len(benchmark_rows) < 20:
        fail("Benchmark set must contain at least 20 questions")
    if len({r["question_id"] for r in benchmark_rows}) != len(benchmark_rows):
        fail("Duplicate benchmark question IDs")

    print("Dataset validation summary")
    print(f"  Accounts:       {len(coa)}")
    print(f"  Vendors:        {len(vendors)}")
    print(f"  Vendor aliases: {len(aliases)}")
    print(f"  Transactions:   {len(txns)}")
    print(f"  Payouts:        {len(payouts)}")
    print(f"  Reconciliation: {len(recs)}")
    print(f"  Benchmarks:     {len(benchmark_rows)}")
    print(f"  Warnings:       {len(warnings)}")
    for message in warnings:
        print(f"WARNING: {message}")
    if errors:
        for message in errors:
            print(f"ERROR: {message}", file=sys.stderr)
        print(f"FAILED with {len(errors)} error(s)", file=sys.stderr)
        return 1
    print("PASS: referential integrity, accounting invariants, planted edge cases, and gold aggregates are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
