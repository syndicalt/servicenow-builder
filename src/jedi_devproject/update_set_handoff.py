from __future__ import annotations

import math
from datetime import UTC, datetime
from html import escape
from typing import Any, Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from jedi_devproject.generic_dictionary_form import (
    DictionaryFormIntent,
    dictionary_form_customer_updates,
)
from jedi_devproject.models import CandidateChange, CandidateStatus, UpdateSetCandidate
from jedi_devproject.servicenow import StoryStateChoice
from jedi_devproject.ui_policy_generation import ui_policy_customer_updates
from jedi_devproject.work_note_safety import safe_work_note_value
from jedi_devproject.writeback import build_state_mapping_from_choices

CUSTOMER_UPDATE_NON_JSON_DIAGNOSTIC = (
    "retrieved Update Set customer update contains non-JSON value"
)
DICTIONARY_FORM_FIELD_NON_JSON_DIAGNOSTIC = (
    "dictionary/form handoff field contains non-JSON value"
)
IMPORTED_UPDATE_SET_LOOKUP_NON_JSON_DIAGNOSTIC = (
    "retrieved Update Set lookup contains non-JSON value"
)
IMPORTED_UPDATE_SET_METADATA_NON_JSON_DIAGNOSTIC = (
    "retrieved Update Set metadata contains non-JSON value"
)
HANDOFF_CHANGES_NON_JSON_DIAGNOSTIC = (
    "retrieved Update Set handoff changes contain non-JSON value"
)
HANDOFF_CHANGE_FIELDS_NON_JSON_DIAGNOSTIC = (
    "retrieved Update Set handoff change fields contain non-JSON value"
)
HANDOFF_REVIEWER_NOTES_NON_JSON_DIAGNOSTIC = (
    "retrieved Update Set handoff reviewer notes contain non-JSON value"
)
HANDOFF_STORY_NUMBER_NON_JSON_DIAGNOSTIC = (
    "retrieved Update Set handoff story number contains non-JSON value"
)
HANDOFF_STORY_SYS_ID_NON_JSON_DIAGNOSTIC = (
    "retrieved Update Set handoff story sys_id contains non-JSON value"
)
HANDOFF_ARTIFACT_REF_NON_JSON_DIAGNOSTIC = (
    "retrieved Update Set handoff artifact reference contains non-JSON value"
)
HANDOFF_INSTANCE_URL_NON_JSON_DIAGNOSTIC = (
    "retrieved Update Set handoff instance URL contains non-JSON value"
)
HANDOFF_STATE_CHOICES_NON_JSON_DIAGNOSTIC = (
    "retrieved Update Set handoff state choices contain non-JSON value"
)
NON_JSON_SUMMARY_KEY = "[non-json summary key]"
NON_JSON_SUMMARY_VALUE = "[non-json summary value]"
MAX_UPDATE_SET_SUMMARY_VALUE_CHARS = 500


class UpdateSetImportClient(Protocol):
    """Narrow client surface needed to import a Retrieved Update Set."""

    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...

    def import_update_set_xml(
        self,
        *,
        service_id: str,
        update_set_xml: str,
    ) -> dict[str, Any]: ...


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
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        hide_input_in_errors=True,
    )

    story_sys_id: str
    story_number: str
    candidate: UpdateSetCandidate
    candidate_artifact_ref: str
    instance_url: str


