from __future__ import annotations

from html import escape
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict


class DictionaryFormMetadataClient(Protocol):
    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...


class DictionaryFormIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_table: str
    field_label: str
    field_name: str
    field_type: str
    max_length: int | None = None
    mandatory: bool = False
    default_value: str = ""
    placement_anchor: str | None = None
    placement_position: str = "below"


def dictionary_form_customer_updates(
    *,
    client: DictionaryFormMetadataClient,
    intent: DictionaryFormIntent,
    remote_update_set_sys_id: str,
) -> list[dict[str, Any]]:
    return [
        _dictionary_update(intent, remote_update_set_sys_id),
        _documentation_update(intent, remote_update_set_sys_id),
        *_form_updates(
            client=client,
            intent=intent,
            remote_update_set_sys_id=remote_update_set_sys_id,
        ),
    ]


def _dictionary_update(
    intent: DictionaryFormIntent,
    remote_update_set_sys_id: str,
) -> dict[str, Any]:
    dictionary_name = f"sys_dictionary_{intent.target_table}_{intent.field_name}"
    return {
        "name": dictionary_name,
        "remote_update_set": remote_update_set_sys_id,
        "action": "INSERT_OR_UPDATE",
        "type": "Dictionary",
        "target_name": _target_name(intent),
        "payload": _dictionary_payload(intent=intent),
        "application": "global",
    }


def _documentation_update(
    intent: DictionaryFormIntent,
    remote_update_set_sys_id: str,
) -> dict[str, Any]:
    documentation_name = f"sys_documentation_{intent.target_table}_{intent.field_name}_en"
    return {
        "name": documentation_name,
        "remote_update_set": remote_update_set_sys_id,
        "action": "INSERT_OR_UPDATE",
        "type": "Field Label",
        "target_name": _target_name(intent),
        "payload": _documentation_payload(intent=intent),
        "application": "global",
    }


def _form_updates(
    *,
    client: DictionaryFormMetadataClient,
    intent: DictionaryFormIntent,
    remote_update_set_sys_id: str,
) -> list[dict[str, Any]]:
    sections = client.fetch_table_records(
        table="sys_ui_section",
        lookup={"name": intent.target_table},
        fields=["sys_id", "name", "caption", "view", "sys_user"],
        limit=100,
    )
    updates: list[dict[str, Any]] = []
    anchor_found = False
    for section in sections:
        if not _is_global_main_view_section(section):
            continue
        section_sys_id = _reference_value(section.get("sys_id"))
        elements = client.fetch_table_records(
            table="sys_ui_element",
            lookup={"name": intent.target_table, "sys_ui_section": section_sys_id},
            fields=["sys_id", "element", "position"],
            limit=200,
        )
        insert_position = _insert_position(elements=elements, intent=intent)
        anchor_found = anchor_found or insert_position is not None
        if insert_position is None:
            continue
        planned_elements = _form_elements_with_inserted_field(
            elements=elements,
            field_element=intent.field_name,
            insert_position=insert_position,
        )
        update_name = f"sys_ui_section_{section_sys_id}"
        updates.append(
            {
                "name": update_name,
                "remote_update_set": remote_update_set_sys_id,
                "action": "INSERT_OR_UPDATE",
                "type": "Form Layout",
                "target_name": _table_label(intent.target_table),
                "payload": _form_layout_payload(
                    table_name=intent.target_table,
                    section_sys_id=section_sys_id,
                    section=section,
                    elements=planned_elements,
                ),
                "application": "global",
            }
        )
    if intent.placement_anchor and not anchor_found:
        raise ValueError(f"form placement anchor not found: {intent.placement_anchor}")
    if not updates:
        raise ValueError(f"form layout handoff found no main sections for {intent.target_table}")
    return updates


def _insert_position(
    *,
    elements: list[dict[str, Any]],
    intent: DictionaryFormIntent,
) -> int | None:
    if intent.placement_anchor is None:
        last_position = max((_record_position(record) for record in elements), default=0)
        return last_position + 1
    anchor_positions = [
        _record_position(record)
        for record in elements
        if str(record.get("element") or "") == intent.placement_anchor
    ]
    if len(anchor_positions) != 1:
        return None
    anchor_position = anchor_positions[0]
    if intent.placement_position == "above":
        return anchor_position
    if intent.placement_position == "end":
        return max((_record_position(record) for record in elements), default=0) + 1
    return anchor_position + 1


def _is_global_main_view_section(section: dict[str, Any]) -> bool:
    if _reference_value(section.get("sys_user")).strip() != "":
        return False
    if _reference_value(section.get("caption")).strip() != "":
        return False
    view = section.get("view")
    if isinstance(view, dict):
        display_value = str(view.get("display_value") or "").strip().lower()
        reference_value = str(view.get("value") or "").strip().lower()
        values = {display_value or reference_value}
    else:
        values = {str(view or "").strip().lower()}
    return bool(values.intersection({"", "default", "default view", "scrum"}))


def _form_elements_with_inserted_field(
    *,
    elements: list[dict[str, Any]],
    field_element: str,
    insert_position: int,
) -> list[dict[str, str]]:
    planned: list[dict[str, str]] = []
    inserted = False
    for record in sorted(elements, key=_record_position):
        element = str(record.get("element") or "")
        if element == field_element:
            continue
        position = _record_position(record)
        if not inserted and position >= insert_position:
            planned.append({"element": field_element, "position": str(insert_position)})
            inserted = True
        planned.append(
            {
                "sys_id": _reference_value(record.get("sys_id")),
                "element": element,
                "position": str(position + 1 if position >= insert_position else position),
            }
        )
    if not inserted:
        planned.append({"element": field_element, "position": str(insert_position)})
    return planned


