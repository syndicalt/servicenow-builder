from __future__ import annotations

from itertools import islice
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from jedi_devproject.diagnostic_redaction import _redact_diagnostic_text
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
from jedi_devproject.servicenow import HttpRequest, HttpResponse, HttpTransport


class OpenAIProviderError(RuntimeError):
    """Raised when the OpenAI provider cannot return validated JSON."""


MAX_OPENAI_PROVIDER_DIAGNOSTIC_CHARS = 4096
MAX_OPENAI_PROVIDER_OUTPUT_CHARS = 1_000_000
MAX_OPENAI_PROVIDER_RESPONSE_COLLECTION_ITEMS = 100
OPENAI_PROVIDER_TRUNCATION_MARKER = "...[truncated]"


class OpenAIProviderSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    api_key: str
    model: str
    base_url: str = "https://api.openai.com/v1"

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


class OpenAIResponsesProvider:
    def __init__(
        self,
        *,
        settings: OpenAIProviderSettings,
        transport: HttpTransport,
    ) -> None:
        self._settings = settings
        self._transport = transport

    def generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._transport.send(
            HttpRequest(
                method="POST",
                url=f"{self._settings.base_url.rstrip('/')}/responses",
                headers={
                    "Authorization": f"Bearer {self._settings.api_key}",
                    "Content-Type": "application/json",
                },
                body={
                    "model": self._settings.model,
                    "input": [
                        {
                            "role": "system",
                            "content": IMPLEMENTATION_SYSTEM_PROMPT,
                        },
                        {
                            "role": "user",
                            "content": implementation_payload_json(
                                payload,
                                error_factory=OpenAIProviderError,
                            ),
                        },
                    ],
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "name": "implementation_candidate",
                            "strict": True,
                            "schema": implementation_candidate_schema(),
                        }
                    },
                },
            )
        )
        status_code = _response_status_code(response)
        if status_code >= 400:
            raise OpenAIProviderError(
                _api_error_message(
                    status_code,
                    response.json_body,
                    api_key=self._settings.api_key,
                )
            )
        return _parse_response_json(response.json_body)


def _parse_response_json(response: dict[str, Any]) -> dict[str, Any]:
    if type(response) is not dict:
        raise OpenAIProviderError("OpenAI response did not include output JSON")
    output_text = response.get("output_text")
    if type(output_text) is str:
        return _normalise_candidate_response(_loads_json_object(output_text))

    output = response.get("output", [])
    if type(output) is list:
        for item in islice(output, MAX_OPENAI_PROVIDER_RESPONSE_COLLECTION_ITEMS):
            if type(item) is not dict:
                continue
            content = item.get("content", [])
            if type(content) is not list:
                continue
            for content_item in islice(
                content,
                MAX_OPENAI_PROVIDER_RESPONSE_COLLECTION_ITEMS,
            ):
                if type(content_item) is not dict:
                    continue
                content_type = content_item.get("type")
                content_text = content_item.get("text")
                if (
                    type(content_type) is str
                    and content_type == "output_text"
                    and type(content_text) is str
                ):
                    return _normalise_candidate_response(
                        _loads_json_object(content_text)
                    )

    raise OpenAIProviderError("OpenAI response did not include output JSON")


def _api_error_message(
    status_code: int,
    response_body: dict[str, Any],
    *,
    api_key: str = "",
) -> str:
    details = _api_error_details(response_body, api_key=api_key)
    if details:
        return _bound_provider_diagnostic(
            _redact_configured_api_key(
                f"OpenAI Responses API failed with status {status_code}: {details}",
                api_key=api_key,
            )
        )
    return f"OpenAI Responses API failed with status {status_code}"


def _response_status_code(response: Any) -> int:
    if type(response) is not HttpResponse:
        raise OpenAIProviderError("OpenAI transport response must be an exact HttpResponse")
    status_code = response.status_code
    if type(status_code) is not int:
        raise OpenAIProviderError("OpenAI response status code must be an exact integer")
    if status_code < 100 or status_code > 599:
        raise OpenAIProviderError("OpenAI response status code must be in the HTTP range")
    return status_code


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
        parts.append(
            f"type={_safe_structured_error_metadata(error_type, api_key=api_key)}"
        )

    code = error.get("code")
    if type(code) is str and code:
        parts.append(f"code={_safe_structured_error_metadata(code, api_key=api_key)}")

    return "; ".join(parts)


def _safe_structured_error_metadata(value: str, *, api_key: str) -> str:
    redacted = _redact_provider_message(value, api_key=api_key)
    return " ".join(redacted.split())


def _redact_provider_message(value: str, *, api_key: str) -> str:
    redacted = _redact_diagnostic_text(value) or ""
    return _redact_configured_api_key(redacted, api_key=api_key)


def _redact_configured_api_key(value: str, *, api_key: str) -> str:
    if api_key:
        return value.replace(api_key, "***REDACTED***")
    return value


def _bound_provider_diagnostic(value: str) -> str:
    if len(value) <= MAX_OPENAI_PROVIDER_DIAGNOSTIC_CHARS:
        return value
    return (
        f"{value[:MAX_OPENAI_PROVIDER_DIAGNOSTIC_CHARS]}"
        f"{OPENAI_PROVIDER_TRUNCATION_MARKER}"
    )


def _loads_json_object(raw_json: str) -> dict[str, Any]:
    if len(raw_json) > MAX_OPENAI_PROVIDER_OUTPUT_CHARS:
        raise OpenAIProviderError(
            "OpenAI response output exceeded "
            f"{MAX_OPENAI_PROVIDER_OUTPUT_CHARS} characters"
        )
    return loads_strict_json_object(
        raw_json,
        error_factory=OpenAIProviderError,
        invalid_json_message="OpenAI response was not valid JSON",
        non_object_message="OpenAI response JSON must be an object",
    )


def _normalise_candidate_response(candidate: dict[str, Any]) -> dict[str, Any]:
    return normalise_provider_candidate_response(
        candidate,
        provider_name="OpenAI",
        error_factory=OpenAIProviderError,
    )
