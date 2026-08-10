from __future__ import annotations

import asyncio
import base64
import inspect
import json
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any, SupportsIndex, cast
from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from jedi_devproject import (
    admin_routes,
    runtime_auth,
    runtime_config,
    runtime_fulfillment,
    runtime_servicenow,
)
from jedi_devproject.admin_routes import (
    _admin_alert_row,
    _admin_artifact_payload_json,
    _admin_artifact_payload_view,
    _admin_request_size_error,
    _bounded_redacted_artifact_payload,
    _get_job_or_404,
    _safe_request_id,
)
from jedi_devproject.fulfillment_worker import FulfillmentExecutionResult
from jedi_devproject.lifecycle_events import LifecycleStateChangeEvent
from jedi_devproject.operational_store import (
    ArtifactBlobRecord,
    ArtifactRefRecord,
    FulfillmentJobRecord,
    FulfillmentJobStatusSummaryRecord,
    JobEventRecord,
    LifecycleEventRecord,
)
from jedi_devproject.rate_limit import (
    MAX_CONFIGURABLE_RATE_LIMIT_BUCKETS,
    MAX_CONFIGURABLE_RATE_LIMIT_REQUESTS,
    MAX_CONFIGURABLE_RATE_LIMIT_WINDOW_SECONDS,
    InMemoryRateLimiter,
)
from jedi_devproject.runtime import (
    RuntimeConfigError,
    RuntimeSettings,
    SplitServiceNowClient,
    create_runtime_api,
    load_runtime_settings,
    process_one_runtime_fulfillment,
    validate_runtime_settings,
)
from jedi_devproject.runtime_servicenow import (
    _servicenow_complete_notifier,
    _servicenow_failure_notifier,
)
from jedi_devproject.servicenow import HttpRequest, HttpResponse, ServiceNowClient


class FakeAdminStreamingRequest:
    def __init__(self, *, chunks: list[bytes], headers: dict[str, str] | None = None) -> None:
        self._chunks = chunks
        self.headers = headers or {}

    async def stream(self) -> Any:
        for chunk in self._chunks:
            yield chunk


class FakeRuntimeStore:
    def __init__(self, claimed_job: FulfillmentJobRecord | None = None) -> None:
        self.claimed_job = claimed_job
        self.recorded_events: list[str] = []
        self.enqueued_jobs: list[tuple[str, str]] = []
        self.closed_story_jobs: list[tuple[str, str]] = []
        self.rework_story_jobs: list[tuple[str, str, str]] = []
        self.rejected_story_jobs: list[tuple[str, str]] = []
        self.completed_jobs: list[tuple[str, str, str]] = []
        self.failed_jobs: list[tuple[str, str, str]] = []
        self.artifact_refs: list[tuple[str, str, str, str]] = []
        self.json_artifacts: list[tuple[str, str, str, str, dict[str, Any]]] = []
        self.artifact_blob_records: dict[int, ArtifactBlobRecord] = {}
        self.artifact_ref_records: dict[str, list[ArtifactRefRecord]] = {}
        self.job_event_records: dict[str, list[JobEventRecord]] = {}
        self.lifecycle_event_records: list[LifecycleEventRecord] = []
        self.fulfillment_job_records: list[FulfillmentJobRecord] = []
        self.lifecycle_event_limits: list[int] = []
        self.fulfillment_job_limits: list[int] = []
        self.fulfillment_job_status_summary_stale_before: list[datetime] = []
        self.fulfillment_job_status_summary_record = FulfillmentJobStatusSummaryRecord(
            queued=0,
            running=0,
            completed=0,
            failed=0,
            rejected=0,
            stale_running=0,
            total=0,
        )
        self.get_job_ids: list[str] = []
        self.raise_on_recent_lifecycle_events = False
        self.schema_ready = True
        self.raise_on_schema_ready = False
        self.schema_ready_checks = 0
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
        worker_id: str,
        message: str,
    ) -> FulfillmentJobRecord:
        self.completed_jobs.append((job_id, worker_id, message))
        assert self.claimed_job is not None
        return self.claimed_job.model_copy(update={"status": "completed"})

    def fail_fulfillment_job(
        self,
        *,
        job_id: str,
        worker_id: str,
        error_message: str,
    ) -> FulfillmentJobRecord:
        self.failed_jobs.append((job_id, worker_id, error_message))
        assert self.claimed_job is not None
        return self.claimed_job.model_copy(update={"status": "failed"})

    def touch_fulfillment_job_heartbeat(
        self,
        *,
        job_id: str,
        worker_id: str,
    ) -> FulfillmentJobRecord | None:
        if self.claimed_job is None:
            return None
        return self.claimed_job.model_copy(update={"updated_at": datetime.now(UTC)})

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

    def get_job(self, job_id: str) -> FulfillmentJobRecord:
        self.get_job_ids.append(job_id)
        for job in self.fulfillment_job_records:
            if job.job_id == job_id:
                return job
        if self.claimed_job is not None and self.claimed_job.job_id == job_id:
            return self.claimed_job
        raise KeyError(f"Fulfillment job not found: {job_id}")

    def artifact_refs_for_job(self, job_id: str) -> list[ArtifactRefRecord]:
        return self.artifact_ref_records.get(job_id, [])

    def job_events_for_job(self, job_id: str) -> list[JobEventRecord]:
        return self.job_event_records.get(job_id, [])

    def recent_lifecycle_events(self, *, limit: int = 50) -> list[LifecycleEventRecord]:
        if self.raise_on_recent_lifecycle_events:
            raise RuntimeError("postgresql://jedi:secret@db.example.invalid/jedi unavailable")
        self.lifecycle_event_limits.append(limit)
        return self.lifecycle_event_records[:limit]

    def verify_schema_ready(self) -> bool:
        self.schema_ready_checks += 1
        if self.raise_on_schema_ready:
            raise RuntimeError("postgresql://jedi:secret@db.example.invalid/jedi missing table")
        return self.schema_ready

    def recent_fulfillment_jobs(self, *, limit: int = 50) -> list[FulfillmentJobRecord]:
        self.fulfillment_job_limits.append(limit)
        return self.fulfillment_job_records[:limit]

    def fulfillment_job_status_summary(
        self,
        *,
        stale_before: datetime,
    ) -> FulfillmentJobStatusSummaryRecord:
        self.fulfillment_job_status_summary_stale_before.append(stale_before)
        return self.fulfillment_job_status_summary_record


def _runtime_route_endpoint(app: Any, path: str) -> Any:
    for route in app.routes:
        if getattr(route, "path", None) == path:
            return route.endpoint
    raise AssertionError(f"runtime route was not registered: {path}")


class RecordingTransport:
    def __init__(self, responses: list[HttpResponse]) -> None:
        self.responses = responses
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        return self.responses.pop(0)


class RecordingServiceNowEndpoint:
    def __init__(self, name: str) -> None:
        self.name = name
        self.calls: list[str] = []

    def fetch_ready_stories(
        self,
        project_sys_id: str | None = None,
        *,
        limit: int = 100,
    ) -> list[Any]:
        self.calls.append(f"fetch_ready_stories:{project_sys_id}:{limit}")
        return []

    def fetch_stories(self, sysparm_query: str | None = None, *, limit: int = 100) -> list[Any]:
        self.calls.append(f"fetch_stories:{sysparm_query}:{limit}")
        return []

    def fetch_story_state_choices(self) -> list[Any]:
        self.calls.append("fetch_story_state_choices")
        return []

    def fetch_story_dictionary_fields(self) -> list[Any]:
        self.calls.append("fetch_story_dictionary_fields")
        return []

    def update_story_fields(self, story_sys_id: str, fields: dict[str, object]) -> dict[str, str]:
        self.calls.append(f"update_story_fields:{story_sys_id}:{sorted(fields)}")
        return {"sys_id": story_sys_id}

    def fetch_table_record(self, *, table: str, lookup: dict[str, str]) -> dict[str, str] | None:
        self.calls.append(f"fetch_table_record:{table}:{sorted(lookup)}")
        return None

    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, str]]:
        self.calls.append(f"fetch_table_records:{table}:{sorted(lookup)}:{fields}:{limit}")
        return []

    def upsert_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: dict[str, object],
    ) -> dict[str, str]:
        self.calls.append(f"upsert_table_record:{table}:{sorted(lookup)}:{sorted(fields)}")
        return {"sys_id": "record-sys-id"}

    def import_update_set_xml(self, *, service_id: str, update_set_xml: str) -> dict[str, str]:
        self.calls.append(f"import_update_set_xml:{service_id}:{len(update_set_xml)}")
        return {"status": "imported"}


def _settings(tmp_path: Path, *, apply: bool = False) -> RuntimeSettings:
    return RuntimeSettings(
        database_url="postgresql://jedi:secret@localhost:5432/jedi",
        servicenow_instance_url="https://dev205693.service-now.com",
        servicenow_client_id="client-id",
        servicenow_client_secret="client-secret",
        worker_id="worker-1",
        audit_root=tmp_path,
        build_claim_apply=apply,
        trusted_hosts=["testserver"],
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


@pytest.mark.parametrize(
    ("field_name", "field_value", "sensitive_parts"),
    [
        ("database_url", 123, ("123",)),
        ("admin_auth_mode", "dev_basic_secret_mode", ("dev_basic_secret_mode",)),
        ("public_web_access", "worker_secret_mode", ("worker_secret_mode",)),
        ("lifecycle_webhook_max_body_bytes", "secret-bytes", ("secret-bytes",)),
    ],
)
def test_runtime_settings_validation_errors_do_not_echo_rejected_inputs(
    tmp_path: Path,
    field_name: str,
    field_value: object,
    sensitive_parts: tuple[str, ...],
) -> None:
    values: dict[str, Any] = {
        "database_url": "postgresql://jedi:secret@db.example.gov:5432/jedi",
        "servicenow_instance_url": "https://dev.example.service-now.com",
        "servicenow_client_id": "client-id",
        "servicenow_client_secret": "client-secret",
        "audit_root": tmp_path,
    }
    values[field_name] = field_value

    with pytest.raises(ValidationError) as exc:
        RuntimeSettings(**values)

    message = str(exc.value)
    assert "input_value" not in message
    for sensitive_part in sensitive_parts:
        assert sensitive_part not in message


def test_split_servicenow_client_routes_story_and_development_operations() -> None:
    story_endpoint = RecordingServiceNowEndpoint("pm")
    development_endpoint = RecordingServiceNowEndpoint("dev")
    client = SplitServiceNowClient(
        story_client=cast(ServiceNowClient, story_endpoint),
        development_client=cast(ServiceNowClient, development_endpoint),
    )

    client.fetch_stories(sysparm_query="number=STRY0010013", limit=1)
    client.fetch_story_state_choices()
    client.fetch_story_dictionary_fields()
    client.update_story_fields("story-sys-id", {"u_ai_status": "Complete"})
    client.fetch_table_records(table="sys_dictionary", lookup={"name": "incident"})
    client.fetch_table_record(table="sys_user", lookup={"user_name": "admin"})
    client.upsert_table_record(
        table="sys_remote_update_set",
        lookup={"name": "JEDI STRY0010013 - AI Candidate"},
        fields={"state": "loaded"},
    )
    client.import_update_set_xml(service_id="jedi_update_set_import", update_set_xml="<xml/>")

    assert story_endpoint.calls == [
        "fetch_stories:number=STRY0010013:1",
        "fetch_story_state_choices",
        "fetch_story_dictionary_fields",
        "update_story_fields:story-sys-id:['u_ai_status']",
    ]
    assert development_endpoint.calls == [
        "fetch_table_records:sys_dictionary:['name']:None:100",
        "fetch_table_record:sys_user:['user_name']",
        "upsert_table_record:sys_remote_update_set:['name']:['state']",
        "import_update_set_xml:jedi_update_set_import:6",
    ]


def test_split_servicenow_client_rejects_ready_story_collection_subclass_without_leak() -> None:
    class SecretBearingStories(list[Any]):
        def __bool__(self) -> bool:
            raise AssertionError("client_secret=split-ready-stories-bool-secret")

    class HostileReadyStoryEndpoint(RecordingServiceNowEndpoint):
        def fetch_ready_stories(
            self,
            project_sys_id: str | None = None,
            *,
            limit: int = 100,
        ) -> list[Any]:
            self.calls.append(f"fetch_ready_stories:{project_sys_id}:{limit}")
            return SecretBearingStories([SimpleNamespace(sys_id="story-sys-id")])

    story_endpoint = HostileReadyStoryEndpoint("pm")
    development_endpoint = RecordingServiceNowEndpoint("dev")
    client = SplitServiceNowClient(
        story_client=cast(ServiceNowClient, story_endpoint),
        development_client=cast(ServiceNowClient, development_endpoint),
    )

    with pytest.raises(RuntimeError) as exc:
        client.fetch_ready_stories(project_sys_id="project-123", limit=5)

    diagnostic = str(exc.value)
    assert diagnostic == "story lookup result is unsafe"
    assert story_endpoint.calls == ["fetch_ready_stories:project-123:5"]
    assert development_endpoint.calls == []
    assert "SecretBearingStories" not in diagnostic
    assert "split-ready-stories-bool-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_split_servicenow_client_rejects_story_lookup_collection_subclass_without_leak() -> None:
    class SecretBearingStories(list[Any]):
        def __len__(self) -> int:
            raise AssertionError("client_secret=split-stories-len-secret")

    class HostileStoryEndpoint(RecordingServiceNowEndpoint):
        def fetch_stories(
            self,
            sysparm_query: str | None = None,
            *,
            limit: int = 100,
        ) -> list[Any]:
            self.calls.append(f"fetch_stories:{sysparm_query}:{limit}")
            return SecretBearingStories([SimpleNamespace(sys_id="story-sys-id")])

    story_endpoint = HostileStoryEndpoint("pm")
    development_endpoint = RecordingServiceNowEndpoint("dev")
    client = SplitServiceNowClient(
        story_client=cast(ServiceNowClient, story_endpoint),
        development_client=cast(ServiceNowClient, development_endpoint),
    )

    with pytest.raises(RuntimeError) as exc:
        client.fetch_stories(sysparm_query="number=STRY0010013", limit=1)

    diagnostic = str(exc.value)
    assert diagnostic == "story lookup result is unsafe"
    assert story_endpoint.calls == ["fetch_stories:number=STRY0010013:1"]
    assert development_endpoint.calls == []
    assert "SecretBearingStories" not in diagnostic
    assert "split-stories-len-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_split_servicenow_client_rejects_table_record_collection_subclass_without_leak() -> None:
    class SecretBearingRecords(list[dict[str, str]]):
        def __len__(self) -> int:
            raise AssertionError("client_secret=split-table-records-len-secret")

    class HostileDevelopmentEndpoint(RecordingServiceNowEndpoint):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, str]]:
            self.calls.append(f"fetch_table_records:{table}:{sorted(lookup)}:{fields}:{limit}")
            return SecretBearingRecords([{"sys_id": "record-sys-id"}])

    story_endpoint = RecordingServiceNowEndpoint("pm")
    development_endpoint = HostileDevelopmentEndpoint("dev")
    client = SplitServiceNowClient(
        story_client=cast(ServiceNowClient, story_endpoint),
        development_client=cast(ServiceNowClient, development_endpoint),
    )

    with pytest.raises(RuntimeError) as exc:
        client.fetch_table_records(table="sys_dictionary", lookup={"name": "incident"})

    diagnostic = str(exc.value)
    assert diagnostic == "table record lookup result is unsafe"
    assert story_endpoint.calls == []
    assert development_endpoint.calls == [
        "fetch_table_records:sys_dictionary:['name']:None:100"
    ]
    assert "SecretBearingRecords" not in diagnostic
    assert "split-table-records-len-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_split_servicenow_client_rejects_alternate_table_record_collection() -> None:
    class TupleDevelopmentEndpoint(RecordingServiceNowEndpoint):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> Any:
            self.calls.append(f"fetch_table_records:{table}:{sorted(lookup)}:{fields}:{limit}")
            return ({"sys_id": "record-sys-id"},)

    story_endpoint = RecordingServiceNowEndpoint("pm")
    development_endpoint = TupleDevelopmentEndpoint("dev")
    client = SplitServiceNowClient(
        story_client=cast(ServiceNowClient, story_endpoint),
        development_client=cast(ServiceNowClient, development_endpoint),
    )

    with pytest.raises(RuntimeError) as exc:
        client.fetch_table_records(table="sys_dictionary", lookup={"name": "incident"})

    assert str(exc.value) == "table record lookup result is unsafe"
    assert story_endpoint.calls == []
    assert development_endpoint.calls == [
        "fetch_table_records:sys_dictionary:['name']:None:100"
    ]


def test_split_servicenow_client_rejects_state_choice_collection_subclass_without_leak() -> None:
    class SecretBearingChoices(list[Any]):
        def __len__(self) -> int:
            raise AssertionError("client_secret=split-state-choices-len-secret")

    class HostileStoryEndpoint(RecordingServiceNowEndpoint):
        def fetch_story_state_choices(self) -> list[Any]:
            self.calls.append("fetch_story_state_choices")
            return SecretBearingChoices([SimpleNamespace(label="Draft", value="-6")])

    story_endpoint = HostileStoryEndpoint("pm")
    development_endpoint = RecordingServiceNowEndpoint("dev")
    client = SplitServiceNowClient(
        story_client=cast(ServiceNowClient, story_endpoint),
        development_client=cast(ServiceNowClient, development_endpoint),
    )

    with pytest.raises(RuntimeError) as exc:
        client.fetch_story_state_choices()

    diagnostic = str(exc.value)
    assert diagnostic == "story state choices result is unsafe"
    assert story_endpoint.calls == ["fetch_story_state_choices"]
    assert development_endpoint.calls == []
    assert "SecretBearingChoices" not in diagnostic
    assert "split-state-choices-len-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_split_servicenow_client_rejects_dictionary_field_collection_subclass() -> None:
    class SecretBearingFields(list[Any]):
        def __bool__(self) -> bool:
            raise AssertionError("client_secret=split-dictionary-fields-bool-secret")

    class HostileStoryEndpoint(RecordingServiceNowEndpoint):
        def fetch_story_dictionary_fields(self) -> list[Any]:
            self.calls.append("fetch_story_dictionary_fields")
            return SecretBearingFields([SimpleNamespace(element="state")])

    story_endpoint = HostileStoryEndpoint("pm")
    development_endpoint = RecordingServiceNowEndpoint("dev")
    client = SplitServiceNowClient(
        story_client=cast(ServiceNowClient, story_endpoint),
        development_client=cast(ServiceNowClient, development_endpoint),
    )

    with pytest.raises(RuntimeError) as exc:
        client.fetch_story_dictionary_fields()

    diagnostic = str(exc.value)
    assert diagnostic == "story dictionary fields result is unsafe"
    assert story_endpoint.calls == ["fetch_story_dictionary_fields"]
    assert development_endpoint.calls == []
    assert "SecretBearingFields" not in diagnostic
    assert "split-dictionary-fields-bool-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_split_servicenow_client_rejects_table_record_subclass_without_leak() -> None:
    class SecretBearingRecord(dict[str, str]):
        def __bool__(self) -> bool:
            raise AssertionError("client_secret=split-table-record-bool-secret")

    class HostileDevelopmentEndpoint(RecordingServiceNowEndpoint):
        def fetch_table_record(
            self,
            *,
            table: str,
            lookup: dict[str, str],
        ) -> dict[str, str] | None:
            self.calls.append(f"fetch_table_record:{table}:{sorted(lookup)}")
            return SecretBearingRecord({"sys_id": "record-sys-id"})

    story_endpoint = RecordingServiceNowEndpoint("pm")
    development_endpoint = HostileDevelopmentEndpoint("dev")
    client = SplitServiceNowClient(
        story_client=cast(ServiceNowClient, story_endpoint),
        development_client=cast(ServiceNowClient, development_endpoint),
    )

    with pytest.raises(RuntimeError) as exc:
        client.fetch_table_record(table="sys_user", lookup={"user_name": "admin"})

    diagnostic = str(exc.value)
    assert diagnostic == "table record lookup result is unsafe"
    assert story_endpoint.calls == []
    assert development_endpoint.calls == ["fetch_table_record:sys_user:['user_name']"]
    assert "SecretBearingRecord" not in diagnostic
    assert "split-table-record-bool-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_split_servicenow_client_rejects_upsert_response_subclass_without_leak() -> None:
    class SecretBearingResponse(dict[str, str]):
        def __len__(self) -> int:
            raise AssertionError("client_secret=split-upsert-response-len-secret")

    class HostileDevelopmentEndpoint(RecordingServiceNowEndpoint):
        def upsert_table_record(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: dict[str, object],
        ) -> dict[str, str]:
            self.calls.append(f"upsert_table_record:{table}:{sorted(lookup)}:{sorted(fields)}")
            return SecretBearingResponse({"sys_id": "record-sys-id"})

    story_endpoint = RecordingServiceNowEndpoint("pm")
    development_endpoint = HostileDevelopmentEndpoint("dev")
    client = SplitServiceNowClient(
        story_client=cast(ServiceNowClient, story_endpoint),
        development_client=cast(ServiceNowClient, development_endpoint),
    )

    with pytest.raises(RuntimeError) as exc:
        client.upsert_table_record(
            table="sys_remote_update_set",
            lookup={"name": "JEDI STRY0010013 - AI Candidate"},
            fields={"state": "loaded"},
        )

    diagnostic = str(exc.value)
    assert diagnostic == "table mutation result is unsafe"
    assert story_endpoint.calls == []
    assert development_endpoint.calls == [
        "upsert_table_record:sys_remote_update_set:['name']:['state']"
    ]
    assert "SecretBearingResponse" not in diagnostic
    assert "split-upsert-response-len-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_split_servicenow_client_rejects_update_set_import_response_subclass() -> None:
    class SecretBearingResponse(dict[str, str]):
        def __bool__(self) -> bool:
            raise AssertionError("client_secret=split-import-response-bool-secret")

    class HostileDevelopmentEndpoint(RecordingServiceNowEndpoint):
        def import_update_set_xml(
            self,
            *,
            service_id: str,
            update_set_xml: str,
        ) -> dict[str, str]:
            self.calls.append(f"import_update_set_xml:{service_id}:{len(update_set_xml)}")
            return SecretBearingResponse({"status": "imported"})

    story_endpoint = RecordingServiceNowEndpoint("pm")
    development_endpoint = HostileDevelopmentEndpoint("dev")
    client = SplitServiceNowClient(
        story_client=cast(ServiceNowClient, story_endpoint),
        development_client=cast(ServiceNowClient, development_endpoint),
    )

    with pytest.raises(RuntimeError) as exc:
        client.import_update_set_xml(service_id="jedi_update_set_import", update_set_xml="<xml/>")

    diagnostic = str(exc.value)
    assert diagnostic == "update set import result is unsafe"
    assert story_endpoint.calls == []
    assert development_endpoint.calls == ["import_update_set_xml:jedi_update_set_import:6"]
    assert "SecretBearingResponse" not in diagnostic
    assert "split-import-response-bool-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_split_servicenow_client_rejects_story_update_response_subclass_without_leak() -> None:
    class SecretBearingResponse(dict[str, str]):
        def __len__(self) -> int:
            raise AssertionError("client_secret=split-story-update-len-secret")

    class HostileStoryEndpoint(RecordingServiceNowEndpoint):
        def update_story_fields(
            self,
            story_sys_id: str,
            fields: dict[str, object],
        ) -> dict[str, str]:
            self.calls.append(f"update_story_fields:{story_sys_id}:{sorted(fields)}")
            return SecretBearingResponse({"sys_id": story_sys_id})

    story_endpoint = HostileStoryEndpoint("pm")
    development_endpoint = RecordingServiceNowEndpoint("dev")
    client = SplitServiceNowClient(
        story_client=cast(ServiceNowClient, story_endpoint),
        development_client=cast(ServiceNowClient, development_endpoint),
    )

    with pytest.raises(RuntimeError) as exc:
        client.update_story_fields("story-sys-id", {"u_ai_status": "Complete"})

    diagnostic = str(exc.value)
    assert diagnostic == "story mutation result is unsafe"
    assert story_endpoint.calls == ["update_story_fields:story-sys-id:['u_ai_status']"]
    assert development_endpoint.calls == []
    assert "SecretBearingResponse" not in diagnostic
    assert "split-story-update-len-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_split_servicenow_client_rejects_alternate_story_update_response() -> None:
    class TupleStoryEndpoint(RecordingServiceNowEndpoint):
        def update_story_fields(
            self,
            story_sys_id: str,
            fields: dict[str, object],
        ) -> Any:
            self.calls.append(f"update_story_fields:{story_sys_id}:{sorted(fields)}")
            return (("sys_id", story_sys_id),)

    story_endpoint = TupleStoryEndpoint("pm")
    development_endpoint = RecordingServiceNowEndpoint("dev")
    client = SplitServiceNowClient(
        story_client=cast(ServiceNowClient, story_endpoint),
        development_client=cast(ServiceNowClient, development_endpoint),
    )

    with pytest.raises(RuntimeError) as exc:
        client.update_story_fields("story-sys-id", {"u_ai_status": "Complete"})

    assert str(exc.value) == "story mutation result is unsafe"
    assert story_endpoint.calls == ["update_story_fields:story-sys-id:['u_ai_status']"]
    assert development_endpoint.calls == []


