from jedi_devproject.bootstrap import plan_bootstrap_fields
from jedi_devproject.servicenow import StoryDictionaryField


def test_bootstrap_plan_only_includes_missing_custom_writeback_fields() -> None:
    plan = plan_bootstrap_fields(
        [
            StoryDictionaryField(
                element="state",
                column_label="State",
                internal_type="choice",
                active=True,
            ),
            StoryDictionaryField(
                element="u_ai_status",
                column_label="AI Status",
                internal_type="string",
                active=True,
            ),
        ]
    )

    assert plan.table == "rm_story"
    assert plan.missing_fields == ["u_ai_build_reference", "u_ai_candidate_artifact"]
    assert [field.element for field in plan.fields_to_create] == [
        "u_ai_build_reference",
        "u_ai_candidate_artifact",
    ]
    assert "state" not in [field.element for field in plan.fields_to_create]
    assert plan.requires_apply_confirmation is True
    assert plan.form_layout_changes == []


def test_bootstrap_plan_is_noop_when_custom_fields_exist() -> None:
    plan = plan_bootstrap_fields(
        [
            StoryDictionaryField(
                element="u_ai_status",
                column_label="AI Status",
                internal_type="string",
                active=True,
            ),
            StoryDictionaryField(
                element="u_ai_build_reference",
                column_label="AI Build Reference",
                internal_type="string",
                active=True,
            ),
            StoryDictionaryField(
                element="u_ai_candidate_artifact",
                column_label="AI Candidate Artifact",
                internal_type="string",
                active=True,
            ),
        ]
    )

    assert plan.missing_fields == []
    assert plan.fields_to_create == []
    assert plan.ready is True
