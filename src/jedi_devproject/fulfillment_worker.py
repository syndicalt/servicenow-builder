from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from pydantic import BaseModel, ConfigDict

from jedi_devproject.operational_store import FulfillmentJobRecord


class FulfillmentWorkerStore(Protocol):
    def claim_next_fulfillment_job(
        self,
        *,
        worker_id: str,
    ) -> FulfillmentJobRecord | None: ...

    def complete_fulfillment_job(
        self,
        *,
        job_id: str,
        message: str,
    ) -> FulfillmentJobRecord: ...

    def fail_fulfillment_job(
        self,
        *,
        job_id: str,
        error_message: str,
    ) -> FulfillmentJobRecord: ...


class FulfillmentExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str


class FulfillmentWorkerResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    job_id: str | None
    story_number: str | None
    message: str | None
    error_message: str | None


FulfillmentHandler = Callable[[FulfillmentJobRecord], FulfillmentExecutionResult]
FulfillmentFailureNotifier = Callable[[FulfillmentJobRecord, str], None]


def process_one_fulfillment_job(
    *,
    store: FulfillmentWorkerStore,
    worker_id: str,
    handler: FulfillmentHandler,
    failure_notifier: FulfillmentFailureNotifier | None = None,
) -> FulfillmentWorkerResult:
    if worker_id.strip() == "":
        raise ValueError("worker_id must not be empty")

    job = store.claim_next_fulfillment_job(worker_id=worker_id)
    if job is None:
        return FulfillmentWorkerResult(
            status="idle",
            job_id=None,
            story_number=None,
            message="No queued fulfillment job available",
            error_message=None,
        )

    try:
        execution_result = handler(job)
    except Exception as exc:
        error_message = str(exc)
        if failure_notifier is not None:
            try:
                failure_notifier(job, error_message)
            except Exception as notifier_exc:
                error_message = (
                    f"{error_message}; failure notifier failed: {notifier_exc}"
                )
        store.fail_fulfillment_job(job_id=job.job_id, error_message=error_message)
        return FulfillmentWorkerResult(
            status="failed",
            job_id=job.job_id,
            story_number=job.story_number,
            message=None,
            error_message=error_message,
        )

    store.complete_fulfillment_job(
        job_id=job.job_id,
        message=execution_result.message,
    )
    return FulfillmentWorkerResult(
        status="completed",
        job_id=job.job_id,
        story_number=job.story_number,
        message=execution_result.message,
        error_message=None,
    )
