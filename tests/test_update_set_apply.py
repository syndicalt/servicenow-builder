from __future__ import annotations

from typing import Any, cast

import pytest

from jedi_devproject.models import (
    CandidateChange,
    CandidateStatus,
    UpdateSetCandidate,
)
from jedi_devproject.update_set_apply import (
    UPDATE_SET_APPLY_CANDIDATE_FIELD_NON_JSON_DIAGNOSTIC,
    UPDATE_SET_APPLY_CHANGE_FIELDS_NON_JSON_DIAGNOSTIC,
    UPDATE_SET_APPLY_CHANGE_IDENTIFIER_NON_JSON_DIAGNOSTIC,
    UPDATE_SET_APPLY_CHANGES_NON_JSON_DIAGNOSTIC,
    UPDATE_SET_APPLY_LOOKUP_NON_JSON_DIAGNOSTIC,
    UPDATE_SET_APPLY_METADATA_MISSING_DIAGNOSTIC,
    UPDATE_SET_APPLY_METADATA_NON_JSON_DIAGNOSTIC,
    UPDATE_SET_APPLY_POSITION_INVALID_DIAGNOSTIC,
    UPDATE_SET_APPLY_RECORD_NON_JSON_DIAGNOSTIC,
    UPDATE_SET_APPLY_RECORDS_NON_JSON_DIAGNOSTIC,
    UPDATE_SET_APPLY_REQUEST_NON_JSON_DIAGNOSTIC,
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
        if table == "sys_ui_section" and lookup == {"name": "rm_story"}:
            return [
                {
                    "sys_id": "main-section-sys-id",
                    "name": "rm_story",
                    "caption": "",
                    "view": {"display_value": "Default view", "value": "Default view"},
                    "sys_user": "",
                },
                {
                    "sys_id": "schedule-section-sys-id",
                    "name": "rm_story",
                    "caption": "Schedule",
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
                    "sys_id": "personal-main-section-sys-id",
                    "name": "rm_story",
                    "caption": "",
                    "view": {"display_value": "Scrum", "value": "scrum-view-sys-id"},
                    "sys_user": "user-sys-id",
                },
            ]
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
                    "sys_user": "",
                },
                {
                    "sys_id": "scrum-description-element-sys-id",
                    "name": "rm_story",
                    "element": "description",
                    "sys_ui_section": {"value": "scrum-main-section-sys-id"},
                    "position": "19",
                    "sys_user": "",
                },
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
        if table == "sys_ui_element" and lookup == {
            "name": "rm_story",
            "sys_ui_section": "scrum-main-section-sys-id",
        }:
            return [
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


def test_apply_candidate_rejects_request_update_set_sys_id_string_subclass() -> None:
    class SecretBearingUpdateSetSysId(str):
        pass

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
            )
        ]
    )
    request = UpdateSetApplyRequest.model_construct(
        update_set_sys_id=SecretBearingUpdateSetSysId(
            "client_secret=legacy-apply-update-set-subclass"
        ),
        integration_user_name="jedi.integration",
        candidate=candidate,
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(client=client, request=request)

    diagnostic = str(exc_info.value)
    assert diagnostic == UPDATE_SET_APPLY_REQUEST_NON_JSON_DIAGNOSTIC
    assert client.fetches == []
    assert client.upserts == []
    assert "SecretBearingUpdateSetSysId" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "legacy-apply-update-set-subclass" not in diagnostic


def test_apply_candidate_rejects_request_integration_user_string_subclass() -> None:
    class SecretBearingIntegrationUser(str):
        pass

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
            )
        ]
    )
    request = UpdateSetApplyRequest.model_construct(
        update_set_sys_id="update-set-sys-id",
        integration_user_name=SecretBearingIntegrationUser(
            "client_secret=legacy-apply-integration-user-subclass"
        ),
        candidate=candidate,
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(client=client, request=request)

    diagnostic = str(exc_info.value)
    assert diagnostic == UPDATE_SET_APPLY_REQUEST_NON_JSON_DIAGNOSTIC
    assert client.fetches == []
    assert client.upserts == []
    assert "SecretBearingIntegrationUser" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "legacy-apply-integration-user-subclass" not in diagnostic


def test_apply_candidate_rejects_changes_collection_subclass_without_leak() -> None:
    class SecretBearingChanges(list[CandidateChange]):
        def __bool__(self) -> bool:
            raise RuntimeError("client_secret=legacy-apply-changes-bool")

        def __iter__(self) -> Any:
            raise RuntimeError("client_secret=legacy-apply-changes-iter")

    client = FakeApplyClient()
    candidate = _candidate([]).model_copy(
        update={
            "changes": SecretBearingChanges(
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
        }
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == UPDATE_SET_APPLY_CHANGES_NON_JSON_DIAGNOSTIC
    assert client.fetches == []
    assert client.upserts == []
    assert "SecretBearingChanges" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "legacy-apply-changes-bool" not in diagnostic
    assert "legacy-apply-changes-iter" not in diagnostic


def test_apply_candidate_rejects_non_candidate_change_without_leak() -> None:
    class SecretBearingChange:
        @property
        def table(self) -> str:
            raise RuntimeError("client_secret=legacy-apply-change-table")

    client = FakeApplyClient()
    candidate = _candidate([]).model_copy(update={"changes": [SecretBearingChange()]})

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == UPDATE_SET_APPLY_CHANGES_NON_JSON_DIAGNOSTIC
    assert client.fetches == []
    assert client.upserts == []
    assert "SecretBearingChange" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "legacy-apply-change-table" not in diagnostic


def test_apply_candidate_rejects_dictionary_change_fields_subclass_without_leak() -> None:
    class SecretBearingDictionaryFields(dict[str, Any]):
        def items(self) -> Any:
            raise RuntimeError("client_secret=legacy-apply-dictionary-fields-items")

        def get(self, key: object, default: object = None) -> object:
            raise RuntimeError("client_secret=legacy-apply-dictionary-fields-get")

    client = FakeApplyClient()
    candidate = _candidate(
        [
            CandidateChange.model_construct(
                table="sys_dictionary",
                operation="insert",
                fields=SecretBearingDictionaryFields(
                    {
                        "name": "rm_story",
                        "element": "u_ai_review_notes",
                        "column_label": "AI Review Notes",
                        "internal_type": "journal_input",
                    }
                ),
            )
        ]
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == UPDATE_SET_APPLY_CHANGE_FIELDS_NON_JSON_DIAGNOSTIC
    assert client.fetches == []
    assert client.upserts == []
    assert "SecretBearingDictionaryFields" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "legacy-apply-dictionary-fields-items" not in diagnostic
    assert "legacy-apply-dictionary-fields-get" not in diagnostic


def test_apply_candidate_rejects_form_change_fields_subclass_without_leak() -> None:
    class SecretBearingFormFields(dict[str, Any]):
        def get(self, key: object, default: object = None) -> object:
            raise RuntimeError("client_secret=legacy-apply-form-fields-get")

    client = FakeApplyClient()
    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_release_summary",
                    "column_label": "Release Summary",
                    "internal_type": "string",
                },
            ),
            CandidateChange.model_construct(
                table="sys_ui_form",
                operation="update",
                fields=SecretBearingFormFields(
                    {
                        "field_name": "u_release_summary",
                        "form_section_name": "Notes",
                    }
                ),
            ),
        ]
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == UPDATE_SET_APPLY_CHANGE_FIELDS_NON_JSON_DIAGNOSTIC
    assert client.fetches == []
    assert client.upserts == []
    assert "SecretBearingFormFields" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "legacy-apply-form-fields-get" not in diagnostic


def test_apply_candidate_rejects_dictionary_change_field_key_object_without_leak() -> None:
    class SecretBearingFieldKey:
        def __hash__(self) -> int:
            return 17

        def __str__(self) -> str:
            raise RuntimeError("client_secret=legacy-apply-dictionary-field-key")

    client = FakeApplyClient()
    candidate = _candidate(
        [
            CandidateChange.model_construct(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_ai_review_notes",
                    "column_label": "AI Review Notes",
                    "internal_type": "journal_input",
                    SecretBearingFieldKey(): "must not reach payload",
                },
            )
        ]
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == UPDATE_SET_APPLY_CHANGE_FIELDS_NON_JSON_DIAGNOSTIC
    assert client.fetches == []
    assert client.upserts == []
    assert "SecretBearingFieldKey" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "legacy-apply-dictionary-field-key" not in diagnostic


def test_apply_candidate_rejects_form_change_field_key_string_subclass() -> None:
    class SecretBearingFieldKey(str):
        pass

    client = FakeApplyClient()
    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_release_summary",
                    "column_label": "Release Summary",
                    "internal_type": "string",
                },
            ),
            CandidateChange.model_construct(
                table="sys_ui_form",
                operation="update",
                fields={
                    "field_name": "u_release_summary",
                    "form_section_name": "Notes",
                    SecretBearingFieldKey(
                        "client_secret=legacy-apply-form-field-key-subclass"
                    ): "must not reach planning",
                },
            ),
        ]
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == UPDATE_SET_APPLY_CHANGE_FIELDS_NON_JSON_DIAGNOSTIC
    assert client.fetches == []
    assert client.upserts == []
    assert "SecretBearingFieldKey" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "legacy-apply-form-field-key-subclass" not in diagnostic


