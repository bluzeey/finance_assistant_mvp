"""Metadata and glossary endpoints."""
from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from finance_assistant.api.serializers import GlossaryResponseSerializer, MetaResponseSerializer
from finance_assistant.metadata import build_meta_response
from finance_assistant.semantic.glossary import glossary_items


class MetaView(APIView):
    authentication_classes: list[type] = []
    permission_classes: list[type] = []

    def get(self, request: Request) -> Response:
        serializer = MetaResponseSerializer(data=build_meta_response())
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class GlossaryView(APIView):
    authentication_classes: list[type] = []
    permission_classes: list[type] = []

    def get(self, request: Request) -> Response:
        search = request.query_params.get("search")
        serializer = GlossaryResponseSerializer(data={"items": glossary_items(search)})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)
