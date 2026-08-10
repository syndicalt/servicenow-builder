"""Secret redaction for runtime surfaces: handler errors and diagnostic output."""

from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import urlsplit

from jedi_devproject.diagnostic_redaction import (
    _redact_diagnostic_text as _shared_redact_diagnostic_text,
)
from jedi_devproject.exception_diagnostics import exception_diagnostic_message
from jedi_devproject.fulfillment_worker import FulfillmentExecutionResult, FulfillmentHandler
from jedi_devproject.literal_secret_values import safe_literal_secret_values
from jedi_devproject.operational_store import FulfillmentJobRecord
from jedi_devproject.runtime_config import RuntimeSettings


def _redacting_handler(
    *,
    handler: FulfillmentHandler,
    secret_values: Iterable[str],
) -> FulfillmentHandler:
    def handle(job: FulfillmentJobRecord) -> FulfillmentExecutionResult:
        try:
            return handler(job)
        except Exception as exc:
            raise RuntimeError(
                _redact_text(
                    exception_diagnostic_message(exc, fallback_subject="handler"),
                    secret_values,
                )
            ) from None

    return handle


def _runtime_secret_values(settings: RuntimeSettings) -> tuple[str, ...]:
    values = [
        settings.database_url,
        _url_password(settings.database_url),
        settings.servicenow_client_secret,
        settings.servicenow_pm_client_secret,
        settings.servicenow_dev_client_secret,
        settings.lifecycle_webhook_secret or "",
        settings.lifecycle_webhook_previous_secret or "",
    ]
    return tuple(value for value in values if value)


def _url_password(url: str) -> str:
    try:
        return urlsplit(url).password or ""
    except ValueError:
        return ""


def _redact_text(text: str, secret_values: Iterable[str]) -> str:
    redacted = _redact_literal_secrets(text, secret_values)
    redacted = _shared_redact_diagnostic_text(redacted) or ""
    return _redact_literal_secrets(redacted, secret_values)


def _redact_literal_secrets(text: str, secret_values: Iterable[str]) -> str:
    redacted = text
    for secret in safe_literal_secret_values(secret_values):
        redacted = redacted.replace(secret, "***REDACTED***")
    return redacted


def _redact_diagnostic_text(text: str | None) -> str | None:
    return _shared_redact_diagnostic_text(text)
