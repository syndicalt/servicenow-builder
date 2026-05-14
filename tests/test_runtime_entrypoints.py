from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI

from jedi_devproject import runtime_api, runtime_worker
from jedi_devproject.fulfillment_worker import FulfillmentWorkerResult
from jedi_devproject.lifecycle_events import LifecycleStateChangeEvent
from jedi_devproject.operational_store import FulfillmentJobRecord, LifecycleEventRecord
from jedi_devproject.runtime import RuntimeSettings


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


def _store_factory(database_urls: list[str]) -> Callable[[str], _NoopStore]:
    def create(database_url: str) -> _NoopStore:
        database_urls.append(database_url)
        return _NoopStore()

    return create


class _NoopStore:
    def __enter__(self) -> _NoopStore:
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
        message: str,
    ) -> FulfillmentJobRecord:
        raise AssertionError("not called")

    def fail_fulfillment_job(
        self,
        *,
        job_id: str,
        error_message: str,
    ) -> FulfillmentJobRecord:
        raise AssertionError("not called")
