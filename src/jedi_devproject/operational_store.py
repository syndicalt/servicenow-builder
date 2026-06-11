from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
from datetime import UTC, datetime, timedelta
from importlib import resources
from types import TracebackType
from typing import Any, Protocol, Self, SupportsInt, cast

from pydantic import BaseModel, ConfigDict, Field

from jedi_devproject.lifecycle_events import LifecycleStateChangeEvent

MIGRATION_PACKAGE = "jedi_devproject.migrations"
MIGRATION_FILENAME = "0001_operational_store.sql"
RETENTION_MIGRATION_FILENAME = "0002_retention.sql"
MIGRATION_FILENAMES = (MIGRATION_FILENAME, RETENTION_MIGRATION_FILENAME)

DEFAULT_RETENTION_PRUNE_BATCH_SIZE = 500

RETENTION_ARTIFACT_BLOB_DAYS_ENV = "JEDI_RETENTION_ARTIFACT_BLOB_DAYS"
RETENTION_JOB_EVENT_DAYS_ENV = "JEDI_RETENTION_JOB_EVENT_DAYS"
RETENTION_PRUNE_BATCH_SIZE_ENV = "JEDI_RETENTION_PRUNE_BATCH_SIZE"

_PRUNE_ARTIFACT_BLOBS_SQL = """
WITH prunable AS (
    SELECT artifact_blobs.id
    FROM artifact_blobs
    JOIN fulfillment_jobs
      ON fulfillment_jobs.job_id = artifact_blobs.job_id
    WHERE artifact_blobs.created_at < %s
      AND fulfillment_jobs.updated_at < %s
      AND fulfillment_jobs.status IN ('completed', 'failed', 'rejected')
    ORDER BY artifact_blobs.id
    LIMIT %s
),
detached_refs AS (
    UPDATE artifact_refs
    SET artifact_id = NULL
    WHERE artifact_id IN (SELECT id FROM prunable)
),
deleted_blobs AS (
    DELETE FROM artifact_blobs
    WHERE id IN (SELECT id FROM prunable)
    RETURNING id
)
SELECT COUNT(*) AS deleted_count FROM deleted_blobs
"""

_PRUNE_JOB_EVENTS_SQL = """
WITH prunable AS (
    SELECT job_events.id
    FROM job_events
    JOIN fulfillment_jobs
      ON fulfillment_jobs.job_id = job_events.job_id
    WHERE job_events.created_at < %s
      AND fulfillment_jobs.updated_at < %s
      AND fulfillment_jobs.status IN ('completed', 'failed', 'rejected')
    ORDER BY job_events.id
    LIMIT %s
),
deleted_events AS (
    DELETE FROM job_events
    WHERE id IN (SELECT id FROM prunable)
    RETURNING id
)
SELECT COUNT(*) AS deleted_count FROM deleted_events
"""

_SURFACE_MATURITY_EVIDENCE_SQL = """
WITH surface_jobs AS (
    SELECT DISTINCT fulfillment_jobs.job_id, fulfillment_jobs.status
    FROM fulfillment_jobs
    JOIN artifact_blobs
      ON artifact_blobs.job_id = fulfillment_jobs.job_id
    WHERE fulfillment_jobs.status IN ('completed', 'failed', 'rejected')
      AND artifact_blobs.artifact_kind = 'implementation_packet'
      AND artifact_blobs.payload_json->'context_dossier'->'target'->'required_surfaces' ? %s
),
rework_jobs AS (
    SELECT DISTINCT job_id
    FROM job_events
    WHERE status = 'rework_requested'
)
SELECT
    COUNT(*) AS samples,
    COUNT(*) FILTER (
        WHERE surface_jobs.status = 'completed'
          AND rework_jobs.job_id IS NULL
    ) AS successes,
    COUNT(*) FILTER (
        WHERE surface_jobs.status IN ('failed', 'rejected')
           OR rework_jobs.job_id IS NOT NULL
    ) AS failures
FROM surface_jobs
LEFT JOIN rework_jobs
  ON rework_jobs.job_id = surface_jobs.job_id
"""


