from __future__ import annotations

import hashlib
from typing import Any

import pytest
from pydantic import ValidationError

from jedi_devproject.flow_builder import (
    FlowRetrievedNodeEvidence,
    build_flow_customer_updates,
    flow_builder_available,
    stable_flow_sys_id,
)
from jedi_devproject.flow_designer_generation import (
    FlowGraphDiffIntent,
    FlowRuntimeEvidenceSummary,
    flow_builder_readiness_contract,
    validate_flow_xml_shape_evidence,
)
from jedi_devproject.flow_xml_evidence import (
    FlowXmlEvidenceBundle,
    flow_builder_readiness_from_evidence,
)

FLOW_SYS_ID = "f1" * 16
ACTION_SYS_ID = "a2" * 16
LOGIC_SYS_ID = "b3" * 16
SNAPSHOT_SYS_ID = "c4" * 16
GRAPH_HASH = "d5" * 32

SHAPE_TABLES = [
    "sys_hub_flow",
    "sys_hub_action_instance",
    "sys_hub_flow_logic_instance_v2",
]


def _evidence_bundle(**overrides: Any) -> FlowXmlEvidenceBundle:
    payload: dict[str, Any] = {
        "version": "flow-xml-evidence-v1",
        "repository_version": "flow-xml-shapes-v1",
        "flow_name": "Incident Triage",
        "flow_sys_id": FLOW_SYS_ID,
        "retrieved_graph_hash": GRAPH_HASH,
        "shapes": [
            {
                "table": table,
                "customer_update_name": f"{table}_{FLOW_SYS_ID}",
                "status": "validated",
                "payload_sha256": "0" * 64,
            }
            for table in SHAPE_TABLES
        ],
        "snapshot": {
            "snapshot_table": "sys_hub_flow_snapshot",
            "snapshot_reference_field": "latest_snapshot",
            "status": "collected",
            "snapshot_sys_id": SNAPSHOT_SYS_ID,
            "content_sha256": "1" * 64,
        },
        "evidence": [],
    }
    payload.update(overrides)
    return FlowXmlEvidenceBundle.model_validate(payload)


def _add_action_step(**overrides: Any) -> dict[str, Any]:
    step: dict[str, Any] = {
        "operation": "add_action",
        "node_id": "new-action-node",
        "after_node_id": ACTION_SYS_ID,
        "action_type": "core-create-task",
        "summary": "Create triage task for high impact incidents",
        "inputs": {},
    }
    step.update(overrides)
    return step


def _update_condition_step(**overrides: Any) -> dict[str, Any]:
    step: dict[str, Any] = {
        "operation": "update_condition",
        "node_id": LOGIC_SYS_ID,
        "summary": "Tighten the high impact condition",
        "inputs": {"condition": "impact=1^urgency=1"},
    }
    step.update(overrides)
    return step


def _intent(**overrides: Any) -> FlowGraphDiffIntent:
    fields: dict[str, Any] = {
        "capability": "flow_modify",
        "flow_name": "Incident Triage",
        "flow_sys_id_or_stable_key": FLOW_SYS_ID,
        "target_table": "incident",
        "trigger_summary": "When Incident impact is high",
        "existing_graph_hash": GRAPH_HASH,
        "requested_graph_diff": [_add_action_step()],
        "affected_nodes": [ACTION_SYS_ID],
        "affected_edges": [f"{ACTION_SYS_ID}:new-action-node"],
        "customer_update_records": [],
        "test_plan": ["Create a high impact incident and confirm the triage task."],
        "rollback_notes": ["Remove the added Flow Designer action."],
    }
    fields.update(overrides)
    return FlowGraphDiffIntent.model_validate(fields)


