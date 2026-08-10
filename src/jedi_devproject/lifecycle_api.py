from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import logging
import time
from collections.abc import Callable
from typing import Any, Literal, Protocol

from fastapi import FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, ValidationError

from jedi_devproject import lifecycle_webhook_policy
from jedi_devproject.exception_diagnostics import exception_diagnostic_message
from jedi_devproject.lifecycle_events import (
    LifecycleStateChangeEvent,
    plan_story_ready_lifecycle_event,
)
from jedi_devproject.operational_store import FulfillmentJobRecord, LifecycleEventRecord
from jedi_devproject.rate_limit import InMemoryRateLimiter, is_valid_rate_limit_decision

LOGGER = logging.getLogger(__name__)
MAX_LIFECYCLE_WEBHOOK_CREDENTIAL_BYTES = (
    lifecycle_webhook_policy.MAX_LIFECYCLE_WEBHOOK_CREDENTIAL_BYTES
)


class LifecycleCompleteNotifier(Protocol):
    def __call__(
        self,
        *,
        story_number: str,
        story_sys_id: str | None,
        event_id: str,
    ) -> None: ...


LifecycleRejectedJobNotifier = Callable[[FulfillmentJobRecord], None]


class LifecycleEventStore(Protocol):
    def record_lifecycle_event(
        self,
        event: LifecycleStateChangeEvent,
        *,
        validation_status: str = "accepted",
    ) -> LifecycleEventRecord: ...

    def enqueue_fulfillment_job(
        self,
        *,
        event_id: str,
        story_number: str,
    ) -> FulfillmentJobRecord: ...

    def close_latest_fulfillment_job_for_story(
        self,
        *,
        story_number: str,
        event_id: str,
    ) -> FulfillmentJobRecord | None: ...

    def record_rework_requested_for_story(
        self,
        *,
        story_number: str,
        event_id: str,
        target_state: str,
    ) -> FulfillmentJobRecord | None: ...

    def reject_latest_fulfillment_job_for_story(
        self,
        *,
        story_number: str,
        event_id: str,
    ) -> FulfillmentJobRecord | None: ...


class LifecycleWebhookResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    accepted: bool
    event_id: str
    story_number: str
    should_evaluate: bool
    lifecycle_action: str | None
    job_id: str | None
    reasons: list[str]


LifecycleWebhookAuthMode = Literal[
    "disabled",
    "shared_secret",
    "hmac_sha256",
    "servicenow_oauth",
]


