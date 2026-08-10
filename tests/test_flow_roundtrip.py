from __future__ import annotations

from typing import Any

import pytest

from jedi_devproject.flow_builder import stable_flow_sys_id
from jedi_devproject.flow_designer_generation import FlowGraphDiffIntent
from jedi_devproject.flow_roundtrip import (
    FlowGraphNodeState,
    flow_graph_state_hash,
    retrieve_flow_graph_state,
    run_flow_roundtrip,
)
from jedi_devproject.flow_xml_evidence import FlowXmlEvidenceBundle

FLOW_SYS_ID = "f1" * 16
ACTION_SYS_ID = "a2" * 16
LOGIC_SYS_ID = "b3" * 16
SNAPSHOT_BEFORE = "c4" * 16
SNAPSHOT_AFTER = "e5" * 16
UPDATE_SET_SYS_ID = "0a" * 16

NEW_ACTION_SYS_ID = stable_flow_sys_id("sys_hub_action_instance", FLOW_SYS_ID, "new-action-node")
NEW_EDGE_SYS_ID = stable_flow_sys_id(
    "sys_hub_flow_logic_instance_v2", FLOW_SYS_ID, ACTION_SYS_ID, "new-action-node"
)

SHAPE_TABLES = [
    "sys_hub_flow",
    "sys_hub_action_instance",
    "sys_hub_flow_logic_instance_v2",
]


def _pre_action_records() -> list[dict[str, Any]]:
    return [
        {
            "sys_id": ACTION_SYS_ID,
            "flow": {"value": FLOW_SYS_ID, "display_value": "Incident Triage"},
            "order": "100",
            "action_type": "core-create-task",
            "display_text": "Create triage task",
            "connected_to": "",
        }
    ]


def _pre_logic_records() -> list[dict[str, Any]]:
    return [
        {
            "sys_id": LOGIC_SYS_ID,
            "flow": FLOW_SYS_ID,
            "order": "200",
            "logic_definition": "IF",
            "display_text": "If impact is high",
            "connected_to": "",
            "condition": "impact=1",
        }
    ]


def _post_add_action_records() -> list[dict[str, Any]]:
    return [
        *_pre_action_records(),
        {
            "sys_id": NEW_ACTION_SYS_ID,
            "flow": FLOW_SYS_ID,
            "order": "101",
            "action_type": "core-create-task",
            "display_text": "Create triage task for high impact incidents",
            "connected_to": "",
        },
    ]


def _post_add_action_logic_records() -> list[dict[str, Any]]:
    return [
        *_pre_logic_records(),
        {
            "sys_id": NEW_EDGE_SYS_ID,
            "flow": FLOW_SYS_ID,
            "order": "102",
            "logic_definition": "SEQUENCE",
            "display_text": "Connect after Create triage task",
            "connected_to": NEW_ACTION_SYS_ID,
            "condition": "",
        },
    ]


class FakeRoundTripClient:
    def __init__(self) -> None:
        self.flow_name = "Incident Triage"
        self.latest_snapshot = SNAPSHOT_BEFORE
        self.post_latest_snapshot = SNAPSHOT_AFTER
        self.action_records = _pre_action_records()
        self.logic_records = _pre_logic_records()
        self.post_action_records = _post_add_action_records()
        self.post_logic_records = _post_add_action_logic_records()
        self.apply_on_import = True
        self.fail_import: Exception | None = None
        self.remote_update_set_rows: list[dict[str, Any]] = [
            {
                "sys_id": UPDATE_SET_SYS_ID,
                "name": "JEDI Flow Round-Trip - Incident Triage",
                "state": "loaded",
            }
        ]
        self.imported_xml: list[str] = []
        self.import_service_ids: list[str] = []
        self.duplicate_flow_rows = False
        self._imported = False

    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        applied = self._imported and self.apply_on_import
        if table == "sys_hub_flow":
            if lookup.get("name") != self.flow_name:
                return []
            row = {
                "sys_id": FLOW_SYS_ID,
                "name": self.flow_name,
                "active": "true",
                "status": "published",
                "latest_snapshot": (self.post_latest_snapshot if applied else self.latest_snapshot),
            }
            return [dict(row), dict(row)] if self.duplicate_flow_rows else [row]
        if table == "sys_hub_action_instance":
            records = self.post_action_records if applied else self.action_records
            return [dict(record) for record in records]
        if table == "sys_hub_flow_logic_instance_v2":
            records = self.post_logic_records if applied else self.logic_records
            return [dict(record) for record in records]
        if table == "sys_remote_update_set" and self._imported:
            return [dict(row) for row in self.remote_update_set_rows]
        return []

    def import_update_set_xml(
        self,
        *,
        service_id: str,
        update_set_xml: str,
    ) -> dict[str, Any]:
        if self.fail_import is not None:
            raise self.fail_import
        self.import_service_ids.append(service_id)
        self.imported_xml.append(update_set_xml)
        self._imported = True
        return {"result": {"status": "imported"}}


