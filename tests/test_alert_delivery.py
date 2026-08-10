from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, cast

import pytest

from jedi_devproject.alert_delivery import (
    MAX_ALERT_BODY_TEXT_CHARS,
    AlertDeliveryError,
    ExternalAlert,
    _alert_body_bytes,
    _alert_response_diagnostic,
    _ensure_alert_payload_json_safe,
    emit_alert_webhook,
    rejected_job_alert,
    stale_requeue_alert,
    worker_failure_alert,
)
from jedi_devproject.fulfillment_worker import FulfillmentWorkerResult
from jedi_devproject.operational_store import FulfillmentJobRecord
from jedi_devproject.servicenow import HttpRequest, HttpResponse


class RecordingTransport:
    def __init__(self, responses: list[HttpResponse]) -> None:
        self.responses = responses
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        return self.responses.pop(0)


class ArbitraryAlertResponse:
    status_code = 202
    json_body: dict[str, Any] = {"ok": True}


class HttpResponseSubclass(HttpResponse):
    pass


class SecretBearingAlertTransportError(RuntimeError):
    def __str__(self) -> str:
        return "client_secret=alert-transport-secret"


def _alert(**updates: Any) -> ExternalAlert:
    payload = {
        "alert_id": "job-evt-failed:failed",
        "severity": "critical",
        "job_id": "job-evt-failed",
        "event_id": "evt-failed",
        "story_number": "STRY0010100",
        "correlation_id": "corr-evt-failed",
        "status": "failed",
        "summary": "Fulfillment job failed",
        "detail": "ServiceNow writeback failed",
        "operator_action": "Inspect job events and ServiceNow work notes",
        "created_at": datetime(2026, 5, 13, 17, 0, tzinfo=UTC),
    }
    payload.update(updates)
    return ExternalAlert.model_validate(payload)


def test_emit_alert_webhook_sends_bounded_json_payload() -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    response = emit_alert_webhook(
        alert=_alert(),
        webhook_url="https://alerts.example.gov/jedi",
        transport=transport,
        max_body_bytes=4096,
    )

    assert response.status_code == 202
    assert len(transport.requests) == 1
    request = transport.requests[0]
    assert request.method == "POST"
    assert request.url == "https://alerts.example.gov/jedi"
    assert request.headers == {
        "Content-Type": "application/json",
        "Idempotency-Key": "job-evt-failed:failed",
        "X-JEDI-Alert-ID": "job-evt-failed:failed",
        "X-JEDI-Job-ID": "job-evt-failed",
        "X-JEDI-Event-ID": "evt-failed",
        "X-JEDI-Story-Number": "STRY0010100",
        "X-JEDI-Correlation-ID": "corr-evt-failed",
    }
    assert request.body == {}
    assert request.body_bytes is not None
    assert b'"job_id":"job-evt-failed"' in request.body_bytes
    assert b'"created_at":"2026-05-13T17:00:00Z"' in request.body_bytes


@pytest.mark.parametrize(
    "response",
    [
        ArbitraryAlertResponse(),
        HttpResponseSubclass(status_code=202, json_body={"ok": True}),
    ],
)
def test_emit_alert_webhook_rejects_non_exact_transport_responses(
    response: object,
) -> None:
    class MalformedTransport:
        def __init__(self) -> None:
            self.requests: list[HttpRequest] = []

        def send(self, request: HttpRequest) -> object:
            self.requests.append(request)
            return response

    transport = MalformedTransport()

    with pytest.raises(
        AlertDeliveryError,
        match="alert webhook transport returned invalid response",
    ):
        emit_alert_webhook(
            alert=_alert(),
            webhook_url="https://alerts.example.gov/jedi",
            transport=cast(Any, transport),
            max_body_bytes=4096,
        )

    assert len(transport.requests) == 1


