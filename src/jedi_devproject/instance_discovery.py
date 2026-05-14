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


def _display_or_value(value: object) -> str:
    if isinstance(value, dict):
        return str(value.get("display_value") or value.get("value") or "")
    return str(value or "")


def _optional_int(value: object) -> int | None:
    text = str(value or "").strip()
    return int(text) if text.isdigit() else None