def _retrieved_nodes() -> list[FlowRetrievedNodeEvidence]:
    return [
        FlowRetrievedNodeEvidence(
            table="sys_hub_action_instance",
            sys_id=ACTION_SYS_ID,
            display_text="Create triage task",
            order=100,
            action_type="core-create-task",
        ),
        FlowRetrievedNodeEvidence(
            table="sys_hub_flow_logic_instance_v2",
            sys_id=LOGIC_SYS_ID,
            display_text="If impact is high",
            order=200,
            logic_definition="IF",
            condition="impact=1",
        ),
    ]


def _build(
    *,
    intent: FlowGraphDiffIntent | None = None,
    evidence_bundle: FlowXmlEvidenceBundle | None = None,
    retrieved_nodes: list[FlowRetrievedNodeEvidence] | None = None,
) -> Any:
    return build_flow_customer_updates(
        intent=intent if intent is not None else _intent(),
        evidence_bundle=evidence_bundle if evidence_bundle is not None else _evidence_bundle(),
        retrieved_nodes=retrieved_nodes if retrieved_nodes is not None else _retrieved_nodes(),
    )


def test_add_action_builds_exact_shape_conformant_customer_updates() -> None:
    result = _build()

    action_sys_id = stable_flow_sys_id("sys_hub_action_instance", FLOW_SYS_ID, "new-action-node")
    edge_sys_id = stable_flow_sys_id(
        "sys_hub_flow_logic_instance_v2", FLOW_SYS_ID, ACTION_SYS_ID, "new-action-node"
    )
    expected_action_payload = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<record_update table="sys_hub_action_instance">'
        '<sys_hub_action_instance action="INSERT_OR_UPDATE">'
        f"<sys_id>{action_sys_id}</sys_id>"
        f"<sys_update_name>sys_hub_action_instance_{action_sys_id}</sys_update_name>"
        f"<flow>{FLOW_SYS_ID}</flow>"
        "<action_type>core-create-task</action_type>"
        "<display_text>Create triage task for high impact incidents</display_text>"
        "<order>101</order>"
        "</sys_hub_action_instance>"
        "</record_update>"
    )
    expected_edge_payload = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<record_update table="sys_hub_flow_logic_instance_v2">'
        '<sys_hub_flow_logic_instance_v2 action="INSERT_OR_UPDATE">'
        f"<sys_id>{edge_sys_id}</sys_id>"
        f"<sys_update_name>sys_hub_flow_logic_instance_v2_{edge_sys_id}</sys_update_name>"
        f"<flow>{FLOW_SYS_ID}</flow>"
        "<logic_definition>SEQUENCE</logic_definition>"
        "<display_text>Connect after Create triage task</display_text>"
        "<order>102</order>"
        f"<connected_to>{action_sys_id}</connected_to>"
        "</sys_hub_flow_logic_instance_v2>"
        "</record_update>"
    )

    assert result.builder_version == "flow-builder-v1"
    assert result.operation == "add_action"
    assert result.flow_sys_id == FLOW_SYS_ID
    assert result.graph_hash == GRAPH_HASH
    assert [update.table for update in result.customer_updates] == [
        "sys_hub_action_instance",
        "sys_hub_flow_logic_instance_v2",
    ]
    action_update, edge_update = result.customer_updates
    assert action_update.payload == expected_action_payload
    assert edge_update.payload == expected_edge_payload
    assert action_update.name == f"sys_hub_action_instance_{action_sys_id}"
    assert edge_update.name == f"sys_hub_flow_logic_instance_v2_{edge_sys_id}"
    assert action_update.update_type == "Flow Action Instance"
    assert edge_update.update_type == "Flow Logic Instance"
    assert action_update.target_name == "Create triage task for high impact incidents"
    assert edge_update.target_name == "Connect after Create triage task"
    assert action_update.payload_sha256 == (
        hashlib.sha256(expected_action_payload.encode("utf-8")).hexdigest()
    )
    # The generated payloads re-validate against flow-xml-shapes-v1.
    for update in result.customer_updates:
        validate_flow_xml_shape_evidence(table=update.table, xml_payload=update.payload)


