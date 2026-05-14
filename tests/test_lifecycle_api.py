from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from jedi_devproject.lifecycle_api import create_lifecycle_api
from jedi_devproject.lifecycle_events import LifecycleStateChangeEvent
from jedi_devproject.operational_store import FulfillmentJobRecord, LifecycleEventRecord


class FakeOperationalStore:
    def __init__(self) -> None:
        self.recorded_events: list[LifecycleStateChangeEvent] = []
        self.enqueued_jobs: list[tuple[str, str]] = []

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


def test_lifecycle_webhook_records_ready_event_and_enqueues_fulfillment() -> None:
    store = FakeOperationalStore()
    client = TestClient(create_lifecycle_api(store=store))

    response = client.post("/lifecycle/events", json=_ready_event_payload())

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


def test_lifecycle_webhook_records_unsupported_transition_without_enqueueing() -> None:
    store = FakeOperationalStore()
    client = TestClient(create_lifecycle_api(store=store))
    payload = _ready_event_payload()
    payload["previous_state"] = "Ready"
    payload["current_state"] = "Work in Progress"

    response = client.post("/lifecycle/events", json=payload)

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


def test_lifecycle_webhook_rejects_forbidden_servicenow_identifiers() -> None:
    store = FakeOperationalStore()
    client = TestClient(create_lifecycle_api(store=store))
    payload = _ready_event_payload()
    payload["story_sys_id"] = "must-not-cross-this-boundary"

    response = client.post("/lifecycle/events", json=payload)

    assert response.status_code == 422
    assert store.recorded_events == []
    assert store.enqueued_jobs == []


def test_health_endpoint_does_not_touch_operational_store() -> None:
    store = FakeOperationalStore()
    client = TestClient(create_lifecycle_api(store=store))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert store.recorded_events == []
    assert store.enqueued_jobs == []
