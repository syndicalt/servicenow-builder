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


def test_lifecycle_event_accepts_story_sys_id_for_authoritative_lookup() -> None:
    event = LifecycleStateChangeEvent.model_validate(
        {
            "event_id": "evt-20260513-001",
            "event_type": "story_state_changed",
            "source": "servicenow-business-rule",
            "table": "rm_story",
            "story_number": "STRY0010013",
            "story_sys_id": "rm-story-sys-id",
            "previous_state": "Draft",
            "current_state": "Ready",
            "occurred_at": "2026-05-13T15:45:00Z",
            "correlation_id": "STRY0010013-Draft-Ready-20260513T154500Z",
            "emitted_by": "jedi-devproject-lifecycle-integration",
        }
    )

    assert event.story_sys_id == "rm-story-sys-id"


def test_lifecycle_event_still_rejects_unknown_payload_fields() -> None:
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
                "story_url": "https://dev205693.service-now.com/rm_story.do",
            }
        )

    assert "Extra inputs are not permitted" in str(exc.value)


def test_lifecycle_event_validation_errors_do_not_echo_rejected_inputs() -> None:
    with pytest.raises(ValidationError) as exc:
        LifecycleStateChangeEvent.model_validate(
            {
                "event_id": "evt-20260513-001",
                "event_type": "story_state_changed",
                "source": "servicenow-business-rule",
                "table": "rm_story",
                "story_number": "",
                "previous_state": "Draft",
                "current_state": "Ready",
                "occurred_at": "2026-05-13T15:45:00Z",
                "correlation_id": "STRY0010013-Draft-Ready-20260513T154500Z",
                "emitted_by": "jedi-devproject-lifecycle-integration",
            }
        )

    message = str(exc.value)
    assert "story_number" in message
    assert "input_value" not in message


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


def test_ready_for_testing_to_complete_event_plans_story_closeout_without_build() -> None:
    event = LifecycleStateChangeEvent.model_validate(
        {
            "event_id": "evt-20260514-uat-complete",
            "event_type": LifecycleEventType.STORY_STATE_CHANGED,
            "source": "servicenow-business-rule",
            "table": "rm_story",
            "story_number": "STRY0010002",
            "previous_state": "Ready for Testing",
            "current_state": "Complete",
            "occurred_at": "2026-05-14T18:45:00Z",
            "correlation_id": "STRY0010002-ReadyForTesting-Complete-20260514T184500Z",
            "emitted_by": "jedi-devproject-lifecycle-integration",
        }
    )

    plan = plan_story_ready_lifecycle_event(event)

    assert plan.should_evaluate is False
    assert plan.lifecycle_action == "close_story"
    assert plan.story_number == "STRY0010002"
    assert plan.from_state == "Ready for Testing"
    assert plan.current_state == "Complete"
    assert plan.claim_state is None
    assert plan.idempotency_key == "evt-20260514-uat-complete"
    assert plan.reasons == []


def test_ready_for_testing_to_ready_plans_rework_without_build() -> None:
    event = LifecycleStateChangeEvent.model_validate(
        {
            "event_id": "evt-20260514-rework-ready",
            "event_type": LifecycleEventType.STORY_STATE_CHANGED,
            "source": "servicenow-business-rule",
            "table": "rm_story",
            "story_number": "STRY0010002",
            "previous_state": "Ready for Testing",
            "current_state": "Ready",
            "occurred_at": "2026-05-14T19:10:00Z",
            "correlation_id": "STRY0010002-ReadyForTesting-Ready-20260514T191000Z",
            "emitted_by": "jedi-devproject-lifecycle-integration",
        }
    )

    plan = plan_story_ready_lifecycle_event(event)

    assert plan.should_evaluate is False
    assert plan.lifecycle_action == "rework_requested"
    assert plan.story_number == "STRY0010002"
    assert plan.from_state == "Ready for Testing"
    assert plan.current_state == "Ready"
    assert plan.claim_state is None
    assert plan.idempotency_key == event.event_id
    assert plan.reasons == []


def test_ready_for_testing_to_draft_plans_story_rejected_reset_without_build() -> None:
    event = LifecycleStateChangeEvent.model_validate(
        {
            "event_id": "evt-20260514-story-rejected",
            "event_type": LifecycleEventType.STORY_STATE_CHANGED,
            "source": "servicenow-business-rule",
            "table": "rm_story",
            "story_number": "STRY0010002",
            "previous_state": "Ready for Testing",
            "current_state": "Draft",
            "occurred_at": "2026-05-14T19:12:00Z",
            "correlation_id": "STRY0010002-ReadyForTesting-Draft-20260514T191200Z",
            "emitted_by": "jedi-devproject-lifecycle-integration",
        }
    )

    plan = plan_story_ready_lifecycle_event(event)

    assert plan.should_evaluate is False
    assert plan.lifecycle_action == "story_rejected"
    assert plan.story_number == "STRY0010002"
    assert plan.from_state == "Ready for Testing"
    assert plan.current_state == "Draft"
    assert plan.claim_state is None
    assert plan.idempotency_key == "evt-20260514-story-rejected"
    assert plan.reasons == []


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
