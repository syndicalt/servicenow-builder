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
        self.upserts: list[dict[str, object]] = []
        self.story_updates: list[dict[str, object]] = []

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


def test_create_update_set_handoff_creates_native_update_set_and_links_story() -> None:
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
        "https://dev205693.service-now.com/sys_update_set.do?sys_id=update-set-sys-id"
    )
    assert client.upserts == [
        {
            "table": "sys_update_set",
            "lookup": {"name": "JEDI STRY0010013 - AI Candidate"},
            "fields": {
                "name": "JEDI STRY0010013 - AI Candidate",
                "state": "in progress",
                "description": (
                    "Jedi DevProject generated handoff for STRY0010013.\n\n"
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
                    "This Update Set is a review handoff. Do not commit until the "
                    "ServiceNow-native update contents have been reviewed."
                ),
            },
        }
    ]
    assert client.story_updates == [
        {
            "story_sys_id": "story-sys-id",
            "fields": {
                "work_notes": (
                    "ServiceNow Update Set handoff created for STRY0010013. "
                    "Update Set: JEDI STRY0010013 - AI Candidate "
                    "(https://dev205693.service-now.com/sys_update_set.do?"
                    "sys_id=update-set-sys-id). "
                    "Candidate artifact: db://artifact_blobs/2."
                )
            },
        }
    ]


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
