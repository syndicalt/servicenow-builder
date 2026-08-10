"""Table schema and form section/layout discovery."""

from __future__ import annotations

from jedi_devproject.discovery.fetch import _display_or_value, _optional_int
from jedi_devproject.discovery.models import (
    DiscoveredField,
    DiscoveredFormElement,
    DiscoveredFormSection,
    InstanceDiscoveryClient,
    InstanceDiscoveryContext,
)

DICTIONARY_FORM_DISCOVERY_METADATA_NON_JSON_DIAGNOSTIC = (
    "dictionary/form discovery metadata contains non-JSON value"
)


def discover_dictionary_form_context(
    *,
    client: InstanceDiscoveryClient,
    target_table: str,
) -> InstanceDiscoveryContext:
    table_records = _metadata_records(
        client.fetch_table_records(
            table="sys_db_object",
            lookup={"name": target_table},
            fields=["name", "label", "is_extendable"],
            limit=1,
        )
    )
    table_exists = bool(table_records)
    table_label = (
        _metadata_text_or_default(table_records[0].get("label"), default=target_table)
        if table_records
        else target_table
    )

    dictionary_records = _metadata_records(
        client.fetch_table_records(
            table="sys_dictionary",
            lookup={"name": target_table},
            fields=["element", "column_label", "internal_type", "max_length"],
            limit=500,
        )
    )
    fields = [
        DiscoveredField(
            element=_metadata_text(record.get("element")),
            column_label=_metadata_text_or_default(
                record.get("column_label"),
                default=_metadata_text(record.get("element")),
            ),
            internal_type=_display_or_value(record.get("internal_type")),
            max_length=_optional_int(record.get("max_length")),
            inherited=False,
        )
        for record in dictionary_records
        if _metadata_text(record.get("element")).strip()
    ]

    section_records = _metadata_records(
        client.fetch_table_records(
            table="sys_ui_section",
            lookup={"name": target_table},
            fields=["sys_id", "name", "caption", "view", "sys_user"],
            limit=100,
        )
    )
    sections: list[DiscoveredFormSection] = []
    for section in section_records:
        section_id = _metadata_text(section.get("sys_id"))
        element_records = _metadata_records(
            client.fetch_table_records(
                table="sys_ui_element",
                lookup={"name": target_table, "sys_ui_section": section_id},
                fields=["sys_id", "element", "position"],
                limit=500,
            )
        )
        sections.append(
            DiscoveredFormSection(
                sys_id=section_id,
                name=_metadata_text_or_default(section.get("name"), default=target_table),
                caption=_metadata_text(section.get("caption")),
                view_name=_display_or_value(section.get("view")) or "Default view",
                elements=[
                    DiscoveredFormElement(
                        sys_id=_metadata_text(element.get("sys_id")),
                        element=_metadata_text(element.get("element")),
                        position=_optional_int(element.get("position")) or 0,
                    )
                    for element in element_records
                    if _metadata_text(element.get("element")).strip()
                ],
            )
        )

    acl_records = _metadata_records(
        client.fetch_table_records(
            table="sys_security_acl",
            lookup={"name": target_table},
            fields=["sys_id", "name", "operation"],
            limit=100,
        )
    )
    acl_indicators = []
    for record in acl_records:
        operation = _metadata_text(record.get("operation"))
        name = _metadata_text(record.get("name"))
        acl_indicators.append(operation or name)

    return InstanceDiscoveryContext(
        target_table=target_table,
        table_label=table_label,
        table_exists=table_exists,
        supports_custom_fields=table_exists,
        fields=fields,
        form_sections=sections,
        acl_indicators=acl_indicators,
        evidence=[
            f"sys_db_object:{target_table}",
            f"sys_dictionary:{target_table}",
            f"sys_ui_section:{target_table}",
            f"sys_security_acl:{target_table}",
        ],
    )


def _metadata_records(value: object) -> list[dict[str, object]]:
    if type(value) is not list:
        raise ValueError(DICTIONARY_FORM_DISCOVERY_METADATA_NON_JSON_DIAGNOSTIC)
    records: list[dict[str, object]] = []
    for record in value:
        if type(record) is not dict:
            raise ValueError(DICTIONARY_FORM_DISCOVERY_METADATA_NON_JSON_DIAGNOSTIC)
        records.append(record)
    return records


def _metadata_text(value: object) -> str:
    if value is None:
        return ""
    if type(value) is str:
        return value
    raise ValueError(DICTIONARY_FORM_DISCOVERY_METADATA_NON_JSON_DIAGNOSTIC)


def _metadata_text_or_default(value: object, *, default: str) -> str:
    text = _metadata_text(value)
    if text:
        return text
    return default
