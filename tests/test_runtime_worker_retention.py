from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from jedi_devproject import runtime_worker
from jedi_devproject.fulfillment_worker import FulfillmentWorkerResult
from jedi_devproject.operational_store import (
    FulfillmentJobRecord,
    RetentionPolicy,
    RetentionPruneReport,
)
from jedi_devproject.runtime import RuntimeConfigError, RuntimeSettings
from jedi_devproject.runtime_worker import RuntimeWorkerLoopSummary
from jedi_devproject.servicenow import HttpRequest, HttpResponse


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


def _idle_result() -> FulfillmentWorkerResult:
    return FulfillmentWorkerResult(
        status="idle",
        job_id=None,
        story_number=None,
        message="No queued fulfillment job available",
        error_message=None,
    )


def _failed_result() -> FulfillmentWorkerResult:
    return FulfillmentWorkerResult(
        status="failed",
        job_id="job-evt-failed",
        story_number="STRY0010100",
        message=None,
        error_message="provider unavailable",
    )


class _HostileRuntimeReportText(str):
    def __str__(self) -> str:
        raise AssertionError("client_secret=runtime-report-str-secret")


class _RuntimeReportProbe(BaseModel):
    payload: dict[Any, Any]


class _UnstringifiableRuntimeWorkerError(RuntimeError):
    def __str__(self) -> str:
        raise ValueError("client-secret-value")


def _empty_report() -> RetentionPruneReport:
    return RetentionPruneReport(
        enabled=True,
        pruned_at=datetime(2026, 6, 11, 12, 0, tzinfo=UTC),
        prune_batch_size=500,
        results=[],
    )


def test_runtime_report_json_rejects_string_subclass_values_without_stringifying() -> None:
    report = RuntimeWorkerLoopSummary.model_construct(
        iterations=1,
        completed=0,
        idle=1,
        failed=0,
        alerts_emitted=0,
        alert_failures=0,
        prune_failures=0,
        stale_job_recovery_failures=0,
        stopped_reason=_HostileRuntimeReportText("client_secret=runtime-report-secret"),
    )

    with pytest.raises(ValueError) as exc:
        runtime_worker._runtime_report_json(report)

    diagnostic = str(exc.value)
    assert diagnostic == "runtime worker report contains non-JSON values"
    assert exc.value.__cause__ is None
    assert "runtime-report" not in diagnostic
    assert "client_secret" not in diagnostic


def test_runtime_report_json_rejects_string_subclass_keys_without_stringifying() -> None:
    report = _RuntimeReportProbe.model_construct(
        payload={
            _HostileRuntimeReportText("client_secret"): "visible value",
        }
    )

    with pytest.raises(ValueError) as exc:
        runtime_worker._runtime_report_json(report)

    diagnostic = str(exc.value)
    assert diagnostic == "runtime worker report contains non-JSON values"
    assert exc.value.__cause__ is None
    assert "runtime-report" not in diagnostic
    assert "client_secret" not in diagnostic


