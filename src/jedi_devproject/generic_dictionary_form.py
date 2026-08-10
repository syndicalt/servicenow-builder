from __future__ import annotations

from html import escape
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, model_validator

from jedi_devproject.xml_builder import (
    SYS_SCOPE_GLOBAL,
    bool_element,
    container_element,
    record_update,
    reference_qualifier_elements,
    text_element,
)

DICTIONARY_FORM_METADATA_NON_JSON_DIAGNOSTIC = (
    "dictionary/form metadata field contains non-JSON value"
)
DICTIONARY_FORM_METADATA_MISSING_DIAGNOSTIC = "dictionary/form metadata field is missing"


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
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    target_table: str
    field_label: str
    field_name: str
    field_type: str
    reference_table: str | None = None
    reference_qualifier: str | None = None
    max_length: int | None = None
    mandatory: bool = False
    default_value: str = ""
    placement_anchor: str | None = None
    placement_position: str = "below"

    @model_validator(mode="after")
    def require_reference_table_for_reference_fields(self) -> DictionaryFormIntent:
        if self.field_type == "reference" and not (self.reference_table or "").strip():
            raise ValueError("reference_table is required for reference fields")
        return self


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
    sections = _dictionary_form_metadata_records(
        client.fetch_table_records(
            table="sys_ui_section",
            lookup={"name": intent.target_table},
            fields=["sys_id", "name", "caption", "view", "sys_user"],
            limit=100,
        )
    )
    updates: list[dict[str, Any]] = []
    anchor_found = False
    for section in sections:
        if not _is_global_main_view_section(section):
            continue
        section_sys_id = reference_value(section.get("sys_id"))
        elements = _dictionary_form_metadata_records(
            client.fetch_table_records(
                table="sys_ui_element",
                lookup={"name": intent.target_table, "sys_ui_section": section_sys_id},
                fields=["sys_id", "element", "position"],
                limit=200,
            )
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


def _dictionary_form_metadata_records(value: Any) -> list[dict[str, Any]]:
    if type(value) is not list:
        raise ValueError(DICTIONARY_FORM_METADATA_NON_JSON_DIAGNOSTIC)
    records: list[dict[str, Any]] = []
    for record in value:
        if type(record) is not dict:
            raise ValueError(DICTIONARY_FORM_METADATA_NON_JSON_DIAGNOSTIC)
        records.append(record)
    return records


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
        if _metadata_text(record.get("element")) == intent.placement_anchor
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
    if reference_value(section.get("sys_user")).strip() != "":
        return False
    if reference_value(section.get("caption")).strip() != "":
        return False
    view = section.get("view")
    if type(view) is dict:
        display_value = _metadata_text(view.get("display_value")).strip().lower()
        reference = _metadata_text(view.get("value")).strip().lower()
        values = {display_value or reference}
    else:
        values = {_metadata_text(view).strip().lower()}
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
        element = _metadata_text(record.get("element"))
        if element == field_element:
            continue
        position = _record_position(record)
        if not inserted and position >= insert_position:
            planned.append({"element": field_element, "position": str(insert_position)})
            inserted = True
        planned.append(
            {
                "sys_id": required_reference_value(record.get("sys_id")),
                "element": element,
                "position": str(position + 1 if position >= insert_position else position),
            }
        )
    if not inserted:
        planned.append({"element": field_element, "position": str(insert_position)})
    return planned


def _dictionary_payload(*, intent: DictionaryFormIntent) -> str:
    update_name = f"sys_dictionary_{intent.target_table}_{intent.field_name}"
    return record_update(
        container_element(
            "sys_dictionary",
            "<active>true</active>",
            text_element("column_label", intent.field_label),
            text_element("default_value", intent.default_value),
            text_element("element", intent.field_name),
            text_element(
                "internal_type",
                intent.field_type,
                display_value=intent.field_type.title(),
            ),
            bool_element("mandatory", intent.mandatory),
            text_element("max_length", str(intent.max_length or 8000)),
            text_element("name", intent.target_table),
            _reference_payload(intent),
            "<read_only>false</read_only>",
            "<sys_class_name>sys_dictionary</sys_class_name>",
            SYS_SCOPE_GLOBAL,
            text_element("sys_update_name", update_name),
            action="INSERT_OR_UPDATE",
            element=intent.field_name,
            table=intent.target_table,
        )
    )


def _reference_payload(intent: DictionaryFormIntent) -> str:
    if intent.field_type != "reference":
        return ""
    return reference_qualifier_elements(
        reference_table=intent.reference_table or "",
        reference_qualifier=intent.reference_qualifier or "",
    )


def _documentation_payload(*, intent: DictionaryFormIntent) -> str:
    update_name = f"sys_documentation_{intent.target_table}_{intent.field_name}_en"
    return record_update(
        container_element(
            "sys_documentation",
            container_element(
                "sys_documentation",
                text_element("element", intent.field_name),
                text_element("label", intent.field_label),
                "<language>en</language>",
                text_element("name", intent.target_table),
                text_element("plural", intent.field_label),
                "<sys_class_name>sys_documentation</sys_class_name>",
                SYS_SCOPE_GLOBAL,
                text_element("sys_update_name", update_name),
                action="INSERT_OR_UPDATE",
            ),
            element=intent.field_name,
            label=intent.field_label,
            language="en",
            table=intent.target_table,
        )
    )


def _form_layout_payload(
    *,
    table_name: str,
    section_sys_id: str,
    section: dict[str, Any],
    elements: list[dict[str, str]],
) -> str:
    caption = reference_value(section.get("caption"))
    view = section.get("view")
    view_name = _view_payload_value(view)
    if type(view) is dict:
        view_display = _metadata_first_text(view.get("display_value"), view.get("value"))
    else:
        view_display = _metadata_text(view)
    section_update_name = f"sys_ui_section_{section_sys_id}"
    element_xml = "".join(
        container_element(
            "sys_ui_element",
            text_element("element", element["element"]),
            text_element("position", element["position"]),
            text_element("sys_id", element.get("sys_id", "")),
            "<sys_mod_count>0</sys_mod_count>",
            "<sys_ui_formatter/>",
            text_element(
                "sys_ui_section",
                section_sys_id,
                caption=caption or "NULL",
                display_value="",
                name=table_name,
                sys_domain="global",
                view=view_display,
            ),
            "<sys_user/>",
            f"<type>{_element_type(element['element'])}</type>",
            action="INSERT_OR_UPDATE",
        )
        for element in elements
    )
    return record_update(
        container_element(
            "sys_ui_section",
            element_xml,
            container_element(
                "sys_ui_section",
                text_element("caption", caption),
                "<header>false</header>",
                text_element("name", table_name),
                "<roles/>",
                "<sys_class_name>sys_ui_section</sys_class_name>",
                "<sys_domain>global</sys_domain>",
                text_element("sys_id", section_sys_id),
                SYS_SCOPE_GLOBAL,
                text_element("sys_update_name", section_update_name),
                "<sys_user/>",
                "<title>true</title>",
                text_element("view", view_name, display_value=view_display, name="NULL"),
                "<view_name/>",
                action="INSERT_OR_UPDATE",
            ),
            caption=caption,
            section_id=section_sys_id,
            sys_domain="global",
            table=table_name,
            version="3",
            view=view_name,
        )
    )


def _view_payload_value(view: Any) -> str:
    if type(view) is dict:
        value = _metadata_text(view.get("value"))
        display = _metadata_text(view.get("display_value"))
        return "" if value.lower() in {"default", "default view"} else display or value
    text = _metadata_text(view)
    return "" if text.lower() in {"default", "default view"} else text


def _element_type(element: str) -> str:
    return escape(element) if element.startswith(".") else ""


def _target_name(intent: DictionaryFormIntent) -> str:
    return f"{_table_label(intent.target_table)}.{intent.field_label}"


def _table_label(table_name: str) -> str:
    if table_name == "rm_story":
        return "Story"
    return table_name.replace("_", " ").title()


def _record_position(record: dict[str, Any]) -> int:
    text = _metadata_text(record.get("position")) or "0"
    return int(text)


def reference_value(value: Any) -> str:
    if type(value) is dict:
        return _metadata_text(value.get("value"))
    return _metadata_text(value)


def required_reference_value(value: Any) -> str:
    text = reference_value(value)
    if text == "":
        raise ValueError(DICTIONARY_FORM_METADATA_MISSING_DIAGNOSTIC)
    return text


def _metadata_first_text(*values: Any) -> str:
    for value in values:
        text = _metadata_text(value)
        if text:
            return text
    return ""


def _metadata_text(value: Any) -> str:
    if value is None:
        return ""
    if type(value) is str:
        return value
    if type(value) is bool or type(value) is int:
        return str(value)
    raise ValueError(DICTIONARY_FORM_METADATA_NON_JSON_DIAGNOSTIC)
