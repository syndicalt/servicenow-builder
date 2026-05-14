from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
from datetime import UTC, datetime
from importlib import resources
from types import TracebackType
from typing import Any, Protocol, Self, SupportsInt, cast

from pydantic import BaseModel, ConfigDict

from jedi_devproject.lifecycle_events import LifecycleStateChangeEvent

MIGRATION_PACKAGE = "jedi_devproject.migrations"
MIGRATION_FILENAME = "0001_operational_store.sql"


def _utc_now() -> datetime:
    return datetime.now(UTC)


def load_operational_store_migration() -> str:
    return (
        resources.files(MIGRATION_PACKAGE).joinpath(MIGRATION_FILENAME).read_text(encoding="utf-8")
    )


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
    received_at: datetime
    validation_status: str


class FulfillmentJobRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    event_id: str
    story_number: str
    status: str
    attempt_count: int
    created_at: datetime
    updated_at: datetime
    locked_by: str | None
    locked_at: datetime | None
    last_error: str | None


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
            self._connection.execute(load_operational_store_migration())

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
                SELECT job_id, event_id, story_number, status, attempt_count,
                       created_at, updated_at, locked_by, locked_at, last_error
                FROM selected_job
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
                SELECT job_id, event_id, story_number, status, attempt_count,
                       created_at, updated_at, locked_by, locked_at, last_error
                FROM updated_job
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
            SELECT job_id, event_id, story_number, status, attempt_count,
                   created_at, updated_at, locked_by, locked_at, last_error
            FROM fulfillment_jobs
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
