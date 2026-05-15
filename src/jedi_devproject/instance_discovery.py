from __future__ import annotations

import re
from typing import Any, Literal, Protocol
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field

from jedi_devproject.requirement_text import positive_requirement_text


class InstanceDiscoveryClient(Protocol):
    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...


class DiscoveredField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    element: str
    column_label: str
    internal_type: str
    max_length: int | None = None
    inherited: bool = False


class DiscoveredFormElement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sys_id: str
    element: str
    position: int


class DiscoveredFormSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sys_id: str
    name: str
    caption: str = ""
    view_name: str = "Default view"
    elements: list[DiscoveredFormElement] = Field(default_factory=list)


class InstanceDiscoveryContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_table: str
    table_label: str
    table_exists: bool
    supports_custom_fields: bool
    fields: list[DiscoveredField] = Field(default_factory=list)
    form_sections: list[DiscoveredFormSection] = Field(default_factory=list)
    acl_indicators: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)

    def field_exists(self, element: str) -> bool:
        return any(field.element == element for field in self.fields)

    def anchor_exists(self, element: str) -> bool:
        return any(
            form_element.element == element
            for section in self.form_sections
            for form_element in section.elements
        )

    def primary_section(self) -> DiscoveredFormSection:
        if not self.form_sections:
            raise ValueError(f"no form sections discovered for {self.target_table}")
        return self.form_sections[0]


SurfaceName = Literal[
    "table_schema",
    "form_layout",
    "catalog_definitions",
    "catalog_categories",
    "employee_center_topics",
    "employee_center_connected_content",
    "business_rules",
    "client_scripts",
    "ui_policies",
    "flows",
    "flow_graph",
    "script_includes",
    "cmdb_discovery_maps",
    "integration_surfaces",
    "public_docs",
]

EMPTY_REQUIRED_SURFACE_IS_SUFFICIENT: set[SurfaceName] = {
    "business_rules",
    "client_scripts",
    "ui_policies",
    "script_includes",
}


class ServiceNowSurfaceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_table: str
    name: str
    active: bool | None = None
    summary: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)


class ServiceNowSurfaceContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    surface: SurfaceName
    source_table: str
    required: bool
    records: list[ServiceNowSurfaceRecord] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    citations: list[dict[str, str]] = Field(default_factory=list)


class ServiceNowSurfaceContextBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_table: str
    required_surfaces: list[SurfaceName]
    surfaces: list[ServiceNowSurfaceContext]
    table_context: InstanceDiscoveryContext
    public_doc_queries: list[str] = Field(default_factory=list)
    missing_required_surfaces: list[SurfaceName] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)

    @property
    def context_sufficient(self) -> bool:
        return not self.missing_required_surfaces

    def surface_record_count(self, surface: SurfaceName) -> int:
        for context in self.surfaces:
            if context.surface == surface:
                return len(context.records)
        return 0

    def surface(self, surface: SurfaceName) -> ServiceNowSurfaceContext:
        for context in self.surfaces:
            if context.surface == surface:
                return context
        raise KeyError(f"surface context not found: {surface}")


def discover_dictionary_form_context(
    *,
    client: InstanceDiscoveryClient,
    target_table: str,
) -> InstanceDiscoveryContext:
    table_records = client.fetch_table_records(
        table="sys_db_object",
        lookup={"name": target_table},
        fields=["name", "label", "is_extendable"],
        limit=1,
    )
    table_exists = bool(table_records)
    table_label = (
        str(table_records[0].get("label") or target_table) if table_records else target_table
    )

    dictionary_records = client.fetch_table_records(
        table="sys_dictionary",
        lookup={"name": target_table},
        fields=["element", "column_label", "internal_type", "max_length"],
        limit=500,
    )
    fields = [
        DiscoveredField(
            element=str(record.get("element", "")),
            column_label=str(record.get("column_label") or record.get("element", "")),
            internal_type=_display_or_value(record.get("internal_type")),
            max_length=_optional_int(record.get("max_length")),
            inherited=False,
        )
        for record in dictionary_records
        if str(record.get("element", "")).strip()
    ]

    section_records = client.fetch_table_records(
        table="sys_ui_section",
        lookup={"name": target_table},
        fields=["sys_id", "name", "caption", "view", "sys_user"],
        limit=100,
    )
    sections: list[DiscoveredFormSection] = []
    for section in section_records:
        section_id = str(section["sys_id"])
        element_records = client.fetch_table_records(
            table="sys_ui_element",
            lookup={"name": target_table, "sys_ui_section": section_id},
            fields=["sys_id", "element", "position"],
            limit=500,
        )
        sections.append(
            DiscoveredFormSection(
                sys_id=section_id,
                name=str(section.get("name") or target_table),
                caption=str(section.get("caption") or ""),
                view_name=_display_or_value(section.get("view")) or "Default view",
                elements=[
                    DiscoveredFormElement(
                        sys_id=str(element["sys_id"]),
                        element=str(element.get("element") or ""),
                        position=int(element.get("position") or 0),
                    )
                    for element in element_records
                    if str(element.get("element") or "").strip()
                ],
            )
        )

    acl_records = client.fetch_table_records(
        table="sys_security_acl",
        lookup={"name": target_table},
        fields=["sys_id", "name", "operation"],
        limit=100,
    )

    return InstanceDiscoveryContext(
        target_table=target_table,
        table_label=table_label,
        table_exists=table_exists,
        supports_custom_fields=table_exists,
        fields=fields,
        form_sections=sections,
        acl_indicators=[
            str(record.get("operation") or record.get("name") or "") for record in acl_records
        ],
        evidence=[
            f"sys_db_object:{target_table}",
            f"sys_dictionary:{target_table}",
            f"sys_ui_section:{target_table}",
            f"sys_security_acl:{target_table}",
        ],
    )


