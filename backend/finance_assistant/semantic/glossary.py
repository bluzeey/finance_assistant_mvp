"""Build user-facing glossary entries from versioned semantic metadata."""
from __future__ import annotations

from typing import Any

from finance_assistant.semantic.registry import load_semantic_registry


def glossary_items(search: str | None = None) -> list[dict[str, Any]]:
    registry = load_semantic_registry()
    items: list[dict[str, Any]] = []

    for metric in registry.metrics.values():
        items.append(
            {
                "id": f"metric:{metric.metric_id}",
                "kind": "metric",
                "label": metric.display_name,
                "description": metric.description,
                "source": metric.source,
                "aggregation": metric.aggregation,
                "mandatory_filters": metric.mandatory_filters,
                "date_field": metric.date_field,
                "aliases": metric.aliases,
                "exclusions": metric.exclusions,
            }
        )

    for key, value in registry.relative_dates.items():
        items.append(
            {
                "id": f"date:{key}",
                "kind": "date",
                "label": key.replace("_", " ").title(),
                "description": value.get("rule", ""),
                "example_range": value.get("example_range"),
            }
        )

    for index, domain in enumerate(registry.unsupported_domains, start=1):
        items.append(
            {
                "id": f"unsupported:{index}",
                "kind": "unsupported_domain",
                "label": domain,
                "description": "LedgerProof returns no number for this unsupported domain.",
            }
        )

    if not search:
        return items

    normalized = search.strip().lower()
    return [
        item
        for item in items
        if normalized in str(item.get("label", "")).lower()
        or normalized in str(item.get("description", "")).lower()
    ]
