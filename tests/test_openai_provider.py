from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import pytest
from pydantic import ValidationError

from jedi_devproject.openai_provider import (
    MAX_OPENAI_PROVIDER_OUTPUT_CHARS,
    OpenAIProviderError,
    OpenAIProviderSettings,
    OpenAIResponsesProvider,
)
from jedi_devproject.servicenow import HttpRequest, HttpResponse


class RecordingTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        return self.response


class HostileResponseTransport:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> Any:
        self.requests.append(request)
        return self.response


def _settings() -> OpenAIProviderSettings:
    return OpenAIProviderSettings(
        api_key="openai-key",
        model="gpt-4o-2024-08-06",
    )


def _payload() -> dict[str, object]:
    return {
        "task": "generate_implementation_candidate",
        "story": {"number": "STRY0010013"},
        "controls": {
            "allowed_tables": ["sys_dictionary"],
            "allowed_operations": ["insert"],
        },
    }


def _candidate() -> dict[str, object]:
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


def test_openai_provider_settings_reject_control_character_base_url() -> None:
    with pytest.raises(ValidationError, match="base_url"):
        OpenAIProviderSettings(
            api_key="openai-key",
            model="gpt-4o-2024-08-06",
            base_url="https://api.openai.example.gov/v1\nX-Injected: yes",
        )


@pytest.mark.parametrize(
    "base_url",
    [
        "https://api.openai.example.gov/v1/%0aX-Injected",
        "https://api.openai.example.gov/v1/%09responses",
        "https://api.openai.example.gov/v1/%250aX-Injected",
        "https://api.openai.example.gov/v1/%2509responses",
    ],
)
def test_openai_provider_settings_reject_encoded_control_character_base_url(
    base_url: str,
) -> None:
    with pytest.raises(ValidationError, match="base_url"):
        OpenAIProviderSettings(
            api_key="openai-key",
            model="gpt-4o-2024-08-06",
            base_url=base_url,
        )


def test_openai_provider_settings_reject_empty_base_url() -> None:
    with pytest.raises(ValidationError, match="base_url"):
        OpenAIProviderSettings(
            api_key="openai-key",
            model="gpt-4o-2024-08-06",
            base_url="",
        )


def test_openai_provider_settings_reject_oversized_base_url() -> None:
    with pytest.raises(ValidationError, match="base_url"):
        OpenAIProviderSettings(
            api_key="openai-key",
            model="gpt-4o-2024-08-06",
            base_url=f"https://api.openai.example.gov/v1/{'a' * 2048}",
        )


@pytest.mark.parametrize(
    "base_url",
    [
        "api.openai.example.gov/v1",
        "http://api.openai.example.gov/v1",
        "https://openai-user:openai-secret@api.openai.example.gov/v1",
        "https://api.openai.example.gov/v1?token=secret",
        "https://api.openai.example.gov/v1#responses",
    ],
)
def test_openai_provider_settings_reject_unsafe_base_url_shape(
    base_url: str,
) -> None:
    with pytest.raises(ValidationError, match="base_url"):
        OpenAIProviderSettings(
            api_key="openai-key",
            model="gpt-4o-2024-08-06",
            base_url=base_url,
        )


@pytest.mark.parametrize(
    ("base_url", "sensitive_parts"),
    [
        (
            "https://169.254.169.254/latest/meta-data",
            ("169.254.169.254", "latest/meta-data"),
        ),
        (
            "https://openai-user:openai-secret@api.openai.example.gov/v1",
            ("openai-user", "openai-secret"),
        ),
    ],
)
def test_openai_provider_settings_validation_errors_do_not_echo_base_url(
    base_url: str,
    sensitive_parts: tuple[str, ...],
) -> None:
    with pytest.raises(ValidationError, match="base_url") as exc:
        OpenAIProviderSettings(
            api_key="openai-key",
            model="gpt-4o-2024-08-06",
            base_url=base_url,
        )

    message = str(exc.value)
    assert "input_value" not in message
    for sensitive_part in sensitive_parts:
        assert sensitive_part not in message


def test_openai_provider_settings_reject_control_character_api_key() -> None:
    with pytest.raises(ValidationError, match="api_key"):
        OpenAIProviderSettings(
            api_key="openai-key\nX-Injected: yes",
            model="gpt-4o-2024-08-06",
        )