def test_runtime_report_json_rejects_container_subclasses_without_payload_leak() -> (
    None
):
    class HostileRuntimeReportDict(dict[str, Any]):
        def items(self) -> Any:
            raise AssertionError("client_secret=runtime-report-dict-subclass-secret")

    class HostileRuntimeReportList(list[Any]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=runtime-report-list-subclass-secret")

    class HostileRuntimeReportTuple(tuple[Any, ...]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=runtime-report-tuple-subclass-secret")

    for value in (
        HostileRuntimeReportDict({"client_secret": "hidden dict"}),
        HostileRuntimeReportList(["hidden list"]),
        HostileRuntimeReportTuple(("hidden tuple",)),
    ):
        with pytest.raises(TypeError) as exc:
            runtime_worker._ensure_runtime_report_json_safe(value)

        diagnostic = str(exc.value)
        assert diagnostic == "non-JSON runtime report value"
        assert "HostileRuntimeReport" not in diagnostic
        assert "client_secret" not in diagnostic
        assert "subclass-secret" not in diagnostic
        assert "hidden" not in diagnostic


class _RecordingPruneStore:
    def __init__(self, policies: list[RetentionPolicy]) -> None:
        self._policies = policies

    def __enter__(self) -> _RecordingPruneStore:
        return self

    def __exit__(self, *_args: object) -> None:
        pass

    def prune_expired_records(
        self,
        *,
        policy: RetentionPolicy,
        now: datetime | None = None,
    ) -> RetentionPruneReport:
        self._policies.append(policy)
        return _empty_report()


def _prune_store_factory(
    database_urls: list[str],
    policies: list[RetentionPolicy],
) -> runtime_worker.PruneStoreFactory:
    def create(database_url: str) -> runtime_worker.PrunableStore:
        database_urls.append(database_url)
        return _RecordingPruneStore(policies)

    return create


class _RecordingAlertTransport:
    def __init__(self, responses: list[HttpResponse]) -> None:
        self.responses = responses
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        return self.responses.pop(0)


class _RecordingRecoveryStore:
    def __init__(
        self,
        calls: list[tuple[datetime, int, str]],
        jobs: list[FulfillmentJobRecord],
    ) -> None:
        self._calls = calls
        self._jobs = jobs

    def __enter__(self) -> _RecordingRecoveryStore:
        return self

    def __exit__(self, *_args: object) -> None:
        pass

    def requeue_stale_running_jobs(
        self,
        *,
        stale_before: datetime,
        limit: int,
        message: str,
    ) -> list[FulfillmentJobRecord]:
        self._calls.append((stale_before, limit, message))
        return self._jobs


def _recovery_store_factory(
    database_urls: list[str],
    calls: list[tuple[datetime, int, str]],
    jobs: list[FulfillmentJobRecord],
) -> runtime_worker.StaleJobRecoveryStoreFactory:
    def create(database_url: str) -> runtime_worker.StaleJobRecoveryStore:
        database_urls.append(database_url)
        return _RecordingRecoveryStore(calls, jobs)

    return create


def _running_job() -> FulfillmentJobRecord:
    return FulfillmentJobRecord(
        job_id="job-evt-stale",
        event_id="evt-stale",
        story_number="STRY0010103",
        story_sys_id=None,
        status="queued",
        attempt_count=2,
        created_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
        updated_at=datetime(2026, 5, 13, 16, 0, tzinfo=UTC),
        locked_by=None,
        locked_at=None,
        last_error=None,
        correlation_id="corr-evt-stale",
    )


def test_run_loop_invokes_pruner_only_when_interval_elapses(tmp_path: Path) -> None:
    clock_values = [0.0, 10.0, 3700.0]
    prune_calls: list[str] = []

    def processor(_settings: RuntimeSettings) -> FulfillmentWorkerResult:
        return _idle_result()

    summary = runtime_worker.run_loop(
        settings=_settings(tmp_path),
        processor=processor,
        max_iterations=3,
        idle_sleep_seconds=0,
        sleep=lambda _seconds: None,
        pruner=lambda: prune_calls.append("pruned"),
        prune_interval_seconds=3600.0,
        clock=lambda: clock_values.pop(0),
    )

    assert summary.iterations == 3
    assert prune_calls == ["pruned", "pruned"]


@pytest.mark.parametrize(
    ("kwargs", "expected_error"),
    [
        ({"max_iterations": 0}, "JEDI_WORKER_MAX_ITERATIONS"),
        ({"max_iterations": -1}, "JEDI_WORKER_MAX_ITERATIONS"),
        (
            {"max_iterations": runtime_worker.MAX_WORKER_MAX_ITERATIONS + 1},
            "JEDI_WORKER_MAX_ITERATIONS",
        ),
        (
            {"max_iterations": None, "idle_sleep_seconds": 0},
            "JEDI_WORKER_IDLE_SLEEP_SECONDS",
        ),
        (
            {"idle_sleep_seconds": runtime_worker.MAX_WORKER_IDLE_SLEEP_SECONDS + 1},
            "JEDI_WORKER_IDLE_SLEEP_SECONDS",
        ),
        ({"idle_sleep_seconds": float("inf")}, "JEDI_WORKER_IDLE_SLEEP_SECONDS"),
        (
            {"pruner": lambda: None, "prune_interval_seconds": 0},
            "JEDI_RETENTION_PRUNE_INTERVAL_SECONDS",
        ),
        (
            {
                "pruner": lambda: None,
                "prune_interval_seconds": runtime_worker.MAX_MAINTENANCE_INTERVAL_SECONDS + 1,
            },
            "JEDI_RETENTION_PRUNE_INTERVAL_SECONDS",
        ),
        (
            {"stale_job_recoverer": lambda: None, "stale_job_recovery_interval_seconds": 0},
            "JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS",
        ),
        (
            {
                "stale_job_recoverer": lambda: None,
                "stale_job_recovery_interval_seconds": float("nan"),
            },
            "JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS",
        ),
    ],
)
def test_run_loop_rejects_invalid_controls_before_processing(
    tmp_path: Path,
    kwargs: dict[str, object],
    expected_error: str,
) -> None:
    processed: list[str] = []

    def processor(_settings: RuntimeSettings) -> FulfillmentWorkerResult:
        processed.append("processed")
        return _idle_result()

    with pytest.raises(ValueError, match=expected_error):
        runtime_worker.run_loop(
            settings=_settings(tmp_path),
            processor=processor,
            sleep=lambda _seconds: None,
            **kwargs,  # type: ignore[arg-type]
        )

    assert processed == []


def test_run_loop_rejects_stop_on_failure_in_production_before_processing(
    tmp_path: Path,
) -> None:
    processed: list[str] = []
    settings = _settings(tmp_path).model_copy(update={"runtime_environment": "production"})

    def processor(_settings: RuntimeSettings) -> FulfillmentWorkerResult:
        processed.append("processed")
        return _idle_result()

    with pytest.raises(ValueError, match="JEDI_WORKER_STOP_ON_FAILURE"):
        runtime_worker.run_loop(
            settings=settings,
            processor=processor,
            max_iterations=1,
            idle_sleep_seconds=0,
            sleep=lambda _seconds: None,
            stop_on_failure=True,
        )

    assert processed == []


def test_run_loop_validates_runtime_environment_before_stop_on_failure_branch(
    tmp_path: Path,
) -> None:
    class SecretBearingRuntimeEnvironment(str):
        def __eq__(self, _other: object) -> bool:
            raise RuntimeError("client_secret=worker-loop-env-secret")

    processed: list[str] = []
    settings = _settings(tmp_path).model_copy(
        update={"runtime_environment": SecretBearingRuntimeEnvironment("production")}
    )

    def processor(_settings: RuntimeSettings) -> FulfillmentWorkerResult:
        processed.append("processed")
        return _idle_result()

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_worker.run_loop(
            settings=settings,
            processor=processor,
            max_iterations=1,
            idle_sleep_seconds=0,
            sleep=lambda _seconds: None,
            stop_on_failure=True,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_ENVIRONMENT must be a string runtime setting"
    assert "SecretBearingRuntimeEnvironment" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "worker-loop-env-secret" not in diagnostic
    assert processed == []


def test_run_once_validates_runtime_role_before_api_role_branch(tmp_path: Path) -> None:
    class SecretBearingRuntimeRole(str):
        def __eq__(self, _other: object) -> bool:
            raise RuntimeError("client_secret=worker-run-once-role-secret")

    processed: list[str] = []
    settings = _settings(tmp_path).model_copy(
        update={"runtime_role": SecretBearingRuntimeRole("worker")}
    )

    def processor(_settings: RuntimeSettings) -> FulfillmentWorkerResult:
        processed.append("processed")
        return _idle_result()

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_worker.run_once(settings=settings, processor=processor)

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_RUNTIME_ROLE must be a string runtime setting"
    assert "SecretBearingRuntimeRole" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "worker-run-once-role-secret" not in diagnostic
    assert processed == []


def test_run_loop_logs_pruner_failure_and_continues_processing(
    tmp_path: Path,
    caplog: Any,
) -> None:
    caplog.set_level("WARNING", logger="jedi_devproject.runtime_worker")
    processed: list[str] = []

    def failing_pruner() -> None:
        raise RuntimeError("retention prune failed password=secret-value")

    def processor(_settings: RuntimeSettings) -> FulfillmentWorkerResult:
        processed.append("processed")
        return _idle_result()

    summary = runtime_worker.run_loop(
        settings=_settings(tmp_path),
        processor=processor,
        max_iterations=1,
        idle_sleep_seconds=0,
        sleep=lambda _seconds: None,
        pruner=failing_pruner,
    )

    assert processed == ["processed"]
    assert summary.iterations == 1
    assert summary.idle == 1
    assert summary.prune_failures == 1
    assert "worker retention prune failed" in caplog.text
    assert "secret-value" not in caplog.text
    assert "***REDACTED***" in caplog.text


def test_run_loop_logs_unstringifiable_pruner_failure_and_continues_processing(
    tmp_path: Path,
    caplog: Any,
) -> None:
    caplog.set_level("WARNING", logger="jedi_devproject.runtime_worker")
    processed: list[str] = []

    def failing_pruner() -> None:
        raise _UnstringifiableRuntimeWorkerError("unused")

    def processor(_settings: RuntimeSettings) -> FulfillmentWorkerResult:
        processed.append("processed")
        return _idle_result()

    summary = runtime_worker.run_loop(
        settings=_settings(tmp_path),
        processor=processor,
        max_iterations=1,
        idle_sleep_seconds=0,
        sleep=lambda _seconds: None,
        pruner=failing_pruner,
    )

    assert processed == ["processed"]
    assert summary.prune_failures == 1
    assert "worker retention prune failed" in caplog.text
    assert "runtime worker raised unstringifiable _UnstringifiableRuntimeWorkerError" in caplog.text
    assert "client-secret-value" not in caplog.text


def test_run_loop_invokes_stale_job_recoverer_only_when_interval_elapses(
    tmp_path: Path,
) -> None:
    clock_values = [0.0, 10.0, 3700.0]
    recover_calls: list[str] = []

    summary = runtime_worker.run_loop(
        settings=_settings(tmp_path),
        processor=lambda _settings: _idle_result(),
        max_iterations=3,
        idle_sleep_seconds=0,
        sleep=lambda _seconds: None,
        stale_job_recoverer=lambda: recover_calls.append("recovered"),
        stale_job_recovery_interval_seconds=3600.0,
        clock=lambda: clock_values.pop(0),
    )

    assert summary.iterations == 3
    assert recover_calls == ["recovered", "recovered"]


def test_run_loop_logs_stale_recovery_failure_and_continues_processing(
    tmp_path: Path,
    caplog: Any,
) -> None:
    caplog.set_level("WARNING", logger="jedi_devproject.runtime_worker")
    processed: list[str] = []

    def failing_stale_recoverer() -> runtime_worker.StaleJobRequeueReport:
        raise RuntimeError("stale recovery failed access_token=token-value")

    def processor(_settings: RuntimeSettings) -> FulfillmentWorkerResult:
        processed.append("processed")
        return _idle_result()

    summary = runtime_worker.run_loop(
        settings=_settings(tmp_path),
        processor=processor,
        max_iterations=1,
        idle_sleep_seconds=0,
        sleep=lambda _seconds: None,
        stale_job_recoverer=failing_stale_recoverer,
    )

    assert processed == ["processed"]
    assert summary.iterations == 1
    assert summary.idle == 1
    assert summary.stale_job_recovery_failures == 1
    assert "worker stale job recovery failed" in caplog.text
    assert "token-value" not in caplog.text
    assert "***REDACTED***" in caplog.text


def test_run_loop_logs_unstringifiable_stale_recovery_failure_and_continues_processing(
    tmp_path: Path,
    caplog: Any,
) -> None:
    caplog.set_level("WARNING", logger="jedi_devproject.runtime_worker")
    processed: list[str] = []

    def failing_stale_recoverer() -> runtime_worker.StaleJobRequeueReport:
        raise _UnstringifiableRuntimeWorkerError("unused")

    def processor(_settings: RuntimeSettings) -> FulfillmentWorkerResult:
        processed.append("processed")
        return _idle_result()

    summary = runtime_worker.run_loop(
        settings=_settings(tmp_path),
        processor=processor,
        max_iterations=1,
        idle_sleep_seconds=0,
        sleep=lambda _seconds: None,
        stale_job_recoverer=failing_stale_recoverer,
    )

    assert processed == ["processed"]
    assert summary.stale_job_recovery_failures == 1
    assert "worker stale job recovery failed" in caplog.text
    assert "runtime worker raised unstringifiable _UnstringifiableRuntimeWorkerError" in caplog.text
    assert "client-secret-value" not in caplog.text


def test_run_loop_emits_stale_requeue_alert_only_when_jobs_requeued(
    tmp_path: Path,
) -> None:
    reports = [
        runtime_worker.StaleJobRequeueReport(
            enabled=True,
            requeued_at=datetime(2026, 5, 13, 17, 0, tzinfo=UTC),
            stale_before=datetime(2026, 5, 13, 16, 45, tzinfo=UTC),
            stale_after_seconds=900,
            requeued_count=0,
            job_ids=[],
        ),
        runtime_worker.StaleJobRequeueReport(
            enabled=True,
            requeued_at=datetime(2026, 5, 13, 18, 0, tzinfo=UTC),
            stale_before=datetime(2026, 5, 13, 17, 45, tzinfo=UTC),
            stale_after_seconds=900,
            requeued_count=1,
            job_ids=["job-evt-stale"],
        ),
    ]
    emitted: list[runtime_worker.StaleJobRequeueReport] = []
    clock_values = [0.0, 3700.0]

    summary = runtime_worker.run_loop(
        settings=_settings(tmp_path),
        processor=lambda _settings: _idle_result(),
        max_iterations=2,
        idle_sleep_seconds=0,
        sleep=lambda _seconds: None,
        stale_job_recoverer=lambda: reports.pop(0),
        stale_job_requeue_alert_emitter=emitted.append,
        stale_job_recovery_interval_seconds=3600.0,
        clock=lambda: clock_values.pop(0),
    )

    assert summary.iterations == 2
    assert summary.alerts_emitted == 1
    assert summary.alert_failures == 0
    assert [report.job_ids for report in emitted] == [["job-evt-stale"]]


def test_run_loop_counts_stale_requeue_alert_delivery_failures(
    tmp_path: Path,
    caplog: Any,
) -> None:
    caplog.set_level("WARNING", logger="jedi_devproject.runtime_worker")
    report = runtime_worker.StaleJobRequeueReport(
        enabled=True,
        requeued_at=datetime(2026, 5, 13, 18, 0, tzinfo=UTC),
        stale_before=datetime(2026, 5, 13, 17, 45, tzinfo=UTC),
        stale_after_seconds=900,
        requeued_count=1,
        job_ids=["job-evt-stale"],
    )

    def failing_alert_emitter(_report: runtime_worker.StaleJobRequeueReport) -> None:
        raise RuntimeError("alert backend unavailable access_token=token-value")

    summary = runtime_worker.run_loop(
        settings=_settings(tmp_path),
        processor=lambda _settings: _idle_result(),
        max_iterations=1,
        idle_sleep_seconds=0,
        sleep=lambda _seconds: None,
        stale_job_recoverer=lambda: report,
        stale_job_requeue_alert_emitter=failing_alert_emitter,
    )

    assert summary.iterations == 1
    assert summary.idle == 1
    assert summary.alerts_emitted == 0
    assert summary.alert_failures == 1
    assert "stale requeue alert delivery failed for jobs job-evt-stale" in caplog.text
    assert "token-value" not in caplog.text
    assert "***REDACTED***" in caplog.text


def test_run_loop_counts_unstringifiable_stale_requeue_alert_delivery_failures(
    tmp_path: Path,
    caplog: Any,
) -> None:
    caplog.set_level("WARNING", logger="jedi_devproject.runtime_worker")
    report = runtime_worker.StaleJobRequeueReport(
        enabled=True,
        requeued_at=datetime(2026, 5, 13, 18, 0, tzinfo=UTC),
        stale_before=datetime(2026, 5, 13, 17, 45, tzinfo=UTC),
        stale_after_seconds=900,
        requeued_count=1,
        job_ids=["job-evt-stale"],
    )

    def failing_alert_emitter(_report: runtime_worker.StaleJobRequeueReport) -> None:
        raise _UnstringifiableRuntimeWorkerError("unused")

    summary = runtime_worker.run_loop(
        settings=_settings(tmp_path),
        processor=lambda _settings: _idle_result(),
        max_iterations=1,
        idle_sleep_seconds=0,
        sleep=lambda _seconds: None,
        stale_job_recoverer=lambda: report,
        stale_job_requeue_alert_emitter=failing_alert_emitter,
    )

    assert summary.idle == 1
    assert summary.alert_failures == 1
    assert "stale requeue alert delivery failed for jobs job-evt-stale" in caplog.text
    assert "runtime worker raised unstringifiable _UnstringifiableRuntimeWorkerError" in caplog.text
    assert "client-secret-value" not in caplog.text


def test_run_loop_counts_unstringifiable_worker_alert_delivery_failures(
    tmp_path: Path,
    caplog: Any,
) -> None:
    caplog.set_level("WARNING", logger="jedi_devproject.runtime_worker")

    def failing_alert_emitter(_result: FulfillmentWorkerResult) -> None:
        raise _UnstringifiableRuntimeWorkerError("unused")

    summary = runtime_worker.run_loop(
        settings=_settings(tmp_path),
        processor=lambda _settings: _failed_result(),
        max_iterations=1,
        idle_sleep_seconds=0,
        sleep=lambda _seconds: None,
        alert_emitter=failing_alert_emitter,
    )

    assert summary.failed == 1
    assert summary.alert_failures == 1
    assert summary.stopped_reason == "failed_job"
    assert "worker alert delivery failed for job job-evt-failed" in caplog.text
    assert "runtime worker raised unstringifiable _UnstringifiableRuntimeWorkerError" in caplog.text
    assert "client-secret-value" not in caplog.text


def test_run_loop_without_pruner_never_consults_clock(tmp_path: Path) -> None:
    def failing_clock() -> float:
        raise AssertionError("clock must not be consulted when no pruner is configured")

    summary = runtime_worker.run_loop(
        settings=_settings(tmp_path),
        processor=lambda _settings: _idle_result(),
        max_iterations=1,
        idle_sleep_seconds=0,
        sleep=lambda _seconds: None,
        clock=failing_clock,
    )

    assert summary.iterations == 1


def test_load_worker_settings_defaults_retention_disabled(tmp_path: Path) -> None:
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

    settings = runtime_worker.load_worker_settings(env_path)

    assert settings.retention.enabled is False
    assert settings.retention.artifact_blob_retention_days is None
    assert settings.retention.job_event_retention_days is None
    assert settings.prune_interval_seconds == 3600.0
    assert settings.stale_job_requeue_enabled is False
    assert settings.stale_job_requeue_interval_seconds == 3600.0
    assert settings.stale_job_requeue_batch_size == 10


def test_load_worker_settings_reads_retention_and_stale_requeue_environment(
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
                "JEDI_RETENTION_ARTIFACT_BLOB_DAYS=90",
                "JEDI_RETENTION_JOB_EVENT_DAYS=365",
                "JEDI_RETENTION_PRUNE_BATCH_SIZE=250",
                "JEDI_RETENTION_PRUNE_INTERVAL_SECONDS=600",
                "JEDI_STALE_JOB_REQUEUE_ENABLED=true",
                "JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS=300",
                "JEDI_STALE_JOB_REQUEUE_BATCH_SIZE=7",
            ]
        ),
        encoding="utf-8",
    )

    settings = runtime_worker.load_worker_settings(env_path)

    assert settings.retention.enabled is True
    assert settings.retention.artifact_blob_retention_days == 90
    assert settings.retention.job_event_retention_days == 365
    assert settings.retention.prune_batch_size == 250
    assert settings.prune_interval_seconds == 600.0
    assert settings.stale_job_requeue_enabled is True
    assert settings.stale_job_requeue_interval_seconds == 300.0
    assert settings.stale_job_requeue_batch_size == 7


def test_load_worker_settings_rejects_malformed_worker_boolean_values(
    tmp_path: Path,
) -> None:
    for setting_name in [
        "JEDI_WORKER_STOP_ON_FAILURE",
        "JEDI_STALE_JOB_REQUEUE_ENABLED",
    ]:
        env_path = tmp_path / f"{setting_name}.env"
        env_path.write_text(
            "\n".join(
                [
                    "DATABASE_URL=postgresql://jedi:jedi@postgres:5432/jedi",
                    "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                    "SERVICENOW_CLIENT_ID=client-id",
                    "SERVICENOW_CLIENT_SECRET=client-secret",
                    "JEDI_AUDIT_ROOT=/app/artifacts/audit",
                    f"{setting_name}=ture",
                ]
            ),
            encoding="utf-8",
        )

        try:
            runtime_worker.load_worker_settings(env_path)
        except ValueError as exc:
            assert setting_name in str(exc)
            assert "must be a boolean value" in str(exc)
        else:
            raise AssertionError(f"malformed {setting_name} did not raise")


def test_load_worker_settings_rejects_padded_worker_boolean_values(
    tmp_path: Path,
) -> None:
    boolean_settings = {
        "JEDI_WORKER_STOP_ON_FAILURE": 'JEDI_WORKER_STOP_ON_FAILURE=" true"',
        "JEDI_STALE_JOB_REQUEUE_ENABLED": 'JEDI_STALE_JOB_REQUEUE_ENABLED="false\tfallback"',
    }
    for setting_name, env_line in boolean_settings.items():
        env_path = tmp_path / f"{setting_name}.env"
        env_path.write_text(
            "\n".join(
                [
                    "DATABASE_URL=postgresql://jedi:jedi@postgres:5432/jedi",
                    "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                    "SERVICENOW_CLIENT_ID=client-id",
                    "SERVICENOW_CLIENT_SECRET=client-secret",
                    "JEDI_AUDIT_ROOT=/app/artifacts/audit",
                    env_line,
                ]
            ),
            encoding="utf-8",
        )

        try:
            runtime_worker.load_worker_settings(env_path)
        except ValueError as exc:
            message = str(exc)
            assert setting_name in message
            assert "without padding or control characters" in message
            assert "fallback" not in message
            assert "\t" not in message
        else:
            raise AssertionError(f"padded {setting_name} did not raise")


def test_load_worker_settings_rejects_malformed_worker_numeric_values(
    tmp_path: Path,
) -> None:
    numeric_settings = {
        "JEDI_WORKER_MAX_ITERATIONS": "integer",
        "JEDI_STALE_JOB_REQUEUE_BATCH_SIZE": "integer",
        "JEDI_WORKER_IDLE_SLEEP_SECONDS": "number",
        "JEDI_RETENTION_PRUNE_INTERVAL_SECONDS": "number",
        "JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS": "number",
    }
    for setting_name, expected_type in numeric_settings.items():
        env_path = tmp_path / f"{setting_name}.env"
        env_path.write_text(
            "\n".join(
                [
                    "DATABASE_URL=postgresql://jedi:jedi@postgres:5432/jedi",
                    "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                    "SERVICENOW_CLIENT_ID=client-id",
                    "SERVICENOW_CLIENT_SECRET=client-secret",
                    "JEDI_AUDIT_ROOT=/app/artifacts/audit",
                    f"{setting_name}=invalid",
                ]
            ),
            encoding="utf-8",
        )

        try:
            runtime_worker.load_worker_settings(env_path)
        except ValueError as exc:
            assert setting_name in str(exc)
            assert f"must be an {expected_type}" in str(exc) or (
                f"must be a {expected_type}" in str(exc)
            )
        else:
            raise AssertionError(f"malformed {setting_name} did not raise")


def test_load_worker_settings_rejects_padded_worker_numeric_values(
    tmp_path: Path,
) -> None:
    numeric_settings = {
        "JEDI_WORKER_MAX_ITERATIONS": (
            'JEDI_WORKER_MAX_ITERATIONS=" 2"',
            "integer without padding or control characters",
        ),
        "JEDI_STALE_JOB_REQUEUE_BATCH_SIZE": (
            'JEDI_STALE_JOB_REQUEUE_BATCH_SIZE="7 "',
            "integer without padding or control characters",
        ),
        "JEDI_WORKER_IDLE_SLEEP_SECONDS": (
            'JEDI_WORKER_IDLE_SLEEP_SECONDS="0.5 "',
            "number without padding or control characters",
        ),
        "JEDI_RETENTION_PRUNE_INTERVAL_SECONDS": (
            'JEDI_RETENTION_PRUNE_INTERVAL_SECONDS="3600\tfallback"',
            "number without padding or control characters",
        ),
        "JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS": (
            'JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS=" 3600"',
            "number without padding or control characters",
        ),
    }
    for setting_name, (env_line, expected_message) in numeric_settings.items():
        env_path = tmp_path / f"{setting_name}.env"
        env_path.write_text(
            "\n".join(
                [
                    "DATABASE_URL=postgresql://jedi:jedi@postgres:5432/jedi",
                    "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                    "SERVICENOW_CLIENT_ID=client-id",
                    "SERVICENOW_CLIENT_SECRET=client-secret",
                    "JEDI_AUDIT_ROOT=/app/artifacts/audit",
                    env_line,
                ]
            ),
            encoding="utf-8",
        )

        try:
            runtime_worker.load_worker_settings(env_path)
        except ValueError as exc:
            message = str(exc)
            assert setting_name in message
            assert expected_message in message
            assert "fallback" not in message
            assert "\t" not in message
        else:
            raise AssertionError(f"padded {setting_name} did not raise")


def test_load_worker_settings_rejects_non_decimal_worker_integer_values(
    tmp_path: Path,
) -> None:
    worker_settings = {
        "JEDI_WORKER_MAX_ITERATIONS": "1_000",
        "JEDI_STALE_JOB_REQUEUE_BATCH_SIZE": "+10",
    }
    for setting_name, setting_value in worker_settings.items():
        env_path = tmp_path / f"{setting_name}.env"
        env_path.write_text(
            "\n".join(
                [
                    "DATABASE_URL=postgresql://jedi:jedi@postgres:5432/jedi",
                    "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                    "SERVICENOW_CLIENT_ID=client-id",
                    "SERVICENOW_CLIENT_SECRET=client-secret",
                    "JEDI_AUDIT_ROOT=/app/artifacts/audit",
                    f"{setting_name}={setting_value}",
                ]
            ),
            encoding="utf-8",
        )

        try:
            runtime_worker.load_worker_settings(env_path)
        except ValueError as exc:
            message = str(exc)
            assert setting_name in message
            assert "base-10 digits only" in message
            assert setting_value not in message
        else:
            raise AssertionError(f"non-decimal {setting_name} did not raise")


def test_load_worker_settings_rejects_non_finite_worker_float_values(
    tmp_path: Path,
) -> None:
    for setting_name, invalid_value in [
        ("JEDI_WORKER_IDLE_SLEEP_SECONDS", "nan"),
        ("JEDI_RETENTION_PRUNE_INTERVAL_SECONDS", "inf"),
        ("JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS", "-inf"),
    ]:
        env_path = tmp_path / f"{setting_name}.env"
        env_path.write_text(
            "\n".join(
                [
                    "DATABASE_URL=postgresql://jedi:jedi@postgres:5432/jedi",
                    "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                    "SERVICENOW_CLIENT_ID=client-id",
                    "SERVICENOW_CLIENT_SECRET=client-secret",
                    "JEDI_AUDIT_ROOT=/app/artifacts/audit",
                    f"{setting_name}={invalid_value}",
                ]
            ),
            encoding="utf-8",
        )

        try:
            runtime_worker.load_worker_settings(env_path)
        except ValueError as exc:
            assert setting_name in str(exc)
            assert "must be a finite number" in str(exc)
        else:
            raise AssertionError(f"non-finite {setting_name} did not raise")


def test_load_worker_settings_rejects_non_ascii_fixed_decimal_worker_float_values(
    tmp_path: Path,
) -> None:
    worker_settings = {
        "JEDI_WORKER_IDLE_SLEEP_SECONDS": "1_000.5",
        "JEDI_RETENTION_PRUNE_INTERVAL_SECONDS": "１２.5",
        "JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS": "1e3",
    }
    for setting_name, setting_value in worker_settings.items():
        env_path = tmp_path / f"{setting_name}.env"
        env_path.write_text(
            "\n".join(
                [
                    "DATABASE_URL=postgresql://jedi:jedi@postgres:5432/jedi",
                    "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                    "SERVICENOW_CLIENT_ID=client-id",
                    "SERVICENOW_CLIENT_SECRET=client-secret",
                    "JEDI_AUDIT_ROOT=/app/artifacts/audit",
                    f"{setting_name}={setting_value}",
                ]
            ),
            encoding="utf-8",
        )

        try:
            runtime_worker.load_worker_settings(env_path)
        except ValueError as exc:
            message = str(exc)
            assert setting_name in message
            assert "ASCII decimal number" in message
            assert setting_value not in message
        else:
            raise AssertionError(f"non-ASCII fixed decimal {setting_name} did not raise")


class UnstringifiableWorkerFloatError(ValueError):
    def __str__(self) -> str:
        raise ValueError("client-secret-value")


def test_worker_optional_float_wraps_unstringifiable_parser_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_parse_optional_ascii_decimal_float(
        _value: str | None,
        *,
        name: str,
    ) -> float | None:
        raise UnstringifiableWorkerFloatError

    monkeypatch.setattr(
        runtime_worker,
        "parse_optional_ascii_decimal_float",
        fail_parse_optional_ascii_decimal_float,
    )

    with pytest.raises(ValueError) as exc:
        runtime_worker._optional_float(
            "1.5",
            name="JEDI_WORKER_IDLE_SLEEP_SECONDS",
            default=1.0,
        )

    assert str(exc.value) == "runtime worker raised unstringifiable UnstringifiableWorkerFloatError"
    assert "client-secret-value" not in str(exc.value)
    assert exc.value.__cause__ is None


def test_load_worker_settings_rejects_non_positive_stale_requeue_batch_size(
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
                "JEDI_STALE_JOB_REQUEUE_ENABLED=true",
                "JEDI_STALE_JOB_REQUEUE_BATCH_SIZE=0",
            ]
        ),
        encoding="utf-8",
    )

    try:
        runtime_worker.load_worker_settings(env_path)
    except ValueError as exc:
        assert "JEDI_STALE_JOB_REQUEUE_BATCH_SIZE must be greater than 0" in str(exc)
    else:
        raise AssertionError("non-positive stale job requeue batch size did not raise")


