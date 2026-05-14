from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from jedi_devproject.fulfillment_worker import (
    FulfillmentArtifactRef,
    FulfillmentExecutionResult,
    FulfillmentPersistedArtifact,
    process_one_fulfillment_job,
)
from jedi_devproject.operational_store import FulfillmentJobRecord


class FakeWorkerStore:
    def __init__(self, claimed_job: FulfillmentJobRecord | None) -> None:
        self.claimed_job = claimed_job
        self.claim_calls: list[str] = []
        self.completed_jobs: list[tuple[str, str]] = []
        self.failed_jobs: list[tuple[str, str]] = []
        self.artifact_refs: list[tuple[str, str, str, str]] = []
        self.json_artifacts: list[tuple[str, str, str, str, dict[str, Any]]] = []
        self.next_artifact_id = 1

    def claim_next_fulfillment_job(
        self,
        *,
        worker_id: str,
    ) -> FulfillmentJobRecord | None:
        self.claim_calls.append(worker_id)
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
        return self.claimed_job.model_copy(
            update={"status": "failed", "last_error": error_message}
        )

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
        artifact = SimpleArtifactRecord(
            id=self.next_artifact_id,
            sha256="b" * 64,
        )
        self.next_artifact_id += 1
        return artifact


class SimpleArtifactRecord:
    def __init__(self, *, id: int, sha256: str) -> None:
        self.id = id
        self.sha256 = sha256


def _job() -> FulfillmentJobRecord:
    return FulfillmentJobRecord(
        job_id="job-evt-001",
        event_id="evt-001",
        story_number="STRY0010013",
        status="running",
        attempt_count=1,
        created_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
        updated_at=datetime(2026, 5, 13, 15, 1, tzinfo=UTC),
        locked_by="worker-1",
        locked_at=datetime(2026, 5, 13, 15, 1, tzinfo=UTC),
        last_error=None,
    )


def test_worker_returns_idle_when_no_job_is_available() -> None:
    store = FakeWorkerStore(claimed_job=None)

    result = process_one_fulfillment_job(
        store=store,
        worker_id="worker-1",
        handler=lambda job: FulfillmentExecutionResult(message=f"handled {job.job_id}"),
    )

    assert result.status == "idle"
    assert result.job_id is None
    assert store.claim_calls == ["worker-1"]
    assert store.completed_jobs == []
    assert store.failed_jobs == []


def test_worker_completes_claimed_job_after_handler_success() -> None:
    store = FakeWorkerStore(claimed_job=_job())
    handled_jobs: list[str] = []

    def handler(job: FulfillmentJobRecord) -> FulfillmentExecutionResult:
        handled_jobs.append(job.job_id)
        return FulfillmentExecutionResult(message="implementation packet built")

    result = process_one_fulfillment_job(
        store=store,
        worker_id="worker-1",
        handler=handler,
    )

    assert result.status == "completed"
    assert result.job_id == "job-evt-001"
    assert handled_jobs == ["job-evt-001"]
    assert store.completed_jobs == [("job-evt-001", "implementation packet built")]
    assert store.failed_jobs == []
    assert store.artifact_refs == []


def test_worker_records_artifact_refs_before_completing_job() -> None:
    store = FakeWorkerStore(claimed_job=_job())

    def handler(job: FulfillmentJobRecord) -> FulfillmentExecutionResult:
        return FulfillmentExecutionResult(
            message=f"processed {job.story_number}",
            artifacts=[
                FulfillmentArtifactRef(
                    artifact_kind="implementation_candidate",
                    path="artifacts/job-evt-001/STRY0010013.json",
                    sha256="a" * 64,
                )
            ],
        )

    result = process_one_fulfillment_job(
        store=store,
        worker_id="worker-1",
        handler=handler,
    )

    assert result.status == "completed"
    assert store.artifact_refs == [
        (
            "job-evt-001",
            "implementation_candidate",
            "artifacts/job-evt-001/STRY0010013.json",
            "a" * 64,
        )
    ]
    assert store.completed_jobs == [("job-evt-001", "processed STRY0010013")]


def test_worker_records_json_artifacts_before_completing_job() -> None:
    store = FakeWorkerStore(claimed_job=_job())

    def handler(job: FulfillmentJobRecord) -> FulfillmentExecutionResult:
        return FulfillmentExecutionResult(
            message=f"processed {job.story_number}",
            artifacts=[
                FulfillmentArtifactRef(
                    artifact_kind="implementation_packet",
                    schema_version="implementation-packet-v1",
                    payload_json={"task": "generate", "story": {"number": job.story_number}},
                )
            ],
        )

    result = process_one_fulfillment_job(
        store=store,
        worker_id="worker-1",
        handler=handler,
    )

    assert result.status == "completed"
    assert store.artifact_refs == []
    assert store.json_artifacts == [
        (
            "job-evt-001",
            "STRY0010013",
            "implementation_packet",
            "implementation-packet-v1",
            {"task": "generate", "story": {"number": "STRY0010013"}},
        )
    ]
    assert store.completed_jobs == [("job-evt-001", "processed STRY0010013")]


