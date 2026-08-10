import json
from pathlib import Path, PosixPath

import pytest

from jedi_devproject.artifacts import (
    ArtifactReadError,
    ArtifactWriteError,
    artifact_sha256_file,
    read_regular_artifact_bytes,
    write_delivery_attachment_audit,
    write_json_artifact_once,
    write_lifecycle_manifest,
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
    with pytest.raises(ArtifactWriteError) as exc_info:
        write_json_artifact_once(
            tmp_path,
            filename="batch-run.json",
            payload={"summary": {"applied": 1}},
        )
    assert exc_info.value.__cause__ is None


def test_write_json_artifact_once_rejects_non_finite_payload_without_file_or_leak(
    tmp_path: Path,
) -> None:
    artifact_root = tmp_path / "artifacts"

    with pytest.raises(ArtifactWriteError) as exc_info:
        write_json_artifact_once(
            artifact_root,
            filename="batch-run.json",
            payload={
                "safe_score": 1.0,
                "bad_score": float("nan"),
                "client_secret": "artifact-secret",
            },
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "artifact JSON payload contains non-finite numeric values"
    assert exc_info.value.__cause__ is None
    assert "bad_score" not in diagnostic
    assert "NaN" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "artifact-secret" not in diagnostic
    assert not (artifact_root / "batch-run.json").exists()


def test_write_json_artifact_once_rejects_broken_symlink_escape(
    tmp_path: Path,
) -> None:
    artifacts_root = tmp_path / "artifacts"
    artifacts_root.mkdir()
    outside_path = tmp_path / "escape.json"
    artifact_link = artifacts_root / "batch-run.json"
    artifact_link.symlink_to(outside_path)

    with pytest.raises(ArtifactWriteError):
        write_json_artifact_once(
            artifacts_root,
            filename="batch-run.json",
            payload={"escaped": True},
        )

    assert artifact_link.is_symlink()
    assert not outside_path.exists()


def test_write_json_artifact_once_rejects_path_traversal_filename(
    tmp_path: Path,
) -> None:
    outside_path = tmp_path / "escape.json"

    with pytest.raises(ArtifactWriteError, match="unsafe artifact filename"):
        write_json_artifact_once(
            tmp_path / "artifacts",
            filename="../escape.json",
            payload={"escaped": True},
        )

    assert not outside_path.exists()


def test_lifecycle_manifest_rejects_path_traversal_run_id(tmp_path: Path) -> None:
    packet_path = tmp_path / "packets" / "STRY0010013.json"
    candidate_path = tmp_path / "candidates" / "STRY0010013.json"
    for path, payload in [
        (packet_path, {"story": {"number": "STRY0010013"}, "task": "generate"}),
        (candidate_path, {"story_number": "STRY0010013", "artifact_hash": "abc"}),
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ArtifactWriteError, match="unsafe artifact filename"):
        write_lifecycle_manifest(
            tmp_path / "manifests",
            run_id="../escape",
            story_number="STRY0010013",
            build_reference="build-20260513-001",
            packet_path=packet_path,
            candidate_path=candidate_path,
            writeback_audit_path=None,
            verification={"verified": True},
        )

    assert not (tmp_path / "escape.json").exists()


def test_write_lifecycle_manifest_ties_phase_artifacts_without_sys_ids(
    tmp_path: Path,
) -> None:
    packet_path = tmp_path / "packets" / "STRY0010013.json"
    candidate_path = tmp_path / "candidates" / "STRY0010013.json"
    writeback_audit_path = tmp_path / "writeback" / "STRY0010013-build.json"
    for path, payload in [
        (packet_path, {"story": {"number": "STRY0010013"}, "task": "generate"}),
        (candidate_path, {"story_number": "STRY0010013", "artifact_hash": "abc"}),
        (writeback_audit_path, {"story_number": "STRY0010013", "applied": True}),
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    manifest_path = write_lifecycle_manifest(
        tmp_path / "manifests",
        run_id="lifecycle-001",
        story_number="STRY0010013",
        build_reference="build-20260513-001",
        packet_path=packet_path,
        candidate_path=candidate_path,
        writeback_audit_path=writeback_audit_path,
        verification={
            "verified": True,
            "expected_state": "-7",
            "actual_fields": {"state": "-7"},
            "reasons": [],
        },
    )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_path.name == "lifecycle-001.json"
    assert payload["run_id"] == "lifecycle-001"
    assert payload["story_number"] == "STRY0010013"
    assert payload["build_reference"] == "build-20260513-001"
    assert payload["artifacts"]["implementation_packet"]["path"] == str(packet_path)
    assert payload["artifacts"]["implementation_packet"]["sha256"]
    assert payload["artifacts"]["implementation_candidate"]["path"] == str(candidate_path)
    assert payload["artifacts"]["writeback_audit"]["path"] == str(writeback_audit_path)
    assert payload["verification"]["verified"] is True
    assert "sys_id" not in json.dumps(payload)

    with pytest.raises(ArtifactWriteError):
        write_lifecycle_manifest(
            tmp_path / "manifests",
            run_id="lifecycle-001",
            story_number="STRY0010013",
            build_reference="build-20260513-001",
            packet_path=packet_path,
            candidate_path=candidate_path,
            writeback_audit_path=writeback_audit_path,
            verification={"verified": True},
        )


def test_lifecycle_manifest_rejects_path_subclass_without_leak(tmp_path: Path) -> None:
    class SecretBearingPath(PosixPath):
        def __str__(self) -> str:
            return "api_key=path-subclass-secret"

    packet_path = SecretBearingPath(tmp_path / "packets" / "STRY0010013.json")
    candidate_path = tmp_path / "candidates" / "STRY0010013.json"
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(
        json.dumps({"story_number": "STRY0010013", "artifact_hash": "abc"}),
        encoding="utf-8",
    )

    with pytest.raises(ArtifactWriteError) as exc_info:
        write_lifecycle_manifest(
            tmp_path / "manifests",
            run_id="lifecycle-002",
            story_number="STRY0010013",
            build_reference="build-20260513-001",
            packet_path=packet_path,
            candidate_path=candidate_path,
            writeback_audit_path=None,
            verification={"verified": True},
        )

    message = str(exc_info.value)
    assert message == "artifact path must be a concrete pathlib Path"
    assert "SecretBearingPath" not in message
    assert "path-subclass-secret" not in message
    assert "api_key" not in message
    assert not (tmp_path / "manifests" / "lifecycle-002.json").exists()


def test_lifecycle_manifest_hashes_artifacts_without_whole_file_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    packet_path = tmp_path / "packets" / "STRY0010013.json"
    candidate_path = tmp_path / "candidates" / "STRY0010013.json"
    writeback_audit_path = tmp_path / "writeback" / "STRY0010013-build.json"
    for path, payload in [
        (packet_path, {"story": {"number": "STRY0010013"}, "task": "generate"}),
        (candidate_path, {"story_number": "STRY0010013", "artifact_hash": "abc"}),
        (writeback_audit_path, {"story_number": "STRY0010013", "applied": True}),
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def fail_read_bytes(self: Path) -> bytes:
        raise AssertionError(f"unexpected whole-file read for {self}")

    monkeypatch.setattr(Path, "read_bytes", fail_read_bytes)

    manifest_path = write_lifecycle_manifest(
        tmp_path / "manifests",
        run_id="lifecycle-001",
        story_number="STRY0010013",
        build_reference="build-20260513-001",
        packet_path=packet_path,
        candidate_path=candidate_path,
        writeback_audit_path=writeback_audit_path,
        verification={"verified": True},
    )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(payload["artifacts"]["implementation_packet"]["sha256"]) == 64
    assert len(payload["artifacts"]["implementation_candidate"]["sha256"]) == 64
    assert len(payload["artifacts"]["writeback_audit"]["sha256"]) == 64


def test_artifact_sha256_file_rejects_symlinked_artifact(tmp_path: Path) -> None:
    target_path = tmp_path / "target.json"
    target_path.write_text('{"artifact": true}', encoding="utf-8")
    artifact_link = tmp_path / "artifact.json"
    artifact_link.symlink_to(target_path)

    with pytest.raises(
        ArtifactReadError,
        match="artifact path must be a regular file",
    ) as exc_info:
        artifact_sha256_file(artifact_link)
    assert exc_info.value.__cause__ is None


def test_read_regular_artifact_bytes_marks_oversized_read_errors(
    tmp_path: Path,
) -> None:
    artifact_path = tmp_path / "oversized.xml"
    artifact_path.write_bytes(b"xx")

    with pytest.raises(ArtifactReadError) as exc_info:
        read_regular_artifact_bytes(artifact_path, max_bytes=1)

    assert exc_info.value.reason == "too_large"
    assert exc_info.value.max_bytes == 1


def test_delivery_attachment_audit_is_write_once_without_story_sys_id(
    tmp_path: Path,
) -> None:
    path = write_delivery_attachment_audit(
        tmp_path,
        run_id="attach-001",
        story_number="STRY0010013",
        actor_id="svc-jedi-orchestrator",
        report_path=Path("artifacts/handoff.json"),
        attachments=[
            {
                "artifact_kind": "update_set_xml",
                "artifact_path": "artifacts/export.xml",
                "attachment_label": "Approved Update Set XML",
                "attachment_sys_id": "attachment-sys-id",
            }
        ],
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert path.name == "attach-001.json"
    assert payload["story_number"] == "STRY0010013"
    assert payload["actor_id"] == "svc-jedi-orchestrator"
    assert payload["report_path"] == "artifacts/handoff.json"
    assert payload["attachments"][0]["attachment_sys_id"] == "attachment-sys-id"
    assert "story_sys_id" not in json.dumps(payload)

    with pytest.raises(ArtifactWriteError):
        write_delivery_attachment_audit(
            tmp_path,
            run_id="attach-001",
            story_number="STRY0010013",
            actor_id="svc-jedi-orchestrator",
            report_path=Path("artifacts/handoff.json"),
            attachments=[],
        )


def test_delivery_attachment_audit_rejects_path_subclass_without_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingPath(PosixPath):
        def __str__(self) -> str:
            return "client_secret=path-subclass-secret"

    report_path = SecretBearingPath("artifacts/handoff.json")

    with pytest.raises(ArtifactWriteError) as exc_info:
        write_delivery_attachment_audit(
            tmp_path,
            run_id="attach-002",
            story_number="STRY0010013",
            actor_id="svc-jedi-orchestrator",
            report_path=report_path,
            attachments=[],
        )

    message = str(exc_info.value)
    assert message == "artifact path must be a concrete pathlib Path"
    assert "SecretBearingPath" not in message
    assert "path-subclass-secret" not in message
    assert "client_secret" not in message
    assert not (tmp_path / "attach-002.json").exists()
