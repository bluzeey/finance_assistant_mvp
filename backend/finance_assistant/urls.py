"""Versioned API routes owned by the finance assistant app."""
from __future__ import annotations

from django.urls import path

from finance_assistant.api.views_data_health import DataHealthView
from finance_assistant.api.views_meta import GlossaryView, MetaView

urlpatterns = [
    path("meta", MetaView.as_view(), name="meta"),
    path("glossary", GlossaryView.as_view(), name="glossary"),
    path("data-health", DataHealthView.as_view(), name="data-health"),
]
