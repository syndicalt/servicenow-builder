from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from jedi_devproject.lifecycle_events import (
    LifecycleEventType,
    LifecycleStateChangeEvent,
)
from jedi_devproject.operational_store import connect_operational_store


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


def test_operational_store_initializes_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "runtime" / "operational.sqlite3"

    with connect_operational_store(db_path) as store:
        table_names = store.table_names()

    assert table_names >= {
        "lifecycle_events",
        "fulfillment_jobs",
        "job_events",
        "artifact_refs",
    }


def test_record_lifecycle_event_is_idempotent_and_preserves_original_payload(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "operational.sqlite3"

    with connect_operational_store(db_path) as store:
        first_record = store.record_lifecycle_event(
            _lifecycle_event(event_id="evt-dup", story_number="STRY0010013")
        )
        duplicate_record = store.record_lifecycle_event(
            _lifecycle_event(event_id="evt-dup", story_number="STRY9999999")
        )

    assert duplicate_record == first_record
    assert duplicate_record.story_number == "STRY0010013"
    assert "STRY9999999" not in duplicate_record.payload_json


def test_enqueue_fulfillment_job_is_idempotent_and_records_job_event(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "operational.sqlite3"

    with connect_operational_store(db_path) as store:
        event = store.record_lifecycle_event(_lifecycle_event(event_id="evt-job"))

        first_job = store.enqueue_fulfillment_job(
            event_id=event.event_id,
            story_number=event.story_number,
        )
        duplicate_job = store.enqueue_fulfillment_job(
            event_id=event.event_id,
            story_number=event.story_number,
        )
        job_events = store.job_events_for_job(first_job.job_id)

    assert duplicate_job == first_job
    assert first_job.job_id == "job-evt-job"
    assert first_job.status == "queued"
    assert first_job.attempt_count == 0
    assert [job_event.status for job_event in job_events] == ["queued"]


def test_claim_next_fulfillment_job_marks_running_with_worker_lock(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "operational.sqlite3"

    with connect_operational_store(db_path) as store:
        event = store.record_lifecycle_event(_lifecycle_event(event_id="evt-claim"))
        store.enqueue_fulfillment_job(
            event_id=event.event_id,
            story_number=event.story_number,
        )

        claimed_job = store.claim_next_fulfillment_job(worker_id="worker-local-1")
        no_second_claim = store.claim_next_fulfillment_job(worker_id="worker-local-2")
        job_events = store.job_events_for_job("job-evt-claim")

    assert claimed_job is not None
    assert claimed_job.status == "running"
    assert claimed_job.attempt_count == 1
    assert claimed_job.locked_by == "worker-local-1"
    assert claimed_job.locked_at is not None
    assert no_second_claim is None
    assert [job_event.status for job_event in job_events] == ["queued", "running"]


def test_record_artifact_ref_requires_existing_job(tmp_path: Path) -> None:
    db_path = tmp_path / "operational.sqlite3"

    with connect_operational_store(db_path) as store:
        event = store.record_lifecycle_event(_lifecycle_event(event_id="evt-artifact"))
        job = store.enqueue_fulfillment_job(
            event_id=event.event_id,
            story_number=event.story_number,
        )
        artifact_ref = store.record_artifact_ref(
            job_id=job.job_id,
            artifact_kind="implementation_packet",
            path="artifacts/implementation-packets/packet.json",
            sha256="a" * 64,
        )
        artifact_refs = store.artifact_refs_for_job(job.job_id)

        with pytest.raises(sqlite3.IntegrityError):
            store.record_artifact_ref(
                job_id="missing-job",
                artifact_kind="implementation_packet",
                path="artifacts/missing.json",
                sha256="b" * 64,
            )

    assert artifact_ref.job_id == job.job_id
    assert artifact_ref.artifact_kind == "implementation_packet"
    assert [record.path for record in artifact_refs] == [
        "artifacts/implementation-packets/packet.json"
    ]