class _BadFlowSysIdClient(FakeRoundTripClient):
    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        records = super().fetch_table_records(
            table=table, lookup=lookup, fields=fields, limit=limit
        )
        if table == "sys_hub_flow":
            return [{**record, "sys_id": "not-a-sys-id"} for record in records]
        return records


def _pre_graph_hash() -> str:
    state = retrieve_flow_graph_state(client=FakeRoundTripClient(), flow_name="Incident Triage")
    return state.graph_hash


def test_flow_graph_state_hash_rejects_non_finite_node_state_without_payload_leak() -> None:
    node = FlowGraphNodeState.model_construct(
        table="sys_hub_action_instance",
        sys_id=ACTION_SYS_ID,
        fields={"private_value_marker": "do-not-echo-this", "order": float("nan")},
    )

    with pytest.raises(ValueError) as exc_info:
        flow_graph_state_hash({ACTION_SYS_ID: node})

    diagnostic = str(exc_info.value)
    assert diagnostic == "Flow graph node canonical state contains non-finite numeric values"
    assert exc_info.value.__cause__ is None
    assert "private_value_marker" not in diagnostic
    assert "do-not-echo-this" not in diagnostic
    assert "order" not in diagnostic
    assert "NaN" not in diagnostic


def _evidence_bundle(graph_hash: str) -> FlowXmlEvidenceBundle:
    return FlowXmlEvidenceBundle.model_validate(
        {
            "version": "flow-xml-evidence-v1",
            "repository_version": "flow-xml-shapes-v1",
            "flow_name": "Incident Triage",
            "flow_sys_id": FLOW_SYS_ID,
            "retrieved_graph_hash": graph_hash,
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
                "snapshot_sys_id": SNAPSHOT_BEFORE,
                "content_sha256": "1" * 64,
            },
            "evidence": [],
        }
    )


def _add_action_intent(graph_hash: str) -> FlowGraphDiffIntent:
    return FlowGraphDiffIntent.model_validate(
        {
            "capability": "flow_modify",
            "flow_name": "Incident Triage",
            "flow_sys_id_or_stable_key": FLOW_SYS_ID,
            "target_table": "incident",
            "trigger_summary": "When Incident impact is high",
            "existing_graph_hash": graph_hash,
            "requested_graph_diff": [
                {
                    "operation": "add_action",
                    "node_id": "new-action-node",
                    "after_node_id": ACTION_SYS_ID,
                    "action_type": "core-create-task",
                    "summary": "Create triage task for high impact incidents",
                    "inputs": {},
                }
            ],
            "affected_nodes": [ACTION_SYS_ID],
            "affected_edges": [f"{ACTION_SYS_ID}:new-action-node"],
            "customer_update_records": [],
            "test_plan": ["Create a high impact incident and confirm the triage task."],
            "rollback_notes": ["Remove the added Flow Designer action."],
        }
    )


def _update_condition_intent(graph_hash: str) -> FlowGraphDiffIntent:
    intent = _add_action_intent(graph_hash)
    return intent.model_copy(
        update={
            "requested_graph_diff": [
                intent.requested_graph_diff[0].model_copy(
                    update={
                        "operation": "update_condition",
                        "node_id": LOGIC_SYS_ID,
                        "after_node_id": None,
                        "action_type": "",
                        "summary": "Tighten the high impact condition",
                        "inputs": {"condition": "impact=1^urgency=1"},
                    }
                )
            ]
        }
    )


def _assertion(report: Any, name: str) -> Any:
    matches = [item for item in report.assertions if item.name == name]
    assert len(matches) == 1, f"assertion not found: {name}"
    return matches[0]


