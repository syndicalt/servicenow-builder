from __future__ import annotations

from typing import Any, SupportsIndex

import pytest

import jedi_devproject.update_set_handoff as update_set_handoff_module
from jedi_devproject.form_section_generation import (
    FORM_SECTION_FIELD_NON_JSON_DIAGNOSTIC,
    form_section_customer_updates,
)
from jedi_devproject.models import (
    CandidateChange,
    CandidateStatus,
    UpdateSetCandidate,
)
from jedi_devproject.servicenow import StoryStateChoice
from jedi_devproject.update_set_handoff import (
    CUSTOMER_UPDATE_NON_JSON_DIAGNOSTIC,
    IMPORTED_UPDATE_SET_LOOKUP_NON_JSON_DIAGNOSTIC,
    UpdateSetHandoffRequest,
    create_update_set_handoff,
    import_retrieved_update_set,
)


class FakeUpdateSetClient:
    def __init__(self) -> None:
        self.fetches: list[dict[str, object]] = []
        self.upserts: list[dict[str, Any]] = []
        self.story_updates: list[dict[str, Any]] = []
        self.imports: list[dict[str, str]] = []

    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        self.fetches.append({"table": table, "lookup": lookup, "fields": fields, "limit": limit})
        if table == "sys_remote_update_set" and lookup == {
            "remote_sys_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        }:
            return [
                {
                    "sys_id": "remote-update-set-sys-id",
                    "name": "JEDI STRY0010013 - AI Candidate",
                    "state": "loaded",
                }
            ]
        if table == "sys_remote_update_set" and str(lookup.get("remote_sys_id") or "").strip():
            return [
                {
                    "sys_id": "remote-update-set-sys-id",
                    "name": "JEDI Generated AI Candidate",
                    "state": "loaded",
                }
            ]
        if table == "sys_ui_section" and lookup == {"name": "rm_story"}:
            return [
                {
                    "sys_id": "default-main-section-sys-id",
                    "name": "rm_story",
                    "caption": "",
                    "view": {"display_value": "Default view", "value": "Default view"},
                    "sys_user": "",
                },
                {
                    "sys_id": "scrum-main-section-sys-id",
                    "name": "rm_story",
                    "caption": "",
                    "view": {"display_value": "Scrum", "value": "scrum-view-sys-id"},
                    "sys_user": "",
                },
                {
                    "sys_id": "notes-section-sys-id",
                    "name": "rm_story",
                    "caption": "Notes",
                    "view": {"display_value": "Scrum", "value": "scrum-view-sys-id"},
                    "sys_user": "",
                },
            ]
        if table == "sys_ui_section" and lookup == {"name": "problem"}:
            return [
                {
                    "sys_id": "problem-main-section-sys-id",
                    "name": "problem",
                    "caption": "",
                    "view": {"display_value": "Default view", "value": "Default view"},
                    "sys_user": "",
                },
            ]
        if table == "sys_ui_section" and lookup == {"name": "dmn_demand"}:
            return [
                {
                    "sys_id": "demand-main-section-sys-id",
                    "name": "dmn_demand",
                    "caption": "",
                    "view": {"display_value": "Default view", "value": "Default view"},
                    "sys_user": "",
                },
                {
                    "sys_id": "demand-assessment-section-sys-id",
                    "name": "dmn_demand",
                    "caption": "Assessment Data",
                    "view": {"display_value": "Default view", "value": "Default view"},
                    "sys_user": "",
                },
                {
                    "sys_id": "demand-financials-section-sys-id",
                    "name": "dmn_demand",
                    "caption": "Financials",
                    "view": {"display_value": "Default view", "value": "Default view"},
                    "sys_user": "",
                },
            ]
        if table == "sys_ui_element" and lookup == {
            "name": "rm_story",
            "sys_ui_section": "default-main-section-sys-id",
        }:
            return [
                {"sys_id": "default-number-element-sys-id", "element": "number", "position": "1"},
                {
                    "sys_id": "default-description-element-sys-id",
                    "element": "description",
                    "position": "4",
                },
                {
                    "sys_id": "default-acceptance-element-sys-id",
                    "element": "acceptance_criteria",
                    "position": "5",
                },
            ]
        if table == "sys_ui_element" and lookup == {
            "name": "rm_story",
            "sys_ui_section": "scrum-main-section-sys-id",
        }:
            return [
                {"sys_id": "scrum-number-element-sys-id", "element": "number", "position": "0"},
                {
                    "sys_id": "scrum-description-element-sys-id",
                    "element": "description",
                    "position": "19",
                },
                {
                    "sys_id": "scrum-acceptance-element-sys-id",
                    "element": "acceptance_criteria",
                    "position": "20",
                },
            ]
        if table == "sys_ui_element" and lookup == {
            "name": "problem",
            "sys_ui_section": "problem-main-section-sys-id",
        }:
            return [
                {
                    "sys_id": "problem-description-element-sys-id",
                    "element": "description",
                    "position": "8",
                },
            ]
        if table == "sc_catalog" and lookup == {}:
            return [
                {
                    "sys_id": "service-catalog-sys-id",
                    "title": "Service Catalog",
                    "active": "true",
                }
            ]
        if table == "sc_category" and lookup == {}:
            return [
                {
                    "sys_id": "services-category-sys-id",
                    "title": "Services",
                    "active": "true",
                    "sc_catalog": {
                        "value": "service-catalog-sys-id",
                        "display_value": "Service Catalog",
                    },
                }
            ]
        if table == "taxonomy" and lookup == {}:
            return [
                {
                    "sys_id": "employee-taxonomy-sys-id",
                    "name": "Employee",
                    "active": "true",
                }
            ]
        if table == "topic" and lookup == {}:
            return [
                {
                    "sys_id": "access-topic-sys-id",
                    "name": "Access issues",
                    "topic_path": "Technology services / Software / Access issues",
                    "active": "true",
                    "taxonomy": {
                        "value": "employee-taxonomy-sys-id",
                        "display_value": "Employee",
                    },
                }
            ]
        if table == "taxonomy_content_configuration" and lookup == {}:
            return [
                {
                    "sys_id": "catalog-item-content-type-sys-id",
                    "name": "Catalog Item",
                    "active": "true",
                }
            ]
        return []

    def upsert_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: dict[str, Any],
    ) -> dict[str, Any]:
        self.upserts.append({"table": table, "lookup": lookup, "fields": fields})
        return {"sys_id": "update-set-sys-id", "name": fields["name"]}

    def update_story_fields(self, story_sys_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        self.story_updates.append({"story_sys_id": story_sys_id, "fields": fields})
        return {"sys_id": story_sys_id}

    def fetch_story_state_choices(self) -> list[StoryStateChoice]:
        return [
            StoryStateChoice(label="Ready", value="1", sequence=100),
            StoryStateChoice(label="Work in Progress", value="2", sequence=200),
            StoryStateChoice(label="Ready for Testing", value="-7", sequence=300),
        ]

    def import_update_set_xml(
        self,
        *,
        service_id: str,
        update_set_xml: str,
    ) -> dict[str, Any]:
        self.imports.append({"service_id": service_id, "update_set_xml": update_set_xml})
        return {"status_code": 201, "result": {"status": "imported"}}


def _candidate() -> UpdateSetCandidate:
    return UpdateSetCandidate(
        story_number="STRY0010013",
        name="UPD_STRY0010013_LLM_Implementation",
        eligibility_decision="eligible",
        eligibility_reasons=["Low-risk dictionary/form story."],
        confidence=0.75,
        risk_score=0.1,
        status=CandidateStatus.READY_FOR_REVIEW,
        changes=[
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_ai_review_notes",
                    "column_label": "AI Review Notes",
                },
                rationale="Add the requested review notes field.",
            ),
            CandidateChange(
                table="sys_ui_form",
                operation="update",
                fields={
                    "name": "rm_story",
                    "field_order": "u_ai_review_notes",
                    "placement_anchor": "description",
                    "placement_position": "below",
                },
                rationale="Place the requested field on the Story form.",
            ),
        ],
        reviewer_notes=["Confirm the field exists."],
        artifact_hash="a" * 64,
    )


def _dictionary_form_candidate() -> UpdateSetCandidate:
    return _candidate()


def _aliased_dictionary_form_candidate() -> UpdateSetCandidate:
    return _candidate().model_copy(
        update={
            "changes": [
                CandidateChange(
                    table="sys_dictionary",
                    operation="insert",
                    fields={
                        "name": "rm_story",
                        "column_name": "u_ai_review_notes",
                        "field_label": "AI Review Notes",
                        "help_text": "Notes from human review.",
                        "mandatory": False,
                        "max_length": 8000,
                        "default_value": "",
                        "internal_type": "string",
                    },
                    rationale="Create the requested field.",
                ),
                CandidateChange(
                    table="sys_ui_form",
                    operation="insert",
                    fields={
                        "form_name": "rm_story",
                        "field_name": "u_ai_review_notes",
                        "field_order": "after_description",
                        "section_name": "notes",
                    },
                    rationale="Place the requested field on the Story form.",
                ),
            ]
        }
    )


def _minimal_model_dictionary_form_candidate() -> UpdateSetCandidate:
    return _candidate().model_copy(
        update={
            "changes": [
                CandidateChange(
                    table="sys_dictionary",
                    operation="insert",
                    fields={
                        "name": "u_ai_review_notes",
                        "type": "string",
                        "label": "AI Review Notes",
                        "help_text": "Notes from human review.",
                        "mandatory": False,
                        "max_length": 8000,
                        "default_value": "",
                    },
                    rationale="Create the requested field on the Story table.",
                ),
                CandidateChange(
                    table="sys_ui_form",
                    operation="update",
                    fields={"field_order": "u_ai_review_notes"},
                    rationale="Place the requested field on the Story form.",
                ),
            ]
        }
    )


