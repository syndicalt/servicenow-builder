"""Anthropic Messages API provider adapter for implementation-candidate generation.

Mirrors :mod:`jedi_devproject.openai_provider`: hand-rolled HTTP against an
injectable transport (no SDK dependency), strict fail-closed validation of the
structured response, and no secrets in raised errors. The adapter is
boundary-agnostic; whether it may run for a given data class/task remains a
provider-policy decision enforced by :mod:`jedi_devproject.providers`.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Mapping
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from jedi_devproject.provider_contract import (
    IMPLEMENTATION_SYSTEM_PROMPT,
    implementation_candidate_schema,
)
from jedi_devproject.servicenow import HttpRequest, HttpResponse

ANTHROPIC_API_VERSION = "2023-06-01"
DEFAULT_ANTHROPIC_BASE_URL = "https://api.anthropic.com"
DEFAULT_ANTHROPIC_MODEL = "claude-opus-4-8"
DEFAULT_ANTHROPIC_MAX_TOKENS = 16000

ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"
ANTHROPIC_BASE_URL_ENV = "ANTHROPIC_BASE_URL"
ANTHROPIC_MODEL_ENV = "ANTHROPIC_MODEL"
ANTHROPIC_MAX_TOKENS_ENV = "ANTHROPIC_MAX_TOKENS"

_RETRYABLE_STATUS_CODES = frozenset({429, 500, 529})
_BACKOFF_BASE_SECONDS = 1.0
_BACKOFF_MAX_SECONDS = 30.0
_REDACTED = "[REDACTED]"

# Anthropic structured outputs reject these JSON Schema constraints; the
# deterministic validators downstream still enforce the stripped invariants.
_UNSUPPORTED_SCHEMA_CONSTRAINTS = frozenset(
    {
        "exclusiveMaximum",
        "exclusiveMinimum",
        "maxItems",
        "maxLength",
        "maximum",
        "minItems",
        "minLength",
        "minimum",
        "multipleOf",
    }
)

class AnthropicProviderError(RuntimeError):
    """Raised when the Anthropic provider cannot return validated JSON."""


class AnthropicProviderRefusal(AnthropicProviderError):
    """Raised when the model declines the request (``stop_reason=refusal``).

    Callers route this outcome to manual review instead of retrying; the
    structured output may be absent or schema-invalid on refusal.
    """


class AnthropicProviderConfigError(ValueError):
    """Raised when Anthropic provider environment configuration is invalid."""


class AnthropicProviderSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    api_key: str
    model: str = DEFAULT_ANTHROPIC_MODEL
    base_url: str = DEFAULT_ANTHROPIC_BASE_URL
    max_tokens: int = Field(default=DEFAULT_ANTHROPIC_MAX_TOKENS, gt=0)


class AnthropicHttpResponse(BaseModel):
    """HTTP response carrying headers (``retry-after``, ``request-id``).

    The shared :class:`jedi_devproject.servicenow.HttpResponse` drops response
    headers; transports that can surface them return this model instead. Both
    shapes satisfy :class:`AnthropicHttpTransport`.
    """

    model_config = ConfigDict(extra="forbid")

    status_code: int
    json_body: dict[str, Any] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)


class AnthropicHttpTransport(Protocol):
    def send(self, request: HttpRequest) -> HttpResponse | AnthropicHttpResponse:
        """Send an HTTP request and return a JSON response."""


def anthropic_provider_settings_from_env(
    env: Mapping[str, str] | None = None,
) -> AnthropicProviderSettings:
    """Build settings from the environment, failing closed on bad config.

    Follows the OpenAI adapter's vendor-prefixed naming convention
    (``OPENAI_API_KEY``/``OPENAI_MODEL`` -> ``ANTHROPIC_API_KEY``/...).
    Raises :class:`AnthropicProviderConfigError` rather than returning a
    partially configured client.
    """
    values: Mapping[str, str] = os.environ if env is None else env
    api_key = (values.get(ANTHROPIC_API_KEY_ENV) or "").strip()
    if not api_key:
        raise AnthropicProviderConfigError(
            f"{ANTHROPIC_API_KEY_ENV} is required to configure the Anthropic provider"
        )
    return AnthropicProviderSettings(
        api_key=api_key,
        model=(values.get(ANTHROPIC_MODEL_ENV) or "").strip() or DEFAULT_ANTHROPIC_MODEL,
        base_url=(values.get(ANTHROPIC_BASE_URL_ENV) or "").strip() or DEFAULT_ANTHROPIC_BASE_URL,
        max_tokens=_max_tokens_from_env(values.get(ANTHROPIC_MAX_TOKENS_ENV)),
    )


class AnthropicMessagesProvider:
    """ModelProvider adapter for ``POST /v1/messages`` structured outputs."""

    def __init__(
        self,
        *,
        settings: AnthropicProviderSettings,
        transport: AnthropicHttpTransport,
        max_retries: int = 2,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if max_retries < 0:
            raise AnthropicProviderConfigError("max_retries must be >= 0")
        self._settings = settings
        self._transport = transport
        self._max_retries = max_retries
        self._sleep = sleep

    def generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._send_with_retries(self._build_request(payload))
        if response.status_code >= 400:
            raise AnthropicProviderError(self._api_error_message(response))
        return self._parse_message(response.json_body)

    def _build_request(self, payload: dict[str, Any]) -> HttpRequest:
        return HttpRequest(
            method="POST",
            url=f"{self._settings.base_url.rstrip('/')}/v1/messages",
            headers={
                "x-api-key": self._settings.api_key,
                "anthropic-version": ANTHROPIC_API_VERSION,
                "content-type": "application/json",
            },
            body={
                "model": self._settings.model,
                "max_tokens": self._settings.max_tokens,
                # Shared with the OpenAI adapter via provider_contract so the
                # two providers stay byte-identical for model_fulfillment.
                "system": IMPLEMENTATION_SYSTEM_PROMPT,
                "messages": [
                    {
                        "role": "user",
                        "content": json.dumps(payload, sort_keys=True),
                    }
                ],
                "output_config": {
                    "format": {
                        "type": "json_schema",
                        "schema": _anthropic_candidate_schema(),
                    }
                },
            },
        )

    def _send_with_retries(self, request: HttpRequest) -> HttpResponse | AnthropicHttpResponse:
        attempt = 0
        while True:
            response = self._transport.send(request)
            if response.status_code not in _RETRYABLE_STATUS_CODES:
                return response
            if attempt >= self._max_retries:
                return response
            self._sleep(
                _retry_delay(
                    attempt=attempt,
                    retry_after_header=_response_headers(response).get("retry-after"),
                )
            )
            attempt += 1

    def _parse_message(self, body: dict[str, Any]) -> dict[str, Any]:
        stop_reason = body.get("stop_reason")
        if stop_reason == "refusal":
            raise AnthropicProviderRefusal(
                "Anthropic model declined the request (stop_reason=refusal); "
                "route the story to manual review"
            )
        if stop_reason == "max_tokens":
            raise AnthropicProviderError(
                "Anthropic response was truncated (stop_reason=max_tokens); "
                "the structured output is incomplete"
            )
        if stop_reason != "end_turn":
            raise AnthropicProviderError(
                f"Anthropic response had unexpected stop_reason: {stop_reason!r}"
            )
        return _normalise_candidate_response(
            _loads_json_object(_first_text_block(body.get("content")))
        )

    def _api_error_message(self, response: HttpResponse | AnthropicHttpResponse) -> str:
        details = _api_error_details(response.json_body)
        request_id = _response_headers(response).get("request-id")
        message = f"Anthropic Messages API failed with status {response.status_code}"
        if details:
            message = f"{message}: {details}"
        if request_id:
            message = f"{message}; request_id={request_id}"
        return self._redact(message)

    def _redact(self, text: str) -> str:
        api_key = self._settings.api_key
        if api_key and api_key in text:
            return text.replace(api_key, _REDACTED)
        return text


def _max_tokens_from_env(raw: str | None) -> int:
    text = (raw or "").strip()
    if not text:
        return DEFAULT_ANTHROPIC_MAX_TOKENS
    try:
        max_tokens = int(text)
    except ValueError as exc:
        raise AnthropicProviderConfigError(
            f"{ANTHROPIC_MAX_TOKENS_ENV} must be a positive integer"
        ) from exc
    if max_tokens <= 0:
        raise AnthropicProviderConfigError(
            f"{ANTHROPIC_MAX_TOKENS_ENV} must be a positive integer"
        )
    return max_tokens


def _response_headers(response: HttpResponse | AnthropicHttpResponse) -> dict[str, str]:
    if isinstance(response, AnthropicHttpResponse):
        return {key.lower(): value for key, value in response.headers.items()}
    return {}


def _retry_delay(*, attempt: int, retry_after_header: str | None) -> float:
    if retry_after_header is not None:
        try:
            retry_after = float(retry_after_header.strip())
        except ValueError:
            retry_after = -1.0
        if retry_after >= 0:
            return min(retry_after, _BACKOFF_MAX_SECONDS)
    return min(_BACKOFF_BASE_SECONDS * (2.0**attempt), _BACKOFF_MAX_SECONDS)


def _first_text_block(content: Any) -> str:
    if isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and isinstance(block.get("text"), str):
                return str(block["text"])
    raise AnthropicProviderError("Anthropic response did not include a text content block")


def _api_error_details(response_body: dict[str, Any]) -> str:
    error = response_body.get("error")
    if not isinstance(error, dict):
        return ""

    parts: list[str] = []
    message = error.get("message")
    if isinstance(message, str) and message:
        parts.append(message)

    error_type = error.get("type")
    if isinstance(error_type, str) and error_type:
        parts.append(f"type={error_type}")

    return "; ".join(parts)


def _loads_json_object(raw_json: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise AnthropicProviderError("Anthropic response was not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise AnthropicProviderError("Anthropic response JSON must be an object")
    return parsed


def _normalise_candidate_response(candidate: dict[str, Any]) -> dict[str, Any]:
    changes = candidate.get("changes")
    if not isinstance(changes, list):
        raise AnthropicProviderError("Anthropic response changes must be a list")

    normalised_changes: list[dict[str, Any]] = []
    for change in changes:
        if not isinstance(change, dict):
            raise AnthropicProviderError("Anthropic response change must be an object")
        fields = change.get("fields")
        if not isinstance(fields, list):
            raise AnthropicProviderError(
                "Anthropic response change fields must be a list of name/value pairs"
            )
        normalised_fields: dict[str, Any] = {}
        for field in fields:
            if not isinstance(field, dict):
                raise AnthropicProviderError("Anthropic response field entry must be an object")
            name = field.get("name")
            if not isinstance(name, str) or not name:
                raise AnthropicProviderError(
                    "Anthropic response field entry must include a non-empty name"
                )
            normalised_fields[name] = field.get("value")
        normalised_changes.append({**change, "fields": normalised_fields})

    return {**candidate, "changes": normalised_changes}


def _anthropic_candidate_schema() -> dict[str, Any]:
    """The shared implementation-candidate schema, minus constraints the
    Anthropic structured-output validator rejects (numeric/length bounds).
    """
    schema = _without_unsupported_constraints(implementation_candidate_schema())
    if not isinstance(schema, dict):  # pragma: no cover - schema source is a dict literal
        raise AnthropicProviderError("implementation candidate schema must be an object")
    return schema


def _without_unsupported_constraints(node: Any) -> Any:
    if isinstance(node, dict):
        return {
            key: _without_unsupported_constraints(value)
            for key, value in node.items()
            if key not in _UNSUPPORTED_SCHEMA_CONSTRAINTS
        }
    if isinstance(node, list):
        return [_without_unsupported_constraints(item) for item in node]
    return node
