from __future__ import annotations

import math
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from jedi_devproject.artifacts import artifact_sha256_file, open_regular_artifact_file
from jedi_devproject.work_note_safety import safe_work_note_value


class ArtifactKind(StrEnum):
    IMPLEMENTATION_PACKET = "implementation_packet"
    IMPLEMENTATION_CANDIDATE = "implementation_candidate"
    LIFECYCLE_MANIFEST = "lifecycle_manifest"
    WRITEBACK_AUDIT = "writeback_audit"
    UPDATE_SET_XML = "update_set_xml"
    TEST_EVIDENCE_BUNDLE = "test_evidence_bundle"


class ArtifactExposure(StrEnum):
    INTERNAL_EVIDENCE = "internal_evidence"
    DELIVERY_EVIDENCE = "delivery_evidence"


class ArtifactHandoffPlan(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    story_number: str
    artifact_kind: ArtifactKind
    artifact_path: str
    delivery_contract: str | None = None
    exposure: ArtifactExposure
    attach_to_servicenow: bool
    write_story_link: bool
    required_before_ready_for_testing: bool
    service_now_attachment_label: str | None = None
    rationale: str

    @field_validator("story_number", "artifact_path", "rationale")
    @classmethod
    def require_non_empty_text(cls, value: str) -> str:
        if value.strip() == "":
            raise ValueError("must not be empty")
        return value


_ATTACHMENT_LABELS = {
    ArtifactKind.UPDATE_SET_XML: "Approved Update Set XML",
    ArtifactKind.TEST_EVIDENCE_BUNDLE: "Test Evidence Bundle",
}
_REVIEWED_DELIVERY_CONTRACT = "reviewed_export"
_XML_SCAN_CHUNK_BYTES = 64 * 1024
_XML_MARKER_SCAN_BYTES = 10 * 1024 * 1024
_PLACEHOLDER_UPDATE_SET_MARKER = b"<placeholder_update_set"
_SYS_UPDATE_XML_MARKER = b"<sys_update_xml"
ARTIFACT_HANDOFF_REPORT_INVALID = "artifact_handoff_report_invalid"


def build_reviewed_delivery_artifact_job(
    *,
    story_number: str,
    artifact_kind: ArtifactKind,
    artifact_path: Path,
    reviewer_id: str,
) -> dict[str, Any]:
    if artifact_kind not in _ATTACHMENT_LABELS:
        raise ValueError("delivery_artifact_kind_required")
    if reviewer_id.strip() == "":
        raise ValueError("reviewer_id_required")
    if artifact_kind is ArtifactKind.UPDATE_SET_XML and not _is_reviewed_update_set_xml_artifact(
        artifact_path
    ):
        raise ValueError("reviewed_export_artifact_required")
    return {
        "story_number": story_number,
        "artifact_kind": artifact_kind.value,
        "artifact_path": str(artifact_path),
        "approved_for_delivery": True,
        "delivery_contract": _REVIEWED_DELIVERY_CONTRACT,
        "reviewer_id": reviewer_id,
        "artifact_sha256": artifact_sha256_file(artifact_path),
    }


def plan_artifact_handoff(
    *,
    story_number: str,
    artifact_kind: ArtifactKind,
    artifact_path: str,
    approved_for_delivery: bool,
    delivery_contract: str | None = None,
) -> ArtifactHandoffPlan:
    can_attach = (
        artifact_kind in _ATTACHMENT_LABELS
        and approved_for_delivery
        and delivery_contract == _REVIEWED_DELIVERY_CONTRACT
    )
    if can_attach:
        return ArtifactHandoffPlan(
            story_number=story_number,
            artifact_kind=artifact_kind,
            artifact_path=artifact_path,
            delivery_contract=delivery_contract,
            exposure=ArtifactExposure.DELIVERY_EVIDENCE,
            attach_to_servicenow=True,
            write_story_link=True,
            required_before_ready_for_testing=True,
            service_now_attachment_label=_ATTACHMENT_LABELS[artifact_kind],
            rationale="Approved delivery evidence can be attached to the story.",
        )

    if artifact_kind in _ATTACHMENT_LABELS and approved_for_delivery:
        approval_reason = (
            "reviewed export contract is required before this artifact can become "
            "delivery evidence"
        )
    elif artifact_kind in _ATTACHMENT_LABELS:
        approval_reason = (
            "human approval is required before this artifact can become delivery evidence"
        )
    else:
        approval_reason = (
            "internal audit evidence should remain in controlled artifact storage"
        )
    return ArtifactHandoffPlan(
        story_number=story_number,
        artifact_kind=artifact_kind,
        artifact_path=artifact_path,
        delivery_contract=delivery_contract,
        exposure=ArtifactExposure.INTERNAL_EVIDENCE,
        attach_to_servicenow=False,
        write_story_link=True,
        required_before_ready_for_testing=False,
        rationale=approval_reason,
    )


def build_artifact_handoff_report(
    *,
    run_id: str,
    story_number: str,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    run_id = _handoff_required_text(run_id)
    story_number = _handoff_required_text(story_number)
    if type(artifacts) is not list:
        raise ValueError(ARTIFACT_HANDOFF_REPORT_INVALID)
    decisions = []
    for artifact in artifacts:
        if type(artifact) is not dict:
            raise ValueError(ARTIFACT_HANDOFF_REPORT_INVALID)
        artifact_path_text = _handoff_required_text(artifact.get("artifact_path"))
        artifact_kind_text = _handoff_required_text(artifact.get("artifact_kind"))
        approved_for_delivery = artifact.get("approved_for_delivery")
        if type(approved_for_delivery) is not bool:
            raise ValueError(ARTIFACT_HANDOFF_REPORT_INVALID)
        delivery_contract_value = artifact.get("delivery_contract")
        if delivery_contract_value is not None:
            delivery_contract_value = _handoff_required_text(delivery_contract_value)
        artifact_path = Path(artifact_path_text)
        plan = plan_artifact_handoff(
            story_number=story_number,
            artifact_kind=ArtifactKind(artifact_kind_text),
            artifact_path=artifact_path_text,
            approved_for_delivery=approved_for_delivery,
            delivery_contract=delivery_contract_value,
        ).model_dump(mode="json")
        plan["artifact_sha256"] = artifact_sha256_file(artifact_path)
        decisions.append(plan)
    return {
        "run_id": run_id,
        "story_number": story_number,
        "summary": {
            "total": len(decisions),
            "attach_to_servicenow": sum(
                1 for decision in decisions if decision["attach_to_servicenow"]
            ),
            "internal_evidence": sum(
                1
                for decision in decisions
                if decision["exposure"] == ArtifactExposure.INTERNAL_EVIDENCE.value
            ),
            "delivery_evidence": sum(
                1
                for decision in decisions
                if decision["exposure"] == ArtifactExposure.DELIVERY_EVIDENCE.value
            ),
        },
        "decisions": decisions,
    }


def build_artifact_handoff_work_note(
    *,
    report: dict[str, Any],
    report_path: Path,
) -> str:
    summary = report["summary"]
    return (
        "Artifact handoff planned. "
        f"Report: {safe_work_note_value(str(report_path))}. "
        f"total={safe_work_note_value(_handoff_summary_value(summary['total']))} "
        "attach_to_servicenow="
        f"{safe_work_note_value(_handoff_summary_value(summary['attach_to_servicenow']))} "
        "internal_evidence="
        f"{safe_work_note_value(_handoff_summary_value(summary['internal_evidence']))} "
        "delivery_evidence="
        f"{safe_work_note_value(_handoff_summary_value(summary['delivery_evidence']))}."
    )


def _handoff_summary_value(value: Any) -> str:
    if type(value) is str:
        return value
    if value is None:
        return "None"
    if type(value) is bool:
        return "True" if value else "False"
    if type(value) is int:
        return str(value)
    if type(value) is float and math.isfinite(value):
        return str(value)
    return "[unsupported handoff summary value]"


def delivery_attachment_jobs_from_report(report: dict[str, Any]) -> list[dict[str, str]]:
    story_number = _handoff_required_text(report.get("story_number"))
    decisions = report.get("decisions")
    if type(decisions) is not list:
        raise ValueError(ARTIFACT_HANDOFF_REPORT_INVALID)
    jobs = []
    for decision in decisions:
        if type(decision) is not dict:
            raise ValueError(ARTIFACT_HANDOFF_REPORT_INVALID)
        attach_to_servicenow = decision.get("attach_to_servicenow")
        if type(attach_to_servicenow) is not bool:
            raise ValueError(ARTIFACT_HANDOFF_REPORT_INVALID)
        if not attach_to_servicenow:
            continue
        if decision.get("delivery_contract") != _REVIEWED_DELIVERY_CONTRACT:
            raise ValueError("delivery_contract_required")
        if decision.get("artifact_sha256") is None:
            raise ValueError("artifact_hash_required")
        jobs.append(
            {
                "story_number": story_number,
                "artifact_kind": _handoff_required_text(decision.get("artifact_kind")),
                "artifact_path": _handoff_required_text(decision.get("artifact_path")),
                "delivery_contract": _handoff_required_text(
                    decision.get("delivery_contract")
                ),
                "artifact_sha256": _handoff_required_text(decision.get("artifact_sha256")),
                "attachment_label": _handoff_required_text(
                    decision.get("service_now_attachment_label")
                ),
            }
        )
    return jobs


def _handoff_required_text(value: Any) -> str:
    if type(value) is not str or value.strip() == "":
        raise ValueError(ARTIFACT_HANDOFF_REPORT_INVALID)
    return value


def _is_reviewed_update_set_xml_artifact(path: Path) -> bool:
    first_content_prefix = _first_non_whitespace_prefix(
        path,
        max_prefix_bytes=len(_PLACEHOLDER_UPDATE_SET_MARKER),
        max_scan_bytes=_XML_MARKER_SCAN_BYTES,
    )
    if first_content_prefix.startswith(_PLACEHOLDER_UPDATE_SET_MARKER):
        return False
    return _file_contains_marker(
        path,
        marker=_SYS_UPDATE_XML_MARKER,
        max_scan_bytes=_XML_MARKER_SCAN_BYTES,
    )


def _first_non_whitespace_prefix(
    path: Path,
    *,
    max_prefix_bytes: int,
    max_scan_bytes: int,
) -> bytes:
    prefix = b""
    found_content = False
    scanned = 0
    with open_regular_artifact_file(path) as artifact:
        while scanned < max_scan_bytes and len(prefix) < max_prefix_bytes:
            chunk = artifact.read(min(_XML_SCAN_CHUNK_BYTES, max_scan_bytes - scanned))
            if not chunk:
                break
            scanned += len(chunk)
            candidate = chunk if found_content else chunk.lstrip()
            if not candidate:
                continue
            found_content = True
            remaining = max_prefix_bytes - len(prefix)
            prefix += candidate[:remaining]
    return prefix


def _file_contains_marker(
    path: Path,
    *,
    marker: bytes,
    max_scan_bytes: int,
) -> bool:
    tail = b""
    scanned = 0
    with open_regular_artifact_file(path) as artifact:
        while scanned < max_scan_bytes:
            chunk = artifact.read(min(_XML_SCAN_CHUNK_BYTES, max_scan_bytes - scanned))
            if not chunk:
                break
            scanned += len(chunk)
            window = tail + chunk
            if marker in window:
                return True
            tail = window[-(len(marker) - 1) :]
    return False
