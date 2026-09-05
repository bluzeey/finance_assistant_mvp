from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MySQLContractTests(unittest.TestCase):
    def test_schema_creates_exact_three_source_tables(self) -> None:
        text = (ROOT / "database/schema.sql").read_text(encoding="utf-8")
        tables = re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?([A-Za-z_]+)`?", text, re.I)
        self.assertEqual(tables, ["bank", "account", "transaction"])

    def test_mysql_specific_types_and_constraints_are_preserved(self) -> None:
        text = (ROOT / "database/schema.sql").read_text(encoding="utf-8")
        for token in ["TIMESTAMP(6)", "DECIMAL(15,2)", "ENUM('credit','debit')", "ENGINE=InnoDB"]:
            self.assertIn(token, text)
        self.assertIn("FOREIGN KEY (`bank_code`) REFERENCES `bank` (`bank_code`)", text)
        self.assertIn("FOREIGN KEY (`account_id`) REFERENCES `account` (`account_id`)", text)

    def test_query_templates_quote_reserved_transaction_name(self) -> None:
        text = (ROOT / "database/query_templates.sql").read_text(encoding="utf-8")
        self.assertNotRegex(text, r"(?i)\bFROM\s+transaction\b")
        self.assertNotRegex(text, r"(?i)\bJOIN\s+transaction\b")
        self.assertIn("FROM `transaction`", text)

    def test_calendar_queries_are_half_open(self) -> None:
        text = (ROOT / "database/query_templates.sql").read_text(encoding="utf-8")
        self.assertIn("transaction_date >= %(start_inclusive)s", text)
        self.assertIn("transaction_date <  %(end_exclusive)s", text)
        self.assertNotIn("BETWEEN %(start", text)

    def test_reference_lookup_has_case_sensitive_exact_check(self) -> None:
        text = (ROOT / "database/query_templates.sql").read_text(encoding="utf-8")
        self.assertIn("BINARY t.transaction_reference_id = BINARY %(transaction_reference_id)s", text)
        self.assertNotIn("LIKE %(transaction_reference_id)s", text)

    def test_loader_dry_run_validates_without_database(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/load_mysql.py", "--dry-run"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("DRY RUN PASS", completed.stdout)
        self.assertIn("transactions=2426", completed.stdout)


if __name__ == "__main__":
    unittest.main()
