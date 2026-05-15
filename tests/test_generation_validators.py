from __future__ import annotations

import pytest

from jedi_devproject.business_rule_generation import business_rule_customer_updates
from jedi_devproject.client_script_generation import client_script_customer_updates
from jedi_devproject.flow_designer_generation import (
    plan_flow_graph_builder,
    validate_flow_graph_diff_candidate,
)
from jedi_devproject.models import CandidateChange
from jedi_devproject.script_include_generation import script_include_customer_updates
from jedi_devproject.ui_policy_generation import ui_policy_customer_updates


def _business_rule_change(**field_overrides: object) -> CandidateChange:
    fields: dict[str, object] = {
        "name": "JEDI Incident Priority Note",
        "collection": "incident",
        "when": "before",
        "action_update": True,
        "filter_condition": "priority changes to 1",
        "script": (
            "if (current.priority.changesTo('1')) {\n"
            "    current.work_notes = 'Priority escalated by automation.';\n"
            "}"
        ),
        "fields_read": ["priority"],
        "fields_written": ["work_notes"],
    }
    fields.update(field_overrides)
    return CandidateChange(
        table="sys_script",
        operation="insert",
        fields=fields,
        rationale="Add the requested table-local Business Rule.",
    )


def _client_script_change(**field_overrides: object) -> CandidateChange:
    fields: dict[str, object] = {
        "name": "JEDI Incident Category CI Message",
        "table": "incident",
        "type": "onChange",
        "field": "category",
        "script": (
            "function onChange(control, oldValue, newValue, isLoading) {\n"
            "    if (isLoading || newValue !== 'software') {\n"
            "        return;\n"
            "    }\n"
            "    g_form.addInfoMessage('Confirm the CI before saving.');\n"
            "}"
        ),
        "fields_read": ["category"],
        "fields_written": [],
        "messages_shown": ["Confirm the CI before saving."],
    }
    fields.update(field_overrides)
    return CandidateChange(
        table="sys_script_client",
        operation="insert",
        fields=fields,
        rationale="Add the requested table-local Client Script.",
    )


def _script_include_change(**field_overrides: object) -> CandidateChange:
    fields: dict[str, object] = {
        "name": "JediIncidentUtils",
        "api_name": "global.JediIncidentUtils",
        "scope": "global",
        "client_callable": False,
        "active": True,
        "description": "Utility helpers for Incident automation.",
        "script": (
            "var JediIncidentUtils = Class.create();\n"
            "JediIncidentUtils.prototype = {\n"
            "    initialize: function() {},\n"
            "    normalizeCategory: function(category) {\n"
            "        return String(category || '').toLowerCase();\n"
            "    },\n"
            "    type: 'JediIncidentUtils'\n"
            "};"
        ),
        "public_methods": ["normalizeCategory(category)"],
        "tables_read": [],
        "tables_written": [],
        "fields_read": [],
        "fields_written": [],
    }
    fields.update(field_overrides)
    return CandidateChange(
        table="sys_script_include",
        operation="insert",
        fields=fields,
        rationale="Add the requested server-side utility Script Include.",
    )


def _ui_policy_change(**field_overrides: object) -> CandidateChange:
    fields: dict[str, object] = {
        "short_description": "JEDI Incident Assignment Group Required",
        "table": "incident",
        "conditions": "category=software",
        "reverse_if_false": True,
        "run_scripts": False,
    }
    fields.update(field_overrides)
    return CandidateChange(
        table="sys_ui_policy",
        operation="insert",
        fields=fields,
        rationale="Add the requested declarative UI Policy.",
    )


def _ui_policy_action_change(**field_overrides: object) -> CandidateChange:
    fields: dict[str, object] = {
        "policy_name": "JEDI Incident Assignment Group Required",
        "table": "incident",
        "field": "assignment_group",
        "mandatory": "true",
        "visible": "true",
        "disabled": "ignore",
        "cleared": False,
    }
    fields.update(field_overrides)
    return CandidateChange(
        table="sys_ui_policy_action",
        operation="insert",
        fields=fields,
        rationale="Make Assignment group mandatory and visible.",
    )


def _flow_graph_diff_change(**field_overrides: object) -> CandidateChange:
    fields: dict[str, object] = {
        "capability": "flow_modify",
        "flow_name": "Incident Triage",
        "flow_sys_id_or_stable_key": "flow-sys-id",
        "target_table": "incident",
        "trigger_summary": "When Incident category is Software",
        "existing_graph_hash": "a" * 64,
        "requested_graph_diff": [
            {
                "operation": "add_action",
                "node_id": "new-action-node",
                "after_node_id": "trigger-sys-id",
                "action_type": "set_field_value",
                "summary": "Set assignment group to Service Desk",
                "inputs": {"field": "assignment_group", "value": "Service Desk"},
            }
        ],
        "affected_nodes": ["trigger-sys-id"],
        "affected_edges": ["trigger-sys-id:new-action-node"],
        "customer_update_records": [],
        "test_plan": ["Create a Software incident and confirm assignment group is set."],
        "rollback_notes": ["Remove the added Flow Designer action."],
        "reviewer_notes": ["Graph diff only; no Update Set XML generated in this sprint."],
    }
    fields.update(field_overrides)
    return CandidateChange(
        table="sys_hub_flow_graph_diff",
        operation="update",
        fields=fields,
        rationale="Describe a narrow Flow Designer graph diff.",
    )