def create_lifecycle_api(
    *,
    store: LifecycleEventStore,
    complete_notifier: LifecycleCompleteNotifier | None = None,
    rejected_job_notifier: LifecycleRejectedJobNotifier | None = None,
    webhook_auth_mode: LifecycleWebhookAuthMode = "disabled",
    webhook_secret: str | None = None,
    webhook_previous_secret: str | None = None,
    runtime_environment: str = "production",
    webhook_max_skew_seconds: int = 300,
    max_request_body_bytes: int = 64 * 1024,
    rate_limiter: InMemoryRateLimiter | None = None,
) -> FastAPI:
    _validate_max_request_body_bytes(max_request_body_bytes)
    app = FastAPI(
        title="Jedi DevProject Lifecycle API",
        version="0.2.0",
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post(
        "/lifecycle/events",
        response_model=LifecycleWebhookResponse,
        status_code=status.HTTP_202_ACCEPTED,
    )
    async def receive_lifecycle_event(
        request: Request,
        x_jedi_webhook_secret: str | None = Header(
            default=None,
            alias="X-JEDI-Webhook-Secret",
        ),
        x_jedi_webhook_timestamp: str | None = Header(
            default=None,
            alias="X-JEDI-Webhook-Timestamp",
        ),
        x_jedi_webhook_signature: str | None = Header(
            default=None,
            alias="X-JEDI-Webhook-Signature",
        ),
    ) -> LifecycleWebhookResponse:
        body = await _read_bounded_request_body(
            request,
            max_request_body_bytes=max_request_body_bytes,
        )
        _require_rate_limit(
            rate_limiter=rate_limiter,
            key=_request_rate_limit_key(request),
        )
        _require_lifecycle_webhook_auth(
            auth_mode=webhook_auth_mode,
            configured_secret=webhook_secret,
            configured_previous_secret=webhook_previous_secret,
            runtime_environment=runtime_environment,
            max_skew_seconds=webhook_max_skew_seconds,
            body=body,
            provided_secret=x_jedi_webhook_secret,
            timestamp_header=x_jedi_webhook_timestamp,
            signature_header=x_jedi_webhook_signature,
        )
        try:
            event = LifecycleStateChangeEvent.model_validate(_loads_lifecycle_json(body))
        except ValidationError as exc:
            raise HTTPException(
                status_code=422,
                detail=exc.errors(include_url=False, include_input=False),
            ) from None
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            raise HTTPException(
                status_code=422,
                detail="invalid lifecycle webhook JSON",
            ) from None

        store.record_lifecycle_event(event)
        plan = plan_story_ready_lifecycle_event(event)

        job_id: str | None = None
        if plan.should_evaluate:
            job = store.enqueue_fulfillment_job(
                event_id=event.event_id,
                story_number=event.story_number,
            )
            job_id = job.job_id
        elif plan.lifecycle_action == "close_story":
            closeout_job = store.close_latest_fulfillment_job_for_story(
                story_number=event.story_number,
                event_id=event.event_id,
            )
            job_id = closeout_job.job_id if closeout_job is not None else None
            if complete_notifier is not None:
                complete_notifier(
                    story_number=event.story_number,
                    story_sys_id=event.story_sys_id,
                    event_id=event.event_id,
                )
        elif plan.lifecycle_action == "rework_requested":
            rework_job = store.record_rework_requested_for_story(
                story_number=event.story_number,
                event_id=event.event_id,
                target_state=event.current_state,
            )
            job_id = rework_job.job_id if rework_job is not None else None
        elif plan.lifecycle_action == "story_rejected":
            rejected_job = store.reject_latest_fulfillment_job_for_story(
                story_number=event.story_number,
                event_id=event.event_id,
            )
            job_id = rejected_job.job_id if rejected_job is not None else None
            if rejected_job is not None and rejected_job_notifier is not None:
                _notify_rejected_job(
                    rejected_job_notifier=rejected_job_notifier,
                    job=rejected_job,
                )

        return LifecycleWebhookResponse(
            accepted=True,
            event_id=event.event_id,
            story_number=event.story_number,
            should_evaluate=plan.should_evaluate,
            lifecycle_action=plan.lifecycle_action,
            job_id=job_id,
            reasons=plan.reasons,
        )

    return app


def _validate_max_request_body_bytes(max_request_body_bytes: object) -> None:
    if (
        isinstance(max_request_body_bytes, bool)
        or not isinstance(max_request_body_bytes, int)
        or max_request_body_bytes < 1
    ):
        raise ValueError("max_request_body_bytes must be a positive integer")


async def _read_bounded_request_body(
    request: Any,
    *,
    max_request_body_bytes: int,
) -> bytes:
    if max_request_body_bytes < 1:
        raise RuntimeError("max_request_body_bytes must be at least 1")
    chunks: list[bytes] = []
    total_size = 0
    async for chunk in request.stream():
        total_size += len(chunk)
        if total_size > max_request_body_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="lifecycle webhook payload is too large",
            )
        chunks.append(chunk)
    return b"".join(chunks)


def _notify_rejected_job(
    *,
    rejected_job_notifier: LifecycleRejectedJobNotifier,
    job: FulfillmentJobRecord,
) -> None:
    try:
        rejected_job_notifier(job)
    except Exception as exc:
        LOGGER.warning(
            "rejected job alert delivery failed for job %s: %s",
            job.job_id,
            _redact_lifecycle_diagnostic_text(
                exception_diagnostic_message(exc, fallback_subject="lifecycle")
            ),
        )


def _redact_lifecycle_diagnostic_text(value: str | None) -> str | None:
    from jedi_devproject.runtime_redaction import _redact_diagnostic_text

    return _redact_diagnostic_text(value)


def _require_rate_limit(
    *,
    rate_limiter: InMemoryRateLimiter | None,
    key: str,
) -> None:
    if rate_limiter is None:
        return
    decision = rate_limiter.check(key)
    _validate_lifecycle_rate_limit_decision(decision)
    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="rate limit exceeded",
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )


def _validate_lifecycle_rate_limit_decision(decision: object) -> None:
    if not is_valid_rate_limit_decision(decision):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="lifecycle rate limiter is invalid",
        )


def _request_rate_limit_key(request: Request) -> str:
    client_host = request.client.host if request.client is not None else "unknown"
    return f"{client_host}:{request.url.path}"


def _require_lifecycle_webhook_auth(
    *,
    auth_mode: LifecycleWebhookAuthMode,
    configured_secret: str | None,
    configured_previous_secret: str | None,
    runtime_environment: str,
    max_skew_seconds: int,
    body: bytes,
    provided_secret: str | None,
    timestamp_header: str | None,
    signature_header: str | None,
) -> None:
    if auth_mode == "disabled":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="lifecycle webhook authentication is disabled",
        )
    if auth_mode == "servicenow_oauth":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="lifecycle webhook auth mode is not implemented: servicenow_oauth",
        )
    secrets = _configured_webhook_secrets(
        configured_secret=configured_secret,
        configured_previous_secret=configured_previous_secret,
    )
    if auth_mode == "shared_secret":
        _require_shared_secret_webhook_auth(
            configured_secrets=secrets,
            provided_secret=provided_secret,
        )
        return
    if auth_mode == "hmac_sha256":
        _require_hmac_webhook_auth(
            configured_secrets=secrets,
            max_skew_seconds=max_skew_seconds,
            body=body,
            timestamp_header=timestamp_header,
            signature_header=signature_header,
        )
        return
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"lifecycle webhook auth mode is not supported: {auth_mode}",
    )


