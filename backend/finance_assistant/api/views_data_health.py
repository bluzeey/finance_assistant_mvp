"""Data-health endpoints."""
from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from finance_assistant.api.serializers import DataHealthResponseSerializer
from finance_assistant.checks.data_health import build_data_health_response


class DataHealthView(APIView):
    authentication_classes: list[type] = []
    permission_classes: list[type] = []

    def get(self, request: Request) -> Response:
        serializer = DataHealthResponseSerializer(data=build_data_health_response())
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)