def test_apply_candidate_rejects_change_table_string_subclass() -> None:
    class SecretBearingChangeTable(str):
        pass

    client = FakeApplyClient()
    candidate = _candidate(
        [
            CandidateChange.model_construct(
                table=SecretBearingChangeTable(
                    "sys_dictionary-client_secret=legacy-apply-table-subclass"
                ),
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

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == UPDATE_SET_APPLY_CHANGE_IDENTIFIER_NON_JSON_DIAGNOSTIC
    assert client.fetches == []
    assert client.upserts == []
    assert "SecretBearingChangeTable" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "legacy-apply-table-subclass" not in diagnostic


def test_apply_candidate_rejects_change_table_object_before_dictionary_discovery() -> None:
    class SecretBearingChangeTable:
        def __eq__(self, other: object) -> bool:
            raise RuntimeError("client_secret=legacy-apply-table-eq")

    client = FakeApplyClient()
    candidate = _candidate(
        [
            CandidateChange.model_construct(
                table=SecretBearingChangeTable(),
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

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == UPDATE_SET_APPLY_CHANGE_IDENTIFIER_NON_JSON_DIAGNOSTIC
    assert client.fetches == []
    assert client.upserts == []
    assert "SecretBearingChangeTable" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "legacy-apply-table-eq" not in diagnostic


def test_apply_candidate_rejects_change_operation_string_subclass() -> None:
    class SecretBearingChangeOperation(str):
        pass

    client = FakeApplyClient()
    candidate = _candidate(
        [
            CandidateChange.model_construct(
                table="sys_dictionary",
                operation=SecretBearingChangeOperation(
                    "insert-client_secret=legacy-apply-operation-subclass"
                ),
                fields={
                    "name": "rm_story",
                    "element": "u_ai_review_notes",
                    "column_label": "AI Review Notes",
                    "internal_type": "journal_input",
                },
            )
        ]
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == UPDATE_SET_APPLY_CHANGE_IDENTIFIER_NON_JSON_DIAGNOSTIC
    assert client.fetches == []
    assert client.upserts == []
    assert "SecretBearingChangeOperation" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "legacy-apply-operation-subclass" not in diagnostic


def test_apply_candidate_places_known_story_field_below_description_by_default() -> None:
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

    assert result.applied_change_count == 3
    assert [upsert["table"] for upsert in client.upserts] == [
        "sys_user_preference",
        "sys_dictionary",
        "sys_ui_element",
        "sys_ui_element",
        "sys_ui_section",
        "sys_ui_element",
        "sys_ui_element",
        "sys_ui_section",
    ]
    assert client.upserts[3]["lookup"] == {
        "name": "rm_story",
        "element": "u_ai_review_notes",
        "sys_ui_section": "main-section-sys-id",
    }
    assert client.upserts[6]["lookup"] == {
        "name": "rm_story",
        "element": "u_ai_review_notes",
        "sys_ui_section": "scrum-main-section-sys-id",
    }


def test_apply_candidate_places_description_anchored_field_on_all_main_story_views() -> None:
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
                    "table": "rm_story",
                    "field": "u_ai_review_notes",
                    "position_hint": "Notes section below Description",
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

    assert result.applied_change_count == 3
    assert {
        "table": "sys_ui_section",
        "lookup": {"name": "rm_story"},
        "fields": ["sys_id", "name", "caption", "view", "sys_user"],
        "limit": 100,
    } in client.fetches
    assert {
        "table": "sys_ui_element",
        "lookup": {"name": "rm_story", "element": "description"},
        "fields": ["sys_id", "element", "position", "sys_ui_section", "sys_user"],
        "limit": 50,
    } not in client.fetches
    assert client.upserts[2:] == [
        {
            "table": "sys_ui_element",
            "lookup": {"sys_id": "acceptance-element-sys-id"},
            "fields": {"position": "5"},
        },
        {
            "table": "sys_ui_element",
            "lookup": {
                "name": "rm_story",
                "element": "u_ai_review_notes",
                "sys_ui_section": "main-section-sys-id",
            },
            "fields": {
                "name": "rm_story",
                "element": "u_ai_review_notes",
                "sys_ui_section": "main-section-sys-id",
                "position": "4",
            },
        },
        {
            "table": "sys_ui_section",
            "lookup": {"sys_id": "main-section-sys-id"},
            "fields": {"caption": ""},
        },
        {
            "table": "sys_ui_element",
            "lookup": {"sys_id": "scrum-acceptance-element-sys-id"},
            "fields": {"position": "21"},
        },
        {
            "table": "sys_ui_element",
            "lookup": {
                "name": "rm_story",
                "element": "u_ai_review_notes",
                "sys_ui_section": "scrum-main-section-sys-id",
            },
            "fields": {
                "name": "rm_story",
                "element": "u_ai_review_notes",
                "sys_ui_section": "scrum-main-section-sys-id",
                "position": "20",
            },
        },
        {
            "table": "sys_ui_section",
            "lookup": {"sys_id": "scrum-main-section-sys-id"},
            "fields": {"caption": ""},
        },
    ]


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

    assert client.upserts[-2]["lookup"] == {
        "name": "rm_story",
        "element": "u_ai_review_notes",
        "sys_ui_section": "scrum-main-section-sys-id",
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
                    "element": "u_release_summary",
                    "column_label": "Release Summary",
                    "internal_type": "string",
                },
            ),
            CandidateChange(
                table="sys_ui_form",
                operation="update",
                fields={
                    "field_name": "u_release_summary",
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

    assert client.upserts[-2]["lookup"] == {
        "name": "rm_story",
        "element": "u_release_summary",
        "sys_ui_section": "notes-section-sys-id",
    }


def test_apply_candidate_rejects_named_form_section_missing_sys_id() -> None:
    class MissingNamedSectionSysIdClient(FakeApplyClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            if table == "sys_ui_section" and lookup == {
                "name": "rm_story",
                "caption": "Notes",
            }:
                return [{"caption": "Notes"}]
            return super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )

    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_release_summary",
                    "column_label": "Release Summary",
                    "internal_type": "string",
                },
            ),
            CandidateChange(
                table="sys_ui_form",
                operation="update",
                fields={
                    "field_name": "u_release_summary",
                    "form_section_name": "Notes",
                },
            ),
        ]
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=MissingNamedSectionSysIdClient(),
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    assert str(exc_info.value) == UPDATE_SET_APPLY_METADATA_MISSING_DIAGNOSTIC


def test_apply_candidate_rejects_section_records_collection_subclass_without_leak() -> None:
    class SecretBearingSections(list[dict[str, Any]]):
        def __len__(self) -> int:
            raise RuntimeError("client_secret=update-set-apply-section-records-len")

        def __iter__(self) -> Any:
            raise RuntimeError("client_secret=update-set-apply-section-records-iter")

    class SectionRecordsSubclassClient(FakeApplyClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            if table == "sys_ui_section" and lookup == {
                "name": "rm_story",
                "caption": "Notes",
            }:
                return SecretBearingSections(
                    [{"sys_id": "notes-section-sys-id", "caption": "Notes"}]
                )
            return super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )

    client = SectionRecordsSubclassClient()
    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_release_summary",
                    "column_label": "Release Summary",
                    "internal_type": "string",
                },
            ),
            CandidateChange(
                table="sys_ui_form",
                operation="update",
                fields={
                    "field_name": "u_release_summary",
                    "form_section_name": "Notes",
                },
            ),
        ]
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == UPDATE_SET_APPLY_RECORDS_NON_JSON_DIAGNOSTIC
    assert client.upserts == []
    assert "SecretBearingSections" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "update-set-apply-section-records-len" not in diagnostic
    assert "update-set-apply-section-records-iter" not in diagnostic


def test_apply_candidate_rejects_named_form_section_non_json_sys_id_without_leak() -> None:
    class SecretBearingSectionSysId:
        def __str__(self) -> str:
            return "leaked-update-set-apply-section-secret"

    class NonJsonNamedSectionSysIdClient(FakeApplyClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            if table == "sys_ui_section" and lookup == {
                "name": "rm_story",
                "caption": "Notes",
            }:
                return [{"sys_id": SecretBearingSectionSysId(), "caption": "Notes"}]
            return super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )

    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_release_summary",
                    "column_label": "Release Summary",
                    "internal_type": "string",
                },
            ),
            CandidateChange(
                table="sys_ui_form",
                operation="update",
                fields={
                    "field_name": "u_release_summary",
                    "form_section_name": "Notes",
                },
            ),
        ]
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=NonJsonNamedSectionSysIdClient(),
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    message = str(exc_info.value)
    assert message == UPDATE_SET_APPLY_METADATA_NON_JSON_DIAGNOSTIC
    assert "SecretBearingSectionSysId" not in message
    assert "leaked-update-set-apply-section-secret" not in message


