from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from jedi_devproject.artifact_handoff import (
    ArtifactKind,
    build_reviewed_delivery_artifact_job,
)


class ExternalBuildPipelineStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"


class ExternalBuildPipelineResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    story_number: str
    build_reference: str
    status: ExternalBuildPipelineStatus
    candidate_artifact_path: Path
    reviewed_update_set_xml_path: Path | None = None
    test_evidence_path: Path | None = None
    build_actor_id: str
    failure_reasons: list[str] = Field(default_factory=list)
    message: str | None = None

    @model_validator(mode="after")
    def validate_contract(self) -> ExternalBuildPipelineResult:
        if self.status is ExternalBuildPipelineStatus.SUCCEEDED and (
            self.reviewed_update_set_xml_path is None or self.test_evidence_path is None
        ):
            raise ValueError("successful builds require reviewed delivery outputs")
        if (
            self.status is not ExternalBuildPipelineStatus.SUCCEEDED
            and not self.failure_reasons
            and self.message is None
        ):
            raise ValueError("unsuccessful builds require failure evidence")
        return self


def writeback_job_from_build_result(
    result: ExternalBuildPipelineResult,
    *,
    from_state: str,
) -> dict[str, str]:
    return {
        "story_number": result.story_number,
        "build_reference": result.build_reference,
        "artifact_url": str(result.candidate_artifact_path),
        "build_status": result.status.value,
        "from_state": from_state,
    }


def reviewed_delivery_jobs_from_build_result(
    result: ExternalBuildPipelineResult,
) -> list[dict[str, object]]:
    if result.status is not ExternalBuildPipelineStatus.SUCCEEDED:
        raise ValueError("successful_build_required")
    if result.reviewed_update_set_xml_path is None or result.test_evidence_path is None:
        raise ValueError("reviewed_delivery_outputs_required")
    return [
        build_reviewed_delivery_artifact_job(
            story_number=result.story_number,
            artifact_kind=ArtifactKind.UPDATE_SET_XML,
            artifact_path=result.reviewed_update_set_xml_path,
            reviewer_id=result.build_actor_id,
        ),
        build_reviewed_delivery_artifact_job(
            story_number=result.story_number,
            artifact_kind=ArtifactKind.TEST_EVIDENCE_BUNDLE,
            artifact_path=result.test_evidence_path,
            reviewer_id=result.build_actor_id,
        ),
    ]
