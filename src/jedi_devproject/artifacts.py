from __future__ import annotations

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
    payload: dict[str, Any],
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / filename
    if path.exists():
        raise ArtifactWriteError(f"json artifact already exists: {path}")
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path