def _job(
    *,
    event_id: str = "evt-001",
    story_number: str = "STRY0010013",
    story_sys_id: str | None = None,
) -> FulfillmentJobRecord:
    return FulfillmentJobRecord(
        job_id=f"job-{event_id}",
        event_id=event_id,
        story_number=story_number,
        story_sys_id=story_sys_id,
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


def _complete_event_payload() -> dict[str, str]:
    payload = _ready_event_payload()
    payload.update(
        {
            "event_id": "evt-complete-001",
            "story_number": "STRY0010013",
            "story_sys_id": "story-sys-id",
            "previous_state": "Ready for Testing",
            "current_state": "Complete",
            "correlation_id": "STRY0010013-ReadyForTesting-Complete-20260516T150000Z",
        }
    )
    return payload


def _draft_rejected_event_payload() -> dict[str, str]:
    payload = _complete_event_payload()
    payload.update(
        {
            "event_id": "evt-story-rejected-001",
            "previous_state": "Ready for Testing",
            "current_state": "Draft",
            "correlation_id": "STRY0010013-ReadyForTesting-Draft-20260516T151000Z",
        }
    )
    return payload


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
            # Intake feedback assessment re-fetches the story after the claim.
            HttpResponse(status_code=200, json_body={"result": [_story_record()]}),
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
                "JEDI_CLASSIFIER_GATE=false",
                "JEDI_ADMIN_MAX_BODY_BYTES=4096",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_runtime_settings(env_path)

    assert settings.database_url == "postgresql://jedi:secret@localhost:5432/jedi"
    assert settings.worker_id == "worker-1"
    assert settings.audit_root == tmp_path
    assert settings.build_claim_apply is True
    assert settings.classifier_gate is False
    assert settings.admin_max_body_bytes == 4096
    assert settings.model_provider is None


@pytest.mark.parametrize(
    ("setting_line", "expected_error"),
    [
        ("DATABASE_URL=sqlite:///tmp/jedi.db", "DATABASE_URL"),
        (
            'DATABASE_URL="postgresql://jedi:secret@localhost:5432/jedi#fragment"',
            "DATABASE_URL",
        ),
        (
            'DATABASE_URL="postgresql://jedi:secret@localhost:5432/jedi/%0aheader"',
            "DATABASE_URL",
        ),
        ("JEDI_AUDIT_ROOT=artifacts/audit", "JEDI_AUDIT_ROOT"),
        ('JEDI_AUDIT_ROOT=" /app/artifacts/audit"', "JEDI_AUDIT_ROOT"),
        ('JEDI_AUDIT_ROOT="/app/artifacts/audit\tfallback"', "JEDI_AUDIT_ROOT"),
    ],
)
def test_load_runtime_settings_rejects_malformed_store_and_audit_values(
    tmp_path: Path,
    setting_line: str,
    expected_error: str,
) -> None:
    env_path = tmp_path / ".env"
    settings = {
        "DATABASE_URL": "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
        "SERVICENOW_INSTANCE_URL": ("SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com"),
        "SERVICENOW_CLIENT_ID": "SERVICENOW_CLIENT_ID=client-id",
        "SERVICENOW_CLIENT_SECRET": "SERVICENOW_CLIENT_SECRET=client-secret",
        "JEDI_AUDIT_ROOT": f"JEDI_AUDIT_ROOT={tmp_path}",
    }
    setting_name = setting_line.split("=", maxsplit=1)[0].strip()
    settings[setting_name] = setting_line
    env_path.write_text(
        "\n".join(
            [
                settings["DATABASE_URL"],
                settings["SERVICENOW_INSTANCE_URL"],
                settings["SERVICENOW_CLIENT_ID"],
                settings["SERVICENOW_CLIENT_SECRET"],
                settings["JEDI_AUDIT_ROOT"],
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=expected_error) as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "secret" not in message
    assert "fallback" not in message
    assert "\t" not in message


def test_load_runtime_settings_rejects_non_string_database_url_without_value_leak(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class SecretBearingDatabaseUrl:
        def __str__(self) -> str:
            return "postgresql://jedi:client_secret=db-secret@localhost:5432/jedi"

    env_path = tmp_path / ".env"
    env_path.write_text("# patched loader\n", encoding="utf-8")
    monkeypatch.setattr(
        runtime_config,
        "load_dotenv_values",
        lambda _path: {
            "DATABASE_URL": cast(Any, SecretBearingDatabaseUrl()),
            "SERVICENOW_INSTANCE_URL": "https://dev205693.service-now.com",
            "SERVICENOW_CLIENT_ID": "client-id",
            "SERVICENOW_CLIENT_SECRET": "client-secret",
            "JEDI_AUDIT_ROOT": str(tmp_path),
        },
    )

    with pytest.raises(RuntimeConfigError) as exc:
        load_runtime_settings(env_path)

    diagnostic = str(exc.value)
    assert diagnostic == "DATABASE_URL must be a string runtime setting"
    assert "SecretBearingDatabaseUrl" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "db-secret" not in diagnostic


def test_load_runtime_settings_rejects_non_string_audit_root_without_value_leak(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class SecretBearingAuditRoot:
        def __fspath__(self) -> str:
            return "/tmp/client_secret=audit-secret"

        def __str__(self) -> str:
            return "/tmp/client_secret=audit-secret"

    env_path = tmp_path / ".env"
    env_path.write_text("# patched loader\n", encoding="utf-8")
    monkeypatch.setattr(
        runtime_config,
        "load_dotenv_values",
        lambda _path: {
            "DATABASE_URL": "postgresql://jedi:secret@localhost:5432/jedi",
            "SERVICENOW_INSTANCE_URL": "https://dev205693.service-now.com",
            "SERVICENOW_CLIENT_ID": "client-id",
            "SERVICENOW_CLIENT_SECRET": "client-secret",
            "JEDI_AUDIT_ROOT": cast(Any, SecretBearingAuditRoot()),
        },
    )

    with pytest.raises(RuntimeConfigError) as exc:
        load_runtime_settings(env_path)

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_AUDIT_ROOT must be a string runtime setting"
    assert "SecretBearingAuditRoot" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "audit-secret" not in diagnostic


@pytest.mark.parametrize(
    "worker_id_line",
    [
        'JEDI_WORKER_ID=" worker-1"',
        'JEDI_WORKER_ID="worker-1 "',
        'JEDI_WORKER_ID="worker-1\tfallback"',
    ],
)
def test_load_runtime_settings_rejects_malformed_worker_id(
    tmp_path: Path,
    worker_id_line: str,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                worker_id_line,
                f"JEDI_AUDIT_ROOT={tmp_path}",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_WORKER_ID") as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "empty, padded, or contain control characters" in message
    assert "fallback" not in message
    assert "\t" not in message


def test_load_runtime_settings_separates_pm_source_from_dev_target(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
                "SERVICENOW_PM_INSTANCE_URL=https://pm.service-now.com",
                "SERVICENOW_PM_CLIENT_ID=pm-client-id",
                "SERVICENOW_PM_CLIENT_SECRET=pm-client-secret",
                "SERVICENOW_DEV_INSTANCE_URL=https://dev.service-now.com",
                "SERVICENOW_DEV_CLIENT_ID=dev-client-id",
                "SERVICENOW_DEV_CLIENT_SECRET=dev-client-secret",
                f"JEDI_AUDIT_ROOT={tmp_path}",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_runtime_settings(env_path)

    assert settings.servicenow_pm_instance_url == "https://pm.service-now.com"
    assert settings.servicenow_pm_client_id == "pm-client-id"
    assert settings.servicenow_pm_client_secret == "pm-client-secret"
    assert settings.servicenow_dev_instance_url == "https://dev.service-now.com"
    assert settings.servicenow_dev_client_id == "dev-client-id"
    assert settings.servicenow_dev_client_secret == "dev-client-secret"
    assert settings.servicenow_instance_url == "https://dev.service-now.com"
    assert settings.servicenow_client_id == "dev-client-id"
    assert settings.servicenow_client_secret == "dev-client-secret"


@pytest.mark.parametrize(
    ("override_line", "expected_error"),
    [
        ('SERVICENOW_PM_INSTANCE_URL=" "', "SERVICENOW_PM_INSTANCE_URL"),
        ("SERVICENOW_DEV_INSTANCE_URL=", "SERVICENOW_DEV_INSTANCE_URL"),
        ('SERVICENOW_PM_CLIENT_ID=" "', "SERVICENOW_PM_CLIENT_ID"),
        ("SERVICENOW_DEV_CLIENT_SECRET=", "SERVICENOW_DEV_CLIENT_SECRET"),
    ],
)
def test_load_runtime_settings_rejects_blank_split_servicenow_overrides(
    tmp_path: Path,
    override_line: str,
    expected_error: str,
) -> None:
    env_path = tmp_path / ".env"
    split_lines = {
        "SERVICENOW_PM_INSTANCE_URL": "SERVICENOW_PM_INSTANCE_URL=https://pm.service-now.com",
        "SERVICENOW_DEV_INSTANCE_URL": "SERVICENOW_DEV_INSTANCE_URL=https://dev.service-now.com",
        "SERVICENOW_PM_CLIENT_ID": "SERVICENOW_PM_CLIENT_ID=pm-client-id",
        "SERVICENOW_PM_CLIENT_SECRET": "SERVICENOW_PM_CLIENT_SECRET=pm-client-secret",
        "SERVICENOW_DEV_CLIENT_ID": "SERVICENOW_DEV_CLIENT_ID=dev-client-id",
        "SERVICENOW_DEV_CLIENT_SECRET": ("SERVICENOW_DEV_CLIENT_SECRET=dev-client-secret"),
    }
    override_name = override_line.split("=", maxsplit=1)[0]
    split_lines[override_name] = override_line
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://legacy.service-now.com",
                "SERVICENOW_CLIENT_ID=legacy-client-id",
                "SERVICENOW_CLIENT_SECRET=legacy-client-secret",
                split_lines["SERVICENOW_PM_INSTANCE_URL"],
                split_lines["SERVICENOW_PM_CLIENT_ID"],
                split_lines["SERVICENOW_PM_CLIENT_SECRET"],
                split_lines["SERVICENOW_DEV_INSTANCE_URL"],
                split_lines["SERVICENOW_DEV_CLIENT_ID"],
                split_lines["SERVICENOW_DEV_CLIENT_SECRET"],
                f"JEDI_AUDIT_ROOT={tmp_path}",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=expected_error) as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "empty" in message
    assert "legacy" not in message
    assert "client-secret" not in message


@pytest.mark.parametrize(
    ("credential_line", "expected_error"),
    [
        ('SERVICENOW_PM_CLIENT_ID=" pm-client-id"', "SERVICENOW_PM_CLIENT_ID"),
        ('SERVICENOW_PM_CLIENT_SECRET="pm-client-secret "', "SERVICENOW_PM_CLIENT_SECRET"),
        (
            'SERVICENOW_DEV_CLIENT_ID="dev-client-id\tfallback"',
            "SERVICENOW_DEV_CLIENT_ID",
        ),
        (
            'SERVICENOW_DEV_CLIENT_SECRET="dev-client-secret\tfallback"',
            "SERVICENOW_DEV_CLIENT_SECRET",
        ),
    ],
)
def test_load_runtime_settings_rejects_malformed_split_servicenow_oauth_credentials(
    tmp_path: Path,
    credential_line: str,
    expected_error: str,
) -> None:
    env_path = tmp_path / ".env"
    credential_lines = {
        "SERVICENOW_PM_CLIENT_ID": "SERVICENOW_PM_CLIENT_ID=pm-client-id",
        "SERVICENOW_PM_CLIENT_SECRET": "SERVICENOW_PM_CLIENT_SECRET=pm-client-secret",
        "SERVICENOW_DEV_CLIENT_ID": "SERVICENOW_DEV_CLIENT_ID=dev-client-id",
        "SERVICENOW_DEV_CLIENT_SECRET": ("SERVICENOW_DEV_CLIENT_SECRET=dev-client-secret"),
    }
    credential_name = credential_line.split("=", maxsplit=1)[0]
    credential_lines[credential_name] = credential_line
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
                "SERVICENOW_PM_INSTANCE_URL=https://pm.service-now.com",
                credential_lines["SERVICENOW_PM_CLIENT_ID"],
                credential_lines["SERVICENOW_PM_CLIENT_SECRET"],
                "SERVICENOW_DEV_INSTANCE_URL=https://dev.service-now.com",
                credential_lines["SERVICENOW_DEV_CLIENT_ID"],
                credential_lines["SERVICENOW_DEV_CLIENT_SECRET"],
                f"JEDI_AUDIT_ROOT={tmp_path}",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=expected_error) as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "empty, padded, or contain control characters" in message
    assert "fallback" not in message
    assert "\t" not in message
    assert "client-secret" not in message
    assert "client-id" not in message


@pytest.mark.parametrize(
    ("url_line", "expected_error"),
    [
        ("SERVICENOW_PM_INSTANCE_URL=http://pm.service-now.com", "SERVICENOW_PM_INSTANCE_URL"),
        (
            "SERVICENOW_DEV_INSTANCE_URL=https://user:secret@dev.service-now.com",
            "SERVICENOW_DEV_INSTANCE_URL",
        ),
        (
            "SERVICENOW_PM_INSTANCE_URL=https://pm.service-now.com#fragment",
            "SERVICENOW_PM_INSTANCE_URL",
        ),
        (
            "SERVICENOW_DEV_INSTANCE_URL=https://dev.service-now.com/%0aheader",
            "SERVICENOW_DEV_INSTANCE_URL",
        ),
    ],
)
def test_load_runtime_settings_rejects_malformed_split_servicenow_instance_urls(
    tmp_path: Path,
    url_line: str,
    expected_error: str,
) -> None:
    env_path = tmp_path / ".env"
    url_lines = {
        "SERVICENOW_PM_INSTANCE_URL": "SERVICENOW_PM_INSTANCE_URL=https://pm.service-now.com",
        "SERVICENOW_DEV_INSTANCE_URL": "SERVICENOW_DEV_INSTANCE_URL=https://dev.service-now.com",
    }
    url_name = url_line.split("=", maxsplit=1)[0]
    url_lines[url_name] = url_line
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
                url_lines["SERVICENOW_PM_INSTANCE_URL"],
                "SERVICENOW_PM_CLIENT_ID=pm-client-id",
                "SERVICENOW_PM_CLIENT_SECRET=pm-client-secret",
                url_lines["SERVICENOW_DEV_INSTANCE_URL"],
                "SERVICENOW_DEV_CLIENT_ID=dev-client-id",
                "SERVICENOW_DEV_CLIENT_SECRET=dev-client-secret",
                f"JEDI_AUDIT_ROOT={tmp_path}",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=expected_error) as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "HTTPS ServiceNow instance URL" in message
    assert "secret" not in message
    assert "#fragment" not in message
    assert "%0a" not in message


def test_load_runtime_settings_defaults_classifier_gate_enabled(tmp_path: Path) -> None:
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

    assert settings.classifier_gate is True


@pytest.mark.parametrize(
    "setting_name",
    [
        "JEDI_BUILD_CLAIM_APPLY",
        "JEDI_STRICT_TRANSPORT_SECURITY_ENABLED",
        "JEDI_ALERT_WEBHOOK_ENABLED",
        "JEDI_UPDATE_SET_APPLY",
        "JEDI_CLASSIFIER_GATE",
    ],
)
def test_load_runtime_settings_rejects_malformed_runtime_boolean_values(
    tmp_path: Path,
    setting_name: str,
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
                f"{setting_name}=ture",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=setting_name):
        load_runtime_settings(env_path)


@pytest.mark.parametrize(
    ("setting_name", "env_line"),
    [
        ("JEDI_BUILD_CLAIM_APPLY", 'JEDI_BUILD_CLAIM_APPLY=" true"'),
        (
            "JEDI_STRICT_TRANSPORT_SECURITY_ENABLED",
            'JEDI_STRICT_TRANSPORT_SECURITY_ENABLED="false "',
        ),
        ("JEDI_ALERT_WEBHOOK_ENABLED", 'JEDI_ALERT_WEBHOOK_ENABLED="true\tfallback"'),
        ("JEDI_UPDATE_SET_APPLY", 'JEDI_UPDATE_SET_APPLY=" yes"'),
        ("JEDI_CLASSIFIER_GATE", 'JEDI_CLASSIFIER_GATE="off "'),
    ],
)
def test_load_runtime_settings_rejects_padded_runtime_boolean_values(
    tmp_path: Path,
    setting_name: str,
    env_line: str,
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
                env_line,
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=setting_name) as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "without padding or control characters" in message
    assert "fallback" not in message
    assert "\t" not in message


def test_load_runtime_settings_reads_public_web_worker_controls(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                f"JEDI_AUDIT_ROOT={tmp_path}",
                "JEDI_PUBLIC_WEB_ACCESS=worker",
                "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS=docs.servicenow.com,developer.servicenow.com",
                "JEDI_PUBLIC_WEB_DOC_URLS=https://docs.servicenow.com/ui-policy",
                "JEDI_PUBLIC_WEB_TIMEOUT_SECONDS=4",
                "JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES=4096",
                "JEDI_PUBLIC_WEB_MAX_EXCERPT_CHARS=1200",
                "JEDI_PUBLIC_WEB_MAX_RESULTS=2",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_runtime_settings(env_path)

    assert settings.public_web_access == "worker"
    assert settings.public_web_allowed_domains == [
        "docs.servicenow.com",
        "developer.servicenow.com",
    ]
    assert settings.public_web_doc_urls == ["https://docs.servicenow.com/ui-policy"]
    assert settings.public_web_timeout_seconds == 4.0
    assert settings.public_web_max_response_bytes == 4096
    assert settings.public_web_max_excerpt_chars == 1200
    assert settings.public_web_max_results == 2


def test_load_runtime_settings_rejects_non_positive_public_web_worker_limits(
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
                "JEDI_PUBLIC_WEB_ACCESS=worker",
                "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS=docs.servicenow.com",
                "JEDI_PUBLIC_WEB_DOC_URLS=https://docs.servicenow.com/ui-policy",
                "JEDI_PUBLIC_WEB_TIMEOUT_SECONDS=0",
                "JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES=0",
                "JEDI_PUBLIC_WEB_MAX_EXCERPT_CHARS=0",
                "JEDI_PUBLIC_WEB_MAX_RESULTS=0",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError) as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "JEDI_PUBLIC_WEB_TIMEOUT_SECONDS must be greater than 0" in message
    assert "JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES must be greater than 0" in message
    assert "JEDI_PUBLIC_WEB_MAX_EXCERPT_CHARS must be greater than 0" in message
    assert "JEDI_PUBLIC_WEB_MAX_RESULTS must be greater than 0" in message


def test_load_runtime_settings_rejects_malformed_public_web_worker_allowlist(
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
                "JEDI_PUBLIC_WEB_ACCESS=worker",
                "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS=docs.servicenow.com, developer.servicenow.com",
                "JEDI_PUBLIC_WEB_DOC_URLS=https://docs.servicenow.com/ui-policy",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_PUBLIC_WEB_ALLOWED_DOMAINS"):
        load_runtime_settings(env_path)


def test_load_runtime_settings_rejects_public_web_worker_docs_outside_allowlist(
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
                "JEDI_PUBLIC_WEB_ACCESS=worker",
                "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS=docs.servicenow.com",
                "JEDI_PUBLIC_WEB_DOC_URLS=https://example.com/leak",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_PUBLIC_WEB_DOC_URLS"):
        load_runtime_settings(env_path)


def test_load_runtime_settings_rejects_public_web_worker_doc_url_secrets_without_echo(
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
                "JEDI_PUBLIC_WEB_ACCESS=worker",
                "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS=docs.servicenow.com",
                (
                    "JEDI_PUBLIC_WEB_DOC_URLS="
                    "https://doc-user:doc-secret@docs.servicenow.com/ui-policy"
                    "?client_secret=query-secret"
                ),
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_PUBLIC_WEB_DOC_URLS") as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "doc-secret" not in message
    assert "query-secret" not in message
    assert "client_secret" not in message


@pytest.mark.parametrize(
    ("setting_lines", "expected_error"),
    [
        (
            ["JEDI_PUBLIC_WEB_ALLOWED_DOMAINS=docs.servicenow.com, localhost"],
            "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS",
        ),
        (
            [
                "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS=docs.servicenow.com",
                "JEDI_PUBLIC_WEB_DOC_URLS=https://doc-user:doc-secret@docs.servicenow.com"
                "/api?client_secret=query-secret",
            ],
            "JEDI_PUBLIC_WEB_DOC_URLS",
        ),
        (
            [
                "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS=docs.servicenow.com",
                "JEDI_PUBLIC_WEB_DOC_URLS=https://example.com/leak",
            ],
            "JEDI_PUBLIC_WEB_DOC_URLS",
        ),
    ],
)
def test_load_runtime_settings_rejects_dormant_unsafe_public_web_config(
    tmp_path: Path,
    setting_lines: list[str],
    expected_error: str,
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
                *setting_lines,
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=expected_error) as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "doc-secret" not in message
    assert "query-secret" not in message
    assert "client_secret" not in message


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


@pytest.mark.parametrize(
    ("state_line", "expected_error"),
    [
        ('JEDI_BUILD_CLAIM_FROM_STATE=" 1"', "JEDI_BUILD_CLAIM_FROM_STATE"),
        ('JEDI_BUILD_CLAIM_FROM_STATE="1 "', "JEDI_BUILD_CLAIM_FROM_STATE"),
        ('JEDI_BUILD_CLAIM_STATE="2\tfallback"', "JEDI_BUILD_CLAIM_STATE"),
    ],
)
def test_load_runtime_settings_rejects_malformed_build_claim_state_values(
    tmp_path: Path,
    state_line: str,
    expected_error: str,
) -> None:
    env_path = tmp_path / ".env"
    from_state = "JEDI_BUILD_CLAIM_FROM_STATE=1"
    claim_state = "JEDI_BUILD_CLAIM_STATE=2"
    if state_line.startswith("JEDI_BUILD_CLAIM_FROM_STATE="):
        from_state = state_line
    else:
        claim_state = state_line
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                f"JEDI_AUDIT_ROOT={tmp_path}",
                from_state,
                claim_state,
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=expected_error) as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "empty, padded, or contain control characters" in message
    assert "fallback" not in message
    assert "\t" not in message


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


@pytest.mark.parametrize(
    "token_line",
    [
        'JEDI_ADMIN_API_TOKEN=" admin-token"',
        'JEDI_ADMIN_API_TOKEN="admin-token "',
        'JEDI_ADMIN_API_TOKEN="admin-token\tfallback"',
    ],
)
def test_load_runtime_settings_rejects_malformed_admin_api_token(
    tmp_path: Path,
    token_line: str,
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
                token_line,
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_ADMIN_API_TOKEN") as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "empty, padded, or contain control characters" in message
    assert "fallback" not in message
    assert "\t" not in message
    assert "admin-token" not in message


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


@pytest.mark.parametrize(
    ("credential_line", "expected_error"),
    [
        (
            'JEDI_ADMIN_CONSOLE_USERNAME=" console-admin"',
            "JEDI_ADMIN_CONSOLE_USERNAME",
        ),
        (
            'JEDI_ADMIN_CONSOLE_USERNAME="console-admin "',
            "JEDI_ADMIN_CONSOLE_USERNAME",
        ),
        (
            'JEDI_ADMIN_CONSOLE_PASSWORD="console-password\tfallback"',
            "JEDI_ADMIN_CONSOLE_PASSWORD",
        ),
    ],
)
def test_load_runtime_settings_rejects_malformed_admin_console_credentials(
    tmp_path: Path,
    credential_line: str,
    expected_error: str,
) -> None:
    env_path = tmp_path / ".env"
    username_line = "JEDI_ADMIN_CONSOLE_USERNAME=console-admin"
    password_line = "JEDI_ADMIN_CONSOLE_PASSWORD=console-password"
    if credential_line.startswith("JEDI_ADMIN_CONSOLE_USERNAME="):
        username_line = credential_line
    else:
        password_line = credential_line
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
                username_line,
                password_line,
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=expected_error) as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "empty, padded, or contain control characters" in message
    assert "fallback" not in message
    assert "\t" not in message


@pytest.mark.parametrize(
    ("credential_name", "expected_error"),
    [
        ("JEDI_ADMIN_CONSOLE_USERNAME", "JEDI_ADMIN_CONSOLE_USERNAME"),
        ("JEDI_ADMIN_CONSOLE_PASSWORD", "JEDI_ADMIN_CONSOLE_PASSWORD"),
    ],
)
def test_load_runtime_settings_rejects_oversized_admin_console_credentials(
    tmp_path: Path,
    credential_name: str,
    expected_error: str,
) -> None:
    username_line = "JEDI_ADMIN_CONSOLE_USERNAME=console-admin"
    password_line = "JEDI_ADMIN_CONSOLE_PASSWORD=console-password"
    oversized_credential = "x" * 8193
    if credential_name == "JEDI_ADMIN_CONSOLE_USERNAME":
        username_line = f"JEDI_ADMIN_CONSOLE_USERNAME={oversized_credential}"
    else:
        password_line = f"JEDI_ADMIN_CONSOLE_PASSWORD={oversized_credential}"
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
                username_line,
                password_line,
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=expected_error) as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "must be at most 8192 bytes" in message
    assert oversized_credential not in message


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


@pytest.mark.parametrize(
    ("setting_name", "invalid_value"),
    [
        ("JEDI_ADMIN_AUTH_MODE", "oauth2"),
        ("JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE", "token"),
        ("JEDI_PUBLIC_WEB_ACCESS", "internet"),
    ],
)
def test_load_runtime_settings_rejects_malformed_runtime_enum_values(
    tmp_path: Path,
    setting_name: str,
    invalid_value: str,
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
                f"{setting_name}={invalid_value}",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=setting_name) as exc:
        load_runtime_settings(env_path)

    assert "must be one of" in str(exc.value)


@pytest.mark.parametrize(
    ("setting_name", "malformed_line"),
    [
        ("JEDI_ADMIN_AUTH_MODE", 'JEDI_ADMIN_AUTH_MODE=" dev_basic"'),
        ("JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE", 'JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE="hmac_sha256 "'),
        ("JEDI_PUBLIC_WEB_ACCESS", 'JEDI_PUBLIC_WEB_ACCESS="worker\tfallback"'),
    ],
)
def test_load_runtime_settings_rejects_runtime_enum_boundary_whitespace(
    tmp_path: Path,
    setting_name: str,
    malformed_line: str,
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
                malformed_line,
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=setting_name) as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "whitespace or control characters" in message
    assert "fallback" not in message
    assert "\t" not in message


def test_load_runtime_settings_rejects_malformed_runtime_environment(
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
                "JEDI_ENVIRONMENT=prod",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_ENVIRONMENT") as exc:
        load_runtime_settings(env_path)

    assert "must be one of" in str(exc.value)


@pytest.mark.parametrize(
    "environment_line",
    [
        'JEDI_ENVIRONMENT=" production"',
        'JEDI_ENVIRONMENT="production "',
        'JEDI_ENVIRONMENT="production\tfallback"',
    ],
)
def test_load_runtime_settings_rejects_runtime_environment_whitespace(
    tmp_path: Path,
    environment_line: str,
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
                environment_line,
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_ENVIRONMENT") as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "whitespace or control characters" in message
    assert "fallback" not in message
    assert "\t" not in message


def test_load_runtime_settings_normalizes_runtime_environment_case(
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
                "JEDI_ENVIRONMENT=Production",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_runtime_settings(env_path)

    assert settings.runtime_environment == "production"


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
                "JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET=previous-webhook-secret",
                "JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS=120",
                "JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES=4096",
                "JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS=5",
                "JEDI_LIFECYCLE_RATE_LIMIT_WINDOW_SECONDS=30",
                "JEDI_LIFECYCLE_RATE_LIMIT_MAX_BUCKETS=11",
                "JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS=7",
                "JEDI_ADMIN_RATE_LIMIT_WINDOW_SECONDS=45",
                "JEDI_ADMIN_RATE_LIMIT_MAX_BUCKETS=13",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_runtime_settings(env_path)

    assert settings.lifecycle_webhook_auth_mode == "hmac_sha256"
    assert settings.lifecycle_webhook_secret == "webhook-secret"
    assert settings.lifecycle_webhook_previous_secret == "previous-webhook-secret"
    assert settings.lifecycle_webhook_max_skew_seconds == 120
    assert settings.lifecycle_webhook_max_body_bytes == 4096
    assert settings.lifecycle_rate_limit_max_requests == 5
    assert settings.lifecycle_rate_limit_window_seconds == 30
    assert settings.lifecycle_rate_limit_max_buckets == 11
    assert settings.admin_rate_limit_max_requests == 7
    assert settings.admin_rate_limit_window_seconds == 45
    assert settings.admin_rate_limit_max_buckets == 13


@pytest.mark.parametrize(
    "secret_line",
    [
        'JEDI_LIFECYCLE_WEBHOOK_SECRET=" webhook-secret"',
        'JEDI_LIFECYCLE_WEBHOOK_SECRET="webhook-secret "',
        'JEDI_LIFECYCLE_WEBHOOK_SECRET="webhook-secret\tfallback"',
    ],
)
def test_load_runtime_settings_rejects_malformed_lifecycle_webhook_secret(
    tmp_path: Path,
    secret_line: str,
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
                "JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE=hmac_sha256",
                secret_line,
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_LIFECYCLE_WEBHOOK_SECRET") as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "empty, padded, or contain control characters" in message
    assert "fallback" not in message
    assert "\t" not in message
    assert "webhook-secret" not in message


@pytest.mark.parametrize(
    "secret_line",
    [
        'JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET=" previous-secret"',
        'JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET="previous-secret "',
        'JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET="previous-secret\tfallback"',
    ],
)
def test_load_runtime_settings_rejects_malformed_lifecycle_webhook_previous_secret(
    tmp_path: Path,
    secret_line: str,
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
                "JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE=hmac_sha256",
                "JEDI_LIFECYCLE_WEBHOOK_SECRET=webhook-secret",
                secret_line,
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeConfigError,
        match="JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET",
    ) as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "empty, padded, or contain control characters" in message
    assert "fallback" not in message
    assert "\t" not in message
    assert "previous-secret" not in message


@pytest.mark.parametrize(
    "setting_name",
    [
        "JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS",
        "JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES",
        "JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS",
        "JEDI_LIFECYCLE_RATE_LIMIT_WINDOW_SECONDS",
        "JEDI_LIFECYCLE_RATE_LIMIT_MAX_BUCKETS",
        "JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS",
        "JEDI_ADMIN_RATE_LIMIT_WINDOW_SECONDS",
        "JEDI_ADMIN_RATE_LIMIT_MAX_BUCKETS",
        "JEDI_ADMIN_MAX_BODY_BYTES",
        "JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS",
        "JEDI_RUNNING_JOB_STALE_AFTER_SECONDS",
        "JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES",
        "JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES",
        "JEDI_PUBLIC_WEB_MAX_EXCERPT_CHARS",
        "JEDI_PUBLIC_WEB_MAX_RESULTS",
    ],
)
def test_load_runtime_settings_rejects_malformed_runtime_integer_values(
    tmp_path: Path,
    setting_name: str,
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
                f"{setting_name}=ten",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=setting_name) as exc:
        load_runtime_settings(env_path)

    assert "must be an integer" in str(exc.value)


@pytest.mark.parametrize(
    ("setting_name", "env_line"),
    [
        ("JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS", 'JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS=" 120"'),
        (
            "JEDI_ADMIN_RATE_LIMIT_MAX_BUCKETS",
            'JEDI_ADMIN_RATE_LIMIT_MAX_BUCKETS=" 10000"',
        ),
        (
            "JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES",
            'JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES="65536 "',
        ),
        (
            "JEDI_PUBLIC_WEB_MAX_RESULTS",
            'JEDI_PUBLIC_WEB_MAX_RESULTS="3\tfallback"',
        ),
    ],
)
def test_load_runtime_settings_rejects_padded_runtime_integer_values(
    tmp_path: Path,
    setting_name: str,
    env_line: str,
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
                env_line,
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=setting_name) as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "must be an integer without padding or control characters" in message
    assert "fallback" not in message
    assert "\t" not in message


@pytest.mark.parametrize(
    ("setting_name", "env_line"),
    [
        (
            "JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS",
            "JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS=+60",
        ),
        (
            "JEDI_LIFECYCLE_RATE_LIMIT_MAX_BUCKETS",
            "JEDI_LIFECYCLE_RATE_LIMIT_MAX_BUCKETS=10_000",
        ),
        (
            "JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES",
            "JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES=128_000",
        ),
    ],
)
def test_load_runtime_settings_rejects_non_decimal_runtime_integer_values(
    tmp_path: Path,
    setting_name: str,
    env_line: str,
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
                env_line,
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=setting_name) as exc:
        load_runtime_settings(env_path)

    assert "base-10 digits only" in str(exc.value)


@pytest.mark.parametrize(
    "setting_name",
    [
        "JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS",
        "JEDI_PUBLIC_WEB_TIMEOUT_SECONDS",
    ],
)
def test_load_runtime_settings_rejects_malformed_runtime_float_values(
    tmp_path: Path,
    setting_name: str,
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
                f"{setting_name}=fast",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=setting_name) as exc:
        load_runtime_settings(env_path)

    assert "must be a number" in str(exc.value)


@pytest.mark.parametrize(
    ("setting_name", "env_line"),
    [
        (
            "JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS",
            'JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS=" 2.5"',
        ),
        (
            "JEDI_PUBLIC_WEB_TIMEOUT_SECONDS",
            'JEDI_PUBLIC_WEB_TIMEOUT_SECONDS="3.0\tfallback"',
        ),
    ],
)
def test_load_runtime_settings_rejects_padded_runtime_float_values(
    tmp_path: Path,
    setting_name: str,
    env_line: str,
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
                env_line,
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=setting_name) as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "must be a number without padding or control characters" in message
    assert "fallback" not in message
    assert "\t" not in message


@pytest.mark.parametrize(
    ("setting_name", "invalid_value"),
    [
        ("JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS", "nan"),
        ("JEDI_PUBLIC_WEB_TIMEOUT_SECONDS", "inf"),
    ],
)
def test_load_runtime_settings_rejects_non_finite_runtime_float_values(
    tmp_path: Path,
    setting_name: str,
    invalid_value: str,
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
                f"{setting_name}={invalid_value}",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=setting_name) as exc:
        load_runtime_settings(env_path)

    assert "must be a finite number" in str(exc.value)


@pytest.mark.parametrize(
    ("setting_name", "invalid_value"),
    [
        ("JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS", "1_000.5"),
        ("JEDI_PUBLIC_WEB_TIMEOUT_SECONDS", "１２.5"),
        ("JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS", "1e3"),
        ("JEDI_PUBLIC_WEB_TIMEOUT_SECONDS", "+2.5"),
    ],
)
def test_load_runtime_settings_rejects_non_ascii_fixed_decimal_float_values(
    tmp_path: Path,
    setting_name: str,
    invalid_value: str,
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
                f"{setting_name}={invalid_value}",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=setting_name) as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "ASCII decimal number" in message
    assert invalid_value not in message


def test_load_runtime_settings_reads_strict_transport_security_config(
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
                "JEDI_STRICT_TRANSPORT_SECURITY_ENABLED=true",
                "JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS=63072000",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_runtime_settings(env_path)

    assert settings.strict_transport_security_enabled is True
    assert settings.strict_transport_security_max_age_seconds == 63072000


def test_load_runtime_settings_reads_alert_webhook_config(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                f"JEDI_AUDIT_ROOT={tmp_path}",
                "JEDI_ALERT_WEBHOOK_ENABLED=true",
                "JEDI_ALERT_WEBHOOK_URL=https://alerts.example.gov/jedi",
                "JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS=2.5",
                "JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES=4096",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_runtime_settings(env_path)

    assert settings.alert_webhook_enabled is True
    assert settings.alert_webhook_url == "https://alerts.example.gov/jedi"
    assert settings.alert_webhook_timeout_seconds == 2.5
    assert settings.alert_webhook_max_body_bytes == 4096


@pytest.mark.parametrize(
    "webhook_url_line, expected_message",
    [
        (
            'JEDI_ALERT_WEBHOOK_URL=" https://alerts.example.gov/jedi"',
            "must not be empty, padded, or contain control characters",
        ),
        (
            'JEDI_ALERT_WEBHOOK_URL="https://alerts.example.gov/jedi "',
            "must not be empty, padded, or contain control characters",
        ),
        (
            'JEDI_ALERT_WEBHOOK_URL="https://alerts.example.gov/jedi\tfallback"',
            "must not be empty, padded, or contain control characters",
        ),
        (
            "JEDI_ALERT_WEBHOOK_URL=http://alerts.example.gov/jedi",
            "must use HTTPS",
        ),
        (
            "JEDI_ALERT_WEBHOOK_URL=https://alert-user:alert-secret@alerts.example.gov/jedi",
            "must not include credentials",
        ),
    ],
)
def test_load_runtime_settings_rejects_malformed_alert_webhook_url(
    tmp_path: Path,
    webhook_url_line: str,
    expected_message: str,
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
                webhook_url_line,
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_ALERT_WEBHOOK_URL") as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert expected_message in message
    assert "fallback" not in message
    assert "\t" not in message
    assert "alert-secret" not in message


def test_load_runtime_settings_reads_running_job_stale_threshold(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                f"JEDI_AUDIT_ROOT={tmp_path}",
                "JEDI_RUNNING_JOB_STALE_AFTER_SECONDS=900",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_runtime_settings(env_path)

    assert settings.running_job_stale_after_seconds == 900


def test_load_runtime_settings_reads_trusted_hosts(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                f"JEDI_AUDIT_ROOT={tmp_path}",
                "JEDI_TRUSTED_HOSTS=api.example.gov,*.apps.example.gov",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_runtime_settings(env_path)

    assert settings.trusted_hosts == ["api.example.gov", "*.apps.example.gov"]


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


def test_validate_runtime_settings_rejects_production_api_without_trusted_hosts(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": "api",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "trusted_hosts": [],
            "admin_api_token": "y" * 32,
            "strict_transport_security_enabled": True,
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_TRUSTED_HOSTS") as exc:
        validate_runtime_settings(settings)

    assert "required for public production runtime roles" in str(exc.value)


@pytest.mark.parametrize(
    "trusted_hosts",
    [
        ["*"],
        [" api.example.gov"],
        ["api.example.gov "],
        ["api.example.gov/admin"],
        ["https://api.example.gov"],
        ["api.example.gov\nfallback"],
        ["api.example.gov:bad-port"],
        [".example.gov"],
        ["*.localhost"],
    ],
)
def test_validate_runtime_settings_rejects_malformed_production_trusted_hosts(
    tmp_path: Path,
    trusted_hosts: list[str],
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": "api",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "trusted_hosts": trusted_hosts,
            "admin_api_token": "y" * 32,
            "strict_transport_security_enabled": True,
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_TRUSTED_HOSTS") as exc:
        validate_runtime_settings(settings)

    message = str(exc.value)
    assert "must contain hostnames or wildcard subdomains" in message
    assert "fallback" not in message


def test_validate_runtime_settings_rejects_duplicate_lifecycle_webhook_rotation_secret(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": "api",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "lifecycle_webhook_previous_secret": "x" * 32,
            "admin_api_token": "y" * 32,
            "strict_transport_security_enabled": True,
        }
    )

    with pytest.raises(
        RuntimeConfigError,
        match="JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET",
    ) as exc:
        validate_runtime_settings(settings)

    assert "must differ from JEDI_LIFECYCLE_WEBHOOK_SECRET" in str(exc.value)


def test_validate_runtime_settings_rejects_weak_lifecycle_webhook_previous_secret(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": "api",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "lifecycle_webhook_previous_secret": "short",
            "admin_api_token": "y" * 32,
            "strict_transport_security_enabled": True,
        }
    )

    with pytest.raises(
        RuntimeConfigError,
        match="JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET",
    ) as exc:
        validate_runtime_settings(settings)

    assert "at least 32 characters" in str(exc.value)


def test_validate_runtime_settings_rejects_production_without_admin_api_token_or_auth(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": "api",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "strict_transport_security_enabled": True,
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_ADMIN_API_TOKEN"):
        validate_runtime_settings(settings)


def test_validate_runtime_settings_allows_production_api_with_admin_console_disabled_and_token(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": "api",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "strict_transport_security_enabled": True,
            "admin_auth_mode": "disabled",
            "admin_api_token": "y" * 32,
        }
    )

    validate_runtime_settings(settings)


@pytest.mark.parametrize("runtime_role", ["api", "combined"])
def test_validate_runtime_settings_rejects_admin_console_credentials_on_public_production_roles(
    tmp_path: Path,
    runtime_role: str,
) -> None:
    settings_base = (
        _settings(tmp_path) if runtime_role == "api" else _settings_with_openai(tmp_path)
    )
    settings = settings_base.model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": runtime_role,
            "allow_combined_production": runtime_role == "combined",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "strict_transport_security_enabled": True,
            "admin_auth_mode": "disabled",
            "admin_api_token": "y" * 32,
            "admin_console_username": "console-admin",
            "admin_console_password": "console-password",
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings)

    message = str(exc.value)
    assert "JEDI_ADMIN_CONSOLE_USERNAME is development-only in production" in message
    assert "JEDI_ADMIN_CONSOLE_PASSWORD is development-only in production" in message


def test_validate_runtime_settings_rejects_admin_console_password_string_subclass_without_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingAdminConsolePassword(str):
        def __str__(self) -> str:
            return "client_secret=direct-admin-console-password-secret"

    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": "api",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "strict_transport_security_enabled": True,
            "admin_auth_mode": "disabled",
            "admin_api_token": "y" * 32,
            "admin_console_password": SecretBearingAdminConsolePassword(
                "console-password"
            ),
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings)

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_ADMIN_CONSOLE_PASSWORD must be a string runtime setting"
    assert "SecretBearingAdminConsolePassword" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-admin-console-password-secret" not in diagnostic


def test_runtime_role_helpers_do_not_read_raw_settings_for_normalized_fields() -> None:
    api_source = inspect.getsource(runtime_config._api_runtime_role_errors)
    worker_source = inspect.getsource(runtime_config._worker_runtime_role_errors)

    for raw_read in (
        "settings.model_provider",
        "settings.openai_api_key",
        "settings.openai_model",
    ):
        assert raw_read not in api_source

    for raw_read in (
        "settings.lifecycle_webhook_auth_mode",
        "settings.lifecycle_webhook_secret",
        "settings.admin_api_token",
        "settings.admin_auth_mode",
        "settings.admin_console_username",
        "settings.admin_console_password",
    ):
        assert raw_read not in worker_source


def test_validate_runtime_settings_rejects_non_postgres_production_database_url(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "database_url": "sqlite:///tmp/jedi.db",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
        }
    )

    with pytest.raises(RuntimeConfigError, match="DATABASE_URL"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_malformed_runtime_environment_without_skipping(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={"runtime_environment": "production\nfallback"}
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    message = str(exc.value)
    assert "JEDI_ENVIRONMENT" in message
    assert "whitespace or control characters" in message
    assert "fallback" not in message
    assert "\n" not in message


def test_validate_runtime_settings_rejects_runtime_environment_string_subclass_without_method_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingRuntimeEnvironment(str):
        def strip(self, chars: str | None = None) -> str:
            raise RuntimeError("client_secret=direct-runtime-env-secret")

    settings = _settings(tmp_path).model_copy(
        update={"runtime_environment": SecretBearingRuntimeEnvironment("production")}
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_ENVIRONMENT must be a string runtime setting"
    assert "SecretBearingRuntimeEnvironment" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-runtime-env-secret" not in diagnostic


def test_validate_runtime_settings_rejects_runtime_role_non_string_without_str_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingRuntimeRole:
        def __str__(self) -> str:
            raise RuntimeError("client_secret=direct-runtime-role-secret")

    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": cast(Any, SecretBearingRuntimeRole()),
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "admin_auth_mode": "oidc",
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_RUNTIME_ROLE must be a string runtime setting"
    assert "SecretBearingRuntimeRole" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-runtime-role-secret" not in diagnostic


def test_validate_runtime_settings_rejects_production_database_url_fragments(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "database_url": "postgresql://jedi:secret@db.example.invalid:5432/jedi#fragment",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
        }
    )

    with pytest.raises(RuntimeConfigError, match="DATABASE_URL"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_database_url_string_subclass_without_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingDatabaseUrl(str):
        def decode(self, *_args: object, **_kwargs: object) -> str:
            raise RuntimeError("client_secret=direct-database-url-secret")

        def __str__(self) -> str:
            return "postgresql://jedi:client_secret=direct-database-url-secret@db/jedi"

    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "database_url": SecretBearingDatabaseUrl(
                "postgresql://jedi:secret@db.example.invalid:5432/jedi"
            ),
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    diagnostic = str(exc.value)
    assert diagnostic == "DATABASE_URL must be a string runtime setting"
    assert "SecretBearingDatabaseUrl" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-database-url-secret" not in diagnostic


def test_validate_runtime_settings_rejects_disabled_classifier_gate_in_production(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "classifier_gate": False,
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_CLASSIFIER_GATE"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_boolean_setting_object_without_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingClassifierGate:
        def __bool__(self) -> bool:
            raise RuntimeError("client_secret=direct-classifier-gate-secret")

    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "classifier_gate": SecretBearingClassifierGate(),
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_CLASSIFIER_GATE must be a boolean runtime setting"
    assert "SecretBearingClassifierGate" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-classifier-gate-secret" not in diagnostic


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


def test_validate_runtime_settings_rejects_non_positive_stale_threshold(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "model_provider": "openai",
            "openai_api_key": "openai-key",
            "openai_model": "gpt-5",
            "running_job_stale_after_seconds": 0,
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_RUNNING_JOB_STALE_AFTER_SECONDS"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_excessive_production_stale_threshold(
    tmp_path: Path,
) -> None:
    excessive_stale_threshold = 7 * 24 * 60 * 60
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": "worker",
            "running_job_stale_after_seconds": excessive_stale_threshold,
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    message = str(exc.value)
    assert "JEDI_RUNNING_JOB_STALE_AFTER_SECONDS must be at most 86400" in message
    assert str(excessive_stale_threshold) not in message


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


def test_load_runtime_settings_reads_runtime_role(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:jedi@postgres:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                f"JEDI_AUDIT_ROOT={tmp_path}",
                "JEDI_RUNTIME_ROLE=worker",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_runtime_settings(env_path)

    assert settings.runtime_role == "worker"


def test_validate_runtime_settings_api_role_does_not_require_model_provider(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": "api",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "strict_transport_security_enabled": True,
        }
    )

    validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_combined_role_in_production_without_explicit_opt_in(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": "combined",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "strict_transport_security_enabled": True,
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_ALLOW_COMBINED_PRODUCTION=true"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_allows_combined_role_in_production_with_explicit_opt_in(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": "combined",
            "allow_combined_production": True,
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "strict_transport_security_enabled": True,
        }
    )

    validate_runtime_settings(settings, require_admin_auth=False)


@pytest.mark.parametrize("runtime_role", ["api", "worker"])
def test_validate_runtime_settings_rejects_combined_production_opt_in_on_split_roles(
    tmp_path: Path,
    runtime_role: str,
) -> None:
    settings_base = (
        _settings(tmp_path) if runtime_role == "api" else _settings_with_openai(tmp_path)
    )
    settings = settings_base.model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": runtime_role,
            "allow_combined_production": True,
            "lifecycle_webhook_auth_mode": "hmac_sha256" if runtime_role == "api" else "disabled",
            "lifecycle_webhook_secret": "x" * 32 if runtime_role == "api" else None,
            "strict_transport_security_enabled": runtime_role == "api",
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_ALLOW_COMBINED_PRODUCTION"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_build_claim_apply_on_api_role(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": "api",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "strict_transport_security_enabled": True,
            "build_claim_apply": True,
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_BUILD_CLAIM_APPLY=true"):
        validate_runtime_settings(settings, require_admin_auth=False)


@pytest.mark.parametrize("runtime_role", ["api", "combined"])
def test_validate_runtime_settings_requires_hsts_on_public_production_roles(
    tmp_path: Path,
    runtime_role: str,
) -> None:
    settings_base = (
        _settings(tmp_path) if runtime_role == "api" else _settings_with_openai(tmp_path)
    )
    settings = settings_base.model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": runtime_role,
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_STRICT_TRANSPORT_SECURITY_ENABLED"):
        validate_runtime_settings(settings, require_admin_auth=False)


@pytest.mark.parametrize("runtime_role", ["api", "combined"])
def test_validate_runtime_settings_rejects_short_hsts_max_age_on_public_production_roles(
    tmp_path: Path,
    runtime_role: str,
) -> None:
    settings_base = (
        _settings(tmp_path) if runtime_role == "api" else _settings_with_openai(tmp_path)
    )
    settings = settings_base.model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": runtime_role,
            "allow_combined_production": runtime_role == "combined",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "strict_transport_security_enabled": True,
            "strict_transport_security_max_age_seconds": 300,
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_worker_secrets_on_api_role(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": "api",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "strict_transport_security_enabled": True,
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    message = str(exc.value)
    assert "JEDI_MODEL_PROVIDER is worker-only when JEDI_RUNTIME_ROLE=api" in message
    assert "OPENAI_API_KEY is worker-only when JEDI_RUNTIME_ROLE=api" in message


def test_validate_runtime_settings_worker_role_does_not_require_api_secrets(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": "worker",
            "trusted_hosts": [],
        }
    )

    validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_api_secrets_on_worker_role(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": "worker",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "lifecycle_webhook_previous_secret": "z" * 32,
            "trusted_hosts": ["api.example.gov"],
            "admin_api_token": "y" * 32,
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    message = str(exc.value)
    assert "JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE is api-only when JEDI_RUNTIME_ROLE=worker" in message
    assert "JEDI_LIFECYCLE_WEBHOOK_SECRET is api-only when JEDI_RUNTIME_ROLE=worker" in message
    assert (
        "JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET is api-only "
        "when JEDI_RUNTIME_ROLE=worker"
    ) in message
    assert "JEDI_TRUSTED_HOSTS is api-only when JEDI_RUNTIME_ROLE=worker" in message
    assert "JEDI_ADMIN_API_TOKEN is api-only when JEDI_RUNTIME_ROLE=worker" in message


def test_validate_runtime_settings_rejects_malformed_model_provider_without_echoing_value(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "admin_auth_mode": "oidc",
            "model_provider": "openai\nfallback",
            "openai_api_key": "sk-" + ("x" * 64),
            "openai_model": "gpt-4.1",
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    message = str(exc.value)
    assert "JEDI_MODEL_PROVIDER" in message
    assert "whitespace or control characters" in message
    assert "fallback" not in message
    assert "\n" not in message


def test_validate_runtime_settings_rejects_malformed_admin_auth_mode_without_echoing_value(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "admin_auth_mode": "oidc\nfallback",
            "model_provider": "openai",
            "openai_api_key": "sk-" + ("x" * 64),
            "openai_model": "gpt-4.1",
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=True)

    message = str(exc.value)
    assert "JEDI_ADMIN_AUTH_MODE" in message
    assert "whitespace or control characters" in message
    assert "fallback" not in message
    assert "\n" not in message


def test_validate_runtime_settings_rejects_lifecycle_auth_mode_string_subclass_without_eq_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingLifecycleAuthMode(str):
        def __ne__(self, _other: object) -> bool:
            raise RuntimeError("client_secret=direct-lifecycle-auth-mode-secret")

    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "allow_combined_production": True,
            "lifecycle_webhook_auth_mode": SecretBearingLifecycleAuthMode(
                "hmac_sha256"
            ),
            "lifecycle_webhook_secret": "x" * 32,
            "admin_auth_mode": "oidc",
            "strict_transport_security_enabled": True,
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE must be a string runtime setting"
    assert "SecretBearingLifecycleAuthMode" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-lifecycle-auth-mode-secret" not in diagnostic


def test_validate_runtime_settings_rejects_admin_auth_mode_non_string_without_str_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingAdminAuthMode:
        def __str__(self) -> str:
            raise RuntimeError("client_secret=direct-admin-auth-mode-secret")

    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "admin_auth_mode": cast(Any, SecretBearingAdminAuthMode()),
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=True)

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_ADMIN_AUTH_MODE must be a string runtime setting"
    assert "SecretBearingAdminAuthMode" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-admin-auth-mode-secret" not in diagnostic


def test_validate_runtime_settings_rejects_oversized_model_provider_without_echoing_value(
    tmp_path: Path,
) -> None:
    oversized_provider = "x" * 257
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "admin_auth_mode": "oidc",
            "model_provider": oversized_provider,
            "openai_api_key": "sk-" + ("x" * 64),
            "openai_model": "gpt-4.1",
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    message = str(exc.value)
    assert "JEDI_MODEL_PROVIDER" in message
    assert "<= 256 characters" in message
    assert oversized_provider not in message


def test_validate_runtime_settings_rejects_unsupported_model_provider_without_echoing_value(
    tmp_path: Path,
) -> None:
    unsupported_provider = "unapproved-provider"
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "admin_auth_mode": "oidc",
            "model_provider": unsupported_provider,
            "openai_api_key": "sk-" + ("x" * 64),
            "openai_model": "gpt-4.1",
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    message = str(exc.value)
    assert "Unsupported JEDI_MODEL_PROVIDER" in message
    assert unsupported_provider not in message


def test_validate_runtime_settings_rejects_model_provider_string_subclass_without_len_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingModelProvider(str):
        def __len__(self) -> int:
            raise RuntimeError("client_secret=direct-model-provider-secret")

    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "allow_combined_production": True,
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "admin_auth_mode": "oidc",
            "strict_transport_security_enabled": True,
            "model_provider": SecretBearingModelProvider("openai"),
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_MODEL_PROVIDER must be a string runtime setting"
    assert "SecretBearingModelProvider" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-model-provider-secret" not in diagnostic


def test_validate_runtime_settings_rejects_openai_api_key_string_subclass_without_truthiness_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingOpenAIKey(str):
        def __len__(self) -> int:
            raise RuntimeError("client_secret=direct-openai-key-secret")

    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "allow_combined_production": True,
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "admin_auth_mode": "oidc",
            "strict_transport_security_enabled": True,
            "openai_api_key": SecretBearingOpenAIKey("sk-" + ("x" * 64)),
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    diagnostic = str(exc.value)
    assert diagnostic == "OPENAI_API_KEY must be a string runtime setting"
    assert "SecretBearingOpenAIKey" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-openai-key-secret" not in diagnostic


def test_validate_runtime_settings_rejects_openai_api_key_control_characters(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "admin_auth_mode": "oidc",
            "model_provider": "openai",
            "openai_api_key": ("sk-" + ("x" * 32) + "\n" + ("y" * 32)),
            "openai_model": "gpt-4.1",
        }
    )

    with pytest.raises(RuntimeConfigError, match="OPENAI_API_KEY"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_openai_model_control_characters(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "admin_auth_mode": "oidc",
            "model_provider": "openai",
            "openai_api_key": "sk-" + ("x" * 64),
            "openai_model": "gpt-4.1\nfallback",
        }
    )

    with pytest.raises(RuntimeConfigError, match="OPENAI_MODEL"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_non_https_servicenow_instance_url(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "servicenow_dev_instance_url": "http://dev.service-now.com",
        }
    )

    with pytest.raises(RuntimeConfigError, match="SERVICENOW_DEV_INSTANCE_URL"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_servicenow_instance_url_string_subclass_without_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingServiceNowUrl(str):
        def __str__(self) -> str:
            return "https://client_secret=direct-servicenow-url-secret@example.service-now.com"

    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "servicenow_dev_instance_url": SecretBearingServiceNowUrl(
                "https://dev.service-now.com"
            ),
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    diagnostic = str(exc.value)
    assert diagnostic == "SERVICENOW_DEV_INSTANCE_URL must be a string runtime setting"
    assert "SecretBearingServiceNowUrl" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-servicenow-url-secret" not in diagnostic


def test_validate_runtime_settings_rejects_servicenow_oauth_secret_control_characters(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "servicenow_dev_client_secret": "dev-secret\nnext-line",
        }
    )

    with pytest.raises(RuntimeConfigError, match="SERVICENOW_DEV_CLIENT_SECRET"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_servicenow_oauth_secret_string_subclass_without_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingServiceNowSecret(str):
        def __len__(self) -> int:
            raise RuntimeError("client_secret=direct-servicenow-oauth-secret")

    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "servicenow_dev_client_secret": SecretBearingServiceNowSecret("dev-secret"),
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    diagnostic = str(exc.value)
    assert diagnostic == "SERVICENOW_DEV_CLIENT_SECRET must be a string runtime setting"
    assert "SecretBearingServiceNowSecret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-servicenow-oauth-secret" not in diagnostic


def test_validate_runtime_settings_rejects_production_public_web_without_allowlist(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "webhook-secret",
            "admin_auth_mode": "oidc",
            "public_web_access": "worker",
            "public_web_allowed_domains": [],
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_PUBLIC_WEB_ALLOWED_DOMAINS"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_public_web_access_string_subclass_without_eq_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingPublicWebAccess(str):
        def __eq__(self, _other: object) -> bool:
            raise RuntimeError("client_secret=direct-public-web-access-secret")

    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "allow_combined_production": True,
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "admin_auth_mode": "oidc",
            "strict_transport_security_enabled": True,
            "public_web_access": SecretBearingPublicWebAccess("worker"),
            "public_web_allowed_domains": ["docs.servicenow.com"],
            "public_web_doc_urls": ["https://docs.servicenow.com/csh"],
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_PUBLIC_WEB_ACCESS must be a string runtime setting"
    assert "SecretBearingPublicWebAccess" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-public-web-access-secret" not in diagnostic


def test_validate_runtime_settings_rejects_production_weak_webhook_secret(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "short",
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_LIFECYCLE_WEBHOOK_SECRET"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_webhook_secret_string_subclass_without_len_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingWebhookSecret(str):
        def __len__(self) -> int:
            raise RuntimeError("client_secret=direct-webhook-secret")

    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": SecretBearingWebhookSecret("x" * 32),
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_LIFECYCLE_WEBHOOK_SECRET must be a string runtime setting"
    assert "SecretBearingWebhookSecret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-webhook-secret" not in diagnostic


def test_validate_runtime_settings_rejects_webhook_secret_control_characters(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": ("x" * 32) + "\n" + ("y" * 32),
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_LIFECYCLE_WEBHOOK_SECRET"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_oversized_lifecycle_webhook_secret(
    tmp_path: Path,
) -> None:
    oversized_secret = "x" * 8193
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "allow_combined_production": True,
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": oversized_secret,
            "strict_transport_security_enabled": True,
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    message = str(exc.value)
    assert (
        "JEDI_LIFECYCLE_WEBHOOK_SECRET must be at most 8192 bytes in production"
        in message
    )
    assert oversized_secret not in message


def test_lifecycle_webhook_credential_policy_is_shared_by_startup_and_request_time() -> None:
    from jedi_devproject import lifecycle_webhook_policy
    from jedi_devproject.lifecycle_api import (
        MAX_LIFECYCLE_WEBHOOK_CREDENTIAL_BYTES,
        _has_padded_or_control_webhook_credential,
    )

    assert (
        runtime_config.MAX_PRODUCTION_LIFECYCLE_WEBHOOK_SECRET_BYTES
        == lifecycle_webhook_policy.MAX_LIFECYCLE_WEBHOOK_CREDENTIAL_BYTES
    )
    assert (
        MAX_LIFECYCLE_WEBHOOK_CREDENTIAL_BYTES
        == lifecycle_webhook_policy.MAX_LIFECYCLE_WEBHOOK_CREDENTIAL_BYTES
    )
    oversized_secret = (
        "x" * (lifecycle_webhook_policy.MAX_LIFECYCLE_WEBHOOK_CREDENTIAL_BYTES + 1)
    )
    assert (
        lifecycle_webhook_policy.is_malformed_lifecycle_webhook_credential(
            oversized_secret
        )
        is True
    )
    assert _has_padded_or_control_webhook_credential(oversized_secret) is True


def test_validate_runtime_settings_rejects_production_weak_admin_api_token(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "admin_api_token": "short",
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_ADMIN_API_TOKEN"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_admin_api_token_string_subclass_without_len_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingAdminToken(str):
        def __len__(self) -> int:
            raise RuntimeError("client_secret=direct-admin-token-secret")

    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "admin_api_token": SecretBearingAdminToken("y" * 32),
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_ADMIN_API_TOKEN must be a string runtime setting"
    assert "SecretBearingAdminToken" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-admin-token-secret" not in diagnostic


def test_validate_runtime_settings_rejects_admin_api_token_control_characters(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "admin_api_token": ("x" * 32) + "\n" + ("y" * 32),
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_ADMIN_API_TOKEN"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_oversized_admin_api_token(
    tmp_path: Path,
) -> None:
    oversized_token = "x" * 8193
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "admin_api_token": oversized_token,
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    message = str(exc.value)
    assert "JEDI_ADMIN_API_TOKEN must be at most 8192 bytes in production when configured" in (
        message
    )
    assert oversized_token not in message


def test_validate_runtime_settings_rejects_non_ascii_admin_api_token(
    tmp_path: Path,
) -> None:
    non_ascii_token = ("x" * 32) + "é"
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "allow_combined_production": True,
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "strict_transport_security_enabled": True,
            "admin_api_token": non_ascii_token,
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    message = str(exc.value)
    assert (
        "JEDI_ADMIN_API_TOKEN must contain only ASCII characters in production when configured"
        in message
    )
    assert non_ascii_token not in message


def test_admin_bearer_token_limit_policy_is_shared_by_startup_and_request_time() -> None:
    from jedi_devproject import admin_token_policy

    assert (
        runtime_config.MAX_PRODUCTION_ADMIN_API_TOKEN_BYTES
        == admin_token_policy.MAX_ADMIN_BEARER_TOKEN_BYTES
    )
    assert (
        runtime_auth.MAX_ADMIN_BEARER_TOKEN_BYTES
        == admin_token_policy.MAX_ADMIN_BEARER_TOKEN_BYTES
    )
    oversized_token = "x" * (admin_token_policy.MAX_ADMIN_BEARER_TOKEN_BYTES + 1)
    assert admin_token_policy.is_malformed_admin_bearer_token(oversized_token) is True
    assert runtime_auth._has_malformed_admin_bearer_token(oversized_token) is True


def test_admin_basic_auth_policy_is_shared_by_startup_and_request_time() -> None:
    from jedi_devproject import admin_basic_auth_policy

    assert (
        runtime_config.MAX_ADMIN_CONSOLE_CREDENTIAL_BYTES
        == admin_basic_auth_policy.MAX_BASIC_AUTH_CREDENTIAL_BYTES
    )
    assert (
        runtime_auth.MAX_BASIC_AUTH_ENCODED_BYTES
        == admin_basic_auth_policy.MAX_BASIC_AUTH_ENCODED_BYTES
    )
    oversized_credential = "x" * (admin_basic_auth_policy.MAX_BASIC_AUTH_CREDENTIAL_BYTES + 1)
    assert (
        admin_basic_auth_policy.is_malformed_admin_console_credential_part(
            oversized_credential
        )
        is True
    )
    assert runtime_auth._has_malformed_admin_console_credential_part(oversized_credential) is True


@pytest.mark.parametrize(
    "encoded_section",
    [
        "dXNlcjpwYXNz ",
        " dXNlcjpwYXNz",
        "dXNlcjpwYXNz\n",
        "dXNlcjpwYXNzé",
        "A" * 8193,
    ],
)
def test_admin_basic_auth_encoded_section_policy_is_shared(
    encoded_section: str,
) -> None:
    from jedi_devproject import admin_basic_auth_policy

    assert admin_basic_auth_policy.is_malformed_basic_auth_encoded_section(encoded_section) is True
    assert runtime_auth._basic_auth_credentials(f"Basic {encoded_section}") is None


def test_validate_runtime_settings_rejects_non_positive_runtime_limits(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "lifecycle_webhook_max_skew_seconds": 0,
            "lifecycle_webhook_max_body_bytes": 0,
            "lifecycle_rate_limit_max_requests": 0,
            "lifecycle_rate_limit_window_seconds": 0,
            "lifecycle_rate_limit_max_buckets": 0,
            "admin_rate_limit_max_requests": 0,
            "admin_rate_limit_window_seconds": 0,
            "admin_rate_limit_max_buckets": 0,
            "admin_max_body_bytes": 0,
            "strict_transport_security_max_age_seconds": 0,
            "alert_webhook_timeout_seconds": 0,
            "alert_webhook_max_body_bytes": 0,
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    message = str(exc.value)
    assert "JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS" in message
    assert "JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES" in message
    assert "JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS" in message
    assert "JEDI_LIFECYCLE_RATE_LIMIT_WINDOW_SECONDS" in message
    assert "JEDI_LIFECYCLE_RATE_LIMIT_MAX_BUCKETS" in message
    assert "JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS" in message
    assert "JEDI_ADMIN_RATE_LIMIT_WINDOW_SECONDS" in message
    assert "JEDI_ADMIN_RATE_LIMIT_MAX_BUCKETS" in message
    assert "JEDI_ADMIN_MAX_BODY_BYTES" in message
    assert "JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS" in message
    assert "JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS" in message
    assert "JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES" in message


def test_validate_runtime_settings_rejects_excessive_production_outbound_timeouts(
    tmp_path: Path,
) -> None:
    excessive_timeout_seconds = 300.0
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": "worker",
            "alert_webhook_timeout_seconds": excessive_timeout_seconds,
            "public_web_timeout_seconds": excessive_timeout_seconds,
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    message = str(exc.value)
    assert "JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS must be at most 30" in message
    assert "JEDI_PUBLIC_WEB_TIMEOUT_SECONDS must be at most 30" in message
    assert str(excessive_timeout_seconds) not in message


@pytest.mark.parametrize("runtime_role", ["api", "combined"])
def test_validate_runtime_settings_rejects_excessive_lifecycle_webhook_replay_window(
    tmp_path: Path,
    runtime_role: str,
) -> None:
    settings_base = (
        _settings(tmp_path) if runtime_role == "api" else _settings_with_openai(tmp_path)
    )
    settings = settings_base.model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": runtime_role,
            "allow_combined_production": runtime_role == "combined",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "lifecycle_webhook_max_skew_seconds": 86_400,
            "strict_transport_security_enabled": True,
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_excessive_production_body_size_caps(
    tmp_path: Path,
) -> None:
    excessive_body_bytes = 10 * 1024 * 1024
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": "api",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "lifecycle_webhook_max_body_bytes": excessive_body_bytes,
            "admin_max_body_bytes": excessive_body_bytes,
            "alert_webhook_max_body_bytes": excessive_body_bytes,
            "strict_transport_security_enabled": True,
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    message = str(exc.value)
    assert "JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES must be at most" in message
    assert "JEDI_ADMIN_MAX_BODY_BYTES must be at most" in message
    assert "JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES must be at most" in message
    assert str(excessive_body_bytes) not in message


def test_validate_runtime_settings_rejects_excessive_public_web_resource_limits(
    tmp_path: Path,
) -> None:
    excessive_response_bytes = 10 * 1024 * 1024
    excessive_excerpt_chars = 1_000_000
    excessive_results = 1_000
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": "worker",
            "public_web_access": "worker",
            "public_web_allowed_domains": ["docs.servicenow.com"],
            "public_web_doc_urls": ["https://docs.servicenow.com/ui-policy"],
            "public_web_max_response_bytes": excessive_response_bytes,
            "public_web_max_excerpt_chars": excessive_excerpt_chars,
            "public_web_max_results": excessive_results,
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    message = str(exc.value)
    assert "JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES must be at most" in message
    assert "JEDI_PUBLIC_WEB_MAX_EXCERPT_CHARS must be at most" in message
    assert "JEDI_PUBLIC_WEB_MAX_RESULTS must be at most" in message
    assert str(excessive_response_bytes) not in message
    assert str(excessive_excerpt_chars) not in message
    assert str(excessive_results) not in message


def test_validate_runtime_settings_rejects_excessive_rate_limit_bucket_caps(
    tmp_path: Path,
) -> None:
    excessive_bucket_cap = MAX_CONFIGURABLE_RATE_LIMIT_BUCKETS + 1
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "lifecycle_rate_limit_max_buckets": excessive_bucket_cap,
            "admin_rate_limit_max_buckets": excessive_bucket_cap,
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    message = str(exc.value)
    assert "JEDI_LIFECYCLE_RATE_LIMIT_MAX_BUCKETS must be at most" in message
    assert "JEDI_ADMIN_RATE_LIMIT_MAX_BUCKETS must be at most" in message
    assert str(excessive_bucket_cap) not in message


def test_validate_runtime_settings_rejects_excessive_rate_limit_request_caps(
    tmp_path: Path,
) -> None:
    excessive_request_cap = MAX_CONFIGURABLE_RATE_LIMIT_REQUESTS + 1
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "lifecycle_rate_limit_max_requests": excessive_request_cap,
            "admin_rate_limit_max_requests": excessive_request_cap,
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    message = str(exc.value)
    assert "JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS must be at most" in message
    assert "JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS must be at most" in message
    assert str(excessive_request_cap) not in message


def test_validate_runtime_settings_rejects_excessive_rate_limit_windows(
    tmp_path: Path,
) -> None:
    excessive_window_seconds = MAX_CONFIGURABLE_RATE_LIMIT_WINDOW_SECONDS + 1
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "lifecycle_rate_limit_window_seconds": excessive_window_seconds,
            "admin_rate_limit_window_seconds": excessive_window_seconds,
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    message = str(exc.value)
    assert "JEDI_LIFECYCLE_RATE_LIMIT_WINDOW_SECONDS must be at most" in message
    assert "JEDI_ADMIN_RATE_LIMIT_WINDOW_SECONDS must be at most" in message
    assert str(excessive_window_seconds) not in message


def test_validate_runtime_settings_rejects_public_web_docs_outside_allowlist(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "public_web_access": "worker",
            "public_web_allowed_domains": ["docs.servicenow.com"],
            "public_web_doc_urls": [
                "https://docs.servicenow.com/ui-policy",
                "https://example.com/leak",
            ],
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_PUBLIC_WEB_DOC_URLS"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_malformed_public_web_allowed_domains(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "public_web_access": "worker",
            "public_web_allowed_domains": [" docs.servicenow.com"],
            "public_web_doc_urls": ["https://docs.servicenow.com/ui-policy"],
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_PUBLIC_WEB_ALLOWED_DOMAINS"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_public_web_allowed_domains_string_subclass_without_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingAllowedDomain(str):
        def strip(self, _chars: str | None = None) -> str:
            raise RuntimeError("client_secret=direct-public-web-domain-secret")

    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "public_web_access": "worker",
            "public_web_allowed_domains": [
                SecretBearingAllowedDomain("docs.servicenow.com")
            ],
            "public_web_doc_urls": ["https://docs.servicenow.com/ui-policy"],
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS must be a string list setting"
    assert "SecretBearingAllowedDomain" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-public-web-domain-secret" not in diagnostic


def test_load_runtime_settings_rejects_padded_public_web_csv_values_from_env(
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
                "JEDI_ENVIRONMENT=production",
                "JEDI_MODEL_PROVIDER=openai",
                "OPENAI_API_KEY=openai-api-key",
                "OPENAI_MODEL=gpt-4.1",
                "JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE=hmac_sha256",
                "JEDI_LIFECYCLE_WEBHOOK_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "JEDI_PUBLIC_WEB_ACCESS=worker",
                "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS=docs.servicenow.com, developer.servicenow.com",
                (
                    "JEDI_PUBLIC_WEB_DOC_URLS=https://docs.servicenow.com/ui-policy,"
                    " https://developer.servicenow.com/api"
                ),
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError) as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS" in message
    assert "JEDI_PUBLIC_WEB_DOC_URLS" in message


@pytest.mark.parametrize(
    ("setting_name", "env_line"),
    [
        (
            "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS",
            "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS=docs.servicenow.com,,developer.servicenow.com",
        ),
        (
            "JEDI_PUBLIC_WEB_DOC_URLS",
            "JEDI_PUBLIC_WEB_DOC_URLS=https://docs.servicenow.com/ui-policy,",
        ),
    ],
)
def test_load_runtime_settings_rejects_empty_public_web_csv_items_from_env(
    tmp_path: Path,
    setting_name: str,
    env_line: str,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            (
                [
                    "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
                    "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                    "SERVICENOW_CLIENT_ID=client-id",
                    "SERVICENOW_CLIENT_SECRET=client-secret",
                    f"JEDI_AUDIT_ROOT={tmp_path}",
                ]
                + (
                    [
                        env_line,
                        "JEDI_PUBLIC_WEB_DOC_URLS=https://docs.servicenow.com/ui-policy",
                    ]
                    if setting_name == "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS"
                    else [
                        "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS=docs.servicenow.com",
                        env_line,
                    ]
                )
            ),
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=setting_name) as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "must not contain empty CSV items" in message
    assert ",," not in message
    assert "ui-policy" not in message


def test_runtime_csv_values_rejects_non_string_without_truthiness_leak() -> None:
    class SecretBearingCsvValue:
        def __bool__(self) -> bool:
            raise RuntimeError("client_secret=runtime-csv-secret")

        def __str__(self) -> str:
            return "docs.servicenow.com,client_secret=runtime-csv-secret"

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_config._csv_values(
            cast(Any, SecretBearingCsvValue()),
            name="JEDI_PUBLIC_WEB_ALLOWED_DOMAINS",
        )

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS must be a string runtime setting"
    assert "SecretBearingCsvValue" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "runtime-csv-secret" not in diagnostic


def test_runtime_csv_values_rejects_string_subclass_without_method_leak() -> None:
    class SecretBearingCsvText(str):
        def split(
            self,
            sep: str | None = None,
            maxsplit: SupportsIndex = -1,
        ) -> list[str]:
            raise RuntimeError("client_secret=runtime-csv-subclass-secret")

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_config._csv_values(
            SecretBearingCsvText("docs.servicenow.com"),
            name="JEDI_PUBLIC_WEB_ALLOWED_DOMAINS",
        )

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS must be a string runtime setting"
    assert "SecretBearingCsvText" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "runtime-csv-subclass-secret" not in diagnostic


def test_optional_model_provider_rejects_string_subclass_without_method_leak() -> None:
    class SecretBearingProviderText(str):
        def strip(self, chars: str | None = None) -> str:
            raise RuntimeError("client_secret=runtime-provider-secret")

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_config._optional_model_provider(SecretBearingProviderText("openai"))

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_MODEL_PROVIDER must be a string runtime setting"
    assert "SecretBearingProviderText" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "runtime-provider-secret" not in diagnostic


def test_optional_alert_webhook_url_rejects_non_string_without_equality_leak() -> None:
    class SecretBearingAlertUrl:
        def __eq__(self, _other: object) -> bool:
            raise RuntimeError("client_secret=runtime-alert-secret")

        def __str__(self) -> str:
            return "https://hooks.example.test?client_secret=runtime-alert-secret"

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_config._optional_alert_webhook_url(cast(Any, SecretBearingAlertUrl()))

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_ALERT_WEBHOOK_URL must be a string runtime setting"
    assert "SecretBearingAlertUrl" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "runtime-alert-secret" not in diagnostic


def test_optional_admin_console_credential_rejects_string_subclass_without_method_leak() -> None:
    class SecretBearingAdminCredential(str):
        def strip(self, chars: str | None = None) -> str:
            raise RuntimeError("client_secret=runtime-admin-secret")

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_config._optional_admin_console_credential(
            SecretBearingAdminCredential("admin"),
            name="JEDI_ADMIN_USERNAME",
        )

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_ADMIN_USERNAME must be a string runtime setting"
    assert "SecretBearingAdminCredential" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "runtime-admin-secret" not in diagnostic


def test_optional_openai_provider_value_rejects_string_subclass_without_method_leak() -> None:
    class SecretBearingOpenAISetting(str):
        def strip(self, chars: str | None = None) -> str:
            raise RuntimeError("client_secret=runtime-openai-secret")

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_config._optional_openai_provider_value(
            SecretBearingOpenAISetting("gpt-4.1"),
            name="OPENAI_MODEL",
        )

    diagnostic = str(exc.value)
    assert diagnostic == "OPENAI_MODEL must be a string runtime setting"
    assert "SecretBearingOpenAISetting" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "runtime-openai-secret" not in diagnostic


def test_validate_runtime_settings_rejects_public_web_doc_url_credentials(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "public_web_access": "worker",
            "public_web_allowed_domains": ["docs.servicenow.com"],
            "public_web_doc_urls": [
                "https://doc-user:doc-secret@docs.servicenow.com/ui-policy",
            ],
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_PUBLIC_WEB_DOC_URLS"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_redacts_public_web_doc_url_credentials(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "public_web_access": "worker",
            "public_web_allowed_domains": ["docs.servicenow.com"],
            "public_web_doc_urls": [
                "https://doc-user:doc-secret@docs.servicenow.com/ui-policy",
            ],
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_PUBLIC_WEB_DOC_URLS") as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    message = str(exc.value)
    assert "doc-user" not in message
    assert "doc-secret" not in message
    assert "ui-policy" not in message


def test_validate_runtime_settings_redacts_public_web_doc_url_query_secrets(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "public_web_access": "worker",
            "public_web_allowed_domains": ["docs.servicenow.com"],
            "public_web_doc_urls": [
                "https://docs.servicenow.com/ui-policy?client_secret=query-secret",
            ],
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_PUBLIC_WEB_DOC_URLS") as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    message = str(exc.value)
    assert "client_secret" not in message
    assert "query-secret" not in message
    assert "ui-policy" not in message


@pytest.mark.parametrize(
    "doc_url",
    [
        "https://docs.servicenow.com/ui-policy?client_secret=doc-secret",
        "https://docs.servicenow.com/ui-policy#section",
        "https://docs.servicenow.com/ui policy",
        "https://docs.servicenow.com/ui-policy%0aX-Injected",
    ],
)
def test_validate_runtime_settings_rejects_unsafe_public_web_doc_url_content(
    tmp_path: Path,
    doc_url: str,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "public_web_access": "worker",
            "public_web_allowed_domains": ["docs.servicenow.com"],
            "public_web_doc_urls": [doc_url],
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_PUBLIC_WEB_DOC_URLS"):
        validate_runtime_settings(settings, require_admin_auth=False)


@pytest.mark.parametrize(
    ("allowed_domain", "doc_url"),
    [
        ("127.0.0.1", "https://127.0.0.1/ui-policy"),
        ("localhost", "https://localhost/ui-policy"),
        ("alerts.localhost", "https://alerts.localhost/ui-policy"),
        ("10.0.0.1", "https://10.0.0.1/ui-policy"),
        ("169.254.169.254", "https://169.254.169.254/latest/meta-data"),
        ("2130706433", "https://2130706433/ui-policy"),
        ("2852039166", "https://2852039166/latest/meta-data"),
    ],
)
def test_validate_runtime_settings_rejects_private_public_web_doc_hosts(
    tmp_path: Path,
    allowed_domain: str,
    doc_url: str,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "public_web_access": "worker",
            "public_web_allowed_domains": [allowed_domain],
            "public_web_doc_urls": [doc_url],
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_PUBLIC_WEB_DOC_URLS"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_enabled_alert_webhook_without_url(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "alert_webhook_enabled": True,
            "alert_webhook_url": None,
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_ALERT_WEBHOOK_URL"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_alert_webhook_url_string_subclass_without_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingAlertWebhookUrl(str):
        def __len__(self) -> int:
            raise RuntimeError("client_secret=direct-alert-webhook-url-secret")

    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "alert_webhook_enabled": True,
            "alert_webhook_url": SecretBearingAlertWebhookUrl(
                "https://alerts.example.gov/jedi"
            ),
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_ALERT_WEBHOOK_URL must be a string runtime setting"
    assert "SecretBearingAlertWebhookUrl" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-alert-webhook-url-secret" not in diagnostic


def test_validate_runtime_settings_rejects_non_https_alert_webhook_url(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "alert_webhook_enabled": True,
            "alert_webhook_url": "http://alerts.example.gov/jedi",
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_ALERT_WEBHOOK_URL must use HTTPS"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_alert_webhook_url_credentials(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "alert_webhook_enabled": True,
            "alert_webhook_url": "https://alert-user:alert-secret@alerts.example.gov/jedi",
        }
    )

    with pytest.raises(
        RuntimeConfigError,
        match="JEDI_ALERT_WEBHOOK_URL must not include credentials",
    ):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_alert_webhook_sensitive_query_params(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "alert_webhook_enabled": True,
            "alert_webhook_url": "https://alerts.example.gov/jedi?token=secret",
        }
    )

    with pytest.raises(
        RuntimeConfigError,
        match="JEDI_ALERT_WEBHOOK_URL must not include sensitive query parameters: token",
    ):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_alert_webhook_semicolon_sensitive_query_params(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "alert_webhook_enabled": True,
            "alert_webhook_url": "https://alerts.example.gov/jedi?team=platform;token=secret",
        }
    )

    with pytest.raises(
        RuntimeConfigError,
        match="JEDI_ALERT_WEBHOOK_URL must not include sensitive query parameters: token",
    ):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_alert_webhook_encoded_separator_query_params(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "alert_webhook_enabled": True,
            "alert_webhook_url": (
                "https://alerts.example.gov/jedi?team=platform%3Bclient_secret=secret"
            ),
        }
    )

    with pytest.raises(
        RuntimeConfigError,
        match=("JEDI_ALERT_WEBHOOK_URL must not include sensitive query parameters: client_secret"),
    ):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_alert_webhook_double_encoded_separator_query_params(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "alert_webhook_enabled": True,
            "alert_webhook_url": (
                "https://alerts.example.gov/jedi?team=platform%253Bclient_secret=secret"
            ),
        }
    )

    with pytest.raises(
        RuntimeConfigError,
        match=("JEDI_ALERT_WEBHOOK_URL must not include sensitive query parameters: client_secret"),
    ):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_alert_webhook_url_fragments(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "alert_webhook_enabled": True,
            "alert_webhook_url": "https://alerts.example.gov/jedi#ignored",
        }
    )

    with pytest.raises(
        RuntimeConfigError,
        match="JEDI_ALERT_WEBHOOK_URL must not include fragments",
    ):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_alert_webhook_url_control_characters(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "alert_webhook_enabled": True,
            "alert_webhook_url": "https://alerts.example.gov/jedi\nX-Injected: value",
        }
    )

    with pytest.raises(
        RuntimeConfigError,
        match=("JEDI_ALERT_WEBHOOK_URL must not include whitespace or control characters"),
    ):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_alert_webhook_url_encoded_control_characters(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "alert_webhook_enabled": True,
            "alert_webhook_url": "https://alerts.example.gov/jedi%0d%0aX-Injected",
        }
    )

    with pytest.raises(
        RuntimeConfigError,
        match=("JEDI_ALERT_WEBHOOK_URL must not include encoded whitespace or control characters"),
    ):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_alert_webhook_url_legacy_ipv4_loopback(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "alert_webhook_enabled": True,
            "alert_webhook_url": "https://0177.0.0.1/jedi",
        }
    )

    with pytest.raises(
        RuntimeConfigError,
        match="JEDI_ALERT_WEBHOOK_URL must not target local or link-local addresses",
    ):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_alert_webhook_unicode_dot_loopback(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "alert_webhook_enabled": True,
            "alert_webhook_url": "https://localhost。/jedi",
        }
    )

    with pytest.raises(
        RuntimeConfigError,
        match="JEDI_ALERT_WEBHOOK_URL must not target local or link-local addresses",
    ):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_update_set_apply_without_operator(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "update_set_apply": True,
            "update_set_user_name": None,
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_UPDATE_SET_USER_NAME"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_malformed_update_set_apply_operator(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "update_set_apply": True,
            "update_set_user_name": "jedi.integration\n",
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_UPDATE_SET_USER_NAME"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_update_set_apply_operator_string_subclass_without_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingUpdateSetUserName(str):
        def __len__(self) -> int:
            raise RuntimeError("client_secret=direct-update-set-user-secret")

    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "update_set_apply": True,
            "update_set_user_name": SecretBearingUpdateSetUserName(
                "jedi.integration"
            ),
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_UPDATE_SET_USER_NAME must be a string runtime setting"
    assert "SecretBearingUpdateSetUserName" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-update-set-user-secret" not in diagnostic


def test_validate_runtime_settings_rejects_padded_build_claim_states_in_production(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "build_claim_apply": True,
            "build_claim_from_state": " 1",
            "build_claim_state": "Work in Progress",
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_BUILD_CLAIM_FROM_STATE"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_build_claim_state_string_subclass_without_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingBuildClaimState(str):
        def __len__(self) -> int:
            raise RuntimeError("client_secret=direct-build-claim-state-secret")

    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "build_claim_apply": True,
            "build_claim_from_state": SecretBearingBuildClaimState("1"),
            "build_claim_state": "2",
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_BUILD_CLAIM_FROM_STATE must be a string runtime setting"
    assert "SecretBearingBuildClaimState" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-build-claim-state-secret" not in diagnostic


def test_validate_runtime_settings_rejects_malformed_worker_id_in_production(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "worker_id": "worker-1\n",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_WORKER_ID"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_worker_id_string_subclass_without_truthiness_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingWorkerId(str):
        def __len__(self) -> int:
            raise RuntimeError("client_secret=direct-worker-id-secret")

    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "worker_id": SecretBearingWorkerId("worker-1"),
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_WORKER_ID must be a string runtime setting"
    assert "SecretBearingWorkerId" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-worker-id-secret" not in diagnostic


def test_validate_runtime_settings_rejects_relative_audit_root_in_production(
    tmp_path: Path,
) -> None:
    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "audit_root": Path("artifacts/audit"),
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
        }
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_AUDIT_ROOT"):
        validate_runtime_settings(settings, require_admin_auth=False)


def test_validate_runtime_settings_rejects_direct_audit_root_object_without_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingAuditRoot:
        def __fspath__(self) -> str:
            raise RuntimeError("client_secret=direct-audit-root-secret")

        def __str__(self) -> str:
            raise RuntimeError("client_secret=direct-audit-root-secret")

    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "audit_root": cast(Any, SecretBearingAuditRoot()),
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_AUDIT_ROOT must be a path runtime setting"
    assert "SecretBearingAuditRoot" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-audit-root-secret" not in diagnostic


def test_create_runtime_api_validates_production_settings_before_store_open(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(update={"runtime_environment": "production"})

    def store_factory(_database_url: str) -> FakeRuntimeStore:
        raise AssertionError("store factory should not be called")

    with pytest.raises(RuntimeConfigError, match="JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE"):
        create_runtime_api(settings=settings, store_factory=store_factory)


def test_validate_runtime_settings_rejects_positive_int_setting_subclass_without_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingBodyLimit(int):
        def __le__(self, _other: object) -> bool:
            raise RuntimeError("client_secret=direct-body-limit-secret")

    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "lifecycle_webhook_max_body_bytes": SecretBearingBodyLimit(4096),
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    diagnostic = str(exc.value)
    assert diagnostic == (
        "JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES must be an integer runtime setting"
    )
    assert "SecretBearingBodyLimit" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-body-limit-secret" not in diagnostic


def test_validate_runtime_settings_rejects_timeout_setting_subclass_without_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingTimeout(float):
        def __le__(self, _other: object) -> bool:
            raise RuntimeError("client_secret=direct-timeout-secret")

    settings = _settings_with_openai(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "alert_webhook_timeout_seconds": SecretBearingTimeout(2.5),
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        validate_runtime_settings(settings, require_admin_auth=False)

    diagnostic = str(exc.value)
    assert diagnostic == (
        "JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS must be a finite number runtime setting"
    )
    assert "SecretBearingTimeout" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "direct-timeout-secret" not in diagnostic


@pytest.mark.parametrize(
    ("field_name", "bad_value", "expected_error"),
    [
        (
            "alert_webhook_timeout_seconds",
            0.0,
            "JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS",
        ),
        (
            "alert_webhook_timeout_seconds",
            -1.0,
            "JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS",
        ),
        (
            "alert_webhook_timeout_seconds",
            runtime_config.MAX_PRODUCTION_OUTBOUND_TIMEOUT_SECONDS + 1,
            "JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS",
        ),
        (
            "alert_webhook_max_body_bytes",
            0,
            "JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES",
        ),
        (
            "alert_webhook_max_body_bytes",
            -1,
            "JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES",
        ),
        (
            "alert_webhook_max_body_bytes",
            runtime_config.MAX_PRODUCTION_ALERT_WEBHOOK_BODY_BYTES + 1,
            "JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES",
        ),
    ],
)
def test_create_runtime_api_rejects_invalid_alert_webhook_settings_before_store_open(
    tmp_path: Path,
    field_name: str,
    bad_value: object,
    expected_error: str,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "alert_webhook_enabled": True,
            "alert_webhook_url": "https://alerts.example.gov/jedi",
            field_name: bad_value,
        }
    )

    def store_factory(_database_url: str) -> FakeRuntimeStore:
        raise AssertionError("store factory should not be called")

    with pytest.raises(RuntimeConfigError, match=expected_error) as exc:
        create_runtime_api(settings=settings, store_factory=store_factory)

    assert "secret" not in str(exc.value).lower()


@pytest.mark.parametrize(
    ("field_name", "bad_value", "expected_error"),
    [
        (
            "lifecycle_webhook_max_body_bytes",
            0,
            "JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES",
        ),
        (
            "lifecycle_webhook_max_body_bytes",
            -1,
            "JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES",
        ),
        (
            "lifecycle_webhook_max_body_bytes",
            runtime_config.MAX_PRODUCTION_LIFECYCLE_WEBHOOK_BODY_BYTES + 1,
            "JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES",
        ),
        (
            "admin_max_body_bytes",
            0,
            "JEDI_ADMIN_MAX_BODY_BYTES",
        ),
        (
            "admin_max_body_bytes",
            -1,
            "JEDI_ADMIN_MAX_BODY_BYTES",
        ),
        (
            "admin_max_body_bytes",
            runtime_config.MAX_PRODUCTION_ADMIN_BODY_BYTES + 1,
            "JEDI_ADMIN_MAX_BODY_BYTES",
        ),
    ],
)
def test_create_runtime_api_rejects_invalid_request_body_limits_before_store_open(
    tmp_path: Path,
    field_name: str,
    bad_value: object,
    expected_error: str,
) -> None:
    settings = _settings(tmp_path).model_copy(update={field_name: bad_value})

    def store_factory(_database_url: str) -> FakeRuntimeStore:
        raise AssertionError("store factory should not be called")

    with pytest.raises(RuntimeConfigError, match=expected_error) as exc:
        create_runtime_api(settings=settings, store_factory=store_factory)

    assert "secret" not in str(exc.value).lower()


def test_create_runtime_api_allows_production_with_disabled_console_and_admin_token(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    token = "y" * 32
    settings = _settings(tmp_path).model_copy(
        update={
            "runtime_environment": "production",
            "runtime_role": "api",
            "lifecycle_webhook_auth_mode": "hmac_sha256",
            "lifecycle_webhook_secret": "x" * 32,
            "strict_transport_security_enabled": True,
            "admin_auth_mode": "disabled",
            "admin_api_token": token,
        }
    )
    client = TestClient(
        create_runtime_api(
            settings=settings,
            store_factory=lambda _database_url: store,
        )
    )

    console_response = client.get("/admin")
    jobs_without_token = client.get("/admin/jobs")
    jobs_with_token = client.get("/admin/jobs", headers={"Authorization": f"Bearer {token}"})

    assert console_response.status_code == 503
    assert console_response.json()["detail"] == "admin console authentication is disabled"
    assert jobs_without_token.status_code == 401
    assert jobs_with_token.status_code == 200


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


def test_process_one_runtime_fulfillment_rejects_api_role_before_servicenow_or_store(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(update={"runtime_role": "api"})
    transport = RecordingTransport([])

    def store_factory(_database_url: str) -> FakeRuntimeStore:
        raise AssertionError("store factory should not be called")

    with pytest.raises(RuntimeConfigError, match="JEDI_RUNTIME_ROLE=api"):
        process_one_runtime_fulfillment(
            settings=settings,
            store_factory=store_factory,
            transport=transport,
        )

    assert transport.requests == []


def test_process_one_runtime_fulfillment_validates_runtime_role_before_api_role_branch(
    tmp_path: Path,
) -> None:
    class SecretBearingRuntimeRole(str):
        def __eq__(self, _other: object) -> bool:
            raise RuntimeError("client_secret=fulfillment-runtime-role-secret")

    settings = _settings(tmp_path).model_copy(
        update={"runtime_role": SecretBearingRuntimeRole("worker")}
    )
    transport = RecordingTransport([])

    def store_factory(_database_url: str) -> FakeRuntimeStore:
        raise AssertionError("store factory should not be called")

    with pytest.raises(RuntimeConfigError) as exc:
        process_one_runtime_fulfillment(
            settings=settings,
            store_factory=store_factory,
            transport=transport,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_RUNTIME_ROLE must be a string runtime setting"
    assert "SecretBearingRuntimeRole" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "fulfillment-runtime-role-secret" not in diagnostic
    assert transport.requests == []


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


@pytest.mark.parametrize(
    "provider_line",
    [
        'JEDI_MODEL_PROVIDER=" openai"',
        'JEDI_MODEL_PROVIDER="openai "',
        'JEDI_MODEL_PROVIDER="openai\tfallback"',
    ],
)
def test_load_runtime_settings_rejects_model_provider_env_whitespace(
    tmp_path: Path,
    provider_line: str,
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
                provider_line,
                "OPENAI_API_KEY=openai-key",
                "OPENAI_MODEL=gpt-4o-2024-08-06",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_MODEL_PROVIDER"):
        load_runtime_settings(env_path)


def test_load_runtime_settings_rejects_oversized_model_provider_env_value(
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
                f"JEDI_MODEL_PROVIDER={'x' * 257}",
                "OPENAI_API_KEY=openai-key",
                "OPENAI_MODEL=gpt-4o-2024-08-06",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_MODEL_PROVIDER.*<= 256"):
        load_runtime_settings(env_path)


@pytest.mark.parametrize(
    ("env_line", "expected_error"),
    [
        ('OPENAI_API_KEY=" openai-key"', "OPENAI_API_KEY"),
        ('OPENAI_API_KEY="openai-key "', "OPENAI_API_KEY"),
        ('OPENAI_MODEL=" gpt-4o-2024-08-06"', "OPENAI_MODEL"),
        ('OPENAI_MODEL="gpt-4o-2024-08-06 "', "OPENAI_MODEL"),
    ],
)
def test_load_runtime_settings_rejects_openai_env_values_with_boundary_whitespace(
    tmp_path: Path,
    env_line: str,
    expected_error: str,
) -> None:
    env_path = tmp_path / ".env"
    openai_api_key = "OPENAI_API_KEY=openai-key"
    openai_model = "OPENAI_MODEL=gpt-4o-2024-08-06"
    if env_line.startswith("OPENAI_API_KEY="):
        openai_api_key = env_line
    else:
        openai_model = env_line
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:secret@localhost:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                f"JEDI_AUDIT_ROOT={tmp_path}",
                "JEDI_MODEL_PROVIDER=openai",
                openai_api_key,
                openai_model,
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match=expected_error):
        load_runtime_settings(env_path)


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


@pytest.mark.parametrize(
    "username_line",
    [
        'JEDI_UPDATE_SET_USER_NAME=" jedi.integration"',
        'JEDI_UPDATE_SET_USER_NAME="jedi.integration "',
        'JEDI_UPDATE_SET_USER_NAME="jedi.integration\tfallback"',
    ],
)
def test_load_runtime_settings_rejects_malformed_update_set_user_name(
    tmp_path: Path,
    username_line: str,
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
                username_line,
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeConfigError, match="JEDI_UPDATE_SET_USER_NAME") as exc:
        load_runtime_settings(env_path)

    message = str(exc.value)
    assert "empty, padded, or contain control characters" in message
    assert "fallback" not in message
    assert "\t" not in message


def test_create_runtime_api_wires_store_factory(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    database_urls: list[str] = []

    def store_factory(database_url: str) -> FakeRuntimeStore:
        database_urls.append(database_url)
        return store

    settings = _settings(tmp_path).model_copy(
        update={
            "lifecycle_webhook_auth_mode": "shared_secret",
            "lifecycle_webhook_secret": "test-webhook-secret",
        }
    )
    client = TestClient(
        create_runtime_api(settings=settings, store_factory=store_factory)
    )

    response = client.post(
        "/lifecycle/events",
        json=_ready_event_payload(),
        headers={"X-JEDI-Webhook-Secret": "test-webhook-secret"},
    )

    assert response.status_code == 202
    assert database_urls == ["postgresql://jedi:secret@localhost:5432/jedi"]
    assert store.recorded_events == ["evt-001"]
    assert store.enqueued_jobs == [("evt-001", "STRY0010013")]


def test_runtime_readiness_checks_operational_store_without_auth(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": [{"name": "operational_store", "status": "ok"}],
    }
    assert store.schema_ready_checks == 1
    assert store.lifecycle_event_limits == []


def test_runtime_readiness_fails_closed_without_secret_leakage(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.raise_on_schema_ready = True
    client = TestClient(
        create_runtime_api(
            settings=_settings(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unready",
        "checks": [{"name": "operational_store", "status": "failed"}],
    }
    assert "secret" not in response.text
    assert "postgresql://" not in response.text


def test_runtime_readiness_reports_missing_schema_without_secret_leakage(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.schema_ready = False
    client = TestClient(
        create_runtime_api(
            settings=_settings(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unready",
        "checks": [{"name": "operational_store_schema", "status": "missing"}],
    }
    assert "secret" not in response.text
    assert "postgresql://" not in response.text


def test_runtime_complete_event_updates_ai_status_without_enqueueing_worker(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(status_code=200, json_body={"result": {"sys_id": "story-sys-id"}}),
        ]
    )
    settings = _settings(tmp_path).model_copy(
        update={
            "lifecycle_webhook_auth_mode": "shared_secret",
            "lifecycle_webhook_secret": "test-webhook-secret",
        }
    )
    client = TestClient(
        create_runtime_api(
            settings=settings,
            store_factory=lambda _database_url: store,
            transport=transport,
        )
    )

    response = client.post(
        "/lifecycle/events",
        json=_complete_event_payload(),
        headers={"X-JEDI-Webhook-Secret": "test-webhook-secret"},
    )

    assert response.status_code == 202
    assert response.json()["lifecycle_action"] == "close_story"
    assert store.enqueued_jobs == []
    assert store.closed_story_jobs == [("STRY0010013", "evt-complete-001")]
    assert [request.method for request in transport.requests] == ["POST", "PATCH"]
    assert transport.requests[-1].url.endswith("/api/now/table/rm_story/story-sys-id")
    assert transport.requests[-1].body == {
        "u_ai_status": "Complete",
        "work_notes": (
            "Automation loop closed after ServiceNow marked the story Complete. "
            "Lifecycle event: evt-complete-001."
        ),
    }


class RecordingCompleteNotifierClient:
    def __init__(self) -> None:
        self.updated_fields: dict[str, object] | None = None
        self.updated_story_sys_id: str | None = None

    def update_story_fields(self, story_sys_id: str, fields: dict[str, object]) -> dict[str, str]:
        self.updated_story_sys_id = story_sys_id
        self.updated_fields = fields
        return {"sys_id": story_sys_id}


def test_servicenow_complete_notifier_sanitizes_work_note_event_id() -> None:
    client = RecordingCompleteNotifierClient()
    notifier = _servicenow_complete_notifier(client=cast(ServiceNowClient, client))

    notifier(
        story_number="STRY0010013",
        story_sys_id="story-sys-id",
        event_id="evt-complete-001\nclient_secret=complete-secret",
    )

    assert client.updated_fields is not None
    work_notes = cast(str, client.updated_fields["work_notes"])
    assert "complete-secret" not in work_notes
    assert "client_secret=***REDACTED***" in work_notes
    assert "\n" not in work_notes
    assert "evt-complete-001" in work_notes


def test_servicenow_complete_notifier_bounds_work_note_event_id() -> None:
    client = RecordingCompleteNotifierClient()
    notifier = _servicenow_complete_notifier(client=cast(ServiceNowClient, client))

    notifier(
        story_number="STRY0010013",
        story_sys_id="story-sys-id",
        event_id=f"evt-complete-001 {'A' * 2200}",
    )

    assert client.updated_fields is not None
    work_notes = cast(str, client.updated_fields["work_notes"])
    assert "...[truncated]" in work_notes
    assert len(work_notes) < 700


def test_servicenow_complete_notifier_sanitizes_missing_sys_id_story_number() -> None:
    client = RecordingCompleteNotifierClient()
    notifier = _servicenow_complete_notifier(client=cast(ServiceNowClient, client))

    with pytest.raises(RuntimeError) as exc_info:
        notifier(
            story_number="STRY0010013\nclient_secret=complete-story-secret",
            story_sys_id=None,
            event_id="evt-complete-001",
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == (
        "story_sys_id missing for completed story: "
        "STRY0010013 client_secret=***REDACTED***"
    )
    assert "complete-story-secret" not in diagnostic
    assert "\n" not in diagnostic


def test_servicenow_complete_notifier_rejects_unsafe_story_sys_id() -> None:
    client = RecordingCompleteNotifierClient()
    notifier = _servicenow_complete_notifier(client=cast(ServiceNowClient, client))

    with pytest.raises(RuntimeError) as exc_info:
        notifier(
            story_number="STRY0010013",
            story_sys_id="story sys id",
            event_id="evt-complete-001",
        )

    assert str(exc_info.value) == "completed story_sys_id is unsafe"
    assert client.updated_story_sys_id is None
    assert client.updated_fields is None


def test_runtime_rejected_event_emits_external_alert_without_enqueueing_worker(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    alert_transport = RecordingTransport([HttpResponse(status_code=202, json_body={"ok": True})])
    settings = _settings(tmp_path).model_copy(
        update={
            "alert_webhook_enabled": True,
            "alert_webhook_url": "https://alerts.example.gov/jedi",
            "alert_webhook_max_body_bytes": 4096,
            "lifecycle_webhook_auth_mode": "shared_secret",
            "lifecycle_webhook_secret": "test-webhook-secret",
        }
    )
    client = TestClient(
        create_runtime_api(
            settings=settings,
            store_factory=lambda _database_url: store,
            transport=RecordingTransport([]),
            alert_transport=alert_transport,
        )
    )

    response = client.post(
        "/lifecycle/events",
        json=_draft_rejected_event_payload(),
        headers={"X-JEDI-Webhook-Secret": "test-webhook-secret"},
    )

    assert response.status_code == 202
    assert response.json()["lifecycle_action"] == "story_rejected"
    assert response.json()["job_id"] == "job-evt-prior-ready"
    assert store.enqueued_jobs == []
    assert store.rejected_story_jobs == [("STRY0010013", "evt-story-rejected-001")]
    assert len(alert_transport.requests) == 1
    assert alert_transport.requests[0].url == "https://alerts.example.gov/jedi"
    assert alert_transport.requests[0].body_bytes is not None
    assert b'"alert_id":"job-evt-prior-ready:rejected"' in (alert_transport.requests[0].body_bytes)
    assert b'"status":"rejected"' in alert_transport.requests[0].body_bytes


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


def test_admin_artifact_api_not_found_does_not_retain_store_cause(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    app = create_runtime_api(
        settings=_settings_with_admin_token(tmp_path),
        store_factory=lambda _database_url: store,
    )
    endpoint = _runtime_route_endpoint(app, "/artifacts/{artifact_id}")

    with pytest.raises(HTTPException) as exc_info:
        endpoint(artifact_id=404, authorization="Bearer admin-token")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "artifact not found"
    assert exc_info.value.__cause__ is None


def test_admin_get_job_or_404_does_not_retain_store_cause() -> None:
    store = FakeRuntimeStore()

    with pytest.raises(HTTPException) as exc_info:
        _get_job_or_404(store=store, job_id="missing-job")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "job not found"
    assert exc_info.value.__cause__ is None


def test_artifact_read_returns_metadata_and_payload(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-001", story_number="STRY0010013").model_copy(
            update={"correlation_id": "corr-evt-001"}
        )
    ]
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
        "event_id": "evt-001",
        "story_number": "STRY0010013",
        "correlation_id": "corr-evt-001",
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


def test_artifact_read_redacts_sensitive_payload_values(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-001", story_number="STRY0010013").model_copy(
            update={"correlation_id": "corr-evt-001"}
        )
    ]
    store.artifact_blob_records[4] = ArtifactBlobRecord(
        id=4,
        job_id="job-evt-001",
        story_number="STRY0010013",
        artifact_kind="implementation_candidate",
        schema_version="implementation-candidate-v1",
        payload_json={
            "safe_url": "https://docs.example.gov/path?sysparm_limit=1",
            "diagnostic": (
                "provider called https://api-user:url-secret@example.service-now.com/api"
                "?access_token=token-secret"
            ),
            "provider_response": {
                "client_secret": "client-secret-value",
                "notes": ["Authorization: Bearer bearer-secret"],
            },
        },
        sha256="e" * 64,
        created_at=datetime(2026, 5, 13, 15, 3, tzinfo=UTC),
    )
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/artifacts/4",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    assert response.json()["payload"] == {
        "safe_url": "https://docs.example.gov/path?sysparm_limit=1",
        "diagnostic": (
            "provider called https://***REDACTED***@example.service-now.com/api"
            "?access_token=***REDACTED***"
        ),
        "provider_response": {
            "client_secret": "***REDACTED***",
            "notes": ["Authorization: Bearer ***REDACTED***"],
        },
    }
    assert "url-secret" not in response.text
    assert "token-secret" not in response.text
    assert "client-secret-value" not in response.text
    assert "bearer-secret" not in response.text


def test_artifact_read_bounds_persisted_diagnostic_payload_strings(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-001", story_number="STRY0010013").model_copy(
            update={"correlation_id": "corr-evt-001"}
        )
    ]
    store.artifact_blob_records[5] = ArtifactBlobRecord(
        id=5,
        job_id="job-evt-001",
        story_number="STRY0010013",
        artifact_kind="implementation_candidate",
        schema_version="implementation-candidate-v1",
        payload_json={
            "diagnostic": (
                "provider called https://api-user:url-secret@example.service-now.com/api"
                "?access_token=token-secret " + ("x" * 5000)
            ),
        },
        sha256="f" * 64,
        created_at=datetime(2026, 5, 13, 15, 4, tzinfo=UTC),
    )
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/artifacts/5",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    diagnostic = response.json()["payload"]["diagnostic"]
    assert len(diagnostic) < 4300
    assert diagnostic.endswith("...[truncated]")
    assert "url-secret" not in response.text
    assert "token-secret" not in response.text


def test_artifact_read_bounds_large_persisted_payload_views(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-001", story_number="STRY0010013").model_copy(
            update={"correlation_id": "corr-evt-001"}
        )
    ]
    store.artifact_blob_records[6] = ArtifactBlobRecord(
        id=6,
        job_id="job-evt-001",
        story_number="STRY0010013",
        artifact_kind="implementation_candidate",
        schema_version="implementation-candidate-v1",
        payload_json={
            "records": [
                {
                    "index": index,
                    "diagnostic": (
                        "provider called "
                        "https://api-user:url-secret@example.service-now.com/api"
                        "?access_token=token-secret"
                    ),
                }
                for index in range(900)
            ]
        },
        sha256="0" * 64,
        created_at=datetime(2026, 5, 13, 15, 5, tzinfo=UTC),
    )
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/artifacts/6",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    assert response.json()["payload_truncated"] is True
    payload = response.json()["payload"]
    assert payload["truncated"] is True
    assert payload["original_payload_type"] == "dict"
    assert len(payload["diagnostic_preview"]) < 17000
    assert payload["diagnostic_preview"].endswith("...[truncated]")
    assert response.json()["sha256"] == "0" * 64
    assert "url-secret" not in response.text
    assert "token-secret" not in response.text


def test_artifact_read_bounds_large_payload_traversal_before_projection(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-001", story_number="STRY0010013").model_copy(
            update={"correlation_id": "corr-evt-001"}
        )
    ]
    store.artifact_blob_records[7] = ArtifactBlobRecord(
        id=7,
        job_id="job-evt-001",
        story_number="STRY0010013",
        artifact_kind="implementation_candidate",
        schema_version="implementation-candidate-v1",
        payload_json={
            "records": [{"index": index, "value": f"record-{index}"} for index in range(900)]
        },
        sha256="1" * 64,
        created_at=datetime(2026, 5, 13, 15, 6, tzinfo=UTC),
    )
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/artifacts/7",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    assert response.json()["payload_truncated"] is True
    preview = response.json()["payload"]["diagnostic_preview"]
    assert '"omitted_items": 800' in preview
    assert "record-899" not in preview
    assert response.json()["sha256"] == "1" * 64


def test_artifact_read_bounds_large_payload_object_fields_before_projection(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-001", story_number="STRY0010013").model_copy(
            update={"correlation_id": "corr-evt-001"}
        )
    ]
    store.artifact_blob_records[8] = ArtifactBlobRecord(
        id=8,
        job_id="job-evt-001",
        story_number="STRY0010013",
        artifact_kind="implementation_candidate",
        schema_version="implementation-candidate-v1",
        payload_json={f"field_{index}": f"value-{index}" for index in range(150)},
        sha256="2" * 64,
        created_at=datetime(2026, 5, 13, 15, 7, tzinfo=UTC),
    )
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/artifacts/8",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    assert response.json()["payload_truncated"] is True
    preview = response.json()["payload"]["diagnostic_preview"]
    assert '"omitted_fields": 50' in preview
    assert "field_149" not in preview
    assert response.json()["sha256"] == "2" * 64


def test_artifact_read_does_not_consume_all_fields_for_wide_payload_projection() -> None:
    payload, payload_truncated = _admin_artifact_payload_view(
        {f"field_{index}": f"value-{index}" for index in range(150)}
    )

    assert payload_truncated is True
    preview = payload["diagnostic_preview"]
    assert '"omitted_fields": 50' in preview
    assert "field_149" not in preview


def test_artifact_payload_view_rejects_container_subclasses() -> None:
    class HostileArtifactPayloadDict(dict[str, Any]):
        def items(self) -> Any:
            raise AssertionError("client_secret=admin-dict-subclass-secret")

    class HostileArtifactPayloadList(list[Any]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=admin-list-subclass-secret")

    class HostileArtifactPayloadTuple(tuple[Any, ...]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=admin-tuple-subclass-secret")

    rendered_payload, truncated = _bounded_redacted_artifact_payload(
        {
            "dict": HostileArtifactPayloadDict({"message": "hidden dict"}),
            "list": HostileArtifactPayloadList(["hidden list"]),
            "tuple": HostileArtifactPayloadTuple(("hidden tuple",)),
        }
    )

    payload_json = json.dumps(rendered_payload, sort_keys=True)
    assert truncated is False
    assert rendered_payload == {
        "dict": "[non-json value]",
        "list": "[non-json value]",
        "tuple": "[non-json value]",
    }
    assert "hidden dict" not in payload_json
    assert "hidden list" not in payload_json
    assert "hidden tuple" not in payload_json


def test_artifact_read_redacts_and_normalizes_untrusted_payload_keys(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-001", story_number="STRY0010013").model_copy(
            update={"correlation_id": "corr-evt-001"}
        )
    ]
    store.artifact_blob_records[9] = ArtifactBlobRecord(
        id=9,
        job_id="job-evt-001",
        story_number="STRY0010013",
        artifact_kind="implementation_candidate",
        schema_version="implementation-candidate-v1",
        payload_json={
            "diagnostic\nclient_secret=key-secret": "ok",
            "nested": {"api_key=nested-key-secret": "ok"},
        },
        sha256="3" * 64,
        created_at=datetime(2026, 5, 13, 15, 8, tzinfo=UTC),
    )
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/artifacts/9",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    payload_json = json.dumps(response.json()["payload"], sort_keys=True)
    assert "key-secret" not in payload_json
    assert "nested-key-secret" not in payload_json
    assert "diagnostic client_secret=***REDACTED***" in payload_json
    assert "api_key=***REDACTED***" in payload_json


def test_artifact_read_bounds_untrusted_payload_keys(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-001", story_number="STRY0010013").model_copy(
            update={"correlation_id": "corr-evt-001"}
        )
    ]
    store.artifact_blob_records[10] = ArtifactBlobRecord(
        id=10,
        job_id="job-evt-001",
        story_number="STRY0010013",
        artifact_kind="implementation_candidate",
        schema_version="implementation-candidate-v1",
        payload_json={f"diagnostic {'A' * 2200}": "ok"},
        sha256="4" * 64,
        created_at=datetime(2026, 5, 13, 15, 9, tzinfo=UTC),
    )
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/artifacts/10",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    payload_json = json.dumps(response.json()["payload"], sort_keys=True)
    assert "...[truncated]" in payload_json
    assert len(payload_json) < 800


def test_artifact_read_bounds_duplicate_sanitized_payload_keys(tmp_path: Path) -> None:
    first_key = f"diagnostic {'A' * 2200}"
    second_key = f"diagnostic {'A' * 2199}B"
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-001", story_number="STRY0010013").model_copy(
            update={"correlation_id": "corr-evt-001"}
        )
    ]
    store.artifact_blob_records[11] = ArtifactBlobRecord(
        id=11,
        job_id="job-evt-001",
        story_number="STRY0010013",
        artifact_kind="implementation_candidate",
        schema_version="implementation-candidate-v1",
        payload_json={first_key: "first", second_key: "second"},
        sha256="5" * 64,
        created_at=datetime(2026, 5, 13, 15, 10, tzinfo=UTC),
    )
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/artifacts/11",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    payload = response.json()["payload"]
    keys = list(payload)
    assert len(keys) == 2
    assert all(len(key) <= 500 for key in keys)
    assert keys[0].endswith("...[truncated]")
    assert keys[1].endswith("[duplicate 2]")


def test_artifact_read_replaces_empty_sanitized_payload_keys(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-001", story_number="STRY0010013").model_copy(
            update={"correlation_id": "corr-evt-001"}
        )
    ]
    store.artifact_blob_records[12] = ArtifactBlobRecord(
        id=12,
        job_id="job-evt-001",
        story_number="STRY0010013",
        artifact_kind="implementation_candidate",
        schema_version="implementation-candidate-v1",
        payload_json={"\n\t ": "first", "\r\n": "second"},
        sha256="6" * 64,
        created_at=datetime(2026, 5, 13, 15, 11, tzinfo=UTC),
    )
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/artifacts/12",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    payload = response.json()["payload"]
    assert "" not in payload
    assert payload["[empty key]"] == "first"
    assert payload["[empty key] [duplicate 2]"] == "second"


def test_artifact_payload_projection_replaces_non_string_payload_keys() -> None:
    object_key = object()

    rendered_payload, truncated = _bounded_redacted_artifact_payload(
        {
            ("client_secret=tuple-secret",): "tuple value",
            object_key: "object value",
        }
    )

    payload_json = json.dumps(rendered_payload, sort_keys=True)
    assert truncated is False
    assert isinstance(rendered_payload, dict)
    assert rendered_payload == {
        "[non-string key]": "tuple value",
        "[non-string key] [duplicate 2]": "object value",
    }
    assert "tuple-secret" not in payload_json
    assert "<object object at" not in payload_json


class UnstringifiableArtifactPayloadKey:
    def __str__(self) -> str:
        raise ValueError("client_secret=key-secret")


def test_artifact_payload_projection_handles_unstringifiable_payload_keys() -> None:
    rendered_payload, truncated = _bounded_redacted_artifact_payload(
        {UnstringifiableArtifactPayloadKey(): "visible diagnostic"}
    )

    assert truncated is False
    assert rendered_payload == {"[non-string key]": "visible diagnostic"}


def test_artifact_payload_projection_rejects_string_subclass_payload_keys() -> None:
    class HostileArtifactPayloadKey(str):
        def split(self, *args: object, **kwargs: object) -> list[str]:
            raise AssertionError("client_secret=admin-key-subclass-secret")

    rendered_payload, truncated = _bounded_redacted_artifact_payload(
        {HostileArtifactPayloadKey("client_secret=key-payload"): "visible diagnostic"}
    )

    payload_json = json.dumps(rendered_payload, sort_keys=True)
    assert truncated is False
    assert rendered_payload == {"[non-string key]": "visible diagnostic"}
    assert "key-payload" not in payload_json


def test_artifact_payload_projection_skips_sensitive_check_for_key_subclasses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class HostileArtifactPayloadKey(str):
        pass

    def reject_subclass_key(key: object) -> bool:
        assert type(key) is str
        return False

    monkeypatch.setattr(admin_routes, "is_sensitive_key", reject_subclass_key)

    rendered_payload, truncated = _bounded_redacted_artifact_payload(
        {HostileArtifactPayloadKey("client_secret=key-payload"): "visible diagnostic"}
    )

    assert truncated is False
    assert rendered_payload == {"[non-string key]": "visible diagnostic"}


def test_artifact_payload_view_replaces_non_json_scalar_values() -> None:
    rendered_payload, truncated = _admin_artifact_payload_view(
        {
            "object_value": object(),
            "bytes_value": b"client_secret=bytes-secret",
            "safe_value": "visible diagnostic",
        }
    )

    payload_json = json.dumps(rendered_payload, sort_keys=True)
    assert truncated is False
    assert rendered_payload == {
        "bytes_value": "[non-json value]",
        "object_value": "[non-json value]",
        "safe_value": "visible diagnostic",
    }
    assert "bytes-secret" not in payload_json
    assert "<object object at" not in payload_json


def test_artifact_payload_view_rejects_scalar_subclass_values() -> None:
    class HostileArtifactText(str):
        def split(self, *args: object, **kwargs: object) -> list[str]:
            raise AssertionError("client_secret=admin-string-subclass-secret")

    class HostileArtifactOrder(int):
        def __str__(self) -> str:
            raise AssertionError("client_secret=admin-scalar-subclass-secret")

    rendered_payload, truncated = _admin_artifact_payload_view(
        {
            "text_value": HostileArtifactText("client_secret=text-payload"),
            "order_value": HostileArtifactOrder(3),
        }
    )

    payload_json = json.dumps(rendered_payload, sort_keys=True)
    assert truncated is False
    assert rendered_payload == {
        "order_value": "[non-json value]",
        "text_value": "[non-json value]",
    }
    assert "text-payload" not in payload_json


def test_admin_artifact_payload_json_rejects_non_finite_payload_without_leak() -> None:
    with pytest.raises(ValueError) as exc_info:
        _admin_artifact_payload_json(
            {
                "risk_score": float("nan"),
                "operator_feedback": "client_secret=do-not-echo-this",
            }
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "admin artifact payload diagnostic contains non-finite numeric values"
    assert exc_info.value.__cause__ is None
    assert "risk_score" not in diagnostic
    assert "NaN" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "do-not-echo-this" not in diagnostic


def test_artifact_payload_projection_replaces_circular_references() -> None:
    cyclic_payload: dict[str, Any] = {"safe_value": "visible diagnostic"}
    cyclic_payload["self"] = cyclic_payload

    rendered_payload, truncated = _bounded_redacted_artifact_payload(cyclic_payload)

    assert truncated is True
    assert rendered_payload == {
        "safe_value": "visible diagnostic",
        "self": "[circular reference]",
    }


def test_artifact_payload_projection_bounds_excessive_depth() -> None:
    payload: dict[str, Any] = {"leaf": "visible diagnostic"}
    for depth in range(40):
        payload = {f"level_{depth}": payload}

    rendered_payload, truncated = _bounded_redacted_artifact_payload(payload)

    assert truncated is True
    cursor: Any = rendered_payload
    for depth in range(39, 7, -1):
        cursor = cursor[f"level_{depth}"]
    assert cursor == "[max depth exceeded]"


def test_artifact_payload_projection_preserves_user_truncation_marker_key() -> None:
    payload = {
        "__jedi_payload_truncated__": "operator supplied value",
        **{f"field_{index}": f"value-{index}" for index in range(150)},
    }

    rendered_payload, truncated = _bounded_redacted_artifact_payload(payload)

    assert truncated is True
    assert isinstance(rendered_payload, dict)
    assert rendered_payload["__jedi_payload_truncated__"] == "operator supplied value"
    assert rendered_payload["__jedi_payload_truncated__ [duplicate 2]"] == {
        "truncated": True,
        "omitted_fields": 51,
    }


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
    store.fulfillment_job_records = [
        _job(event_id="evt-001", story_number="STRY0010013").model_copy(
            update={"correlation_id": "corr-evt-001"}
        )
    ]
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
        "event_id": "evt-001",
        "story_number": "STRY0010013",
        "correlation_id": "corr-evt-001",
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


def test_job_artifacts_rejects_oversized_job_id_before_store_lookup(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        f"/jobs/{'j' * 257}/artifacts",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid job id"
    assert store.get_job_ids == []


def test_job_events_rejects_control_character_job_id_before_store_lookup(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/jobs/job-%0aevt/events",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid job id"
    assert store.get_job_ids == []


def test_job_artifacts_redacts_sensitive_reference_paths(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-001", story_number="STRY0010013").model_copy(
            update={"correlation_id": "corr-evt-001"}
        )
    ]
    store.artifact_ref_records["job-evt-001"] = [
        ArtifactRefRecord(
            id=4,
            job_id="job-evt-001",
            artifact_kind="implementation_candidate",
            path=(
                "https://api-user:url-secret@example.service-now.com/artifact"
                "?client_secret=query-secret"
            ),
            sha256="d" * 64,
            artifact_id=None,
            created_at=datetime(2026, 5, 13, 15, 3, tzinfo=UTC),
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
    assert response.json()["artifacts"][0]["path"] == (
        "https://***REDACTED***@example.service-now.com/artifact?client_secret=***REDACTED***"
    )
    assert "url-secret" not in response.text
    assert "query-secret" not in response.text


def test_job_artifacts_returns_404_for_missing_job(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/jobs/job-missing/artifacts",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "job not found"


def test_job_events_returns_correlation_metadata_and_redacted_messages(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-001", story_number="STRY0010013").model_copy(
            update={"correlation_id": "corr-evt-001"}
        )
    ]
    store.job_event_records["job-evt-001"] = [
        JobEventRecord(
            id=1,
            job_id="job-evt-001",
            status="running",
            message=(
                "Worker called https://api-user:url-secret@example.service-now.com/api"
                "?access_token=token-secret"
            ),
            created_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
        )
    ]
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/jobs/job-evt-001/events",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "job_id": "job-evt-001",
        "event_id": "evt-001",
        "story_number": "STRY0010013",
        "correlation_id": "corr-evt-001",
        "events": [
            {
                "id": 1,
                "job_id": "job-evt-001",
                "status": "running",
                "message": (
                    "Worker called "
                    "https://***REDACTED***@example.service-now.com/api"
                    "?access_token=***REDACTED***"
                ),
                "created_at": "2026-05-13T15:00:00Z",
            }
        ],
    }
    assert "url-secret" not in response.text
    assert "token-secret" not in response.text


def test_job_events_bound_persisted_diagnostic_messages(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-001", story_number="STRY0010013").model_copy(
            update={"correlation_id": "corr-evt-001"}
        )
    ]
    store.job_event_records["job-evt-001"] = [
        JobEventRecord(
            id=1,
            job_id="job-evt-001",
            status="failed",
            message=(
                "Worker called https://api-user:url-secret@example.service-now.com/api"
                "?access_token=token-secret " + ("x" * 5000)
            ),
            created_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
        )
    ]
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/jobs/job-evt-001/events",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    message = response.json()["events"][0]["message"]
    assert len(message) < 4300
    assert message.endswith("...[truncated]")
    assert "url-secret" not in response.text
    assert "token-secret" not in response.text


def test_job_events_returns_404_for_missing_job(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/jobs/job-missing/events",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "job not found"


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


def test_admin_json_endpoint_rejects_oversized_request_body_before_store_access(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    settings = _settings_with_admin_token(tmp_path).model_copy(update={"admin_max_body_bytes": 8})
    client = TestClient(
        create_runtime_api(
            settings=settings,
            store_factory=lambda _database_url: store,
        )
    )

    response = client.request(
        "GET",
        "/admin/jobs",
        headers={"Authorization": "Bearer admin-token", "Content-Length": "9"},
        content=b"x" * 9,
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "admin request payload is too large"
    assert store.fulfillment_job_limits == []


def test_admin_query_validation_error_does_not_echo_rejected_input(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin/jobs?limit=client_secret=super-secret")

    assert response.status_code == 422
    body = response.text
    assert "int_parsing" in body
    assert "client_secret" not in body
    assert "super-secret" not in body
    assert '"input"' not in body
    assert store.fulfillment_job_limits == []


def test_admin_request_size_error_rejects_oversized_stream_without_content_length() -> None:
    request = FakeAdminStreamingRequest(chunks=[b"x" * 8, b"y"])

    result = asyncio.run(_admin_request_size_error(request=request, max_request_body_bytes=8))

    assert result is not None
    assert result.status_code == 413
    assert b"admin request payload is too large" in result.body


def test_admin_artifact_endpoint_rejects_oversized_request_body_before_store_access(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    settings = _settings_with_admin_token(tmp_path).model_copy(update={"admin_max_body_bytes": 8})
    client = TestClient(
        create_runtime_api(
            settings=settings,
            store_factory=lambda _database_url: store,
        )
    )

    response = client.request(
        "GET",
        "/artifacts/1",
        headers={"Authorization": "Bearer admin-token", "Content-Length": "9"},
        content=b"x" * 9,
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "admin request payload is too large"


def test_admin_lifecycle_events_caps_excessive_limits(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/admin/lifecycle-events?limit=100000",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    assert response.json() == {"events": []}
    assert store.lifecycle_event_limits == [100]


@pytest.mark.parametrize(
    ("endpoint", "store_limit_attr"),
    [
        ("/admin/lifecycle-events", "lifecycle_event_limits"),
        ("/admin/jobs", "fulfillment_job_limits"),
        ("/admin/alerts", "fulfillment_job_limits"),
    ],
)
@pytest.mark.parametrize("limit", [0, -1])
def test_admin_list_endpoints_reject_non_positive_limits_before_store_access(
    tmp_path: Path,
    endpoint: str,
    store_limit_attr: str,
    limit: int,
) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        f"{endpoint}?limit={limit}",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "admin result limit must be a positive integer"
    assert getattr(store, store_limit_attr) == []


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


def test_admin_operations_returns_db_backed_fulfillment_summary(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_status_summary_record = FulfillmentJobStatusSummaryRecord(
        queued=4,
        running=2,
        completed=10,
        failed=1,
        rejected=3,
        stale_running=1,
        total=20,
    )
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path).model_copy(
                update={"running_job_stale_after_seconds": 900}
            ),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/admin/operations",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "fulfillment_jobs": {
            "queued": 4,
            "running": 2,
            "completed": 10,
            "failed": 1,
            "rejected": 3,
            "stale_running": 1,
            "total": 20,
        },
        "running_job_stale_after_seconds": 900,
    }
    assert len(store.fulfillment_job_status_summary_stale_before) == 1
    assert store.fulfillment_job_limits == []


def test_admin_jobs_rate_limits_repeated_requests(tmp_path: Path) -> None:
    now = [1000.0]
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
            admin_rate_limiter=InMemoryRateLimiter(
                max_requests=2,
                window_seconds=60,
                clock=lambda: now[0],
            ),
        )
    )
    headers = {"Authorization": "Bearer admin-token"}

    assert client.get("/admin/jobs", headers=headers).status_code == 200
    assert client.get("/admin/jobs", headers=headers).status_code == 200
    response = client.get("/admin/jobs", headers=headers)

    assert response.status_code == 429
    assert response.json()["detail"] == "rate limit exceeded"


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
def test_admin_rate_limit_rejects_malformed_limiter_decisions(
    decision: object,
) -> None:
    class MalformedLimiter:
        def check(self, _key: str) -> object:
            return decision

    with pytest.raises(HTTPException) as exc_info:
        runtime_auth._require_admin_rate_limit(
            admin_rate_limiter=cast(InMemoryRateLimiter, MalformedLimiter()),
            key="jobs",
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "admin rate limiter is invalid"


def test_admin_jobs_uses_runtime_rate_limit_settings(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    settings = _settings_with_admin_token(tmp_path).model_copy(
        update={
            "admin_rate_limit_max_requests": 1,
            "admin_rate_limit_window_seconds": 60,
        }
    )
    client = TestClient(
        create_runtime_api(
            settings=settings,
            store_factory=lambda _database_url: store,
        )
    )
    headers = {"Authorization": "Bearer admin-token"}

    assert client.get("/admin/jobs", headers=headers).status_code == 200
    response = client.get("/admin/jobs", headers=headers)

    assert response.status_code == 429
    assert response.json()["detail"] == "rate limit exceeded"


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("lifecycle_rate_limit_max_requests", 0),
        ("lifecycle_rate_limit_window_seconds", 0),
        ("lifecycle_rate_limit_max_buckets", 0),
        ("admin_rate_limit_max_requests", 0),
        ("admin_rate_limit_window_seconds", 0),
        ("admin_rate_limit_max_buckets", 0),
    ],
)
def test_runtime_api_rejects_non_positive_rate_limit_settings_before_serving(
    tmp_path: Path,
    field_name: str,
    field_value: int,
) -> None:
    settings = _settings_with_admin_token(tmp_path).model_copy(
        update={field_name: field_value}
    )

    with pytest.raises(RuntimeConfigError, match=field_name.upper()):
        create_runtime_api(
            settings=settings,
            store_factory=lambda _database_url: FakeRuntimeStore(),
        )


def test_admin_rate_limiter_uses_runtime_bucket_cap(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    settings = _settings_with_admin_token(tmp_path).model_copy(
        update={
            "admin_rate_limit_max_requests": 1,
            "admin_rate_limit_window_seconds": 60,
            "admin_rate_limit_max_buckets": 1,
        }
    )
    client = TestClient(
        create_runtime_api(
            settings=settings,
            store_factory=lambda _database_url: store,
        )
    )
    headers = {"Authorization": "Bearer admin-token"}

    assert client.get("/admin/jobs", headers=headers).status_code == 200
    assert client.get("/admin/lifecycle-events", headers=headers).status_code == 200
    response = client.get("/admin/alerts", headers=headers)

    assert response.status_code == 429
    assert response.json()["detail"] == "rate limit exceeded"


def test_admin_json_diagnostics_are_not_cacheable_and_disable_sniffing(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
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
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_admin_console_diagnostics_are_not_cacheable_and_disable_sniffing(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_console(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin", auth=("console-admin", "console-password"))

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_admin_console_artifact_diagnostics_are_not_cacheable_and_disable_sniffing(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    store.artifact_blob_records[3] = ArtifactBlobRecord(
        id=3,
        job_id="job-evt-001",
        story_number="STRY0010013",
        artifact_kind="implementation_candidate",
        schema_version="implementation-candidate-v1",
        payload_json={"candidate": {"status": "ready"}},
        sha256="c" * 64,
        created_at=datetime(2026, 5, 13, 16, 0, tzinfo=UTC),
    )
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_console(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/admin/artifacts/3",
        auth=("console-admin", "console-password"),
    )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_admin_console_html_uses_restrictive_browser_security_headers(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_console(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin", auth=("console-admin", "console-password"))

    assert response.status_code == 200
    assert response.headers["Content-Security-Policy"] == (
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
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_admin_console_artifact_html_uses_restrictive_browser_security_headers(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    store.artifact_blob_records[3] = ArtifactBlobRecord(
        id=3,
        job_id="job-evt-001",
        story_number="STRY0010013",
        artifact_kind="implementation_candidate",
        schema_version="implementation-candidate-v1",
        payload_json={"candidate": {"status": "ready"}},
        sha256="c" * 64,
        created_at=datetime(2026, 5, 13, 16, 0, tzinfo=UTC),
    )
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_console(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/admin/artifacts/3",
        auth=("console-admin", "console-password"),
    )

    assert response.status_code == 200
    assert "default-src 'none'" in response.headers["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_admin_console_html_disables_browser_capabilities(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_console(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin", auth=("console-admin", "console-password"))

    assert response.status_code == 200
    assert response.headers["Permissions-Policy"] == (
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


def test_admin_console_artifact_html_disables_browser_capabilities(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    store.artifact_blob_records[3] = ArtifactBlobRecord(
        id=3,
        job_id="job-evt-001",
        story_number="STRY0010013",
        artifact_kind="implementation_candidate",
        schema_version="implementation-candidate-v1",
        payload_json={"candidate": {"status": "ready"}},
        sha256="c" * 64,
        created_at=datetime(2026, 5, 13, 16, 0, tzinfo=UTC),
    )
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_console(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/admin/artifacts/3",
        auth=("console-admin", "console-password"),
    )

    assert response.status_code == 200
    assert "camera=()" in response.headers["Permissions-Policy"]
    assert "microphone=()" in response.headers["Permissions-Policy"]
    assert "geolocation=()" in response.headers["Permissions-Policy"]


def test_admin_json_diagnostics_do_not_receive_html_csp(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
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
    assert "Content-Security-Policy" not in response.headers
    assert "X-Frame-Options" not in response.headers
    assert "Referrer-Policy" not in response.headers
    assert "Permissions-Policy" not in response.headers


def test_liveness_disables_sniffing_without_forcing_no_store(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "Cache-Control" not in response.headers
    assert "Pragma" not in response.headers


def test_runtime_does_not_emit_hsts_by_default(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert "Strict-Transport-Security" not in response.headers


def test_runtime_emits_hsts_when_enabled(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    settings = _settings_with_admin_token(tmp_path).model_copy(
        update={"strict_transport_security_enabled": True}
    )
    client = TestClient(
        create_runtime_api(
            settings=settings,
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["Strict-Transport-Security"] == ("max-age=31536000; includeSubDomains")


def test_runtime_hsts_uses_configured_max_age(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    settings = _settings_with_admin_token(tmp_path).model_copy(
        update={
            "strict_transport_security_enabled": True,
            "strict_transport_security_max_age_seconds": 63072000,
        }
    )
    client = TestClient(
        create_runtime_api(
            settings=settings,
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["Strict-Transport-Security"] == ("max-age=63072000; includeSubDomains")


def test_admin_json_diagnostics_vary_by_authorization(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
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
    assert response.headers["Vary"] == "Authorization"


def test_admin_console_diagnostics_vary_by_authorization(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_console(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin", auth=("console-admin", "console-password"))

    assert response.status_code == 200
    assert response.headers["Vary"] == "Authorization"


def test_admin_bearer_auth_failure_is_not_cacheable(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin/jobs")

    assert response.status_code == 401
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["Expires"] == "0"
    assert response.headers["Vary"] == "Authorization"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_admin_basic_auth_failure_is_not_cacheable(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_console(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin")

    assert response.status_code == 401
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["Expires"] == "0"
    assert response.headers["Vary"] == "Authorization"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["WWW-Authenticate"] == 'Basic realm="jedi-admin"'


def test_basic_auth_decoder_rejects_oversized_payload_before_decode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_decode(*_args: object, **_kwargs: object) -> bytes:
        raise AssertionError("oversized Basic auth payload should not be decoded")

    monkeypatch.setattr("jedi_devproject.runtime_auth.base64.b64decode", fail_decode)

    assert runtime_auth._basic_auth_credentials("Basic " + ("A" * 8193)) is None


def test_basic_auth_decoder_rejects_padded_payload_before_decode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_decode(*_args: object, **_kwargs: object) -> bytes:
        raise AssertionError("padded Basic auth payload should not be decoded")

    monkeypatch.setattr("jedi_devproject.runtime_auth.base64.b64decode", fail_decode)

    assert runtime_auth._basic_auth_credentials("Basic dXNlcjpwYXNz ") is None
    assert runtime_auth._basic_auth_credentials("Basic  dXNlcjpwYXNz") is None


def test_basic_auth_decoder_rejects_non_ascii_payload_before_decode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_decode(*_args: object, **_kwargs: object) -> bytes:
        raise AssertionError("non-ASCII Basic auth payload should not be decoded")

    monkeypatch.setattr("jedi_devproject.runtime_auth.base64.b64decode", fail_decode)

    assert runtime_auth._basic_auth_credentials("Basic dXNlcjpwYXNzé") is None


@pytest.mark.parametrize(
    "decoded_credentials",
    [
        " console-admin:console-password",
        "console-admin :console-password",
        "console-admin: console-password",
        "console-admin:console-password\t",
    ],
)
def test_admin_basic_auth_rejects_padded_decoded_credentials_before_compare(
    decoded_credentials: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fail_compare(*_args: object, **_kwargs: object) -> bool:
        raise AssertionError("padded decoded Basic auth credentials should not be compared")

    monkeypatch.setattr("jedi_devproject.runtime_auth.secrets.compare_digest", fail_compare)
    encoded = base64.b64encode(decoded_credentials.encode("utf-8")).decode("ascii")

    with pytest.raises(HTTPException) as exc_info:
        runtime_auth._require_admin_console_credentials(
            settings=_settings_with_admin_console(tmp_path),
            authorization=f"Basic {encoded}",
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "admin console credentials required"


def test_admin_console_rejects_auth_mode_subclass_before_equality(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class SecretBearingAdminAuthMode(str):
        def __eq__(self, _other: object) -> bool:
            raise AssertionError("client_secret=runtime-auth-mode-secret")

    def fail_decode(*_args: object, **_kwargs: object) -> bytes:
        raise AssertionError("malformed configured auth mode should fail before decode")

    monkeypatch.setattr("jedi_devproject.runtime_auth.base64.b64decode", fail_decode)
    encoded = base64.b64encode(b"console-admin:console-password").decode("ascii")

    with pytest.raises(HTTPException) as exc_info:
        runtime_auth._require_admin_console_credentials(
            settings=_settings_with_admin_console(tmp_path).model_copy(
                update={"admin_auth_mode": SecretBearingAdminAuthMode("dev_basic")}
            ),
            authorization=f"Basic {encoded}",
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "admin console configuration is invalid"


def test_admin_console_rejects_password_subclass_before_compare(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class SecretBearingAdminPassword(str):
        def __len__(self) -> int:
            raise AssertionError("client_secret=runtime-admin-password-secret")

    def fail_compare(*_args: object, **_kwargs: object) -> bool:
        raise AssertionError("malformed configured console password should not be compared")

    monkeypatch.setattr("jedi_devproject.runtime_auth.secrets.compare_digest", fail_compare)
    encoded = base64.b64encode(b"console-admin:console-password").decode("ascii")

    with pytest.raises(HTTPException) as exc_info:
        runtime_auth._require_admin_console_credentials(
            settings=_settings_with_admin_console(tmp_path).model_copy(
                update={"admin_console_password": SecretBearingAdminPassword("console-password")}
            ),
            authorization=f"Basic {encoded}",
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "admin console configuration is invalid"


@pytest.mark.parametrize(
    ("configured_field", "configured_value"),
    [
        ("admin_console_username", " console-admin"),
        ("admin_console_username", "console-admin\n"),
        ("admin_console_username", "console-admin-é"),
        ("admin_console_username", "x" * (runtime_auth.MAX_BASIC_AUTH_ENCODED_BYTES + 1)),
        ("admin_console_password", " console-password"),
        ("admin_console_password", "console-password\n"),
        ("admin_console_password", "console-password-é"),
        ("admin_console_password", "x" * (runtime_auth.MAX_BASIC_AUTH_ENCODED_BYTES + 1)),
    ],
)
def test_admin_console_rejects_malformed_configured_credentials_before_decode(
    configured_field: str,
    configured_value: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fail_decode(*_args: object, **_kwargs: object) -> bytes:
        raise AssertionError("malformed configured console credentials should fail before decode")

    def fail_compare(*_args: object, **_kwargs: object) -> bool:
        raise AssertionError("malformed configured console credentials should not be compared")

    monkeypatch.setattr("jedi_devproject.runtime_auth.base64.b64decode", fail_decode)
    monkeypatch.setattr("jedi_devproject.runtime_auth.secrets.compare_digest", fail_compare)
    encoded = base64.b64encode(b"console-admin:console-password").decode("ascii")

    with pytest.raises(HTTPException) as exc_info:
        runtime_auth._require_admin_console_credentials(
            settings=_settings_with_admin_console(tmp_path).model_copy(
                update={configured_field: configured_value}
            ),
            authorization=f"Basic {encoded}",
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "admin console credentials are invalid"


def test_admin_console_rejects_padded_development_environment_before_auth(
    tmp_path: Path,
) -> None:
    encoded = base64.b64encode(b"console-admin:console-password").decode("ascii")

    with pytest.raises(HTTPException) as exc_info:
        runtime_auth._require_admin_console_credentials(
            settings=_settings_with_admin_console(tmp_path).model_copy(
                update={"runtime_environment": " development "}
            ),
            authorization=f"Basic {encoded}",
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "dev_basic admin auth is development-only"


def test_admin_bearer_token_rejects_oversized_token_before_compare(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fail_compare(*_args: object, **_kwargs: object) -> bool:
        raise AssertionError("oversized Bearer token should not be compared")

    monkeypatch.setattr("jedi_devproject.runtime_auth.secrets.compare_digest", fail_compare)

    with pytest.raises(HTTPException) as exc_info:
        runtime_auth._require_admin_token(
            settings=_settings_with_admin_token(tmp_path),
            authorization="Bearer " + ("x" * 8193),
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "admin bearer token rejected"


def test_admin_bearer_token_rejects_padded_token_before_compare(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fail_compare(*_args: object, **_kwargs: object) -> bool:
        raise AssertionError("padded Bearer token should not be compared")

    monkeypatch.setattr("jedi_devproject.runtime_auth.secrets.compare_digest", fail_compare)

    for authorization in ("Bearer admin-token ", "Bearer  admin-token"):
        with pytest.raises(HTTPException) as exc_info:
            runtime_auth._require_admin_token(
                settings=_settings_with_admin_token(tmp_path),
                authorization=authorization,
            )

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "admin bearer token rejected"


def test_admin_bearer_token_rejects_configured_token_subclass_before_compare(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class SecretBearingAdminToken(str):
        def __len__(self) -> int:
            raise AssertionError("client_secret=runtime-admin-token-secret")

    def fail_compare(*_args: object, **_kwargs: object) -> bool:
        raise AssertionError("malformed configured admin token should not be compared")

    monkeypatch.setattr("jedi_devproject.runtime_auth.secrets.compare_digest", fail_compare)

    with pytest.raises(HTTPException) as exc_info:
        runtime_auth._require_admin_token(
            settings=_settings_with_admin_token(tmp_path).model_copy(
                update={"admin_api_token": SecretBearingAdminToken("admin-token")}
            ),
            authorization="Bearer admin-token",
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "admin artifact API token is invalid"


@pytest.mark.parametrize(
    "configured_token",
    [
        " admin-token",
        "admin-token\n",
        "admin-token-é",
        "x" * (runtime_auth.MAX_ADMIN_BEARER_TOKEN_BYTES + 1),
    ],
)
def test_admin_bearer_token_rejects_malformed_configured_token_before_compare(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    configured_token: str,
) -> None:
    def fail_compare(*_args: object, **_kwargs: object) -> bool:
        raise AssertionError("malformed configured admin token should not be compared")

    monkeypatch.setattr("jedi_devproject.runtime_auth.secrets.compare_digest", fail_compare)

    with pytest.raises(HTTPException) as exc_info:
        runtime_auth._require_admin_token(
            settings=_settings_with_admin_token(tmp_path).model_copy(
                update={"admin_api_token": configured_token}
            ),
            authorization="Bearer admin-token",
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "admin artifact API token is invalid"


def test_admin_json_diagnostics_disable_robot_indexing(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
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
    assert response.headers["X-Robots-Tag"] == "noindex, nofollow, noarchive"


def test_admin_console_disables_robot_indexing(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_console(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin", auth=("console-admin", "console-password"))

    assert response.status_code == 200
    assert response.headers["X-Robots-Tag"] == "noindex, nofollow, noarchive"


def test_liveness_does_not_emit_robot_indexing_policy(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert "X-Robots-Tag" not in response.headers


def test_runtime_api_trusted_hosts_rejects_unlisted_host(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    settings = _settings_with_admin_token(tmp_path).model_copy(
        update={"trusted_hosts": ["api.example.gov"]}
    )
    client = TestClient(
        create_runtime_api(
            settings=settings,
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/health", headers={"Host": "attacker.example.net"})

    assert response.status_code == 400
    assert response.text == "Invalid host header"


def test_runtime_api_trusted_hosts_allows_listed_host(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    settings = _settings_with_admin_token(tmp_path).model_copy(
        update={"trusted_hosts": ["api.example.gov"]}
    )
    client = TestClient(
        create_runtime_api(
            settings=settings,
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/health", headers={"Host": "api.example.gov"})

    assert response.status_code == 200


def test_runtime_generates_request_id_header_when_absent(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert UUID(response.headers["X-JEDI-Request-ID"]).version == 4


def test_runtime_preserves_safe_inbound_request_id(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/admin/jobs",
        headers={
            "Authorization": "Bearer admin-token",
            "X-Request-ID": "edge-request-01",
        },
    )

    assert response.status_code == 200
    assert response.headers["X-JEDI-Request-ID"] == "edge-request-01"


def test_runtime_replaces_sensitive_inbound_request_id(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/health",
        headers={"X-Request-ID": "client_secret=header-secret"},
    )

    assert response.status_code == 200
    assert response.headers["X-JEDI-Request-ID"] != "client_secret=header-secret"
    assert "header-secret" not in response.headers["X-JEDI-Request-ID"]
    assert UUID(response.headers["X-JEDI-Request-ID"]).version == 4


def test_runtime_replaces_whitespace_inbound_request_id(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/health", headers={"X-Request-ID": "edge request 01"})

    assert response.status_code == 200
    assert response.headers["X-JEDI-Request-ID"] != "edge request 01"
    assert UUID(response.headers["X-JEDI-Request-ID"]).version == 4


def test_runtime_replaces_non_ascii_inbound_request_id() -> None:
    assert _safe_request_id("edge-requête-01") is False


def test_runtime_replaces_overlong_inbound_request_id(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/health", headers={"X-Request-ID": "x" * 129})

    assert response.status_code == 200
    assert response.headers["X-JEDI-Request-ID"] != "x" * 129
    assert UUID(response.headers["X-JEDI-Request-ID"]).version == 4


def test_liveness_does_not_vary_by_authorization(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert "Vary" not in response.headers


def test_admin_console_rate_limits_repeated_requests(tmp_path: Path) -> None:
    now = [1000.0]
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_console(tmp_path),
            store_factory=lambda _database_url: store,
            admin_rate_limiter=InMemoryRateLimiter(
                max_requests=1,
                window_seconds=60,
                clock=lambda: now[0],
            ),
        )
    )

    assert client.get("/admin", auth=("console-admin", "console-password")).status_code == 200
    response = client.get("/admin", auth=("console-admin", "console-password"))

    assert response.status_code == 429
    assert response.json()["detail"] == "rate limit exceeded"
    assert response.headers["Retry-After"] == "60"


def test_admin_console_artifact_view_rate_limits_repeated_requests(tmp_path: Path) -> None:
    now = [1000.0]
    store = FakeRuntimeStore()
    store.artifact_blob_records[3] = ArtifactBlobRecord(
        id=3,
        job_id="job-evt-001",
        story_number="STRY0010013",
        artifact_kind="implementation_candidate",
        schema_version="implementation-candidate-v1",
        payload_json={"candidate": {"status": "ready"}},
        sha256="c" * 64,
        created_at=datetime(2026, 5, 13, 16, 0, tzinfo=UTC),
    )
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_console(tmp_path),
            store_factory=lambda _database_url: store,
            admin_rate_limiter=InMemoryRateLimiter(
                max_requests=1,
                window_seconds=60,
                clock=lambda: now[0],
            ),
        )
    )

    assert (
        client.get(
            "/admin/artifacts/3",
            auth=("console-admin", "console-password"),
        ).status_code
        == 200
    )
    response = client.get("/admin/artifacts/3", auth=("console-admin", "console-password"))

    assert response.status_code == 429
    assert response.json()["detail"] == "rate limit exceeded"
    assert response.headers["Retry-After"] == "60"


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


def test_admin_jobs_redacts_generic_url_credentials_and_sensitive_query_values(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-002", story_number="STRY0010002").model_copy(
            update={
                "status": "failed",
                "last_error": (
                    "request failed for "
                    "https://api-user:url-secret@example.service-now.com/api/now/table"
                    "?sysparm_query=number=INC001"
                    "&access_token=token-secret"
                    "&client_secret=client-secret-from-query"
                    "&signature=signature-secret"
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
    assert "url-secret" not in response.text
    assert "token-secret" not in response.text
    assert "client-secret-from-query" not in response.text
    assert "signature-secret" not in response.text
    assert "sysparm_query=number=INC001" in response.text
    assert "***REDACTED***" in response.text


def test_admin_jobs_bounds_persisted_last_error_diagnostics(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-002", story_number="STRY0010002").model_copy(
            update={
                "status": "failed",
                "last_error": (
                    "request failed for "
                    "https://api-user:url-secret@example.service-now.com/api"
                    "?access_token=token-secret " + ("x" * 5000)
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
    last_error = response.json()["jobs"][0]["last_error"]
    assert len(last_error) < 4300
    assert last_error.endswith("...[truncated]")
    assert "url-secret" not in response.text
    assert "token-secret" not in response.text


def test_admin_jobs_normalizes_persisted_last_error_diagnostics(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-002", story_number="STRY0010002").model_copy(
            update={
                "status": "failed",
                "last_error": (
                    "first line\nsecond line\tapi_key=admin-diagnostic-secret"
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
    last_error = response.json()["jobs"][0]["last_error"]
    assert last_error == "first line second line api_key=***REDACTED***"
    assert "\n" not in last_error
    assert "\t" not in last_error
    assert "admin-diagnostic-secret" not in response.text


def test_admin_alerts_lists_attention_jobs_with_correlation_and_redacted_details(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-failed", story_number="STRY0010100").model_copy(
            update={
                "status": "failed",
                "attempt_count": 2,
                "last_error": (
                    "ServiceNow writeback failed for "
                    "https://api-user:url-secret@example.service-now.com/api"
                    "?access_token=token-secret"
                ),
            }
        ),
        _job(event_id="evt-rejected", story_number="STRY0010101").model_copy(
            update={
                "status": "rejected",
                "last_error": "Story returned to Draft from Ready for Testing",
            }
        ),
        _job(event_id="evt-complete", story_number="STRY0010102").model_copy(
            update={"status": "completed", "last_error": None}
        ),
    ]
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/admin/alerts",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "alerts": [
            {
                "alert_id": "job-evt-failed:failed",
                "severity": "critical",
                "job_id": "job-evt-failed",
                "event_id": "evt-failed",
                "story_number": "STRY0010100",
                "correlation_id": "corr-evt-failed",
                "status": "failed",
                "attempt_count": 2,
                "updated_at": "2026-05-13T15:01:00Z",
                "summary": "Fulfillment job failed",
                "detail": (
                    "ServiceNow writeback failed for "
                    "https://***REDACTED***@example.service-now.com/api"
                    "?access_token=***REDACTED***"
                ),
                "operator_action": "Inspect job events and ServiceNow work notes",
            },
            {
                "alert_id": "job-evt-rejected:rejected",
                "severity": "warning",
                "job_id": "job-evt-rejected",
                "event_id": "evt-rejected",
                "story_number": "STRY0010101",
                "correlation_id": "corr-evt-rejected",
                "status": "rejected",
                "attempt_count": 1,
                "updated_at": "2026-05-13T15:01:00Z",
                "summary": "Fulfillment job requires review",
                "detail": "Story returned to Draft from Ready for Testing",
                "operator_action": "Inspect job events and ServiceNow work notes",
            },
        ]
    }
    assert store.fulfillment_job_limits == [50]
    assert "url-secret" not in response.text
    assert "token-secret" not in response.text
    assert "STRY0010102" not in response.text


def test_admin_alerts_include_stale_running_jobs_without_mutating_state(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    old_updated_at = datetime.now(UTC) - timedelta(seconds=901)
    fresh_updated_at = datetime.now(UTC) - timedelta(seconds=60)
    stale_job = _job(event_id="evt-stale", story_number="STRY0010103").model_copy(
        update={
            "status": "running",
            "updated_at": old_updated_at,
            "locked_at": old_updated_at,
            "locked_by": "worker-stalled",
        }
    )
    fresh_job = _job(event_id="evt-fresh", story_number="STRY0010104").model_copy(
        update={
            "status": "running",
            "updated_at": fresh_updated_at,
            "locked_at": fresh_updated_at,
            "locked_by": "worker-active",
        }
    )
    store.fulfillment_job_records = [stale_job, fresh_job]
    settings = _settings_with_admin_token(tmp_path).model_copy(
        update={"running_job_stale_after_seconds": 900}
    )
    client = TestClient(
        create_runtime_api(
            settings=settings,
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/admin/alerts",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "alerts": [
            {
                "alert_id": "job-evt-stale:running_stale",
                "severity": "warning",
                "job_id": "job-evt-stale",
                "event_id": "evt-stale",
                "story_number": "STRY0010103",
                "correlation_id": "corr-evt-stale",
                "status": "running",
                "attempt_count": 1,
                "updated_at": old_updated_at.isoformat().replace("+00:00", "Z"),
                "summary": "Fulfillment job appears stale",
                "detail": "Running job has not updated within 900 seconds",
                "operator_action": "Inspect worker logs before retrying or restarting work",
            }
        ]
    }
    assert store.failed_jobs == []
    assert store.completed_jobs == []
    assert "STRY0010104" not in response.text


def test_admin_alerts_requires_admin_bearer_token(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin/alerts")

    assert response.status_code == 401


def test_admin_alerts_caps_excessive_limits(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_token(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get(
        "/admin/alerts?limit=100000",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    assert response.json() == {"alerts": []}
    assert store.fulfillment_job_limits == [100]


def test_admin_console_redacts_sensitive_diagnostics(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-002", story_number="STRY0010002").model_copy(
            update={
                "status": "failed",
                "last_error": (
                    "connection failed for "
                    "postgresql://jedi:super-secret@db.example.invalid:5432/jedi"
                    " and https://api-user:url-secret@example.service-now.com/api"
                    "?access_token=token-secret"
                ),
            }
        )
    ]
    settings = _settings(tmp_path).model_copy(
        update={
            "admin_auth_mode": "dev_basic",
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

    assert response.status_code == 200
    assert "super-secret" not in response.text
    assert "url-secret" not in response.text
    assert "token-secret" not in response.text
    assert "***REDACTED***" in response.text


def test_admin_console_normalizes_persisted_last_error_diagnostics(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-002", story_number="STRY0010002").model_copy(
            update={
                "status": "failed",
                "last_error": (
                    "first line\nsecond line\tapi_key=admin-console-secret"
                ),
            }
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
    assert "first line second line api_key=***REDACTED***" in response.text
    assert "first line\nsecond line" not in response.text
    assert "second line\tapi_key" not in response.text
    assert "admin-console-secret" not in response.text


def test_admin_console_renders_operational_alerts(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.fulfillment_job_records = [
        _job(event_id="evt-failed", story_number="STRY0010100").model_copy(
            update={
                "status": "failed",
                "last_error": (
                    "provider error at "
                    "https://api-user:url-secret@example.service-now.com/api"
                    "?client_secret=client-secret"
                ),
            }
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
    assert "Operational Alerts" in response.text
    assert "STRY0010100" in response.text
    assert "job-evt-failed" in response.text
    assert "critical" in response.text
    assert "provider error at" in response.text
    assert "url-secret" not in response.text
    assert "client-secret" not in response.text


class HostileAdminAlertText:
    def __str__(self) -> str:
        raise ValueError("admin-alert-secret")


def test_admin_alert_row_rejects_malformed_response_text_without_leak(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def malformed_operational_alert_response(
        *_args: object,
        **_kwargs: object,
    ) -> dict[str, object]:
        return {
            "severity": HostileAdminAlertText(),
            "detail": HostileAdminAlertText(),
        }

    monkeypatch.setattr(
        "jedi_devproject.admin_routes._operational_alert_response",
        malformed_operational_alert_response,
    )

    row = _admin_alert_row(
        (_job(event_id="evt-failed").model_copy(update={"status": "failed"}), "failed"),
        running_job_stale_after_seconds=3600,
    )

    assert "admin-alert-secret" not in row
    assert "[invalid alert severity]" in row
    assert "None" in row


def test_admin_console_renders_stale_running_alerts(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    stale_updated_at = datetime.now(UTC) - timedelta(seconds=7201)
    store.fulfillment_job_records = [
        _job(event_id="evt-stale", story_number="STRY0010103").model_copy(
            update={
                "status": "running",
                "updated_at": stale_updated_at,
                "locked_at": stale_updated_at,
                "locked_by": "worker-stalled",
            }
        )
    ]
    settings = _settings_with_admin_console(tmp_path).model_copy(
        update={"running_job_stale_after_seconds": 7200}
    )
    client = TestClient(
        create_runtime_api(
            settings=settings,
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin", auth=("console-admin", "console-password"))

    assert response.status_code == 200
    assert "Operational Alerts" in response.text
    assert "job-evt-stale" in response.text
    assert "STRY0010103" in response.text
    assert "running" in response.text
    assert "Running job has not updated within 7200 seconds" in response.text


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


def test_admin_console_rejects_unsupported_auth_mode_without_echoing_value(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    settings = _settings(tmp_path).model_copy(update={"admin_auth_mode": "custom-secret-mode"})
    client = TestClient(
        create_runtime_api(
            settings=settings,
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin")

    assert response.status_code == 503
    assert response.json()["detail"] == "admin auth mode is not supported"


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


def test_admin_console_artifact_not_found_does_not_retain_store_cause(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    app = create_runtime_api(
        settings=_settings_with_admin_console(tmp_path),
        store_factory=lambda _database_url: store,
    )
    endpoint = _runtime_route_endpoint(app, "/admin/artifacts/{artifact_id}")
    authorization = "Basic " + base64.b64encode(
        b"console-admin:console-password"
    ).decode("ascii")

    with pytest.raises(HTTPException) as exc_info:
        endpoint(artifact_id=404, authorization=authorization)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "artifact not found"
    assert exc_info.value.__cause__ is None


def test_admin_console_artifact_view_redacts_sensitive_payload_values(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    store.artifact_blob_records[4] = ArtifactBlobRecord(
        id=4,
        job_id="job-evt-002",
        story_number="STRY0010002",
        artifact_kind="implementation_candidate",
        schema_version="implementation-candidate-v1",
        payload_json={
            "diagnostic": (
                "provider called https://api-user:url-secret@example.service-now.com/api"
                "?client_secret=query-secret"
            ),
            "provider_response": {
                "api_key": "api-key-secret",
                "notes": ["Cookie: JSESSIONID=session-secret; route=node"],
            },
        },
        sha256="e" * 64,
        created_at=datetime(2026, 5, 14, 18, 3, tzinfo=UTC),
    )
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_console(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin/artifacts/4", auth=("console-admin", "console-password"))

    assert response.status_code == 200
    assert "***REDACTED***" in response.text
    assert "url-secret" not in response.text
    assert "query-secret" not in response.text
    assert "api-key-secret" not in response.text
    assert "session-secret" not in response.text


def test_admin_console_artifact_view_bounds_large_persisted_payloads(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore()
    store.artifact_blob_records[6] = ArtifactBlobRecord(
        id=6,
        job_id="job-evt-002",
        story_number="STRY0010002",
        artifact_kind="implementation_candidate",
        schema_version="implementation-candidate-v1",
        payload_json={
            "records": [
                {
                    "index": index,
                    "diagnostic": (
                        "provider called "
                        "https://api-user:url-secret@example.service-now.com/api"
                        "?access_token=token-secret"
                    ),
                }
                for index in range(900)
            ]
        },
        sha256="0" * 64,
        created_at=datetime(2026, 5, 14, 18, 4, tzinfo=UTC),
    )
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_console(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin/artifacts/6", auth=("console-admin", "console-password"))

    assert response.status_code == 200
    assert len(response.text) < 25000
    assert "payload_truncated" in response.text
    assert "...[truncated]" in response.text
    assert "url-secret" not in response.text
    assert "token-secret" not in response.text


def test_admin_console_artifact_view_sanitizes_payload_keys(tmp_path: Path) -> None:
    store = FakeRuntimeStore()
    store.artifact_blob_records[7] = ArtifactBlobRecord(
        id=7,
        job_id="job-evt-002",
        story_number="STRY0010002",
        artifact_kind="implementation_candidate",
        schema_version="implementation-candidate-v1",
        payload_json={
            "diagnostic\nclient_secret=key-secret": "ok",
            f"oversized {'A' * 2200}": "ok",
        },
        sha256="1" * 64,
        created_at=datetime(2026, 5, 14, 18, 5, tzinfo=UTC),
    )
    client = TestClient(
        create_runtime_api(
            settings=_settings_with_admin_console(tmp_path),
            store_factory=lambda _database_url: store,
        )
    )

    response = client.get("/admin/artifacts/7", auth=("console-admin", "console-password"))

    assert response.status_code == 200
    assert "key-secret" not in response.text
    assert "diagnostic client_secret=***REDACTED***" in response.text
    assert "...[truncated]" in response.text
    assert "A" * 800 not in response.text


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
    assert store.completed_jobs == [
        ("job-evt-001", "worker-1", "Build claim applied for STRY0010013")
    ]
    assert store.failed_jobs == []
    assert store.closed is True
    assert [request.method for request in transport.requests] == [
        "POST",
        "GET",
        "GET",
        "PATCH",
        "GET",
    ]


def test_servicenow_story_client_rejects_pm_url_subclass_before_fallback_truthiness(
    tmp_path: Path,
) -> None:
    class SecretBearingServiceNowUrl(str):
        def __len__(self) -> int:
            raise AssertionError("client_secret=servicenow-story-url-secret")

    settings = _settings(tmp_path).model_copy(
        update={
            "servicenow_pm_instance_url": SecretBearingServiceNowUrl(
                "https://pm.example.service-now.com"
            ),
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_servicenow._servicenow_story_client_from_settings(
            settings=settings,
            transport=RecordingTransport([]),
        )

    diagnostic = str(exc.value)
    assert diagnostic == "SERVICENOW_PM_INSTANCE_URL must be a string runtime setting"
    assert "SecretBearingServiceNowUrl" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-story-url-secret" not in diagnostic


def test_servicenow_pm_dev_match_rejects_secret_subclass_before_equality(
    tmp_path: Path,
) -> None:
    class SecretBearingServiceNowSecret(str):
        def __eq__(self, _other: object) -> bool:
            raise AssertionError("client_secret=servicenow-match-secret")

    settings = _settings(tmp_path).model_copy(
        update={
            "servicenow_pm_client_secret": SecretBearingServiceNowSecret("client-secret"),
            "servicenow_dev_client_secret": "client-secret",
        }
    )

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_servicenow._servicenow_pm_and_dev_settings_match(settings)

    diagnostic = str(exc.value)
    assert diagnostic == "SERVICENOW_PM_CLIENT_SECRET must be a string runtime setting"
    assert "SecretBearingServiceNowSecret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "servicenow-match-secret" not in diagnostic


def test_process_one_runtime_fulfillment_generates_openai_candidate_when_enabled(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore(claimed_job=_job())
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            # Model fulfillment fetches the story while it is still in Ready state.
            HttpResponse(status_code=200, json_body={"result": [_story_record()]}),
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
            # Build claim runs only after candidate generation succeeds.
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
                            "read_only": "false",
                        },
                        {
                            "element": "work_notes",
                            "column_label": "Work notes",
                            "internal_type": "journal_input",
                            "active": "true",
                            "read_only": "false",
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
            # Intake feedback assessment re-fetches the story after the claim.
            HttpResponse(status_code=200, json_body={"result": [_story_record()]}),
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
        "PATCH",
        "GET",
        "GET",
        "GET",
        "GET",
        "POST",
        "GET",
        "GET",
        "PATCH",
    ]
    assert transport.requests[2].url.endswith("/api/now/table/sys_db_object")
    assert transport.requests[2].params["sysparm_query"] == "name=rm_story"
    assert transport.requests[3].url.endswith("/api/now/table/sys_dictionary")
    assert transport.requests[3].params["sysparm_query"] == "name=rm_story"
    assert transport.requests[4].url.endswith("/api/now/table/sys_ui_section")
    assert transport.requests[4].params["sysparm_query"] == "name=rm_story"
    assert transport.requests[5].url.endswith("/api/now/table/sys_ui_element")
    assert transport.requests[5].params["sysparm_query"] == (
        "name=rm_story^sys_ui_section=rm-story-main-section"
    )
    assert transport.requests[6].url.endswith("/api/now/table/sys_security_acl")
    assert transport.requests[6].params["sysparm_query"] == "name=rm_story"
    assert transport.requests[7].url.endswith("/api/now/table/sys_script")
    assert transport.requests[7].params["sysparm_query"] == "collection=rm_story"
    assert transport.requests[14].url == "https://api.openai.com/v1/responses"
    assert transport.requests[14].headers["Authorization"] == "Bearer openai-key"
    assert "openai-key" not in repr(transport.requests[14].body)
    # Build claim is applied only after the model stage succeeds.
    assert transport.requests[15].url.endswith("/api/now/table/rm_story")
    assert transport.requests[17].method == "PATCH"
    assert transport.requests[19].url.endswith("/api/now/table/sys_ui_section")
    assert transport.requests[19].params["sysparm_query"] == "name=rm_story"
    assert transport.requests[20].url.endswith("/api/now/table/sys_ui_element")
    assert transport.requests[20].params["sysparm_query"] == (
        "name=rm_story^sys_ui_section=rm-story-main-section"
    )
    assert transport.requests[21].url.endswith("/api/now/table/sys_ws_operation")
    assert transport.requests[21].params["sysparm_query"] == (
        "web_service_definition.service_id=jedi_update_set_import"
        "^name=import_update_set_xml^active=true"
    )
    assert transport.requests[22].url.endswith("/api/1860704/jedi_update_set_import")
    assert (
        "sys_dictionary_rm_story_u_ai_review_notes" in transport.requests[22].body["update_set_xml"]
    )
    assert transport.requests[23].url.endswith("/api/now/table/sys_remote_update_set")
    assert transport.requests[23].params["sysparm_query"].startswith("remote_sys_id=")
    assert transport.requests[24].url.endswith("/api/now/table/sys_choice")
    assert transport.requests[24].params["sysparm_query"] == (
        "name=rm_story^element=state^inactive=false"
    )
    assert store.artifact_refs == []
    assert [artifact[2] for artifact in store.json_artifacts] == [
        "instance_context_bundle",
        "implementation_packet",
        "implementation_candidate",
        "atf_test_plan",
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


def test_process_one_runtime_fulfillment_rolls_back_when_model_stage_fails(
    tmp_path: Path,
) -> None:
    """If candidate generation fails, the build claim must not be applied."""
    store = FakeRuntimeStore(claimed_job=_job())
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(status_code=200, json_body={"result": [_story_record()]}),
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
            # Model returns an unparseable payload, so the claim PATCH must never fire.
            HttpResponse(status_code=200, json_body={"output_text": "not-json"}),
        ]
    )

    result = process_one_runtime_fulfillment(
        settings=_settings_with_openai(tmp_path, apply=True),
        store_factory=lambda _database_url: store,
        transport=transport,
    )

    assert result.status == "failed"
    patch_methods = [r.method for r in transport.requests if r.method == "PATCH"]
    assert patch_methods == [], "story state must not change when model stage fails"
    assert store.completed_jobs == []
    assert store.failed_jobs[0][1] == "worker-1"
    assert "OpenAI response" in store.failed_jobs[0][2]


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
            # Model fulfillment fetches the story while it is still in Ready state.
            HttpResponse(status_code=200, json_body={"result": [incident_story]}),
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
                        {
                            "sys_id": "number-element",
                            "element": "number",
                            "position": "1",
                        },
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
            # Build claim runs only after candidate generation succeeds.
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
                            "read_only": "false",
                        },
                        {
                            "element": "work_notes",
                            "column_label": "Work notes",
                            "internal_type": "journal_input",
                            "active": "true",
                            "read_only": "false",
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
            # Intake feedback assessment re-fetches the story after the claim.
            HttpResponse(status_code=200, json_body={"result": [incident_story]}),
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
                        {
                            "sys_id": "number-element",
                            "element": "number",
                            "position": "1",
                        },
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
    assert result.message == "Implementation candidate generated for STRY0010001"
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


def test_runtime_handler_rejects_model_provider_subclass_before_len(
    tmp_path: Path,
) -> None:
    class SecretBearingModelProvider(str):
        def __len__(self) -> int:
            raise AssertionError("client_secret=runtime-handler-model-secret")

    settings = _settings_with_openai(tmp_path).model_copy(
        update={"model_provider": SecretBearingModelProvider("openai")}
    )
    claim_calls: list[str] = []

    def claim_handler(_job: FulfillmentJobRecord) -> FulfillmentExecutionResult:
        claim_calls.append("claim")
        return FulfillmentExecutionResult(message="claimed")

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_fulfillment._runtime_handler(
            settings=settings,
            client=object(),
            claim_handler=claim_handler,
            transport=RecordingTransport([]),
        )

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_MODEL_PROVIDER must be a string runtime setting"
    assert "SecretBearingModelProvider" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "runtime-handler-model-secret" not in diagnostic
    assert claim_calls == []


def test_runtime_handler_rejects_public_web_access_subclass_before_eq(
    tmp_path: Path,
) -> None:
    class SecretBearingPublicWebAccess(str):
        def __eq__(self, _other: object) -> bool:
            raise AssertionError("client_secret=runtime-handler-public-web-secret")

    settings = _settings_with_openai(tmp_path).model_copy(
        update={"public_web_access": SecretBearingPublicWebAccess("disabled")}
    )
    claim_calls: list[str] = []

    def claim_handler(_job: FulfillmentJobRecord) -> FulfillmentExecutionResult:
        claim_calls.append("claim")
        return FulfillmentExecutionResult(message="claimed")

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_fulfillment._runtime_handler(
            settings=settings,
            client=object(),
            claim_handler=claim_handler,
            transport=RecordingTransport([]),
        )

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_PUBLIC_WEB_ACCESS must be a string runtime setting"
    assert "SecretBearingPublicWebAccess" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "runtime-handler-public-web-secret" not in diagnostic
    assert claim_calls == []


def test_process_one_runtime_fulfillment_rejects_malformed_provider_without_echoing_value(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore(claimed_job=None)
    transport = RecordingTransport([])
    settings = _settings(tmp_path).model_copy(update={"model_provider": "openai\nfallback"})

    with pytest.raises(RuntimeConfigError) as exc:
        process_one_runtime_fulfillment(
            settings=settings,
            store_factory=lambda _database_url: store,
            transport=transport,
        )

    message = str(exc.value)
    assert "JEDI_MODEL_PROVIDER" in message
    assert "whitespace or control characters" in message
    assert "fallback" not in message
    assert "\n" not in message
    assert store.get_job_ids == []
    assert transport.requests == []


def test_process_one_runtime_fulfillment_rejects_unsupported_provider_without_echoing_value(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore(claimed_job=None)
    transport = RecordingTransport([])
    unsupported_provider = "unapproved-provider"
    settings = _settings(tmp_path).model_copy(update={"model_provider": unsupported_provider})

    with pytest.raises(RuntimeConfigError) as exc:
        process_one_runtime_fulfillment(
            settings=settings,
            store_factory=lambda _database_url: store,
            transport=transport,
        )

    message = str(exc.value)
    assert "Unsupported JEDI_MODEL_PROVIDER" in message
    assert unsupported_provider not in message
    assert store.get_job_ids == []
    assert transport.requests == []


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("openai_api_key", "openai-key\ninjected"),
        ("openai_model", "gpt-4o\nfallback"),
    ],
)
def test_process_one_runtime_fulfillment_wraps_invalid_openai_provider_settings(
    tmp_path: Path,
    field_name: str,
    field_value: str,
) -> None:
    store = FakeRuntimeStore(claimed_job=None)
    transport = RecordingTransport([])
    settings = _settings_with_openai(tmp_path).model_copy(update={field_name: field_value})

    with pytest.raises(RuntimeConfigError, match=field_name.upper()) as exc_info:
        process_one_runtime_fulfillment(
            settings=settings,
            store_factory=lambda _database_url: store,
            transport=transport,
        )

    assert exc_info.value.__cause__ is None
    assert store.get_job_ids == []
    assert transport.requests == []


class UnstringifiableNumericRuntimeConfigError(ValueError):
    def __str__(self) -> str:
        raise ValueError("client-secret-value")


class UnstringifiableOpenAIProviderSettingError(ValueError):
    def __str__(self) -> str:
        raise ValueError("openai-client-secret-value")


class HostileOpenAIValidationLocation:
    def __str__(self) -> str:
        raise ValueError("openai-key-value")


class FakeOpenAIValidationError:
    def errors(self) -> list[dict[str, object]]:
        return [{"loc": (HostileOpenAIValidationLocation(),)}]


def test_openai_runtime_error_fields_rejects_unstringifiable_locations_without_leak() -> None:
    validation_error = cast(ValidationError, FakeOpenAIValidationError())
    assert runtime_fulfillment._openai_runtime_error_fields(validation_error) == [
        "OPENAI_PROVIDER_SETTINGS"
    ]


def test_runtime_config_int_value_wraps_unstringifiable_parser_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_parse_optional_base10_int(_value: str | None, *, name: str) -> int | None:
        raise UnstringifiableNumericRuntimeConfigError

    monkeypatch.setattr(
        runtime_config,
        "parse_optional_base10_int",
        fail_parse_optional_base10_int,
    )

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_config._int_value("5", name="JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS", default=60)

    assert str(exc.value) == (
        "runtime config raised unstringifiable UnstringifiableNumericRuntimeConfigError"
    )
    assert exc.value.__cause__ is None
    assert "client-secret-value" not in str(exc.value)


def test_runtime_config_float_value_wraps_unstringifiable_parser_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_parse_optional_ascii_decimal_float(
        _value: str | None,
        *,
        name: str,
    ) -> float | None:
        raise UnstringifiableNumericRuntimeConfigError

    monkeypatch.setattr(
        runtime_config,
        "parse_optional_ascii_decimal_float",
        fail_parse_optional_ascii_decimal_float,
    )

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_config._float_value("1.5", name="JEDI_WORKER_IDLE_SLEEP_SECONDS", default=1.0)

    assert str(exc.value) == (
        "runtime config raised unstringifiable UnstringifiableNumericRuntimeConfigError"
    )
    assert exc.value.__cause__ is None
    assert "client-secret-value" not in str(exc.value)


def test_runtime_config_openai_api_key_wraps_unstringifiable_provider_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_validate_provider_api_key(_value: str) -> str:
        raise UnstringifiableOpenAIProviderSettingError

    monkeypatch.setattr(
        runtime_config,
        "validate_provider_api_key",
        fail_validate_provider_api_key,
    )

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_config._optional_openai_provider_value("openai-key", name="OPENAI_API_KEY")

    assert str(exc.value) == (
        "OPENAI_API_KEY provider setting raised unstringifiable "
        "UnstringifiableOpenAIProviderSettingError"
    )
    assert exc.value.__cause__ is None
    assert "openai-client-secret-value" not in str(exc.value)


def test_runtime_config_openai_model_wraps_unstringifiable_provider_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_validate_provider_model(_value: str) -> str:
        raise UnstringifiableOpenAIProviderSettingError

    monkeypatch.setattr(
        runtime_config,
        "validate_provider_model",
        fail_validate_provider_model,
    )

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_config._optional_openai_provider_value("gpt-4.1", name="OPENAI_MODEL")

    assert str(exc.value) == (
        "OPENAI_MODEL provider setting raised unstringifiable "
        "UnstringifiableOpenAIProviderSettingError"
    )
    assert exc.value.__cause__ is None
    assert "openai-client-secret-value" not in str(exc.value)


def test_runtime_config_bool_value_rejects_non_string_without_truthiness_leak() -> None:
    class SecretBearingRuntimeValue:
        def __bool__(self) -> bool:
            raise RuntimeError("client_secret=runtime-bool-secret")

        def __str__(self) -> str:
            return "client_secret=runtime-bool-secret"

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_config._bool_value(
            cast(Any, SecretBearingRuntimeValue()), name="JEDI_TEST_BOOL"
        )

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_TEST_BOOL must be a string runtime setting"
    assert "SecretBearingRuntimeValue" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "runtime-bool-secret" not in diagnostic


def test_runtime_config_enum_value_rejects_string_subclass_without_string_leak() -> None:
    class SecretBearingRuntimeText(str):
        def __str__(self) -> str:
            raise RuntimeError("client_secret=runtime-enum-secret")

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_config._enum_value(
            SecretBearingRuntimeText("api"),
            name="JEDI_TEST_ENUM",
            allowed={"api", "worker"},
            default="api",
        )

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_TEST_ENUM must be a string runtime setting"
    assert "SecretBearingRuntimeText" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "runtime-enum-secret" not in diagnostic


def test_runtime_environment_value_rejects_non_string_without_value_leak() -> None:
    class SecretBearingEnvironment:
        def __bool__(self) -> bool:
            return True

        def __str__(self) -> str:
            return "client_secret=runtime-env-secret"

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_config._runtime_environment_value(cast(Any, SecretBearingEnvironment()))

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_ENVIRONMENT must be a string runtime setting"
    assert "SecretBearingEnvironment" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "runtime-env-secret" not in diagnostic


def test_runtime_env_value_rejects_non_string_primary_without_truthiness_leak() -> None:
    class SecretBearingEnvValue:
        def __bool__(self) -> bool:
            raise RuntimeError("client_secret=runtime-env-value-secret")

        def __str__(self) -> str:
            return "client_secret=runtime-env-value-secret"

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_config._env_value(
            {
                "SERVICENOW_PM_INSTANCE_URL": cast(Any, SecretBearingEnvValue()),
                "SERVICENOW_INSTANCE_URL": "https://fallback.service-now.com",
            },
            "SERVICENOW_PM_INSTANCE_URL",
            "SERVICENOW_INSTANCE_URL",
        )

    diagnostic = str(exc.value)
    assert diagnostic == "SERVICENOW_PM_INSTANCE_URL must be a string runtime setting"
    assert "SecretBearingEnvValue" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "runtime-env-value-secret" not in diagnostic


def test_blank_split_servicenow_overrides_reject_non_string_without_value_leak() -> None:
    class SecretBearingSplitOverride:
        def __str__(self) -> str:
            return "client_secret=runtime-split-secret"

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_config._blank_split_servicenow_override_errors(
            {
                "SERVICENOW_PM_CLIENT_ID": cast(Any, SecretBearingSplitOverride()),
            }
        )

    diagnostic = str(exc.value)
    assert diagnostic == "SERVICENOW_PM_CLIENT_ID must be a string runtime setting"
    assert "SecretBearingSplitOverride" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "runtime-split-secret" not in diagnostic


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
    store = FakeRuntimeStore(claimed_job=_job(story_sys_id="correct-story-sys-id"))
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
    assert store.failed_jobs == [("job-evt-001", "worker-1", "fresh_story_state_mismatch")]
    assert [request.method for request in transport.requests] == [
        "POST",
        "GET",
        "GET",
        "GET",
        "PATCH",
    ]
    assert transport.requests[1].params["sysparm_query"] == "sys_id=correct-story-sys-id"
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


class RecordingFailureNotifierClient:
    def __init__(self) -> None:
        self.updated_fields: dict[str, object] | None = None
        self.fetch_queries: list[str | None] = []

    def fetch_stories(self, sysparm_query: str | None = None, *, limit: int = 100) -> list[Any]:
        self.fetch_queries.append(sysparm_query)
        return [{"sys_id": "story-sys-id"}]

    def fetch_story_state_choices(self) -> list[Any]:
        return [{"label": "Draft", "value": "-6"}]

    def update_story_fields(self, story_sys_id: str, fields: dict[str, object]) -> dict[str, str]:
        self.updated_fields = fields
        return {"sys_id": story_sys_id}


class EmptyFailureNotifierClient(RecordingFailureNotifierClient):
    def fetch_stories(self, sysparm_query: str | None = None, *, limit: int = 100) -> list[Any]:
        return []


class HostileFailureNotifierSecretValues:
    def __iter__(self) -> Iterator[str]:
        raise AssertionError("client_secret=failure-notifier-iterator-secret")


class HostileStateChoiceLabel(str):
    def strip(self, *_args: object, **_kwargs: object) -> str:
        raise AssertionError("client_secret=state-choice-secret")


class MalformedStateChoiceClient(RecordingFailureNotifierClient):
    def fetch_story_state_choices(self) -> list[Any]:
        return [
            {"label": HostileStateChoiceLabel("Draft"), "value": "-7"},
            {"label": "Draft", "value": "-6"},
        ]


class UnsafeStateChoiceValueClient(RecordingFailureNotifierClient):
    def fetch_story_state_choices(self) -> list[Any]:
        return [
            {"label": "Draft", "value": "-7\nclient_secret=state-secret"},
            {"label": "Draft", "value": "-6"},
        ]


class UnsafeFoundStoryClient(RecordingFailureNotifierClient):
    def fetch_stories(self, sysparm_query: str | None = None, *, limit: int = 100) -> list[Any]:
        self.fetch_queries.append(sysparm_query)
        return [{"sys_id": "story sys id"}]


class HostileStoryCollectionClient(RecordingFailureNotifierClient):
    def fetch_stories(self, sysparm_query: str | None = None, *, limit: int = 100) -> list[Any]:
        self.fetch_queries.append(sysparm_query)

        class SecretBearingStories(list[Any]):
            def __len__(self) -> int:
                raise RuntimeError("client_secret=failure-notifier-stories-len-secret")

        return SecretBearingStories([{"sys_id": "story-sys-id"}])


class TupleStoryCollectionClient(RecordingFailureNotifierClient):
    def fetch_stories(self, sysparm_query: str | None = None, *, limit: int = 100) -> Any:
        self.fetch_queries.append(sysparm_query)
        return ({"sys_id": "story-sys-id"},)


def test_servicenow_failure_notifier_sanitizes_work_note_values() -> None:
    client = RecordingFailureNotifierClient()
    notifier = _servicenow_failure_notifier(
        client=cast(ServiceNowClient, client),
        secret_values=("literal-secret",),
    )
    job = _job(event_id="evt-001\nclient_secret=event-secret").model_copy(
        update={"job_id": "job-001\napi_key=job-secret"}
    )

    notifier(job, "Failure details\nclient_secret=error-secret literal-secret")

    assert client.updated_fields is not None
    work_notes = cast(str, client.updated_fields["work_notes"])
    assert "event-secret" not in work_notes
    assert "job-secret" not in work_notes
    assert "error-secret" not in work_notes
    assert "literal-secret" not in work_notes
    assert "client_secret=***REDACTED***" in work_notes
    assert "api_key=***REDACTED***" in work_notes
    assert "\n" not in work_notes
    assert "evt-001" in work_notes
    assert "job-001" in work_notes


def test_servicenow_failure_notifier_ignores_hostile_secret_iterator() -> None:
    client = RecordingFailureNotifierClient()
    notifier = _servicenow_failure_notifier(
        client=cast(ServiceNowClient, client),
        secret_values=HostileFailureNotifierSecretValues(),
    )
    job = _job(event_id="evt-001")

    notifier(job, "Failure details client_secret=error-secret")

    assert client.updated_fields is not None
    work_notes = cast(str, client.updated_fields["work_notes"])
    assert "failure-notifier-iterator-secret" not in work_notes
    assert "error-secret" not in work_notes
    assert "client_secret=***REDACTED***" in work_notes


def test_servicenow_failure_notifier_bounds_work_note_values() -> None:
    client = RecordingFailureNotifierClient()
    notifier = _servicenow_failure_notifier(client=cast(ServiceNowClient, client))
    job = _job(event_id=f"evt-001 {'A' * 2200}").model_copy(
        update={"job_id": f"job-001 {'B' * 2200}"}
    )

    notifier(job, f"Failure details {'C' * 2200}")

    assert client.updated_fields is not None
    work_notes = cast(str, client.updated_fields["work_notes"])
    assert "...[truncated]" in work_notes
    assert len(work_notes) < 1800


def test_servicenow_failure_notifier_sanitizes_story_not_found_diagnostic() -> None:
    client = EmptyFailureNotifierClient()
    notifier = _servicenow_failure_notifier(
        client=cast(ServiceNowClient, client),
        secret_values=("missing-story-secret",),
    )
    job = _job(story_number="STRY0010013 missing-story-secret")

    with pytest.raises(RuntimeError) as exc_info:
        notifier(job, "Failure details")

    diagnostic = str(exc_info.value)
    assert diagnostic == "story not found: STRY0010013 ***REDACTED***"
    assert "missing-story-secret" not in diagnostic
    assert "\n" not in diagnostic


def test_servicenow_failure_notifier_rejects_unsafe_story_number_lookup() -> None:
    client = RecordingFailureNotifierClient()
    notifier = _servicenow_failure_notifier(client=cast(ServiceNowClient, client))
    job = _job(story_number="STRY0010013^ORnumberISNOTEMPTY")

    with pytest.raises(RuntimeError) as exc_info:
        notifier(job, "Failure details")

    assert str(exc_info.value) == "story lookup query is unsafe"
    assert client.fetch_queries == []


def test_servicenow_failure_notifier_rejects_unsafe_story_sys_id_lookup() -> None:
    client = RecordingFailureNotifierClient()
    notifier = _servicenow_failure_notifier(client=cast(ServiceNowClient, client))
    job = _job(story_sys_id="story sys id")

    with pytest.raises(RuntimeError) as exc_info:
        notifier(job, "Failure details")

    assert str(exc_info.value) == "story lookup query is unsafe"
    assert client.fetch_queries == []


def test_servicenow_failure_notifier_rejects_unsafe_found_story_sys_id() -> None:
    client = UnsafeFoundStoryClient()
    notifier = _servicenow_failure_notifier(client=cast(ServiceNowClient, client))

    with pytest.raises(RuntimeError) as exc_info:
        notifier(_job(), "Failure details")

    assert str(exc_info.value) == "story lookup result is unsafe"
    assert client.updated_fields is None


class NonDictStoryClient(RecordingFailureNotifierClient):
    def fetch_stories(self, sysparm_query: str | None = None, *, limit: int = 100) -> list[Any]:
        self.fetch_queries.append(sysparm_query)
        return [SimpleNamespace(sys_id="story-sys-id")]


def test_servicenow_failure_notifier_rejects_non_dict_story_record() -> None:
    client = NonDictStoryClient()
    notifier = _servicenow_failure_notifier(client=cast(ServiceNowClient, client))

    with pytest.raises(RuntimeError) as exc_info:
        notifier(_job(), "Failure details")

    assert str(exc_info.value) == "story lookup result is unsafe"
    assert client.updated_fields is None


class NonDictStateChoiceClient(RecordingFailureNotifierClient):
    def fetch_story_state_choices(self) -> list[Any]:
        return [SimpleNamespace(label="Draft", value="-6")]


def test_servicenow_failure_notifier_skips_non_dict_state_choice() -> None:
    client = NonDictStateChoiceClient()
    notifier = _servicenow_failure_notifier(client=cast(ServiceNowClient, client))

    notifier(_job(), "Failure details")

    assert client.updated_fields is not None
    assert "state" not in client.updated_fields


def test_servicenow_failure_notifier_rejects_story_collection_subclass_without_leak() -> None:
    client = HostileStoryCollectionClient()
    notifier = _servicenow_failure_notifier(client=cast(ServiceNowClient, client))

    with pytest.raises(RuntimeError) as exc_info:
        notifier(_job(), "Failure details")

    diagnostic = str(exc_info.value)
    assert diagnostic == "story lookup result is unsafe"
    assert client.updated_fields is None
    assert "SecretBearingStories" not in diagnostic
    assert "failure-notifier-stories-len-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_servicenow_failure_notifier_rejects_alternate_story_iterable() -> None:
    client = TupleStoryCollectionClient()
    notifier = _servicenow_failure_notifier(client=cast(ServiceNowClient, client))

    with pytest.raises(RuntimeError) as exc_info:
        notifier(_job(), "Failure details")

    assert str(exc_info.value) == "story lookup result is unsafe"
    assert client.updated_fields is None


def test_servicenow_failure_notifier_skips_malformed_state_choices() -> None:
    client = MalformedStateChoiceClient()
    notifier = _servicenow_failure_notifier(client=cast(ServiceNowClient, client))

    notifier(_job(), "Failure details")

    assert client.updated_fields is not None
    assert client.updated_fields["state"] == "-6"


def test_servicenow_failure_notifier_skips_unsafe_state_choice_values() -> None:
    client = UnsafeStateChoiceValueClient()
    notifier = _servicenow_failure_notifier(client=cast(ServiceNowClient, client))

    notifier(_job(), "Failure details")

    assert client.updated_fields is not None
    assert client.updated_fields["state"] == "-6"
