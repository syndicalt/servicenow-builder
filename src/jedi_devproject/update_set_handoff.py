from __future__ import annotations

from datetime import UTC, datetime
from html import escape
from typing import Any, Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from jedi_devproject.models import CandidateChange, CandidateStatus, UpdateSetCandidate


class UpdateSetHandoffClient(Protocol):
    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...

    def upsert_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: dict[str, Any],
    ) -> dict[str, Any]: ...

    def update_story_fields(
        self,
        story_sys_id: str,
        fields: dict[str, object],
    ) -> object: ...

    def import_update_set_xml(
        self,
        *,
        service_id: str,
        update_set_xml: str,
    ) -> dict[str, Any]: ...


class UpdateSetHandoffRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    story_sys_id: str
    story_number: str
    candidate: UpdateSetCandidate
    candidate_artifact_ref: str
    instance_url: str


class UpdateSetHandoffResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    update_set_sys_id: str
    update_set_name: str
    update_set_url: str


def create_update_set_handoff(
    *,
    client: UpdateSetHandoffClient,
    request: UpdateSetHandoffRequest,
) -> UpdateSetHandoffResult:
    if request.candidate.status is not CandidateStatus.READY_FOR_REVIEW:
        raise ValueError("candidate is not ready for Update Set handoff")

    update_set_name = _update_set_name(request.story_number)
    remote_sys_id = _remote_sys_id(request.candidate)
    customer_updates = _customer_updates_for_candidate(
        client=client,
        candidate=request.candidate,
        remote_update_set_sys_id=remote_sys_id,
    )
    update_set_xml = _update_set_unload_xml(
        update_set_name=update_set_name,
        remote_sys_id=remote_sys_id,
        description=_update_set_description(request),
        customer_updates=customer_updates,
    )
    client.import_update_set_xml(
        service_id="jedi_update_set_import",
        update_set_xml=update_set_xml,
    )
    imported_update_sets = client.fetch_table_records(
        table="sys_remote_update_set",
        lookup={"remote_sys_id": remote_sys_id},
        fields=["sys_id", "name", "state", "remote_sys_id"],
        limit=1,
    )
    update_set_sys_id = str(imported_update_sets[0].get("sys_id") if imported_update_sets else "")
    if update_set_sys_id.strip() == "":
        raise RuntimeError("ServiceNow imported Update Set lookup did not include sys_id")

    update_set_url = _update_set_url(
        instance_url=request.instance_url,
        update_set_sys_id=update_set_sys_id,
    )
    client.update_story_fields(
        request.story_sys_id,
        {
            "work_notes": (
                f"ServiceNow retrieved Update Set handoff created for {request.story_number}. "
                f"Retrieved Update Set: {update_set_name} ({update_set_url}). "
                f"Candidate artifact: {request.candidate_artifact_ref}."
            )
        },
    )
    return UpdateSetHandoffResult(
        update_set_sys_id=update_set_sys_id,
        update_set_name=update_set_name,
        update_set_url=update_set_url,
    )


def _update_set_name(story_number: str) -> str:
    return f"JEDI {story_number} - AI Candidate"


def _update_set_url(*, instance_url: str, update_set_sys_id: str) -> str:
    return f"{instance_url.rstrip('/')}/sys_remote_update_set.do?sys_id={update_set_sys_id}"


def _update_set_unload_xml(
    *,
    update_set_name: str,
    remote_sys_id: str,
    description: str,
    customer_updates: list[dict[str, Any]],
) -> str:
    unload_date = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    customer_update_xml = "\n".join(
        _customer_update_xml(
            update=update,
            update_set_name=update_set_name,
            remote_sys_id=remote_sys_id,
        )
        for update in customer_updates
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<unload unload_date="{escape(unload_date)}">\n'
        '<sys_remote_update_set action="INSERT_OR_UPDATE">\n'
        '<application display_value="Global">global</application>\n'
        f"<description>{escape(description)}</description>\n"
        f"<name>{escape(update_set_name)}</name>\n"
        f"<origin_sys_id>{escape(remote_sys_id)}</origin_sys_id>\n"
        f"<remote_sys_id>{escape(remote_sys_id)}</remote_sys_id>\n"
        "<state>loaded</state>\n"
        "<sys_class_name>sys_remote_update_set</sys_class_name>\n"
        f"<sys_id>{escape(remote_sys_id)}</sys_id>\n"
        "</sys_remote_update_set>\n"
        f"{customer_update_xml}\n"
        "</unload>"
    )


