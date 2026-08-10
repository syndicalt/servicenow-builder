from __future__ import annotations

from typing import Any, Protocol

from defusedxml import ElementTree
from pydantic import BaseModel, ConfigDict

from jedi_devproject.models import CandidateChange, CandidateStatus, UpdateSetCandidate

UPDATE_SET_APPLY_LOOKUP_NON_JSON_DIAGNOSTIC = (
    "Update Set apply lookup contains non-JSON value"
)
UPDATE_SET_APPLY_CANDIDATE_FIELD_NON_JSON_DIAGNOSTIC = (
    "Update Set apply candidate field contains non-JSON value"
)
UPDATE_SET_APPLY_CHANGE_IDENTIFIER_NON_JSON_DIAGNOSTIC = (
    "Update Set apply change identifier contains non-JSON value"
)
UPDATE_SET_APPLY_CHANGES_NON_JSON_DIAGNOSTIC = (
    "Update Set apply changes contain non-JSON value"
)
UPDATE_SET_APPLY_CHANGE_FIELDS_NON_JSON_DIAGNOSTIC = (
    "Update Set apply change fields contain non-JSON value"
)
UPDATE_SET_APPLY_METADATA_NON_JSON_DIAGNOSTIC = (
    "Update Set apply metadata contains non-JSON value"
)
UPDATE_SET_APPLY_METADATA_MISSING_DIAGNOSTIC = "Update Set apply metadata field is missing"
UPDATE_SET_APPLY_POSITION_INVALID_DIAGNOSTIC = (
    "Update Set apply position field is invalid"
)
UPDATE_SET_APPLY_REQUEST_NON_JSON_DIAGNOSTIC = (
    "Update Set apply request contains non-JSON value"
)
UPDATE_SET_APPLY_RECORDS_NON_JSON_DIAGNOSTIC = (
    "Update Set apply records contain non-JSON value"
)
UPDATE_SET_APPLY_RECORD_NON_JSON_DIAGNOSTIC = (
    "Update Set apply record contains non-JSON value"
)


class UpdateSetApplyClient(Protocol):
    def fetch_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
    ) -> dict[str, Any] | None: ...

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


class UpdateSetApplyRequest(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        hide_input_in_errors=True,
    )

    update_set_sys_id: str
    integration_user_name: str
    candidate: UpdateSetCandidate