def discover_servicenow_surface_context(
    *,
    client: InstanceDiscoveryClient,
    target_table: str,
    story_text: str,
    public_doc_queries: list[str],
    required_surfaces_override: list[SurfaceName] | None = None,
) -> ServiceNowSurfaceContextBundle:
    table_context = discover_dictionary_form_context(client=client, target_table=target_table)
    required_surfaces = required_surfaces_override or _required_surfaces(story_text)
    surfaces = [
        ServiceNowSurfaceContext(
            surface="table_schema",
            source_table="sys_dictionary",
            required="table_schema" in required_surfaces,
            records=[
                ServiceNowSurfaceRecord(
                    source_table="sys_dictionary",
                    name=field.element,
                    active=True,
                    summary=field.column_label,
                    metadata={"internal_type": field.internal_type},
                )
                for field in table_context.fields
            ],
            evidence=[f"sys_dictionary:{target_table}"],
            confidence=1.0 if table_context.fields else 0.0,
            citations=[
                {
                    "source_table": "sys_dictionary",
                    "query": f"name={target_table}",
                    "record_count": str(len(table_context.fields)),
                }
            ],
        ),
        ServiceNowSurfaceContext(
            surface="form_layout",
            source_table="sys_ui_section",
            required="form_layout" in required_surfaces,
            records=[
                ServiceNowSurfaceRecord(
                    source_table="sys_ui_section",
                    name=section.name,
                    active=True,
                    summary=section.caption,
                    metadata={"view_name": section.view_name},
                )
                for section in table_context.form_sections
            ],
            evidence=[f"sys_ui_section:{target_table}"],
            confidence=1.0 if table_context.form_sections else 0.0,
            citations=[
                {
                    "source_table": "sys_ui_section",
                    "query": f"name={target_table}",
                    "record_count": str(len(table_context.form_sections)),
                }
            ],
        ),
        _table_surface(
            client=client,
            surface="business_rules",
            source_table="sys_script",
            lookup={"collection": target_table},
            fields=["name", "active", "when"],
            required="business_rules" in required_surfaces,
            evidence=f"sys_script:{target_table}",
        ),
        _table_surface(
            client=client,
            surface="client_scripts",
            source_table="sys_script_client",
            lookup={"table": target_table},
            fields=["name", "active", "type"],
            required="client_scripts" in required_surfaces,
            evidence=f"sys_script_client:{target_table}",
        ),
        _table_surface(
            client=client,
            surface="ui_policies",
            source_table="sys_ui_policy",
            lookup={"table": target_table},
            fields=["short_description", "active"],
            required="ui_policies" in required_surfaces,
            evidence=f"sys_ui_policy:{target_table}",
        ),
        *_flow_surfaces(client=client, required_surfaces=required_surfaces),
        _table_surface(
            client=client,
            surface="script_includes",
            source_table="sys_script_include",
            lookup={},
            fields=["name", "active"],
            required="script_includes" in required_surfaces,
            evidence="sys_script_include:active",
            limit=25,
        ),
        _table_surface(
            client=client,
            surface="cmdb_discovery_maps",
            source_table="cmdb_ci",
            lookup={"sys_class_name": "cmdb_ci_discovery"},
            fields=["name", "sys_class_name"],
            required="cmdb_discovery_maps" in required_surfaces,
            evidence="cmdb_ci:cmdb_ci_discovery",
            limit=25,
        ),
        _table_surface(
            client=client,
            surface="integration_surfaces",
            source_table="sys_rest_message",
            lookup={},
            fields=["name", "rest_endpoint"],
            required="integration_surfaces" in required_surfaces,
            evidence="sys_rest_message",
            limit=25,
        ),
        ServiceNowSurfaceContext(
            surface="public_docs",
            source_table="curated_rag",
            required="public_docs" in required_surfaces,
            records=[
                ServiceNowSurfaceRecord(
                    source_table="curated_rag",
                    name=query,
                    active=True,
                    summary="Public documentation query routed through approved RAG boundary.",
                )
                for query in public_doc_queries
            ],
            evidence=[f"public_docs:{query}" for query in public_doc_queries],
            confidence=0.8 if public_doc_queries else 0.0,
            citations=[
                {
                    "source_table": "curated_rag",
                    "query": query,
                    "record_count": "1",
                }
                for query in public_doc_queries
            ],
        ),
        _catalog_definitions_surface(
            client=client,
            required="catalog_definitions" in required_surfaces,
        ),
        _catalog_categories_surface(
            client=client,
            required="catalog_categories" in required_surfaces,
        ),
        _employee_center_topics_surface(
            client=client,
            required="employee_center_topics" in required_surfaces,
        ),
        _employee_center_connected_content_surface(
            client=client,
            required="employee_center_connected_content" in required_surfaces,
        ),
    ]
    missing_required_surfaces = [
        context.surface
        for context in surfaces
        if context.required
        and (not context.records or context.confidence <= 0.0)
        and context.surface not in EMPTY_REQUIRED_SURFACE_IS_SUFFICIENT
    ]
    evidence = [
        *table_context.evidence,
        *[item for context in surfaces for item in context.evidence],
    ]
    return ServiceNowSurfaceContextBundle(
        target_table=target_table,
        required_surfaces=required_surfaces,
        surfaces=surfaces,
        table_context=table_context,
        public_doc_queries=public_doc_queries,
        missing_required_surfaces=missing_required_surfaces,
        evidence=evidence,
    )


