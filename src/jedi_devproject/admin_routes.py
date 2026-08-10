"""Runtime FastAPI app factory: lifecycle API plus admin artifact and console routes."""

from __future__ import annotations

import html
import json
import math
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from functools import partial
from itertools import islice
from typing import Any, Literal, TypeAlias

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from jedi_devproject.alert_delivery import emit_alert_webhook, rejected_job_alert
from jedi_devproject.lifecycle_api import create_lifecycle_api
from jedi_devproject.operational_store import (
    ArtifactBlobRecord,
    ArtifactRefRecord,
    FulfillmentJobRecord,
    FulfillmentJobStatusSummaryRecord,
    JobEventRecord,
    LifecycleEventRecord,
)
from jedi_devproject.rate_limit import InMemoryRateLimiter
from jedi_devproject.runtime_auth import (
    _require_admin_console_credentials,
    _require_admin_rate_limit,
    _require_admin_token,
)
from jedi_devproject.runtime_config import (
    MAX_PRODUCTION_ADMIN_BODY_BYTES,
    MAX_PRODUCTION_ALERT_WEBHOOK_BODY_BYTES,
    MAX_PRODUCTION_LIFECYCLE_WEBHOOK_BODY_BYTES,
    MAX_PRODUCTION_OUTBOUND_TIMEOUT_SECONDS,
    RuntimeConfigError,
    RuntimeSettings,
    validate_runtime_settings,
)
from jedi_devproject.runtime_redaction import _redact_diagnostic_text
from jedi_devproject.runtime_servicenow import (
    _servicenow_complete_notifier,
    _servicenow_story_client_from_settings,
)
from jedi_devproject.runtime_store import DEFAULT_STORE_FACTORY, RuntimeStore, StoreFactory
from jedi_devproject.sensitive_keys import is_sensitive_key
from jedi_devproject.servicenow import HttpTransport, UrllibTransport
from jedi_devproject.work_note_safety import (
    MAX_WORK_NOTE_VALUE_CHARS,
    WORK_NOTE_TRUNCATION_MARKER,
    safe_work_note_value,
)

OperationalAlertKind: TypeAlias = Literal["failed", "rejected", "running_stale"]
OperationalAlert: TypeAlias = tuple[FulfillmentJobRecord, OperationalAlertKind]
MAX_ADMIN_JOB_ID_CHARS = 256
MAX_ADMIN_DIAGNOSTIC_CHARS = 4096
MAX_ADMIN_ARTIFACT_PAYLOAD_JSON_CHARS = 16384
MAX_ADMIN_ARTIFACT_COLLECTION_ITEMS = 100
MAX_ADMIN_ARTIFACT_PAYLOAD_DEPTH = 32
ADMIN_DIAGNOSTIC_TRUNCATION_MARKER = "...[truncated]"
ADMIN_EMPTY_PAYLOAD_KEY_LABEL = "[empty key]"
ADMIN_NON_STRING_PAYLOAD_KEY_LABEL = "[non-string key]"
ADMIN_NON_JSON_PAYLOAD_VALUE_LABEL = "[non-json value]"
ADMIN_CIRCULAR_PAYLOAD_VALUE_LABEL = "[circular reference]"
ADMIN_MAX_DEPTH_PAYLOAD_VALUE_LABEL = "[max depth exceeded]"
ADMIN_ARTIFACT_PAYLOAD_NON_FINITE_DIAGNOSTIC = (
    "admin artifact payload diagnostic contains non-finite numeric values"
)
ADMIN_HTML_CONTENT_SECURITY_POLICY = (
    "default-src 'none'; "
    "script-src 'none'; "
    "style-src 'unsafe-inline'; "
    "img-src 'none'; "
    "connect-src 'none'; "
    "object-src 'none'; "
    "base-uri 'none'; "
    "form-action 'none'; "
    "frame-ancestors 'none'"
)
ADMIN_HTML_PERMISSIONS_POLICY = (
    "accelerometer=(), "
    "camera=(), "
    "fullscreen=(), "
    "geolocation=(), "
    "gyroscope=(), "
    "magnetometer=(), "
    "microphone=(), "
    "payment=(), "
    "usb=()"
)


