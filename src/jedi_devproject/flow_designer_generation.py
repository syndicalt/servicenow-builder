from __future__ import annotations

import json
import re
from typing import Any, Literal
from xml.etree import ElementTree

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
    xml_shape_repository_version: str
    xml_shape_tables: list[str]
    customer_update_strategy_version: str
    snapshot_update_strategy_version: str
    preview_commit_review_strategy_version: str
    readiness_contract_version: str
    ready_for_runtime_generation: bool
    ready_for_retrieved_update_set_handoff: bool
    readiness_blocked_reason: str
    unsupported_reason_codes: list[str]
    unsupported_reason_guidance: list[FlowUnsupportedReasonGuidance]
    missing_builder_evidence: list[str]


class FlowXmlShape(BaseModel):
    model_config = ConfigDict(extra="forbid")

    table: str
    update_type: str
    root_element: Literal["record_update"]
    record_element: str
    action: Literal["INSERT_OR_UPDATE"]
    required_fields: list[str]
    forbidden_fields: list[str] = Field(default_factory=list)
    review_notes: list[str]


class FlowXmlShapeRepository(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal["flow-xml-shapes-v1"]
    runtime_generation_enabled: bool
    retrieved_update_set_handoff_enabled: bool
    shapes: list[FlowXmlShape]
    evidence: list[str]

    def shape(self, table: str) -> FlowXmlShape:
        for shape in self.shapes:
            if shape.table == table:
                return shape
        raise KeyError(f"Flow XML shape not found: {table}")


class FlowXmlShapeEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    table: str
    repository_version: Literal["flow-xml-shapes-v1"]
    root_element: Literal["record_update"]
    record_element: str
    action: Literal["INSERT_OR_UPDATE"]
    required_fields_present: list[str]
    forbidden_fields_absent: bool
    runtime_generation_enabled: bool
    retrieved_update_set_handoff_enabled: bool


class FlowCustomerUpdateStrategy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal["flow-customer-update-strategy-v1"]
    naming_pattern: Literal["table_sys_id"]
    runtime_generation_enabled: bool
    retrieved_update_set_handoff_enabled: bool
    rollback_strategy_by_operation: dict[FlowGraphDiffOperation, str]
    evidence: list[str]

    def customer_update_name(self, table: str, sys_id: str) -> str:
        flow_xml_shape_repository().shape(table)
        cleaned_sys_id = sys_id.strip()
        if not re.fullmatch(r"[a-fA-F0-9]{32}", cleaned_sys_id):
            raise ValueError("Flow customer update sys_id must be 32 hex characters")
        return f"{table}_{cleaned_sys_id.lower()}"


class FlowSnapshotUpdateStrategy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal["flow-snapshot-update-strategy-v1"]
    flow_record_table: Literal["sys_hub_flow"]
    snapshot_reference_field: Literal["latest_snapshot"]
    unsupported_mutation_tables: list[str]
    runtime_generation_enabled: bool
    retrieved_update_set_handoff_enabled: bool
    evidence: list[str]

    def validate_latest_snapshot(self, latest_snapshot: str) -> str:
        cleaned = latest_snapshot.strip()
        if cleaned == "":
            raise ValueError("Flow latest_snapshot evidence is required")
        if not re.fullmatch(r"[a-fA-F0-9]{32}", cleaned):
            raise ValueError("Flow latest_snapshot must be 32 hex characters")
        return cleaned.lower()

    def validate_mutation_table(self, table: str) -> str:
        cleaned = table.strip()
        if cleaned in self.unsupported_mutation_tables:
            raise ValueError("Flow snapshot table mutation is not supported")
        flow_xml_shape_repository().shape(cleaned)
        return cleaned


class FlowPreviewCommitReviewStrategy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal["flow-preview-commit-review-strategy-v1"]
    review_boundary: Literal["retrieved_update_set_preview_commit"]
    runtime_generation_enabled: bool
    retrieved_update_set_handoff_enabled: bool
    auto_commit_enabled: bool
    require_preview: bool
    require_human_commit: bool
    evidence: list[str]

    def validate_review_request(self, *, auto_commit: bool, preview_requested: bool) -> None:
        if auto_commit:
            raise ValueError("Flow Designer auto-commit is not supported")
        if not preview_requested:
            raise ValueError("Flow Designer preview is required before commit")


class FlowBuilderReadinessContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal["flow-builder-readiness-v1"]
    required_evidence: list[str]
    missing_evidence: list[str]
    ready_for_runtime_generation: bool
    ready_for_retrieved_update_set_handoff: bool
    blocked_reason: str
    unsupported_reason_codes: list[str]
    unsupported_reason_guidance: list[FlowUnsupportedReasonGuidance]


class FlowUnsupportedReasonGuidance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    summary: str
    operator_action: Literal["route_to_human_review"]
    work_note: str


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
    repository = flow_xml_shape_repository()
    strategy = flow_customer_update_strategy()
    snapshot_strategy = flow_snapshot_update_strategy()
    review_strategy = flow_preview_commit_review_strategy()
    readiness = flow_builder_readiness_contract()
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
            "xml_shape_evidence_validator_available",
            "customer_update_name_strategy_defined",
            "flow_snapshot_update_strategy_defined",
            "rollback_customer_update_strategy_defined",
            "servicenow_preview_commit_review_required",
        ],
        xml_shape_repository_version=repository.version,
        xml_shape_tables=[shape.table for shape in repository.shapes],
        customer_update_strategy_version=strategy.version,
        snapshot_update_strategy_version=snapshot_strategy.version,
        preview_commit_review_strategy_version=review_strategy.version,
        readiness_contract_version=readiness.version,
        ready_for_runtime_generation=readiness.ready_for_runtime_generation,
        ready_for_retrieved_update_set_handoff=readiness.ready_for_retrieved_update_set_handoff,
        readiness_blocked_reason=readiness.blocked_reason,
        unsupported_reason_codes=readiness.unsupported_reason_codes,
        unsupported_reason_guidance=readiness.unsupported_reason_guidance,
        missing_builder_evidence=readiness.missing_evidence,
    )


