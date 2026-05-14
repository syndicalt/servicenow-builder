from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

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

    def record_artifact_ref(
        self,
        *,
        job_id: str,
        artifact_kind: str,
        path: str,
        sha256: str,
    ) -> object: ...

    def record_json_artifact(
        self,
        *,
        job_id: str,
        story_number: str,
        artifact_kind: str,
        schema_version: str,
        payload: dict[str, Any],
    ) -> object: ...


class FulfillmentArtifactRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_kind: str
    path: str = ""
    sha256: str = ""
    schema_version: str | None = None
    payload_json: dict[str, Any] | None = None


class FulfillmentExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    artifacts: list[FulfillmentArtifactRef] = Field(default_factory=list)


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

    for artifact in execution_result.artifacts:
        if artifact.payload_json is None:
            store.record_artifact_ref(
                job_id=job.job_id,
                artifact_kind=artifact.artifact_kind,
                path=artifact.path,
                sha256=artifact.sha256,
            )
        else:
            store.record_json_artifact(
                job_id=job.job_id,
                story_number=job.story_number,
                artifact_kind=artifact.artifact_kind,
                schema_version=artifact.schema_version or artifact.artifact_kind,
                payload=artifact.payload_json,
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
