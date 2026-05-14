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
            )
        ],
        reviewer_notes=["Confirm the field exists."],
        artifact_hash="a" * 64,
    )


def _dictionary_form_candidate() -> UpdateSetCandidate:
    return _candidate().model_copy(
        update={
            "changes": [
                *_candidate().changes,
                CandidateChange(
                    table="sys_ui_form",
                    operation="update",
                    fields={
                        "table": "rm_story",
                        "field": "u_ai_review_notes",
                        "position_hint": "below Description",
                    },
                    rationale="Place the requested field on the Story form.",
                ),
            ]
        }
    )


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
                "work_notes": (
                    "ServiceNow retrieved Update Set handoff created for STRY0010013. "
                    "Retrieved Update Set: JEDI STRY0010013 - AI Candidate "
                    "(https://dev205693.service-now.com/sys_remote_update_set.do?"
                    "sys_id=remote-update-set-sys-id). "
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
