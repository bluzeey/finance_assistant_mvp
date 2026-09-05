#!/usr/bin/env python3
"""Create schema and bulk-load CSV fixtures into PostgreSQL using psycopg COPY."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

try:
    import psycopg
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Install backend dependencies first: pip install psycopg[binary]") from exc

ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "data" / "csv"

LOAD_ORDER = [
    ("chart_of_accounts", "chart_of_accounts.csv"),
    ("vendors", "vendors.csv"),
    ("vendor_aliases", "vendor_aliases.csv"),
    ("transactions", "transactions.csv"),
    ("vendor_payouts", "vendor_payouts.csv"),
    ("reconciliation_status", "reconciliation_status.csv"),
]


def execute_sql_file(cur: psycopg.Cursor, path: Path) -> None:
    cur.execute(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", default=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ledgerproof"))
    parser.add_argument("--truncate", action="store_true", help="Delete existing fixture rows before loading.")
    args = parser.parse_args()
    metadata = json.loads((ROOT / "data" / "company_metadata.json").read_text(encoding="utf-8"))

    with psycopg.connect(args.dsn, autocommit=False) as conn:
        with conn.cursor() as cur:
            execute_sql_file(cur, ROOT / "database" / "schema.sql")
            if args.truncate:
                cur.execute("TRUNCATE reconciliation_status, vendor_payouts, transactions, vendor_aliases, vendors, chart_of_accounts, companies CASCADE")
            cur.execute(
                """INSERT INTO companies(company_id, legal_name, display_name, currency, timezone, fiscal_year_start_month, data_as_of, generated_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (company_id) DO UPDATE SET
                     legal_name=EXCLUDED.legal_name, display_name=EXCLUDED.display_name,
                     currency=EXCLUDED.currency, timezone=EXCLUDED.timezone,
                     fiscal_year_start_month=EXCLUDED.fiscal_year_start_month,
                     data_as_of=EXCLUDED.data_as_of, generated_at=EXCLUDED.generated_at""",
                (
                    metadata["company_id"], metadata["legal_name"], metadata["display_name"], metadata["currency"],
                    metadata["timezone"], metadata["fiscal_year_start_month"], metadata["data_as_of"], metadata["generated_at"],
                ),
            )
            for table, filename in LOAD_ORDER:
                path = CSV_DIR / filename
                with path.open("r", encoding="utf-8", newline="") as f:
                    header = f.readline().strip()
                    columns = ",".join(f'"{c}"' for c in header.split(","))
                    with cur.copy(f"COPY {table} ({columns}) FROM STDIN WITH (FORMAT CSV, HEADER FALSE, NULL '')") as copy:
                        while chunk := f.read(1 << 20):
                            copy.write(chunk)
                cur.execute(f"SELECT count(*) FROM {table}")
                print(f"Loaded {table}: {cur.fetchone()[0]} rows")
            execute_sql_file(cur, ROOT / "database" / "views.sql")
            execute_sql_file(cur, ROOT / "database" / "indexes.sql")
        conn.commit()
    print("PostgreSQL load complete.")


if __name__ == "__main__":
    main()