def test_roundtrip_add_action_passes_with_committed_post_diff_graph() -> None:
    graph_hash = _pre_graph_hash()
    client = FakeRoundTripClient()

    report = run_flow_roundtrip(
        client=client,
        intent=_add_action_intent(graph_hash),
        evidence_bundle=_evidence_bundle(graph_hash),
    )

    assert report.passed is True
    assert report.version == "flow-roundtrip-report-v1"
    assert report.operation == "add_action"
    assert report.flow_sys_id == FLOW_SYS_ID
    assert report.update_set_sys_id == UPDATE_SET_SYS_ID
    assert report.update_set_name == "JEDI Flow Round-Trip - Incident Triage"
    assert report.update_set_remote_sys_id == stable_flow_sys_id(
        "flow-roundtrip", FLOW_SYS_ID, graph_hash, "add_action"
    )
    assert report.customer_update_names == [
        f"sys_hub_action_instance_{NEW_ACTION_SYS_ID}",
        f"sys_hub_flow_logic_instance_v2_{NEW_EDGE_SYS_ID}",
    ]
    assert report.graph_hash_before == graph_hash
    assert report.graph_hash_after != ""
    assert report.graph_hash_after != report.graph_hash_before
    assert report.snapshot_before == SNAPSHOT_BEFORE
    assert report.snapshot_after == SNAPSHOT_AFTER
    assert all(assertion.passed for assertion in report.assertions)
    assert _assertion(report, "pre_import_graph_current").passed is True
    assert _assertion(report, "retrieved_update_set_imported").passed is True
    assert _assertion(
        report, f"graph_matches_intent:sys_hub_action_instance:{NEW_ACTION_SYS_ID}"
    ).passed
    assert _assertion(
        report, f"graph_matches_intent:sys_hub_flow_logic_instance_v2:{NEW_EDGE_SYS_ID}"
    ).passed
    assert _assertion(report, "unchanged_nodes_byte_stable").passed is True
    assert _assertion(report, "node_count_matches_diff").passed is True
    assert _assertion(report, "flow_snapshot_regenerated").passed is True


def test_roundtrip_never_commits_and_imports_a_loaded_update_set() -> None:
    graph_hash = _pre_graph_hash()
    client = FakeRoundTripClient()

    report = run_flow_roundtrip(
        client=client,
        intent=_add_action_intent(graph_hash),
        evidence_bundle=_evidence_bundle(graph_hash),
    )

    assert report.committed_by_harness is False
    assert report.review_boundary == "retrieved_update_set_preview_commit"
    assert client.import_service_ids == ["jedi_update_set_import"]
    assert len(client.imported_xml) == 1
    assert "<state>loaded</state>" in client.imported_xml[0]
    assert f"sys_hub_action_instance_{NEW_ACTION_SYS_ID}" in client.imported_xml[0]
    assert "the harness never" in client.imported_xml[0]


def test_roundtrip_update_condition_passes() -> None:
    graph_hash = _pre_graph_hash()
    client = FakeRoundTripClient()
    client.post_action_records = _pre_action_records()
    updated_logic = _pre_logic_records()
    updated_logic[0]["condition"] = "impact=1^urgency=1"
    client.post_logic_records = updated_logic

    report = run_flow_roundtrip(
        client=client,
        intent=_update_condition_intent(graph_hash),
        evidence_bundle=_evidence_bundle(graph_hash),
    )

    assert report.passed is True
    assert report.operation == "update_condition"
    assert report.customer_update_names == [
        f"sys_hub_flow_logic_instance_v2_{LOGIC_SYS_ID}",
    ]
    assert _assertion(
        report, f"graph_matches_intent:sys_hub_flow_logic_instance_v2:{LOGIC_SYS_ID}"
    ).passed
    assert _assertion(report, "node_count_matches_diff").passed is True


def test_roundtrip_fails_closed_on_stale_pre_import_graph_without_importing() -> None:
    client = FakeRoundTripClient()
    stale_hash = "e6" * 32

    report = run_flow_roundtrip(
        client=client,
        intent=_add_action_intent(stale_hash),
        evidence_bundle=_evidence_bundle(stale_hash),
    )

    assert report.passed is False
    assert client.imported_xml == []
    assert report.update_set_sys_id == ""
    assert report.customer_update_names == []
    assert [item.name for item in report.assertions] == ["pre_import_graph_current"]
    assert "retrieved graph hash does not match" in report.assertions[0].detail