def test_add_action_handoff_records_carry_customer_update_shape() -> None:
    result = _build()

    record = result.customer_updates[0].handoff_record()
    assert record["name"] == result.customer_updates[0].name
    assert record["action"] == "INSERT_OR_UPDATE"
    assert record["type"] == "Flow Action Instance"
    assert record["target_name"] == result.customer_updates[0].target_name
    assert record["payload"] == result.customer_updates[0].payload
    assert record["application"] == "global"


def test_update_condition_builds_exact_narrow_condition_update() -> None:
    result = _build(intent=_intent(requested_graph_diff=[_update_condition_step()]))

    expected_payload = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<record_update table="sys_hub_flow_logic_instance_v2">'
        '<sys_hub_flow_logic_instance_v2 action="INSERT_OR_UPDATE">'
        f"<sys_id>{LOGIC_SYS_ID}</sys_id>"
        f"<sys_update_name>sys_hub_flow_logic_instance_v2_{LOGIC_SYS_ID}</sys_update_name>"
        f"<flow>{FLOW_SYS_ID}</flow>"
        "<logic_definition>IF</logic_definition>"
        "<display_text>If impact is high</display_text>"
        "<order>200</order>"
        "<condition>impact=1^urgency=1</condition>"
        "</sys_hub_flow_logic_instance_v2>"
        "</record_update>"
    )

    assert result.operation == "update_condition"
    assert len(result.customer_updates) == 1
    update = result.customer_updates[0]
    assert update.record_sys_id == LOGIC_SYS_ID
    assert update.payload == expected_payload
    validate_flow_xml_shape_evidence(table=update.table, xml_payload=update.payload)


def test_update_condition_preserves_retrieved_edge_reference() -> None:
    nodes = _retrieved_nodes()
    nodes[1] = nodes[1].model_copy(update={"connected_to": ACTION_SYS_ID})

    result = _build(
        intent=_intent(requested_graph_diff=[_update_condition_step()]),
        retrieved_nodes=nodes,
    )

    assert f"<condition>impact=1^urgency=1</condition><connected_to>{ACTION_SYS_ID}" in (
        result.customer_updates[0].payload
    )


def test_builder_marks_flow_for_resnapshot_and_never_touches_snapshot_tables() -> None:
    result = _build()

    assert result.requires_resnapshot_on_import is True
    assert result.snapshot_strategy_version == "flow-snapshot-update-strategy-v1"
    assert result.readiness_contract_version == "flow-builder-readiness-v1"
    assert "flow_resnapshot_on_import_required" in result.evidence
    assert "snapshot_table_mutation_blocked" in result.evidence
    assert "retrieved_update_set_preview_commit_required" in result.evidence
    emitted_tables = {update.table for update in result.customer_updates}
    assert emitted_tables.isdisjoint(
        {"sys_hub_flow", "sys_hub_flow_snapshot", "sys_hub_flow_snapshot_blob"}
    )


def test_builder_output_is_deterministic_across_runs() -> None:
    first = _build()
    second = _build()

    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_builder_fails_closed_on_stale_graph_hash() -> None:
    with pytest.raises(ValueError, match="stale Flow XML evidence"):
        _build(intent=_intent(existing_graph_hash="e6" * 32))


def test_builder_fails_closed_on_missing_shape_evidence() -> None:
    bundle = _evidence_bundle(
        shapes=[
            {
                "table": table,
                "status": "missing" if table == "sys_hub_action_instance" else "validated",
                "reason": "no records" if table == "sys_hub_action_instance" else "",
            }
            for table in SHAPE_TABLES
        ]
    )

    with pytest.raises(ValueError, match="readiness contract is not satisfied") as exc_info:
        _build(evidence_bundle=bundle)
    assert "flow_xml_shape_evidence_validated:sys_hub_action_instance" in str(exc_info.value)


