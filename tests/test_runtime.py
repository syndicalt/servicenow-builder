from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from jedi_devproject.lifecycle_events import LifecycleStateChangeEvent
from jedi_devproject.operational_store import (
    ArtifactBlobRecord,
    ArtifactRefRecord,
    FulfillmentJobRecord,
    LifecycleEventRecord,
)
from jedi_devproject.runtime import (
    RuntimeConfigError,
    RuntimeSettings,
    create_runtime_api,
    load_runtime_settings,
    process_one_runtime_fulfillment,
    validate_runtime_settings,
)
from jedi_devproject.servicenow import HttpRequest, HttpResponse


class FakeRuntimeStore:
    def __init__(self, claimed_job: FulfillmentJobRecord | None = None) -> None:
        self.claimed_job = claimed_job
        self.recorded_events: list[str] = []
        self.enqueued_jobs: list[tuple[str, str]] = []
        self.closed_story_jobs: list[tuple[str, str]] = []
        self.rework_story_jobs: list[tuple[str, str, str]] = []
        self.rejected_story_jobs: list[tuple[str, str]] = []
        self.completed_jobs: list[tuple[str, str]] = []
        self.failed_jobs: list[tuple[str, str]] = []
        self.artifact_refs: list[tuple[str, str, str, str]] = []
        self.json_artifacts: list[tuple[str, str, str, str, dict[str, Any]]] = []
        self.artifact_blob_records: dict[int, ArtifactBlobRecord] = {}
        self.artifact_ref_records: dict[str, list[ArtifactRefRecord]] = {}
        self.lifecycle_event_records: list[LifecycleEventRecord] = []
        self.fulfillment_job_records: list[FulfillmentJobRecord] = []
        self.next_artifact_id = 1
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
            correlation_id=event.correlation_id,
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

    def close_latest_fulfillment_job_for_story(
        self,
        *,
        story_number: str,
        event_id: str,
    ) -> FulfillmentJobRecord | None:
        self.closed_story_jobs.append((story_number, event_id))
        return _job(event_id="evt-prior-ready", story_number=story_number).model_copy(
            update={"status": "completed"}
        )

    def record_rework_requested_for_story(
        self,
        *,
        story_number: str,
        event_id: str,
        target_state: str,
    ) -> FulfillmentJobRecord | None:
        self.rework_story_jobs.append((story_number, event_id, target_state))
        return _job(event_id="evt-prior-ready", story_number=story_number).model_copy(
            update={"status": "completed"}
        )

    def reject_latest_fulfillment_job_for_story(
        self,
        *,
        story_number: str,
        event_id: str,
    ) -> FulfillmentJobRecord | None:
        self.rejected_story_jobs.append((story_number, event_id))
        return _job(event_id="evt-prior-ready", story_number=story_number).model_copy(
            update={"status": "rejected"}
        )

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
        self.json_artifacts.append((job_id, story_number, artifact_kind, schema_version, payload))
        artifact = ArtifactBlobRecord(
            id=self.next_artifact_id,
            job_id=job_id,
            story_number=story_number,
            artifact_kind=artifact_kind,
            schema_version=schema_version,
            payload_json=payload,
            sha256="a" * 64,
            created_at=datetime(2026, 5, 13, 15, self.next_artifact_id, tzinfo=UTC),
        )
        self.artifact_blob_records[self.next_artifact_id] = artifact
        self.next_artifact_id += 1
        return artifact

    def get_artifact_blob(self, artifact_id: int) -> ArtifactBlobRecord:
        if artifact_id not in self.artifact_blob_records:
            raise KeyError(f"Artifact blob not found: {artifact_id}")
        return self.artifact_blob_records[artifact_id]

    def artifact_refs_for_job(self, job_id: str) -> list[ArtifactRefRecord]:
        return self.artifact_ref_records.get(job_id, [])

    def recent_lifecycle_events(self, *, limit: int = 50) -> list[LifecycleEventRecord]:
        return self.lifecycle_event_records[:limit]

    def recent_fulfillment_jobs(self, *, limit: int = 50) -> list[FulfillmentJobRecord]:
        return self.fulfillment_job_records[:limit]


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


