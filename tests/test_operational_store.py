from __future__ import annotations

import sys
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

from pydantic import ValidationError

from jedi_devproject.lifecycle_events import (
    LifecycleEventType,
    LifecycleStateChangeEvent,
)
from jedi_devproject.operational_store import (
    ArtifactBlobRecord,
    ArtifactRefRecord,
    FulfillmentJobRecord,
    LifecycleEventRecord,
    OperationalConnection,
    PostgresOperationalStore,
    RetentionPolicy,
    SurfaceMaturityEvidenceRecord,
    connect_operational_store,
    load_operational_store_migration,
    load_operational_store_migrations,
    load_retention_policy,
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
    story_sys_id: str | None = None,
) -> LifecycleStateChangeEvent:
    return LifecycleStateChangeEvent(
        event_id=event_id,
        event_type=LifecycleEventType.STORY_STATE_CHANGED,
        source="servicenow",
        table="rm_story",
        story_number=story_number,
        story_sys_id=story_sys_id,
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
        "locked_at": datetime(2026, 5, 13, 15, 1, tzinfo=UTC) if status == "running" else None,
        "last_error": None,
        "story_sys_id": "rm-story-sys-id",
        "correlation_id": "corr-evt-job",
    }


def test_postgres_migration_defines_operational_schema() -> None:
    migration = Path("db/migrations/0001_operational_store.sql").read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS lifecycle_events" in migration
    assert "payload_json JSONB NOT NULL" in migration
    assert "received_at TIMESTAMPTZ NOT NULL" in migration
    assert "CREATE TABLE IF NOT EXISTS fulfillment_jobs" in migration
    assert "event_id TEXT NOT NULL UNIQUE" in migration
    assert "locked_by TEXT" in migration
    assert "locked_at TIMESTAMPTZ" in migration
    assert "CREATE TABLE IF NOT EXISTS job_events" in migration
    assert "payload_json->>'correlation_id'" in migration
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
                "correlation_id": "corr-evt-job",
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
    assert record.correlation_id == "corr-evt-job"


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
    assert "payload_json->>'story_sys_id' AS story_sys_id" in joined_sql
    assert "lifecycle_events.payload_json->>'correlation_id'" in joined_sql
    assert job == FulfillmentJobRecord.model_validate(_job_row())
    assert job.story_sys_id == "rm-story-sys-id"
    assert job.correlation_id == "corr-evt-job"
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


def test_close_latest_fulfillment_job_for_story_records_uat_complete_event() -> None:
    connection = ScriptedPostgresConnection(rows=[_job_row(status="completed", attempt_count=1)])
    store = _store(connection)

    completed_job = store.close_latest_fulfillment_job_for_story(
        story_number="STRY0010013",
        event_id="evt-uat-complete",
    )

    executed_sql = connection.executed[0][0]
    executed_params = connection.executed[0][1]
    assert completed_job is not None
    assert completed_job.status == "completed"
    assert completed_job.story_number == "STRY0010013"
    assert "WHERE story_number = %s" in executed_sql
    assert "ORDER BY created_at DESC, job_id DESC" in executed_sql
    assert "story_completed" in executed_params
    assert (
        "Story marked Complete in ServiceNow by lifecycle event evt-uat-complete" in executed_params
    )
    assert "STRY0010013" in executed_params


def test_record_rework_requested_for_story_records_rework_event_without_reopening_job() -> None:
    connection = ScriptedPostgresConnection(rows=[_job_row(status="completed", attempt_count=1)])
    store = _store(connection)

    job = store.record_rework_requested_for_story(
        story_number="STRY0010013",
        event_id="evt-uat-rework",
        target_state="Ready",
    )

    executed_sql = connection.executed[0][0]
    executed_params = connection.executed[0][1]
    assert job is not None
    assert job.status == "completed"
    assert job.story_number == "STRY0010013"
    assert "WHERE story_number = %s" in executed_sql
    assert "ORDER BY created_at DESC, job_id DESC" in executed_sql
    assert "INSERT INTO job_events" in executed_sql
    assert "UPDATE fulfillment_jobs" not in executed_sql
    assert "rework_requested" in executed_params
    assert (
        "Story returned to Ready from Ready for Testing by lifecycle event evt-uat-rework"
        in executed_params
    )
    assert "STRY0010013" in executed_params