def test_builder_fails_closed_on_missing_snapshot_evidence() -> None:
    bundle = _evidence_bundle(
        snapshot={
            "snapshot_table": "sys_hub_flow_snapshot",
            "snapshot_reference_field": "latest_snapshot",
            "status": "missing",
            "reason": "flow_snapshot_evidence_missing",
        }
    )

    with pytest.raises(ValueError, match="flow_snapshot_evidence_current"):
        _build(evidence_bundle=bundle)


def test_builder_rejects_provider_customer_updates() -> None:
    intent = _intent(customer_update_records=[{"name": "provider-made"}])

    with pytest.raises(ValueError, match="does not accept provider customer updates"):
        _build(intent=intent)


def test_builder_rejects_multi_step_diffs() -> None:
    intent = _intent(
        requested_graph_diff=[_add_action_step(), _update_condition_step()],
    )

    with pytest.raises(ValueError, match="exactly one graph diff step"):
        _build(intent=intent)


def test_builder_rejects_evidence_for_a_different_flow() -> None:
    with pytest.raises(ValueError, match="different flow"):
        _build(evidence_bundle=_evidence_bundle(flow_name="Other Triage"))

    with pytest.raises(ValueError, match="different flow"):
        _build(intent=_intent(flow_sys_id_or_stable_key="9f" * 16))


def test_builder_rejects_unstable_evidence_flow_sys_id() -> None:
    bundle = _evidence_bundle(flow_sys_id="not-a-sys-id")

    with pytest.raises(ValueError, match="flow sys_id must be 32 hex characters"):
        _build(evidence_bundle=bundle, intent=_intent(flow_sys_id_or_stable_key="triage-key"))


def test_builder_requires_retrieved_nodes_and_rejects_ambiguous_nodes() -> None:
    with pytest.raises(ValueError, match="requires retrieved graph nodes"):
        _build(retrieved_nodes=[])

    duplicate = _retrieved_nodes() + [_retrieved_nodes()[0]]
    with pytest.raises(ValueError, match="retrieved nodes are ambiguous"):
        _build(retrieved_nodes=duplicate)


def test_add_action_rejects_unretrieved_or_missing_after_node() -> None:
    intent = _intent(requested_graph_diff=[_add_action_step(after_node_id="c9" * 16)])
    with pytest.raises(ValueError, match="references unretrieved node"):
        _build(intent=intent)

    intent = _intent(requested_graph_diff=[_add_action_step(after_node_id=None)])
    with pytest.raises(ValueError, match="references unretrieved node"):
        _build(intent=intent)


def test_add_action_rejects_existing_node_id_and_missing_action_type() -> None:
    intent = _intent(requested_graph_diff=[_add_action_step(node_id=ACTION_SYS_ID)])
    with pytest.raises(ValueError, match="node already exists"):
        _build(intent=intent)

    intent = _intent(requested_graph_diff=[_add_action_step(action_type="  ")])
    with pytest.raises(ValueError, match="requires an action_type"):
        _build(intent=intent)


def test_update_condition_rejects_unknown_or_non_logic_nodes() -> None:
    intent = _intent(requested_graph_diff=[_update_condition_step(node_id="c9" * 16)])
    with pytest.raises(ValueError, match="references unretrieved node"):
        _build(intent=intent)

    intent = _intent(requested_graph_diff=[_update_condition_step(node_id=ACTION_SYS_ID)])
    with pytest.raises(ValueError, match="requires a retrieved flow logic node"):
        _build(intent=intent)


def test_update_condition_rejects_missing_or_extra_inputs() -> None:
    intent = _intent(requested_graph_diff=[_update_condition_step(inputs={})])
    with pytest.raises(ValueError, match="requires a condition input"):
        _build(intent=intent)

    intent = _intent(
        requested_graph_diff=[
            _update_condition_step(inputs={"condition": "impact=1", "order": "5"})
        ]
    )
    with pytest.raises(ValueError, match="accepts only the condition input"):
        _build(intent=intent)