def _settings_with_admin_token(tmp_path: Path) -> RuntimeSettings:
    return _settings(tmp_path).model_copy(update={"admin_api_token": "admin-token"})


def _settings_with_admin_console(tmp_path: Path) -> RuntimeSettings:
    return _settings(tmp_path).model_copy(
        update={
            "admin_auth_mode": "dev_basic",
            "admin_console_username": "console-admin",
            "admin_console_password": "console-password",
        }
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
        correlation_id=f"corr-{event_id}",
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


def test_load_runtime_settings_reads_admin_api_token(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                f"JEDI_AUDIT_ROOT={tmp_path}",
                "JEDI_ADMIN_API_TOKEN=admin-token",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_runtime_settings(env_path)

    assert settings.admin_api_token == "admin-token"


def test_load_runtime_settings_reads_admin_console_credentials(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                f"JEDI_AUDIT_ROOT={tmp_path}",
                "JEDI_ENVIRONMENT=development",
                "JEDI_ADMIN_AUTH_MODE=dev_basic",
                "JEDI_ADMIN_CONSOLE_USERNAME=console-admin",
                "JEDI_ADMIN_CONSOLE_PASSWORD=console-password",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_runtime_settings(env_path)

    assert settings.admin_console_username == "console-admin"
    assert settings.admin_console_password == "console-password"
    assert settings.runtime_environment == "development"
    assert settings.admin_auth_mode == "dev_basic"


def test_load_runtime_settings_defaults_admin_console_auth_disabled(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                f"JEDI_AUDIT_ROOT={tmp_path}",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_runtime_settings(env_path)

    assert settings.runtime_environment == "development"
    assert settings.admin_auth_mode == "disabled"


def test_load_runtime_settings_reads_lifecycle_webhook_hmac_config(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                f"JEDI_AUDIT_ROOT={tmp_path}",
                "JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE=hmac_sha256",
                "JEDI_LIFECYCLE_WEBHOOK_SECRET=webhook-secret",
                "JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS=120",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_runtime_settings(env_path)

    assert settings.lifecycle_webhook_auth_mode == "hmac_sha256"
    assert settings.lifecycle_webhook_secret == "webhook-secret"
    assert settings.lifecycle_webhook_max_skew_seconds == 120


def test_validate_runtime_settings_allows_development_disabled_auth(
    tmp_path: Path,
) -> None:
    validate_runtime_settings(_settings(tmp_path))


def test_validate_runtime_settings_rejects_production_disabled_webhook_auth(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(update={"runtime_environment": "production"})

    with pytest.raises(RuntimeConfigError, match="JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE"):
        validate_runtime_settings(settings)


def test_validate_runtime_settings_rejects_production_hmac_without_secret(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": None,
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_LIFECYCLE_WEBHOOK_SECRET"):
        validate_runtime_settings(settings)


def test_validate_runtime_settings_rejects_production_without_admin_auth(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "webhook-secret",
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_ADMIN_AUTH_MODE"):
        validate_runtime_settings(settings)


def test_validate_runtime_settings_rejects_development_basic_auth_in_production(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "webhook-secret",
            "admin_auth_mode": "dev_basic",
            "admin_console_username": "admin",
            "admin_console_password": "password",
        }
    )

    with pytest.raises(RuntimeConfigError, match="dev_basic"):
        validate_runtime_settings(settings)


def test_validate_runtime_settings_rejects_unimplemented_production_admin_auth(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "webhook-secret",
            "admin_auth_mode": "oidc",
        }
    )

    with pytest.raises(RuntimeConfigError, match="not implemented"):
        validate_runtime_settings(settings)


def test_validate_runtime_settings_requires_production_model_provider(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "webhook-secret",
            "admin_auth_mode": "oidc",
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_MODEL_PROVIDER"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_requires_openai_production_secrets(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "webhook-secret",
            "admin_auth_mode": "oidc",
            "model_provider": "openai",
            "openai_api_key": None,
            "openai_model": None,
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    message = str(exc.value)
    assert "OPENAI_API_KEY" in message
    assert "OPENAI_MODEL" in message


def test_create_runtime_api_validates_production_settings_before_store_open(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(update={"runtime_environment": "production"})

    def store_factory(_database_url: str) -> FakeRuntimeStore:
        raise AssertionError("store factory should not be called")

    with pytest.raises(RuntimeConfigError, match="JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE"):
        create_runtime_api(settings=settings, store_factory=store_factory)


def test_process_one_runtime_fulfillment_validates_production_settings_before_store_open(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(update={"runtime_environment": "production"})

    def store_factory(_database_url: str) -> FakeRuntimeStore:
        raise AssertionError("store factory should not be called")

    with pytest.raises(RuntimeConfigError, match="JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE"):
        process_one_runtime_fulfillment(
            settings=settings,
            store_factory=store_factory,
            transport=RecordingTransport([]),
        )


def test_runtime_lifecycle_webhook_rejects_when_auth_disabled_in_production(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    settings = _settings(tmp_path).model_copy(update={"runtime_environment": "production"})

    with pytest.raises(RuntimeConfigError, match="JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE"):
        create_runtime_api(
            settings=settings,
            store_factory=lambda _database_url: store,
        )

    assert store.recorded_events == []
    assert store.enqueued_jobs == []


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


def test_load_runtime_settings_reads_update_set_apply_controls(
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
                "JEDI_UPDATE_SET_APPLY=true",
                "JEDI_UPDATE_SET_USER_NAME=jedi.integration",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_runtime_settings(env_path)

    assert settings.update_set_apply is True
    assert settings.update_set_user_name == "jedi.integration"


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


def test_artifact_read_requires_admin_bearer_token(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/artifacts/1")

    assert response.status_code == 401


def test_artifact_read_rejects_wrong_admin_bearer_token(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/artifacts/1",
        headers={"Authorization": "Bearer wrong-token"},
    )

    assert response.status_code == 403


def test_artifact_read_returns_metadata_and_payload(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.artifact_blob_records[2] = ArtifactBlobRecord(
        id=2,
        job_id="job-evt-001",
        story_number="STRY0010013",
        artifact_kind="implementation_candidate",
        schema_version="implementation-candidate-v1",
        payload_json={
            "story_number": "STRY0010013",
            "changes": [{"fields": {"element": "u_ai_review_notes"}}],
        },
        sha256="a" * 64,
        created_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
    )
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/artifacts/2",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 2,
        "job_id": "job-evt-001",
        "story_number": "STRY0010013",
        "artifact_kind": "implementation_candidate",
        "schema_version": "implementation-candidate-v1",
        "sha256": "a" * 64,
        "created_at": "2026-05-13T15:00:00Z",
        "payload": {
            "story_number": "STRY0010013",
            "changes": [{"fields": {"element": "u_ai_review_notes"}}],
        },
    }
    assert "story-sys-id" not in response.text


def test_artifact_read_returns_404_for_missing_artifact(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/artifacts/404",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 404


def test_job_artifacts_lists_only_refs_for_requested_job(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.artifact_ref_records["job-evt-001"] = [
        ArtifactRefRecord(
            id=1,
            job_id="job-evt-001",
            artifact_kind="implementation_packet",
            path="db://artifact_blobs/1",
            sha256="a" * 64,
            artifact_id=1,
            created_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
        ),
        ArtifactRefRecord(
            id=2,
            job_id="job-evt-001",
            artifact_kind="implementation_candidate",
            path="db://artifact_blobs/2",
            sha256="b" * 64,
            artifact_id=2,
            created_at=datetime(2026, 5, 13, 15, 1, tzinfo=UTC),
        ),
    ]
    store.artifact_ref_records["job-other"] = [
        ArtifactRefRecord(
            id=3,
            job_id="job-other",
            artifact_kind="implementation_candidate",
            path="db://artifact_blobs/3",
            sha256="c" * 64,
            artifact_id=3,
            created_at=datetime(2026, 5, 13, 15, 2, tzinfo=UTC),
        )
    ]
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/jobs/job-evt-001/artifacts",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "job_id": "job-evt-001",
        "artifacts": [
            {
                "id": 1,
                "job_id": "job-evt-001",
                "artifact_kind": "implementation_packet",
                "path": "db://artifact_blobs/1",
                "sha256": "a" * 64,
                "artifact_id": 1,
                "created_at": "2026-05-13T15:00:00Z",
            },
            {
                "id": 2,
                "job_id": "job-evt-001",
                "artifact_kind": "implementation_candidate",
                "path": "db://artifact_blobs/2",
                "sha256": "b" * 64,
                "artifact_id": 2,
                "created_at": "2026-05-13T15:01:00Z",
            },
        ],
    }


def test_admin_lifecycle_events_lists_recent_events(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.lifecycle_event_records = [
        LifecycleEventRecord(
            event_id="evt-002",
            event_type="story_state_changed",
            story_number="STRY0010002",
            payload_json={
                "story_number": "STRY0010002",
                "story_sys_id": "secret-sys-id-payload",
            },
            correlation_id="corr-evt-002",
            received_at=datetime(2026, 5, 14, 18, 0, tzinfo=UTC),
            validation_status="accepted",
        )
    ]
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/admin/lifecycle-events",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "events": [
            {
                "event_id": "evt-002",
                "event_type": "story_state_changed",
                "story_number": "STRY0010002",
                "correlation_id": "corr-evt-002",
                "received_at": "2026-05-14T18:00:00Z",
                "validation_status": "accepted",
            }
        ]
    }
    assert "story_sys_id" not in response.text


def test_admin_jobs_lists_recent_fulfillment_jobs(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-002", story_number="STRY0010002").model_copy(
            update={"status": "rejected", "last_error": "Story returned to Draft"}
        )
    ]
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/admin/jobs",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "jobs": [
            {
                "job_id": "job-evt-002",
                "event_id": "evt-002",
                "story_number": "STRY0010002",
                "correlation_id": "corr-evt-002",
                "status": "rejected",
                "attempt_count": 1,
                "created_at": "2026-05-13T15:00:00Z",
                "updated_at": "2026-05-13T15:01:00Z",
                "locked_by": "worker-1",
                "locked_at": "2026-05-13T15:01:00Z",
                "last_error": "Story returned to Draft",
            }
        ]
    }


def test_admin_jobs_redacts_sensitive_diagnostics(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-002", story_number="STRY0010002").model_copy(
            update={
                "status": "failed",
                "last_error": (
                    "connection failed for "
                    "postgresql://jedi:super-secret@db.example.invalid:5432/jedi"
                ),
            }
        )
    ]
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/admin/jobs",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    assert "super-secret" not in response.text
    assert "***REDACTED***" in response.text


def test_admin_console_requires_configured_credentials(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin", auth=("console-admin", "console-password"))

    assert response.status_code == 503


def test_admin_console_is_disabled_without_explicit_auth_mode(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    settings = _settings(tmp_path).model_copy(
        update={
            "admin_console_username": "console-admin",
            "admin_console_password": "console-password",
        }
    )
    client = TestClient(
        create_runtime_api(
            settings=settings,
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin", auth=("console-admin", "console-password"))

    assert response.status_code == 503
    assert response.json()["detail"] == "admin console authentication is disabled"


def test_admin_console_rejects_dev_basic_in_production_environment(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    settings = _settings_with_admin_console(tmp_path).model_copy(
        update={"runtime_environment": "production"}
    )

    with pytest.raises(RuntimeConfigError, match="dev_basic"):
        create_runtime_api(
            settings=settings,
            store_factory=lambda _database_url: store,
        )

    assert store.recorded_events == []


def test_admin_console_future_oidc_mode_fails_closed_until_implemented(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    settings = _settings(tmp_path).model_copy(update={"admin_auth_mode": "oidc"})
    client = TestClient(
        create_runtime_api(
            settings=settings,
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin")

    assert response.status_code == 501
    assert response.json()["detail"] == "admin auth mode is not implemented: oidc"


def test_admin_console_future_servicenow_oauth_mode_fails_closed_until_implemented(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    settings = _settings(tmp_path).model_copy(update={"admin_auth_mode": "servicenow_oauth"})
    client = TestClient(
        create_runtime_api(
            settings=settings,
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin")

    assert response.status_code == 501
    assert response.json()["detail"] == ("admin auth mode is not implemented: servicenow_oauth")


def test_admin_console_requires_basic_auth(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_console(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == 'Basic realm="jedi-admin"'


def test_admin_console_rejects_wrong_basic_auth(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_console(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin", auth=("console-admin", "wrong-password"))

    assert response.status_code == 401


def test_admin_console_renders_jobs_events_and_artifact_links(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.lifecycle_event_records = [
        LifecycleEventRecord(
            event_id="evt-002",
            event_type="story_state_changed",
            story_number="STRY0010002",
            payload_json={"story_number": "STRY0010002", "story_sys_id": "hidden"},
            correlation_id="corr-evt-002",
            received_at=datetime(2026, 5, 14, 18, 0, tzinfo=UTC),
            validation_status="accepted",
        )
    ]
    store.fulfillment_job_records = [
        _job(event_id="evt-002", story_number="STRY0010002").model_copy(
            update={"status": "rejected", "last_error": "Story returned to Draft"}
        )
    ]
    store.artifact_ref_records["job-evt-002"] = [
        ArtifactRefRecord(
            id=3,
            job_id="job-evt-002",
            artifact_kind="implementation_candidate",
            path="db://artifact_blobs/3",
            sha256="c" * 64,
            artifact_id=3,
            created_at=datetime(2026, 5, 14, 18, 1, tzinfo=UTC),
        )
    ]
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_console(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin", auth=("console-admin", "console-password"))

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "JEDI Admin Console" in response.text
    assert "Fulfillment Jobs" in response.text
    assert "Lifecycle Events" in response.text
    assert "STRY0010002" in response.text
    assert "corr-evt-002" in response.text
    assert "rejected" in response.text
    assert "Story returned to Draft" in response.text
    assert "/admin/artifacts/3" in response.text
    assert "implementation_candidate" in response.text
    assert "story_sys_id" not in response.text
    assert "secret-sys-id-payload" not in response.text


def test_admin_console_artifact_view_renders_payload_with_basic_auth(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.artifact_blob_records[3] = ArtifactBlobRecord(
        id=3,
        job_id="job-evt-002",
        story_number="STRY0010002",
        artifact_kind="implementation_candidate",
        schema_version="implementation-candidate-v1",
        payload_json={
            "story_number": "STRY0010002",
            "changes": [{"fields": {"element": "u_vendor_reference"}}],
        },
        sha256="d" * 64,
        created_at=datetime(2026, 5, 14, 18, 2, tzinfo=UTC),
    )
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_console(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin/artifacts/3", auth=("console-admin", "console-password"))

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Artifact 3" in response.text
    assert "implementation_candidate" in response.text
    assert "u_vendor_reference" in response.text
    assert "&quot;" in response.text


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
                json_body={"result": [{"name": "rm_story", "label": "Story"}]},
            ),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "element": "description",
                            "column_label": "Description",
                            "internal_type": "string",
                            "max_length": "4000",
                        }
                    ]
                },
            ),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "sys_id": "rm-story-main-section",
                            "name": "rm_story",
                            "caption": "",
                            "view": {"display_value": "Default view", "value": "default"},
                        }
                    ]
                },
            ),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "sys_id": "description-element",
                            "element": "description",
                            "position": "2",
                        }
                    ]
                },
            ),
            HttpResponse(status_code=200, json_body={"result": []}),
            HttpResponse(status_code=200, json_body={"result": []}),
            HttpResponse(status_code=200, json_body={"result": []}),
            HttpResponse(status_code=200, json_body={"result": []}),
            HttpResponse(status_code=200, json_body={"result": []}),
            HttpResponse(status_code=200, json_body={"result": []}),
            HttpResponse(status_code=200, json_body={"result": []}),
            HttpResponse(status_code=200, json_body={"result": []}),
            HttpResponse(
                status_code=200,
                json_body={
                    "output_text": (
                        '{"changes":[{"table":"sys_dictionary","operation":"insert",'
                        '"fields":[{"name":"name","value":"rm_story"},'
                        '{"name":"element","value":"u_ai_review_notes"}],'
                        '"sys_id":null,"rationale":null},'
                        '{"table":"sys_ui_form","operation":"update",'
                        '"fields":[{"name":"name","value":"rm_story"},'
                        '{"name":"field_order","value":"u_ai_review_notes"},'
                        '{"name":"placement_anchor","value":"description"},'
                        '{"name":"placement_position","value":"below"}],'
                        '"sys_id":null,"rationale":null}],'
                        '"test_plan":["Confirm the field exists."],'
                        '"rollback_notes":["Remove the field."]}'
                    )
                },
            ),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "sys_id": "rm-story-main-section",
                            "name": "rm_story",
                            "caption": "",
                            "view": {"display_value": "Default view", "value": "default"},
                        }
                    ]
                },
            ),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "sys_id": "description-element",
                            "element": "description",
                            "position": "2",
                        }
                    ]
                },
            ),
            HttpResponse(
                status_code=200,
                json_body={"result": [{"operation_uri": "/api/1860704/jedi_update_set_import"}]},
            ),
            HttpResponse(status_code=201, json_body={"result": {"status": "imported"}}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "sys_id": "remote-update-set-sys-id",
                            "name": "JEDI STRY0010013 - AI Candidate",
                        }
                    ]
                },
            ),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "label": "Ready for Testing",
                            "value": "-7",
                            "sequence": "300",
                            "inactive": "false",
                        }
                    ]
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
        "GET",
        "GET",
        "GET",
        "GET",
        "GET",
        "GET",
        "GET",
        "GET",
        "GET",
        "GET",
        "GET",
        "GET",
        "POST",
        "GET",
        "GET",
        "GET",
        "POST",
        "GET",
        "GET",
        "PATCH",
    ]
    assert transport.requests[5].url.endswith("/api/now/table/sys_db_object")
    assert transport.requests[5].params["sysparm_query"] == "name=rm_story"
    assert transport.requests[6].url.endswith("/api/now/table/sys_dictionary")
    assert transport.requests[6].params["sysparm_query"] == "name=rm_story"
    assert transport.requests[7].url.endswith("/api/now/table/sys_ui_section")
    assert transport.requests[7].params["sysparm_query"] == "name=rm_story"
    assert transport.requests[8].url.endswith("/api/now/table/sys_ui_element")
    assert transport.requests[8].params["sysparm_query"] == (
        "name=rm_story^sys_ui_section=rm-story-main-section"
    )
    assert transport.requests[9].url.endswith("/api/now/table/sys_security_acl")
    assert transport.requests[9].params["sysparm_query"] == "name=rm_story"
    assert transport.requests[10].url.endswith("/api/now/table/sys_script")
    assert transport.requests[10].params["sysparm_query"] == "collection=rm_story"
    assert transport.requests[17].url == "https://api.openai.com/v1/responses"
    assert transport.requests[17].headers["Authorization"] == "Bearer openai-key"
    assert "openai-key" not in repr(transport.requests[17].body)
    assert transport.requests[18].url.endswith("/api/now/table/sys_ui_section")
    assert transport.requests[18].params["sysparm_query"] == "name=rm_story"
    assert transport.requests[19].url.endswith("/api/now/table/sys_ui_element")
    assert transport.requests[19].params["sysparm_query"] == (
        "name=rm_story^sys_ui_section=rm-story-main-section"
    )
    assert transport.requests[20].url.endswith("/api/now/table/sys_ws_operation")
    assert transport.requests[20].params["sysparm_query"] == (
        "web_service_definition.service_id=jedi_update_set_import"
        "^name=import_update_set_xml^active=true"
    )
    assert transport.requests[21].url.endswith("/api/1860704/jedi_update_set_import")
    assert (
        "sys_dictionary_rm_story_u_ai_review_notes" in transport.requests[21].body["update_set_xml"]
    )
    assert transport.requests[22].url.endswith("/api/now/table/sys_remote_update_set")
    assert transport.requests[22].params["sysparm_query"].startswith("remote_sys_id=")
    assert transport.requests[23].url.endswith("/api/now/table/sys_choice")
    assert transport.requests[23].params["sysparm_query"] == (
        "name=rm_story^element=state^inactive=false"
    )
    assert store.artifact_refs == []
    assert [artifact[2] for artifact in store.json_artifacts] == [
        "instance_context_bundle",
        "implementation_packet",
        "implementation_candidate",
    ]
    assert store.json_artifacts[0][3] == "servicenow-surface-context-v1"
    assert store.json_artifacts[1][3] == "implementation-packet-v1"
    assert store.json_artifacts[2][3] == "implementation-candidate-v1"
    assert store.json_artifacts[0][4]["target_table"] == "rm_story"
    assert store.json_artifacts[1][4]["story"]["number"] == "STRY0010013"
    assert store.json_artifacts[1][4]["instance_context"]["target_table"] == "rm_story"
    assert store.json_artifacts[2][4]["changes"][0]["fields"]["element"] == ("u_ai_review_notes")
    assert (
        "ServiceNow retrieved Update Set handoff created"
        in transport.requests[-1].body["work_notes"]
    )
    assert transport.requests[-1].body["state"] == "-7"
    assert transport.requests[-1].body["u_ai_status"] == "Ready for Testing"
    assert "sys_id=remote-update-set-sys-id" in transport.requests[-1].body["work_notes"]
    assert "db://artifact_blobs/3" in transport.requests[-1].body["work_notes"]


