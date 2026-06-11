from __future__ import annotations

import hashlib
from typing import Any

import pytest

from jedi_devproject.flow_designer_generation import (
    FlowRuntimeEvidenceSummary,
    flow_builder_readiness_contract,
)
from jedi_devproject.flow_xml_evidence import (
    FLOW_SNAPSHOT_EVIDENCE_MISSING_REASON,
    FLOW_SNAPSHOT_EVIDENCE_STALE_REASON,
    collect_flow_xml_evidence,
    flow_builder_readiness_from_evidence,
)

FLOW_SYS_ID = "f1" * 16
ACTION_SYS_ID = "a2" * 16
LOGIC_SYS_ID = "b3" * 16
SNAPSHOT_SYS_ID = "c4" * 16
GRAPH_HASH = "d5" * 32

FLOW_UPDATE_NAME = f"sys_hub_flow_{FLOW_SYS_ID}"
ACTION_UPDATE_NAME = f"sys_hub_action_instance_{ACTION_SYS_ID}"
LOGIC_UPDATE_NAME = f"sys_hub_flow_logic_instance_v2_{LOGIC_SYS_ID}"

FLOW_PAYLOAD = (
    '<record_update table="sys_hub_flow">'
    '<sys_hub_flow action="INSERT_OR_UPDATE">'
    f"<sys_id>{FLOW_SYS_ID}</sys_id>"
    f"<sys_update_name>{FLOW_UPDATE_NAME}</sys_update_name>"
    "<name>Incident Triage</name>"
    "<active>true</active>"
    "<status>published</status>"
    f"<latest_snapshot>{SNAPSHOT_SYS_ID}</latest_snapshot>"
    "</sys_hub_flow>"
    "</record_update>"
)
ACTION_PAYLOAD = (
    '<record_update table="sys_hub_action_instance">'
    '<sys_hub_action_instance action="INSERT_OR_UPDATE">'
    f"<sys_id>{ACTION_SYS_ID}</sys_id>"
    f"<sys_update_name>{ACTION_UPDATE_NAME}</sys_update_name>"
    f"<flow>{FLOW_SYS_ID}</flow>"
    "<action_type>core-create-task</action_type>"
    "<display_text>Create triage task</display_text>"
    "<order>100</order>"
    "</sys_hub_action_instance>"
    "</record_update>"
)
LOGIC_PAYLOAD = (
    '<record_update table="sys_hub_flow_logic_instance_v2">'
    '<sys_hub_flow_logic_instance_v2 action="INSERT_OR_UPDATE">'
    f"<sys_id>{LOGIC_SYS_ID}</sys_id>"
    f"<sys_update_name>{LOGIC_UPDATE_NAME}</sys_update_name>"
    f"<flow>{FLOW_SYS_ID}</flow>"
    "<logic_definition>IF</logic_definition>"
    "<display_text>If impact is high</display_text>"
    "<order>200</order>"
    "</sys_hub_flow_logic_instance_v2>"
    "</record_update>"
)


def _update_xml_row(*, name: str, update_type: str, payload: str) -> dict[str, Any]:
    return {
        "sys_id": "1" * 32,
        "name": name,
        "action": "INSERT_OR_UPDATE",
        "type": update_type,
        "target_name": "Incident Triage",
        "payload": payload,
    }


