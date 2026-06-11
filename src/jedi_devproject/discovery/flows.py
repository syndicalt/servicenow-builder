"""Flow and flow-graph discovery surfaces."""

from __future__ import annotations

from typing import Any

from jedi_devproject.discovery.fetch import (
    _display_or_value,
    _optional_bool,
    _query_string,
    _record_metadata,
    _record_name,
    _record_summary,
    _records_surface,
    _unique_record_values,
)
from jedi_devproject.discovery.models import (
    InstanceDiscoveryClient,
    ServiceNowSurfaceContext,
    ServiceNowSurfaceRecord,
    SurfaceName,
)


def _flow_surfaces(
    *,
    client: InstanceDiscoveryClient,
    required_surfaces: list[SurfaceName],
) -> list[ServiceNowSurfaceContext]:
    flow_records = client.fetch_table_records(
        table="sys_hub_flow",
        lookup={},
        fields=["sys_id", "name", "active", "status", "type", "internal_name"],
        limit=25,
    )
    flow_graph_required = "flow_graph" in required_surfaces
    return [
        _records_surface(
            surface="flows",
            source_table="sys_hub_flow",
            records=flow_records,
            lookup={},
            required="flows" in required_surfaces,
            evidence="sys_hub_flow:active",
        ),
        (
            _flow_graph_surface(
                client=client,
                flow_records=flow_records,
                required=True,
            )
            if flow_graph_required
            else ServiceNowSurfaceContext(
                surface="flow_graph",
                source_table="sys_hub_flow_graph",
                required=False,
                records=[],
                evidence=[],
                confidence=0.0,
                citations=[],
            )
        ),
    ]


