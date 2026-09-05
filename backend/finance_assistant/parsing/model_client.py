"""Provider-independent model client with a Sarvam implementation.

The model returns only an InterpretationDraft. It never receives authority to
select arbitrary tables/fields, emit SQL, or calculate finance values.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol, cast

from django.conf import settings
from pydantic import ValidationError

from finance_assistant.domain.query_state import QueryState
from finance_assistant.parsing.model_schema import (
    InterpretationDraft,
    interpretation_draft_json_schema,
)
from finance_assistant.parsing.prompts import ChatMessage, build_interpretation_messages

SARVAM_CHAT_COMPLETIONS_PATH = "/chat/completions"
DEFAULT_SARVAM_BASE_URL = "https://api.sarvam.ai/v1"
DEFAULT_SARVAM_MODEL = "sarvam-105b-conversations"


class ModelProviderError(RuntimeError):
    """Base class for safe model-provider failures."""


class ModelConfigurationError(ModelProviderError):
    """Raised when provider credentials/configuration are missing or invalid."""


class ModelTimeoutError(ModelProviderError):
    """Raised when the provider call times out."""


class ModelRateLimitError(ModelProviderError):
    """Raised when the provider returns a rate-limit response."""


class ModelSchemaError(ModelProviderError):
    """Raised when the provider response cannot be validated as InterpretationDraft."""


@dataclass(frozen=True, slots=True)
class ModelUsage:
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None


@dataclass(frozen=True, slots=True)
class ModelCallResult:
    draft: InterpretationDraft
    provider: str
    model_id: str
    provider_response_id: str | None
    system_fingerprint: str | None
    finish_reason: str | None
    usage: ModelUsage
    latency_ms: int
    raw_content: str


class InterpretationModelClient(Protocol):
    """Provider interface used by orchestration code and tests."""

    def parse_interpretation(
        self,
        *,
        question: str,
        query_state: QueryState | None = None,
    ) -> ModelCallResult: ...


class JsonTransport(Protocol):
    def post_json(
        self,
        *,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]: ...


class UrllibJsonTransport:
    """Small stdlib transport to avoid tying the backend to one SDK."""

    def post_json(
        self,
        *,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]:
        data = json.dumps(body, ensure_ascii=False).encode()
        request = urllib.request.Request(url=url, data=data, method="POST", headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            _raise_http_error(exc)
        except TimeoutError as exc:
            raise ModelTimeoutError("Sarvam model request timed out") from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise ModelTimeoutError("Sarvam model request timed out") from exc
            raise ModelProviderError("Sarvam model request failed") from exc

        parsed = json.loads(response_body)
        if not isinstance(parsed, dict):
            raise ModelProviderError("Sarvam response was not a JSON object")
        return cast(dict[str, Any], parsed)


class SarvamChatCompletionClient:
    """Sarvam chat-completions client for structured InterpretationDraft output."""

    def __init__(
        self,
        *,
        api_key: str,
        api_subscription_key: str | None = None,
        base_url: str = DEFAULT_SARVAM_BASE_URL,
        model_id: str = DEFAULT_SARVAM_MODEL,
        timeout_seconds: float = 10.0,
        temperature: float = 0.1,
        max_tokens: int = 800,
        reasoning_effort: str | None = "low",
        seed: int | None = 20260904,
        transport: JsonTransport | None = None,
    ) -> None:
        if not api_key:
            raise ModelConfigurationError("SARVAM_API_KEY is required for Sarvam model calls")
        if model_id not in {"sarvam-105b", "sarvam-105b-conversations"}:
            raise ModelConfigurationError("Unsupported Sarvam chat model ID")
        self.api_key = api_key
        self.api_subscription_key = api_subscription_key or api_key
        self.base_url = base_url.rstrip("/")
        self.model_id = model_id
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort
        self.seed = seed
        self.transport = transport or UrllibJsonTransport()

    def parse_interpretation(
        self,
        *,
        question: str,
        query_state: QueryState | None = None,
    ) -> ModelCallResult:
        messages = build_interpretation_messages(question, query_state)
        return self._parse_with_repair(messages)

    def _parse_with_repair(self, messages: list[ChatMessage]) -> ModelCallResult:
        try:
            return self._call_and_validate(messages)
        except ModelSchemaError as first_error:
            repair_messages = [
                *messages,
                ChatMessage(
                    role="user",
                    content=(
                        "Your prior output did not validate against the "
                        "InterpretationDraft schema. "
                        f"Validation error: {first_error}. Return only a valid JSON object."
                    ),
                ),
            ]
            return self._call_and_validate(repair_messages)

    def _call_and_validate(self, messages: Sequence[ChatMessage]) -> ModelCallResult:
        body = self._request_body(messages)
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "api-subscription-key": self.api_subscription_key,
        }
        started = time.perf_counter()
        response = self.transport.post_json(
            url=f"{self.base_url}{SARVAM_CHAT_COMPLETIONS_PATH}",
            headers=headers,
            body=body,
            timeout_seconds=self.timeout_seconds,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        return _parse_sarvam_response(response, model_id=self.model_id, latency_ms=latency_ms)

    def _request_body(self, messages: Sequence[ChatMessage]) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self.model_id,
            "messages": [message.to_api() for message in messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "n": 1,
            "stream": False,
            "wiki_grounding": False,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "ledgerproof_interpretation_draft",
                    "description": (
                        "Constrained finance InterpretationDraft. It is not SQL "
                        "or an answer."
                    ),
                    "schema": interpretation_draft_json_schema(),
                    "strict": True,
                },
            },
        }
        if self.reasoning_effort is not None:
            body["reasoning_effort"] = self.reasoning_effort
        if self.seed is not None:
            body["seed"] = self.seed
        return body


class FakeInterpretationModelClient:
    """Network-free fake provider for unit and API tests."""

    def __init__(self, responses: Sequence[dict[str, Any] | InterpretationDraft]) -> None:
        if not responses:
            raise ValueError("FakeInterpretationModelClient requires at least one response")
        self._responses = list(responses)
        self.calls = 0

    def parse_interpretation(
        self,
        *,
        question: str,
        query_state: QueryState | None = None,
    ) -> ModelCallResult:
        del question, query_state
        response = self._responses[min(self.calls, len(self._responses) - 1)]
        self.calls += 1
        if isinstance(response, InterpretationDraft):
            draft = response
        else:
            draft = InterpretationDraft.model_validate(response)
        return ModelCallResult(
            draft=draft,
            provider="fake",
            model_id="fake-interpretation-model",
            provider_response_id="fake-response",
            system_fingerprint=None,
            finish_reason="stop",
            usage=ModelUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            latency_ms=0,
            raw_content=draft.model_dump_json(),
        )


class RecordingTransport:
    """Test transport that records requests and returns queued JSON responses."""

    def __init__(self, responses: Sequence[dict[str, Any]]) -> None:
        self.responses = list(responses)
        self.requests: list[dict[str, Any]] = []

    def post_json(
        self,
        *,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]:
        self.requests.append(
            {"url": url, "headers": headers, "body": body, "timeout_seconds": timeout_seconds}
        )
        if not self.responses:
            raise ModelProviderError("no fake transport response queued")
        return self.responses.pop(0)


def model_client_from_settings() -> InterpretationModelClient:
    provider = str(settings.LEDGERPROOF.get("MODEL_PROVIDER", "sarvam")).lower()
    if provider == "fake":
        return FakeInterpretationModelClient([_empty_response_payload()])
    if provider != "sarvam":
        raise ModelConfigurationError(f"Unsupported model provider: {provider}")

    api_key = str(settings.LEDGERPROOF.get("SARVAM_API_KEY") or "")
    api_subscription_key = settings.LEDGERPROOF.get("SARVAM_API_SUBSCRIPTION_KEY")
    return SarvamChatCompletionClient(
        api_key=api_key,
        api_subscription_key=str(api_subscription_key) if api_subscription_key else None,
        base_url=str(settings.LEDGERPROOF.get("SARVAM_BASE_URL", DEFAULT_SARVAM_BASE_URL)),
        model_id=str(settings.LEDGERPROOF.get("SARVAM_MODEL_ID", DEFAULT_SARVAM_MODEL)),
        timeout_seconds=_setting_float("SARVAM_TIMEOUT_SECONDS", 10.0),
        temperature=_setting_float("SARVAM_TEMPERATURE", 0.1),
        max_tokens=_setting_int("SARVAM_MAX_TOKENS", 800),
        reasoning_effort=cast(
            str | None,
            settings.LEDGERPROOF.get("SARVAM_REASONING_EFFORT", "low"),
        ),
        seed=cast(int | None, settings.LEDGERPROOF.get("SARVAM_SEED", 20260904)),
    )


def _setting_float(key: str, default: float) -> float:
    value = settings.LEDGERPROOF.get(key, default)
    return float(cast(str | int | float, value))


def _setting_int(key: str, default: int) -> int:
    value = settings.LEDGERPROOF.get(key, default)
    return int(cast(str | int, value))


def _parse_sarvam_response(
    response: dict[str, Any],
    *,
    model_id: str,
    latency_ms: int,
) -> ModelCallResult:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ModelSchemaError("Sarvam response did not contain choices")
    choice = choices[0]
    if not isinstance(choice, dict):
        raise ModelSchemaError("Sarvam choice was not an object")
    message = choice.get("message")
    if not isinstance(message, dict):
        raise ModelSchemaError("Sarvam choice message was not an object")
    raw_content = message.get("content")
    if not isinstance(raw_content, str):
        raise ModelSchemaError("Sarvam message content was not a string")

    try:
        parsed_content = json.loads(raw_content)
        draft = InterpretationDraft.model_validate(parsed_content)
    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
        raise ModelSchemaError(str(exc)) from exc

    usage_raw = response.get("usage") if isinstance(response.get("usage"), dict) else {}
    usage = cast(dict[str, Any], usage_raw)
    return ModelCallResult(
        draft=draft,
        provider="sarvam",
        model_id=str(response.get("model") or model_id),
        provider_response_id=str(response["id"]) if response.get("id") else None,
        system_fingerprint=str(response["system_fingerprint"])
        if response.get("system_fingerprint")
        else None,
        finish_reason=str(choice["finish_reason"]) if choice.get("finish_reason") else None,
        usage=ModelUsage(
            prompt_tokens=_optional_int(usage.get("prompt_tokens")),
            completion_tokens=_optional_int(usage.get("completion_tokens")),
            total_tokens=_optional_int(usage.get("total_tokens")),
        ),
        latency_ms=latency_ms,
        raw_content=raw_content,
    )


def _raise_http_error(exc: urllib.error.HTTPError) -> None:
    if exc.code == 429:
        raise ModelRateLimitError("Sarvam rate limit exceeded") from exc
    if exc.code == 408:
        raise ModelTimeoutError("Sarvam model request timed out") from exc
    raise ModelProviderError(f"Sarvam model request failed with HTTP {exc.code}") from exc


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _empty_response_payload() -> dict[str, Any]:
    return {
        "intent": None,
        "metric_candidate": None,
        "entities": [],
        "periods": [],
        "dimensions": [],
        "statuses": [],
        "correction_operations": [],
        "unsupported_concepts": [],
        "ambiguity_notes": [],
    }
