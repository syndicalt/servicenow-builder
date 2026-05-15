from __future__ import annotations

import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from jedi_devproject.models import CandidateChange

FlowGraphDiffOperation = Literal["add_action", "update_condition"]


class FlowGraphDiffStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: FlowGraphDiffOperation
    node_id: str
    summary: str
    after_node_id: str | None = None
    action_type: str = ""
    inputs: dict[str, Any] = Field(default_factory=dict)

    @field_validator("node_id", "summary")
    @classmethod
    def require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned == "":
            raise ValueError("must not be empty")
        return cleaned


class FlowGraphDiffIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: Literal["flow_modify"]
    flow_name: str
    flow_sys_id_or_stable_key: str
    target_table: str
    trigger_summary: str
    existing_graph_hash: str
    requested_graph_diff: list[FlowGraphDiffStep]
    affected_nodes: list[str]
    affected_edges: list[str]
    customer_update_records: list[dict[str, Any]]
    test_plan: list[str]
    rollback_notes: list[str]
    reviewer_notes: list[str] = Field(default_factory=list)

    @field_validator(
        "flow_name",
        "flow_sys_id_or_stable_key",
        "target_table",
        "trigger_summary",
        "existing_graph_hash",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned == "":
            raise ValueError("must not be empty")
        return cleaned

    @model_validator(mode="after")
    def validate_flow_graph_boundary(self) -> FlowGraphDiffIntent:
        if not self.requested_graph_diff:
            raise ValueError("Flow graph diff requires at least one diff step")
        if not self.test_plan:
            raise ValueError("Flow graph diff requires a test plan")
        if not self.rollback_notes:
            raise ValueError("Flow graph diff requires rollback notes")
        if not _looks_like_hash(self.existing_graph_hash):
            raise ValueError("Flow graph diff existing_graph_hash must be a stable hash")
        _validate_no_raw_xml(self.customer_update_records)
        _validate_safe_payload(self.model_dump(mode="json"))
        return self


class FlowGraphBuilderPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: Literal["flow_modify"]
    flow_name: str
    target_table: str
    operation_count: int
    runtime_generation_enabled: bool
    retrieved_update_set_handoff_enabled: bool
    graph_hash_verified: bool
    blocked_reason: str
    required_customer_update_tables: list[str]
    preflight_checks: list[str]
    required_builder_evidence: list[str]


def validate_flow_graph_diff_candidate(
    *,
    changes: list[CandidateChange],
    retrieved_node_ids: set[str],
) -> FlowGraphDiffIntent:
    if len(changes) != 1:
        raise ValueError("Flow graph diff validation requires exactly one change")
    change = changes[0]
    if change.table != "sys_hub_flow_graph_diff":
        raise ValueError("Flow graph diff validation requires sys_hub_flow_graph_diff")
    if change.operation != "update":
        raise ValueError("Flow graph diff validation supports update only")
    try:
        intent = FlowGraphDiffIntent.model_validate(dict(change.fields))
    except ValidationError as exc:
        if "requested_graph_diff" in str(exc) and "operation" in str(exc):
            raise ValueError("unsupported Flow graph diff operation") from exc
        raise
    _validate_retrieved_nodes(intent=intent, retrieved_node_ids=retrieved_node_ids)
    return intent


def plan_flow_graph_builder(
    *,
    changes: list[CandidateChange],
    retrieved_node_ids: set[str],
    retrieved_graph_hash: str,
) -> FlowGraphBuilderPlan:
    intent = validate_flow_graph_diff_candidate(
        changes=changes,
        retrieved_node_ids=retrieved_node_ids,
    )
    if intent.customer_update_records:
        raise ValueError("Flow builder design does not accept customer updates")
    if intent.existing_graph_hash != retrieved_graph_hash:
        raise ValueError("retrieved graph hash does not match Flow graph diff")
    return FlowGraphBuilderPlan(
        capability=intent.capability,
        flow_name=intent.flow_name,
        target_table=intent.target_table,
        operation_count=len(intent.requested_graph_diff),
        runtime_generation_enabled=False,
        retrieved_update_set_handoff_enabled=False,
        graph_hash_verified=True,
        blocked_reason="Flow Designer builder is design-only",
        required_customer_update_tables=[
            "sys_hub_flow",
            "sys_hub_action_instance",
            "sys_hub_flow_logic_instance_v2",
        ],
        preflight_checks=[
            "retrieved_graph_hash_matches_existing_graph_hash",
            "diff_references_only_retrieved_nodes",
            "diff_operation_is_add_action_or_update_condition",
            "runtime_history_tables_excluded",
            "forbidden_flow_tokens_absent",
            "retrieved_update_set_handoff_disabled",
        ],
        required_builder_evidence=[
            "xml_shape_repository_available",
            "customer_update_name_strategy_defined",
            "flow_snapshot_update_strategy_defined",
            "rollback_customer_update_strategy_defined",
            "servicenow_preview_commit_review_required",
        ],
    )


def _validate_retrieved_nodes(
    *,
    intent: FlowGraphDiffIntent,
    retrieved_node_ids: set[str],
) -> None:
    if not retrieved_node_ids:
        raise ValueError("Flow graph diff validation requires retrieved graph nodes")
    existing_node_references = {intent.flow_sys_id_or_stable_key, *intent.affected_nodes}
    for step in intent.requested_graph_diff:
        if step.after_node_id:
            existing_node_references.add(step.after_node_id)
    for node_id in sorted(existing_node_references):
        if node_id not in retrieved_node_ids:
            raise ValueError(f"Flow graph diff references unretrieved node: {node_id}")


def _validate_no_raw_xml(customer_update_records: list[dict[str, Any]]) -> None:
    raw_text = json.dumps(customer_update_records, sort_keys=True, default=str)
    if re.search(r"<\s*/?\s*(record_update|sys_hub_|xml|sys_update_xml)", raw_text, re.I):
        raise ValueError("Flow graph diff must not include raw XML")


FORBIDDEN_FLOW_TOKENS = [
    "custom action",
    "custom_action",
    "script",
    "spoke",
    "credential",
    "password",
    "token",
    "api_key",
    "http://",
    "https://",
    "subflow",
    "approval",
    "RESTMessageV2",
    "SOAPMessageV2",
]


def _validate_safe_payload(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, sort_keys=True, default=str).lower()
    for token in FORBIDDEN_FLOW_TOKENS:
        if token.lower() in text:
            raise ValueError(f"forbidden Flow graph diff token: {token}")


def _looks_like_hash(value: str) -> bool:
    cleaned = value.strip()
    return bool(re.fullmatch(r"[a-fA-F0-9]{32,128}", cleaned))