def _catalog_item_candidate() -> UpdateSetCandidate:
    return UpdateSetCandidate(
        story_number="STRY0010101",
        name="UPD_STRY0010101_LLM_Implementation",
        eligibility_decision="eligible",
        eligibility_reasons=["supported standard catalog item generation request"],
        confidence=0.77,
        risk_score=0.22,
        status=CandidateStatus.READY_FOR_REVIEW,
        changes=[
            CandidateChange(
                table="sc_cat_item",
                operation="insert",
                fields={
                    "name": "Request Temporary Badge",
                    "short_description": "Request a temporary access badge for a visitor.",
                    "description": "Use this item when a visitor needs temporary access.",
                    "catalog": "Service Catalog",
                    "category": "Services",
                    "taxonomy": "Employee",
                    "employee_center_topic": "Technology services / Software / Access issues",
                },
                rationale="Create the standard catalog item.",
            ),
            CandidateChange(
                table="item_option_new",
                operation="insert",
                fields={
                    "name": "visitor_name",
                    "question_text": "Visitor name",
                    "type": "single_line_text",
                    "mandatory": "true",
                    "order": "100",
                },
                rationale="Collect the visitor name.",
            ),
            CandidateChange(
                table="item_option_new",
                operation="insert",
                fields={
                    "name": "sponsor",
                    "question_text": "Sponsor",
                    "type": "reference",
                    "reference": "sys_user",
                    "reference_qualifier": "active=true",
                    "mandatory": "true",
                    "order": "200",
                },
                rationale="Collect the sponsoring employee.",
            ),
            CandidateChange(
                table="sc_cat_item_category",
                operation="insert",
                fields={"catalog": "Service Catalog", "category": "Services"},
                rationale="Place the item in the Services category.",
            ),
            CandidateChange(
                table="m2m_connected_content",
                operation="insert",
                fields={
                    "taxonomy": "Employee",
                    "topic": "Technology services / Software / Access issues",
                },
                rationale="Associate the item to the Employee Center topic.",
            ),
        ],
        reviewer_notes=["Preview the retrieved Update Set and open the item in Employee Center."],
        artifact_hash="c" * 64,
    )


def _business_rule_candidate() -> UpdateSetCandidate:
    return UpdateSetCandidate(
        story_number="STRY0010116",
        name="UPD_STRY0010116_LLM_Implementation",
        eligibility_decision="eligible",
        eligibility_reasons=["supported table-local business rule generation request"],
        confidence=0.72,
        risk_score=0.25,
        status=CandidateStatus.READY_FOR_REVIEW,
        changes=[
            CandidateChange(
                table="sys_script",
                operation="insert",
                fields={
                    "name": "JEDI Incident Priority Note",
                    "collection": "incident",
                    "when": "before",
                    "action_insert": False,
                    "action_update": True,
                    "filter_condition": "priority changes to 1",
                    "script": (
                        "if (current.priority.changesTo('1')) {\n"
                        "    current.work_notes = 'Priority escalated by automation.';\n"
                        "}"
                    ),
                    "fields_read": ["priority"],
                    "fields_written": ["work_notes"],
                },
                rationale="Add the requested table-local Business Rule.",
            )
        ],
        reviewer_notes=["Update an Incident priority to Critical and confirm the work note."],
        artifact_hash="b" * 64,
    )


def _client_script_candidate() -> UpdateSetCandidate:
    return UpdateSetCandidate(
        story_number="STRY0010118",
        name="UPD_STRY0010118_LLM_Implementation",
        eligibility_decision="eligible",
        eligibility_reasons=["supported table-local client script generation request"],
        confidence=0.72,
        risk_score=0.25,
        status=CandidateStatus.READY_FOR_REVIEW,
        changes=[
            CandidateChange(
                table="sys_script_client",
                operation="insert",
                fields={
                    "name": "JEDI Incident Category CI Message",
                    "table": "incident",
                    "type": "onChange",
                    "field": "category",
                    "script": (
                        "function onChange(control, oldValue, newValue, isLoading) {\n"
                        "    if (isLoading || newValue !== 'software') {\n"
                        "        return;\n"
                        "    }\n"
                        "    g_form.addInfoMessage('Confirm the CI before saving.');\n"
                        "}"
                    ),
                    "fields_read": ["category"],
                    "fields_written": [],
                    "messages_shown": ["Confirm the CI before saving."],
                },
                rationale="Add the requested table-local Client Script.",
            )
        ],
        reviewer_notes=["Change Incident category to Software and confirm the message."],
        artifact_hash="c" * 64,
    )


def _script_include_candidate() -> UpdateSetCandidate:
    return UpdateSetCandidate(
        story_number="STRY0010120",
        name="UPD_STRY0010120_LLM_Implementation",
        eligibility_decision="eligible",
        eligibility_reasons=["supported utility script include generation request"],
        confidence=0.7,
        risk_score=0.3,
        status=CandidateStatus.READY_FOR_REVIEW,
        changes=[
            CandidateChange(
                table="sys_script_include",
                operation="insert",
                fields={
                    "name": "JediIncidentUtils",
                    "api_name": "global.JediIncidentUtils",
                    "scope": "global",
                    "client_callable": False,
                    "active": True,
                    "description": "Utility helpers for Incident automation.",
                    "script": (
                        "var JediIncidentUtils = Class.create();\n"
                        "JediIncidentUtils.prototype = {\n"
                        "    initialize: function() {},\n"
                        "    normalizeCategory: function(category) {\n"
                        "        return String(category || '').toLowerCase();\n"
                        "    },\n"
                        "    type: 'JediIncidentUtils'\n"
                        "};"
                    ),
                    "public_methods": ["normalizeCategory(category)"],
                    "tables_read": [],
                    "tables_written": [],
                    "fields_read": [],
                    "fields_written": [],
                },
                rationale="Add the requested server-side utility Script Include.",
            )
        ],
        reviewer_notes=["Call normalizeCategory('Software') and confirm software."],
        artifact_hash="d" * 64,
    )


def _ui_policy_candidate() -> UpdateSetCandidate:
    return UpdateSetCandidate(
        story_number="STRY0010123",
        name="UPD_STRY0010123_LLM_Implementation",
        eligibility_decision="eligible",
        eligibility_reasons=["supported declarative ui policy generation request"],
        confidence=0.74,
        risk_score=0.22,
        status=CandidateStatus.READY_FOR_REVIEW,
        changes=[
            CandidateChange(
                table="sys_ui_policy",
                operation="insert",
                fields={
                    "short_description": "JEDI Incident Assignment Group Required",
                    "table": "incident",
                    "conditions": "category=software",
                    "reverse_if_false": True,
                    "run_scripts": False,
                    "active": True,
                    "on_load": False,
                    "order": 100,
                    "description": (
                        "Make Assignment group mandatory when Incident category is Software."
                    ),
                },
                rationale="Add the requested declarative UI Policy.",
            ),
            CandidateChange(
                table="sys_ui_policy_action",
                operation="insert",
                fields={
                    "policy_name": "JEDI Incident Assignment Group Required",
                    "table": "incident",
                    "field": "assignment_group",
                    "mandatory": "true",
                    "visible": "true",
                    "disabled": "ignore",
                    "cleared": False,
                },
                rationale="Make Assignment group mandatory and visible.",
            ),
        ],
        reviewer_notes=[
            "Set Incident category to Software and confirm Assignment group is mandatory."
        ],
        artifact_hash="e" * 64,
    )


def _form_section_removal_candidate() -> UpdateSetCandidate:
    return UpdateSetCandidate(
        story_number="STRY0010011",
        name="UPD_STRY0010011_Form_Section_Removal",
        eligibility_decision="eligible",
        eligibility_reasons=["supported form section removal request"],
        confidence=0.72,
        risk_score=0.24,
        status=CandidateStatus.READY_FOR_REVIEW,
        changes=[
            CandidateChange(
                table="sys_ui_section",
                operation="delete",
                fields={
                    "table": "dmn_demand",
                    "sections": ["Assessment", "Financials"],
                    "view": "Default view",
                },
                rationale="Remove the requested Demand form sections from the default view.",
            )
        ],
        reviewer_notes=[
            "Preview the retrieved Update Set and confirm the Demand form no longer "
            "shows the Assessment and Financials tabs."
        ],
        artifact_hash="f" * 64,
    )


