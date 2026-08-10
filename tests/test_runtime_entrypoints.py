from __future__ import annotations

import math
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI

from jedi_devproject import runtime_api, runtime_worker
from jedi_devproject.fulfillment_worker import FulfillmentWorkerResult
from jedi_devproject.lifecycle_events import LifecycleStateChangeEvent
from jedi_devproject.operational_store import (
    ArtifactBlobRecord,
    ArtifactRefRecord,
    FulfillmentJobRecord,
    FulfillmentJobStatusSummaryRecord,
    JobEventRecord,
    LifecycleEventRecord,
)
from jedi_devproject.runtime import RuntimeConfigError, RuntimeSettings
from jedi_devproject.runtime_store import RuntimeStore


def _settings(tmp_path: Path) -> RuntimeSettings:
    return RuntimeSettings(
        database_url="postgresql://jedi:jedi@postgres:5432/jedi",
        servicenow_instance_url="https://dev205693.service-now.com",
        servicenow_client_id="client-id",
        servicenow_client_secret="client-secret",
        worker_id="worker-1",
        audit_root=tmp_path,
        build_claim_apply=False,
    )


def test_runtime_api_build_app_uses_env_file_and_returns_fastapi_app(
    tmp_path: Path,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:jedi@postgres:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                "JEDI_AUDIT_ROOT=/app/artifacts/audit",
            ]
        ),
        encoding="utf-8",
    )
    database_urls: list[str] = []

    app = runtime_api.build_app(
        env_path=env_path,
        store_factory=_store_factory(database_urls),
    )

    assert isinstance(app, FastAPI)
    assert database_urls == ["postgresql://jedi:jedi@postgres:5432/jedi"]


def test_runtime_api_build_app_rejects_worker_role_before_store_open(
    tmp_path: Path,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:jedi@postgres:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                "JEDI_AUDIT_ROOT=/app/artifacts/audit",
                "JEDI_RUNTIME_ROLE=worker",
            ]
        ),
        encoding="utf-8",
    )
    database_urls: list[str] = []

    with pytest.raises(RuntimeConfigError, match="JEDI_RUNTIME_ROLE=worker"):
        runtime_api.build_app(
            store_factory=_store_factory(database_urls),
            env_path=env_path,
        )

    assert database_urls == []