def create_runtime_api(
    *,
    settings: RuntimeSettings,
    store_factory: StoreFactory = DEFAULT_STORE_FACTORY,
    transport: HttpTransport | None = None,
    alert_transport: HttpTransport | None = None,
    lifecycle_rate_limiter: InMemoryRateLimiter | None = None,
    admin_rate_limiter: InMemoryRateLimiter | None = None,
) -> FastAPI:
    if settings.runtime_role == "worker":
        raise RuntimeConfigError("JEDI_RUNTIME_ROLE=worker cannot run the runtime API")
    validate_runtime_settings(settings)
    _validate_alert_webhook_runtime_settings(settings)
    _validate_runtime_api_request_body_settings(settings)
    lifecycle_limiter = lifecycle_rate_limiter or _rate_limiter(
        max_requests=settings.lifecycle_rate_limit_max_requests,
        window_seconds=settings.lifecycle_rate_limit_window_seconds,
        max_buckets=settings.lifecycle_rate_limit_max_buckets,
        max_requests_setting="JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS",
        window_seconds_setting="JEDI_LIFECYCLE_RATE_LIMIT_WINDOW_SECONDS",
        max_buckets_setting="JEDI_LIFECYCLE_RATE_LIMIT_MAX_BUCKETS",
    )
    admin_limiter = admin_rate_limiter or _rate_limiter(
        max_requests=settings.admin_rate_limit_max_requests,
        window_seconds=settings.admin_rate_limit_window_seconds,
        max_buckets=settings.admin_rate_limit_max_buckets,
        max_requests_setting="JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS",
        window_seconds_setting="JEDI_ADMIN_RATE_LIMIT_WINDOW_SECONDS",
        max_buckets_setting="JEDI_ADMIN_RATE_LIMIT_MAX_BUCKETS",
    )
    store = store_factory(settings.database_url)
    request_transport = transport or UrllibTransport()
    alert_delivery_transport: HttpTransport | None = None
    if settings.alert_webhook_enabled and settings.alert_webhook_url:
        alert_delivery_transport = alert_transport or UrllibTransport(
            timeout_seconds=settings.alert_webhook_timeout_seconds
        )
    story_client = _servicenow_story_client_from_settings(
        settings=settings,
        transport=request_transport,
    )
    app = create_lifecycle_api(
        store=store,
        complete_notifier=_servicenow_complete_notifier(client=story_client),
        rejected_job_notifier=(
            partial(
                _emit_rejected_job_alert,
                settings=settings,
                transport=alert_delivery_transport,
            )
            if alert_delivery_transport is not None
            else None
        ),
        webhook_auth_mode=settings.lifecycle_webhook_auth_mode,
        webhook_secret=settings.lifecycle_webhook_secret,
        webhook_previous_secret=settings.lifecycle_webhook_previous_secret,
        runtime_environment=settings.runtime_environment,
        webhook_max_skew_seconds=settings.lifecycle_webhook_max_skew_seconds,
        max_request_body_bytes=settings.lifecycle_webhook_max_body_bytes,
        rate_limiter=lifecycle_limiter,
    )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": _validation_errors_without_input(exc.errors())},
        )

    @app.get("/ready")
    def readiness() -> JSONResponse:
        try:
            schema_ready = store.verify_schema_ready()
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "unready",
                    "checks": [{"name": "operational_store", "status": "failed"}],
                },
            )
        if not schema_ready:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "unready",
                    "checks": [{"name": "operational_store_schema", "status": "missing"}],
                },
            )
        return JSONResponse(
            content={
                "status": "ready",
                "checks": [{"name": "operational_store", "status": "ok"}],
            }
        )

    @app.middleware("http")
    async def reject_oversized_admin_requests(
        request: Request,
        call_next: Any,
    ) -> Any:
        if _is_admin_diagnostic_path(request.url.path):
            size_error = await _admin_request_size_error(
                request=request,
                max_request_body_bytes=settings.admin_max_body_bytes,
            )
            if size_error is not None:
                return size_error
        return await call_next(request)

    @app.middleware("http")
    async def apply_runtime_security_headers(
        request: Request,
        call_next: Any,
    ) -> Any:
        response = await call_next(request)
        if "x-jedi-request-id" not in response.headers:
            response.headers["X-JEDI-Request-ID"] = _request_id_for_response(request)
        if "x-content-type-options" not in response.headers:
            response.headers["X-Content-Type-Options"] = "nosniff"
        if (
            settings.strict_transport_security_enabled
            and "strict-transport-security" not in response.headers
        ):
            response.headers["Strict-Transport-Security"] = (
                f"max-age={settings.strict_transport_security_max_age_seconds}; includeSubDomains"
            )
        if _is_admin_diagnostic_path(request.url.path):
            if "cache-control" not in response.headers:
                response.headers["Cache-Control"] = "no-store"
            if "pragma" not in response.headers:
                response.headers["Pragma"] = "no-cache"
            if "expires" not in response.headers:
                response.headers["Expires"] = "0"
            if "x-robots-tag" not in response.headers:
                response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
            _add_vary_header(response.headers, "Authorization")
        if _is_admin_html_path(request.url.path):
            if "content-security-policy" not in response.headers:
                response.headers["Content-Security-Policy"] = ADMIN_HTML_CONTENT_SECURITY_POLICY
            if "x-frame-options" not in response.headers:
                response.headers["X-Frame-Options"] = "DENY"
            if "referrer-policy" not in response.headers:
                response.headers["Referrer-Policy"] = "no-referrer"
            if "permissions-policy" not in response.headers:
                response.headers["Permissions-Policy"] = ADMIN_HTML_PERMISSIONS_POLICY
        return response

    @app.get("/artifacts/{artifact_id}")
    def get_artifact(
        artifact_id: int,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _require_admin_rate_limit(admin_rate_limiter=admin_limiter, key="artifacts")
        _require_admin_token(settings=settings, authorization=authorization)
        try:
            artifact = store.get_artifact_blob(artifact_id)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="artifact not found",
            ) from None
        job = _get_job_or_404(store=store, job_id=artifact.job_id)
        return _artifact_blob_response(artifact, job=job)

    @app.get("/jobs/{job_id}/artifacts")
    def list_job_artifacts(
        job_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _require_admin_rate_limit(admin_rate_limiter=admin_limiter, key="job-artifacts")
        _require_admin_token(settings=settings, authorization=authorization)
        _validate_admin_job_id(job_id)
        job = _get_job_or_404(store=store, job_id=job_id)
        return {
            "job_id": job_id,
            "event_id": job.event_id,
            "story_number": job.story_number,
            "correlation_id": job.correlation_id,
            "artifacts": [
                _artifact_ref_response(ref) for ref in store.artifact_refs_for_job(job_id)
            ],
        }

    @app.get("/jobs/{job_id}/events")
    def list_job_events(
        job_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _require_admin_rate_limit(admin_rate_limiter=admin_limiter, key="job-events")
        _require_admin_token(settings=settings, authorization=authorization)
        _validate_admin_job_id(job_id)
        job = _get_job_or_404(store=store, job_id=job_id)
        return {
            "job_id": job_id,
            "event_id": job.event_id,
            "story_number": job.story_number,
            "correlation_id": job.correlation_id,
            "events": [_job_event_response(event) for event in store.job_events_for_job(job_id)],
        }

    @app.get("/admin/lifecycle-events")
    def list_lifecycle_events(
        authorization: str | None = Header(default=None),
        limit: int = 50,
    ) -> dict[str, Any]:
        _require_admin_rate_limit(admin_rate_limiter=admin_limiter, key="lifecycle-events")
        _require_admin_token(settings=settings, authorization=authorization)
        safe_limit = _bounded_limit(limit)
        return {
            "events": [
                _lifecycle_event_response(event)
                for event in store.recent_lifecycle_events(limit=safe_limit)
            ]
        }

    @app.get("/admin/jobs")
    def list_jobs(
        authorization: str | None = Header(default=None),
        limit: int = 50,
    ) -> dict[str, Any]:
        _require_admin_rate_limit(admin_rate_limiter=admin_limiter, key="jobs")
        _require_admin_token(settings=settings, authorization=authorization)
        safe_limit = _bounded_limit(limit)
        return {
            "jobs": [
                _fulfillment_job_response(job)
                for job in store.recent_fulfillment_jobs(limit=safe_limit)
            ]
        }

    @app.get("/admin/alerts")
    def list_alerts(
        authorization: str | None = Header(default=None),
        limit: int = 50,
    ) -> dict[str, Any]:
        _require_admin_rate_limit(admin_rate_limiter=admin_limiter, key="alerts")
        _require_admin_token(settings=settings, authorization=authorization)
        safe_limit = _bounded_limit(limit)
        return {
            "alerts": [
                _operational_alert_response(
                    alert,
                    running_job_stale_after_seconds=settings.running_job_stale_after_seconds,
                )
                for alert in _operational_alerts(
                    store.recent_fulfillment_jobs(limit=safe_limit),
                    running_job_stale_after_seconds=settings.running_job_stale_after_seconds,
                )
            ]
        }

    @app.get("/admin/operations")
    def operational_summary(
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _require_admin_rate_limit(admin_rate_limiter=admin_limiter, key="operations")
        _require_admin_token(settings=settings, authorization=authorization)
        stale_before = datetime.now(UTC) - timedelta(
            seconds=settings.running_job_stale_after_seconds
        )
        summary = store.fulfillment_job_status_summary(stale_before=stale_before)
        return {
            "fulfillment_jobs": _fulfillment_job_status_summary_response(summary),
            "running_job_stale_after_seconds": settings.running_job_stale_after_seconds,
        }

    @app.get("/admin", response_class=HTMLResponse)
    def admin_console(authorization: str | None = Header(default=None)) -> HTMLResponse:
        _require_admin_rate_limit(admin_rate_limiter=admin_limiter, key="admin-console")
        _require_admin_console_credentials(settings=settings, authorization=authorization)
        jobs = store.recent_fulfillment_jobs(limit=25)
        events = store.recent_lifecycle_events(limit=25)
        alerts = _operational_alerts(
            jobs,
            running_job_stale_after_seconds=settings.running_job_stale_after_seconds,
        )
        artifact_refs_by_job = {job.job_id: store.artifact_refs_for_job(job.job_id) for job in jobs}
        return HTMLResponse(
            _admin_console_html(
                jobs=jobs,
                events=events,
                alerts=alerts,
                running_job_stale_after_seconds=settings.running_job_stale_after_seconds,
                artifact_refs_by_job=artifact_refs_by_job,
            )
        )

    @app.get("/admin/artifacts/{artifact_id}", response_class=HTMLResponse)
    def admin_console_artifact(
        artifact_id: int,
        authorization: str | None = Header(default=None),
    ) -> HTMLResponse:
        _require_admin_rate_limit(
            admin_rate_limiter=admin_limiter,
            key="admin-console-artifacts",
        )
        _require_admin_console_credentials(settings=settings, authorization=authorization)
        try:
            artifact = store.get_artifact_blob(artifact_id)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="artifact not found",
            ) from None
        return HTMLResponse(_admin_artifact_html(artifact))

    _apply_trusted_host_middleware(app=app, trusted_hosts=settings.trusted_hosts)
    return app


def _apply_trusted_host_middleware(*, app: FastAPI, trusted_hosts: list[str]) -> None:
    if trusted_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)


def _validation_errors_without_input(
    errors: Sequence[Any],
) -> list[dict[str, Any]]:
    return [
        {key: value for key, value in error.items() if key != "input"}
        for error in errors
        if isinstance(error, dict)
    ]


def _rate_limiter(
    *,
    max_requests: int,
    window_seconds: int,
    max_buckets: int,
    max_requests_setting: str,
    window_seconds_setting: str,
    max_buckets_setting: str,
) -> InMemoryRateLimiter:
    if max_requests < 1:
        raise RuntimeConfigError(f"{max_requests_setting} must be greater than 0")
    if window_seconds < 1:
        raise RuntimeConfigError(f"{window_seconds_setting} must be greater than 0")
    if max_buckets < 1:
        raise RuntimeConfigError(f"{max_buckets_setting} must be greater than 0")
    try:
        return InMemoryRateLimiter(
            max_requests=max_requests,
            window_seconds=window_seconds,
            max_buckets=max_buckets,
        )
    except ValueError as exc:
        message = str(exc)
        if "max_requests" in message:
            raise RuntimeConfigError(f"{max_requests_setting} {message}") from None
        if "window_seconds" in message:
            raise RuntimeConfigError(f"{window_seconds_setting} {message}") from None
        if "max_buckets" in message:
            raise RuntimeConfigError(f"{max_buckets_setting} {message}") from None
        raise RuntimeConfigError("runtime rate limiter configuration is invalid") from None


def _validate_alert_webhook_runtime_settings(settings: RuntimeSettings) -> None:
    if not settings.alert_webhook_enabled or not settings.alert_webhook_url:
        return
    timeout_seconds = settings.alert_webhook_timeout_seconds
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, int | float)
        or not math.isfinite(float(timeout_seconds))
        or timeout_seconds <= 0
    ):
        raise RuntimeConfigError("JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS must be greater than 0")
    if timeout_seconds > MAX_PRODUCTION_OUTBOUND_TIMEOUT_SECONDS:
        raise RuntimeConfigError(
            "JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS must be at most "
            f"{MAX_PRODUCTION_OUTBOUND_TIMEOUT_SECONDS}"
        )
    max_body_bytes = settings.alert_webhook_max_body_bytes
    if (
        isinstance(max_body_bytes, bool)
        or not isinstance(max_body_bytes, int)
        or max_body_bytes <= 0
    ):
        raise RuntimeConfigError("JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES must be greater than 0")
    if max_body_bytes > MAX_PRODUCTION_ALERT_WEBHOOK_BODY_BYTES:
        raise RuntimeConfigError(
            "JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES must be at most "
            f"{MAX_PRODUCTION_ALERT_WEBHOOK_BODY_BYTES}"
        )