class UpdateSetHandoffResult(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

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

    story_sys_id = _handoff_story_sys_id(request.story_sys_id)
    candidate_artifact_ref = _handoff_artifact_ref(request.candidate_artifact_ref)
    update_set_name = _update_set_name(request.story_number)
    remote_sys_id = _remote_sys_id(request.candidate)
    customer_updates = _customer_updates_for_candidate(
        client=client,
        candidate=request.candidate,
        remote_update_set_sys_id=remote_sys_id,
    )
    update_set_sys_id = import_retrieved_update_set(
        client=client,
        update_set_name=update_set_name,
        remote_sys_id=remote_sys_id,
        description=_update_set_description(request),
        customer_updates=customer_updates,
    )

    update_set_url = _update_set_url(
        instance_url=request.instance_url,
        update_set_sys_id=update_set_sys_id,
    )
    ready_for_testing_state = _ready_for_testing_state(client)
    client.update_story_fields(
        story_sys_id,
        {
            "state": ready_for_testing_state,
            "u_ai_status": "Ready for Testing",
            "u_ai_handoff_type": "retrieved_update_set",
            "u_ai_handoff_reference": update_set_sys_id,
            "u_ai_artifact_reference": candidate_artifact_ref,
            "work_notes": _handoff_work_notes(
                story_number=request.story_number,
                update_set_name=update_set_name,
                update_set_url=update_set_url,
                candidate_artifact_ref=candidate_artifact_ref,
            ),
        },
    )
    return UpdateSetHandoffResult(
        update_set_sys_id=update_set_sys_id,
        update_set_name=update_set_name,
        update_set_url=update_set_url,
    )


def _handoff_work_notes(
    *,
    story_number: str,
    update_set_name: str,
    update_set_url: str,
    candidate_artifact_ref: str,
) -> str:
    return (
        "ServiceNow retrieved Update Set handoff created for "  # nosec B608
        f"{safe_work_note_value(story_number)}. "
        f"Retrieved Update Set: {safe_work_note_value(update_set_name)}\n"
        f"Retrieved Update Set link: {safe_work_note_value(update_set_url)}\n"
        f"Candidate artifact: {safe_work_note_value(candidate_artifact_ref)}."
    )


def import_retrieved_update_set(
    *,
    client: UpdateSetImportClient,
    update_set_name: str,
    remote_sys_id: str,
    description: str,
    customer_updates: list[dict[str, Any]],
) -> str:
    """Import customer updates as a loaded Retrieved Update Set; return its sys_id.

    The imported set is left in the ``loaded`` state. ServiceNow-native
    preview/commit remains the human review boundary; nothing here commits.
    """
    update_set_name = _import_metadata_text(update_set_name)
    remote_sys_id = _import_metadata_text(remote_sys_id)
    description = _import_metadata_text(description)
    customer_updates = _customer_updates(customer_updates)
    update_set_xml = _update_set_unload_xml(
        update_set_name=update_set_name,
        remote_sys_id=remote_sys_id,
        description=description,
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
    update_set_sys_id = _imported_update_set_sys_id(imported_update_sets)
    if update_set_sys_id.strip() == "":
        raise RuntimeError("ServiceNow imported Update Set lookup did not include sys_id")
    return update_set_sys_id


def _ready_for_testing_state(client: UpdateSetHandoffClient) -> str:
    mapping = build_state_mapping_from_choices(
        [choice.model_dump() for choice in _handoff_state_choices(client)]
    )
    if mapping is None:
        raise RuntimeError("ServiceNow Ready for Testing state choice was not found")
    return mapping.ready_for_testing


def _handoff_state_choices(client: UpdateSetHandoffClient) -> list[StoryStateChoice]:
    choices = client.fetch_story_state_choices()
    if type(choices) is not list:
        raise ValueError(HANDOFF_STATE_CHOICES_NON_JSON_DIAGNOSTIC)
    for choice in choices:
        if type(choice) is not StoryStateChoice:
            raise ValueError(HANDOFF_STATE_CHOICES_NON_JSON_DIAGNOSTIC)
    return choices


def _update_set_name(story_number: object) -> str:
    if type(story_number) is not str:
        raise ValueError(HANDOFF_STORY_NUMBER_NON_JSON_DIAGNOSTIC)
    return f"JEDI {story_number} - AI Candidate"


def _handoff_story_sys_id(story_sys_id: object) -> str:
    if type(story_sys_id) is str:
        return story_sys_id
    raise ValueError(HANDOFF_STORY_SYS_ID_NON_JSON_DIAGNOSTIC)


def _handoff_artifact_ref(candidate_artifact_ref: object) -> str:
    if type(candidate_artifact_ref) is str:
        return candidate_artifact_ref
    raise ValueError(HANDOFF_ARTIFACT_REF_NON_JSON_DIAGNOSTIC)


def _update_set_url(*, instance_url: object, update_set_sys_id: str) -> str:
    if type(instance_url) is not str:
        raise ValueError(HANDOFF_INSTANCE_URL_NON_JSON_DIAGNOSTIC)
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
    payload = _customer_update_scalar(update, "payload")
    payload = payload.replace("]]>", "]]]]><![CDATA[>")
    return (
        '<sys_update_xml action="INSERT_OR_UPDATE">\n'
        f"<action>{escape(_customer_update_scalar(update, 'action'))}</action>\n"
        '<application display_value="Global">global</application>\n'
        f"<name>{escape(_customer_update_scalar(update, 'name'))}</name>\n"
        f"<payload><![CDATA[{payload}]]></payload>\n"
        f'<remote_update_set display_value="{escape(update_set_name)}">'
        f"{escape(remote_sys_id)}</remote_update_set>\n"
        "<sys_class_name>sys_update_xml</sys_class_name>\n"
        f"<sys_id>{uuid4().hex}</sys_id>\n"
        f"<target_name>{escape(_customer_update_scalar(update, 'target_name'))}</target_name>\n"
        f"<type>{escape(_customer_update_scalar(update, 'type'))}</type>\n"
        "</sys_update_xml>"
    )


def _customer_update_scalar(update: dict[str, Any], key: str) -> str:
    value = update.get(key)
    if type(value) is str:
        return value
    raise ValueError(CUSTOMER_UPDATE_NON_JSON_DIAGNOSTIC)


def _customer_updates(updates: object) -> list[dict[str, Any]]:
    if type(updates) is not list:
        raise ValueError(CUSTOMER_UPDATE_NON_JSON_DIAGNOSTIC)
    if any(type(update) is not dict for update in updates):
        raise ValueError(CUSTOMER_UPDATE_NON_JSON_DIAGNOSTIC)
    return updates


def _import_metadata_text(value: object) -> str:
    if type(value) is str:
        return value
    raise ValueError(IMPORTED_UPDATE_SET_METADATA_NON_JSON_DIAGNOSTIC)


def _update_set_description(request: UpdateSetHandoffRequest) -> str:
    candidate = request.candidate
    lines = [
        "Jedi DevProject generated retrieved update set for "  # nosec B608
        f"{safe_work_note_value(request.story_number)}.",
        "",
        f"Candidate artifact: {safe_work_note_value(request.candidate_artifact_ref)}",
        f"Candidate hash: {_description_optional_text(candidate.artifact_hash)}",
        f"Status: {candidate.status.value}",
        f"Confidence: {_description_metric_text(candidate.confidence)}",
        f"Risk score: {_description_metric_text(candidate.risk_score)}",
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


def _description_optional_text(value: object | None) -> str:
    if value is None:
        return "unavailable"
    return safe_work_note_value(value)


def _description_metric_text(value: object) -> str:
    if type(value) is int:
        return str(value)
    if type(value) is float and math.isfinite(value):
        return str(value)
    return NON_JSON_SUMMARY_VALUE


def _remote_sys_id(candidate: UpdateSetCandidate) -> str:
    source = _remote_sys_id_source(candidate)
    sanitized = "".join(
        character for character in source.lower() if character in "0123456789abcdef"
    )
    return (sanitized + ("0" * 32))[:32]


def _remote_sys_id_source(candidate: UpdateSetCandidate) -> str:
    artifact_hash = candidate.artifact_hash
    if type(artifact_hash) is str and artifact_hash != "":
        return artifact_hash
    name = candidate.name
    if type(name) is str and name != "":
        return name
    return "jedi-candidate"


def _customer_updates_for_candidate(
    *,
    client: UpdateSetHandoffClient,
    candidate: UpdateSetCandidate,
    remote_update_set_sys_id: str,
) -> list[dict[str, Any]]:
    changes = _candidate_changes(candidate)
    if len(changes) == 0:
        raise ValueError("retrieved Update Set handoff requires at least one candidate change")
    tables = {_handoff_change_identifier_text(change.table) for change in changes}
    if tables.issubset({"sys_dictionary", "sys_ui_form"}):
        intent = _dictionary_form_intent(changes)
        updates = dictionary_form_customer_updates(
            client=client,
            intent=intent,
            remote_update_set_sys_id=remote_update_set_sys_id,
        )
    elif tables.issubset({"sys_ui_policy", "sys_ui_policy_action"}):
        updates = ui_policy_customer_updates(
            changes=changes,
            remote_update_set_sys_id=remote_update_set_sys_id,
        )
    else:
        raise ValueError(
            "no mature deterministic retrieved Update Set builder for candidate tables: "  # nosec B608
            f"{', '.join(sorted(tables))}"
        )
    updates = _customer_updates(updates)
    if len(updates) == 0:
        raise ValueError("retrieved Update Set handoff requires at least one customer update")
    return updates


def _candidate_changes(candidate: UpdateSetCandidate) -> list[CandidateChange]:
    changes = candidate.changes
    if type(changes) is not list:
        raise ValueError(HANDOFF_CHANGES_NON_JSON_DIAGNOSTIC)
    if any(type(change) is not CandidateChange for change in changes):
        raise ValueError(HANDOFF_CHANGES_NON_JSON_DIAGNOSTIC)
    return changes


def _handoff_change_identifier_text(value: Any) -> str:
    if type(value) is str:
        return value
    raise ValueError(HANDOFF_CHANGES_NON_JSON_DIAGNOSTIC)


def _dictionary_form_intent(changes: list[CandidateChange]) -> DictionaryFormIntent:
    dictionary_change = next(
        (
            change
            for change in changes
            if _handoff_change_identifier_text(change.table) == "sys_dictionary"
        ),
        None,
    )
    if dictionary_change is None:
        raise ValueError("dictionary/form handoff requires a sys_dictionary change")
    form_change = next(
        (
            change
            for change in changes
            if _handoff_change_identifier_text(change.table) == "sys_ui_form"
        ),
        None,
    )
    if form_change is None:
        raise ValueError("dictionary/form handoff requires a sys_ui_form change")

    dictionary_fields = _handoff_change_fields(dictionary_change.fields)
    form_fields = _handoff_change_fields(form_change.fields)
    target_table = _story_table_name(dictionary_fields)
    form_table = _form_table_name(form_fields, default=target_table)
    if form_table != target_table:
        raise ValueError("dictionary/form handoff changes must target the same table")

    field_name = _candidate_field_text(
        _first_present(
            dictionary_fields.get("element"),
            dictionary_fields.get("field_name"),
            dictionary_fields.get("column_name"),
            _custom_field_value(dictionary_fields.get("name")),
            _custom_field_value(form_fields.get("field_order")),
            form_fields.get("field"),
            form_fields.get("element"),
            form_fields.get("field_name"),
            "",
        )
    )
    field_label = _candidate_field_text(
        _first_present(
            dictionary_fields.get("column_label"),
            dictionary_fields.get("field_label"),
            dictionary_fields.get("label"),
            "",
        )
    )
    if field_name == "u_ai_review_notes" and field_label.strip() == "":
        field_label = "AI Review Notes"
    field_type = _candidate_field_text(
        _first_present(
            dictionary_fields.get("internal_type"),
            dictionary_fields.get("type"),
            "string",
        )
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
        default_value=_candidate_field_text(dictionary_fields.get("default_value")),
        placement_anchor=_placement_anchor(form_fields),
        placement_position=_placement_position(form_fields),
    )


def _form_table_name(fields: dict[str, Any], *, default: str) -> str:
    raw_table = _first_present(
        fields.get("table"),
        fields.get("table_name"),
        fields.get("form_name"),
        fields.get("name"),
    )
    if _candidate_field_present(raw_table):
        text = _candidate_field_text(raw_table)
        if not text.startswith("u_"):
            return _normalize_table_name(text)
    return default


def _reference_table(fields: dict[str, Any]) -> str | None:
    raw_reference = _first_present(fields.get("reference"), fields.get("reference_table"))
    if not _candidate_field_present(raw_reference):
        return None
    if type(raw_reference) is dict:
        return _candidate_field_text(
            _first_present(raw_reference.get("value"), raw_reference.get("display_value"), "")
        )
    return _candidate_field_text(raw_reference)


def _reference_qualifier(fields: dict[str, Any]) -> str | None:
    raw_qualifier = _first_present(
        fields.get("reference_qualifier"),
        fields.get("reference_qual"),
        fields.get("reference_qual_condition"),
    )
    if not _candidate_field_present(raw_qualifier):
        return None
    return _candidate_field_text(raw_qualifier)


def _placement_anchor(fields: dict[str, Any]) -> str | None:
    explicit_anchor = fields.get("placement_anchor")
    if _candidate_field_present(explicit_anchor):
        return _candidate_field_text(explicit_anchor)
    position_hint = _candidate_field_text(fields.get("position_hint")).strip().lower()
    if "description" in position_hint:
        return "description"
    field_order = _candidate_field_text(fields.get("field_order")).strip().lower()
    if field_order == "after_description":
        return "description"
    return None


def _placement_position(fields: dict[str, Any]) -> str:
    explicit_position = _candidate_field_text(fields.get("placement_position")).strip().lower()
    if explicit_position in {"above", "below", "end"}:
        return explicit_position
    position_hint = _candidate_field_text(fields.get("position_hint")).strip().lower()
    if "above" in position_hint:
        return "above"
    if "end" in position_hint:
        return "end"
    return "below"


def _optional_int(value: Any) -> int | None:
    text = _candidate_field_text(value).strip()
    return int(text) if text.isdigit() else None


def _bool_value(value: Any) -> bool:
    return _candidate_field_text(value).strip().lower() in {"1", "true", "yes"}


def _story_table_name(fields: dict[str, Any]) -> str:
    raw_table = _first_present(fields.get("table"), fields.get("table_name"))
    if _candidate_field_present(raw_table):
        return _normalize_table_name(_candidate_field_text(raw_table))
    raw_name = _candidate_field_text(fields.get("name")).strip()
    if raw_name.startswith("u_") or raw_name == "":
        return "rm_story"
    return _normalize_table_name(raw_name)


def _normalize_table_name(value: str) -> str:
    text = value.strip().lower()
    text = text.removesuffix(" table").removesuffix(" form")
    return text.replace(" ", "_")


def _custom_field_value(value: Any) -> str:
    text = _candidate_field_text(value).strip()
    return text if text.startswith("u_") else ""


def _first_present(*values: Any) -> Any:
    for value in values:
        if _candidate_field_present(value):
            return value
    return ""


def _candidate_field_present(value: Any) -> bool:
    if value is None:
        return False
    if type(value) is str:
        return value != ""
    if type(value) is bool:
        return value
    if type(value) is int:
        return value != 0
    return True


def _candidate_field_text(value: Any) -> str:
    if value is None:
        return ""
    if type(value) is str:
        return value
    if type(value) in {bool, int}:
        return str(value)
    raise ValueError(DICTIONARY_FORM_FIELD_NON_JSON_DIAGNOSTIC)


def _imported_update_set_lookup_text(value: Any) -> str:
    if value is None:
        return ""
    if type(value) is str:
        return value
    if type(value) in {bool, int}:
        return str(value)
    raise ValueError(IMPORTED_UPDATE_SET_LOOKUP_NON_JSON_DIAGNOSTIC)


def _imported_update_set_sys_id(records: object) -> str:
    if type(records) is not list:
        raise ValueError(IMPORTED_UPDATE_SET_LOOKUP_NON_JSON_DIAGNOSTIC)
    if len(records) == 0:
        return ""
    record = records[0]
    if type(record) is not dict:
        raise ValueError(IMPORTED_UPDATE_SET_LOOKUP_NON_JSON_DIAGNOSTIC)
    return _imported_update_set_lookup_text(record.get("sys_id"))


def _change_summary_lines(candidate: UpdateSetCandidate) -> list[str]:
    changes = _candidate_changes(candidate)
    if len(changes) == 0:
        return ["- No structured changes were generated."]
    return [
        "- "
        f"{_handoff_change_identifier_text(change.operation)} "
        f"{_handoff_change_identifier_text(change.table)}: "
        f"{_field_summary(_handoff_change_fields(change.fields))}"
        for change in changes
    ]


def _handoff_change_fields(fields: Any) -> dict[str, Any]:
    if type(fields) is not dict:
        raise ValueError(HANDOFF_CHANGE_FIELDS_NON_JSON_DIAGNOSTIC)
    for field_name in fields:
        if type(field_name) is not str:
            raise ValueError(HANDOFF_CHANGE_FIELDS_NON_JSON_DIAGNOSTIC)
    return fields


def _field_summary(fields: dict[str, Any]) -> str:
    if len(fields) == 0:
        return "no fields"
    return ", ".join(
        f"{_summary_key(name)}={_summary_value(value)}" for name, value in fields.items()
    )


def _summary_key(value: Any) -> str:
    if type(value) is str:
        return safe_work_note_value(value, max_chars=MAX_UPDATE_SET_SUMMARY_VALUE_CHARS)
    return NON_JSON_SUMMARY_KEY


def _summary_value(value: Any) -> str:
    if value is None:
        return "null"
    if type(value) is str:
        return safe_work_note_value(value, max_chars=MAX_UPDATE_SET_SUMMARY_VALUE_CHARS)
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is int:
        return str(value)
    if type(value) is float and math.isfinite(value):
        return str(value)
    return NON_JSON_SUMMARY_VALUE


def _reviewer_note_lines(candidate: UpdateSetCandidate) -> list[str]:
    reviewer_notes = _reviewer_notes(candidate)
    if len(reviewer_notes) == 0:
        return ["- No reviewer notes generated."]
    return [f"- {safe_work_note_value(note)}" for note in reviewer_notes]


def _reviewer_notes(candidate: UpdateSetCandidate) -> list[str]:
    reviewer_notes = candidate.reviewer_notes
    if type(reviewer_notes) is not list:
        raise ValueError(HANDOFF_REVIEWER_NOTES_NON_JSON_DIAGNOSTIC)
    return reviewer_notes