def _utc_now() -> datetime:
    return datetime.now(UTC)


def load_operational_store_migration() -> str:
    return (
        resources.files(MIGRATION_PACKAGE).joinpath(MIGRATION_FILENAME).read_text(encoding="utf-8")
    )


def load_operational_store_migrations() -> tuple[str, ...]:
    package = resources.files(MIGRATION_PACKAGE)
    return tuple(
        package.joinpath(filename).read_text(encoding="utf-8") for filename in MIGRATION_FILENAMES
    )


class RetentionPolicy(BaseModel):
    """Operational store retention windows. Retention is disabled by default.

    Deletion in a regulated system must follow explicit agency/customer
    retention rules, so a record class is pruned only when its window is
    explicitly configured.
    """

    model_config = ConfigDict(extra="forbid")

    artifact_blob_retention_days: int | None = Field(default=None, ge=1)
    job_event_retention_days: int | None = Field(default=None, ge=1)
    prune_batch_size: int = Field(default=DEFAULT_RETENTION_PRUNE_BATCH_SIZE, ge=1)

    @property
    def enabled(self) -> bool:
        return (
            self.artifact_blob_retention_days is not None
            or self.job_event_retention_days is not None
        )


def load_retention_policy(values: Mapping[str, str]) -> RetentionPolicy:
    batch_size = _optional_int(values.get(RETENTION_PRUNE_BATCH_SIZE_ENV))
    return RetentionPolicy(
        artifact_blob_retention_days=_optional_int(values.get(RETENTION_ARTIFACT_BLOB_DAYS_ENV)),
        job_event_retention_days=_optional_int(values.get(RETENTION_JOB_EVENT_DAYS_ENV)),
        prune_batch_size=(
            batch_size if batch_size is not None else DEFAULT_RETENTION_PRUNE_BATCH_SIZE
        ),
    )


def _optional_int(value: str | None) -> int | None:
    if value is None or value.strip() == "":
        return None
    return int(value)


class RetentionClassPruneResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_class: str
    cutoff: datetime
    deleted_count: int
    batches: int


class RetentionPruneReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
    pruned_at: datetime
    prune_batch_size: int
    results: list[RetentionClassPruneResult]


class OperationalConnection(Protocol):
    def execute(self, sql: str, params: tuple[object, ...] = ()) -> None: ...

    def fetch_one(
        self,
        sql: str,
        params: tuple[object, ...] = (),
    ) -> Mapping[str, object] | None: ...

    def fetch_all(
        self,
        sql: str,
        params: tuple[object, ...] = (),
    ) -> Sequence[Mapping[str, object]]: ...

    def transaction(self) -> AbstractContextManager[None]: ...

    def close(self) -> None: ...


class LifecycleEventRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    event_type: str
    story_number: str
    payload_json: dict[str, object]
    correlation_id: str | None = None
    received_at: datetime
    validation_status: str


class FulfillmentJobRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    event_id: str
    story_number: str
    story_sys_id: str | None = None
    status: str
    attempt_count: int
    created_at: datetime
    updated_at: datetime
    locked_by: str | None
    locked_at: datetime | None
    last_error: str | None
    correlation_id: str | None = None


class JobEventRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    job_id: str
    status: str
    message: str | None
    created_at: datetime


class ArtifactRefRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    job_id: str
    artifact_kind: str
    path: str
    sha256: str
    artifact_id: int | None = None
    created_at: datetime


class ArtifactBlobRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    job_id: str
    story_number: str
    artifact_kind: str
    schema_version: str
    payload_json: dict[str, Any]
    sha256: str
    created_at: datetime


class SurfaceMaturityEvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    surface: str
    samples: int
    successes: int
    failures: int