def test_apply_candidate_rejects_form_element_non_json_position_without_leak() -> None:
    class SecretBearingPosition:
        def __str__(self) -> str:
            return "leaked-update-set-apply-position-secret"

    class NonJsonFormElementPositionClient(FakeApplyClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            if table == "sys_ui_element" and lookup == {
                "name": "rm_story",
                "sys_ui_section": "notes-section-sys-id",
            }:
                return [
                    {
                        "sys_id": "work-notes-element-sys-id",
                        "element": "work_notes",
                        "position": SecretBearingPosition(),
                    }
                ]
            return super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )

    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_release_summary",
                    "column_label": "Release Summary",
                    "internal_type": "string",
                },
            ),
            CandidateChange(
                table="sys_ui_form",
                operation="update",
                fields={
                    "field_name": "u_release_summary",
                    "form_section_name": "Notes",
                },
            ),
        ]
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=NonJsonFormElementPositionClient(),
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    message = str(exc_info.value)
    assert message == UPDATE_SET_APPLY_METADATA_NON_JSON_DIAGNOSTIC
    assert "SecretBearingPosition" not in message
    assert "leaked-update-set-apply-position-secret" not in message


def test_apply_candidate_rejects_form_element_invalid_position_without_leak() -> None:
    class InvalidFormElementPositionClient(FakeApplyClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            if table == "sys_ui_element" and lookup == {
                "name": "rm_story",
                "sys_ui_section": "notes-section-sys-id",
            }:
                return [
                    {
                        "sys_id": "work-notes-element-sys-id",
                        "element": "work_notes",
                        "position": "leaked-update-set-apply-position-secret",
                    }
                ]
            return super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )

    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_release_summary",
                    "column_label": "Release Summary",
                    "internal_type": "string",
                },
            ),
            CandidateChange(
                table="sys_ui_form",
                operation="update",
                fields={
                    "field_name": "u_release_summary",
                    "form_section_name": "Notes",
                },
            ),
        ]
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=InvalidFormElementPositionClient(),
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    message = str(exc_info.value)
    assert message == UPDATE_SET_APPLY_POSITION_INVALID_DIAGNOSTIC
    assert "leaked-update-set-apply-position-secret" not in message


