from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from jedi_devproject.diagnostic_redaction import _redact_diagnostic_text
from jedi_devproject.exception_diagnostics import exception_diagnostic_message
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
        worker_id: str,
        message: str,
    ) -> FulfillmentJobRecord: ...

    def fail_fulfillment_job(
        self,
        *,
        job_id: str,
        worker_id: str,
        error_message: str,
    ) -> FulfillmentJobRecord: ...

    def touch_fulfillment_job_heartbeat(
        self,
        *,
        job_id: str,
        worker_id: str,
    ) -> FulfillmentJobRecord | None: ...

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
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    artifact_kind: str
    path: str = ""
    sha256: str = ""
    schema_version: str | None = None
    payload_json: dict[str, Any] | None = None


class FulfillmentPersistedArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    artifact_kind: str
    path: str
    sha256: str
    artifact_id: int | None = None


class FulfillmentExecutionResult(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        hide_input_in_errors=True,
    )

    message: str
    artifacts: list[FulfillmentArtifactRef] = Field(default_factory=list)
    after_artifacts_persisted: Callable[[list[FulfillmentPersistedArtifact]], None] | None = Field(
        default=None, exclude=True
    )


class FulfillmentWorkerResult(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    status: str
    job_id: str | None
    story_number: str | None
    message: str | None
    error_message: str | None


FulfillmentHandler = Callable[[FulfillmentJobRecord], FulfillmentExecutionResult]
FulfillmentFailureNotifier = Callable[[FulfillmentJobRecord, str], None]


def _require_heartbeat(
    *,
    store: FulfillmentWorkerStore,
    job_id: str,
    worker_id: str,
) -> None:
    """Touch the job heartbeat, raising if the job is no longer owned by this worker."""
    touched = store.touch_fulfillment_job_heartbeat(
        job_id=job_id,
        worker_id=worker_id,
    )
    if touched is None:
        raise RuntimeError(f"fulfillment job no longer owned by worker: {job_id}")


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

    _require_heartbeat(store=store, job_id=job.job_id, worker_id=worker_id)

    try:
        execution_result = handler(job)
        persisted_artifacts: list[FulfillmentPersistedArtifact] = []
        for artifact in execution_result.artifacts:
            if artifact.payload_json is None:
                store.record_artifact_ref(
                    job_id=job.job_id,
                    artifact_kind=artifact.artifact_kind,
                    path=artifact.path,
                    sha256=artifact.sha256,
                )
                persisted_artifacts.append(
                    FulfillmentPersistedArtifact(
                        artifact_kind=artifact.artifact_kind,
                        path=artifact.path,
                        sha256=artifact.sha256,
                    )
                )
            else:
                persisted = store.record_json_artifact(
                    job_id=job.job_id,
                    story_number=job.story_number,
                    artifact_kind=artifact.artifact_kind,
                    schema_version=artifact.schema_version or artifact.artifact_kind,
                    payload=artifact.payload_json,
                )
                artifact_id = _persisted_artifact_id(persisted)
                persisted_artifacts.append(
                    FulfillmentPersistedArtifact(
                        artifact_kind=artifact.artifact_kind,
                        path=f"db://artifact_blobs/{artifact_id}",
                        sha256=_persisted_artifact_sha256(persisted),
                        artifact_id=artifact_id,
                    )
                )
            _require_heartbeat(store=store, job_id=job.job_id, worker_id=worker_id)
        if execution_result.after_artifacts_persisted is not None:
            execution_result.after_artifacts_persisted(persisted_artifacts)
    except Exception as exc:
        return _fail_job(
            store=store,
            job=job,
            worker_id=worker_id,
            error_message=_redact_worker_exception(exc),
            failure_notifier=failure_notifier,
        )

    store.complete_fulfillment_job(
        job_id=job.job_id,
        worker_id=worker_id,
        message=execution_result.message,
    )
    return FulfillmentWorkerResult(
        status="completed",
        job_id=job.job_id,
        story_number=job.story_number,
        message=execution_result.message,
        error_message=None,
    )


def _fail_job(
    *,
    store: FulfillmentWorkerStore,
    job: FulfillmentJobRecord,
    worker_id: str,
    error_message: str,
    failure_notifier: FulfillmentFailureNotifier | None,
) -> FulfillmentWorkerResult:
    error_message = _redact_worker_diagnostic(error_message)
    if failure_notifier is not None:
        try:
            failure_notifier(job, error_message)
        except Exception as notifier_exc:
            notifier_error = _redact_worker_exception(notifier_exc)
            error_message = f"{error_message}; failure notifier failed: {notifier_error}"
    store.fail_fulfillment_job(
        job_id=job.job_id,
        worker_id=worker_id,
        error_message=error_message,
    )
    return FulfillmentWorkerResult(
        status="failed",
        job_id=job.job_id,
        story_number=job.story_number,
        message=None,
        error_message=error_message,
    )


def _redact_worker_diagnostic(message: str) -> str:
    return _redact_diagnostic_text(message) or ""


def _redact_worker_exception(exc: Exception) -> str:
    return _redact_worker_diagnostic(exception_diagnostic_message(exc, fallback_subject="worker"))


def _persisted_artifact_id(record: object) -> int:
    value = getattr(record, "id", None)
    if not isinstance(value, int):
        raise RuntimeError("persisted JSON artifact did not include integer id")
    return value


def _persisted_artifact_sha256(record: object) -> str:
    value = getattr(record, "sha256", None)
    if not isinstance(value, str) or not value:
        raise RuntimeError("persisted JSON artifact did not include sha256")
    return value