class UpdateSetApplyResult(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    applied_change_count: int
    customer_update_count: int


class PlannedFormLayoutChange(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    table_name: str
    element: str
    section_sys_id: str
    section_caption: str
    position: int
    shifted_elements: list[dict[str, str]]


def apply_candidate_to_update_set(
    *,
    client: UpdateSetApplyClient,
    request: UpdateSetApplyRequest,
) -> UpdateSetApplyResult:
    if request.candidate.status is not CandidateStatus.READY_FOR_REVIEW:
        raise ValueError("candidate is not ready for Update Set apply")
    update_set_sys_id = _apply_request_text(request.update_set_sys_id)
    integration_user_name = _apply_request_text(request.integration_user_name)
    changes = _apply_changes(request.candidate.changes)
    custom_dictionary_elements = _custom_dictionary_elements(changes)
    prepared_changes: list[CandidateChange | PlannedFormLayoutChange] = []
    for change in changes:
        prepared_change = _prepare_supported_change(
            client=client,
            change=change,
            custom_dictionary_elements=custom_dictionary_elements,
        )
        if isinstance(prepared_change, list):
            prepared_changes.extend(prepared_change)
        else:
            prepared_changes.append(prepared_change)

    user_sys_id = _integration_user_sys_id(
        client=client,
        integration_user_name=integration_user_name,
    )
    _set_current_update_set(
        client=client,
        user_sys_id=user_sys_id,
        update_set_sys_id=update_set_sys_id,
    )
    for applied_change in prepared_changes:
        if isinstance(applied_change, PlannedFormLayoutChange):
            _apply_form_layout_change(client=client, change=applied_change)
        else:
            _apply_dictionary_change(client=client, change=applied_change)

    customer_updates = _apply_records(
        client.fetch_table_records(
            table="sys_update_xml",
            lookup={"update_set": update_set_sys_id},
            fields=["sys_id", "name", "target_name", "type"],
            limit=100,
        )
    )
    if not customer_updates:
        raise RuntimeError(
            f"no customer updates captured for generated Update Set {request.update_set_sys_id}"  # nosec B608
        )
    return UpdateSetApplyResult(
        applied_change_count=len(prepared_changes),
        customer_update_count=len(customer_updates),
    )


def _prepare_supported_change(
    *,
    client: UpdateSetApplyClient,
    change: CandidateChange,
    custom_dictionary_elements: list[str],
) -> CandidateChange | list[PlannedFormLayoutChange]:
    change_table = _apply_change_identifier_text(change.table)
    fields = _apply_change_fields(change.fields)
    if change_table == "sys_dictionary":
        return _normalize_dictionary_change(change, fields)
    if change_table == "sys_ui_form":
        return _plan_form_layout_change(
            client=client,
            change=change,
            fields=fields,
            custom_dictionary_elements=custom_dictionary_elements,
        )
    raise ValueError(f"unsupported update-set apply table: {change_table}")


def _normalize_dictionary_change(
    change: CandidateChange, fields: dict[str, Any]
) -> CandidateChange:
    operation = _apply_change_identifier_text(change.operation)
    if operation not in {"insert", "update"}:
        raise ValueError(f"unsupported update-set apply operation: {operation}")
    fields = _normalize_dictionary_field_aliases(fields)

    required_fields = ["name", "element", "column_label", "internal_type"]
    missing = [
        field_name
        for field_name in required_fields
        if _apply_candidate_field_text(fields.get(field_name)).strip() == ""
    ]
    if missing:
        raise ValueError("sys_dictionary change missing required fields: " + ", ".join(missing))
    return change.model_copy(update={"fields": _service_now_field_values(fields)})


def _normalize_dictionary_field_aliases(fields: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(fields)
    _copy_alias(normalized, source="column_name", target="element")
    _copy_alias(normalized, source="field_name", target="element")
    _copy_alias(normalized, source="field_label", target="column_label")
    _copy_alias(normalized, source="help_text", target="help")
    _copy_alias(normalized, source="hint", target="help")
    normalized.setdefault("name", "rm_story")
    if normalized.get("element") == "u_ai_review_notes":
        normalized.setdefault("column_label", "AI Review Notes")
    return normalized


def _copy_alias(fields: dict[str, Any], *, source: str, target: str) -> None:
    if (target not in fields or _is_blank(fields.get(target))) and source in fields:
        fields[target] = fields.pop(source)


def _is_blank(value: Any) -> bool:
    return _apply_candidate_field_text(value).strip() == ""


def _plan_form_layout_change(
    *,
    client: UpdateSetApplyClient,
    change: CandidateChange,
    fields: dict[str, Any],
    custom_dictionary_elements: list[str],
) -> list[PlannedFormLayoutChange]:
    operation = _apply_change_identifier_text(change.operation)
    if operation != "update":
        raise ValueError(f"unsupported update-set apply operation: {operation}")
    table_name = _apply_candidate_field_text(
        fields.get("table") or fields.get("name") or "rm_story"
    )
    element = _form_target_element(
        fields=fields, custom_dictionary_elements=custom_dictionary_elements
    )
    view = (
        _apply_candidate_field_text(
            fields.get("view") or fields.get("view_name") or "default"
        )
        .strip()
        .lower()
    )
    if table_name != "rm_story":
        raise ValueError("sys_ui_form change must target rm_story")
    if not element.startswith("u_"):
        raise ValueError("sys_ui_form change must target a custom field")
    if view not in {"", "default"}:
        raise ValueError("only default rm_story form view placement is supported")

    section_name = _apply_candidate_field_text(
        fields.get("form_section_name")
        or fields.get("section_name")
        or fields.get("section")
        or fields.get("caption")
        or _form_xml_attribute(fields, "section")
        or "Notes"
    ).strip()
    if _uses_description_anchor(change=change, fields=fields, element=element):
        return _plan_description_anchor_form_layout_changes(
            client=client,
            table_name=table_name,
            element=element,
        )
    return [
        _plan_named_section_form_layout_change(
            client=client,
            table_name=table_name,
            element=element,
            section_name=section_name,
        )
    ]


def _plan_named_section_form_layout_change(
    *,
    client: UpdateSetApplyClient,
    table_name: str,
    element: str,
    section_name: str,
) -> PlannedFormLayoutChange:
    sections = _apply_records(
        client.fetch_table_records(
            table="sys_ui_section",
            lookup={"name": table_name, "caption": section_name},
            fields=["sys_id", "name", "caption", "view"],
            limit=10,
        )
    )
    if len(sections) != 1:
        raise RuntimeError(f"form section lookup was ambiguous: {section_name}")
    section_sys_id = _required_metadata_reference_value(sections[0].get("sys_id"))
    section_elements = _apply_records(
        client.fetch_table_records(
            table="sys_ui_element",
            lookup={"name": table_name, "sys_ui_section": section_sys_id},
            fields=["sys_id", "element", "position"],
            limit=200,
        )
    )
    insert_position = max([_record_position(record) for record in section_elements], default=-1) + 1
    return _plan_section_form_layout_change(
        table_name=table_name,
        element=element,
        section_sys_id=section_sys_id,
        section_caption=section_name,
        section_elements=section_elements,
        insert_position=insert_position,
    )


def _uses_description_anchor(
    *, change: CandidateChange, fields: dict[str, Any], element: str
) -> bool:
    if element == "u_ai_review_notes":
        return True
    placement_text = " ".join(
        _apply_candidate_field_text(value)
        for value in [
            fields.get("position"),
            fields.get("position_hint"),
            fields.get("placement"),
            fields.get("location"),
            change.rationale,
        ]
    ).lower()
    return "description" in placement_text


def _plan_description_anchor_form_layout_changes(
    *,
    client: UpdateSetApplyClient,
    table_name: str,
    element: str,
) -> list[PlannedFormLayoutChange]:
    sections = _apply_records(
        client.fetch_table_records(
            table="sys_ui_section",
            lookup={"name": table_name},
            fields=["sys_id", "name", "caption", "view", "sys_user"],
            limit=100,
        )
    )
    section_ids = [
        _required_metadata_reference_value(section.get("sys_id"))
        for section in sections
        if _is_global_main_story_view_section(section)
    ]
    if not section_ids:
        raise RuntimeError("description form placement found no global rm_story main sections")
    changes: list[PlannedFormLayoutChange] = []
    for section_sys_id in section_ids:
        section_elements = _apply_records(
            client.fetch_table_records(
                table="sys_ui_element",
                lookup={"name": table_name, "sys_ui_section": section_sys_id},
                fields=["sys_id", "element", "position"],
                limit=200,
            )
        )
        description_positions = [
            _record_position(record)
            for record in section_elements
            if _record_element(record) == "description"
        ]
        if len(description_positions) != 1:
            raise RuntimeError("description form element lookup was ambiguous")
        changes.append(
            _plan_section_form_layout_change(
                table_name=table_name,
                element=element,
                section_sys_id=section_sys_id,
                section_caption="",
                section_elements=section_elements,
                insert_position=description_positions[0] + 1,
            )
        )
    return changes


def _is_global_main_story_view_section(section: dict[str, Any]) -> bool:
    if _reference_value(section.get("sys_user")).strip() != "":
        return False
    if _reference_value(section.get("caption")).strip() != "":
        return False
    view = section.get("view")
    view_values: set[str] = set()
    if type(view) is dict:
        view_values = {
            _apply_metadata_text(view.get("value")).strip().lower(),
            _apply_metadata_text(view.get("display_value")).strip().lower(),
        }
    else:
        view_values = {_apply_metadata_text(view).strip().lower()}
    return bool(view_values.intersection({"", "default", "default view", "scrum"}))


def _plan_section_form_layout_change(
    *,
    table_name: str,
    element: str,
    section_sys_id: str,
    section_caption: str,
    section_elements: list[dict[str, Any]],
    insert_position: int,
) -> PlannedFormLayoutChange:
    shifted_elements = [
        {
            "sys_id": _reference_value(record.get("sys_id")),
            "position": str(_record_position(record) + 1),
        }
        for record in section_elements
        if _record_element(record) != element
        and _record_position(record) >= insert_position
        and _reference_value(record.get("sys_id")).strip() != ""
    ]
    return PlannedFormLayoutChange(
        table_name=table_name,
        element=element,
        section_sys_id=section_sys_id,
        section_caption=section_caption,
        position=insert_position,
        shifted_elements=shifted_elements,
    )


def _custom_dictionary_elements(changes: list[CandidateChange]) -> list[str]:
    elements: list[str] = []
    for change in changes:
        if _apply_change_identifier_text(change.table) != "sys_dictionary":
            continue
        fields = _normalize_dictionary_field_aliases(
            _apply_change_fields(change.fields)
        )
        element = _apply_candidate_field_text(fields.get("element"))
        if element.startswith("u_"):
            elements.append(element)
    return sorted(set(elements))


def _form_target_element(
    *,
    fields: dict[str, Any],
    custom_dictionary_elements: list[str],
) -> str:
    element = _apply_candidate_field_text(
        fields.get("field")
        or fields.get("element")
        or fields.get("field_name")
        or _form_xml_attribute(fields, "name")
        or ""
    )
    if element:
        return element
    if len(custom_dictionary_elements) == 1:
        return custom_dictionary_elements[0]
    raise ValueError("sys_ui_form change must identify one custom field")


def _form_xml_attribute(fields: dict[str, Any], attribute_name: str) -> str | None:
    raw_elements = fields.get("elements")
    if raw_elements is None:
        return None
    if type(raw_elements) is not str:
        raise ValueError(UPDATE_SET_APPLY_CANDIDATE_FIELD_NON_JSON_DIAGNOSTIC)
    if raw_elements.strip() == "":
        return None
    try:
        element = ElementTree.fromstring(raw_elements)
    except ElementTree.ParseError:
        return None
    value = element.attrib.get(attribute_name)
    return value if value else None


def _service_now_field_values(fields: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        field_name: _apply_candidate_field_value(field_value)
        for field_name, field_value in fields.items()
    }
    if "max_length" in normalized and normalized["max_length"] is not None:
        normalized["max_length"] = _apply_candidate_field_text(normalized["max_length"])
    return normalized


def _integration_user_sys_id(
    *,
    client: UpdateSetApplyClient,
    integration_user_name: str,
) -> str:
    user_record = _apply_optional_record(
        client.fetch_table_record(
            table="sys_user",
            lookup={"user_name": integration_user_name},
        )
    )
    user_sys_id = (
        "" if user_record is None else _apply_lookup_text(user_record.get("sys_id"))
    )
    if user_sys_id.strip() == "":
        raise RuntimeError(f"integration user not found: {integration_user_name}")
    return user_sys_id


def _set_current_update_set(
    *,
    client: UpdateSetApplyClient,
    user_sys_id: str,
    update_set_sys_id: str,
) -> None:
    client.upsert_table_record(
        table="sys_user_preference",
        lookup={"name": "sys_update_set", "user": user_sys_id},
        fields={
            "name": "sys_update_set",
            "user": user_sys_id,
            "value": update_set_sys_id,
        },
    )


def _apply_dictionary_change(
    *,
    client: UpdateSetApplyClient,
    change: CandidateChange,
) -> None:
    fields = _apply_change_fields(change.fields)
    client.upsert_table_record(
        table="sys_dictionary",
        lookup={
            "name": _apply_candidate_field_text(fields["name"]),
            "element": _apply_candidate_field_text(fields["element"]),
        },
        fields=fields,
    )


def _apply_form_layout_change(
    *,
    client: UpdateSetApplyClient,
    change: PlannedFormLayoutChange,
) -> None:
    for shifted_element in change.shifted_elements:
        client.upsert_table_record(
            table="sys_ui_element",
            lookup={"sys_id": shifted_element["sys_id"]},
            fields={"position": shifted_element["position"]},
        )
    client.upsert_table_record(
        table="sys_ui_element",
        lookup={
            "name": change.table_name,
            "element": change.element,
            "sys_ui_section": change.section_sys_id,
        },
        fields={
            "name": change.table_name,
            "element": change.element,
            "sys_ui_section": change.section_sys_id,
            "position": str(change.position),
        },
    )
    client.upsert_table_record(
        table="sys_ui_section",
        lookup={"sys_id": change.section_sys_id},
        fields={"caption": change.section_caption},
    )


def _reference_value(value: Any) -> str:
    if type(value) is dict:
        return _apply_metadata_text(value.get("value"))
    return _apply_metadata_text(value)


def _required_metadata_reference_value(value: Any) -> str:
    text = _reference_value(value).strip()
    if text == "":
        raise ValueError(UPDATE_SET_APPLY_METADATA_MISSING_DIAGNOSTIC)
    return text


def _record_position(record: dict[str, Any]) -> int:
    try:
        return int(_apply_metadata_text(record.get("position") or "0"))
    except ValueError as exc:
        if str(exc) == UPDATE_SET_APPLY_METADATA_NON_JSON_DIAGNOSTIC:
            raise
        raise ValueError(UPDATE_SET_APPLY_POSITION_INVALID_DIAGNOSTIC) from None


def _record_element(record: dict[str, Any]) -> str:
    return _apply_metadata_text(record.get("element"))


def _apply_lookup_text(value: Any) -> str:
    if value is None:
        return ""
    if type(value) is str:
        return value
    if type(value) in {bool, int}:
        return str(value)
    raise ValueError(UPDATE_SET_APPLY_LOOKUP_NON_JSON_DIAGNOSTIC)


def _apply_request_text(value: Any) -> str:
    if type(value) is str:
        return value
    raise ValueError(UPDATE_SET_APPLY_REQUEST_NON_JSON_DIAGNOSTIC)


def _apply_change_identifier_text(value: Any) -> str:
    if type(value) is str:
        return value
    raise ValueError(UPDATE_SET_APPLY_CHANGE_IDENTIFIER_NON_JSON_DIAGNOSTIC)


def _apply_changes(changes: Any) -> list[CandidateChange]:
    if type(changes) is not list:
        raise ValueError(UPDATE_SET_APPLY_CHANGES_NON_JSON_DIAGNOSTIC)
    for change in changes:
        if type(change) is not CandidateChange:
            raise ValueError(UPDATE_SET_APPLY_CHANGES_NON_JSON_DIAGNOSTIC)
    return changes


def _apply_change_fields(fields: Any) -> dict[str, Any]:
    if type(fields) is not dict:
        raise ValueError(UPDATE_SET_APPLY_CHANGE_FIELDS_NON_JSON_DIAGNOSTIC)
    for field_name in fields:
        if type(field_name) is not str:
            raise ValueError(UPDATE_SET_APPLY_CHANGE_FIELDS_NON_JSON_DIAGNOSTIC)
    return fields


def _apply_records(records: Any) -> list[dict[str, Any]]:
    if type(records) is not list:
        raise ValueError(UPDATE_SET_APPLY_RECORDS_NON_JSON_DIAGNOSTIC)
    for record in records:
        if type(record) is not dict:
            raise ValueError(UPDATE_SET_APPLY_RECORDS_NON_JSON_DIAGNOSTIC)
    return records


def _apply_optional_record(record: Any) -> dict[str, Any] | None:
    if record is None:
        return None
    if type(record) is dict:
        return record
    raise ValueError(UPDATE_SET_APPLY_RECORD_NON_JSON_DIAGNOSTIC)


def _apply_candidate_field_text(value: Any) -> str:
    if value is None:
        return ""
    if type(value) is str:
        return value
    if type(value) in {bool, int}:
        return str(value)
    raise ValueError(UPDATE_SET_APPLY_CANDIDATE_FIELD_NON_JSON_DIAGNOSTIC)


def _apply_candidate_field_value(value: Any) -> Any:
    if value is None:
        return None
    if type(value) in {str, bool, int}:
        return value
    raise ValueError(UPDATE_SET_APPLY_CANDIDATE_FIELD_NON_JSON_DIAGNOSTIC)


def _apply_metadata_text(value: Any) -> str:
    if value is None:
        return ""
    if type(value) is str:
        return value
    if type(value) in {bool, int}:
        return str(value)
    raise ValueError(UPDATE_SET_APPLY_METADATA_NON_JSON_DIAGNOSTIC)
