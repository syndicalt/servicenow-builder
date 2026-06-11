from __future__ import annotations

import pytest

from jedi_devproject.catalog_ui_policy_generation import (
    CatalogUiPolicyActionIntent,
    CatalogUiPolicyIntent,
    catalog_ui_policy_condition_variables,
    catalog_ui_policy_customer_updates,
    parse_catalog_ui_policy_conditions,
)
from jedi_devproject.models import CandidateChange

_VARIABLE_SYS_IDS = {
    "needs_schedule": "needs-schedule-sys-id",
    "start_date": "start-date-sys-id",
    "end_date": "end-date-sys-id",
}


def _policy_change(**field_overrides: object) -> CandidateChange:
    fields: dict[str, object] = {
        "short_description": "Show schedule",
        "catalog_conditions": "needs_schedule=yes",
        "reverse_if_false": "true",
        "on_load": "true",
        "order": "100",
    }
    fields.update(field_overrides)
    return CandidateChange(
        table="catalog_ui_policy",
        operation="insert",
        fields=fields,
        rationale="Show the schedule section when requested.",
    )


def _action_change(**field_overrides: object) -> CandidateChange:
    fields: dict[str, object] = {
        "ui_policy": "Show schedule",
        "variable": "start_date",
        "visible": "true",
        "mandatory": "true",
    }
    fields.update(field_overrides)
    return CandidateChange(
        table="catalog_ui_policy_action",
        operation="insert",
        fields=fields,
        rationale="Reveal and require the start date.",
    )


def _updates(changes: list[CandidateChange]) -> list[dict[str, object]]:
    return catalog_ui_policy_customer_updates(
        changes=changes,
        remote_update_set_sys_id="remote-update-set-sys-id",
        catalog_item_name="Request Temporary Badge",
        catalog_item_sys_id="catalog-item-sys-id",
        variable_sys_ids=_VARIABLE_SYS_IDS,
    )


def test_catalog_ui_policy_builds_policy_and_action_payloads() -> None:
    updates = _updates([_policy_change(), _action_change()])

    assert [update["type"] for update in updates] == [
        "Catalog UI Policy",
        "Catalog UI Policy Action",
    ]
    policy_payload = str(updates[0]["payload"])
    assert '<record_update table="catalog_ui_policy">' in policy_payload
    assert (
        "<catalog_conditions>IO:needs-schedule-sys-id=yes^EQ</catalog_conditions>"
        in policy_payload
    )
    assert (
        '<catalog_item display_value="Request Temporary Badge">'
        "catalog-item-sys-id</catalog_item>"
    ) in policy_payload
    assert "<short_description>Show schedule</short_description>" in policy_payload
    assert "<run_scripts>false</run_scripts>" in policy_payload
    assert "<script_false/><script_true/>" in policy_payload
    assert "<reverse_if_false>true</reverse_if_false>" in policy_payload
    assert "<applies_catalog>true</applies_catalog>" in policy_payload
    assert "<applies_req_item>true</applies_req_item>" in policy_payload
    assert "<applies_sc_task>false</applies_sc_task>" in policy_payload
    assert "<sys_class_name>catalog_ui_policy</sys_class_name>" in policy_payload

    action_payload = str(updates[1]["payload"])
    assert '<record_update table="catalog_ui_policy_action">' in action_payload
    assert (
        '<catalog_variable display_value="start_date">'
        "IO:start-date-sys-id</catalog_variable>"
    ) in action_payload
    assert "<variable>start_date</variable>" in action_payload
    assert "<visible>true</visible>" in action_payload
    assert "<mandatory>true</mandatory>" in action_payload
    assert "<disabled>ignore</disabled>" in action_payload
    assert "<cleared>false</cleared>" in action_payload
    assert 'ui_policy display_value="Show schedule"' in action_payload
    assert str(updates[1]["name"]).endswith("start_date_required_visible")


def test_catalog_ui_policy_payloads_are_deterministic() -> None:
    first = _updates([_policy_change(), _action_change()])
    second = _updates([_policy_change(), _action_change()])

    assert first == second


