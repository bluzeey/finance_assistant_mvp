"""Request ID middleware.

Trace IDs are safe opaque identifiers that can be shared with users. The
middleware intentionally does not log raw source rows or prompts.
"""
from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from django.http import HttpRequest, HttpResponse

TRACE_HEADER = "X-Trace-Id"


class RequestIdMiddleware:
    """Attach a stable trace ID to each request and response."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        incoming = request.headers.get(TRACE_HEADER)
        trace_id: str = (
            incoming if incoming is not None and _is_safe_trace_id(incoming) else str(uuid.uuid4())
        )
        request.trace_id = trace_id  # type: ignore[attr-defined]
        response = self.get_response(request)
        response[TRACE_HEADER] = trace_id
        return response


def get_trace_id(request: Any | None) -> str:
    trace_id = getattr(request, "trace_id", None)
    return trace_id if isinstance(trace_id, str) and trace_id else str(uuid.uuid4())


def _is_safe_trace_id(value: str | None) -> bool:
    if not value or len(value) > 128:
        return False
    return all(char.isalnum() or char in {"-", "_", "."} for char in value)
