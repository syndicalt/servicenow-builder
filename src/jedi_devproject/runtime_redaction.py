"""Secret redaction for runtime surfaces: handler errors and diagnostic output."""

from __future__ import annotations

import re
from collections.abc import Iterable
from urllib.parse import urlsplit, urlunsplit

from jedi_devproject.fulfillment_worker import FulfillmentExecutionResult, FulfillmentHandler
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
            raise RuntimeError(_redact_text(str(exc), secret_values)) from exc

    return handle


def _runtime_secret_values(settings: RuntimeSettings) -> tuple[str, ...]:
    values = [
        settings.database_url,
        _url_password(settings.database_url),
        settings.servicenow_client_secret,
        settings.servicenow_pm_client_secret,
        settings.servicenow_dev_client_secret,
        settings.lifecycle_webhook_secret or "",
    ]
    return tuple(value for value in values if value)


def _url_password(url: str) -> str:
    try:
        return urlsplit(url).password or ""
    except ValueError:
        return ""


def _redact_text(text: str, secret_values: Iterable[str]) -> str:
    redacted = text
    for secret in sorted(set(secret_values), key=len, reverse=True):
        if secret:
            redacted = redacted.replace(secret, "***REDACTED***")
    return redacted


def _redact_diagnostic_text(text: str | None) -> str | None:
    if text is None:
        return None
    return re.sub(
        r"\b(postgresql|postgres)://[^\s]+",
        lambda match: _redact_url_password(match.group(0)),
        text,
    )


def _redact_url_password(url: str) -> str:
    try:
        parts = urlsplit(url)
    except ValueError:
        return "***REDACTED***"
    if parts.password is None:
        return url
    username = parts.username or ""
    host = parts.hostname or ""
    port = f":{parts.port}" if parts.port is not None else ""
    userinfo = f"{username}:***REDACTED***@"
    netloc = f"{userinfo}{host}{port}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
