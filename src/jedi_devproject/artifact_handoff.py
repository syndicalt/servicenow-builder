from __future__ import annotations

import hashlib
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, field_validator


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
    if artifact_kind is ArtifactKind.UPDATE_SET_XML and artifact_path.read_text(
        encoding="utf-8"
    ).lstrip().startswith("<placeholder_update_set"):
        raise ValueError("reviewed_export_artifact_required")
    return {
        "story_number": story_number,
        "artifact_kind": artifact_kind.value,
        "artifact_path": str(artifact_path),
        "approved_for_delivery": True,
        "delivery_contract": _REVIEWED_DELIVERY_CONTRACT,
        "reviewer_id": reviewer_id,
        "artifact_sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
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
    decisions = []
    for artifact in artifacts:
        artifact_path = Path(str(artifact["artifact_path"]))
        plan = plan_artifact_handoff(
            story_number=story_number,
            artifact_kind=ArtifactKind(str(artifact["artifact_kind"])),
            artifact_path=str(artifact_path),
            approved_for_delivery=bool(artifact["approved_for_delivery"]),
            delivery_contract=(
                str(artifact["delivery_contract"])
                if artifact.get("delivery_contract") is not None
                else None
            ),
        ).model_dump(mode="json")
        plan["artifact_sha256"] = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
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
        f"Report: {report_path}. "
        f"total={summary['total']} "
        f"attach_to_servicenow={summary['attach_to_servicenow']} "
        f"internal_evidence={summary['internal_evidence']} "
        f"delivery_evidence={summary['delivery_evidence']}."
    )


def delivery_attachment_jobs_from_report(report: dict[str, Any]) -> list[dict[str, str]]:
    story_number = str(report["story_number"])
    jobs = []
    for decision in report["decisions"]:
        if not decision["attach_to_servicenow"]:
            continue
        if decision.get("delivery_contract") != _REVIEWED_DELIVERY_CONTRACT:
            raise ValueError("delivery_contract_required")
        if decision.get("artifact_sha256") is None:
            raise ValueError("artifact_hash_required")
        jobs.append(
            {
                "story_number": story_number,
                "artifact_kind": str(decision["artifact_kind"]),
                "artifact_path": str(decision["artifact_path"]),
                "delivery_contract": str(decision["delivery_contract"]),
                "artifact_sha256": str(decision["artifact_sha256"]),
                "attachment_label": str(decision["service_now_attachment_label"]),
            }
        )
    return jobs