def _validate_runtime_api_request_body_settings(settings: RuntimeSettings) -> None:
    _validate_runtime_api_request_body_limit(
        value=settings.lifecycle_webhook_max_body_bytes,
        setting_name="JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES",
        maximum=MAX_PRODUCTION_LIFECYCLE_WEBHOOK_BODY_BYTES,
    )
    _validate_runtime_api_request_body_limit(
        value=settings.admin_max_body_bytes,
        setting_name="JEDI_ADMIN_MAX_BODY_BYTES",
        maximum=MAX_PRODUCTION_ADMIN_BODY_BYTES,
    )


def _validate_runtime_api_request_body_limit(
    *,
    value: object,
    setting_name: str,
    maximum: int,
) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise RuntimeConfigError(f"{setting_name} must be greater than 0")
    if value > maximum:
        raise RuntimeConfigError(f"{setting_name} must be at most {maximum}")


def _emit_rejected_job_alert(
    job: FulfillmentJobRecord,
    *,
    settings: RuntimeSettings,
    transport: HttpTransport,
) -> None:
    if settings.alert_webhook_url is None:
        return
    emit_alert_webhook(
        alert=rejected_job_alert(job),
        webhook_url=settings.alert_webhook_url,
        transport=transport,
        max_body_bytes=settings.alert_webhook_max_body_bytes,
    )