class FakeFlowEvidenceClient:
    def __init__(self) -> None:
        self.flow_records: list[dict[str, Any]] = [
            {
                "sys_id": FLOW_SYS_ID,
                "name": "Incident Triage",
                "active": "true",
                "status": "published",
                "latest_snapshot": {
                    "value": SNAPSHOT_SYS_ID,
                    "display_value": "Incident Triage v3",
                },
            }
        ]
        self.action_instances: list[dict[str, Any]] = [{"sys_id": ACTION_SYS_ID}]
        self.logic_instances: list[dict[str, Any]] = [{"sys_id": LOGIC_SYS_ID}]
        self.snapshot_records: list[dict[str, Any]] = [
            {
                "sys_id": SNAPSHOT_SYS_ID,
                "name": "Incident Triage",
                "parent_flow": FLOW_SYS_ID,
                "note": "autosaved snapshot",
            }
        ]
        self.update_xml: dict[str, dict[str, Any]] = {
            FLOW_UPDATE_NAME: _update_xml_row(
                name=FLOW_UPDATE_NAME, update_type="Flow", payload=FLOW_PAYLOAD
            ),
            ACTION_UPDATE_NAME: _update_xml_row(
                name=ACTION_UPDATE_NAME,
                update_type="Flow Action Instance",
                payload=ACTION_PAYLOAD,
            ),
            LOGIC_UPDATE_NAME: _update_xml_row(
                name=LOGIC_UPDATE_NAME,
                update_type="Flow Logic Instance",
                payload=LOGIC_PAYLOAD,
            ),
        }
        self.calls: list[dict[str, object]] = []

    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        self.calls.append({"table": table, "lookup": lookup, "fields": fields, "limit": limit})
        if table == "sys_hub_flow":
            return [
                record
                for record in self.flow_records
                if record.get("name") == lookup.get("name")
            ]
        if table == "sys_hub_action_instance" and lookup == {"flow": FLOW_SYS_ID}:
            return list(self.action_instances)
        if table == "sys_hub_flow_logic_instance_v2" and lookup == {"flow": FLOW_SYS_ID}:
            return list(self.logic_instances)
        if table == "sys_hub_flow_snapshot":
            return [
                record
                for record in self.snapshot_records
                if record.get("sys_id") == lookup.get("sys_id")
            ]
        if table == "sys_update_xml":
            row = self.update_xml.get(lookup.get("name", ""))
            return [dict(row)] if row else []
        return []


def _collect(client: FakeFlowEvidenceClient) -> Any:
    return collect_flow_xml_evidence(
        client=client,
        flow_name="Incident Triage",
        retrieved_graph_hash=GRAPH_HASH,
    )


def test_collects_and_validates_all_flow_xml_shape_evidence() -> None:
    bundle = _collect(FakeFlowEvidenceClient())

    assert bundle.version == "flow-xml-evidence-v1"
    assert bundle.repository_version == "flow-xml-shapes-v1"
    assert bundle.flow_sys_id == FLOW_SYS_ID
    assert bundle.retrieved_graph_hash == GRAPH_HASH
    assert [shape.status for shape in bundle.shapes] == ["validated", "validated", "validated"]
    flow_shape = bundle.shape("sys_hub_flow")
    assert flow_shape.customer_update_name == FLOW_UPDATE_NAME
    assert "latest_snapshot" in flow_shape.required_fields_present
    assert bundle.shape("sys_hub_action_instance").customer_update_name == ACTION_UPDATE_NAME
    assert bundle.shape("sys_hub_flow_logic_instance_v2").customer_update_name == (
        LOGIC_UPDATE_NAME
    )
    assert bundle.snapshot.status == "collected"
    assert bundle.snapshot.snapshot_sys_id == SNAPSHOT_SYS_ID
    assert len(bundle.snapshot.content_sha256) == 64
    assert "sys_update_xml:sys_hub_flow:validated" in bundle.evidence
    assert "sys_update_xml:sys_hub_action_instance:validated" in bundle.evidence
    assert "sys_update_xml:sys_hub_flow_logic_instance_v2:validated" in bundle.evidence
    assert "sys_hub_flow_snapshot:collected" in bundle.evidence


def test_payload_hashes_are_stable_for_audit() -> None:
    bundle = _collect(FakeFlowEvidenceClient())

    assert bundle.shape("sys_hub_flow").payload_sha256 == (
        hashlib.sha256(FLOW_PAYLOAD.encode("utf-8")).hexdigest()
    )
    assert bundle.shape("sys_hub_action_instance").payload_sha256 == (
        hashlib.sha256(ACTION_PAYLOAD.encode("utf-8")).hexdigest()
    )