def _required_surfaces(story_text: str) -> list[SurfaceName]:
    lowered = positive_requirement_text(story_text)
    surfaces: list[SurfaceName] = ["table_schema", "form_layout"]
    keyword_map: list[tuple[SurfaceName, tuple[str, ...]]] = [
        ("business_rules", (r"\bbusiness\s+rules?\b", r"\bserver\s+scripts?\b")),
        (
            "client_scripts",
            (r"\bclient\s+scripts?\b", r"\bonchange\b", r"\bonsubmit\b", r"\bonload\b"),
        ),
        (
            "ui_policies",
            (
                r"\bui\s+polic(?:y|ies)\b",
                r"\bvisible\b",
                r"\bmandatory\b",
                r"\bread-only\b",
            ),
        ),
        ("flows", (r"\bflows?\b", r"\bworkflows?\b", r"\bflow\s+designer\b")),
        ("flow_graph", (r"\bflows?\b", r"\bworkflows?\b", r"\bflow\s+designer\b")),
        ("script_includes", (r"\bscript\s+includes?\b", r"\butility\s+script\b")),
        (
            "cmdb_discovery_maps",
            (r"\bdiscovery(?:\s+map)?s?\b", r"\bcmdb\b"),
        ),
        ("integration_surfaces", (r"\bintegrations?\b", r"\brest\s+message\b", r"\bapi\b")),
        (
            "public_docs",
            (
                r"\bdocumentation\b",
                r"\bpublic\s+documentation\b",
                r"\bpublic\s+docs\b",
                r"\bdocs\b",
            ),
        ),
        (
            "catalog_definitions",
            (
                r"\bcatalog\s+items?\b",
                r"\bservice\s+catalog\b",
                r"\bemployee\s+center\b",
            ),
        ),
        (
            "catalog_categories",
            (
                r"\bcatalog\s+items?\b",
                r"\bservice\s+catalog\b",
                r"\bemployee\s+center\b",
            ),
        ),
        (
            "employee_center_topics",
            (r"\bemployee\s+center\b", r"\btopics?\b", r"\btaxonom(?:y|ies)\b"),
        ),
        (
            "employee_center_connected_content",
            (r"\bemployee\s+center\b", r"\bconnected\s+content\b", r"\btopics?\b"),
        ),
    ]
    for surface, patterns in keyword_map:
        if any(re.search(pattern, lowered) for pattern in patterns) and surface not in surfaces:
            surfaces.append(surface)
    return surfaces


