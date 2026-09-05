from __future__ import annotations

import csv
import json
import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class DatasetIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        def read(name: str) -> list[dict[str, str]]:
            with (ROOT / "data" / "csv" / name).open(newline="", encoding="utf-8") as handle:
                return list(csv.DictReader(handle))

        cls.banks = read("bank.csv")
        cls.accounts = read("account.csv")
        cls.transactions = read("transaction.csv")

    def test_exact_source_table_set(self) -> None:
        files = {path.name for path in (ROOT / "data" / "csv").glob("*.csv")}
        self.assertEqual(files, {"bank.csv", "account.csv", "transaction.csv", "data_dictionary.csv"})

    def test_expected_counts(self) -> None:
        self.assertEqual(len(self.banks), 10)
        self.assertEqual(len(self.accounts), 30)
        self.assertEqual(len(self.transactions), 2426)

    def test_foreign_keys(self) -> None:
        bank_codes = {row["bank_code"] for row in self.banks}
        account_ids = {row["account_id"] for row in self.accounts}
        self.assertTrue(all(row["bank_code"] in bank_codes for row in self.accounts))
        self.assertTrue(all(row["account_id"] in account_ids for row in self.transactions))

    def test_money_is_decimal_compatible(self) -> None:
        for row in self.accounts:
            value = Decimal(row["available_balance"])
            self.assertGreaterEqual(value, Decimal("-9999999999999.99"))
            self.assertLessEqual(value, Decimal("9999999999999.99"))
            self.assertGreaterEqual(-value.as_tuple().exponent, 0)
        for row in self.transactions:
            value = Decimal(row["transaction_amount"])
            self.assertGreaterEqual(value, Decimal("0.00"))
            self.assertLessEqual(value, Decimal("9999999999999.99"))
            self.assertGreaterEqual(-value.as_tuple().exponent, 0)

    def test_provided_seed_rows_are_preserved(self) -> None:
        tx_by_id = {row["transaction_id"]: row for row in self.transactions}
        self.assertEqual(tx_by_id["0266384b-929c-478d-a7da-a54acf984343"]["transaction_reference_id"], "HDFCH01078324740")
        self.assertEqual(tx_by_id["001cb576-eb28-44b1-a219-0f3f27093fad"]["transaction_amount"], "14866.00")
        account_by_id = {row["account_id"]: row for row in self.accounts}
        self.assertEqual(account_by_id["acfbe204-7541-492c-a352-040aa984bedc"]["account_number"], "50200013729069")

    def test_manifest_matches_counts(self) -> None:
        manifest = json.loads((ROOT / "data" / "dataset_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["row_counts"], {"bank": 10, "account": 30, "transaction": 2426})
        self.assertEqual(manifest["source_tables"], ["bank", "account", "transaction"])

    def test_uuid_like_ids_are_treated_as_opaque(self) -> None:
        # This organiser-provided sample is not a strict 8-4-4-4-12 UUID. The DB column
        # is VARCHAR(36), so application contracts must not reject it as a string ID.
        ids = {row["transaction_id"] for row in self.transactions}
        self.assertIn("0178b656-4a7d-98e8-9540f6e24caf", ids)


if __name__ == "__main__":
    unittest.main()
