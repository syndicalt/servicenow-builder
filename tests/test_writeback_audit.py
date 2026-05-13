import json
from pathlib import Path

import pytest

from jedi_devproject.artifacts import (
    ArtifactWriteError,
    write_json_artifact_once,
    write_writeback_audit_artifact,
)
from jedi_devproject.writeback import ActorType, WritebackAuditEvent


def _event() -> WritebackAuditEvent:
    return WritebackAuditEvent(
        story_number="STRY0010013",
        build_reference="build-20260513-001",
        actor_type=ActorType.SERVICE,
        actor_id="svc-jedi-orchestrator",
        run_id="run-20260513-001",
        apply_requested=True,
        applied=True,
        allowed=True,
        fields={"state": "-7", "u_ai_status": "Ready for Testing"},
        reasons=[],
    )


def test_writeback_audit_event_excludes_story_sys_id() -> None:
    event = _event()

    payload = event.model_dump()

    assert "story_sys_id" not in payload
    assert payload["story_number"] == "STRY0010013"
    assert payload["actor_type"] == "service"
    assert payload["actor_id"] == "svc-jedi-orchestrator"
    assert payload["run_id"] == "run-20260513-001"


def test_writeback_audit_artifact_is_write_once(tmp_path: Path) -> None:
    event = _event()

    path = write_writeback_audit_artifact(tmp_path, event=event)

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert path.name == "STRY0010013-build-20260513-001.json"
    assert payload["story_number"] == "STRY0010013"
    assert payload["applied"] is True

    with pytest.raises(ArtifactWriteError):
        write_writeback_audit_artifact(tmp_path, event=event)


def test_write_json_artifact_once_rejects_existing_file(tmp_path: Path) -> None:
    path = write_json_artifact_once(
        tmp_path,
        filename="batch-run.json",
        payload={"summary": {"applied": 1}},
    )

    assert path.name == "batch-run.json"
    with pytest.raises(ArtifactWriteError):
        write_json_artifact_once(
            tmp_path,
            filename="batch-run.json",
            payload={"summary": {"applied": 1}},
        )
