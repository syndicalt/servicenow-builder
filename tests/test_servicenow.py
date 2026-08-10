import urllib.error
from collections.abc import Callable, Iterator
from email.message import EmailMessage
from http.client import HTTPMessage
from io import BytesIO
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch
from urllib.request import Request

import pytest
from pydantic import ValidationError

from jedi_devproject import servicenow
from jedi_devproject.artifacts import ArtifactReadError
from jedi_devproject.models import DataClassification
from jedi_devproject.servicenow import (
    HTTP_ERROR_TRUNCATION_MARKER,
    MAX_ATTACHMENT_UPLOAD_BYTES,
    MAX_HTTP_ERROR_DIAGNOSTIC_CHARS,
    SERVICENOW_LOOKUP_NON_JSON_DIAGNOSTIC,
    SERVICENOW_LOOKUP_QUERY_UNSAFE_DIAGNOSTIC,
    SERVICENOW_OPERATION_URI_UNSAFE_DIAGNOSTIC,
    SERVICENOW_RECORD_ID_UNSAFE_DIAGNOSTIC,
    SERVICENOW_RESULT_LIMIT_UNSAFE_DIAGNOSTIC,
    SERVICENOW_STORY_QUERY_UNSAFE_DIAGNOSTIC,
    SERVICENOW_TABLE_NAME_UNSAFE_DIAGNOSTIC,
    HttpRequest,
    HttpResponse,
    OAuthClientCredentials,
    ServiceNowApiError,
    ServiceNowClient,
    ServiceNowSettings,
    StoryDictionaryField,
    StoryStateChoice,
    UrllibTransport,
    _bound_http_error_diagnostics,
    _servicenow_api_error_message,
    _servicenow_diagnostic_value,
    _truncate_http_error_diagnostic,
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


class HostileTransport:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> Any:
        self.requests.append(request)
        return self.response


class FakeUrlResponse:
    status = 200

    def __enter__(self) -> "FakeUrlResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, n: int = -1) -> bytes:
        body = b'{"result": []}'
        return body if n < 0 else body[:n]


class FakeLargeUrlResponse:
    status = 200

    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> "FakeLargeUrlResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, n: int = -1) -> bytes:
        return self._body if n < 0 else self._body[:n]


class FakeUrlResponseWithStatus:
    def __init__(self, *, status: Any, body: bytes = b'{"result": []}') -> None:
        self.status = status
        self._body = body

    def __enter__(self) -> "FakeUrlResponseWithStatus":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, n: int = -1) -> bytes:
        return self._body if n < 0 else self._body[:n]


class FakeHttpError(urllib.error.HTTPError):
    def __init__(self, *, code: Any, body: bytes) -> None:
        super().__init__(
            "https://api.openai.com/v1/responses",
            code,
            "Too Many Requests",
            hdrs=EmailMessage(),
            fp=None,
        )
        self._body = body

    def read(self, n: int = -1) -> bytes:
        return self._body if n < 0 else self._body[:n]


class FakeUrlOpener:
    def __init__(self, open_func: Callable[[Any, int], Any]) -> None:
        self._open_func = open_func

    def open(self, request: Any, *, timeout: int) -> Any:
        return self._open_func(request, timeout)


def _patch_urllib_transport_opener(open_func: Callable[[Any, int], Any]) -> Any:
    def fake_build_opener(*_handlers: object) -> FakeUrlOpener:
        return FakeUrlOpener(open_func)

    return patch("urllib.request.build_opener", fake_build_opener)


class SecretBearingServiceNowSysId:
    def __str__(self) -> str:
        return "client_secret=servicenow-sys-id-secret"

    def __repr__(self) -> str:
        return "SecretBearingServiceNowSysId(client_secret=servicenow-sys-id-secret)"


class SecretBearingServiceNowProjectId:
    def __bool__(self) -> bool:
        raise RuntimeError("client_secret=servicenow-project-id-secret")

    def __str__(self) -> str:
        return "client_secret=servicenow-project-id-secret"

    def __repr__(self) -> str:
        return "SecretBearingServiceNowProjectId(client_secret=servicenow-project-id-secret)"


class SecretBearingServiceNowCicdSourceId:
    def __bool__(self) -> bool:
        raise RuntimeError("client_secret=servicenow-cicd-source-id-secret")

    def __str__(self) -> str:
        return "client_secret=servicenow-cicd-source-id-secret"

    def __repr__(self) -> str:
        return "SecretBearingServiceNowCicdSourceId(client_secret=servicenow-cicd-source-id-secret)"


class SecretBearingServiceNowCicdProbeAction:
    def __hash__(self) -> int:
        raise RuntimeError("client_secret=servicenow-cicd-probe-action-secret")

    def __str__(self) -> str:
        return "client_secret=servicenow-cicd-probe-action-secret"

    def __repr__(self) -> str:
        return (
            "SecretBearingServiceNowCicdProbeAction("
            "client_secret=servicenow-cicd-probe-action-secret)"
        )


class ExplodingServiceNowLookupResponseText(str):
    def __str__(self) -> str:
        raise RuntimeError("client_secret=servicenow-lookup-response-text-secret")


class ExplodingServiceNowSysId(str):
    def strip(self, chars: str | None = None) -> str:
        raise RuntimeError("client_secret=servicenow-sys-id-strip-secret")


class SecretBearingServiceNowFieldName:
    def __str__(self) -> str:
        return "client_secret=servicenow-field-secret"

    def __repr__(self) -> str:
        return "SecretBearingServiceNowFieldName(client_secret=servicenow-field-secret)"


class ExplodingServiceNowFieldName(str):
    def strip(self, chars: str | None = None) -> str:
        raise RuntimeError("client_secret=servicenow-field-name-strip-secret")


class ExplodingServiceNowAccessToken(str):
    def strip(self, chars: str | None = None) -> str:
        raise RuntimeError("client_secret=servicenow-access-token-strip-secret")


class ExplodingServiceNowOperationUri(str):
    def strip(self, chars: str | None = None) -> str:
        raise RuntimeError("client_secret=servicenow-operation-uri-strip-secret")


class SecretBearingServiceNowTableName:
    def __str__(self) -> str:
        return "client_secret=servicenow-table-secret"

    def __repr__(self) -> str:
        return "SecretBearingServiceNowTableName(client_secret=servicenow-table-secret)"


class ExplodingServiceNowTableName(str):
    def strip(self, chars: str | None = None) -> str:
        raise RuntimeError("client_secret=servicenow-table-name-strip-secret")


class SecretBearingServiceNowLookupPart:
    def __str__(self) -> str:
        return "client_secret=servicenow-lookup-secret"

    def __repr__(self) -> str:
        return "SecretBearingServiceNowLookupPart(client_secret=servicenow-lookup-secret)"


class ExplodingServiceNowLookupPart(str):
    def __iter__(self) -> Any:
        raise RuntimeError("client_secret=servicenow-lookup-iter-secret")


class SecretBearingServiceNowResultLimit:
    def __str__(self) -> str:
        return "client_secret=servicenow-limit-secret"

    def __repr__(self) -> str:
        return "SecretBearingServiceNowResultLimit(client_secret=servicenow-limit-secret)"


class SecretBearingServiceNowStoryQuery:
    def __bool__(self) -> bool:
        raise RuntimeError("client_secret=servicenow-story-query-secret")

    def __str__(self) -> str:
        return "number=STRY0010013^client_secret=servicenow-story-query-secret"

    def __repr__(self) -> str:
        return "SecretBearingServiceNowStoryQuery(client_secret=servicenow-story-query-secret)"


class SecretBearingServiceNowDictionaryInternalType:
    def __str__(self) -> str:
        return "client_secret=servicenow-internal-type-secret"

    def __repr__(self) -> str:
        return (
            "SecretBearingServiceNowDictionaryInternalType("
            "client_secret=servicenow-internal-type-secret)"
        )


class ExplodingServiceNowDictionaryInternalType(str):
    def strip(self, chars: str | None = None) -> str:
        raise RuntimeError("client_secret=servicenow-internal-type-strip-secret")


class ExplodingServiceNowDictionaryColumnLabel(str):
    def strip(self, chars: str | None = None) -> str:
        raise RuntimeError("client_secret=servicenow-column-label-strip-secret")


class SecretBearingServiceNowAttachmentFileName:
    def __str__(self) -> str:
        return "client_secret=servicenow-attachment-file-name-secret"

    def __repr__(self) -> str:
        return (
            "SecretBearingServiceNowAttachmentFileName("
            "client_secret=servicenow-attachment-file-name-secret)"
        )


class ExplodingServiceNowAttachmentFileName(str):
    def strip(self, chars: str | None = None) -> str:
        raise RuntimeError("client_secret=servicenow-attachment-file-name-strip-secret")


class SecretBearingServiceNowAttachmentContentType:
    def __str__(self) -> str:
        return "client_secret=servicenow-attachment-content-type-secret"

    def __repr__(self) -> str:
        return (
            "SecretBearingServiceNowAttachmentContentType("
            "client_secret=servicenow-attachment-content-type-secret)"
        )


class ExplodingServiceNowAttachmentContentType(str):
    def strip(self, chars: str | None = None) -> str:
        raise RuntimeError("client_secret=servicenow-attachment-content-type-strip-secret")


class SecretBearingServiceNowStoryField:
    def __str__(self) -> str:
        return "client_secret=servicenow-story-field-secret"

    def __repr__(self) -> str:
        return "SecretBearingServiceNowStoryField(client_secret=servicenow-story-field-secret)"


class ExplodingServiceNowStoryText(str):
    def strip(self, chars: str | None = None) -> str:
        raise RuntimeError("client_secret=servicenow-story-text-strip-secret")


class ExplodingServiceNowStoryPriorityInt(int):
    def __ge__(self, other: object) -> bool:
        raise RuntimeError("client_secret=servicenow-story-priority-int-secret")

    def __le__(self, other: object) -> bool:
        raise RuntimeError("client_secret=servicenow-story-priority-int-secret")


class ExplodingServiceNowStoryPointsFloat(float):
    def __ge__(self, other: object) -> bool:
        raise RuntimeError("client_secret=servicenow-story-points-float-secret")


class SecretBearingServiceNowMetadataField:
    def __str__(self) -> str:
        return "client_secret=servicenow-metadata-field-secret"

    def __repr__(self) -> str:
        return (
            "SecretBearingServiceNowMetadataField("
            "client_secret=servicenow-metadata-field-secret)"
        )


class ExplodingServiceNowMetadataBoolean(str):
    def lower(self) -> str:
        raise RuntimeError("client_secret=servicenow-metadata-boolean-secret")


class SecretBearingServiceNowMetadataText(str):
    pass


class ExplodingServiceNowMetadataSequence(str):
    def isascii(self) -> bool:
        raise RuntimeError("client_secret=servicenow-metadata-sequence-secret")


class ExplodingServiceNowMetadataSequenceInt(int):
    def __ge__(self, other: object) -> bool:
        raise RuntimeError("client_secret=servicenow-metadata-sequence-int-secret")


@pytest.mark.parametrize(
    ("model_class", "values", "sensitive_parts"),
    [
        (ServiceNowSettings, {"instance_url": 123}, ("123",)),
        (HttpRequest, {"method": "GET", "url": 123}, ("123",)),
        (
            HttpRequest,
            {
                "method": "POST",
                "url": "https://example.service-now.com/api",
                "headers": {"Authorization": 123},
            },
            ("123",),
        ),
        (HttpResponse, {"status_code": "secret-status", "json_body": {}}, ("secret-status",)),
    ],
)
def test_servicenow_boundary_validation_errors_do_not_echo_rejected_inputs(
    model_class: type[Any],
    values: dict[str, Any],
    sensitive_parts: tuple[str, ...],
) -> None:
    with pytest.raises(ValidationError) as exc:
        model_class(**values)

    message = str(exc.value)
    assert "input_value" not in message
    for sensitive_part in sensitive_parts:
        assert sensitive_part not in message


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


def test_load_dotenv_values_accepts_matching_quoted_values(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                'SERVICENOW_CLIENT_ID="client-id"',
                "SERVICENOW_CLIENT_SECRET='client-secret'",
            ]
        ),
        encoding="utf-8",
    )

    assert load_dotenv_values(env_path) == {
        "SERVICENOW_CLIENT_ID": "client-id",
        "SERVICENOW_CLIENT_SECRET": "client-secret",
    }


def test_load_dotenv_values_rejects_duplicate_keys_without_last_value_wins(
    tmp_path: Path,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_CLIENT_SECRET=first-secret",
                "SERVICENOW_CLIENT_SECRET=second-secret",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="dotenv_duplicate_key") as exc:
        load_dotenv_values(env_path)

    message = str(exc.value)
    assert "SERVICENOW_CLIENT_SECRET" in message
    assert "first-secret" not in message
    assert "second-secret" not in message


@pytest.mark.parametrize(
    "env_line",
    [
        " SERVICENOW_CLIENT_ID=client-id",
        "SERVICENOW_CLIENT_ID =client-id",
        "=client-id",
        "SERVICE\tNOW_CLIENT_ID=client-id",
        "servicenow_client_id=client-id",
        "SERVICE-NOW_CLIENT_ID=client-id",
        "SERVICENOW.CLIENT_ID=client-id",
        "1SERVICENOW_CLIENT_ID=client-id",
    ],
)
def test_load_dotenv_values_rejects_malformed_key_names(
    tmp_path: Path,
    env_line: str,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(env_line, encoding="utf-8")

    with pytest.raises(ValueError, match="dotenv_invalid_key") as exc:
        load_dotenv_values(env_path)

    message = str(exc.value)
    assert "client-id" not in message
    assert "\t" not in message


@pytest.mark.parametrize(
    "env_line",
    [
        'SERVICENOW_CLIENT_SECRET="client-secret',
        "SERVICENOW_CLIENT_SECRET=client-secret'",
        "SERVICENOW_CLIENT_SECRET=\"client-secret'",
        "SERVICENOW_CLIENT_SECRET='client-secret\"",
    ],
)
def test_load_dotenv_values_rejects_unmatched_or_mixed_value_quotes(
    tmp_path: Path,
    env_line: str,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(env_line, encoding="utf-8")

    with pytest.raises(ValueError, match="dotenv_invalid_value_quotes") as exc:
        load_dotenv_values(env_path)

    message = str(exc.value)
    assert "SERVICENOW_CLIENT_SECRET" in message
    assert "client-secret" not in message


def test_load_dotenv_values_rejects_oversized_env_without_whole_file_text_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("SERVICENOW_CLIENT_ID=client-id\n", encoding="utf-8")
    monkeypatch.setattr(
        "jedi_devproject.servicenow.DOTENV_INPUT_MAX_BYTES",
        4,
        raising=False,
    )

    def fail_read_text(
        self: Path,
        encoding: str | None = None,
        errors: str | None = None,
    ) -> str:
        raise AssertionError(f"unexpected whole-file text read for {self}")

    monkeypatch.setattr(Path, "read_text", fail_read_text)

    with pytest.raises(ValueError, match="dotenv_input_too_large"):
        load_dotenv_values(env_path)


def test_load_dotenv_values_oversized_error_does_not_echo_env_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_path = tmp_path / "client_secret=dotenv-size-secret.env"
    env_path.write_text("SERVICENOW_CLIENT_ID=client-id\n", encoding="utf-8")
    monkeypatch.setattr(
        "jedi_devproject.servicenow.DOTENV_INPUT_MAX_BYTES",
        4,
        raising=False,
    )

    with pytest.raises(ValueError) as exc_info:
        load_dotenv_values(env_path)

    diagnostic = str(exc_info.value)
    assert "dotenv_input_too_large" in diagnostic
    assert "dotenv-size-secret" not in diagnostic
    assert str(env_path) not in diagnostic


def test_load_dotenv_values_rejects_symlinked_env_file(tmp_path: Path) -> None:
    target_path = tmp_path / "target.env"
    target_path.write_text("SERVICENOW_CLIENT_ID=client-id\n", encoding="utf-8")
    env_link = tmp_path / ".env"
    env_link.symlink_to(target_path)

    with pytest.raises(ValueError, match="dotenv_must_be_regular_file"):
        load_dotenv_values(env_link)


def test_load_dotenv_values_regular_file_error_does_not_echo_env_path(
    tmp_path: Path,
) -> None:
    target_path = tmp_path / "target.env"
    target_path.write_text("SERVICENOW_CLIENT_ID=client-id\n", encoding="utf-8")
    env_link = tmp_path / "client_secret=dotenv-link-secret.env"
    env_link.symlink_to(target_path)

    with pytest.raises(ValueError) as exc_info:
        load_dotenv_values(env_link)

    diagnostic = str(exc_info.value)
    assert "dotenv_must_be_regular_file" in diagnostic
    assert "dotenv-link-secret" not in diagnostic
    assert str(env_link) not in diagnostic
    assert exc_info.value.__cause__ is None


def test_load_dotenv_values_invalid_utf8_error_does_not_echo_env_path_or_bytes(
    tmp_path: Path,
) -> None:
    env_path = tmp_path / "client_secret=dotenv-utf8-secret.env"
    env_path.write_bytes(b"SERVICENOW_CLIENT_SECRET=\xff\n")

    with pytest.raises(ValueError) as exc_info:
        load_dotenv_values(env_path)

    diagnostic = str(exc_info.value)
    assert "dotenv_invalid_utf8" in diagnostic
    assert "dotenv-utf8-secret" not in diagnostic
    assert str(env_path) not in diagnostic
    assert "SERVICENOW_CLIENT_SECRET" not in diagnostic
    assert exc_info.value.__cause__ is None


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

    with _patch_urllib_transport_opener(fake_urlopen):
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


def test_urllib_transport_rejects_timeout_int_subclass_before_open() -> None:
    class HostileTimeout(int):
        def __float__(self) -> float:
            raise AssertionError("client_secret=servicenow-timeout-float-secret")

    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponse:
        raise AssertionError("transport should reject malformed timeout before opening")

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError) as exc,
    ):
        UrllibTransport(timeout_seconds=HostileTimeout(30)).send(
            HttpRequest(method="GET", url="https://example.service-now.com/api")
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow transport timeout must be a finite positive number"
    assert "HostileTimeout" not in diagnostic
    assert "servicenow-timeout-float-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_rejects_non_finite_timeout_before_open() -> None:
    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponse:
        raise AssertionError("transport should reject non-finite timeout before opening")

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError) as exc,
    ):
        UrllibTransport(timeout_seconds=float("inf")).send(
            HttpRequest(method="GET", url="https://example.service-now.com/api")
        )

    assert str(exc.value) == "ServiceNow transport timeout must be a finite positive number"


