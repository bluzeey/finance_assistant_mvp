"""URL routes for the LedgerProof API."""
from __future__ import annotations

from django.urls import include, path

from finance_assistant.api.views_health import HealthView

urlpatterns = [
    path("health", HealthView.as_view(), name="health"),
    path("api/v1/health", HealthView.as_view(), name="api-health"),
    path("api/v1/", include("finance_assistant.urls")),
]
