"""Deterministic Flow Designer graph-diff to customer-update builder.

This module implements the ``flow_builder_implemented`` readiness requirement
(roadmap item 4.2.2, ADR 0011 sprints 124-138). It converts a validated
``FlowGraphDiffIntent`` plus a validated ``FlowXmlEvidenceBundle`` into
``sys_update_xml`` customer-update payloads for the approved narrow subset
only:

- ``add_action``: one ``sys_hub_action_instance`` insert plus the one
  ``sys_hub_flow_logic_instance_v2`` edge splice after the named retrieved
  node (the named node must be a retrieved action or flow-logic record).
- ``update_condition``: one narrow condition update on one retrieved
  ``sys_hub_flow_logic_instance_v2`` node of a record-triggered flow.

Everything else fails closed. The builder consumes only validated evidence
and validated structured diffs; it never accepts raw model XML
(``FlowGraphDiffIntent`` rejects raw XML and forbidden Flow tokens, and the
builder additionally rejects provider-supplied customer-update records).
Generated payloads are re-validated against ``flow-xml-shapes-v1`` via
``validate_flow_xml_shape_evidence`` before they are returned, so the builder
can never emit a record shape the evidence collector did not prove.

Snapshot decision (``flow-snapshot-update-strategy-v1``, sprint 131): the
strategy forbids mutating ``sys_hub_flow_snapshot``,
``sys_hub_flow_snapshot_blob``, and ``sys_hub_flow_version``, and requires
retrieved ``latest_snapshot`` evidence. The builder therefore never
hand-mutates the snapshot and never emits a ``sys_hub_flow`` record update:
it emits only the action/logic customer updates and marks the flow for
platform re-snapshot on import (``requires_resnapshot_on_import=True``).
Post-import snapshot regeneration evidence is verified by the round-trip
harness (``flow_roundtrip``), exactly as the strategy requires.

ServiceNow Retrieved Update Set preview/commit remains the human review
boundary; this module produces customer-update payloads only and never
imports or commits anything itself.
"""

from __future__ import annotations

import hashlib
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from jedi_devproject.flow_designer_generation import (
    FlowGraphDiffIntent,
    FlowGraphDiffOperation,
    FlowGraphDiffStep,
    flow_builder_readiness_contract,
    flow_customer_update_strategy,
    flow_snapshot_update_strategy,
    flow_xml_shape_repository,
    validate_flow_xml_shape_evidence,
)
from jedi_devproject.flow_xml_evidence import FlowXmlEvidenceBundle
from jedi_devproject.xml_builder import container_element, record_update, text_element

FLOW_BUILDER_VERSION: Literal["flow-builder-v1"] = "flow-builder-v1"

# Deterministic logic definition emitted for the additive edge splice. The
# edge record connects the named retrieved node to the generated action via
# ``connected_to``; sequencing semantics are reconciled by the platform
# re-snapshot on import (see module docstring).
FLOW_EDGE_LOGIC_DEFINITION = "SEQUENCE"

FlowBuilderNodeTable = Literal["sys_hub_action_instance", "sys_hub_flow_logic_instance_v2"]

_SYS_ID_PATTERN = r"[a-f0-9]{32}"


def flow_builder_available() -> bool:
    """Builder availability signal for the readiness contract.

    ``flow_builder_readiness_contract(builder_available=...)`` consumes this
    so that the ``flow_builder_implemented`` requirement is satisfied only by
    importing the implemented builder, never by hand-set flags elsewhere.
    """
    return True


def stable_flow_sys_id(*parts: str) -> str:
    """Deterministic 32-hex sys_id (same approach as the catalog builder)."""
    payload = "|".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