def test_apply_candidate_rejects_section_view_non_json_value_without_leak() -> None:
    class SecretBearingViewValue:
        def __str__(self) -> str:
            return "leaked-update-set-apply-view-secret"

    class NonJsonSectionViewClient(FakeApplyClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            if table == "sys_ui_section" and lookup == {"name": "rm_story"}:
                return [
                    {
                        "sys_id": "main-section-sys-id",
                        "name": "rm_story",
                        "caption": "",
                        "view": {
                            "display_value": SecretBearingViewValue(),
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

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=NonJsonSectionViewClient(),
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    message = str(exc_info.value)
    assert message == UPDATE_SET_APPLY_METADATA_NON_JSON_DIAGNOSTIC
    assert "SecretBearingViewValue" not in message
    assert "leaked-update-set-apply-view-secret" not in message


def test_apply_candidate_rejects_section_view_dict_subclass_without_leak() -> None:
    class SecretBearingViewReference(dict[str, str]):
        def get(self, key: str, default: Any = None) -> Any:
            raise RuntimeError("client_secret=update-set-apply-view-reference")

    class HostileSectionViewClient(FakeApplyClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            if table == "sys_ui_section" and lookup == {"name": "rm_story"}:
                return [
                    {
                        "sys_id": "main-section-sys-id",
                        "name": "rm_story",
                        "caption": "",
                        "view": SecretBearingViewReference(
                            {
                                "display_value": "Default view",
                                "value": "Default view",
                            }
                        ),
                        "sys_user": "",
                    }
                ]
            return super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )

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

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=HostileSectionViewClient(),
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    message = str(exc_info.value)
    assert message == UPDATE_SET_APPLY_METADATA_NON_JSON_DIAGNOSTIC
    assert exc_info.value.__cause__ is None
    assert "SecretBearingViewReference" not in message
    assert "client_secret" not in message
    assert "update-set-apply-view-reference" not in message


def test_apply_candidate_rejects_form_element_non_json_element_without_leak() -> None:
    class SecretBearingElementName:
        def __str__(self) -> str:
            return "leaked-update-set-apply-element-secret"

    class NonJsonFormElementNameClient(FakeApplyClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            if table == "sys_ui_element" and lookup == {
                "name": "rm_story",
                "sys_ui_section": "notes-section-sys-id",
            }:
                return [
                    {
                        "sys_id": "work-notes-element-sys-id",
                        "element": SecretBearingElementName(),
                        "position": "0",
                    }
                ]
            return super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )

    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_release_summary",
                    "column_label": "Release Summary",
                    "internal_type": "string",
                },
            ),
            CandidateChange(
                table="sys_ui_form",
                operation="update",
                fields={
                    "field_name": "u_release_summary",
                    "form_section_name": "Notes",
                },
            ),
        ]
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=NonJsonFormElementNameClient(),
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    message = str(exc_info.value)
    assert message == UPDATE_SET_APPLY_METADATA_NON_JSON_DIAGNOSTIC
    assert "SecretBearingElementName" not in message
    assert "leaked-update-set-apply-element-secret" not in message


def test_apply_candidate_rejects_form_element_string_subclass_metadata() -> None:
    class SecretBearingElementName(str):
        pass

    class SubclassFormElementNameClient(FakeApplyClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            if table == "sys_ui_element" and lookup == {
                "name": "rm_story",
                "sys_ui_section": "notes-section-sys-id",
            }:
                return [
                    {
                        "sys_id": "work-notes-element-sys-id",
                        "element": SecretBearingElementName(
                            "leaked-update-set-apply-element-subclass-secret"
                        ),
                        "position": "0",
                    }
                ]
            return super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )

    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_release_summary",
                    "column_label": "Release Summary",
                    "internal_type": "string",
                },
            ),
            CandidateChange(
                table="sys_ui_form",
                operation="update",
                fields={
                    "field_name": "u_release_summary",
                    "form_section_name": "Notes",
                },
            ),
        ]
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=SubclassFormElementNameClient(),
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    message = str(exc_info.value)
    assert message == UPDATE_SET_APPLY_METADATA_NON_JSON_DIAGNOSTIC
    assert "SecretBearingElementName" not in message
    assert "leaked-update-set-apply-element-subclass-secret" not in message


