"""DRF serializers for public HTTP shapes."""
from __future__ import annotations

from typing import Any

from rest_framework import serializers


class HealthSerializer(serializers.Serializer[dict[str, Any]]):
    status = serializers.ChoiceField(choices=["ok"])
    database = serializers.ChoiceField(choices=["ok", "degraded"])
    dataset_version = serializers.CharField()
    app_version = serializers.CharField()
    trace_id = serializers.CharField()


class CompanySerializer(serializers.Serializer[dict[str, Any]]):
    company_id = serializers.CharField()
    display_name = serializers.CharField()
    currency = serializers.ChoiceField(choices=["INR"])
    timezone = serializers.ChoiceField(choices=["Asia/Kolkata"])
    fiscal_year_start_month = serializers.IntegerField(min_value=1, max_value=12)
    synthetic = serializers.BooleanField()


class DatasetSerializer(serializers.Serializer[dict[str, Any]]):
    version = serializers.CharField()
    data_as_of = serializers.DateField()
    max_posting_date = serializers.DateField()
    max_payout_date = serializers.DateField()
    freshness_state = serializers.ChoiceField(choices=["fresh", "stale", "unknown"])
    generated_at = serializers.CharField()


class MetaResponseSerializer(serializers.Serializer[dict[str, Any]]):
    company = CompanySerializer()
    dataset = DatasetSerializer()
    supported_metrics = serializers.ListField(child=serializers.DictField())
    supported_examples = serializers.ListField(child=serializers.CharField())
    versions = serializers.DictField()
    features = serializers.DictField()


class GlossaryResponseSerializer(serializers.Serializer[dict[str, Any]]):
    items = serializers.ListField(child=serializers.DictField())


class DataHealthCheckSerializer(serializers.Serializer[dict[str, Any]]):
    check_id = serializers.CharField()
    category = serializers.ChoiceField(
        choices=[
            "freshness",
            "schema",
            "referential_integrity",
            "coverage",
            "duplicates",
            "precision",
            "reconciliation",
        ]
    )
    status = serializers.ChoiceField(choices=["pass", "warning", "fail"])
    label = serializers.CharField()  # type: ignore[assignment]
    details = serializers.CharField()
    affected_record_count = serializers.IntegerField(min_value=0)
    sample_record_ids = serializers.ListField(child=serializers.CharField(), required=False)


class DataHealthResponseSerializer(serializers.Serializer[dict[str, Any]]):
    overall_state = serializers.ChoiceField(choices=["healthy", "warning", "error"])
    data_as_of = serializers.DateField()
    checks = DataHealthCheckSerializer(many=True)