def test_form_section_customer_updates_rejects_non_json_section_scalar_without_leak() -> None:
    class SecretBearingObject:
        def __str__(self) -> str:
            return "client_secret=form-section-secret"

    client = FakeUpdateSetClient()

    with pytest.raises(ValueError) as exc_info:
        form_section_customer_updates(
            client=client,
            remote_update_set_sys_id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            changes=[
                CandidateChange(
                    table="sys_ui_section",
                    operation="delete",
                    fields={
                        "table": "dmn_demand",
                        "sections": ["Assessment", SecretBearingObject()],
                        "view": "Default view",
                    },
                    rationale="Remove requested Demand form sections.",
                )
            ],
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "form section removal field contains non-JSON value"
    assert client.fetches == []
    assert "SecretBearingObject" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "form-section-secret" not in diagnostic


def test_form_section_customer_updates_rejects_string_subclass_field_without_leak() -> None:
    class SecretBearingFormSectionText(str):
        def strip(self, chars: str | None = None) -> str:
            raise RuntimeError("client_secret=form-section-string-subclass")

    client = FakeUpdateSetClient()

    with pytest.raises(ValueError) as exc_info:
        form_section_customer_updates(
            client=client,
            remote_update_set_sys_id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            changes=[
                CandidateChange(
                    table="sys_ui_section",
                    operation="delete",
                    fields={
                        "table": "dmn_demand",
                        "sections": [SecretBearingFormSectionText("Assessment")],
                        "view": "Default view",
                    },
                    rationale="Remove requested Demand form sections.",
                )
            ],
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "form section removal field contains non-JSON value"
    assert client.fetches == []
    assert "SecretBearingFormSectionText" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "form-section-string-subclass" not in diagnostic


def test_form_section_customer_updates_rejects_scalar_subclass_field_without_leak() -> None:
    class SecretBearingFormSectionOrder(int):
        def __str__(self) -> str:
            raise RuntimeError("client_secret=form-section-scalar-subclass")

    client = FakeUpdateSetClient()

    with pytest.raises(ValueError) as exc_info:
        form_section_customer_updates(
            client=client,
            remote_update_set_sys_id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            changes=[
                CandidateChange(
                    table="sys_ui_section",
                    operation="delete",
                    fields={
                        "table": "dmn_demand",
                        "sections": [SecretBearingFormSectionOrder(1)],
                        "view": "Default view",
                    },
                    rationale="Remove requested Demand form sections.",
                )
            ],
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "form section removal field contains non-JSON value"
    assert client.fetches == []
    assert "SecretBearingFormSectionOrder" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "form-section-scalar-subclass" not in diagnostic


def test_form_section_customer_updates_rejects_list_subclass_field_without_leak() -> None:
    class SecretBearingFormSectionList(list[str]):
        def __iter__(self) -> Any:
            raise RuntimeError("client_secret=form-section-list-subclass")

    client = FakeUpdateSetClient()

    with pytest.raises(ValueError) as exc_info:
        form_section_customer_updates(
            client=client,
            remote_update_set_sys_id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            changes=[
                CandidateChange(
                    table="sys_ui_section",
                    operation="delete",
                    fields={
                        "table": "dmn_demand",
                        "sections": SecretBearingFormSectionList(["Assessment"]),
                        "view": "Default view",
                    },
                    rationale="Remove requested Demand form sections.",
                )
            ],
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "form section removal field contains non-JSON value"
    assert exc_info.value.__cause__ is None
    assert client.fetches == []
    assert "SecretBearingFormSectionList" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "form-section-list-subclass" not in diagnostic


def test_form_section_customer_updates_rejects_dict_subclass_metadata_without_leak() -> None:
    class SecretBearingFormSectionReference(dict[str, str]):
        def get(self, key: str, default: Any = None) -> Any:
            raise RuntimeError("client_secret=form-section-reference-subclass")

    class HostileSectionClient(FakeUpdateSetClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            records = super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )
            if table == "sys_ui_section" and lookup == {"name": "dmn_demand"}:
                return [
                    {
                        **records[1],
                        "caption": SecretBearingFormSectionReference(
                            {
                                "display_value": "Assessment Data",
                                "value": "Assessment Data",
                            }
                        ),
                    }
                ]
            return records

    with pytest.raises(ValueError) as exc_info:
        form_section_customer_updates(
            client=HostileSectionClient(),
            remote_update_set_sys_id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            changes=[
                CandidateChange(
                    table="sys_ui_section",
                    operation="delete",
                    fields={
                        "table": "dmn_demand",
                        "sections": ["Assessment Data"],
                        "view": "Default view",
                    },
                    rationale="Remove requested Demand form sections.",
                )
            ],
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "form section removal field contains non-JSON value"
    assert exc_info.value.__cause__ is None
    assert "SecretBearingFormSectionReference" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "form-section-reference-subclass" not in diagnostic


def test_form_section_customer_updates_rejects_missing_section_sys_id() -> None:
    class MissingSectionSysIdClient(FakeUpdateSetClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            if table == "sys_ui_section" and lookup == {"name": "dmn_demand"}:
                return [
                    {
                        "name": "dmn_demand",
                        "caption": "Assessment Data",
                        "view": {
                            "display_value": "Default view",
                            "value": "Default view",
                        },
                        "sys_user": "",
                    }
                ]
            return super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )

    with pytest.raises(ValueError) as exc_info:
        form_section_customer_updates(
            client=MissingSectionSysIdClient(),
            remote_update_set_sys_id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            changes=[
                CandidateChange(
                    table="sys_ui_section",
                    operation="delete",
                    fields={
                        "table": "dmn_demand",
                        "sections": ["Assessment Data"],
                        "view": "Default view",
                    },
                    rationale="Remove requested Demand form sections.",
                )
            ],
        )

    assert str(exc_info.value) == "form section removal field is missing"


def test_create_update_set_handoff_imports_retrieved_update_set_and_links_story() -> None:
    client = FakeUpdateSetClient()

    result = create_update_set_handoff(
        client=client,
        request=UpdateSetHandoffRequest(
            story_sys_id="story-sys-id",
            story_number="STRY0010013",
            candidate=_candidate(),
            candidate_artifact_ref="db://artifact_blobs/2",
            instance_url="https://dev205693.service-now.com",
        ),
    )

    assert result.update_set_sys_id == "remote-update-set-sys-id"
    assert result.update_set_name == "JEDI STRY0010013 - AI Candidate"
    assert result.update_set_url == (
        "https://dev205693.service-now.com/sys_remote_update_set.do?sys_id=remote-update-set-sys-id"
    )
    assert client.upserts == []
    assert len(client.imports) == 1
    imported_xml = client.imports[0]["update_set_xml"]
    assert "<name>JEDI STRY0010013 - AI Candidate</name>" in imported_xml
    assert "<remote_sys_id>aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa</remote_sys_id>" in imported_xml
    assert "sys_dictionary_rm_story_u_ai_review_notes" in imported_xml
    assert "sys_documentation_rm_story_u_ai_review_notes_en" in imported_xml
    assert client.story_updates == [
        {
            "story_sys_id": "story-sys-id",
            "fields": {
                "state": "-7",
                "u_ai_status": "Ready for Testing",
                "u_ai_handoff_type": "retrieved_update_set",
                "u_ai_handoff_reference": "remote-update-set-sys-id",
                "u_ai_artifact_reference": "db://artifact_blobs/2",
                "work_notes": (
                    "ServiceNow retrieved Update Set handoff created for STRY0010013. "
                    "Retrieved Update Set: JEDI STRY0010013 - AI Candidate\n"
                    "Retrieved Update Set link: https://dev205693.service-now.com/"
                    "sys_remote_update_set.do?sys_id=remote-update-set-sys-id\n"
                    "Candidate artifact: db://artifact_blobs/2."
                ),
            },
        }
    ]


def test_create_update_set_handoff_imports_xml_instead_of_table_writing_updates() -> None:
    client = FakeUpdateSetClient()

    result = create_update_set_handoff(
        client=client,
        request=UpdateSetHandoffRequest(
            story_sys_id="story-sys-id",
            story_number="STRY0010013",
            candidate=_candidate(),
            candidate_artifact_ref="db://artifact_blobs/2",
            instance_url="https://dev205693.service-now.com",
        ),
    )

    assert result.update_set_sys_id == "remote-update-set-sys-id"
    assert client.upserts == []
    assert client.imports[0]["service_id"] == "jedi_update_set_import"
    assert "<unload" in client.imports[0]["update_set_xml"]
    assert (
        '<sys_remote_update_set action="INSERT_OR_UPDATE">' in client.imports[0]["update_set_xml"]
    )
    assert "<name>JEDI STRY0010013 - AI Candidate</name>" in client.imports[0]["update_set_xml"]
    assert '<sys_update_xml action="INSERT_OR_UPDATE">' in client.imports[0]["update_set_xml"]
    assert (
        '<remote_update_set display_value="JEDI STRY0010013 - AI Candidate">'
        in (client.imports[0]["update_set_xml"])
    )
    assert any(fetch["table"] == "sys_remote_update_set" for fetch in client.fetches)
    assert client.story_updates[-1]["fields"]["work_notes"].startswith(
        "ServiceNow retrieved Update Set handoff created for STRY0010013."
    )
    assert client.story_updates[-1]["fields"]["state"] == "-7"
    assert client.story_updates[-1]["fields"]["u_ai_status"] == "Ready for Testing"


def test_create_update_set_handoff_rejects_story_number_object_without_leak() -> None:
    class SecretBearingStoryNumber:
        def __str__(self) -> str:
            raise RuntimeError("client_secret=handoff-story-number-secret")

    client = FakeUpdateSetClient()

    with pytest.raises(ValueError) as exc_info:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest.model_construct(
                story_sys_id="story-sys-id",
                story_number=SecretBearingStoryNumber(),
                candidate=_candidate(),
                candidate_artifact_ref="db://artifact_blobs/43",
                instance_url="https://dev205693.service-now.com",
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "retrieved Update Set handoff story number contains non-JSON value"
    assert client.imports == []
    assert client.story_updates == []
    assert "SecretBearingStoryNumber" not in diagnostic
    assert "handoff-story-number-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_create_update_set_handoff_rejects_instance_url_object_without_leak() -> None:
    class SecretBearingInstanceUrl:
        def rstrip(self, chars: str | None = None) -> str:
            raise RuntimeError("client_secret=handoff-instance-url-secret")

        def __str__(self) -> str:
            raise RuntimeError("client_secret=handoff-instance-url-string-secret")

    client = FakeUpdateSetClient()

    with pytest.raises(ValueError) as exc_info:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest.model_construct(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=_candidate(),
                candidate_artifact_ref="db://artifact_blobs/44",
                instance_url=SecretBearingInstanceUrl(),
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "retrieved Update Set handoff instance URL contains non-JSON value"
    assert len(client.imports) == 1
    assert client.story_updates == []
    assert "SecretBearingInstanceUrl" not in diagnostic
    assert "handoff-instance-url-secret" not in diagnostic
    assert "handoff-instance-url-string-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_create_update_set_handoff_rejects_story_sys_id_object_without_leak() -> None:
    class SecretBearingStorySysId:
        def __str__(self) -> str:
            raise RuntimeError("client_secret=handoff-story-sys-id-secret")

    client = FakeUpdateSetClient()

    with pytest.raises(ValueError) as exc_info:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest.model_construct(
                story_sys_id=SecretBearingStorySysId(),
                story_number="STRY0010013",
                candidate=_candidate(),
                candidate_artifact_ref="db://artifact_blobs/45",
                instance_url="https://dev205693.service-now.com",
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "retrieved Update Set handoff story sys_id contains non-JSON value"
    assert client.imports == []
    assert client.story_updates == []
    assert "SecretBearingStorySysId" not in diagnostic
    assert "handoff-story-sys-id-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_create_update_set_handoff_rejects_artifact_ref_object_without_leak() -> None:
    class SecretBearingArtifactRef:
        def __str__(self) -> str:
            raise RuntimeError("client_secret=handoff-artifact-ref-secret")

    client = FakeUpdateSetClient()

    with pytest.raises(ValueError) as exc_info:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest.model_construct(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=_candidate(),
                candidate_artifact_ref=SecretBearingArtifactRef(),
                instance_url="https://dev205693.service-now.com",
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "retrieved Update Set handoff artifact reference contains non-JSON value"
    assert client.imports == []
    assert client.story_updates == []
    assert "SecretBearingArtifactRef" not in diagnostic
    assert "handoff-artifact-ref-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_import_retrieved_update_set_rejects_non_json_customer_update_scalar_without_leak() -> None:
    class SecretBearingObject:
        def __str__(self) -> str:
            return "client_secret=handoff-secret"

    client = FakeUpdateSetClient()

    with pytest.raises(ValueError) as exc_info:
        import_retrieved_update_set(
            client=client,
            update_set_name="JEDI STRY0010013 - AI Candidate",
            remote_sys_id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            description="Generated retrieved update set.",
            customer_updates=[
                {
                    "action": "INSERT_OR_UPDATE",
                    "name": SecretBearingObject(),
                    "payload": "<record_update/>",
                    "target_name": "AI Review Notes",
                    "type": "Dictionary",
                }
            ],
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "retrieved Update Set customer update contains non-JSON value"
    assert client.imports == []
    assert "SecretBearingObject" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "handoff-secret" not in diagnostic


def test_import_retrieved_update_set_rejects_string_subclass_customer_update_without_leak() -> None:
    class SecretBearingPayloadText(str):
        def replace(self, old: str, new: str, count: SupportsIndex = -1) -> str:
            raise RuntimeError("client_secret=customer-update-string-subclass")

    client = FakeUpdateSetClient()

    with pytest.raises(ValueError) as exc_info:
        import_retrieved_update_set(
            client=client,
            update_set_name="JEDI STRY0010013 - AI Candidate",
            remote_sys_id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            description="Generated retrieved update set.",
            customer_updates=[
                {
                    "action": "INSERT_OR_UPDATE",
                    "name": "sys_dictionary_rm_story_u_ai_review_notes",
                    "payload": SecretBearingPayloadText("<record_update/>"),
                    "target_name": "AI Review Notes",
                    "type": "Dictionary",
                }
            ],
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == CUSTOMER_UPDATE_NON_JSON_DIAGNOSTIC
    assert client.imports == []
    assert "SecretBearingPayloadText" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "customer-update-string-subclass" not in diagnostic


def test_import_retrieved_update_set_rejects_customer_update_collection_subclass() -> None:
    class SecretBearingCustomerUpdates(list[dict[str, Any]]):
        def __iter__(self) -> Any:
            raise RuntimeError("client_secret=customer-updates-iter-secret")

    client = FakeUpdateSetClient()

    with pytest.raises(ValueError) as exc_info:
        import_retrieved_update_set(
            client=client,
            update_set_name="JEDI STRY0010013 - AI Candidate",
            remote_sys_id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            description="Generated retrieved update set.",
            customer_updates=SecretBearingCustomerUpdates(
                [
                    {
                        "action": "INSERT_OR_UPDATE",
                        "name": "sys_dictionary_rm_story_u_ai_review_notes",
                        "payload": "<record_update/>",
                        "target_name": "AI Review Notes",
                        "type": "Dictionary",
                    }
                ]
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == CUSTOMER_UPDATE_NON_JSON_DIAGNOSTIC
    assert client.imports == []
    assert "SecretBearingCustomerUpdates" not in diagnostic
    assert "customer-updates-iter-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_create_update_set_handoff_rejects_generated_customer_update_collection_subclass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class SecretBearingGeneratedUpdates(list[dict[str, Any]]):
        def __bool__(self) -> bool:
            raise RuntimeError("client_secret=generated-customer-updates-bool")

        def __iter__(self) -> Any:
            raise RuntimeError("client_secret=generated-customer-updates-iter")

    def generated_customer_updates(**_: object) -> list[dict[str, Any]]:
        return SecretBearingGeneratedUpdates(
            [
                {
                    "action": "INSERT_OR_UPDATE",
                    "name": "sys_dictionary_rm_story_u_ai_review_notes",
                    "payload": "<record_update/>",
                    "target_name": "AI Review Notes",
                    "type": "Dictionary",
                }
            ]
        )

    monkeypatch.setattr(
        update_set_handoff_module,
        "dictionary_form_customer_updates",
        generated_customer_updates,
    )
    client = FakeUpdateSetClient()

    with pytest.raises(ValueError) as exc_info:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=_candidate(),
                candidate_artifact_ref="db://artifact_blobs/40",
                instance_url="https://dev205693.service-now.com",
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == CUSTOMER_UPDATE_NON_JSON_DIAGNOSTIC
    assert client.imports == []
    assert client.story_updates == []
    assert "SecretBearingGeneratedUpdates" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "generated-customer-updates-bool" not in diagnostic
    assert "generated-customer-updates-iter" not in diagnostic


def test_import_retrieved_update_set_rejects_metadata_string_subclass_without_leak() -> None:
    class SecretBearingUpdateSetName(str):
        def replace(self, old: str, new: str, count: SupportsIndex = -1) -> str:
            raise RuntimeError("client_secret=update-set-metadata-secret")

    client = FakeUpdateSetClient()

    with pytest.raises(ValueError) as exc_info:
        import_retrieved_update_set(
            client=client,
            update_set_name=SecretBearingUpdateSetName("JEDI STRY0010013 - AI Candidate"),
            remote_sys_id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            description="Generated retrieved update set.",
            customer_updates=[
                {
                    "action": "INSERT_OR_UPDATE",
                    "name": "sys_dictionary_rm_story_u_ai_review_notes",
                    "payload": "<record_update/>",
                    "target_name": "AI Review Notes",
                    "type": "Dictionary",
                }
            ],
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "retrieved Update Set metadata contains non-JSON value"
    assert client.imports == []
    assert "SecretBearingUpdateSetName" not in diagnostic
    assert "update-set-metadata-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_import_retrieved_update_set_rejects_non_json_lookup_sys_id_without_leak() -> None:
    class SecretBearingSysId:
        def __str__(self) -> str:
            return "client_secret=lookup-secret"

    class CorruptLookupClient(FakeUpdateSetClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            if table == "sys_remote_update_set":
                return [{"sys_id": SecretBearingSysId()}]
            return super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )

    client = CorruptLookupClient()

    with pytest.raises(ValueError) as exc_info:
        import_retrieved_update_set(
            client=client,
            update_set_name="JEDI STRY0010013 - AI Candidate",
            remote_sys_id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            description="Generated retrieved update set.",
            customer_updates=[
                {
                    "action": "INSERT_OR_UPDATE",
                    "name": "sys_dictionary_rm_story_u_ai_review_notes",
                    "payload": "<record_update/>",
                    "target_name": "AI Review Notes",
                    "type": "Dictionary",
                }
            ],
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == IMPORTED_UPDATE_SET_LOOKUP_NON_JSON_DIAGNOSTIC
    assert len(client.imports) == 1
    assert "SecretBearingSysId" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "lookup-secret" not in diagnostic


def test_import_retrieved_update_set_rejects_lookup_collection_subclass_without_leak() -> None:
    class SecretBearingLookupRecords(list[dict[str, Any]]):
        def __bool__(self) -> bool:
            raise RuntimeError("client_secret=lookup-records-bool-secret")

    class CorruptLookupClient(FakeUpdateSetClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            if table == "sys_remote_update_set":
                return SecretBearingLookupRecords([{"sys_id": "remote-update-set-sys-id"}])
            return super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )

    client = CorruptLookupClient()

    with pytest.raises(ValueError) as exc_info:
        import_retrieved_update_set(
            client=client,
            update_set_name="JEDI STRY0010013 - AI Candidate",
            remote_sys_id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            description="Generated retrieved update set.",
            customer_updates=[
                {
                    "action": "INSERT_OR_UPDATE",
                    "name": "sys_dictionary_rm_story_u_ai_review_notes",
                    "payload": "<record_update/>",
                    "target_name": "AI Review Notes",
                    "type": "Dictionary",
                }
            ],
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == IMPORTED_UPDATE_SET_LOOKUP_NON_JSON_DIAGNOSTIC
    assert len(client.imports) == 1
    assert "SecretBearingLookupRecords" not in diagnostic
    assert "lookup-records-bool-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_create_update_set_handoff_sanitizes_work_note_artifact_reference() -> None:
    client = FakeUpdateSetClient()
    artifact_ref = "db://artifact_blobs/2\nclient_secret=artifact-secret"

    create_update_set_handoff(
        client=client,
        request=UpdateSetHandoffRequest(
            story_sys_id="story-sys-id",
            story_number="STRY0010013",
            candidate=_candidate(),
            candidate_artifact_ref=artifact_ref,
            instance_url="https://dev205693.service-now.com",
        ),
    )

    fields = client.story_updates[-1]["fields"]
    work_notes = str(fields["work_notes"])
    assert fields["u_ai_artifact_reference"] == artifact_ref
    assert "artifact-secret" not in work_notes
    assert "client_secret=***REDACTED***" in work_notes
    assert "Candidate artifact: db://artifact_blobs/2 client_secret=" in work_notes


def test_create_update_set_handoff_bounds_work_note_artifact_reference() -> None:
    client = FakeUpdateSetClient()
    artifact_ref = f"db://artifact_blobs/2 {'A' * 2200}"

    create_update_set_handoff(
        client=client,
        request=UpdateSetHandoffRequest(
            story_sys_id="story-sys-id",
            story_number="STRY0010013",
            candidate=_candidate(),
            candidate_artifact_ref=artifact_ref,
            instance_url="https://dev205693.service-now.com",
        ),
    )

    fields = client.story_updates[-1]["fields"]
    work_notes = str(fields["work_notes"])
    assert fields["u_ai_artifact_reference"] == artifact_ref
    assert "...[truncated]" in work_notes
    assert len(work_notes) < 900


def test_create_update_set_handoff_imports_retrieved_form_layout_updates() -> None:
    client = FakeUpdateSetClient()

    create_update_set_handoff(
        client=client,
        request=UpdateSetHandoffRequest(
            story_sys_id="story-sys-id",
            story_number="STRY0010013",
            candidate=_dictionary_form_candidate(),
            candidate_artifact_ref="db://artifact_blobs/2",
            instance_url="https://dev205693.service-now.com",
        ),
    )

    form_updates = [
        marker
        for marker in [
            "sys_ui_section_default-main-section-sys-id",
            "sys_ui_section_scrum-main-section-sys-id",
        ]
        if marker in client.imports[0]["update_set_xml"]
    ]
    assert form_updates == [
        "sys_ui_section_default-main-section-sys-id",
        "sys_ui_section_scrum-main-section-sys-id",
    ]
    assert "notes-section-sys-id" not in client.imports[0]["update_set_xml"]
    assert "<element>u_ai_review_notes</element><position>5</position>" in str(
        client.imports[0]["update_set_xml"]
    )
    assert "<element>u_ai_review_notes</element><position>20</position>" in str(
        client.imports[0]["update_set_xml"]
    )


def test_create_update_set_handoff_normalizes_model_aliases_for_retrieved_updates() -> None:
    client = FakeUpdateSetClient()

    create_update_set_handoff(
        client=client,
        request=UpdateSetHandoffRequest(
            story_sys_id="story-sys-id",
            story_number="STRY0010013",
            candidate=_aliased_dictionary_form_candidate(),
            candidate_artifact_ref="db://artifact_blobs/2",
            instance_url="https://dev205693.service-now.com",
        ),
    )

    imported_xml = client.imports[0]["update_set_xml"]
    assert "sys_dictionary_rm_story_u_ai_review_notes" in imported_xml
    assert "Story.AI Review Notes" in imported_xml
    assert "<max_length>8000</max_length>" in imported_xml
    assert "<mandatory>false</mandatory>" in imported_xml
    assert "sys_ui_section_default-main-section-sys-id" in imported_xml


def test_create_update_set_handoff_normalizes_minimal_model_shape() -> None:
    client = FakeUpdateSetClient()

    create_update_set_handoff(
        client=client,
        request=UpdateSetHandoffRequest(
            story_sys_id="story-sys-id",
            story_number="STRY0010013",
            candidate=_minimal_model_dictionary_form_candidate(),
            candidate_artifact_ref="db://artifact_blobs/30",
            instance_url="https://dev205693.service-now.com",
        ),
    )

    imported_xml = client.imports[0]["update_set_xml"]
    assert "sys_dictionary_rm_story_u_ai_review_notes" in imported_xml
    assert "Story.AI Review Notes" in imported_xml
    assert "<name>rm_story</name>" in imported_xml
    assert "<element>u_ai_review_notes</element>" in imported_xml
    assert '<internal_type display_value="String">string</internal_type>' in imported_xml
    assert "sys_ui_section_default-main-section-sys-id" in imported_xml


def test_form_section_customer_updates_respects_non_default_view() -> None:
    client = FakeUpdateSetClient()

    updates = form_section_customer_updates(
        client=client,
        changes=[
            CandidateChange(
                table="sys_ui_section",
                operation="delete",
                fields={"table": "rm_story", "sections": "Notes", "view": "Scrum"},
                rationale="Remove the Notes section from the Scrum view.",
            )
        ],
        remote_update_set_sys_id="remote-sys-id",
    )

    assert len(updates) == 1
    assert updates[0]["name"] == "sys_ui_section_notes-section-sys-id"
    assert updates[0]["target_name"] == "Rm Story.Notes"
    assert '<view display_value="Scrum" name="NULL">scrum-view-sys-id</view>' in str(
        updates[0]["payload"]
    )


def test_form_section_customer_updates_fail_closed_for_invalid_requests() -> None:
    client = FakeUpdateSetClient()
    invalid_change_cases = [
        ([], "form section removal requires exactly one candidate change"),
        (
            [
                CandidateChange(
                    table="sys_ui_section",
                    operation="update",
                    fields={"table": "dmn_demand", "sections": ["Assessment"]},
                    rationale="Wrong operation.",
                )
            ],
            "form section removal requires one sys_ui_section delete change",
        ),
        (
            [
                CandidateChange(
                    table="sys_ui_section",
                    operation="delete",
                    fields={"sections": ["Assessment"]},
                    rationale="Missing table.",
                )
            ],
            "form section removal missing required field: table",
        ),
        (
            [
                CandidateChange(
                    table="sys_ui_section",
                    operation="delete",
                    fields={"table": "dmn_demand", "sections": []},
                    rationale="Missing section.",
                )
            ],
            "form section removal requires at least one section",
        ),
        (
            [
                CandidateChange(
                    table="sys_ui_section",
                    operation="delete",
                    fields={"table": "dmn_demand", "sections": ["Unknown"]},
                    rationale="Unknown section.",
                )
            ],
            "form section not found: Unknown",
        ),
    ]

    for changes, expected_message in invalid_change_cases:
        try:
            form_section_customer_updates(
                client=client,
                changes=changes,
                remote_update_set_sys_id="remote-sys-id",
            )
        except ValueError as exc:
            assert expected_message in str(exc)
        else:
            raise AssertionError(f"invalid form section request was accepted: {changes}")


def test_form_section_customer_updates_rejects_ambiguous_section_match() -> None:
    class AmbiguousSectionClient(FakeUpdateSetClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            if table == "sys_ui_section" and lookup == {"name": "dmn_demand"}:
                return [
                    {
                        "sys_id": "assessment-a",
                        "name": "dmn_demand",
                        "caption": "Assessment Data",
                        "view": {"display_value": "Default view", "value": "Default view"},
                    },
                    {
                        "sys_id": "assessment-b",
                        "name": "dmn_demand",
                        "caption": "Assessment Data",
                        "view": {"display_value": "Default view", "value": "Default view"},
                    },
                ]
            return super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )

    try:
        form_section_customer_updates(
            client=AmbiguousSectionClient(),
            changes=[
                CandidateChange(
                    table="sys_ui_section",
                    operation="delete",
                    fields={"table": "dmn_demand", "sections": ["Assessment Data"]},
                    rationale="Ambiguous section.",
                )
            ],
            remote_update_set_sys_id="remote-sys-id",
        )
    except ValueError as exc:
        assert "form section match is ambiguous: Assessment Data" in str(exc)
    else:
        raise AssertionError("ambiguous form section request was accepted")


def test_form_section_customer_updates_rejects_metadata_collection_subclass_without_leak() -> (
    None
):
    class SecretBearingSectionRecords(list[dict[str, Any]]):
        def __iter__(self) -> Any:
            raise RuntimeError("client_secret=form-section-record-collection")

    class CorruptSectionClient(FakeUpdateSetClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            records = super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )
            if table == "sys_ui_section" and lookup == {"name": "rm_story"}:
                return SecretBearingSectionRecords(records)
            return records

    with pytest.raises(ValueError) as exc_info:
        form_section_customer_updates(
            client=CorruptSectionClient(),
            changes=[
                CandidateChange(
                    table="sys_ui_section",
                    operation="delete",
                    fields={"table": "rm_story", "sections": "Notes", "view": "Scrum"},
                    rationale="Remove the Notes section from the Scrum view.",
                )
            ],
            remote_update_set_sys_id="remote-sys-id",
        )

    message = str(exc_info.value)
    assert message == FORM_SECTION_FIELD_NON_JSON_DIAGNOSTIC
    assert "form-section-record-collection" not in message
    assert "SecretBearingSectionRecords" not in message
    assert "client_secret" not in message


def test_form_section_customer_updates_rejects_metadata_record_subclass_without_leak() -> None:
    class SecretBearingSectionRecord(dict[str, Any]):
        def get(self, key: str, default: Any = None) -> Any:
            raise RuntimeError("client_secret=form-section-record")

    class CorruptSectionClient(FakeUpdateSetClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            records = super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )
            if table == "sys_ui_section" and lookup == {"name": "rm_story"}:
                return [SecretBearingSectionRecord(records[0])]
            return records

    with pytest.raises(ValueError) as exc_info:
        form_section_customer_updates(
            client=CorruptSectionClient(),
            changes=[
                CandidateChange(
                    table="sys_ui_section",
                    operation="delete",
                    fields={"table": "rm_story", "sections": "Notes", "view": "Scrum"},
                    rationale="Remove the Notes section from the Scrum view.",
                )
            ],
            remote_update_set_sys_id="remote-sys-id",
        )

    message = str(exc_info.value)
    assert message == FORM_SECTION_FIELD_NON_JSON_DIAGNOSTIC
    assert "form-section-record" not in message
    assert "SecretBearingSectionRecord" not in message
    assert "client_secret" not in message


def test_create_update_set_handoff_accepts_table_aliases_and_position_hints() -> None:
    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={
            "changes": [
                CandidateChange(
                    table="sys_dictionary",
                    operation="insert",
                    fields={
                        "table": "rm_story",
                        "field_name": "u_alias_field",
                        "field_label": "Alias Field",
                        "type": "string",
                        "mandatory": "true",
                    },
                    rationale="Create the alias field.",
                ),
                CandidateChange(
                    table="sys_ui_form",
                    operation="update",
                    fields={
                        "table_name": "rm_story",
                        "field": "u_alias_field",
                        "position_hint": "above Description",
                    },
                    rationale="Place the alias field above Description.",
                ),
            ]
        }
    )

    create_update_set_handoff(
        client=client,
        request=UpdateSetHandoffRequest(
            story_sys_id="story-sys-id",
            story_number="STRY0010013",
            candidate=candidate,
            candidate_artifact_ref="db://artifact_blobs/31",
            instance_url="https://dev205693.service-now.com",
        ),
    )

    imported_xml = client.imports[0]["update_set_xml"]
    assert "sys_dictionary_rm_story_u_alias_field" in imported_xml
    assert "<mandatory>true</mandatory>" in imported_xml
    assert "<element>u_alias_field</element><position>4</position>" in imported_xml


def test_create_update_set_handoff_preserves_reference_field_metadata() -> None:
    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={
            "changes": [
                CandidateChange(
                    table="sys_dictionary",
                    operation="insert",
                    fields={
                        "name": "Problem",
                        "element": "u_vendor_reference",
                        "column_label": "Vendor Reference",
                        "internal_type": "reference",
                        "reference": "core_company",
                        "reference_qual": "vendor=true",
                        "reference_qual_condition": "vendor=true",
                        "use_reference_qualifier": "simple",
                    },
                    rationale="Create the vendor reference field.",
                ),
                CandidateChange(
                    table="sys_ui_form",
                    operation="update",
                    fields={
                        "name": "Problem",
                        "field": "u_vendor_reference",
                        "position_hint": "below Description",
                    },
                    rationale="Place the field below Description.",
                ),
            ]
        }
    )

    create_update_set_handoff(
        client=client,
        request=UpdateSetHandoffRequest(
            story_sys_id="story-sys-id",
            story_number="STRY0010002",
            candidate=candidate,
            candidate_artifact_ref="db://artifact_blobs/44",
            instance_url="https://dev205693.service-now.com",
        ),
    )

    imported_xml = client.imports[0]["update_set_xml"]
    assert "sys_dictionary_problem_u_vendor_reference" in imported_xml
    assert "<reference>core_company</reference>" in imported_xml
    assert "<use_reference_qualifier>simple</use_reference_qualifier>" in imported_xml
    assert "<reference_qual>vendor=true</reference_qual>" in imported_xml
    assert "<reference_qual_condition>vendor=true</reference_qual_condition>" in imported_xml


def test_create_update_set_handoff_rejects_reference_dict_subclass_without_leak() -> None:
    class SecretBearingReference(dict[str, str]):
        def get(self, key: str, default: Any = None) -> Any:
            raise RuntimeError("client_secret=handoff-reference-dict-subclass")

    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={
            "changes": [
                CandidateChange(
                    table="sys_dictionary",
                    operation="insert",
                    fields={
                        "name": "Problem",
                        "element": "u_vendor_reference",
                        "column_label": "Vendor Reference",
                        "internal_type": "reference",
                        "reference": SecretBearingReference(
                            {"value": "core_company", "display_value": "Company"}
                        ),
                    },
                    rationale="Create the vendor reference field.",
                ),
                CandidateChange(
                    table="sys_ui_form",
                    operation="update",
                    fields={
                        "name": "Problem",
                        "field": "u_vendor_reference",
                        "position_hint": "below Description",
                    },
                    rationale="Place the field below Description.",
                ),
            ]
        }
    )

    with pytest.raises(ValueError) as exc_info:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010002",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/45",
                instance_url="https://dev205693.service-now.com",
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "dictionary/form handoff field contains non-JSON value"
    assert client.imports == []
    assert client.story_updates == []
    assert "SecretBearingReference" not in diagnostic
    assert "handoff-reference-dict-subclass" not in diagnostic
    assert "client_secret" not in diagnostic


def test_create_update_set_handoff_blocks_non_dictionary_candidates_until_builder_matures() -> None:
    client = FakeUpdateSetClient()

    for candidate in [
        _business_rule_candidate(),
        _catalog_item_candidate(),
        _form_section_removal_candidate(),
        _client_script_candidate(),
        _script_include_candidate(),
    ]:
        try:
            create_update_set_handoff(
                client=client,
                request=UpdateSetHandoffRequest(
                    story_sys_id="story-sys-id",
                    story_number=candidate.story_number,
                    candidate=candidate,
                    candidate_artifact_ref="db://artifact_blobs/900",
                    instance_url="https://dev205693.service-now.com",
                ),
            )
        except ValueError as exc:
            assert "no mature deterministic retrieved Update Set builder" in str(exc)
        else:
            raise AssertionError(f"non-dictionary candidate was handed off: {candidate.name}")

    assert client.imports == []
    assert client.story_updates == []


def test_create_update_set_handoff_imports_ui_policy_customer_updates() -> None:
    client = FakeUpdateSetClient()

    result = create_update_set_handoff(
        client=client,
        request=UpdateSetHandoffRequest(
            story_sys_id="story-sys-id",
            story_number="STRY0010123",
            candidate=_ui_policy_candidate(),
            candidate_artifact_ref="db://artifact_blobs/901",
            instance_url="https://dev205693.service-now.com",
        ),
    )

    assert result.update_set_sys_id == "remote-update-set-sys-id"
    assert len(client.imports) == 1
    imported_xml = client.imports[0]["update_set_xml"]
    assert "sys_ui_policy_incident_jedi_incident_assignment_group_required" in imported_xml
    assert "sys_ui_policy_action_incident_assignment_group_required_visible" in imported_xml
    assert "<sys_ui_policy action=\"INSERT_OR_UPDATE\">" in imported_xml
    assert "<sys_ui_policy_action action=\"INSERT_OR_UPDATE\">" in imported_xml
    assert "<conditions>category=software</conditions>" in imported_xml
    assert "<field>assignment_group</field>" in imported_xml
    assert "<mandatory>true</mandatory>" in imported_xml
    assert "<visible>true</visible>" in imported_xml
    assert client.story_updates[0]["fields"]["u_ai_status"] == "Ready for Testing"


def test_create_update_set_handoff_rejects_empty_candidate_changes_before_table_routing() -> None:
    client = FakeUpdateSetClient()
    candidate = _script_include_candidate().model_copy(update={"changes": []})

    try:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010120",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/120",
                instance_url="https://dev205693.service-now.com",
            ),
        )
    except ValueError as exc:
        assert "at least one candidate change" in str(exc)
    else:
        raise AssertionError("empty candidate changes reached table-specific handoff")


def test_create_update_set_handoff_rejects_unsupported_candidate_tables() -> None:
    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={
            "changes": [
                *_candidate().changes,
                CandidateChange(
                    table="sys_script_include",
                    operation="insert",
                    fields={"name": "BadIdea"},
                    rationale="Unsupported script change.",
                ),
            ]
        }
    )

    try:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/32",
                instance_url="https://dev205693.service-now.com",
            ),
        )
    except ValueError as exc:
        assert "no mature deterministic retrieved Update Set builder" in str(exc)
    else:
        raise AssertionError("unsupported candidate table was accepted")

    assert client.imports == []


def test_create_update_set_handoff_rejects_non_reviewable_candidate() -> None:
    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(update={"status": CandidateStatus.REJECTED})

    try:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/2",
                instance_url="https://dev205693.service-now.com",
            ),
        )
    except ValueError as exc:
        assert "candidate is not ready for Update Set handoff" in str(exc)
    else:
        raise AssertionError("rejected candidate was handed off")

    assert client.upserts == []
    assert client.story_updates == []


def test_create_update_set_handoff_requires_dictionary_and_form_changes() -> None:
    client = FakeUpdateSetClient()
    dictionary_only = _candidate().model_copy(update={"changes": [_candidate().changes[0]]})
    form_only = _candidate().model_copy(update={"changes": [_candidate().changes[1]]})

    for candidate, expected_message in [
        (dictionary_only, "dictionary/form handoff requires a sys_ui_form change"),
        (form_only, "dictionary/form handoff requires a sys_dictionary change"),
    ]:
        try:
            create_update_set_handoff(
                client=client,
                request=UpdateSetHandoffRequest(
                    story_sys_id="story-sys-id",
                    story_number="STRY0010013",
                    candidate=candidate,
                    candidate_artifact_ref="db://artifact_blobs/2",
                    instance_url="https://dev205693.service-now.com",
                ),
            )
        except ValueError as exc:
            assert expected_message in str(exc)
        else:
            raise AssertionError("incomplete dictionary/form candidate was handed off")

    assert client.imports == []
    assert client.story_updates == []


def test_create_update_set_handoff_rejects_missing_dictionary_required_fields() -> None:
    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={
            "changes": [
                CandidateChange(
                    table="sys_dictionary",
                    operation="insert",
                    fields={"name": "rm_story", "element": "u_missing_label"},
                    rationale="Missing label.",
                ),
                _candidate().changes[1],
            ]
        }
    )

    try:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/33",
                instance_url="https://dev205693.service-now.com",
            ),
        )
    except ValueError as exc:
        assert "sys_dictionary change missing required retrieved update fields" in str(exc)
    else:
        raise AssertionError("dictionary change with missing required fields was accepted")

    assert client.imports == []


def test_create_update_set_handoff_rejects_non_json_dictionary_form_field_without_leak() -> None:
    class SecretBearingObject:
        def __str__(self) -> str:
            return "client_secret=dictionary-form-secret"

    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={
            "changes": [
                CandidateChange(
                    table="sys_dictionary",
                    operation="insert",
                    fields={
                        "name": "rm_story",
                        "element": "u_ai_review_notes",
                        "column_label": SecretBearingObject(),
                    },
                    rationale="Malformed label.",
                ),
                _candidate().changes[1],
            ]
        }
    )

    with pytest.raises(ValueError) as exc_info:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/34",
                instance_url="https://dev205693.service-now.com",
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "dictionary/form handoff field contains non-JSON value"
    assert client.imports == []
    assert client.story_updates == []
    assert "SecretBearingObject" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "dictionary-form-secret" not in diagnostic


def test_create_update_set_handoff_rejects_truthy_object_field_without_leak() -> None:
    class SecretBearingTruthyObject:
        def __bool__(self) -> bool:
            raise RuntimeError("client_secret=dictionary-form-truthiness-secret")

        def __str__(self) -> str:
            return "client_secret=dictionary-form-truthiness-string"

    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={
            "changes": [
                CandidateChange(
                    table="sys_dictionary",
                    operation="insert",
                    fields={
                        "name": "rm_story",
                        "element": "u_ai_review_notes",
                        "column_label": SecretBearingTruthyObject(),
                    },
                    rationale="Malformed label.",
                ),
                _candidate().changes[1],
            ]
        }
    )

    with pytest.raises(ValueError) as exc_info:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/36",
                instance_url="https://dev205693.service-now.com",
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "dictionary/form handoff field contains non-JSON value"
    assert client.imports == []
    assert client.story_updates == []
    assert "SecretBearingTruthyObject" not in diagnostic
    assert "dictionary-form-truthiness-secret" not in diagnostic
    assert "dictionary-form-truthiness-string" not in diagnostic
    assert "client_secret" not in diagnostic


def test_create_update_set_handoff_sanitizes_description_summary_without_stringifying() -> None:
    class SecretBearingSummaryValue:
        def __str__(self) -> str:
            raise RuntimeError("client_secret=handoff-description-summary-secret")

    client = FakeUpdateSetClient()
    dictionary_change = _candidate().changes[0].model_copy(
        update={
            "fields": {
                **_candidate().changes[0].fields,
                "diagnostic_notes": SecretBearingSummaryValue(),
            }
        }
    )
    candidate = _candidate().model_copy(
        update={"changes": [dictionary_change, _candidate().changes[1]]}
    )

    create_update_set_handoff(
        client=client,
        request=UpdateSetHandoffRequest(
            story_sys_id="story-sys-id",
            story_number="STRY0010013",
            candidate=candidate,
            candidate_artifact_ref="db://artifact_blobs/37",
            instance_url="https://dev205693.service-now.com",
        ),
    )

    imported_xml = client.imports[0]["update_set_xml"]
    assert "diagnostic_notes=[non-json summary value]" in imported_xml
    assert "SecretBearingSummaryValue" not in imported_xml
    assert "handoff-description-summary-secret" not in imported_xml
    assert "client_secret" not in imported_xml


def test_create_update_set_handoff_sanitizes_reviewer_note_without_stringifying() -> None:
    class SecretBearingReviewerNote:
        def __str__(self) -> str:
            raise RuntimeError("client_secret=handoff-reviewer-note-secret")

    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={"reviewer_notes": [SecretBearingReviewerNote()]}
    )

    create_update_set_handoff(
        client=client,
        request=UpdateSetHandoffRequest(
            story_sys_id="story-sys-id",
            story_number="STRY0010013",
            candidate=candidate,
            candidate_artifact_ref="db://artifact_blobs/38",
            instance_url="https://dev205693.service-now.com",
        ),
    )

    imported_xml = client.imports[0]["update_set_xml"]
    assert "- [non-string work note value]" in imported_xml
    assert "SecretBearingReviewerNote" not in imported_xml
    assert "handoff-reviewer-note-secret" not in imported_xml
    assert "client_secret" not in imported_xml


