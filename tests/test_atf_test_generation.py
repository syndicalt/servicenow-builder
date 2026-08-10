from __future__ import annotations

import pytest
from pydantic import ValidationError

from jedi_devproject.atf_test_generation import (
    ATF_GENERATION_FIELD_NON_JSON_DIAGNOSTIC,
    REASON_FORM_PLACEMENT_WITHOUT_DICTIONARY_INSERT,
    REASON_MISSING_REQUIRED_FIELDS,
    REASON_POLICY_ACTION_WITHOUT_POLICY,
    REASON_UNSUPPORTED_OPERATION,
    REASON_UNSUPPORTED_TABLE,
    REASON_VARIABLE_WITHOUT_CATALOG_ITEM,
    STEP_CONFIG_FIELD_STATE_VALIDATION,
    STEP_CONFIG_OPEN_CATALOG_ITEM,
    STEP_CONFIG_OPEN_NEW_FORM,
    STEP_CONFIG_RECORD_INSERT,
    STEP_CONFIG_RECORD_UPDATE,
    STEP_CONFIG_RECORD_VALIDATION,
    STEP_CONFIG_SET_FIELD_VALUES,
    STEP_CONFIG_SET_VARIABLE_VALUES,
    STEP_CONFIG_VARIABLE_STATE_VALIDATION,
    AtfStepCandidate,
    AtfTestCandidate,
    generate_atf_test_plan,
    step_config_sys_id_assumption,
)
from jedi_devproject.models import CandidateChange, CandidateStatus, UpdateSetCandidate
from jedi_devproject.validation_helpers import stable_record_sys_id


def _candidate(changes: list[CandidateChange]) -> UpdateSetCandidate:
    return UpdateSetCandidate(
        story_number="STRY0001",
        name="UPD_STRY0001_Candidate",
        eligibility_decision="eligible",
        eligibility_reasons=[],
        confidence=0.9,
        risk_score=0.1,
        status=CandidateStatus.READY_FOR_REVIEW,
        changes=changes,
    )


def _dictionary_insert() -> CandidateChange:
    return CandidateChange(
        table="sys_dictionary",
        operation="insert",
        fields={
            "name": "rm_story",
            "element": "u_ai_review_notes",
            "column_label": "AI Review Notes",
            "internal_type": "string",
        },
    )


def _form_placement() -> CandidateChange:
    return CandidateChange(
        table="sys_ui_form",
        operation="update",
        fields={"table": "rm_story", "field": "u_ai_review_notes"},
    )


def test_dictionary_insert_with_form_placement_generates_field_test() -> None:
    plan = generate_atf_test_plan(_candidate([_dictionary_insert(), _form_placement()]))

    assert plan is not None
    assert plan.schema_version == "atf-test-plan-v1"
    assert plan.story_number == "STRY0001"
    assert plan.candidate_name == "UPD_STRY0001_Candidate"
    assert plan.not_covered == []
    assert len(plan.tests) == 1
    test = plan.tests[0]
    assert test.name == "ATF STRY0001 field rm_story.u_ai_review_notes"
    assert test.sys_id == stable_record_sys_id("sys_atf_test", "STRY0001", test.name)
    assert [step.step_config_name for step in test.steps] == [
        STEP_CONFIG_RECORD_VALIDATION,
        STEP_CONFIG_OPEN_NEW_FORM,
        STEP_CONFIG_FIELD_STATE_VALIDATION,
    ]
    assert [step.order for step in test.steps] == [1, 2, 3]
    assert test.steps[0].inputs == {
        "execution_context": "server",
        "table": "sys_dictionary",
        "record_conditions": "name=rm_story^element=u_ai_review_notes",
        "assert_type": "record_validated",
    }
    assert test.steps[1].inputs == {
        "execution_context": "client",
        "table": "rm_story",
        "view": "default",
    }
    assert test.steps[2].inputs == {
        "execution_context": "client",
        "table": "rm_story",
        "field_states": {"u_ai_review_notes": {"visible": True}},
    }
    assert test.steps[0].sys_id == stable_record_sys_id(
        "sys_atf_step", test.name, "1", STEP_CONFIG_RECORD_VALIDATION
    )


