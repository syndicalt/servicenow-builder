from __future__ import annotations

import json
from typing import Any

import pytest

from jedi_devproject.anthropic_provider import (
    AnthropicHttpResponse,
    AnthropicMessagesProvider,
    AnthropicProviderConfigError,
    AnthropicProviderError,
    AnthropicProviderRefusal,
    AnthropicProviderSettings,
    anthropic_provider_settings_from_env,
)
from jedi_devproject.openai_provider import OpenAIProviderSettings, OpenAIResponsesProvider
from jedi_devproject.servicenow import HttpRequest, HttpResponse


class SequenceTransport:
    def __init__(self, responses: list[HttpResponse | AnthropicHttpResponse]) -> None:
        self.responses = list(responses)
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse | AnthropicHttpResponse:
        self.requests.append(request)
        return self.responses.pop(0)


class HttpResponseTransport:
    """Transport satisfying the narrower OpenAI ``HttpTransport`` protocol."""

    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        return self.response


class RecordingSleep:
    def __init__(self) -> None:
        self.delays: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


def _settings() -> AnthropicProviderSettings:
    return AnthropicProviderSettings(api_key="anthropic-key")


def _payload() -> dict[str, object]:
    return {
        "task": "generate_implementation_candidate",
        "story": {"number": "STRY0010013"},
        "controls": {
            "allowed_tables": ["sys_dictionary"],
            "allowed_operations": ["insert"],
        },
    }


def _candidate() -> dict[str, Any]:
    return {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [
                    {"name": "name", "value": "rm_story"},
                    {"name": "element", "value": "u_ai_review_notes"},
                ],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": ["Confirm the field exists."],
        "rollback_notes": ["Remove the field."],
    }


def _message_response(
    text: str,
    *,
    stop_reason: str = "end_turn",
    leading_blocks: list[Any] | None = None,
) -> AnthropicHttpResponse:
    return AnthropicHttpResponse(
        status_code=200,
        json_body={
            "content": [*(leading_blocks or []), {"type": "text", "text": text}],
            "stop_reason": stop_reason,
            "model": "claude-opus-4-8",
            "usage": {"input_tokens": 10, "output_tokens": 20},
        },
    )


def _provider(
    responses: list[HttpResponse | AnthropicHttpResponse],
    *,
    sleep: RecordingSleep | None = None,
    max_retries: int = 2,
) -> tuple[AnthropicMessagesProvider, SequenceTransport]:
    transport = SequenceTransport(responses)
    provider = AnthropicMessagesProvider(
        settings=_settings(),
        transport=transport,
        max_retries=max_retries,
        sleep=sleep or RecordingSleep(),
    )
    return provider, transport


def test_anthropic_provider_posts_structured_output_request() -> None:
    provider, transport = _provider([_message_response(json.dumps(_candidate()))])

    result = provider.generate(_payload())

    assert result == {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": {"name": "rm_story", "element": "u_ai_review_notes"},
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": ["Confirm the field exists."],
        "rollback_notes": ["Remove the field."],
    }
    request = transport.requests[0]
    assert request.method == "POST"
    assert request.url == "https://api.anthropic.com/v1/messages"
    assert request.headers["x-api-key"] == "anthropic-key"
    assert request.headers["anthropic-version"] == "2023-06-01"
    assert request.headers["content-type"] == "application/json"
    assert request.body["model"] == "claude-opus-4-8"
    assert request.body["max_tokens"] == 16000
    assert request.body["messages"] == [
        {"role": "user", "content": json.dumps(_payload(), sort_keys=True)}
    ]
    assert "output_format" not in request.body
    for forbidden in ("temperature", "top_p", "top_k", "thinking"):
        assert forbidden not in request.body
    system_prompt = request.body["system"]
    assert "JSON" in system_prompt
    assert "Business Rule" in system_prompt
    assert "current.<field>" in system_prompt
    assert "fields_written" in system_prompt
    assert "at least one concrete ServiceNow change" in system_prompt
    assert "anthropic-key" not in repr(request.body)


def test_anthropic_provider_sends_same_instructions_and_payload_as_openai() -> None:
    anthropic_provider, anthropic_transport = _provider(
        [_message_response(json.dumps(_candidate()))]
    )
    openai_transport = HttpResponseTransport(
        HttpResponse(status_code=200, json_body={"output_text": json.dumps(_candidate())})
    )
    openai_provider = OpenAIResponsesProvider(
        settings=OpenAIProviderSettings(api_key="openai-key", model="gpt-4o-2024-08-06"),
        transport=openai_transport,
    )

    anthropic_result = anthropic_provider.generate(_payload())
    openai_result = openai_provider.generate(_payload())

    assert anthropic_result == openai_result
    anthropic_body = anthropic_transport.requests[0].body
    openai_body = openai_transport.requests[0].body
    assert anthropic_body["system"] == openai_body["input"][0]["content"]
    assert anthropic_body["messages"][0]["content"] == openai_body["input"][1]["content"]