def _is_admin_diagnostic_path(path: str) -> bool:
    return path.startswith(("/admin", "/artifacts/", "/jobs/"))


def _is_admin_html_path(path: str) -> bool:
    return path == "/admin" or path.startswith("/admin/artifacts/")


def _request_id_for_response(request: Request) -> str:
    request_id = request.headers.get("x-request-id")
    if request_id is not None and _safe_request_id(request_id):
        return request_id
    return str(uuid.uuid4())


def _safe_request_id(request_id: str | None) -> bool:
    if request_id is None:
        return False
    if not 1 <= len(request_id) <= 128:
        return False
    return all(
        character.isascii() and (character.isalnum() or character in "-_.")
        for character in request_id
    )


def _add_vary_header(headers: Any, value: str) -> None:
    current_value = headers.get("vary")
    if current_value is None:
        headers["Vary"] = value
        return
    existing_values = [part.strip().lower() for part in current_value.split(",")]
    if value.lower() not in existing_values:
        headers["Vary"] = f"{current_value}, {value}"


async def _admin_request_size_error(
    *,
    request: Any,
    max_request_body_bytes: int,
) -> JSONResponse | None:
    if max_request_body_bytes < 1:
        raise RuntimeError("max_request_body_bytes must be at least 1")
    content_length = request.headers.get("content-length")
    if content_length is None:
        return await _admin_stream_size_error(
            request=request,
            max_request_body_bytes=max_request_body_bytes,
        )
    try:
        body_bytes = int(content_length)
    except ValueError:
        body_bytes = max_request_body_bytes + 1
    if body_bytes > max_request_body_bytes:
        return JSONResponse(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            content={"detail": "admin request payload is too large"},
        )
    return await _admin_stream_size_error(
        request=request,
        max_request_body_bytes=max_request_body_bytes,
    )


async def _admin_stream_size_error(
    *,
    request: Request,
    max_request_body_bytes: int,
) -> JSONResponse | None:
    chunks: list[bytes] = []
    total_size = 0
    async for chunk in request.stream():
        total_size += len(chunk)
        if total_size > max_request_body_bytes:
            return JSONResponse(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                content={"detail": "admin request payload is too large"},
            )
        chunks.append(chunk)
    request._body = b"".join(chunks)
    return None