def test_dictionary_insert_without_form_placement_only_validates_field_exists() -> None:
    plan = generate_atf_test_plan(_candidate([_dictionary_insert()]))

    assert plan is not None
    assert len(plan.tests) == 1
    assert [step.step_config_name for step in plan.tests[0].steps] == [
        STEP_CONFIG_RECORD_VALIDATION
    ]


def test_ui_policy_with_action_generates_form_steps() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [
                CandidateChange(
                    table="sys_ui_policy",
                    operation="insert",
                    fields={
                        "short_description": "Assignment Group Required",
                        "table": "incident",
                        "conditions": "category=software",
                        "reverse_if_false": True,
                    },
                ),
                CandidateChange(
                    table="sys_ui_policy_action",
                    operation="insert",
                    fields={
                        "table": "incident",
                        "field": "assignment_group",
                        "mandatory": "true",
                        "visible": "true",
                        "disabled": "ignore",
                    },
                ),
            ]
        )
    )

    assert plan is not None
    assert plan.not_covered == []
    assert len(plan.tests) == 1
    test = plan.tests[0]
    assert test.name == "ATF STRY0001 ui policy Assignment Group Required"
    assert [step.step_config_name for step in test.steps] == [
        STEP_CONFIG_OPEN_NEW_FORM,
        STEP_CONFIG_SET_FIELD_VALUES,
        STEP_CONFIG_FIELD_STATE_VALIDATION,
    ]
    assert test.steps[1].inputs == {
        "execution_context": "client",
        "table": "incident",
        "field_values": {"category": "software"},
    }
    assert test.steps[2].inputs == {
        "execution_context": "client",
        "table": "incident",
        "field_states": {"assignment_group": {"visible": True, "mandatory": True}},
    }


def test_ui_policy_with_unconvertible_condition_records_assumption() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [
                CandidateChange(
                    table="sys_ui_policy",
                    operation="insert",
                    fields={
                        "short_description": "Priority Guard",
                        "table": "incident",
                        "conditions": "priority!=1^ORcategory=hardware^EQ",
                    },
                ),
                CandidateChange(
                    table="sys_ui_policy_action",
                    operation="insert",
                    fields={"field": "urgency", "read_only": "true", "visible": "false"},
                ),
            ]
        )
    )

    assert plan is not None
    test = plan.tests[0]
    assert [step.step_config_name for step in test.steps] == [
        STEP_CONFIG_OPEN_NEW_FORM,
        STEP_CONFIG_FIELD_STATE_VALIDATION,
    ]
    assert test.steps[1].inputs["field_states"] == {
        "urgency": {"visible": False, "read_only": True}
    }
    assert any(
        "UI policy Priority Guard" in assumption and "priority!=1" in assumption
        for assumption in plan.evidence_assumptions
    )


def test_catalog_ui_policy_generates_catalog_item_steps() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [
                CandidateChange(
                    table="catalog_ui_policy",
                    operation="insert",
                    fields={
                        "short_description": "Show justification",
                        "catalog_item": "Laptop Request",
                        "catalog_conditions": "approval_needed=yes",
                    },
                ),
                CandidateChange(
                    table="catalog_ui_policy_action",
                    operation="insert",
                    fields={
                        "variable": "justification",
                        "visible": "true",
                        "mandatory": "true",
                    },
                ),
            ]
        )
    )

    assert plan is not None
    assert plan.not_covered == []
    test = plan.tests[0]
    assert test.name == "ATF STRY0001 catalog ui policy Show justification"
    assert [step.step_config_name for step in test.steps] == [
        STEP_CONFIG_OPEN_CATALOG_ITEM,
        STEP_CONFIG_SET_VARIABLE_VALUES,
        STEP_CONFIG_VARIABLE_STATE_VALIDATION,
    ]
    assert test.steps[0].inputs == {
        "execution_context": "client",
        "catalog_item": "Laptop Request",
    }
    assert test.steps[1].inputs == {
        "execution_context": "client",
        "table": "Laptop Request",
        "variable_values": {"approval_needed": "yes"},
    }
    assert test.steps[2].inputs == {
        "execution_context": "client",
        "catalog_item": "Laptop Request",
        "variable_states": {"justification": {"visible": True, "mandatory": True}},
    }


