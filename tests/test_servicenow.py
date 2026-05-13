from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from jedi_devproject.models import DataClassification
from jedi_devproject.servicenow import (
    HttpRequest,
    HttpResponse,
    OAuthClientCredentials,
    ServiceNowApiError,
    ServiceNowClient,
    ServiceNowSettings,
    StoryDictionaryField,
    StoryStateChoice,
    UrllibTransport,
    load_dotenv_values,
    oauth_auth_from_env,
    redact_secrets,
    servicenow_client_from_env,
)


class RecordingTransport:
    def __init__(self, responses: list[HttpResponse]) -> None:
        self.responses = responses
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        return self.responses.pop(0)


class FakeUrlResponse:
    status = 200

    def __enter__(self) -> "FakeUrlResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return b'{"result": []}'


def test_load_dotenv_values_reads_expected_keys_without_required_dependency(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )

    values = load_dotenv_values(env_path)

    assert values["SERVICENOW_CLIENT_ID"] == "client-id"
    assert values["SERVICENOW_CLIENT_SECRET"] == "client-secret"


def test_load_dotenv_values_ignores_comments_blanks_and_malformed_lines(
    tmp_path: Path,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "# local secrets",
                "",
                "MALFORMED",
                "SERVICENOW_CLIENT_ID='client-id'",
            ]
        ),
        encoding="utf-8",
    )

    assert load_dotenv_values(env_path) == {"SERVICENOW_CLIENT_ID": "client-id"}


def test_oauth_auth_from_env_uses_expected_servicenow_keys(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
    )

    auth = oauth_auth_from_env(
        env_path,
        instance_url="https://dev205693.service-now.com",
        transport=transport,
    )

    assert auth.authorization_header() == "Bearer token-123"
    assert transport.requests[0].body["client_id"] == "client-id"
    assert transport.requests[0].body["client_secret"] == "client-secret"


def test_servicenow_client_from_env_uses_instance_url_and_oauth_keys(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(status_code=200, json_body={"result": []}),
        ]
    )

    client = servicenow_client_from_env(env_path, transport=transport)
    client.fetch_ready_stories()

    assert transport.requests[0].url == "https://dev205693.service-now.com/oauth_token.do"
    assert transport.requests[1].url == "https://dev205693.service-now.com/api/now/table/rm_story"


def test_servicenow_client_from_env_requires_instance_url(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ServiceNowApiError) as exc:
        servicenow_client_from_env(env_path, transport=RecordingTransport([]))

    assert "SERVICENOW_INSTANCE_URL" in str(exc.value)


def test_urllib_transport_encodes_query_and_form_body() -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponse:
        captured["full_url"] = request.full_url
        captured["data"] = request.data
        captured["headers"] = dict(request.header_items())
        captured["method"] = request.get_method()
        captured["timeout"] = timeout
        return FakeUrlResponse()

    with patch("urllib.request.urlopen", fake_urlopen):
        response = UrllibTransport().send(
            HttpRequest(
                method="POST",
                url="https://example.service-now.com/oauth_token.do",
                params={"sysparm_limit": "1"},
                body={"grant_type": "client_credentials"},
            )
        )

    assert response == HttpResponse(status_code=200, json_body={"result": []})
    assert captured["full_url"].endswith("?sysparm_limit=1")
    assert captured["data"] == b"grant_type=client_credentials"
    assert captured["headers"]["Content-type"] == "application/x-www-form-urlencoded"
    assert captured["method"] == "POST"
    assert captured["timeout"] == 30


def test_urllib_transport_handles_request_without_params_or_body() -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponse:
        captured["full_url"] = request.full_url
        captured["data"] = request.data
        return FakeUrlResponse()

    with patch("urllib.request.urlopen", fake_urlopen):
        UrllibTransport().send(HttpRequest(method="GET", url="https://example.service-now.com/api"))

    assert captured["full_url"] == "https://example.service-now.com/api"
    assert captured["data"] is None


def test_oauth_client_credentials_requests_token_without_logging_secret() -> None:
    transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
    )
    auth = OAuthClientCredentials(
        instance_url="https://dev205693.service-now.com",
        client_id="client-id",
        client_secret="client-secret",
        transport=transport,
    )

    header = auth.authorization_header()

    assert header == "Bearer token-123"
    request = transport.requests[0]
    assert request.url == "https://dev205693.service-now.com/oauth_token.do"
    assert request.body["grant_type"] == "client_credentials"
    assert request.body["client_id"] == "client-id"
    assert request.body["client_secret"] == "client-secret"
    assert "client-secret" not in repr(request.sanitized())


def test_oauth_client_credentials_reuses_cached_token() -> None:
    transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
    )
    auth = OAuthClientCredentials(
        instance_url="https://dev205693.service-now.com/",
        client_id="client-id",
        client_secret="client-secret",
        transport=transport,
    )

    assert auth.authorization_header() == "Bearer token-123"
    assert auth.authorization_header() == "Bearer token-123"
    assert len(transport.requests) == 1


