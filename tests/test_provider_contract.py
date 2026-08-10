from __future__ import annotations

import json
from typing import Any

import pytest

from jedi_devproject.anthropic_provider import (
    AnthropicHttpResponse,
    AnthropicMessagesProvider,
    AnthropicProviderSettings,
    _without_unsupported_constraints,
)
from jedi_devproject.openai_provider import OpenAIProviderSettings, OpenAIResponsesProvider
from jedi_devproject.provider_contract import (
    IMPLEMENTATION_SYSTEM_PROMPT,
    implementation_candidate_schema,
    implementation_payload_json,
    loads_strict_json_object,
)
from jedi_devproject.servicenow import HttpRequest, HttpResponse


class SequenceTransport:
    def __init__(self, responses: list[HttpResponse | AnthropicHttpResponse]) -> None:
        self.responses = list(responses)
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse | AnthropicHttpResponse:
        self.requests.append(request)
        return self.responses.pop(0)


class RecordingTransport:
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


def _anthropic_response(text: str) -> AnthropicHttpResponse:
    return AnthropicHttpResponse(
        status_code=200,
        json_body={
            "content": [{"type": "text", "text": text}],
            "stop_reason": "end_turn",
            "model": "claude-3-opus-20240229",
            "usage": {"input_tokens": 10, "output_tokens": 20},
        },
    )


def _anthropic_provider() -> tuple[AnthropicMessagesProvider, SequenceTransport]:
    transport = SequenceTransport([_anthropic_response(json.dumps(_candidate()))])
    provider = AnthropicMessagesProvider(
        settings=AnthropicProviderSettings(api_key="anthropic-key"),
        transport=transport,
        sleep=RecordingSleep(),
    )
    return provider, transport


def _openai_provider() -> tuple[OpenAIResponsesProvider, RecordingTransport]:
    transport = RecordingTransport(
        HttpResponse(status_code=200, json_body={"output_text": json.dumps(_candidate())})
    )
    provider = OpenAIResponsesProvider(
        settings=OpenAIProviderSettings(api_key="openai-key", model="gpt-4o-2024-08-06"),
        transport=transport,
    )
    return provider, transport


def test_both_adapters_send_the_shared_system_prompt() -> None:
    anthropic_provider, anthropic_transport = _anthropic_provider()
    openai_provider, openai_transport = _openai_provider()

    anthropic_provider.generate(_payload())
    openai_provider.generate(_payload())

    anthropic_prompt = anthropic_transport.requests[0].body["system"]
    openai_prompt = openai_transport.requests[0].body["input"][0]["content"]
    assert anthropic_prompt == IMPLEMENTATION_SYSTEM_PROMPT
    assert openai_prompt == IMPLEMENTATION_SYSTEM_PROMPT
    assert anthropic_prompt == openai_prompt


def test_implementation_system_prompt_has_sentence_boundary_before_catalog_guidance() -> None:
    assert "script.For standard Catalog" not in IMPLEMENTATION_SYSTEM_PROMPT
    assert "script. For standard Catalog Item builds" in IMPLEMENTATION_SYSTEM_PROMPT


def test_implementation_payload_rejects_mapping_subclass_without_leak() -> None:
    class HostilePayload(dict[str, Any]):
        def items(self) -> Any:  # pragma: no cover - must not run
            raise AssertionError("client_secret=prompt-mapping-secret")

    with pytest.raises(ValueError) as exc:
        implementation_payload_json(
            HostilePayload({"story": {"number": "STRY0010013"}}),
            error_factory=ValueError,
        )

    error = str(exc.value)
    assert error == "Model provider prompt payload contains unsupported JSON value types"
    assert "prompt-mapping-secret" not in error
    assert "client_secret" not in error
    assert exc.value.__cause__ is None


def test_implementation_payload_rejects_key_subclass_without_normalization() -> None:
    class SneakyKey(str):
        pass

    with pytest.raises(ValueError) as exc:
        implementation_payload_json(
            {"story": {SneakyKey("number"): "STRY0010013"}},
            error_factory=ValueError,
        )

    assert str(exc.value) == (
        "Model provider prompt payload contains unsupported JSON value types"
    )
    assert exc.value.__cause__ is None


def test_implementation_payload_rejects_list_subclass_without_leak() -> None:
    class HostileList(list[str]):
        def __iter__(self) -> Any:  # pragma: no cover - must not run
            raise AssertionError("client_secret=prompt-list-secret")

    with pytest.raises(ValueError) as exc:
        implementation_payload_json(
            {"controls": {"allowed_tables": HostileList(["sys_dictionary"])}},
            error_factory=ValueError,
        )

    error = str(exc.value)
    assert error == "Model provider prompt payload contains unsupported JSON value types"
    assert "prompt-list-secret" not in error
    assert "client_secret" not in error
    assert exc.value.__cause__ is None


def test_implementation_payload_rejects_string_subclass_without_normalization() -> None:
    class SneakyString(str):
        pass

    with pytest.raises(ValueError) as exc:
        implementation_payload_json(
            {"story": {"number": SneakyString("STRY0010013")}},
            error_factory=ValueError,
        )

    assert str(exc.value) == (
        "Model provider prompt payload contains unsupported JSON value types"
    )
    assert exc.value.__cause__ is None


def test_implementation_payload_rejects_non_finite_number_without_cause() -> None:
    with pytest.raises(ValueError) as exc:
        implementation_payload_json(
            {"story": {"number": "STRY0010013"}, "score": float("nan")},
            error_factory=ValueError,
        )

    assert str(exc.value) == "Model provider prompt payload contains non-finite numeric values"
    assert exc.value.__cause__ is None


def test_loads_strict_json_object_invalid_json_does_not_retain_parser_cause() -> None:
    with pytest.raises(ValueError) as exc:
        loads_strict_json_object(
            '{"client_secret":"provider-response-secret"',
            error_factory=ValueError,
            invalid_json_message="provider response invalid JSON",
            non_object_message="provider response must be object",
        )

    assert str(exc.value) == "provider response invalid JSON"
    assert exc.value.__cause__ is None


def test_loads_strict_json_object_non_finite_json_does_not_retain_parser_cause() -> None:
    with pytest.raises(ValueError) as exc:
        loads_strict_json_object(
            '{"score": NaN, "client_secret": "provider-response-secret"}',
            error_factory=ValueError,
            invalid_json_message="provider response invalid JSON",
            non_object_message="provider response must be object",
        )

    assert str(exc.value) == "provider response invalid JSON"
    assert exc.value.__cause__ is None


def test_openai_request_schema_is_the_shared_schema_unmodified() -> None:
    provider, transport = _openai_provider()

    provider.generate(_payload())

    request_schema = transport.requests[0].body["text"]["format"]["schema"]
    assert request_schema == implementation_candidate_schema()


def test_anthropic_request_schema_is_the_shared_schema_without_unsupported_constraints() -> None:
    provider, transport = _anthropic_provider()

    provider.generate(_payload())

    request_schema = transport.requests[0].body["output_config"]["format"]["schema"]
    assert request_schema == _without_unsupported_constraints(implementation_candidate_schema())


def test_implementation_candidate_schema_returns_a_fresh_dict_per_call() -> None:
    first = implementation_candidate_schema()
    first["properties"]["changes"]["minItems"] = 99

    second = implementation_candidate_schema()

    assert first is not second
    assert second["properties"]["changes"]["minItems"] == 1
