from __future__ import annotations

from typing import Any

from jedi_devproject.models import (
    CandidateChange,
    CandidateStatus,
    UpdateSetCandidate,
)
from jedi_devproject.servicenow import StoryStateChoice
from jedi_devproject.update_set_handoff import (
    UpdateSetHandoffRequest,
    create_update_set_handoff,
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


def test_create_update_set_handoff_imports_business_rule_customer_update() -> None:
    client = FakeUpdateSetClient()

    create_update_set_handoff(
        client=client,
        request=UpdateSetHandoffRequest(
            story_sys_id="story-sys-id",
            story_number="STRY0010116",
            candidate=_business_rule_candidate(),
            candidate_artifact_ref="db://artifact_blobs/116",
            instance_url="https://dev205693.service-now.com",
        ),
    )

    imported_xml = client.imports[0]["update_set_xml"]
    assert "sys_script_incident_jedi_incident_priority_note" in imported_xml
    assert "<sys_script action=\"INSERT_OR_UPDATE\">" in imported_xml
    assert "<collection>incident</collection>" in imported_xml
    assert "<when>before</when>" in imported_xml
    assert "<action_update>true</action_update>" in imported_xml
    assert "current.priority.changesTo" in imported_xml
    assert client.story_updates[-1]["fields"]["state"] == "-7"
    assert client.story_updates[-1]["fields"]["u_ai_status"] == "Ready for Testing"


def test_create_update_set_handoff_rejects_forbidden_business_rule_script() -> None:
    client = FakeUpdateSetClient()
    forbidden_fields = {
        **_business_rule_candidate().changes[0].fields,
        "script": "new GlideRecord('sys_user').query();",
    }
    candidate = _business_rule_candidate().model_copy(
        update={
            "changes": [
                _business_rule_candidate().changes[0].model_copy(
                    update={"fields": forbidden_fields}
                )
            ]
        }
    )

    try:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010116",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/116",
                instance_url="https://dev205693.service-now.com",
            ),
        )
    except ValueError as exc:
        assert "forbidden Business Rule script token: GlideRecord" in str(exc)
    else:
        raise AssertionError("forbidden Business Rule script was accepted")

    assert client.imports == []


def test_create_update_set_handoff_imports_client_script_customer_update() -> None:
    client = FakeUpdateSetClient()

    create_update_set_handoff(
        client=client,
        request=UpdateSetHandoffRequest(
            story_sys_id="story-sys-id",
            story_number="STRY0010118",
            candidate=_client_script_candidate(),
            candidate_artifact_ref="db://artifact_blobs/118",
            instance_url="https://dev205693.service-now.com",
        ),
    )

    imported_xml = client.imports[0]["update_set_xml"]
    assert "sys_script_client_incident_jedi_incident_category_ci_message" in imported_xml
    assert "<sys_script_client action=\"INSERT_OR_UPDATE\">" in imported_xml
    assert "<table>incident</table>" in imported_xml
    assert "<type>onChange</type>" in imported_xml
    assert "<field>category</field>" in imported_xml
    assert "g_form.addInfoMessage" in imported_xml
    assert client.story_updates[-1]["fields"]["state"] == "-7"
    assert client.story_updates[-1]["fields"]["u_ai_status"] == "Ready for Testing"


def test_create_update_set_handoff_rejects_forbidden_client_script_browser_api() -> None:
    client = FakeUpdateSetClient()
    forbidden_fields = {
        **_client_script_candidate().changes[0].fields,
        "script": "fetch('https://example.com');",
    }
    candidate = _client_script_candidate().model_copy(
        update={
            "changes": [
                _client_script_candidate().changes[0].model_copy(
                    update={"fields": forbidden_fields}
                )
            ]
        }
    )

    try:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010118",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/118",
                instance_url="https://dev205693.service-now.com",
            ),
        )
    except ValueError as exc:
        assert "forbidden Client Script token: fetch" in str(exc)
    else:
        raise AssertionError("forbidden Client Script was accepted")

    assert client.imports == []


def test_create_update_set_handoff_imports_script_include_customer_update() -> None:
    client = FakeUpdateSetClient()

    create_update_set_handoff(
        client=client,
        request=UpdateSetHandoffRequest(
            story_sys_id="story-sys-id",
            story_number="STRY0010120",
            candidate=_script_include_candidate(),
            candidate_artifact_ref="db://artifact_blobs/120",
            instance_url="https://dev205693.service-now.com",
        ),
    )

    imported_xml = client.imports[0]["update_set_xml"]
    assert "sys_script_include_jediincidentutils" in imported_xml
    assert "<sys_script_include action=\"INSERT_OR_UPDATE\">" in imported_xml
    assert "<name>JediIncidentUtils</name>" in imported_xml
    assert "<api_name>global.JediIncidentUtils</api_name>" in imported_xml
    assert "<client_callable>false</client_callable>" in imported_xml
    assert "normalizeCategory" in imported_xml
    assert client.story_updates[-1]["fields"]["state"] == "-7"
    assert client.story_updates[-1]["fields"]["u_ai_status"] == "Ready for Testing"


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