def test_catalog_ui_policy_renders_or_join_and_unary_operators() -> None:
    updates = _updates(
        [
            _policy_change(
                catalog_conditions="needs_schedule=yes^ORstart_dateISNOTEMPTY^end_dateISEMPTY",
            ),
            _action_change(),
        ]
    )

    policy_payload = str(updates[0]["payload"])
    assert (
        "<catalog_conditions>IO:needs-schedule-sys-id=yes"
        "^ORIO:start-date-sys-idISNOTEMPTY"
        "^IO:end-date-sys-idISEMPTY^EQ</catalog_conditions>"
    ) in policy_payload


def test_catalog_ui_policy_groups_actions_by_named_policy() -> None:
    updates = _updates(
        [
            _policy_change(),
            _policy_change(
                short_description="Hide end date",
                catalog_conditions="needs_schedule=no",
            ),
            _action_change(),
            _action_change(ui_policy="Hide end date", variable="end_date", visible="false"),
        ]
    )

    assert [update["target_name"] for update in updates] == [
        "Request Temporary Badge.Show schedule",
        "Show schedule.start_date",
        "Request Temporary Badge.Hide end date",
        "Hide end date.end_date",
    ]


def test_catalog_ui_policy_rejects_unsupported_tables() -> None:
    with pytest.raises(ValueError, match="unsupported tables: sys_ui_policy"):
        _updates(
            [
                _policy_change(),
                _action_change(),
                CandidateChange(
                    table="sys_ui_policy",
                    operation="insert",
                    fields={},
                    rationale="Wrong surface.",
                ),
            ]
        )


def test_catalog_ui_policy_requires_policy_and_action_changes() -> None:
    with pytest.raises(ValueError, match="requires a catalog_ui_policy change"):
        _updates([_action_change()])
    with pytest.raises(ValueError, match="requires at least one catalog_ui_policy_action change"):
        _updates([_policy_change()])


def test_catalog_ui_policy_supports_insert_only() -> None:
    with pytest.raises(ValueError, match="supports policy insert only"):
        _updates(
            [_policy_change().model_copy(update={"operation": "update"}), _action_change()]
        )
    with pytest.raises(ValueError, match="supports action insert only"):
        _updates(
            [_policy_change(), _action_change().model_copy(update={"operation": "update"})]
        )


def test_catalog_ui_policy_rejects_duplicate_policy_titles() -> None:
    with pytest.raises(ValueError, match="duplicate policy: Show schedule"):
        _updates([_policy_change(), _policy_change(), _action_change()])


def test_catalog_ui_policy_action_must_resolve_its_policy() -> None:
    with pytest.raises(ValueError, match="references unknown policy: Other policy"):
        _updates([_policy_change(), _action_change(ui_policy="Other policy")])
    with pytest.raises(ValueError, match="must name its policy"):
        _updates(
            [
                _policy_change(),
                _policy_change(short_description="Hide end date"),
                _action_change(ui_policy=""),
            ]
        )


def test_catalog_ui_policy_unnamed_action_defaults_to_single_policy() -> None:
    updates = _updates([_policy_change(), _action_change(ui_policy="")])

    assert str(updates[1]["target_name"]) == "Show schedule.start_date"


def test_catalog_ui_policy_rejects_condition_on_unknown_variable() -> None:
    with pytest.raises(
        ValueError,
        match="condition references a variable .* not .* own variables: badge_color",
    ):
        _updates([_policy_change(catalog_conditions="badge_color=red"), _action_change()])


def test_catalog_ui_policy_rejects_action_on_unknown_variable() -> None:
    with pytest.raises(
        ValueError,
        match="action references a variable .* not .* own variables: badge_color",
    ):
        _updates([_policy_change(), _action_change(variable="badge_color")])


