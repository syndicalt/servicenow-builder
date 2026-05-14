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
    assert store.closed_story_jobs == []


def test_lifecycle_webhook_records_complete_event_and_closes_related_job() -> None:
    store = FakeOperationalStore()
    client = TestClient(create_lifecycle_api(store=store))

    response = client.post("/lifecycle/events", json=_complete_event_payload())

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


def test_lifecycle_webhook_records_rework_event_without_enqueueing_build() -> None:
    store = FakeOperationalStore()
    client = TestClient(create_lifecycle_api(store=store))

    response = client.post("/lifecycle/events", json=_ready_rework_event_payload())

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
    client = TestClient(create_lifecycle_api(store=store))

    response = client.post("/lifecycle/events", json=_draft_rejected_event_payload())

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
