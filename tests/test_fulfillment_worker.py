from __future__ import annotations

from datetime import UTC, datetime

import pytest

from jedi_devproject.fulfillment_worker import (
    FulfillmentExecutionResult,
    process_one_fulfillment_job,
)
from jedi_devproject.operational_store import FulfillmentJobRecord


class FakeWorkerStore:
    def __init__(self, claimed_job: FulfillmentJobRecord | None) -> None:
        self.claimed_job = claimed_job
        self.claim_calls: list[str] = []
        self.completed_jobs: list[tuple[str, str]] = []
        self.failed_jobs: list[tuple[str, str]] = []

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


def test_worker_fails_claimed_job_when_handler_raises() -> None:
    store = FakeWorkerStore(claimed_job=_job())

    def handler(job: FulfillmentJobRecord) -> FulfillmentExecutionResult:
        raise RuntimeError(f"build failed for {job.story_number}")

    result = process_one_fulfillment_job(
        store=store,
        worker_id="worker-1",
        handler=handler,
    )

    assert result.status == "failed"
    assert result.job_id == "job-evt-001"
    assert result.error_message == "build failed for STRY0010013"
    assert store.completed_jobs == []
    assert store.failed_jobs == [("job-evt-001", "build failed for STRY0010013")]


def test_worker_requires_non_empty_worker_id() -> None:
    store = FakeWorkerStore(claimed_job=None)

    with pytest.raises(ValueError, match="worker_id"):
        process_one_fulfillment_job(
            store=store,
            worker_id=" ",
            handler=lambda job: FulfillmentExecutionResult(message=job.job_id),
        )
