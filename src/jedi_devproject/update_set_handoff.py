from __future__ import annotations

from datetime import UTC, datetime
from html import escape
from typing import Any, Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from jedi_devproject.business_rule_generation import business_rule_customer_updates
from jedi_devproject.client_script_generation import client_script_customer_updates
from jedi_devproject.generic_dictionary_form import (
    DictionaryFormIntent,
    dictionary_form_customer_updates,
)
from jedi_devproject.models import CandidateChange, CandidateStatus, UpdateSetCandidate
from jedi_devproject.script_include_generation import script_include_customer_updates
from jedi_devproject.servicenow import StoryStateChoice
from jedi_devproject.ui_policy_generation import ui_policy_customer_updates
from jedi_devproject.writeback import build_state_mapping_from_choices


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

    def fetch_story_state_choices(self) -> list[StoryStateChoice]: ...

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
    ready_for_testing_state = _ready_for_testing_state(client)
    client.update_story_fields(
        request.story_sys_id,
        {
            "state": ready_for_testing_state,
            "u_ai_status": "Ready for Testing",
            "u_ai_handoff_type": "retrieved_update_set",
            "u_ai_handoff_reference": update_set_sys_id,
            "u_ai_artifact_reference": request.candidate_artifact_ref,
            "work_notes": (
                f"ServiceNow retrieved Update Set handoff created for {request.story_number}. "
                f"Retrieved Update Set: {update_set_name}\n"
                f"Retrieved Update Set link: {update_set_url}\n"
                f"Candidate artifact: {request.candidate_artifact_ref}."
            ),
        },
    )
    return UpdateSetHandoffResult(
        update_set_sys_id=update_set_sys_id,
        update_set_name=update_set_name,
        update_set_url=update_set_url,
    )


def _ready_for_testing_state(client: UpdateSetHandoffClient) -> str:
    mapping = build_state_mapping_from_choices(
        [choice.model_dump() for choice in client.fetch_story_state_choices()]
    )
    if mapping is None:
        raise RuntimeError("ServiceNow Ready for Testing state choice was not found")
    return mapping.ready_for_testing


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
    tables = {change.table for change in candidate.changes}
    if tables == {"sys_script"}:
        updates = business_rule_customer_updates(
            changes=candidate.changes,
            remote_update_set_sys_id=remote_update_set_sys_id,
        )
    elif tables == {"sys_script_client"}:
        updates = client_script_customer_updates(
            changes=candidate.changes,
            remote_update_set_sys_id=remote_update_set_sys_id,
        )
    elif tables == {"sys_script_include"}:
        updates = script_include_customer_updates(
            changes=candidate.changes,
            remote_update_set_sys_id=remote_update_set_sys_id,
        )
    elif tables == {"sys_ui_policy", "sys_ui_policy_action"}:
        updates = ui_policy_customer_updates(
            changes=candidate.changes,
            remote_update_set_sys_id=remote_update_set_sys_id,
        )
    elif tables.issubset({"sys_dictionary", "sys_ui_form"}):
        intent = _dictionary_form_intent(candidate.changes)
        updates = dictionary_form_customer_updates(
            client=client,
            intent=intent,
            remote_update_set_sys_id=remote_update_set_sys_id,
        )
    else:
        unsupported_tables = tables - {
            "sys_dictionary",
            "sys_ui_form",
            "sys_script",
            "sys_script_client",
            "sys_script_include",
            "sys_ui_policy",
            "sys_ui_policy_action",
        }
        if not unsupported_tables:
            raise ValueError("retrieved Update Set candidate mixes unsupported change types")
        raise ValueError(f"unsupported retrieved Update Set table: {sorted(unsupported_tables)[0]}")
    if not updates:
        raise ValueError("retrieved Update Set handoff requires at least one customer update")
    return updates