def test_openai_provider_settings_reject_empty_api_key() -> None:
    with pytest.raises(ValidationError, match="api_key"):
        OpenAIProviderSettings(api_key="", model="gpt-4o-2024-08-06")


def test_openai_provider_settings_reject_oversized_api_key() -> None:
    with pytest.raises(ValidationError, match="api_key"):
        OpenAIProviderSettings(api_key="k" * 4097, model="gpt-4o-2024-08-06")


def test_openai_provider_settings_reject_control_character_model() -> None:
    with pytest.raises(ValidationError, match="model"):
        OpenAIProviderSettings(
            api_key="openai-key",
            model="gpt-4o-2024-08-06\nX-Injected: yes",
        )


def test_openai_provider_settings_reject_empty_model() -> None:
    with pytest.raises(ValidationError, match="model"):
        OpenAIProviderSettings(api_key="openai-key", model="")


def test_openai_provider_settings_reject_oversized_model() -> None:
    with pytest.raises(ValidationError, match="model"):
        OpenAIProviderSettings(api_key="openai-key", model="m" * 257)


def test_openai_responses_provider_posts_structured_output_request() -> None:
    expected = {
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
    transport = RecordingTransport(
        HttpResponse(
            status_code=200,
            json_body={"output_text": json.dumps(expected)},
        )
    )
    provider = OpenAIResponsesProvider(settings=_settings(), transport=transport)

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
    assert request.url == "https://api.openai.com/v1/responses"
    assert request.headers["Authorization"] == "Bearer openai-key"
    assert request.body["model"] == "gpt-4o-2024-08-06"
    assert request.body["text"]["format"]["type"] == "json_schema"
    assert request.body["text"]["format"]["strict"] is True
    schema = request.body["text"]["format"]["schema"]
    assert schema["additionalProperties"] is False
    assert schema["properties"]["changes"]["minItems"] == 1
    assert schema["properties"]["changes"]["maxItems"] == 100
    change_schema = schema["properties"]["changes"]["items"]
    assert change_schema["additionalProperties"] is False
    assert change_schema["required"] == [
        "table",
        "operation",
        "fields",
        "sys_id",
        "rationale",
    ]
    assert change_schema["properties"]["table"]["maxLength"] == 200
    assert change_schema["properties"]["table"]["pattern"] == r"^[A-Za-z_][A-Za-z0-9_]*$"
    assert change_schema["properties"]["rationale"]["maxLength"] == 2000
    assert change_schema["properties"]["rationale"]["pattern"] == (
        r"^[^\u0000-\u001F\u007F-\u009F\ud800-\udfff]*"
        r"[^\s\u0000-\u001F\u007F-\u009F\ud800-\udfff]"
        r"[^\u0000-\u001F\u007F-\u009F\ud800-\udfff]*$"
    )
    fields_schema = change_schema["properties"]["fields"]
    assert fields_schema["type"] == "array"
    assert fields_schema["maxItems"] == 100
    assert fields_schema["items"]["additionalProperties"] is False
    assert fields_schema["items"]["properties"]["name"]["maxLength"] == 200
    assert fields_schema["items"]["properties"]["name"]["pattern"] == (
        r"^[A-Za-z_][A-Za-z0-9_]*$"
    )
    value_schema = fields_schema["items"]["properties"]["value"]
    assert value_schema["maxLength"] == 100000
    assert value_schema["minimum"] == -9007199254740991
    assert value_schema["maximum"] == 9007199254740991
    assert change_schema["properties"]["sys_id"] == {"type": "null"}
    assert schema["properties"]["test_plan"]["maxItems"] == 100
    assert schema["properties"]["test_plan"]["items"]["minLength"] == 1
    assert schema["properties"]["test_plan"]["items"]["maxLength"] == 2000
    assert schema["properties"]["test_plan"]["items"]["pattern"] == (
        r"^[^\u0000-\u001F\u007F-\u009F\ud800-\udfff]*"
        r"[^\s\u0000-\u001F\u007F-\u009F\ud800-\udfff]"
        r"[^\u0000-\u001F\u007F-\u009F\ud800-\udfff]*$"
    )
    assert schema["properties"]["rollback_notes"]["maxItems"] == 100
    assert schema["properties"]["rollback_notes"]["items"]["minLength"] == 1
    assert schema["properties"]["rollback_notes"]["items"]["maxLength"] == 2000
    assert schema["properties"]["rollback_notes"]["items"]["pattern"] == (
        r"^[^\u0000-\u001F\u007F-\u009F\ud800-\udfff]*"
        r"[^\s\u0000-\u001F\u007F-\u009F\ud800-\udfff]"
        r"[^\u0000-\u001F\u007F-\u009F\ud800-\udfff]*$"
    )
    system_prompt = request.body["input"][0]["content"]
    assert "JSON" in system_prompt
    assert "Business Rule" in system_prompt
    assert "current.<field>" in system_prompt
    assert "fields_written" in system_prompt
    assert "JSON field metadata only" in system_prompt
    assert "Do not put fields_written" in system_prompt
    assert "at least one concrete ServiceNow change" in system_prompt
    assert "return no changes" not in system_prompt
    assert "openai-key" not in repr(request.body)


def test_openai_responses_provider_rejects_non_finite_prompt_payload_before_transport() -> None:
    transport = RecordingTransport(
        HttpResponse(status_code=200, json_body={"output_text": json.dumps({})})
    )
    provider = OpenAIResponsesProvider(settings=_settings(), transport=transport)
    payload = {
        **_payload(),
        "risk": {
            "score": float("nan"),
            "secret": "client_secret=prompt-secret",
        },
    }

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(payload)

    diagnostic = str(exc.value)
    assert diagnostic == "Model provider prompt payload contains non-finite numeric values"
    assert transport.requests == []
    assert "prompt-secret" not in diagnostic
    assert "score" not in diagnostic
    assert "NaN" not in diagnostic


def test_openai_responses_provider_parses_output_item_text() -> None:
    expected: dict[str, object] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [{"name": "element", "value": "u_ai_review_notes"}],
                "sys_id": None,
                "rationale": "Create requested field.",
            }
        ],
        "test_plan": ["Review generated artifact."],
        "rollback_notes": ["No platform changes were generated."],
    }
    normalized_expected = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": {"element": "u_ai_review_notes"},
                "sys_id": None,
                "rationale": "Create requested field.",
            }
        ],
        "test_plan": ["Review generated artifact."],
        "rollback_notes": ["No platform changes were generated."],
    }
    transport = RecordingTransport(
        HttpResponse(
            status_code=200,
            json_body={
                "output": [
                    {
                        "content": [
                            {
                                "type": "output_text",
                                "text": json.dumps(expected),
                            }
                        ]
                    }
                ]
            },
        )
    )

    result = OpenAIResponsesProvider(settings=_settings(), transport=transport).generate(_payload())

    assert result == normalized_expected


