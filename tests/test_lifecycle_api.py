from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import time
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException
from starlette.requests import Request

from jedi_devproject.lifecycle_api import (
    MAX_LIFECYCLE_WEBHOOK_CREDENTIAL_BYTES,
    _configured_webhook_secret,
    _read_bounded_request_body,
    _require_hmac_webhook_auth,
    _require_rate_limit,
    _require_shared_secret_webhook_auth,
    create_lifecycle_api,
)
from jedi_devproject.lifecycle_events import LifecycleStateChangeEvent
from jedi_devproject.operational_store import FulfillmentJobRecord, LifecycleEventRecord
from jedi_devproject.rate_limit import InMemoryRateLimiter

_TEST_WEBHOOK_SECRET = "test-secret"


def _create_test_lifecycle_api(
    *, store: FakeOperationalStore, **kwargs: Any
) -> Any:
    """Create a lifecycle API configured with a test shared secret for non-auth tests."""
    return create_lifecycle_api(
        store=store,
        webhook_auth_mode="shared_secret",
        webhook_secret=_TEST_WEBHOOK_SECRET,
        **kwargs,
    )


def _test_auth_headers() -> dict[str, str]:
    return {"X-JEDI-Webhook-Secret": _TEST_WEBHOOK_SECRET}


class FakeOperationalStore:
    def __init__(self) -> None:
        self.recorded_events: list[LifecycleStateChangeEvent] = []
        self.enqueued_jobs: list[tuple[str, str]] = []
        self.closed_story_jobs: list[tuple[str, str]] = []
        self.rework_story_jobs: list[tuple[str, str, str]] = []
        self.rejected_story_jobs: list[tuple[str, str]] = []

    def record_lifecycle_event(
        self,
        event: LifecycleStateChangeEvent,
        *,
        validation_status: str = "accepted",
    ) -> LifecycleEventRecord:
        self.recorded_events.append(event)
        return LifecycleEventRecord(
            event_id=event.event_id,
            event_type=event.event_type.value,
            story_number=event.story_number,
            payload_json=event.model_dump(mode="json"),
            received_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
            validation_status=validation_status,
        )

    def enqueue_fulfillment_job(
        self,
        *,
        event_id: str,
        story_number: str,
    ) -> FulfillmentJobRecord:
        self.enqueued_jobs.append((event_id, story_number))
        return FulfillmentJobRecord(
            job_id=f"job-{event_id}",
            event_id=event_id,
            story_number=story_number,
            status="queued",
            attempt_count=0,
            created_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
            updated_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
            locked_by=None,
            locked_at=None,
            last_error=None,
        )

    def close_latest_fulfillment_job_for_story(
        self,
        *,
        story_number: str,
        event_id: str,
    ) -> FulfillmentJobRecord | None:
        self.closed_story_jobs.append((story_number, event_id))
        return FulfillmentJobRecord(
            job_id=f"job-prior-{story_number}",
            event_id="evt-prior-ready",
            story_number=story_number,
            status="completed",
            attempt_count=1,
            created_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
            updated_at=datetime(2026, 5, 14, 18, 45, tzinfo=UTC),
            locked_by=None,
            locked_at=None,
            last_error=None,
        )

    def record_rework_requested_for_story(
        self,
        *,
        story_number: str,
        event_id: str,
        target_state: str,
    ) -> FulfillmentJobRecord | None:
        self.rework_story_jobs.append((story_number, event_id, target_state))
        return FulfillmentJobRecord(
            job_id=f"job-prior-{story_number}",
            event_id="evt-prior-ready",
            story_number=story_number,
            status="completed",
            attempt_count=1,
            created_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
            updated_at=datetime(2026, 5, 14, 19, 10, tzinfo=UTC),
            locked_by=None,
            locked_at=None,
            last_error=None,
        )

    def reject_latest_fulfillment_job_for_story(
        self,
        *,
        story_number: str,
        event_id: str,
    ) -> FulfillmentJobRecord | None:
        self.rejected_story_jobs.append((story_number, event_id))
        return FulfillmentJobRecord(
            job_id=f"job-prior-{story_number}",
            event_id="evt-prior-ready",
            story_number=story_number,
            status="rejected",
            attempt_count=1,
            created_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
            updated_at=datetime(2026, 5, 14, 19, 12, tzinfo=UTC),
            locked_by=None,
            locked_at=None,
            last_error="Story returned to Draft from Ready for Testing",
        )


class FakeCompleteNotifier:
    def __init__(self) -> None:
        self.completed: list[tuple[str, str | None, str]] = []

    def __call__(
        self,
        *,
        story_number: str,
        story_sys_id: str | None,
        event_id: str,
    ) -> None:
        self.completed.append((story_number, story_sys_id, event_id))


class FakeRejectedJobNotifier:
    def __init__(self) -> None:
        self.jobs: list[FulfillmentJobRecord] = []

    def __call__(self, job: FulfillmentJobRecord) -> None:
        self.jobs.append(job)


class FakeStreamingRequest:
    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = chunks

    async def stream(self) -> Any:
        for chunk in self._chunks:
            yield chunk


def _ready_event_payload() -> dict[str, str]:
    return {
        "event_id": "evt-20260513-001",
        "event_type": "story_state_changed",
        "source": "servicenow-business-rule",
        "table": "rm_story",
        "story_number": "STRY0010013",
        "previous_state": "Draft",
        "current_state": "Ready",
        "occurred_at": "2026-05-13T15:45:00Z",
        "correlation_id": "STRY0010013-Draft-Ready-20260513T154500Z",
        "emitted_by": "jedi-devproject-lifecycle-integration",
    }


