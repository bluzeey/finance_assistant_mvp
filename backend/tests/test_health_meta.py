from __future__ import annotations

import pytest
from django.test import Client


@pytest.mark.django_db
def test_health_endpoint_returns_dataset_and_trace_id(client: Client) -> None:
    response = client.get("/api/v1/health", headers={"X-Trace-Id": "trace-test-1"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["dataset_version"] == "2026.09.04-hackathon-v1"
    assert body["trace_id"] == "trace-test-1"
    assert response.headers["X-Trace-Id"] == "trace-test-1"


@pytest.mark.django_db
def test_meta_endpoint_exposes_dataset_anchor_and_semantics(client: Client) -> None:
    response = client.get("/api/v1/meta")

    assert response.status_code == 200
    body = response.json()
    assert body["company"]["display_name"] == "Northstar Labs"
    assert body["company"]["currency"] == "INR"
    assert body["dataset"]["data_as_of"] == "2026-09-03"
    assert body["dataset"]["freshness_state"] == "fresh"

    payout_metric = next(
        metric
        for metric in body["supported_metrics"]
        if metric["metric_id"] == "vendor_payout_amount"
    )
    assert payout_metric["date_field"] == "payout_date"
    assert payout_metric["mandatory_filters"] == {"payout_status": ["completed"]}
    assert body["versions"]["model_provider"] == "sarvam"
    assert body["versions"]["model_id"] == "sarvam-105b-conversations"


@pytest.mark.django_db
def test_glossary_search_is_generated_from_semantic_contract(client: Client) -> None:
    response = client.get("/api/v1/glossary", {"search": "forecast"})

    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    forbidden_fragment = "expected" + "_aggregates"
    assert all(forbidden_fragment not in str(item) for item in items)
    assert any(item["kind"] == "unsupported_domain" for item in items)
