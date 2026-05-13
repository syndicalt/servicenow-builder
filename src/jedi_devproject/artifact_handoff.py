from __future__ import annotations

from enum import StrEnum

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


def plan_artifact_handoff(
    *,
    story_number: str,
    artifact_kind: ArtifactKind,
    artifact_path: str,
    approved_for_delivery: bool,
) -> ArtifactHandoffPlan:
    can_attach = artifact_kind in _ATTACHMENT_LABELS and approved_for_delivery
    if can_attach:
        return ArtifactHandoffPlan(
            story_number=story_number,
            artifact_kind=artifact_kind,
            artifact_path=artifact_path,
            exposure=ArtifactExposure.DELIVERY_EVIDENCE,
            attach_to_servicenow=True,
            write_story_link=True,
            required_before_ready_for_testing=True,
            service_now_attachment_label=_ATTACHMENT_LABELS[artifact_kind],
            rationale="Approved delivery evidence can be attached to the story.",
        )

    approval_reason = (
        "human approval is required before this artifact can become delivery evidence"
        if artifact_kind in _ATTACHMENT_LABELS
        else "internal audit evidence should remain in controlled artifact storage"
    )
    return ArtifactHandoffPlan(
        story_number=story_number,
        artifact_kind=artifact_kind,
        artifact_path=artifact_path,
        exposure=ArtifactExposure.INTERNAL_EVIDENCE,
        attach_to_servicenow=False,
        write_story_link=True,
        required_before_ready_for_testing=False,
        rationale=approval_reason,
    )