class PsycopgOperationalConnection:
    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def execute(self, sql: str, params: tuple[object, ...] = ()) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(sql, params)

    def fetch_one(
        self,
        sql: str,
        params: tuple[object, ...] = (),
    ) -> Mapping[str, object] | None:
        with self._connection.cursor() as cursor:
            cursor.execute(sql, params)
            row = cursor.fetchone()
        return cast(Mapping[str, object] | None, row)

    def fetch_all(
        self,
        sql: str,
        params: tuple[object, ...] = (),
    ) -> list[Mapping[str, object]]:
        with self._connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        return list(rows)

    def transaction(self) -> AbstractContextManager[None]:
        return cast(AbstractContextManager[None], self._connection.transaction())

    def close(self) -> None:
        self._connection.close()


class PostgresOperationalStore:
    def __init__(self, connection: OperationalConnection) -> None:
        self._connection = connection

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self._connection.close()

    def initialize_schema(self) -> None:
        with self._connection.transaction():
            for migration_sql in load_operational_store_migrations():
                self._connection.execute(migration_sql)

    def record_lifecycle_event(
        self,
        event: LifecycleStateChangeEvent,
        *,
        validation_status: str = "accepted",
    ) -> LifecycleEventRecord:
        payload_json = json.dumps(event.model_dump(mode="json"), sort_keys=True)
        received_at = _utc_now()
        with self._connection.transaction():
            self._connection.execute(
                """
                INSERT INTO lifecycle_events (
                    event_id,
                    event_type,
                    story_number,
                    payload_json,
                    received_at,
                    validation_status
                )
                VALUES (%s, %s, %s, %s::jsonb, %s, %s)
                ON CONFLICT (event_id) DO NOTHING
                """,
                (
                    event.event_id,
                    event.event_type.value,
                    event.story_number,
                    payload_json,
                    received_at,
                    validation_status,
                ),
            )

        return self.get_lifecycle_event(event.event_id)

    def get_lifecycle_event(self, event_id: str) -> LifecycleEventRecord:
        row = self._connection.fetch_one(
            """
            SELECT event_id, event_type, story_number, payload_json,
                   payload_json->>'correlation_id' AS correlation_id,
                   received_at, validation_status
            FROM lifecycle_events
            WHERE event_id = %s
            """,
            (event_id,),
        )
        if row is None:
            raise KeyError(f"Lifecycle event not found: {event_id}")
        return LifecycleEventRecord.model_validate(row)

    def enqueue_fulfillment_job(
        self,
        *,
        event_id: str,
        story_number: str,
    ) -> FulfillmentJobRecord:
        job_id = f"job-{event_id}"
        now = _utc_now()
        with self._connection.transaction():
            row = self._connection.fetch_one(
                """
                WITH inserted_job AS (
                    INSERT INTO fulfillment_jobs (
                        job_id,
                        event_id,
                        story_number,
                        status,
                        attempt_count,
                        created_at,
                        updated_at
                    )
                    VALUES (%s, %s, %s, 'queued', 0, %s, %s)
                    ON CONFLICT (event_id) DO NOTHING
                    RETURNING job_id, event_id, story_number, status, attempt_count,
                              created_at, updated_at, locked_by, locked_at, last_error
                ),
                inserted_job_event AS (
                    INSERT INTO job_events (job_id, status, message, created_at)
                    SELECT job_id, 'queued', %s, %s
                    FROM inserted_job
                ),
                selected_job AS (
                    SELECT job_id, event_id, story_number, status, attempt_count,
                           created_at, updated_at, locked_by, locked_at, last_error
                    FROM inserted_job
                    UNION ALL
                    SELECT job_id, event_id, story_number, status, attempt_count,
                           created_at, updated_at, locked_by, locked_at, last_error
                    FROM fulfillment_jobs
                    WHERE event_id = %s
                      AND NOT EXISTS (SELECT 1 FROM inserted_job)
                )
                SELECT selected_job.job_id, selected_job.event_id, selected_job.story_number,
                       selected_job.status, selected_job.attempt_count,
                       selected_job.created_at, selected_job.updated_at,
                       selected_job.locked_by, selected_job.locked_at,
                       selected_job.last_error,
                       lifecycle_events.payload_json->>'story_sys_id' AS story_sys_id,
                       lifecycle_events.payload_json->>'correlation_id' AS correlation_id
                FROM selected_job
                JOIN lifecycle_events
                  ON lifecycle_events.event_id = selected_job.event_id
                """,
                (
                    job_id,
                    event_id,
                    story_number,
                    now,
                    now,
                    "Fulfillment job queued",
                    now,
                    event_id,
                ),
            )
        if row is None:
            raise RuntimeError(f"Fulfillment job was not returned for event: {event_id}")
        return FulfillmentJobRecord.model_validate(row)

    def claim_next_fulfillment_job(self, *, worker_id: str) -> FulfillmentJobRecord | None:
        now = _utc_now()
        with self._connection.transaction():
            row = self._connection.fetch_one(
                """
                WITH next_job AS (
                    SELECT job_id
                    FROM fulfillment_jobs
                    WHERE status = 'queued'
                    ORDER BY created_at, job_id
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                ),
                updated_job AS (
                    UPDATE fulfillment_jobs
                    SET status = 'running',
                        attempt_count = attempt_count + 1,
                        updated_at = %s,
                        locked_by = %s,
                        locked_at = %s
                    FROM next_job
                    WHERE fulfillment_jobs.job_id = next_job.job_id
                    RETURNING fulfillment_jobs.job_id,
                              fulfillment_jobs.event_id,
                              fulfillment_jobs.story_number,
                              fulfillment_jobs.status,
                              fulfillment_jobs.attempt_count,
                              fulfillment_jobs.created_at,
                              fulfillment_jobs.updated_at,
                              fulfillment_jobs.locked_by,
                              fulfillment_jobs.locked_at,
                              fulfillment_jobs.last_error
                ),
                inserted_job_event AS (
                    INSERT INTO job_events (job_id, status, message, created_at)
                    SELECT job_id, 'running', %s, %s
                    FROM updated_job
                )
                SELECT updated_job.job_id, updated_job.event_id, updated_job.story_number,
                       updated_job.status, updated_job.attempt_count,
                       updated_job.created_at, updated_job.updated_at,
                       updated_job.locked_by, updated_job.locked_at,
                       updated_job.last_error,
                       lifecycle_events.payload_json->>'story_sys_id' AS story_sys_id,
                       lifecycle_events.payload_json->>'correlation_id' AS correlation_id
                FROM updated_job
                JOIN lifecycle_events
                  ON lifecycle_events.event_id = updated_job.event_id
                """,
                (
                    now,
                    worker_id,
                    now,
                    f"Fulfillment job claimed by {worker_id}",
                    now,
                ),
            )

        if row is None:
            return None
        return FulfillmentJobRecord.model_validate(row)

    def get_job(self, job_id: str) -> FulfillmentJobRecord:
        row = self._connection.fetch_one(
            """
            SELECT fulfillment_jobs.job_id, fulfillment_jobs.event_id,
                   fulfillment_jobs.story_number, fulfillment_jobs.status,
                   fulfillment_jobs.attempt_count, fulfillment_jobs.created_at,
                   fulfillment_jobs.updated_at, fulfillment_jobs.locked_by,
                   fulfillment_jobs.locked_at, fulfillment_jobs.last_error,
                   lifecycle_events.payload_json->>'story_sys_id' AS story_sys_id,
                   lifecycle_events.payload_json->>'correlation_id' AS correlation_id
            FROM fulfillment_jobs
            JOIN lifecycle_events
              ON lifecycle_events.event_id = fulfillment_jobs.event_id
            WHERE job_id = %s
            """,
            (job_id,),
        )
        if row is None:
            raise KeyError(f"Fulfillment job not found: {job_id}")
        return FulfillmentJobRecord.model_validate(row)

    def complete_fulfillment_job(
        self,
        *,
        job_id: str,
        message: str,
    ) -> FulfillmentJobRecord:
        now = _utc_now()
        row = self._transition_fulfillment_job(
            job_id=job_id,
            status="completed",
            message=message,
            now=now,
            last_error=None,
        )
        if row is None:
            raise KeyError(f"Fulfillment job not found: {job_id}")
        return FulfillmentJobRecord.model_validate(row)

    def close_latest_fulfillment_job_for_story(
        self,
        *,
        story_number: str,
        event_id: str,
    ) -> FulfillmentJobRecord | None:
        now = _utc_now()
        with self._connection.transaction():
            row = self._connection.fetch_one(
                """
                WITH latest_story_job AS (
                    SELECT job_id
                    FROM fulfillment_jobs
                    WHERE story_number = %s
                    ORDER BY created_at DESC, job_id DESC
                    LIMIT 1
                    FOR UPDATE
                ),
                updated_job AS (
                    UPDATE fulfillment_jobs
                    SET status = 'completed',
                        updated_at = %s,
                        locked_by = NULL,
                        locked_at = NULL,
                        last_error = NULL
                    FROM latest_story_job
                    WHERE fulfillment_jobs.job_id = latest_story_job.job_id
                    RETURNING fulfillment_jobs.job_id,
                              fulfillment_jobs.event_id,
                              fulfillment_jobs.story_number,
                              fulfillment_jobs.status,
                              fulfillment_jobs.attempt_count,
                              fulfillment_jobs.created_at,
                              fulfillment_jobs.updated_at,
                              fulfillment_jobs.locked_by,
                              fulfillment_jobs.locked_at,
                              fulfillment_jobs.last_error
                ),
                inserted_job_event AS (
                    INSERT INTO job_events (job_id, status, message, created_at)
                    SELECT job_id, %s, %s, %s
                    FROM updated_job
                )
                SELECT job_id, event_id, story_number, status, attempt_count,
                       created_at, updated_at, locked_by, locked_at, last_error
                FROM updated_job
                """,
                (
                    story_number,
                    now,
                    "story_completed",
                    f"Story marked Complete in ServiceNow by lifecycle event {event_id}",
                    now,
                ),
            )
        if row is None:
            return None
        return FulfillmentJobRecord.model_validate(row)

    def record_rework_requested_for_story(
        self,
        *,
        story_number: str,
        event_id: str,
        target_state: str,
    ) -> FulfillmentJobRecord | None:
        now = _utc_now()
        with self._connection.transaction():
            row = self._connection.fetch_one(
                """
                WITH latest_story_job AS (
                    SELECT job_id
                    FROM fulfillment_jobs
                    WHERE story_number = %s
                    ORDER BY created_at DESC, job_id DESC
                    LIMIT 1
                    FOR UPDATE
                ),
                selected_job AS (
                    SELECT job_id, event_id, story_number, status, attempt_count,
                           created_at, updated_at, locked_by, locked_at, last_error
                    FROM fulfillment_jobs
                    WHERE job_id = (SELECT job_id FROM latest_story_job)
                ),
                inserted_job_event AS (
                    INSERT INTO job_events (job_id, status, message, created_at)
                    SELECT job_id, %s, %s, %s
                    FROM selected_job
                )
                SELECT job_id, event_id, story_number, status, attempt_count,
                       created_at, updated_at, locked_by, locked_at, last_error
                FROM selected_job
                """,
                (
                    story_number,
                    "rework_requested",
                    (
                        f"Story returned to {target_state} from Ready for Testing "
                        f"by lifecycle event {event_id}"
                    ),
                    now,
                ),
            )
        if row is None:
            return None
        return FulfillmentJobRecord.model_validate(row)

    def reject_latest_fulfillment_job_for_story(
        self,
        *,
        story_number: str,
        event_id: str,
    ) -> FulfillmentJobRecord | None:
        now = _utc_now()
        rejected_message = (
            f"Story returned to Draft from Ready for Testing by lifecycle event {event_id}"
        )
        with self._connection.transaction():
            row = self._connection.fetch_one(
                """
                WITH latest_story_job AS (
                    SELECT job_id
                    FROM fulfillment_jobs
                    WHERE story_number = %s
                    ORDER BY created_at DESC, job_id DESC
                    LIMIT 1
                    FOR UPDATE
                ),
                updated_job AS (
                    UPDATE fulfillment_jobs
                    SET status = 'rejected',
                        updated_at = %s,
                        locked_by = NULL,
                        locked_at = NULL,
                        last_error = %s
                    FROM latest_story_job
                    WHERE fulfillment_jobs.job_id = latest_story_job.job_id
                    RETURNING fulfillment_jobs.job_id,
                              fulfillment_jobs.event_id,
                              fulfillment_jobs.story_number,
                              fulfillment_jobs.status,
                              fulfillment_jobs.attempt_count,
                              fulfillment_jobs.created_at,
                              fulfillment_jobs.updated_at,
                              fulfillment_jobs.locked_by,
                              fulfillment_jobs.locked_at,
                              fulfillment_jobs.last_error
                ),
                inserted_job_event AS (
                    INSERT INTO job_events (job_id, status, message, created_at)
                    SELECT job_id, %s, %s, %s
                    FROM updated_job
                )
                SELECT job_id, event_id, story_number, status, attempt_count,
                       created_at, updated_at, locked_by, locked_at, last_error
                FROM updated_job
                """,
                (
                    story_number,
                    now,
                    rejected_message,
                    "story_rejected",
                    rejected_message,
                    now,
                ),
            )
        if row is None:
            return None
        return FulfillmentJobRecord.model_validate(row)

    def fail_fulfillment_job(
        self,
        *,
        job_id: str,
        error_message: str,
    ) -> FulfillmentJobRecord:
        now = _utc_now()
        row = self._transition_fulfillment_job(
            job_id=job_id,
            status="failed",
            message=error_message,
            now=now,
            last_error=error_message,
        )
        if row is None:
            raise KeyError(f"Fulfillment job not found: {job_id}")
        return FulfillmentJobRecord.model_validate(row)

    def _transition_fulfillment_job(
        self,
        *,
        job_id: str,
        status: str,
        message: str,
        now: datetime,
        last_error: str | None,
    ) -> Mapping[str, object] | None:
        with self._connection.transaction():
            return self._connection.fetch_one(
                """
                WITH updated_job AS (
                    UPDATE fulfillment_jobs
                    SET status = %s,
                        updated_at = %s,
                        locked_by = NULL,
                        locked_at = NULL,
                        last_error = %s
                    WHERE job_id = %s
                    RETURNING job_id, event_id, story_number, status, attempt_count,
                              created_at, updated_at, locked_by, locked_at, last_error
                ),
                inserted_job_event AS (
                    INSERT INTO job_events (job_id, status, message, created_at)
                    SELECT job_id, %s, %s, %s
                    FROM updated_job
                )
                SELECT job_id, event_id, story_number, status, attempt_count,
                       created_at, updated_at, locked_by, locked_at, last_error
                FROM updated_job
                """,
                (status, now, last_error, job_id, status, message, now),
            )

    def job_events_for_job(self, job_id: str) -> list[JobEventRecord]:
        rows = self._connection.fetch_all(
            """
            SELECT id, job_id, status, message, created_at
            FROM job_events
            WHERE job_id = %s
            ORDER BY id
            """,
            (job_id,),
        )
        return [JobEventRecord.model_validate(row) for row in rows]

    def recent_lifecycle_events(self, *, limit: int = 50) -> list[LifecycleEventRecord]:
        rows = self._connection.fetch_all(
            """
            SELECT event_id, event_type, story_number, payload_json,
                   payload_json->>'correlation_id' AS correlation_id,
                   received_at, validation_status
            FROM lifecycle_events
            ORDER BY received_at DESC, event_id DESC
            LIMIT %s
            """,
            (limit,),
        )
        return [LifecycleEventRecord.model_validate(row) for row in rows]

    def recent_fulfillment_jobs(self, *, limit: int = 50) -> list[FulfillmentJobRecord]:
        rows = self._connection.fetch_all(
            """
            SELECT fulfillment_jobs.job_id, fulfillment_jobs.event_id,
                   fulfillment_jobs.story_number, fulfillment_jobs.status,
                   fulfillment_jobs.attempt_count, fulfillment_jobs.created_at,
                   fulfillment_jobs.updated_at, fulfillment_jobs.locked_by,
                   fulfillment_jobs.locked_at, fulfillment_jobs.last_error,
                   lifecycle_events.payload_json->>'story_sys_id' AS story_sys_id,
                   lifecycle_events.payload_json->>'correlation_id' AS correlation_id
            FROM fulfillment_jobs
            JOIN lifecycle_events
              ON lifecycle_events.event_id = fulfillment_jobs.event_id
            ORDER BY updated_at DESC, job_id DESC
            LIMIT %s
            """,
            (limit,),
        )
        return [FulfillmentJobRecord.model_validate(row) for row in rows]

    def builder_maturity_evidence_for_surface(
        self,
        surface: str,
    ) -> SurfaceMaturityEvidenceRecord:
        """Aggregate terminal fulfillment outcomes for one builder surface.

        Read-only. A job is a sample when it reached a terminal status and its
        recorded implementation packet required the surface. It counts as a
        success when the terminal status is ``completed`` and UAT never
        requested rework; ``failed``, ``rejected``, and reworked jobs count as
        failures.
        """
        row = self._connection.fetch_one(_SURFACE_MATURITY_EVIDENCE_SQL, (surface,))
        if row is None:
            raise RuntimeError(
                f"PostgreSQL did not return surface maturity evidence for {surface}"
            )
        return SurfaceMaturityEvidenceRecord(
            surface=surface,
            samples=int(cast(SupportsInt, row["samples"])),
            successes=int(cast(SupportsInt, row["successes"])),
            failures=int(cast(SupportsInt, row["failures"])),
        )

    def record_artifact_ref(
        self,
        *,
        job_id: str,
        artifact_kind: str,
        path: str,
        sha256: str,
    ) -> ArtifactRefRecord:
        with self._connection.transaction():
            row = self._connection.fetch_one(
                """
                INSERT INTO artifact_refs (
                    job_id,
                    artifact_kind,
                    path,
                    sha256,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, job_id, artifact_kind, path, sha256, created_at
                """,
                (job_id, artifact_kind, path, sha256, _utc_now()),
            )
        if row is None:
            raise RuntimeError("PostgreSQL did not return an artifact ref row")
        return ArtifactRefRecord.model_validate(row)

    def record_json_artifact(
        self,
        *,
        job_id: str,
        story_number: str,
        artifact_kind: str,
        schema_version: str,
        payload: dict[str, Any],
    ) -> ArtifactBlobRecord:
        canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        artifact_sha256 = _sha256_text(canonical_payload)
        now = _utc_now()
        with self._connection.transaction():
            blob_row = self._connection.fetch_one(
                """
                INSERT INTO artifact_blobs (
                    job_id,
                    story_number,
                    artifact_kind,
                    schema_version,
                    payload_json,
                    sha256,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s)
                RETURNING id, job_id, story_number, artifact_kind, schema_version,
                          payload_json, sha256, created_at
                """,
                (
                    job_id,
                    story_number,
                    artifact_kind,
                    schema_version,
                    canonical_payload,
                    artifact_sha256,
                    now,
                ),
            )
            if blob_row is None:
                raise RuntimeError("PostgreSQL did not return an artifact blob row")
            artifact_id = int(cast(SupportsInt, blob_row["id"]))
            self._connection.fetch_one(
                """
                INSERT INTO artifact_refs (
                    job_id,
                    artifact_kind,
                    path,
                    sha256,
                    artifact_id,
                    created_at
                )
                VALUES (%s, %s, 'db://artifact_blobs/' || %s, %s, %s, %s)
                RETURNING id, job_id, artifact_kind, path, sha256,
                          artifact_id, created_at
                """,
                (
                    job_id,
                    artifact_kind,
                    artifact_id,
                    artifact_sha256,
                    artifact_id,
                    now,
                ),
            )
        return ArtifactBlobRecord.model_validate(blob_row)

    def artifact_refs_for_job(self, job_id: str) -> list[ArtifactRefRecord]:
        rows = self._connection.fetch_all(
            """
            SELECT id, job_id, artifact_kind, path, sha256, artifact_id, created_at
            FROM artifact_refs
            WHERE job_id = %s
            ORDER BY id
            """,
            (job_id,),
        )
        return [ArtifactRefRecord.model_validate(row) for row in rows]

    def get_artifact_blob(self, artifact_id: int) -> ArtifactBlobRecord:
        row = self._connection.fetch_one(
            """
            SELECT id, job_id, story_number, artifact_kind, schema_version,
                   payload_json, sha256, created_at
            FROM artifact_blobs
            WHERE id = %s
            """,
            (artifact_id,),
        )
        if row is None:
            raise KeyError(f"Artifact blob not found: {artifact_id}")
        return ArtifactBlobRecord.model_validate(row)

    def prune_expired_records(
        self,
        *,
        policy: RetentionPolicy,
        now: datetime | None = None,
    ) -> RetentionPruneReport:
        """Delete expired prunable records and return an audit-ready report.

        Only artifact_blobs and job_events rows older than the configured
        window whose fulfillment job is terminal are deleted. Deletes run in
        bounded batches, each in its own short transaction, and every prune
        run that deletes rows writes retention_prune_audit evidence.
        """
        pruned_at = now if now is not None else _utc_now()
        if not policy.enabled:
            return RetentionPruneReport(
                enabled=False,
                pruned_at=pruned_at,
                prune_batch_size=policy.prune_batch_size,
                results=[],
            )
        results: list[RetentionClassPruneResult] = []
        if policy.artifact_blob_retention_days is not None:
            results.append(
                self._prune_record_class(
                    record_class="artifact_blobs",
                    sql=_PRUNE_ARTIFACT_BLOBS_SQL,
                    cutoff=pruned_at - timedelta(days=policy.artifact_blob_retention_days),
                    batch_size=policy.prune_batch_size,
                )
            )
        if policy.job_event_retention_days is not None:
            results.append(
                self._prune_record_class(
                    record_class="job_events",
                    sql=_PRUNE_JOB_EVENTS_SQL,
                    cutoff=pruned_at - timedelta(days=policy.job_event_retention_days),
                    batch_size=policy.prune_batch_size,
                )
            )
        self._record_prune_audit(results=results, pruned_at=pruned_at)
        return RetentionPruneReport(
            enabled=True,
            pruned_at=pruned_at,
            prune_batch_size=policy.prune_batch_size,
            results=results,
        )

    def _prune_record_class(
        self,
        *,
        record_class: str,
        sql: str,
        cutoff: datetime,
        batch_size: int,
    ) -> RetentionClassPruneResult:
        deleted_count = 0
        batches = 0
        while True:
            with self._connection.transaction():
                row = self._connection.fetch_one(sql, (cutoff, cutoff, batch_size))
            if row is None:
                raise RuntimeError(
                    f"PostgreSQL did not return a retention prune count for {record_class}"
                )
            deleted_in_batch = int(cast(SupportsInt, row["deleted_count"]))
            batches += 1
            deleted_count += deleted_in_batch
            if deleted_in_batch < batch_size:
                break
        return RetentionClassPruneResult(
            record_class=record_class,
            cutoff=cutoff,
            deleted_count=deleted_count,
            batches=batches,
        )

    def _record_prune_audit(
        self,
        *,
        results: Sequence[RetentionClassPruneResult],
        pruned_at: datetime,
    ) -> None:
        audited = [result for result in results if result.deleted_count > 0]
        if not audited:
            return
        with self._connection.transaction():
            for result in audited:
                self._connection.execute(
                    """
                    INSERT INTO retention_prune_audit (
                        record_class,
                        cutoff,
                        deleted_count,
                        batches,
                        pruned_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        result.record_class,
                        result.cutoff,
                        result.deleted_count,
                        result.batches,
                        pruned_at,
                    ),
                )


OperationalStore = PostgresOperationalStore


def _sha256_text(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def connect_operational_store(database_url: str) -> PostgresOperationalStore:
    import psycopg
    from psycopg.rows import dict_row

    raw_connection = psycopg.connect(
        database_url,
        row_factory=dict_row,
        autocommit=True,
    )
    store = PostgresOperationalStore(PsycopgOperationalConnection(raw_connection))
    store.initialize_schema()
    return store