def test_create_update_set_handoff_rejects_reviewer_note_collection_subclass_without_leak() -> None:
    class SecretBearingReviewerNotes(list[object]):
        def __bool__(self) -> bool:
            raise RuntimeError("client_secret=handoff-reviewer-notes-bool-secret")

        def __iter__(self) -> Any:
            raise RuntimeError("client_secret=handoff-reviewer-notes-iter-secret")

    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={"reviewer_notes": SecretBearingReviewerNotes(["Confirm the field exists."])}
    )

    with pytest.raises(ValueError) as exc_info:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/42",
                instance_url="https://dev205693.service-now.com",
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "retrieved Update Set handoff reviewer notes contain non-JSON value"
    assert client.imports == []
    assert client.story_updates == []
    assert "SecretBearingReviewerNotes" not in diagnostic
    assert "handoff-reviewer-notes-bool-secret" not in diagnostic
    assert "handoff-reviewer-notes-iter-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_create_update_set_handoff_sanitizes_description_header_without_stringifying() -> None:
    class SecretBearingArtifactHash:
        def __str__(self) -> str:
            raise RuntimeError("client_secret=handoff-description-header-secret")

    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(update={"artifact_hash": SecretBearingArtifactHash()})

    create_update_set_handoff(
        client=client,
        request=UpdateSetHandoffRequest.model_construct(
            story_sys_id="story-sys-id",
            story_number="STRY0010013",
            candidate=candidate,
            candidate_artifact_ref="db://artifact_blobs/40",
            instance_url="https://dev205693.service-now.com",
        ),
    )

    imported_xml = client.imports[0]["update_set_xml"]
    assert "Candidate hash: [non-string work note value]" in imported_xml
    assert "SecretBearingArtifactHash" not in imported_xml
    assert "handoff-description-header-secret" not in imported_xml
    assert "client_secret" not in imported_xml