def test_load_worker_settings_rejects_excessive_stale_requeue_batch_size(
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
                "JEDI_STALE_JOB_REQUEUE_ENABLED=true",
                "JEDI_STALE_JOB_REQUEUE_BATCH_SIZE=1000000",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc:
        runtime_worker.load_worker_settings(env_path)

    message = str(exc.value)
    assert "JEDI_STALE_JOB_REQUEUE_BATCH_SIZE must be at most 100" in message
    assert "1000000" not in message


def test_load_worker_settings_rejects_excessive_retention_prune_batch_size(
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
                "JEDI_RETENTION_ARTIFACT_BLOB_DAYS=90",
                "JEDI_RETENTION_PRUNE_BATCH_SIZE=1000000",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc:
        runtime_worker.load_worker_settings(env_path)

    message = str(exc.value)
    assert "JEDI_RETENTION_PRUNE_BATCH_SIZE must be at most 5000" in message
    assert "1000000" not in message


def test_load_worker_settings_rejects_non_positive_stale_requeue_interval(
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
                "JEDI_STALE_JOB_REQUEUE_ENABLED=true",
                "JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS=0",
            ]
        ),
        encoding="utf-8",
    )

    try:
        runtime_worker.load_worker_settings(env_path)
    except ValueError as exc:
        assert "JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS must be greater than 0" in str(exc)
    else:
        raise AssertionError("non-positive stale job requeue interval did not raise")