def _get_job_or_404(*, store: RuntimeStore, job_id: str) -> FulfillmentJobRecord:
    try:
        return store.get_job(job_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="job not found",
        ) from None


def _validate_admin_job_id(job_id: str) -> None:
    if (
        not job_id
        or len(job_id) > MAX_ADMIN_JOB_ID_CHARS
        or job_id != job_id.strip()
        or any(ord(character) < 33 or ord(character) > 126 for character in job_id)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid job id",
        )


def _artifact_blob_response(
    artifact: ArtifactBlobRecord,
    *,
    job: FulfillmentJobRecord,
) -> dict[str, Any]:
    payload, payload_truncated = _admin_artifact_payload_view(artifact.payload_json)
    response = {
        "id": artifact.id,
        "job_id": artifact.job_id,
        "event_id": job.event_id,
        "story_number": artifact.story_number,
        "correlation_id": job.correlation_id,
        "artifact_kind": artifact.artifact_kind,
        "schema_version": artifact.schema_version,
        "sha256": artifact.sha256,
        "created_at": _json_timestamp(artifact.created_at),
        "payload": payload,
    }
    if payload_truncated:
        response["payload_truncated"] = True
    return response


def _artifact_ref_response(ref: ArtifactRefRecord) -> dict[str, Any]:
    return {
        "id": ref.id,
        "job_id": ref.job_id,
        "artifact_kind": ref.artifact_kind,
        "path": _admin_diagnostic_text(ref.path),
        "sha256": ref.sha256,
        "artifact_id": ref.artifact_id,
        "created_at": _json_timestamp(ref.created_at),
    }


def _job_event_response(event: JobEventRecord) -> dict[str, Any]:
    return {
        "id": event.id,
        "job_id": event.job_id,
        "status": event.status,
        "message": _admin_diagnostic_text(event.message),
        "created_at": _json_timestamp(event.created_at),
    }


def _lifecycle_event_response(event: LifecycleEventRecord) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "story_number": event.story_number,
        "correlation_id": event.correlation_id,
        "received_at": _json_timestamp(event.received_at),
        "validation_status": event.validation_status,
    }


def _fulfillment_job_response(job: FulfillmentJobRecord) -> dict[str, Any]:
    return {
        "job_id": job.job_id,
        "event_id": job.event_id,
        "story_number": job.story_number,
        "status": job.status,
        "attempt_count": job.attempt_count,
        "created_at": _json_timestamp(job.created_at),
        "updated_at": _json_timestamp(job.updated_at),
        "locked_by": job.locked_by,
        "locked_at": _json_timestamp(job.locked_at) if job.locked_at is not None else None,
        "correlation_id": job.correlation_id,
        "last_error": _admin_diagnostic_text(job.last_error),
    }


def _fulfillment_job_status_summary_response(
    summary: FulfillmentJobStatusSummaryRecord,
) -> dict[str, int]:
    return {
        "queued": summary.queued,
        "running": summary.running,
        "completed": summary.completed,
        "failed": summary.failed,
        "rejected": summary.rejected,
        "stale_running": summary.stale_running,
        "total": summary.total,
    }


def _operational_alerts(
    jobs: list[FulfillmentJobRecord],
    *,
    running_job_stale_after_seconds: int,
) -> list[OperationalAlert]:
    now = datetime.now(UTC)
    alerts: list[OperationalAlert] = []
    for job in jobs:
        if job.status == "failed":
            alerts.append((job, "failed"))
        elif job.status == "rejected":
            alerts.append((job, "rejected"))
        elif _running_job_is_stale(
            job,
            now=now,
            running_job_stale_after_seconds=running_job_stale_after_seconds,
        ):
            alerts.append((job, "running_stale"))
    return alerts


def _running_job_is_stale(
    job: FulfillmentJobRecord,
    *,
    now: datetime,
    running_job_stale_after_seconds: int,
) -> bool:
    if job.status != "running":
        return False
    updated_at = job.updated_at
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=UTC)
    return (now - updated_at).total_seconds() > running_job_stale_after_seconds


def _operational_alert_response(
    alert: OperationalAlert,
    *,
    running_job_stale_after_seconds: int,
) -> dict[str, Any]:
    job, alert_kind = alert
    return {
        "alert_id": f"{job.job_id}:{alert_kind}",
        "severity": _operational_alert_severity(alert_kind),
        "job_id": job.job_id,
        "event_id": job.event_id,
        "story_number": job.story_number,
        "correlation_id": job.correlation_id,
        "status": job.status,
        "attempt_count": job.attempt_count,
        "updated_at": _json_timestamp(job.updated_at),
        "summary": _operational_alert_summary(alert_kind),
        "detail": _operational_alert_detail(
            job,
            alert_kind=alert_kind,
            running_job_stale_after_seconds=running_job_stale_after_seconds,
        ),
        "operator_action": _operational_alert_operator_action(alert_kind),
    }


def _operational_alert_severity(alert_kind: OperationalAlertKind) -> str:
    if alert_kind == "failed":
        return "critical"
    return "warning"


def _operational_alert_summary(alert_kind: OperationalAlertKind) -> str:
    if alert_kind == "failed":
        return "Fulfillment job failed"
    if alert_kind == "running_stale":
        return "Fulfillment job appears stale"
    return "Fulfillment job requires review"


def _operational_alert_detail(
    job: FulfillmentJobRecord,
    *,
    alert_kind: OperationalAlertKind,
    running_job_stale_after_seconds: int,
) -> str:
    if alert_kind == "running_stale":
        return f"Running job has not updated within {running_job_stale_after_seconds} seconds"
    return _admin_diagnostic_text(job.last_error) or ""