def test_emit_alert_webhook_wraps_transport_exceptions_without_leaking_secret() -> None:
    class FailingTransport:
        def __init__(self) -> None:
            self.requests: list[HttpRequest] = []

        def send(self, request: HttpRequest) -> HttpResponse:
            self.requests.append(request)
            raise SecretBearingAlertTransportError()

    transport = FailingTransport()

    with pytest.raises(AlertDeliveryError) as exc_info:
        emit_alert_webhook(
            alert=_alert(),
            webhook_url="https://alerts.example.gov/jedi",
            transport=transport,
            max_body_bytes=4096,
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "alert webhook transport request failed"
    assert exc_info.value.__cause__ is None
    assert "alert-transport-secret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert len(transport.requests) == 1


def test_alert_body_bytes_rejects_non_finite_payload_without_warning_or_leak(
    recwarn: pytest.WarningsRecorder,
) -> None:
    alert = ExternalAlert.model_construct(
        alert_id="job-evt-failed:failed",
        severity="critical",
        job_id="job-evt-failed",
        event_id="evt-failed",
        story_number="STRY0010100",
        correlation_id="corr-secret",
        status="failed",
        summary="Fulfillment job failed",
        detail=float("nan"),
        operator_action="Inspect job events and ServiceNow work notes",
        created_at=datetime(2026, 5, 13, 17, 0, tzinfo=UTC),
    )

    with pytest.raises(AlertDeliveryError) as exc_info:
        _alert_body_bytes(alert)

    diagnostic = str(exc_info.value)
    assert diagnostic == "alert webhook payload contains non-finite numeric values"
    assert exc_info.value.__cause__ is None
    assert "detail" not in diagnostic
    assert "NaN" not in diagnostic
    assert "corr-secret" not in diagnostic
    assert list(recwarn) == []


def test_alert_body_bytes_rejects_non_json_payload_without_warning_or_leak(
    recwarn: pytest.WarningsRecorder,
) -> None:
    class SecretBearingObject:
        def __str__(self) -> str:
            return "client_secret=alert-secret"

    alert = ExternalAlert.model_construct(
        alert_id="job-evt-failed:failed",
        severity="critical",
        job_id="job-evt-failed",
        event_id="evt-failed",
        story_number="STRY0010100",
        correlation_id="corr-secret",
        status="failed",
        summary="Fulfillment job failed",
        detail=SecretBearingObject(),
        operator_action="Inspect job events and ServiceNow work notes",
        created_at=datetime(2026, 5, 13, 17, 0, tzinfo=UTC),
    )

    with pytest.raises(AlertDeliveryError) as exc_info:
        _alert_body_bytes(alert)

    diagnostic = str(exc_info.value)
    assert diagnostic == "alert webhook payload contains non-JSON values"
    assert exc_info.value.__cause__ is None
    assert "detail" not in diagnostic
    assert "SecretBearingObject" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "alert-secret" not in diagnostic
    assert "corr-secret" not in diagnostic
    assert list(recwarn) == []


def test_alert_body_bytes_rejects_string_subclass_payload_without_warning_or_leak(
    recwarn: pytest.WarningsRecorder,
) -> None:
    class HostileAlertText(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=alert-str-secret")

    alert = ExternalAlert.model_construct(
        alert_id="job-evt-failed:failed",
        severity="critical",
        job_id="job-evt-failed",
        event_id="evt-failed",
        story_number="STRY0010100",
        correlation_id="corr-secret",
        status="failed",
        summary="Fulfillment job failed",
        detail=HostileAlertText("alert-secret"),
        operator_action="Inspect job events and ServiceNow work notes",
        created_at=datetime(2026, 5, 13, 17, 0, tzinfo=UTC),
    )

    with pytest.raises(AlertDeliveryError) as exc_info:
        _alert_body_bytes(alert)

    diagnostic = str(exc_info.value)
    assert diagnostic == "alert webhook payload contains non-JSON values"
    assert exc_info.value.__cause__ is None
    assert "detail" not in diagnostic
    assert "HostileAlertText" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "alert-secret" not in diagnostic
    assert "corr-secret" not in diagnostic
    assert list(recwarn) == []


def test_alert_payload_rejects_container_subclasses_without_payload_leak() -> None:
    class HostileAlertPayloadDict(dict[str, Any]):
        def items(self) -> Any:
            raise AssertionError("client_secret=alert-payload-dict-subclass-secret")

    class HostileAlertPayloadList(list[Any]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=alert-payload-list-subclass-secret")

    class HostileAlertPayloadTuple(tuple[Any, ...]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=alert-payload-tuple-subclass-secret")

    for value in (
        HostileAlertPayloadDict({"client_secret": "hidden dict"}),
        HostileAlertPayloadList(["hidden list"]),
        HostileAlertPayloadTuple(("hidden tuple",)),
    ):
        with pytest.raises(TypeError) as exc_info:
            _ensure_alert_payload_json_safe(value)

        diagnostic = str(exc_info.value)
        assert diagnostic == "non-JSON alert webhook payload value"
        assert "HostileAlertPayload" not in diagnostic
        assert "client_secret" not in diagnostic
        assert "subclass-secret" not in diagnostic
        assert "hidden" not in diagnostic


def test_emit_alert_webhook_omits_empty_correlation_header() -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    emit_alert_webhook(
        alert=_alert(correlation_id=None),
        webhook_url="https://alerts.example.gov/jedi",
        transport=transport,
        max_body_bytes=4096,
    )

    assert len(transport.requests) == 1
    assert "X-JEDI-Correlation-ID" not in transport.requests[0].headers
    assert transport.requests[0].headers["Idempotency-Key"] == "job-evt-failed:failed"


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("alert_id", "job-evt-failed:failed\r\nX-Injected: true"),
        ("job_id", "job-evt-failed\nX-Injected: true"),
        ("event_id", "evt-failed\rX-Injected: true"),
        ("story_number", "STRY0010100\x1f"),
        ("correlation_id", "corr-evt-failed\nX-Injected: true"),
    ],
)
def test_emit_alert_webhook_rejects_unsafe_header_values_before_send(
    field_name: str,
    field_value: str,
) -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    with pytest.raises(AlertDeliveryError, match=f"unsafe alert webhook header: {field_name}"):
        emit_alert_webhook(
            alert=_alert(**{field_name: field_value}),
            webhook_url="https://alerts.example.gov/jedi",
            transport=transport,
            max_body_bytes=4096,
        )

    assert transport.requests == []


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("alert_id", "alert-" + ("x" * 300)),
        ("job_id", "job-" + ("x" * 300)),
        ("event_id", "evt-" + ("x" * 300)),
        ("story_number", "STRY" + ("1" * 300)),
        ("correlation_id", "corr-" + ("x" * 300)),
    ],
)
def test_emit_alert_webhook_rejects_oversized_header_values_before_send(
    field_name: str,
    field_value: str,
) -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    with pytest.raises(AlertDeliveryError, match=f"unsafe alert webhook header: {field_name}"):
        emit_alert_webhook(
            alert=_alert(**{field_name: field_value}),
            webhook_url="https://alerts.example.gov/jedi",
            transport=transport,
            max_body_bytes=4096,
        )

    assert transport.requests == []


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("alert_id", ""),
        ("job_id", " "),
        ("event_id", "evt-failed "),
        ("story_number", " STRY0010100"),
        ("correlation_id", " corr-evt-failed "),
    ],
)
def test_emit_alert_webhook_rejects_blank_or_padded_header_values_before_send(
    field_name: str,
    field_value: str,
) -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    with pytest.raises(AlertDeliveryError, match=f"unsafe alert webhook header: {field_name}"):
        emit_alert_webhook(
            alert=_alert(**{field_name: field_value}),
            webhook_url="https://alerts.example.gov/jedi",
            transport=transport,
            max_body_bytes=4096,
        )

    assert transport.requests == []