def test_openai_responses_provider_does_not_scan_unbounded_output_items() -> None:
    class WideOutputProbe(list[object]):
        def __len__(self) -> int:
            return 150

        def __iter__(self) -> Iterator[object]:
            for index in range(150):
                if index >= 100:
                    raise AssertionError("OpenAI output scan consumed too many items")
                yield {"content": [{"type": "summary_text", "text": f"summary {index}"}]}

    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(status_code=200, json_body={"output": WideOutputProbe()})
        ),
    )

    with pytest.raises(OpenAIProviderError, match="did not include output JSON"):
        provider.generate(_payload())


def test_openai_responses_provider_rejects_output_list_subclass_without_leak() -> None:
    class HostileOutputList(list[object]):
        def __iter__(self) -> Iterator[object]:
            raise AssertionError("client_secret=output-list-secret")

    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(status_code=200, json_body={"output": HostileOutputList()})
        ),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert error == "OpenAI response did not include output JSON"
    assert "HostileOutputList" not in error
    assert "output-list-secret" not in error
    assert "client_secret" not in error


def test_openai_responses_provider_does_not_scan_unbounded_content_items() -> None:
    class WideContentProbe(list[object]):
        def __len__(self) -> int:
            return 150

        def __iter__(self) -> Iterator[object]:
            for index in range(150):
                if index >= 100:
                    raise AssertionError("OpenAI content scan consumed too many items")
                yield {"type": "summary_text", "text": f"summary {index}"}

    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(
                status_code=200,
                json_body={"output": [{"content": WideContentProbe()}]},
            )
        ),
    )

    with pytest.raises(OpenAIProviderError, match="did not include output JSON"):
        provider.generate(_payload())