def test_reject_latest_fulfillment_job_marks_rejected_without_deleting_artifacts() -> None:
    rejected_row = _job_row(status="rejected", attempt_count=1)
    rejected_row["last_error"] = "Story returned to Draft from Ready for Testing"
    connection = ScriptedPostgresConnection(rows=[rejected_row])
    store = _store(connection)

    job = store.reject_latest_fulfillment_job_for_story(
        story_number="STRY0010013",
        event_id="evt-story-rejected",
    )

    joined_sql = "\n".join(sql for sql, _params in connection.executed)
    executed_params = connection.executed[0][1]
    assert job is not None
    assert job.status == "rejected"
    assert job.story_number == "STRY0010013"
    assert "UPDATE fulfillment_jobs" in joined_sql
    assert "status = 'rejected'" in joined_sql
    assert "DELETE FROM artifact_refs" not in joined_sql
    assert "DELETE FROM artifact_blobs" not in joined_sql
    assert "story_rejected" in executed_params
    assert (
        "Story returned to Draft from Ready for Testing by lifecycle event evt-story-rejected"
        in executed_params
    )


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
    assert connection.executed[0][1][4] == ('{"story":{"number":"STRY0010013"},"task":"generate"}')
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


def test_recent_lifecycle_events_returns_newest_events() -> None:
    row = {
        "event_id": "evt-002",
        "event_type": "story_state_changed",
        "story_number": "STRY0010002",
        "payload_json": {"story_number": "STRY0010002"},
        "received_at": datetime(2026, 5, 14, 18, 0, tzinfo=UTC),
        "validation_status": "accepted",
    }
    connection = ScriptedPostgresConnection(rows=[[row]])
    store = _store(connection)

    events = store.recent_lifecycle_events(limit=10)

    joined_sql = "\n".join(sql for sql, _params in connection.executed)
    assert "FROM lifecycle_events" in joined_sql
    assert "ORDER BY received_at DESC, event_id DESC" in joined_sql
    assert connection.executed[0][1] == (10,)
    assert events == [LifecycleEventRecord.model_validate(row)]


def test_retention_migration_defines_prune_audit_and_created_at_indexes() -> None:
    migration = Path("db/migrations/0002_retention.sql").read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS retention_prune_audit" in migration
    assert "record_class TEXT NOT NULL" in migration
    assert "cutoff TIMESTAMPTZ NOT NULL" in migration
    assert "deleted_count BIGINT NOT NULL" in migration
    assert "pruned_at TIMESTAMPTZ NOT NULL" in migration
    assert "idx_artifact_blobs_created_at" in migration
    assert "idx_job_events_created_at" in migration


def test_packaged_migrations_match_reviewed_sql_in_order() -> None:
    reviewed_retention = Path("db/migrations/0002_retention.sql").read_text(encoding="utf-8")

    assert load_operational_store_migrations() == (
        load_operational_store_migration(),
        reviewed_retention,
    )


def test_initialize_schema_applies_all_migrations_in_order() -> None:
    connection = ScriptedPostgresConnection(rows=[])
    store = _store(connection)

    store.initialize_schema()

    assert len(connection.executed) == 2
    assert "CREATE TABLE IF NOT EXISTS lifecycle_events" in connection.executed[0][0]
    assert "CREATE TABLE IF NOT EXISTS retention_prune_audit" in connection.executed[1][0]
    assert connection.transaction_count == 1


def test_retention_policy_is_disabled_by_default() -> None:
    policy = load_retention_policy({})

    assert policy.enabled is False
    assert policy.artifact_blob_retention_days is None
    assert policy.job_event_retention_days is None
    assert policy.prune_batch_size == 500


