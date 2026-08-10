from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from jedi_devproject.discovery.models import (
    DiscoveredField,
    InstanceDiscoveryContext,
    ServiceNowSurfaceContext,
    ServiceNowSurfaceContextBundle,
    ServiceNowSurfaceRecord,
)
from jedi_devproject.flow_builder import (
    FlowCustomerUpdateBuildResult,
    FlowGeneratedCustomerUpdate,
    FlowRetrievedNodeEvidence,
)
from jedi_devproject.flow_roundtrip import (
    FlowGraphNodeState,
    FlowGraphState,
    FlowRoundTripAssertion,
    FlowRoundTripReport,
)
from jedi_devproject.flow_xml_evidence import (
    FlowSnapshotEvidenceRecord,
    FlowXmlEvidenceBundle,
    FlowXmlShapeEvidenceRecord,
)


def test_context_and_flow_dto_validation_errors_do_not_echo_rejected_inputs() -> None:
    cases: list[tuple[type[BaseModel], dict[str, object], tuple[str, ...]]] = [
        (
            DiscoveredField,
            {
                "element": "u_secret_field",
                "column_label": "Secret Field",
                "internal_type": "string",
                "max_length": "secret-max-length",
            },
            ("u_secret_field", "secret-max-length"),
        ),
        (
            InstanceDiscoveryContext,
            {
                "target_table": "secret_table",
                "table_label": "Secret Table",
                "table_exists": "secret-table-exists",
                "supports_custom_fields": True,
            },
            ("secret_table", "secret-table-exists"),
        ),
        (
            ServiceNowSurfaceRecord,
            {
                "source_table": "sys_script",
                "name": "Secret Business Rule",
                "active": "secret-active",
                "metadata": {"script": "secret-script-body"},
            },
            ("Secret Business Rule", "secret-active", "secret-script-body"),
        ),
        (
            ServiceNowSurfaceContext,
            {
                "surface": "secret-surface",
                "source_table": "sys_script",
                "required": True,
                "records": [],
            },
            ("secret-surface",),
        ),
        (
            ServiceNowSurfaceContextBundle,
            {
                "target_table": "secret-target",
                "required_surfaces": ["secret-surface"],
                "surfaces": [],
                "table_context": "secret-table-context",
            },
            ("secret-target", "secret-surface", "secret-table-context"),
        ),
        (
            FlowRetrievedNodeEvidence,
            {
                "table": "secret-table",
                "sys_id": "secret-sys-id",
                "display_text": "secret-node-display",
            },
            ("secret-table", "secret-sys-id", "secret-node-display"),
        ),
        (
            FlowGeneratedCustomerUpdate,
            {
                "table": "sys_hub_action_instance",
                "record_sys_id": "secret-record-sys-id",
                "name": "secret-update-name",
                "update_type": "Flow Action",
                "target_name": "secret-target-name",
                "action": "secret-action",
                "payload": "secret-payload",
                "payload_sha256": "secret-payload-sha",
                "fields": {},
            },
            ("secret-action", "secret-payload"),
        ),
        (
            FlowCustomerUpdateBuildResult,
            {
                "builder_version": "secret-builder-version",
                "flow_name": "Secret Flow",
                "flow_sys_id": "secret-flow-sys-id",
                "target_table": "incident",
                "operation": "add_action",
                "graph_hash": "secret-graph-hash",
                "customer_updates": [],
                "requires_resnapshot_on_import": True,
                "snapshot_strategy_version": "v1",
                "readiness_contract_version": "v1",
                "evidence": [],
            },
            ("secret-builder-version", "secret-flow-sys-id", "secret-graph-hash"),
        ),
        (
            FlowGraphNodeState,
            {
                "table": "sys_hub_action_instance",
                "sys_id": "secret-node-sys-id",
                "fields": "secret-fields",
            },
            ("secret-node-sys-id", "secret-fields"),
        ),
        (
            FlowGraphState,
            {
                "flow_name": "Secret Flow",
                "flow_sys_id": "secret-flow-sys-id",
                "latest_snapshot": "secret-snapshot",
                "nodes": "secret-nodes",
                "graph_hash": "secret-graph-hash",
            },
            ("secret-flow-sys-id", "secret-nodes", "secret-graph-hash"),
        ),
        (
            FlowRoundTripAssertion,
            {
                "name": "secret-assertion",
                "passed": "secret-passed",
                "detail": "secret-detail",
            },
            ("secret-assertion", "secret-passed", "secret-detail"),
        ),
        (
            FlowRoundTripReport,
            {
                "version": "secret-version",
                "flow_name": "Secret Flow",
                "flow_sys_id": "secret-flow-sys-id",
                "operation": "add_action",
                "update_set_name": "secret-update-set",
                "update_set_remote_sys_id": "secret-remote-update-set",
                "customer_update_names": [],
                "graph_hash_before": "secret-before",
                "assertions": [],
            },
            ("secret-version", "secret-remote-update-set", "secret-before"),
        ),
        (
            FlowXmlShapeEvidenceRecord,
            {
                "table": "sys_hub_action_instance",
                "customer_update_name": "secret-customer-update",
                "status": "secret-status",
            },
            ("secret-customer-update", "secret-status"),
        ),
        (
            FlowSnapshotEvidenceRecord,
            {
                "snapshot_table": "secret-snapshot-table",
                "snapshot_reference_field": "latest_snapshot",
                "status": "collected",
                "snapshot_sys_id": "secret-snapshot-sys-id",
            },
            ("secret-snapshot-table", "secret-snapshot-sys-id"),
        ),
        (
            FlowXmlEvidenceBundle,
            {
                "version": "secret-version",
                "repository_version": "flow-xml-shapes-v1",
                "flow_name": "Secret Flow",
                "flow_sys_id": "secret-flow-sys-id",
                "retrieved_graph_hash": "secret-graph-hash",
                "shapes": [],
                "snapshot": "secret-snapshot",
                "evidence": [],
            },
            ("secret-version", "secret-flow-sys-id", "secret-snapshot"),
        ),
    ]

    for model_class, values, secret_fragments in cases:
        with pytest.raises(ValidationError) as exc_info:
            model_class.model_validate(values)

        error_text = str(exc_info.value)
        assert "input_value" not in error_text
        for fragment in secret_fragments:
            assert fragment not in error_text