def test_create_update_set_handoff_sanitizes_description_metrics_without_stringifying() -> None:
    class SecretBearingMetric:
        def __str__(self) -> str:
            raise RuntimeError("client_secret=handoff-description-metric-secret")

    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={"confidence": SecretBearingMetric(), "risk_score": SecretBearingMetric()}
    )

    create_update_set_handoff(
        client=client,
        request=UpdateSetHandoffRequest(
            story_sys_id="story-sys-id",
            story_number="STRY0010013",
            candidate=candidate,
            candidate_artifact_ref="db://artifact_blobs/40",
            instance_url="https://dev205693.service-now.com",
        ),
    )

    imported_xml = client.imports[0]["update_set_xml"]
    assert "Confidence: [non-json summary value]" in imported_xml
    assert "Risk score: [non-json summary value]" in imported_xml
    assert "SecretBearingMetric" not in imported_xml
    assert "handoff-description-metric-secret" not in imported_xml
    assert "client_secret" not in imported_xml


def test_create_update_set_handoff_rejects_changes_collection_subclass_without_leak() -> None:
    class SecretBearingChanges(list[CandidateChange]):
        def __bool__(self) -> bool:
            raise RuntimeError("client_secret=handoff-changes-bool-secret")

        def __iter__(self) -> Any:
            raise RuntimeError("client_secret=handoff-changes-iter-secret")

    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={"changes": SecretBearingChanges(_candidate().changes)}
    )

    with pytest.raises(ValueError) as exc_info:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/41",
                instance_url="https://dev205693.service-now.com",
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "retrieved Update Set handoff changes contain non-JSON value"
    assert client.imports == []
    assert client.story_updates == []
    assert "SecretBearingChanges" not in diagnostic
    assert "handoff-changes-bool-secret" not in diagnostic
    assert "handoff-changes-iter-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_create_update_set_handoff_rejects_change_table_string_subclass_without_leak() -> None:
    class SecretBearingTable(str):
        def __str__(self) -> str:
            raise RuntimeError("client_secret=handoff-change-table-str-secret")

        def __lt__(self, other: object) -> bool:
            raise RuntimeError("client_secret=handoff-change-table-sort-secret")

    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={
            "changes": [
                CandidateChange.model_construct(
                    table=SecretBearingTable("sys_dictionary"),
                    operation="insert",
                    fields={
                        "name": "rm_story",
                        "element": "u_ai_review_notes",
                        "column_label": "AI Review Notes",
                        "internal_type": "string",
                    },
                    rationale="Create a malformed field change.",
                ),
                _candidate().changes[1],
            ]
        }
    )

    with pytest.raises(ValueError) as exc_info:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/43",
                instance_url="https://dev205693.service-now.com",
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "retrieved Update Set handoff changes contain non-JSON value"
    assert client.imports == []
    assert client.story_updates == []
    assert "SecretBearingTable" not in diagnostic
    assert "handoff-change-table-str-secret" not in diagnostic
    assert "handoff-change-table-sort-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_create_update_set_handoff_rejects_change_operation_string_subclass_without_leak() -> None:
    class SecretBearingOperation(str):
        def __str__(self) -> str:
            raise RuntimeError("client_secret=handoff-change-operation-str-secret")

    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={
            "changes": [
                CandidateChange.model_construct(
                    table="sys_dictionary",
                    operation=SecretBearingOperation("insert"),
                    fields={
                        "name": "rm_story",
                        "element": "u_ai_review_notes",
                        "column_label": "AI Review Notes",
                        "internal_type": "string",
                    },
                    rationale="Create a malformed field change.",
                ),
                _candidate().changes[1],
            ]
        }
    )

    with pytest.raises(ValueError) as exc_info:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/44",
                instance_url="https://dev205693.service-now.com",
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "retrieved Update Set handoff changes contain non-JSON value"
    assert client.imports == []
    assert client.story_updates == []
    assert "SecretBearingOperation" not in diagnostic
    assert "handoff-change-operation-str-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_create_update_set_handoff_rejects_change_fields_dict_subclass_without_leak() -> None:
    class SecretBearingFields(dict[str, Any]):
        def __bool__(self) -> bool:
            raise RuntimeError("client_secret=handoff-change-fields-bool-secret")

        def items(self) -> Any:
            raise RuntimeError("client_secret=handoff-change-fields-items-secret")

    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={
            "changes": [
                CandidateChange.model_construct(
                    table="sys_dictionary",
                    operation="insert",
                    fields=SecretBearingFields(
                        {
                            "name": "rm_story",
                            "element": "u_ai_review_notes",
                            "column_label": "AI Review Notes",
                            "internal_type": "string",
                        }
                    ),
                    rationale="Create a malformed field change.",
                ),
                _candidate().changes[1],
            ]
        }
    )

    with pytest.raises(ValueError) as exc_info:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/45",
                instance_url="https://dev205693.service-now.com",
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "retrieved Update Set handoff change fields contain non-JSON value"
    assert client.imports == []
    assert client.story_updates == []
    assert "SecretBearingFields" not in diagnostic
    assert "handoff-change-fields-bool-secret" not in diagnostic
    assert "handoff-change-fields-items-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_create_update_set_handoff_rejects_change_field_key_string_subclass_without_leak() -> None:
    class SecretBearingFieldKey(str):
        def __str__(self) -> str:
            raise RuntimeError("client_secret=handoff-change-field-key-str-secret")

    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={
            "changes": [
                CandidateChange.model_construct(
                    table="sys_dictionary",
                    operation="insert",
                    fields={
                        SecretBearingFieldKey("name"): "rm_story",
                        "element": "u_ai_review_notes",
                        "column_label": "AI Review Notes",
                        "internal_type": "string",
                    },
                    rationale="Create a malformed field change.",
                ),
                _candidate().changes[1],
            ]
        }
    )

    with pytest.raises(ValueError) as exc_info:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/46",
                instance_url="https://dev205693.service-now.com",
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "retrieved Update Set handoff change fields contain non-JSON value"
    assert client.imports == []
    assert client.story_updates == []
    assert "SecretBearingFieldKey" not in diagnostic
    assert "handoff-change-field-key-str-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_create_update_set_handoff_rejects_truthy_form_table_alias_without_leak() -> None:
    class SecretBearingTruthyAlias:
        def __bool__(self) -> bool:
            raise RuntimeError("client_secret=handoff-form-table-alias-bool-secret")

        def __str__(self) -> str:
            return "client_secret=handoff-form-table-alias-str-secret"

    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={
            "changes": [
                _candidate().changes[0],
                CandidateChange(
                    table="sys_ui_form",
                    operation="update",
                    fields={
                        "table": SecretBearingTruthyAlias(),
                        "field": "u_ai_review_notes",
                        "position_hint": "below Description",
                    },
                    rationale="Malformed form table alias.",
                ),
            ]
        }
    )

    with pytest.raises(ValueError) as exc_info:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/47",
                instance_url="https://dev205693.service-now.com",
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "dictionary/form handoff field contains non-JSON value"
    assert client.imports == []
    assert client.story_updates == []
    assert "SecretBearingTruthyAlias" not in diagnostic
    assert "handoff-form-table-alias-bool-secret" not in diagnostic
    assert "handoff-form-table-alias-str-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_create_update_set_handoff_rejects_truthy_placement_anchor_without_leak() -> None:
    class SecretBearingPlacementAnchor:
        def __bool__(self) -> bool:
            raise RuntimeError("client_secret=handoff-placement-anchor-bool-secret")

        def __str__(self) -> str:
            return "client_secret=handoff-placement-anchor-str-secret"

    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={
            "changes": [
                _candidate().changes[0],
                CandidateChange(
                    table="sys_ui_form",
                    operation="update",
                    fields={
                        "name": "rm_story",
                        "field": "u_ai_review_notes",
                        "placement_anchor": SecretBearingPlacementAnchor(),
                    },
                    rationale="Malformed placement anchor.",
                ),
            ]
        }
    )

    with pytest.raises(ValueError) as exc_info:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/48",
                instance_url="https://dev205693.service-now.com",
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "dictionary/form handoff field contains non-JSON value"
    assert client.imports == []
    assert client.story_updates == []
    assert "SecretBearingPlacementAnchor" not in diagnostic
    assert "handoff-placement-anchor-bool-secret" not in diagnostic
    assert "handoff-placement-anchor-str-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_create_update_set_handoff_rejects_truthy_reference_alias_without_leak() -> None:
    class SecretBearingReferenceAlias:
        def __bool__(self) -> bool:
            raise RuntimeError("client_secret=handoff-reference-alias-bool-secret")

        def __str__(self) -> str:
            return "client_secret=handoff-reference-alias-str-secret"

    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={
            "changes": [
                CandidateChange(
                    table="sys_dictionary",
                    operation="insert",
                    fields={
                        "name": "rm_story",
                        "element": "u_vendor_reference",
                        "column_label": "Vendor Reference",
                        "internal_type": "reference",
                        "reference": SecretBearingReferenceAlias(),
                    },
                    rationale="Malformed reference metadata.",
                ),
                _candidate().changes[1],
            ]
        }
    )

    with pytest.raises(ValueError) as exc_info:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/49",
                instance_url="https://dev205693.service-now.com",
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "dictionary/form handoff field contains non-JSON value"
    assert client.imports == []
    assert client.story_updates == []
    assert "SecretBearingReferenceAlias" not in diagnostic
    assert "handoff-reference-alias-bool-secret" not in diagnostic
    assert "handoff-reference-alias-str-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_create_update_set_handoff_rejects_state_choice_collection_subclass_without_leak() -> None:
    class SecretBearingStateChoices(list[StoryStateChoice]):
        def __iter__(self) -> Any:
            raise RuntimeError("client_secret=handoff-state-choices-iter-secret")

    class MalformedStateChoiceClient(FakeUpdateSetClient):
        def fetch_story_state_choices(self) -> list[StoryStateChoice]:
            return SecretBearingStateChoices(
                [
                    StoryStateChoice(label="Ready for Testing", value="-7", sequence=300),
                ]
            )

    client = MalformedStateChoiceClient()

    with pytest.raises(ValueError) as exc_info:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=_candidate(),
                candidate_artifact_ref="db://artifact_blobs/50",
                instance_url="https://dev205693.service-now.com",
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "retrieved Update Set handoff state choices contain non-JSON value"
    assert len(client.imports) == 1
    assert client.imports[0]["service_id"] == "jedi_update_set_import"
    assert client.story_updates == []
    assert "SecretBearingStateChoices" not in diagnostic
    assert "handoff-state-choices-iter-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_create_update_set_handoff_rejects_state_choice_item_subclass_without_leak() -> None:
    class SecretBearingStateChoice(StoryStateChoice):
        def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
            raise RuntimeError("client_secret=handoff-state-choice-model-dump-secret")

    class MalformedStateChoiceClient(FakeUpdateSetClient):
        def fetch_story_state_choices(self) -> list[StoryStateChoice]:
            return [
                SecretBearingStateChoice(
                    label="Ready for Testing",
                    value="-7",
                    sequence=300,
                ),
            ]

    client = MalformedStateChoiceClient()

    with pytest.raises(ValueError) as exc_info:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=_candidate(),
                candidate_artifact_ref="db://artifact_blobs/51",
                instance_url="https://dev205693.service-now.com",
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "retrieved Update Set handoff state choices contain non-JSON value"
    assert len(client.imports) == 1
    assert client.story_updates == []
    assert "SecretBearingStateChoice" not in diagnostic
    assert "handoff-state-choice-model-dump-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_create_update_set_handoff_remote_sys_id_ignores_malformed_hash() -> None:
    class SecretBearingArtifactHash:
        def __bool__(self) -> bool:
            raise RuntimeError("client_secret=handoff-remote-sys-id-secret")

        def lower(self) -> str:
            raise RuntimeError("client_secret=handoff-remote-sys-id-lower-secret")

    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={"artifact_hash": SecretBearingArtifactHash()}
    )

    create_update_set_handoff(
        client=client,
        request=UpdateSetHandoffRequest(
            story_sys_id="story-sys-id",
            story_number="STRY0010013",
            candidate=candidate,
            candidate_artifact_ref="db://artifact_blobs/39",
            instance_url="https://dev205693.service-now.com",
        ),
    )

    imported_xml = client.imports[0]["update_set_xml"]
    assert "<remote_sys_id>d0010013eea000000000000000000000</remote_sys_id>" in imported_xml
    assert "SecretBearingArtifactHash" not in imported_xml
    assert "handoff-remote-sys-id-secret" not in imported_xml
    assert "handoff-remote-sys-id-lower-secret" not in imported_xml
    assert "client_secret" not in imported_xml