def _operational_alert_operator_action(alert_kind: OperationalAlertKind) -> str:
    if alert_kind == "running_stale":
        return "Inspect worker logs before retrying or restarting work"
    return "Inspect job events and ServiceNow work notes"


def _admin_console_html(
    *,
    jobs: list[FulfillmentJobRecord],
    events: list[LifecycleEventRecord],
    alerts: list[OperationalAlert],
    running_job_stale_after_seconds: int,
    artifact_refs_by_job: dict[str, list[ArtifactRefRecord]],
) -> str:
    alert_rows = "\n".join(
        _admin_alert_row(
            alert,
            running_job_stale_after_seconds=running_job_stale_after_seconds,
        )
        for alert in alerts
    )
    job_rows = "\n".join(
        _admin_job_row(job, artifact_refs_by_job.get(job.job_id, [])) for job in jobs
    )
    event_rows = "\n".join(_admin_event_row(event) for event in events)
    if not alert_rows:
        alert_rows = '<tr><td colspan="8" class="empty">No operational alerts found.</td></tr>'
    if not job_rows:
        job_rows = '<tr><td colspan="8" class="empty">No fulfillment jobs found.</td></tr>'
    if not event_rows:
        event_rows = '<tr><td colspan="5" class="empty">No lifecycle events found.</td></tr>'
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>JEDI Admin Console</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f8fa;
      --panel: #ffffff;
      --border: #d8dee4;
      --text: #24292f;
      --muted: #57606a;
      --accent: #0969da;
      --error: #b42318;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, Helvetica, sans-serif;
      font-size: 14px;
    }}
    header {{
      background: var(--panel);
      border-bottom: 1px solid var(--border);
      padding: 18px 24px;
    }}
    h1 {{
      margin: 0 0 4px;
      font-size: 22px;
      font-weight: 700;
    }}
    header p {{
      margin: 0;
      color: var(--muted);
    }}
    main {{
      padding: 24px;
      display: grid;
      gap: 24px;
    }}
    section {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
    }}
    h2 {{
      margin: 0;
      padding: 14px 16px;
      border-bottom: 1px solid var(--border);
      font-size: 16px;
    }}
    .table-wrap {{ overflow-x: auto; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 920px;
    }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
      font-size: 12px;
    }}
    a {{ color: var(--accent); }}
    .muted {{ color: var(--muted); }}
    .error {{ color: var(--error); }}
    .empty {{
      color: var(--muted);
      text-align: center;
      padding: 22px;
    }}
  </style>
</head>
<body>
  <header>
    <h1>JEDI Admin Console</h1>
    <p>Read-only operational view. ServiceNow remains the user work surface.</p>
  </header>
  <main>
    <section>
      <h2>Operational Alerts</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Severity</th>
              <th>Job</th>
              <th>Story</th>
              <th>Correlation</th>
              <th>Status</th>
              <th>Attempts</th>
              <th>Updated</th>
              <th>Detail</th>
            </tr>
          </thead>
          <tbody>{alert_rows}</tbody>
        </table>
      </div>
    </section>
    <section>
      <h2>Fulfillment Jobs</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Job</th>
              <th>Story</th>
              <th>Correlation</th>
              <th>Status</th>
              <th>Attempts</th>
              <th>Updated</th>
              <th>Locked By</th>
              <th>Last Error</th>
              <th>Artifacts</th>
            </tr>
          </thead>
          <tbody>{job_rows}</tbody>
        </table>
      </div>
    </section>
    <section>
      <h2>Lifecycle Events</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Event</th>
              <th>Type</th>
              <th>Story</th>
              <th>Correlation</th>
              <th>Received</th>
              <th>Validation</th>
            </tr>
          </thead>
          <tbody>{event_rows}</tbody>
        </table>
      </div>
    </section>
  </main>