def test_apply_candidate_rejects_form_section_candidate_field_without_leak() -> None:
    class SecretBearingSectionName:
        def __str__(self) -> str:
            return "leaked-update-set-apply-section-candidate-secret"

    client = FakeApplyClient()
    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_release_summary",
                    "column_label": "Release Summary",
                    "internal_type": "string",
                },
            ),
            CandidateChange(
                table="sys_ui_form",
                operation="update",
                fields={
                    "field_name": "u_release_summary",
                    "form_section_name": SecretBearingSectionName(),
                },
            ),
        ]
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    message = str(exc_info.value)
    assert message == UPDATE_SET_APPLY_CANDIDATE_FIELD_NON_JSON_DIAGNOSTIC
    assert "SecretBearingSectionName" not in message
    assert "leaked-update-set-apply-section-candidate-secret" not in message
    assert all(fetch["table"] != "sys_ui_section" for fetch in client.fetches)


def test_apply_candidate_rejects_dictionary_element_candidate_field_without_leak() -> None:
    class SecretBearingDictionaryElement:
        def __str__(self) -> str:
            return "u_leaked_update_set_apply_dictionary_element_secret"

    client = FakeApplyClient()
    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": SecretBearingDictionaryElement(),
                    "column_label": "Release Summary",
                    "internal_type": "string",
                },
            )
        ]
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    message = str(exc_info.value)
    assert message == UPDATE_SET_APPLY_CANDIDATE_FIELD_NON_JSON_DIAGNOSTIC
    assert "SecretBearingDictionaryElement" not in message
    assert "u_leaked_update_set_apply_dictionary_element_secret" not in message
    assert client.fetches == []
    assert client.upserts == []