def test_create_update_set_handoff_rejects_integer_subclass_field_without_leak() -> None:
    class SecretBearingInt(int):
        def __str__(self) -> str:
            return "client_secret=integer-subclass-secret"

    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={
            "changes": [
                CandidateChange(
                    table="sys_dictionary",
                    operation="insert",
                    fields={
                        "name": "rm_story",
                        "element": "u_ai_review_notes",
                        "column_label": "AI Review Notes",
                        "internal_type": "string",
                        "max_length": SecretBearingInt(100),
                    },
                    rationale="Malformed length.",
                ),
                _candidate().changes[1],
            ]
        }
    )

    with pytest.raises(ValueError) as exc_info:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/35",
                instance_url="https://dev205693.service-now.com",
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "dictionary/form handoff field contains non-JSON value"
    assert client.imports == []
    assert client.story_updates == []
    assert "SecretBearingInt" not in diagnostic
    assert "integer-subclass-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_create_update_set_handoff_rejects_mismatched_dictionary_and_form_tables() -> None:
    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={
            "changes": [
                _candidate().changes[0],
                CandidateChange(
                    table="sys_ui_form",
                    operation="update",
                    fields={
                        "name": "incident",
                        "field_order": "u_ai_review_notes",
                        "placement_anchor": "description",
                    },
                    rationale="Wrong form target.",
                ),
            ]
        }
    )

    try:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010013",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/2",
                instance_url="https://dev205693.service-now.com",
            ),
        )
    except ValueError as exc:
        assert "dictionary/form handoff changes must target the same table" in str(exc)
    else:
        raise AssertionError("mismatched dictionary/form tables were accepted")

    assert client.imports == []
    assert client.story_updates == []