def test_oauth_client_credentials_raises_on_token_failure() -> None:
    transport = RecordingTransport([HttpResponse(status_code=401, json_body={})])
    auth = OAuthClientCredentials(
        instance_url="https://dev205693.service-now.com",
        client_id="client-id",
        client_secret="client-secret",
        transport=transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        auth.authorization_header()

    assert "ServiceNow OAuth failed with status 401" in str(exc.value)


def test_oauth_client_credentials_raises_when_access_token_is_missing() -> None:
    transport = RecordingTransport([HttpResponse(status_code=200, json_body={})])
    auth = OAuthClientCredentials(
        instance_url="https://dev205693.service-now.com",
        client_id="client-id",
        client_secret="client-secret",
        transport=transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        auth.authorization_header()

    assert "access_token" in str(exc.value)


def test_servicenow_client_builds_read_only_story_query_without_credentials() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(status_code=200, json_body={"result": []}),
        ]
    )
    auth = OAuthClientCredentials(
        instance_url="https://dev205693.service-now.com",
        client_id="client-id",
        client_secret="client-secret",
        transport=transport,
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=auth,
        transport=transport,
    )

    client.fetch_ready_stories(project_sys_id="project-123", limit=5)

    request = transport.requests[1]
    assert request.method == "GET"
    assert request.url == "https://dev205693.service-now.com/api/now/table/rm_story"
    assert request.params["sysparm_query"] == "state=Ready^project=project-123"
    assert request.params["sysparm_limit"] == "5"
    assert "sys_id,number,short_description" in request.params["sysparm_fields"]
    assert request.headers["Authorization"] == "Bearer token-123"
    assert "client-secret" not in repr(request.sanitized())


def test_servicenow_client_fetch_stories_allows_explicit_query() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(status_code=200, json_body={"result": []}),
        ]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=transport,
        ),
        transport=transport,
    )

    client.fetch_stories(sysparm_query="active=true", limit=3)

    request = transport.requests[1]
    assert request.params["sysparm_query"] == "active=true"
    assert request.params["sysparm_limit"] == "3"


def test_servicenow_client_fetch_stories_can_query_without_state_filter() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(status_code=200, json_body={"result": []}),
        ]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=transport,
        ),
        transport=transport,
    )

    client.fetch_stories(limit=1)

    request = transport.requests[1]
    assert "sysparm_query" not in request.params
    assert request.params["sysparm_limit"] == "1"


def test_servicenow_client_maps_missing_optional_record_values_to_safe_defaults() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "sys_id": "abc123",
                            "number": "STORY0010001",
                            "short_description": "Update portal help text",
                            "state": "Ready",
                        }
                    ]
                },
            ),
        ]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com/"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=transport,
        ),
        transport=transport,
    )

    story = client.fetch_ready_stories()[0]

    assert story.description == "Update portal help text"
    assert story.story_points == 0
    assert story.priority == 5


def test_servicenow_client_maps_records_to_validated_stories() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "sys_id": "abc123",
                            "number": "STORY0010001",
                            "short_description": "Update portal help text",
                            "description": "Change Submit to Send.",
                            "acceptance_criteria": "The field is visible and saves.",
                            "story_points": "2",
                            "priority": "3",
                            "state": "Ready",
                        }
                    ]
                },
            ),
        ]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=transport,
        ),
        transport=transport,
    )

    stories = client.fetch_ready_stories()

    assert stories[0].number == "STORY0010001"
    assert stories[0].story_points == 2
    assert stories[0].acceptance_criteria == "The field is visible and saves."
    assert stories[0].data_classification is DataClassification.PUBLIC


def test_servicenow_client_requests_acceptance_criteria_field() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(status_code=200, json_body={"result": []}),
        ]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=transport,
        ),
        transport=transport,
    )

    client.fetch_stories(sysparm_query="number=STRY0010013", limit=1)

    requested_fields = transport.requests[1].params["sysparm_fields"].split(",")
    assert "acceptance_criteria" in requested_fields


def test_servicenow_client_requests_and_maps_writeback_idempotency_fields() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "sys_id": "abc123",
                            "number": "STRY0010013",
                            "short_description": "Add AI Review Notes",
                            "description": "Add field to form.",
                            "story_points": "3",
                            "priority": "4",
                            "state": "-7",
                            "u_ai_status": "Ready for Testing",
                            "u_ai_build_reference": "build-20260513-001",
                            "u_ai_candidate_artifact": "artifacts/STRY0010013.json",
                        }
                    ]
                },
            ),
        ]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=transport,
        ),
        transport=transport,
    )

    story = client.fetch_stories(sysparm_query="number=STRY0010013", limit=1)[0]

    requested_fields = transport.requests[1].params["sysparm_fields"].split(",")
    assert "u_ai_status" in requested_fields
    assert "u_ai_build_reference" in requested_fields
    assert "u_ai_candidate_artifact" in requested_fields
    assert story.additional_context["u_ai_status"] == "Ready for Testing"
    assert story.additional_context["u_ai_build_reference"] == "build-20260513-001"
    assert story.additional_context["u_ai_candidate_artifact"] == "artifacts/STRY0010013.json"


