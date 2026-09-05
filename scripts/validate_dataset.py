#!/usr/bin/env python3
"""Validate the generated bank/account/transaction fixture and gold evaluations."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
import uuid
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from reference_evaluator import Fixture, aggregate_metric, current_balance, filter_transactions

ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "data" / "csv"
EVAL_DIR = ROOT / "evaluation"
EXPECTED_TABLE_FILES = {"bank.csv", "account.csv", "transaction.csv", "data_dictionary.csv"}
EXPECTED_BANK_CODES = {"HDFC", "ICIC", "SBIN", "UTIB", "KKBK", "CNRB", "UBIN", "AUBL", "TMBL", "RATN"}
EXPECTED_COUNTS = {"bank": 10, "account": 30, "transaction": 2426, "benchmarks": 30}
MAX_DECIMAL_15_2 = Decimal("9999999999999.99")
DATA_AS_OF = datetime.strptime("2026-09-03 23:59:59.999999", "%Y-%m-%d %H:%M:%S.%f")


def read_csv(name: str) -> list[dict[str, str]]:
    with (CSV_DIR / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    h = hashlib.sha256(path.read_bytes())
    return h.hexdigest()


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def parse_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def parse_money(value: str, label: str, errors: list[str]) -> Decimal | None:
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError):
        fail(errors, f"{label}: invalid decimal {value!r}")
        return None
    if parsed.as_tuple().exponent < -2:
        fail(errors, f"{label}: more than two decimal places: {value}")
    if abs(parsed) > MAX_DECIMAL_15_2:
        fail(errors, f"{label}: exceeds DECIMAL(15,2): {value}")
    return parsed


def main() -> int:
    errors: list[str] = []
    known_quality_signals: list[str] = []

    actual_csv_files = {p.name for p in CSV_DIR.glob("*.csv")}
    if actual_csv_files != EXPECTED_TABLE_FILES:
        fail(errors, f"CSV file set mismatch: expected {sorted(EXPECTED_TABLE_FILES)}, got {sorted(actual_csv_files)}")

    banks = read_csv("bank.csv")
    accounts = read_csv("account.csv")
    transactions = read_csv("transaction.csv")
    dictionary = read_csv("data_dictionary.csv")

    if len(banks) != EXPECTED_COUNTS["bank"]:
        fail(errors, f"bank row count: {len(banks)}")
    if len(accounts) != EXPECTED_COUNTS["account"]:
        fail(errors, f"account row count: {len(accounts)}")
    if len(transactions) != EXPECTED_COUNTS["transaction"]:
        fail(errors, f"transaction row count: {len(transactions)}")
    if len(dictionary) != 16:
        fail(errors, f"data dictionary should document 16 source columns, got {len(dictionary)}")

    bank_codes = [row["bank_code"] for row in banks]
    if set(bank_codes) != EXPECTED_BANK_CODES:
        fail(errors, f"bank codes mismatch: {set(bank_codes)}")
    if len(bank_codes) != len(set(bank_codes)):
        fail(errors, "duplicate bank_code")
    for row in banks:
        if not row["bank_name"] or row["bank_name"] != row["bank_name"].upper():
            fail(errors, f"bank_name must be canonical all caps: {row}")
        if len(row["bank_code"]) > 10 or len(row["bank_name"]) > 150:
            fail(errors, f"bank length overflow: {row}")

    account_ids = [row["account_id"] for row in accounts]
    if len(account_ids) != len(set(account_ids)):
        fail(errors, "duplicate account_id")
    account_numbers = [row["account_number"] for row in accounts]
    if len(account_numbers) != len(set(account_numbers)):
        fail(errors, "fixture account_number values should be unique")
    malformed_account_ids = 0
    malformed_entity_ids = 0
    for row in accounts:
        if not parse_uuid(row["account_id"]):
            malformed_account_ids += 1
        if not parse_uuid(row["entity_id"]):
            malformed_entity_ids += 1
        if row["bank_code"] not in EXPECTED_BANK_CODES:
            fail(errors, f"account references missing bank: {row}")
        if len(row["account_number"]) > 20 or not row["account_number"]:
            fail(errors, f"invalid account_number length: {row['account_id']}")
        try:
            int(row["program_id"])
        except ValueError:
            fail(errors, f"program_id must be integer: {row}")
        parse_money(row["available_balance"], f"account {row['account_id']} balance", errors)

    account_set = set(account_ids)
    transaction_ids = [row["transaction_id"] for row in transactions]
    if len(transaction_ids) != len(set(transaction_ids)):
        fail(errors, "duplicate transaction_id")
    refs = Counter(row["transaction_reference_id"] for row in transactions if row["transaction_reference_id"])
    duplicate_refs = {key: count for key, count in refs.items() if count > 1}
    if duplicate_refs.get("DUP-REF-2026-001") != 2:
        fail(errors, "expected duplicate-reference fixture is missing")
    else:
        known_quality_signals.append("one deliberately non-unique transaction reference")

    lookalike_counter = Counter()
    malformed_transaction_ids = 0
    null_descriptions = 0
    zero_amounts = 0
    raw_account_mentions = 0
    for row in transactions:
        tx_id = row["transaction_id"]
        if not parse_uuid(tx_id):
            malformed_transaction_ids += 1
        if row["account_id"] not in account_set:
            fail(errors, f"orphan transaction account_id: {tx_id}")
        if row["transaction_type"] not in {"credit", "debit"}:
            fail(errors, f"invalid transaction_type: {tx_id}")
        try:
            stamp = datetime.strptime(row["transaction_date"], "%Y-%m-%d %H:%M:%S.%f")
            if stamp > DATA_AS_OF:
                fail(errors, f"transaction after data_as_of: {tx_id}")
        except ValueError:
            fail(errors, f"invalid TIMESTAMP(6): {tx_id} {row['transaction_date']}")
        amount = parse_money(row["transaction_amount"], f"transaction {tx_id} amount", errors)
        if amount is not None:
            if amount < 0:
                fail(errors, f"fixture uses positive absolute amounts; negative found: {tx_id}")
            if amount == 0:
                zero_amounts += 1
        description = row["description"]
        if not description:
            null_descriptions += 1
        elif len(description) > 500:
            fail(errors, f"description overflow: {tx_id}")
        if len(row["transaction_reference_id"]) > 64:
            fail(errors, f"transaction_reference_id overflow: {tx_id}")
        if len(row["utr_number"]) > 256:
            fail(errors, f"utr_number overflow: {tx_id}")
        if description and any(number in description for number in account_numbers):
            raw_account_mentions += 1
        lookalike_counter[(row["account_id"], row["transaction_date"], row["transaction_type"], row["description"], row["transaction_amount"])] += 1

    if malformed_account_ids or malformed_entity_ids or malformed_transaction_ids:
        known_quality_signals.append(
            f"opaque UUID-like IDs that fail strict UUID parsing: accounts={malformed_account_ids}, entities={malformed_entity_ids}, transactions={malformed_transaction_ids}"
        )

    duplicate_lookalikes = sum(1 for count in lookalike_counter.values() if count > 1)
    if duplicate_lookalikes < 1:
        fail(errors, "expected duplicate-lookalike pair missing")
    else:
        known_quality_signals.append(f"{duplicate_lookalikes} deliberate duplicate-lookalike signature(s)")
    if null_descriptions < 1:
        fail(errors, "expected null description fixture missing")
    else:
        known_quality_signals.append(f"{null_descriptions} transaction(s) with null description")
    if zero_amounts < 1:
        fail(errors, "expected zero-amount fixture missing")
    else:
        known_quality_signals.append(f"{zero_amounts} zero-amount transaction(s)")
    if raw_account_mentions < 1:
        fail(errors, "expected account-number-in-description fixture missing")
    else:
        known_quality_signals.append(f"{raw_account_mentions} narration(s) require account-number redaction")

    manifest = json.loads((ROOT / "data" / "dataset_manifest.json").read_text(encoding="utf-8"))
    if manifest["source_tables"] != ["bank", "account", "transaction"]:
        fail(errors, f"manifest source tables are wrong: {manifest['source_tables']}")
    if manifest["row_counts"] != {"bank": len(banks), "account": len(accounts), "transaction": len(transactions)}:
        fail(errors, "manifest row counts do not match CSVs")
    for file_entry in manifest["files"]:
        path = ROOT / file_entry["path"]
        if not path.exists():
            fail(errors, f"manifest file missing: {path}")
        elif sha256(path) != file_entry["sha256"]:
            fail(errors, f"manifest hash mismatch: {path}")

    metadata = json.loads((ROOT / "data" / "company_metadata.json").read_text(encoding="utf-8"))
    if metadata["currency"] != "INR" or metadata["timezone"] != "Asia/Kolkata":
        fail(errors, "metadata currency/timezone mismatch")
    if metadata["scope"] != ["bank", "account", "transaction"]:
        fail(errors, "metadata scope mismatch")

    edge_rows = read_csv("../evaluation/edge_case_manifest.csv") if False else None
    with (EVAL_DIR / "edge_case_manifest.csv").open("r", encoding="utf-8", newline="") as handle:
        edges = list(csv.DictReader(handle))
    tx_set = set(transaction_ids)
    for edge in edges:
        if edge["transaction_id"] not in tx_set:
            fail(errors, f"edge manifest points to missing transaction: {edge}")

    with (EVAL_DIR / "benchmark_cases.jsonl").open("r", encoding="utf-8") as handle:
        cases = [json.loads(line) for line in handle if line.strip()]
    if len(cases) != EXPECTED_COUNTS["benchmarks"]:
        fail(errors, f"expected {EXPECTED_COUNTS['benchmarks']} benchmark cases, got {len(cases)}")
    if len({case["case_id"] for case in cases}) != len(cases):
        fail(errors, "duplicate benchmark case_id")
    required_unsupported = {"Q019", "Q020", "Q021", "Q022", "Q025"}
    if not required_unsupported.issubset({c["case_id"] for c in cases if c["expected_disposition"] == "unsupported"}):
        fail(errors, "unsupported-schema benchmark cases missing")

    # Recompute the most important gold totals from source rows.
    fixture = Fixture(banks, accounts, transactions)
    aug = filter_transactions(fixture, start="2026-08-01 00:00:00.000000", end="2026-09-01 00:00:00.000000")
    gold = json.loads((EVAL_DIR / "expected_aggregates.json").read_text(encoding="utf-8"))
    for metric in ["debit_total", "credit_total", "net_cash_flow", "transaction_count"]:
        actual = aggregate_metric(metric, aug)
        if actual != gold["august_2026"][metric]:
            fail(errors, f"gold aggregate mismatch for August {metric}: {actual} vs {gold['august_2026'][metric]}")
    balance = current_balance(fixture)
    balance.pop("records", None)
    if balance != gold["current_available_balance"]:
        fail(errors, "current available-balance gold mismatch")

    forbidden_old_files = [
        ROOT / "data" / "csv" / "vendors.csv",
        ROOT / "data" / "csv" / "vendor_payouts.csv",
        ROOT / "data" / "csv" / "reconciliation_status.csv",
        ROOT / "data" / "csv" / "chart_of_accounts.csv",
        ROOT / "scripts" / "load_postgres.py",
        ROOT / "database" / "views.sql",
    ]
    for path in forbidden_old_files:
        if path.exists():
            fail(errors, f"obsolete schema artifact still exists: {path.relative_to(ROOT)}")

    print(f"Banks:                 {len(banks)}")
    print(f"Accounts:              {len(accounts)}")
    print(f"Transactions:          {len(transactions)}")
    print(f"Data-dictionary rows:  {len(dictionary)}")
    print(f"Benchmark cases:       {len(cases)}")
    print(f"Edge-case records:     {len(edges)}")
    print("Known quality signals:")
    for signal in known_quality_signals:
        print(f"  - {signal}")

    if errors:
        print("\nFAIL")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("\nPASS: dataset integrity, finance semantics, privacy fixtures, and gold totals")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