def _customer_update_xml(
    *,
    update: dict[str, Any],
    update_set_name: str,
    remote_sys_id: str,
) -> str:
    payload = str(update["payload"])
    payload = payload.replace("]]>", "]]]]><![CDATA[>")
    return (
        '<sys_update_xml action="INSERT_OR_UPDATE">\n'
        f"<action>{escape(str(update['action']))}</action>\n"
        '<application display_value="Global">global</application>\n'
        f"<name>{escape(str(update['name']))}</name>\n"
        f"<payload><![CDATA[{payload}]]></payload>\n"
        f'<remote_update_set display_value="{escape(update_set_name)}">'
        f"{escape(remote_sys_id)}</remote_update_set>\n"
        "<sys_class_name>sys_update_xml</sys_class_name>\n"
        f"<sys_id>{uuid4().hex}</sys_id>\n"
        f"<target_name>{escape(str(update['target_name']))}</target_name>\n"
        f"<type>{escape(str(update['type']))}</type>\n"
        "</sys_update_xml>"
    )


def _update_set_description(request: UpdateSetHandoffRequest) -> str:
    candidate = request.candidate
    lines = [
        f"Jedi DevProject generated retrieved update set for {request.story_number}.",
        "",
        f"Candidate artifact: {request.candidate_artifact_ref}",
        f"Candidate hash: {candidate.artifact_hash or 'unavailable'}",
        f"Status: {candidate.status.value}",
        f"Confidence: {candidate.confidence}",
        f"Risk score: {candidate.risk_score}",
        "",
        "Proposed changes:",
        *_change_summary_lines(candidate),
        "",
        "Reviewer notes:",
        *_reviewer_note_lines(candidate),
        "",
        (
            "This retrieved Update Set is a review handoff. Preview, scan, "
            "and commit only after ServiceNow-native review."
        ),
    ]
    return "\n".join(lines)


def _remote_sys_id(candidate: UpdateSetCandidate) -> str:
    source = candidate.artifact_hash or candidate.name
    sanitized = "".join(
        character for character in source.lower() if character in "0123456789abcdef"
    )
    return (sanitized + ("0" * 32))[:32]


def _customer_updates_for_candidate(
    *,
    client: UpdateSetHandoffClient,
    candidate: UpdateSetCandidate,
    remote_update_set_sys_id: str,
) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    for change in candidate.changes:
        if change.table == "sys_dictionary":
            updates.extend(
                _dictionary_customer_updates(
                    change=change,
                    remote_update_set_sys_id=remote_update_set_sys_id,
                )
            )
        elif change.table == "sys_ui_form":
            updates.extend(
                _form_layout_customer_updates(
                    client=client,
                    change=change,
                    remote_update_set_sys_id=remote_update_set_sys_id,
                )
            )
        else:
            raise ValueError(f"unsupported retrieved Update Set table: {change.table}")
    if not updates:
        raise ValueError("retrieved Update Set handoff requires at least one customer update")
    return updates


