"""Health endpoint."""
from __future__ import annotations

import logging

from django.conf import settings
from django.db import connection
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from finance_assistant.api.serializers import HealthSerializer
from finance_assistant.metadata import dataset_manifest
from finance_assistant.telemetry.request_id import get_trace_id

logger = logging.getLogger(__name__)


class HealthView(APIView):
    authentication_classes: list[type] = []
    permission_classes: list[type] = []

    def get(self, request: Request) -> Response:
        payload = {
            "status": "ok",
            "database": _database_status(),
            "dataset_version": dataset_manifest()["dataset_version"],
            "app_version": settings.LEDGERPROOF["APP_VERSION"],
            "trace_id": get_trace_id(request),
        }
        serializer = HealthSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


def _database_status() -> str:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as exc:
        logger.warning("health.database_degraded", extra={"error_type": type(exc).__name__})
        return "degraded"
    return "ok"