def test_servicenow_client_fetches_story_state_choices_from_sys_choice() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "label": "Ready for Testing",
                            "value": "-7",
                            "sequence": "50",
                            "inactive": "false",
                        },
                        {
                            "label": "Cancelled",
                            "value": "4",
                            "sequence": "90",
                            "inactive": "true",
                        },
                    ]
                },
            ),
        ]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=transport,
        ),
        transport=transport,
    )

    choices = client.fetch_story_state_choices()

    request = transport.requests[1]
    assert request.url == "https://dev205693.service-now.com/api/now/table/sys_choice"
    assert request.params["sysparm_query"] == "name=rm_story^element=state^inactive=false"
    assert request.params["sysparm_fields"] == "label,value,sequence,inactive"
    assert choices == [
        StoryStateChoice(
            label="Ready for Testing",
            value="-7",
            sequence=50,
            inactive=False,
        )
    ]


def test_servicenow_client_fetches_active_story_dictionary_fields() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "element": "u_ai_status",
                            "column_label": "AI Status",
                            "internal_type": "string",
                            "active": "true",
                        },
                        {
                            "element": "u_old_ai_status",
                            "column_label": "Old AI Status",
                            "internal_type": "string",
                            "active": "false",
                        },
                    ]
                },
            ),
        ]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=transport,
        ),
        transport=transport,
    )

    fields = client.fetch_story_dictionary_fields()

    request = transport.requests[1]
    assert request.url == "https://dev205693.service-now.com/api/now/table/sys_dictionary"
    assert request.params["sysparm_query"] == "name=rm_story^active=true"
    assert request.params["sysparm_fields"] == "element,column_label,internal_type,active"
    assert fields == [
        StoryDictionaryField(
            element="u_ai_status",
            column_label="AI Status",
            internal_type="string",
            active=True,
        )
    ]


def test_servicenow_client_creates_story_dictionary_field() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=201,
                json_body={
                    "result": {
                        "name": "rm_story",
                        "element": "u_ai_status",
                    }
                },
            ),
        ]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=transport,
        ),
        transport=transport,
    )

    client.create_story_dictionary_field(
        element="u_ai_status",
        column_label="AI Status",
        internal_type="string",
        max_length=80,
    )

    request = transport.requests[1]
    assert request.method == "POST"
    assert request.url == "https://dev205693.service-now.com/api/now/table/sys_dictionary"
    assert request.headers["Authorization"] == "Bearer token-123"
    assert request.headers["Content-Type"] == "application/json"
    assert request.body == {
        "name": "rm_story",
        "element": "u_ai_status",
        "column_label": "AI Status",
        "internal_type": "string",
        "max_length": "80",
        "active": "true",
    }
    assert "client-secret" not in repr(request.sanitized())


def test_servicenow_client_updates_story_fields_with_patch_without_secret_leakage() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(status_code=200, json_body={"result": {"sys_id": "story-sys-id"}}),
        ]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=transport,
        ),
        transport=transport,
    )

    client.update_story_fields(
        "story-sys-id",
        {
            "state": "Ready for Testing",
            "u_ai_status": "Ready for Testing",
        },
    )

    request = transport.requests[1]
    assert request.method == "PATCH"
    assert request.url.endswith("/api/now/table/rm_story/story-sys-id")
    assert request.headers["Authorization"] == "Bearer token-123"
    assert request.headers["Content-Type"] == "application/json"
    assert request.body["state"] == "Ready for Testing"
    assert "client-secret" not in repr(request.sanitized())


def test_servicenow_api_failure_raises_without_secret_leakage() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(status_code=500, json_body={"error": {"message": "boom"}}),
        ]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=transport,
        ),
        transport=transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_ready_stories()

    assert "ServiceNow API failed with status 500" in str(exc.value)
    assert "client-secret" not in str(exc.value)


@pytest.mark.parametrize(
    "payload",
    [
        {"Authorization": "Bearer token-123", "client_secret": "secret"},
        {"access_token": "token-123", "nested": {"client_secret": "secret"}},
    ],
)
def test_redact_secrets_masks_sensitive_values(payload: dict[str, Any]) -> None:
    redacted = redact_secrets(payload)

    assert "'secret'" not in repr(redacted)
    assert "Bearer token-123" not in repr(redacted)
    assert "'token-123'" not in repr(redacted)


def test_redact_secrets_masks_sensitive_values_inside_lists() -> None:
    redacted = redact_secrets([{"access_token": "token-123"}])

    assert "'token-123'" not in repr(redacted)
