from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict

from jedi_devproject.models import CandidateStatus, UpdateSetCandidate


class UpdateSetHandoffClient(Protocol):
    def upsert_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: dict[str, Any],
    ) -> dict[str, Any]: ...

    def update_story_fields(
        self,
        story_sys_id: str,
        fields: dict[str, object],
    ) -> object: ...


class UpdateSetHandoffRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    story_sys_id: str
    story_number: str
    candidate: UpdateSetCandidate
    candidate_artifact_ref: str
    instance_url: str


class UpdateSetHandoffResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    update_set_sys_id: str
    update_set_name: str
    update_set_url: str


def create_update_set_handoff(
    *,
    client: UpdateSetHandoffClient,
    request: UpdateSetHandoffRequest,
) -> UpdateSetHandoffResult:
    if request.candidate.status is not CandidateStatus.READY_FOR_REVIEW:
        raise ValueError("candidate is not ready for Update Set handoff")

    update_set_name = _update_set_name(request.story_number)
    result = client.upsert_table_record(
        table="sys_update_set",
        lookup={"name": update_set_name},
        fields={
            "name": update_set_name,
            "state": "in progress",
            "description": _update_set_description(request),
        },
    )
    update_set_sys_id = str(result.get("sys_id", ""))
    if update_set_sys_id.strip() == "":
        raise RuntimeError("ServiceNow Update Set response did not include sys_id")

    update_set_url = _update_set_url(
        instance_url=request.instance_url,
        update_set_sys_id=update_set_sys_id,
    )
    client.update_story_fields(
        request.story_sys_id,
        {
            "work_notes": (
                f"ServiceNow Update Set handoff created for {request.story_number}. "
                f"Update Set: {update_set_name} ({update_set_url}). "
                f"Candidate artifact: {request.candidate_artifact_ref}."
            )
        },
    )
    return UpdateSetHandoffResult(
        update_set_sys_id=update_set_sys_id,
        update_set_name=update_set_name,
        update_set_url=update_set_url,
    )


def _update_set_name(story_number: str) -> str:
    return f"JEDI {story_number} - AI Candidate"


def _update_set_url(*, instance_url: str, update_set_sys_id: str) -> str:
    return f"{instance_url.rstrip('/')}/sys_update_set.do?sys_id={update_set_sys_id}"


def _update_set_description(request: UpdateSetHandoffRequest) -> str:
    candidate = request.candidate
    lines = [
        f"Jedi DevProject generated handoff for {request.story_number}.",
        "",
        f"Candidate artifact: {request.candidate_artifact_ref}",
        f"Candidate hash: {candidate.artifact_hash or 'unavailable'}",
        f"Status: {candidate.status.value}",
        f"Confidence: {candidate.confidence}",
        f"Risk score: {candidate.risk_score}",
        "",
        "Proposed changes:",
        *_change_summary_lines(candidate),
        "",
        "Reviewer notes:",
        *_reviewer_note_lines(candidate),
        "",
        (
            "This Update Set is a review handoff. Do not commit until the "
            "ServiceNow-native update contents have been reviewed."
        ),
    ]
    return "\n".join(lines)


def _change_summary_lines(candidate: UpdateSetCandidate) -> list[str]:
    if not candidate.changes:
        return ["- No structured changes were generated."]
    return [
        f"- {change.operation} {change.table}: {_field_summary(change.fields)}"
        for change in candidate.changes
    ]


def _field_summary(fields: dict[str, Any]) -> str:
    if not fields:
        return "no fields"
    return ", ".join(f"{name}={value}" for name, value in fields.items())


def _reviewer_note_lines(candidate: UpdateSetCandidate) -> list[str]:
    if not candidate.reviewer_notes:
        return ["- No reviewer notes generated."]
    return [f"- {note}" for note in candidate.reviewer_notes]