def test_worker_runs_post_artifact_callback_after_json_artifact_persistence() -> None:
    store = FakeWorkerStore(claimed_job=_job())
    callback_artifacts: list[FulfillmentPersistedArtifact] = []

    def handler(job: FulfillmentJobRecord) -> FulfillmentExecutionResult:
        return FulfillmentExecutionResult(
            message=f"processed {job.story_number}",
            artifacts=[
                FulfillmentArtifactRef(
                    artifact_kind="implementation_candidate",
                    schema_version="implementation-candidate-v1",
                    payload_json={"story_number": job.story_number},
                )
            ],
            after_artifacts_persisted=callback_artifacts.extend,
        )

    result = process_one_fulfillment_job(
        store=store,
        worker_id="worker-1",
        handler=handler,
    )

    assert result.status == "completed"
    assert callback_artifacts == [
        FulfillmentPersistedArtifact(
            artifact_kind="implementation_candidate",
            path="db://artifact_blobs/1",
            sha256="b" * 64,
            artifact_id=1,
        )
    ]
    assert store.completed_jobs == [("job-evt-001", "processed STRY0010013")]


def test_worker_fails_job_when_post_artifact_callback_raises() -> None:
    store = FakeWorkerStore(claimed_job=_job())

    def handler(job: FulfillmentJobRecord) -> FulfillmentExecutionResult:
        def fail_after_persist(
            _artifacts: list[FulfillmentPersistedArtifact],
        ) -> None:
            raise RuntimeError("Update Set handoff failed")

        return FulfillmentExecutionResult(
            message=f"processed {job.story_number}",
            artifacts=[
                FulfillmentArtifactRef(
                    artifact_kind="implementation_candidate",
                    schema_version="implementation-candidate-v1",
                    payload_json={"story_number": job.story_number},
                )
            ],
            after_artifacts_persisted=fail_after_persist,
        )

    result = process_one_fulfillment_job(
        store=store,
        worker_id="worker-1",
        handler=handler,
    )

    assert result.status == "failed"
    assert result.error_message == "Update Set handoff failed"
    assert store.completed_jobs == []
    assert store.failed_jobs == [("job-evt-001", "Update Set handoff failed")]


def test_worker_fails_claimed_job_when_handler_raises() -> None:
    store = FakeWorkerStore(claimed_job=_job())
    notified_failures: list[tuple[str, str]] = []

    def handler(job: FulfillmentJobRecord) -> FulfillmentExecutionResult:
        raise RuntimeError(f"build failed for {job.story_number}")

    result = process_one_fulfillment_job(
        store=store,
        worker_id="worker-1",
        handler=handler,
        failure_notifier=lambda job, error: notified_failures.append(
            (job.job_id, error)
        ),
    )

    assert result.status == "failed"
    assert result.job_id == "job-evt-001"
    assert result.error_message == "build failed for STRY0010013"
    assert store.completed_jobs == []
    assert store.failed_jobs == [("job-evt-001", "build failed for STRY0010013")]
    assert notified_failures == [("job-evt-001", "build failed for STRY0010013")]


def test_worker_records_failed_job_even_when_failure_notifier_fails() -> None:
    store = FakeWorkerStore(claimed_job=_job())

    def handler(job: FulfillmentJobRecord) -> FulfillmentExecutionResult:
        raise RuntimeError(f"build failed for {job.story_number}")

    def failure_notifier(_job: FulfillmentJobRecord, _error: str) -> None:
        raise RuntimeError("work note writeback failed")

    result = process_one_fulfillment_job(
        store=store,
        worker_id="worker-1",
        handler=handler,
        failure_notifier=failure_notifier,
    )

    assert result.status == "failed"
    assert result.error_message == (
        "build failed for STRY0010013; failure notifier failed: "
        "work note writeback failed"
    )
    assert store.failed_jobs == [
        (
            "job-evt-001",
            "build failed for STRY0010013; failure notifier failed: "
            "work note writeback failed",
        )
    ]


def test_worker_requires_non_empty_worker_id() -> None:
    store = FakeWorkerStore(claimed_job=None)

    with pytest.raises(ValueError, match="worker_id"):
        process_one_fulfillment_job(
            store=store,
            worker_id=" ",
            handler=lambda job: FulfillmentExecutionResult(message=job.job_id),
        )
