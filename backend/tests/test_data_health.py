from __future__ import annotations

import pytest
from django.test import Client

from finance_assistant.checks.data_health import build_data_health_response


@pytest.mark.django_db
def test_data_health_endpoint_exposes_planted_warnings(client: Client) -> None:
    response = client.get("/api/v1/data-health")

    assert response.status_code == 200
    body = response.json()
    assert body["overall_state"] == "warning"
    assert body["data_as_of"] == "2026-09-03"

    checks = {check["check_id"]: check for check in body["checks"]}
    assert checks["DH-MISSING-RECONCILIATION"]["affected_record_count"] == 1
    assert "TXN-MISSING-REC-001" in checks["DH-MISSING-RECONCILIATION"]["sample_record_ids"]
    assert "PAY-DUP-001" in checks["DH-DUPLICATE-PAYOUTS"]["sample_record_ids"]
    assert "PAY-DUP-002" in checks["DH-DUPLICATE-PAYOUTS"]["sample_record_ids"]
    assert checks["DH-PAYOUT-CASH-SEMANTICS"]["status"] == "pass"


def test_data_health_uses_dataset_anchor_not_wall_clock() -> None:
    body = build_data_health_response()
    checks = {check["check_id"]: check for check in body["checks"]}

    assert body["data_as_of"] == "2026-09-03"
    assert "data_as_of is 2026-09-03" in checks["DH-FRESHNESS-TRANSACTIONS"]["details"]
