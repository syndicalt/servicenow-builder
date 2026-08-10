from __future__ import annotations

import re
from typing import Any, Protocol

from jedi_devproject.models import CandidateChange
from jedi_devproject.validation_helpers import reference_value
from jedi_devproject.xml_builder import (
    SYS_SCOPE_GLOBAL,
    container_element,
    record_update,
    text_element,
)

FORM_SECTION_FIELD_NON_JSON_DIAGNOSTIC = (
    "form section removal field contains non-JSON value"
)
FORM_SECTION_FIELD_MISSING_DIAGNOSTIC = "form section removal field is missing"


class FormSectionMetadataClient(Protocol):
    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...


def form_section_customer_updates(
    *,
    client: FormSectionMetadataClient,
    changes: list[CandidateChange],
    remote_update_set_sys_id: str,
) -> list[dict[str, Any]]:
    change = _single_form_section_change(changes)
    fields = dict(change.fields)
    target_table = _required_text(fields, "table")
    requested_sections = _section_names(fields.get("sections"))
    requested_view = _form_section_field_text(fields.get("view") or "Default view")
    if not requested_sections:
        raise ValueError("form section removal requires at least one section")

    sections = _form_section_metadata_records(
        client.fetch_table_records(
            table="sys_ui_section",
            lookup={"name": target_table},
            fields=["sys_id", "name", "caption", "view", "sys_user"],
            limit=200,
        )
    )
    resolved_sections = _resolve_sections(
        sections=sections,
        requested_sections=requested_sections,
        requested_view=requested_view,
    )
    updates: list[dict[str, Any]] = []
    for section in resolved_sections:
        section_sys_id = _required_reference_value(section.get("sys_id"))
        updates.append(
            {
                "name": f"sys_ui_section_{section_sys_id}",
                "remote_update_set": remote_update_set_sys_id,
                "action": "DELETE",
                "type": "Form Layout",
                "target_name": _target_name(target_table=target_table, section=section),
                "payload": _form_section_delete_payload(
                    target_table=target_table,
                    section=section,
                    section_sys_id=section_sys_id,
                ),
                "application": "global",
            }
        )
    return updates


def _form_section_metadata_records(value: Any) -> list[dict[str, Any]]:
    if type(value) is not list:
        raise ValueError(FORM_SECTION_FIELD_NON_JSON_DIAGNOSTIC)
    records: list[dict[str, Any]] = []
    for record in value:
        if type(record) is not dict:
            raise ValueError(FORM_SECTION_FIELD_NON_JSON_DIAGNOSTIC)
        records.append(record)
    return records


def _single_form_section_change(changes: list[CandidateChange]) -> CandidateChange:
    if len(changes) != 1:
        raise ValueError("form section removal requires exactly one candidate change")
    change = changes[0]
    if change.table != "sys_ui_section" or change.operation != "delete":
        raise ValueError("form section removal requires one sys_ui_section delete change")
    return change


def _resolve_sections(
    *,
    sections: list[dict[str, Any]],
    requested_sections: list[str],
    requested_view: str,
) -> list[dict[str, Any]]:
    resolved: list[dict[str, Any]] = []
    for requested in requested_sections:
        matches = [
            section
            for section in sections
            if _view_matches(section.get("view"), requested_view)
            and _section_matches(section.get("caption"), requested)
        ]
        if not matches:
            raise ValueError(f"form section not found: {requested}")
        if len(matches) > 1:
            raise ValueError(f"form section match is ambiguous: {requested}")
        resolved.append(matches[0])
    return resolved


def _section_matches(caption: Any, requested: str) -> bool:
    normalized_caption = _normalize_label(_reference_display_or_value(caption))
    normalized_requested = _normalize_label(requested)
    if normalized_caption == "" or normalized_requested == "":
        return False
    return normalized_caption == normalized_requested


def _view_matches(view: Any, requested_view: str) -> bool:
    requested = _normalize_view(requested_view)
    display = _normalize_view(_reference_display_or_value(view))
    value = _normalize_view(reference_value(view))
    if requested == "default":
        return display in {"", "default"} or value in {"", "default"}
    return requested in {display, value}


def _form_section_delete_payload(
    *,
    target_table: str,
    section: dict[str, Any],
    section_sys_id: str,
) -> str:
    caption = _reference_display_or_value(section.get("caption"))
    view = section.get("view")
    view_value = reference_value(view)
    view_display = _reference_display_or_value(view)
    update_name = f"sys_ui_section_{section_sys_id}"
    return record_update(
        container_element(
            "sys_ui_section",
            text_element("caption", caption),
            "<header>false</header>",
            text_element("name", target_table),
            "<roles/>",
            "<sys_class_name>sys_ui_section</sys_class_name>",
            "<sys_domain>global</sys_domain>",
            text_element("sys_id", section_sys_id),
            SYS_SCOPE_GLOBAL,
            text_element("sys_update_name", update_name),
            text_element("sys_user", reference_value(section.get("sys_user"))),
            "<title>true</title>",
            text_element(
                "view",
                _payload_view_value(view_value),
                display_value=view_display,
                name="NULL",
            ),
            "<view_name/>",
            action="DELETE",
        ),
        table="sys_ui_section",
    )


def _target_name(*, target_table: str, section: dict[str, Any]) -> str:
    caption = _reference_display_or_value(section.get("caption"))
    return f"{target_table.replace('_', ' ').title()}.{caption or 'Default section'}"


def _section_names(value: Any) -> list[str]:
    if type(value) is list:
        return [
            text
            for item in value
            if (text := _form_section_field_text(item).strip())
        ]
    text = _form_section_field_text(value).strip()
    if not text:
        return []
    return [item.strip() for item in re.split(r",|\band\b", text) if item.strip()]


def _required_text(fields: dict[str, Any], key: str) -> str:
    value = _form_section_field_text(fields.get(key)).strip()
    if not value:
        raise ValueError(f"form section removal missing required field: {key}")
    return value


def _reference_display_or_value(value: Any) -> str:
    if type(value) is dict:
        return _form_section_field_text(
            value.get("display_value") or value.get("value") or ""
        )
    return _form_section_field_text(value)


def _required_reference_value(value: Any) -> str:
    text = reference_value(value)
    if text == "":
        raise ValueError(FORM_SECTION_FIELD_MISSING_DIAGNOSTIC)
    return text


def _payload_view_value(value: str) -> str:
    return "" if _normalize_view(value) == "default" else value


def _normalize_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _normalize_view(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"", "default view", "default"}:
        return "default"
    return normalized


def _form_section_field_text(value: Any) -> str:
    if value is None:
        return ""
    if type(value) is str:
        return value
    if type(value) is bool or type(value) is int:
        return str(value)
    raise ValueError(FORM_SECTION_FIELD_NON_JSON_DIAGNOSTIC)