def _records_surface(
    *,
    surface: SurfaceName,
    source_table: str,
    records: list[dict[str, Any]],
    lookup: dict[str, str],
    required: bool,
    evidence: str,
) -> ServiceNowSurfaceContext:
    return ServiceNowSurfaceContext(
        surface=surface,
        source_table=source_table,
        required=required,
        records=[
            ServiceNowSurfaceRecord(
                source_table=source_table,
                name=_record_name(record),
                active=_optional_bool(record.get("active")),
                summary=_record_summary(record),
                metadata=_record_metadata(record, exclude={"sys_id", "name", "active"}),
            )
            for record in records
        ],
        evidence=[evidence],
        confidence=0.95 if records else 0.0,
        citations=[
            {
                "source_table": source_table,
                "query": _query_string(lookup),
                "record_count": str(len(records)),
            }
        ],
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


def _catalog_definitions_surface(
    *,
    client: InstanceDiscoveryClient,
    required: bool,
) -> ServiceNowSurfaceContext:
    if not required:
        return _empty_surface(
            surface="catalog_definitions",
            source_table="sc_catalog",
            required=False,
        )
    return _table_surface(
        client=client,
        surface="catalog_definitions",
        source_table="sc_catalog",
        lookup={},
        fields=["sys_id", "title", "active"],
        required=True,
        evidence="sc_catalog:active",
        limit=100,
    )


def _catalog_categories_surface(
    *,
    client: InstanceDiscoveryClient,
    required: bool,
) -> ServiceNowSurfaceContext:
    if not required:
        return _empty_surface(
            surface="catalog_categories",
            source_table="sc_category",
            required=False,
        )
    return _table_surface(
        client=client,
        surface="catalog_categories",
        source_table="sc_category",
        lookup={},
        fields=["sys_id", "title", "active", "sc_catalog"],
        required=True,
        evidence="sc_category:active",
        limit=250,
    )


def _employee_center_topics_surface(
    *,
    client: InstanceDiscoveryClient,
    required: bool,
) -> ServiceNowSurfaceContext:
    if not required:
        return _empty_surface(
            surface="employee_center_topics",
            source_table="topic",
            required=False,
        )
    taxonomy_records = client.fetch_table_records(
        table="taxonomy",
        lookup={},
        fields=["sys_id", "name", "active"],
        limit=100,
    )
    topic_records = client.fetch_table_records(
        table="topic",
        lookup={},
        fields=["sys_id", "name", "topic_path", "active", "taxonomy", "parent_topic"],
        limit=250,
    )
    records = [
        ServiceNowSurfaceRecord(
            source_table="topic",
            name=_record_name(record),
            active=_optional_bool(record.get("active")),
            summary=_display_or_value(record.get("name")),
            metadata={
                "taxonomy": _reference_value(record.get("taxonomy")),
                "parent_topic": _reference_value(record.get("parent_topic")),
            },
        )
        for record in topic_records
    ]
    return ServiceNowSurfaceContext(
        surface="employee_center_topics",
        source_table="topic",
        required=required,
        records=records,
        evidence=["taxonomy:active", "topic:active"],
        confidence=0.95 if records and taxonomy_records else 0.0,
        citations=[
            {
                "source_table": "taxonomy",
                "query": "",
                "record_count": str(len(taxonomy_records)),
            },
            {
                "source_table": "topic",
                "query": "",
                "record_count": str(len(topic_records)),
            },
        ],
    )


def _employee_center_connected_content_surface(
    *,
    client: InstanceDiscoveryClient,
    required: bool,
) -> ServiceNowSurfaceContext:
    if not required:
        return _empty_surface(
            surface="employee_center_connected_content",
            source_table="taxonomy_content_configuration",
            required=False,
        )
    content_types = client.fetch_table_records(
        table="taxonomy_content_configuration",
        lookup={},
        fields=["sys_id", "name", "active"],
        limit=100,
    )
    connected_content = client.fetch_table_records(
        table="m2m_connected_content",
        lookup={},
        fields=["sys_id", "topic", "catalog_item", "content_type"],
        limit=100,
    )
    catalog_item_types = [
        record
        for record in content_types
        if _record_name(record).strip().lower() == "catalog item"
        and _optional_bool(record.get("active")) is not False
    ]
    records = [
        ServiceNowSurfaceRecord(
            source_table="taxonomy_content_configuration",
            name=_record_name(record),
            active=_optional_bool(record.get("active")),
            summary="Employee Center connected content type.",
            metadata={"sys_id": _display_or_value(record.get("sys_id"))},
        )
        for record in catalog_item_types
    ]
    return ServiceNowSurfaceContext(
        surface="employee_center_connected_content",
        source_table="taxonomy_content_configuration",
        required=required,
        records=records,
        evidence=["taxonomy_content_configuration:active", "m2m_connected_content"],
        confidence=0.95 if records else 0.0,
        citations=[
            {
                "source_table": "taxonomy_content_configuration",
                "query": "",
                "record_count": str(len(content_types)),
            },
            {
                "source_table": "m2m_connected_content",
                "query": "",
                "record_count": str(len(connected_content)),
            },
        ],
    )


def _empty_surface(
    *,
    surface: SurfaceName,
    source_table: str,
    required: bool,
) -> ServiceNowSurfaceContext:
    return ServiceNowSurfaceContext(
        surface=surface,
        source_table=source_table,
        required=required,
        records=[],
        evidence=[],
        confidence=0.0,
        citations=[],
    )


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


def _unique_record_values(
    records: list[dict[str, Any]],
    *,
    fields: list[str],
) -> list[str]:
    values: list[str] = []
    for record in records:
        for field_name in fields:
            value = _display_or_value(record.get(field_name)).strip()
            if value and value not in values:
                values.append(value)
    return values


def _table_surface(
    *,
    client: InstanceDiscoveryClient,
    surface: SurfaceName,
    source_table: str,
    lookup: dict[str, str],
    fields: list[str],
    required: bool,
    evidence: str,
    limit: int = 100,
) -> ServiceNowSurfaceContext:
    records = client.fetch_table_records(
        table=source_table,
        lookup=lookup,
        fields=fields,
        limit=limit,
    )
    return ServiceNowSurfaceContext(
        surface=surface,
        source_table=source_table,
        required=required,
        records=[
            ServiceNowSurfaceRecord(
                source_table=source_table,
                name=_record_name(record),
                active=_optional_bool(record.get("active")),
                summary=_record_summary(record),
                metadata=_record_metadata(record, exclude={"sys_id", "name", "active"}),
            )
            for record in records
        ],
        evidence=[evidence],
        confidence=0.95 if records else 0.0,
        citations=[
            {
                "source_table": source_table,
                "query": _query_string(lookup),
                "record_count": str(len(records)),
            }
        ],
    )


def _display_or_value(value: object) -> str:
    if isinstance(value, dict):
        return str(value.get("display_value") or value.get("value") or "")
    return str(value or "")


def _reference_value(value: object) -> str:
    if isinstance(value, dict):
        return str(value.get("value") or value.get("display_value") or "")
    return str(value or "")


def _optional_int(value: object) -> int | None:
    text = str(value or "").strip()
    return int(text) if text.isdigit() else None


def _optional_bool(value: object) -> bool | None:
    text = str(value or "").strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def _record_name(record: dict[str, Any]) -> str:
    for field_name in [
        "topic_path",
        "title",
        "name",
        "short_description",
        "display_text",
        "column_label",
        "element",
    ]:
        value = str(record.get(field_name) or "").strip()
        if value:
            return value
    return "unnamed"


def _record_summary(record: dict[str, Any]) -> str:
    for field_name in ["short_description", "description", "type", "when", "rest_endpoint"]:
        value = str(record.get(field_name) or "").strip()
        if value:
            if field_name == "rest_endpoint":
                return _redact_url(value)
            return value
    return ""


def _record_metadata(
    record: dict[str, Any],
    *,
    exclude: set[str],
) -> dict[str, str]:
    return {
        key: _minimize_metadata_value(key=key, value=value)
        for key, value in record.items()
        if key not in exclude and key != "sys_id"
    }


def _query_string(lookup: dict[str, str]) -> str:
    return "^".join(f"{key}={value}" for key, value in lookup.items())


def _minimize_metadata_value(*, key: str, value: Any) -> str:
    if key in {"script", "condition", "operation_script"}:
        return "[redacted_script_body]"
    if key in {
        "sc_catalog",
        "taxonomy",
        "parent_topic",
        "topic",
        "catalog_item",
        "content_type",
    } and isinstance(value, dict):
        return str(value.get("value") or value.get("display_value") or "")
    text = _display_or_value(value)
    if key in {"rest_endpoint", "endpoint", "url"}:
        return _redact_url(text)
    return text


def _redact_url(value: str) -> str:
    try:
        parts = urlsplit(value)
    except ValueError:
        return "[redacted_url]"
    query = "[redacted_query]" if parts.query else ""
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))
