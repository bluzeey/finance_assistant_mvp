"""Read reproducibility metadata for API responses."""
from __future__ import annotations

import csv
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

from django.conf import settings

from finance_assistant.semantic.registry import load_semantic_registry

SUPPORTED_EXAMPLES = [
    "How much did we spend on vendor payouts last month?",
    "How did that compare with the month before?",
    "Who were the top five vendors in August 2026?",
    "Which transactions are still unreconciled?",
    "Show unreconciled items older than 30 days.",
    "Is anything unusual in August payouts?",
]


def repo_root() -> Path:
    root_setting = settings.LEDGERPROOF["REPO_ROOT"]
    return root_setting if isinstance(root_setting, Path) else Path(str(root_setting))


@lru_cache(maxsize=1)
def company_metadata() -> dict[str, Any]:
    raw = json.loads((repo_root() / "data" / "company_metadata.json").read_text())
    return cast(dict[str, Any], raw)


@lru_cache(maxsize=1)
def dataset_manifest() -> dict[str, Any]:
    raw = json.loads((repo_root() / "data" / "dataset_manifest.json").read_text())
    return cast(dict[str, Any], raw)


@lru_cache(maxsize=1)
def max_posting_date() -> str:
    return _max_csv_date("transactions.csv", "posting_date")


@lru_cache(maxsize=1)
def max_payout_date() -> str:
    return _max_csv_date("vendor_payouts.csv", "payout_date")


def build_meta_response() -> dict[str, Any]:
    company = company_metadata()
    manifest = dataset_manifest()
    registry = load_semantic_registry()
    posting_date = max_posting_date()
    data_as_of = str(company["data_as_of"])

    return {
        "company": {
            "company_id": company["company_id"],
            "display_name": company["display_name"],
            "currency": company["currency"],
            "timezone": company["timezone"],
            "fiscal_year_start_month": company["fiscal_year_start_month"],
            "synthetic": company["synthetic"],
        },
        "dataset": {
            "version": manifest["dataset_version"],
            "data_as_of": data_as_of,
            "max_posting_date": posting_date,
            "max_payout_date": max_payout_date(),
            "freshness_state": "fresh" if posting_date <= data_as_of else "unknown",
            "generated_at": manifest["generated_at"],
        },
        "supported_metrics": registry.metric_summaries(),
        "supported_examples": SUPPORTED_EXAMPLES,
        "versions": {
            "app_version": settings.LEDGERPROOF["APP_VERSION"],
            "semantic_version": registry.version,
            "prompt_version": settings.LEDGERPROOF["PROMPT_VERSION"],
            "model_provider": settings.LEDGERPROOF["MODEL_PROVIDER"],
            "model_id": settings.LEDGERPROOF["SARVAM_MODEL_ID"],
        },
        "features": {
            "evaluation_enabled": settings.LEDGERPROOF["ENABLE_EVALUATION"],
        },
    }


def _max_csv_date(filename: str, field: str) -> str:
    values: list[str] = []
    path = repo_root() / "data" / "csv" / filename
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            value = row.get(field) or ""
            if value:
                values.append(value)
    if not values:
        raise ValueError(f"{filename} has no values for {field}")
    return max(values)