def test_urllib_transport_rejects_method_string_subclass_before_request_construction() -> None:
    class HostileRequestMethod(str):
        def upper(self) -> str:
            raise AssertionError("client_secret=servicenow-method-upper-secret")

    def fake_build_opener(*_handlers: object) -> FakeUrlOpener:
        raise AssertionError("transport should reject malformed method before opening")

    with (
        patch("urllib.request.build_opener", fake_build_opener),
        pytest.raises(ServiceNowApiError) as exc,
    ):
        UrllibTransport().send(
            HttpRequest.model_construct(
                method=HostileRequestMethod("GET"),
                url="https://example.service-now.com/api",
                headers={},
                params={},
                body={},
                body_bytes=None,
            )
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow request method is unsafe"
    assert "HostileRequestMethod" not in diagnostic
    assert "servicenow-method-upper-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_rejects_url_string_subclass_before_request_construction() -> None:
    class HostileRequestUrl(str):
        def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
            raise AssertionError("client_secret=servicenow-url-encode-secret")

    def fake_build_opener(*_handlers: object) -> FakeUrlOpener:
        raise AssertionError("transport should reject malformed URL before opening")

    with (
        patch("urllib.request.build_opener", fake_build_opener),
        pytest.raises(ServiceNowApiError) as exc,
    ):
        UrllibTransport().send(
            HttpRequest.model_construct(
                method="GET",
                url=HostileRequestUrl("https://example.service-now.com/api"),
                headers={},
                params={},
                body={},
                body_bytes=None,
            )
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow request URL is unsafe"
    assert "HostileRequestUrl" not in diagnostic
    assert "servicenow-url-encode-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_rejects_credentialed_url_before_request_construction() -> None:
    def fake_build_opener(*_handlers: object) -> FakeUrlOpener:
        raise AssertionError("transport should reject credentialed URL before opening")

    with (
        patch("urllib.request.build_opener", fake_build_opener),
        pytest.raises(ServiceNowApiError) as exc,
    ):
        UrllibTransport().send(
            HttpRequest(
                method="GET",
                url="https://user:client-secret@example.service-now.com/api",
            )
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow request URL is unsafe"
    assert "client-secret" not in diagnostic


def test_urllib_transport_rejects_query_params_dict_subclass_before_url_encoding() -> None:
    class HostileQueryParams(dict[str, str]):
        def __len__(self) -> int:
            raise AssertionError("client_secret=servicenow-query-params-len-secret")

        def items(self) -> Any:
            raise AssertionError("client_secret=servicenow-query-params-items-secret")

    def fake_build_opener(*_handlers: object) -> FakeUrlOpener:
        raise AssertionError("transport should reject malformed query params before opening")

    with (
        patch("urllib.request.build_opener", fake_build_opener),
        pytest.raises(ServiceNowApiError) as exc,
    ):
        UrllibTransport().send(
            HttpRequest.model_construct(
                method="GET",
                url="https://example.service-now.com/api",
                headers={},
                params=HostileQueryParams(sysparm_limit="1"),
                body={},
                body_bytes=None,
            )
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow request query params must be an exact dictionary"
    assert "HostileQueryParams" not in diagnostic
    assert "servicenow-query-params-len-secret" not in diagnostic
    assert "servicenow-query-params-items-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_rejects_query_param_key_string_subclass_before_urlencode() -> None:
    class HostileQueryParamKey(str):
        def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
            raise AssertionError("client_secret=servicenow-query-key-secret")

    def fake_build_opener(*_handlers: object) -> FakeUrlOpener:
        raise AssertionError("transport should reject malformed query key before opening")

    with (
        patch("urllib.request.build_opener", fake_build_opener),
        pytest.raises(ServiceNowApiError) as exc,
    ):
        UrllibTransport().send(
            HttpRequest.model_construct(
                method="GET",
                url="https://example.service-now.com/api",
                headers={},
                params={HostileQueryParamKey("sysparm_limit"): "1"},
                body={},
                body_bytes=None,
            )
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow query params must contain exact string keys and values"
    assert "HostileQueryParamKey" not in diagnostic
    assert "servicenow-query-key-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_rejects_query_param_value_string_subclass_before_urlencode() -> None:
    class HostileQueryParamValue(str):
        def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
            raise AssertionError("client_secret=servicenow-query-value-secret")

    def fake_build_opener(*_handlers: object) -> FakeUrlOpener:
        raise AssertionError("transport should reject malformed query value before opening")

    with (
        patch("urllib.request.build_opener", fake_build_opener),
        pytest.raises(ServiceNowApiError) as exc,
    ):
        UrllibTransport().send(
            HttpRequest.model_construct(
                method="GET",
                url="https://example.service-now.com/api",
                headers={},
                params={"sysparm_limit": HostileQueryParamValue("1")},
                body={},
                body_bytes=None,
            )
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow query params must contain exact string keys and values"
    assert "HostileQueryParamValue" not in diagnostic
    assert "servicenow-query-value-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_wraps_query_urlencode_error_without_leak() -> None:
    def fake_urlencode(query: object, doseq: bool = False, safe: str = "", **kwargs: object) -> str:
        raise RuntimeError("client_secret=servicenow-query-urlencode-secret")

    with (
        patch("urllib.parse.urlencode", fake_urlencode),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(
                method="GET",
                url="https://example.service-now.com/api",
                params={"sysparm_limit": "1"},
            )
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "ServiceNow transport URL encoding failed"
    assert "servicenow-query-urlencode-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_rejects_non_finite_json_request_body_without_sending() -> None:
    def fake_build_opener(*_handlers: object) -> FakeUrlOpener:
        raise AssertionError("transport should reject malformed JSON before opening")

    with (
        patch("urllib.request.build_opener", fake_build_opener),
        pytest.raises(ServiceNowApiError) as exc,
    ):
        UrllibTransport().send(
            HttpRequest(
                method="PATCH",
                url="https://example.service-now.com/api/now/table/incident/sys-id",
                headers={"Content-Type": "application/json"},
                body={
                    "safe_score": 1.25,
                    "bad_score": float("nan"),
                    "secret": "client_secret=body-secret",
                },
            )
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow JSON request body contains non-finite numeric values"
    assert "body-secret" not in diagnostic
    assert "bad_score" not in diagnostic
    assert "NaN" not in diagnostic
    assert exc.value.__cause__ is None


def test_urllib_transport_rejects_json_body_string_subclass_key_before_serialization() -> None:
    class HostileJsonBodyKey(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=servicenow-json-key-secret")

    def fake_build_opener(*_handlers: object) -> FakeUrlOpener:
        raise AssertionError("transport should reject malformed JSON key before opening")

    with (
        patch("urllib.request.build_opener", fake_build_opener),
        pytest.raises(ServiceNowApiError) as exc,
    ):
        UrllibTransport().send(
            HttpRequest.model_construct(
                method="PATCH",
                url="https://example.service-now.com/api/now/table/incident/sys-id",
                headers={"Content-Type": "application/json"},
                params={},
                body={HostileJsonBodyKey("short_description"): "Updated"},
                body_bytes=None,
            )
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow JSON request body contains non-JSON values"
    assert "HostileJsonBodyKey" not in diagnostic
    assert "servicenow-json-key-secret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert exc.value.__cause__ is None


def test_urllib_transport_rejects_json_body_non_json_value_before_serialization() -> None:
    class HostileJsonBodyValue:
        def __repr__(self) -> str:
            return "HostileJsonBodyValue(client_secret=servicenow-json-value-secret)"

    def fake_build_opener(*_handlers: object) -> FakeUrlOpener:
        raise AssertionError("transport should reject malformed JSON value before opening")

    with (
        patch("urllib.request.build_opener", fake_build_opener),
        pytest.raises(ServiceNowApiError) as exc,
    ):
        UrllibTransport().send(
            HttpRequest.model_construct(
                method="PATCH",
                url="https://example.service-now.com/api/now/table/incident/sys-id",
                headers={"Content-Type": "application/json"},
                params={},
                body={"nested": ["safe", HostileJsonBodyValue()]},
                body_bytes=None,
            )
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow JSON request body contains non-JSON values"
    assert "HostileJsonBodyValue" not in diagnostic
    assert "servicenow-json-value-secret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert exc.value.__cause__ is None


def test_urllib_transport_rejects_circular_json_body_before_serialization() -> None:
    circular_body: dict[str, Any] = {"short_description": "Updated"}
    circular_body["self"] = circular_body

    def fake_build_opener(*_handlers: object) -> FakeUrlOpener:
        raise AssertionError("transport should reject circular JSON before opening")

    with (
        patch("urllib.request.build_opener", fake_build_opener),
        pytest.raises(ServiceNowApiError) as exc,
    ):
        UrllibTransport().send(
            HttpRequest.model_construct(
                method="PATCH",
                url="https://example.service-now.com/api/now/table/incident/sys-id",
                headers={"Content-Type": "application/json"},
                params={},
                body=circular_body,
                body_bytes=None,
            )
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow JSON request body contains circular references"
    assert "short_description" not in diagnostic


def test_urllib_transport_rejects_deep_json_body_before_serialization() -> None:
    nested_value: Any = "leaf"
    for _index in range(150):
        nested_value = {"nested": nested_value}

    def fake_build_opener(*_handlers: object) -> FakeUrlOpener:
        raise AssertionError("transport should reject over-depth JSON before opening")

    with (
        patch("urllib.request.build_opener", fake_build_opener),
        pytest.raises(ServiceNowApiError) as exc,
    ):
        UrllibTransport().send(
            HttpRequest.model_construct(
                method="PATCH",
                url="https://example.service-now.com/api/now/table/incident/sys-id",
                headers={"Content-Type": "application/json"},
                params={},
                body=nested_value,
                body_bytes=None,
            )
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow JSON request body is too deeply nested"
    assert "leaf" not in diagnostic


def test_urllib_transport_rejects_body_dict_subclass_before_encoding() -> None:
    class HostileRequestBody(dict[str, object]):
        def __len__(self) -> int:
            raise AssertionError("client_secret=servicenow-body-len-secret")

        def items(self) -> Any:
            raise AssertionError("client_secret=servicenow-body-items-secret")

    def fake_build_opener(*_handlers: object) -> FakeUrlOpener:
        raise AssertionError("transport should reject malformed body before opening")

    with (
        patch("urllib.request.build_opener", fake_build_opener),
        pytest.raises(ServiceNowApiError) as exc,
    ):
        UrllibTransport().send(
            HttpRequest.model_construct(
                method="PATCH",
                url="https://example.service-now.com/api/now/table/incident/sys-id",
                headers={"Content-Type": "application/json"},
                params={},
                body=HostileRequestBody(short_description="Updated"),
                body_bytes=None,
            )
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow request body must be an exact dictionary"
    assert "HostileRequestBody" not in diagnostic
    assert "servicenow-body-len-secret" not in diagnostic
    assert "servicenow-body-items-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_rejects_form_body_string_subclass_key_before_urlencode() -> None:
    class HostileFormBodyKey(str):
        def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
            raise AssertionError("client_secret=servicenow-form-key-secret")

    def fake_build_opener(*_handlers: object) -> FakeUrlOpener:
        raise AssertionError("transport should reject malformed form key before opening")

    with (
        patch("urllib.request.build_opener", fake_build_opener),
        pytest.raises(ServiceNowApiError) as exc,
    ):
        UrllibTransport().send(
            HttpRequest.model_construct(
                method="POST",
                url="https://example.service-now.com/oauth_token.do",
                headers={},
                params={},
                body={HostileFormBodyKey("grant_type"): "client_credentials"},
                body_bytes=None,
            )
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow form request body must contain exact string keys and values"
    assert "HostileFormBodyKey" not in diagnostic
    assert "servicenow-form-key-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_rejects_form_body_string_subclass_value_before_urlencode() -> None:
    class HostileFormBodyValue(str):
        def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
            raise AssertionError("client_secret=servicenow-form-value-secret")

    def fake_build_opener(*_handlers: object) -> FakeUrlOpener:
        raise AssertionError("transport should reject malformed form value before opening")

    with (
        patch("urllib.request.build_opener", fake_build_opener),
        pytest.raises(ServiceNowApiError) as exc,
    ):
        UrllibTransport().send(
            HttpRequest.model_construct(
                method="POST",
                url="https://example.service-now.com/oauth_token.do",
                headers={},
                params={},
                body={"grant_type": HostileFormBodyValue("client_credentials")},
                body_bytes=None,
            )
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow form request body must contain exact string keys and values"
    assert "HostileFormBodyValue" not in diagnostic
    assert "servicenow-form-value-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_wraps_form_urlencode_error_without_leak() -> None:
    def fake_urlencode(query: object, doseq: bool = False, safe: str = "", **kwargs: object) -> str:
        raise RuntimeError("client_secret=servicenow-form-urlencode-secret")

    with (
        patch("urllib.parse.urlencode", fake_urlencode),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(
                method="POST",
                url="https://example.service-now.com/oauth_token.do",
                body={"grant_type": "client_credentials"},
            )
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "ServiceNow transport URL encoding failed"
    assert "servicenow-form-urlencode-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_rejects_headers_dict_subclass_before_encoding() -> None:
    class HostileRequestHeaders(dict[str, str]):
        def items(self) -> Any:
            raise AssertionError("client_secret=servicenow-headers-items-secret")

        def get(self, key: str, default: Any = None) -> Any:
            raise AssertionError("client_secret=servicenow-headers-get-secret")

    def fake_build_opener(*_handlers: object) -> FakeUrlOpener:
        raise AssertionError("transport should reject malformed headers before opening")

    with (
        patch("urllib.request.build_opener", fake_build_opener),
        pytest.raises(ServiceNowApiError) as exc,
    ):
        UrllibTransport().send(
            HttpRequest.model_construct(
                method="PATCH",
                url="https://example.service-now.com/api/now/table/incident/sys-id",
                headers=HostileRequestHeaders({"Content-Type": "application/json"}),
                params={},
                body={"short_description": "Updated"},
                body_bytes=None,
            )
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow request headers must be an exact dictionary"
    assert "HostileRequestHeaders" not in diagnostic
    assert "servicenow-headers-items-secret" not in diagnostic
    assert "servicenow-headers-get-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_rejects_header_key_string_subclass_before_request_construction() -> None:
    class HostileHeaderKey(str):
        def title(self) -> str:
            raise AssertionError("client_secret=servicenow-header-key-title-secret")

    def fake_build_opener(*_handlers: object) -> FakeUrlOpener:
        raise AssertionError("transport should reject malformed header key before opening")

    with (
        patch("urllib.request.build_opener", fake_build_opener),
        pytest.raises(ServiceNowApiError) as exc,
    ):
        UrllibTransport().send(
            HttpRequest.model_construct(
                method="GET",
                url="https://example.service-now.com/api",
                headers={HostileHeaderKey("Accept"): "application/json"},
                params={},
                body={},
                body_bytes=None,
            )
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow request headers must contain exact string keys and values"
    assert "HostileHeaderKey" not in diagnostic
    assert "servicenow-header-key-title-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_rejects_header_value_string_subclass_before_request() -> None:
    class HostileHeaderValue(str):
        def title(self) -> str:
            raise AssertionError("client_secret=servicenow-header-value-title-secret")

    def fake_build_opener(*_handlers: object) -> FakeUrlOpener:
        raise AssertionError("transport should reject malformed header value before opening")

    with (
        patch("urllib.request.build_opener", fake_build_opener),
        pytest.raises(ServiceNowApiError) as exc,
    ):
        UrllibTransport().send(
            HttpRequest.model_construct(
                method="GET",
                url="https://example.service-now.com/api",
                headers={"Accept": HostileHeaderValue("application/json")},
                params={},
                body={},
                body_bytes=None,
            )
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow request headers must contain exact string keys and values"
    assert "HostileHeaderValue" not in diagnostic
    assert "servicenow-header-value-title-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_rejects_body_bytes_subclass_before_opening() -> None:
    class HostileRequestBodyBytes(bytes):
        def __bytes__(self) -> bytes:
            raise AssertionError("client_secret=servicenow-body-bytes-secret")

    def fake_build_opener(*_handlers: object) -> FakeUrlOpener:
        raise AssertionError("transport should reject malformed body bytes before opening")

    with (
        patch("urllib.request.build_opener", fake_build_opener),
        pytest.raises(ServiceNowApiError) as exc,
    ):
        UrllibTransport().send(
            HttpRequest.model_construct(
                method="POST",
                url="https://example.service-now.com/api/now/attachment/file",
                headers={"Content-Type": "application/xml"},
                params={},
                body={},
                body_bytes=HostileRequestBodyBytes(b"<unload/>"),
            )
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow request body bytes must be exact bytes"
    assert "HostileRequestBodyBytes" not in diagnostic
    assert "servicenow-body-bytes-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_handles_request_without_params_or_body() -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponse:
        captured["full_url"] = request.full_url
        captured["data"] = request.data
        return FakeUrlResponse()

    with _patch_urllib_transport_opener(fake_urlopen):
        UrllibTransport().send(HttpRequest(method="GET", url="https://example.service-now.com/api"))

    assert captured["full_url"] == "https://example.service-now.com/api"
    assert captured["data"] is None


def test_urllib_transport_installs_no_redirect_handler() -> None:
    captured_handlers: list[object] = []

    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponse:
        assert request.full_url == "https://example.service-now.com/api"
        assert timeout == 30
        return FakeUrlResponse()

    def fake_build_opener(*handlers: object) -> FakeUrlOpener:
        captured_handlers.extend(handlers)
        return FakeUrlOpener(fake_urlopen)

    with patch("urllib.request.build_opener", fake_build_opener):
        response = UrllibTransport().send(
            HttpRequest(method="GET", url="https://example.service-now.com/api")
        )

    assert response == HttpResponse(status_code=200, json_body={"result": []})
    assert [handler.__class__.__name__ for handler in captured_handlers] == [
        "_NoServiceNowRedirectHandler"
    ]


def test_urllib_transport_blocks_redirect_before_following() -> None:
    handler = UrllibTransport().redirect_handler

    with pytest.raises(ServiceNowApiError, match="ServiceNow API redirects are not allowed"):
        handler.redirect_request(
            req=Request("https://example.service-now.com/api/now/table/rm_story"),
            fp=BytesIO(),
            code=302,
            msg="Found",
            headers=HTTPMessage(),
            newurl="https://evil.example/api",
        )


def test_urllib_transport_rejects_oversized_success_response_body() -> None:
    oversized_body = b'{"result":"' + (b"x" * (10 * 1024 * 1024 + 1)) + b'"}'

    def fake_urlopen(request: Any, timeout: int) -> FakeLargeUrlResponse:
        return FakeLargeUrlResponse(oversized_body)

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError, match="exceeded 10485760 bytes"),
    ):
        UrllibTransport().send(HttpRequest(method="GET", url="https://example.service-now.com/api"))


def test_urllib_transport_rejects_invalid_utf8_success_response_without_body_leak() -> None:
    def fake_urlopen(request: Any, timeout: int) -> FakeLargeUrlResponse:
        return FakeLargeUrlResponse(b'{"access_token":"\xff"}')

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="GET", url="https://example.service-now.com/oauth_token.do")
        )

    diagnostic = str(exc_info.value)
    assert "ServiceNow API response body is not valid UTF-8 JSON" in diagnostic
    assert "access_token" not in diagnostic
    assert exc_info.value.__cause__ is None


def test_urllib_transport_rejects_malformed_success_json_without_body_leak() -> None:
    def fake_urlopen(request: Any, timeout: int) -> FakeLargeUrlResponse:
        return FakeLargeUrlResponse(b'{"client_secret":"transport-secret"')

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="GET", url="https://example.service-now.com/oauth_token.do")
        )

    diagnostic = str(exc_info.value)
    assert "ServiceNow API response body is not valid JSON" in diagnostic
    assert "client_secret" not in diagnostic
    assert "transport-secret" not in diagnostic
    assert exc_info.value.__cause__ is None


def test_urllib_transport_rejects_non_finite_success_json_without_body_leak() -> None:
    def fake_urlopen(request: Any, timeout: int) -> FakeLargeUrlResponse:
        return FakeLargeUrlResponse(
            b'{"result":{"score":NaN,"client_secret":"transport-secret"}}'
        )

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="GET", url="https://example.service-now.com/oauth_token.do")
        )

    diagnostic = str(exc_info.value)
    assert "ServiceNow API response body is not valid JSON" in diagnostic
    assert "score" not in diagnostic
    assert "NaN" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "transport-secret" not in diagnostic
    assert exc_info.value.__cause__ is None


def test_urllib_transport_rejects_success_body_bytes_subclass_before_decode() -> None:
    class HostileResponseBody(bytes):
        def decode(self, encoding: str = "utf-8", errors: str = "strict") -> str:
            raise AssertionError("client_secret=servicenow-success-body-decode-secret")

    class FakeSubclassBodyResponse(FakeLargeUrlResponse):
        def read(self, n: int = -1) -> bytes:
            return self._body

    def fake_urlopen(request: Any, timeout: int) -> FakeSubclassBodyResponse:
        return FakeSubclassBodyResponse(HostileResponseBody(b'{"result": []}'))

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="GET", url="https://example.service-now.com/api")
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "ServiceNow transport response body must be exact bytes"
    assert "HostileResponseBody" not in diagnostic
    assert "servicenow-success-body-decode-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_wraps_success_context_enter_error_without_leak() -> None:
    class HostileEnterResponse(FakeUrlResponseWithStatus):
        def __enter__(self) -> "HostileEnterResponse":
            raise AssertionError("client_secret=servicenow-success-enter-secret")

    def fake_urlopen(request: Any, timeout: int) -> HostileEnterResponse:
        return HostileEnterResponse(status=200)

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="GET", url="https://example.service-now.com/api")
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "ServiceNow transport response context failed"
    assert "HostileEnterResponse" not in diagnostic
    assert "servicenow-success-enter-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_wraps_success_context_exit_error_without_leak() -> None:
    class HostileExitResponse(FakeUrlResponseWithStatus):
        def __exit__(self, *_args: object) -> None:
            raise AssertionError("client_secret=servicenow-success-exit-secret")

    def fake_urlopen(request: Any, timeout: int) -> HostileExitResponse:
        return HostileExitResponse(status=200)

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="GET", url="https://example.service-now.com/api")
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "ServiceNow transport response context failed"
    assert "HostileExitResponse" not in diagnostic
    assert "servicenow-success-exit-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_wraps_success_body_read_error_without_leak() -> None:
    class FakeFailingReadResponse(FakeUrlResponseWithStatus):
        def read(self, n: int = -1) -> bytes:
            raise OSError("client_secret=servicenow-success-body-read-error-secret")

    def fake_urlopen(request: Any, timeout: int) -> FakeFailingReadResponse:
        return FakeFailingReadResponse(status=200)

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="GET", url="https://example.service-now.com/api")
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "ServiceNow transport response body read failed"
    assert "servicenow-success-body-read-error-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_rejects_success_status_int_subclass_without_leak() -> None:
    class HostileResponseStatus(int):
        def __lt__(self, other: object) -> bool:
            raise AssertionError("client_secret=servicenow-success-status-lt-secret")

    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponseWithStatus:
        return FakeUrlResponseWithStatus(status=HostileResponseStatus(200))

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="GET", url="https://example.service-now.com/api")
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "ServiceNow transport response status must be an exact HTTP status code"
    assert "HostileResponseStatus" not in diagnostic
    assert "servicenow-success-status-lt-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_rejects_success_status_before_body_read() -> None:
    class HostileResponseStatus(int):
        pass

    class FakeUnreadableBodyResponse(FakeUrlResponseWithStatus):
        def read(self, n: int = -1) -> bytes:
            raise AssertionError("client_secret=servicenow-success-body-read-secret")

    def fake_urlopen(request: Any, timeout: int) -> FakeUnreadableBodyResponse:
        return FakeUnreadableBodyResponse(status=HostileResponseStatus(200))

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="GET", url="https://example.service-now.com/api")
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "ServiceNow transport response status must be an exact HTTP status code"
    assert "servicenow-success-body-read-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_rejects_success_status_attribute_error_without_leak() -> None:
    class HostileStatusAttributeResponse(FakeUrlResponse):
        @property
        def status(self) -> int:  # type: ignore[override]
            raise AssertionError("client_secret=servicenow-success-status-attr-secret")

        def read(self, n: int = -1) -> bytes:
            raise AssertionError("transport should reject malformed status before body read")

    def fake_urlopen(request: Any, timeout: int) -> HostileStatusAttributeResponse:
        return HostileStatusAttributeResponse()

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="GET", url="https://example.service-now.com/api")
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "ServiceNow transport response status must be an exact HTTP status code"
    assert "HostileStatusAttributeResponse" not in diagnostic
    assert "servicenow-success-status-attr-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_returns_json_body_for_http_error_response() -> None:
    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponse:
        raise FakeHttpError(
            code=429,
            body=b'{"error":{"message":"quota exceeded","type":"insufficient_quota"}}',
        )

    with _patch_urllib_transport_opener(fake_urlopen):
        response = UrllibTransport().send(
            HttpRequest(method="POST", url="https://api.openai.com/v1/responses")
        )

    assert response == HttpResponse(
        status_code=429,
        json_body={
            "error": {
                "message": "quota exceeded",
                "type": "insufficient_quota",
            }
        },
    )


def test_urllib_transport_rejects_http_error_body_bytes_subclass_before_parse() -> None:
    class HostileHttpErrorBody(bytes):
        def decode(self, encoding: str = "utf-8", errors: str = "strict") -> str:
            raise AssertionError("client_secret=servicenow-error-body-decode-secret")

    class FakeSubclassBodyHttpError(FakeHttpError):
        def read(self, n: int = -1) -> bytes:
            return self._body

    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponse:
        raise FakeSubclassBodyHttpError(
            code=502,
            body=HostileHttpErrorBody(b'{"error":{"message":"bad gateway"}}'),
        )

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="POST", url="https://api.openai.com/v1/responses")
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "ServiceNow transport response body must be exact bytes"
    assert "HostileHttpErrorBody" not in diagnostic
    assert "servicenow-error-body-decode-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_wraps_http_error_body_read_error_without_leak() -> None:
    class FakeFailingReadHttpError(FakeHttpError):
        def read(self, n: int = -1) -> bytes:
            raise OSError("client_secret=servicenow-error-body-read-error-secret")

    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponse:
        raise FakeFailingReadHttpError(
            code=502,
            body=b'{"error":{"message":"bad gateway"}}',
        )

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="POST", url="https://api.openai.com/v1/responses")
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "ServiceNow transport response body read failed"
    assert "servicenow-error-body-read-error-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_rejects_http_error_code_int_subclass_without_leak() -> None:
    class HostileHttpErrorCode(int):
        def __gt__(self, other: object) -> bool:
            raise AssertionError("client_secret=servicenow-http-error-code-gt-secret")

    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponse:
        raise FakeHttpError(
            code=HostileHttpErrorCode(502),
            body=b'{"error":{"message":"bad gateway"}}',
        )

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="POST", url="https://api.openai.com/v1/responses")
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "ServiceNow transport response status must be an exact HTTP status code"
    assert "HostileHttpErrorCode" not in diagnostic
    assert "servicenow-http-error-code-gt-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_rejects_http_error_code_before_body_read() -> None:
    class HostileHttpErrorCode(int):
        pass

    class FakeUnreadableBodyHttpError(FakeHttpError):
        def read(self, n: int = -1) -> bytes:
            raise AssertionError("client_secret=servicenow-error-body-read-secret")

    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponse:
        raise FakeUnreadableBodyHttpError(
            code=HostileHttpErrorCode(502),
            body=b'{"error":{"message":"bad gateway"}}',
        )

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="POST", url="https://api.openai.com/v1/responses")
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "ServiceNow transport response status must be an exact HTTP status code"
    assert "servicenow-error-body-read-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_rejects_http_error_code_attribute_error_without_leak() -> None:
    class HostileCodeAttributeHttpError(FakeHttpError):
        def __getattribute__(self, name: str) -> Any:
            if name == "code":
                raise AssertionError("client_secret=servicenow-http-error-code-attr-secret")
            return super().__getattribute__(name)

        def read(self, n: int = -1) -> bytes:
            raise AssertionError("transport should reject malformed code before body read")

    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponse:
        raise HostileCodeAttributeHttpError(
            code=502,
            body=b'{"error":{"message":"bad gateway"}}',
        )

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="POST", url="https://api.openai.com/v1/responses")
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "ServiceNow transport response status must be an exact HTTP status code"
    assert "HostileCodeAttributeHttpError" not in diagnostic
    assert "servicenow-http-error-code-attr-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_rejects_non_finite_http_error_json_without_body_leak() -> None:
    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponse:
        raise FakeHttpError(
            code=502,
            body=b'{"error":{"message":NaN,"client_secret":"transport-secret"}}',
        )

    with _patch_urllib_transport_opener(fake_urlopen):
        response = UrllibTransport().send(
            HttpRequest(method="POST", url="https://api.openai.com/v1/responses")
        )

    assert response.status_code == 502
    assert response.json_body == {
        "error": {"message": "ServiceNow API error response body is not valid JSON"}
    }
    diagnostic = repr(response.json_body)
    assert "NaN" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "transport-secret" not in diagnostic


def test_urllib_transport_preserves_non_json_http_error_body() -> None:
    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponse:
        raise FakeHttpError(code=502, body=b"Bad gateway")

    with _patch_urllib_transport_opener(fake_urlopen):
        response = UrllibTransport().send(
            HttpRequest(method="POST", url="https://api.openai.com/v1/responses")
        )

    assert response == HttpResponse(
        status_code=502,
        json_body={"error": {"message": "Bad gateway"}},
    )


def test_urllib_transport_wraps_url_error_without_reason_leak() -> None:
    class HostileUrlErrorReason(Exception):
        def __str__(self) -> str:
            raise AssertionError("client_secret=servicenow-url-error-reason-secret")

    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponse:
        raise urllib.error.URLError(HostileUrlErrorReason())

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="POST", url="https://api.openai.com/v1/responses")
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "ServiceNow transport request failed"
    assert "HostileUrlErrorReason" not in diagnostic
    assert "servicenow-url-error-reason-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_wraps_os_error_without_reason_leak() -> None:
    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponse:
        raise OSError("client_secret=servicenow-os-error-secret")

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="POST", url="https://api.openai.com/v1/responses")
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "ServiceNow transport request failed"
    assert "servicenow-os-error-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_wraps_unexpected_open_error_without_leak() -> None:
    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponse:
        raise RuntimeError("client_secret=servicenow-open-runtime-secret")

    with (
        _patch_urllib_transport_opener(fake_urlopen),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="POST", url="https://api.openai.com/v1/responses")
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "ServiceNow transport request failed"
    assert "servicenow-open-runtime-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_wraps_open_attribute_error_without_leak() -> None:
    class HostileOpenAttributeOpener:
        def __getattribute__(self, name: str) -> Any:
            if name == "open":
                raise RuntimeError("client_secret=servicenow-open-attr-secret")
            return super().__getattribute__(name)

    def fake_build_opener(*_handlers: object) -> HostileOpenAttributeOpener:
        return HostileOpenAttributeOpener()

    with (
        patch("urllib.request.build_opener", fake_build_opener),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="POST", url="https://api.openai.com/v1/responses")
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "ServiceNow transport request failed"
    assert "servicenow-open-attr-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_wraps_build_opener_error_without_leak() -> None:
    def fake_build_opener(*_handlers: object) -> FakeUrlOpener:
        raise RuntimeError("client_secret=servicenow-build-opener-secret")

    with (
        patch("urllib.request.build_opener", fake_build_opener),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="POST", url="https://api.openai.com/v1/responses")
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "ServiceNow transport request failed"
    assert "servicenow-build-opener-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_wraps_request_construction_error_without_leak() -> None:
    def fake_request(*_args: object, **_kwargs: object) -> Request:
        raise RuntimeError("client_secret=servicenow-request-construction-secret")

    with (
        patch("urllib.request.Request", fake_request),
        pytest.raises(ServiceNowApiError) as exc_info,
    ):
        UrllibTransport().send(
            HttpRequest(method="POST", url="https://api.openai.com/v1/responses")
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "ServiceNow transport request failed"
    assert "servicenow-request-construction-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_urllib_transport_truncates_large_non_json_http_error_body() -> None:
    raw_body = b"upstream failure " + (b"x" * 5000)

    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponse:
        raise FakeHttpError(code=502, body=raw_body)

    with _patch_urllib_transport_opener(fake_urlopen):
        response = UrllibTransport().send(
            HttpRequest(method="POST", url="https://api.openai.com/v1/responses")
        )

    message = response.json_body["error"]["message"]
    assert isinstance(message, str)
    assert len(message) < len(raw_body)
    assert message.endswith("...[truncated]")


def test_urllib_transport_truncates_large_json_http_error_strings() -> None:
    raw_body = json_bytes = (
        b'{"error":{"message":"' + (b"x" * 5000) + b'","type":"insufficient_quota"}}'
    )

    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponse:
        raise FakeHttpError(code=429, body=raw_body)

    with _patch_urllib_transport_opener(fake_urlopen):
        response = UrllibTransport().send(
            HttpRequest(method="POST", url="https://api.openai.com/v1/responses")
        )

    message = response.json_body["error"]["message"]
    assert isinstance(message, str)
    assert len(message) < len(json_bytes)
    assert message.endswith("...[truncated]")
    assert response.json_body["error"]["type"] == "insufficient_quota"


def test_bound_http_error_diagnostics_does_not_consume_all_fields_for_wide_payload() -> None:
    payload = {f"field_{index}": f"value-{index}" for index in range(150)}

    diagnostic = repr(_bound_http_error_diagnostics(payload))

    assert "'omitted_fields': 50" in diagnostic
    assert "field_149" not in diagnostic
    assert len(diagnostic) < MAX_HTTP_ERROR_DIAGNOSTIC_CHARS


def test_bound_http_error_diagnostics_rejects_dict_subclass_payloads() -> None:
    class HostileHttpErrorPayload(dict[str, Any]):
        def items(self) -> Any:
            raise AssertionError("client_secret=http-error-dict-subclass-secret")

    diagnostic = repr(
        _bound_http_error_diagnostics(
            {"error": HostileHttpErrorPayload({"message": "hidden diagnostic"})}
        )
    )

    assert "[non-json value]" in diagnostic
    assert "hidden diagnostic" not in diagnostic
    assert "dict-subclass-secret" not in diagnostic


def test_bound_http_error_diagnostics_rejects_string_subclass_values() -> None:
    class ExplodingHttpErrorText(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=http-error-diagnostic-str-secret")

    diagnostic = repr(
        _bound_http_error_diagnostics(
            {
                "error": {
                    "message": ExplodingHttpErrorText(
                        "client_secret=http-error-diagnostic-value-secret"
                    )
                }
            }
        )
    )

    assert "[non-json value]" in diagnostic
    assert "ExplodingHttpErrorText" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "http-error-diagnostic" not in diagnostic


def test_bound_http_error_diagnostics_normalizes_exact_string_values() -> None:
    diagnostic = _bound_http_error_diagnostics(
        {"error": {"message": "first line\nsecond line\tthird line"}}
    )

    assert isinstance(diagnostic, dict)
    error = diagnostic["error"]
    assert isinstance(error, dict)
    message = error["message"]
    assert message == "first line second line third line"
    assert "\n" not in message
    assert "\t" not in message


def test_bound_http_error_diagnostics_normalizes_exact_string_keys() -> None:
    diagnostic = _bound_http_error_diagnostics(
        {"error": {"first key\nsecond key\tthird key": "value"}}
    )

    assert isinstance(diagnostic, dict)
    error = diagnostic["error"]
    assert isinstance(error, dict)
    keys = list(error)
    assert keys == ["first key second key third key"]
    assert "\n" not in keys[0]
    assert "\t" not in keys[0]


def test_bound_http_error_diagnostics_rejects_non_json_keys() -> None:
    class ExplodingHttpErrorKey:
        def __hash__(self) -> int:
            return 1

        def __repr__(self) -> str:
            return "ExplodingHttpErrorKey(client_secret=http-error-key-secret)"

    diagnostic = repr(
        _bound_http_error_diagnostics(
            {
                "error": {
                    ExplodingHttpErrorKey(): "http-error-key-value",
                }
            }
        )
    )

    assert "[non-json key]" in diagnostic
    assert "ExplodingHttpErrorKey" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "http-error-key-secret" not in diagnostic
    assert "http-error-key-value" in diagnostic


def test_bound_http_error_diagnostics_normalizes_non_json_scalar_values() -> None:
    class ExplodingHttpErrorValue:
        def __repr__(self) -> str:
            return "ExplodingHttpErrorValue(client_secret=http-error-value-secret)"

    diagnostic = repr(
        _bound_http_error_diagnostics(
            {
                "error": {
                    "bad_object": ExplodingHttpErrorValue(),
                    "bad_float": float("nan"),
                    "none": None,
                    "bool": True,
                    "int": 7,
                    "float": 1.25,
                }
            }
        )
    )

    assert diagnostic.count("[non-json value]") == 2
    assert "ExplodingHttpErrorValue" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "http-error-value-secret" not in diagnostic
    assert "'none': None" in diagnostic
    assert "'bool': True" in diagnostic
    assert "'int': 7" in diagnostic
    assert "'float': 1.25" in diagnostic


def test_bound_http_error_diagnostics_handles_circular_payload() -> None:
    circular_payload: dict[str, Any] = {"message": "Bad gateway"}
    circular_payload["self"] = circular_payload

    diagnostic = repr(_bound_http_error_diagnostics({"error": circular_payload}))

    assert "[circular reference]" in diagnostic
    assert "Bad gateway" in diagnostic
    assert len(diagnostic) < MAX_HTTP_ERROR_DIAGNOSTIC_CHARS


def test_truncate_http_error_diagnostic_keeps_marker_inside_configured_cap() -> None:
    diagnostic = _truncate_http_error_diagnostic(
        "x" * (MAX_HTTP_ERROR_DIAGNOSTIC_CHARS + 1)
    )

    assert diagnostic.endswith(HTTP_ERROR_TRUNCATION_MARKER)
    assert len(diagnostic) == MAX_HTTP_ERROR_DIAGNOSTIC_CHARS


def test_bound_http_error_diagnostics_keeps_duplicate_keys_inside_cap() -> None:
    first_key = "x" * (MAX_HTTP_ERROR_DIAGNOSTIC_CHARS + 1)
    second_key = "x" * (MAX_HTTP_ERROR_DIAGNOSTIC_CHARS + 2)

    diagnostic = _bound_http_error_diagnostics(
        {"error": {first_key: "one", second_key: "two"}}
    )

    assert isinstance(diagnostic, dict)
    error = diagnostic["error"]
    assert isinstance(error, dict)
    keys = list(error)
    assert len(keys) == 2
    assert keys[0].endswith(HTTP_ERROR_TRUNCATION_MARKER)
    assert keys[1].endswith(" (2)")
    assert all(len(key) <= MAX_HTTP_ERROR_DIAGNOSTIC_CHARS for key in keys)
    assert list(error.values()) == ["one", "two"]


def test_bound_http_error_diagnostics_preserves_user_truncation_marker_key() -> None:
    payload: dict[str, Any] = {"__jedi_response_truncated__": "user marker"}
    payload.update({f"field_{index}": f"value-{index}" for index in range(101)})

    diagnostic = _bound_http_error_diagnostics(payload)

    assert isinstance(diagnostic, dict)
    assert diagnostic["__jedi_response_truncated__"] == "user marker"
    assert diagnostic["__jedi_response_truncated__ (2)"] == {
        "truncated": True,
        "omitted_fields": 2,
    }


def test_urllib_transport_bounds_oversized_http_error_response_body() -> None:
    oversized_body = b"upstream failure " + (b"x" * (10 * 1024 * 1024 + 1))
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: int) -> FakeUrlResponse:
        error = FakeHttpError(code=502, body=oversized_body)
        original_read = error.read

        def tracked_read(n: int = -1) -> bytes:
            captured["read_size"] = n
            return original_read(n)

        error.read = tracked_read  # type: ignore[method-assign]
        raise error

    with _patch_urllib_transport_opener(fake_urlopen):
        response = UrllibTransport().send(
            HttpRequest(method="POST", url="https://api.openai.com/v1/responses")
        )

    assert captured["read_size"] == 10 * 1024 * 1024 + 1
    assert response == HttpResponse(
        status_code=502,
        json_body={
            "error": {"message": "ServiceNow API error response body exceeded 10485760 bytes"}
        },
    )


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


def test_oauth_client_credentials_rejects_response_object_without_leak() -> None:
    class HostileResponse:
        @property
        def status_code(self) -> int:
            raise AssertionError("client_secret=oauth-response-object-secret")

    auth = OAuthClientCredentials(
        instance_url="https://dev205693.service-now.com",
        client_id="client-id",
        client_secret="client-secret",
        transport=HostileTransport(HostileResponse()),
    )

    with pytest.raises(ServiceNowApiError) as exc:
        auth.authorization_header()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow OAuth response must be an exact HttpResponse"
    assert "HostileResponse" not in diagnostic
    assert "oauth-response-object-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_oauth_client_credentials_rejects_status_code_object_without_leak() -> None:
    class HostileStatusCode:
        def __ge__(self, other: object) -> bool:
            raise AssertionError("client_secret=oauth-status-code-secret")

    transport = RecordingTransport(
        [
            HttpResponse.model_construct(
                status_code=HostileStatusCode(),
                json_body={"access_token": "token-123"},
            )
        ]
    )
    auth = OAuthClientCredentials(
        instance_url="https://dev205693.service-now.com",
        client_id="client-id",
        client_secret="client-secret",
        transport=transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        auth.authorization_header()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow OAuth response status code must be an exact integer"
    assert "HostileStatusCode" not in diagnostic
    assert "oauth-status-code-secret" not in diagnostic
    assert "client_secret" not in diagnostic


@pytest.mark.parametrize("status_code", [99, 600])
def test_oauth_client_credentials_rejects_status_code_outside_http_range(
    status_code: int,
) -> None:
    transport = RecordingTransport(
        [HttpResponse(status_code=status_code, json_body={"access_token": "token-123"})]
    )
    auth = OAuthClientCredentials(
        instance_url="https://dev205693.service-now.com",
        client_id="client-id",
        client_secret="client-secret",
        transport=transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        auth.authorization_header()

    assert str(exc.value) == "ServiceNow OAuth response status code must be in the HTTP range"


def test_oauth_client_credentials_rejects_json_body_object_without_leak() -> None:
    class HostileJsonBody:
        def get(self, key: object, default: object | None = None) -> object:
            raise AssertionError("client_secret=oauth-json-body-secret")

    transport = RecordingTransport(
        [
            HttpResponse.model_construct(
                status_code=200,
                json_body=HostileJsonBody(),
            )
        ]
    )
    auth = OAuthClientCredentials(
        instance_url="https://dev205693.service-now.com",
        client_id="client-id",
        client_secret="client-secret",
        transport=transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        auth.authorization_header()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow OAuth response body must be an exact dictionary"
    assert "HostileJsonBody" not in diagnostic
    assert "oauth-json-body-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_oauth_client_credentials_rejects_json_body_dict_subclass_without_leak() -> None:
    class HostileJsonBody(dict[str, object]):
        def get(self, key: object, default: object | None = None) -> object:
            raise AssertionError("client_secret=oauth-json-dict-secret")

    transport = RecordingTransport(
        [
            HttpResponse.model_construct(
                status_code=200,
                json_body=HostileJsonBody(access_token="token-123"),
            )
        ]
    )
    auth = OAuthClientCredentials(
        instance_url="https://dev205693.service-now.com",
        client_id="client-id",
        client_secret="client-secret",
        transport=transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        auth.authorization_header()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow OAuth response body must be an exact dictionary"
    assert "HostileJsonBody" not in diagnostic
    assert "oauth-json-dict-secret" not in diagnostic
    assert "client_secret" not in diagnostic


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


@pytest.mark.parametrize(
    "access_token",
    [
        "tokén-123",
        " token-123",
        "token-123 ",
        "token\t123",
    ],
)
def test_oauth_client_credentials_rejects_malformed_access_token(
    access_token: str,
) -> None:
    transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": access_token})]
    )
    auth = OAuthClientCredentials(
        instance_url="https://dev205693.service-now.com",
        client_id="client-id",
        client_secret="client-secret",
        transport=transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        auth.authorization_header()

    assert "access_token" in str(exc.value)


def test_oauth_client_credentials_rejects_oversized_access_token_without_caching() -> None:
    oversized_access_token = "a" * 8193
    transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": oversized_access_token})]
    )
    auth = OAuthClientCredentials(
        instance_url="https://dev205693.service-now.com",
        client_id="client-id",
        client_secret="client-secret",
        transport=transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        auth.authorization_header()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow OAuth response did not include access_token"
    assert oversized_access_token not in diagnostic


def test_oauth_client_credentials_rejects_access_token_str_subclass_without_caching() -> (
    None
):
    transport = RecordingTransport(
        [
            HttpResponse(
                status_code=200,
                json_body={
                    "access_token": ExplodingServiceNowAccessToken("token-123")
                },
            )
        ]
    )
    auth = OAuthClientCredentials(
        instance_url="https://dev205693.service-now.com",
        client_id="client-id",
        client_secret="client-secret",
        transport=transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        auth.authorization_header()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow OAuth response did not include access_token"
    assert "Bearer" not in diagnostic
    assert "ExplodingServiceNowAccessToken" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-access-token-strip-secret" not in diagnostic


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


def test_servicenow_client_rejects_unsafe_ready_story_project_id_before_request() -> None:
    transport = RecordingTransport([])
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
        client.fetch_ready_stories(
            project_sys_id="project-123^state=Draft^client_secret=project-secret",
            limit=5,
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_RECORD_ID_UNSAFE_DIAGNOSTIC
    assert "client_secret" not in diagnostic
    assert "project-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_hostile_ready_story_project_id_before_truthiness() -> None:
    transport = RecordingTransport([])
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
        client.fetch_ready_stories(
            project_sys_id=cast(str, SecretBearingServiceNowProjectId()),
            limit=5,
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_RECORD_ID_UNSAFE_DIAGNOSTIC
    assert "SecretBearingServiceNowProjectId" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-project-id-secret" not in diagnostic
    assert transport.requests == []


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


def test_servicenow_client_rejects_non_positive_story_limit_before_request() -> None:
    transport = RecordingTransport([])
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
        client.fetch_stories(sysparm_query="number=STRY0010013", limit=0)

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_RESULT_LIMIT_UNSAFE_DIAGNOSTIC
    assert "STRY0010013" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_non_integer_story_limit_before_request() -> None:
    transport = RecordingTransport([])
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
        client.fetch_stories(
            sysparm_query="number=STRY0010013",
            limit=cast(int, SecretBearingServiceNowResultLimit()),
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_RESULT_LIMIT_UNSAFE_DIAGNOSTIC
    assert "SecretBearingServiceNowResultLimit" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-limit-secret" not in diagnostic
    assert "STRY0010013" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_unsafe_story_query_before_request() -> None:
    transport = RecordingTransport([])
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
        client.fetch_stories(
            sysparm_query=cast(str, SecretBearingServiceNowStoryQuery()),
            limit=1,
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_STORY_QUERY_UNSAFE_DIAGNOSTIC
    assert "SecretBearingServiceNowStoryQuery" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-story-query-secret" not in diagnostic
    assert transport.requests == []


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


def test_servicenow_client_maps_decimal_story_points_to_validated_stories() -> None:
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
                            "story_points": "2.5",
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

    assert stories[0].story_points == 2.5


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


def test_servicenow_client_rejects_non_string_story_response_text_without_stringifying() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "sys_id": "abc123",
                            "number": SecretBearingServiceNowStoryField(),
                            "short_description": "Add AI Review Notes",
                            "description": "Add field to form.",
                            "story_points": "3",
                            "priority": "4",
                            "state": "-7",
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_stories(sysparm_query="number=STRY0010013", limit=1)

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API story response field is unsafe"
    assert "SecretBearingServiceNowStoryField" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-story-field-secret" not in diagnostic


def test_servicenow_client_rejects_story_response_text_str_subclass() -> None:
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
                            "acceptance_criteria": ExplodingServiceNowStoryText(
                                "Given a story, then it is reviewed."
                            ),
                            "story_points": "3",
                            "priority": "4",
                            "state": "-7",
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_stories(sysparm_query="number=STRY0010013", limit=1)

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API story response field is unsafe"
    assert "ExplodingServiceNowStoryText" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-story-text-strip-secret" not in diagnostic


def test_servicenow_client_rejects_oversized_story_additional_context() -> None:
    oversized_context = "a" * 1025
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
                            "u_ai_build_reference": oversized_context,
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_stories(sysparm_query="number=STRY0010013", limit=1)

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API story response field is unsafe"
    assert oversized_context not in diagnostic
    assert transport.requests[1].method == "GET"


def test_servicenow_client_rejects_non_numeric_story_points_without_stringifying() -> (
    None
):
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
                            "story_points": SecretBearingServiceNowStoryField(),
                            "priority": "4",
                            "state": "-7",
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_stories(sysparm_query="number=STRY0010013", limit=1)

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API story response field is unsafe"
    assert "SecretBearingServiceNowStoryField" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-story-field-secret" not in diagnostic


def test_servicenow_client_rejects_story_points_float_subclass_without_comparing() -> (
    None
):
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
                            "story_points": ExplodingServiceNowStoryPointsFloat(3.0),
                            "priority": "4",
                            "state": "-7",
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_stories(sysparm_query="number=STRY0010013", limit=1)

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API story response field is unsafe"
    assert "ExplodingServiceNowStoryPointsFloat" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-story-points-float-secret" not in diagnostic


@pytest.mark.parametrize(
    "story_points_value",
    [False, "-1", "+1", " 3", "3 ", "٣", "nan", "inf", "3e1", "3.0.0"],
)
def test_servicenow_client_rejects_malformed_story_points_values(
    story_points_value: Any,
) -> None:
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
                            "story_points": story_points_value,
                            "priority": "4",
                            "state": "-7",
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_stories(sysparm_query="number=STRY0010013", limit=1)

    assert str(exc.value) == "ServiceNow API story response field is unsafe"


def test_servicenow_client_rejects_non_integer_story_priority_without_stringifying() -> (
    None
):
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
                            "priority": SecretBearingServiceNowStoryField(),
                            "state": "-7",
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_stories(sysparm_query="number=STRY0010013", limit=1)

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API story response field is unsafe"
    assert "SecretBearingServiceNowStoryField" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-story-field-secret" not in diagnostic


def test_servicenow_client_rejects_story_priority_int_subclass_before_validation() -> (
    None
):
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
                            "priority": ExplodingServiceNowStoryPriorityInt(4),
                            "state": "-7",
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_stories(sysparm_query="number=STRY0010013", limit=1)

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API story response field is unsafe"
    assert "ExplodingServiceNowStoryPriorityInt" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-story-priority-int-secret" not in diagnostic


@pytest.mark.parametrize("priority_value", [False, "-1", "+1", " 3", "3 ", "٣", "3.0"])
def test_servicenow_client_rejects_malformed_story_priority_values(
    priority_value: Any,
) -> None:
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
                            "priority": priority_value,
                            "state": "-7",
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_stories(sysparm_query="number=STRY0010013", limit=1)

    assert str(exc.value) == "ServiceNow API story response field is unsafe"


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


def test_servicenow_client_rejects_non_string_state_choice_response_text_without_stringifying() -> (
    None
):
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "label": SecretBearingServiceNowMetadataField(),
                            "value": "-7",
                            "sequence": "50",
                            "inactive": "false",
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_story_state_choices()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API metadata response field is unsafe"
    assert "SecretBearingServiceNowMetadataField" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-metadata-field-secret" not in diagnostic


def test_servicenow_client_rejects_metadata_text_str_subclass() -> None:
    subclass_label = SecretBearingServiceNowMetadataText("Ready for Testing")
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "label": subclass_label,
                            "value": "-7",
                            "sequence": "50",
                            "inactive": "false",
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_story_state_choices()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API metadata response field is unsafe"
    assert "SecretBearingServiceNowMetadataText" not in diagnostic
    assert "Ready for Testing" not in diagnostic


def test_servicenow_client_rejects_oversized_metadata_response_text() -> None:
    oversized_label = "a" * 1025
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "label": oversized_label,
                            "value": "-7",
                            "sequence": "50",
                            "inactive": "false",
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_story_state_choices()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API metadata response field is unsafe"
    assert oversized_label not in diagnostic
    assert transport.requests[1].method == "GET"


def test_servicenow_client_rejects_control_character_metadata_response_text() -> None:
    unsafe_label = "Ready\nTesting"
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "label": unsafe_label,
                            "value": "-7",
                            "sequence": "50",
                            "inactive": "false",
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_story_state_choices()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API metadata response field is unsafe"
    assert unsafe_label not in diagnostic
    assert transport.requests[1].method == "GET"


def test_servicenow_client_rejects_non_bool_state_choice_response_flag_without_stringifying() -> (
    None
):
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
                            "inactive": SecretBearingServiceNowMetadataField(),
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_story_state_choices()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API metadata response field is unsafe"
    assert "SecretBearingServiceNowMetadataField" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-metadata-field-secret" not in diagnostic


def test_servicenow_client_rejects_non_integer_state_choice_sequence_without_stringifying() -> (
    None
):
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
                            "sequence": SecretBearingServiceNowMetadataField(),
                            "inactive": "false",
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_story_state_choices()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API metadata response field is unsafe"
    assert "SecretBearingServiceNowMetadataField" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-metadata-field-secret" not in diagnostic


def test_servicenow_client_rejects_state_choice_sequence_str_subclass_without_methods() -> (
    None
):
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
                            "sequence": ExplodingServiceNowMetadataSequence("50"),
                            "inactive": "false",
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_story_state_choices()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API metadata response field is unsafe"
    assert "ExplodingServiceNowMetadataSequence" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-metadata-sequence-secret" not in diagnostic


def test_servicenow_client_rejects_state_choice_sequence_int_subclass_without_comparing() -> (
    None
):
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
                            "sequence": ExplodingServiceNowMetadataSequenceInt(50),
                            "inactive": "false",
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_story_state_choices()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API metadata response field is unsafe"
    assert "ExplodingServiceNowMetadataSequenceInt" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-metadata-sequence-int-secret" not in diagnostic


def test_servicenow_client_rejects_oversized_state_choice_sequence() -> None:
    oversized_sequence = "9" * 11
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
                            "sequence": oversized_sequence,
                            "inactive": "false",
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_story_state_choices()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API metadata response field is unsafe"
    assert oversized_sequence not in diagnostic
    assert transport.requests[1].method == "GET"


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
    assert request.params["sysparm_fields"] == (
        "element,column_label,internal_type,active,read_only"
    )
    assert fields == [
        StoryDictionaryField(
            element="u_ai_status",
            column_label="AI Status",
            internal_type="string",
            active=True,
        )
    ]


def test_servicenow_client_rejects_non_string_dictionary_response_text_without_stringifying() -> (
    None
):
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "element": SecretBearingServiceNowMetadataField(),
                            "column_label": "AI Status",
                            "internal_type": "string",
                            "active": "true",
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_story_dictionary_fields()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API metadata response field is unsafe"
    assert "SecretBearingServiceNowMetadataField" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-metadata-field-secret" not in diagnostic


def test_servicenow_client_rejects_non_bool_dictionary_response_flag_without_stringifying() -> (
    None
):
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
                            "active": SecretBearingServiceNowMetadataField(),
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_story_dictionary_fields()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API metadata response field is unsafe"
    assert "SecretBearingServiceNowMetadataField" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-metadata-field-secret" not in diagnostic


def test_servicenow_client_rejects_metadata_boolean_str_subclass_without_lowering() -> (
    None
):
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
                            "active": ExplodingServiceNowMetadataBoolean("true"),
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_story_dictionary_fields()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API metadata response field is unsafe"
    assert "ExplodingServiceNowMetadataBoolean" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-metadata-boolean-secret" not in diagnostic


def test_servicenow_client_rejects_padded_metadata_boolean_response_flag() -> None:
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
                            "active": " true ",
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_story_dictionary_fields()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API metadata response field is unsafe"
    assert " true " not in diagnostic
    assert transport.requests[1].method == "GET"


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
        read_only=True,
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
        "read_only": "true",
    }
    assert "client-secret" not in repr(request.sanitized())


def test_servicenow_client_rejects_unsafe_story_dictionary_element_before_request() -> None:
    transport = RecordingTransport([])
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
        client.create_story_dictionary_field(
            element="u_ai_status,sys_created_by^client_secret=field-secret",
            column_label="AI Status",
            internal_type="string",
            max_length=80,
            read_only=True,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API field name is unsafe"
    assert "client_secret" not in diagnostic
    assert "field-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_unsafe_story_dictionary_internal_type_before_request() -> None:
    transport = RecordingTransport([])
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
        client.create_story_dictionary_field(
            element="u_ai_status",
            column_label="AI Status",
            internal_type="string\r\nclient_secret=type-secret",
            max_length=80,
            read_only=True,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow dictionary internal type is unsafe"
    assert "client_secret" not in diagnostic
    assert "type-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_non_string_story_dictionary_internal_type_before_request() -> (
    None
):
    transport = RecordingTransport([])
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
        client.create_story_dictionary_field(
            element="u_ai_status",
            column_label="AI Status",
            internal_type=cast(str, SecretBearingServiceNowDictionaryInternalType()),
            max_length=80,
            read_only=True,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow dictionary internal type is unsafe"
    assert "SecretBearingServiceNowDictionaryInternalType" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-internal-type-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_story_dictionary_internal_type_str_subclass() -> (
    None
):
    transport = RecordingTransport([])
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
        client.create_story_dictionary_field(
            element="u_ai_status",
            column_label="AI Status",
            internal_type=cast(str, ExplodingServiceNowDictionaryInternalType("string")),
            max_length=80,
            read_only=True,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow dictionary internal type is unsafe"
    assert "ExplodingServiceNowDictionaryInternalType" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-internal-type-strip-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_oversized_story_dictionary_internal_type_before_request() -> (
    None
):
    oversized_internal_type = "a" * 129
    transport = RecordingTransport([])
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
        client.create_story_dictionary_field(
            element="u_ai_status",
            column_label="AI Status",
            internal_type=oversized_internal_type,
            max_length=80,
            read_only=True,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow dictionary internal type is unsafe"
    assert oversized_internal_type not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_unsafe_story_dictionary_max_length_before_request() -> None:
    transport = RecordingTransport([])
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
        client.create_story_dictionary_field(
            element="u_ai_status",
            column_label="AI Status",
            internal_type="string",
            max_length=cast(Any, "80\r\nclient_secret=max-length-secret"),
            read_only=True,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow dictionary max length is unsafe"
    assert "client_secret" not in diagnostic
    assert "max-length-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_story_dictionary_max_length_int_subclass_before_request() -> (
    None
):
    class HostileDictionaryMaxLength(int):
        def __lt__(self, other: object) -> bool:
            raise AssertionError("client_secret=servicenow-max-length-lt-secret")

        def __str__(self) -> str:
            raise AssertionError("client_secret=servicenow-max-length-str-secret")

    transport = RecordingTransport([])
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
        client.create_story_dictionary_field(
            element="u_ai_status",
            column_label="AI Status",
            internal_type="string",
            max_length=cast(int, HostileDictionaryMaxLength(80)),
            read_only=True,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow dictionary max length is unsafe"
    assert "HostileDictionaryMaxLength" not in diagnostic
    assert "servicenow-max-length-lt-secret" not in diagnostic
    assert "servicenow-max-length-str-secret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_unsafe_story_dictionary_column_label_before_request() -> None:
    transport = RecordingTransport([])
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
        client.create_story_dictionary_field(
            element="u_ai_status",
            column_label="AI Status\r\nclient_secret=label-secret",
            internal_type="string",
            max_length=80,
            read_only=True,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow dictionary column label is unsafe"
    assert "client_secret" not in diagnostic
    assert "label-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_story_dictionary_column_label_str_subclass() -> None:
    transport = RecordingTransport([])
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
        client.create_story_dictionary_field(
            element="u_ai_status",
            column_label=cast(str, ExplodingServiceNowDictionaryColumnLabel("AI Status")),
            internal_type="string",
            max_length=80,
            read_only=True,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow dictionary column label is unsafe"
    assert "ExplodingServiceNowDictionaryColumnLabel" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-column-label-strip-secret" not in diagnostic
    assert transport.requests == []


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


def test_servicenow_client_rejects_unsafe_story_patch_field_before_request() -> None:
    transport = RecordingTransport([])
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
        client.update_story_fields(
            "story-sys-id",
            {
                "u_ai_status,work_notes^client_secret=patch-secret": "Ready for Testing",
            },
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API field name is unsafe"
    assert "client_secret" not in diagnostic
    assert "patch-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_non_string_story_patch_field_before_request() -> None:
    transport = RecordingTransport([])
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

    fields = cast(
        dict[str, Any],
        {
            SecretBearingServiceNowFieldName(): "Ready for Testing",
        },
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.update_story_fields("story-sys-id", fields)

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API field name is unsafe"
    assert "SecretBearingServiceNowFieldName" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-field-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_story_patch_field_body_dict_subclass_before_request() -> None:
    class HostileFieldBody(dict[str, object]):
        def items(self) -> Iterator[tuple[str, object]]:  # type: ignore[override]
            raise AssertionError("client_secret=servicenow-field-body-secret")

    transport = RecordingTransport([])
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
        client.update_story_fields(
            "story-sys-id",
            cast(dict[str, Any], HostileFieldBody(u_ai_status="Ready for Testing")),
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API field body must be an exact dictionary"
    assert "HostileFieldBody" not in diagnostic
    assert "servicenow-field-body-secret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_story_patch_field_str_subclass_without_methods() -> (
    None
):
    transport = RecordingTransport([])
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
    fields = cast(
        dict[str, Any],
        {
            ExplodingServiceNowFieldName("u_ai_status"): "Ready for Testing",
        },
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.update_story_fields("story-sys-id", fields)

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API field name is unsafe"
    assert "ExplodingServiceNowFieldName" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-field-name-strip-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_unsafe_story_record_id_before_request() -> None:
    transport = RecordingTransport([])
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
        client.update_story_fields(
            "story-sys-id/../../rm_story?client_secret=sysid-secret",
            {"u_ai_status": "Ready for Testing"},
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_RECORD_ID_UNSAFE_DIAGNOSTIC
    assert "client_secret" not in diagnostic
    assert "sysid-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_non_string_story_record_id_before_request() -> None:
    transport = RecordingTransport([])
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
        client.update_story_fields(
            cast(str, SecretBearingServiceNowSysId()),
            {"u_ai_status": "Ready for Testing"},
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_RECORD_ID_UNSAFE_DIAGNOSTIC
    assert "SecretBearingServiceNowSysId" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-sys-id-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_story_record_id_str_subclass_without_methods() -> None:
    transport = RecordingTransport([])
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
        client.update_story_fields(
            cast(str, ExplodingServiceNowSysId("story-sys-id")),
            {"u_ai_status": "Ready for Testing"},
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_RECORD_ID_UNSAFE_DIAGNOSTIC
    assert "ExplodingServiceNowSysId" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-sys-id-strip-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_oversized_story_record_id_before_request() -> None:
    oversized_sys_id = "a" * 129
    transport = RecordingTransport([])
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
        client.update_story_fields(
            oversized_sys_id,
            {"u_ai_status": "Ready for Testing"},
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_RECORD_ID_UNSAFE_DIAGNOSTIC
    assert oversized_sys_id not in diagnostic
    assert transport.requests == []


def test_servicenow_client_upserts_table_record_with_lookup_query() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(status_code=200, json_body={"result": []}),
            HttpResponse(
                status_code=201,
                json_body={"result": {"sys_id": "rest-message-sys-id"}},
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

    result = client.upsert_table_record(
        table="sys_rest_message",
        lookup={"name": "Jedi DevProject Lifecycle Event API"},
        fields={
            "name": "Jedi DevProject Lifecycle Event API",
            "endpoint": "https://sidecar.example.gov/lifecycle/events",
        },
    )

    lookup_request = transport.requests[1]
    create_request = transport.requests[2]
    assert result == {"sys_id": "rest-message-sys-id"}
    assert lookup_request.method == "GET"
    assert lookup_request.url.endswith("/api/now/table/sys_rest_message")
    assert lookup_request.params["sysparm_query"] == ("name=Jedi DevProject Lifecycle Event API")
    assert lookup_request.params["sysparm_limit"] == "1"
    assert create_request.method == "POST"
    assert create_request.url.endswith("/api/now/table/sys_rest_message")
    assert create_request.body["endpoint"] == "https://sidecar.example.gov/lifecycle/events"
    assert "client-secret" not in repr(create_request.sanitized())


def test_servicenow_client_rejects_upsert_field_body_dict_subclass_before_lookup() -> None:
    class HostileFieldBody(dict[str, object]):
        def items(self) -> Iterator[tuple[str, object]]:  # type: ignore[override]
            raise AssertionError("client_secret=servicenow-upsert-field-body-secret")

    transport = RecordingTransport([])
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
        client.upsert_table_record(
            table="sys_script",
            lookup={"name": "Jedi DevProject lifecycle event emitter"},
            fields=cast(dict[str, Any], HostileFieldBody(script="answer = true;")),
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API field body must be an exact dictionary"
    assert "HostileFieldBody" not in diagnostic
    assert "servicenow-upsert-field-body-secret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_upsert_updates_existing_table_record() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={"result": [{"sys_id": "script-sys-id"}]},
            ),
            HttpResponse(
                status_code=200,
                json_body={"result": {"sys_id": "script-sys-id"}},
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

    client.upsert_table_record(
        table="sys_script",
        lookup={
            "name": "Jedi DevProject lifecycle event emitter",
            "collection": "rm_story",
        },
        fields={"active": True, "when": "after"},
    )

    update_request = transport.requests[2]
    assert update_request.method == "PATCH"
    assert update_request.url.endswith("/api/now/table/sys_script/script-sys-id")
    assert update_request.body == {"active": True, "when": "after"}


def test_servicenow_client_rejects_unsafe_upsert_field_before_lookup_request() -> None:
    transport = RecordingTransport([])
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
        client.upsert_table_record(
            table="sys_script",
            lookup={
                "name": "Jedi DevProject lifecycle event emitter",
                "collection": "rm_story",
            },
            fields={
                "active,when^client_secret=upsert-secret": True,
            },
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API field name is unsafe"
    assert "client_secret" not in diagnostic
    assert "upsert-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_upsert_rejects_non_json_existing_record_sys_id() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={"result": [{"sys_id": SecretBearingServiceNowSysId()}]},
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.upsert_table_record(
            table="sys_script",
            lookup={
                "name": "Jedi DevProject lifecycle event emitter",
                "collection": "rm_story",
            },
            fields={"active": True, "when": "after"},
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_LOOKUP_NON_JSON_DIAGNOSTIC
    assert "SecretBearingServiceNowSysId" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-sys-id-secret" not in diagnostic
    assert [request.method for request in transport.requests] == ["POST", "GET"]


def test_servicenow_client_upsert_rejects_existing_record_sys_id_str_subclass() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {"sys_id": ExplodingServiceNowLookupResponseText("script-sys-id")}
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.upsert_table_record(
            table="sys_script",
            lookup={
                "name": "Jedi DevProject lifecycle event emitter",
                "collection": "rm_story",
            },
            fields={"active": True, "when": "after"},
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_LOOKUP_NON_JSON_DIAGNOSTIC
    assert "ExplodingServiceNowLookupResponseText" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-lookup-response-text-secret" not in diagnostic
    assert [request.method for request in transport.requests] == ["POST", "GET"]


def test_servicenow_client_upsert_rejects_existing_record_sys_id_int_subclass() -> None:
    class HostileLookupResponseInt(int):
        def __str__(self) -> str:
            raise AssertionError("client_secret=servicenow-lookup-response-int-secret")

    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={"result": [{"sys_id": HostileLookupResponseInt(123)}]},
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.upsert_table_record(
            table="sys_script",
            lookup={
                "name": "Jedi DevProject lifecycle event emitter",
                "collection": "rm_story",
            },
            fields={"active": True, "when": "after"},
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_LOOKUP_NON_JSON_DIAGNOSTIC
    assert "HostileLookupResponseInt" not in diagnostic
    assert "servicenow-lookup-response-int-secret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert [request.method for request in transport.requests] == ["POST", "GET"]


def test_servicenow_client_rejects_unsafe_lookup_query_before_request() -> None:
    transport = RecordingTransport([])
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
        client.fetch_table_record(
            table="sys_script",
            lookup={"name": "safe-name^client_secret=query-secret"},
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_LOOKUP_QUERY_UNSAFE_DIAGNOSTIC
    assert "client_secret" not in diagnostic
    assert "query-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_lookup_dict_subclass_before_request() -> None:
    class HostileLookup(dict[str, str]):
        def items(self) -> Iterator[tuple[str, str]]:  # type: ignore[override]
            raise AssertionError("client_secret=servicenow-lookup-body-secret")

    transport = RecordingTransport([])
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
        client.fetch_table_record(
            table="sys_script",
            lookup=cast(dict[str, str], HostileLookup(name="safe-name")),
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API lookup body must be an exact dictionary"
    assert "HostileLookup" not in diagnostic
    assert "servicenow-lookup-body-secret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_upsert_lookup_dict_subclass_before_lookup() -> None:
    class HostileLookup(dict[str, str]):
        def items(self) -> Iterator[tuple[str, str]]:  # type: ignore[override]
            raise AssertionError("client_secret=servicenow-upsert-lookup-body-secret")

    transport = RecordingTransport([])
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
        client.upsert_table_record(
            table="sys_script",
            lookup=cast(dict[str, str], HostileLookup(name="safe-name")),
            fields={"script": "answer = true;"},
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API lookup body must be an exact dictionary"
    assert "HostileLookup" not in diagnostic
    assert "servicenow-upsert-lookup-body-secret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_empty_lookup_before_request() -> None:
    transport = RecordingTransport([])
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
        client.fetch_table_record(table="sys_script", lookup={})

    assert str(exc.value) == "ServiceNow API lookup body must not be empty"
    assert transport.requests == []


def test_servicenow_client_rejects_empty_upsert_lookup_before_lookup() -> None:
    transport = RecordingTransport([])
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
        client.upsert_table_record(
            table="sys_script",
            lookup={},
            fields={"script": "answer = true;"},
        )

    assert str(exc.value) == "ServiceNow API lookup body must not be empty"
    assert transport.requests == []


def test_servicenow_client_allows_empty_bounded_table_record_list_lookup() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(status_code=200, json_body={"result": [{"sys_id": "record-sys-id"}]}),
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

    records = client.fetch_table_records(
        table="sys_db_object",
        lookup={},
        fields=["sys_id"],
        limit=10,
    )

    request = transport.requests[1]
    assert records == [{"sys_id": "record-sys-id"}]
    assert request.params == {
        "sysparm_query": "",
        "sysparm_limit": "10",
        "sysparm_fields": "sys_id",
    }


def test_servicenow_client_rejects_non_string_lookup_key_before_request() -> None:
    transport = RecordingTransport([])
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

    lookup = cast(
        dict[str, str],
        {
            SecretBearingServiceNowLookupPart(): "safe-name",
        },
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_table_record(table="sys_script", lookup=lookup)

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_LOOKUP_QUERY_UNSAFE_DIAGNOSTIC
    assert "SecretBearingServiceNowLookupPart" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-lookup-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_non_string_lookup_value_before_request() -> None:
    transport = RecordingTransport([])
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

    lookup = cast(
        dict[str, str],
        {
            "name": SecretBearingServiceNowLookupPart(),
        },
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_table_record(table="sys_script", lookup=lookup)

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_LOOKUP_QUERY_UNSAFE_DIAGNOSTIC
    assert "SecretBearingServiceNowLookupPart" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-lookup-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_lookup_key_str_subclass_before_request() -> None:
    transport = RecordingTransport([])
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

    lookup = cast(
        dict[str, str],
        {
            ExplodingServiceNowLookupPart("name"): "safe-name",
        },
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_table_record(table="sys_script", lookup=lookup)

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_LOOKUP_QUERY_UNSAFE_DIAGNOSTIC
    assert "ExplodingServiceNowLookupPart" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-lookup-iter-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_lookup_value_str_subclass_before_request() -> None:
    transport = RecordingTransport([])
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

    lookup = cast(
        dict[str, str],
        {
            "name": ExplodingServiceNowLookupPart("safe-name"),
        },
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_table_record(table="sys_script", lookup=lookup)

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_LOOKUP_QUERY_UNSAFE_DIAGNOSTIC
    assert "ExplodingServiceNowLookupPart" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-lookup-iter-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_oversized_lookup_value_before_request() -> None:
    oversized_lookup_value = "a" * 1025
    transport = RecordingTransport([])
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
        client.fetch_table_record(
            table="sys_script",
            lookup={"name": oversized_lookup_value},
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_LOOKUP_QUERY_UNSAFE_DIAGNOSTIC
    assert oversized_lookup_value not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_unsafe_table_name_before_request() -> None:
    transport = RecordingTransport([])
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
        client.fetch_table_record(
            table="sys_script/../../rm_story?client_secret=table-secret",
            lookup={"name": "safe-name"},
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_TABLE_NAME_UNSAFE_DIAGNOSTIC
    assert "client_secret" not in diagnostic
    assert "table-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_non_string_table_name_before_request() -> None:
    transport = RecordingTransport([])
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
        client.fetch_table_record(
            table=cast(str, SecretBearingServiceNowTableName()),
            lookup={"name": "safe-name"},
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_TABLE_NAME_UNSAFE_DIAGNOSTIC
    assert "SecretBearingServiceNowTableName" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-table-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_table_name_str_subclass_without_methods() -> None:
    transport = RecordingTransport([])
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
        client.fetch_table_record(
            table=cast(str, ExplodingServiceNowTableName("sys_script")),
            lookup={"name": "safe-name"},
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_TABLE_NAME_UNSAFE_DIAGNOSTIC
    assert "ExplodingServiceNowTableName" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-table-name-strip-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_oversized_table_name_before_request() -> None:
    oversized_table_name = "a" * 129
    transport = RecordingTransport([])
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
        client.fetch_table_record(
            table=oversized_table_name,
            lookup={"name": "safe-name"},
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_TABLE_NAME_UNSAFE_DIAGNOSTIC
    assert oversized_table_name not in diagnostic
    assert transport.requests == []


def test_servicenow_client_upsert_failure_includes_operation_context() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(status_code=200, json_body={"result": []}),
            HttpResponse(
                status_code=403,
                json_body={
                    "error": {
                        "message": "Operation Failed",
                        "detail": "ACL Exception Insert Failed due to security constraints",
                    },
                    "status": "failure",
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.upsert_table_record(
            table="sys_remote_update_set",
            lookup={"name": "JEDI STRY0010013 - AI Candidate"},
            fields={"name": "JEDI STRY0010013 - AI Candidate"},
        )

    message = str(exc.value)
    assert "ServiceNow API POST sys_remote_update_set failed with status 403" in message
    assert "ACL Exception Insert Failed due to security constraints" in message
    assert "client-secret" not in message


def test_servicenow_client_probes_cicd_update_set_endpoint_without_state_change() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=400,
                json_body={
                    "result": {
                        "status": "3",
                        "status_label": "Failed",
                        "status_message": "Missing required parameter: update_set_name",
                        "status_detail": "",
                        "error": "",
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

    result = client.probe_cicd_update_set_endpoint(action="create")

    request = transport.requests[1]
    assert result["status_code"] == 400
    assert result["result"]["status_message"] == ("Missing required parameter: update_set_name")
    assert request.method == "POST"
    assert request.url.endswith("/api/sn_cicd/update_set/create")
    assert request.body == {}
    assert request.params == {}
    assert "client-secret" not in repr(request.sanitized())


def test_servicenow_cicd_probe_rejects_response_object_without_leak() -> None:
    class HostileResponse:
        @property
        def status_code(self) -> int:
            raise AssertionError("client_secret=servicenow-probe-response-object-secret")

    auth_transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
    )
    client_transport = HostileTransport(HostileResponse())
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=auth_transport,
        ),
        transport=client_transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.probe_cicd_update_set_endpoint(action="create")

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API response must be an exact HttpResponse"
    assert "HostileResponse" not in diagnostic
    assert "servicenow-probe-response-object-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_servicenow_cicd_probe_rejects_unsafe_action_before_membership() -> None:
    transport = RecordingTransport([])
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
        client.probe_cicd_update_set_endpoint(
            action=cast(str, SecretBearingServiceNowCicdProbeAction())
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow CI/CD probe action is unsafe"
    assert "SecretBearingServiceNowCicdProbeAction" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-cicd-probe-action-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_cicd_probe_rejects_status_code_object_without_leak() -> None:
    class HostileStatusCode:
        def __lt__(self, other: object) -> bool:
            raise AssertionError("client_secret=servicenow-probe-status-code-secret")

    auth_transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
    )
    client_transport = RecordingTransport(
        [
            HttpResponse.model_construct(
                status_code=HostileStatusCode(),
                json_body={"result": {"status": "ok"}},
            )
        ]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=auth_transport,
        ),
        transport=client_transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.probe_cicd_update_set_endpoint(action="create")

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API response status code must be an exact integer"
    assert "HostileStatusCode" not in diagnostic
    assert "servicenow-probe-status-code-secret" not in diagnostic
    assert "client_secret" not in diagnostic


@pytest.mark.parametrize("status_code", [99, 600])
def test_servicenow_cicd_probe_rejects_status_code_outside_http_range(
    status_code: int,
) -> None:
    auth_transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
    )
    client_transport = RecordingTransport(
        [HttpResponse(status_code=status_code, json_body={"result": {"status": "ok"}})]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=auth_transport,
        ),
        transport=client_transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.probe_cicd_update_set_endpoint(action="create")

    assert str(exc.value) == "ServiceNow API response status code must be in the HTTP range"


def test_servicenow_cicd_probe_rejects_body_object_without_leak() -> None:
    class HostileJsonBody:
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=servicenow-probe-body-secret")

    auth_transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
    )
    client_transport = RecordingTransport(
        [HttpResponse.model_construct(status_code=200, json_body=HostileJsonBody())]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=auth_transport,
        ),
        transport=client_transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.probe_cicd_update_set_endpoint(action="create")

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API response body must be an exact dictionary"
    assert "HostileJsonBody" not in diagnostic
    assert "servicenow-probe-body-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_servicenow_cicd_probe_rejects_body_dict_subclass_without_leak() -> None:
    class HostileJsonBody(dict[str, object]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=servicenow-probe-dict-secret")

    auth_transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
    )
    client_transport = RecordingTransport(
        [
            HttpResponse.model_construct(
                status_code=200,
                json_body=HostileJsonBody(result={"status": "ok"}),
            )
        ]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=auth_transport,
        ),
        transport=client_transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.probe_cicd_update_set_endpoint(action="create")

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API response body must be an exact dictionary"
    assert "HostileJsonBody" not in diagnostic
    assert "servicenow-probe-dict-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_servicenow_client_retrieves_cicd_update_set_from_update_source() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=202,
                json_body={
                    "result": {
                        "links": {
                            "progress": {
                                "id": "progress-sys-id",
                                "url": "https://dev205693.service-now.com/api/sn_cicd/progress/progress-sys-id",
                            }
                        },
                        "status": "0",
                        "status_label": "Pending",
                        "status_message": "",
                        "status_detail": "",
                        "error": "",
                        "percent_complete": 0,
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

    result = client.retrieve_cicd_update_set(
        update_set_id="source-update-set-sys-id",
        update_source_id="update-source-sys-id",
        auto_preview=True,
        cleanup_retrieved=True,
    )

    request = transport.requests[1]
    assert result["status_code"] == 202
    assert result["result"]["links"]["progress"]["id"] == "progress-sys-id"
    assert request.method == "POST"
    assert request.url.endswith("/api/sn_cicd/update_set/retrieve")
    assert request.params == {
        "update_set_id": "source-update-set-sys-id",
        "update_source_id": "update-source-sys-id",
        "auto_preview": "true",
        "cleanup_retrieved": "true",
    }
    assert request.body == {}


def test_servicenow_client_rejects_unsafe_cicd_retrieve_update_set_id_before_request() -> None:
    transport = RecordingTransport([])
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
        client.retrieve_cicd_update_set(
            update_set_id="source-update-set-sys-id&client_secret=retrieve-secret",
            update_source_id="update-source-sys-id",
            auto_preview=True,
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_RECORD_ID_UNSAFE_DIAGNOSTIC
    assert "client_secret" not in diagnostic
    assert "retrieve-secret" not in diagnostic
    assert transport.requests == []


@pytest.mark.parametrize("source_field", ["update_source_id", "update_source_instance_id"])
def test_servicenow_client_rejects_cicd_retrieve_source_ids_before_truthiness(
    source_field: str,
) -> None:
    transport = RecordingTransport([])
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
        if source_field == "update_source_id":
            client.retrieve_cicd_update_set(
                update_set_id="source-update-set-sys-id",
                update_source_id=cast(str, SecretBearingServiceNowCicdSourceId()),
            )
        else:
            client.retrieve_cicd_update_set(
                update_set_id="source-update-set-sys-id",
                update_source_instance_id=cast(str, SecretBearingServiceNowCicdSourceId()),
            )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_RECORD_ID_UNSAFE_DIAGNOSTIC
    assert "SecretBearingServiceNowCicdSourceId" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-cicd-source-id-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_non_bool_cicd_retrieve_flag_before_request() -> None:
    transport = RecordingTransport([])
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
        client.retrieve_cicd_update_set(
            update_set_id="source-update-set-sys-id",
            auto_preview="client_secret=flag-secret",  # type: ignore[arg-type]
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API boolean value is unsafe"
    assert "client_secret" not in diagnostic
    assert "flag-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_cicd_request_params_before_truthiness() -> None:
    class HostileParams(dict[str, str]):
        def __bool__(self) -> bool:
            raise AssertionError("client_secret=servicenow-cicd-params-secret")

    transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
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
        client._send_cicd_update_set_request(
            method="POST",
            action="retrieve",
            params=cast(dict[str, str], HostileParams(update_set_id="source-update-set-sys-id")),
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow CI/CD request params must be an exact dictionary"
    assert "HostileParams" not in diagnostic
    assert "servicenow-cicd-params-secret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_cicd_request_body_before_truthiness() -> None:
    class HostileBody(dict[str, Any]):
        def __bool__(self) -> bool:
            raise AssertionError("client_secret=servicenow-cicd-body-secret")

    transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
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
        client._send_cicd_update_set_request(
            method="POST",
            action="commit/remote-update-set-sys-id",
            body=cast(dict[str, Any], HostileBody(force_commit="false")),
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow CI/CD request body must be an exact dictionary"
    assert "HostileBody" not in diagnostic
    assert "servicenow-cicd-body-secret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_cicd_request_method_before_auth() -> None:
    transport = RecordingTransport([])
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
        client._send_cicd_update_set_request(
            method="TRACE",
            action="retrieve",
            params={"update_set_id": "source-update-set-sys-id"},
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow request method is unsafe"
    assert "TRACE" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_cicd_request_action_before_url_construction() -> None:
    class HostileAction(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=servicenow-cicd-action-secret")

    transport = RecordingTransport([])
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
        client._send_cicd_update_set_request(
            method="POST",
            action=cast(str, HostileAction("retrieve?client_secret=action-secret")),
            params={"update_set_id": "source-update-set-sys-id"},
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow CI/CD request action is unsafe"
    assert "HostileAction" not in diagnostic
    assert "servicenow-cicd-action-secret" not in diagnostic
    assert "action-secret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_previews_commits_and_fetches_cicd_progress() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=202,
                json_body={
                    "result": {
                        "links": {"progress": {"id": "preview-progress-sys-id"}},
                        "status": "0",
                        "status_label": "Pending",
                    }
                },
            ),
            HttpResponse(
                status_code=202,
                json_body={
                    "result": {
                        "links": {"progress": {"id": "commit-progress-sys-id"}},
                        "status": "0",
                        "status_label": "Pending",
                    }
                },
            ),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": {
                        "status": "2",
                        "status_label": "Successful",
                        "percent_complete": 100,
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

    preview = client.preview_cicd_update_set(remote_update_set_id="remote-update-set-sys-id")
    commit = client.commit_cicd_update_set(
        remote_update_set_id="remote-update-set-sys-id",
        force_commit=False,
    )
    progress = client.fetch_cicd_progress(progress_id="commit-progress-sys-id")

    preview_request = transport.requests[1]
    commit_request = transport.requests[2]
    progress_request = transport.requests[3]
    assert preview["result"]["links"]["progress"]["id"] == "preview-progress-sys-id"
    assert commit["result"]["links"]["progress"]["id"] == "commit-progress-sys-id"
    assert progress["result"]["status_label"] == "Successful"
    assert preview_request.method == "POST"
    assert preview_request.url.endswith("/api/sn_cicd/update_set/preview/remote-update-set-sys-id")
    assert commit_request.method == "POST"
    assert commit_request.url.endswith("/api/sn_cicd/update_set/commit/remote-update-set-sys-id")
    assert commit_request.body == {"force_commit": "false"}
    assert progress_request.method == "GET"
    assert progress_request.url.endswith("/api/sn_cicd/progress/commit-progress-sys-id")


def test_servicenow_client_rejects_unsafe_cicd_progress_id_before_request() -> None:
    transport = RecordingTransport([])
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
        client.fetch_cicd_progress(
            progress_id="progress-sys-id/../../oauth_token.do?client_secret=progress-secret"
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_RECORD_ID_UNSAFE_DIAGNOSTIC
    assert "client_secret" not in diagnostic
    assert "progress-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_discovers_and_calls_update_set_importer() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "operation_uri": "/api/1860704/jedi_update_set_import",
                        }
                    ]
                },
            ),
            HttpResponse(
                status_code=201,
                json_body={
                    "result": {
                        "status": "imported",
                        "load_result": "remote-update-set-sys-id",
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

    result = client.import_update_set_xml(
        service_id="jedi_update_set_import",
        update_set_xml="<unload />",
    )

    discovery_request = transport.requests[1]
    import_request = transport.requests[2]
    assert result["status_code"] == 201
    assert result["result"]["status"] == "imported"
    assert discovery_request.method == "GET"
    assert discovery_request.url.endswith("/api/now/table/sys_ws_operation")
    assert discovery_request.params["sysparm_query"] == (
        "web_service_definition.service_id=jedi_update_set_import"
        "^name=import_update_set_xml^active=true"
    )
    assert import_request.method == "POST"
    assert import_request.url.endswith("/api/1860704/jedi_update_set_import")
    assert import_request.body == {"update_set_xml": "<unload />"}


def test_servicenow_client_rejects_unsafe_update_set_importer_operation_uri() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "operation_uri": (
                                "/api/1860704/../oauth_token.do?client_secret=uri-secret"
                            ),
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.import_update_set_xml(
            service_id="jedi_update_set_import",
            update_set_xml="<unload />",
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_OPERATION_URI_UNSAFE_DIAGNOSTIC
    assert "client_secret" not in diagnostic
    assert "uri-secret" not in diagnostic
    assert [request.method for request in transport.requests] == ["POST", "GET"]


def test_servicenow_client_rejects_update_set_importer_operation_uri_str_subclass() -> (
    None
):
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "operation_uri": ExplodingServiceNowOperationUri(
                                "/api/1860704/jedi_update_set_import"
                            ),
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.import_update_set_xml(
            service_id="jedi_update_set_import",
            update_set_xml="<unload />",
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_OPERATION_URI_UNSAFE_DIAGNOSTIC
    assert "ExplodingServiceNowOperationUri" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-operation-uri-strip-secret" not in diagnostic
    assert [request.method for request in transport.requests] == ["POST", "GET"]


def test_servicenow_client_rejects_oversized_update_set_importer_operation_uri() -> None:
    oversized_operation_uri = f"/api/{'a' * 126}/{'b' * 126}"
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "operation_uri": oversized_operation_uri,
                        }
                    ]
                },
            ),
            HttpResponse(
                status_code=201,
                json_body={
                    "result": {
                        "status": "imported",
                        "load_result": "remote-update-set-sys-id",
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.import_update_set_xml(
            service_id="jedi_update_set_import",
            update_set_xml="<unload />",
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_OPERATION_URI_UNSAFE_DIAGNOSTIC
    assert oversized_operation_uri not in diagnostic
    assert [request.method for request in transport.requests] == ["POST", "GET"]


def test_servicenow_client_fetches_table_record_by_lookup() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "sys_id": "rest-message-sys-id",
                            "name": "Jedi DevProject Lifecycle Event API",
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

    record = client.fetch_table_record(
        table="sys_rest_message",
        lookup={"name": "Jedi DevProject Lifecycle Event API"},
    )

    request = transport.requests[1]
    assert record == {
        "sys_id": "rest-message-sys-id",
        "name": "Jedi DevProject Lifecycle Event API",
    }
    assert request.method == "GET"
    assert request.url.endswith("/api/now/table/sys_rest_message")
    assert request.params["sysparm_query"] == ("name=Jedi DevProject Lifecycle Event API")
    assert request.params["sysparm_limit"] == "1"


def test_servicenow_client_fetches_table_records_by_lookup_and_fields() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "sys_id": "customer-update-sys-id",
                            "name": "sys_dictionary_rm_story_u_ai_review_notes",
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

    records = client.fetch_table_records(
        table="sys_update_xml",
        lookup={"update_set": "update-set-sys-id"},
        fields=["sys_id", "name"],
        limit=25,
    )

    request = transport.requests[1]
    assert records == [
        {
            "sys_id": "customer-update-sys-id",
            "name": "sys_dictionary_rm_story_u_ai_review_notes",
        }
    ]
    assert request.method == "GET"
    assert request.url.endswith("/api/now/table/sys_update_xml")
    assert request.params["sysparm_query"] == "update_set=update-set-sys-id"
    assert request.params["sysparm_fields"] == "sys_id,name"
    assert request.params["sysparm_limit"] == "25"


def test_servicenow_client_rejects_oversized_table_record_field_before_request() -> None:
    oversized_field_name = "u_" + ("a" * 255)
    transport = RecordingTransport([])
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
        client.fetch_table_records(
            table="sys_update_xml",
            lookup={"update_set": "update-set-sys-id"},
            fields=[oversized_field_name],
            limit=25,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API field name is unsafe"
    assert oversized_field_name not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_unsafe_table_record_fields_before_request() -> None:
    transport = RecordingTransport([])
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
        client.fetch_table_records(
            table="sys_update_xml",
            lookup={"update_set": "update-set-sys-id"},
            fields=["sys_id", "name,sys_created_by^client_secret=field-secret"],
            limit=25,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API field name is unsafe"
    assert "client_secret" not in diagnostic
    assert "field-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_table_record_fields_list_subclass_before_request() -> None:
    class HostileFieldList(list[str]):
        def __iter__(self) -> Iterator[str]:
            raise AssertionError("client_secret=servicenow-field-list-secret")

    transport = RecordingTransport([])
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
        client.fetch_table_records(
            table="sys_update_xml",
            lookup={"update_set": "update-set-sys-id"},
            fields=cast(list[str], HostileFieldList(["sys_id", "name"])),
            limit=25,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API field list must be an exact list"
    assert "HostileFieldList" not in diagnostic
    assert "servicenow-field-list-secret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_empty_table_record_fields_before_request() -> None:
    transport = RecordingTransport([])
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
        client.fetch_table_records(
            table="sys_update_xml",
            lookup={"update_set": "update-set-sys-id"},
            fields=[],
            limit=25,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API field list must not be empty"
    assert "sys_update_xml" not in diagnostic
    assert "update-set-sys-id" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_table_record_fields_before_truthiness() -> None:
    class HostileTruthyFieldList(list[str]):
        def __bool__(self) -> bool:
            raise AssertionError("client_secret=servicenow-field-list-bool-secret")

    transport = RecordingTransport([])
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
        client.fetch_table_records(
            table="sys_update_xml",
            lookup={"update_set": "update-set-sys-id"},
            fields=cast(list[str], HostileTruthyFieldList(["sys_id", "name"])),
            limit=25,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API field list must be an exact list"
    assert "HostileTruthyFieldList" not in diagnostic
    assert "servicenow-field-list-bool-secret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_oversized_table_record_limit_before_request() -> None:
    transport = RecordingTransport([])
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
        client.fetch_table_records(
            table="sys_update_xml",
            lookup={"update_set": "update-set-sys-id"},
            fields=["sys_id", "name"],
            limit=501,
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_RESULT_LIMIT_UNSAFE_DIAGNOSTIC
    assert "update-set-sys-id" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_result_limit_int_subclass_before_request() -> None:
    class HostileResultLimit(int):
        def __lt__(self, other: object) -> bool:
            raise AssertionError("client_secret=servicenow-result-limit-lt-secret")

        def __str__(self) -> str:
            raise AssertionError("client_secret=servicenow-result-limit-str-secret")

    transport = RecordingTransport([])
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
        client.fetch_table_records(
            table="sys_update_xml",
            lookup={"update_set": "update-set-sys-id"},
            fields=["sys_id", "name"],
            limit=cast(int, HostileResultLimit(25)),
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_RESULT_LIMIT_UNSAFE_DIAGNOSTIC
    assert "HostileResultLimit" not in diagnostic
    assert "servicenow-result-limit-lt-secret" not in diagnostic
    assert "servicenow-result-limit-str-secret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_fetch_table_record_returns_none_when_missing() -> None:
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

    record = client.fetch_table_record(
        table="sys_script",
        lookup={"name": "Jedi DevProject lifecycle event emitter"},
    )

    assert record is None


def test_servicenow_client_uploads_story_attachment_with_binary_body(
    tmp_path: Path,
) -> None:
    attachment_path = tmp_path / "STRY0010013.xml"
    attachment_path.write_bytes(b"<unload/>")
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=201,
                json_body={"result": {"sys_id": "attachment-sys-id"}},
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

    result = client.attach_story_file(
        "story-sys-id",
        file_path=attachment_path,
        file_name="STRY0010013.xml",
        content_type="application/xml",
    )

    request = transport.requests[1]
    assert result == {"sys_id": "attachment-sys-id"}
    assert request.method == "POST"
    assert request.url == "https://dev205693.service-now.com/api/now/attachment/file"
    assert request.params == {
        "table_name": "rm_story",
        "table_sys_id": "story-sys-id",
        "file_name": "STRY0010013.xml",
    }
    assert request.headers["Content-Type"] == "application/xml"
    assert request.body_bytes == b"<unload/>"
    assert request.body == {}


def test_servicenow_client_rejects_unsafe_attachment_story_id_before_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attachment_path = tmp_path / "STRY0010013.xml"
    attachment_path.write_bytes(b"<unload/>")
    transport = RecordingTransport([])
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

    def fail_read_regular_artifact_bytes(_path: Path, *, max_bytes: int) -> bytes:
        raise AssertionError("attachment bytes must not be read for unsafe story sys_id")

    monkeypatch.setattr(
        servicenow,
        "read_regular_artifact_bytes",
        fail_read_regular_artifact_bytes,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.attach_story_file(
            "story-sys-id/../../rm_story?client_secret=attachment-secret",
            file_path=attachment_path,
            file_name="STRY0010013.xml",
            content_type="application/xml",
        )

    diagnostic = str(exc.value)
    assert diagnostic == SERVICENOW_RECORD_ID_UNSAFE_DIAGNOSTIC
    assert "client_secret" not in diagnostic
    assert "attachment-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_unsafe_attachment_file_name_before_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attachment_path = tmp_path / "STRY0010013.xml"
    attachment_path.write_bytes(b"<unload/>")
    transport = RecordingTransport([])
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

    def fail_read_regular_artifact_bytes(_path: Path, *, max_bytes: int) -> bytes:
        raise AssertionError("attachment bytes must not be read for unsafe file name")

    monkeypatch.setattr(
        servicenow,
        "read_regular_artifact_bytes",
        fail_read_regular_artifact_bytes,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.attach_story_file(
            "story-sys-id",
            file_path=attachment_path,
            file_name="STRY0010013.xml\r\nclient_secret=attachment-secret",
            content_type="application/xml",
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow attachment file name is unsafe"
    assert "client_secret" not in diagnostic
    assert "attachment-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_non_string_attachment_file_name_before_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attachment_path = tmp_path / "STRY0010013.xml"
    attachment_path.write_bytes(b"<unload/>")
    transport = RecordingTransport([])
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

    def fail_read_regular_artifact_bytes(_path: Path, *, max_bytes: int) -> bytes:
        raise AssertionError("attachment bytes must not be read for non-string file name")

    monkeypatch.setattr(
        servicenow,
        "read_regular_artifact_bytes",
        fail_read_regular_artifact_bytes,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.attach_story_file(
            "story-sys-id",
            file_path=attachment_path,
            file_name=cast(str, SecretBearingServiceNowAttachmentFileName()),
            content_type="application/xml",
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow attachment file name is unsafe"
    assert "SecretBearingServiceNowAttachmentFileName" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-attachment-file-name-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_attachment_file_name_str_subclass_before_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attachment_path = tmp_path / "STRY0010013.xml"
    attachment_path.write_bytes(b"<unload/>")
    transport = RecordingTransport([])
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

    def fail_read_regular_artifact_bytes(_path: Path, *, max_bytes: int) -> bytes:
        raise AssertionError("attachment bytes must not be read for subclassed file name")

    monkeypatch.setattr(
        servicenow,
        "read_regular_artifact_bytes",
        fail_read_regular_artifact_bytes,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.attach_story_file(
            "story-sys-id",
            file_path=attachment_path,
            file_name=cast(str, ExplodingServiceNowAttachmentFileName("STRY0010013.xml")),
            content_type="application/xml",
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow attachment file name is unsafe"
    assert "ExplodingServiceNowAttachmentFileName" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-attachment-file-name-strip-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_unsafe_attachment_content_type_before_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attachment_path = tmp_path / "STRY0010013.xml"
    attachment_path.write_bytes(b"<unload/>")
    transport = RecordingTransport([])
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

    def fail_read_regular_artifact_bytes(_path: Path, *, max_bytes: int) -> bytes:
        raise AssertionError("attachment bytes must not be read for unsafe content type")

    monkeypatch.setattr(
        servicenow,
        "read_regular_artifact_bytes",
        fail_read_regular_artifact_bytes,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.attach_story_file(
            "story-sys-id",
            file_path=attachment_path,
            file_name="STRY0010013.xml",
            content_type="application/xml\r\nX-Client-Secret: attachment-secret",
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow attachment content type is unsafe"
    assert "Client-Secret" not in diagnostic
    assert "attachment-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_non_string_attachment_content_type_before_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attachment_path = tmp_path / "STRY0010013.xml"
    attachment_path.write_bytes(b"<unload/>")
    transport = RecordingTransport([])
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

    def fail_read_regular_artifact_bytes(_path: Path, *, max_bytes: int) -> bytes:
        raise AssertionError("attachment bytes must not be read for non-string content type")

    monkeypatch.setattr(
        servicenow,
        "read_regular_artifact_bytes",
        fail_read_regular_artifact_bytes,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.attach_story_file(
            "story-sys-id",
            file_path=attachment_path,
            file_name="STRY0010013.xml",
            content_type=cast(str, SecretBearingServiceNowAttachmentContentType()),
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow attachment content type is unsafe"
    assert "SecretBearingServiceNowAttachmentContentType" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-attachment-content-type-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_attachment_content_type_str_subclass_before_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attachment_path = tmp_path / "STRY0010013.xml"
    attachment_path.write_bytes(b"<unload/>")
    transport = RecordingTransport([])
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

    def fail_read_regular_artifact_bytes(_path: Path, *, max_bytes: int) -> bytes:
        raise AssertionError("attachment bytes must not be read for subclassed content type")

    monkeypatch.setattr(
        servicenow,
        "read_regular_artifact_bytes",
        fail_read_regular_artifact_bytes,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.attach_story_file(
            "story-sys-id",
            file_path=attachment_path,
            file_name="STRY0010013.xml",
            content_type=cast(
                str,
                ExplodingServiceNowAttachmentContentType("application/xml"),
            ),
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow attachment content type is unsafe"
    assert "ExplodingServiceNowAttachmentContentType" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-attachment-content-type-strip-secret" not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_oversized_attachment_content_type_before_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attachment_path = tmp_path / "STRY0010013.xml"
    attachment_path.write_bytes(b"<unload/>")
    oversized_content_type = f"application/{'x' * 244}"
    transport = RecordingTransport([])
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

    def fail_read_regular_artifact_bytes(_path: Path, *, max_bytes: int) -> bytes:
        raise AssertionError("attachment bytes must not be read for oversized content type")

    monkeypatch.setattr(
        servicenow,
        "read_regular_artifact_bytes",
        fail_read_regular_artifact_bytes,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.attach_story_file(
            "story-sys-id",
            file_path=attachment_path,
            file_name="STRY0010013.xml",
            content_type=oversized_content_type,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow attachment content type is unsafe"
    assert oversized_content_type not in diagnostic
    assert transport.requests == []


def test_servicenow_client_rejects_oversized_story_attachment_before_reading(
    tmp_path: Path,
) -> None:
    attachment_path = tmp_path / "oversized.xml"
    attachment_path.write_bytes(b"x" * (MAX_ATTACHMENT_UPLOAD_BYTES + 1))
    transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
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

    with pytest.raises(ServiceNowApiError, match="attachment file exceeds") as exc:
        client.attach_story_file(
            "story-sys-id",
            file_path=attachment_path,
            file_name="oversized.xml",
            content_type="application/xml",
        )

    assert exc.value.__cause__ is None
    assert transport.requests == []


def test_servicenow_client_rejects_symlinked_story_attachment_before_upload(
    tmp_path: Path,
) -> None:
    target_path = tmp_path / "target.xml"
    target_path.write_text("<unload/>", encoding="utf-8")
    attachment_path = tmp_path / "attachment-client_secret=path-secret.xml"
    attachment_path.symlink_to(target_path)
    transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
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
        client.attach_story_file(
            "story-sys-id",
            file_path=attachment_path,
            file_name="STRY0010013.xml",
            content_type="application/xml",
        )

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow attachment file must be a regular file"
    assert "attachment-client_secret" not in diagnostic
    assert "path-secret" not in diagnostic
    assert exc.value.__cause__ is None
    assert transport.requests == []


def test_servicenow_client_attachment_read_error_uses_typed_reason_not_message_prefix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attachment_path = tmp_path / "attachment.xml"
    attachment_path.write_text("<unload/>", encoding="utf-8")
    transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
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

    def fail_read_regular_artifact_bytes(_path: Path, *, max_bytes: int) -> bytes:
        raise ArtifactReadError(
            "artifact file exceeds spoofed-message",
            reason="not_regular",
        )

    monkeypatch.setattr(
        servicenow,
        "read_regular_artifact_bytes",
        fail_read_regular_artifact_bytes,
    )

    with pytest.raises(ServiceNowApiError) as exc_info:
        client.attach_story_file(
            "story-sys-id",
            file_path=attachment_path,
            file_name="STRY0010013.xml",
            content_type="application/xml",
        )

    assert "attachment file must be a regular file" in str(exc_info.value)
    assert "attachment file exceeds" not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert transport.requests == []


def test_servicenow_client_uploads_story_attachment_without_whole_file_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attachment_path = tmp_path / "STRY0010013.xml"
    attachment_path.write_text("<unload/>", encoding="utf-8")
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=201,
                json_body={"result": {"sys_id": "attachment-sys-id"}},
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

    def fail_read_bytes(self: Path) -> bytes:
        raise AssertionError(f"unexpected whole-file read for {self}")

    monkeypatch.setattr(Path, "read_bytes", fail_read_bytes)

    result = client.attach_story_file(
        "story-sys-id",
        file_path=attachment_path,
        file_name="STRY0010013.xml",
        content_type="application/xml",
    )

    assert result == {"sys_id": "attachment-sys-id"}
    assert transport.requests[1].body_bytes == b"<unload/>"


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


def test_servicenow_api_error_message_requires_validated_status_code() -> None:
    with pytest.raises(ServiceNowApiError) as exc:
        _servicenow_api_error_message(
            HttpResponse(status_code=500, json_body={"error": {"message": "boom"}})
        )

    assert str(exc.value) == "ServiceNow API error status code must be prevalidated"


def test_servicenow_api_error_message_does_not_read_hostile_status_fallback() -> None:
    class HostileStatusCode:
        def __str__(self) -> str:
            raise AssertionError("client_secret=servicenow-error-status-secret")

    response = HttpResponse.model_construct(
        status_code=HostileStatusCode(),
        json_body={"error": {"message": "boom"}},
    )

    with pytest.raises(ServiceNowApiError) as exc:
        _servicenow_api_error_message(response)

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API error status code must be prevalidated"
    assert "HostileStatusCode" not in diagnostic
    assert "servicenow-error-status-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_servicenow_response_body_helper_rejects_body_object_without_leak() -> None:
    class HostileJsonBody:
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=servicenow-response-body-secret")

    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse.model_construct(status_code=200, json_body=HostileJsonBody()),
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
        client.fetch_cicd_progress(progress_id="progress-123")

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API response body must be an exact dictionary"
    assert "HostileJsonBody" not in diagnostic
    assert "servicenow-response-body-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_servicenow_response_body_helper_rejects_body_dict_subclass_without_leak() -> None:
    class HostileJsonBody(dict[str, object]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=servicenow-response-dict-secret")

    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse.model_construct(
                status_code=200,
                json_body=HostileJsonBody(result={"status": "ok"}),
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_cicd_progress(progress_id="progress-123")

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API response body must be an exact dictionary"
    assert "HostileJsonBody" not in diagnostic
    assert "servicenow-response-dict-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_servicenow_response_body_helper_rejects_response_object_without_leak() -> None:
    class HostileResponse:
        @property
        def status_code(self) -> int:
            raise AssertionError("client_secret=servicenow-api-response-object-secret")

    auth_transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
    )
    client_transport = HostileTransport(HostileResponse())
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=auth_transport,
        ),
        transport=client_transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_cicd_progress(progress_id="progress-123")

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API response must be an exact HttpResponse"
    assert "HostileResponse" not in diagnostic
    assert "servicenow-api-response-object-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_servicenow_response_body_helper_rejects_status_code_object_without_leak() -> None:
    class HostileStatusCode:
        def __ge__(self, other: object) -> bool:
            raise AssertionError("client_secret=servicenow-api-status-code-secret")

    auth_transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
    )
    client_transport = RecordingTransport(
        [
            HttpResponse.model_construct(
                status_code=HostileStatusCode(),
                json_body={"result": {"status": "ok"}},
            )
        ]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=auth_transport,
        ),
        transport=client_transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_cicd_progress(progress_id="progress-123")

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API response status code must be an exact integer"
    assert "HostileStatusCode" not in diagnostic
    assert "servicenow-api-status-code-secret" not in diagnostic
    assert "client_secret" not in diagnostic


@pytest.mark.parametrize("status_code", [99, 600])
def test_servicenow_response_body_helper_rejects_status_code_outside_http_range(
    status_code: int,
) -> None:
    auth_transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
    )
    client_transport = RecordingTransport(
        [HttpResponse(status_code=status_code, json_body={"result": {"status": "ok"}})]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=auth_transport,
        ),
        transport=client_transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_cicd_progress(progress_id="progress-123")

    assert str(exc.value) == "ServiceNow API response status code must be in the HTTP range"


def test_servicenow_api_error_body_object_collapses_without_leak() -> None:
    class HostileJsonBody:
        def __repr__(self) -> str:
            raise AssertionError("client_secret=servicenow-error-body-repr-secret")

    auth_transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
    )
    client_transport = RecordingTransport(
        [HttpResponse.model_construct(status_code=500, json_body=HostileJsonBody())]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=auth_transport,
        ),
        transport=client_transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_cicd_progress(progress_id="progress-123")

    diagnostic = str(exc.value)
    assert "ServiceNow API GET sn_cicd/progress/progress-123 failed with status 500" in (
        diagnostic
    )
    assert "[non-json value]" in diagnostic
    assert "HostileJsonBody" not in diagnostic
    assert "servicenow-error-body-repr-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_servicenow_api_error_body_dict_subclass_collapses_without_leak() -> None:
    class HostileJsonBody(dict[str, object]):
        def items(self) -> Any:
            raise AssertionError("client_secret=servicenow-error-body-items-secret")

    auth_transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
    )
    client_transport = RecordingTransport(
        [
            HttpResponse.model_construct(
                status_code=500,
                json_body=HostileJsonBody(error={"message": "boom"}),
            )
        ]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=auth_transport,
        ),
        transport=client_transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_cicd_progress(progress_id="progress-123")

    diagnostic = str(exc.value)
    assert "ServiceNow API GET sn_cicd/progress/progress-123 failed with status 500" in (
        diagnostic
    )
    assert "[non-json value]" in diagnostic
    assert "HostileJsonBody" not in diagnostic
    assert "servicenow-error-body-items-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_servicenow_success_result_list_shape_error_does_not_echo_result_value() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(status_code=200, json_body={"result": "client_secret=result-secret"}),
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

    diagnostic = str(exc.value)
    assert "ServiceNow API response result must be a list" in diagnostic
    assert "client_secret" not in diagnostic
    assert "result-secret" not in diagnostic


def test_servicenow_result_record_list_rejects_body_object_without_leak() -> None:
    class HostileJsonBody:
        def get(self, key: object, default: object | None = None) -> object:
            raise AssertionError("client_secret=servicenow-result-body-secret")

    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse.model_construct(status_code=200, json_body=HostileJsonBody()),
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

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API response body must be an exact dictionary"
    assert "HostileJsonBody" not in diagnostic
    assert "servicenow-result-body-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_servicenow_result_record_list_rejects_body_dict_subclass_without_leak() -> None:
    class HostileJsonBody(dict[str, object]):
        def get(self, key: object, default: object | None = None) -> object:
            raise AssertionError("client_secret=servicenow-result-dict-secret")

    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse.model_construct(
                status_code=200,
                json_body=HostileJsonBody(result=[]),
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_ready_stories()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API response body must be an exact dictionary"
    assert "HostileJsonBody" not in diagnostic
    assert "servicenow-result-dict-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_servicenow_result_record_list_rejects_missing_result_without_silent_empty() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(status_code=200, json_body={}),
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

    assert str(exc.value) == "ServiceNow API response result is missing"


def test_servicenow_table_api_rejects_response_object_without_leak() -> None:
    class HostileResponse:
        @property
        def status_code(self) -> int:
            raise AssertionError("client_secret=servicenow-table-response-object-secret")

    auth_transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
    )
    client_transport = HostileTransport(HostileResponse())
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=auth_transport,
        ),
        transport=client_transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_ready_stories()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API response must be an exact HttpResponse"
    assert "HostileResponse" not in diagnostic
    assert "servicenow-table-response-object-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_servicenow_table_api_rejects_status_code_object_without_leak() -> None:
    class HostileStatusCode:
        def __ge__(self, other: object) -> bool:
            raise AssertionError("client_secret=servicenow-table-status-code-secret")

    auth_transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
    )
    client_transport = RecordingTransport(
        [
            HttpResponse.model_construct(
                status_code=HostileStatusCode(),
                json_body={"result": []},
            )
        ]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=auth_transport,
        ),
        transport=client_transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_ready_stories()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API response status code must be an exact integer"
    assert "HostileStatusCode" not in diagnostic
    assert "servicenow-table-status-code-secret" not in diagnostic
    assert "client_secret" not in diagnostic


@pytest.mark.parametrize("status_code", [99, 600])
def test_servicenow_table_api_rejects_status_code_outside_http_range(
    status_code: int,
) -> None:
    auth_transport = RecordingTransport(
        [HttpResponse(status_code=200, json_body={"access_token": "token-123"})]
    )
    client_transport = RecordingTransport(
        [HttpResponse(status_code=status_code, json_body={"result": []})]
    )
    client = ServiceNowClient(
        settings=ServiceNowSettings(instance_url="https://dev205693.service-now.com"),
        auth=OAuthClientCredentials(
            instance_url="https://dev205693.service-now.com",
            client_id="client-id",
            client_secret="client-secret",
            transport=auth_transport,
        ),
        transport=client_transport,
    )

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_ready_stories()

    assert str(exc.value) == "ServiceNow API response status code must be in the HTTP range"


def test_servicenow_success_result_record_shape_error_does_not_echo_result_value() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(status_code=200, json_body={"result": ["client_secret=result-secret"]}),
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

    diagnostic = str(exc.value)
    assert "ServiceNow API response result entries must be objects" in diagnostic
    assert "client_secret" not in diagnostic
    assert "result-secret" not in diagnostic


def test_servicenow_result_record_list_rejects_list_subclass_without_leak() -> None:
    class HostileResultList(list[object]):
        def __iter__(self) -> Iterator[object]:
            raise AssertionError("client_secret=servicenow-result-list-secret")

    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse.model_construct(
                status_code=200,
                json_body={"result": HostileResultList([{"sys_id": "story-sys-id"}])},
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_ready_stories()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API response result must be an exact list"
    assert "HostileResultList" not in diagnostic
    assert "servicenow-result-list-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_servicenow_result_record_list_rejects_entry_dict_subclass_without_leak() -> None:
    class HostileRecord(dict[str, object]):
        def get(self, key: object, default: object | None = None) -> object:
            raise AssertionError("client_secret=servicenow-result-record-secret")

    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse.model_construct(
                status_code=200,
                json_body={"result": [HostileRecord(sys_id="story-sys-id")]},
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_ready_stories()

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API response result entries must be exact objects"
    assert "HostileRecord" not in diagnostic
    assert "servicenow-result-record-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_servicenow_result_object_rejects_body_dict_subclass_without_leak() -> None:
    class HostileJsonBody(dict[str, object]):
        def get(self, key: object, default: object | None = None) -> object:
            raise AssertionError("client_secret=servicenow-result-object-dict-secret")

    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse.model_construct(
                status_code=200,
                json_body=HostileJsonBody(result={"sys_id": "story-sys-id"}),
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.update_story_fields("story-sys-id", {"u_ai_status": "Ready for Testing"})

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API response body must be an exact dictionary"
    assert "HostileJsonBody" not in diagnostic
    assert "servicenow-result-object-dict-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_servicenow_result_object_rejects_result_dict_subclass_without_leak() -> None:
    class HostileResultObject(dict[str, object]):
        def get(self, key: object, default: object | None = None) -> object:
            raise AssertionError("client_secret=servicenow-result-object-secret")

    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse.model_construct(
                status_code=200,
                json_body={"result": HostileResultObject(sys_id="story-sys-id")},
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.update_story_fields("story-sys-id", {"u_ai_status": "Ready for Testing"})

    diagnostic = str(exc.value)
    assert diagnostic == "ServiceNow API response result must be an exact object"
    assert "HostileResultObject" not in diagnostic
    assert "servicenow-result-object-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_servicenow_result_object_rejects_missing_result_without_silent_empty() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(status_code=200, json_body={}),
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
        client.update_story_fields("story-sys-id", {"u_ai_status": "Ready for Testing"})

    assert str(exc.value) == "ServiceNow API response result is missing"


def test_servicenow_success_result_object_shape_error_does_not_echo_result_value() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(status_code=200, json_body={"result": "client_secret=result-secret"}),
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
        client.update_story_fields("story-sys-id", {"u_ai_status": "Ready for Testing"})

    diagnostic = str(exc.value)
    assert "ServiceNow API response result must be an object" in diagnostic
    assert "client_secret" not in diagnostic
    assert "result-secret" not in diagnostic


def test_servicenow_api_failure_normalizes_untrusted_error_diagnostics() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=500,
                json_body={
                    "error": {
                        "message": (
                            "boom\n"
                            "url=https://api-user:url-secret@example.service-now.com/api"
                            "?client_secret=query-secret\tapi_key=assignment-secret"
                        )
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_ready_stories()

    diagnostic = str(exc.value)
    assert "ServiceNow API failed with status 500" in diagnostic
    assert "\\n" not in diagnostic
    assert "\\t" not in diagnostic
    assert "url-secret" not in diagnostic
    assert "query-secret" not in diagnostic
    assert "assignment-secret" not in diagnostic
    assert "***REDACTED***" in diagnostic


def test_servicenow_api_failure_bounds_final_error_diagnostic() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=500,
                json_body={"error": {"message": "x" * (MAX_HTTP_ERROR_DIAGNOSTIC_CHARS + 1000)}},
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_ready_stories()

    diagnostic = str(exc.value)
    assert "ServiceNow API failed with status 500" in diagnostic
    assert diagnostic.endswith(HTTP_ERROR_TRUNCATION_MARKER)
    assert len(diagnostic) <= MAX_HTTP_ERROR_DIAGNOSTIC_CHARS + 128


def test_servicenow_diagnostic_value_does_not_consume_all_fields_for_wide_response() -> None:
    payload = {f"field_{index}": f"value-{index}" for index in range(150)}

    diagnostic = repr(_servicenow_diagnostic_value(payload))

    assert "'omitted_fields': 50" in diagnostic
    assert "field_149" not in diagnostic
    assert len(diagnostic) < MAX_HTTP_ERROR_DIAGNOSTIC_CHARS


def test_servicenow_diagnostic_value_rejects_dict_subclass_payloads() -> None:
    class HostileServiceNowDiagnosticPayload(dict[str, Any]):
        def items(self) -> Any:
            raise AssertionError("client_secret=servicenow-dict-subclass-secret")

    diagnostic = repr(
        _servicenow_diagnostic_value(
            {"error": HostileServiceNowDiagnosticPayload({"message": "hidden diagnostic"})}
        )
    )

    assert "[non-json value]" in diagnostic
    assert "hidden diagnostic" not in diagnostic
    assert "dict-subclass-secret" not in diagnostic


def test_servicenow_diagnostic_value_handles_circular_response_payload() -> None:
    circular_payload: dict[str, Any] = {"message": "ServiceNow failed"}
    circular_payload["self"] = circular_payload

    diagnostic = repr(_servicenow_diagnostic_value({"error": circular_payload}))

    assert "[circular reference]" in diagnostic
    assert "ServiceNow failed" in diagnostic
    assert len(diagnostic) < MAX_HTTP_ERROR_DIAGNOSTIC_CHARS


def test_servicenow_diagnostic_value_caps_normalized_text_values() -> None:
    diagnostic = _servicenow_diagnostic_value(
        {"error": {"message": "x" * (MAX_HTTP_ERROR_DIAGNOSTIC_CHARS + 1)}}
    )

    assert isinstance(diagnostic, dict)
    error = diagnostic["error"]
    assert isinstance(error, dict)
    message = error["message"]
    assert isinstance(message, str)
    assert message.endswith(HTTP_ERROR_TRUNCATION_MARKER)
    assert len(message) == MAX_HTTP_ERROR_DIAGNOSTIC_CHARS


def test_servicenow_api_failure_rejects_string_subclass_diagnostic_text() -> None:
    class ExplodingServiceNowDiagnosticText(str):
        def split(self, sep: str | None = None, maxsplit: Any = -1) -> list[str]:
            raise AssertionError("client_secret=servicenow-diagnostic-text-split-secret")

    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=500,
                json_body={
                    "error": {
                        "message": ExplodingServiceNowDiagnosticText(
                            "client_secret=servicenow-diagnostic-text-value-secret"
                        )
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_ready_stories()

    diagnostic = str(exc.value)
    assert "ServiceNow API failed with status 500" in diagnostic
    assert "[non-json value]" in diagnostic
    assert "ExplodingServiceNowDiagnosticText" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-diagnostic-text" not in diagnostic


def test_servicenow_api_failure_rejects_non_json_diagnostic_keys() -> None:
    class ExplodingServiceNowDiagnosticKey:
        def __hash__(self) -> int:
            return 1

        def __repr__(self) -> str:
            return "ExplodingServiceNowDiagnosticKey(client_secret=diagnostic-key-secret)"

    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=500,
                json_body={
                    "error": {
                        ExplodingServiceNowDiagnosticKey(): "diagnostic-key-value"
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

    with pytest.raises(ServiceNowApiError) as exc:
        client.fetch_ready_stories()

    diagnostic = str(exc.value)
    assert "ServiceNow API failed with status 500" in diagnostic
    assert "[non-json key]" in diagnostic
    assert "ExplodingServiceNowDiagnosticKey" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "diagnostic-key-secret" not in diagnostic
    assert "diagnostic-key-value" in diagnostic


def test_servicenow_diagnostic_value_keeps_duplicate_keys_inside_cap() -> None:
    first_key = "x" * (MAX_HTTP_ERROR_DIAGNOSTIC_CHARS + 1)
    second_key = "x" * (MAX_HTTP_ERROR_DIAGNOSTIC_CHARS + 2)

    diagnostic = _servicenow_diagnostic_value({"error": {first_key: "one", second_key: "two"}})

    assert isinstance(diagnostic, dict)
    error = diagnostic["error"]
    assert isinstance(error, dict)
    keys = list(error)
    assert len(keys) == 2
    assert keys[0].endswith(HTTP_ERROR_TRUNCATION_MARKER)
    assert keys[1].endswith(" (2)")
    assert all(len(key) <= MAX_HTTP_ERROR_DIAGNOSTIC_CHARS for key in keys)
    assert list(error.values()) == ["one", "two"]


def test_servicenow_diagnostic_value_preserves_user_truncation_marker_key() -> None:
    payload: dict[str, Any] = {"__jedi_response_truncated__": "user marker"}
    payload.update({f"field_{index}": f"value-{index}" for index in range(101)})

    diagnostic = _servicenow_diagnostic_value(payload)

    assert isinstance(diagnostic, dict)
    assert diagnostic["__jedi_response_truncated__"] == "user marker"
    assert diagnostic["__jedi_response_truncated__ (2)"] == {
        "truncated": True,
        "omitted_fields": 2,
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"Authorization": "Bearer token-123", "client_secret": "secret"},
        {"access_token": "token-123", "nested": {"client_secret": "secret"}},
        {
            "api_key": "api-key-secret",
            "id_token": "id-token-secret",
            "signature": "signature-secret",
            "token": "generic-token-secret",
        },
        {"api-key": "api-key-secret", "client-secret": "client-secret"},
        {"x-api-key": "x-api-value", "x-client-secret": "x-client-value"},
        {"accessToken": "camel-access-value", "clientSecret": "camel-client-value"},
        {"Cookie": "session-secret", "Set-Cookie": "set-cookie-secret"},
        {
            "private_key": "private-key-secret",
            "privateKey": "camel-private-key-secret",
            "ssh_private_key": "ssh-private-key-secret",
        },
        {
            "aws_secret_access_key": "aws-secret-value",
            "awsSessionToken": "aws-session-value",
            "azureClientSecret": "azure-secret-value",
        },
    ],
)
def test_redact_secrets_masks_sensitive_values(payload: dict[str, Any]) -> None:
    redacted = redact_secrets(payload)

    assert "'secret'" not in repr(redacted)
    assert "Bearer token-123" not in repr(redacted)
    assert "'token-123'" not in repr(redacted)
    assert "api-key-secret" not in repr(redacted)
    assert "x-api-value" not in repr(redacted)
    assert "x-client-value" not in repr(redacted)
    assert "camel-access-value" not in repr(redacted)
    assert "camel-client-value" not in repr(redacted)
    assert "session-secret" not in repr(redacted)
    assert "set-cookie-secret" not in repr(redacted)
    assert "private-key-secret" not in repr(redacted)
    assert "camel-private-key-secret" not in repr(redacted)
    assert "ssh-private-key-secret" not in repr(redacted)
    assert "aws-secret-value" not in repr(redacted)
    assert "aws-session-value" not in repr(redacted)
    assert "azure-secret-value" not in repr(redacted)
    assert "id-token-secret" not in repr(redacted)
    assert "signature-secret" not in repr(redacted)
    assert "generic-token-secret" not in repr(redacted)


def test_redact_secrets_masks_sensitive_values_inside_lists() -> None:
    redacted = redact_secrets([{"access_token": "token-123"}])

    assert "'token-123'" not in repr(redacted)


def test_redact_secrets_does_not_consume_all_fields_for_wide_diagnostic() -> None:
    payload = {f"field_{index}": f"value-{index}" for index in range(150)}

    diagnostic = repr(redact_secrets(payload))

    assert "'omitted_fields': 50" in diagnostic
    assert "field_149" not in diagnostic


def test_redact_secrets_rejects_dict_subclass_payloads() -> None:
    class HostileSecretDiagnosticPayload(dict[str, Any]):
        def items(self) -> Any:
            raise AssertionError("client_secret=redact-dict-subclass-secret")

    diagnostic = repr(
        redact_secrets(
            {"error": HostileSecretDiagnosticPayload({"message": "hidden diagnostic"})}
        )
    )

    assert "[non-json value]" in diagnostic
    assert "hidden diagnostic" not in diagnostic
    assert "dict-subclass-secret" not in diagnostic


def test_redact_secrets_preserves_user_truncation_marker_key() -> None:
    payload: dict[str, Any] = {"__jedi_response_truncated__": "user marker"}
    payload.update({f"field_{index}": f"value-{index}" for index in range(101)})

    diagnostic = redact_secrets(payload)

    assert isinstance(diagnostic, dict)
    assert diagnostic["__jedi_response_truncated__"] == "user marker"
    assert diagnostic["__jedi_response_truncated__ (2)"] == {
        "truncated": True,
        "omitted_fields": 2,
    }


def test_redact_secrets_handles_circular_diagnostic_payload() -> None:
    circular_payload: dict[str, Any] = {"message": "ServiceNow failed"}
    circular_payload["self"] = circular_payload

    diagnostic = repr(redact_secrets({"error": circular_payload}))

    assert "[circular reference]" in diagnostic
    assert "ServiceNow failed" in diagnostic
    assert "RecursionError" not in diagnostic


def test_redact_secrets_masks_sensitive_strings_under_non_sensitive_keys() -> None:
    redacted = redact_secrets(
        {
            "error": {
                "message": (
                    "ServiceNow rejected request at "
                    "https://api-user:url-secret@example.service-now.com/api"
                    "?client_secret=query-secret with api_key=assignment-secret"
                )
            }
        }
    )

    representation = repr(redacted)
    assert "url-secret" not in representation
    assert "query-secret" not in representation
    assert "assignment-secret" not in representation
    assert "***REDACTED***" in representation


def test_redact_secrets_caps_exact_string_values_after_redaction() -> None:
    redacted = redact_secrets(
        {"error": {"message": "x" * (MAX_HTTP_ERROR_DIAGNOSTIC_CHARS + 1)}}
    )

    assert isinstance(redacted, dict)
    error = redacted["error"]
    assert isinstance(error, dict)
    message = error["message"]
    assert isinstance(message, str)
    assert message.endswith(HTTP_ERROR_TRUNCATION_MARKER)
    assert len(message) == MAX_HTTP_ERROR_DIAGNOSTIC_CHARS


def test_redact_secrets_normalizes_exact_string_values_after_redaction() -> None:
    redacted = redact_secrets(
        {
            "error": {
                "message": "first line\nsecond line\tapi_key=redaction-secret",
            }
        }
    )

    assert isinstance(redacted, dict)
    error = redacted["error"]
    assert isinstance(error, dict)
    message = error["message"]
    assert isinstance(message, str)
    assert message == "first line second line api_key=***REDACTED***"
    assert "\n" not in message
    assert "\t" not in message
    assert "redaction-secret" not in message


def test_redact_secrets_rejects_string_subclass_diagnostic_text() -> None:
    class ExplodingSecretDiagnosticText(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=redact-secrets-str-secret")

    redacted = redact_secrets(
        {
            "error": {
                "message": ExplodingSecretDiagnosticText(
                    "client_secret=redact-secrets-value-secret"
                )
            }
        }
    )

    diagnostic = repr(redacted)
    assert "[non-json value]" in diagnostic
    assert "ExplodingSecretDiagnosticText" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "redact-secrets" not in diagnostic


def test_redact_secrets_rejects_non_json_diagnostic_keys() -> None:
    class ExplodingSecretDiagnosticKey:
        def __hash__(self) -> int:
            return 1

        def __repr__(self) -> str:
            return "ExplodingSecretDiagnosticKey(client_secret=redact-key-secret)"

    redacted = redact_secrets(
        {
            "error": {
                ExplodingSecretDiagnosticKey(): "redact-key-value",
            }
        }
    )

    diagnostic = repr(redacted)
    assert "[non-json key]" in diagnostic
    assert "ExplodingSecretDiagnosticKey" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "redact-key-secret" not in diagnostic
    assert "redact-key-value" in diagnostic


def test_redact_secrets_normalizes_non_json_scalar_values() -> None:
    class ExplodingSecretDiagnosticValue:
        def __repr__(self) -> str:
            return "ExplodingSecretDiagnosticValue(client_secret=redact-value-secret)"

    redacted = redact_secrets(
        {
            "error": {
                "bad_object": ExplodingSecretDiagnosticValue(),
                "bad_float": float("nan"),
                "none": None,
                "bool": False,
                "int": 9,
                "float": 2.5,
            }
        }
    )

    diagnostic = repr(redacted)
    assert diagnostic.count("[non-json value]") == 2
    assert "ExplodingSecretDiagnosticValue" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "redact-value-secret" not in diagnostic
    assert "'none': None" in diagnostic
    assert "'bool': False" in diagnostic
    assert "'int': 9" in diagnostic
    assert "'float': 2.5" in diagnostic


def test_http_request_sanitized_redacts_body_bytes_without_mutating_original() -> None:
    request = HttpRequest(
        method="POST",
        url="https://dev205693.service-now.com/api/now/attachment/file",
        body_bytes=b"binary-secret-payload",
    )

    sanitized = request.sanitized()

    assert request.body_bytes == b"binary-secret-payload"
    assert sanitized.body_bytes == b"***REDACTED***"
    assert "binary-secret-payload" not in repr(sanitized)


def test_http_request_sanitized_redacts_url_credentials_and_sensitive_query() -> None:
    request = HttpRequest(
        method="GET",
        url=(
            "https://api-user:url-secret@dev205693.service-now.com/api/now/table/rm_story"
            "?access_token=query-secret&sysparm_limit=1"
        ),
    )

    sanitized = request.sanitized()

    assert "url-secret" in request.url
    assert "query-secret" in request.url
    assert "url-secret" not in sanitized.url
    assert "query-secret" not in sanitized.url
    assert "access_token=***REDACTED***" in sanitized.url
    assert "sysparm_limit=1" in sanitized.url
