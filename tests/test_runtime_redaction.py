from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest

from jedi_devproject.fulfillment_worker import FulfillmentExecutionResult
from jedi_devproject.operational_store import FulfillmentJobRecord
from jedi_devproject.runtime_redaction import _redact_diagnostic_text, _redacting_handler


def _job() -> FulfillmentJobRecord:
    now = datetime.now(UTC)
    return FulfillmentJobRecord(
        job_id="job-1",
        event_id="event-1",
        story_number="STRY0010001",
        story_sys_id="story-sys-id",
        status="queued",
        attempt_count=0,
        created_at=now,
        updated_at=now,
        locked_by=None,
        locked_at=None,
        last_error=None,
        correlation_id="correlation-1",
    )


class _UnstringifiableRuntimeError(RuntimeError):
    def __str__(self) -> str:
        raise ValueError("client-secret-value")


class _HostileDiagnosticText(str):
    def split(self, *_args: object, **_kwargs: object) -> list[str]:
        raise AssertionError("client_secret=diagnostic-subclass-secret")


class _HostileSecretValues:
    def __iter__(self) -> Iterator[str]:
        raise AssertionError("client_secret=handler-secret-iterator")


class _SecretValueSubclass(str):
    pass


def test_redacting_handler_handles_unstringifiable_exceptions_without_leaking_secret() -> None:
    def handler(_job: FulfillmentJobRecord) -> FulfillmentExecutionResult:
        raise _UnstringifiableRuntimeError("unused")

    redacting_handler = _redacting_handler(
        handler=handler,
        secret_values=("client-secret-value",),
    )

    with pytest.raises(RuntimeError) as exc_info:
        redacting_handler(_job())

    assert str(exc_info.value) == "handler raised unstringifiable _UnstringifiableRuntimeError"
    assert exc_info.value.__cause__ is None
    assert "client-secret-value" not in str(exc_info.value)


def test_redacting_handler_sanitizes_unstringifiable_exception_type_label() -> None:
    _UnstringifiableRuntimeError.__name__ = "client-secret-value"

    def handler(_job: FulfillmentJobRecord) -> FulfillmentExecutionResult:
        raise _UnstringifiableRuntimeError("unused")

    try:
        redacting_handler = _redacting_handler(
            handler=handler,
            secret_values=("client-secret-value",),
        )

        with pytest.raises(RuntimeError) as exc_info:
            redacting_handler(_job())
    finally:
        _UnstringifiableRuntimeError.__name__ = "_UnstringifiableRuntimeError"

    assert str(exc_info.value) == "handler raised unstringifiable exception"
    assert "client-secret-value" not in str(exc_info.value)


def test_redacting_handler_ignores_hostile_secret_iterator_without_leaking() -> None:
    def handler(_job: FulfillmentJobRecord) -> FulfillmentExecutionResult:
        raise RuntimeError("handler failed client_secret=payload-secret")

    redacting_handler = _redacting_handler(
        handler=handler,
        secret_values=_HostileSecretValues(),
    )

    with pytest.raises(RuntimeError) as exc_info:
        redacting_handler(_job())

    diagnostic = str(exc_info.value)
    assert diagnostic == "handler failed client_secret=***REDACTED***"
    assert "handler-secret-iterator" not in diagnostic
    assert "payload-secret" not in diagnostic


def test_redacting_handler_ignores_non_exact_literal_secret_values() -> None:
    secret_values: list[Any] = [
        "literal-secret",
        _SecretValueSubclass("subclass-secret"),
        123,
    ]

    def handler(_job: FulfillmentJobRecord) -> FulfillmentExecutionResult:
        raise RuntimeError(
            "handler failed literal-secret subclass-secret client_secret=payload-secret"
        )

    redacting_handler = _redacting_handler(
        handler=handler,
        secret_values=secret_values,
    )

    with pytest.raises(RuntimeError) as exc_info:
        redacting_handler(_job())

    diagnostic = str(exc_info.value)
    assert diagnostic == (
        "handler failed ***REDACTED*** subclass-secret client_secret=***REDACTED***"
    )
    assert "payload-secret" not in diagnostic


