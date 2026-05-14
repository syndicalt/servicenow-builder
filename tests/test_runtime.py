from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from jedi_devproject.lifecycle_events import LifecycleStateChangeEvent
from jedi_devproject.operational_store import FulfillmentJobRecord, LifecycleEventRecord
from jedi_devproject.runtime import (
    RuntimeConfigError,
    RuntimeSettings,
    create_runtime_api,
    load_runtime_settings,
    process_one_runtime_fulfillment,
)
from jedi_devproject.servicenow import HttpRequest, HttpResponse


class FakeRuntimeStore:
    def __init__(self, claimed_job: FulfillmentJobRecord | None = None) -> None:
        self.claimed_job = claimed_job
        self.recorded_events: list[str] = []
        self.enqueued_jobs: list[tuple[str, str]] = []
        self.completed_jobs: list[tuple[str, str]] = []
        self.failed_jobs: list[tuple[str, str]] = []
        self.closed = False

    def __enter__(self) -> FakeRuntimeStore:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def close(self) -> None:
        self.closed = True

    def record_lifecycle_event(
        self,
        event: LifecycleStateChangeEvent,
        *,
        validation_status: str = "accepted",
    ) -> LifecycleEventRecord:
        self.recorded_events.append(event.event_id)
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
        return _job(event_id=event_id, story_number=story_number)

    def claim_next_fulfillment_job(
        self,
        *,
        worker_id: str,
    ) -> FulfillmentJobRecord | None:
        return self.claimed_job

    def complete_fulfillment_job(
        self,
        *,
        job_id: str,
        message: str,
    ) -> FulfillmentJobRecord:
        self.completed_jobs.append((job_id, message))
        assert self.claimed_job is not None
        return self.claimed_job.model_copy(update={"status": "completed"})

    def fail_fulfillment_job(
        self,
        *,
        job_id: str,
        error_message: str,
    ) -> FulfillmentJobRecord:
        self.failed_jobs.append((job_id, error_message))
        assert self.claimed_job is not None
        return self.claimed_job.model_copy(update={"status": "failed"})


class RecordingTransport:
    def __init__(self, responses: list[HttpResponse]) -> None:
        self.responses = responses
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        return self.responses.pop(0)


def _settings(tmp_path: Path, *, apply: bool = False) -> RuntimeSettings:
    return RuntimeSettings(
        database_url="postgresql://jedi:secret@localhost:5432/jedi",
        servicenow_instance_url="https://dev205693.service-now.com",
        servicenow_client_id="client-id",
        servicenow_client_secret="client-secret",
        worker_id="worker-1",
        audit_root=tmp_path,
        build_claim_apply=apply,
    )


def _job(
    *,
    event_id: str = "evt-001",
    story_number: str = "STRY0010013",
) -> FulfillmentJobRecord:
    return FulfillmentJobRecord(
        job_id=f"job-{event_id}",
        event_id=event_id,
        story_number=story_number,
        status="running",
        attempt_count=1,
        created_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
        updated_at=datetime(2026, 5, 13, 15, 1, tzinfo=UTC),
        locked_by="worker-1",
        locked_at=datetime(2026, 5, 13, 15, 1, tzinfo=UTC),
        last_error=None,
    )


def _ready_event_payload() -> dict[str, str]:
    return {
        "event_id": "evt-001",
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


def _transport_for_successful_claim() -> RecordingTransport:
    return RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "sys_id": "story-sys-id",
                            "number": "STRY0010013",
                            "short_description": "Add AI Review Notes field",
                            "description": "Add AI Review Notes field.",
                            "story_points": "3",
                            "priority": "4",
                            "state": "Ready",
                        }
                    ]
                },
            ),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "element": "state",
                            "column_label": "State",
                            "internal_type": "choice",
                            "active": "true",
                        },
                        {
                            "element": "u_ai_status",
                            "column_label": "AI Status",
                            "internal_type": "string",
                            "active": "true",
                        },
                    ]
                },
            ),
            HttpResponse(status_code=200, json_body={"result": {"sys_id": "story-sys-id"}}),
        ]
    )


def test_load_runtime_settings_requires_runtime_values(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com\n")

    with pytest.raises(RuntimeConfigError) as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "DATABASE_URL" in message
    assert "SERVICENOW_CLIENT_ID" in message
    assert "SERVICENOW_CLIENT_SECRET" in message
    assert "JEDI_AUDIT_ROOT" in message


def test_load_runtime_settings_accepts_env_file(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                "JEDI_WORKER_ID=worker-1",
                f"JEDI_AUDIT_ROOT={tmp_path}",
                "JEDI_BUILD_CLAIM_APPLY=true",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_runtime_settings(env_path)

    assert settings.database_url == "postgresql://jedi:secret@localhost:5432/jedi"
    assert settings.worker_id == "worker-1"
    assert settings.audit_root == tmp_path
    assert settings.build_claim_apply is True


def test_create_runtime_api_wires_store_factory(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    database_urls: list[str] = []

    def store_factory(database_url: str) -> FakeRuntimeStore:
        database_urls.append(database_url)
        return store

    client = TestClient(
        create_runtime_api(settings=_settings(tmp_path), store_factory=store_factory)
    )

    response = client.post("/lifecycle/events", json=_ready_event_payload())

    assert response.status_code == 202
    assert database_urls == ["postgresql://jedi:secret@localhost:5432/jedi"]
    assert store.recorded_events == ["evt-001"]
    assert store.enqueued_jobs == [("evt-001", "STRY0010013")]


def test_process_one_runtime_fulfillment_wires_store_servicenow_and_handler(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore(claimed_job=_job())
    transport = _transport_for_successful_claim()

    result = process_one_runtime_fulfillment(
        settings=_settings(tmp_path, apply=True),
        store_factory=lambda _database_url: store,
        transport=transport,
    )

    assert result.status == "completed"
    assert result.message == "Build claim applied for STRY0010013"
    assert store.completed_jobs == [("job-evt-001", "Build claim applied for STRY0010013")]
    assert store.failed_jobs == []
    assert store.closed is True
    assert [request.method for request in transport.requests] == ["POST", "GET", "GET", "PATCH"]


def test_process_one_runtime_fulfillment_returns_idle_without_servicenow_calls(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore(claimed_job=None)
    transport = RecordingTransport([])

    result = process_one_runtime_fulfillment(
        settings=_settings(tmp_path, apply=True),
        store_factory=lambda _database_url: store,
        transport=transport,
    )

    assert result.status == "idle"
    assert transport.requests == []
    assert store.closed is True
