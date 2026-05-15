from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Literal, Protocol

from fastapi import FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, ValidationError

from jedi_devproject.lifecycle_events import (
    LifecycleStateChangeEvent,
    plan_story_ready_lifecycle_event,
)
from jedi_devproject.operational_store import FulfillmentJobRecord, LifecycleEventRecord
from jedi_devproject.rate_limit import InMemoryRateLimiter


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
    model_config = ConfigDict(extra="forbid")

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
    webhook_auth_mode: LifecycleWebhookAuthMode = "disabled",
    webhook_secret: str | None = None,
    runtime_environment: str = "development",
    webhook_max_skew_seconds: int = 300,
    max_request_body_bytes: int = 64 * 1024,
    rate_limiter: InMemoryRateLimiter | None = None,
) -> FastAPI:
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
        body = await request.body()
        _require_request_size(body=body, max_request_body_bytes=max_request_body_bytes)
        _require_rate_limit(
            rate_limiter=rate_limiter,
            key=_request_rate_limit_key(request),
        )
        _require_lifecycle_webhook_auth(
            auth_mode=webhook_auth_mode,
            configured_secret=webhook_secret,
            runtime_environment=runtime_environment,
            max_skew_seconds=webhook_max_skew_seconds,
            body=body,
            provided_secret=x_jedi_webhook_secret,
            timestamp_header=x_jedi_webhook_timestamp,
            signature_header=x_jedi_webhook_signature,
        )
        try:
            event = LifecycleStateChangeEvent.model_validate(await request.json())
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=422,
                detail="invalid lifecycle webhook JSON",
            ) from exc
        except ValidationError as exc:
            raise HTTPException(
                status_code=422,
                detail=exc.errors(include_url=False),
            ) from exc

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


def _require_request_size(*, body: bytes, max_request_body_bytes: int) -> None:
    if max_request_body_bytes < 1:
        raise RuntimeError("max_request_body_bytes must be at least 1")
    if len(body) > max_request_body_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="lifecycle webhook payload is too large",
        )


def _require_rate_limit(
    *,
    rate_limiter: InMemoryRateLimiter | None,
    key: str,
) -> None:
    if rate_limiter is None:
        return
    decision = rate_limiter.check(key)
    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="rate limit exceeded",
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )


def _request_rate_limit_key(request: Request) -> str:
    client_host = request.client.host if request.client is not None else "unknown"
    return f"{client_host}:{request.url.path}"


def _require_lifecycle_webhook_auth(
    *,
    auth_mode: LifecycleWebhookAuthMode,
    configured_secret: str | None,
    runtime_environment: str,
    max_skew_seconds: int,
    body: bytes,
    provided_secret: str | None,
    timestamp_header: str | None,
    signature_header: str | None,
) -> None:
    if auth_mode == "disabled":
        if runtime_environment.strip().lower() == "development":
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="lifecycle webhook authentication is disabled",
        )
    if auth_mode == "servicenow_oauth":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="lifecycle webhook auth mode is not implemented: servicenow_oauth",
        )
    secret = _configured_webhook_secret(configured_secret)
    if auth_mode == "shared_secret":
        _require_shared_secret_webhook_auth(
            configured_secret=secret,
            provided_secret=provided_secret,
        )
        return
    if auth_mode == "hmac_sha256":
        _require_hmac_webhook_auth(
            configured_secret=secret,
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


def _configured_webhook_secret(configured_secret: str | None) -> str:
    if not configured_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="lifecycle webhook secret is not configured",
        )
    return configured_secret


def _require_shared_secret_webhook_auth(
    *,
    configured_secret: str,
    provided_secret: str | None,
) -> None:
    if provided_secret is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="lifecycle webhook secret required",
        )
    if not hmac.compare_digest(provided_secret, configured_secret):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="lifecycle webhook secret rejected",
        )


def _require_hmac_webhook_auth(
    *,
    configured_secret: str,
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
    try:
        issued_at = int(timestamp_header)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="lifecycle webhook timestamp invalid",
        ) from exc
    safe_skew = max(max_skew_seconds, 1)
    if abs(int(time.time()) - issued_at) > safe_skew:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="lifecycle webhook timestamp outside replay window",
        )
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
    if not (
        hmac.compare_digest(signature_header, expected_signature)
        or hmac.compare_digest(signature_header, expected_servicenow_signature)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="lifecycle webhook signature rejected",
        )


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
