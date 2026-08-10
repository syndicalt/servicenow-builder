"""Flow Designer XML shape evidence collection and snapshot evidence.

This module implements the runtime half of the Flow Designer readiness
pipeline staged across sprints 124-138 (ADR 0011): a deterministic, read-only
collector that retrieves the customer-update XML records (``sys_update_xml``)
for a named flow, validates each retrieved shape against the
``flow-xml-shapes-v1`` repository, and records ``latest_snapshot`` evidence
with content hashes for audit.

Collection never mutates ServiceNow records, never stores raw XML payloads,
and redacts script bodies before storage. Redaction behavior here is a
compliance control; do not alter it (see discovery/fetch.py).
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from jedi_devproject.discovery.fetch import (
    _display_or_value,
    _record_metadata,
    _reference_value,
)
from jedi_devproject.discovery.models import InstanceDiscoveryClient
from jedi_devproject.exception_diagnostics import exception_diagnostic_message
from jedi_devproject.flow_designer_generation import (
    FlowBuilderReadinessContract,
    FlowRuntimeEvidenceSummary,
    flow_builder_readiness_contract,
    flow_customer_update_strategy,
    flow_snapshot_update_strategy,
    flow_xml_shape_repository,
    validate_flow_xml_shape_evidence,
)

FlowXmlEvidenceStatus = Literal["collected", "validated", "missing", "invalid"]

FLOW_SNAPSHOT_EVIDENCE_MISSING_REASON = "flow_snapshot_evidence_missing"
FLOW_SNAPSHOT_EVIDENCE_INVALID_REASON = "flow_snapshot_evidence_invalid"
FLOW_SNAPSHOT_EVIDENCE_STALE_REASON = "flow_snapshot_evidence_stale_graph_hash_mismatch"
FLOW_XML_EVIDENCE_RECORDS_NON_JSON_DIAGNOSTIC = (
    "Flow XML evidence records contain non-JSON value"
)

_SYS_UPDATE_XML_FIELDS = ["sys_id", "name", "action", "type", "target_name", "payload"]
_FLOW_RECORD_FIELDS = ["sys_id", "name", "active", "status", "latest_snapshot"]
_SNAPSHOT_RECORD_FIELDS = ["sys_id", "name", "parent_flow", "note"]


class FlowXmlShapeEvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    table: str
    customer_update_name: str = ""
    status: FlowXmlEvidenceStatus
    reason: str = ""
    payload_sha256: str = ""
    required_fields_present: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class FlowSnapshotEvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    snapshot_table: Literal["sys_hub_flow_snapshot"]
    snapshot_reference_field: Literal["latest_snapshot"]
    status: FlowXmlEvidenceStatus
    reason: str = ""
    snapshot_sys_id: str = ""
    content_sha256: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)


class FlowXmlEvidenceBundle(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    version: Literal["flow-xml-evidence-v1"]
    repository_version: Literal["flow-xml-shapes-v1"]
    flow_name: str
    flow_sys_id: str
    retrieved_graph_hash: str
    shapes: list[FlowXmlShapeEvidenceRecord]
    snapshot: FlowSnapshotEvidenceRecord
    evidence: list[str]

    def shape(self, table: str) -> FlowXmlShapeEvidenceRecord:
        for shape in self.shapes:
            if shape.table == table:
                return shape
        raise KeyError(f"Flow XML evidence shape not found: {table}")

    def snapshot_staleness_reason(self, *, current_graph_hash: str) -> str:
        """Stable reason the snapshot evidence is not current, or empty string.

        Snapshot evidence is current only when it was collected and the graph
        hash captured at collection time matches the currently retrieved flow
        graph hash; any mismatch fails closed with a stable reason.
        """
        if self.snapshot.status == "missing":
            return FLOW_SNAPSHOT_EVIDENCE_MISSING_REASON
        if self.snapshot.status != "collected":
            return self.snapshot.reason or FLOW_SNAPSHOT_EVIDENCE_INVALID_REASON
        if current_graph_hash.strip().lower() != self.retrieved_graph_hash:
            return FLOW_SNAPSHOT_EVIDENCE_STALE_REASON
        return ""

    def readiness_summary(self, *, current_graph_hash: str) -> FlowRuntimeEvidenceSummary:
        staleness_reason = self.snapshot_staleness_reason(current_graph_hash=current_graph_hash)
        return FlowRuntimeEvidenceSummary(
            bundle_version=self.version,
            flow_name=self.flow_name,
            validated_shape_tables=[
                shape.table for shape in self.shapes if shape.status == "validated"
            ],
            snapshot_current=staleness_reason == "",
            snapshot_staleness_reason=staleness_reason,
        )


def collect_flow_xml_evidence(
    *,
    client: InstanceDiscoveryClient,
    flow_name: str,
    retrieved_graph_hash: str,
) -> FlowXmlEvidenceBundle:
    """Collect Flow Designer XML shape and snapshot evidence for one flow.

    This is the public entrypoint intended for later CLI wiring. It is
    read-only and deterministic: the same instance state always produces the
    same bundle, including stable content hashes for audit.
    """
    cleaned_flow_name = flow_name.strip()
    if cleaned_flow_name == "":
        raise ValueError("Flow XML evidence collection requires a flow name")
    cleaned_graph_hash = retrieved_graph_hash.strip().lower()
    if not re.fullmatch(r"[a-f0-9]{32,128}", cleaned_graph_hash):
        raise ValueError("Flow XML evidence retrieved_graph_hash must be a stable hash")
    flow_records = _flow_evidence_records(
        client.fetch_table_records(
            table="sys_hub_flow",
            lookup={"name": cleaned_flow_name},
            fields=list(_FLOW_RECORD_FIELDS),
            limit=2,
        )
    )
    if not flow_records:
        raise ValueError(f"Flow XML evidence flow not found: {cleaned_flow_name}")
    if len(flow_records) > 1:
        raise ValueError(f"Flow XML evidence requires exactly one flow match: {cleaned_flow_name}")
    flow_record = flow_records[0]
    flow_sys_id = _reference_value(flow_record.get("sys_id")).strip().lower()
    if not re.fullmatch(r"[a-f0-9]{32}", flow_sys_id):
        raise ValueError("Flow XML evidence flow sys_id must be 32 hex characters")

    repository = flow_xml_shape_repository()
    evidence: list[str] = []
    shapes = [
        _collect_shape_evidence(
            client=client,
            table="sys_hub_flow",
            record_sys_ids=[flow_sys_id],
            evidence=evidence,
        ),
        _collect_shape_evidence(
            client=client,
            table="sys_hub_action_instance",
            record_sys_ids=_flow_instance_sys_ids(
                client=client,
                table="sys_hub_action_instance",
                flow_sys_id=flow_sys_id,
            ),
            evidence=evidence,
        ),
        _collect_shape_evidence(
            client=client,
            table="sys_hub_flow_logic_instance_v2",
            record_sys_ids=_flow_instance_sys_ids(
                client=client,
                table="sys_hub_flow_logic_instance_v2",
                flow_sys_id=flow_sys_id,
            ),
            evidence=evidence,
        ),
    ]
    snapshot = _collect_snapshot_evidence(
        client=client,
        flow_record=flow_record,
        evidence=evidence,
    )
    return FlowXmlEvidenceBundle(
        version="flow-xml-evidence-v1",
        repository_version=repository.version,
        flow_name=cleaned_flow_name,
        flow_sys_id=flow_sys_id,
        retrieved_graph_hash=cleaned_graph_hash,
        shapes=shapes,
        snapshot=snapshot,
        evidence=evidence,
    )


def flow_builder_readiness_from_evidence(
    *,
    bundle: FlowXmlEvidenceBundle,
    current_graph_hash: str,
    builder_available: bool = False,
) -> FlowBuilderReadinessContract:
    """Public entrypoint: evaluate builder readiness from collected evidence.

    ``builder_available`` is the deterministic builder availability signal
    (``flow_builder.flow_builder_available()``). The default keeps today's
    fail-closed behavior: without the signal the ``flow_builder_implemented``
    requirement stays missing and retrieved Update Set handoff stays blocked.
    """
    return flow_builder_readiness_contract(
        runtime_evidence=bundle.readiness_summary(current_graph_hash=current_graph_hash),
        builder_available=builder_available,
    )


def _flow_instance_sys_ids(
    *,
    client: InstanceDiscoveryClient,
    table: str,
    flow_sys_id: str,
) -> list[str]:
    records = _flow_evidence_records(
        client.fetch_table_records(
            table=table,
            lookup={"flow": flow_sys_id},
            fields=["sys_id"],
            limit=200,
        )
    )
    sys_ids: list[str] = []
    for record in records:
        sys_id = _reference_value(record.get("sys_id")).strip().lower()
        if re.fullmatch(r"[a-f0-9]{32}", sys_id):
            sys_ids.append(sys_id)
    return sorted(set(sys_ids))


def _collect_shape_evidence(
    *,
    client: InstanceDiscoveryClient,
    table: str,
    record_sys_ids: list[str],
    evidence: list[str],
) -> FlowXmlShapeEvidenceRecord:
    strategy = flow_customer_update_strategy()
    if not record_sys_ids:
        evidence.append(f"sys_update_xml:{table}:missing")
        return FlowXmlShapeEvidenceRecord(
            table=table,
            status="missing",
            reason=f"no {table} records retrieved for flow",
        )
    customer_update_name = ""
    for record_sys_id in record_sys_ids:
        customer_update_name = strategy.customer_update_name(table, record_sys_id)
        rows = _flow_evidence_records(
            client.fetch_table_records(
                table="sys_update_xml",
                lookup={"name": customer_update_name},
                fields=list(_SYS_UPDATE_XML_FIELDS),
                limit=1,
            )
        )
        if rows:
            return _validate_shape_row(
                table=table,
                customer_update_name=customer_update_name,
                row=rows[0],
                evidence=evidence,
            )
    evidence.append(f"sys_update_xml:{table}:missing")
    return FlowXmlShapeEvidenceRecord(
        table=table,
        customer_update_name=customer_update_name,
        status="missing",
        reason=f"no sys_update_xml customer update retrieved for {table}",
    )


def _validate_shape_row(
    *,
    table: str,
    customer_update_name: str,
    row: dict[str, Any],
    evidence: list[str],
) -> FlowXmlShapeEvidenceRecord:
    metadata = _record_metadata(row, exclude={"payload"})
    payload = _display_or_value(row.get("payload"))
    if payload.strip() == "":
        evidence.append(f"sys_update_xml:{table}:invalid")
        return FlowXmlShapeEvidenceRecord(
            table=table,
            customer_update_name=customer_update_name,
            status="invalid",
            reason="customer update payload is empty",
            metadata=metadata,
        )
    payload_sha256 = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    try:
        shape_evidence = validate_flow_xml_shape_evidence(table=table, xml_payload=payload)
    except ValueError as exc:
        evidence.append(f"sys_update_xml:{table}:invalid")
        return FlowXmlShapeEvidenceRecord(
            table=table,
            customer_update_name=customer_update_name,
            status="invalid",
            reason=exception_diagnostic_message(
                exc,
                fallback_subject="flow xml evidence",
            ),
            payload_sha256=payload_sha256,
            metadata=metadata,
        )
    evidence.append(f"sys_update_xml:{table}:validated")
    return FlowXmlShapeEvidenceRecord(
        table=table,
        customer_update_name=customer_update_name,
        status="validated",
        payload_sha256=payload_sha256,
        required_fields_present=shape_evidence.required_fields_present,
        metadata=metadata,
    )


def _collect_snapshot_evidence(
    *,
    client: InstanceDiscoveryClient,
    flow_record: dict[str, Any],
    evidence: list[str],
) -> FlowSnapshotEvidenceRecord:
    strategy = flow_snapshot_update_strategy()
    latest_snapshot = _reference_value(flow_record.get("latest_snapshot")).strip()
    if latest_snapshot == "":
        evidence.append("sys_hub_flow_snapshot:missing")
        return FlowSnapshotEvidenceRecord(
            snapshot_table="sys_hub_flow_snapshot",
            snapshot_reference_field="latest_snapshot",
            status="missing",
            reason=FLOW_SNAPSHOT_EVIDENCE_MISSING_REASON,
        )
    try:
        snapshot_sys_id = strategy.validate_latest_snapshot(latest_snapshot)
    except ValueError as exc:
        evidence.append("sys_hub_flow_snapshot:invalid")
        return FlowSnapshotEvidenceRecord(
            snapshot_table="sys_hub_flow_snapshot",
            snapshot_reference_field="latest_snapshot",
            status="invalid",
            reason=f"{FLOW_SNAPSHOT_EVIDENCE_INVALID_REASON}: {exc}",
        )
    rows = _flow_evidence_records(
        client.fetch_table_records(
            table="sys_hub_flow_snapshot",
            lookup={"sys_id": snapshot_sys_id},
            fields=list(_SNAPSHOT_RECORD_FIELDS),
            limit=1,
        )
    )
    if not rows:
        evidence.append("sys_hub_flow_snapshot:missing")
        return FlowSnapshotEvidenceRecord(
            snapshot_table="sys_hub_flow_snapshot",
            snapshot_reference_field="latest_snapshot",
            status="missing",
            reason=FLOW_SNAPSHOT_EVIDENCE_MISSING_REASON,
            snapshot_sys_id=snapshot_sys_id,
        )
    row = rows[0]
    try:
        snapshot_json = json.dumps(row, sort_keys=True, allow_nan=False)
    except ValueError:
        evidence.append("sys_hub_flow_snapshot:invalid")
        return FlowSnapshotEvidenceRecord(
            snapshot_table="sys_hub_flow_snapshot",
            snapshot_reference_field="latest_snapshot",
            status="invalid",
            reason=f"{FLOW_SNAPSHOT_EVIDENCE_INVALID_REASON}: non-finite snapshot value",
            snapshot_sys_id=snapshot_sys_id,
        )
    except TypeError:
        evidence.append("sys_hub_flow_snapshot:invalid")
        return FlowSnapshotEvidenceRecord(
            snapshot_table="sys_hub_flow_snapshot",
            snapshot_reference_field="latest_snapshot",
            status="invalid",
            reason=f"{FLOW_SNAPSHOT_EVIDENCE_INVALID_REASON}: non-JSON snapshot value",
            snapshot_sys_id=snapshot_sys_id,
        )
    content_sha256 = hashlib.sha256(snapshot_json.encode("utf-8")).hexdigest()
    evidence.append("sys_hub_flow_snapshot:collected")
    return FlowSnapshotEvidenceRecord(
        snapshot_table="sys_hub_flow_snapshot",
        snapshot_reference_field="latest_snapshot",
        status="collected",
        snapshot_sys_id=snapshot_sys_id,
        content_sha256=content_sha256,
        metadata=_record_metadata(row, exclude=set()),
    )


def _flow_evidence_records(records: object) -> list[dict[str, Any]]:
    if type(records) is not list:
        raise ValueError(FLOW_XML_EVIDENCE_RECORDS_NON_JSON_DIAGNOSTIC)
    for record in records:
        if type(record) is not dict:
            raise ValueError(FLOW_XML_EVIDENCE_RECORDS_NON_JSON_DIAGNOSTIC)
    return records
