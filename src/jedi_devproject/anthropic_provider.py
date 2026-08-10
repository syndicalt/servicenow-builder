"""Anthropic Messages API provider adapter for implementation-candidate generation.

Mirrors :mod:`jedi_devproject.openai_provider`: hand-rolled HTTP against an
injectable transport (no SDK dependency), strict fail-closed validation of the
structured response, and no secrets in raised errors. The adapter is
boundary-agnostic; whether it may run for a given data class/task remains a
provider-policy decision enforced by :mod:`jedi_devproject.providers`.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable, Mapping
from itertools import islice
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator

from jedi_devproject.diagnostic_redaction import _redact_diagnostic_text
from jedi_devproject.numeric_settings import (
    parse_optional_ascii_decimal_float,
    parse_optional_base10_int,
)
from jedi_devproject.provider_contract import (
    IMPLEMENTATION_SYSTEM_PROMPT,
    implementation_candidate_schema,
    implementation_payload_json,
    loads_strict_json_object,
)
from jedi_devproject.provider_response_normalization import (
    normalise_provider_candidate_response,
)
from jedi_devproject.provider_settings_safety import (
    validate_provider_api_key,
    validate_provider_model,
)
from jedi_devproject.provider_url_safety import validate_provider_base_url
from jedi_devproject.servicenow import HttpRequest, HttpResponse
from jedi_devproject.url_query_safety import has_whitespace_or_control_character

ANTHROPIC_API_VERSION = "2023-06-01"
DEFAULT_ANTHROPIC_BASE_URL = "https://api.anthropic.com"
DEFAULT_ANTHROPIC_MODEL = "claude-3-opus-20240229"
DEFAULT_ANTHROPIC_MAX_TOKENS = 16000
MAX_ANTHROPIC_MAX_TOKENS = 128000

ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"
ANTHROPIC_BASE_URL_ENV = "ANTHROPIC_BASE_URL"
ANTHROPIC_MODEL_ENV = "ANTHROPIC_MODEL"
ANTHROPIC_MAX_TOKENS_ENV = "ANTHROPIC_MAX_TOKENS"

_RETRYABLE_STATUS_CODES = frozenset({429, 500, 529})
MAX_ANTHROPIC_PROVIDER_RETRIES = 5
_BACKOFF_BASE_SECONDS = 1.0
_BACKOFF_MAX_SECONDS = 30.0
_REDACTED = "[REDACTED]"
MAX_ANTHROPIC_PROVIDER_DIAGNOSTIC_CHARS = 4096
MAX_ANTHROPIC_PROVIDER_MESSAGE_CHARS = 3600
MAX_ANTHROPIC_HEADER_DIAGNOSTIC_CHARS = 256
MAX_ANTHROPIC_PROVIDER_OUTPUT_CHARS = 1_000_000
MAX_ANTHROPIC_PROVIDER_RESPONSE_COLLECTION_ITEMS = 100
ANTHROPIC_PROVIDER_TRUNCATION_MARKER = "...[truncated]"
UNSUPPORTED_ANTHROPIC_METADATA_VALUE = "[unsupported provider metadata value]"

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
        "pattern",
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
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    api_key: str
    model: str = DEFAULT_ANTHROPIC_MODEL
    base_url: str = DEFAULT_ANTHROPIC_BASE_URL
    max_tokens: int = Field(
        default=DEFAULT_ANTHROPIC_MAX_TOKENS,
        gt=0,
        le=MAX_ANTHROPIC_MAX_TOKENS,
    )

    @field_validator("api_key", "model")
    @classmethod
    def _credential_fields_must_not_contain_control_characters(
        cls,
        value: str,
        info: Any,
    ) -> str:
        if info.field_name == "api_key":
            return validate_provider_api_key(value)
        return validate_provider_model(value)

    @field_validator("base_url")
    @classmethod
    def _base_url_must_not_contain_control_characters(cls, value: str) -> str:
        return validate_provider_base_url(value)


class AnthropicHttpResponse(BaseModel):
    """HTTP response carrying headers (``retry-after``, ``request-id``).

    The shared :class:`jedi_devproject.servicenow.HttpResponse` drops response
    headers; transports that can surface them return this model instead. Both
    shapes satisfy :class:`AnthropicHttpTransport`.
    """

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

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
    api_key = _required_provider_env_value(values, ANTHROPIC_API_KEY_ENV)
    if not api_key:
        raise AnthropicProviderConfigError(
            f"{ANTHROPIC_API_KEY_ENV} is required to configure the Anthropic provider"
        )
    return AnthropicProviderSettings(
        api_key=api_key,
        model=_optional_provider_env_value(
            values,
            ANTHROPIC_MODEL_ENV,
            default=DEFAULT_ANTHROPIC_MODEL,
        ),
        base_url=_optional_provider_env_value(
            values,
            ANTHROPIC_BASE_URL_ENV,
            default=DEFAULT_ANTHROPIC_BASE_URL,
        ),
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
        if max_retries > MAX_ANTHROPIC_PROVIDER_RETRIES:
            raise AnthropicProviderConfigError(
                f"max_retries must be <= {MAX_ANTHROPIC_PROVIDER_RETRIES}"
            )
        self._settings = settings
        self._transport = transport
        self._max_retries = max_retries
        self._sleep = sleep

    def generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._send_with_retries(self._build_request(payload))
        status_code = _response_status_code(response)
        if status_code >= 400:
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
                        "content": implementation_payload_json(
                            payload,
                            error_factory=AnthropicProviderError,
                        ),
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
            status_code = _response_status_code(response)
            if status_code not in _RETRYABLE_STATUS_CODES:
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
        if type(body) is not dict:
            raise AnthropicProviderError("Anthropic response JSON body must be an exact object")
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
                "Anthropic response had unexpected stop_reason: "
                f"{self._diagnostic_value(stop_reason)}"
            )
        return _normalise_candidate_response(
            _loads_json_object(_first_text_block(body.get("content")))
        )

    def _api_error_message(self, response: HttpResponse | AnthropicHttpResponse) -> str:
        details = _api_error_details(response.json_body, api_key=self._settings.api_key)
        request_id = _response_headers(response).get("request-id")
        message = f"Anthropic Messages API failed with status {response.status_code}"
        if details:
            message = f"{message}: {details}"
        if request_id:
            message = (
                f"{message}; request_id="
                f"{_safe_header_diagnostic_value(request_id, api_key=self._settings.api_key)}"
            )
        return _bound_provider_diagnostic(self._redact_configured_api_key(message))

    def _redact_configured_api_key(self, text: str) -> str:
        api_key = self._settings.api_key
        if api_key and api_key in text:
            return text.replace(api_key, _REDACTED)
        return text

    def _diagnostic_value(self, value: Any) -> str:
        return _safe_provider_metadata_value(value, api_key=self._settings.api_key)


def _max_tokens_from_env(raw: str | None) -> int:
    text = _optional_provider_env_value(
        {ANTHROPIC_MAX_TOKENS_ENV: raw or ""},
        ANTHROPIC_MAX_TOKENS_ENV,
        default="",
    )
    if not text:
        return DEFAULT_ANTHROPIC_MAX_TOKENS
    try:
        max_tokens = parse_optional_base10_int(text, name=ANTHROPIC_MAX_TOKENS_ENV)
    except ValueError:
        raise AnthropicProviderConfigError(
            f"{ANTHROPIC_MAX_TOKENS_ENV} must use ASCII base-10 digits only"
        ) from None
    if max_tokens is None:
        return DEFAULT_ANTHROPIC_MAX_TOKENS
    if max_tokens <= 0:
        raise AnthropicProviderConfigError(
            f"{ANTHROPIC_MAX_TOKENS_ENV} must be a positive integer"
        )
    if max_tokens > MAX_ANTHROPIC_MAX_TOKENS:
        raise AnthropicProviderConfigError(
            f"{ANTHROPIC_MAX_TOKENS_ENV} must be <= {MAX_ANTHROPIC_MAX_TOKENS}"
        )
    return max_tokens


def _required_provider_env_value(values: Mapping[str, str], key: str) -> str:
    raw_value = values.get(key) or ""
    if not raw_value:
        return ""
    if raw_value.strip() != raw_value:
        raise AnthropicProviderConfigError(
            f"{key} must not include leading or trailing whitespace"
        )
    return raw_value


def _optional_provider_env_value(
    values: Mapping[str, str],
    key: str,
    *,
    default: str,
) -> str:
    raw_value = values.get(key)
    if raw_value is None or raw_value == "":
        return default
    if raw_value.strip() == "":
        return default
    if raw_value.strip() != raw_value:
        raise AnthropicProviderConfigError(
            f"{key} must not include leading or trailing whitespace"
        )
    return raw_value


def _response_headers(response: HttpResponse | AnthropicHttpResponse) -> dict[str, str]:
    if not isinstance(response, AnthropicHttpResponse):
        return {}
    headers = response.headers
    if type(headers) is not dict:
        return {}
    normalized_headers: dict[str, str] = {}
    for key, value in headers.items():
        if type(key) is not str or type(value) is not str:
            continue
        normalized_headers[key.lower()] = value
    return normalized_headers


def _response_status_code(response: Any) -> int:
    if type(response) not in {HttpResponse, AnthropicHttpResponse}:
        raise AnthropicProviderError(
            "Anthropic transport response must be an exact HttpResponse or AnthropicHttpResponse"
        )
    status_code = response.status_code
    if type(status_code) is not int:
        raise AnthropicProviderError("Anthropic response status code must be an exact integer")
    if status_code < 100 or status_code > 599:
        raise AnthropicProviderError("Anthropic response status code must be in the HTTP range")
    return status_code


def _retry_delay(*, attempt: int, retry_after_header: str | None) -> float:
    if retry_after_header is not None:
        retry_after = _retry_after_seconds(retry_after_header)
        if retry_after is not None:
            return min(retry_after, _BACKOFF_MAX_SECONDS)
    return min(_BACKOFF_BASE_SECONDS * (2.0**attempt), _BACKOFF_MAX_SECONDS)


def _retry_after_seconds(retry_after_header: str) -> float | None:
    if (
        retry_after_header == ""
        or retry_after_header != retry_after_header.strip()
        or has_whitespace_or_control_character(retry_after_header)
    ):
        return None
    try:
        retry_after = parse_optional_ascii_decimal_float(
            retry_after_header,
            name="retry-after",
        )
    except ValueError:
        return None
    if retry_after is None or retry_after < 0:
        return None
    return retry_after


def _first_text_block(content: Any) -> str:
    if type(content) is list:
        for block in islice(content, MAX_ANTHROPIC_PROVIDER_RESPONSE_COLLECTION_ITEMS):
            if type(block) is not dict:
                continue
            block_type = block.get("type")
            text = block.get("text")
            if type(block_type) is str and block_type == "text" and type(text) is str:
                return text
    raise AnthropicProviderError("Anthropic response did not include a text content block")


def _api_error_details(response_body: dict[str, Any], *, api_key: str = "") -> str:
    if type(response_body) is not dict:
        return ""
    error = response_body.get("error")
    if type(error) is not dict:
        return ""

    parts: list[str] = []
    message = error.get("message")
    if type(message) is str and message:
        parts.append(_redact_provider_message(message, api_key=api_key))

    error_type = error.get("type")
    if type(error_type) is str and error_type:
        parts.append(f"type={_safe_structured_error_metadata(error_type, api_key=api_key)}")

    return "; ".join(parts)


def _redact_provider_message(value: str, *, api_key: str) -> str:
    redacted = _redact_diagnostic_text(value) or ""
    if api_key:
        redacted = redacted.replace(api_key, _REDACTED)
    return _bound_provider_message(redacted)


def _safe_structured_error_metadata(value: str, *, api_key: str) -> str:
    redacted = _redact_provider_message(value, api_key=api_key)
    return " ".join(redacted.split())


def _bound_provider_message(value: str) -> str:
    if len(value) <= MAX_ANTHROPIC_PROVIDER_MESSAGE_CHARS:
        return value
    return (
        f"{value[:MAX_ANTHROPIC_PROVIDER_MESSAGE_CHARS]}"
        f"{ANTHROPIC_PROVIDER_TRUNCATION_MARKER}"
    )


def _safe_header_diagnostic_value(value: str, *, api_key: str) -> str:
    redacted = _redact_diagnostic_text(value) or ""
    if api_key:
        redacted = redacted.replace(api_key, _REDACTED)
    printable = "".join(char if char.isprintable() else " " for char in redacted)
    if len(printable) <= MAX_ANTHROPIC_HEADER_DIAGNOSTIC_CHARS:
        return printable
    return (
        f"{printable[:MAX_ANTHROPIC_HEADER_DIAGNOSTIC_CHARS]}"
        f"{ANTHROPIC_PROVIDER_TRUNCATION_MARKER}"
    )


def _safe_provider_metadata_value(value: Any, *, api_key: str) -> str:
    if type(value) is not str:
        return UNSUPPORTED_ANTHROPIC_METADATA_VALUE
    redacted = _redact_diagnostic_text(value) or ""
    if api_key:
        redacted = redacted.replace(api_key, _REDACTED)
    printable = "".join(char if char.isprintable() else " " for char in redacted)
    if len(printable) <= MAX_ANTHROPIC_PROVIDER_DIAGNOSTIC_CHARS:
        return printable
    return (
        f"{printable[:MAX_ANTHROPIC_PROVIDER_DIAGNOSTIC_CHARS]}"
        f"{ANTHROPIC_PROVIDER_TRUNCATION_MARKER}"
    )


def _bound_provider_diagnostic(value: str) -> str:
    if len(value) <= MAX_ANTHROPIC_PROVIDER_DIAGNOSTIC_CHARS:
        return value
    return (
        f"{value[:MAX_ANTHROPIC_PROVIDER_DIAGNOSTIC_CHARS]}"
        f"{ANTHROPIC_PROVIDER_TRUNCATION_MARKER}"
    )


def _loads_json_object(raw_json: str) -> dict[str, Any]:
    if len(raw_json) > MAX_ANTHROPIC_PROVIDER_OUTPUT_CHARS:
        raise AnthropicProviderError(
            "Anthropic response output exceeded "
            f"{MAX_ANTHROPIC_PROVIDER_OUTPUT_CHARS} characters"
        )
    return loads_strict_json_object(
        raw_json,
        error_factory=AnthropicProviderError,
        invalid_json_message="Anthropic response was not valid JSON",
        non_object_message="Anthropic response JSON must be an object",
    )


def _normalise_candidate_response(candidate: dict[str, Any]) -> dict[str, Any]:
    return normalise_provider_candidate_response(
        candidate,
        provider_name="Anthropic",
        error_factory=AnthropicProviderError,
    )


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
