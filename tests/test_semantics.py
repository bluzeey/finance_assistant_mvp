from __future__ import annotations

import csv
import json
import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reference_evaluator import Fixture, aggregate_metric, current_balance, filter_transactions


class FinanceSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        def read(name: str) -> list[dict[str, str]]:
            with (ROOT / "data" / "csv" / name).open(newline="", encoding="utf-8") as handle:
                return list(csv.DictReader(handle))
        cls.fixture = Fixture(read("bank.csv"), read("account.csv"), read("transaction.csv"))
        cls.gold = json.loads((ROOT / "evaluation" / "expected_aggregates.json").read_text(encoding="utf-8"))

    def test_august_range_is_half_open(self) -> None:
        rows = filter_transactions(
            self.fixture,
            start="2026-08-01 00:00:00.000000",
            end="2026-09-01 00:00:00.000000",
        )
        refs = {row["transaction_reference_id"] for row in rows}
        self.assertIn("BOUNDARY-AUG-START", refs)
        self.assertIn("BOUNDARY-AUG-END", refs)
        self.assertNotIn("BOUNDARY-JUL-END", refs)
        self.assertNotIn("BOUNDARY-SEP-START", refs)

    def test_august_gold_totals(self) -> None:
        rows = filter_transactions(
            self.fixture,
            start="2026-08-01 00:00:00.000000",
            end="2026-09-01 00:00:00.000000",
        )
        for metric in ["debit_total", "credit_total", "net_cash_flow", "transaction_count"]:
            self.assertEqual(aggregate_metric(metric, rows), self.gold["august_2026"][metric])

    def test_net_is_credit_minus_debit(self) -> None:
        month = self.gold["august_2026"]
        expected = Decimal(month["credit_total"]["value"]) - Decimal(month["debit_total"]["value"])
        self.assertEqual(expected, Decimal(month["net_cash_flow"]["value"]))

    def test_current_balance_uses_distinct_accounts_not_transaction_join(self) -> None:
        result = current_balance(self.fixture)
        self.assertEqual(result["record_count"], 30)
        self.assertEqual(result["value"], self.gold["current_available_balance"]["value"])

    def test_reference_match_is_case_sensitive(self) -> None:
        exact = filter_transactions(self.fixture, transaction_reference_id="CaseRef-AbC-001")
        wrong_case = filter_transactions(self.fixture, transaction_reference_id="caseref-abc-001")
        self.assertEqual(len(exact), 1)
        self.assertEqual(len(wrong_case), 0)

    def test_duplicate_reference_is_not_silently_collapsed(self) -> None:
        rows = filter_transactions(self.fixture, transaction_reference_id="DUP-REF-2026-001")
        self.assertEqual(len(rows), 2)
        self.assertEqual({row["transaction_type"] for row in rows}, {"credit", "debit"})

    def test_description_search_is_literal_not_vendor_resolution(self) -> None:
        rows = filter_transactions(self.fixture, description_contains="SELECTION MOBILE")
        self.assertGreaterEqual(len(rows), 3)
        self.assertTrue(all("selection mobile" in (row["description"] or "").casefold() for row in rows))


if __name__ == "__main__":
    unittest.main()
