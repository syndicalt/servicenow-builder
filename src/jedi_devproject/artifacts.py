from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jedi_devproject.models import UpdateSetCandidate
from jedi_devproject.writeback import WritebackAuditEvent


class ArtifactWriteError(RuntimeError):
    """Raised when an artifact write would violate audit safety."""


def write_candidate_artifact(
    root: Path,
    *,
    run_id: str,
    candidate: UpdateSetCandidate,
) -> Path:
    run_dir = root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / f"{candidate.story_number}.json"

    if path.exists():
        raise ArtifactWriteError(f"candidate artifact already exists: {path}")

    path.write_text(candidate.model_dump_json(indent=2), encoding="utf-8")
    return path


def write_writeback_audit_artifact(root: Path, *, event: WritebackAuditEvent) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = writeback_audit_artifact_path(root, event=event)

    if path.exists():
        raise ArtifactWriteError(f"writeback audit artifact already exists: {path}")

    path.write_text(event.model_dump_json(indent=2), encoding="utf-8")
    return path


def writeback_audit_artifact_path(root: Path, *, event: WritebackAuditEvent) -> Path:
    safe_build_reference = event.build_reference.replace("/", "_").replace("\\", "_")
    return root / f"{event.story_number}-{safe_build_reference}.json"


def write_json_artifact_once(
    root: Path,
    *,
    filename: str,
    payload: Any,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / filename
    if path.exists():
        raise ArtifactWriteError(f"json artifact already exists: {path}")
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_lifecycle_manifest(
    root: Path,
    *,
    run_id: str,
    story_number: str,
    build_reference: str,
    packet_path: Path,
    candidate_path: Path,
    candidate_batch_path: Path | None = None,
    writeback_audit_path: Path | None,
    verification: dict[str, Any],
    writeback: dict[str, Any] | None = None,
) -> Path:
    artifacts: dict[str, dict[str, str]] = {
        "implementation_packet": _artifact_reference(packet_path),
        "implementation_candidate": _artifact_reference(candidate_path),
    }
    if candidate_batch_path is not None:
        artifacts["implementation_candidate_batch"] = _artifact_reference(
            candidate_batch_path
        )
    if writeback_audit_path is not None:
        artifacts["writeback_audit"] = _artifact_reference(writeback_audit_path)

    return write_json_artifact_once(
        root,
        filename=f"{run_id}.json",
        payload={
            "run_id": run_id,
            "story_number": story_number,
            "build_reference": build_reference,
            "artifacts": artifacts,
            "writeback": writeback or {},
            "verification": verification,
        },
    )


def write_delivery_attachment_audit(
    root: Path,
    *,
    run_id: str,
    story_number: str,
    actor_id: str,
    report_path: Path,
    attachments: list[dict[str, Any]],
) -> Path:
    return write_json_artifact_once(
        root,
        filename=f"{run_id}.json",
        payload={
            "run_id": run_id,
            "story_number": story_number,
            "actor_id": actor_id,
            "report_path": str(report_path),
            "attachments": attachments,
        },
    )


def write_reviewed_delivery_lifecycle_manifest(
    root: Path,
    *,
    run_id: str,
    story_number: str,
    delivery_artifact_path: Path,
    reviewed_delivery_job_path: Path,
    artifact_handoff_report_path: Path,
    delivery_attachment_plan: dict[str, Any],
) -> Path:
    return write_json_artifact_once(
        root,
        filename=f"{run_id}.json",
        payload={
            "run_id": run_id,
            "story_number": story_number,
            "artifacts": {
                "delivery_artifact": _artifact_reference(delivery_artifact_path),
                "reviewed_delivery_job": _artifact_reference(
                    reviewed_delivery_job_path
                ),
                "artifact_handoff_report": _artifact_reference(
                    artifact_handoff_report_path
                ),
            },
            "delivery_attachment_plan": delivery_attachment_plan,
        },
    )


def _artifact_reference(path: Path) -> dict[str, str]:
    return {
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
