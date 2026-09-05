from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from privacy import mask_account_number, mask_utr, redact_known_account_numbers, sanitize_record


class PrivacyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with (ROOT / "data" / "csv" / "account.csv").open(newline="", encoding="utf-8") as handle:
            cls.accounts = list(csv.DictReader(handle))
        with (ROOT / "data" / "csv" / "transaction.csv").open(newline="", encoding="utf-8") as handle:
            cls.transactions = list(csv.DictReader(handle))
        cls.account_numbers = [row["account_number"] for row in cls.accounts]

    def test_account_number_mask(self) -> None:
        self.assertEqual(mask_account_number("50200013729069"), "••••••••••9069")
        self.assertNotIn("50200013729069", mask_account_number("50200013729069") or "")

    def test_utr_mask(self) -> None:
        masked = mask_utr("sensitive-encrypted-token-ABC123")
        self.assertTrue(masked.endswith("ABC123"))
        self.assertNotIn("sensitive-encrypted-token-", masked)

    def test_description_redaction_catches_known_account_number(self) -> None:
        text = "Transfer from 50200013729069 to beneficiary"
        redacted = redact_known_account_numbers(text, self.account_numbers)
        self.assertNotIn("50200013729069", redacted or "")
        self.assertIn("9069", redacted or "")

    def test_sanitize_record_never_returns_raw_sensitive_values(self) -> None:
        account = self.accounts[0]
        joined = {
            "transaction_id": "opaque-id",
            "account_number": account["account_number"],
            "description": f"Transfer from {account['account_number']}",
            "utr_number": "sensitive-encrypted-token-ABC123",
        }
        safe = sanitize_record(joined, self.account_numbers)
        self.assertNotEqual(safe["account_number"], account["account_number"])
        self.assertNotIn(account["account_number"], safe["description"] or "")
        self.assertNotEqual(safe["utr_number"], joined["utr_number"])

    def test_prompt_text_is_preserved_as_text_for_escaped_rendering(self) -> None:
        tx = next(row for row in self.transactions if row["transaction_reference_id"] == "PROMPT-REF-001")
        safe = sanitize_record(tx, self.account_numbers)
        self.assertIn("IGNORE ALL PREVIOUS INSTRUCTIONS", safe["description"] or "")
        self.assertIn("<script>", safe["description"] or "")
        # Escaping is the React renderer's responsibility; backend must not execute or
        # reinterpret this text, nor pass it into the model as instructions.


if __name__ == "__main__":
    unittest.main()