def test_create_update_set_handoff_rejects_client_callable_script_include() -> None:
    client = FakeUpdateSetClient()
    forbidden_fields = {
        **_script_include_candidate().changes[0].fields,
        "client_callable": True,
    }
    candidate = _script_include_candidate().model_copy(
        update={
            "changes": [
                _script_include_candidate().changes[0].model_copy(
                    update={"fields": forbidden_fields}
                )
            ]
        }
    )

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
        assert "client callable Script Includes are not supported" in str(exc)
    else:
        raise AssertionError("client callable Script Include was accepted")

    assert client.imports == []


def test_create_update_set_handoff_imports_ui_policy_customer_updates() -> None:
    client = FakeUpdateSetClient()

    create_update_set_handoff(
        client=client,
        request=UpdateSetHandoffRequest(
            story_sys_id="story-sys-id",
            story_number="STRY0010123",
            candidate=_ui_policy_candidate(),
            candidate_artifact_ref="db://artifact_blobs/123",
            instance_url="https://dev205693.service-now.com",
        ),
    )

    imported_xml = client.imports[0]["update_set_xml"]
    assert "sys_ui_policy_incident_jedi_incident_assignment_group_required" in imported_xml
    assert "sys_ui_policy_action_incident_assignment_group_required" in imported_xml
    assert "<sys_ui_policy action=\"INSERT_OR_UPDATE\">" in imported_xml
    assert "<sys_ui_policy_action action=\"INSERT_OR_UPDATE\">" in imported_xml
    assert "<table>incident</table>" in imported_xml
    assert "<conditions>category=software</conditions>" in imported_xml
    assert "<reverse_if_false>true</reverse_if_false>" in imported_xml
    assert "<run_scripts>false</run_scripts>" in imported_xml
    assert "<field>assignment_group</field>" in imported_xml
    assert "<mandatory>true</mandatory>" in imported_xml
    assert "<visible>true</visible>" in imported_xml
    assert "<disabled>ignore</disabled>" in imported_xml
    assert "<cleared>false</cleared>" in imported_xml
    assert client.story_updates[-1]["fields"]["state"] == "-7"
    assert client.story_updates[-1]["fields"]["u_ai_status"] == "Ready for Testing"


def test_create_update_set_handoff_rejects_ui_policy_run_scripts() -> None:
    client = FakeUpdateSetClient()
    forbidden_fields = {
        **_ui_policy_candidate().changes[0].fields,
        "run_scripts": True,
        "script_true": "g_form.setMandatory('assignment_group', true);",
    }
    candidate = _ui_policy_candidate().model_copy(
        update={
            "changes": [
                _ui_policy_candidate().changes[0].model_copy(
                    update={"fields": forbidden_fields}
                ),
                _ui_policy_candidate().changes[1],
            ]
        }
    )

    try:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010123",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/123",
                instance_url="https://dev205693.service-now.com",
            ),
        )
    except ValueError as exc:
        assert "UI Policy run_scripts must be false" in str(exc)
    else:
        raise AssertionError("UI Policy with run scripts was accepted")

    assert client.imports == []


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
        assert "retrieved Update Set candidate mixes unsupported change types" in str(exc)
    else:
        raise AssertionError("unsupported candidate table was accepted")

    assert client.imports == []


def test_create_update_set_handoff_rejects_flow_graph_diff_until_builder_exists() -> None:
    client = FakeUpdateSetClient()
    candidate = _candidate().model_copy(
        update={
            "changes": [
                CandidateChange(
                    table="sys_hub_flow_graph_diff",
                    operation="update",
                    fields={
                        "capability": "flow_modify",
                        "flow_name": "Incident Triage",
                    },
                    rationale="Validation-only Flow graph diff.",
                )
            ]
        }
    )

    try:
        create_update_set_handoff(
            client=client,
            request=UpdateSetHandoffRequest(
                story_sys_id="story-sys-id",
                story_number="STRY0010126",
                candidate=candidate,
                candidate_artifact_ref="db://artifact_blobs/126",
                instance_url="https://dev205693.service-now.com",
            ),
        )
    except ValueError as exc:
        assert "unsupported retrieved Update Set table: sys_hub_flow_graph_diff" in str(exc)
    else:
        raise AssertionError("Flow graph diff was accepted for Update Set handoff")

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