def _form_layout_customer_updates(
    *,
    client: UpdateSetHandoffClient,
    change: CandidateChange,
    remote_update_set_sys_id: str,
) -> list[dict[str, Any]]:
    table_name = _story_table_name(change.fields)
    element = str(
        change.fields.get("field")
        or change.fields.get("element")
        or change.fields.get("field_name")
        or _custom_field_value(change.fields.get("field_order"))
        or "u_ai_review_notes"
    )
    if table_name != "rm_story" or not element.startswith("u_"):
        raise ValueError("sys_ui_form retrieved handoff must target an rm_story custom field")
    sections = client.fetch_table_records(
        table="sys_ui_section",
        lookup={"name": table_name},
        fields=["sys_id", "name", "caption", "view", "sys_user"],
        limit=100,
    )
    updates: list[dict[str, Any]] = []
    for section in sections:
        if not _is_global_main_story_view_section(section):
            continue
        section_sys_id = _reference_value(section.get("sys_id"))
        elements = client.fetch_table_records(
            table="sys_ui_element",
            lookup={"name": table_name, "sys_ui_section": section_sys_id},
            fields=["sys_id", "element", "position"],
            limit=200,
        )
        description_positions = [
            _record_position(record)
            for record in elements
            if str(record.get("element") or "") == "description"
        ]
        if len(description_positions) != 1:
            raise ValueError("description form element lookup was ambiguous")
        insert_position = description_positions[0] + 1
        planned_elements = _form_elements_with_inserted_field(
            elements=elements,
            field_element=element,
            insert_position=insert_position,
        )
        update_name = f"sys_ui_section_{section_sys_id}"
        updates.append(
            {
                "name": update_name,
                "remote_update_set": remote_update_set_sys_id,
                "action": "INSERT_OR_UPDATE",
                "type": "Form Layout",
                "target_name": "Story",
                "payload": _form_layout_payload(
                    table_name=table_name,
                    section_sys_id=section_sys_id,
                    section=section,
                    elements=planned_elements,
                ),
                "application": "global",
            }
        )
    if not updates:
        raise ValueError("sys_ui_form retrieved handoff found no rm_story main sections")
    return updates


def _is_global_main_story_view_section(section: dict[str, Any]) -> bool:
    if _reference_value(section.get("sys_user")).strip() != "":
        return False
    if _reference_value(section.get("caption")).strip() != "":
        return False
    view = section.get("view")
    if isinstance(view, dict):
        values = {
            str(view.get("display_value") or "").strip().lower(),
            str(view.get("value") or "").strip().lower(),
        }
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


def _form_layout_payload(
    *,
    table_name: str,
    section_sys_id: str,
    section: dict[str, Any],
    elements: list[dict[str, str]],
) -> str:
    caption = _reference_value(section.get("caption"))
    view = section.get("view")
    view_name = ""
    if isinstance(view, dict):
        view_name = str(view.get("display_value") or view.get("value") or "")
        if view_name == "Default view":
            view_name = ""
    element_xml = "".join(
        '<sys_ui_element action="INSERT_OR_UPDATE">'
        f"<element>{escape(element['element'])}</element>"
        f"<position>{escape(element['position'])}</position>"
        f"<sys_id>{escape(element.get('sys_id', ''))}</sys_id>"
        f'<sys_ui_section display_value="{escape(caption)}" name="{escape(table_name)}" '
        f'view="{escape(view_name)}">{escape(section_sys_id)}</sys_ui_section>'
        "</sys_ui_element>"
        for element in elements
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<record_update>"
        f'<sys_ui_section caption="{escape(caption)}" section_id="{escape(section_sys_id)}" '
        f'table="{escape(table_name)}" view="{escape(view_name)}">'
        f"{element_xml}"
        "</sys_ui_section>"
        "</record_update>"
    )


def _dictionary_customer_updates(
    *,
    change: CandidateChange,
    remote_update_set_sys_id: str,
) -> list[dict[str, Any]]:
    fields = dict(change.fields)
    table_name = _story_table_name(fields)
    element = str(
        fields.get("element")
        or fields.get("field_name")
        or fields.get("column_name")
        or _custom_field_value(fields.get("name"))
        or ""
    )
    label = str(
        fields.get("column_label") or fields.get("field_label") or fields.get("label") or ""
    )
    if element == "u_ai_review_notes" and label.strip() == "":
        label = "AI Review Notes"
    internal_type = str(fields.get("internal_type") or fields.get("type") or "string")
    max_length = str(fields.get("max_length") or "8000")
    mandatory = _bool_text(fields.get("mandatory"))
    if table_name.strip() == "" or element.strip() == "" or label.strip() == "":
        raise ValueError("sys_dictionary change missing required retrieved update fields")
    dictionary_name = f"sys_dictionary_{table_name}_{element}"
    documentation_name = f"sys_documentation_{table_name}_{element}_en"
    target_name = f"{_table_label(table_name)}.{label}"
    return [
        {
            "name": dictionary_name,
            "remote_update_set": remote_update_set_sys_id,
            "action": "INSERT_OR_UPDATE",
            "type": "Dictionary",
            "target_name": target_name,
            "payload": _dictionary_payload(
                table_name=table_name,
                element=element,
                label=label,
                internal_type=internal_type,
                max_length=max_length,
                mandatory=mandatory,
            ),
            "application": "global",
        },
        {
            "name": documentation_name,
            "remote_update_set": remote_update_set_sys_id,
            "action": "INSERT_OR_UPDATE",
            "type": "Field Label",
            "target_name": target_name,
            "payload": _documentation_payload(
                table_name=table_name,
                element=element,
                label=label,
            ),
            "application": "global",
        },
    ]


