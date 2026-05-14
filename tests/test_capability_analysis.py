from jedi_devproject.capabilities import Capability, SuitabilityOutcome
from jedi_devproject.capability_analysis import analyze_story_capabilities
from jedi_devproject.models import DataClassification, Story


def _story(
    *,
    short_description: str,
    description: str,
    acceptance_criteria: str,
    number: str = "STRY0010001",
    story_points: float = 2,
) -> Story:
    return Story(
        sys_id="story-sys-id",
        number=number,
        short_description=short_description,
        description=description,
        acceptance_criteria=acceptance_criteria,
        story_points=story_points,
        priority=4,
        state="Ready",
        data_classification=DataClassification.PUBLIC,
    )


def test_incident_field_story_is_automated_dictionary_form() -> None:
    assessment = analyze_story_capabilities(
        _story(
            short_description="Add a New Field to the Incident Form",
            description=(
                "As an incident manager, I would like a new field added to the "
                "Incident form.\n\n- Field Name: Antics\n- Field Type: String\n"
                "- Length: 4000"
            ),
            acceptance_criteria=(
                "- A new field labeled Antics exists on the incident form.\n"
                "- The field is placed below the Description field.\n"
                "- All incident users are able to read and write to the Antics field."
            ),
        )
    )

    assert assessment.outcome is SuitabilityOutcome.AUTOMATED_BUILD
    assert assessment.intent is not None
    assert assessment.intent.target_table == "incident"
    assert assessment.intent.field_label == "Antics"
    assert assessment.intent.field_name == "u_antics"
    assert assessment.intent.field_type == "string"
    assert assessment.intent.max_length == 4000
    assert assessment.intent.placement_anchor == "description"
    assert assessment.intent.placement_position == "below"
    assert assessment.capabilities == {
        Capability.DICTIONARY_FIELD_CREATE,
        Capability.FIELD_LABEL_CREATE,
        Capability.FORM_LAYOUT_PLACE_FIELD,
    }


def test_story_field_story_remains_automated_dictionary_form() -> None:
    assessment = analyze_story_capabilities(
        _story(
            number="STRY0010013",
            short_description="Add AI Review Notes field to Story form",
            description=(
                "Add a new custom field to the rm_story table named u_ai_review_notes "
                "and place it on the Story form below Description."
            ),
            acceptance_criteria="The AI Review Notes field stores review notes.",
        )
    )

    assert assessment.outcome is SuitabilityOutcome.AUTOMATED_BUILD
    assert assessment.intent is not None
    assert assessment.intent.target_table == "rm_story"
    assert assessment.intent.field_name == "u_ai_review_notes"


def test_missing_target_table_needs_clarification() -> None:
    assessment = analyze_story_capabilities(
        _story(
            short_description="Add a new field",
            description="Add a string field named Comments below Description.",
            acceptance_criteria="The field is visible on the form.",
        )
    )

    assert assessment.outcome is SuitabilityOutcome.NEEDS_CLARIFICATION
    assert "target table" in assessment.missing_details


def test_acl_requirement_is_unsupported_capability() -> None:
    assessment = analyze_story_capabilities(
        _story(
            short_description="Add restricted Incident field",
            description=(
                "Add a string field named Security Notes to the Incident form and "
                "create an ACL so only admins can write it."
            ),
            acceptance_criteria="Only admins can write Security Notes.",
        )
    )

    assert assessment.outcome is SuitabilityOutcome.UNSUPPORTED_CAPABILITY
    assert Capability.ACL_MODIFY in assessment.unsupported_capabilities


def test_high_point_story_routes_to_manual_developer_build() -> None:
    assessment = analyze_story_capabilities(
        _story(
            short_description="Add incident automation",
            description="Add a field to the Incident form and update assignment workflow.",
            acceptance_criteria="The workflow assigns incidents to the right group.",
            story_points=8,
        )
    )

    assert assessment.outcome is SuitabilityOutcome.MANUAL_DEVELOPER_BUILD
    assert "story points exceed max: 8.0 > 3" in assessment.reasons