def test_load_worker_settings_rejects_excessive_worker_scheduler_intervals(
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
                "JEDI_WORKER_IDLE_SLEEP_SECONDS=3600",
                "JEDI_RETENTION_PRUNE_INTERVAL_SECONDS=604800",
                "JEDI_STALE_JOB_REQUEUE_ENABLED=true",
                "JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS=604800",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc:
        runtime_worker.load_worker_settings(env_path)

    message = str(exc.value)
    assert "JEDI_WORKER_IDLE_SLEEP_SECONDS must be at most 300" in message
    assert "JEDI_RETENTION_PRUNE_INTERVAL_SECONDS must be at most 86400" in message
    assert "JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS must be at most 86400" in message
    assert "604800" not in message


def test_load_worker_settings_rejects_non_positive_retention_prune_interval(
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
                "JEDI_RETENTION_ARTIFACT_BLOB_DAYS=90",
                "JEDI_RETENTION_PRUNE_INTERVAL_SECONDS=0",
            ]
        ),
        encoding="utf-8",
    )

    try:
        runtime_worker.load_worker_settings(env_path)
    except ValueError as exc:
        assert "JEDI_RETENTION_PRUNE_INTERVAL_SECONDS must be greater than 0" in str(exc)
    else:
        raise AssertionError("non-positive retention prune interval did not raise")