def test_collection_is_deterministic_across_runs() -> None:
    first = _collect(FakeFlowEvidenceClient())
    second = _collect(FakeFlowEvidenceClient())

    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_readiness_from_complete_evidence_enables_runtime_generation_only() -> None:
    bundle = _collect(FakeFlowEvidenceClient())

    readiness = flow_builder_readiness_from_evidence(
        bundle=bundle,
        current_graph_hash=GRAPH_HASH,
    )

    assert readiness.ready_for_runtime_generation is True
    assert readiness.ready_for_retrieved_update_set_handoff is False
    assert readiness.missing_evidence == ["flow_builder_implemented"]
    assert readiness.requirement_status["flow_snapshot_evidence_current"] == "satisfied"
    assert readiness.requirement_status["flow_builder_implemented"] == "missing"
    assert readiness.blocked_reason == "Flow Designer builder is not implemented"
    assert readiness.unsupported_reason_codes == [
        "flow_builder_not_implemented",
        "retrieved_update_set_handoff_disabled",
    ]
    assert [item.code for item in readiness.unsupported_reason_guidance] == (
        readiness.unsupported_reason_codes
    )


def test_missing_customer_update_marks_shape_missing_and_blocks_readiness() -> None:
    client = FakeFlowEvidenceClient()
    del client.update_xml[ACTION_UPDATE_NAME]

    bundle = _collect(client)
    readiness = flow_builder_readiness_from_evidence(
        bundle=bundle,
        current_graph_hash=GRAPH_HASH,
    )

    action_shape = bundle.shape("sys_hub_action_instance")
    assert action_shape.status == "missing"
    assert "no sys_update_xml customer update retrieved" in action_shape.reason
    assert readiness.ready_for_runtime_generation is False
    assert "flow_xml_shape_evidence_validated:sys_hub_action_instance" in (
        readiness.missing_evidence
    )
    assert "runtime_generation_disabled" in readiness.unsupported_reason_codes


def test_missing_instance_records_mark_shape_missing() -> None:
    client = FakeFlowEvidenceClient()
    client.logic_instances = []

    bundle = _collect(client)

    logic_shape = bundle.shape("sys_hub_flow_logic_instance_v2")
    assert logic_shape.status == "missing"
    assert logic_shape.reason == (
        "no sys_hub_flow_logic_instance_v2 records retrieved for flow"
    )
    assert "sys_update_xml:sys_hub_flow_logic_instance_v2:missing" in bundle.evidence


def test_unstable_instance_sys_ids_are_ignored() -> None:
    client = FakeFlowEvidenceClient()
    client.action_instances = [{"sys_id": "generated-action-node"}, {"sys_id": ACTION_SYS_ID}]

    bundle = _collect(client)

    assert bundle.shape("sys_hub_action_instance").status == "validated"

    client = FakeFlowEvidenceClient()
    client.action_instances = [{"sys_id": "generated-action-node"}]

    bundle = _collect(client)

    assert bundle.shape("sys_hub_action_instance").status == "missing"


def test_forbidden_field_marks_shape_invalid_with_audit_hash() -> None:
    client = FakeFlowEvidenceClient()
    forbidden_payload = FLOW_PAYLOAD.replace(
        "</sys_hub_flow>",
        "<sys_updated_by>admin</sys_updated_by></sys_hub_flow>",
    )
    client.update_xml[FLOW_UPDATE_NAME]["payload"] = forbidden_payload

    bundle = _collect(client)

    flow_shape = bundle.shape("sys_hub_flow")
    assert flow_shape.status == "invalid"
    assert "forbidden field" in flow_shape.reason
    assert flow_shape.payload_sha256 == (
        hashlib.sha256(forbidden_payload.encode("utf-8")).hexdigest()
    )
    assert "sys_update_xml:sys_hub_flow:invalid" in bundle.evidence


def test_missing_required_field_marks_shape_invalid() -> None:
    client = FakeFlowEvidenceClient()
    client.update_xml[LOGIC_UPDATE_NAME]["payload"] = LOGIC_PAYLOAD.replace(
        "<logic_definition>IF</logic_definition>", ""
    )

    bundle = _collect(client)

    logic_shape = bundle.shape("sys_hub_flow_logic_instance_v2")
    assert logic_shape.status == "invalid"
    assert "missing required field: logic_definition" in logic_shape.reason


