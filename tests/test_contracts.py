from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    def test_json_schemas_are_valid(self) -> None:
        for path in sorted((ROOT / "contracts").glob("*.schema.json")):
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)

    def test_sample_receipt_validates(self) -> None:
        schema = json.loads((ROOT / "contracts" / "answer_receipt.schema.json").read_text(encoding="utf-8"))
        computed_schema = json.loads((ROOT / "contracts" / "computed_facts.schema.json").read_text(encoding="utf-8"))
        receipt = json.loads((ROOT / "contracts" / "sample_verified_answer_receipt.json").read_text(encoding="utf-8"))
        # Inline the one local reference so this test remains deterministic without a
        # network or URI resolver.
        schema["properties"]["computation"] = {"oneOf": [{"type": "null"}, computed_schema]}
        Draft202012Validator(schema).validate(receipt)

    def test_openapi_and_semantics_yaml_parse(self) -> None:
        openapi = yaml.safe_load((ROOT / "contracts" / "openapi.yaml").read_text(encoding="utf-8"))
        semantics = yaml.safe_load((ROOT / "contracts" / "semantic_metrics.yaml").read_text(encoding="utf-8"))
        self.assertEqual(openapi["openapi"], "3.1.0")
        self.assertEqual(semantics["dataset"]["source_tables"], ["bank", "account", "transaction"])
        self.assertIn("reconciliation_status", semantics["unsupported_concepts"])

    def test_query_plan_has_no_sql_property(self) -> None:
        schema_text = (ROOT / "contracts" / "query_plan.schema.json").read_text(encoding="utf-8").lower()
        self.assertNotIn('"sql"', schema_text)
        self.assertNotIn('"utr_number"', schema_text)


if __name__ == "__main__":
    unittest.main()
