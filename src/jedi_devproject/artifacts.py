from __future__ import annotations

import errno
import hashlib
import json
import math
import os
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any, BinaryIO, Literal

from pydantic import BaseModel
from pydantic_core import PydanticSerializationError

from jedi_devproject.models import UpdateSetCandidate
from jedi_devproject.writeback import BuildClaimAuditEvent, WritebackAuditEvent

ARTIFACT_HASH_CHUNK_BYTES = 1024 * 1024
ARTIFACT_DTO_NON_FINITE_DIAGNOSTIC = (
    "artifact DTO payload contains non-finite numeric values"
)
ARTIFACT_DTO_NON_JSON_DIAGNOSTIC = "artifact DTO payload contains non-JSON values"
_CONCRETE_PATH_TYPE = type(Path())


class ArtifactWriteError(RuntimeError):
    """Raised when an artifact write would violate audit safety."""


ArtifactReadErrorReason = Literal["not_regular", "read_failed", "too_large"]


class ArtifactReadError(RuntimeError):
    """Raised when artifact evidence cannot be read safely."""

    def __init__(
        self,
        message: str,
        *,
        reason: ArtifactReadErrorReason = "read_failed",
        max_bytes: int | None = None,
    ) -> None:
        super().__init__(message)
        self.reason = reason
        self.max_bytes = max_bytes


def write_candidate_artifact(
    root: Path,
    *,
    run_id: str,
    candidate: UpdateSetCandidate,
) -> Path:
    run_dir = root / _safe_artifact_path_component(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / _safe_artifact_filename(f"{candidate.story_number}.json")

    write_text_artifact_once(path, _artifact_model_json(candidate))
    return path


def write_writeback_audit_artifact(root: Path, *, event: WritebackAuditEvent) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = writeback_audit_artifact_path(root, event=event)

    write_text_artifact_once(path, _artifact_model_json(event))
    return path


def writeback_audit_artifact_path(root: Path, *, event: WritebackAuditEvent) -> Path:
    safe_story_number = _safe_artifact_path_component(event.story_number)
    safe_build_reference = _safe_artifact_path_component(
        event.build_reference.replace("/", "_").replace("\\", "_")
    )
    return root / f"{safe_story_number}-{safe_build_reference}.json"


def write_build_claim_audit_artifact(
    root: Path,
    *,
    event: BuildClaimAuditEvent,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = build_claim_audit_artifact_path(root, event=event)

    write_text_artifact_once(path, _artifact_model_json(event))
    return path


def build_claim_audit_artifact_path(
    root: Path,
    *,
    event: BuildClaimAuditEvent,
) -> Path:
    safe_story_number = _safe_artifact_path_component(event.story_number)
    safe_event_id = _safe_artifact_path_component(
        event.lifecycle_event_id.replace("/", "_").replace("\\", "_")
    )
    return root / f"{safe_story_number}-{safe_event_id}-claim.json"


def write_json_artifact_once(
    root: Path,
    *,
    filename: str,
    payload: Any,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / _safe_artifact_filename(filename)
    try:
        content = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False)
    except ValueError:
        raise ArtifactWriteError(
            "artifact JSON payload contains non-finite numeric values"
        ) from None
    write_text_artifact_once(path, content)
    return path


def _artifact_model_json(model: BaseModel) -> str:
    try:
        _ensure_artifact_dto_payload_json_safe(
            model.model_dump(mode="python", warnings=False)
        )
        json.dumps(
            model.model_dump(mode="json", warnings=False),
            sort_keys=True,
            allow_nan=False,
        )
    except PydanticSerializationError:
        raise ArtifactWriteError(ARTIFACT_DTO_NON_JSON_DIAGNOSTIC) from None
    except ValueError:
        raise ArtifactWriteError(ARTIFACT_DTO_NON_FINITE_DIAGNOSTIC) from None
    except TypeError:
        raise ArtifactWriteError(ARTIFACT_DTO_NON_JSON_DIAGNOSTIC) from None
    return model.model_dump_json(indent=2, warnings=False)


def _ensure_artifact_dto_payload_json_safe(value: Any) -> None:
    if (
        value is None
        or type(value) is str
        or type(value) is bool
        or type(value) is int
        or type(value) is date
        or isinstance(value, Enum)
    ):
        return
    if type(value) is float:
        if math.isfinite(value):
            return
        raise ValueError("non-finite artifact DTO payload value")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("non-JSON artifact DTO payload key")
            _ensure_artifact_dto_payload_json_safe(item)
        return
    if type(value) is list:
        for item in value:
            _ensure_artifact_dto_payload_json_safe(item)
        return
    if type(value) is tuple:
        for item in value:
            _ensure_artifact_dto_payload_json_safe(item)
        return
    raise TypeError("non-JSON artifact DTO payload value")


def write_text_artifact_once(path: Path, content: str) -> None:
    try:
        with path.open("x", encoding="utf-8") as artifact:
            artifact.write(content)
    except FileExistsError:
        raise ArtifactWriteError(f"artifact already exists: {path}") from None


def _safe_artifact_path_component(value: str) -> str:
    if not _is_safe_artifact_path_component(value):
        raise ArtifactWriteError("unsafe artifact path component")
    return value


def _safe_artifact_filename(filename: str) -> str:
    if not _is_safe_artifact_path_component(filename):
        raise ArtifactWriteError("unsafe artifact filename")
    return filename


def _is_safe_artifact_path_component(value: str) -> bool:
    if value in {"", ".", ".."}:
        return False
    if any(char in value for char in {"/", "\\"}):
        return False
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        return False
    return not Path(value).is_absolute()


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
        artifacts["implementation_candidate_batch"] = _artifact_reference(candidate_batch_path)
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
            "report_path": _artifact_path_text(report_path),
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
                "reviewed_delivery_job": _artifact_reference(reviewed_delivery_job_path),
                "artifact_handoff_report": _artifact_reference(artifact_handoff_report_path),
            },
            "delivery_attachment_plan": delivery_attachment_plan,
        },
    )