def _complete_event_payload() -> dict[str, str]:
    payload = _ready_event_payload()
    payload.update(
        {
            "event_id": "evt-20260514-uat-complete",
            "story_number": "STRY0010002",
            "story_sys_id": "story-sys-id-0002",
            "previous_state": "Ready for Testing",
            "current_state": "Complete",
            "occurred_at": "2026-05-14T18:45:00Z",
            "correlation_id": "STRY0010002-ReadyForTesting-Complete-20260514T184500Z",
        }
    )
    return payload


def _ready_rework_event_payload() -> dict[str, str]:
    payload = _complete_event_payload()
    payload.update(
        {
            "event_id": "evt-20260514-uat-rework",
            "current_state": "Ready",
            "occurred_at": "2026-05-14T19:10:00Z",
            "correlation_id": "STRY0010002-ReadyForTesting-Ready-20260514T191000Z",
        }
    )
    return payload


def _draft_rejected_event_payload() -> dict[str, str]:
    payload = _complete_event_payload()
    payload.update(
        {
            "event_id": "evt-20260514-story-rejected",
            "current_state": "Draft",
            "occurred_at": "2026-05-14T19:12:00Z",
            "correlation_id": "STRY0010002-ReadyForTesting-Draft-20260514T191200Z",
        }
    )
    return payload


def _signed_webhook_request(
    payload: dict[str, str],
    *,
    secret: str = "webhook-secret",
    timestamp: int | str | None = None,
) -> tuple[bytes, dict[str, str]]:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    issued_at = str(timestamp if timestamp is not None else int(time.time()))
    digest = hmac.new(
        secret.encode("utf-8"),
        issued_at.encode("utf-8") + b"." + body,
        hashlib.sha256,
    ).hexdigest()
    return body, {
        "content-type": "application/json",
        "X-JEDI-Webhook-Timestamp": issued_at,
        "X-JEDI-Webhook-Signature": f"sha256={digest}",
    }


def _signed_base64_webhook_request(
    payload: dict[str, str],
    *,
    secret: str = "webhook-secret",
    timestamp: int | str | None = None,
) -> tuple[bytes, dict[str, str]]:
    import base64

    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    issued_at = str(timestamp if timestamp is not None else int(time.time()))
    digest = hmac.new(
        secret.encode("utf-8"),
        issued_at.encode("utf-8") + b"." + body,
        hashlib.sha256,
    ).digest()
    return body, {
        "content-type": "application/json",
        "X-JEDI-Webhook-Timestamp": issued_at,
        "X-JEDI-Webhook-Signature": f"sha256-base64={base64.b64encode(digest).decode()}",
    }


def _request_with_body(body: bytes) -> Request:
    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/lifecycle/events",
            "headers": [],
            "query_string": b"",
        },
        receive,
    )


def _lifecycle_events_endpoint(app: Any) -> Any:
    for route in app.routes:
        if getattr(route, "path", None) == "/lifecycle/events":
            return route.endpoint
    raise AssertionError("lifecycle events route was not registered")


def test_lifecycle_webhook_records_ready_event_and_enqueues_fulfillment() -> None:
    store = FakeOperationalStore()
    client = TestClient(_create_test_lifecycle_api(store=store))

    response = client.post(
        "/lifecycle/events",
        json=_ready_event_payload(),
        headers=_test_auth_headers(),
    )

    assert response.status_code == 202
    assert response.json() == {
        "accepted": True,
        "event_id": "evt-20260513-001",
        "story_number": "STRY0010013",
        "should_evaluate": True,
        "lifecycle_action": "evaluate_story",
        "job_id": "job-evt-20260513-001",
        "reasons": [],
    }
    assert [event.event_id for event in store.recorded_events] == ["evt-20260513-001"]
    assert store.enqueued_jobs == [("evt-20260513-001", "STRY0010013")]
    assert store.closed_story_jobs == []


def test_lifecycle_webhook_disabled_auth_rejects_all_environments() -> None:
    store = FakeOperationalStore()
    client = TestClient(
        create_lifecycle_api(
            store=store,
            webhook_auth_mode="disabled",
            runtime_environment="development",
        )
    )

    response = client.post("/lifecycle/events", json=_ready_event_payload())

    assert response.status_code == 503
    assert response.json()["detail"] == "lifecycle webhook authentication is disabled"
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


def test_lifecycle_api_defaults_to_production_runtime_environment() -> None:
    store = FakeOperationalStore()
    client = TestClient(create_lifecycle_api(store=store, webhook_auth_mode="disabled"))

    response = client.post("/lifecycle/events", json=_ready_event_payload())

    assert response.status_code == 503
    assert response.json()["detail"] == "lifecycle webhook authentication is disabled"
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