@pytest.mark.parametrize(
    "text",
    [
        True,
        123,
        b"client_secret=diagnostic-bytes-secret",
        _HostileDiagnosticText("client_secret=diagnostic-subclass-secret"),
    ],
)
def test_redact_diagnostic_text_rejects_non_exact_strings(text: Any) -> None:
    redacted = _redact_diagnostic_text(text)

    assert redacted == "[non-string diagnostic text]"
    assert "diagnostic-bytes-secret" not in redacted
    assert "diagnostic-subclass-secret" not in redacted


def test_redact_diagnostic_text_masks_sensitive_key_value_assignments() -> None:
    redacted = _redact_diagnostic_text(
        "alert failed client_secret=secret-value access_token: token-value"
    )

    assert redacted == ("alert failed client_secret=***REDACTED*** access_token: ***REDACTED***")
    assert "secret-value" not in redacted
    assert "token-value" not in redacted


def test_redact_diagnostic_text_masks_hyphenated_sensitive_assignments() -> None:
    redacted = _redact_diagnostic_text(
        "alert failed client-secret=secret-value api-key: token-value"
    )

    assert redacted == ("alert failed client-secret=***REDACTED*** api-key: ***REDACTED***")
    assert "secret-value" not in redacted
    assert "token-value" not in redacted


def test_redact_diagnostic_text_masks_x_prefixed_sensitive_assignments() -> None:
    redacted = _redact_diagnostic_text(
        "alert failed x-api-key=api-value x-client-secret: client-value"
    )

    assert redacted == ("alert failed x-api-key=***REDACTED*** x-client-secret: ***REDACTED***")
    assert "api-value" not in redacted
    assert "client-value" not in redacted


def test_redact_diagnostic_text_masks_camel_case_sensitive_assignments() -> None:
    redacted = _redact_diagnostic_text(
        "alert failed clientSecret=client-value accessToken: access-value"
    )

    assert redacted == ("alert failed clientSecret=***REDACTED*** accessToken: ***REDACTED***")
    assert "client-value" not in redacted
    assert "access-value" not in redacted


def test_redact_diagnostic_text_masks_cloud_credential_assignments() -> None:
    redacted = _redact_diagnostic_text(
        "provider failed aws_secret_access_key=aws-secret "
        "awsSessionToken: session-secret azureClientSecret=azure-secret"
    )

    assert redacted == (
        "provider failed aws_secret_access_key=***REDACTED*** "
        "awsSessionToken: ***REDACTED*** azureClientSecret=***REDACTED***"
    )
    assert "aws-secret" not in redacted
    assert "session-secret" not in redacted
    assert "azure-secret" not in redacted


def test_redact_diagnostic_text_masks_bearer_authorization_values() -> None:
    redacted = _redact_diagnostic_text(
        "ServiceNow returned Authorization: Bearer bearer-token-secret for request"
    )

    assert redacted == ("ServiceNow returned Authorization: Bearer ***REDACTED*** for request")
    assert "bearer-token-secret" not in redacted


def test_redact_diagnostic_text_masks_cookie_header_values() -> None:
    redacted = _redact_diagnostic_text(
        "ServiceNow returned Cookie: JSESSIONID=session-secret; route=node-a"
    )

    assert redacted == "ServiceNow returned Cookie: ***REDACTED***"
    assert "session-secret" not in redacted
    assert "node-a" not in redacted


def test_redact_diagnostic_text_masks_set_cookie_header_values_without_eating_next_line() -> None:
    redacted = _redact_diagnostic_text(
        "Set-Cookie: JSESSIONID=session-secret; HttpOnly\nstatus=500"
    )

    assert redacted == "Set-Cookie: ***REDACTED***\nstatus=500"
    assert "session-secret" not in redacted
    assert "HttpOnly" not in redacted


def test_redact_diagnostic_text_masks_quoted_sensitive_assignments_cleanly() -> None:
    redacted = _redact_diagnostic_text(
        "provider failed with client_secret=\"quoted-secret\" and token='single-secret'"
    )

    assert redacted == (
        "provider failed with client_secret=***REDACTED*** and token=***REDACTED***"
    )
    assert "quoted-secret" not in redacted
    assert "single-secret" not in redacted


def test_redact_diagnostic_text_masks_spaced_quoted_sensitive_assignments() -> None:
    redacted = _redact_diagnostic_text(
        'provider failed with client_secret="secret with spaces" '
        "and api-key='api secret with spaces'"
    )

    assert redacted == (
        "provider failed with client_secret=***REDACTED*** and api-key=***REDACTED***"
    )
    assert "secret with spaces" not in redacted
    assert "api secret with spaces" not in redacted