def test_load_worker_settings_rejects_unbounded_zero_idle_sleep(
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
                "JEDI_WORKER_IDLE_SLEEP_SECONDS=0",
            ]
        ),
        encoding="utf-8",
    )

    try:
        runtime_worker.load_worker_settings(env_path)
    except ValueError as exc:
        assert "JEDI_WORKER_IDLE_SLEEP_SECONDS must be greater than 0" in str(exc)
    else:
        raise AssertionError("unbounded zero idle sleep did not raise")


def test_load_worker_settings_rejects_non_positive_max_iterations(
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
                "JEDI_WORKER_MAX_ITERATIONS=0",
            ]
        ),
        encoding="utf-8",
    )

    try:
        runtime_worker.load_worker_settings(env_path)
    except ValueError as exc:
        assert "JEDI_WORKER_MAX_ITERATIONS must be greater than 0" in str(exc)
    else:
        raise AssertionError("non-positive worker max iterations did not raise")


def test_load_worker_settings_rejects_excessive_max_iterations(
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
                "JEDI_WORKER_MAX_ITERATIONS=1000000",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc:
        runtime_worker.load_worker_settings(env_path)

    message = str(exc.value)
    assert "JEDI_WORKER_MAX_ITERATIONS must be at most 10000 when configured" in message
    assert "1000000" not in message


def test_load_worker_settings_rejects_stop_on_failure_in_production(
    tmp_path: Path,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "JEDI_ENVIRONMENT=production",
                "JEDI_RUNTIME_ROLE=worker",
                "DATABASE_URL=postgresql://jedi:jedi@postgres:5432/jedi",
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
                "JEDI_AUDIT_ROOT=/app/artifacts/audit",
                "JEDI_MODEL_PROVIDER=openai",
                "OPENAI_API_KEY=openai-key",
                "OPENAI_MODEL=gpt-5",
                "JEDI_WORKER_STOP_ON_FAILURE=true",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc:
        runtime_worker.load_worker_settings(env_path)

    message = str(exc.value)
    assert "JEDI_WORKER_STOP_ON_FAILURE must be false in production" in message
    assert "openai-key" not in message


def test_prune_operational_store_uses_store_factory_and_prints_report(
    tmp_path: Path,
    capsys: Any,
) -> None:
    database_urls: list[str] = []
    policies: list[RetentionPolicy] = []
    policy = RetentionPolicy(artifact_blob_retention_days=90)

    report = runtime_worker.prune_operational_store(
        settings=_settings(tmp_path),
        policy=policy,
        store_factory=_prune_store_factory(database_urls, policies),
    )

    captured = capsys.readouterr()
    assert database_urls == ["postgresql://jedi:jedi@postgres:5432/jedi"]
    assert policies == [policy]
    assert report.enabled is True
    assert '"enabled":true' in captured.out


@pytest.mark.parametrize(
    ("policy", "expected_error"),
    [
        (
            RetentionPolicy.model_construct(artifact_blob_retention_days=0),
            "JEDI_RETENTION_ARTIFACT_BLOB_DAYS",
        ),
        (
            RetentionPolicy.model_construct(artifact_blob_retention_days=True),
            "JEDI_RETENTION_ARTIFACT_BLOB_DAYS",
        ),
        (
            RetentionPolicy.model_construct(artifact_blob_retention_days="90"),
            "JEDI_RETENTION_ARTIFACT_BLOB_DAYS",
        ),
        (
            RetentionPolicy.model_construct(job_event_retention_days=0),
            "JEDI_RETENTION_JOB_EVENT_DAYS",
        ),
        (
            RetentionPolicy.model_construct(job_event_retention_days=True),
            "JEDI_RETENTION_JOB_EVENT_DAYS",
        ),
        (
            RetentionPolicy.model_construct(job_event_retention_days="365"),
            "JEDI_RETENTION_JOB_EVENT_DAYS",
        ),
        (
            RetentionPolicy.model_construct(prune_batch_size=0),
            "JEDI_RETENTION_PRUNE_BATCH_SIZE",
        ),
        (
            RetentionPolicy.model_construct(prune_batch_size=True),
            "JEDI_RETENTION_PRUNE_BATCH_SIZE",
        ),
        (
            RetentionPolicy.model_construct(prune_batch_size="500"),
            "JEDI_RETENTION_PRUNE_BATCH_SIZE",
        ),
        (
            RetentionPolicy.model_construct(prune_batch_size=5001),
            "JEDI_RETENTION_PRUNE_BATCH_SIZE",
        ),
    ],
)
def test_prune_operational_store_rejects_invalid_policy_before_store_open(
    tmp_path: Path,
    policy: RetentionPolicy,
    expected_error: str,
) -> None:
    def store_factory(_database_url: str) -> runtime_worker.PrunableStore:
        raise AssertionError("store factory should not be called")

    with pytest.raises(ValueError, match=expected_error):
        runtime_worker.prune_operational_store(
            settings=_settings(tmp_path),
            policy=policy,
            store_factory=store_factory,
        )


def test_prune_operational_store_rejects_database_url_string_subclass_before_store_open(
    tmp_path: Path,
) -> None:
    class SecretBearingDatabaseUrl(str):
        def __str__(self) -> str:
            return "postgresql://jedi:client_secret=maintenance-prune-secret@postgres/jedi"

    settings = _settings(tmp_path).model_copy(
        update={"database_url": SecretBearingDatabaseUrl("postgresql://jedi@postgres/jedi")}
    )

    def store_factory(_database_url: str) -> runtime_worker.PrunableStore:
        raise AssertionError("store factory should not be called")

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_worker.prune_operational_store(
            settings=settings,
            policy=RetentionPolicy(artifact_blob_retention_days=90),
            store_factory=store_factory,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "DATABASE_URL must be a string runtime setting"
    assert "SecretBearingDatabaseUrl" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "maintenance-prune-secret" not in diagnostic


def test_prune_operational_store_rejects_malformed_database_url_before_store_open(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(update={"database_url": "sqlite:///tmp/jedi.db"})

    def store_factory(_database_url: str) -> runtime_worker.PrunableStore:
        raise AssertionError("store factory should not be called")

    with pytest.raises(RuntimeConfigError, match="DATABASE_URL"):
        runtime_worker.prune_operational_store(
            settings=settings,
            policy=RetentionPolicy(artifact_blob_retention_days=90),
            store_factory=store_factory,
        )


def test_requeue_stale_running_jobs_uses_store_factory_and_prints_report(
    tmp_path: Path,
    capsys: Any,
) -> None:
    database_urls: list[str] = []
    calls: list[tuple[datetime, int, str]] = []
    now = datetime(2026, 5, 13, 17, 0, tzinfo=UTC)

    report = runtime_worker.requeue_stale_running_jobs(
        settings=_settings(tmp_path),
        stale_after_seconds=900,
        batch_size=7,
        now=now,
        store_factory=_recovery_store_factory(database_urls, calls, [_running_job()]),
    )

    captured = capsys.readouterr()
    assert database_urls == ["postgresql://jedi:jedi@postgres:5432/jedi"]
    assert calls == [
        (
            now - timedelta(seconds=900),
            7,
            "Stale running job requeued after 900 seconds without update",
        )
    ]
    assert report.requeued_count == 1
    assert report.job_ids == ["job-evt-stale"]
    assert '"requeued_count":1' in captured.out
    assert "job-evt-stale" in captured.out


@pytest.mark.parametrize(
    ("kwargs", "expected_error"),
    [
        ({"stale_after_seconds": 0, "batch_size": 7}, "JEDI_RUNNING_JOB_STALE_AFTER_SECONDS"),
        ({"stale_after_seconds": -1, "batch_size": 7}, "JEDI_RUNNING_JOB_STALE_AFTER_SECONDS"),
        ({"stale_after_seconds": True, "batch_size": 7}, "JEDI_RUNNING_JOB_STALE_AFTER_SECONDS"),
        ({"stale_after_seconds": "900", "batch_size": 7}, "JEDI_RUNNING_JOB_STALE_AFTER_SECONDS"),
        (
            {
                "stale_after_seconds": runtime_worker.MAX_RUNNING_JOB_STALE_AFTER_SECONDS + 1,
                "batch_size": 7,
            },
            "JEDI_RUNNING_JOB_STALE_AFTER_SECONDS",
        ),
        ({"stale_after_seconds": 900, "batch_size": 0}, "JEDI_STALE_JOB_REQUEUE_BATCH_SIZE"),
        ({"stale_after_seconds": 900, "batch_size": -1}, "JEDI_STALE_JOB_REQUEUE_BATCH_SIZE"),
        ({"stale_after_seconds": 900, "batch_size": True}, "JEDI_STALE_JOB_REQUEUE_BATCH_SIZE"),
        ({"stale_after_seconds": 900, "batch_size": "7"}, "JEDI_STALE_JOB_REQUEUE_BATCH_SIZE"),
        (
            {
                "stale_after_seconds": 900,
                "batch_size": runtime_worker.MAX_STALE_JOB_REQUEUE_BATCH_SIZE + 1,
            },
            "JEDI_STALE_JOB_REQUEUE_BATCH_SIZE",
        ),
    ],
)
def test_requeue_stale_running_jobs_rejects_invalid_controls_before_store_open(
    tmp_path: Path,
    kwargs: dict[str, object],
    expected_error: str,
) -> None:
    def store_factory(_database_url: str) -> runtime_worker.StaleJobRecoveryStore:
        raise AssertionError("store factory should not be called")

    with pytest.raises(ValueError, match=expected_error):
        runtime_worker.requeue_stale_running_jobs(
            settings=_settings(tmp_path),
            store_factory=store_factory,
            **kwargs,  # type: ignore[arg-type]
        )


def test_requeue_stale_running_jobs_rejects_database_url_string_subclass_before_store_open(
    tmp_path: Path,
) -> None:
    class SecretBearingDatabaseUrl(str):
        def __str__(self) -> str:
            return "postgresql://jedi:client_secret=maintenance-requeue-secret@postgres/jedi"

    settings = _settings(tmp_path).model_copy(
        update={"database_url": SecretBearingDatabaseUrl("postgresql://jedi@postgres/jedi")}
    )

    def store_factory(_database_url: str) -> runtime_worker.StaleJobRecoveryStore:
        raise AssertionError("store factory should not be called")

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_worker.requeue_stale_running_jobs(
            settings=settings,
            stale_after_seconds=900,
            batch_size=7,
            store_factory=store_factory,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "DATABASE_URL must be a string runtime setting"
    assert "SecretBearingDatabaseUrl" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "maintenance-requeue-secret" not in diagnostic


def test_requeue_stale_running_jobs_rejects_malformed_database_url_before_store_open(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(update={"database_url": "sqlite:///tmp/jedi.db"})

    def store_factory(_database_url: str) -> runtime_worker.StaleJobRecoveryStore:
        raise AssertionError("store factory should not be called")

    with pytest.raises(RuntimeConfigError, match="DATABASE_URL"):
        runtime_worker.requeue_stale_running_jobs(
            settings=settings,
            stale_after_seconds=900,
            batch_size=7,
            store_factory=store_factory,
        )


def test_main_wires_interval_gated_pruner_when_retention_enabled(
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
                "JEDI_RETENTION_ARTIFACT_BLOB_DAYS=90",
                "JEDI_RETENTION_PRUNE_INTERVAL_SECONDS=3600",
            ]
        ),
        encoding="utf-8",
    )
    database_urls: list[str] = []
    policies: list[RetentionPolicy] = []

    exit_code = runtime_worker.main(
        env_path=env_path,
        processor=lambda _settings: _idle_result(),
        sleep=lambda _seconds: None,
        prune_store_factory=_prune_store_factory(database_urls, policies),
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert database_urls == ["postgresql://jedi:jedi@postgres:5432/jedi"]
    assert len(policies) == 1
    assert policies[0].artifact_blob_retention_days == 90
    assert '"iterations":2' in captured.out


def test_main_wires_interval_gated_stale_job_recovery_when_enabled(
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
                "JEDI_WORKER_MAX_ITERATIONS=1",
                "JEDI_WORKER_IDLE_SLEEP_SECONDS=0",
                "JEDI_RUNNING_JOB_STALE_AFTER_SECONDS=900",
                "JEDI_STALE_JOB_REQUEUE_ENABLED=true",
                "JEDI_STALE_JOB_REQUEUE_BATCH_SIZE=7",
            ]
        ),
        encoding="utf-8",
    )
    database_urls: list[str] = []
    calls: list[tuple[datetime, int, str]] = []

    exit_code = runtime_worker.main(
        env_path=env_path,
        processor=lambda _settings: _idle_result(),
        sleep=lambda _seconds: None,
        stale_job_recovery_store_factory=_recovery_store_factory(
            database_urls,
            calls,
            [_running_job()],
        ),
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert database_urls == ["postgresql://jedi:jedi@postgres:5432/jedi"]
    assert calls[0][1] == 7
    assert calls[0][2] == "Stale running job requeued after 900 seconds without update"
    assert '"requeued_count":1' in captured.out


def test_main_wires_alert_webhook_emitter_when_enabled(
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
                "JEDI_WORKER_MAX_ITERATIONS=1",
                "JEDI_WORKER_IDLE_SLEEP_SECONDS=0",
                "JEDI_ALERT_WEBHOOK_ENABLED=true",
                "JEDI_ALERT_WEBHOOK_URL=https://alerts.example.gov/jedi",
                "JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES=4096",
            ]
        ),
        encoding="utf-8",
    )
    transport = _RecordingAlertTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    exit_code = runtime_worker.main(
        env_path=env_path,
        processor=lambda _settings: _failed_result(),
        sleep=lambda _seconds: None,
        alert_transport=transport,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert len(transport.requests) == 1
    assert transport.requests[0].url == "https://alerts.example.gov/jedi"
    assert transport.requests[0].body_bytes is not None
    assert b'"alert_id":"job-evt-failed:worker_failed"' in transport.requests[0].body_bytes
    assert '"alerts_emitted":1' in captured.out
    assert '"alert_failures":0' in captured.out


def test_emit_worker_failure_alert_rejects_alert_url_subclass_before_transport(
    tmp_path: Path,
) -> None:
    class SecretBearingAlertUrl(str):
        def __str__(self) -> str:
            return "https://alerts.example.gov/jedi?client_secret=worker-alert-secret"

    settings = _settings(tmp_path).model_copy(
        update={
            "alert_webhook_url": SecretBearingAlertUrl("https://alerts.example.gov/jedi"),
            "alert_webhook_max_body_bytes": 4096,
        }
    )
    transport = _RecordingAlertTransport(
        [HttpResponse(status_code=202, json_body={"ok": True})]
    )

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_worker._emit_worker_failure_alert(
            _failed_result(),
            settings=settings,
            transport=transport,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_ALERT_WEBHOOK_URL must be a string runtime setting"
    assert "SecretBearingAlertUrl" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "worker-alert-secret" not in diagnostic
    assert transport.requests == []


def test_emit_stale_requeue_alert_rejects_invalid_body_limit_before_transport(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path).model_copy(
        update={
            "alert_webhook_url": "https://alerts.example.gov/jedi",
            "alert_webhook_max_body_bytes": 0,
        }
    )
    report = runtime_worker.StaleJobRequeueReport(
        enabled=True,
        requeued_at=datetime(2026, 6, 11, 12, 0, tzinfo=UTC),
        stale_before=datetime(2026, 6, 11, 11, 45, tzinfo=UTC),
        stale_after_seconds=900,
        requeued_count=1,
        job_ids=["job-evt-stale"],
    )
    transport = _RecordingAlertTransport(
        [HttpResponse(status_code=202, json_body={"ok": True})]
    )

    with pytest.raises(RuntimeConfigError) as exc:
        runtime_worker._emit_stale_requeue_alert(
            report,
            settings=settings,
            transport=transport,
        )

    diagnostic = str(exc.value)
    assert diagnostic == "JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES must be greater than 0"
    assert transport.requests == []


def test_main_emits_stale_requeue_alert_when_recovery_requeues_jobs(
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
                "JEDI_WORKER_MAX_ITERATIONS=1",
                "JEDI_WORKER_IDLE_SLEEP_SECONDS=0",
                "JEDI_RUNNING_JOB_STALE_AFTER_SECONDS=900",
                "JEDI_STALE_JOB_REQUEUE_ENABLED=true",
                "JEDI_STALE_JOB_REQUEUE_BATCH_SIZE=7",
                "JEDI_ALERT_WEBHOOK_ENABLED=true",
                "JEDI_ALERT_WEBHOOK_URL=https://alerts.example.gov/jedi",
                "JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES=4096",
            ]
        ),
        encoding="utf-8",
    )
    database_urls: list[str] = []
    calls: list[tuple[datetime, int, str]] = []
    transport = _RecordingAlertTransport([HttpResponse(status_code=202, json_body={"ok": True})])

    exit_code = runtime_worker.main(
        env_path=env_path,
        processor=lambda _settings: _idle_result(),
        sleep=lambda _seconds: None,
        stale_job_recovery_store_factory=_recovery_store_factory(
            database_urls,
            calls,
            [_running_job()],
        ),
        alert_transport=transport,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert len(transport.requests) == 1
    assert transport.requests[0].url == "https://alerts.example.gov/jedi"
    assert transport.requests[0].body_bytes is not None
    assert b'"status":"stale_requeued"' in transport.requests[0].body_bytes
    assert b"job-evt-stale" in transport.requests[0].body_bytes
    assert '"requeued_count":1' in captured.out
    assert '"alerts_emitted":1' in captured.out
    assert '"alert_failures":0' in captured.out


def test_main_does_not_prune_when_retention_disabled(
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
                "JEDI_WORKER_MAX_ITERATIONS=1",
                "JEDI_WORKER_IDLE_SLEEP_SECONDS=0",
            ]
        ),
        encoding="utf-8",
    )
    database_urls: list[str] = []
    policies: list[RetentionPolicy] = []

    exit_code = runtime_worker.main(
        env_path=env_path,
        processor=lambda _settings: _idle_result(),
        sleep=lambda _seconds: None,
        prune_store_factory=_prune_store_factory(database_urls, policies),
    )

    capsys.readouterr()
    assert exit_code == 0
    assert database_urls == []
    assert policies == []
