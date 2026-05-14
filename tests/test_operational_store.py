from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jedi_devproject.lifecycle_events import (
    LifecycleEventType,
    LifecycleStateChangeEvent,
)
from jedi_devproject.operational_store import (
    ArtifactRefRecord,
    FulfillmentJobRecord,
    OperationalConnection,
    PostgresOperationalStore,
    connect_operational_store,
)

ScriptedRow = dict[str, object]
ScriptedResult = ScriptedRow | list[ScriptedRow] | None


class ScriptedPostgresConnection:
    def __init__(self, rows: Sequence[ScriptedResult]) -> None:
        self._rows = list(rows)
        self.executed: list[tuple[str, tuple[object, ...]]] = []
        self.closed = False
        self.transaction_count = 0

    def execute(self, sql: str, params: tuple[object, ...] = ()) -> None:
        self.executed.append((sql, params))

    def fetch_one(
        self,
        sql: str,
        params: tuple[object, ...] = (),
    ) -> dict[str, object] | None:
        self.executed.append((sql, params))
        row = self._rows.pop(0)
        assert not isinstance(row, list)
        return row

    def fetch_all(
        self,
        sql: str,
        params: tuple[object, ...] = (),
    ) -> list[ScriptedRow]:
        self.executed.append((sql, params))
        row = self._rows.pop(0)
        assert isinstance(row, list)
        return row

    @contextmanager
    def transaction(self) -> Iterator[None]:
        self.transaction_count += 1
        yield

    def close(self) -> None:
        self.closed = True


def _store(connection: OperationalConnection) -> PostgresOperationalStore:
    return PostgresOperationalStore(connection)


def _lifecycle_event(
    *,
    event_id: str = "evt-001",
    story_number: str = "STRY0010013",
) -> LifecycleStateChangeEvent:
    return LifecycleStateChangeEvent(
        event_id=event_id,
        event_type=LifecycleEventType.STORY_STATE_CHANGED,
        source="servicenow",
        table="rm_story",
        story_number=story_number,
        previous_state="Draft",
        current_state="Ready",
        occurred_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
        correlation_id=f"corr-{event_id}",
        emitted_by="jedi-devproject-lifecycle-integration",
    )


def _job_row(*, status: str = "queued", attempt_count: int = 0) -> dict[str, object]:
    return {
        "job_id": "job-evt-job",
        "event_id": "evt-job",
        "story_number": "STRY0010013",
        "status": status,
        "attempt_count": attempt_count,
        "created_at": datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
        "updated_at": datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
        "locked_by": "worker-local-1" if status == "running" else None,
        "locked_at": datetime(2026, 5, 13, 15, 1, tzinfo=UTC)
        if status == "running"
        else None,
        "last_error": None,
    }


def test_postgres_migration_defines_operational_schema() -> None:
    migration = Path("db/migrations/0001_operational_store.sql").read_text(
        encoding="utf-8"
    )

    assert "CREATE TABLE IF NOT EXISTS lifecycle_events" in migration
    assert "payload_json JSONB NOT NULL" in migration
    assert "received_at TIMESTAMPTZ NOT NULL" in migration
    assert "CREATE TABLE IF NOT EXISTS fulfillment_jobs" in migration
    assert "event_id TEXT NOT NULL UNIQUE" in migration
    assert "locked_by TEXT" in migration
    assert "locked_at TIMESTAMPTZ" in migration
    assert "CREATE TABLE IF NOT EXISTS job_events" in migration
    assert "BIGSERIAL PRIMARY KEY" in migration
    assert "CREATE TABLE IF NOT EXISTS artifact_refs" in migration


def test_connect_operational_store_requires_postgres_database_url() -> None:
    assert connect_operational_store.__annotations__["database_url"] == "str"


def test_record_lifecycle_event_uses_postgres_idempotency() -> None:
    connection = ScriptedPostgresConnection(
        rows=[
            {
                "event_id": "evt-job",
                "event_type": "story_state_changed",
                "story_number": "STRY0010013",
                "payload_json": {"event_id": "evt-job", "story_number": "STRY0010013"},
                "received_at": datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
                "validation_status": "accepted",
            }
        ]
    )
    store = _store(connection)

    record = store.record_lifecycle_event(_lifecycle_event(event_id="evt-job"))

    joined_sql = "\n".join(sql for sql, _params in connection.executed)
    assert "ON CONFLICT (event_id) DO NOTHING" in joined_sql
    assert "%s" in joined_sql
    assert "?" not in joined_sql
    assert record.event_id == "evt-job"
    assert record.story_number == "STRY0010013"