def test_openai_responses_provider_rejects_content_list_subclass_without_leak() -> None:
    class HostileContentList(list[object]):
        def __iter__(self) -> Iterator[object]:
            raise AssertionError("client_secret=content-list-secret")

    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(
                status_code=200,
                json_body={"output": [{"content": HostileContentList()}]},
            )
        ),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert error == "OpenAI response did not include output JSON"
    assert "HostileContentList" not in error
    assert "content-list-secret" not in error
    assert "client_secret" not in error


def test_openai_responses_provider_rejects_output_item_dict_subclass_without_leak() -> None:
    class HostileOutputItem(dict[str, object]):
        def get(self, key: object, default: object = None) -> object:
            raise AssertionError("client_secret=output-item-secret")

    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(status_code=200, json_body={"output": [HostileOutputItem()]})
        ),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert error == "OpenAI response did not include output JSON"
    assert "HostileOutputItem" not in error
    assert "output-item-secret" not in error
    assert "client_secret" not in error


def test_openai_responses_provider_rejects_content_item_dict_subclass_without_leak() -> None:
    class HostileContentItem(dict[str, object]):
        def get(self, key: object, default: object = None) -> object:
            raise AssertionError("client_secret=content-item-secret")

    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(
                status_code=200,
                json_body={"output": [{"content": [HostileContentItem()]}]},
            )
        ),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert error == "OpenAI response did not include output JSON"
    assert "HostileContentItem" not in error
    assert "content-item-secret" not in error
    assert "client_secret" not in error


def test_openai_responses_provider_rejects_content_type_marker_object_without_leak() -> None:
    class HostileTypeMarker:
        def __eq__(self, other: object) -> bool:
            raise AssertionError("client_secret=type-marker-secret")

    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(
                status_code=200,
                json_body={
                    "output": [
                        {
                            "content": [
                                {
                                    "type": HostileTypeMarker(),
                                    "text": json.dumps(_candidate()),
                                }
                            ]
                        }
                    ]
                },
            )
        ),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert error == "OpenAI response did not include output JSON"
    assert "HostileTypeMarker" not in error
    assert "type-marker-secret" not in error
    assert "client_secret" not in error


def test_openai_responses_provider_rejects_status_code_object_without_leak() -> None:
    class HostileStatusCode:
        def __ge__(self, other: object) -> bool:
            raise AssertionError("client_secret=status-code-secret")

    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse.model_construct(
                status_code=HostileStatusCode(),
                json_body={"output_text": json.dumps(_candidate())},
            )
        ),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert error == "OpenAI response status code must be an exact integer"
    assert "HostileStatusCode" not in error
    assert "status-code-secret" not in error
    assert "client_secret" not in error


def test_openai_responses_provider_rejects_response_object_without_leak() -> None:
    class HostileResponse:
        @property
        def status_code(self) -> int:
            raise AssertionError("client_secret=response-object-secret")

    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=HostileResponseTransport(HostileResponse()),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert error == "OpenAI transport response must be an exact HttpResponse"
    assert "HostileResponse" not in error
    assert "response-object-secret" not in error
    assert "client_secret" not in error


@pytest.mark.parametrize("status_code", [99, 600])
def test_openai_responses_provider_rejects_status_code_outside_http_range(
    status_code: int,
) -> None:
    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(
                status_code=status_code,
                json_body={"output_text": json.dumps(_candidate())},
            )
        ),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    assert str(exc.value) == "OpenAI response status code must be in the HTTP range"


def test_openai_responses_provider_fails_closed_for_api_error() -> None:
    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(status_code=500, json_body={"error": {"message": "boom"}})
        ),
    )

    with pytest.raises(OpenAIProviderError, match="status 500: boom"):
        provider.generate(_payload())