def test_catalog_item_with_variables_generates_presence_assertions() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [
                CandidateChange(
                    table="sc_cat_item",
                    operation="insert",
                    fields={"name": "Laptop Request", "short_description": "Order a laptop"},
                ),
                CandidateChange(
                    table="item_option_new",
                    operation="insert",
                    fields={"name": "business_need", "mandatory": "true"},
                ),
                CandidateChange(
                    table="item_option_new",
                    operation="insert",
                    fields={"name": "manager_approval"},
                ),
            ]
        )
    )

    assert plan is not None
    assert plan.not_covered == []
    test = plan.tests[0]
    assert [step.step_config_name for step in test.steps] == [
        STEP_CONFIG_OPEN_CATALOG_ITEM,
        STEP_CONFIG_VARIABLE_STATE_VALIDATION,
    ]
    assert test.steps[1].inputs["variable_states"] == {
        "business_need": {"visible": True, "mandatory": True},
        "manager_approval": {"visible": True},
    }


def test_business_rule_update_timing_generates_insert_update_validation() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [
                CandidateChange(
                    table="sys_script",
                    operation="insert",
                    fields={
                        "name": "Incident Priority Note",
                        "collection": "incident",
                        "when": "before",
                        "action_insert": False,
                        "action_update": True,
                        "filter_condition": "priority=1",
                        "fields_written": ["work_notes", "u_escalated"],
                    },
                )
            ]
        )
    )

    assert plan is not None
    assert plan.not_covered == []
    test = plan.tests[0]
    assert test.name == "ATF STRY0001 business rule Incident Priority Note"
    assert [step.step_config_name for step in test.steps] == [
        STEP_CONFIG_RECORD_INSERT,
        STEP_CONFIG_RECORD_UPDATE,
        STEP_CONFIG_RECORD_VALIDATION,
    ]
    insert_step, update_step, validation_step = test.steps
    assert insert_step.inputs == {
        "execution_context": "server",
        "table": "incident",
        "field_values": {"priority": "1"},
    }
    assert update_step.inputs["record_source_step_sys_id"] == insert_step.sys_id
    assert validation_step.inputs == {
        "execution_context": "server",
        "table": "incident",
        "record_source_step_sys_id": update_step.sys_id,
        "record_conditions": "work_notesISNOTEMPTY^u_escalatedISNOTEMPTY",
        "assert_type": "record_validated",
    }


def test_atf_test_plan_rejects_non_json_candidate_field_without_leak() -> None:
    class SecretBearingAtfField:
        def __str__(self) -> str:
            return "leaked-atf-secret"

    with pytest.raises(ValueError) as exc_info:
        generate_atf_test_plan(
            _candidate(
                [
                    CandidateChange(
                        table="sys_script",
                        operation="insert",
                        fields={
                            "name": SecretBearingAtfField(),
                            "collection": "incident",
                            "action_insert": True,
                            "fields_written": ["work_notes"],
                        },
                    )
                ]
            )
        )

    message = str(exc_info.value)
    assert message == ATF_GENERATION_FIELD_NON_JSON_DIAGNOSTIC
    assert "leaked-atf-secret" not in message
    assert "SecretBearingAtfField" not in message