def test_process_one_runtime_fulfillment_generates_incident_update_set_candidate(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore(claimed_job=_job().model_copy(update={"story_number": "STRY0010001"}))
    incident_story = {
        "sys_id": "incident-story-sys-id",
        "number": "STRY0010001",
        "short_description": "Add a New Field to the Incident Form",
        "description": (
            "As an incident manager, I would like a new field added to the "
            "Incident form.\n\n- Field Name: Antics\n- Field Type: String\n"
            "- Length: 4000"
        ),
        "acceptance_criteria": (
            "- A new field labeled Antics exists on the incident form.\n"
            "- The field is placed below the Description field."
        ),
        "story_points": "2",
        "priority": "4",
        "state": "Ready",
    }
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(status_code=200, json_body={"result": [incident_story]}),
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
            HttpResponse(
                status_code=200,
                json_body={"result": {"sys_id": "incident-story-sys-id"}},
            ),
            HttpResponse(
                status_code=200,
                json_body={"result": [dict(incident_story, state="Work in Progress")]},
            ),
            HttpResponse(
                status_code=200,
                json_body={"result": [{"name": "incident", "label": "Incident"}]},
            ),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "element": "description",
                            "column_label": "Description",
                            "internal_type": "string",
                            "max_length": "4000",
                        }
                    ]
                },
            ),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "sys_id": "incident-main-section",
                            "name": "incident",
                            "caption": "",
                            "view": {"display_value": "Default view", "value": "default"},
                            "sys_user": "",
                        }
                    ]
                },
            ),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {"sys_id": "number-element", "element": "number", "position": "1"},
                        {
                            "sys_id": "description-element",
                            "element": "description",
                            "position": "2",
                        },
                    ]
                },
            ),
            HttpResponse(status_code=200, json_body={"result": []}),
            HttpResponse(status_code=200, json_body={"result": []}),
            HttpResponse(status_code=200, json_body={"result": []}),
            HttpResponse(status_code=200, json_body={"result": []}),
            HttpResponse(status_code=200, json_body={"result": []}),
            HttpResponse(status_code=200, json_body={"result": []}),
            HttpResponse(status_code=200, json_body={"result": []}),
            HttpResponse(status_code=200, json_body={"result": []}),
            HttpResponse(
                status_code=200,
                json_body={
                    "output_text": (
                        '{"changes":[{"table":"sys_dictionary","operation":"insert",'
                        '"fields":[{"name":"name","value":"incident"},'
                        '{"name":"element","value":"u_antics"},'
                        '{"name":"column_label","value":"Antics"},'
                        '{"name":"internal_type","value":"string"},'
                        '{"name":"max_length","value":4000}],'
                        '"sys_id":null,"rationale":null},'
                        '{"table":"sys_ui_form","operation":"update",'
                        '"fields":[{"name":"name","value":"incident"},'
                        '{"name":"field_order","value":"u_antics"},'
                        '{"name":"placement_anchor","value":"description"},'
                        '{"name":"placement_position","value":"below"}],'
                        '"sys_id":null,"rationale":null}],'
                        '"test_plan":["Confirm Antics below Description."],'
                        '"rollback_notes":["Remove incident.u_antics."]}'
                    )
                },
            ),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "sys_id": "incident-main-section",
                            "name": "incident",
                            "caption": "",
                            "view": {"display_value": "Default view", "value": "default"},
                            "sys_user": "",
                        }
                    ]
                },
            ),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {"sys_id": "number-element", "element": "number", "position": "1"},
                        {
                            "sys_id": "description-element",
                            "element": "description",
                            "position": "2",
                        },
                    ]
                },
            ),
            HttpResponse(
                status_code=200,
                json_body={"result": [{"operation_uri": "/api/1860704/jedi_update_set_import"}]},
            ),
            HttpResponse(status_code=201, json_body={"result": {"status": "imported"}}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "sys_id": "incident-remote-update-set",
                            "name": "JEDI STRY0010001 - AI Candidate",
                        }
                    ]
                },
            ),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "label": "Ready for Testing",
                            "value": "-7",
                            "sequence": "300",
                            "inactive": "false",
                        }
                    ]
                },
            ),
            HttpResponse(
                status_code=200,
                json_body={"result": {"sys_id": "incident-story-sys-id"}},
            ),
        ]
    )

    result = process_one_runtime_fulfillment(
        settings=_settings_with_openai(tmp_path, apply=True),
        store_factory=lambda _database_url: store,
        transport=transport,
    )

    posted_xml_requests = [
        request
        for request in transport.requests
        if request.method == "POST" and request.url.endswith("/api/1860704/jedi_update_set_import")
    ]
    assert result.status == "completed"
    assert len(posted_xml_requests) == 1
    assert "sys_dictionary_incident_u_antics" in posted_xml_requests[0].body["update_set_xml"]
    assert "sys_ui_section_incident-main-section" in posted_xml_requests[0].body["update_set_xml"]
    assert transport.requests[-1].body["state"] == "-7"
    assert transport.requests[-1].body["u_ai_status"] == "Ready for Testing"


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
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "label": "Draft",
                            "value": "-6",
                            "sequence": "10",
                            "inactive": "false",
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
        "GET",
        "PATCH",
    ]
    assert transport.requests[-2].url.endswith("/api/now/table/sys_choice")
    assert transport.requests[-1].body["work_notes"] == (
        "Automated fulfillment failed for lifecycle event evt-001. "
        "Job: job-evt-001. Error: fresh_story_state_mismatch"
    )
    assert transport.requests[-1].body["state"] == "-6"
    assert transport.requests[-1].body["u_ai_status"] == "Automation Failed"


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
                            "client-secret leaked with postgresql://jedi:secret@localhost:5432/jedi"
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
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "label": "Draft",
                            "value": "-6",
                            "sequence": "10",
                            "inactive": "false",
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