def test_load_retention_policy_enables_explicit_windows() -> None:
    policy = load_retention_policy(
        {
            "JEDI_RETENTION_ARTIFACT_BLOB_DAYS": "90",
            "JEDI_RETENTION_JOB_EVENT_DAYS": "365",
            "JEDI_RETENTION_PRUNE_BATCH_SIZE": "200",
        }
    )

    assert policy.enabled is True
    assert policy.artifact_blob_retention_days == 90
    assert policy.job_event_retention_days == 365
    assert policy.prune_batch_size == 200


def test_load_retention_policy_treats_blank_values_as_disabled() -> None:
    policy = load_retention_policy(
        {
            "JEDI_RETENTION_ARTIFACT_BLOB_DAYS": " ",
            "JEDI_RETENTION_JOB_EVENT_DAYS": "",
            "JEDI_RETENTION_PRUNE_BATCH_SIZE": "",
        }
    )

    assert policy.enabled is False
    assert policy.prune_batch_size == 500


def test_load_retention_policy_rejects_non_positive_windows() -> None:
    try:
        load_retention_policy({"JEDI_RETENTION_ARTIFACT_BLOB_DAYS": "0"})
    except ValidationError as exc:
        assert "artifact_blob_retention_days" in str(exc)
    else:
        raise AssertionError("non-positive retention window did not raise")


def test_prune_expired_records_is_noop_when_retention_disabled() -> None:
    connection = ScriptedPostgresConnection(rows=[])
    store = _store(connection)

    report = store.prune_expired_records(policy=RetentionPolicy())

    assert report.enabled is False
    assert report.results == []
    assert connection.executed == []
    assert connection.transaction_count == 0


def test_prune_expired_records_deletes_only_terminal_expired_records() -> None:
    connection = ScriptedPostgresConnection(rows=[{"deleted_count": 2}, {"deleted_count": 1}])
    store = _store(connection)
    now = datetime(2026, 6, 11, 12, 0, tzinfo=UTC)
    policy = RetentionPolicy(artifact_blob_retention_days=90, job_event_retention_days=365)

    report = store.prune_expired_records(policy=policy, now=now)

    blob_sql, blob_params = connection.executed[0]
    event_sql, event_params = connection.executed[1]
    assert "FROM artifact_blobs" in blob_sql
    assert "status IN ('completed', 'failed', 'rejected')" in blob_sql
    assert "fulfillment_jobs.updated_at < %s" in blob_sql
    assert "SET artifact_id = NULL" in blob_sql
    assert "DELETE FROM artifact_blobs" in blob_sql
    assert "DELETE FROM artifact_refs" not in blob_sql
    assert "LIMIT %s" in blob_sql
    assert blob_params == (now - timedelta(days=90), now - timedelta(days=90), 500)
    assert "DELETE FROM job_events" in event_sql
    assert "status IN ('completed', 'failed', 'rejected')" in event_sql
    assert event_params == (now - timedelta(days=365), now - timedelta(days=365), 500)
    audit_calls = [
        params
        for sql, params in connection.executed
        if "INSERT INTO retention_prune_audit" in sql
    ]
    assert audit_calls == [
        ("artifact_blobs", now - timedelta(days=90), 2, 1, now),
        ("job_events", now - timedelta(days=365), 1, 1, now),
    ]
    assert report.enabled is True
    assert report.pruned_at == now
    assert report.prune_batch_size == 500
    assert [
        (result.record_class, result.cutoff, result.deleted_count, result.batches)
        for result in report.results
    ] == [
        ("artifact_blobs", now - timedelta(days=90), 2, 1),
        ("job_events", now - timedelta(days=365), 1, 1),
    ]


def test_prune_expired_records_batches_deletes_until_drained() -> None:
    connection = ScriptedPostgresConnection(
        rows=[{"deleted_count": 2}, {"deleted_count": 2}, {"deleted_count": 0}]
    )
    store = _store(connection)
    policy = RetentionPolicy(artifact_blob_retention_days=30, prune_batch_size=2)

    report = store.prune_expired_records(policy=policy)

    delete_calls = [
        params for sql, params in connection.executed if "DELETE FROM artifact_blobs" in sql
    ]
    assert [params[2] for params in delete_calls] == [2, 2, 2]
    assert all("DELETE FROM job_events" not in sql for sql, _params in connection.executed)
    assert [
        (result.record_class, result.deleted_count, result.batches) for result in report.results
    ] == [("artifact_blobs", 4, 3)]


