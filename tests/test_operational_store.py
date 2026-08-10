from __future__ import annotations

import sys
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError

from jedi_devproject.lifecycle_events import (
    LifecycleEventType,
    LifecycleStateChangeEvent,
)
from jedi_devproject.operational_store import (
    ArtifactBlobRecord,
    ArtifactRefRecord,
    FulfillmentJobRecord,
    FulfillmentJobStatusSummaryRecord,
    JobEventRecord,
    LifecycleEventRecord,
    OperationalConnection,
    PostgresOperationalStore,
    RetentionClassPruneResult,
    RetentionPolicy,
    RetentionPruneReport,
    SurfaceMaturityEvidenceRecord,
    _ensure_lifecycle_event_payload_json_safe,
    _ensure_operational_artifact_payload_json_safe,
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


@pytest.mark.parametrize(
    ("model_class", "values", "sensitive_parts"),
    [
        (
            LifecycleEventRecord,
            {
                "event_id": 123,
                "event_type": "story_state_changed",
                "story_number": "STRY0010013",
                "payload_json": {"story_sys_id": "secret-story-sys-id"},
                "received_at": datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
                "validation_status": "accepted",
            },
            ("123", "secret-story-sys-id"),
        ),
        (
            FulfillmentJobRecord,
            {
                **_job_row(),
                "attempt_count": "secret-attempt",
                "last_error": "provider failed with token-secret",
            },
            ("secret-attempt", "token-secret"),
        ),
        (
            JobEventRecord,
            {
                "id": "secret-id",
                "job_id": "job-evt-job",
                "status": "failed",
                "message": "error includes secret-message",
                "created_at": datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
            },
            ("secret-id", "secret-message"),
        ),
        (
            ArtifactRefRecord,
            {
                "id": 1,
                "job_id": "job-evt-job",
                "artifact_kind": "implementation_candidate",
                "path": 123,
                "sha256": "a" * 64,
                "created_at": datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
            },
            ("123",),
        ),
        (
            ArtifactBlobRecord,
            {
                "id": 1,
                "job_id": "job-evt-job",
                "story_number": "STRY0010013",
                "artifact_kind": "implementation_candidate",
                "schema_version": "implementation-candidate-v1",
                "payload_json": "secret-payload",
                "sha256": "a" * 64,
                "created_at": datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
            },
            ("secret-payload",),
        ),
    ],
)
def test_operational_record_validation_errors_do_not_echo_rejected_inputs(
    model_class: type[Any],
    values: dict[str, Any],
    sensitive_parts: tuple[str, ...],
) -> None:
    with pytest.raises(ValidationError) as exc:
        model_class.model_validate(values)

    message = str(exc.value)
    assert "input_value" not in message
    for sensitive_part in sensitive_parts:
        assert sensitive_part not in message


def test_fulfillment_job_record_rejects_string_subclass_without_leak() -> None:
    class HostileJobText(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=operational-job-text")

    values = _job_row()
    values["job_id"] = HostileJobText("job-evt-job")

    with pytest.raises(ValidationError) as exc_info:
        FulfillmentJobRecord.model_validate(values)

    diagnostic = str(exc_info.value)
    assert "operational store record scalar is unsafe" in diagnostic
    assert "HostileJobText" not in diagnostic
    assert "operational-job-text" not in diagnostic
    assert "client_secret" not in diagnostic


def test_lifecycle_event_record_rejects_payload_subclass_without_leak() -> None:
    class HostilePayload(dict[str, object]):
        def items(self) -> Any:
            raise AssertionError("client_secret=operational-payload")

    values = {
        "event_id": "evt-001",
        "event_type": "story_state_changed",
        "story_number": "STRY0010013",
        "payload_json": HostilePayload({"story_sys_id": "secret-story-sys-id"}),
        "received_at": datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
        "validation_status": "accepted",
    }

    with pytest.raises(ValidationError) as exc_info:
        LifecycleEventRecord.model_validate(values)

    diagnostic = str(exc_info.value)
    assert "operational store record payload is unsafe" in diagnostic
    assert "HostilePayload" not in diagnostic
    assert "operational-payload" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "secret-story-sys-id" not in diagnostic


def test_lifecycle_event_record_rejects_cyclic_payload_without_leak() -> None:
    payload: dict[str, object] = {"story_sys_id": "secret-story-sys-id"}
    payload["self"] = payload
    values = {
        "event_id": "evt-001",
        "event_type": "story_state_changed",
        "story_number": "STRY0010013",
        "payload_json": payload,
        "received_at": datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
        "validation_status": "accepted",
    }

    with pytest.raises(ValidationError) as exc_info:
        LifecycleEventRecord.model_validate(values)

    diagnostic = str(exc_info.value)
    assert "operational store record payload is unsafe" in diagnostic
    assert "RecursionError" not in diagnostic
    assert "story_sys_id" not in diagnostic
    assert "secret-story-sys-id" not in diagnostic


def test_lifecycle_event_record_rejects_excessively_nested_payload_without_leak() -> None:
    payload: dict[str, object] = {"leaf": "secret-story-sys-id"}
    for _index in range(40):
        payload = {"nested": payload}
    values = {
        "event_id": "evt-001",
        "event_type": "story_state_changed",
        "story_number": "STRY0010013",
        "payload_json": payload,
        "received_at": datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
        "validation_status": "accepted",
    }

    with pytest.raises(ValidationError) as exc_info:
        LifecycleEventRecord.model_validate(values)

    diagnostic = str(exc_info.value)
    assert "operational store record payload is unsafe" in diagnostic
    assert "leaf" not in diagnostic
    assert "secret-story-sys-id" not in diagnostic


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


def test_record_lifecycle_event_rejects_non_finite_payload_before_transaction(
    recwarn: pytest.WarningsRecorder,
) -> None:
    connection = ScriptedPostgresConnection(rows=[])
    store = _store(connection)
    event = LifecycleStateChangeEvent.model_construct(
        event_id=float("nan"),
        event_type=LifecycleEventType.STORY_STATE_CHANGED,
        source="servicenow",
        table="rm_story",
        story_number="STRY0010013",
        story_sys_id="secret-story-sys-id",
        previous_state="Draft",
        current_state="Ready",
        occurred_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
        correlation_id="corr-secret",
        emitted_by="jedi-devproject-lifecycle-integration",
    )

    with pytest.raises(ValueError) as exc_info:
        store.record_lifecycle_event(event)

    diagnostic = str(exc_info.value)
    assert diagnostic == "operational lifecycle event payload contains non-finite numeric values"
    assert exc_info.value.__cause__ is None
    assert "event_id" not in diagnostic
    assert "NaN" not in diagnostic
    assert "secret-story-sys-id" not in diagnostic
    assert "corr-secret" not in diagnostic
    assert list(recwarn) == []
    assert connection.executed == []
    assert connection.transaction_count == 0


def test_record_lifecycle_event_rejects_non_json_payload_before_transaction(
    recwarn: pytest.WarningsRecorder,
) -> None:
    class StringifiesSecret:
        def __str__(self) -> str:
            return "event-secret"

    connection = ScriptedPostgresConnection(rows=[])
    store = _store(connection)
    event = LifecycleStateChangeEvent.model_construct(
        event_id=StringifiesSecret(),
        event_type=LifecycleEventType.STORY_STATE_CHANGED,
        source="servicenow",
        table="rm_story",
        story_number="STRY0010013",
        story_sys_id="secret-story-sys-id",
        previous_state="Draft",
        current_state="Ready",
        occurred_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
        correlation_id="corr-secret",
        emitted_by="jedi-devproject-lifecycle-integration",
    )

    with pytest.raises(ValueError) as exc_info:
        store.record_lifecycle_event(event)

    diagnostic = str(exc_info.value)
    assert diagnostic == "operational lifecycle event payload contains non-JSON values"
    assert exc_info.value.__cause__ is None
    assert "event_id" not in diagnostic
    assert "StringifiesSecret" not in diagnostic
    assert "event-secret" not in diagnostic
    assert "secret-story-sys-id" not in diagnostic
    assert "corr-secret" not in diagnostic
    assert list(recwarn) == []
    assert connection.executed == []
    assert connection.transaction_count == 0


def test_record_lifecycle_event_rejects_string_subclass_payload_before_transaction(
    recwarn: pytest.WarningsRecorder,
) -> None:
    class HostileLifecycleText(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=lifecycle-str-secret")

        def strip(self, *_args: Any, **_kwargs: Any) -> str:
            raise AssertionError("client_secret=lifecycle-strip-secret")

    connection = ScriptedPostgresConnection(rows=[])
    store = _store(connection)
    event = LifecycleStateChangeEvent.model_construct(
        event_id=HostileLifecycleText("evt-secret"),
        event_type=LifecycleEventType.STORY_STATE_CHANGED,
        source="servicenow",
        table="rm_story",
        story_number="STRY0010013",
        story_sys_id="secret-story-sys-id",
        previous_state="Draft",
        current_state="Ready",
        occurred_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
        correlation_id="corr-secret",
        emitted_by="jedi-devproject-lifecycle-integration",
    )

    with pytest.raises(ValueError) as exc_info:
        store.record_lifecycle_event(event)

    diagnostic = str(exc_info.value)
    assert diagnostic == "operational lifecycle event payload contains non-JSON values"
    assert exc_info.value.__cause__ is None
    assert "event_id" not in diagnostic
    assert "HostileLifecycleText" not in diagnostic
    assert "lifecycle-" not in diagnostic
    assert "secret-story-sys-id" not in diagnostic
    assert "corr-secret" not in diagnostic
    assert list(recwarn) == []
    assert connection.executed == []
    assert connection.transaction_count == 0


def test_lifecycle_event_payload_rejects_container_subclasses_without_payload_leak() -> (
    None
):
    class HostileLifecycleDict(dict[str, Any]):
        def items(self) -> Any:
            raise AssertionError("client_secret=lifecycle-dict-subclass-secret")

    class HostileLifecycleList(list[Any]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=lifecycle-list-subclass-secret")

    class HostileLifecycleTuple(tuple[Any, ...]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=lifecycle-tuple-subclass-secret")

    for value in (
        HostileLifecycleDict({"story_sys_id": "hidden dict"}),
        HostileLifecycleList(["hidden list"]),
        HostileLifecycleTuple(("hidden tuple",)),
    ):
        with pytest.raises(TypeError) as exc_info:
            _ensure_lifecycle_event_payload_json_safe(value)

        diagnostic = str(exc_info.value)
        assert diagnostic == "non-JSON lifecycle event payload value"
        assert "HostileLifecycle" not in diagnostic
        assert "client_secret" not in diagnostic
        assert "subclass-secret" not in diagnostic
        assert "hidden" not in diagnostic


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


def test_enqueue_fulfillment_job_rejects_row_subclass_without_leak() -> None:
    class HostileJobRow(dict[str, object]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=operational-job-row")

    connection = ScriptedPostgresConnection(rows=[HostileJobRow(_job_row())])
    store = _store(connection)

    with pytest.raises(ValueError) as exc_info:
        store.enqueue_fulfillment_job(
            event_id="evt-job",
            story_number="STRY0010013",
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "operational store read row contains non-JSON value"
    assert "HostileJobRow" not in diagnostic
    assert "operational-job-row" not in diagnostic
    assert "client_secret" not in diagnostic


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


def test_requeue_stale_running_jobs_uses_skip_locked_and_records_audit_event() -> None:
    requeued_row = _job_row(status="queued", attempt_count=2)
    requeued_row["locked_by"] = None
    requeued_row["locked_at"] = None
    connection = ScriptedPostgresConnection(rows=[[requeued_row]])
    store = _store(connection)
    stale_before = datetime(2026, 5, 13, 16, 0, tzinfo=UTC)

    requeued_jobs = store.requeue_stale_running_jobs(
        stale_before=stale_before,
        limit=5,
        message="Stale running job requeued after worker lease timeout",
    )

    joined_sql = "\n".join(sql for sql, _params in connection.executed)
    assert "status = 'running'" in joined_sql
    assert "updated_at < %s" in joined_sql
    assert "ORDER BY updated_at, job_id" in joined_sql
    assert "FOR UPDATE SKIP LOCKED" in joined_sql
    assert "SET status = 'queued'" in joined_sql
    assert "locked_by = NULL" in joined_sql
    assert "locked_at = NULL" in joined_sql
    assert "last_error = NULL" in joined_sql
    assert "INSERT INTO job_events" in joined_sql
    assert "SELECT job_id, 'queued', %s, %s" in joined_sql
    assert connection.executed[0][1][0] == stale_before
    assert connection.executed[0][1][1] == 5
    assert connection.executed[0][1][3] == "Stale running job requeued after worker lease timeout"
    assert connection.transaction_count == 1
    assert len(requeued_jobs) == 1
    assert requeued_jobs[0].status == "queued"
    assert requeued_jobs[0].attempt_count == 2
    assert requeued_jobs[0].locked_by is None
    assert requeued_jobs[0].correlation_id == "corr-evt-job"


def test_requeue_stale_running_jobs_returns_empty_when_no_rows_match() -> None:
    connection = ScriptedPostgresConnection(rows=[[]])
    store = _store(connection)

    requeued_jobs = store.requeue_stale_running_jobs(
        stale_before=datetime(2026, 5, 13, 16, 0, tzinfo=UTC),
        limit=10,
        message="Stale running job requeued after worker lease timeout",
    )

    assert requeued_jobs == []
    assert connection.transaction_count == 1


def test_fulfillment_job_status_summary_uses_postgres_aggregate_counts() -> None:
    stale_before = datetime(2026, 5, 13, 14, 45, tzinfo=UTC)
    connection = ScriptedPostgresConnection(
        rows=[
            {
                "queued": 3,
                "running": 2,
                "completed": 11,
                "failed": 1,
                "rejected": 4,
                "stale_running": 1,
                "total": 21,
            }
        ]
    )
    store = _store(connection)

    summary = store.fulfillment_job_status_summary(stale_before=stale_before)

    assert summary == FulfillmentJobStatusSummaryRecord(
        queued=3,
        running=2,
        completed=11,
        failed=1,
        rejected=4,
        stale_running=1,
        total=21,
    )
    executed_sql, params = connection.executed[0]
    assert "COUNT(*) FILTER (WHERE status = 'queued') AS queued" in executed_sql
    assert "COUNT(*) FILTER (WHERE status = 'running') AS running" in executed_sql
    assert "COUNT(*) FILTER (WHERE status = 'running' AND updated_at < %s)" in (
        executed_sql
    )
    assert params == (stale_before,)


def test_complete_fulfillment_job_marks_completed_and_records_event() -> None:
    connection = ScriptedPostgresConnection(rows=[_job_row(status="completed", attempt_count=1)])
    store = _store(connection)

    completed_job = store.complete_fulfillment_job(
        job_id="job-evt-job",
        worker_id="worker-1",
        message="Fulfillment completed",
    )

    joined_sql = "\n".join(sql for sql, _params in connection.executed)
    assert "UPDATE fulfillment_jobs" in joined_sql
    assert "locked_by = %s" in joined_sql
    assert "status = 'running'" in joined_sql
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
        worker_id="worker-1",
        error_message="provider unavailable",
    )

    joined_sql = "\n".join(sql for sql, _params in connection.executed)
    assert "UPDATE fulfillment_jobs" in joined_sql
    assert "locked_by = %s" in joined_sql
    assert "status = 'running'" in joined_sql
    assert connection.executed[0][1][0] == "failed"
    assert "last_error = %s" in joined_sql
    assert "INSERT INTO job_events" in joined_sql
    assert failed_job.status == "failed"
    assert failed_job.last_error == "provider unavailable"


def test_complete_fulfillment_job_raises_when_not_owned_or_not_running() -> None:
    connection = ScriptedPostgresConnection(rows=[None])
    store = _store(connection)

    with pytest.raises(KeyError, match="not found or not owned"):
        store.complete_fulfillment_job(
            job_id="job-evt-job",
            worker_id="worker-1",
            message="Fulfillment completed",
        )


def test_fail_fulfillment_job_raises_when_not_owned_or_not_running() -> None:
    connection = ScriptedPostgresConnection(rows=[None])
    store = _store(connection)

    with pytest.raises(KeyError, match="not found or not owned"):
        store.fail_fulfillment_job(
            job_id="job-evt-job",
            worker_id="worker-1",
            error_message="provider unavailable",
        )


def test_touch_fulfillment_job_heartbeat_updates_running_job() -> None:
    connection = ScriptedPostgresConnection(rows=[_job_row(status="running", attempt_count=1)])
    store = _store(connection)

    touched = store.touch_fulfillment_job_heartbeat(
        job_id="job-evt-job",
        worker_id="worker-1",
    )

    assert touched is not None
    assert touched.status == "running"
    executed_sql, params = connection.executed[0]
    assert "UPDATE fulfillment_jobs" in executed_sql
    assert "locked_by = %s" in executed_sql
    assert "status = 'running'" in executed_sql
    assert params[2] == "worker-1"


def test_touch_fulfillment_job_heartbeat_returns_none_when_not_owned() -> None:
    connection = ScriptedPostgresConnection(rows=[None])
    store = _store(connection)

    touched = store.touch_fulfillment_job_heartbeat(
        job_id="job-evt-job",
        worker_id="worker-1",
    )

    assert touched is None


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


def test_record_json_artifact_rejects_blob_row_subclass_before_indexing_without_leak() -> (
    None
):
    class HostileArtifactBlobRow(dict[str, object]):
        def __getitem__(self, key: str) -> object:
            raise AssertionError("client_secret=operational-artifact-blob-row")

    connection = ScriptedPostgresConnection(
        rows=[
            HostileArtifactBlobRow(
                {
                    "id": 7,
                    "job_id": "job-evt-job",
                    "story_number": "STRY0010013",
                    "artifact_kind": "implementation_packet",
                    "schema_version": "implementation-packet-v1",
                    "payload_json": {"story": {"number": "STRY0010013"}},
                    "sha256": "b" * 64,
                    "created_at": datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
                }
            )
        ]
    )
    store = _store(connection)

    with pytest.raises(ValueError) as exc_info:
        store.record_json_artifact(
            job_id="job-evt-job",
            story_number="STRY0010013",
            artifact_kind="implementation_packet",
            schema_version="implementation-packet-v1",
            payload={"story": {"number": "STRY0010013"}},
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "operational store read row contains non-JSON value"
    assert "HostileArtifactBlobRow" not in diagnostic
    assert "operational-artifact-blob-row" not in diagnostic
    assert "client_secret" not in diagnostic
    assert connection.transaction_count == 1


def test_record_json_artifact_rejects_blob_id_object_before_int_conversion() -> None:
    class HostileArtifactBlobId:
        def __int__(self) -> int:
            raise AssertionError("client_secret=operational-artifact-blob-id")

    connection = ScriptedPostgresConnection(
        rows=[
            {
                "id": HostileArtifactBlobId(),
                "job_id": "job-evt-job",
                "story_number": "STRY0010013",
                "artifact_kind": "implementation_packet",
                "schema_version": "implementation-packet-v1",
                "payload_json": {"story": {"number": "STRY0010013"}},
                "sha256": "b" * 64,
                "created_at": datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
            }
        ]
    )
    store = _store(connection)

    with pytest.raises(ValueError) as exc_info:
        store.record_json_artifact(
            job_id="job-evt-job",
            story_number="STRY0010013",
            artifact_kind="implementation_packet",
            schema_version="implementation-packet-v1",
            payload={"story": {"number": "STRY0010013"}},
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "operational store read scalar is unsafe"
    assert "HostileArtifactBlobId" not in diagnostic
    assert "operational-artifact-blob-id" not in diagnostic
    assert "client_secret" not in diagnostic
    assert connection.transaction_count == 1


@pytest.mark.parametrize("unsafe_id", [False, 0, -1])
def test_record_json_artifact_rejects_invalid_blob_id_scalars(unsafe_id: object) -> None:
    connection = ScriptedPostgresConnection(
        rows=[
            {
                "id": unsafe_id,
                "job_id": "job-evt-job",
                "story_number": "STRY0010013",
                "artifact_kind": "implementation_packet",
                "schema_version": "implementation-packet-v1",
                "payload_json": {"story": {"number": "STRY0010013"}},
                "sha256": "b" * 64,
                "created_at": datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
            }
        ]
    )
    store = _store(connection)

    with pytest.raises(ValueError) as exc_info:
        store.record_json_artifact(
            job_id="job-evt-job",
            story_number="STRY0010013",
            artifact_kind="implementation_packet",
            schema_version="implementation-packet-v1",
            payload={"story": {"number": "STRY0010013"}},
        )

    assert str(exc_info.value) == "operational store read scalar is unsafe"


def test_record_json_artifact_rejects_non_finite_payload_before_transaction() -> None:
    connection = ScriptedPostgresConnection(rows=[])
    store = _store(connection)

    with pytest.raises(ValueError) as exc_info:
        store.record_json_artifact(
            job_id="job-evt-job",
            story_number="STRY0010013",
            artifact_kind="implementation_packet",
            schema_version="implementation-packet-v1",
            payload={
                "safe_score": 1.0,
                "bad_score": float("nan"),
                "client_secret": "db-artifact-secret",
            },
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "operational artifact JSON payload contains non-finite numeric values"
    assert exc_info.value.__cause__ is None
    assert "bad_score" not in diagnostic
    assert "NaN" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "db-artifact-secret" not in diagnostic
    assert connection.executed == []
    assert connection.transaction_count == 0


def test_record_json_artifact_rejects_non_json_payload_before_transaction() -> None:
    class StringifiesSecret:
        def __str__(self) -> str:
            return "db-artifact-secret"

    connection = ScriptedPostgresConnection(rows=[])
    store = _store(connection)

    with pytest.raises(ValueError) as exc_info:
        store.record_json_artifact(
            job_id="job-evt-job",
            story_number="STRY0010013",
            artifact_kind="implementation_packet",
            schema_version="implementation-packet-v1",
            payload={
                "safe_score": 1.0,
                "unsafe_object": StringifiesSecret(),
                "client_secret": "db-artifact-secret",
            },
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "operational artifact JSON payload contains non-JSON values"
    assert exc_info.value.__cause__ is None
    assert "unsafe_object" not in diagnostic
    assert "StringifiesSecret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "db-artifact-secret" not in diagnostic
    assert connection.executed == []
    assert connection.transaction_count == 0


def test_record_json_artifact_rejects_string_subclass_payload_before_transaction() -> None:
    class HostileArtifactText(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=db-artifact-str-secret")

    connection = ScriptedPostgresConnection(rows=[])
    store = _store(connection)

    with pytest.raises(ValueError) as exc_info:
        store.record_json_artifact(
            job_id="job-evt-job",
            story_number="STRY0010013",
            artifact_kind="implementation_packet",
            schema_version="implementation-packet-v1",
            payload={
                "safe_score": 1.0,
                "unsafe_text": HostileArtifactText("db-artifact-secret"),
                "client_secret": "db-artifact-secret",
            },
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "operational artifact JSON payload contains non-JSON values"
    assert exc_info.value.__cause__ is None
    assert "unsafe_text" not in diagnostic
    assert "HostileArtifactText" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "db-artifact" not in diagnostic
    assert connection.executed == []
    assert connection.transaction_count == 0


def test_operational_artifact_payload_rejects_container_subclasses_without_payload_leak() -> (
    None
):
    class HostileOperationalArtifactDict(dict[str, Any]):
        def items(self) -> Any:
            raise AssertionError("client_secret=operational-dict-subclass-secret")

    class HostileOperationalArtifactList(list[Any]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=operational-list-subclass-secret")

    class HostileOperationalArtifactTuple(tuple[Any, ...]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=operational-tuple-subclass-secret")

    for value in (
        HostileOperationalArtifactDict({"client_secret": "hidden dict"}),
        HostileOperationalArtifactList(["hidden list"]),
        HostileOperationalArtifactTuple(("hidden tuple",)),
    ):
        with pytest.raises(TypeError) as exc_info:
            _ensure_operational_artifact_payload_json_safe(value)

        diagnostic = str(exc_info.value)
        assert diagnostic == "non-JSON operational artifact payload value"
        assert "HostileOperationalArtifact" not in diagnostic
        assert "client_secret" not in diagnostic
        assert "subclass-secret" not in diagnostic
        assert "hidden" not in diagnostic


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


def test_recent_lifecycle_events_rejects_row_collection_subclass_without_leak() -> None:
    class HostileLifecycleRows(list[dict[str, object]]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=operational-lifecycle-rows")

    row = {
        "event_id": "evt-002",
        "event_type": "story_state_changed",
        "story_number": "STRY0010002",
        "payload_json": {"story_number": "STRY0010002"},
        "received_at": datetime(2026, 5, 14, 18, 0, tzinfo=UTC),
        "validation_status": "accepted",
    }
    connection = ScriptedPostgresConnection(rows=[HostileLifecycleRows([row])])
    store = _store(connection)

    with pytest.raises(ValueError) as exc_info:
        store.recent_lifecycle_events(limit=10)

    diagnostic = str(exc_info.value)
    assert diagnostic == "operational store read rows contain non-JSON value"
    assert "HostileLifecycleRows" not in diagnostic
    assert "operational-lifecycle-rows" not in diagnostic
    assert "client_secret" not in diagnostic


def test_recent_lifecycle_events_rejects_row_subclass_without_leak() -> None:
    class HostileLifecycleRow(dict[str, object]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=operational-lifecycle-row")

    row = HostileLifecycleRow(
        {
            "event_id": "evt-002",
            "event_type": "story_state_changed",
            "story_number": "STRY0010002",
            "payload_json": {"story_number": "STRY0010002"},
            "received_at": datetime(2026, 5, 14, 18, 0, tzinfo=UTC),
            "validation_status": "accepted",
        }
    )
    connection = ScriptedPostgresConnection(rows=[[row]])
    store = _store(connection)

    with pytest.raises(ValueError) as exc_info:
        store.recent_lifecycle_events(limit=10)

    diagnostic = str(exc_info.value)
    assert diagnostic == "operational store read rows contain non-JSON value"
    assert "HostileLifecycleRow" not in diagnostic
    assert "operational-lifecycle-row" not in diagnostic
    assert "client_secret" not in diagnostic


def test_verify_schema_ready_checks_required_operational_tables() -> None:
    rows: list[ScriptedRow] = [
        {"table_name": "artifact_blobs"},
        {"table_name": "artifact_refs"},
        {"table_name": "fulfillment_jobs"},
        {"table_name": "job_events"},
        {"table_name": "lifecycle_events"},
        {"table_name": "retention_prune_audit"},
    ]
    connection = ScriptedPostgresConnection(rows=[rows])
    store = _store(connection)

    assert store.verify_schema_ready() is True

    sql, params = connection.executed[0]
    assert "information_schema.tables" in sql
    assert "table_schema = 'public'" in sql
    assert params == (
        [
            "artifact_blobs",
            "artifact_refs",
            "fulfillment_jobs",
            "job_events",
            "lifecycle_events",
            "retention_prune_audit",
        ],
    )


def test_verify_schema_ready_returns_false_when_required_table_is_missing() -> None:
    rows: list[ScriptedRow] = [
        {"table_name": "artifact_blobs"},
        {"table_name": "artifact_refs"},
        {"table_name": "fulfillment_jobs"},
        {"table_name": "job_events"},
        {"table_name": "lifecycle_events"},
    ]
    connection = ScriptedPostgresConnection(rows=[rows])
    store = _store(connection)

    assert store.verify_schema_ready() is False


def test_verify_schema_ready_rejects_schema_row_subclass_without_leak() -> None:
    class HostileSchemaRow(dict[str, object]):
        def get(self, key: str, default: object = None) -> object:
            raise AssertionError("client_secret=schema-readiness-row")

    rows: list[ScriptedRow] = [
        HostileSchemaRow({"table_name": "artifact_blobs"}),
    ]
    connection = ScriptedPostgresConnection(rows=[rows])
    store = _store(connection)

    with pytest.raises(ValueError) as exc_info:
        store.verify_schema_ready()

    diagnostic = str(exc_info.value)
    assert diagnostic == "operational store schema readiness row contains non-JSON value"
    assert "HostileSchemaRow" not in diagnostic
    assert "schema-readiness-row" not in diagnostic
    assert "client_secret" not in diagnostic


def test_surface_maturity_evidence_rejects_row_subclass_without_leak() -> None:
    class HostileMaturityRow(dict[str, object]):
        def __getitem__(self, key: str) -> object:
            raise AssertionError("client_secret=surface-maturity-row")

    connection = ScriptedPostgresConnection(
        rows=[HostileMaturityRow({"samples": 1, "successes": 1, "failures": 0})]
    )
    store = _store(connection)

    with pytest.raises(ValueError) as exc_info:
        store.builder_maturity_evidence_for_surface("business_rules")

    diagnostic = str(exc_info.value)
    assert diagnostic == "operational store surface maturity row contains non-JSON value"
    assert "HostileMaturityRow" not in diagnostic
    assert "surface-maturity-row" not in diagnostic
    assert "client_secret" not in diagnostic


def test_surface_maturity_evidence_rejects_count_object_without_leak() -> None:
    class HostileMaturityCount:
        def __int__(self) -> int:
            raise AssertionError("client_secret=surface-maturity-count")

    connection = ScriptedPostgresConnection(
        rows=[
            {
                "samples": HostileMaturityCount(),
                "successes": 1,
                "failures": 0,
            }
        ]
    )
    store = _store(connection)

    with pytest.raises(ValueError) as exc_info:
        store.builder_maturity_evidence_for_surface("business_rules")

    diagnostic = str(exc_info.value)
    assert diagnostic == "operational store surface maturity row contains non-JSON value"
    assert "HostileMaturityCount" not in diagnostic
    assert "surface-maturity-count" not in diagnostic
    assert "client_secret" not in diagnostic


def test_surface_maturity_evidence_record_rejects_surface_string_subclass_without_leak() -> (
    None
):
    class HostileSurfaceText(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=surface-maturity-record")

    with pytest.raises(ValidationError) as exc_info:
        SurfaceMaturityEvidenceRecord.model_validate(
            {
                "surface": HostileSurfaceText("form_sections"),
                "samples": 1,
                "successes": 1,
                "failures": 0,
            }
        )

    diagnostic = str(exc_info.value)
    assert "operational store surface maturity record scalar is unsafe" in diagnostic
    assert "HostileSurfaceText" not in diagnostic
    assert "surface-maturity-record" not in diagnostic
    assert "client_secret" not in diagnostic


@pytest.mark.parametrize("unsafe_count", [False, -1])
def test_surface_maturity_evidence_record_rejects_invalid_count_scalars(
    unsafe_count: object,
) -> None:
    with pytest.raises(ValidationError) as exc_info:
        SurfaceMaturityEvidenceRecord.model_validate(
            {
                "surface": "form_sections",
                "samples": unsafe_count,
                "successes": 0,
                "failures": 0,
            }
        )

    assert "operational store surface maturity record scalar is unsafe" in str(
        exc_info.value
    )


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
            "JEDI_RETENTION_ARTIFACT_BLOB_DAYS": "",
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


def test_load_retention_policy_rejects_padded_numeric_values() -> None:
    retention_settings = {
        "JEDI_RETENTION_ARTIFACT_BLOB_DAYS": " 90",
        "JEDI_RETENTION_JOB_EVENT_DAYS": "365 ",
        "JEDI_RETENTION_PRUNE_BATCH_SIZE": "500\tfallback",
    }
    for setting_name, setting_value in retention_settings.items():
        try:
            load_retention_policy({setting_name: setting_value})
        except ValueError as exc:
            message = str(exc)
            assert setting_name in message
            assert "integer without padding or control characters" in message
            assert "fallback" not in message
            assert "\t" not in message
        else:
            raise AssertionError(f"padded {setting_name} did not raise")


def test_load_retention_policy_rejects_non_decimal_integer_values() -> None:
    retention_settings = {
        "JEDI_RETENTION_ARTIFACT_BLOB_DAYS": "+90",
        "JEDI_RETENTION_JOB_EVENT_DAYS": "365_000",
        "JEDI_RETENTION_PRUNE_BATCH_SIZE": "+500",
    }
    for setting_name, setting_value in retention_settings.items():
        try:
            load_retention_policy({setting_name: setting_value})
        except ValueError as exc:
            message = str(exc)
            assert setting_name in message
            assert "base-10 digits only" in message
            assert setting_value not in message
        else:
            raise AssertionError(f"non-decimal {setting_name} did not raise")


def test_retention_prune_result_rejects_record_class_string_subclass_without_leak() -> (
    None
):
    class HostileRetentionText(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=retention-record-class")

    with pytest.raises(ValidationError) as exc_info:
        RetentionClassPruneResult.model_validate(
            {
                "record_class": HostileRetentionText("artifact_blobs"),
                "cutoff": datetime(2026, 6, 11, 12, 0, tzinfo=UTC),
                "deleted_count": 1,
                "batches": 1,
            }
        )

    diagnostic = str(exc_info.value)
    assert "operational store retention report scalar is unsafe" in diagnostic
    assert "HostileRetentionText" not in diagnostic
    assert "retention-record-class" not in diagnostic
    assert "client_secret" not in diagnostic


@pytest.mark.parametrize("unsafe_count", [False, -1])
def test_retention_prune_result_rejects_invalid_count_scalars(
    unsafe_count: object,
) -> None:
    with pytest.raises(ValidationError) as exc_info:
        RetentionClassPruneResult.model_validate(
            {
                "record_class": "artifact_blobs",
                "cutoff": datetime(2026, 6, 11, 12, 0, tzinfo=UTC),
                "deleted_count": unsafe_count,
                "batches": 1,
            }
        )

    assert "operational store retention report scalar is unsafe" in str(exc_info.value)


def test_retention_prune_report_rejects_results_collection_subclass_without_leak() -> (
    None
):
    class HostileRetentionResults(list[RetentionClassPruneResult]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=retention-results")

    result = RetentionClassPruneResult(
        record_class="artifact_blobs",
        cutoff=datetime(2026, 6, 11, 12, 0, tzinfo=UTC),
        deleted_count=1,
        batches=1,
    )

    with pytest.raises(ValidationError) as exc_info:
        RetentionPruneReport.model_validate(
            {
                "enabled": True,
                "pruned_at": datetime(2026, 6, 11, 12, 30, tzinfo=UTC),
                "prune_batch_size": 500,
                "results": HostileRetentionResults([result]),
            }
        )

    diagnostic = str(exc_info.value)
    assert "operational store retention report results are unsafe" in diagnostic
    assert "HostileRetentionResults" not in diagnostic
    assert "retention-results" not in diagnostic
    assert "client_secret" not in diagnostic


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


def test_prune_expired_records_rejects_count_object_without_leak() -> None:
    class HostileDeletedCount:
        def __int__(self) -> int:
            raise AssertionError("client_secret=operational-deleted-count")

    connection = ScriptedPostgresConnection(rows=[{"deleted_count": HostileDeletedCount()}])
    store = _store(connection)
    policy = RetentionPolicy(artifact_blob_retention_days=90)

    with pytest.raises(ValueError) as exc_info:
        store.prune_expired_records(policy=policy)

    diagnostic = str(exc_info.value)
    assert diagnostic == "operational store read scalar is unsafe"
    assert "HostileDeletedCount" not in diagnostic
    assert "operational-deleted-count" not in diagnostic
    assert "client_secret" not in diagnostic


@pytest.mark.parametrize("unsafe_count", [False, -1])
def test_prune_expired_records_rejects_invalid_deleted_count_scalars(
    unsafe_count: object,
) -> None:
    connection = ScriptedPostgresConnection(rows=[{"deleted_count": unsafe_count}])
    store = _store(connection)
    policy = RetentionPolicy(artifact_blob_retention_days=90)

    with pytest.raises(ValueError) as exc_info:
        store.prune_expired_records(policy=policy)

    assert str(exc_info.value) == "operational store read scalar is unsafe"


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
