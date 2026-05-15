from __future__ import annotations

import json

import pytest

from jedi_devproject.openai_provider import (
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
    change_schema = schema["properties"]["changes"]["items"]
    assert change_schema["additionalProperties"] is False
    assert change_schema["required"] == [
        "table",
        "operation",
        "fields",
        "sys_id",
        "rationale",
    ]
    fields_schema = change_schema["properties"]["fields"]
    assert fields_schema["type"] == "array"
    assert fields_schema["items"]["additionalProperties"] is False
    assert change_schema["properties"]["sys_id"] == {"type": "null"}
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


def test_openai_responses_provider_parses_output_item_text() -> None:
    expected = {
        "changes": [],
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

    assert result == expected


def test_openai_responses_provider_fails_closed_for_api_error() -> None:
    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(status_code=500, json_body={"error": {"message": "boom"}})
        ),
    )

    with pytest.raises(OpenAIProviderError, match="status 500: boom"):
        provider.generate(_payload())


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


def test_openai_responses_provider_fails_closed_for_invalid_json() -> None:
    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(status_code=200, json_body={"output_text": "not json"})
        ),
    )

    with pytest.raises(OpenAIProviderError, match="valid JSON"):
        provider.generate(_payload())


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

    with pytest.raises(OpenAIProviderError, match="name/value pairs"):
        provider.generate(_payload())