def test_enqueue_fulfillment_job_uses_postgres_idempotency_and_job_event() -> None:
    connection = ScriptedPostgresConnection(rows=[_job_row()])
    store = _store(connection)

    job = store.enqueue_fulfillment_job(
        event_id="evt-job",
        story_number="STRY0010013",
    )

    joined_sql = "\n".join(sql for sql, _params in connection.executed)
    assert "ON CONFLICT (event_id) DO NOTHING" in joined_sql
    assert "INSERT INTO job_events" in joined_sql
    assert job == FulfillmentJobRecord.model_validate(_job_row())


def test_claim_next_fulfillment_job_uses_skip_locked_worker_claim() -> None:
    connection = ScriptedPostgresConnection(rows=[_job_row(status="running", attempt_count=1)])
    store = _store(connection)

    claimed_job = store.claim_next_fulfillment_job(worker_id="worker-local-1")

    joined_sql = "\n".join(sql for sql, _params in connection.executed)
    assert "FOR UPDATE SKIP LOCKED" in joined_sql
    assert "UPDATE fulfillment_jobs" in joined_sql
    assert "RETURNING" in joined_sql
    assert connection.transaction_count == 1
    assert claimed_job is not None
    assert claimed_job.status == "running"
    assert claimed_job.attempt_count == 1
    assert claimed_job.locked_by == "worker-local-1"


def test_claim_next_fulfillment_job_returns_none_when_no_job_is_available() -> None:
    connection = ScriptedPostgresConnection(rows=[None])
    store = _store(connection)

    claimed_job = store.claim_next_fulfillment_job(worker_id="worker-local-1")

    assert claimed_job is None
    assert connection.transaction_count == 1


def test_complete_fulfillment_job_marks_completed_and_records_event() -> None:
    connection = ScriptedPostgresConnection(rows=[_job_row(status="completed", attempt_count=1)])
    store = _store(connection)

    completed_job = store.complete_fulfillment_job(
        job_id="job-evt-job",
        message="Fulfillment completed",
    )

    joined_sql = "\n".join(sql for sql, _params in connection.executed)
    assert "UPDATE fulfillment_jobs" in joined_sql
    assert connection.executed[0][1][0] == "completed"
    assert "locked_by = NULL" in joined_sql
    assert "INSERT INTO job_events" in joined_sql
    assert completed_job.status == "completed"
    assert completed_job.locked_by is None


def test_fail_fulfillment_job_marks_failed_and_preserves_error() -> None:
    failed_row = _job_row(status="failed", attempt_count=1)
    failed_row["last_error"] = "provider unavailable"
    connection = ScriptedPostgresConnection(rows=[failed_row])
    store = _store(connection)

    failed_job = store.fail_fulfillment_job(
        job_id="job-evt-job",
        error_message="provider unavailable",
    )

    joined_sql = "\n".join(sql for sql, _params in connection.executed)
    assert "UPDATE fulfillment_jobs" in joined_sql
    assert connection.executed[0][1][0] == "failed"
    assert "last_error = %s" in joined_sql
    assert "INSERT INTO job_events" in joined_sql
    assert failed_job.status == "failed"
    assert failed_job.last_error == "provider unavailable"


def test_record_artifact_ref_uses_postgres_returning_row() -> None:
    row: dict[str, Any] = {
        "id": 1,
        "job_id": "job-evt-job",
        "artifact_kind": "implementation_packet",
        "path": "artifacts/implementation-packets/packet.json",
        "sha256": "a" * 64,
        "created_at": datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
    }
    connection = ScriptedPostgresConnection(rows=[row])
    store = _store(connection)

    artifact_ref = store.record_artifact_ref(
        job_id="job-evt-job",
        artifact_kind="implementation_packet",
        path="artifacts/implementation-packets/packet.json",
        sha256="a" * 64,
    )

    joined_sql = "\n".join(sql for sql, _params in connection.executed)
    assert "INSERT INTO artifact_refs" in joined_sql
    assert "RETURNING" in joined_sql
    assert artifact_ref == ArtifactRefRecord.model_validate(row)