def _flow_graph_surface(
    *,
    client: InstanceDiscoveryClient,
    flow_records: list[dict[str, Any]],
    required: bool,
) -> ServiceNowSurfaceContext:
    graph_records: list[ServiceNowSurfaceRecord] = []
    evidence: list[str] = []
    citations: list[dict[str, str]] = []
    complete_graph = bool(flow_records)

    for flow_record in flow_records:
        flow_sys_id = _display_or_value(flow_record.get("sys_id")).strip()
        flow_name = _record_name(flow_record)
        if not flow_sys_id:
            complete_graph = False
            evidence.append(f"sys_hub_flow_graph:{flow_name}:missing_flow_sys_id")
            continue

        trigger_records = _fetch_flow_graph_records(
            client=client,
            source_table="sys_hub_trigger_instance",
            lookup={"flow": flow_sys_id},
            fields=[
                "sys_id",
                "name",
                "flow",
                "trigger_type",
                "trigger_definition",
                "display_text",
            ],
            evidence_key=flow_name,
            evidence=evidence,
            citations=citations,
        )
        action_records = _fetch_flow_graph_records(
            client=client,
            source_table="sys_hub_action_instance",
            lookup={"flow": flow_sys_id},
            fields=[
                "sys_id",
                "flow",
                "order",
                "action_type",
                "action_type_parent",
                "display_text",
                "ui_id",
                "parent_ui_id",
            ],
            evidence_key=flow_name,
            evidence=evidence,
            citations=citations,
        )
        logic_records = _fetch_flow_graph_records(
            client=client,
            source_table="sys_hub_flow_logic_instance_v2",
            lookup={"flow": flow_sys_id},
            fields=[
                "sys_id",
                "flow",
                "order",
                "logic_definition",
                "display_text",
                "connected_to",
                "ui_id",
                "parent_ui_id",
            ],
            evidence_key=flow_name,
            evidence=evidence,
            citations=citations,
        )

        if not trigger_records or not action_records:
            complete_graph = False

        graph_records.extend(
            _flow_graph_surface_records(
                source_table="sys_hub_trigger_instance",
                records=trigger_records,
            )
        )
        graph_records.extend(
            _flow_graph_surface_records(
                source_table="sys_hub_action_instance",
                records=action_records,
            )
        )
        graph_records.extend(
            _flow_graph_surface_records(
                source_table="sys_hub_flow_logic_instance_v2",
                records=logic_records,
            )
        )

        for trigger_definition in _unique_record_values(
            trigger_records,
            fields=["trigger_definition"],
        ):
            graph_records.extend(
                _flow_graph_surface_records(
                    source_table="sys_hub_trigger_input",
                    records=_fetch_flow_graph_records(
                        client=client,
                        source_table="sys_hub_trigger_input",
                        lookup={"model": trigger_definition},
                        fields=[
                            "sys_id",
                            "model",
                            "element",
                            "column_label",
                            "internal_type",
                            "reference",
                            "mandatory",
                        ],
                        evidence_key=trigger_definition,
                        evidence=evidence,
                        citations=citations,
                    ),
                )
            )
            graph_records.extend(
                _flow_graph_surface_records(
                    source_table="sys_hub_trigger_output",
                    records=_fetch_flow_graph_records(
                        client=client,
                        source_table="sys_hub_trigger_output",
                        lookup={"model": trigger_definition},
                        fields=[
                            "sys_id",
                            "model",
                            "element",
                            "column_label",
                            "internal_type",
                            "reference",
                            "mandatory",
                        ],
                        evidence_key=trigger_definition,
                        evidence=evidence,
                        citations=citations,
                    ),
                )
            )

        for action_model in _unique_record_values(
            action_records,
            fields=["action_type", "action_type_parent"],
        ):
            graph_records.extend(
                _flow_graph_surface_records(
                    source_table="sys_hub_action_input",
                    records=_fetch_flow_graph_records(
                        client=client,
                        source_table="sys_hub_action_input",
                        lookup={"model": action_model},
                        fields=[
                            "sys_id",
                            "model",
                            "element",
                            "column_label",
                            "internal_type",
                            "reference",
                            "mandatory",
                        ],
                        evidence_key=action_model,
                        evidence=evidence,
                        citations=citations,
                    ),
                )
            )
            graph_records.extend(
                _flow_graph_surface_records(
                    source_table="sys_hub_action_output",
                    records=_fetch_flow_graph_records(
                        client=client,
                        source_table="sys_hub_action_output",
                        lookup={"model": action_model},
                        fields=[
                            "sys_id",
                            "model",
                            "element",
                            "column_label",
                            "internal_type",
                            "reference",
                            "mandatory",
                        ],
                        evidence_key=action_model,
                        evidence=evidence,
                        citations=citations,
                    ),
                )
            )

    confidence = 0.95 if graph_records and complete_graph else 0.0
    return ServiceNowSurfaceContext(
        surface="flow_graph",
        source_table="sys_hub_flow_graph",
        required=required,
        records=graph_records,
        evidence=evidence,
        confidence=confidence,
        citations=citations,
    )


def _fetch_flow_graph_records(
    *,
    client: InstanceDiscoveryClient,
    source_table: str,
    lookup: dict[str, str],
    fields: list[str],
    evidence_key: str,
    evidence: list[str],
    citations: list[dict[str, str]],
) -> list[dict[str, Any]]:
    records = client.fetch_table_records(
        table=source_table,
        lookup=lookup,
        fields=fields,
        limit=200,
    )
    evidence.append(f"{source_table}:{evidence_key}")
    citations.append(
        {
            "source_table": source_table,
            "query": _query_string(lookup),
            "record_count": str(len(records)),
        }
    )
    return records


def _flow_graph_surface_records(
    *,
    source_table: str,
    records: list[dict[str, Any]],
) -> list[ServiceNowSurfaceRecord]:
    return [
        ServiceNowSurfaceRecord(
            source_table=source_table,
            name=_record_name(record),
            active=_optional_bool(record.get("active")),
            summary=_record_summary(record),
            metadata=_record_metadata(record, exclude={"sys_id"}),
        )
        for record in records
    ]