class FlowRetrievedNodeEvidence(BaseModel):
    """One retrieved flow graph node the builder may reference.

    Node evidence comes from instance retrieval (discovery / the round-trip
    harness), never from the model. Only action and flow-logic nodes can be
    referenced by the narrow subset; trigger records remain read-only.
    """

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    table: FlowBuilderNodeTable
    sys_id: str
    display_text: str = ""
    order: int = 0
    action_type: str = ""
    logic_definition: str = ""
    connected_to: str = ""
    condition: str = ""

    @field_validator("sys_id")
    @classmethod
    def require_stable_sys_id(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not re.fullmatch(_SYS_ID_PATTERN, cleaned):
            raise ValueError("retrieved node sys_id must be 32 hex characters")
        return cleaned


class FlowGeneratedCustomerUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    table: str
    record_sys_id: str
    name: str
    update_type: str
    target_name: str
    action: Literal["INSERT_OR_UPDATE"]
    payload: str
    payload_sha256: str
    fields: dict[str, str]

    def handoff_record(self) -> dict[str, str]:
        """Customer-update record in the shape the handoff plumbing expects."""
        return {
            "name": self.name,
            "action": self.action,
            "type": self.update_type,
            "target_name": self.target_name,
            "payload": self.payload,
            "application": "global",
        }


class FlowCustomerUpdateBuildResult(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    builder_version: Literal["flow-builder-v1"]
    flow_name: str
    flow_sys_id: str
    target_table: str
    operation: FlowGraphDiffOperation
    graph_hash: str
    customer_updates: list[FlowGeneratedCustomerUpdate]
    requires_resnapshot_on_import: Literal[True]
    snapshot_strategy_version: str
    readiness_contract_version: str
    evidence: list[str]


def build_flow_customer_updates(
    *,
    intent: FlowGraphDiffIntent,
    evidence_bundle: FlowXmlEvidenceBundle,
    retrieved_nodes: list[FlowRetrievedNodeEvidence],
) -> FlowCustomerUpdateBuildResult:
    """Build customer updates for one validated narrow Flow graph diff.

    Fails closed unless the evidence-driven readiness contract (with the
    builder availability signal) is fully ready, the intent's
    ``existing_graph_hash`` matches the evidence bundle's graph hash, and the
    diff is exactly one approved ``add_action`` or ``update_condition`` step
    that references only retrieved nodes.
    """
    if intent.customer_update_records:
        raise ValueError("Flow builder does not accept provider customer updates")
    flow_sys_id = _validated_flow_sys_id(intent=intent, evidence_bundle=evidence_bundle)
    intent_hash = intent.existing_graph_hash.strip().lower()
    if intent_hash != evidence_bundle.retrieved_graph_hash:
        raise ValueError(
            "stale Flow XML evidence: existing_graph_hash does not match evidence graph hash"
        )
    readiness = flow_builder_readiness_contract(
        runtime_evidence=evidence_bundle.readiness_summary(current_graph_hash=intent_hash),
        builder_available=flow_builder_available(),
    )
    if not (
        readiness.ready_for_runtime_generation
        and readiness.ready_for_retrieved_update_set_handoff
    ):
        raise ValueError(
            "Flow builder readiness contract is not satisfied: "
            + (", ".join(readiness.missing_evidence) or readiness.blocked_reason)
        )
    if len(intent.requested_graph_diff) != 1:
        raise ValueError("Flow builder supports exactly one graph diff step")
    step = intent.requested_graph_diff[0]
    nodes = _node_map(retrieved_nodes)
    snapshot_strategy = flow_snapshot_update_strategy()
    if step.operation == "add_action":
        records = _add_action_records(step=step, flow_sys_id=flow_sys_id, nodes=nodes)
    else:
        records = _update_condition_records(step=step, flow_sys_id=flow_sys_id, nodes=nodes)
    customer_updates = [
        _flow_customer_update(
            table=snapshot_strategy.validate_mutation_table(table),
            fields=fields,
            target_name=fields["display_text"],
        )
        for table, fields in records
    ]
    return FlowCustomerUpdateBuildResult(
        builder_version=FLOW_BUILDER_VERSION,
        flow_name=intent.flow_name,
        flow_sys_id=flow_sys_id,
        target_table=intent.target_table,
        operation=step.operation,
        graph_hash=intent_hash,
        customer_updates=customer_updates,
        requires_resnapshot_on_import=True,
        snapshot_strategy_version=snapshot_strategy.version,
        readiness_contract_version=readiness.version,
        evidence=[
            *(
                f"flow_builder:{step.operation}:{update.table}:generated"
                for update in customer_updates
            ),
            "flow_xml_shape_evidence_revalidated",
            "snapshot_table_mutation_blocked",
            "flow_resnapshot_on_import_required",
            "retrieved_update_set_preview_commit_required",
        ],
    )


def _validated_flow_sys_id(
    *,
    intent: FlowGraphDiffIntent,
    evidence_bundle: FlowXmlEvidenceBundle,
) -> str:
    if intent.flow_name != evidence_bundle.flow_name:
        raise ValueError("Flow builder evidence bundle is for a different flow")
    flow_sys_id = evidence_bundle.flow_sys_id.strip().lower()
    if not re.fullmatch(_SYS_ID_PATTERN, flow_sys_id):
        raise ValueError("Flow builder evidence flow sys_id must be 32 hex characters")
    intent_key = intent.flow_sys_id_or_stable_key.strip().lower()
    if re.fullmatch(_SYS_ID_PATTERN, intent_key) and intent_key != flow_sys_id:
        raise ValueError("Flow builder evidence bundle is for a different flow")
    return flow_sys_id


def _node_map(
    retrieved_nodes: list[FlowRetrievedNodeEvidence],
) -> dict[str, FlowRetrievedNodeEvidence]:
    if not retrieved_nodes:
        raise ValueError("Flow builder requires retrieved graph nodes")
    nodes: dict[str, FlowRetrievedNodeEvidence] = {}
    for node in retrieved_nodes:
        if node.sys_id in nodes:
            raise ValueError(f"Flow builder retrieved nodes are ambiguous: {node.sys_id}")
        nodes[node.sys_id] = node
    return nodes


def _add_action_records(
    *,
    step: FlowGraphDiffStep,
    flow_sys_id: str,
    nodes: dict[str, FlowRetrievedNodeEvidence],
) -> list[tuple[str, dict[str, str]]]:
    if step.action_type.strip() == "":
        raise ValueError("Flow builder add_action requires an action_type")
    after_node_id = (step.after_node_id or "").strip().lower()
    if after_node_id == "" or after_node_id not in nodes:
        raise ValueError(f"Flow graph diff references unretrieved node: {step.after_node_id}")
    if step.node_id.strip().lower() in nodes:
        raise ValueError(f"Flow builder add_action node already exists: {step.node_id}")
    after_node = nodes[after_node_id]
    strategy = flow_customer_update_strategy()
    action_sys_id = stable_flow_sys_id("sys_hub_action_instance", flow_sys_id, step.node_id)
    edge_sys_id = stable_flow_sys_id(
        "sys_hub_flow_logic_instance_v2", flow_sys_id, after_node.sys_id, step.node_id
    )
    action_fields = {
        "sys_id": action_sys_id,
        "sys_update_name": strategy.customer_update_name("sys_hub_action_instance", action_sys_id),
        "flow": flow_sys_id,
        "action_type": step.action_type.strip(),
        "display_text": step.summary,
        "order": str(after_node.order + 1),
    }
    edge_fields = {
        "sys_id": edge_sys_id,
        "sys_update_name": strategy.customer_update_name(
            "sys_hub_flow_logic_instance_v2", edge_sys_id
        ),
        "flow": flow_sys_id,
        "logic_definition": FLOW_EDGE_LOGIC_DEFINITION,
        "display_text": f"Connect after {after_node.display_text}",
        "order": str(after_node.order + 2),
        "connected_to": action_sys_id,
    }
    return [
        ("sys_hub_action_instance", action_fields),
        ("sys_hub_flow_logic_instance_v2", edge_fields),
    ]


def _update_condition_records(
    *,
    step: FlowGraphDiffStep,
    flow_sys_id: str,
    nodes: dict[str, FlowRetrievedNodeEvidence],
) -> list[tuple[str, dict[str, str]]]:
    node_id = step.node_id.strip().lower()
    if node_id not in nodes:
        raise ValueError(f"Flow graph diff references unretrieved node: {step.node_id}")
    node = nodes[node_id]
    if node.table != "sys_hub_flow_logic_instance_v2":
        raise ValueError("Flow builder update_condition requires a retrieved flow logic node")
    extra_inputs = sorted(set(step.inputs) - {"condition"})
    if extra_inputs:
        raise ValueError(
            "Flow builder update_condition accepts only the condition input: "
            + ", ".join(extra_inputs)
        )
    condition = str(step.inputs.get("condition") or "").strip()
    if condition == "":
        raise ValueError("Flow builder update_condition requires a condition input")
    if node.logic_definition.strip() == "":
        raise ValueError("Flow builder update_condition requires retrieved logic_definition")
    strategy = flow_customer_update_strategy()
    fields = {
        "sys_id": node.sys_id,
        "sys_update_name": strategy.customer_update_name(
            "sys_hub_flow_logic_instance_v2", node.sys_id
        ),
        "flow": flow_sys_id,
        "logic_definition": node.logic_definition,
        "display_text": node.display_text,
        "order": str(node.order),
        "condition": condition,
    }
    if node.connected_to:
        fields["connected_to"] = node.connected_to
    return [("sys_hub_flow_logic_instance_v2", fields)]


def _flow_customer_update(
    *,
    table: str,
    fields: dict[str, str],
    target_name: str,
) -> FlowGeneratedCustomerUpdate:
    shape = flow_xml_shape_repository().shape(table)
    extra_fields = sorted(set(fields) - set(shape.required_fields))
    ordered_fields = [*shape.required_fields, *extra_fields]
    payload = record_update(
        container_element(
            shape.record_element,
            *(text_element(name, fields[name]) for name in ordered_fields),
            action=shape.action,
        ),
        table=shape.table,
    )
    validate_flow_xml_shape_evidence(table=table, xml_payload=payload)
    return FlowGeneratedCustomerUpdate(
        table=shape.table,
        record_sys_id=fields["sys_id"],
        name=fields["sys_update_name"],
        update_type=shape.update_type,
        target_name=target_name,
        action="INSERT_OR_UPDATE",
        payload=payload,
        payload_sha256=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        fields=dict(fields),
    )
