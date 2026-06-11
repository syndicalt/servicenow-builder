from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jedi_devproject import runtime_worker
from jedi_devproject.fulfillment_worker import FulfillmentWorkerResult
from jedi_devproject.operational_store import (
    RetentionPolicy,
    RetentionPruneReport,
)
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


def _idle_result() -> FulfillmentWorkerResult:
    return FulfillmentWorkerResult(
        status="idle",
        job_id=None,
        story_number=None,
        message="No queued fulfillment job available",
        error_message=None,
    )


def _empty_report() -> RetentionPruneReport:
    return RetentionPruneReport(
        enabled=True,
        pruned_at=datetime(2026, 6, 11, 12, 0, tzinfo=UTC),
        prune_batch_size=500,
        results=[],
    )


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


def test_load_worker_settings_reads_retention_environment(tmp_path: Path) -> None:
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
