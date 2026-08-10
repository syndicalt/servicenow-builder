from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator


class LifecycleEventType(StrEnum):
    STORY_STATE_CHANGED = "story_state_changed"


class LifecycleStateChangeEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    event_id: str
    event_type: LifecycleEventType
    source: str
    table: str
    story_number: str
    story_sys_id: str | None = None
    previous_state: str
    current_state: str
    occurred_at: datetime
    correlation_id: str
    emitted_by: str

    @field_validator(
        "event_id",
        "source",
        "table",
        "story_number",
        "story_sys_id",
        "previous_state",
        "current_state",
        "correlation_id",
        "emitted_by",
    )
    @classmethod
    def require_non_empty_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value.strip() == "":
            raise ValueError("must not be empty")
        return value


class StoryReadyLifecyclePlan(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    should_evaluate: bool
    lifecycle_action: str | None
    story_number: str
    from_state: str
    current_state: str
    claim_state: str | None
    idempotency_key: str
    reasons: list[str]


def plan_story_ready_lifecycle_event(
    event: LifecycleStateChangeEvent,
) -> StoryReadyLifecyclePlan:
    if (
        event.event_type is LifecycleEventType.STORY_STATE_CHANGED
        and event.table == "rm_story"
        and event.previous_state == "Draft"
        and event.current_state == "Ready"
    ):
        return StoryReadyLifecyclePlan(
            should_evaluate=True,
            lifecycle_action="evaluate_story",
            story_number=event.story_number,
            from_state=event.previous_state,
            current_state=event.current_state,
            claim_state="Work in Progress",
            idempotency_key=event.event_id,
            reasons=[],
        )

    if (
        event.event_type is LifecycleEventType.STORY_STATE_CHANGED
        and event.table == "rm_story"
        and event.previous_state == "Ready for Testing"
        and event.current_state == "Complete"
    ):
        return StoryReadyLifecyclePlan(
            should_evaluate=False,
            lifecycle_action="close_story",
            story_number=event.story_number,
            from_state=event.previous_state,
            current_state=event.current_state,
            claim_state=None,
            idempotency_key=event.event_id,
            reasons=[],
        )

    if (
        event.event_type is LifecycleEventType.STORY_STATE_CHANGED
        and event.table == "rm_story"
        and event.previous_state == "Ready for Testing"
        and event.current_state == "Ready"
    ):
        return StoryReadyLifecyclePlan(
            should_evaluate=False,
            lifecycle_action="rework_requested",
            story_number=event.story_number,
            from_state=event.previous_state,
            current_state=event.current_state,
            claim_state=None,
            idempotency_key=event.event_id,
            reasons=[],
        )

    if (
        event.event_type is LifecycleEventType.STORY_STATE_CHANGED
        and event.table == "rm_story"
        and event.previous_state == "Ready for Testing"
        and event.current_state == "Draft"
    ):
        return StoryReadyLifecyclePlan(
            should_evaluate=False,
            lifecycle_action="story_rejected",
            story_number=event.story_number,
            from_state=event.previous_state,
            current_state=event.current_state,
            claim_state=None,
            idempotency_key=event.event_id,
            reasons=[],
        )

    return StoryReadyLifecyclePlan(
        should_evaluate=False,
        lifecycle_action=None,
        story_number=event.story_number,
        from_state=event.previous_state,
        current_state=event.current_state,
        claim_state=None,
        idempotency_key=event.event_id,
        reasons=["unsupported_lifecycle_transition"],
    )