def test_update_condition_requires_retrieved_logic_definition() -> None:
    nodes = _retrieved_nodes()
    nodes[1] = nodes[1].model_copy(update={"logic_definition": ""})

    intent = _intent(requested_graph_diff=[_update_condition_step()])
    with pytest.raises(ValueError, match="requires retrieved logic_definition"):
        _build(intent=intent, retrieved_nodes=nodes)


def test_forbidden_diff_content_is_rejected_before_the_builder_runs() -> None:
    with pytest.raises(ValidationError, match="forbidden Flow graph diff token"):
        _intent(
            requested_graph_diff=[
                _add_action_step(summary="Add a subflow call to route the work")
            ]
        )

    with pytest.raises(ValidationError, match="operation"):
        _intent(
            requested_graph_diff=[
                {
                    "operation": "rewrite_graph",
                    "node_id": ACTION_SYS_ID,
                    "summary": "Replace the full flow graph",
                }
            ]
        )


def test_retrieved_node_evidence_requires_stable_sys_ids() -> None:
    with pytest.raises(ValidationError, match="32 hex characters"):
        FlowRetrievedNodeEvidence(
            table="sys_hub_action_instance",
            sys_id="generated-node",
            display_text="Create triage task",
            order=100,
        )


def test_readiness_flips_handoff_with_builder_available_and_complete_evidence() -> None:
    readiness = flow_builder_readiness_contract(
        runtime_evidence=FlowRuntimeEvidenceSummary(
            bundle_version="flow-xml-evidence-v1",
            flow_name="Incident Triage",
            validated_shape_tables=list(SHAPE_TABLES),
            snapshot_current=True,
        ),
        builder_available=flow_builder_available(),
    )

    assert readiness.ready_for_runtime_generation is True
    assert readiness.ready_for_retrieved_update_set_handoff is True
    assert readiness.missing_evidence == []
    assert readiness.requirement_status["flow_builder_implemented"] == "satisfied"
    assert readiness.blocked_reason == ""
    assert readiness.unsupported_reason_codes == []
    assert readiness.unsupported_reason_guidance == []


def test_readiness_with_builder_available_but_no_evidence_stays_dark() -> None:
    readiness = flow_builder_readiness_contract(builder_available=True)

    assert readiness.ready_for_runtime_generation is False
    assert readiness.ready_for_retrieved_update_set_handoff is False
    assert readiness.requirement_status["flow_builder_implemented"] == "satisfied"
    assert readiness.blocked_reason == "Flow Designer runtime evidence is incomplete"
    assert readiness.unsupported_reason_codes == [
        "runtime_generation_disabled",
        "retrieved_update_set_handoff_disabled",
    ]


def test_readiness_default_path_without_builder_signal_is_unchanged() -> None:
    readiness = flow_builder_readiness_contract()

    assert readiness.ready_for_runtime_generation is False
    assert readiness.ready_for_retrieved_update_set_handoff is False
    assert readiness.blocked_reason == "Flow Designer builder is not implemented"
    assert readiness.unsupported_reason_codes == [
        "flow_builder_not_implemented",
        "runtime_generation_disabled",
        "retrieved_update_set_handoff_disabled",
    ]
    assert "flow_builder_implemented" in readiness.missing_evidence


def test_readiness_from_evidence_accepts_builder_availability_signal() -> None:
    bundle = _evidence_bundle()

    default_readiness = flow_builder_readiness_from_evidence(
        bundle=bundle,
        current_graph_hash=GRAPH_HASH,
    )
    flipped_readiness = flow_builder_readiness_from_evidence(
        bundle=bundle,
        current_graph_hash=GRAPH_HASH,
        builder_available=flow_builder_available(),
    )

    assert default_readiness.ready_for_retrieved_update_set_handoff is False
    assert default_readiness.missing_evidence == ["flow_builder_implemented"]
    assert flipped_readiness.ready_for_retrieved_update_set_handoff is True
    assert flipped_readiness.missing_evidence == []


def test_flow_builder_available_signal_is_true() -> None:
    assert flow_builder_available() is True