def _retrieved_flow_nodes() -> set[str]:
    return {"flow-sys-id", "trigger-sys-id", "action-sys-id", "logic-sys-id"}


def test_flow_graph_diff_validator_accepts_narrow_add_action_diff() -> None:
    intent = validate_flow_graph_diff_candidate(
        changes=[_flow_graph_diff_change()],
        retrieved_node_ids=_retrieved_flow_nodes(),
    )

    assert intent.capability == "flow_modify"
    assert intent.flow_name == "Incident Triage"
    assert intent.target_table == "incident"
    assert intent.requested_graph_diff[0].operation == "add_action"
    assert intent.customer_update_records == []


def test_flow_graph_diff_validator_rejects_raw_update_xml() -> None:
    with pytest.raises(ValueError, match="Flow graph diff must not include raw XML"):
        validate_flow_graph_diff_candidate(
            changes=[
                _flow_graph_diff_change(
                    customer_update_records=[
                        {"name": "sys_hub_action_instance_bad", "payload": "<record_update/>"}
                    ]
                )
            ],
            retrieved_node_ids=_retrieved_flow_nodes(),
        )


def test_flow_graph_diff_validator_rejects_unretrieved_affected_node() -> None:
    with pytest.raises(ValueError, match="Flow graph diff references unretrieved node"):
        validate_flow_graph_diff_candidate(
            changes=[_flow_graph_diff_change(affected_nodes=["unknown-node"])],
            retrieved_node_ids=_retrieved_flow_nodes(),
        )


def test_flow_graph_diff_validator_rejects_unsupported_graph_rewrite() -> None:
    with pytest.raises(ValueError, match="unsupported Flow graph diff operation"):
        validate_flow_graph_diff_candidate(
            changes=[
                _flow_graph_diff_change(
                    requested_graph_diff=[
                        {
                            "operation": "rewrite_graph",
                            "node_id": "trigger-sys-id",
                            "summary": "Replace the full flow graph",
                        }
                    ]
                )
            ],
            retrieved_node_ids=_retrieved_flow_nodes(),
        )


def test_flow_graph_diff_validator_rejects_forbidden_flow_tokens() -> None:
    with pytest.raises(ValueError, match="forbidden Flow graph diff token"):
        validate_flow_graph_diff_candidate(
            changes=[
                _flow_graph_diff_change(
                    requested_graph_diff=[
                        {
                            "operation": "add_action",
                            "node_id": "new-action-node",
                            "after_node_id": "trigger-sys-id",
                            "action_type": "custom REST credential step",
                            "summary": "Call https://example.invalid with a token",
                        }
                    ]
                )
            ],
            retrieved_node_ids=_retrieved_flow_nodes(),
        )


def test_flow_graph_builder_plan_keeps_generation_and_handoff_disabled() -> None:
    plan = plan_flow_graph_builder(
        changes=[_flow_graph_diff_change()],
        retrieved_node_ids=_retrieved_flow_nodes(),
        retrieved_graph_hash="a" * 64,
    )

    assert plan.capability == "flow_modify"
    assert plan.flow_name == "Incident Triage"
    assert plan.runtime_generation_enabled is False
    assert plan.retrieved_update_set_handoff_enabled is False
    assert plan.graph_hash_verified is True
    assert plan.blocked_reason == "Flow Designer builder is design-only"
    assert plan.required_customer_update_tables == [
        "sys_hub_flow",
        "sys_hub_action_instance",
        "sys_hub_flow_logic_instance_v2",
    ]
    assert "retrieved_graph_hash_matches_existing_graph_hash" in plan.preflight_checks
    assert "xml_shape_repository_available" in plan.required_builder_evidence


def test_flow_graph_builder_plan_rejects_stale_graph_hash() -> None:
    with pytest.raises(ValueError, match="retrieved graph hash does not match"):
        plan_flow_graph_builder(
            changes=[_flow_graph_diff_change()],
            retrieved_node_ids=_retrieved_flow_nodes(),
            retrieved_graph_hash="b" * 64,
        )


def test_flow_graph_builder_plan_rejects_premature_customer_update_records() -> None:
    with pytest.raises(ValueError, match="Flow builder design does not accept customer updates"):
        plan_flow_graph_builder(
            changes=[
                _flow_graph_diff_change(
                    customer_update_records=[
                        {
                            "name": "sys_hub_action_instance_generated",
                            "target_table": "sys_hub_action_instance",
                        }
                    ]
                )
            ],
            retrieved_node_ids=_retrieved_flow_nodes(),
            retrieved_graph_hash="a" * 64,
        )


