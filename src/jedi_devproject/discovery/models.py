"""Data models and client protocol shared across discovery surfaces."""

from __future__ import annotations

from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

from jedi_devproject.rag import RetrievalResult


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
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    element: str
    column_label: str
    internal_type: str
    max_length: int | None = None
    inherited: bool = False


class DiscoveredFormElement(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    sys_id: str
    element: str
    position: int


class DiscoveredFormSection(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    sys_id: str
    name: str
    caption: str = ""
    view_name: str = "Default view"
    elements: list[DiscoveredFormElement] = Field(default_factory=list)


class InstanceDiscoveryContext(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

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
    "form_sections",
    "form_layout",
    "catalog_definitions",
    "catalog_categories",
    "catalog_variable_sets",
    "employee_center_topics",
    "employee_center_connected_content",
    "business_rules",
    "client_scripts",
    "ui_policies",
    "flows",
    "flow_graph",
    "script_includes",
    "cmdb_discovery_maps",
    "cmdb_ire_identification_rules",
    "cmdb_ire_reconciliation_rules",
    "cmdb_data_sources",
    "cmdb_class_hierarchy",
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
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    source_table: str
    name: str
    active: bool | None = None
    summary: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)


class ServiceNowSurfaceContext(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    surface: SurfaceName
    source_table: str
    required: bool
    records: list[ServiceNowSurfaceRecord] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    citations: list[dict[str, str]] = Field(default_factory=list)


class ServiceNowSurfaceContextBundle(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    target_table: str
    required_surfaces: list[SurfaceName]
    surfaces: list[ServiceNowSurfaceContext]
    table_context: InstanceDiscoveryContext
    public_doc_queries: list[str] = Field(default_factory=list)
    public_doc_results: list[RetrievalResult] = Field(default_factory=list)
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