def test_apply_candidate_rejects_dictionary_payload_candidate_field_without_leak() -> None:
    class SecretBearingMaxLength:
        def __str__(self) -> str:
            return "leaked-update-set-apply-dictionary-payload-secret"

    client = FakeApplyClient()
    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_release_summary",
                    "column_label": "Release Summary",
                    "internal_type": "string",
                    "max_length": SecretBearingMaxLength(),
                },
            )
        ]
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    message = str(exc_info.value)
    assert message == UPDATE_SET_APPLY_CANDIDATE_FIELD_NON_JSON_DIAGNOSTIC
    assert "SecretBearingMaxLength" not in message
    assert "leaked-update-set-apply-dictionary-payload-secret" not in message
    assert client.fetches == []
    assert client.upserts == []


def test_apply_candidate_rejects_dictionary_string_subclass_candidate_field() -> None:
    class SecretBearingDictionaryElement(str):
        pass

    client = FakeApplyClient()
    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": SecretBearingDictionaryElement(
                        "u_leaked_update_set_apply_dictionary_subclass_secret"
                    ),
                    "column_label": "Release Summary",
                    "internal_type": "string",
                },
            )
        ]
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    message = str(exc_info.value)
    assert message == UPDATE_SET_APPLY_CANDIDATE_FIELD_NON_JSON_DIAGNOSTIC
    assert "SecretBearingDictionaryElement" not in message
    assert "u_leaked_update_set_apply_dictionary_subclass_secret" not in message
    assert client.fetches == []
    assert client.upserts == []


