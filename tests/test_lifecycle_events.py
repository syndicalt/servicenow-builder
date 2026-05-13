import pytest
from pydantic import ValidationError

from jedi_devproject.lifecycle_events import (
    LifecycleEventType,
    LifecycleStateChangeEvent,
    plan_story_ready_lifecycle_event,
)


def test_draft_to_ready_event_plans_evaluation_and_claim_state() -> None:
    event = LifecycleStateChangeEvent.model_validate(
        {
            "event_id": "evt-20260513-001",
            "event_type": "story_state_changed",
            "source": "servicenow-business-rule",
            "table": "rm_story",
            "story_number": "STRY0010013",
            "previous_state": "Draft",
            "current_state": "Ready",
            "occurred_at": "2026-05-13T15:45:00Z",
            "correlation_id": "STRY0010013-Draft-Ready-20260513T154500Z",
            "emitted_by": "jedi-devproject-lifecycle-integration",
        }
    )

    plan = plan_story_ready_lifecycle_event(event)

    assert event.event_type is LifecycleEventType.STORY_STATE_CHANGED
    assert plan.should_evaluate is True
    assert plan.lifecycle_action == "evaluate_story"
    assert plan.story_number == "STRY0010013"
    assert plan.from_state == "Draft"
    assert plan.current_state == "Ready"
    assert plan.claim_state == "Work in Progress"
    assert plan.idempotency_key == "evt-20260513-001"
    assert plan.reasons == []


def test_lifecycle_event_rejects_unknown_servicenow_identifiers() -> None:
    with pytest.raises(ValidationError) as exc:
        LifecycleStateChangeEvent.model_validate(
            {
                "event_id": "evt-20260513-001",
                "event_type": "story_state_changed",
                "source": "servicenow-business-rule",
                "table": "rm_story",
                "story_number": "STRY0010013",
                "previous_state": "Draft",
                "current_state": "Ready",
                "occurred_at": "2026-05-13T15:45:00Z",
                "correlation_id": "STRY0010013-Draft-Ready-20260513T154500Z",
                "emitted_by": "jedi-devproject-lifecycle-integration",
                "story_sys_id": "must-not-cross-this-boundary",
            }
        )

    assert "Extra inputs are not permitted" in str(exc.value)


def test_non_ready_transition_does_not_plan_evaluation() -> None:
    event = LifecycleStateChangeEvent.model_validate(
        {
            "event_id": "evt-20260513-002",
            "event_type": LifecycleEventType.STORY_STATE_CHANGED,
            "source": "servicenow-business-rule",
            "table": "rm_story",
            "story_number": "STRY0010013",
            "previous_state": "Ready",
            "current_state": "Work in Progress",
            "occurred_at": "2026-05-13T15:46:00Z",
            "correlation_id": "STRY0010013-Ready-WIP-20260513T154600Z",
            "emitted_by": "jedi-devproject-lifecycle-integration",
        }
    )

    plan = plan_story_ready_lifecycle_event(event)

    assert plan.should_evaluate is False
    assert plan.claim_state is None
    assert plan.reasons == ["unsupported_lifecycle_transition"]


def test_lifecycle_event_requires_idempotency_and_source_context() -> None:
    with pytest.raises(ValidationError) as exc:
        LifecycleStateChangeEvent.model_validate(
            {
                "event_id": " ",
                "event_type": "story_state_changed",
                "source": " ",
                "table": "rm_story",
                "story_number": "STRY0010013",
                "previous_state": "Draft",
                "current_state": "Ready",
                "occurred_at": "2026-05-13T15:45:00Z",
                "correlation_id": " ",
                "emitted_by": " ",
            }
        )

    assert "must not be empty" in str(exc.value)