</body>
</html>"""


def _admin_alert_row(
    alert: OperationalAlert,
    *,
    running_job_stale_after_seconds: int,
) -> str:
    job, _alert_kind = alert
    response = _operational_alert_response(
        alert,
        running_job_stale_after_seconds=running_job_stale_after_seconds,
    )
    detail = _admin_alert_response_text(response.get("detail"), fallback="")
    detail = f'<span class="error">{detail}</span>' if detail else '<span class="muted">None</span>'
    severity = _admin_alert_response_text(
        response.get("severity"),
        fallback="[invalid alert severity]",
    )
    return (
        "<tr>"
        f"<td>{severity}</td>"
        f"<td><code>{_html(job.job_id)}</code></td>"
        f"<td>{_html(job.story_number)}</td>"
        f"<td><code>{_html(job.correlation_id or '')}</code></td>"
        f"<td>{_html(job.status)}</td>"
        f"<td>{job.attempt_count}</td>"
        f"<td>{_html(_json_timestamp(job.updated_at))}</td>"
        f"<td>{detail}</td>"
        "</tr>"
    )


def _admin_alert_response_text(value: object, *, fallback: str) -> str:
    if type(value) is not str:
        return _html(fallback)
    return _html(value)


def _admin_job_row(job: FulfillmentJobRecord, refs: list[ArtifactRefRecord]) -> str:
    artifact_links = ", ".join(_admin_artifact_link(ref) for ref in refs)
    if not artifact_links:
        artifact_links = '<span class="muted">None</span>'
    last_error = _html(_admin_diagnostic_text(job.last_error) or "")
    if last_error:
        last_error = f'<span class="error">{last_error}</span>'
    else:
        last_error = '<span class="muted">None</span>'
    return (
        "<tr>"
        f"<td><code>{_html(job.job_id)}</code></td>"
        f"<td>{_html(job.story_number)}</td>"
        f"<td><code>{_html(job.correlation_id or '')}</code></td>"
        f"<td>{_html(job.status)}</td>"
        f"<td>{job.attempt_count}</td>"
        f"<td>{_html(_json_timestamp(job.updated_at))}</td>"
        f"<td>{_html(job.locked_by or '')}</td>"
        f"<td>{last_error}</td>"
        f"<td>{artifact_links}</td>"
        "</tr>"
    )


def _admin_event_row(event: LifecycleEventRecord) -> str:
    return (
        "<tr>"
        f"<td><code>{_html(event.event_id)}</code></td>"
        f"<td>{_html(event.event_type)}</td>"
        f"<td>{_html(event.story_number)}</td>"
        f"<td><code>{_html(event.correlation_id or '')}</code></td>"
        f"<td>{_html(_json_timestamp(event.received_at))}</td>"
        f"<td>{_html(event.validation_status)}</td>"
        "</tr>"
    )


def _admin_artifact_link(ref: ArtifactRefRecord) -> str:
    label = _html(ref.artifact_kind)
    if ref.artifact_id is None:
        return f"<span>{label}</span>"
    return f'<a href="/admin/artifacts/{ref.artifact_id}">{label}</a>'


def _admin_artifact_html(artifact: ArtifactBlobRecord) -> str:
    payload, payload_truncated = _admin_artifact_payload_view(artifact.payload_json)
    payload_json = _admin_artifact_payload_json(
        payload,
        indent=2,
    )
    payload_truncated_row = ""
    if payload_truncated:
        payload_truncated_row = "<dt>payload_truncated</dt><dd>true</dd>"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Artifact {artifact.id} - JEDI Admin Console</title>
  <style>
    body {{
      margin: 0;
      background: #f6f8fa;
      color: #24292f;
      font-family: Arial, Helvetica, sans-serif;
      font-size: 14px;
    }}
    header {{
      background: #ffffff;
      border-bottom: 1px solid #d8dee4;
      padding: 18px 24px;
    }}
    main {{ padding: 24px; }}
    h1 {{ margin: 0 0 4px; font-size: 22px; }}
    dl {{
      display: grid;
      grid-template-columns: max-content 1fr;
      gap: 8px 14px;
      margin: 0 0 20px;
    }}
    dt {{ color: #57606a; font-weight: 700; }}
    dd {{ margin: 0; }}
    pre {{
      background: #ffffff;
      border: 1px solid #d8dee4;
      border-radius: 8px;
      padding: 16px;
      overflow: auto;
      white-space: pre-wrap;
    }}
    a {{ color: #0969da; }}
  </style>
</head>
<body>
  <header>
    <h1>Artifact {artifact.id}</h1>
    <a href="/admin">Back to Admin Console</a>
  </header>
  <main>
    <dl>
      <dt>Kind</dt><dd>{_html(artifact.artifact_kind)}</dd>
      <dt>Story</dt><dd>{_html(artifact.story_number)}</dd>
      <dt>Job</dt><dd>{_html(artifact.job_id)}</dd>
      <dt>Schema</dt><dd>{_html(artifact.schema_version)}</dd>
      <dt>Created</dt><dd>{_html(_json_timestamp(artifact.created_at))}</dd>
      <dt>SHA-256</dt><dd><code>{_html(artifact.sha256)}</code></dd>
      {payload_truncated_row}
    </dl>
    <pre>{_html(payload_json)}</pre>
  </main>
</body>
</html>"""


def _html(value: str) -> str:
    return html.escape(value, quote=True)


def _admin_artifact_payload_view(value: Any) -> tuple[Any, bool]:
    redacted, traversal_truncated = _bounded_redacted_artifact_payload(value)
    payload_json = _admin_artifact_payload_json(redacted)
    if not traversal_truncated and len(payload_json) <= MAX_ADMIN_ARTIFACT_PAYLOAD_JSON_CHARS:
        return redacted, False
    marker = ADMIN_DIAGNOSTIC_TRUNCATION_MARKER
    preview = payload_json[: MAX_ADMIN_ARTIFACT_PAYLOAD_JSON_CHARS - len(marker)] + marker
    return (
        {
            "truncated": True,
            "original_payload_type": type(value).__name__,
            "diagnostic_preview": preview,
        },
        True,
    )


def _admin_artifact_payload_json(value: Any, *, indent: int | None = None) -> str:
    try:
        return json.dumps(
            value,
            indent=indent,
            sort_keys=True,
            allow_nan=False,
        )
    except ValueError:
        raise ValueError(ADMIN_ARTIFACT_PAYLOAD_NON_FINITE_DIAGNOSTIC) from None


def _bounded_redacted_artifact_payload(value: Any) -> tuple[Any, bool]:
    return _bounded_redacted_artifact_payload_node(
        value,
        depth=0,
        seen_container_ids=set(),
    )