def test_apply_candidate_rejects_form_string_subclass_candidate_field() -> None:
    class SecretBearingFormField(str):
        pass

    client = FakeApplyClient()
    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_release_summary",
                    "column_label": "Release Summary",
                    "internal_type": "string",
                },
            ),
            CandidateChange(
                table="sys_ui_form",
                operation="update",
                fields={
                    "field_name": SecretBearingFormField(
                        "u_leaked_update_set_apply_form_subclass_secret"
                    ),
                    "form_section_name": "Notes",
                },
            ),
        ]
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    message = str(exc_info.value)
    assert message == UPDATE_SET_APPLY_CANDIDATE_FIELD_NON_JSON_DIAGNOSTIC
    assert "SecretBearingFormField" not in message
    assert "u_leaked_update_set_apply_form_subclass_secret" not in message
    assert all(fetch["table"] != "sys_ui_section" for fetch in client.fetches)
    assert client.upserts == []


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
    assert client.upserts[-2]["lookup"] == {
        "name": "rm_story",
        "element": "u_ai_review_notes",
        "sys_ui_section": "scrum-main-section-sys-id",
    }


def test_apply_candidate_normalizes_empty_model_field_alias_values() -> None:
    client = FakeApplyClient()
    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "",
                    "field_name": "u_ai_review_notes",
                    "column_label": "",
                    "field_label": "AI Review Notes",
                    "internal_type": "string",
                },
            )
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
            "internal_type": "string",
        },
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
    assert client.upserts[-2]["lookup"] == {
        "name": "rm_story",
        "element": "u_ai_review_notes",
        "sys_ui_section": "scrum-main-section-sys-id",
    }


def test_apply_candidate_rejects_form_xml_string_subclass_candidate_field() -> None:
    class SecretBearingFormElementsXml(str):
        pass

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
                    "elements": SecretBearingFormElementsXml(
                        "<field name='u_leaked_update_set_apply_xml_subclass_secret' "
                        "section='Notes'/>"
                    ),
                },
            ),
        ]
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    message = str(exc_info.value)
    assert message == UPDATE_SET_APPLY_CANDIDATE_FIELD_NON_JSON_DIAGNOSTIC
    assert "SecretBearingFormElementsXml" not in message
    assert "u_leaked_update_set_apply_xml_subclass_secret" not in message
    assert all(fetch["table"] != "sys_ui_section" for fetch in client.fetches)
    assert client.upserts == []


