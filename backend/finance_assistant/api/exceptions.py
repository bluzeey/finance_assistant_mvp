"""Safe application/problem+json exception mapping."""
from __future__ import annotations

from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler

from finance_assistant.telemetry.request_id import get_trace_id


def problem_details_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """Convert DRF exceptions into RFC 9457-style problem details.

    Unhandled exceptions are left to Django so DEBUG/local tooling can surface them;
    production logging/error middleware can translate them later without leaking SQL
    or stack traces from this handler.
    """
    response = exception_handler(exc, context)
    if response is None:
        return None

    request = context.get("request")
    detail: str
    field_errors: dict[str, Any] | None = None

    if isinstance(response.data, dict):
        raw_detail = response.data.get("detail")
        if raw_detail is None:
            detail = "Request validation failed."
            field_errors = dict(response.data)
        else:
            detail = str(raw_detail)
    else:
        detail = str(response.data)

    response.data = {
        "type": _problem_type(response.status_code),
        "title": _title(response.status_code),
        "status": response.status_code,
        "detail": detail,
        "trace_id": get_trace_id(request),
    }
    if field_errors:
        response.data["field_errors"] = field_errors
    response.content_type = "application/problem+json"
    return response


def _problem_type(status_code: int) -> str:
    mapping = {
        400: "https://northstar.local/problems/bad-request",
        404: "https://northstar.local/problems/not-found",
        409: "https://northstar.local/problems/conflict",
        422: "https://northstar.local/problems/validation-error",
        429: "https://northstar.local/problems/rate-limited",
    }
    return mapping.get(status_code, "https://northstar.local/problems/api-error")


def _title(status_code: int) -> str:
    mapping = {
        400: "Bad request",
        404: "Not found",
        409: "Conflict",
        422: "Validation error",
        429: "Rate limited",
    }
    return mapping.get(status_code, "API error")
