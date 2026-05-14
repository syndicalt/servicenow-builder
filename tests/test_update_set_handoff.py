from __future__ import annotations

from typing import Any

from jedi_devproject.models import (
    CandidateChange,
    CandidateStatus,
    UpdateSetCandidate,
)
from jedi_devproject.update_set_handoff import (
    UpdateSetHandoffRequest,
    create_update_set_handoff,
)


class FakeUpdateSetClient:
    def __init__(self) -> None:
        self.fetches: list[dict[str, object]] = []
        self.upserts: list[dict[str, Any]] = []
        self.story_updates: list[dict[str, Any]] = []

    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        self.fetches.append({"table": table, "lookup": lookup, "fields": fields, "limit": limit})
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

    assert result.update_set_sys_id == "update-set-sys-id"
    assert result.update_set_name == "JEDI STRY0010013 - AI Candidate"
    assert result.update_set_url == (
        "https://dev205693.service-now.com/sys_remote_update_set.do?sys_id=update-set-sys-id"
    )
    assert [upsert["table"] for upsert in client.upserts] == [
        "sys_remote_update_set",
        "sys_update_xml",
        "sys_update_xml",
    ]
    assert client.upserts[0] == {
        "table": "sys_remote_update_set",
        "lookup": {"name": "JEDI STRY0010013 - AI Candidate"},
        "fields": {
            "name": "JEDI STRY0010013 - AI Candidate",
            "state": "loaded",
            "description": (
                "Jedi DevProject generated retrieved update set for STRY0010013.\n\n"
                "Candidate artifact: db://artifact_blobs/2\n"
                "Candidate hash: "
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
                "Status: Ready for Review\n"
                "Confidence: 0.75\n"
                "Risk score: 0.1\n\n"
                "Proposed changes:\n"
                "- insert sys_dictionary: name=rm_story, "
                "element=u_ai_review_notes, column_label=AI Review Notes\n\n"
                "Reviewer notes:\n"
                "- Confirm the field exists.\n\n"
                "This retrieved Update Set is a review handoff. Preview, scan, "
                "and commit only after ServiceNow-native review."
            ),
            "remote_sys_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "origin_sys_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "application": "global",
        },
    }
    assert client.upserts[1]["lookup"] == {
        "name": "sys_dictionary_rm_story_u_ai_review_notes",
        "remote_update_set": "update-set-sys-id",
    }
    assert client.upserts[1]["fields"]["type"] == "Dictionary"
    assert client.upserts[1]["fields"]["target_name"] == "Story.AI Review Notes"
    assert client.upserts[1]["fields"]["remote_update_set"] == "update-set-sys-id"
    assert '<sys_dictionary action="INSERT_OR_UPDATE"' in str(
        client.upserts[1]["fields"]["payload"]
    )
    assert client.upserts[2]["lookup"] == {
        "name": "sys_documentation_rm_story_u_ai_review_notes_en",
        "remote_update_set": "update-set-sys-id",
    }
    assert client.upserts[2]["fields"]["type"] == "Field Label"
    assert '<sys_documentation action="INSERT_OR_UPDATE"' in str(
        client.upserts[2]["fields"]["payload"]
    )
    assert all(upsert["table"] != "sys_update_set" for upsert in client.upserts)
    assert all(
        not (upsert["table"] == "sys_update_xml" and "update_set" in dict(upsert["fields"]))
        for upsert in client.upserts
    )
    assert client.story_updates == [
        {
            "story_sys_id": "story-sys-id",
            "fields": {
                "work_notes": (
                    "ServiceNow retrieved Update Set handoff created for STRY0010013. "
                    "Retrieved Update Set: JEDI STRY0010013 - AI Candidate "
                    "(https://dev205693.service-now.com/sys_remote_update_set.do?"
                    "sys_id=update-set-sys-id). "
                    "Candidate artifact: db://artifact_blobs/2."
                )
            },
        }
    ]


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
        upsert for upsert in client.upserts if upsert["fields"].get("type") == "Form Layout"
    ]
    assert [update["lookup"] for update in form_updates] == [
        {
            "name": "sys_ui_section_default-main-section-sys-id",
            "remote_update_set": "update-set-sys-id",
        },
        {
            "name": "sys_ui_section_scrum-main-section-sys-id",
            "remote_update_set": "update-set-sys-id",
        },
    ]
    assert "notes-section-sys-id" not in str(form_updates)
    assert "<element>u_ai_review_notes</element><position>5</position>" in str(
        form_updates[0]["fields"]["payload"]
    )
    assert "<element>u_ai_review_notes</element><position>20</position>" in str(
        form_updates[1]["fields"]["payload"]
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

    assert client.upserts[1]["lookup"] == {
        "name": "sys_dictionary_rm_story_u_ai_review_notes",
        "remote_update_set": "update-set-sys-id",
    }
    assert client.upserts[1]["fields"]["target_name"] == "Story.AI Review Notes"
    assert "<max_length>8000</max_length>" in str(client.upserts[1]["fields"]["payload"])
    assert "<mandatory>false</mandatory>" in str(client.upserts[1]["fields"]["payload"])
    assert client.upserts[3]["lookup"] == {
        "name": "sys_ui_section_default-main-section-sys-id",
        "remote_update_set": "update-set-sys-id",
    }


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

    assert client.upserts[1]["lookup"] == {
        "name": "sys_dictionary_rm_story_u_ai_review_notes",
        "remote_update_set": "update-set-sys-id",
    }
    assert client.upserts[1]["fields"]["target_name"] == "Story.AI Review Notes"
    assert "<name>rm_story</name>" in str(client.upserts[1]["fields"]["payload"])
    assert "<element>u_ai_review_notes</element>" in str(client.upserts[1]["fields"]["payload"])
    assert '<internal_type display_value="String">string</internal_type>' in str(
        client.upserts[1]["fields"]["payload"]
    )
    assert client.upserts[3]["lookup"] == {
        "name": "sys_ui_section_default-main-section-sys-id",
        "remote_update_set": "update-set-sys-id",
    }


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
