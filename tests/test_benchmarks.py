from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BenchmarkContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = [json.loads(line) for line in (ROOT / "evaluation" / "benchmark_cases.jsonl").read_text(encoding="utf-8").splitlines() if line]
        cls.by_id = {case["case_id"]: case for case in cls.cases}

    def test_case_count_and_ids(self) -> None:
        self.assertEqual(len(self.cases), 30)
        self.assertEqual(len(self.by_id), 30)

    def test_missing_schema_concepts_never_have_numeric_answers(self) -> None:
        for case_id in ["Q019", "Q020", "Q021", "Q022", "Q025"]:
            case = self.by_id[case_id]
            self.assertEqual(case["expected_disposition"], "unsupported")
            self.assertIsNone(case["expected_result"])
            self.assertIsNone(case["expected_query_plan"])

    def test_ambiguous_recency_requires_clarification(self) -> None:
        case = self.by_id["Q018"]
        self.assertEqual(case["expected_disposition"], "clarify")
        self.assertIsNone(case["expected_result"])

    def test_description_search_is_qualified(self) -> None:
        case = self.by_id["Q015"]
        self.assertEqual(case["expected_confidence"], "qualified")
        self.assertEqual(case["expected_result"]["qualification"], "description_literal_search")

    def test_case_mismatch_reference_is_no_data_not_fuzzy_match(self) -> None:
        case = self.by_id["Q027"]
        self.assertEqual(case["expected_confidence"], "no_data")
        self.assertEqual(case["expected_result"]["record_count"], 0)


if __name__ == "__main__":
    unittest.main()
