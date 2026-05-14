from __future__ import annotations

from typing import Any, cast

import pytest

from jedi_devproject.models import (
    CandidateChange,
    CandidateStatus,
    UpdateSetCandidate,
)
from jedi_devproject.update_set_apply import (
    UpdateSetApplyRequest,
    apply_candidate_to_update_set,
)

_DEFAULT: Any = object()


class FakeApplyClient:
    def __init__(
        self,
        *,
        user_record: dict[str, Any] | None = _DEFAULT,
        customer_updates: list[dict[str, Any]] = _DEFAULT,
    ) -> None:
        self.user_record = {"sys_id": "user-sys-id"} if user_record is _DEFAULT else user_record
        self.customer_updates = (
            [{"sys_id": "customer-update-sys-id", "name": "sys_dictionary_rm_story_u_ai"}]
            if customer_updates is _DEFAULT
            else customer_updates
        )
        self.fetches: list[dict[str, object]] = []
        self.upserts: list[dict[str, object]] = []

    def fetch_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
    ) -> dict[str, Any] | None:
        self.fetches.append({"table": table, "lookup": lookup})
        if table == "sys_user":
            return cast(dict[str, Any] | None, self.user_record)
        return None

    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        self.fetches.append({"table": table, "lookup": lookup, "fields": fields, "limit": limit})
        if table == "sys_update_xml":
            return cast(list[dict[str, Any]], self.customer_updates)
        if table == "sys_ui_section" and lookup == {
            "name": "rm_story",
            "caption": "Notes",
        }:
            return [{"sys_id": "notes-section-sys-id", "caption": "Notes"}]
        if table == "sys_ui_element" and lookup == {
            "name": "rm_story",
            "sys_ui_section": "notes-section-sys-id",
        }:
            return [
                {
                    "sys_id": "work-notes-element-sys-id",
                    "element": "work_notes",
                    "position": "0",
                },
                {
                    "sys_id": "activity-element-sys-id",
                    "element": "activity.xml",
                    "position": "1",
                },
            ]
        if table == "sys_ui_element" and lookup == {
            "name": "rm_story",
            "element": "description",
        }:
            return [
                {
                    "sys_id": "description-element-sys-id",
                    "name": "rm_story",
                    "element": "description",
                    "sys_ui_section": {"value": "main-section-sys-id"},
                    "position": "3",
                }
            ]
        if table == "sys_ui_element" and lookup == {
            "name": "rm_story",
            "sys_ui_section": "main-section-sys-id",
        }:
            return [
                {
                    "sys_id": "short-description-element-sys-id",
                    "element": "short_description",
                    "position": "1",
                },
                {
                    "sys_id": "description-element-sys-id",
                    "element": "description",
                    "position": "3",
                },
                {
                    "sys_id": "acceptance-element-sys-id",
                    "element": "acceptance_criteria",
                    "position": "4",
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
        return {"sys_id": f"{table}-sys-id"}


def _candidate(changes: list[CandidateChange]) -> UpdateSetCandidate:
    return UpdateSetCandidate(
        story_number="STRY0010013",
        name="UPD_STRY0010013_LLM_Implementation",
        eligibility_decision="eligible",
        eligibility_reasons=["Low-risk dictionary story."],
        confidence=0.82,
        risk_score=0.08,
        status=CandidateStatus.READY_FOR_REVIEW,
        changes=changes,
        reviewer_notes=["Review generated customer updates before commit."],
        artifact_hash="a" * 64,
    )


def test_apply_candidate_sets_current_update_set_then_applies_dictionary_change() -> None:
    client = FakeApplyClient()
    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "column_name": "u_ai_review_notes",
                    "column_label": "AI Review Notes",
                    "internal_type": "journal_input",
                    "max_length": 8000,
                },
            )
        ]
    )

    result = apply_candidate_to_update_set(
        client=client,
        request=UpdateSetApplyRequest(
            update_set_sys_id="update-set-sys-id",
            integration_user_name="jedi.integration",
            candidate=candidate,
        ),
    )

    assert result.customer_update_count == 1
    assert result.applied_change_count == 1
    assert client.fetches[0] == {
        "table": "sys_user",
        "lookup": {"user_name": "jedi.integration"},
    }
    assert client.upserts == [
        {
            "table": "sys_user_preference",
            "lookup": {"name": "sys_update_set", "user": "user-sys-id"},
            "fields": {
                "name": "sys_update_set",
                "user": "user-sys-id",
                "value": "update-set-sys-id",
            },
        },
        {
            "table": "sys_dictionary",
            "lookup": {"name": "rm_story", "element": "u_ai_review_notes"},
            "fields": {
                "name": "rm_story",
                "element": "u_ai_review_notes",
                "column_label": "AI Review Notes",
                "internal_type": "journal_input",
                "max_length": "8000",
            },
        },
    ]
    assert all(upsert["table"] != "sys_update_xml" for upsert in client.upserts)
    assert client.fetches[-1] == {
        "table": "sys_update_xml",
        "lookup": {"update_set": "update-set-sys-id"},
        "fields": ["sys_id", "name", "target_name", "type"],
        "limit": 100,
    }