def test_empty_and_malformed_payloads_mark_shape_invalid() -> None:
    client = FakeFlowEvidenceClient()
    client.update_xml[FLOW_UPDATE_NAME]["payload"] = "   "

    bundle = _collect(client)
    flow_shape = bundle.shape("sys_hub_flow")
    assert flow_shape.status == "invalid"
    assert flow_shape.reason == "customer update payload is empty"
    assert flow_shape.payload_sha256 == ""

    client = FakeFlowEvidenceClient()
    client.update_xml[FLOW_UPDATE_NAME]["payload"] = "<record_update"

    bundle = _collect(client)
    assert bundle.shape("sys_hub_flow").status == "invalid"
    assert "not valid XML" in bundle.shape("sys_hub_flow").reason


def test_snapshot_staleness_blocks_readiness_with_stable_reason() -> None:
    bundle = _collect(FakeFlowEvidenceClient())
    current_hash = "e6" * 32

    assert bundle.snapshot_staleness_reason(current_graph_hash=current_hash) == (
        FLOW_SNAPSHOT_EVIDENCE_STALE_REASON
    )

    readiness = flow_builder_readiness_from_evidence(
        bundle=bundle,
        current_graph_hash=current_hash,
    )

    assert readiness.ready_for_runtime_generation is False
    assert "flow_snapshot_evidence_current" in readiness.missing_evidence
    assert readiness.evidence_notes == [FLOW_SNAPSHOT_EVIDENCE_STALE_REASON]


def test_missing_snapshot_reference_marks_snapshot_missing() -> None:
    client = FakeFlowEvidenceClient()
    client.flow_records[0]["latest_snapshot"] = ""

    bundle = _collect(client)

    assert bundle.snapshot.status == "missing"
    assert bundle.snapshot.reason == FLOW_SNAPSHOT_EVIDENCE_MISSING_REASON
    assert bundle.snapshot_staleness_reason(current_graph_hash=GRAPH_HASH) == (
        FLOW_SNAPSHOT_EVIDENCE_MISSING_REASON
    )


def test_unretrieved_snapshot_record_marks_snapshot_missing() -> None:
    client = FakeFlowEvidenceClient()
    client.snapshot_records = []

    bundle = _collect(client)

    assert bundle.snapshot.status == "missing"
    assert bundle.snapshot.snapshot_sys_id == SNAPSHOT_SYS_ID


def test_unstable_snapshot_reference_marks_snapshot_invalid() -> None:
    client = FakeFlowEvidenceClient()
    client.flow_records[0]["latest_snapshot"] = "snapshot-sys-id"

    bundle = _collect(client)

    assert bundle.snapshot.status == "invalid"
    assert bundle.snapshot.reason.startswith("flow_snapshot_evidence_invalid")
    assert bundle.snapshot_staleness_reason(current_graph_hash=GRAPH_HASH) == (
        bundle.snapshot.reason
    )
    summary = bundle.readiness_summary(current_graph_hash=GRAPH_HASH)
    assert summary.snapshot_current is False
    assert summary.snapshot_staleness_reason == bundle.snapshot.reason


def test_redacts_script_bodies_and_never_stores_raw_payloads() -> None:
    client = FakeFlowEvidenceClient()
    client.update_xml[FLOW_UPDATE_NAME]["operation_script"] = "gs.log('secret-script-body');"
    client.snapshot_records[0]["condition"] = "secret-snapshot-script"

    bundle = _collect(client)

    assert bundle.shape("sys_hub_flow").status == "validated"
    assert bundle.shape("sys_hub_flow").metadata["operation_script"] == "[redacted_script_body]"
    assert bundle.snapshot.metadata["condition"] == "[redacted_script_body]"
    dumped = bundle.model_dump_json()
    assert "secret-script-body" not in dumped
    assert "secret-snapshot-script" not in dumped
    assert "<record_update" not in dumped