def _dictionary_form_intent(changes: list[CandidateChange]) -> DictionaryFormIntent:
    dictionary_change = next(
        (change for change in changes if change.table == "sys_dictionary"),
        None,
    )
    if dictionary_change is None:
        raise ValueError("dictionary/form handoff requires a sys_dictionary change")
    form_change = next((change for change in changes if change.table == "sys_ui_form"), None)
    if form_change is None:
        raise ValueError("dictionary/form handoff requires a sys_ui_form change")

    dictionary_fields = dict(dictionary_change.fields)
    form_fields = dict(form_change.fields)
    target_table = _story_table_name(dictionary_fields)
    form_table = _form_table_name(form_fields, default=target_table)
    if form_table != target_table:
        raise ValueError("dictionary/form handoff changes must target the same table")

    field_name = str(
        dictionary_fields.get("element")
        or dictionary_fields.get("field_name")
        or dictionary_fields.get("column_name")
        or _custom_field_value(dictionary_fields.get("name"))
        or _custom_field_value(form_fields.get("field_order"))
        or form_fields.get("field")
        or form_fields.get("element")
        or form_fields.get("field_name")
        or ""
    )
    field_label = str(
        dictionary_fields.get("column_label")
        or dictionary_fields.get("field_label")
        or dictionary_fields.get("label")
        or ""
    )
    if field_name == "u_ai_review_notes" and field_label.strip() == "":
        field_label = "AI Review Notes"
    field_type = str(
        dictionary_fields.get("internal_type") or dictionary_fields.get("type") or "string"
    )
    if target_table.strip() == "" or field_name.strip() == "" or field_label.strip() == "":
        raise ValueError("sys_dictionary change missing required retrieved update fields")

    return DictionaryFormIntent(
        target_table=target_table,
        field_label=field_label,
        field_name=field_name,
        field_type=field_type,
        reference_table=_reference_table(dictionary_fields),
        reference_qualifier=_reference_qualifier(dictionary_fields),
        max_length=_optional_int(dictionary_fields.get("max_length")),
        mandatory=_bool_value(dictionary_fields.get("mandatory")),
        default_value=str(dictionary_fields.get("default_value") or ""),
        placement_anchor=_placement_anchor(form_fields),
        placement_position=_placement_position(form_fields),
    )


def _form_table_name(fields: dict[str, Any], *, default: str) -> str:
    raw_table = (
        fields.get("table")
        or fields.get("table_name")
        or fields.get("form_name")
        or fields.get("name")
    )
    if raw_table:
        text = str(raw_table)
        if not text.startswith("u_"):
            return _normalize_table_name(text)
    return default


def _reference_table(fields: dict[str, Any]) -> str | None:
    raw_reference = fields.get("reference") or fields.get("reference_table")
    if raw_reference is None:
        return None
    if isinstance(raw_reference, dict):
        return str(raw_reference.get("value") or raw_reference.get("display_value") or "")
    return str(raw_reference)


def _reference_qualifier(fields: dict[str, Any]) -> str | None:
    raw_qualifier = (
        fields.get("reference_qualifier")
        or fields.get("reference_qual")
        or fields.get("reference_qual_condition")
    )
    if raw_qualifier is None:
        return None
    return str(raw_qualifier)


def _placement_anchor(fields: dict[str, Any]) -> str | None:
    explicit_anchor = fields.get("placement_anchor")
    if explicit_anchor:
        return str(explicit_anchor)
    position_hint = str(fields.get("position_hint") or "").strip().lower()
    if "description" in position_hint:
        return "description"
    field_order = str(fields.get("field_order") or "").strip().lower()
    if field_order == "after_description":
        return "description"
    return None


def _placement_position(fields: dict[str, Any]) -> str:
    explicit_position = str(fields.get("placement_position") or "").strip().lower()
    if explicit_position in {"above", "below", "end"}:
        return explicit_position
    position_hint = str(fields.get("position_hint") or "").strip().lower()
    if "above" in position_hint:
        return "above"
    if "end" in position_hint:
        return "end"
    return "below"


def _optional_int(value: Any) -> int | None:
    text = str(value or "").strip()
    return int(text) if text.isdigit() else None


def _bool_value(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _story_table_name(fields: dict[str, Any]) -> str:
    raw_table = fields.get("table") or fields.get("table_name")
    if raw_table:
        return _normalize_table_name(str(raw_table))
    raw_name = str(fields.get("name") or "").strip()
    if raw_name.startswith("u_") or raw_name == "":
        return "rm_story"
    return _normalize_table_name(raw_name)


def _normalize_table_name(value: str) -> str:
    text = value.strip().lower()
    text = text.removesuffix(" table").removesuffix(" form")
    return text.replace(" ", "_")


def _custom_field_value(value: Any) -> str:
    text = str(value or "").strip()
    return text if text.startswith("u_") else ""


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