def validate_flow_xml_shape_evidence(*, table: str, xml_payload: str) -> FlowXmlShapeEvidence:
    repository = flow_xml_shape_repository()
    shape = repository.shape(table)
    try:
        root = ElementTree.fromstring(xml_payload)
    except ElementTree.ParseError as exc:
        raise ValueError("Flow XML shape evidence is not valid XML") from exc
    if root.tag != shape.root_element:
        raise ValueError(f"Flow XML shape evidence root must be {shape.root_element}")
    record = root.find(shape.record_element)
    if record is None:
        raise ValueError(f"Flow XML shape evidence missing record element: {shape.record_element}")
    if record.attrib.get("action") != shape.action:
        raise ValueError(f"Flow XML shape evidence action must be {shape.action}")
    child_tags = {child.tag for child in record}
    required_fields_present: list[str] = []
    for field_name in shape.required_fields:
        field = record.find(field_name)
        if field is None or (field.text is None or field.text.strip() == ""):
            raise ValueError(f"Flow XML shape evidence missing required field: {field_name}")
        required_fields_present.append(field_name)
    for field_name in shape.forbidden_fields:
        if field_name in child_tags:
            raise ValueError(f"Flow XML shape evidence contains forbidden field: {field_name}")
    return FlowXmlShapeEvidence(
        table=shape.table,
        repository_version=repository.version,
        root_element=shape.root_element,
        record_element=shape.record_element,
        action=shape.action,
        required_fields_present=required_fields_present,
        forbidden_fields_absent=True,
        runtime_generation_enabled=repository.runtime_generation_enabled,
        retrieved_update_set_handoff_enabled=repository.retrieved_update_set_handoff_enabled,
    )


def flow_customer_update_strategy() -> FlowCustomerUpdateStrategy:
    return FlowCustomerUpdateStrategy(
        version="flow-customer-update-strategy-v1",
        naming_pattern="table_sys_id",
        runtime_generation_enabled=False,
        retrieved_update_set_handoff_enabled=False,
        rollback_strategy_by_operation={
            "add_action": (
                "Rollback removes the generated sys_hub_action_instance customer update and "
                "restores the previously retrieved graph ordering evidence."
            ),
            "update_condition": (
                "Rollback restores the previous sys_hub_flow_logic_instance_v2 condition value "
                "from retrieved graph evidence."
            ),
        },
        evidence=[
            "customer_update_name_strategy_defined",
            "rollback_customer_update_strategy_defined",
            "runtime_generation_disabled",
            "retrieved_update_set_handoff_disabled",
        ],
    )


def flow_snapshot_update_strategy() -> FlowSnapshotUpdateStrategy:
    return FlowSnapshotUpdateStrategy(
        version="flow-snapshot-update-strategy-v1",
        flow_record_table="sys_hub_flow",
        snapshot_reference_field="latest_snapshot",
        unsupported_mutation_tables=[
            "sys_hub_flow_snapshot",
            "sys_hub_flow_snapshot_blob",
            "sys_hub_flow_version",
        ],
        runtime_generation_enabled=False,
        retrieved_update_set_handoff_enabled=False,
        evidence=[
            "flow_snapshot_update_strategy_defined",
            "latest_snapshot_evidence_required",
            "snapshot_table_mutation_blocked",
            "runtime_generation_disabled",
            "retrieved_update_set_handoff_disabled",
        ],
    )


def flow_preview_commit_review_strategy() -> FlowPreviewCommitReviewStrategy:
    return FlowPreviewCommitReviewStrategy(
        version="flow-preview-commit-review-strategy-v1",
        review_boundary="retrieved_update_set_preview_commit",
        runtime_generation_enabled=False,
        retrieved_update_set_handoff_enabled=False,
        auto_commit_enabled=False,
        require_preview=True,
        require_human_commit=True,
        evidence=[
            "servicenow_preview_commit_review_required",
            "flow_auto_commit_disabled",
            "human_commit_required",
            "runtime_generation_disabled",
            "retrieved_update_set_handoff_disabled",
        ],
    )