def test_emit_alert_webhook_rejects_oversized_payload_before_send() -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    with pytest.raises(AlertDeliveryError, match="alert webhook payload exceeds"):
        emit_alert_webhook(
            alert=_alert(detail="x" * 5000),
            webhook_url="https://alerts.example.gov/jedi",
            transport=transport,
            max_body_bytes=512,
        )

    assert transport.requests == []


@pytest.mark.parametrize("max_body_bytes", [0, -1, True, "4096"])
def test_emit_alert_webhook_rejects_invalid_max_body_bytes_before_url_validation(
    max_body_bytes: object,
) -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    with pytest.raises(
        AlertDeliveryError,
        match="alert webhook max body bytes must be a positive integer",
    ):
        emit_alert_webhook(
            alert=_alert(),
            webhook_url="http://alerts.example.gov/jedi",
            transport=transport,
            max_body_bytes=max_body_bytes,  # type: ignore[arg-type]
        )

    assert transport.requests == []


def test_emit_alert_webhook_normalizes_alert_body_text_before_send() -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    emit_alert_webhook(
        alert=_alert(
            detail="first line\nsecond line\tapi_key=alert-body-secret",
            operator_action="inspect logs\nthen retry\tcarefully",
        ),
        webhook_url="https://alerts.example.gov/jedi",
        transport=transport,
        max_body_bytes=4096,
    )

    assert len(transport.requests) == 1
    body_bytes = transport.requests[0].body_bytes
    assert body_bytes is not None
    body = json.loads(body_bytes.decode("utf-8"))
    assert body["detail"] == "first line second line api_key=***REDACTED***"
    assert body["operator_action"] == "inspect logs then retry carefully"
    assert "\n" not in body["detail"]
    assert "\t" not in body["detail"]
    assert "alert-body-secret" not in repr(body)


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("severity", "notify"),
        ("status", "retry_later"),
    ],
)
def test_emit_alert_webhook_rejects_unknown_routing_values_before_send(
    field_name: str,
    field_value: str,
) -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])
    alert = _alert().model_copy(update={field_name: field_value})

    with pytest.raises(AlertDeliveryError) as exc:
        emit_alert_webhook(
            alert=alert,
            webhook_url="https://alerts.example.gov/jedi",
            transport=transport,
            max_body_bytes=4096,
        )

    message = str(exc.value)
    assert f"unsupported alert webhook {field_name}" in message
    assert field_value not in message
    assert transport.requests == []


def test_emit_alert_webhook_rejects_naive_created_at_before_serialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    def fail_dumps(*_args: Any, **_kwargs: Any) -> str:
        raise AssertionError("json.dumps should not run for naive alert timestamps")

    monkeypatch.setattr("jedi_devproject.alert_delivery.json.dumps", fail_dumps)

    with pytest.raises(AlertDeliveryError, match="alert webhook created_at must be timezone-aware"):
        emit_alert_webhook(
            alert=_alert(created_at=datetime(2026, 5, 13, 17, 0)),
            webhook_url="https://alerts.example.gov/jedi",
            transport=transport,
            max_body_bytes=4096,
        )

    assert transport.requests == []


def test_emit_alert_webhook_accepts_timezone_aware_created_at() -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    emit_alert_webhook(
        alert=_alert(created_at=datetime(2026, 5, 13, 12, 0, tzinfo=UTC)),
        webhook_url="https://alerts.example.gov/jedi",
        transport=transport,
        max_body_bytes=4096,
    )

    assert len(transport.requests) == 1
    assert transport.requests[0].body_bytes is not None
    assert b'"created_at":"2026-05-13T12:00:00Z"' in transport.requests[0].body_bytes