def test_atf_test_plan_rejects_string_subclass_candidate_field_without_leak() -> None:
    class SecretBearingAtfText(str):
        def strip(self, chars: str | None = None) -> str:
            raise RuntimeError("client_secret=atf-string-subclass")

    with pytest.raises(ValueError) as exc_info:
        generate_atf_test_plan(
            _candidate(
                [
                    CandidateChange(
                        table="sys_script",
                        operation="insert",
                        fields={
                            "name": "Set work notes",
                            "collection": "incident",
                            "action_insert": SecretBearingAtfText("true"),
                            "fields_written": ["work_notes"],
                        },
                    )
                ]
            )
        )

    message = str(exc_info.value)
    assert message == ATF_GENERATION_FIELD_NON_JSON_DIAGNOSTIC
    assert "atf-string-subclass" not in message
    assert "SecretBearingAtfText" not in message


def test_atf_test_plan_rejects_scalar_subclass_candidate_field_without_leak() -> None:
    class SecretBearingAtfOrder(int):
        def __str__(self) -> str:
            raise RuntimeError("client_secret=atf-scalar")

    with pytest.raises(ValueError) as exc_info:
        generate_atf_test_plan(
            _candidate(
                [
                    CandidateChange(
                        table="sys_script",
                        operation="insert",
                        fields={
                            "name": "Set work notes",
                            "collection": "incident",
                            "action_insert": SecretBearingAtfOrder(1),
                            "fields_written": ["work_notes"],
                        },
                    )
                ]
            )
        )

    message = str(exc_info.value)
    assert message == ATF_GENERATION_FIELD_NON_JSON_DIAGNOSTIC
    assert exc_info.value.__cause__ is None
    assert "atf-scalar" not in message
    assert "SecretBearingAtfOrder" not in message


def test_atf_test_plan_rejects_list_subclass_candidate_field_without_leak() -> None:
    class SecretBearingAtfList(list[object]):
        def __iter__(self):  # type: ignore[no-untyped-def]
            raise RuntimeError("client_secret=atf-list")

    with pytest.raises(ValueError) as exc_info:
        generate_atf_test_plan(
            _candidate(
                [
                    CandidateChange(
                        table="sys_script",
                        operation="insert",
                        fields={
                            "name": "Set work notes",
                            "collection": "incident",
                            "action_insert": True,
                            "fields_written": SecretBearingAtfList(["work_notes"]),
                        },
                    )
                ]
            )
        )

    message = str(exc_info.value)
    assert message == ATF_GENERATION_FIELD_NON_JSON_DIAGNOSTIC
    assert exc_info.value.__cause__ is None
    assert "atf-list" not in message
    assert "SecretBearingAtfList" not in message


def test_business_rule_insert_timing_skips_record_update_step() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [
                CandidateChange(
                    table="sys_script",
                    operation="insert",
                    fields={
                        "name": "Incident Intake Note",
                        "collection": "incident",
                        "action_insert": True,
                        "action_update": False,
                        "filter_condition": "priority changes to 1",
                        "fields_written": ["work_notes"],
                    },
                )
            ]
        )
    )

    assert plan is not None
    test = plan.tests[0]
    assert [step.step_config_name for step in test.steps] == [
        STEP_CONFIG_RECORD_INSERT,
        STEP_CONFIG_RECORD_VALIDATION,
    ]
    assert test.steps[0].inputs["field_values"] == {}
    assert test.steps[1].inputs["record_source_step_sys_id"] == test.steps[0].sys_id
    assert any(
        "Incident Intake Note" in assumption and "priority changes to 1" in assumption
        for assumption in plan.evidence_assumptions
    )


def test_business_rule_without_declared_fields_written_is_not_covered() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [
                CandidateChange(
                    table="sys_script",
                    operation="insert",
                    fields={"name": "Opaque Rule", "collection": "incident"},
                )
            ]
        )
    )

    assert plan is not None
    assert plan.tests == []
    assert len(plan.not_covered) == 1
    assert plan.not_covered[0].reason_code == REASON_MISSING_REQUIRED_FIELDS


