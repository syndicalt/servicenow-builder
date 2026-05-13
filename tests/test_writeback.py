from jedi_devproject.models import DataClassification, Story
from jedi_devproject.writeback import (
    ExternalBuildResult,
    ExternalBuildStatus,
    StoryStateMapping,
    StoryWritebackPolicy,
    build_state_mapping_from_choices,
    plan_external_build_writeback,
    plan_story_build_claim_writeback,
    validate_writeback_fields,
)


def _story(state: str = "Work in Progress") -> Story:
    return Story(
        sys_id="story-sys-id",
        number="STRY0010013",
        short_description="Add AI Review Notes field to Story form",
        description="Add an optional AI Review Notes field to the Story form.",
        story_points=3,
        priority=4,
        state=state,
        data_classification=DataClassification.PUBLIC,
    )


def test_successful_external_build_plans_ready_for_testing_transition() -> None:
    plan = plan_external_build_writeback(
        story=_story(),
        build_result=ExternalBuildResult(
            status=ExternalBuildStatus.SUCCEEDED,
            build_reference="build-20260513-001",
            artifact_url="artifacts/STRY0010013.json",
        ),
        state_mapping=StoryStateMapping(ready_for_testing="Ready for Testing"),
        policy=StoryWritebackPolicy(
            state_transitions_enabled=True,
            allowed_state_transitions={"Work in Progress": {"Ready for Testing"}},
        ),
    )

    assert plan.allowed is True
    assert plan.fields["state"] == "Ready for Testing"
    assert plan.fields["u_ai_status"] == "Ready for Testing"
    assert plan.fields["u_ai_build_reference"] == "build-20260513-001"
    assert plan.fields["u_ai_candidate_artifact"] == "artifacts/STRY0010013.json"
    assert "External build completed" in plan.work_notes


def test_state_mapping_uses_instance_choice_value_for_ready_for_testing() -> None:
    state_mapping = build_state_mapping_from_choices(
        [{"label": "Ready for Testing", "value": "-7"}]
    )

    assert state_mapping is not None
    assert state_mapping.ready_for_testing == "-7"


def test_state_mapping_fails_closed_when_ready_for_testing_is_missing() -> None:
    state_mapping = build_state_mapping_from_choices([{"label": "Testing", "value": "2"}])

    assert state_mapping is None


def test_successful_external_build_does_not_advance_state_when_transition_is_disabled() -> None:
    plan = plan_external_build_writeback(
        story=_story(),
        build_result=ExternalBuildResult(
            status=ExternalBuildStatus.SUCCEEDED,
            build_reference="build-20260513-001",
        ),
        state_mapping=StoryStateMapping(ready_for_testing="Ready for Testing"),
        policy=StoryWritebackPolicy(state_transitions_enabled=False),
    )

    assert plan.allowed is False
    assert "state" not in plan.fields
    assert "State transitions are disabled" in plan.reasons


def test_validate_writeback_fields_fails_closed_when_structured_fields_are_missing() -> None:
    plan = plan_external_build_writeback(
        story=_story(),
        build_result=ExternalBuildResult(
            status=ExternalBuildStatus.SUCCEEDED,
            build_reference="build-20260513-001",
        ),
        state_mapping=StoryStateMapping(ready_for_testing="-7"),
        policy=StoryWritebackPolicy(
            state_transitions_enabled=True,
            allowed_state_transitions={"Work in Progress": {"-7"}},
        ),
    )

    validated = validate_writeback_fields(
        plan,
        available_fields={"state", "u_ai_status", "u_ai_build_reference"},
    )

    assert validated.allowed is False
    assert "u_ai_candidate_artifact" in validated.reasons[0]


def test_failed_external_build_routes_to_human_review_without_state_change() -> None:
    plan = plan_external_build_writeback(
        story=_story(),
        build_result=ExternalBuildResult(
            status=ExternalBuildStatus.FAILED,
            build_reference="build-20260513-001",
            message="Build validation failed.",
        ),
        state_mapping=StoryStateMapping(ready_for_testing="Ready for Testing"),
        policy=StoryWritebackPolicy(
            state_transitions_enabled=True,
            allowed_state_transitions={"Work in Progress": {"Ready for Testing"}},
        ),
    )

    assert plan.allowed is True
    assert "state" not in plan.fields
    assert plan.fields["u_ai_status"] == "Human Review Required"
    assert "Build validation failed." in plan.work_notes


def test_story_build_claim_plans_work_in_progress_transition() -> None:
    plan = plan_story_build_claim_writeback(
        story=_story(state="Ready"),
        lifecycle_event_id="evt-20260513-001",
        candidate_artifact_url="artifacts/implementation-candidates/STRY0010013.json",
        claim_state="Work in Progress",
        policy=StoryWritebackPolicy(
            state_transitions_enabled=True,
            allowed_state_transitions={"Ready": {"Work in Progress"}},
        ),
    )

    assert plan.allowed is True
    assert plan.fields["state"] == "Work in Progress"
    assert plan.fields["u_ai_status"] == "Build In Progress"
    assert (
        plan.fields["u_ai_candidate_artifact"]
        == "artifacts/implementation-candidates/STRY0010013.json"
    )
    assert "evt-20260513-001" in plan.work_notes
    assert "Automated build started" in plan.work_notes


def test_story_build_claim_fails_closed_when_transition_is_not_allowlisted() -> None:
    plan = plan_story_build_claim_writeback(
        story=_story(state="Draft"),
        lifecycle_event_id="evt-20260513-001",
        candidate_artifact_url=None,
        claim_state="Work in Progress",
        policy=StoryWritebackPolicy(
            state_transitions_enabled=True,
            allowed_state_transitions={"Ready": {"Work in Progress"}},
        ),
    )

    assert plan.allowed is False
    assert "state" not in plan.fields
    assert "Transition from 'Draft' to 'Work in Progress' is not allowlisted" in plan.reasons
