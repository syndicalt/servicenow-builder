"""External alert delivery primitives.

The runtime owns alert generation separately. This module only sends a bounded,
redacted, HTTPS webhook payload when a caller explicitly invokes it.
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from enum import Enum
from itertools import islice
from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic_core import PydanticSerializationError

from jedi_devproject.alert_webhook_url import validate_alert_webhook_url
from jedi_devproject.fulfillment_worker import FulfillmentWorkerResult
from jedi_devproject.operational_store import FulfillmentJobRecord
from jedi_devproject.runtime_redaction import _redact_diagnostic_text
from jedi_devproject.sensitive_keys import is_sensitive_key
from jedi_devproject.servicenow import (
    HttpRequest,
    HttpResponse,
    HttpTransport,
)


class AlertDeliveryError(RuntimeError):
    """Raised when an external alert delivery attempt is unsafe or unsuccessful."""


MAX_ALERT_RESPONSE_DIAGNOSTIC_CHARS = 4096
MAX_ALERT_RESPONSE_COLLECTION_ITEMS = 100
MAX_ALERT_RESPONSE_KEY_CHARS = 500
MAX_ALERT_RESPONSE_DEPTH = 32
MAX_ALERT_HEADER_VALUE_CHARS = 256
MAX_ALERT_BODY_TEXT_CHARS = 16 * 1024
MAX_STALE_REQUEUE_ALERT_JOB_ID_PREVIEW = 50
ALLOWED_ALERT_SEVERITIES = frozenset({"critical", "warning", "info"})
ALLOWED_ALERT_STATUSES = frozenset({"failed", "rejected", "stale_requeued"})
ALERT_RESPONSE_TRUNCATION_MARKER = "...[truncated]"
ALERT_RESPONSE_CIRCULAR_REFERENCE_MARKER = "[circular reference]"
ALERT_RESPONSE_MAX_DEPTH_MARKER = "[max depth exceeded]"
ALERT_RESPONSE_NON_JSON_VALUE_MARKER = "[non-json value]"
ALERT_WEBHOOK_PAYLOAD_NON_JSON_DIAGNOSTIC = (
    "alert webhook payload contains non-JSON values"
)


class ExternalAlert(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    alert_id: str
    severity: str
    job_id: str
    event_id: str
    story_number: str
    correlation_id: str | None = None
    status: str
    summary: str
    detail: str
    operator_action: str
    created_at: datetime


def worker_failure_alert(
    result: FulfillmentWorkerResult,
    *,
    created_at: datetime,
) -> ExternalAlert:
    _validate_timezone_aware_datetime("created_at", created_at)
    job_id = result.job_id or "unknown"
    story_number = result.story_number or "unknown"
    _validate_header_value("job_id", job_id)
    _validate_header_value("story_number", story_number)
    return _validate_generated_alert(
        ExternalAlert(
            alert_id=f"{job_id}:worker_failed",
            severity="critical",
            job_id=job_id,
            event_id=_event_id_from_job_id(job_id),
            story_number=story_number,
            correlation_id=None,
            status="failed",
            summary="Runtime worker fulfillment failed",
            detail=_safe_alert_detail(result.error_message),
            operator_action="Inspect job events, ServiceNow work notes, and worker logs",
            created_at=created_at,
        )
    )


def rejected_job_alert(job: FulfillmentJobRecord) -> ExternalAlert:
    _validate_timezone_aware_datetime("updated_at", job.updated_at)
    _validate_header_value("job_id", job.job_id)
    _validate_header_value("event_id", job.event_id)
    _validate_header_value("story_number", job.story_number)
    if job.correlation_id:
        _validate_header_value("correlation_id", job.correlation_id)
    return _validate_generated_alert(
        ExternalAlert(
            alert_id=f"{job.job_id}:rejected",
            severity="warning",
            job_id=job.job_id,
            event_id=job.event_id,
            story_number=job.story_number,
            correlation_id=job.correlation_id,
            status="rejected",
            summary="Fulfillment job rejected by lifecycle transition",
            detail=_safe_alert_detail(job.last_error),
            operator_action=(
                "Inspect the story, candidate artifacts, work notes, and job event timeline"
            ),
            created_at=job.updated_at,
        )
    )


def stale_requeue_alert(
    *,
    requeued_at: datetime,
    stale_after_seconds: int,
    requeued_count: int,
    job_ids: list[str],
) -> ExternalAlert:
    _validate_timezone_aware_datetime("requeued_at", requeued_at)
    job_id = job_ids[0] if requeued_count == 1 and job_ids else "multiple"
    story_number = "unknown" if requeued_count == 1 else "multiple"
    _validate_header_value("job_id", job_id)
    _validate_header_value("story_number", story_number)
    job_id_list = _stale_requeue_job_id_preview(job_ids)
    detail = _safe_alert_detail(
        f"Requeued {requeued_count} stale running fulfillment job(s) after "
        f"{stale_after_seconds} seconds without update: {job_id_list}"
    )
    return _validate_generated_alert(
        ExternalAlert(
            alert_id=f"stale-requeue:{_timestamp_id(requeued_at)}",
            severity="warning",
            job_id=job_id,
            event_id=_event_id_from_job_id(job_id),
            story_number=story_number,
            correlation_id=None,
            status="stale_requeued",
            summary="Stale running jobs requeued",
            detail=detail,
            operator_action=("Inspect job events and worker logs before assuming recovery success"),
            created_at=requeued_at,
        )
    )


def _stale_requeue_job_id_preview(job_ids: list[str]) -> str:
    if not job_ids:
        return "none"
    preview = ", ".join(job_ids[:MAX_STALE_REQUEUE_ALERT_JOB_ID_PREVIEW])
    omitted_count = len(job_ids) - MAX_STALE_REQUEUE_ALERT_JOB_ID_PREVIEW
    if omitted_count <= 0:
        return preview
    return f"{preview}; {omitted_count} omitted job id(s)"


def _safe_alert_detail(value: str | None) -> str:
    redacted = _redact_diagnostic_text(value) or ""
    normalized = " ".join(redacted.split())
    if len(normalized) <= MAX_ALERT_BODY_TEXT_CHARS:
        return normalized
    marker = ALERT_RESPONSE_TRUNCATION_MARKER
    return f"{normalized[: MAX_ALERT_BODY_TEXT_CHARS - len(marker)]}{marker}"


def emit_alert_webhook(
    *,
    alert: ExternalAlert,
    webhook_url: str,
    transport: HttpTransport,
    max_body_bytes: int,
) -> HttpResponse:
    _validate_alert_webhook_max_body_bytes(max_body_bytes)
    _validate_https_url(webhook_url)
    _validate_alert_created_at(alert)
    _validate_alert_body_text_fields(alert)
    _validate_alert_routing_fields(alert)
    body = _alert_body_bytes(alert)
    if len(body) > max_body_bytes:
        raise AlertDeliveryError(f"alert webhook payload exceeds {max_body_bytes} bytes")
    request = HttpRequest(
        method="POST",
        url=webhook_url,
        headers=_alert_webhook_headers(alert),
        body_bytes=body,
    )
    try:
        response = transport.send(request)
    except Exception:
        raise AlertDeliveryError("alert webhook transport request failed") from None
    _validate_alert_webhook_response(response)
    if response.status_code >= 400:
        raise AlertDeliveryError(
            "alert webhook delivery failed with status "
            f"{response.status_code}: {_alert_response_diagnostic(response.json_body)}"
        )
    return response


def _validate_alert_webhook_response(response: object) -> None:
    if type(response) is not HttpResponse:
        raise AlertDeliveryError("alert webhook transport returned invalid response")


def _validate_alert_webhook_max_body_bytes(max_body_bytes: object) -> None:
    if (
        isinstance(max_body_bytes, bool)
        or not isinstance(max_body_bytes, int)
        or max_body_bytes < 1
    ):
        raise AlertDeliveryError("alert webhook max body bytes must be a positive integer")


def _alert_body_bytes(alert: ExternalAlert) -> bytes:
    try:
        _ensure_alert_payload_json_safe(alert.model_dump(mode="python", warnings=False))
        payload = _sanitized_alert_payload(alert)
        json.dumps(payload, sort_keys=True, allow_nan=False)
    except PydanticSerializationError:
        raise AlertDeliveryError(ALERT_WEBHOOK_PAYLOAD_NON_JSON_DIAGNOSTIC) from None
    except ValueError:
        raise AlertDeliveryError(
            "alert webhook payload contains non-finite numeric values"
        ) from None
    except TypeError:
        raise AlertDeliveryError(ALERT_WEBHOOK_PAYLOAD_NON_JSON_DIAGNOSTIC) from None
    return json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")


def _sanitized_alert_payload(alert: ExternalAlert) -> dict[str, Any]:
    payload = alert.model_dump(mode="json", warnings=False)
    for field_name in ("summary", "detail", "operator_action"):
        field_value = payload.get(field_name)
        if isinstance(field_value, str):
            payload[field_name] = _safe_alert_detail(field_value)
    return payload


def _ensure_alert_payload_json_safe(value: Any) -> None:
    if (
        value is None
        or type(value) is str
        or type(value) is bool
        or type(value) is int
        or type(value) is datetime
        or isinstance(value, Enum)
    ):
        return
    if type(value) is float:
        if math.isfinite(value):
            return
        raise ValueError("non-finite alert webhook payload value")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("non-JSON alert webhook payload key")
            _ensure_alert_payload_json_safe(item)
        return
    if type(value) is list:
        for item in value:
            _ensure_alert_payload_json_safe(item)
        return
    if type(value) is tuple:
        for item in value:
            _ensure_alert_payload_json_safe(item)
        return
    raise TypeError("non-JSON alert webhook payload value")


def _validate_alert_body_text_fields(alert: ExternalAlert) -> None:
    values_by_field = {
        "severity": alert.severity,
        "status": alert.status,
        "summary": alert.summary,
        "detail": alert.detail,
        "operator_action": alert.operator_action,
    }
    for field_name, value in values_by_field.items():
        if len(value) > MAX_ALERT_BODY_TEXT_CHARS:
            raise AlertDeliveryError(
                f"alert webhook field exceeds {MAX_ALERT_BODY_TEXT_CHARS} characters: {field_name}"
            )


def _validate_alert_routing_fields(alert: ExternalAlert) -> None:
    if alert.severity not in ALLOWED_ALERT_SEVERITIES:
        raise AlertDeliveryError("unsupported alert webhook severity")
    if alert.status not in ALLOWED_ALERT_STATUSES:
        raise AlertDeliveryError("unsupported alert webhook status")


def _validate_alert_created_at(alert: ExternalAlert) -> None:
    _validate_timezone_aware_datetime("created_at", alert.created_at)


def _validate_generated_alert(alert: ExternalAlert) -> ExternalAlert:
    _validate_alert_created_at(alert)
    _validate_alert_body_text_fields(alert)
    _validate_alert_routing_fields(alert)
    _alert_webhook_headers(alert)
    return alert


def _validate_timezone_aware_datetime(field_name: str, value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise AlertDeliveryError(f"alert webhook {field_name} must be timezone-aware")


def _redact_alert_response(value: Any) -> Any:
    return _redact_alert_response_node(value, depth=0, seen_container_ids=set())


def _redact_alert_response_node(
    value: Any,
    *,
    depth: int,
    seen_container_ids: set[int],
) -> Any:
    if depth >= MAX_ALERT_RESPONSE_DEPTH and type(value) in (dict, list, tuple):
        return ALERT_RESPONSE_MAX_DEPTH_MARKER
    if type(value) is dict:
        container_id = id(value)
        if container_id in seen_container_ids:
            return ALERT_RESPONSE_CIRCULAR_REFERENCE_MARKER
        seen_container_ids.add(container_id)
        redacted: dict[str, Any] = {}
        try:
            for key, item in islice(value.items(), MAX_ALERT_RESPONSE_COLLECTION_ITEMS):
                redacted_key = _unique_alert_response_key(redacted, _alert_response_key(key))
                redacted[redacted_key] = _redact_alert_response_value(
                    key,
                    item,
                    depth=depth + 1,
                    seen_container_ids=seen_container_ids,
                )
            omitted_fields = len(value) - MAX_ALERT_RESPONSE_COLLECTION_ITEMS
            if omitted_fields > 0:
                redacted[
                    _unique_alert_response_key(redacted, "__jedi_response_truncated__")
                ] = {
                    "truncated": True,
                    "omitted_fields": omitted_fields,
                }
            return redacted
        finally:
            seen_container_ids.remove(container_id)
    if type(value) is list:
        container_id = id(value)
        if container_id in seen_container_ids:
            return ALERT_RESPONSE_CIRCULAR_REFERENCE_MARKER
        seen_container_ids.add(container_id)
        try:
            redacted_items = [
                _redact_alert_response_node(
                    item,
                    depth=depth + 1,
                    seen_container_ids=seen_container_ids,
                )
                for item in islice(value, MAX_ALERT_RESPONSE_COLLECTION_ITEMS)
            ]
            omitted_items = len(value) - MAX_ALERT_RESPONSE_COLLECTION_ITEMS
            if omitted_items > 0:
                redacted_items.append({"truncated": True, "omitted_items": omitted_items})
            return redacted_items
        finally:
            seen_container_ids.remove(container_id)
    if type(value) is tuple:
        container_id = id(value)
        if container_id in seen_container_ids:
            return ALERT_RESPONSE_CIRCULAR_REFERENCE_MARKER
        seen_container_ids.add(container_id)
        try:
            redacted_items = [
                _redact_alert_response_node(
                    item,
                    depth=depth + 1,
                    seen_container_ids=seen_container_ids,
                )
                for item in islice(value, MAX_ALERT_RESPONSE_COLLECTION_ITEMS)
            ]
            omitted_items = len(value) - MAX_ALERT_RESPONSE_COLLECTION_ITEMS
            if omitted_items > 0:
                redacted_items.append({"truncated": True, "omitted_items": omitted_items})
            return redacted_items
        finally:
            seen_container_ids.remove(container_id)
    if type(value) is str:
        return _bounded_alert_response_text(value)
    if value is None or type(value) is bool or type(value) is int:
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        return ALERT_RESPONSE_NON_JSON_VALUE_MARKER
    return ALERT_RESPONSE_NON_JSON_VALUE_MARKER


def _alert_response_key(key: object) -> str:
    if type(key) is not str:
        return "[non-string key]"
    redacted = _redact_diagnostic_text(key) or ""
    normalized = " ".join(redacted.split())
    if not normalized:
        normalized = "[empty key]"
    if len(normalized) <= MAX_ALERT_RESPONSE_KEY_CHARS:
        return normalized
    marker = ALERT_RESPONSE_TRUNCATION_MARKER
    return f"{normalized[: MAX_ALERT_RESPONSE_KEY_CHARS - len(marker)]}{marker}"


def _unique_alert_response_key(existing: dict[str, Any], key: str) -> str:
    if key not in existing:
        return key
    suffix_index = 2
    while True:
        suffix = f" [duplicate {suffix_index}]"
        candidate = f"{key[: MAX_ALERT_RESPONSE_KEY_CHARS - len(suffix)]}{suffix}"
        if candidate not in existing:
            return candidate
        suffix_index += 1


def _alert_response_diagnostic(value: Any) -> str:
    redacted = _redact_alert_response(value)
    diagnostic = json.dumps(redacted, separators=(",", ":"), sort_keys=True)
    if len(diagnostic) <= MAX_ALERT_RESPONSE_DIAGNOSTIC_CHARS:
        return diagnostic
    marker = ALERT_RESPONSE_TRUNCATION_MARKER
    return f"{diagnostic[: MAX_ALERT_RESPONSE_DIAGNOSTIC_CHARS - len(marker)]}{marker}"


def _bounded_alert_response_text(value: str) -> str:
    redacted = _redact_diagnostic_text(value) or ""
    normalized = " ".join(redacted.split())
    if len(normalized) <= MAX_ALERT_RESPONSE_DIAGNOSTIC_CHARS:
        return normalized
    marker = ALERT_RESPONSE_TRUNCATION_MARKER
    return f"{normalized[: MAX_ALERT_RESPONSE_DIAGNOSTIC_CHARS - len(marker)]}{marker}"


def _redact_alert_response_value(
    key: object,
    value: Any,
    *,
    depth: int,
    seen_container_ids: set[int],
) -> Any:
    if is_sensitive_key(key):
        return "***REDACTED***"
    return _redact_alert_response_node(
        value,
        depth=depth,
        seen_container_ids=seen_container_ids,
    )


def _alert_webhook_headers(alert: ExternalAlert) -> dict[str, str]:
    _validate_header_value("alert_id", alert.alert_id)
    _validate_header_value("job_id", alert.job_id)
    _validate_header_value("event_id", alert.event_id)
    _validate_header_value("story_number", alert.story_number)
    if alert.correlation_id:
        _validate_header_value("correlation_id", alert.correlation_id)
    headers = {
        "Content-Type": "application/json",
        "Idempotency-Key": alert.alert_id,
        "X-JEDI-Alert-ID": alert.alert_id,
        "X-JEDI-Job-ID": alert.job_id,
        "X-JEDI-Event-ID": alert.event_id,
        "X-JEDI-Story-Number": alert.story_number,
    }
    if alert.correlation_id:
        headers["X-JEDI-Correlation-ID"] = alert.correlation_id
    return headers


def _validate_header_value(field_name: str, value: str) -> None:
    if value == "" or value != value.strip():
        raise AlertDeliveryError(f"unsafe alert webhook header: {field_name}")
    if len(value) > MAX_ALERT_HEADER_VALUE_CHARS:
        raise AlertDeliveryError(f"unsafe alert webhook header: {field_name}")
    if any(_unsafe_header_character(character) for character in value):
        raise AlertDeliveryError(f"unsafe alert webhook header: {field_name}")


def _unsafe_header_character(character: str) -> bool:
    codepoint = ord(character)
    return codepoint < 32 or codepoint == 127


def _validate_https_url(webhook_url: str) -> None:
    errors = validate_alert_webhook_url(webhook_url)
    if errors:
        raise AlertDeliveryError("; ".join(errors))


def _event_id_from_job_id(job_id: str) -> str:
    if job_id.startswith("job-") and len(job_id) > len("job-"):
        return job_id[len("job-") :]
    return "unknown"


def _timestamp_id(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")
