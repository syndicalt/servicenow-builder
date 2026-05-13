from jedi_devproject.enrichment import enrich_story
from jedi_devproject.models import DataClassification, Story


def _story(
    *,
    short_description: str,
    description: str,
    affected_tables: list[str] | None = None,
) -> Story:
    return Story(
        sys_id="abc123",
        number="STORY0010001",
        short_description=short_description,
        description=description,
        story_points=2,
        priority=3,
        state="Ready",
        data_classification=DataClassification.PUBLIC,
        acceptance_criteria="The requested text is updated.",
        affected_tables=[] if affected_tables is None else affected_tables,
    )


def test_portal_help_text_story_infers_sp_instance_with_evidence() -> None:
    result = enrich_story(
        _story(
            short_description="Update portal help text",
            description="Change the request intake portal help text.",
        )
    )

    assert result.enriched_story.affected_tables == ["sp_instance"]
    assert result.inferred_tables == ["sp_instance"]
    assert result.confidence == 0.85
    assert "portal content signal" in result.evidence


def test_notification_story_infers_email_action_table() -> None:
    result = enrich_story(
        _story(
            short_description="Update notification message",
            description="Change the email notification wording sent to requesters.",
        )
    )

    assert result.enriched_story.affected_tables == ["sysevent_email_action"]
    assert result.inferred_tables == ["sysevent_email_action"]
    assert "notification content signal" in result.evidence


def test_dictionary_field_story_infers_sys_dictionary() -> None:
    result = enrich_story(
        _story(
            short_description="Update field label",
            description="Change the dictionary field label for requester phone.",
        )
    )

    assert result.enriched_story.affected_tables == ["sys_dictionary"]
    assert result.inferred_tables == ["sys_dictionary"]
    assert "dictionary field signal" in result.evidence


def test_add_column_and_form_story_infers_dictionary_and_form_layout_tables() -> None:
    result = enrich_story(
        _story(
            short_description="Add AI Review Notes field to Story form",
            description=(
                "Add a new custom field to the rm_story table named u_ai_review_notes "
                "and place it on the Story form below Description."
            ),
        )
    )

    assert result.enriched_story.affected_tables == ["sys_dictionary", "sys_ui_form"]
    assert result.inferred_tables == ["sys_dictionary", "sys_ui_form"]
    assert "dictionary field signal" in result.evidence
    assert "form placement signal" in result.evidence


def test_existing_affected_tables_are_preserved_without_inference() -> None:
    result = enrich_story(
        _story(
            short_description="Update portal help text",
            description="Change the request intake portal help text.",
            affected_tables=["sp_instance"],
        )
    )

    assert result.enriched_story.affected_tables == ["sp_instance"]
    assert result.inferred_tables == []
    assert result.confidence == 1.0
    assert result.evidence == ["affected tables already provided"]


def test_ambiguous_story_remains_without_affected_tables() -> None:
    result = enrich_story(
        _story(
            short_description="Improve request handling",
            description="Make request handling better for users.",
        )
    )

    assert result.enriched_story.affected_tables == []
    assert result.inferred_tables == []
    assert result.confidence == 0.0
    assert "no deterministic table inference" in result.evidence
