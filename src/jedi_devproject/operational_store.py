from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Self

from pydantic import BaseModel, ConfigDict

from jedi_devproject.lifecycle_events import LifecycleStateChangeEvent


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _row_to_dict(row: sqlite3.Row) -> dict[str, object]:
    return dict(row)


class LifecycleEventRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    event_type: str
    story_number: str
    payload_json: str
    received_at: str
    validation_status: str


class FulfillmentJobRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    event_id: str
    story_number: str
    status: str
    attempt_count: int
    created_at: str
    updated_at: str
    locked_by: str | None
    locked_at: str | None
    last_error: str | None


class JobEventRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    job_id: str
    status: str
    message: str | None
    created_at: str


class ArtifactRefRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    job_id: str
    artifact_kind: str
    path: str
    sha256: str
    created_at: str


class OperationalStore:
    def __init__(self, connection: sqlite3.Connection) -> None:
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
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS lifecycle_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                story_number TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                received_at TEXT NOT NULL,
                validation_status TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS fulfillment_jobs (
                job_id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL UNIQUE,
                story_number TEXT NOT NULL,
                status TEXT NOT NULL,
                attempt_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                locked_by TEXT,
                locked_at TEXT,
                last_error TEXT,
                FOREIGN KEY(event_id) REFERENCES lifecycle_events(event_id)
            );

            CREATE TABLE IF NOT EXISTS job_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(job_id) REFERENCES fulfillment_jobs(job_id)
            );

            CREATE TABLE IF NOT EXISTS artifact_refs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                artifact_kind TEXT NOT NULL,
                path TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(job_id) REFERENCES fulfillment_jobs(job_id)
            );

            CREATE INDEX IF NOT EXISTS idx_fulfillment_jobs_status_created
                ON fulfillment_jobs(status, created_at);
            CREATE INDEX IF NOT EXISTS idx_job_events_job_id
                ON job_events(job_id, id);
            CREATE INDEX IF NOT EXISTS idx_artifact_refs_job_id
                ON artifact_refs(job_id, id);
            """
        )
        self._connection.commit()

    def table_names(self) -> set[str]:
        rows = self._connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()
        return {str(row["name"]) for row in rows}

    def record_lifecycle_event(
        self,
        event: LifecycleStateChangeEvent,
        *,
        validation_status: str = "accepted",
    ) -> LifecycleEventRecord:
        payload_json = json.dumps(event.model_dump(mode="json"), sort_keys=True)
        received_at = _utc_now()
        with self._connection:
            self._connection.execute(
                """
                INSERT OR IGNORE INTO lifecycle_events (
                    event_id,
                    event_type,
                    story_number,
                    payload_json,
                    received_at,
                    validation_status
                )
                VALUES (?, ?, ?, ?, ?, ?)
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
        row = self._connection.execute(
            """
            SELECT event_id, event_type, story_number, payload_json,
                   received_at, validation_status
            FROM lifecycle_events
            WHERE event_id = ?
            """,
            (event_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Lifecycle event not found: {event_id}")
        return LifecycleEventRecord.model_validate(_row_to_dict(row))

    def enqueue_fulfillment_job(
        self,
        *,
        event_id: str,
        story_number: str,
    ) -> FulfillmentJobRecord:
        job_id = f"job-{event_id}"
        now = _utc_now()
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT OR IGNORE INTO fulfillment_jobs (
                    job_id,
                    event_id,
                    story_number,
                    status,
                    attempt_count,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, 'queued', 0, ?, ?)
                """,
                (job_id, event_id, story_number, now, now),
            )
            if cursor.rowcount == 1:
                self._connection.execute(
                    """
                    INSERT INTO job_events (job_id, status, message, created_at)
                    VALUES (?, 'queued', ?, ?)
                    """,
                    (job_id, "Fulfillment job queued", now),
                )

        return self.get_job(job_id)

    def claim_next_fulfillment_job(self, *, worker_id: str) -> FulfillmentJobRecord | None:
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            row = self._connection.execute(
                """
                SELECT job_id
                FROM fulfillment_jobs
                WHERE status = 'queued'
                ORDER BY created_at, job_id
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                self._connection.commit()
                return None

            job_id = str(row["job_id"])
            now = _utc_now()
            self._connection.execute(
                """
                UPDATE fulfillment_jobs
                SET status = 'running',
                    attempt_count = attempt_count + 1,
                    updated_at = ?,
                    locked_by = ?,
                    locked_at = ?
                WHERE job_id = ?
                """,
                (now, worker_id, now, job_id),
            )
            self._connection.execute(
                """
                INSERT INTO job_events (job_id, status, message, created_at)
                VALUES (?, 'running', ?, ?)
                """,
                (job_id, f"Fulfillment job claimed by {worker_id}", now),
            )
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise

        return self.get_job(job_id)

    def get_job(self, job_id: str) -> FulfillmentJobRecord:
        row = self._connection.execute(
            """
            SELECT job_id, event_id, story_number, status, attempt_count,
                   created_at, updated_at, locked_by, locked_at, last_error
            FROM fulfillment_jobs
            WHERE job_id = ?
            """,
            (job_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Fulfillment job not found: {job_id}")
        return FulfillmentJobRecord.model_validate(_row_to_dict(row))

    def job_events_for_job(self, job_id: str) -> list[JobEventRecord]:
        rows = self._connection.execute(
            """
            SELECT id, job_id, status, message, created_at
            FROM job_events
            WHERE job_id = ?
            ORDER BY id
            """,
            (job_id,),
        ).fetchall()
        return [JobEventRecord.model_validate(_row_to_dict(row)) for row in rows]

    def record_artifact_ref(
        self,
        *,
        job_id: str,
        artifact_kind: str,
        path: str,
        sha256: str,
    ) -> ArtifactRefRecord:
        now = _utc_now()
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO artifact_refs (
                    job_id,
                    artifact_kind,
                    path,
                    sha256,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (job_id, artifact_kind, path, sha256, now),
            )
        artifact_ref_id = cursor.lastrowid
        if artifact_ref_id is None:
            raise RuntimeError("SQLite did not return an artifact ref id")
        return self.get_artifact_ref(artifact_ref_id)

    def get_artifact_ref(self, artifact_ref_id: int) -> ArtifactRefRecord:
        row = self._connection.execute(
            """
            SELECT id, job_id, artifact_kind, path, sha256, created_at
            FROM artifact_refs
            WHERE id = ?
            """,
            (artifact_ref_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Artifact ref not found: {artifact_ref_id}")
        return ArtifactRefRecord.model_validate(_row_to_dict(row))

    def artifact_refs_for_job(self, job_id: str) -> list[ArtifactRefRecord]:
        rows = self._connection.execute(
            """
            SELECT id, job_id, artifact_kind, path, sha256, created_at
            FROM artifact_refs
            WHERE job_id = ?
            ORDER BY id
            """,
            (job_id,),
        ).fetchall()
        return [ArtifactRefRecord.model_validate(_row_to_dict(row)) for row in rows]


def connect_operational_store(path: Path) -> OperationalStore:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    store = OperationalStore(connection)
    store.initialize_schema()
    return store
