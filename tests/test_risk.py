from jedi_devproject.risk import RiskInput, calculate_risk_score


def test_optional_custom_dictionary_field_on_form_is_very_low_risk() -> None:
    score = calculate_risk_score(
        RiskInput(
            story_type="dictionary_form",
            affected_tables=["sys_dictionary", "sys_ui_form"],
            target_table="rm_story",
            field_name="u_ai_review_notes",
            mandatory=False,
            has_default=False,
            changes_access_control=False,
            changes_workflow=False,
            changes_integration=False,
            migrates_data=False,
        )
    )

    assert score == 0.12


def test_mandatory_dictionary_field_adds_risk() -> None:
    optional_score = calculate_risk_score(
        RiskInput(
            story_type="dictionary_form",
            affected_tables=["sys_dictionary", "sys_ui_form"],
            target_table="rm_story",
            field_name="u_ai_review_notes",
            mandatory=False,
        )
    )
    mandatory_score = calculate_risk_score(
        RiskInput(
            story_type="dictionary_form",
            affected_tables=["sys_dictionary", "sys_ui_form"],
            target_table="rm_story",
            field_name="u_ai_review_notes",
            mandatory=True,
        )
    )

    assert mandatory_score > optional_score


def test_access_control_workflow_integration_and_migration_drive_high_risk() -> None:
    score = calculate_risk_score(
        RiskInput(
            story_type="dictionary_form",
            affected_tables=["sys_dictionary", "sys_ui_form"],
            target_table="rm_story",
            field_name="u_ai_review_notes",
            changes_access_control=True,
            changes_workflow=True,
            changes_integration=True,
            migrates_data=True,
        )
    )

    assert score == 1.0


def test_non_story_table_and_platform_field_name_add_risk() -> None:
    score = calculate_risk_score(
        RiskInput(
            story_type="dictionary_form",
            affected_tables=["sys_dictionary", "sys_ui_form"],
            target_table="incident",
            field_name="priority_notes",
        )
    )

    assert score == 0.37


def test_default_value_adds_small_risk() -> None:
    score = calculate_risk_score(
        RiskInput(
            story_type="dictionary_form",
            affected_tables=["sys_dictionary", "sys_ui_form"],
            target_table="rm_story",
            field_name="u_ai_review_notes",
            has_default=True,
        )
    )

    assert score == 0.17