def test_unknown_table_and_unsupported_operation_are_not_covered() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [
                CandidateChange(table="cmdb_identifier", operation="update", fields={}),
                CandidateChange(
                    table="sys_dictionary",
                    operation="delete",
                    fields={"name": "rm_story", "element": "u_old"},
                ),
            ]
        )
    )

    assert plan is not None
    assert plan.tests == []
    assert [(entry.table, entry.reason_code) for entry in plan.not_covered] == [
        ("cmdb_identifier", REASON_UNSUPPORTED_TABLE),
        ("sys_dictionary", REASON_UNSUPPORTED_OPERATION),
    ]
    assert plan.evidence_assumptions == []


def test_orphaned_companion_changes_are_not_covered_with_stable_codes() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [
                CandidateChange(
                    table="sys_ui_form",
                    operation="update",
                    fields={"table": "incident", "field": "u_field"},
                ),
                CandidateChange(
                    table="sys_ui_policy_action",
                    operation="insert",
                    fields={"field": "urgency", "visible": "true"},
                ),
                CandidateChange(
                    table="item_option_new",
                    operation="insert",
                    fields={"name": "justification"},
                ),
            ]
        )
    )

    assert plan is not None
    assert plan.tests == []
    assert [entry.reason_code for entry in plan.not_covered] == [
        REASON_FORM_PLACEMENT_WITHOUT_DICTIONARY_INSERT,
        REASON_POLICY_ACTION_WITHOUT_POLICY,
        REASON_VARIABLE_WITHOUT_CATALOG_ITEM,
    ]


def test_ui_policy_without_actions_is_not_covered() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [
                CandidateChange(
                    table="sys_ui_policy",
                    operation="insert",
                    fields={"short_description": "Lonely Policy", "table": "incident"},
                )
            ]
        )
    )

    assert plan is not None
    assert plan.tests == []
    assert plan.not_covered[0].reason_code == REASON_MISSING_REQUIRED_FIELDS


def test_mixed_candidate_covers_each_change_exactly_once() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [
                _dictionary_insert(),
                _form_placement(),
                CandidateChange(
                    table="sys_ui_policy",
                    operation="insert",
                    fields={
                        "short_description": "Notes Guard",
                        "table": "rm_story",
                        "conditions": "state=1",
                    },
                ),
                CandidateChange(
                    table="sys_ui_policy_action",
                    operation="insert",
                    fields={"field": "u_ai_review_notes", "visible": "true"},
                ),
                CandidateChange(table="wf_workflow", operation="insert", fields={}),
            ]
        )
    )

    assert plan is not None
    assert [test.name for test in plan.tests] == [
        "ATF STRY0001 field rm_story.u_ai_review_notes",
        "ATF STRY0001 ui policy Notes Guard",
    ]
    assert [(entry.table, entry.reason_code) for entry in plan.not_covered] == [
        ("wf_workflow", REASON_UNSUPPORTED_TABLE)
    ]


def test_plan_generation_is_deterministic() -> None:
    candidate = _candidate(
        [
            _dictionary_insert(),
            _form_placement(),
            CandidateChange(
                table="sys_script",
                operation="insert",
                fields={
                    "name": "Rule",
                    "collection": "incident",
                    "action_update": True,
                    "fields_written": ["work_notes"],
                },
            ),
        ]
    )

    first = generate_atf_test_plan(candidate)
    second = generate_atf_test_plan(candidate)

    assert first is not None and second is not None
    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_candidate_without_changes_produces_no_plan() -> None:
    assert generate_atf_test_plan(_candidate([])) is None


def test_plan_records_step_config_evidence_assumptions() -> None:
    plan = generate_atf_test_plan(_candidate([_dictionary_insert(), _form_placement()]))

    assert plan is not None
    used_names = sorted({step.step_config_name for test in plan.tests for step in test.steps})
    for name in used_names:
        placeholder = step_config_sys_id_assumption(name)
        assert placeholder == stable_record_sys_id("sys_atf_step_config", name)
        assert any(
            f"'{name}'" in assumption and placeholder in assumption
            for assumption in plan.evidence_assumptions
        )
    assert any(
        "input variable contract" in assumption for assumption in plan.evidence_assumptions
    )
    for test in plan.tests:
        for step in test.steps:
            assert step.step_config_sys_id_assumption == step_config_sys_id_assumption(
                step.step_config_name
            )