def test_openai_responses_provider_rejects_error_dict_subclass_without_leak() -> None:
    class HostileErrorEnvelope(dict[str, object]):
        def get(self, key: object, default: object = None) -> object:
            raise AssertionError("client_secret=error-envelope-secret")

    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(
                status_code=500,
                json_body={"error": HostileErrorEnvelope()},
            )
        ),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert error == "OpenAI Responses API failed with status 500"
    assert "HostileErrorEnvelope" not in error
    assert "error-envelope-secret" not in error
    assert "client_secret" not in error


def test_openai_responses_provider_rejects_error_response_body_dict_subclass_without_leak() -> None:
    class HostileResponseBody(dict[str, object]):
        def get(self, key: object, default: object = None) -> object:
            raise AssertionError("client_secret=error-body-secret")

    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse.model_construct(
                status_code=500,
                json_body=HostileResponseBody(),
            )
        ),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert error == "OpenAI Responses API failed with status 500"
    assert "HostileResponseBody" not in error
    assert "error-body-secret" not in error
    assert "client_secret" not in error


def test_openai_responses_provider_reports_rate_limit_error_details() -> None:
    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(
                status_code=429,
                json_body={
                    "error": {
                        "message": "You exceeded your current quota.",
                        "type": "insufficient_quota",
                        "code": "insufficient_quota",
                    }
                },
            )
        ),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert "status 429" in error
    assert "You exceeded your current quota." in error
    assert "type=insufficient_quota" in error
    assert "code=insufficient_quota" in error
    assert "openai-key" not in error


def test_openai_responses_provider_redacts_and_bounds_error_details() -> None:
    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(
                status_code=500,
                json_body={
                    "error": {
                        "message": (
                            "upstream failure client_secret=openai-key "
                            + ("x" * 5000)
                        ),
                        "type": "server_error",
                    }
                },
            )
        ),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert "status 500" in error
    assert "openai-key" not in error
    assert "client_secret=***REDACTED***" in error
    assert error.endswith("...[truncated]")
    assert len(error) < 4300


def test_openai_responses_provider_redacts_structured_error_metadata() -> None:
    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(
                status_code=400,
                json_body={
                    "error": {
                        "message": "bad request",
                        "type": "invalid_request\napi_key=openai-key",
                        "code": "bad\tcode openai-key",
                    }
                },
            )
        ),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert "bad request" in error
    assert "openai-key" not in error
    assert "\n" not in error
    assert "\t" not in error
    assert "api_key=***REDACTED***" in error
    assert "code=bad code ***REDACTED***" in error


def test_openai_responses_provider_rejects_error_message_subclass_diagnostic() -> None:
    class SneakyMessage(str):
        pass

    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(
                status_code=500,
                json_body={
                    "error": {
                        "message": SneakyMessage("client_secret=message-secret"),
                        "type": "server_error",
                    }
                },
            )
        ),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert "status 500" in error
    assert "type=server_error" in error
    assert "message-secret" not in error
    assert "client_secret" not in error


def test_openai_responses_provider_rejects_error_type_subclass_diagnostic() -> None:
    class SneakyType(str):
        pass

    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(
                status_code=400,
                json_body={
                    "error": {
                        "message": "bad request",
                        "type": SneakyType("invalid_request_error"),
                    }
                },
            )
        ),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert "status 400" in error
    assert "bad request" in error
    assert "type=" not in error


def test_openai_responses_provider_rejects_error_code_subclass_diagnostic() -> None:
    class SneakyCode(str):
        pass

    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(
                status_code=429,
                json_body={
                    "error": {
                        "message": "rate limited",
                        "code": SneakyCode("rate_limit_exceeded"),
                    }
                },
            )
        ),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert "status 429" in error
    assert "rate limited" in error
    assert "code=" not in error


def test_openai_responses_provider_fails_closed_for_invalid_json() -> None:
    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(status_code=200, json_body={"output_text": "not json"})
        ),
    )

    with pytest.raises(OpenAIProviderError, match="valid JSON"):
        provider.generate(_payload())


def test_openai_responses_provider_rejects_response_body_dict_subclass_without_leak() -> None:
    class HostileResponseBody(dict[str, object]):
        def get(self, key: object, default: object = None) -> object:
            raise AssertionError("client_secret=response-body-secret")

    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse.model_construct(
                status_code=200,
                json_body=HostileResponseBody(),
            )
        ),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert error == "OpenAI response did not include output JSON"
    assert "HostileResponseBody" not in error
    assert "response-body-secret" not in error
    assert "client_secret" not in error