def test_collector_fails_closed_on_flow_lookup_problems() -> None:
    client = FakeFlowEvidenceClient()

    with pytest.raises(ValueError, match="requires a flow name"):
        collect_flow_xml_evidence(client=client, flow_name="  ", retrieved_graph_hash=GRAPH_HASH)
    with pytest.raises(ValueError, match="must be a stable hash"):
        collect_flow_xml_evidence(
            client=client,
            flow_name="Incident Triage",
            retrieved_graph_hash="not-a-hash",
        )
    with pytest.raises(ValueError, match="flow not found"):
        collect_flow_xml_evidence(
            client=client,
            flow_name="Unknown Flow",
            retrieved_graph_hash=GRAPH_HASH,
        )

    client.flow_records.append(dict(client.flow_records[0]))
    with pytest.raises(ValueError, match="exactly one flow match"):
        _collect(client)

    client = FakeFlowEvidenceClient()
    client.flow_records[0]["sys_id"] = "not-a-sys-id"
    with pytest.raises(ValueError, match="flow sys_id must be 32 hex characters"):
        _collect(client)


def test_bundle_shape_lookup_fails_closed_for_unknown_table() -> None:
    bundle = _collect(FakeFlowEvidenceClient())

    with pytest.raises(KeyError, match="Flow XML evidence shape not found"):
        bundle.shape("sys_hub_trigger_instance")


def test_readiness_contract_with_no_evidence_keeps_previous_default_routing() -> None:
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
    assert readiness.missing_evidence == [
        "flow_xml_shape_evidence_validated:sys_hub_flow",
        "flow_xml_shape_evidence_validated:sys_hub_action_instance",
        "flow_xml_shape_evidence_validated:sys_hub_flow_logic_instance_v2",
        "flow_snapshot_evidence_current",
        "flow_builder_implemented",
    ]
    assert all(
        readiness.requirement_status[item] == "satisfied"
        for item in readiness.required_evidence
        if item not in readiness.missing_evidence
    )
    assert readiness.evidence_notes == []


def test_readiness_contract_reports_partial_runtime_evidence() -> None:
    readiness = flow_builder_readiness_contract(
        runtime_evidence=FlowRuntimeEvidenceSummary(
            bundle_version="flow-xml-evidence-v1",
            flow_name="Incident Triage",
            validated_shape_tables=["sys_hub_flow"],
            snapshot_current=True,
        )
    )

    assert readiness.ready_for_runtime_generation is False
    assert readiness.missing_evidence == [
        "flow_xml_shape_evidence_validated:sys_hub_action_instance",
        "flow_xml_shape_evidence_validated:sys_hub_flow_logic_instance_v2",
        "flow_builder_implemented",
    ]
    assert readiness.requirement_status[
        "flow_xml_shape_evidence_validated:sys_hub_flow"
    ] == "satisfied"


def test_readiness_contract_treats_uncollected_snapshot_as_missing_without_notes() -> None:
    readiness = flow_builder_readiness_contract(
        runtime_evidence=FlowRuntimeEvidenceSummary(
            bundle_version="flow-xml-evidence-v1",
            flow_name="Incident Triage",
            validated_shape_tables=[],
            snapshot_current=False,
        )
    )

    assert readiness.ready_for_runtime_generation is False
    assert "flow_snapshot_evidence_current" in readiness.missing_evidence
    assert readiness.evidence_notes == []


def test_readiness_contract_keeps_design_evidence_override_behavior() -> None:
    readiness = flow_builder_readiness_contract(
        available_evidence={"retrieved_graph_hash_matches_existing_graph_hash"},
        runtime_evidence=FlowRuntimeEvidenceSummary(
            bundle_version="flow-xml-evidence-v1",
            flow_name="Incident Triage",
            validated_shape_tables=[
                "sys_hub_flow",
                "sys_hub_action_instance",
                "sys_hub_flow_logic_instance_v2",
            ],
            snapshot_current=True,
        ),
    )

    assert readiness.ready_for_runtime_generation is False
    assert "xml_shape_repository_available" in readiness.missing_evidence
    assert "flow_snapshot_evidence_current" not in readiness.missing_evidence