def _bounded_redacted_artifact_payload_node(
    value: Any,
    *,
    depth: int,
    seen_container_ids: set[int],
) -> tuple[Any, bool]:
    if depth >= MAX_ADMIN_ARTIFACT_PAYLOAD_DEPTH and type(value) in (dict, list, tuple):
        return ADMIN_MAX_DEPTH_PAYLOAD_VALUE_LABEL, True
    if type(value) is dict:
        container_id = id(value)
        if container_id in seen_container_ids:
            return ADMIN_CIRCULAR_PAYLOAD_VALUE_LABEL, True
        seen_container_ids.add(container_id)
        redacted: dict[str, Any] = {}
        key_counts: dict[str, int] = {}
        truncated = False
        try:
            for key, item in islice(value.items(), MAX_ADMIN_ARTIFACT_COLLECTION_ITEMS):
                redacted_key = _admin_payload_key(key, key_counts=key_counts)
                if type(key) is str and is_sensitive_key(key):
                    redacted[redacted_key] = "***REDACTED***"
                    continue
                redacted_item, item_truncated = _bounded_redacted_artifact_payload_node(
                    item,
                    depth=depth + 1,
                    seen_container_ids=seen_container_ids,
                )
                redacted[redacted_key] = redacted_item
                truncated = truncated or item_truncated
            omitted_fields = len(value) - MAX_ADMIN_ARTIFACT_COLLECTION_ITEMS
            if omitted_fields > 0:
                marker_key = _admin_payload_key(
                    "__jedi_payload_truncated__",
                    key_counts=key_counts,
                )
                redacted[marker_key] = {
                    "truncated": True,
                    "omitted_fields": omitted_fields,
                }
                truncated = True
            return redacted, truncated
        finally:
            seen_container_ids.remove(container_id)
    if type(value) is list:
        container_id = id(value)
        if container_id in seen_container_ids:
            return ADMIN_CIRCULAR_PAYLOAD_VALUE_LABEL, True
        seen_container_ids.add(container_id)
        redacted_items: list[Any] = []
        truncated = False
        try:
            for item in islice(value, MAX_ADMIN_ARTIFACT_COLLECTION_ITEMS):
                redacted_item, item_truncated = _bounded_redacted_artifact_payload_node(
                    item,
                    depth=depth + 1,
                    seen_container_ids=seen_container_ids,
                )
                redacted_items.append(redacted_item)
                truncated = truncated or item_truncated
            omitted_items = len(value) - MAX_ADMIN_ARTIFACT_COLLECTION_ITEMS
            if omitted_items > 0:
                redacted_items.append({"truncated": True, "omitted_items": omitted_items})
                truncated = True
            return redacted_items, truncated
        finally:
            seen_container_ids.remove(container_id)
    if type(value) is tuple:
        container_id = id(value)
        if container_id in seen_container_ids:
            return ADMIN_CIRCULAR_PAYLOAD_VALUE_LABEL, True
        seen_container_ids.add(container_id)
        redacted_items = []
        truncated = False
        try:
            for item in islice(value, MAX_ADMIN_ARTIFACT_COLLECTION_ITEMS):
                redacted_item, item_truncated = _bounded_redacted_artifact_payload_node(
                    item,
                    depth=depth + 1,
                    seen_container_ids=seen_container_ids,
                )
                redacted_items.append(redacted_item)
                truncated = truncated or item_truncated
            omitted_items = len(value) - MAX_ADMIN_ARTIFACT_COLLECTION_ITEMS
            if omitted_items > 0:
                redacted_items.append({"truncated": True, "omitted_items": omitted_items})
                truncated = True
            return redacted_items, truncated
        finally:
            seen_container_ids.remove(container_id)
    if type(value) is str:
        return _admin_diagnostic_text(value), False
    if value is None or type(value) is bool or type(value) is int:
        return value, False
    if isinstance(value, float):
        if math.isfinite(value):
            return value, False
        return ADMIN_NON_JSON_PAYLOAD_VALUE_LABEL, False
    return ADMIN_NON_JSON_PAYLOAD_VALUE_LABEL, False


def _admin_payload_key(key: object, *, key_counts: dict[str, int]) -> str:
    if type(key) is str:
        redacted_key = safe_work_note_value(key) or ADMIN_EMPTY_PAYLOAD_KEY_LABEL
    else:
        redacted_key = ADMIN_NON_STRING_PAYLOAD_KEY_LABEL
    duplicate_count = key_counts.get(redacted_key, 0)
    key_counts[redacted_key] = duplicate_count + 1
    if duplicate_count == 0:
        return redacted_key
    return _admin_duplicate_payload_key(redacted_key, duplicate_count=duplicate_count)


def _admin_duplicate_payload_key(redacted_key: str, *, duplicate_count: int) -> str:
    suffix = f" [duplicate {duplicate_count + 1}]"
    if len(redacted_key) + len(suffix) <= MAX_WORK_NOTE_VALUE_CHARS:
        return f"{redacted_key}{suffix}"
    prefix_budget = MAX_WORK_NOTE_VALUE_CHARS - len(WORK_NOTE_TRUNCATION_MARKER) - len(suffix)
    return redacted_key[:prefix_budget].rstrip() + WORK_NOTE_TRUNCATION_MARKER + suffix


def _admin_diagnostic_text(value: str | None) -> str | None:
    redacted = _redact_diagnostic_text(value)
    if redacted is None:
        return None
    normalized = " ".join(redacted.split())
    if len(normalized) <= MAX_ADMIN_DIAGNOSTIC_CHARS:
        return normalized
    marker = ADMIN_DIAGNOSTIC_TRUNCATION_MARKER
    return f"{normalized[: MAX_ADMIN_DIAGNOSTIC_CHARS - len(marker)]}{marker}"


def _bounded_limit(limit: int) -> int:
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="admin result limit must be a positive integer",
        )
    return min(limit, 100)


def _json_timestamp(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")