def _artifact_reference(path: Path) -> dict[str, str]:
    return {
        "path": _artifact_path_text(path),
        "sha256": artifact_sha256_file(path),
    }


def _artifact_path_text(path: Path) -> str:
    if type(path) is not _CONCRETE_PATH_TYPE:
        raise ArtifactWriteError("artifact path must be a concrete pathlib Path")
    return str(path)


def artifact_sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open_regular_artifact_file(path) as artifact:
        while chunk := artifact.read(ARTIFACT_HASH_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def read_regular_artifact_bytes(
    path: Path,
    *,
    max_bytes: int,
) -> bytes:
    if max_bytes < 0:
        raise ValueError("max_bytes must not be negative")
    body = bytearray()
    with open_regular_artifact_file(path) as artifact:
        while chunk := artifact.read(min(ARTIFACT_HASH_CHUNK_BYTES, max_bytes + 1 - len(body))):
            body.extend(chunk)
            if len(body) > max_bytes:
                raise ArtifactReadError(
                    f"artifact file exceeds {max_bytes} bytes",
                    reason="too_large",
                    max_bytes=max_bytes,
                )
    return bytes(body)


@contextmanager
def open_regular_artifact_file(path: Path) -> Iterator[BinaryIO]:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = -1
    try:
        fd = os.open(path, flags)
        file_stat = os.fstat(fd)
        if not stat.S_ISREG(file_stat.st_mode):
            raise ArtifactReadError(
                f"artifact path must be a regular file: {path}",
                reason="not_regular",
            )
        with os.fdopen(fd, "rb") as artifact:
            fd = -1
            yield artifact
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise ArtifactReadError(
                f"artifact path must be a regular file: {path}",
                reason="not_regular",
            ) from None
        raise
    finally:
        if fd != -1:
            os.close(fd)