def _dictionary_payload(*, intent: DictionaryFormIntent) -> str:
    update_name = f"sys_dictionary_{intent.target_table}_{intent.field_name}"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<record_update>"
        f'<sys_dictionary action="INSERT_OR_UPDATE" element="{escape(intent.field_name)}" '
        f'table="{escape(intent.target_table)}">'
        "<active>true</active>"
        f"<column_label>{escape(intent.field_label)}</column_label>"
        f"<default_value>{escape(intent.default_value)}</default_value>"
        f"<element>{escape(intent.field_name)}</element>"
        f'<internal_type display_value="{escape(intent.field_type.title())}">'
        f"{escape(intent.field_type)}</internal_type>"
        f"<mandatory>{_bool_text(intent.mandatory)}</mandatory>"
        f"<max_length>{escape(str(intent.max_length or 8000))}</max_length>"
        f"<name>{escape(intent.target_table)}</name>"
        "<read_only>false</read_only>"
        "<sys_class_name>sys_dictionary</sys_class_name>"
        '<sys_scope display_value="Global">global</sys_scope>'
        f"<sys_update_name>{escape(update_name)}</sys_update_name>"
        "</sys_dictionary>"
        "</record_update>"
    )


def _documentation_payload(*, intent: DictionaryFormIntent) -> str:
    update_name = f"sys_documentation_{intent.target_table}_{intent.field_name}_en"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<record_update>"
        f'<sys_documentation element="{escape(intent.field_name)}" '
        f'label="{escape(intent.field_label)}" language="en" table="{escape(intent.target_table)}">'
        '<sys_documentation action="INSERT_OR_UPDATE">'
        f"<element>{escape(intent.field_name)}</element>"
        f"<label>{escape(intent.field_label)}</label>"
        "<language>en</language>"
        f"<name>{escape(intent.target_table)}</name>"
        f"<plural>{escape(intent.field_label)}</plural>"
        "<sys_class_name>sys_documentation</sys_class_name>"
        '<sys_scope display_value="Global">global</sys_scope>'
        f"<sys_update_name>{escape(update_name)}</sys_update_name>"
        "</sys_documentation>"
        "</sys_documentation>"
        "</record_update>"
    )


def _form_layout_payload(
    *,
    table_name: str,
    section_sys_id: str,
    section: dict[str, Any],
    elements: list[dict[str, str]],
) -> str:
    caption = _reference_value(section.get("caption"))
    view = section.get("view")
    view_name = _view_payload_value(view)
    if isinstance(view, dict):
        view_display = str(view.get("display_value") or view.get("value") or "")
    else:
        view_display = str(view or "")
    section_update_name = f"sys_ui_section_{section_sys_id}"
    element_xml = "".join(
        '<sys_ui_element action="INSERT_OR_UPDATE">'
        f"<element>{escape(element['element'])}</element>"
        f"<position>{escape(element['position'])}</position>"
        f"<sys_id>{escape(element.get('sys_id', ''))}</sys_id>"
        "<sys_mod_count>0</sys_mod_count>"
        "<sys_ui_formatter/>"
        f'<sys_ui_section caption="{escape(caption or "NULL")}" display_value="" '
        f'name="{escape(table_name)}" sys_domain="global" view="{escape(view_display)}">'
        f"{escape(section_sys_id)}</sys_ui_section>"
        "<sys_user/>"
        f"<type>{_element_type(element['element'])}</type>"
        "</sys_ui_element>"
        for element in elements
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<record_update>"
        f'<sys_ui_section caption="{escape(caption)}" section_id="{escape(section_sys_id)}" '
        f'sys_domain="global" table="{escape(table_name)}" version="3" '
        f'view="{escape(view_name)}">'
        f"{element_xml}"
        '<sys_ui_section action="INSERT_OR_UPDATE">'
        f"<caption>{escape(caption)}</caption>"
        "<header>false</header>"
        f"<name>{escape(table_name)}</name>"
        "<roles/>"
        "<sys_class_name>sys_ui_section</sys_class_name>"
        "<sys_domain>global</sys_domain>"
        f"<sys_id>{escape(section_sys_id)}</sys_id>"
        '<sys_scope display_value="Global">global</sys_scope>'
        f"<sys_update_name>{escape(section_update_name)}</sys_update_name>"
        "<sys_user/>"
        "<title>true</title>"
        f'<view display_value="{escape(view_display)}" name="NULL">{escape(view_name)}</view>'
        "<view_name/>"
        "</sys_ui_section>"
        "</sys_ui_section>"
        "</record_update>"
    )


def _view_payload_value(view: Any) -> str:
    if isinstance(view, dict):
        value = str(view.get("value") or "")
        display = str(view.get("display_value") or "")
        return "" if value.lower() in {"default", "default view"} else display or value
    text = str(view or "")
    return "" if text.lower() in {"default", "default view"} else text


def _element_type(element: str) -> str:
    return escape(element) if element.startswith(".") else ""


def _target_name(intent: DictionaryFormIntent) -> str:
    return f"{_table_label(intent.target_table)}.{intent.field_label}"


def _table_label(table_name: str) -> str:
    if table_name == "rm_story":
        return "Story"
    return table_name.replace("_", " ").title()


def _reference_value(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("value") or "")
    return str(value or "")


def _record_position(record: dict[str, Any]) -> int:
    return int(str(record.get("position") or "0"))


def _bool_text(value: bool) -> str:
    return "true" if value else "false"