def test_lifecycle_webhook_rejects_oversized_payload_before_recording() -> None:
    store = FakeOperationalStore()
    client = TestClient(create_lifecycle_api(store=store, max_request_body_bytes=32))

    response = client.post(
        "/lifecycle/events",
        content=json.dumps(_ready_event_payload()).encode("utf-8"),
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "lifecycle webhook payload is too large"
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


@pytest.mark.parametrize("max_request_body_bytes", [0, -1, True, "32"])
def test_lifecycle_api_rejects_invalid_body_limit_at_construction(
    max_request_body_bytes: object,
) -> None:
    store = FakeOperationalStore()

    with pytest.raises(ValueError, match="max_request_body_bytes must be a positive integer"):
        create_lifecycle_api(
            store=store,
            max_request_body_bytes=max_request_body_bytes,  # type: ignore[arg-type]
        )

    assert store.recorded_events == []
    assert store.enqueued_jobs == []


def test_lifecycle_bounded_body_reader_rejects_stream_before_unbounded_read() -> None:
    request = FakeStreamingRequest([b"a" * 16, b"b" * 17])

    try:
        asyncio.run(_read_bounded_request_body(request, max_request_body_bytes=32))
    except HTTPException as exc:
        assert exc.status_code == 413
        assert exc.detail == "lifecycle webhook payload is too large"
    else:
        raise AssertionError("oversized lifecycle stream was not rejected")


def test_lifecycle_webhook_rate_limits_repeated_requests_before_recording() -> None:
    now = [1000.0]
    store = FakeOperationalStore()
    limiter = InMemoryRateLimiter(
        max_requests=2,
        window_seconds=60,
        clock=lambda: now[0],
    )
    client = TestClient(_create_test_lifecycle_api(store=store, rate_limiter=limiter))

    assert client.post(
        "/lifecycle/events",
        json=_ready_event_payload(),
        headers=_test_auth_headers(),
    ).status_code == 202
    payload_two = _ready_event_payload()
    payload_two["event_id"] = "evt-20260513-002"
    assert client.post(
        "/lifecycle/events",
        json=payload_two,
        headers=_test_auth_headers(),
    ).status_code == 202
    payload_three = _ready_event_payload()
    payload_three["event_id"] = "evt-20260513-003"

    response = client.post(
        "/lifecycle/events",
        json=payload_three,
        headers=_test_auth_headers(),
    )

    assert response.status_code == 429
    assert response.json()["detail"] == "rate limit exceeded"
    assert [event.event_id for event in store.recorded_events] == [
        "evt-20260513-001",
        "evt-20260513-002",
    ]


@pytest.mark.parametrize(
    "decision",
    [
        None,
        SimpleNamespace(),
        SimpleNamespace(allowed="false", retry_after_seconds=60),
        SimpleNamespace(allowed=False),
        SimpleNamespace(allowed=False, retry_after_seconds=True),
        SimpleNamespace(allowed=False, retry_after_seconds=-1),
    ],
)
def test_lifecycle_rate_limit_rejects_malformed_limiter_decisions(
    decision: object,
) -> None:
    class MalformedLimiter:
        def check(self, _key: str) -> object:
            return decision

    with pytest.raises(HTTPException) as exc_info:
        _require_rate_limit(
            rate_limiter=cast(InMemoryRateLimiter, MalformedLimiter()),
            key="lifecycle-events",
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "lifecycle rate limiter is invalid"


def test_lifecycle_webhook_hmac_auth_requires_signature_before_recording() -> None:
    store = FakeOperationalStore()
    client = TestClient(
        create_lifecycle_api(
            store=store,
            webhook_auth_mode="hmac_sha256",
            webhook_secret="webhook-secret",
        )
    )

    response = client.post("/lifecycle/events", json=_ready_event_payload())

    assert response.status_code == 401
    assert response.json()["detail"] == "lifecycle webhook signature required"
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


def test_lifecycle_webhook_hmac_auth_accepts_valid_signature() -> None:
    store = FakeOperationalStore()
    client = TestClient(
        create_lifecycle_api(
            store=store,
            webhook_auth_mode="hmac_sha256",
            webhook_secret="webhook-secret",
        )
    )
    body, headers = _signed_webhook_request(_ready_event_payload())

    response = client.post("/lifecycle/events", content=body, headers=headers)

    assert response.status_code == 202
    assert response.json()["job_id"] == "job-evt-20260513-001"
    assert [event.event_id for event in store.recorded_events] == ["evt-20260513-001"]
    assert store.enqueued_jobs == [("evt-20260513-001", "STRY0010013")]


def test_lifecycle_webhook_hmac_auth_accepts_previous_secret_during_rotation() -> None:
    store = FakeOperationalStore()
    client = TestClient(
        create_lifecycle_api(
            store=store,
            webhook_auth_mode="hmac_sha256",
            webhook_secret="current-webhook-secret",
            webhook_previous_secret="previous-webhook-secret",
        )
    )
    body, headers = _signed_webhook_request(
        _ready_event_payload(),
        secret="previous-webhook-secret",
    )

    response = client.post("/lifecycle/events", content=body, headers=headers)

    assert response.status_code == 202
    assert response.json()["job_id"] == "job-evt-20260513-001"
    assert [event.event_id for event in store.recorded_events] == ["evt-20260513-001"]
    assert store.enqueued_jobs == [("evt-20260513-001", "STRY0010013")]


def test_lifecycle_webhook_hmac_auth_rejects_unknown_secret_during_rotation() -> None:
    store = FakeOperationalStore()
    client = TestClient(
        create_lifecycle_api(
            store=store,
            webhook_auth_mode="hmac_sha256",
            webhook_secret="current-webhook-secret",
            webhook_previous_secret="previous-webhook-secret",
        )
    )
    body, headers = _signed_webhook_request(
        _ready_event_payload(),
        secret="unknown-webhook-secret",
    )

    response = client.post("/lifecycle/events", content=body, headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "lifecycle webhook signature rejected"
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


def test_lifecycle_webhook_hmac_auth_accepts_valid_servicenow_base64_signature() -> None:
    store = FakeOperationalStore()
    client = TestClient(
        create_lifecycle_api(
            store=store,
            webhook_auth_mode="hmac_sha256",
            webhook_secret="webhook-secret",
        )
    )
    body, headers = _signed_base64_webhook_request(_ready_event_payload())

    response = client.post("/lifecycle/events", content=body, headers=headers)

    assert response.status_code == 202
    assert response.json()["job_id"] == "job-evt-20260513-001"
    assert [event.event_id for event in store.recorded_events] == ["evt-20260513-001"]
    assert store.enqueued_jobs == [("evt-20260513-001", "STRY0010013")]


def test_lifecycle_webhook_hmac_auth_rejects_bad_signature_before_recording() -> None:
    store = FakeOperationalStore()
    client = TestClient(
        create_lifecycle_api(
            store=store,
            webhook_auth_mode="hmac_sha256",
            webhook_secret="webhook-secret",
        )
    )
    body, headers = _signed_webhook_request(_ready_event_payload())
    headers["X-JEDI-Webhook-Signature"] = "sha256=" + ("0" * 64)

    response = client.post("/lifecycle/events", content=body, headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "lifecycle webhook signature rejected"
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


def test_lifecycle_webhook_hmac_auth_rejects_stale_timestamp_before_recording() -> None:
    store = FakeOperationalStore()
    client = TestClient(
        create_lifecycle_api(
            store=store,
            webhook_auth_mode="hmac_sha256",
            webhook_secret="webhook-secret",
            webhook_max_skew_seconds=300,
        )
    )
    body, headers = _signed_webhook_request(_ready_event_payload(), timestamp=1)

    response = client.post("/lifecycle/events", content=body, headers=headers)

    assert response.status_code == 401
    assert response.json()["detail"] == "lifecycle webhook timestamp outside replay window"
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


def test_lifecycle_webhook_hmac_auth_rejects_invalid_timestamp_before_recording() -> None:
    store = FakeOperationalStore()
    client = TestClient(
        create_lifecycle_api(
            store=store,
            webhook_auth_mode="hmac_sha256",
            webhook_secret="webhook-secret",
        )
    )
    body, headers = _signed_webhook_request(_ready_event_payload())
    headers["X-JEDI-Webhook-Timestamp"] = "not-a-timestamp"

    response = client.post("/lifecycle/events", content=body, headers=headers)

    assert response.status_code == 401
    assert response.json()["detail"] == "lifecycle webhook timestamp invalid"
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


def test_lifecycle_webhook_hmac_auth_rejects_padded_timestamp_before_recording() -> None:
    store = FakeOperationalStore()
    client = TestClient(
        create_lifecycle_api(
            store=store,
            webhook_auth_mode="hmac_sha256",
            webhook_secret="webhook-secret",
        )
    )
    body, headers = _signed_webhook_request(
        _ready_event_payload(),
        timestamp=f" {int(time.time())} ",
    )

    response = client.post("/lifecycle/events", content=body, headers=headers)

    assert response.status_code == 401
    assert response.json()["detail"] == "lifecycle webhook timestamp invalid"
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


def test_lifecycle_webhook_hmac_auth_rejects_oversized_timestamp_before_int_parse(
    monkeypatch: Any,
) -> None:
    def fail_time() -> float:
        raise AssertionError("oversized timestamp reached replay-window parsing")

    monkeypatch.setattr(time, "time", fail_time)

    try:
        _require_hmac_webhook_auth(
            configured_secrets=("webhook-secret",),
            max_skew_seconds=300,
            body=b"{}",
            timestamp_header="1" * (MAX_LIFECYCLE_WEBHOOK_CREDENTIAL_BYTES + 1),
            signature_header="sha256=unused",
        )
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "lifecycle webhook timestamp invalid"
    else:
        raise AssertionError("oversized lifecycle timestamp was not rejected")


def test_lifecycle_webhook_hmac_auth_invalid_timestamp_does_not_retain_cause() -> None:
    too_many_digits_for_int = "1" * 5000

    try:
        _require_hmac_webhook_auth(
            configured_secrets=("webhook-secret",),
            max_skew_seconds=300,
            body=b"{}",
            timestamp_header=too_many_digits_for_int,
            signature_header=f"sha256={'0' * 64}",
        )
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "lifecycle webhook timestamp invalid"
        assert exc.__cause__ is None
        assert too_many_digits_for_int not in str(exc.detail)
    else:
        raise AssertionError("invalid lifecycle timestamp was not rejected")


def test_lifecycle_webhook_hmac_auth_rejects_padded_signature_before_compare(
    monkeypatch: Any,
) -> None:
    store = FakeOperationalStore()
    client = TestClient(
        create_lifecycle_api(
            store=store,
            webhook_auth_mode="hmac_sha256",
            webhook_secret="webhook-secret",
        )
    )
    body, headers = _signed_webhook_request(_ready_event_payload())
    headers["X-JEDI-Webhook-Signature"] = f"{headers['X-JEDI-Webhook-Signature']} "

    def fail_compare_digest(left: str, right: str) -> bool:
        raise AssertionError(f"malformed signature was compared: {left!r} {right!r}")

    monkeypatch.setattr(hmac, "compare_digest", fail_compare_digest)

    response = client.post("/lifecycle/events", content=body, headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "lifecycle webhook signature rejected"
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


def test_lifecycle_webhook_hmac_auth_rejects_oversized_signature_before_compare(
    monkeypatch: Any,
) -> None:
    store = FakeOperationalStore()
    client = TestClient(
        create_lifecycle_api(
            store=store,
            webhook_auth_mode="hmac_sha256",
            webhook_secret="webhook-secret",
        )
    )
    body, headers = _signed_webhook_request(_ready_event_payload())
    headers["X-JEDI-Webhook-Signature"] = "sha256=" + ("0" * MAX_LIFECYCLE_WEBHOOK_CREDENTIAL_BYTES)

    def fail_compare_digest(left: str, right: str) -> bool:
        raise AssertionError(f"oversized signature was compared: {left!r} {right!r}")

    monkeypatch.setattr(hmac, "compare_digest", fail_compare_digest)

    response = client.post("/lifecycle/events", content=body, headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "lifecycle webhook signature rejected"
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


def test_lifecycle_webhook_hmac_auth_rejects_non_ascii_signature_before_compare(
    monkeypatch: Any,
) -> None:
    def fail_compare_digest(left: str, right: str) -> bool:
        raise AssertionError(f"non-ASCII signature was compared: {left!r} {right!r}")

    monkeypatch.setattr(hmac, "compare_digest", fail_compare_digest)

    try:
        _require_hmac_webhook_auth(
            configured_secrets=("webhook-secret",),
            max_skew_seconds=300,
            body=b"{}",
            timestamp_header=str(int(time.time())),
            signature_header="sha256=é",
        )
    except HTTPException as exc:
        assert exc.status_code == 403
        assert exc.detail == "lifecycle webhook signature rejected"
    else:
        raise AssertionError("non-ASCII lifecycle signature was not rejected")


@pytest.mark.parametrize(
    "signature_header",
    [
        "sha512=985bf5c484ad5adbe9d7bd8490712908ec6b6650850e85a0bd8b95b4b6541702",
        "sha256=not-hex",
        "sha256-base64=not_base64!",
    ],
)
def test_lifecycle_webhook_hmac_auth_rejects_malformed_signature_shape_before_compare(
    signature_header: str,
    monkeypatch: Any,
) -> None:
    def fail_compare_digest(left: str, right: str) -> bool:
        raise AssertionError(f"malformed signature was compared: {left!r} {right!r}")

    monkeypatch.setattr(hmac, "compare_digest", fail_compare_digest)

    try:
        _require_hmac_webhook_auth(
            configured_secrets=("webhook-secret",),
            max_skew_seconds=300,
            body=b"{}",
            timestamp_header=str(int(time.time())),
            signature_header=signature_header,
        )
    except HTTPException as exc:
        assert exc.status_code == 403
        assert exc.detail == "lifecycle webhook signature rejected"
    else:
        raise AssertionError("malformed lifecycle signature was not rejected")


def test_lifecycle_webhook_hmac_auth_rejects_invalid_json_before_recording() -> None:
    store = FakeOperationalStore()
    client = TestClient(
        create_lifecycle_api(
            store=store,
            webhook_auth_mode="hmac_sha256",
            webhook_secret="webhook-secret",
        )
    )
    body = b"{not-json"
    timestamp = str(int(time.time()))
    digest = hmac.new(
        b"webhook-secret",
        timestamp.encode("utf-8") + b"." + body,
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        "/lifecycle/events",
        content=body,
        headers={
            "content-type": "application/json",
            "X-JEDI-Webhook-Timestamp": timestamp,
            "X-JEDI-Webhook-Signature": f"sha256={digest}",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "invalid lifecycle webhook JSON"
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


def test_lifecycle_webhook_invalid_json_does_not_retain_cause() -> None:
    app = _create_test_lifecycle_api(store=FakeOperationalStore())
    endpoint = _lifecycle_events_endpoint(app)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            endpoint(
                _request_with_body(b"{not-json"),
                x_jedi_webhook_secret=_TEST_WEBHOOK_SECRET,
                x_jedi_webhook_timestamp=None,
                x_jedi_webhook_signature=None,
            )
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "invalid lifecycle webhook JSON"
    assert exc_info.value.__cause__ is None


def test_lifecycle_webhook_hmac_auth_rejects_invalid_utf8_json_before_recording() -> None:
    store = FakeOperationalStore()
    client = TestClient(
        create_lifecycle_api(
            store=store,
            webhook_auth_mode="hmac_sha256",
            webhook_secret="webhook-secret",
        )
    )
    body = b'{"event_id":"evt-001","client_secret":"\xff"}'
    timestamp = str(int(time.time()))
    digest = hmac.new(
        b"webhook-secret",
        timestamp.encode("utf-8") + b"." + body,
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        "/lifecycle/events",
        content=body,
        headers={
            "content-type": "application/json",
            "X-JEDI-Webhook-Timestamp": timestamp,
            "X-JEDI-Webhook-Signature": f"sha256={digest}",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "invalid lifecycle webhook JSON"
    assert "client_secret" not in response.text
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


def test_lifecycle_webhook_hmac_auth_rejects_non_finite_json_before_recording() -> None:
    store = FakeOperationalStore()
    client = TestClient(
        create_lifecycle_api(
            store=store,
            webhook_auth_mode="hmac_sha256",
            webhook_secret="webhook-secret",
        )
    )
    body = (
        b'{"event_id":"evt-20260513-001","event_type":"story_state_changed",'
        b'"story_sys_id":"story-sys-id","story_number":"STRY0010013",'
        b'"previous_state":"Draft","new_state":"Ready",'
        b'"changed_by":"system","changed_at":"2026-05-13T15:00:00Z",'
        b'"risk_score":NaN,"client_secret":"payload-secret"}'
    )
    timestamp = str(int(time.time()))
    digest = hmac.new(
        b"webhook-secret",
        timestamp.encode("utf-8") + b"." + body,
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        "/lifecycle/events",
        content=body,
        headers={
            "content-type": "application/json",
            "X-JEDI-Webhook-Timestamp": timestamp,
            "X-JEDI-Webhook-Signature": f"sha256={digest}",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "invalid lifecycle webhook JSON"
    assert "payload-secret" not in response.text
    assert "risk_score" not in response.text
    assert "NaN" not in response.text
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


def test_lifecycle_webhook_validation_error_does_not_echo_rejected_input() -> None:
    store = FakeOperationalStore()
    client = TestClient(_create_test_lifecycle_api(store=store))
    payload = _ready_event_payload()
    payload["extra_secret"] = "client_secret=super-secret"

    response = client.post(
        "/lifecycle/events",
        json=payload,
        headers=_test_auth_headers(),
    )

    assert response.status_code == 422
    body = response.text
    assert "extra_forbidden" in body
    assert "client_secret" not in body
    assert "super-secret" not in body
    assert '"input"' not in body
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


def test_lifecycle_webhook_validation_error_does_not_retain_cause() -> None:
    app = _create_test_lifecycle_api(store=FakeOperationalStore())
    endpoint = _lifecycle_events_endpoint(app)
    payload = _ready_event_payload()
    payload["extra_secret"] = "client_secret=super-secret"

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            endpoint(
                _request_with_body(json.dumps(payload).encode("utf-8")),
                x_jedi_webhook_secret=_TEST_WEBHOOK_SECRET,
                x_jedi_webhook_timestamp=None,
                x_jedi_webhook_signature=None,
            )
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.__cause__ is None
    assert "extra_forbidden" in str(exc_info.value.detail)


def test_lifecycle_webhook_shared_secret_accepts_valid_secret() -> None:
    store = FakeOperationalStore()
    client = TestClient(
        create_lifecycle_api(
            store=store,
            webhook_auth_mode="shared_secret",
            webhook_secret="webhook-secret",
        )
    )

    response = client.post(
        "/lifecycle/events",
        json=_ready_event_payload(),
        headers={"X-JEDI-Webhook-Secret": "webhook-secret"},
    )

    assert response.status_code == 202
    assert [event.event_id for event in store.recorded_events] == ["evt-20260513-001"]
    assert store.enqueued_jobs == [("evt-20260513-001", "STRY0010013")]


def test_lifecycle_webhook_shared_secret_accepts_previous_secret_during_rotation() -> None:
    store = FakeOperationalStore()
    client = TestClient(
        create_lifecycle_api(
            store=store,
            webhook_auth_mode="shared_secret",
            webhook_secret="current-webhook-secret",
            webhook_previous_secret="previous-webhook-secret",
        )
    )

    response = client.post(
        "/lifecycle/events",
        json=_ready_event_payload(),
        headers={"X-JEDI-Webhook-Secret": "previous-webhook-secret"},
    )

    assert response.status_code == 202
    assert response.json()["job_id"] == "job-evt-20260513-001"
    assert [event.event_id for event in store.recorded_events] == ["evt-20260513-001"]
    assert store.enqueued_jobs == [("evt-20260513-001", "STRY0010013")]


def test_lifecycle_webhook_shared_secret_rejects_bad_secret_before_recording() -> None:
    store = FakeOperationalStore()
    client = TestClient(
        create_lifecycle_api(
            store=store,
            webhook_auth_mode="shared_secret",
            webhook_secret="webhook-secret",
        )
    )

    response = client.post(
        "/lifecycle/events",
        json=_ready_event_payload(),
        headers={"X-JEDI-Webhook-Secret": "wrong-secret"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "lifecycle webhook secret rejected"
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


def test_lifecycle_webhook_shared_secret_rejects_padded_secret_before_compare(
    monkeypatch: Any,
) -> None:
    store = FakeOperationalStore()
    client = TestClient(
        create_lifecycle_api(
            store=store,
            webhook_auth_mode="shared_secret",
            webhook_secret="webhook-secret",
        )
    )

    def fail_compare_digest(left: str, right: str) -> bool:
        raise AssertionError(f"malformed shared secret was compared: {left!r} {right!r}")

    monkeypatch.setattr(hmac, "compare_digest", fail_compare_digest)

    response = client.post(
        "/lifecycle/events",
        json=_ready_event_payload(),
        headers={"X-JEDI-Webhook-Secret": "webhook-secret "},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "lifecycle webhook secret rejected"
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


def test_lifecycle_webhook_shared_secret_rejects_oversized_secret_before_compare(
    monkeypatch: Any,
) -> None:
    store = FakeOperationalStore()
    client = TestClient(
        create_lifecycle_api(
            store=store,
            webhook_auth_mode="shared_secret",
            webhook_secret="webhook-secret",
        )
    )

    def fail_compare_digest(left: str, right: str) -> bool:
        raise AssertionError(f"oversized secret was compared: {left!r} {right!r}")

    monkeypatch.setattr(hmac, "compare_digest", fail_compare_digest)

    response = client.post(
        "/lifecycle/events",
        json=_ready_event_payload(),
        headers={"X-JEDI-Webhook-Secret": "x" * (MAX_LIFECYCLE_WEBHOOK_CREDENTIAL_BYTES + 1)},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "lifecycle webhook secret rejected"
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


def test_lifecycle_webhook_shared_secret_rejects_non_ascii_secret_before_compare(
    monkeypatch: Any,
) -> None:
    def fail_compare_digest(left: str, right: str) -> bool:
        raise AssertionError(f"non-ASCII secret was compared: {left!r} {right!r}")

    monkeypatch.setattr(hmac, "compare_digest", fail_compare_digest)

    try:
        _require_shared_secret_webhook_auth(
            configured_secrets=("webhook-secret",),
            provided_secret="webhook-secret-é",
        )
    except HTTPException as exc:
        assert exc.status_code == 403
        assert exc.detail == "lifecycle webhook secret rejected"
    else:
        raise AssertionError("non-ASCII lifecycle shared secret was not rejected")


def test_lifecycle_webhook_oauth_mode_fails_closed_before_recording() -> None:
    store = FakeOperationalStore()
    client = TestClient(create_lifecycle_api(store=store, webhook_auth_mode="servicenow_oauth"))

    response = client.post("/lifecycle/events", json=_ready_event_payload())

    assert response.status_code == 501
    assert response.json()["detail"] == (
        "lifecycle webhook auth mode is not implemented: servicenow_oauth"
    )
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


def test_lifecycle_webhook_auth_requires_configured_secret_before_recording() -> None:
    store = FakeOperationalStore()
    client = TestClient(create_lifecycle_api(store=store, webhook_auth_mode="hmac_sha256"))

    response = client.post("/lifecycle/events", json=_ready_event_payload())

    assert response.status_code == 503
    assert response.json()["detail"] == "lifecycle webhook secret is not configured"
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


@pytest.mark.parametrize(
    "configured_secret",
    [
        " webhook-secret",
        "webhook-secret\n",
        "webhook-secret-é",
        "x" * (MAX_LIFECYCLE_WEBHOOK_CREDENTIAL_BYTES + 1),
    ],
)
def test_lifecycle_webhook_rejects_malformed_configured_secret(
    configured_secret: str,
) -> None:
    try:
        _configured_webhook_secret(configured_secret)
    except HTTPException as exc:
        assert exc.status_code == 503
        assert exc.detail == "lifecycle webhook secret is invalid"
    else:
        raise AssertionError("malformed configured lifecycle secret was not rejected")


def test_lifecycle_webhook_records_complete_event_and_closes_related_job() -> None:
    store = FakeOperationalStore()
    complete_notifier = FakeCompleteNotifier()
    client = TestClient(
        _create_test_lifecycle_api(store=store, complete_notifier=complete_notifier)
    )

    response = client.post(
        "/lifecycle/events",
        json=_complete_event_payload(),
        headers=_test_auth_headers(),
    )

    assert response.status_code == 202
    assert response.json() == {
        "accepted": True,
        "event_id": "evt-20260514-uat-complete",
        "story_number": "STRY0010002",
        "should_evaluate": False,
        "lifecycle_action": "close_story",
        "job_id": "job-prior-STRY0010002",
        "reasons": [],
    }
    assert [event.event_id for event in store.recorded_events] == ["evt-20260514-uat-complete"]
    assert store.enqueued_jobs == []
    assert store.closed_story_jobs == [("STRY0010002", "evt-20260514-uat-complete")]
    assert store.rework_story_jobs == []
    assert store.rejected_story_jobs == []
    assert complete_notifier.completed == [
        ("STRY0010002", "story-sys-id-0002", "evt-20260514-uat-complete")
    ]


def test_lifecycle_webhook_records_rework_event_without_enqueueing_build() -> None:
    store = FakeOperationalStore()
    client = TestClient(_create_test_lifecycle_api(store=store))

    response = client.post(
        "/lifecycle/events",
        json=_ready_rework_event_payload(),
        headers=_test_auth_headers(),
    )

    assert response.status_code == 202
    assert response.json() == {
        "accepted": True,
        "event_id": "evt-20260514-uat-rework",
        "story_number": "STRY0010002",
        "should_evaluate": False,
        "lifecycle_action": "rework_requested",
        "job_id": "job-prior-STRY0010002",
        "reasons": [],
    }
    assert [event.event_id for event in store.recorded_events] == ["evt-20260514-uat-rework"]
    assert store.enqueued_jobs == []
    assert store.closed_story_jobs == []
    assert store.rework_story_jobs == [("STRY0010002", "evt-20260514-uat-rework", "Ready")]
    assert store.rejected_story_jobs == []


def test_lifecycle_webhook_records_story_rejected_reset_without_enqueueing_build() -> None:
    store = FakeOperationalStore()
    client = TestClient(_create_test_lifecycle_api(store=store))

    response = client.post(
        "/lifecycle/events",
        json=_draft_rejected_event_payload(),
        headers=_test_auth_headers(),
    )

    assert response.status_code == 202
    assert response.json() == {
        "accepted": True,
        "event_id": "evt-20260514-story-rejected",
        "story_number": "STRY0010002",
        "should_evaluate": False,
        "lifecycle_action": "story_rejected",
        "job_id": "job-prior-STRY0010002",
        "reasons": [],
    }
    assert [event.event_id for event in store.recorded_events] == ["evt-20260514-story-rejected"]
    assert store.enqueued_jobs == []
    assert store.closed_story_jobs == []
    assert store.rework_story_jobs == []
    assert store.rejected_story_jobs == [("STRY0010002", "evt-20260514-story-rejected")]


def test_lifecycle_webhook_emits_rejected_job_notification_after_rejecting_story() -> None:
    store = FakeOperationalStore()
    rejected_notifier = FakeRejectedJobNotifier()
    client = TestClient(
        _create_test_lifecycle_api(
            store=store,
            rejected_job_notifier=rejected_notifier,
        )
    )

    response = client.post(
        "/lifecycle/events",
        json=_draft_rejected_event_payload(),
        headers=_test_auth_headers(),
    )

    assert response.status_code == 202
    assert response.json()["job_id"] == "job-prior-STRY0010002"
    assert [job.job_id for job in rejected_notifier.jobs] == ["job-prior-STRY0010002"]
    assert rejected_notifier.jobs[0].status == "rejected"
    assert store.rejected_story_jobs == [("STRY0010002", "evt-20260514-story-rejected")]


def test_lifecycle_webhook_rejected_job_notification_failure_does_not_block_acceptance(
    caplog: Any,
) -> None:
    store = FakeOperationalStore()
    caplog.set_level("WARNING", logger="jedi_devproject.lifecycle_api")

    def failing_notifier(_job: FulfillmentJobRecord) -> None:
        raise RuntimeError("alert backend returned client_secret=secret-value")

    client = TestClient(
        _create_test_lifecycle_api(
            store=store,
            rejected_job_notifier=failing_notifier,
        )
    )

    response = client.post(
        "/lifecycle/events",
        json=_draft_rejected_event_payload(),
        headers=_test_auth_headers(),
    )

    assert response.status_code == 202
    assert response.json()["job_id"] == "job-prior-STRY0010002"
    assert store.rejected_story_jobs == [("STRY0010002", "evt-20260514-story-rejected")]
    assert "rejected job alert delivery failed" in caplog.text
    assert "secret-value" not in caplog.text
    assert "***REDACTED***" in caplog.text


class _UnstringifiableLifecycleAlertError(RuntimeError):
    def __str__(self) -> str:
        raise ValueError("client-secret-value")


def test_lifecycle_webhook_rejected_job_notification_unstringifiable_failure_is_best_effort(
    caplog: Any,
) -> None:
    store = FakeOperationalStore()
    caplog.set_level("WARNING", logger="jedi_devproject.lifecycle_api")

    def failing_notifier(_job: FulfillmentJobRecord) -> None:
        raise _UnstringifiableLifecycleAlertError("unused")

    client = TestClient(
        _create_test_lifecycle_api(
            store=store,
            rejected_job_notifier=failing_notifier,
        )
    )

    response = client.post(
        "/lifecycle/events",
        json=_draft_rejected_event_payload(),
        headers=_test_auth_headers(),
    )

    assert response.status_code == 202
    assert response.json()["job_id"] == "job-prior-STRY0010002"
    assert store.rejected_story_jobs == [("STRY0010002", "evt-20260514-story-rejected")]
    assert "rejected job alert delivery failed" in caplog.text
    assert "lifecycle raised unstringifiable _UnstringifiableLifecycleAlertError" in caplog.text
    assert "client-secret-value" not in caplog.text


def test_lifecycle_webhook_records_unsupported_transition_without_enqueueing() -> None:
    store = FakeOperationalStore()
    client = TestClient(_create_test_lifecycle_api(store=store))
    payload = _ready_event_payload()
    payload["previous_state"] = "Ready"
    payload["current_state"] = "Work in Progress"

    response = client.post(
        "/lifecycle/events",
        json=payload,
        headers=_test_auth_headers(),
    )

    assert response.status_code == 202
    assert response.json() == {
        "accepted": True,
        "event_id": "evt-20260513-001",
        "story_number": "STRY0010013",
        "should_evaluate": False,
        "lifecycle_action": None,
        "job_id": None,
        "reasons": ["unsupported_lifecycle_transition"],
    }
    assert [event.event_id for event in store.recorded_events] == ["evt-20260513-001"]
    assert store.enqueued_jobs == []


def test_lifecycle_webhook_accepts_story_sys_id_without_exposing_it_in_response() -> None:
    store = FakeOperationalStore()
    client = TestClient(_create_test_lifecycle_api(store=store))
    payload = _ready_event_payload()
    payload["story_sys_id"] = "rm-story-sys-id"

    response = client.post(
        "/lifecycle/events",
        json=payload,
        headers=_test_auth_headers(),
    )

    assert response.status_code == 202
    assert response.json()["job_id"] == "job-evt-20260513-001"
    assert "story_sys_id" not in response.json()
    assert [event.story_sys_id for event in store.recorded_events] == ["rm-story-sys-id"]
    assert store.enqueued_jobs == [("evt-20260513-001", "STRY0010013")]


def test_health_endpoint_does_not_touch_operational_store() -> None:
    store = FakeOperationalStore()
    client = TestClient(create_lifecycle_api(store=store))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert store.recorded_events == []
    assert store.enqueued_jobs == []