def test_redact_diagnostic_text_masks_multiline_pem_private_keys() -> None:
    redacted = _redact_diagnostic_text(
        "provider failed with key\n"
        "-----BEGIN PRIVATE KEY-----\n"
        "private-key-secret-line\n"
        "-----END PRIVATE KEY-----\n"
        "status=500"
    )

    assert redacted == "provider failed with key\n***REDACTED***\nstatus=500"
    assert "private-key-secret-line" not in redacted
    assert "BEGIN PRIVATE KEY" not in redacted


def test_redact_diagnostic_text_redacts_malformed_url_with_secret_userinfo() -> None:
    redacted = _redact_diagnostic_text(
        "ServiceNow failed at https://api-user:url-secret@example.service-now.com:bad/api"
    )

    assert redacted is not None
    assert "url-secret" not in redacted
    assert "***REDACTED***" in redacted


def test_redact_diagnostic_text_redacts_username_only_url_userinfo() -> None:
    redacted = _redact_diagnostic_text(
        "ServiceNow failed at https://api-token@example.service-now.com/api"
    )

    assert redacted == "ServiceNow failed at https://***REDACTED***@example.service-now.com/api"
    assert "api-token" not in redacted


def test_redact_diagnostic_text_redacts_encoded_sensitive_query_keys() -> None:
    redacted = _redact_diagnostic_text(
        "ServiceNow failed at https://example.service-now.com/api"
        "?client%5Fsecret=encoded-secret&sysparm_limit=1"
    )

    assert redacted == (
        "ServiceNow failed at https://example.service-now.com/api"
        "?client%5Fsecret=***REDACTED***&sysparm_limit=1"
    )
    assert "encoded-secret" not in redacted


def test_redact_diagnostic_text_redacts_hyphenated_sensitive_query_keys() -> None:
    redacted = _redact_diagnostic_text(
        "ServiceNow failed at https://example.service-now.com/api"
        "?client-secret=query-secret&api-key=api-secret"
    )

    assert redacted == (
        "ServiceNow failed at https://example.service-now.com/api"
        "?client-secret=***REDACTED***&api-key=***REDACTED***"
    )
    assert "query-secret" not in redacted
    assert "api-secret" not in redacted


def test_redact_diagnostic_text_redacts_x_prefixed_sensitive_query_keys() -> None:
    redacted = _redact_diagnostic_text(
        "ServiceNow failed at https://example.service-now.com/api"
        "?x-api-key=api-value&x-client-secret=client-value"
    )

    assert redacted == (
        "ServiceNow failed at https://example.service-now.com/api"
        "?x-api-key=***REDACTED***&x-client-secret=***REDACTED***"
    )
    assert "api-value" not in redacted
    assert "client-value" not in redacted


def test_redact_diagnostic_text_redacts_camel_case_sensitive_query_keys() -> None:
    redacted = _redact_diagnostic_text(
        "ServiceNow failed at https://example.service-now.com/api"
        "?clientSecret=client-value&accessToken=access-value"
    )

    assert redacted == (
        "ServiceNow failed at https://example.service-now.com/api"
        "?clientSecret=***REDACTED***&accessToken=***REDACTED***"
    )
    assert "client-value" not in redacted
    assert "access-value" not in redacted


def test_redact_diagnostic_text_redacts_cloud_credential_query_keys() -> None:
    redacted = _redact_diagnostic_text(
        "ServiceNow failed at https://example.service-now.com/api"
        "?awsSecretAccessKey=aws-secret&azureClientSecret=azure-secret"
    )

    assert redacted == (
        "ServiceNow failed at https://example.service-now.com/api"
        "?awsSecretAccessKey=***REDACTED***&azureClientSecret=***REDACTED***"
    )
    assert "aws-secret" not in redacted
    assert "azure-secret" not in redacted


def test_redact_diagnostic_text_redacts_semicolon_separated_encoded_sensitive_query_keys() -> None:
    redacted = _redact_diagnostic_text(
        "ServiceNow failed at https://example.service-now.com/api"
        "?sysparm_limit=1;client%5Fsecret=encoded-secret"
    )

    assert redacted == (
        "ServiceNow failed at https://example.service-now.com/api"
        "?sysparm_limit=1;client%5Fsecret=***REDACTED***"
    )
    assert "encoded-secret" not in redacted