def _loads_lifecycle_json(body: bytes) -> Any:
    return json.loads(body, parse_constant=_reject_lifecycle_json_constant)


def _reject_lifecycle_json_constant(_value: str) -> None:
    raise ValueError("non-finite JSON number")


def _configured_webhook_secret(configured_secret: str | None) -> str:
    if not configured_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="lifecycle webhook secret is not configured",
        )
    if _has_padded_or_control_webhook_credential(configured_secret):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="lifecycle webhook secret is invalid",
        )
    return configured_secret


def _configured_webhook_secrets(
    *,
    configured_secret: str | None,
    configured_previous_secret: str | None,
) -> tuple[str, ...]:
    active_secret = _configured_webhook_secret(configured_secret)
    if configured_previous_secret is None:
        return (active_secret,)
    previous_secret = _configured_webhook_secret(configured_previous_secret)
    if previous_secret == active_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="lifecycle webhook secret is invalid",
        )
    return (active_secret, previous_secret)


def _require_shared_secret_webhook_auth(
    *,
    configured_secrets: tuple[str, ...],
    provided_secret: str | None,
) -> None:
    if provided_secret is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="lifecycle webhook secret required",
        )
    if _has_padded_or_control_webhook_credential(provided_secret):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="lifecycle webhook secret rejected",
        )
    matches = [
        hmac.compare_digest(provided_secret, configured_secret)
        for configured_secret in configured_secrets
    ]
    if not any(matches):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="lifecycle webhook secret rejected",
        )


def _require_hmac_webhook_auth(
    *,
    configured_secrets: tuple[str, ...],
    max_skew_seconds: int,
    body: bytes,
    timestamp_header: str | None,
    signature_header: str | None,
) -> None:
    if timestamp_header is None or signature_header is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="lifecycle webhook signature required",
        )
    if (
        _has_padded_or_control_webhook_credential(timestamp_header)
        or not timestamp_header
        or not all("0" <= character <= "9" for character in timestamp_header)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="lifecycle webhook timestamp invalid",
        )
    if _has_padded_or_control_webhook_credential(signature_header):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="lifecycle webhook signature rejected",
        )
    if _has_invalid_hmac_signature_shape(signature_header):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="lifecycle webhook signature rejected",
        )
    try:
        issued_at = int(timestamp_header)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="lifecycle webhook timestamp invalid",
        ) from None
    safe_skew = max(max_skew_seconds, 1)
    if abs(int(time.time()) - issued_at) > safe_skew:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="lifecycle webhook timestamp outside replay window",
        )
    matches: list[bool] = []
    for configured_secret in configured_secrets:
        expected_signature = _hmac_signature(
            configured_secret=configured_secret,
            timestamp=timestamp_header,
            body=body,
        )
        expected_servicenow_signature = _hmac_base64_signature(
            configured_secret=configured_secret,
            timestamp=timestamp_header,
            body=body,
        )
        matches.append(hmac.compare_digest(signature_header, expected_signature))
        matches.append(hmac.compare_digest(signature_header, expected_servicenow_signature))
    if not any(matches):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="lifecycle webhook signature rejected",
        )


def _has_padded_or_control_webhook_credential(value: str) -> bool:
    return lifecycle_webhook_policy.is_malformed_lifecycle_webhook_credential(value)


def _has_invalid_hmac_signature_shape(signature_header: str) -> bool:
    hex_prefix = "sha256="
    base64_prefix = "sha256-base64="
    if signature_header.startswith(hex_prefix):
        digest = signature_header[len(hex_prefix) :]
        return len(digest) != 64 or any(
            character not in "0123456789abcdefABCDEF" for character in digest
        )
    if signature_header.startswith(base64_prefix):
        digest = signature_header[len(base64_prefix) :]
        try:
            decoded_digest = base64.b64decode(digest, validate=True)
        except binascii.Error:
            return True
        return len(decoded_digest) != hashlib.sha256().digest_size
    return True


def _hmac_signature(*, configured_secret: str, timestamp: str, body: bytes) -> str:
    digest = hmac.new(
        configured_secret.encode("utf-8"),
        timestamp.encode("utf-8") + b"." + body,
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={digest}"


def _hmac_base64_signature(*, configured_secret: str, timestamp: str, body: bytes) -> str:
    digest = hmac.new(
        configured_secret.encode("utf-8"),
        timestamp.encode("utf-8") + b"." + body,
        hashlib.sha256,
    ).digest()
    return f"sha256-base64={base64.b64encode(digest).decode('ascii')}"