def test_no_scripted_step_configs_are_ever_proposed() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [
                _dictionary_insert(),
                _form_placement(),
                CandidateChange(
                    table="sys_script",
                    operation="insert",
                    fields={
                        "name": "Rule",
                        "collection": "incident",
                        "action_insert": True,
                        "fields_written": ["work_notes"],
                    },
                ),
            ]
        )
    )

    assert plan is not None
    for test in plan.tests:
        for step in test.steps:
            assert "script" not in step.step_config_name.lower()


def test_step_and_test_models_reject_empty_text() -> None:
    with pytest.raises(ValidationError):
        AtfStepCandidate(
            sys_id="a" * 32,
            order=1,
            step_config_name=STEP_CONFIG_OPEN_NEW_FORM,
            step_config_sys_id_assumption="b" * 32,
            description="   ",
        )
    with pytest.raises(ValidationError):
        AtfTestCandidate(sys_id="a" * 32, name="  ", description="valid", steps=[])


def test_dictionary_insert_missing_element_is_not_covered() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [CandidateChange(table="sys_dictionary", operation="insert", fields={"name": "task"})]
        )
    )

    assert plan is not None
    assert plan.tests == []
    assert plan.not_covered[0].reason_code == REASON_MISSING_REQUIRED_FIELDS


def test_non_insert_operations_on_supported_tables_are_not_covered() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [
                CandidateChange(table="sys_ui_policy", operation="update", fields={}),
                CandidateChange(table="catalog_ui_policy", operation="delete", fields={}),
                CandidateChange(table="sc_cat_item", operation="update", fields={}),
                CandidateChange(table="sys_script", operation="update", fields={}),
            ]
        )
    )

    assert plan is not None
    assert plan.tests == []
    assert [entry.reason_code for entry in plan.not_covered] == [
        REASON_UNSUPPORTED_OPERATION
    ] * 4


def test_catalog_ui_policy_without_resolvable_item_is_not_covered() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [
                CandidateChange(
                    table="catalog_ui_policy",
                    operation="insert",
                    fields={"short_description": "Orphan Policy"},
                ),
                CandidateChange(
                    table="catalog_ui_policy_action",
                    operation="insert",
                    fields={"variable": "justification", "visible": "true"},
                ),
            ]
        )
    )

    assert plan is not None
    assert plan.tests == []
    assert plan.not_covered[0].reason_code == REASON_MISSING_REQUIRED_FIELDS


def test_catalog_ui_policy_resolves_item_from_sc_cat_item_change() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [
                CandidateChange(
                    table="sc_cat_item",
                    operation="insert",
                    fields={"name": "Laptop Request"},
                ),
                CandidateChange(
                    table="item_option_new",
                    operation="insert",
                    fields={"name": "justification"},
                ),
                CandidateChange(
                    table="catalog_ui_policy",
                    operation="insert",
                    fields={
                        "short_description": "Show justification",
                        "conditions": "approval_needed=yes",
                    },
                ),
                CandidateChange(
                    table="catalog_ui_policy_action",
                    operation="insert",
                    fields={"variable": "justification", "visible": "true"},
                ),
            ]
        )
    )

    assert plan is not None
    assert plan.not_covered == []
    assert [test.name for test in plan.tests] == [
        "ATF STRY0001 catalog item Laptop Request",
        "ATF STRY0001 catalog ui policy Show justification",
    ]
    policy_test = plan.tests[1]
    assert policy_test.steps[0].inputs["catalog_item"] == "Laptop Request"


def test_catalog_item_missing_name_is_not_covered() -> None:
    plan = generate_atf_test_plan(
        _candidate([CandidateChange(table="sc_cat_item", operation="insert", fields={})])
    )

    assert plan is not None
    assert plan.tests == []
    assert plan.not_covered[0].reason_code == REASON_MISSING_REQUIRED_FIELDS