def test_anthropic_provider_schema_strips_unsupported_constraints() -> None:
    provider, transport = _provider([_message_response(json.dumps(_candidate()))])

    provider.generate(_payload())

    output_format = transport.requests[0].body["output_config"]["format"]
    assert output_format["type"] == "json_schema"
    schema = output_format["schema"]
    assert schema["additionalProperties"] is False
    change_schema = schema["properties"]["changes"]["items"]
    assert change_schema["additionalProperties"] is False
    assert change_schema["properties"]["fields"]["items"]["additionalProperties"] is False
    rendered = json.dumps(schema)
    for constraint in ("minItems", "maxItems", "minimum", "maximum", "minLength", "maxLength"):
        assert f'"{constraint}"' not in rendered


def test_anthropic_provider_uses_configured_model_base_url_and_max_tokens() -> None:
    transport = SequenceTransport([_message_response(json.dumps(_candidate()))])
    provider = AnthropicMessagesProvider(
        settings=AnthropicProviderSettings(
            api_key="anthropic-key",
            model="claude-sonnet-4-6",
            base_url="https://anthropic.boundary.example.gov/",
            max_tokens=4096,
        ),
        transport=transport,
        sleep=RecordingSleep(),
    )

    provider.generate(_payload())

    request = transport.requests[0]
    assert request.url == "https://anthropic.boundary.example.gov/v1/messages"
    assert request.body["model"] == "claude-sonnet-4-6"
    assert request.body["max_tokens"] == 4096


def test_anthropic_provider_request_body_is_deterministic() -> None:
    provider, transport = _provider(
        [
            _message_response(json.dumps(_candidate())),
            _message_response(json.dumps(_candidate())),
        ],
        max_retries=0,
    )

    provider.generate(_payload())
    provider.generate(_payload())

    first, second = transport.requests
    assert json.dumps(first.body, sort_keys=True) == json.dumps(second.body, sort_keys=True)
    assert list(first.body) == list(second.body)


def test_anthropic_provider_skips_non_text_leading_blocks() -> None:
    provider, _ = _provider(
        [
            _message_response(
                json.dumps(_candidate()),
                leading_blocks=[
                    "not-a-block",
                    {"type": "thinking", "thinking": ""},
                    {"type": "text"},
                ],
            )
        ]
    )

    result = provider.generate(_payload())

    assert result["test_plan"] == ["Confirm the field exists."]


def test_anthropic_provider_accepts_plain_http_response() -> None:
    provider, _ = _provider(
        [
            HttpResponse(
                status_code=200,
                json_body={
                    "content": [{"type": "text", "text": json.dumps(_candidate())}],
                    "stop_reason": "end_turn",
                },
            )
        ]
    )

    result = provider.generate(_payload())

    assert result["rollback_notes"] == ["Remove the field."]


def test_anthropic_provider_routes_refusal_to_manual_review() -> None:
    provider, _ = _provider(
        [
            AnthropicHttpResponse(
                status_code=200,
                json_body={"content": [], "stop_reason": "refusal"},
            )
        ]
    )

    with pytest.raises(AnthropicProviderRefusal, match="manual review"):
        provider.generate(_payload())


def test_anthropic_provider_refusal_is_a_provider_error() -> None:
    assert issubclass(AnthropicProviderRefusal, AnthropicProviderError)


def test_anthropic_provider_fails_closed_for_max_tokens_stop_reason() -> None:
    provider, _ = _provider([_message_response(json.dumps(_candidate()), stop_reason="max_tokens")])

    with pytest.raises(AnthropicProviderError, match="max_tokens"):
        provider.generate(_payload())


def test_anthropic_provider_fails_closed_for_unexpected_stop_reason() -> None:
    provider, _ = _provider([_message_response(json.dumps(_candidate()), stop_reason="tool_use")])

    with pytest.raises(AnthropicProviderError, match="unexpected stop_reason"):
        provider.generate(_payload())


def test_anthropic_provider_fails_closed_when_content_is_not_a_list() -> None:
    provider, _ = _provider(
        [
            AnthropicHttpResponse(
                status_code=200,
                json_body={"content": "oops", "stop_reason": "end_turn"},
            )
        ]
    )

    with pytest.raises(AnthropicProviderError, match="text content block"):
        provider.generate(_payload())