def flow_builder_readiness_contract(
    *,
    available_evidence: set[str] | None = None,
) -> FlowBuilderReadinessContract:
    required_evidence = [
        "retrieved_graph_hash_matches_existing_graph_hash",
        "diff_references_only_retrieved_nodes",
        "diff_operation_is_add_action_or_update_condition",
        "xml_shape_repository_available",
        "xml_shape_evidence_validator_available",
        "customer_update_name_strategy_defined",
        "flow_snapshot_update_strategy_defined",
        "rollback_customer_update_strategy_defined",
        "servicenow_preview_commit_review_required",
    ]
    evidence = set(required_evidence) if available_evidence is None else available_evidence
    missing_evidence = [item for item in required_evidence if item not in evidence]
    return FlowBuilderReadinessContract(
        version="flow-builder-readiness-v1",
        required_evidence=required_evidence,
        missing_evidence=missing_evidence,
        ready_for_runtime_generation=False,
        ready_for_retrieved_update_set_handoff=False,
        blocked_reason="Flow Designer builder is not implemented",
        unsupported_reason_codes=[
            "flow_builder_not_implemented",
            "runtime_generation_disabled",
            "retrieved_update_set_handoff_disabled",
        ],
        unsupported_reason_guidance=flow_unsupported_reason_guidance(),
    )


def flow_unsupported_reason_guidance() -> list[FlowUnsupportedReasonGuidance]:
    return [
        FlowUnsupportedReasonGuidance(
            code="flow_builder_not_implemented",
            summary="Flow Designer builder is not implemented.",
            operator_action="route_to_human_review",
            work_note=(
                "Flow Designer automation is context/preflight-only. Route this story to "
                "human review or manual developer build."
            ),
        ),
        FlowUnsupportedReasonGuidance(
            code="runtime_generation_disabled",
            summary="Flow Designer runtime generation is disabled.",
            operator_action="route_to_human_review",
            work_note=(
                "The Flow Designer generation path is disabled until XML builder evidence "
                "and preview/commit controls are implemented."
            ),
        ),
        FlowUnsupportedReasonGuidance(
            code="retrieved_update_set_handoff_disabled",
            summary="Flow Designer retrieved Update Set handoff is disabled.",
            operator_action="route_to_human_review",
            work_note=(
                "No Flow Designer retrieved Update Set will be created by automation. "
                "Use ServiceNow review for manually prepared Flow changes."
            ),
        ),
    ]


def flow_xml_shape_repository() -> FlowXmlShapeRepository:
    return FlowXmlShapeRepository(
        version="flow-xml-shapes-v1",
        runtime_generation_enabled=False,
        retrieved_update_set_handoff_enabled=False,
        shapes=[
            FlowXmlShape(
                table="sys_hub_flow",
                update_type="Flow",
                root_element="record_update",
                record_element="sys_hub_flow",
                action="INSERT_OR_UPDATE",
                required_fields=[
                    "sys_id",
                    "sys_update_name",
                    "name",
                    "active",
                    "status",
                    "latest_snapshot",
                ],
                forbidden_fields=[
                    "sys_created_by",
                    "sys_created_on",
                    "sys_domain",
                    "sys_domain_path",
                    "sys_updated_by",
                    "sys_updated_on",
                ],
                review_notes=[
                    "Flow shape is repository evidence only; it is not generated at runtime.",
                    "Snapshot strategy must be proven before this shape can be emitted.",
                ],
            ),
            FlowXmlShape(
                table="sys_hub_action_instance",
                update_type="Flow Action Instance",
                root_element="record_update",
                record_element="sys_hub_action_instance",
                action="INSERT_OR_UPDATE",
                required_fields=[
                    "sys_id",
                    "sys_update_name",
                    "flow",
                    "action_type",
                    "display_text",
                    "order",
                ],
                forbidden_fields=[
                    "action_inputs",
                    "compiled_snapshot",
                    "sys_created_by",
                    "sys_created_on",
                    "sys_updated_by",
                    "sys_updated_on",
                ],
                review_notes=[
                    "Action inputs require a separate value mapping strategy.",
                    "Custom actions, spokes, credentials, scripts, and endpoints remain forbidden.",
                ],
            ),
            FlowXmlShape(
                table="sys_hub_flow_logic_instance_v2",
                update_type="Flow Logic Instance",
                root_element="record_update",
                record_element="sys_hub_flow_logic_instance_v2",
                action="INSERT_OR_UPDATE",
                required_fields=[
                    "sys_id",
                    "sys_update_name",
                    "flow",
                    "logic_definition",
                    "display_text",
                    "order",
                ],
                forbidden_fields=[
                    "values",
                    "decision_table",
                    "workflow_reference",
                    "sys_created_by",
                    "sys_created_on",
                    "sys_updated_by",
                    "sys_updated_on",
                ],
                review_notes=[
                    (
                        "Condition value serialization must be proven before this shape can be "
                        "emitted."
                    ),
                    "Workflow references and approval orchestration remain forbidden.",
                ],
            ),
        ],
        evidence=[
            "xml_shape_repository_available",
            "flow_shapes_are_review_metadata_only",
            "runtime_generation_disabled",
            "retrieved_update_set_handoff_disabled",
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
