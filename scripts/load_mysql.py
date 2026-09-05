#!/usr/bin/env python3
"""Load deterministic CSV fixtures into the organiser-supplied MySQL schema.

This utility is intentionally separate from Django migrations because the three finance
source tables are externally owned. Application migrations must never alter their meaning.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "data" / "csv"
MANIFEST = ROOT / "data" / "dataset_manifest.json"


def statements(path: Path) -> list[str]:
    """Split repository-controlled SQL files that contain no procedural blocks."""
    text = path.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if not line.lstrip().startswith("--")]
    return [part.strip() for part in "\n".join(lines).split(";") if part.strip()]


def read_rows(name: str) -> list[dict[str, str | None]]:
    with (CSV_DIR / name).open("r", encoding="utf-8", newline="") as handle:
        return [
            {key: (value if value != "" else None) for key, value in raw.items()}
            for raw in csv.DictReader(handle)
        ]


def chunks(rows: Sequence[dict[str, str | None]], size: int = 1000) -> Iterable[Sequence[dict[str, str | None]]]:
    for offset in range(0, len(rows), size):
        yield rows[offset : offset + size]


def expected_counts() -> dict[str, int]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {str(k): int(v) for k, v in data["row_counts"].items()}


def validate_local_inputs() -> tuple[list[dict[str, str | None]], list[dict[str, str | None]], list[dict[str, str | None]]]:
    banks = read_rows("bank.csv")
    accounts = read_rows("account.csv")
    transactions = read_rows("transaction.csv")
    expected = expected_counts()
    actual = {"bank": len(banks), "account": len(accounts), "transaction": len(transactions)}
    if actual != expected:
        raise SystemExit(f"CSV counts do not match manifest: expected={expected}, actual={actual}")
    bank_codes = {row["bank_code"] for row in banks}
    account_ids = {row["account_id"] for row in accounts}
    bad_accounts = [row["account_id"] for row in accounts if row["bank_code"] not in bank_codes]
    bad_transactions = [row["transaction_id"] for row in transactions if row["account_id"] not in account_ids]
    if bad_accounts or bad_transactions:
        raise SystemExit(
            f"Local foreign-key validation failed: bad_accounts={bad_accounts[:5]}, "
            f"bad_transactions={bad_transactions[:5]}"
        )
    return banks, accounts, transactions


def verify_database(cursor, expected: dict[str, int], exact: bool) -> None:
    actual: dict[str, int] = {}
    for table in ["bank", "account", "transaction"]:
        cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
        actual[table] = int(cursor.fetchone()[0])
        print(f"{table}: {actual[table]}")
        if exact and actual[table] != expected[table]:
            raise RuntimeError(f"Unexpected {table} count: expected {expected[table]}, found {actual[table]}")
        if not exact and actual[table] < expected[table]:
            raise RuntimeError(f"{table} count is below fixture count: expected at least {expected[table]}, found {actual[table]}")

    cursor.execute(
        "SELECT COUNT(*) FROM `account` a LEFT JOIN `bank` b ON b.bank_code=a.bank_code "
        "WHERE b.bank_code IS NULL"
    )
    orphan_accounts = int(cursor.fetchone()[0])
    cursor.execute(
        "SELECT COUNT(*) FROM `transaction` t LEFT JOIN `account` a ON a.account_id=t.account_id "
        "WHERE a.account_id IS NULL"
    )
    orphan_transactions = int(cursor.fetchone()[0])
    if orphan_accounts or orphan_transactions:
        raise RuntimeError(
            f"Database foreign-key verification failed: orphan_accounts={orphan_accounts}, "
            f"orphan_transactions={orphan_transactions}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--truncate", action="store_true", help="Delete all source rows before loading; local/demo use only.")
    parser.add_argument("--skip-indexes", action="store_true", help="Skip database/indexes.sql.")
    parser.add_argument("--dry-run", action="store_true", help="Validate local SQL/CSV inputs without connecting to MySQL.")
    args = parser.parse_args()

    banks, accounts, transactions = validate_local_inputs()
    schema_statements = statements(ROOT / "database" / "schema.sql")
    index_statements = statements(ROOT / "database" / "indexes.sql")
    if len(schema_statements) < 5:
        raise SystemExit("database/schema.sql did not parse into expected SET/CREATE statements")
    if args.dry_run:
        print(f"DRY RUN PASS: banks={len(banks)}, accounts={len(accounts)}, transactions={len(transactions)}, "
              f"schema_statements={len(schema_statements)}, index_statements={len(index_statements)}")
        return 0

    try:
        import mysql.connector  # type: ignore
    except ImportError as exc:  # pragma: no cover - dependency error path
        raise SystemExit("Install mysql-connector-python from requirements-tools.txt") from exc

    connection = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "finance"),
        password=os.getenv("MYSQL_PASSWORD", "finance"),
        database=os.getenv("MYSQL_DATABASE", "finance_assistant"),
        autocommit=False,
        charset="utf8mb4",
        use_unicode=True,
    )
    cursor = connection.cursor()
    try:
        cursor.execute("SET time_zone = '+05:30'")
        for statement in schema_statements:
            cursor.execute(statement)

        if args.truncate:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            try:
                cursor.execute("TRUNCATE TABLE `transaction`")
                cursor.execute("TRUNCATE TABLE `account`")
                cursor.execute("TRUNCATE TABLE `bank`")
            finally:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        cursor.executemany(
            "INSERT INTO `bank` (`bank_code`,`bank_name`) VALUES (%(bank_code)s,%(bank_name)s) "
            "ON DUPLICATE KEY UPDATE `bank_name`=VALUES(`bank_name`)",
            banks,
        )
        cursor.executemany(
            "INSERT INTO `account` (`account_id`,`entity_id`,`account_number`,`program_id`,`available_balance`,`bank_code`) "
            "VALUES (%(account_id)s,%(entity_id)s,%(account_number)s,%(program_id)s,%(available_balance)s,%(bank_code)s) "
            "ON DUPLICATE KEY UPDATE `entity_id`=VALUES(`entity_id`),`account_number`=VALUES(`account_number`),"
            "`program_id`=VALUES(`program_id`),`available_balance`=VALUES(`available_balance`),`bank_code`=VALUES(`bank_code`)",
            accounts,
        )
        transaction_sql = (
            "INSERT INTO `transaction` (`transaction_id`,`account_id`,`transaction_date`,`transaction_type`,`description`,"
            "`transaction_amount`,`transaction_reference_id`,`utr_number`) VALUES "
            "(%(transaction_id)s,%(account_id)s,%(transaction_date)s,%(transaction_type)s,%(description)s,"
            "%(transaction_amount)s,%(transaction_reference_id)s,%(utr_number)s) "
            "ON DUPLICATE KEY UPDATE `account_id`=VALUES(`account_id`),`transaction_date`=VALUES(`transaction_date`),"
            "`transaction_type`=VALUES(`transaction_type`),`description`=VALUES(`description`),"
            "`transaction_amount`=VALUES(`transaction_amount`),`transaction_reference_id`=VALUES(`transaction_reference_id`),"
            "`utr_number`=VALUES(`utr_number`)"
        )
        for batch in chunks(transactions):
            cursor.executemany(transaction_sql, batch)
        connection.commit()

        if not args.skip_indexes:
            for statement in index_statements:
                try:
                    cursor.execute(statement)
                except mysql.connector.Error as exc:
                    if exc.errno != 1061:  # duplicate key/index name
                        raise
            connection.commit()

        verify_database(cursor, expected_counts(), exact=args.truncate)
        print("PASS: MySQL fixture loaded and verified")
        return 0
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