def test_anthropic_provider_fails_closed_when_no_text_block_is_present() -> None:
    provider, _ = _provider(
        [
            AnthropicHttpResponse(
                status_code=200,
                json_body={
                    "content": [{"type": "thinking", "thinking": ""}],
                    "stop_reason": "end_turn",
                },
            )
        ]
    )

    with pytest.raises(AnthropicProviderError, match="text content block"):
        provider.generate(_payload())


def test_anthropic_provider_fails_closed_for_invalid_json() -> None:
    provider, _ = _provider([_message_response("not json")])

    with pytest.raises(AnthropicProviderError, match="valid JSON"):
        provider.generate(_payload())


def test_anthropic_provider_fails_closed_for_non_object_json() -> None:
    provider, _ = _provider([_message_response(json.dumps(["not", "an", "object"]))])

    with pytest.raises(AnthropicProviderError, match="must be an object"):
        provider.generate(_payload())


def test_anthropic_provider_rejects_arbitrary_field_object() -> None:
    candidate = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": {"name": "rm_story"},
            }
        ],
        "test_plan": ["Confirm the field exists."],
        "rollback_notes": ["Remove the field."],
    }
    provider, _ = _provider([_message_response(json.dumps(candidate))])

    with pytest.raises(AnthropicProviderError, match="name/value pairs"):
        provider.generate(_payload())


def test_anthropic_provider_rejects_non_list_changes() -> None:
    candidate: dict[str, Any] = {"changes": {}, "test_plan": [], "rollback_notes": []}
    provider, _ = _provider([_message_response(json.dumps(candidate))])

    with pytest.raises(AnthropicProviderError, match="changes must be a list"):
        provider.generate(_payload())


def test_anthropic_provider_rejects_non_object_change() -> None:
    candidate: dict[str, Any] = {"changes": ["nope"], "test_plan": [], "rollback_notes": []}
    provider, _ = _provider([_message_response(json.dumps(candidate))])

    with pytest.raises(AnthropicProviderError, match="change must be an object"):
        provider.generate(_payload())


def test_anthropic_provider_rejects_non_object_field_entry() -> None:
    candidate: dict[str, Any] = {
        "changes": [{"table": "sys_dictionary", "operation": "insert", "fields": ["nope"]}],
        "test_plan": [],
        "rollback_notes": [],
    }
    provider, _ = _provider([_message_response(json.dumps(candidate))])

    with pytest.raises(AnthropicProviderError, match="field entry must be an object"):
        provider.generate(_payload())


def test_anthropic_provider_rejects_field_entries_without_names() -> None:
    candidate = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [{"value": "rm_story"}],
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }
    provider, _ = _provider([_message_response(json.dumps(candidate))])

    with pytest.raises(AnthropicProviderError, match="non-empty name"):
        provider.generate(_payload())


def test_anthropic_provider_retries_rate_limit_honoring_retry_after() -> None:
    sleep = RecordingSleep()
    provider, transport = _provider(
        [
            AnthropicHttpResponse(
                status_code=429,
                json_body={
                    "type": "error",
                    "error": {"type": "rate_limit_error", "message": "slow down"},
                },
                headers={"retry-after": "7"},
            ),
            _message_response(json.dumps(_candidate())),
        ],
        sleep=sleep,
    )

    result = provider.generate(_payload())

    assert result["test_plan"] == ["Confirm the field exists."]
    assert len(transport.requests) == 2
    assert sleep.delays == [7.0]


def test_anthropic_provider_backs_off_exponentially_without_retry_after() -> None:
    sleep = RecordingSleep()
    overloaded = AnthropicHttpResponse(
        status_code=529,
        json_body={"type": "error", "error": {"type": "overloaded_error", "message": "busy"}},
    )
    provider, transport = _provider(
        [overloaded, overloaded.model_copy(deep=True), _message_response(json.dumps(_candidate()))],
        sleep=sleep,
    )

    provider.generate(_payload())

    assert len(transport.requests) == 3
    assert sleep.delays == [1.0, 2.0]