def test_openai_responses_provider_rejects_string_subclass_output_text_without_leak() -> None:
    class HostileOutputText(str):
        def __len__(self) -> int:
            raise AssertionError("client_secret=output-text-secret")

    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(
                status_code=200,
                json_body={"output_text": HostileOutputText(json.dumps(_candidate()))},
            )
        ),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert error == "OpenAI response did not include output JSON"
    assert "HostileOutputText" not in error
    assert "output-text-secret" not in error
    assert "client_secret" not in error


def test_openai_responses_provider_rejects_string_subclass_nested_text_without_leak() -> None:
    class HostileNestedText(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=nested-output-secret")

    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(
                status_code=200,
                json_body={
                    "output": [
                        {
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": HostileNestedText(json.dumps(_candidate())),
                                }
                            ]
                        }
                    ]
                },
            )
        ),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert error == "OpenAI response did not include output JSON"
    assert "HostileNestedText" not in error
    assert "nested-output-secret" not in error
    assert "client_secret" not in error


def test_openai_responses_provider_rejects_non_finite_response_json() -> None:
    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(
                status_code=200,
                json_body={
                    "output_text": (
                        '{"changes":[{"table":"sys_dictionary","operation":"insert",'
                        '"fields":[{"name":"risk_score","value":NaN}],'
                        '"sys_id":null,"rationale":null}],'
                        '"test_plan":["Review."],"rollback_notes":["Rollback."]}'
                    )
                },
            )
        ),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    diagnostic = str(exc.value)
    assert diagnostic == "OpenAI response was not valid JSON"
    assert "NaN" not in diagnostic
    assert "risk_score" not in diagnostic


def test_openai_responses_provider_rejects_oversized_output_before_json_parse() -> None:
    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(
                status_code=200,
                json_body={"output_text": "x" * (MAX_OPENAI_PROVIDER_OUTPUT_CHARS + 1)},
            )
        ),
    )

    with pytest.raises(OpenAIProviderError) as exc:
        provider.generate(_payload())

    error = str(exc.value)
    assert "OpenAI response output exceeded" in error
    assert str(MAX_OPENAI_PROVIDER_OUTPUT_CHARS) in error
    assert "x" * 100 not in error


def test_openai_responses_provider_rejects_arbitrary_field_object() -> None:
    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(
                status_code=200,
                json_body={
                    "output_text": json.dumps(
                        {
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
                    )
                },
            )
        ),
    )

    with pytest.raises(OpenAIProviderError, match="fields must be an exact list"):
        provider.generate(_payload())


def test_openai_responses_provider_rejects_too_many_candidate_changes() -> None:
    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(
                status_code=200,
                json_body={
                    "output_text": json.dumps(
                        {
                            "changes": [
                                {
                                    "table": "sys_dictionary",
                                    "operation": "insert",
                                    "fields": [{"name": "name", "value": "rm_story"}],
                                    "sys_id": None,
                                    "rationale": None,
                                }
                                for _ in range(101)
                            ],
                            "test_plan": ["Confirm generated changes."],
                            "rollback_notes": ["Back out generated changes."],
                        }
                    )
                },
            )
        ),
    )

    with pytest.raises(OpenAIProviderError, match="too many changes"):
        provider.generate(_payload())


def test_openai_responses_provider_rejects_too_many_candidate_fields() -> None:
    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(
                status_code=200,
                json_body={
                    "output_text": json.dumps(
                        {
                            "changes": [
                                {
                                    "table": "sys_dictionary",
                                    "operation": "insert",
                                    "fields": [
                                        {"name": f"field_{index}", "value": "x"}
                                        for index in range(101)
                                    ],
                                    "sys_id": None,
                                    "rationale": None,
                                }
                            ],
                            "test_plan": ["Confirm generated changes."],
                            "rollback_notes": ["Back out generated changes."],
                        }
                    )
                },
            )
        ),
    )

    with pytest.raises(OpenAIProviderError, match="too many fields"):
        provider.generate(_payload())
