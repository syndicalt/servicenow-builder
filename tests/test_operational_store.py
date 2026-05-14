from __future__ import annotations

import sys
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

from jedi_devproject.lifecycle_events import (
    LifecycleEventType,
    LifecycleStateChangeEvent,
)
from jedi_devproject.operational_store import (
    ArtifactBlobRecord,
    ArtifactRefRecord,
    FulfillmentJobRecord,
    OperationalConnection,
    PostgresOperationalStore,
    connect_operational_store,
    load_operational_store_migration,
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
    assert "CREATE TABLE IF NOT EXISTS artifact_blobs" in migration
    assert "payload_json JSONB NOT NULL" in migration
    assert "schema_version TEXT NOT NULL" in migration
    assert "CREATE TABLE IF NOT EXISTS artifact_refs" in migration
    assert "artifact_id BIGINT REFERENCES artifact_blobs(id)" in migration


def test_packaged_operational_store_migration_matches_reviewed_sql() -> None:
    reviewed_migration = Path("db/migrations/0001_operational_store.sql").read_text(
        encoding="utf-8"
    )

    assert load_operational_store_migration() == reviewed_migration


def test_connect_operational_store_requires_postgres_database_url() -> None:
    assert connect_operational_store.__annotations__["database_url"] == "str"


def test_connect_operational_store_enables_autocommit_for_request_safe_reads(
    monkeypatch: Any,
) -> None:
    connect_calls: list[dict[str, object]] = []

    class FakeRawConnection:
        def cursor(self) -> Any:
            return ScriptedCursor()

        @contextmanager
        def transaction(self) -> Iterator[None]:
            yield

        def close(self) -> None:
            pass

    class ScriptedCursor:
        def __enter__(self) -> ScriptedCursor:
            return self

        def __exit__(self, *_args: object) -> None:
            pass

        def execute(self, _sql: str, _params: tuple[object, ...] = ()) -> None:
            pass

    def fake_connect(*args: object, **kwargs: object) -> FakeRawConnection:
        connect_calls.append({"args": args, "kwargs": kwargs})
        return FakeRawConnection()

    psycopg_module = ModuleType("psycopg")
    psycopg_module.connect = fake_connect  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "psycopg", psycopg_module)
    monkeypatch.setitem(
        sys.modules,
        "psycopg.rows",
        SimpleNamespace(dict_row=object()),
    )

    store = connect_operational_store("postgresql://jedi:test@localhost:5432/jedi")

    store.close()
    assert connect_calls == [
        {
            "args": ("postgresql://jedi:test@localhost:5432/jedi",),
            "kwargs": {
                "row_factory": sys.modules["psycopg.rows"].dict_row,
                "autocommit": True,
            },
        }
    ]


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
    assert "UNION ALL" in joined_sql
    assert "NOT EXISTS (SELECT 1 FROM inserted_job)" in joined_sql
    assert "INSERT INTO job_events" in joined_sql
    assert job == FulfillmentJobRecord.model_validate(_job_row())
    assert connection.transaction_count == 1


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
    assert connection.transaction_count == 1


def test_record_json_artifact_persists_payload_and_db_backed_ref() -> None:
    blob_row: dict[str, Any] = {
        "id": 7,
        "job_id": "job-evt-job",
        "story_number": "STRY0010013",
        "artifact_kind": "implementation_packet",
        "schema_version": "implementation-packet-v1",
        "payload_json": {"story": {"number": "STRY0010013"}, "task": "generate"},
        "sha256": "b" * 64,
        "created_at": datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
    }
    ref_row: dict[str, Any] = {
        "id": 8,
        "job_id": "job-evt-job",
        "artifact_kind": "implementation_packet",
        "path": "db://artifact_blobs/7",
        "sha256": "b" * 64,
        "artifact_id": 7,
        "created_at": datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
    }
    connection = ScriptedPostgresConnection(rows=[blob_row, ref_row])
    store = _store(connection)

    artifact = store.record_json_artifact(
        job_id="job-evt-job",
        story_number="STRY0010013",
        artifact_kind="implementation_packet",
        schema_version="implementation-packet-v1",
        payload={"task": "generate", "story": {"number": "STRY0010013"}},
    )

    joined_sql = "\n".join(sql for sql, _params in connection.executed)
    assert "INSERT INTO artifact_blobs" in joined_sql
    assert "INSERT INTO artifact_refs" in joined_sql
    assert "db://artifact_blobs/" in joined_sql
    assert artifact == ArtifactBlobRecord.model_validate(blob_row)
    assert connection.executed[0][1][4] == (
        '{"story":{"number":"STRY0010013"},"task":"generate"}'
    )
    assert connection.transaction_count == 1


def test_artifact_refs_include_artifact_id_when_present() -> None:
    row: dict[str, Any] = {
        "id": 8,
        "job_id": "job-evt-job",
        "artifact_kind": "implementation_packet",
        "path": "db://artifact_blobs/7",
        "sha256": "b" * 64,
        "artifact_id": 7,
        "created_at": datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
    }
    connection = ScriptedPostgresConnection(rows=[[row]])
    store = _store(connection)

    refs = store.artifact_refs_for_job("job-evt-job")

    assert refs == [ArtifactRefRecord.model_validate(row)]


def test_get_artifact_blob_returns_typed_payload() -> None:
    row: dict[str, Any] = {
        "id": 7,
        "job_id": "job-evt-job",
        "story_number": "STRY0010013",
        "artifact_kind": "implementation_candidate",
        "schema_version": "implementation-candidate-v1",
        "payload_json": {"story_number": "STRY0010013", "changes": []},
        "sha256": "c" * 64,
        "created_at": datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
    }
    connection = ScriptedPostgresConnection(rows=[row])
    store = _store(connection)

    artifact = store.get_artifact_blob(7)

    joined_sql = "\n".join(sql for sql, _params in connection.executed)
    assert "FROM artifact_blobs" in joined_sql
    assert artifact == ArtifactBlobRecord.model_validate(row)


def test_get_artifact_blob_raises_for_missing_artifact() -> None:
    connection = ScriptedPostgresConnection(rows=[None])
    store = _store(connection)

    try:
        store.get_artifact_blob(404)
    except KeyError as exc:
        assert "Artifact blob not found: 404" in str(exc)
    else:
        raise AssertionError("missing artifact blob did not raise")