def test_prune_expired_records_supports_job_event_only_window() -> None:
    connection = ScriptedPostgresConnection(rows=[{"deleted_count": 1}])
    store = _store(connection)
    policy = RetentionPolicy(job_event_retention_days=365)

    report = store.prune_expired_records(policy=policy)

    assert all("DELETE FROM artifact_blobs" not in sql for sql, _params in connection.executed)
    assert any("DELETE FROM job_events" in sql for sql, _params in connection.executed)
    assert [result.record_class for result in report.results] == ["job_events"]


def test_prune_expired_records_rerun_deletes_nothing_and_writes_no_audit() -> None:
    connection = ScriptedPostgresConnection(rows=[{"deleted_count": 0}, {"deleted_count": 0}])
    store = _store(connection)
    policy = RetentionPolicy(artifact_blob_retention_days=90, job_event_retention_days=90)

    report = store.prune_expired_records(policy=policy)

    assert all(result.deleted_count == 0 for result in report.results)
    assert all(
        "INSERT INTO retention_prune_audit" not in sql for sql, _params in connection.executed
    )


def test_prune_expired_records_raises_when_postgres_returns_no_count() -> None:
    connection = ScriptedPostgresConnection(rows=[None])
    store = _store(connection)
    policy = RetentionPolicy(artifact_blob_retention_days=90)

    try:
        store.prune_expired_records(policy=policy)
    except RuntimeError as exc:
        assert "retention prune count" in str(exc)
        assert "artifact_blobs" in str(exc)
    else:
        raise AssertionError("missing prune count row did not raise")


def test_builder_maturity_evidence_for_surface_aggregates_terminal_outcomes() -> None:
    connection = ScriptedPostgresConnection(rows=[{"samples": 12, "successes": 9, "failures": 3}])
    store = _store(connection)

    evidence = store.builder_maturity_evidence_for_surface("form_sections")

    executed_sql, executed_params = connection.executed[0]
    assert "FROM fulfillment_jobs" in executed_sql
    assert "status IN ('completed', 'failed', 'rejected')" in executed_sql
    assert "artifact_blobs.artifact_kind = 'implementation_packet'" in executed_sql
    assert "'context_dossier'->'target'->'required_surfaces' ? %s" in executed_sql
    assert "status = 'rework_requested'" in executed_sql
    assert executed_params == ("form_sections",)
    assert all(
        token not in executed_sql for token in ["INSERT", "UPDATE", "DELETE"]
    ), "maturity evidence aggregation must be read-only"
    assert evidence == SurfaceMaturityEvidenceRecord(
        surface="form_sections",
        samples=12,
        successes=9,
        failures=3,
    )


def test_builder_maturity_evidence_for_surface_raises_when_no_count_row() -> None:
    connection = ScriptedPostgresConnection(rows=[None])
    store = _store(connection)

    try:
        store.builder_maturity_evidence_for_surface("form_sections")
    except RuntimeError as exc:
        assert "surface maturity evidence" in str(exc)
        assert "form_sections" in str(exc)
    else:
        raise AssertionError("missing maturity evidence row did not raise")


def test_recent_fulfillment_jobs_returns_newest_jobs() -> None:
    row = _job_row(status="rejected", attempt_count=1)
    connection = ScriptedPostgresConnection(rows=[[row]])
    store = _store(connection)

    jobs = store.recent_fulfillment_jobs(limit=25)

    joined_sql = "\n".join(sql for sql, _params in connection.executed)
    assert "FROM fulfillment_jobs" in joined_sql
    assert "ORDER BY updated_at DESC, job_id DESC" in joined_sql
    assert connection.executed[0][1] == (25,)
    assert jobs == [FulfillmentJobRecord.model_validate(row)]