def test_roundtrip_records_import_transport_failure() -> None:
    graph_hash = _pre_graph_hash()
    client = FakeRoundTripClient()
    client.fail_import = RuntimeError("import transport failed")

    report = run_flow_roundtrip(
        client=client,
        intent=_add_action_intent(graph_hash),
        evidence_bundle=_evidence_bundle(graph_hash),
    )

    assert report.passed is False
    imported = _assertion(report, "retrieved_update_set_imported")
    assert imported.passed is False
    assert "import transport failed" in imported.detail
    assert report.update_set_sys_id == ""
    assert report.graph_hash_after == ""
    assert report.customer_update_names == [
        f"sys_hub_action_instance_{NEW_ACTION_SYS_ID}",
        f"sys_hub_flow_logic_instance_v2_{NEW_EDGE_SYS_ID}",
    ]


class UnstringifiableFlowRoundTripImportError(RuntimeError):
    def __str__(self) -> str:
        raise ValueError("client-secret-value")


def test_roundtrip_records_unstringifiable_import_failure_safely() -> None:
    graph_hash = _pre_graph_hash()
    client = FakeRoundTripClient()
    client.fail_import = UnstringifiableFlowRoundTripImportError()

    report = run_flow_roundtrip(
        client=client,
        intent=_add_action_intent(graph_hash),
        evidence_bundle=_evidence_bundle(graph_hash),
    )

    assert report.passed is False
    imported = _assertion(report, "retrieved_update_set_imported")
    assert imported.passed is False
    assert imported.detail == (
        "flow roundtrip raised unstringifiable UnstringifiableFlowRoundTripImportError"
    )
    assert "client-secret-value" not in imported.detail
    assert report.update_set_sys_id == ""
    assert report.graph_hash_after == ""


def test_roundtrip_records_missing_imported_update_set_lookup() -> None:
    graph_hash = _pre_graph_hash()
    client = FakeRoundTripClient()
    client.remote_update_set_rows = []

    report = run_flow_roundtrip(
        client=client,
        intent=_add_action_intent(graph_hash),
        evidence_bundle=_evidence_bundle(graph_hash),
    )

    assert report.passed is False
    imported = _assertion(report, "retrieved_update_set_imported")
    assert imported.passed is False
    assert "did not include sys_id" in imported.detail


def test_roundtrip_fails_on_graph_mismatch() -> None:
    graph_hash = _pre_graph_hash()
    client = FakeRoundTripClient()
    client.post_action_records = _pre_action_records()
    mismatched_logic = _pre_logic_records()
    mismatched_logic[0]["condition"] = "impact=2"
    client.post_logic_records = mismatched_logic

    report = run_flow_roundtrip(
        client=client,
        intent=_update_condition_intent(graph_hash),
        evidence_bundle=_evidence_bundle(graph_hash),
    )

    assert report.passed is False
    mismatch = _assertion(
        report, f"graph_matches_intent:sys_hub_flow_logic_instance_v2:{LOGIC_SYS_ID}"
    )
    assert mismatch.passed is False
    assert "expected" in mismatch.detail


def test_roundtrip_before_human_commit_reports_pending_graph_assertions() -> None:
    graph_hash = _pre_graph_hash()
    client = FakeRoundTripClient()
    client.apply_on_import = False

    report = run_flow_roundtrip(
        client=client,
        intent=_add_action_intent(graph_hash),
        evidence_bundle=_evidence_bundle(graph_hash),
    )

    assert report.passed is False
    missing = _assertion(
        report, f"graph_matches_intent:sys_hub_action_instance:{NEW_ACTION_SYS_ID}"
    )
    assert missing.passed is False
    assert missing.detail == "expected node was not retrieved after import"
    assert _assertion(report, "node_count_matches_diff").passed is False
    assert _assertion(report, "flow_snapshot_regenerated").passed is False
    assert _assertion(report, "unchanged_nodes_byte_stable").passed is True


def test_roundtrip_fails_on_node_count_drift() -> None:
    graph_hash = _pre_graph_hash()
    client = FakeRoundTripClient()
    client.post_action_records = [
        *_post_add_action_records(),
        {
            "sys_id": "9c" * 16,
            "flow": FLOW_SYS_ID,
            "order": "300",
            "action_type": "core-create-task",
            "display_text": "Unexpected rogue node",
            "connected_to": "",
        },
    ]

    report = run_flow_roundtrip(
        client=client,
        intent=_add_action_intent(graph_hash),
        evidence_bundle=_evidence_bundle(graph_hash),
    )

    assert report.passed is False
    drift = _assertion(report, "node_count_matches_diff")
    assert drift.passed is False
    assert drift.detail == "expected 4, retrieved 5"