@pytest.mark.parametrize(
    "field_name",
    ["severity", "status", "summary", "detail", "operator_action"],
)
def test_emit_alert_webhook_rejects_oversized_body_text_before_serialization(
    field_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    def fail_dumps(*_args: Any, **_kwargs: Any) -> str:
        raise AssertionError("json.dumps should not run for oversized alert text")

    monkeypatch.setattr("jedi_devproject.alert_delivery.json.dumps", fail_dumps)

    with pytest.raises(AlertDeliveryError) as exc:
        emit_alert_webhook(
            alert=_alert(**{field_name: "x" * (MAX_ALERT_BODY_TEXT_CHARS + 1)}),
            webhook_url="https://alerts.example.gov/jedi",
            transport=transport,
            max_body_bytes=4096,
        )

    message = str(exc.value)
    assert f"alert webhook field exceeds {MAX_ALERT_BODY_TEXT_CHARS} characters" in message
    assert field_name in message
    assert "xxx" not in message
    assert transport.requests == []


def test_emit_alert_webhook_failure_redacts_sensitive_response_values() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(
                status_code=500,
                json_body={
                    "error": {
                        "message": (
                            "failed with client_secret=string-secret at "
                            "https://user:url-secret@example.gov/hook"
                            "?access_token=query-secret "
                            "Set-Cookie: JSESSIONID=session-secret; HttpOnly "
                            "-----BEGIN PRIVATE KEY-----\n"
                            "private-key-secret-line\n"
                            "-----END PRIVATE KEY-----"
                        ),
                        "access_token": "token-secret",
                        "api_key": "api-key-secret",
                        "api-key": "hyphen-api-key-secret",
                        "x-api-key": "x-api-value",
                        "accessToken": "camel-access-value",
                        "client_secret": "client-secret-value",
                        "client-secret": "hyphen-client-secret",
                        "clientSecret": "camel-client-value",
                        "x-client-secret": "x-client-value",
                        "aws_secret_access_key": "aws-secret-value",
                        "awsSessionToken": "aws-session-value",
                        "azureClientSecret": "azure-secret-value",
                        "Set-Cookie": "structured-cookie-secret",
                        "private_key": "structured-private-key-secret",
                        "privateKey": "structured-camel-private-key-secret",
                        "code": "auth-code-secret",
                        "id_token": "id-token-secret",
                        "secret": "secret-value",
                        "signature": "signature-secret",
                        "token": "generic-token-secret",
                    }
                },
            )
        ]
    )

    with pytest.raises(AlertDeliveryError) as exc:
        emit_alert_webhook(
            alert=_alert(),
            webhook_url="https://alerts.example.gov/jedi",
            transport=transport,
            max_body_bytes=4096,
        )

    message = str(exc.value)
    assert "status 500" in message
    assert "token-secret" not in message
    assert "api-key-secret" not in message
    assert "hyphen-api-key-secret" not in message
    assert "x-api-value" not in message
    assert "camel-access-value" not in message
    assert "client-secret-value" not in message
    assert "hyphen-client-secret" not in message
    assert "camel-client-value" not in message
    assert "x-client-value" not in message
    assert "aws-secret-value" not in message
    assert "aws-session-value" not in message
    assert "azure-secret-value" not in message
    assert "auth-code-secret" not in message
    assert "id-token-secret" not in message
    assert "secret-value" not in message
    assert "signature-secret" not in message
    assert "generic-token-secret" not in message
    assert "string-secret" not in message
    assert "session-secret" not in message
    assert "structured-cookie-secret" not in message
    assert "private-key-secret-line" not in message
    assert "structured-private-key-secret" not in message
    assert "structured-camel-private-key-secret" not in message
    assert "url-secret" not in message
    assert "query-secret" not in message
    assert "***REDACTED***" in message


def test_emit_alert_webhook_failure_bounds_redacted_response_diagnostics() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(
                status_code=502,
                json_body={"error": ("failed with client_secret=response-secret " + ("x" * 5000))},
            )
        ]
    )

    with pytest.raises(AlertDeliveryError) as exc:
        emit_alert_webhook(
            alert=_alert(),
            webhook_url="https://alerts.example.gov/jedi",
            transport=transport,
            max_body_bytes=4096,
        )

    message = str(exc.value)
    assert "status 502" in message
    assert len(message) < 4300
    assert "...[truncated]" in message
    assert "response-secret" not in message


def test_emit_alert_webhook_failure_bounds_whole_structured_response_diagnostic() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(
                status_code=503,
                json_body={
                    "errors": [
                        {
                            "message": f"sink failure {index}",
                            "request_id": f"req-{index}",
                        }
                        for index in range(500)
                    ],
                    "client_secret": "structured-secret",
                },
            )
        ]
    )

    with pytest.raises(AlertDeliveryError) as exc:
        emit_alert_webhook(
            alert=_alert(),
            webhook_url="https://alerts.example.gov/jedi",
            transport=transport,
            max_body_bytes=4096,
        )

    message = str(exc.value)
    assert "status 503" in message
    assert len(message) < 4300
    assert "...[truncated]" in message
    assert "structured-secret" not in message
    assert "sink failure 499" not in message


def test_alert_response_diagnostic_does_not_consume_all_fields_for_wide_response() -> None:
    payload = {f"field_{index}": f"value-{index}" for index in range(150)}

    diagnostic = _alert_response_diagnostic(payload)

    assert '"omitted_fields":50' in diagnostic
    assert "field_149" not in diagnostic
    assert len(diagnostic) < 4300


