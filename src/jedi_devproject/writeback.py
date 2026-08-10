from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from jedi_devproject.models import Story
from jedi_devproject.work_note_safety import safe_work_note_value


class ExternalBuildStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"


class ActorType(StrEnum):
    SERVICE = "service"
    HUMAN = "human"


class ExternalBuildResult(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    status: ExternalBuildStatus
    build_reference: str
    artifact_url: str | None = None
    message: str | None = None


class StoryStateMapping(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    ready_for_testing: str


class StoryWritebackPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    state_transitions_enabled: bool = False
    allowed_state_transitions: dict[str, set[str]] = Field(default_factory=dict)
    allowed_fields: set[str] = Field(
        default_factory=lambda: {
            "state",
            "u_ai_status",
            "u_ai_build_reference",
            "u_ai_candidate_artifact",
            "work_notes",
        }
    )

    def allows_transition(self, *, from_state: str, to_state: str) -> bool:
        return (
            self.state_transitions_enabled
            and to_state in self.allowed_state_transitions.get(from_state, set())
        )


class StoryWritebackPlan(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    story_sys_id: str
    story_number: str
    fields: dict[str, str] = Field(default_factory=dict)
    work_notes: str
    allowed: bool
    reasons: list[str] = Field(default_factory=list)


class WritebackAuditEvent(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    story_number: str
    build_reference: str
    actor_type: ActorType
    actor_id: str
    run_id: str | None = None
    apply_requested: bool
    applied: bool
    allowed: bool
    fields: dict[str, str] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)


class BuildClaimAuditEvent(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    story_number: str
    lifecycle_event_id: str
    actor_type: ActorType
    actor_id: str
    run_id: str | None = None
    apply_requested: bool
    applied: bool
    allowed: bool
    fields: dict[str, str] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)


REQUIRED_STRUCTURED_WRITEBACK_FIELDS = {
    "state",
    "u_ai_status",
    "u_ai_build_reference",
    "u_ai_candidate_artifact",
}
MAX_EXTERNAL_BUILD_WORK_NOTE_VALUE_CHARS = 500


def build_state_mapping_from_choices(
    choices: list[dict[str, Any]],
) -> StoryStateMapping | None:
    for choice in choices:
        label = _state_choice_text(choice.get("label"))
        if label.strip().lower() == "ready for testing":
            value = _state_choice_text(choice.get("value")).strip()
            if value:
                return StoryStateMapping(ready_for_testing=value)
    return None


def _state_choice_text(value: Any) -> str:
    if type(value) is not str:
        return ""
    return value


def validate_writeback_fields(
    plan: StoryWritebackPlan,
    *,
    available_fields: set[str],
) -> StoryWritebackPlan:
    missing_fields = sorted(REQUIRED_STRUCTURED_WRITEBACK_FIELDS - available_fields)
    if not missing_fields:
        return plan
    return plan.model_copy(
        update={
            "allowed": False,
            "reasons": [
                *plan.reasons,
                f"Required writeback fields are missing: {', '.join(missing_fields)}",
            ],
        }
    )


def plan_external_build_writeback(
    *,
    story: Story,
    build_result: ExternalBuildResult,
    state_mapping: StoryStateMapping,
    policy: StoryWritebackPolicy,
) -> StoryWritebackPlan:
    if build_result.status is not ExternalBuildStatus.SUCCEEDED:
        fields = _base_fields(build_result, status="Human Review Required")
        return _plan(
            story=story,
            fields=fields,
            work_notes=_work_notes(build_result, "External build did not complete successfully"),
            policy=policy,
            allowed=True,
        )

    target_state = state_mapping.ready_for_testing
    if not policy.state_transitions_enabled:
        return _plan(
            story=story,
            fields=_base_fields(build_result, status="Build Complete"),
            work_notes=_work_notes(build_result, "External build completed"),
            policy=policy,
            allowed=False,
            reasons=["State transitions are disabled"],
        )

    if not policy.allows_transition(from_state=story.state, to_state=target_state):
        return _plan(
            story=story,
            fields=_base_fields(build_result, status="Build Complete"),
            work_notes=_work_notes(build_result, "External build completed"),
            policy=policy,
            allowed=False,
            reasons=[
                f"Transition from {story.state!r} to {target_state!r} is not allowlisted"
            ],
        )

    fields = _base_fields(build_result, status="Ready for Testing")
    fields["state"] = target_state
    return _plan(
        story=story,
        fields=fields,
        work_notes=_work_notes(build_result, "External build completed"),
        policy=policy,
        allowed=True,
    )


def plan_story_build_claim_writeback(
    *,
    story: Story,
    lifecycle_event_id: str,
    candidate_artifact_url: str | None,
    claim_state: str,
    policy: StoryWritebackPolicy,
) -> StoryWritebackPlan:
    fields = {"u_ai_status": "Build In Progress"}
    if candidate_artifact_url:
        fields["u_ai_candidate_artifact"] = structured_writeback_field_value(
            candidate_artifact_url
        )

    if not policy.state_transitions_enabled:
        return _plan(
            story=story,
            fields=fields,
            work_notes=_build_claim_work_notes(lifecycle_event_id),
            policy=policy,
            allowed=False,
            reasons=["State transitions are disabled"],
        )

    if not policy.allows_transition(from_state=story.state, to_state=claim_state):
        return _plan(
            story=story,
            fields=fields,
            work_notes=_build_claim_work_notes(lifecycle_event_id),
            policy=policy,
            allowed=False,
            reasons=[
                f"Transition from {story.state!r} to {claim_state!r} is not allowlisted"
            ],
        )

    fields["state"] = claim_state
    return _plan(
        story=story,
        fields=fields,
        work_notes=_build_claim_work_notes(lifecycle_event_id),
        policy=policy,
        allowed=True,
    )


def _base_fields(build_result: ExternalBuildResult, *, status: str) -> dict[str, str]:
    fields = {
        "u_ai_status": status,
        "u_ai_build_reference": structured_writeback_field_value(
            build_result.build_reference
        ),
    }
    if build_result.artifact_url:
        fields["u_ai_candidate_artifact"] = structured_writeback_field_value(
            build_result.artifact_url
        )
    return fields


def _work_notes(build_result: ExternalBuildResult, prefix: str) -> str:
    reference = _safe_work_note_value(build_result.build_reference)
    notes = f"{prefix}. Build reference: {reference}."
    if build_result.message:
        notes = f"{notes} {_safe_work_note_value(build_result.message)}"
    return notes


def _safe_work_note_value(value: str) -> str:
    return safe_work_note_value(value, max_chars=MAX_EXTERNAL_BUILD_WORK_NOTE_VALUE_CHARS)


def structured_writeback_field_value(value: str) -> str:
    return safe_work_note_value(value, max_chars=MAX_EXTERNAL_BUILD_WORK_NOTE_VALUE_CHARS)


def _build_claim_work_notes(lifecycle_event_id: str) -> str:
    safe_lifecycle_event_id = _safe_work_note_value(lifecycle_event_id)
    return (
        "Automated build started. "
        f"Lifecycle event: {safe_lifecycle_event_id}. "
        "The story was claimed for external build orchestration."
    )


def _plan(
    *,
    story: Story,
    fields: dict[str, str],
    work_notes: str,
    policy: StoryWritebackPolicy,
    allowed: bool,
    reasons: list[str] | None = None,
) -> StoryWritebackPlan:
    output_fields = dict(fields)
    output_fields["work_notes"] = work_notes
    disallowed_fields = sorted(set(output_fields) - policy.allowed_fields)
    final_reasons = list(reasons or [])
    if disallowed_fields:
        allowed = False
        final_reasons.append(f"Fields are not allowlisted: {', '.join(disallowed_fields)}")

    return StoryWritebackPlan(
        story_sys_id=story.sys_id,
        story_number=story.number,
        fields={key: value for key, value in output_fields.items() if key != "work_notes"},
        work_notes=work_notes,
        allowed=allowed,
        reasons=final_reasons,
    )