def test_anthropic_provider_surfaces_error_after_exhausting_retries() -> None:
    sleep = RecordingSleep()
    failure = AnthropicHttpResponse(
        status_code=500,
        json_body={"type": "error", "error": {"type": "api_error", "message": "boom"}},
        headers={"request-id": "req_123", "retry-after": "not-a-number"},
    )
    provider, transport = _provider(
        [failure, failure.model_copy(deep=True)],
        sleep=sleep,
        max_retries=1,
    )

    with pytest.raises(AnthropicProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert "status 500" in error
    assert "boom" in error
    assert "type=api_error" in error
    assert "request_id=req_123" in error
    assert len(transport.requests) == 2
    assert sleep.delays == [1.0]


def test_anthropic_provider_does_not_retry_bad_request() -> None:
    sleep = RecordingSleep()
    provider, transport = _provider(
        [
            AnthropicHttpResponse(
                status_code=400,
                json_body={
                    "type": "error",
                    "error": {"type": "invalid_request_error", "message": "bad params"},
                },
                headers={"Request-Id": "req_400"},
            )
        ],
        sleep=sleep,
    )

    with pytest.raises(AnthropicProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert "status 400" in error
    assert "bad params" in error
    assert "type=invalid_request_error" in error
    assert "request_id=req_400" in error
    assert len(transport.requests) == 1
    assert sleep.delays == []


def test_anthropic_provider_reports_status_only_when_error_envelope_is_absent() -> None:
    provider, transport = _provider([HttpResponse(status_code=400, json_body={})])

    with pytest.raises(AnthropicProviderError) as exc:
        provider.generate(_payload())

    assert str(exc.value) == "Anthropic Messages API failed with status 400"
    assert len(transport.requests) == 1


def test_anthropic_provider_reports_status_only_for_empty_error_object() -> None:
    provider, _ = _provider(
        [AnthropicHttpResponse(status_code=400, json_body={"type": "error", "error": {}})]
    )

    with pytest.raises(AnthropicProviderError) as exc:
        provider.generate(_payload())

    assert str(exc.value) == "Anthropic Messages API failed with status 400"


def test_anthropic_provider_reports_error_type_without_message() -> None:
    provider, _ = _provider(
        [
            AnthropicHttpResponse(
                status_code=403,
                json_body={"type": "error", "error": {"type": "permission_error"}},
            )
        ]
    )

    with pytest.raises(
        AnthropicProviderError,
        match=r"status 403: type=permission_error",
    ):
        provider.generate(_payload())


def test_anthropic_provider_redacts_api_key_from_error_paths() -> None:
    provider, _ = _provider(
        [
            AnthropicHttpResponse(
                status_code=401,
                json_body={
                    "type": "error",
                    "error": {
                        "type": "authentication_error",
                        "message": "invalid x-api-key: anthropic-key",
                    },
                },
            )
        ]
    )

    with pytest.raises(AnthropicProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert "anthropic-key" not in error
    assert "[REDACTED]" in error
    assert "status 401" in error


def test_anthropic_provider_rejects_negative_max_retries() -> None:
    with pytest.raises(AnthropicProviderConfigError, match="max_retries"):
        AnthropicMessagesProvider(
            settings=_settings(),
            transport=SequenceTransport([]),
            max_retries=-1,
        )


def test_settings_from_env_reads_all_values() -> None:
    settings = anthropic_provider_settings_from_env(
        {
            "ANTHROPIC_API_KEY": "env-key",
            "ANTHROPIC_MODEL": "claude-sonnet-4-6",
            "ANTHROPIC_BASE_URL": "https://anthropic.boundary.example.gov",
            "ANTHROPIC_MAX_TOKENS": "8192",
        }
    )

    assert settings == AnthropicProviderSettings(
        api_key="env-key",
        model="claude-sonnet-4-6",
        base_url="https://anthropic.boundary.example.gov",
        max_tokens=8192,
    )


def test_settings_from_env_applies_defaults() -> None:
    settings = anthropic_provider_settings_from_env({"ANTHROPIC_API_KEY": "env-key"})

    assert settings.model == "claude-opus-4-8"
    assert settings.base_url == "https://api.anthropic.com"
    assert settings.max_tokens == 16000


def test_settings_from_env_requires_api_key() -> None:
    with pytest.raises(AnthropicProviderConfigError, match="ANTHROPIC_API_KEY"):
        anthropic_provider_settings_from_env({"ANTHROPIC_API_KEY": "   "})


def test_settings_from_env_rejects_non_numeric_max_tokens() -> None:
    with pytest.raises(AnthropicProviderConfigError, match="ANTHROPIC_MAX_TOKENS"):
        anthropic_provider_settings_from_env(
            {"ANTHROPIC_API_KEY": "env-key", "ANTHROPIC_MAX_TOKENS": "lots"}
        )


def test_settings_from_env_rejects_non_positive_max_tokens() -> None:
    with pytest.raises(AnthropicProviderConfigError, match="ANTHROPIC_MAX_TOKENS"):
        anthropic_provider_settings_from_env(
            {"ANTHROPIC_API_KEY": "env-key", "ANTHROPIC_MAX_TOKENS": "0"}
        )