def test_business_rule_validator_rejects_undeclared_set_value_write() -> None:
    change = _business_rule_change(
        script=(
            "if (current.priority.changesTo('1')) {\n"
            "    current.setValue('impact', '1');\n"
            "}"
        )
    )

    with pytest.raises(ValueError, match="Business Rule writes undeclared field: impact"):
        business_rule_customer_updates(
            changes=[change],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_client_script_validator_rejects_undeclared_clear_value_write() -> None:
    change = _client_script_change(
        script=(
            "function onChange(control, oldValue, newValue, isLoading) {\n"
            "    if (isLoading) {\n"
            "        return;\n"
            "    }\n"
            "    g_form.clearValue('assignment_group');\n"
            "}"
        )
    )

    with pytest.raises(ValueError, match="Client Script writes undeclared field: assignment_group"):
        client_script_customer_updates(
            changes=[change],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_script_include_validator_rejects_non_global_scope_until_scoped_xml_is_supported() -> None:
    change = _script_include_change(
        api_name="x_jedi_app.JediIncidentUtils",
        scope="x_jedi_app",
    )

    with pytest.raises(ValueError, match="Script Include scope must be global"):
        script_include_customer_updates(
            changes=[change],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_script_include_validator_requires_public_methods() -> None:
    change = _script_include_change(public_methods=[])

    with pytest.raises(
        ValueError,
        match="Script Include public_methods must name at least one method",
    ):
        script_include_customer_updates(
            changes=[change],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_script_include_validator_rejects_declared_writes_for_utility_only_profile() -> None:
    change = _script_include_change(tables_written=["incident"], fields_written=["category"])

    with pytest.raises(ValueError, match="Script Include writes are not supported"):
        script_include_customer_updates(
            changes=[change],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_ui_policy_validator_rejects_missing_policy_record() -> None:
    with pytest.raises(ValueError, match="UI Policy handoff requires a sys_ui_policy change"):
        ui_policy_customer_updates(
            changes=[_ui_policy_action_change()],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_ui_policy_validator_rejects_missing_action_record() -> None:
    with pytest.raises(
        ValueError,
        match="UI Policy handoff requires at least one sys_ui_policy_action change",
    ):
        ui_policy_customer_updates(
            changes=[_ui_policy_change()],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_ui_policy_validator_rejects_policy_update_operation() -> None:
    with pytest.raises(ValueError, match="UI Policy handoff supports policy insert only"):
        ui_policy_customer_updates(
            changes=[
                _ui_policy_change().model_copy(update={"operation": "update"}),
                _ui_policy_action_change(),
            ],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_ui_policy_validator_rejects_action_update_operation() -> None:
    with pytest.raises(ValueError, match="UI Policy handoff supports action insert only"):
        ui_policy_customer_updates(
            changes=[
                _ui_policy_change(),
                _ui_policy_action_change().model_copy(update={"operation": "update"}),
            ],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_ui_policy_validator_rejects_action_table_mismatch() -> None:
    with pytest.raises(ValueError, match="UI Policy action table must match policy table"):
        ui_policy_customer_updates(
            changes=[_ui_policy_change(), _ui_policy_action_change(table="problem")],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_ui_policy_validator_rejects_action_policy_name_mismatch() -> None:
    with pytest.raises(ValueError, match="UI Policy action policy_name must match policy"):
        ui_policy_customer_updates(
            changes=[
                _ui_policy_change(),
                _ui_policy_action_change(policy_name="Different Policy"),
            ],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_ui_policy_validator_rejects_invalid_action_tristate() -> None:
    with pytest.raises(ValueError, match="UI Policy action values must be true, false, or ignore"):
        ui_policy_customer_updates(
            changes=[_ui_policy_change(), _ui_policy_action_change(mandatory="sometimes")],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_ui_policy_validator_rejects_forbidden_condition_tokens() -> None:
    with pytest.raises(ValueError, match="forbidden UI Policy token"):
        ui_policy_customer_updates(
            changes=[
                _ui_policy_change(conditions="category=software^endpoint=https://example.invalid"),
                _ui_policy_action_change(),
            ],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_ui_policy_validator_normalizes_false_read_only_and_clear_actions() -> None:
    updates = ui_policy_customer_updates(
        changes=[
            _ui_policy_change(order="not-a-number", description="Declarative form behavior."),
            _ui_policy_action_change(
                mandatory=False,
                visible=False,
                read_only=True,
                cleared=True,
            ),
        ],
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    action_update = updates[1]
    assert action_update["name"].endswith(
        "not_required_hidden_read_only_cleared"
    )
    assert "<order>100</order>" in str(updates[0]["payload"])
    assert "<mandatory>false</mandatory>" in str(action_update["payload"])
    assert "<visible>false</visible>" in str(action_update["payload"])
    assert "<disabled>true</disabled>" in str(action_update["payload"])
    assert "<cleared>true</cleared>" in str(action_update["payload"])
