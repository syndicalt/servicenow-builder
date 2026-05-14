from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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
        self.artifact_refs: list[tuple[str, str, str, str]] = []
        self.json_artifacts: list[tuple[str, str, str, str, dict[str, Any]]] = []
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

    def record_artifact_ref(
        self,
        *,
        job_id: str,
        artifact_kind: str,
        path: str,
        sha256: str,
    ) -> object:
        self.artifact_refs.append((job_id, artifact_kind, path, sha256))
        return object()

    def record_json_artifact(
        self,
        *,
        job_id: str,
        story_number: str,
        artifact_kind: str,
        schema_version: str,
        payload: dict[str, Any],
    ) -> object:
        self.json_artifacts.append(
            (job_id, story_number, artifact_kind, schema_version, payload)
        )
        return object()


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


def _settings_with_openai(tmp_path: Path, *, apply: bool = False) -> RuntimeSettings:
    return _settings(tmp_path, apply=apply).model_copy(
        update={
            "model_provider": "openai",
            "openai_api_key": "openai-key",
            "openai_model": "gpt-4o-2024-08-06",
        }
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


def _story_record(*, state: str = "Ready") -> dict[str, str]:
    return {
        "sys_id": "story-sys-id",
        "number": "STRY0010013",
        "short_description": "Add AI Review Notes field to Story form",
        "description": (
            "Add a new custom field to the rm_story table named u_ai_review_notes "
            "and place it on the Story form below Description."
        ),
        "acceptance_criteria": "The AI Review Notes field stores review notes.",
        "story_points": "3",
        "priority": "4",
        "state": state,
    }


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
    assert settings.model_provider is None


def test_load_runtime_settings_accepts_build_claim_state_values(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                f"JEDI_AUDIT_ROOT={tmp_path}",
                "JEDI_BUILD_CLAIM_FROM_STATE=1",
                "JEDI_BUILD_CLAIM_STATE=2",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_runtime_settings(env_path)

    assert settings.build_claim_from_state == "1"
    assert settings.build_claim_state == "2"


def test_load_runtime_settings_requires_explicit_model_provider_to_enable_openai(
    tmp_path: Path,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                f"JEDI_AUDIT_ROOT={tmp_path}",
                "OPENAI_API_KEY=openai-key",
                "OPENAI_MODEL=gpt-4o-2024-08-06",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_runtime_settings(env_path)

    assert settings.model_provider is None
    assert settings.openai_api_key == "openai-key"


def test_load_runtime_settings_enables_openai_when_provider_is_explicit(
    tmp_path: Path,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                f"JEDI_AUDIT_ROOT={tmp_path}",
                "JEDI_MODEL_PROVIDER=openai",
                "OPENAI_API_KEY=openai-key",
                "OPENAI_MODEL=gpt-4o-2024-08-06",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_runtime_settings(env_path)

    assert settings.model_provider == "openai"
    assert settings.openai_api_key == "openai-key"
    assert settings.openai_model == "gpt-4o-2024-08-06"


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


def test_process_one_runtime_fulfillment_generates_openai_candidate_when_enabled(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore(claimed_job=_job())
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(status_code=200, json_body={"result": [_story_record()]}),
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
            HttpResponse(
                status_code=200,
                json_body={"result": [_story_record(state="Work in Progress")]},
            ),
            HttpResponse(
                status_code=200,
                json_body={
                    "output_text": (
                        '{"changes":[{"table":"sys_dictionary","operation":"insert",'
                        '"fields":[{"name":"name","value":"rm_story"},'
                        '{"name":"element","value":"u_ai_review_notes"}],'
                        '"sys_id":null,"rationale":null}],'
                        '"test_plan":["Confirm the field exists."],'
                        '"rollback_notes":["Remove the field."]}'
                    )
                },
            ),
            HttpResponse(status_code=200, json_body={"result": {"sys_id": "story-sys-id"}}),
        ]
    )

    result = process_one_runtime_fulfillment(
        settings=_settings_with_openai(tmp_path, apply=True),
        store_factory=lambda _database_url: store,
        transport=transport,
    )

    assert result.status == "completed"
    assert result.message == "Implementation candidate generated for STRY0010013"
    assert [request.method for request in transport.requests] == [
        "POST",
        "GET",
        "GET",
        "PATCH",
        "GET",
        "POST",
        "PATCH",
    ]
    assert transport.requests[5].url == "https://api.openai.com/v1/responses"
    assert transport.requests[5].headers["Authorization"] == "Bearer openai-key"
    assert "openai-key" not in repr(transport.requests[5].body)
    assert store.artifact_refs == []
    assert [artifact[2] for artifact in store.json_artifacts] == [
        "implementation_packet",
        "implementation_candidate",
    ]
    assert store.json_artifacts[0][3] == "implementation-packet-v1"
    assert store.json_artifacts[1][3] == "implementation-candidate-v1"
    assert store.json_artifacts[0][4]["story"]["number"] == "STRY0010013"
    assert store.json_artifacts[1][4]["changes"][0]["fields"]["element"] == (
        "u_ai_review_notes"
    )
    assert "Implementation candidate generated" in transport.requests[-1].body["work_notes"]


def test_process_one_runtime_fulfillment_rejects_openai_provider_without_api_key(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={"model_provider": "openai", "openai_api_key": None}
    )

    with pytest.raises(RuntimeConfigError, match="OPENAI_API_KEY"):
        process_one_runtime_fulfillment(
            settings=settings,
            store_factory=lambda _database_url: FakeRuntimeStore(claimed_job=None),
            transport=RecordingTransport([]),
        )


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


def test_process_one_runtime_fulfillment_writes_work_note_when_handler_fails(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore(claimed_job=_job())
    transport = RecordingTransport(
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
                            "state": "Draft",
                        }
                    ]
                },
            ),
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
                            "state": "Draft",
                        }
                    ]
                },
            ),
            HttpResponse(status_code=200, json_body={"result": {"sys_id": "story-sys-id"}}),
        ]
    )

    result = process_one_runtime_fulfillment(
        settings=_settings(tmp_path, apply=True),
        store_factory=lambda _database_url: store,
        transport=transport,
    )

    assert result.status == "failed"
    assert result.error_message == "fresh_story_state_mismatch"
    assert store.failed_jobs == [("job-evt-001", "fresh_story_state_mismatch")]
    assert [request.method for request in transport.requests] == [
        "POST",
        "GET",
        "GET",
        "PATCH",
    ]
    assert transport.requests[-1].body["work_notes"] == (
        "Automated fulfillment failed for lifecycle event evt-001. "
        "Job: job-evt-001. Error: fresh_story_state_mismatch"
    )


def test_process_one_runtime_fulfillment_redacts_secrets_from_failure_notes(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore(claimed_job=_job())
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(
                status_code=500,
                json_body={
                    "error": {
                        "message": (
                            "client-secret leaked with "
                            "postgresql://jedi:secret@localhost:5432/jedi"
                        )
                    }
                },
            ),
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
            HttpResponse(status_code=200, json_body={"result": {"sys_id": "story-sys-id"}}),
        ]
    )

    result = process_one_runtime_fulfillment(
        settings=_settings(tmp_path, apply=True),
        store_factory=lambda _database_url: store,
        transport=transport,
    )

    assert result.status == "failed"
    assert result.error_message is not None
    assert "client-secret" not in result.error_message
    assert "postgresql://jedi:secret@localhost:5432/jedi" not in result.error_message
    assert store.failed_jobs
    assert "client-secret" not in store.failed_jobs[0][1]
    assert "postgresql://jedi:secret@localhost:5432/jedi" not in store.failed_jobs[0][1]
    work_notes = transport.requests[-1].body["work_notes"]
    assert "client-secret" not in work_notes
    assert "postgresql://jedi:secret@localhost:5432/jedi" not in work_notes
    assert "***REDACTED***" in work_notes