def test_apply_candidate_places_form_field_in_notes_section_by_default() -> None:
    client = FakeApplyClient()
    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_ai_review_notes",
                    "column_label": "AI Review Notes",
                    "internal_type": "journal_input",
                },
            ),
            CandidateChange(
                table="sys_ui_form",
                operation="update",
                fields={
                    "table": "rm_story",
                    "field": "u_ai_review_notes",
                    "position": "below Description",
                    "view": "default",
                },
            ),
        ]
    )

    result = apply_candidate_to_update_set(
        client=client,
        request=UpdateSetApplyRequest(
            update_set_sys_id="update-set-sys-id",
            integration_user_name="jedi.integration",
            candidate=candidate,
        ),
    )

    assert result.applied_change_count == 2
    assert [upsert["table"] for upsert in client.upserts] == [
        "sys_user_preference",
        "sys_dictionary",
        "sys_ui_element",
    ]
    assert client.upserts[2] == {
        "table": "sys_ui_element",
        "lookup": {
            "name": "rm_story",
            "element": "u_ai_review_notes",
            "sys_ui_section": "notes-section-sys-id",
        },
        "fields": {
            "name": "rm_story",
            "element": "u_ai_review_notes",
            "sys_ui_section": "notes-section-sys-id",
            "position": "2",
        },
    }


def test_apply_candidate_infers_form_target_from_single_custom_dictionary_field() -> None:
    client = FakeApplyClient()
    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_ai_review_notes",
                    "column_label": "AI Review Notes",
                    "internal_type": "string",
                },
            ),
            CandidateChange(
                table="sys_ui_form",
                operation="update",
                fields={"name": "rm_story", "view": "default"},
                rationale="Updating the story form to include the AI Review Notes field.",
            ),
        ]
    )

    apply_candidate_to_update_set(
        client=client,
        request=UpdateSetApplyRequest(
            update_set_sys_id="update-set-sys-id",
            integration_user_name="jedi.integration",
            candidate=candidate,
        ),
    )

    assert client.upserts[-1] == {
        "table": "sys_ui_element",
        "lookup": {
            "name": "rm_story",
            "element": "u_ai_review_notes",
            "sys_ui_section": "notes-section-sys-id",
        },
        "fields": {
            "name": "rm_story",
            "element": "u_ai_review_notes",
            "sys_ui_section": "notes-section-sys-id",
            "position": "2",
        },
    }


def test_apply_candidate_uses_named_form_section_when_provided() -> None:
    client = FakeApplyClient()
    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_ai_review_notes",
                    "column_label": "AI Review Notes",
                    "internal_type": "string",
                },
            ),
            CandidateChange(
                table="sys_ui_form",
                operation="update",
                fields={
                    "field_name": "u_ai_review_notes",
                    "form_section_name": "Notes",
                },
            ),
        ]
    )

    apply_candidate_to_update_set(
        client=client,
        request=UpdateSetApplyRequest(
            update_set_sys_id="update-set-sys-id",
            integration_user_name="jedi.integration",
            candidate=candidate,
        ),
    )

    assert client.upserts[-1]["lookup"] == {
        "name": "rm_story",
        "element": "u_ai_review_notes",
        "sys_ui_section": "notes-section-sys-id",
    }