def test_alert_response_diagnostic_rejects_container_subclasses() -> None:
    class HostileAlertResponseDict(dict[str, Any]):
        def items(self) -> Any:
            raise AssertionError("client_secret=alert-dict-subclass-secret")

    class HostileAlertResponseList(list[Any]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=alert-list-subclass-secret")

    class HostileAlertResponseTuple(tuple[Any, ...]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=alert-tuple-subclass-secret")

    diagnostic = _alert_response_diagnostic(
        {
            "dict": HostileAlertResponseDict({"message": "hidden dict"}),
            "list": HostileAlertResponseList(["hidden list"]),
            "tuple": HostileAlertResponseTuple(("hidden tuple",)),
        }
    )

    assert diagnostic.count("[non-json value]") == 3
    assert "hidden dict" not in diagnostic
    assert "hidden list" not in diagnostic
    assert "hidden tuple" not in diagnostic
    assert "subclass-secret" not in diagnostic


def test_alert_response_diagnostic_preserves_user_truncation_marker_key() -> None:
    diagnostic = _alert_response_diagnostic(
        {
            "__jedi_response_truncated__": "user marker value",
            **{f"field_{index}": f"value-{index}" for index in range(101)},
        }
    )

    payload = json.loads(diagnostic)
    assert payload["__jedi_response_truncated__"] == "user marker value"
    assert payload["__jedi_response_truncated__ [duplicate 2]"] == {
        "truncated": True,
        "omitted_fields": 2,
    }
    assert "value-100" not in diagnostic


def test_alert_response_diagnostic_redacts_sensitive_response_keys() -> None:
    diagnostic = _alert_response_diagnostic(
        {
            "client_secret=alert-key-secret": "visible-value",
            "nested": {
                "https://user:url-secret@example.gov/hook?access_token=query-secret": (
                    "nested-value"
                )
            },
        }
    )

    assert "alert-key-secret" not in diagnostic
    assert "url-secret" not in diagnostic
    assert "query-secret" not in diagnostic
    assert "visible-value" in diagnostic
    assert "nested-value" in diagnostic
    assert "***REDACTED***" in diagnostic


def test_alert_response_diagnostic_normalizes_string_values() -> None:
    diagnostic = _alert_response_diagnostic(
        {
            "error": {
                "message": "first line\nsecond line\tapi_key=alert-response-secret",
            }
        }
    )

    assert '"message":"first line second line api_key=***REDACTED***"' in diagnostic
    assert "\\n" not in diagnostic
    assert "\\t" not in diagnostic
    assert "alert-response-secret" not in diagnostic


def test_alert_response_diagnostic_handles_non_string_response_keys() -> None:
    diagnostic = _alert_response_diagnostic(
        {
            ("client_secret", "tuple-secret"): "tuple-key-value",
            object(): "object-key-value",
        }
    )

    assert "tuple-secret" not in diagnostic
    assert "tuple-key-value" in diagnostic
    assert "object-key-value" in diagnostic
    assert "[non-string key]" in diagnostic


def test_alert_response_diagnostic_rejects_string_subclass_keys_without_stringifying() -> None:
    class HostileStringKey(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=alert-key-str-secret")

        def split(self, *_args: Any, **_kwargs: Any) -> list[str]:
            raise AssertionError("client_secret=alert-key-split-secret")

    diagnostic = _alert_response_diagnostic(
        {
            HostileStringKey("client_secret"): "visible diagnostic",
        }
    )

    assert "[non-string key]" in diagnostic
    assert "visible diagnostic" in diagnostic
    assert "alert-key" not in diagnostic
    assert "client_secret" not in diagnostic


def test_alert_response_diagnostic_rejects_string_subclass_values_without_methods() -> None:
    class HostileStringValue(str):
        def split(self, *_args: Any, **_kwargs: Any) -> list[str]:
            raise AssertionError("client_secret=alert-value-split-secret")

    diagnostic = _alert_response_diagnostic(
        {
            "message": HostileStringValue("client_secret=alert-value-secret"),
        }
    )

    assert '"message":"[non-json value]"' in diagnostic
    assert "alert-value" not in diagnostic
    assert "client_secret" not in diagnostic


def test_alert_response_diagnostic_rejects_scalar_subclass_values() -> None:
    class HostileAlertOrder(int):
        def __str__(self) -> str:
            raise AssertionError("client_secret=alert-scalar-secret")

    diagnostic = _alert_response_diagnostic(
        {
            "order": HostileAlertOrder(3),
        }
    )

    assert '"order":"[non-json value]"' in diagnostic
    assert "HostileAlertOrder" not in diagnostic
    assert "alert-scalar-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_alert_response_diagnostic_handles_circular_response_payloads() -> None:
    payload: dict[str, Any] = {"message": "sink failure"}
    payload["self"] = payload

    diagnostic = _alert_response_diagnostic(payload)

    assert '"message":"sink failure"' in diagnostic
    assert '"self":"[circular reference]"' in diagnostic


def test_alert_response_diagnostic_bounds_excessive_response_depth() -> None:
    payload: dict[str, Any] = {"message": "sink failure"}
    for depth in range(40):
        payload = {f"level_{depth}": payload}

    diagnostic = _alert_response_diagnostic(payload)

    assert '"[max depth exceeded]"' in diagnostic
    assert "level_7" not in diagnostic
    assert "sink failure" not in diagnostic


def test_emit_alert_webhook_failure_handles_non_json_response_values() -> None:
    transport = RecordingTransport(
        [
            HttpResponse(
                status_code=502,
                json_body={
                    "error": {
                        "message": "sink returned non-json diagnostic values",
                        "body": b"binary-secret-value",
                        "raw": object(),
                    }
                },
            )
        ]
    )

    with pytest.raises(AlertDeliveryError) as exc:
        emit_alert_webhook(
            alert=_alert(),
            webhook_url="https://alerts.example.gov/jedi",
            transport=transport,
            max_body_bytes=4096,
        )

    message = str(exc.value)
    assert "status 502" in message
    assert '"body":"[non-json value]"' in message
    assert '"raw":"[non-json value]"' in message
    assert "non_json_type" not in message
    assert "bytes" not in message
    assert "object" not in message
    assert "binary-secret-value" not in message
    assert "<object object at" not in message


def test_alert_response_diagnostic_replaces_non_finite_floats() -> None:
    diagnostic = _alert_response_diagnostic(
        {
            "nan": float("nan"),
            "positive_infinity": float("inf"),
            "negative_infinity": float("-inf"),
            "finite": 1.25,
        }
    )

    assert '"finite":1.25' in diagnostic
    assert '"nan":"[non-json value]"' in diagnostic
    assert '"positive_infinity":"[non-json value]"' in diagnostic
    assert '"negative_infinity":"[non-json value]"' in diagnostic
    assert "NaN" not in diagnostic
    assert "Infinity" not in diagnostic


def test_emit_alert_webhook_rejects_non_https_url() -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    with pytest.raises(AlertDeliveryError, match="alert webhook URL must use HTTPS"):
        emit_alert_webhook(
            alert=_alert(),
            webhook_url="http://alerts.example.gov/jedi",
            transport=transport,
            max_body_bytes=4096,
        )

    assert transport.requests == []


def test_emit_alert_webhook_rejects_url_embedded_credentials() -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    with pytest.raises(AlertDeliveryError, match="alert webhook URL must not include credentials"):
        emit_alert_webhook(
            alert=_alert(),
            webhook_url="https://alert-user:alert-secret@alerts.example.gov/jedi",
            transport=transport,
            max_body_bytes=4096,
        )

    assert transport.requests == []


def test_emit_alert_webhook_rejects_url_control_characters() -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    with pytest.raises(
        AlertDeliveryError,
        match="alert webhook URL must not include whitespace or control characters",
    ):
        emit_alert_webhook(
            alert=_alert(),
            webhook_url="https://alerts.example.gov/jedi\r\nX-Injected: value",
            transport=transport,
            max_body_bytes=4096,
        )

    assert transport.requests == []


def test_emit_alert_webhook_rejects_url_encoded_control_characters() -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    with pytest.raises(
        AlertDeliveryError,
        match="alert webhook URL must not include encoded whitespace or control characters",
    ):
        emit_alert_webhook(
            alert=_alert(),
            webhook_url="https://alerts.example.gov/jedi%0aX-Injected",
            transport=transport,
            max_body_bytes=4096,
        )

    assert transport.requests == []


def test_emit_alert_webhook_rejects_integer_loopback_ipv4_url() -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    with pytest.raises(
        AlertDeliveryError,
        match="alert webhook URL must not target local or link-local addresses",
    ):
        emit_alert_webhook(
            alert=_alert(),
            webhook_url="https://2130706433/jedi",
            transport=transport,
            max_body_bytes=4096,
        )

    assert transport.requests == []


def test_emit_alert_webhook_rejects_unicode_dot_loopback_url() -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    with pytest.raises(
        AlertDeliveryError,
        match="alert webhook URL must not target local or link-local addresses",
    ):
        emit_alert_webhook(
            alert=_alert(),
            webhook_url="https://127。0。0。1/jedi",
            transport=transport,
            max_body_bytes=4096,
        )

    assert transport.requests == []


def test_emit_alert_webhook_rejects_semicolon_sensitive_query_parameter() -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    with pytest.raises(
        AlertDeliveryError,
        match="alert webhook URL must not include sensitive query parameters: token",
    ):
        emit_alert_webhook(
            alert=_alert(),
            webhook_url="https://alerts.example.gov/jedi?team=platform;token=secret",
            transport=transport,
            max_body_bytes=4096,
        )

    assert transport.requests == []


def test_emit_alert_webhook_rejects_encoded_separator_sensitive_query_parameter() -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    with pytest.raises(
        AlertDeliveryError,
        match="alert webhook URL must not include sensitive query parameters: token",
    ):
        emit_alert_webhook(
            alert=_alert(),
            webhook_url="https://alerts.example.gov/jedi?team=platform%26token=secret",
            transport=transport,
            max_body_bytes=4096,
        )

    assert transport.requests == []


def test_emit_alert_webhook_rejects_double_encoded_separator_sensitive_query_parameter() -> None:
    transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    with pytest.raises(
        AlertDeliveryError,
        match="alert webhook URL must not include sensitive query parameters: token",
    ):
        emit_alert_webhook(
            alert=_alert(),
            webhook_url="https://alerts.example.gov/jedi?team=platform%2526token=secret",
            transport=transport,
            max_body_bytes=4096,
        )

    assert transport.requests == []


def test_worker_failure_alert_preserves_job_story_and_redacted_message() -> None:
    alert = worker_failure_alert(
        FulfillmentWorkerResult(
            status="failed",
            job_id="job-evt-failed",
            story_number="STRY0010100",
            message=None,
            error_message=(
                "ServiceNow failed at "
                "https://api-user:url-secret@example.service-now.com/api"
                "?access_token=token-secret"
            ),
        ),
        created_at=datetime(2026, 5, 13, 18, 0, tzinfo=UTC),
    )

    assert alert.alert_id == "job-evt-failed:worker_failed"
    assert alert.severity == "critical"
    assert alert.job_id == "job-evt-failed"
    assert alert.event_id == "evt-failed"
    assert alert.story_number == "STRY0010100"
    assert alert.status == "failed"
    assert alert.summary == "Runtime worker fulfillment failed"
    assert "url-secret" not in alert.detail
    assert "token-secret" not in alert.detail
    assert "***REDACTED***" in alert.detail


def test_worker_failure_alert_bounds_generated_detail_after_redaction() -> None:
    alert = worker_failure_alert(
        FulfillmentWorkerResult(
            status="failed",
            job_id="job-evt-failed",
            story_number="STRY0010100",
            message=None,
            error_message="client_secret=worker-secret " + ("x" * 20000),
        ),
        created_at=datetime(2026, 5, 13, 18, 0, tzinfo=UTC),
    )

    assert len(alert.detail) <= MAX_ALERT_BODY_TEXT_CHARS
    assert alert.detail.endswith("...[truncated]")
    assert "worker-secret" not in alert.detail


def test_worker_failure_alert_rejects_naive_created_at() -> None:
    with pytest.raises(
        AlertDeliveryError,
        match="alert webhook created_at must be timezone-aware",
    ):
        worker_failure_alert(
            FulfillmentWorkerResult(
                status="failed",
                job_id="job-evt-failed",
                story_number="STRY0010100",
                message=None,
                error_message="ServiceNow writeback failed",
            ),
            created_at=datetime(2026, 5, 13, 18, 0),
        )


@pytest.mark.parametrize(
    ("field_name", "field_value", "error_field"),
    [
        ("job_id", "job-evt-failed\r\nX-Injected: true", "job_id"),
        ("story_number", " STRY0010100", "story_number"),
    ],
)
def test_worker_failure_alert_rejects_unsafe_generated_metadata(
    field_name: str,
    field_value: str,
    error_field: str,
) -> None:
    with pytest.raises(
        AlertDeliveryError,
        match=f"unsafe alert webhook header: {error_field}",
    ):
        worker_failure_alert(
            FulfillmentWorkerResult(
                status="failed",
                job_id=field_value if field_name == "job_id" else "job-evt-failed",
                story_number=(field_value if field_name == "story_number" else "STRY0010100"),
                message=None,
                error_message="ServiceNow writeback failed",
            ),
            created_at=datetime(2026, 5, 13, 18, 0, tzinfo=UTC),
        )


def test_rejected_job_alert_preserves_job_context_and_redacts_reason() -> None:
    alert = rejected_job_alert(
        FulfillmentJobRecord(
            job_id="job-evt-prior-ready",
            event_id="evt-prior-ready",
            story_number="STRY0010101",
            story_sys_id=None,
            status="rejected",
            attempt_count=1,
            created_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
            updated_at=datetime(2026, 5, 14, 19, 12, tzinfo=UTC),
            locked_by=None,
            locked_at=None,
            last_error=(
                "Story returned to Draft from Ready for Testing; "
                "details=https://api-user:url-secret@example.service-now.com/x"
                "?client_secret=client-secret"
            ),
            correlation_id="corr-prior-ready",
        )
    )

    assert alert.alert_id == "job-evt-prior-ready:rejected"
    assert alert.severity == "warning"
    assert alert.job_id == "job-evt-prior-ready"
    assert alert.event_id == "evt-prior-ready"
    assert alert.story_number == "STRY0010101"
    assert alert.correlation_id == "corr-prior-ready"
    assert alert.status == "rejected"
    assert alert.summary == "Fulfillment job rejected by lifecycle transition"
    assert "url-secret" not in alert.detail
    assert "client-secret" not in alert.detail
    assert "***REDACTED***" in alert.detail
    assert alert.operator_action == (
        "Inspect the story, candidate artifacts, work notes, and job event timeline"
    )
    assert alert.created_at == datetime(2026, 5, 14, 19, 12, tzinfo=UTC)


def test_rejected_job_alert_bounds_generated_detail_after_redaction() -> None:
    alert = rejected_job_alert(
        FulfillmentJobRecord(
            job_id="job-evt-prior-ready",
            event_id="evt-prior-ready",
            story_number="STRY0010101",
            story_sys_id=None,
            status="rejected",
            attempt_count=1,
            created_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
            updated_at=datetime(2026, 5, 14, 19, 12, tzinfo=UTC),
            locked_by=None,
            locked_at=None,
            last_error="client_secret=rejected-secret " + ("x" * 20000),
            correlation_id="corr-prior-ready",
        )
    )

    assert len(alert.detail) <= MAX_ALERT_BODY_TEXT_CHARS
    assert alert.detail.endswith("...[truncated]")
    assert "rejected-secret" not in alert.detail


def test_rejected_job_alert_rejects_naive_updated_at() -> None:
    with pytest.raises(
        AlertDeliveryError,
        match="alert webhook updated_at must be timezone-aware",
    ):
        rejected_job_alert(
            FulfillmentJobRecord(
                job_id="job-evt-prior-ready",
                event_id="evt-prior-ready",
                story_number="STRY0010101",
                story_sys_id=None,
                status="rejected",
                attempt_count=1,
                created_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
                updated_at=datetime(2026, 5, 14, 19, 12),
                locked_by=None,
                locked_at=None,
                last_error="Story returned to Draft from Ready for Testing",
                correlation_id="corr-prior-ready",
            )
        )


@pytest.mark.parametrize(
    ("field_name", "field_value", "error_field"),
    [
        ("job_id", "job-evt-prior-ready\nX-Injected: true", "job_id"),
        ("event_id", "evt-prior-ready\rX-Injected: true", "event_id"),
        ("story_number", "STRY0010101 ", "story_number"),
        ("correlation_id", "corr-prior-ready\nX-Injected: true", "correlation_id"),
    ],
)
def test_rejected_job_alert_rejects_unsafe_generated_metadata(
    field_name: str,
    field_value: str,
    error_field: str,
) -> None:
    with pytest.raises(
        AlertDeliveryError,
        match=f"unsafe alert webhook header: {error_field}",
    ):
        rejected_job_alert(
            FulfillmentJobRecord(
                job_id=(field_value if field_name == "job_id" else "job-evt-prior-ready"),
                event_id=(field_value if field_name == "event_id" else "evt-prior-ready"),
                story_number=(field_value if field_name == "story_number" else "STRY0010101"),
                story_sys_id=None,
                status="rejected",
                attempt_count=1,
                created_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
                updated_at=datetime(2026, 5, 14, 19, 12, tzinfo=UTC),
                locked_by=None,
                locked_at=None,
                last_error="Story returned to Draft from Ready for Testing",
                correlation_id=(
                    field_value if field_name == "correlation_id" else "corr-prior-ready"
                ),
            )
        )


def test_stale_requeue_alert_summarizes_actual_requeued_jobs() -> None:
    requeued_at = datetime(2026, 5, 13, 19, 0, tzinfo=UTC)

    alert = stale_requeue_alert(
        requeued_at=requeued_at,
        stale_after_seconds=900,
        requeued_count=2,
        job_ids=["job-evt-stale-1", "job-evt-stale-2"],
    )

    assert alert.alert_id == "stale-requeue:2026-05-13T19:00:00Z"
    assert alert.severity == "warning"
    assert alert.job_id == "multiple"
    assert alert.event_id == "unknown"
    assert alert.story_number == "multiple"
    assert alert.status == "stale_requeued"
    assert alert.summary == "Stale running jobs requeued"
    assert "2 stale running fulfillment job(s)" in alert.detail
    assert "900 seconds" in alert.detail
    assert "job-evt-stale-1, job-evt-stale-2" in alert.detail
    assert alert.operator_action == (
        "Inspect job events and worker logs before assuming recovery success"
    )
    assert alert.created_at == requeued_at


def test_stale_requeue_alert_bounds_job_id_detail_preview() -> None:
    requeued_at = datetime(2026, 5, 13, 19, 0, tzinfo=UTC)
    job_ids = [f"job-evt-stale-{index:03d}" for index in range(75)]

    alert = stale_requeue_alert(
        requeued_at=requeued_at,
        stale_after_seconds=900,
        requeued_count=75,
        job_ids=job_ids,
    )

    assert "Requeued 75 stale running fulfillment job(s)" in alert.detail
    assert "job-evt-stale-000" in alert.detail
    assert "job-evt-stale-049" in alert.detail
    assert "job-evt-stale-050" not in alert.detail
    assert "25 omitted job id(s)" in alert.detail


def test_stale_requeue_alert_bounds_generated_detail_after_redaction() -> None:
    requeued_at = datetime(2026, 5, 13, 19, 0, tzinfo=UTC)
    oversized_job_id = "job-" + ("x" * 20000)

    alert = stale_requeue_alert(
        requeued_at=requeued_at,
        stale_after_seconds=900,
        requeued_count=2,
        job_ids=[oversized_job_id, "job-evt-stale-2"],
    )

    assert len(alert.detail) <= MAX_ALERT_BODY_TEXT_CHARS
    assert alert.detail.endswith("...[truncated]")


def test_stale_requeue_alert_rejects_unsafe_single_job_metadata() -> None:
    with pytest.raises(
        AlertDeliveryError,
        match="unsafe alert webhook header: job_id",
    ):
        stale_requeue_alert(
            requeued_at=datetime(2026, 5, 13, 19, 0, tzinfo=UTC),
            stale_after_seconds=900,
            requeued_count=1,
            job_ids=["job-evt-stale-1\nX-Injected: true"],
        )


def test_stale_requeue_alert_rejects_naive_requeued_at() -> None:
    with pytest.raises(
        AlertDeliveryError,
        match="alert webhook requeued_at must be timezone-aware",
    ):
        stale_requeue_alert(
            requeued_at=datetime(2026, 5, 13, 19, 0),
            stale_after_seconds=900,
            requeued_count=1,
            job_ids=["job-evt-stale-1"],
        )
