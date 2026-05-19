from __future__ import annotations

import re
from html import escape
from typing import Any, Protocol

from jedi_devproject.models import CandidateChange


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
    requested_view = str(fields.get("view") or "Default view")
    if not requested_sections:
        raise ValueError("form section removal requires at least one section")

    sections = client.fetch_table_records(
        table="sys_ui_section",
        lookup={"name": target_table},
        fields=["sys_id", "name", "caption", "view", "sys_user"],
        limit=200,
    )
    resolved_sections = _resolve_sections(
        sections=sections,
        requested_sections=requested_sections,
        requested_view=requested_view,
    )
    return [
        {
            "name": f"sys_ui_section_{_reference_value(section.get('sys_id'))}",
            "remote_update_set": remote_update_set_sys_id,
            "action": "DELETE",
            "type": "Form Layout",
            "target_name": _target_name(target_table=target_table, section=section),
            "payload": _form_section_delete_payload(
                target_table=target_table,
                section=section,
            ),
            "application": "global",
        }
        for section in resolved_sections
    ]


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
    return (
        normalized_caption == normalized_requested
        or normalized_caption.startswith(normalized_requested)
        or normalized_requested.startswith(normalized_caption)
    )


def _view_matches(view: Any, requested_view: str) -> bool:
    requested = _normalize_view(requested_view)
    display = _normalize_view(_reference_display_or_value(view))
    value = _normalize_view(_reference_value(view))
    if requested == "default":
        return display in {"", "default"} or value in {"", "default"}
    return requested in {display, value}


def _form_section_delete_payload(
    *,
    target_table: str,
    section: dict[str, Any],
) -> str:
    section_sys_id = _reference_value(section.get("sys_id"))
    caption = _reference_display_or_value(section.get("caption"))
    view = section.get("view")
    view_value = _reference_value(view)
    view_display = _reference_display_or_value(view)
    update_name = f"sys_ui_section_{section_sys_id}"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<record_update table="sys_ui_section">'
        '<sys_ui_section action="DELETE">'
        f"<caption>{escape(caption)}</caption>"
        "<header>false</header>"
        f"<name>{escape(target_table)}</name>"
        "<roles/>"
        "<sys_class_name>sys_ui_section</sys_class_name>"
        "<sys_domain>global</sys_domain>"
        f"<sys_id>{escape(section_sys_id)}</sys_id>"
        '<sys_scope display_value="Global">global</sys_scope>'
        f"<sys_update_name>{escape(update_name)}</sys_update_name>"
        f"<sys_user>{escape(_reference_value(section.get('sys_user')))}</sys_user>"
        "<title>true</title>"
        f'<view display_value="{escape(view_display)}" name="NULL">'
        f"{escape(_payload_view_value(view_value))}</view>"
        "<view_name/>"
        "</sys_ui_section>"
        "</record_update>"
    )


def _target_name(*, target_table: str, section: dict[str, Any]) -> str:
    caption = _reference_display_or_value(section.get("caption"))
    return f"{target_table.replace('_', ' ').title()}.{caption or 'Default section'}"


def _section_names(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    if not text:
        return []
    return [item.strip() for item in re.split(r",|\band\b", text) if item.strip()]


def _required_text(fields: dict[str, Any], key: str) -> str:
    value = str(fields.get(key) or "").strip()
    if not value:
        raise ValueError(f"form section removal missing required field: {key}")
    return value


def _reference_value(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("value") or "")
    return str(value or "")


def _reference_display_or_value(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("display_value") or value.get("value") or "")
    return str(value or "")


def _payload_view_value(value: str) -> str:
    return "" if _normalize_view(value) == "default" else value


def _normalize_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _normalize_view(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"", "default view", "default"}:
        return "default"
    return normalized