def test_apply_candidate_normalizes_model_field_aliases() -> None:
    client = FakeApplyClient()
    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "field_name": "u_ai_review_notes",
                    "field_label": "AI Review Notes",
                    "help_text": "Notes from human review.",
                    "mandatory": False,
                    "max_length": 8000,
                    "default_value": "",
                    "internal_type": "string",
                },
            ),
            CandidateChange(
                table="sys_ui_form",
                operation="update",
                fields={
                    "view_name": "Default",
                    "field_name": "u_ai_review_notes",
                    "form_section_name": "Notes",
                },
            ),
        ]
    )

    apply_candidate_to_update_set(
        client=client,
        request=UpdateSetApplyRequest(
            update_set_sys_id="update-set-sys-id",
            integration_user_name="jedi.integration",
            candidate=candidate,
        ),
    )

    assert client.upserts[1] == {
        "table": "sys_dictionary",
        "lookup": {"name": "rm_story", "element": "u_ai_review_notes"},
        "fields": {
            "name": "rm_story",
            "element": "u_ai_review_notes",
            "column_label": "AI Review Notes",
            "help": "Notes from human review.",
            "mandatory": False,
            "max_length": "8000",
            "default_value": "",
            "internal_type": "string",
        },
    }
    assert client.upserts[-1]["lookup"] == {
        "name": "rm_story",
        "element": "u_ai_review_notes",
        "sys_ui_section": "notes-section-sys-id",
    }


def test_apply_candidate_normalizes_known_field_defaults_and_form_xml_element() -> None:
    client = FakeApplyClient()
    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_ai_review_notes",
                    "hint": "Notes from human review.",
                    "mandatory": False,
                    "max_length": 8000,
                    "default_value": "",
                    "internal_type": "string",
                },
            ),
            CandidateChange(
                table="sys_ui_form",
                operation="update",
                fields={
                    "name": "rm_story",
                    "elements": "<field name='u_ai_review_notes' section='Notes'/>",
                },
            ),
        ]
    )

    apply_candidate_to_update_set(
        client=client,
        request=UpdateSetApplyRequest(
            update_set_sys_id="update-set-sys-id",
            integration_user_name="jedi.integration",
            candidate=candidate,
        ),
    )

    dictionary_fields = cast(dict[str, Any], client.upserts[1]["fields"])
    assert dictionary_fields["column_label"] == "AI Review Notes"
    assert dictionary_fields["help"] == "Notes from human review."
    assert client.upserts[-1]["lookup"] == {
        "name": "rm_story",
        "element": "u_ai_review_notes",
        "sys_ui_section": "notes-section-sys-id",
    }


def test_apply_candidate_rejects_unsupported_change_before_mutation() -> None:
    client = FakeApplyClient()
    candidate = _candidate(
        [CandidateChange(table="sys_user", operation="update", fields={"name": "bad"})]
    )

    with pytest.raises(ValueError, match="unsupported update-set apply table: sys_user"):
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    assert client.fetches == []
    assert client.upserts == []


def test_apply_candidate_requires_integration_user_before_mutation() -> None:
    client = FakeApplyClient(user_record=None)
    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_ai_review_notes",
                    "column_label": "AI Review Notes",
                    "internal_type": "journal_input",
                },
            )
        ]
    )

    with pytest.raises(RuntimeError, match="integration user not found"):
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    assert client.upserts == []


def test_apply_candidate_requires_customer_updates_after_apply() -> None:
    client = FakeApplyClient(customer_updates=[])
    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_ai_review_notes",
                    "column_label": "AI Review Notes",
                    "internal_type": "journal_input",
                },
            )
        ]
    )

    with pytest.raises(RuntimeError, match="no customer updates captured"):
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    assert [upsert["table"] for upsert in client.upserts] == [
        "sys_user_preference",
        "sys_dictionary",
    ]
