from jedi_devproject.models import DataClassification, Story
from jedi_devproject.safety import (
    AllowlistPolicy,
    EligibilityDecision,
    StoryType,
    evaluate_story,
)


def _story(
    *,
    description: str,
    short_description: str = "Update portal help text",
    story_points: float = 2,
    acceptance_criteria: str | None = "Help text is updated and visible in the portal.",
    affected_tables: list[str] | None = None,
) -> Story:
    return Story(
        sys_id="abc123",
        number="STORY0010001",
        short_description=short_description,
        description=description,
        story_points=story_points,
        priority=3,
        state="Ready",
        data_classification=DataClassification.PUBLIC,
        acceptance_criteria=acceptance_criteria,
        affected_tables=["sp_instance"] if affected_tables is None else affected_tables,
    )


def _policy() -> AllowlistPolicy:
    return AllowlistPolicy(
        story_types={StoryType.CONTENT_ONLY},
        tables={"sp_instance", "sys_ui_message"},
        operations={"update"},
        max_points=3,
    )


def test_content_only_story_is_eligible_when_allowlists_pass() -> None:
    result = evaluate_story(
        _story(description="Change the portal help text from Submit to Send."),
        _policy(),
    )

    assert result.decision is EligibilityDecision.ELIGIBLE
    assert result.story_type is StoryType.CONTENT_ONLY
    assert "story type allowed: content_only" in result.reasons
    assert "table allowed: sp_instance" in result.reasons


def test_acl_role_integration_migration_credential_and_delete_stories_reject() -> None:
    descriptions = [
        "Add a new ACL for the intake table.",
        "Create a new admin role and group.",
        "Integrate with an external payment API.",
        "Migrate historical request records.",
        "Store credentials for the downstream service.",
        "Delete obsolete production records.",
    ]

    for description in descriptions:
        result = evaluate_story(_story(description=description), _policy())
        assert result.decision is EligibilityDecision.REJECTED
        assert result.reasons


def test_story_over_three_points_routes_to_manual_review() -> None:
    result = evaluate_story(
        _story(description="Change portal help text.", story_points=5),
        _policy(),
    )

    assert result.decision is EligibilityDecision.MANUAL_REVIEW
    assert "story points exceed max: 5.0 > 3" in result.reasons


def test_missing_acceptance_criteria_routes_to_manual_review() -> None:
    result = evaluate_story(
        _story(description="Change portal help text.", acceptance_criteria=None),
        _policy(),
    )

    assert result.decision is EligibilityDecision.MANUAL_REVIEW
    assert "missing acceptance criteria" in result.reasons


def test_disallowed_table_routes_to_manual_review() -> None:
    result = evaluate_story(
        _story(description="Change portal help text.", affected_tables=["sys_user"]),
        _policy(),
    )

    assert result.decision is EligibilityDecision.MANUAL_REVIEW
    assert "table not allowed: sys_user" in result.reasons


def test_missing_affected_tables_routes_to_manual_review() -> None:
    result = evaluate_story(
        _story(description="Change portal help text.", affected_tables=[]),
        _policy(),
    )

    assert result.decision is EligibilityDecision.MANUAL_REVIEW
    assert "missing affected tables" in result.reasons


def test_disallowed_operation_routes_to_manual_review() -> None:
    result = evaluate_story(
        _story(description="Change portal help text."),
        _policy(),
        proposed_operation="delete",
    )

    assert result.decision is EligibilityDecision.MANUAL_REVIEW
    assert "operation not allowed: delete" in result.reasons


def test_unknown_story_type_routes_to_manual_review() -> None:
    result = evaluate_story(
        _story(
            short_description="Adjust workflow behavior",
            description="Adjust the workflow behavior for request routing.",
        ),
        _policy(),
    )

    assert result.decision is EligibilityDecision.MANUAL_REVIEW
    assert "story type not allowed: unknown" in result.reasons


def test_dictionary_form_story_is_eligible_when_explicitly_allowed() -> None:
    story = _story(
        short_description="Add AI Review Notes field to Story form",
        description=(
            "Add a new custom field to the rm_story table named u_ai_review_notes "
            "and place it on the Story form below Description."
        ),
        affected_tables=["sys_dictionary", "sys_ui_form"],
    )
    policy = AllowlistPolicy(
        story_types={StoryType.DICTIONARY_FORM},
        tables={"sys_dictionary", "sys_ui_form"},
        operations={"insert", "update"},
        max_points=3,
    )

    result = evaluate_story(story, policy, proposed_operation="insert")

    assert result.decision is EligibilityDecision.ELIGIBLE
    assert result.story_type is StoryType.DICTIONARY_FORM