def test_catalog_item_with_unnamed_variable_reports_it_and_skips_state_step() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [
                CandidateChange(
                    table="sc_cat_item",
                    operation="insert",
                    fields={"name": "Laptop Request"},
                ),
                CandidateChange(table="item_option_new", operation="insert", fields={}),
            ]
        )
    )

    assert plan is not None
    assert len(plan.tests) == 1
    assert [step.step_config_name for step in plan.tests[0].steps] == [
        STEP_CONFIG_OPEN_CATALOG_ITEM
    ]
    assert plan.not_covered[0].table == "item_option_new"
    assert plan.not_covered[0].reason_code == REASON_MISSING_REQUIRED_FIELDS


def test_business_rule_missing_name_is_not_covered() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [
                CandidateChange(
                    table="sys_script",
                    operation="insert",
                    fields={"collection": "incident", "fields_written": ["work_notes"]},
                )
            ]
        )
    )

    assert plan is not None
    assert plan.tests == []
    assert plan.not_covered[0].reason_code == REASON_MISSING_REQUIRED_FIELDS


def test_equality_condition_with_empty_value_is_reported_not_converted() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [
                CandidateChange(
                    table="sys_ui_policy",
                    operation="insert",
                    fields={
                        "short_description": "Empty Value Guard",
                        "table": "incident",
                        "conditions": "category=",
                    },
                ),
                CandidateChange(
                    table="sys_ui_policy_action",
                    operation="insert",
                    fields={"field": "urgency", "visible": "true"},
                ),
            ]
        )
    )

    assert plan is not None
    test = plan.tests[0]
    assert [step.step_config_name for step in test.steps] == [
        STEP_CONFIG_OPEN_NEW_FORM,
        STEP_CONFIG_FIELD_STATE_VALIDATION,
    ]
    assert any("category=" in assumption for assumption in plan.evidence_assumptions)


def test_catalog_item_without_variables_only_opens_the_item() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [CandidateChange(table="sc_cat_item", operation="insert", fields={"name": "Item"})]
        )
    )

    assert plan is not None
    assert [step.step_config_name for step in plan.tests[0].steps] == [
        STEP_CONFIG_OPEN_CATALOG_ITEM
    ]


def test_form_placement_for_other_field_is_not_consumed_by_field_test() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [
                _dictionary_insert(),
                CandidateChange(
                    table="sys_ui_form",
                    operation="update",
                    fields={"table": "rm_story", "field": "u_other_field"},
                ),
            ]
        )
    )

    assert plan is not None
    assert [step.step_config_name for step in plan.tests[0].steps] == [
        STEP_CONFIG_RECORD_VALIDATION
    ]
    assert plan.not_covered[0].reason_code == (
        REASON_FORM_PLACEMENT_WITHOUT_DICTIONARY_INSERT
    )


def test_actions_without_names_or_states_are_excluded_from_field_states() -> None:
    plan = generate_atf_test_plan(
        _candidate(
            [
                CandidateChange(
                    table="sys_ui_policy",
                    operation="insert",
                    fields={
                        "short_description": "Sparse Actions",
                        "table": "incident",
                        "conditions": "category=software",
                    },
                ),
                CandidateChange(
                    table="sys_ui_policy_action",
                    operation="insert",
                    fields={"visible": "true"},
                ),
                CandidateChange(
                    table="sys_ui_policy_action",
                    operation="insert",
                    fields={"field": "urgency", "visible": "ignore"},
                ),
                CandidateChange(
                    table="sys_ui_policy_action",
                    operation="insert",
                    fields={"field": "impact", "visible": "true"},
                ),
            ]
        )
    )

    assert plan is not None
    validation_step = plan.tests[0].steps[-1]
    assert validation_step.inputs["field_states"] == {"impact": {"visible": True}}