def test_roundtrip_fails_when_untouched_node_is_not_byte_stable() -> None:
    graph_hash = _pre_graph_hash()
    client = FakeRoundTripClient()
    mutated_actions = _post_add_action_records()
    mutated_actions[0]["display_text"] = "Renamed existing action"
    client.post_action_records = mutated_actions

    report = run_flow_roundtrip(
        client=client,
        intent=_add_action_intent(graph_hash),
        evidence_bundle=_evidence_bundle(graph_hash),
    )

    assert report.passed is False
    stability = _assertion(report, "unchanged_nodes_byte_stable")
    assert stability.passed is False
    assert ACTION_SYS_ID in stability.detail


def test_roundtrip_fails_when_snapshot_is_not_regenerated() -> None:
    graph_hash = _pre_graph_hash()
    client = FakeRoundTripClient()
    client.post_latest_snapshot = SNAPSHOT_BEFORE

    report = run_flow_roundtrip(
        client=client,
        intent=_add_action_intent(graph_hash),
        evidence_bundle=_evidence_bundle(graph_hash),
    )

    assert report.passed is False
    snapshot = _assertion(report, "flow_snapshot_regenerated")
    assert snapshot.passed is False
    assert SNAPSHOT_BEFORE in snapshot.detail


def test_roundtrip_report_is_deterministic_across_runs() -> None:
    graph_hash = _pre_graph_hash()

    first = run_flow_roundtrip(
        client=FakeRoundTripClient(),
        intent=_add_action_intent(graph_hash),
        evidence_bundle=_evidence_bundle(graph_hash),
    )
    second = run_flow_roundtrip(
        client=FakeRoundTripClient(),
        intent=_add_action_intent(graph_hash),
        evidence_bundle=_evidence_bundle(graph_hash),
    )

    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_retrieve_flow_graph_state_is_deterministic_and_canonical() -> None:
    first = retrieve_flow_graph_state(client=FakeRoundTripClient(), flow_name="Incident Triage")
    second = retrieve_flow_graph_state(client=FakeRoundTripClient(), flow_name="Incident Triage")

    assert first.graph_hash == second.graph_hash
    assert first.flow_sys_id == FLOW_SYS_ID
    assert first.latest_snapshot == SNAPSHOT_BEFORE
    assert set(first.nodes) == {ACTION_SYS_ID, LOGIC_SYS_ID}
    assert first.nodes[ACTION_SYS_ID].fields["flow"] == FLOW_SYS_ID
    assert first.nodes[ACTION_SYS_ID].fields["order"] == "100"


def test_retrieve_flow_graph_state_fails_closed() -> None:
    with pytest.raises(ValueError, match="requires a flow name"):
        retrieve_flow_graph_state(client=FakeRoundTripClient(), flow_name="  ")

    with pytest.raises(ValueError, match="flow not found"):
        retrieve_flow_graph_state(client=FakeRoundTripClient(), flow_name="Unknown Flow")

    client = FakeRoundTripClient()
    client.duplicate_flow_rows = True
    with pytest.raises(ValueError, match="exactly one flow match"):
        retrieve_flow_graph_state(client=client, flow_name="Incident Triage")

    client = FakeRoundTripClient()
    client.action_records = [{"sys_id": "not-a-sys-id", "flow": FLOW_SYS_ID, "order": "1"}]
    with pytest.raises(ValueError, match="node sys_id must be 32 hex characters"):
        retrieve_flow_graph_state(client=client, flow_name="Incident Triage")

    client = FakeRoundTripClient()
    client.flow_name = "Unstable Flow"
    with pytest.raises(ValueError, match="flow sys_id must be 32 hex characters"):
        retrieve_flow_graph_state(client=_BadFlowSysIdClient(), flow_name="Incident Triage")

    client = FakeRoundTripClient()
    client.logic_records = [
        {
            "sys_id": ACTION_SYS_ID,
            "flow": FLOW_SYS_ID,
            "order": "200",
            "logic_definition": "IF",
            "display_text": "Duplicate of the action node sys_id",
            "connected_to": "",
            "condition": "",
        }
    ]
    with pytest.raises(ValueError, match="ambiguous node"):
        retrieve_flow_graph_state(client=client, flow_name="Incident Triage")
