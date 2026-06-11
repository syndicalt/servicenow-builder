from __future__ import annotations

import pytest

from jedi_devproject.business_rule_generation import business_rule_customer_updates
from jedi_devproject.client_script_generation import client_script_customer_updates
from jedi_devproject.flow_designer_generation import (
    flow_builder_readiness_contract,
    flow_customer_update_strategy,
    flow_preview_commit_review_strategy,
    flow_snapshot_update_strategy,
    flow_xml_shape_repository,
    plan_flow_graph_builder,
    validate_flow_graph_diff_candidate,
    validate_flow_xml_shape_evidence,
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
    assert plan.xml_shape_repository_version == "flow-xml-shapes-v1"
    assert plan.xml_shape_tables == [
        "sys_hub_flow",
        "sys_hub_action_instance",
        "sys_hub_flow_logic_instance_v2",
    ]
    assert plan.customer_update_strategy_version == "flow-customer-update-strategy-v1"
    assert plan.snapshot_update_strategy_version == "flow-snapshot-update-strategy-v1"
    assert plan.preview_commit_review_strategy_version == (
        "flow-preview-commit-review-strategy-v1"
    )
    assert plan.readiness_contract_version == "flow-builder-readiness-v1"
    assert plan.ready_for_runtime_generation is False
    assert plan.ready_for_retrieved_update_set_handoff is False
    assert plan.readiness_blocked_reason == "Flow Designer builder is not implemented"
    assert plan.unsupported_reason_codes == [
        "flow_builder_not_implemented",
        "runtime_generation_disabled",
        "retrieved_update_set_handoff_disabled",
    ]
    assert [item.code for item in plan.unsupported_reason_guidance] == plan.unsupported_reason_codes
    assert plan.unsupported_reason_guidance[0].operator_action == "route_to_human_review"
    assert plan.missing_builder_evidence == [
        "flow_xml_shape_evidence_validated:sys_hub_flow",
        "flow_xml_shape_evidence_validated:sys_hub_action_instance",
        "flow_xml_shape_evidence_validated:sys_hub_flow_logic_instance_v2",
        "flow_snapshot_evidence_current",
        "flow_builder_implemented",
    ]
    assert "rollback_customer_update_strategy_defined" in plan.required_builder_evidence


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


def test_flow_xml_shape_repository_contains_required_flow_customer_update_shapes() -> None:
    repository = flow_xml_shape_repository()

    assert repository.runtime_generation_enabled is False
    assert repository.retrieved_update_set_handoff_enabled is False
    assert repository.version == "flow-xml-shapes-v1"
    assert [shape.table for shape in repository.shapes] == [
        "sys_hub_flow",
        "sys_hub_action_instance",
        "sys_hub_flow_logic_instance_v2",
    ]
    assert all(shape.root_element == "record_update" for shape in repository.shapes)
    assert all(shape.action == "INSERT_OR_UPDATE" for shape in repository.shapes)
    assert "sys_id" in repository.shape("sys_hub_action_instance").required_fields
    assert "flow" in repository.shape("sys_hub_action_instance").required_fields
    assert "xml_shape_repository_available" in repository.evidence


def test_flow_xml_shape_repository_rejects_unknown_shape_lookup() -> None:
    repository = flow_xml_shape_repository()

    with pytest.raises(KeyError, match="Flow XML shape not found"):
        repository.shape("sys_hub_spoke_instance")


def test_flow_xml_shape_evidence_validator_accepts_review_sample() -> None:
    evidence = validate_flow_xml_shape_evidence(
        table="sys_hub_action_instance",
        xml_payload=(
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<record_update>'
            '<sys_hub_action_instance action="INSERT_OR_UPDATE">'
            "<sys_id>action-sys-id</sys_id>"
            "<sys_update_name>sys_hub_action_instance_action-sys-id</sys_update_name>"
            "<flow>flow-sys-id</flow>"
            "<action_type>set_field_value</action_type>"
            "<display_text>Set Assignment group</display_text>"
            "<order>100</order>"
            "</sys_hub_action_instance>"
            "</record_update>"
        ),
    )

    assert evidence.table == "sys_hub_action_instance"
    assert evidence.repository_version == "flow-xml-shapes-v1"
    assert evidence.record_element == "sys_hub_action_instance"
    assert evidence.required_fields_present == [
        "sys_id",
        "sys_update_name",
        "flow",
        "action_type",
        "display_text",
        "order",
    ]
    assert evidence.forbidden_fields_absent is True
    assert evidence.runtime_generation_enabled is False
    assert evidence.retrieved_update_set_handoff_enabled is False


def test_flow_xml_shape_evidence_validator_rejects_missing_required_field() -> None:
    with pytest.raises(ValueError, match="Flow XML shape evidence missing required field: flow"):
        validate_flow_xml_shape_evidence(
            table="sys_hub_action_instance",
            xml_payload=(
                "<record_update>"
                '<sys_hub_action_instance action="INSERT_OR_UPDATE">'
                "<sys_id>action-sys-id</sys_id>"
                "<sys_update_name>sys_hub_action_instance_action-sys-id</sys_update_name>"
                "<action_type>set_field_value</action_type>"
                "<display_text>Set Assignment group</display_text>"
                "<order>100</order>"
                "</sys_hub_action_instance>"
                "</record_update>"
            ),
        )


def test_flow_xml_shape_evidence_validator_rejects_forbidden_field() -> None:
    with pytest.raises(ValueError, match="Flow XML shape evidence contains forbidden field"):
        validate_flow_xml_shape_evidence(
            table="sys_hub_flow",
            xml_payload=(
                "<record_update>"
                '<sys_hub_flow action="INSERT_OR_UPDATE">'
                "<sys_id>flow-sys-id</sys_id>"
                "<sys_update_name>sys_hub_flow_flow-sys-id</sys_update_name>"
                "<name>Incident Triage</name>"
                "<active>true</active>"
                "<status>published</status>"
                "<latest_snapshot>snapshot-sys-id</latest_snapshot>"
                "<sys_updated_by>admin</sys_updated_by>"
                "</sys_hub_flow>"
                "</record_update>"
            ),
        )


def test_flow_customer_update_strategy_names_approved_flow_updates() -> None:
    strategy = flow_customer_update_strategy()
    sys_id = "a" * 32

    assert strategy.version == "flow-customer-update-strategy-v1"
    assert strategy.runtime_generation_enabled is False
    assert strategy.retrieved_update_set_handoff_enabled is False
    assert strategy.customer_update_name("sys_hub_action_instance", sys_id) == (
        "sys_hub_action_instance_" + sys_id
    )
    assert "add_action" in strategy.rollback_strategy_by_operation
    assert "update_condition" in strategy.rollback_strategy_by_operation
    assert "customer_update_name_strategy_defined" in strategy.evidence
    assert "rollback_customer_update_strategy_defined" in strategy.evidence


def test_flow_customer_update_strategy_rejects_unapproved_table() -> None:
    strategy = flow_customer_update_strategy()

    with pytest.raises(KeyError, match="Flow XML shape not found"):
        strategy.customer_update_name("sys_hub_spoke_instance", "a" * 32)


def test_flow_customer_update_strategy_rejects_unstable_sys_id() -> None:
    strategy = flow_customer_update_strategy()

    with pytest.raises(ValueError, match="Flow customer update sys_id must be 32 hex characters"):
        strategy.customer_update_name("sys_hub_action_instance", "generated-action-node")


def test_flow_snapshot_update_strategy_requires_retrieved_latest_snapshot() -> None:
    strategy = flow_snapshot_update_strategy()

    assert strategy.version == "flow-snapshot-update-strategy-v1"
    assert strategy.runtime_generation_enabled is False
    assert strategy.retrieved_update_set_handoff_enabled is False
    assert strategy.flow_record_table == "sys_hub_flow"
    assert strategy.snapshot_reference_field == "latest_snapshot"
    assert "flow_snapshot_update_strategy_defined" in strategy.evidence
    assert strategy.validate_latest_snapshot("a" * 32) == "a" * 32


def test_flow_snapshot_update_strategy_rejects_missing_snapshot_reference() -> None:
    strategy = flow_snapshot_update_strategy()

    with pytest.raises(ValueError, match="Flow latest_snapshot evidence is required"):
        strategy.validate_latest_snapshot("")


def test_flow_snapshot_update_strategy_rejects_unstable_snapshot_reference() -> None:
    strategy = flow_snapshot_update_strategy()

    with pytest.raises(ValueError, match="Flow latest_snapshot must be 32 hex characters"):
        strategy.validate_latest_snapshot("snapshot-sys-id")


def test_flow_snapshot_update_strategy_rejects_snapshot_table_mutation() -> None:
    strategy = flow_snapshot_update_strategy()

    with pytest.raises(ValueError, match="Flow snapshot table mutation is not supported"):
        strategy.validate_mutation_table("sys_hub_flow_snapshot")


def test_flow_preview_commit_review_strategy_requires_servicenow_review() -> None:
    strategy = flow_preview_commit_review_strategy()

    assert strategy.version == "flow-preview-commit-review-strategy-v1"
    assert strategy.review_boundary == "retrieved_update_set_preview_commit"
    assert strategy.runtime_generation_enabled is False
    assert strategy.retrieved_update_set_handoff_enabled is False
    assert strategy.auto_commit_enabled is False
    assert strategy.require_preview is True
    assert strategy.require_human_commit is True
    assert "servicenow_preview_commit_review_required" in strategy.evidence


def test_flow_preview_commit_review_strategy_rejects_auto_commit() -> None:
    strategy = flow_preview_commit_review_strategy()

    with pytest.raises(ValueError, match="Flow Designer auto-commit is not supported"):
        strategy.validate_review_request(auto_commit=True, preview_requested=True)


def test_flow_preview_commit_review_strategy_rejects_missing_preview() -> None:
    strategy = flow_preview_commit_review_strategy()

    with pytest.raises(ValueError, match="Flow Designer preview is required before commit"):
        strategy.validate_review_request(auto_commit=False, preview_requested=False)


def test_flow_builder_readiness_contract_reports_all_required_evidence() -> None:
    readiness = flow_builder_readiness_contract()

    assert readiness.version == "flow-builder-readiness-v1"
    assert readiness.ready_for_runtime_generation is False
    assert readiness.ready_for_retrieved_update_set_handoff is False
    assert readiness.blocked_reason == "Flow Designer builder is not implemented"
    assert readiness.unsupported_reason_codes == [
        "flow_builder_not_implemented",
        "runtime_generation_disabled",
        "retrieved_update_set_handoff_disabled",
    ]
    assert [item.code for item in readiness.unsupported_reason_guidance] == (
        readiness.unsupported_reason_codes
    )
    assert readiness.unsupported_reason_guidance[0].summary == (
        "Flow Designer builder is not implemented."
    )
    assert readiness.unsupported_reason_guidance[0].operator_action == "route_to_human_review"
    assert readiness.required_evidence == [
        "retrieved_graph_hash_matches_existing_graph_hash",
        "diff_references_only_retrieved_nodes",
        "diff_operation_is_add_action_or_update_condition",
        "xml_shape_repository_available",
        "xml_shape_evidence_validator_available",
        "customer_update_name_strategy_defined",
        "flow_snapshot_update_strategy_defined",
        "rollback_customer_update_strategy_defined",
        "servicenow_preview_commit_review_required",
        "flow_xml_shape_evidence_validated:sys_hub_flow",
        "flow_xml_shape_evidence_validated:sys_hub_action_instance",
        "flow_xml_shape_evidence_validated:sys_hub_flow_logic_instance_v2",
        "flow_snapshot_evidence_current",
        "flow_builder_implemented",
    ]
    assert readiness.missing_evidence == [
        "flow_xml_shape_evidence_validated:sys_hub_flow",
        "flow_xml_shape_evidence_validated:sys_hub_action_instance",
        "flow_xml_shape_evidence_validated:sys_hub_flow_logic_instance_v2",
        "flow_snapshot_evidence_current",
        "flow_builder_implemented",
    ]
    assert readiness.requirement_status["xml_shape_repository_available"] == "satisfied"
    assert readiness.requirement_status["flow_builder_implemented"] == "missing"


def test_flow_builder_readiness_contract_reports_missing_evidence() -> None:
    readiness = flow_builder_readiness_contract(
        available_evidence={
            "retrieved_graph_hash_matches_existing_graph_hash",
            "diff_references_only_retrieved_nodes",
        }
    )

    assert readiness.ready_for_runtime_generation is False
    assert "xml_shape_repository_available" in readiness.missing_evidence
    assert "servicenow_preview_commit_review_required" in readiness.missing_evidence


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


def test_business_rule_validator_rejects_metadata_variable_inside_script() -> None:
    change = _business_rule_change(
        script=(
            "if (current.category == 'inquiry' && !current.short_description) {\n"
            "    current.short_description = 'Inquiry needs triage';\n"
            "}\n"
            "var fields_written = [\"short_description\"];\n"
        ),
        fields_written=["short_description"],
    )

    with pytest.raises(ValueError, match="Business Rule script must not declare fields_written"):
        business_rule_customer_updates(
            changes=[change],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_business_rule_validator_normalizes_model_operation_and_field_aliases() -> None:
    updates = business_rule_customer_updates(
        changes=[
            _business_rule_change(
                action_insert=False,
                action_update=False,
                operation_insert=True,
                operation_update=True,
                insert=False,
                update=False,
                script="",
                action_script="current.short_description = 'Inquiry needs triage';",
                fields_read=[],
                fields_written=[],
            )
        ],
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    payload = updates[0]["payload"]
    assert "<action_insert>true</action_insert>" in payload
    assert "<action_update>true</action_update>" in payload
    assert "current.short_description" in payload


def test_business_rule_validator_infers_operation_flags_from_rationale_when_missing() -> None:
    updates = business_rule_customer_updates(
        changes=[
            _business_rule_change(
                action_insert=False,
                action_update=False,
                script=(
                    "if (current.category == 'inquiry') {\n"
                    "    current.short_description = 'Inquiry needs triage';\n"
                    "}"
                ),
                fields_written=[],
                rationale=(
                    "Applied on before insert and update operations on the incident table."
                ),
            )
        ],
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    payload = updates[0]["payload"]
    assert "<action_insert>true</action_insert>" in payload
    assert "<action_update>true</action_update>" in payload


def test_business_rule_validator_normalizes_action_and_conditions_aliases() -> None:
    updates = business_rule_customer_updates(
        changes=[
            _business_rule_change(
                action_insert=False,
                action_update=False,
                action="insert or update",
                filter_condition="",
                conditions="current.category == 'inquiry' && gs.nil(current.short_description)",
                script="current.short_description = 'Inquiry needs triage';",
                fields_written=[],
            )
        ],
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    payload = updates[0]["payload"]
    assert "<action_insert>true</action_insert>" in payload
    assert "<action_update>true</action_update>" in payload
    assert "current.category == &#x27;inquiry&#x27; &amp;&amp; gs.nil" in payload


def test_business_rule_validator_normalizes_filter_alias() -> None:
    updates = business_rule_customer_updates(
        changes=[
            _business_rule_change(
                action_insert=False,
                action_update=False,
                action="insert, update",
                filter_condition="",
                filter="current.category == 'inquiry' && !current.short_description",
                script=(
                    "if (current.category == 'inquiry' && !current.short_description) {\n"
                    "    current.short_description = 'Inquiry needs triage';\n"
                    "}"
                ),
                fields_written=[],
            )
        ],
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    payload = updates[0]["payload"]
    assert "<action_insert>true</action_insert>" in payload
    assert "<action_update>true</action_update>" in payload
    assert (
        "current.category == &#x27;inquiry&#x27; &amp;&amp; !current.short_description"
        in payload
    )


def test_script_include_validator_infers_public_methods_from_script() -> None:
    updates = script_include_customer_updates(
        changes=[
            _script_include_change(
                name="JediUatStringUtil",
                api_name="global.JediUatStringUtil",
                public_methods=[],
                script=(
                    "var JediUatStringUtil = Class.create();\n"
                    "JediUatStringUtil.prototype = {\n"
                    "    initialize: function() {},\n"
                    "    normalizeText: function(value) { return ''; },\n"
                    "    type: 'JediUatStringUtil'\n"
                    "};"
                ),
            )
        ],
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    assert updates[0]["target_name"] == "JediUatStringUtil"
    assert "normalizeText" in updates[0]["payload"]


def test_script_include_validator_infers_global_api_name_when_model_omits_it() -> None:
    updates = script_include_customer_updates(
        changes=[
            _script_include_change(
                name="JediUatIncidentTextUtils",
                api_name="",
                scope="",
                public_methods=[],
                script=(
                    "var JediUatIncidentTextUtils = Class.create();\n"
                    "JediUatIncidentTextUtils.prototype = {\n"
                    "    initialize: function() {},\n"
                    "    normalizeText: function(value) { return String(value || '').trim(); },\n"
                    "    type: 'JediUatIncidentTextUtils'\n"
                    "};"
                ),
            )
        ],
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    assert updates[0]["target_name"] == "JediUatIncidentTextUtils"
    assert "<api_name>global.JediUatIncidentTextUtils</api_name>" in updates[0]["payload"]


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
    change = _script_include_change(
        public_methods=[],
        script=(
            "var JediIncidentUtils = Class.create();\n"
            "JediIncidentUtils.prototype = {\n"
            "    initialize: function() {},\n"
            "    type: 'JediIncidentUtils'\n"
            "};"
        ),
    )

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


def test_ui_policy_validator_defaults_action_table_from_policy_table() -> None:
    updates = ui_policy_customer_updates(
        changes=[
            _ui_policy_change(table="incident"),
            _ui_policy_action_change(table=""),
        ],
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    assert "<table>incident</table>" in str(updates[1]["payload"])


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