def test_apply_candidate_rejects_form_placement_candidate_field_without_leak() -> None:
    class SecretBearingPlacement:
        def __str__(self) -> str:
            return "below description leaked-update-set-apply-placement-secret"

    client = FakeApplyClient()
    candidate = _candidate(
        [
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_release_summary",
                    "column_label": "Release Summary",
                    "internal_type": "string",
                },
            ),
            CandidateChange(
                table="sys_ui_form",
                operation="update",
                fields={
                    "field_name": "u_release_summary",
                    "form_section_name": "Notes",
                    "position": SecretBearingPlacement(),
                },
            ),
        ]
    )

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    message = str(exc_info.value)
    assert message == UPDATE_SET_APPLY_CANDIDATE_FIELD_NON_JSON_DIAGNOSTIC
    assert "SecretBearingPlacement" not in message
    assert "leaked-update-set-apply-placement-secret" not in message
    assert all(fetch["table"] != "sys_ui_section" for fetch in client.fetches)
    assert client.upserts == []


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


def test_apply_candidate_rejects_integration_user_record_subclass_without_leak() -> None:
    class SecretBearingUserRecord(dict[str, Any]):
        def get(self, key: object, default: object = None) -> object:
            raise RuntimeError("client_secret=legacy-apply-user-record-get")

    client = FakeApplyClient(
        user_record=SecretBearingUserRecord({"sys_id": "user-sys-id"})
    )
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

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == UPDATE_SET_APPLY_RECORD_NON_JSON_DIAGNOSTIC
    assert client.upserts == []
    assert "SecretBearingUserRecord" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "legacy-apply-user-record-get" not in diagnostic


def test_apply_candidate_rejects_non_json_integration_user_sys_id_without_leak() -> None:
    class SecretBearingUserSysId:
        def __str__(self) -> str:
            return "client_secret=legacy-apply-secret"

    client = FakeApplyClient(user_record={"sys_id": SecretBearingUserSysId()})
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

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == UPDATE_SET_APPLY_LOOKUP_NON_JSON_DIAGNOSTIC
    assert client.upserts == []
    assert "SecretBearingUserSysId" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "legacy-apply-secret" not in diagnostic


def test_apply_candidate_rejects_string_subclass_integration_user_sys_id() -> None:
    class SecretBearingUserSysId(str):
        pass

    client = FakeApplyClient(
        user_record={"sys_id": SecretBearingUserSysId("client_secret=legacy-apply-subclass")}
    )
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

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == UPDATE_SET_APPLY_LOOKUP_NON_JSON_DIAGNOSTIC
    assert client.upserts == []
    assert "SecretBearingUserSysId" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "legacy-apply-subclass" not in diagnostic


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


def test_apply_candidate_rejects_customer_updates_collection_subclass_without_leak() -> None:
    class SecretBearingCustomerUpdates(list[dict[str, Any]]):
        def __bool__(self) -> bool:
            raise RuntimeError("client_secret=update-set-apply-customer-updates-bool")

        def __len__(self) -> int:
            raise RuntimeError("client_secret=update-set-apply-customer-updates-len")

    client = FakeApplyClient(
        customer_updates=SecretBearingCustomerUpdates(
            [{"sys_id": "customer-update-sys-id", "name": "sys_dictionary_rm_story_u_ai"}]
        )
    )
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

    with pytest.raises(ValueError) as exc_info:
        apply_candidate_to_update_set(
            client=client,
            request=UpdateSetApplyRequest(
                update_set_sys_id="update-set-sys-id",
                integration_user_name="jedi.integration",
                candidate=candidate,
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == UPDATE_SET_APPLY_RECORDS_NON_JSON_DIAGNOSTIC
    assert [upsert["table"] for upsert in client.upserts] == [
        "sys_user_preference",
        "sys_dictionary",
    ]
    assert "SecretBearingCustomerUpdates" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "update-set-apply-customer-updates-bool" not in diagnostic
    assert "update-set-apply-customer-updates-len" not in diagnostic