def test_runtime_worker_run_once_delegates_to_runtime_fulfillment(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    seen_settings: list[RuntimeSettings] = []

    def processor(runtime_settings: RuntimeSettings) -> FulfillmentWorkerResult:
        seen_settings.append(runtime_settings)
        return FulfillmentWorkerResult(
            status="idle",
            job_id=None,
            story_number=None,
            message="No queued fulfillment job available",
            error_message=None,
        )

    result = runtime_worker.run_once(
        settings=settings,
        processor=processor,
    )

    assert result.status == "idle"
    assert seen_settings == [settings]


def test_runtime_worker_run_once_rejects_api_role_before_processor_call(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(update={"runtime_role": "api"})
    seen_settings: list[RuntimeSettings] = []

    def processor(runtime_settings: RuntimeSettings) -> FulfillmentWorkerResult:
        seen_settings.append(runtime_settings)
        return FulfillmentWorkerResult(
            status="idle",
            job_id=None,
            story_number=None,
            message="No queued fulfillment job available",
            error_message=None,
        )

    with pytest.raises(RuntimeConfigError, match="JEDI_RUNTIME_ROLE=api"):
        runtime_worker.run_once(
            settings=settings,
            processor=processor,
        )

    assert seen_settings == []


def test_runtime_report_json_rejects_non_finite_summary_without_payload_leak() -> None:
    summary = runtime_worker.RuntimeWorkerLoopSummary.model_construct(
        iterations=1,
        completed=0,
        idle=math.nan,
        failed=0,
        alerts_emitted=0,
        alert_failures=0,
        prune_failures=0,
        stale_job_recovery_failures=0,
        stopped_reason="client_secret=do-not-echo-this",
    )

    with pytest.raises(ValueError) as exc_info:
        runtime_worker._runtime_report_json(summary)

    diagnostic = str(exc_info.value)
    assert diagnostic == "runtime worker report contains non-finite numeric values"
    assert exc_info.value.__cause__ is None
    assert "idle" not in diagnostic
    assert "NaN" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "do-not-echo-this" not in diagnostic


def test_runtime_report_json_rejects_non_json_summary_without_payload_leak() -> None:
    class StringifiesSecret:
        def __str__(self) -> str:
            return "do-not-echo-this"

    summary = runtime_worker.RuntimeWorkerLoopSummary.model_construct(
        iterations=1,
        completed=0,
        idle=0,
        failed=0,
        alerts_emitted=0,
        alert_failures=0,
        prune_failures=0,
        stale_job_recovery_failures=0,
        stopped_reason=StringifiesSecret(),
    )

    with pytest.raises(ValueError) as exc_info:
        runtime_worker._runtime_report_json(summary)

    diagnostic = str(exc_info.value)
    assert diagnostic == "runtime worker report contains non-JSON values"
    assert exc_info.value.__cause__ is None
    assert "stopped_reason" not in diagnostic
    assert "StringifiesSecret" not in diagnostic
    assert "do-not-echo-this" not in diagnostic


def test_runtime_worker_run_loop_processes_until_iteration_limit(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    statuses = ["completed", "idle", "completed"]
    seen_settings: list[RuntimeSettings] = []
    sleep_calls: list[float] = []

    def processor(runtime_settings: RuntimeSettings) -> FulfillmentWorkerResult:
        seen_settings.append(runtime_settings)
        status = statuses.pop(0)
        return FulfillmentWorkerResult(
            status=status,
            job_id="job-001" if status == "completed" else None,
            story_number="STRY0010013" if status == "completed" else None,
            message=status,
            error_message=None,
        )

    summary = runtime_worker.run_loop(
        settings=settings,
        processor=processor,
        max_iterations=3,
        idle_sleep_seconds=2.5,
        sleep=sleep_calls.append,
    )

    assert summary.iterations == 3
    assert summary.completed == 2
    assert summary.idle == 1
    assert summary.failed == 0
    assert len(seen_settings) == 3
    assert sleep_calls == [2.5]


def test_runtime_worker_run_loop_stops_on_failed_job_by_default(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)

    def processor(_runtime_settings: RuntimeSettings) -> FulfillmentWorkerResult:
        return FulfillmentWorkerResult(
            status="failed",
            job_id="job-001",
            story_number="STRY0010013",
            message=None,
            error_message="provider unavailable",
        )

    summary = runtime_worker.run_loop(
        settings=settings,
        processor=processor,
        max_iterations=5,
        idle_sleep_seconds=0,
        sleep=lambda _seconds: None,
    )

    assert summary.iterations == 1
    assert summary.failed == 1
    assert summary.stopped_reason == "failed_job"


def test_runtime_worker_run_loop_emits_alert_for_failed_job(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    emitted: list[FulfillmentWorkerResult] = []

    def processor(_runtime_settings: RuntimeSettings) -> FulfillmentWorkerResult:
        return FulfillmentWorkerResult(
            status="failed",
            job_id="job-001",
            story_number="STRY0010013",
            message=None,
            error_message="provider unavailable",
        )

    summary = runtime_worker.run_loop(
        settings=settings,
        processor=processor,
        max_iterations=1,
        idle_sleep_seconds=0,
        sleep=lambda _seconds: None,
        alert_emitter=emitted.append,
    )

    assert [result.job_id for result in emitted] == ["job-001"]
    assert summary.alerts_emitted == 1
    assert summary.alert_failures == 0


def test_runtime_worker_run_loop_alert_failure_does_not_crash_worker_with_redacted_log(
    tmp_path: Path,
    caplog: Any,
) -> None:
    settings = _settings(tmp_path)
    caplog.set_level("WARNING", logger="jedi_devproject.runtime_worker")

    def processor(_runtime_settings: RuntimeSettings) -> FulfillmentWorkerResult:
        return FulfillmentWorkerResult(
            status="failed",
            job_id="job-001",
            story_number="STRY0010013",
            message=None,
            error_message="provider unavailable",
        )

    def failing_alert_emitter(_result: FulfillmentWorkerResult) -> None:
        raise RuntimeError("alert delivery failed client_secret=secret-value")

    summary = runtime_worker.run_loop(
        settings=settings,
        processor=processor,
        max_iterations=1,
        idle_sleep_seconds=0,
        sleep=lambda _seconds: None,
        alert_emitter=failing_alert_emitter,
    )

    assert summary.failed == 1
    assert summary.alerts_emitted == 0
    assert summary.alert_failures == 1
    assert summary.stopped_reason == "failed_job"
    assert "worker alert delivery failed for job job-001" in caplog.text
    assert "secret-value" not in caplog.text
    assert "***REDACTED***" in caplog.text


def test_runtime_worker_load_worker_settings_reads_loop_environment(
    tmp_path: Path,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:jedi@postgres:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                "JEDI_AUDIT_ROOT=/app/artifacts/audit",
                "JEDI_WORKER_MAX_ITERATIONS=7",
                "JEDI_WORKER_IDLE_SLEEP_SECONDS=1.25",
                "JEDI_WORKER_STOP_ON_FAILURE=true",
            ]
        ),
        encoding="utf-8",
    )

    settings = runtime_worker.load_worker_settings(env_path)

    assert settings.runtime.database_url == "postgresql://jedi:jedi@postgres:5432/jedi"
    assert settings.max_iterations == 7
    assert settings.idle_sleep_seconds == 1.25
    assert settings.stop_on_failure is True


def test_runtime_worker_main_runs_loop_from_environment(
    tmp_path: Path,
    capsys: Any,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://jedi:jedi@postgres:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                f"JEDI_AUDIT_ROOT={tmp_path}",
                "JEDI_WORKER_MAX_ITERATIONS=2",
                "JEDI_WORKER_IDLE_SLEEP_SECONDS=0",
            ]
        ),
        encoding="utf-8",
    )
    seen_settings: list[RuntimeSettings] = []

    def processor(settings: RuntimeSettings) -> FulfillmentWorkerResult:
        seen_settings.append(settings)
        return FulfillmentWorkerResult(
            status="idle",
            job_id=None,
            story_number=None,
            message="No queued fulfillment job available",
            error_message=None,
        )

    exit_code = runtime_worker.main(
        env_path=env_path,
        processor=processor,
        sleep=lambda _seconds: None,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert len(seen_settings) == 2
    assert '"iterations":2' in captured.out
    assert '"idle":2' in captured.out


def _store_factory(database_urls: list[str]) -> Callable[[str], _NoopStore]:
    def create(database_url: str) -> _NoopStore:
        database_urls.append(database_url)
        return _NoopStore()

    return create


class _NoopStore:
    def __enter__(self) -> RuntimeStore:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def record_lifecycle_event(
        self,
        event: LifecycleStateChangeEvent,
        *,
        validation_status: str = "accepted",
    ) -> LifecycleEventRecord:
        raise AssertionError("not called")

    def enqueue_fulfillment_job(
        self,
        *,
        event_id: str,
        story_number: str,
    ) -> FulfillmentJobRecord:
        raise AssertionError("not called")

    def close_latest_fulfillment_job_for_story(
        self,
        *,
        story_number: str,
        event_id: str,
    ) -> FulfillmentJobRecord | None:
        raise AssertionError("not called")

    def record_rework_requested_for_story(
        self,
        *,
        story_number: str,
        event_id: str,
        target_state: str,
    ) -> FulfillmentJobRecord | None:
        raise AssertionError("not called")

    def reject_latest_fulfillment_job_for_story(
        self,
        *,
        story_number: str,
        event_id: str,
    ) -> FulfillmentJobRecord | None:
        raise AssertionError("not called")

    def claim_next_fulfillment_job(
        self,
        *,
        worker_id: str,
    ) -> FulfillmentJobRecord | None:
        raise AssertionError("not called")

    def complete_fulfillment_job(
        self,
        *,
        job_id: str,
        worker_id: str,
        message: str,
    ) -> FulfillmentJobRecord:
        raise AssertionError("not called")

    def fail_fulfillment_job(
        self,
        *,
        job_id: str,
        worker_id: str,
        error_message: str,
    ) -> FulfillmentJobRecord:
        raise AssertionError("not called")

    def touch_fulfillment_job_heartbeat(
        self,
        *,
        job_id: str,
        worker_id: str,
    ) -> FulfillmentJobRecord | None:
        raise AssertionError("not called")

    def record_artifact_ref(
        self,
        *,
        job_id: str,
        artifact_kind: str,
        path: str,
        sha256: str,
    ) -> object:
        raise AssertionError("not called")

    def record_json_artifact(
        self,
        *,
        job_id: str,
        story_number: str,
        artifact_kind: str,
        schema_version: str,
        payload: dict[str, Any],
    ) -> object:
        raise AssertionError("not called")

    def get_artifact_blob(self, artifact_id: int) -> ArtifactBlobRecord:
        raise AssertionError("not called")

    def get_job(self, job_id: str) -> FulfillmentJobRecord:
        raise AssertionError("not called")

    def artifact_refs_for_job(self, job_id: str) -> list[ArtifactRefRecord]:
        raise AssertionError("not called")

    def job_events_for_job(self, job_id: str) -> list[JobEventRecord]:
        raise AssertionError("not called")

    def recent_lifecycle_events(self, *, limit: int = 50) -> list[LifecycleEventRecord]:
        raise AssertionError("not called")

    def verify_schema_ready(self) -> bool:
        return True

    def recent_fulfillment_jobs(self, *, limit: int = 50) -> list[FulfillmentJobRecord]:
        raise AssertionError("not called")

    def fulfillment_job_status_summary(
        self,
        *,
        stale_before: datetime,
    ) -> FulfillmentJobStatusSummaryRecord:
        raise AssertionError("not called")