@pytest.mark.parametrize(
    "condition",
    [
        "",
        "   ",
        "needs_schedule",
        "needs_schedule=",
        "needs_scheduleISEMPTYtrue",
        "needs_schedule>yes",
        "Needs_Schedule=yes",
        "javascript:gs.getUser()",
    ],
)
def test_catalog_ui_policy_rejects_non_declarative_conditions(condition: str) -> None:
    with pytest.raises(
        ValueError,
        match="catalog UI policy|must not be empty|forbidden UI Policy token",
    ):
        _updates([_policy_change(catalog_conditions=condition), _action_change()])


def test_catalog_ui_policy_rejects_forbidden_condition_tokens() -> None:
    with pytest.raises(ValueError, match="forbidden UI Policy token"):
        parse_catalog_ui_policy_conditions("needs_schedule=https://example.com")


def test_catalog_ui_policy_rejects_run_scripts_and_policy_scripts() -> None:
    with pytest.raises(ValueError, match="run_scripts must be false"):
        _updates([_policy_change(run_scripts="true"), _action_change()])
    with pytest.raises(ValueError, match="scripts are not supported"):
        _updates(
            [_policy_change(script_true="g_form.setValue('x', 'y');"), _action_change()]
        )


def test_catalog_ui_policy_rejects_action_without_effect() -> None:
    with pytest.raises(ValueError, match="must set visible, mandatory, read-only, or cleared"):
        _updates(
            [
                _policy_change(),
                _action_change(visible="ignore", mandatory="ignore"),
            ]
        )


def test_catalog_ui_policy_rejects_invalid_tristate() -> None:
    with pytest.raises(ValueError, match="must be true, false, or ignore"):
        _updates([_policy_change(), _action_change(mandatory="sometimes")])


def test_catalog_ui_policy_action_accepts_read_only_alias_and_cleared() -> None:
    updates = _updates(
        [
            _policy_change(),
            _action_change(
                visible="ignore",
                mandatory="ignore",
                read_only="true",
                cleared="true",
            ),
        ]
    )

    action_payload = str(updates[1]["payload"])
    assert "<disabled>true</disabled>" in action_payload
    assert "<cleared>true</cleared>" in action_payload
    assert str(updates[1]["name"]).endswith("read_only_cleared")


def test_condition_variable_helper_returns_referenced_variables() -> None:
    assert catalog_ui_policy_condition_variables(
        "needs_schedule=yes^ORstart_dateISEMPTY"
    ) == ["needs_schedule", "start_date"]


def test_catalog_ui_policy_intent_requires_actions_and_matching_action_policy() -> None:
    action = CatalogUiPolicyActionIntent(variable="start_date", visible="true")
    with pytest.raises(ValueError, match="requires at least one action"):
        CatalogUiPolicyIntent(
            catalog_item_name="Request Temporary Badge",
            policy_name="Show schedule",
            conditions="needs_schedule=yes",
            actions=[],
        )
    with pytest.raises(ValueError, match="policy_name must match policy"):
        CatalogUiPolicyIntent(
            catalog_item_name="Request Temporary Badge",
            policy_name="Show schedule",
            conditions="needs_schedule=yes",
            actions=[action.model_copy(update={"policy_name": "Other"})],
        )


def test_catalog_ui_policy_action_requires_variable() -> None:
    with pytest.raises(ValueError, match="requires a variable"):
        CatalogUiPolicyActionIntent(variable="   ", visible="true")


def test_parse_catalog_ui_policy_conditions_requires_text() -> None:
    with pytest.raises(ValueError, match="requires a condition"):
        parse_catalog_ui_policy_conditions("   ")


def test_catalog_ui_policy_condition_join_is_constrained() -> None:
    from jedi_devproject.catalog_ui_policy_generation import CatalogUiPolicyCondition

    with pytest.raises(ValueError, match="join must be AND or OR"):
        CatalogUiPolicyCondition(join="XOR", variable="start_date", operator="=", value="x")


def test_catalog_ui_policy_action_accepts_explicit_disabled_value() -> None:
    updates = _updates(
        [
            _policy_change(),
            _action_change(visible="ignore", mandatory="ignore", disabled="true"),
        ]
    )

    assert "<disabled>true</disabled>" in str(updates[1]["payload"])
