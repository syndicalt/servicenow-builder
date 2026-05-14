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
    change_schema = schema["properties"]["changes"]["items"]
    assert change_schema["additionalProperties"] is False
    fields_schema = change_schema["properties"]["fields"]
    assert fields_schema["type"] == "array"
    assert fields_schema["items"]["additionalProperties"] is False
    assert "JSON" in request.body["input"][0]["content"]
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

    result = OpenAIResponsesProvider(settings=_settings(), transport=transport).generate(
        _payload()
    )

    assert result == expected


def test_openai_responses_provider_fails_closed_for_api_error() -> None:
    provider = OpenAIResponsesProvider(
        settings=_settings(),
        transport=RecordingTransport(
            HttpResponse(status_code=500, json_body={"error": {"message": "boom"}})
        ),
    )

    with pytest.raises(OpenAIProviderError, match="status 500"):
        provider.generate(_payload())


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
