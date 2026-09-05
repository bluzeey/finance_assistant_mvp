"""Load the versioned finance semantic contract.

The semantic YAML is the product source of truth for metric definitions. Runtime
code may read this file; it must never read evaluation gold values.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

import yaml
from django.conf import settings


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    metric_id: str
    display_name: str
    description: str
    source: str
    aggregation: str
    mandatory_filters: dict[str, list[str]]
    date_field: str | None
    currency_field: str | None
    allowed_dimensions: list[str]
    aliases: list[str]
    exclusions: list[str]
    zero_semantics: str | None


@dataclass(frozen=True, slots=True)
class SemanticRegistry:
    version: str
    currency: str
    timezone: str
    metrics: dict[str, MetricDefinition]
    relative_dates: dict[str, dict[str, Any]]
    unsupported_domains: list[str]

    def metric_summaries(self) -> list[dict[str, Any]]:
        return [
            {
                "metric_id": metric.metric_id,
                "display_name": metric.display_name,
                "description": metric.description,
                "source": metric.source,
                "aggregation": metric.aggregation,
                "mandatory_filters": metric.mandatory_filters,
                "date_field": metric.date_field,
                "allowed_dimensions": metric.allowed_dimensions,
                "aliases": metric.aliases,
                "exclusions": metric.exclusions,
                "zero_semantics": metric.zero_semantics,
            }
            for metric in self.metrics.values()
        ]


@lru_cache(maxsize=1)
def load_semantic_registry() -> SemanticRegistry:
    root_setting = settings.LEDGERPROOF["REPO_ROOT"]
    root = root_setting if isinstance(root_setting, Path) else Path(str(root_setting))
    data = cast(
        dict[str, Any],
        yaml.safe_load((root / "contracts" / "semantic_metrics.yaml").read_text()),
    )
    if not isinstance(data, dict) or not isinstance(data.get("metrics"), dict):
        raise ValueError("semantic_metrics.yaml must define a metrics object")

    metrics: dict[str, MetricDefinition] = {}
    for metric_id, raw_metric in data["metrics"].items():
        if not isinstance(raw_metric, dict):
            raise ValueError(f"metric {metric_id} must be an object")
        mandatory_filters = raw_metric.get("mandatory_filters") or {}
        if not isinstance(mandatory_filters, dict):
            raise ValueError(f"metric {metric_id} mandatory_filters must be an object")
        metrics[str(metric_id)] = MetricDefinition(
            metric_id=str(metric_id),
            display_name=str(raw_metric["display_name"]),
            description=str(raw_metric["description"]),
            source=str(raw_metric["source"]),
            aggregation=str(raw_metric["aggregation"]),
            mandatory_filters={
                str(key): [str(item) for item in value]
                for key, value in mandatory_filters.items()
            },
            date_field=str(raw_metric["date_field"]) if raw_metric.get("date_field") else None,
            currency_field=str(raw_metric["currency_field"])
            if raw_metric.get("currency_field")
            else None,
            allowed_dimensions=[str(item) for item in raw_metric.get("allowed_dimensions", [])],
            aliases=[str(item) for item in raw_metric.get("aliases", [])],
            exclusions=[str(item) for item in raw_metric.get("exclusions", [])],
            zero_semantics=str(raw_metric["zero_semantics"])
            if raw_metric.get("zero_semantics")
            else None,
        )

    return SemanticRegistry(
        version=str(data["version"]),
        currency=str(data["currency"]),
        timezone=str(data["timezone"]),
        metrics=metrics,
        relative_dates=dict(data.get("relative_dates", {})),
        unsupported_domains=[str(item) for item in data.get("unsupported_domains", [])],
    )