def _story_table_name(fields: dict[str, Any]) -> str:
    raw_table = fields.get("table") or fields.get("table_name")
    if raw_table:
        return str(raw_table)
    raw_name = str(fields.get("name") or "").strip()
    if raw_name.startswith("u_") or raw_name == "":
        return "rm_story"
    return raw_name


def _custom_field_value(value: Any) -> str:
    text = str(value or "").strip()
    return text if text.startswith("u_") else ""


def _dictionary_payload(
    *,
    table_name: str,
    element: str,
    label: str,
    internal_type: str,
    max_length: str,
    mandatory: str,
) -> str:
    update_name = f"sys_dictionary_{table_name}_{element}"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<record_update>"
        f'<sys_dictionary action="INSERT_OR_UPDATE" element="{escape(element)}" '
        f'table="{escape(table_name)}">'
        "<active>true</active>"
        f"<column_label>{escape(label)}</column_label>"
        f"<element>{escape(element)}</element>"
        f'<internal_type display_value="{escape(internal_type.title())}">'
        f"{escape(internal_type)}</internal_type>"
        f"<mandatory>{mandatory}</mandatory>"
        f"<max_length>{escape(max_length)}</max_length>"
        f"<name>{escape(table_name)}</name>"
        "<read_only>false</read_only>"
        "<sys_class_name>sys_dictionary</sys_class_name>"
        '<sys_scope display_value="Global">global</sys_scope>'
        f"<sys_update_name>{escape(update_name)}</sys_update_name>"
        "</sys_dictionary>"
        "</record_update>"
    )


def _documentation_payload(*, table_name: str, element: str, label: str) -> str:
    update_name = f"sys_documentation_{table_name}_{element}_en"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<record_update>"
        f'<sys_documentation element="{escape(element)}" label="{escape(label)}" '
        f'language="en" table="{escape(table_name)}">'
        '<sys_documentation action="INSERT_OR_UPDATE">'
        f"<element>{escape(element)}</element>"
        f"<label>{escape(label)}</label>"
        "<language>en</language>"
        f"<name>{escape(table_name)}</name>"
        f"<plural>{escape(label)}</plural>"
        "<sys_class_name>sys_documentation</sys_class_name>"
        '<sys_scope display_value="Global">global</sys_scope>'
        f"<sys_update_name>{escape(update_name)}</sys_update_name>"
        "</sys_documentation>"
        "</sys_documentation>"
        "</record_update>"
    )


def _bool_text(value: Any) -> str:
    return "true" if str(value).strip().lower() in {"1", "true", "yes"} else "false"


def _table_label(table_name: str) -> str:
    if table_name == "rm_story":
        return "Story"
    return table_name


def _reference_value(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("value") or "")
    return str(value or "")


def _record_position(record: dict[str, Any]) -> int:
    return int(str(record.get("position") or "0"))


def _change_summary_lines(candidate: UpdateSetCandidate) -> list[str]:
    if not candidate.changes:
        return ["- No structured changes were generated."]
    return [
        f"- {change.operation} {change.table}: {_field_summary(change.fields)}"
        for change in candidate.changes
    ]


def _field_summary(fields: dict[str, Any]) -> str:
    if not fields:
        return "no fields"
    return ", ".join(f"{name}={value}" for name, value in fields.items())


def _reviewer_note_lines(candidate: UpdateSetCandidate) -> list[str]:
    if not candidate.reviewer_notes:
        return ["- No reviewer notes generated."]
    return [f"- {note}" for note in candidate.reviewer_notes]
