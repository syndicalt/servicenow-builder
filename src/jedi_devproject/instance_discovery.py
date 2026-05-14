from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


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
