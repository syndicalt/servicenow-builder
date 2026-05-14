from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from jedi_devproject.fulfillment_worker import FulfillmentPersistedArtifact
from jedi_devproject.model_fulfillment import (
    ModelCandidateFulfillmentConfig,
    model_candidate_fulfillment_handler,
)
from jedi_devproject.models import DataClassification, ProviderPolicy, ProviderStatus, Story
from jedi_devproject.operational_store import FulfillmentJobRecord
from jedi_devproject.rag import Document, RagDomain, SpecializedRags
from jedi_devproject.safety import AllowlistPolicy, StoryType
from jedi_devproject.servicenow import StoryDictionaryField, StoryStateChoice


class FakeModelClient:
    def __init__(self) -> None:
        self.updated_fields: list[dict[str, object]] = []
        self.upserts: list[dict[str, object]] = []
        self.fetches: list[dict[str, object]] = []
        self.imports: list[dict[str, str]] = []

    def fetch_stories(
        self,
        sysparm_query: str | None = None,
        *,
        limit: int = 100,
    ) -> list[Story]:
        return [
            Story(
                sys_id="story-sys-id",
                number="STRY0010013",
                short_description="Add AI Review Notes field to Story form",
                description=(
                    "Add a new custom field to the rm_story table named "
                    "u_ai_review_notes and place it on the Story form below "
                    "Description."
                ),
                acceptance_criteria=(
                    "The AI Review Notes field stores implementation review notes "
                    "on the Story record."
                ),
                story_points=3,
                priority=4,
                state="Work in Progress",
                data_classification=DataClassification.PUBLIC,
            )
        ]

    def fetch_story_state_choices(self) -> list[StoryStateChoice]:
        return [
            StoryStateChoice(label="Ready", value="1", sequence=100),
            StoryStateChoice(label="Work in Progress", value="2", sequence=200),
            StoryStateChoice(label="Ready for Testing", value="-7", sequence=300),
        ]

    def fetch_story_dictionary_fields(self) -> list[StoryDictionaryField]:
        return []

    def update_story_fields(self, story_sys_id: str, fields: dict[str, object]) -> None:
        self.updated_fields.append({"story_sys_id": story_sys_id, "fields": fields})

    def upsert_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: dict[str, object],
    ) -> dict[str, object]:
        self.upserts.append({"table": table, "lookup": lookup, "fields": fields})
        return {"sys_id": "update-set-sys-id", "name": fields["name"]}

    def fetch_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
    ) -> dict[str, object] | None:
        self.fetches.append({"table": table, "lookup": lookup})
        if table == "sys_user":
            return {"sys_id": "user-sys-id"}
        return None

    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        self.fetches.append({"table": table, "lookup": lookup, "fields": fields, "limit": limit})
        if table == "sys_remote_update_set":
            return [
                {
                    "sys_id": "remote-update-set-sys-id",
                    "name": "JEDI STRY0010013 - AI Candidate",
                }
            ]
        if table == "sys_update_xml":
            return [{"sys_id": "customer-update-sys-id"}]
        return []

    def import_update_set_xml(
        self,
        *,
        service_id: str,
        update_set_xml: str,
    ) -> dict[str, object]:
        self.imports.append({"service_id": service_id, "update_set_xml": update_set_xml})
        return {"status_code": 201, "result": {"status": "imported"}}


class RecordingModelProvider:
    def __init__(self, response: dict[str, Any] | None = None) -> None:
        self.response = response or {
            "changes": [
                {
                    "table": "sys_dictionary",
                    "operation": "insert",
                    "fields": {
                        "name": "rm_story",
                        "element": "u_ai_review_notes",
                        "column_label": "AI Review Notes",
                        "internal_type": "journal_input",
                    },
                }
            ],
            "test_plan": ["Confirm AI Review Notes is available for review notes."],
            "rollback_notes": ["Remove u_ai_review_notes from rm_story."],
        }
        self.payloads: list[dict[str, Any]] = []

    def generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.payloads.append(payload)
        return self.response


def _job() -> FulfillmentJobRecord:
    return FulfillmentJobRecord(
        job_id="job-evt-001",
        event_id="evt-001",
        story_number="STRY0010013",
        status="running",
        attempt_count=1,
        created_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
        updated_at=datetime(2026, 5, 13, 15, 1, tzinfo=UTC),
        locked_by="worker-1",
        locked_at=datetime(2026, 5, 13, 15, 1, tzinfo=UTC),
        last_error=None,
    )


def _policy() -> AllowlistPolicy:
    return AllowlistPolicy(
        story_types={StoryType.DICTIONARY_FORM},
        tables={"sys_dictionary", "sys_ui_form"},
        operations={"insert", "update"},
        max_points=3,
    )


def _provider_policy() -> ProviderPolicy:
    return ProviderPolicy(
        provider_id="openai-chatgpt",
        deployment_boundary="railway-dev-pdi",
        authorization_level="explicit-dev-evaluation",
        allowed_data_classes={DataClassification.PUBLIC},
        allowed_tasks={"generate_implementation_candidate"},
        max_context_policy="implementation-packet-v1",
        retention_policy="no-training-dev-evaluation",
        status=ProviderStatus.APPROVED,
    )


def _rags() -> SpecializedRags:
    return SpecializedRags.from_documents(
        [
            Document(
                domain=RagDomain.SERVICENOW_PLATFORM,
                source="servicenow/dictionary",
                content="rm_story custom field work uses sys_dictionary.",
                version="test",
            ),
            Document(
                domain=RagDomain.INSTANCE_METADATA,
                source="instance/rm_story",
                content="rm_story supports u_ai_review_notes for review notes.",
                version="test",
            ),
            Document(
                domain=RagDomain.PROJECT_CONTEXT,
                source="project/ai-review-notes",
                content="AI Review Notes supports implementation review.",
                version="test",
            ),
            Document(
                domain=RagDomain.COMPLIANCE,
                source="compliance/evaluation",
                content="Public PDI story context may be used for dev evaluation.",
                version="test",
            ),
        ]
    )


def test_model_candidate_handler_returns_packet_candidate_payloads_and_work_note(
    tmp_path: Path,
) -> None:
    client = FakeModelClient()
    provider = RecordingModelProvider()
    handler = model_candidate_fulfillment_handler(
        client=client,
        config=ModelCandidateFulfillmentConfig(
            policy=_policy(),
            provider_policy=_provider_policy(),
            rags=_rags(),
            provider=provider,
            instance_url="https://dev205693.service-now.com",
        ),
    )

    result = handler(_job())

    assert result.message == "Implementation candidate generated for STRY0010013"
    assert [artifact.artifact_kind for artifact in result.artifacts] == [
        "implementation_packet",
        "implementation_candidate",
    ]
    assert result.artifacts[0].schema_version == "implementation-packet-v1"
    assert result.artifacts[1].schema_version == "implementation-candidate-v1"
    packet = result.artifacts[0].payload_json
    candidate = result.artifacts[1].payload_json
    assert packet is not None
    assert candidate is not None
    assert packet["provider_id"] == "openai-chatgpt"
    assert packet["story"]["number"] == "STRY0010013"
    assert "story-sys-id" not in str(packet)
    assert candidate["status"] == "Ready for Review"
    assert candidate["changes"][0]["fields"]["element"] == "u_ai_review_notes"
    assert provider.payloads[0]["task"] == "generate_implementation_candidate"
    assert client.updated_fields == []
    assert result.after_artifacts_persisted is not None

    result.after_artifacts_persisted(
        [
            FulfillmentPersistedArtifact(
                artifact_kind="implementation_packet",
                path="db://artifact_blobs/1",
                sha256="a" * 64,
                artifact_id=1,
            ),
            FulfillmentPersistedArtifact(
                artifact_kind="implementation_candidate",
                path="db://artifact_blobs/2",
                sha256="b" * 64,
                artifact_id=2,
            ),
        ]
    )

    assert client.upserts == []
    assert client.imports[0]["service_id"] == "jedi_update_set_import"
    assert "sys_dictionary_rm_story_u_ai_review_notes" in client.imports[0]["update_set_xml"]
    assert client.updated_fields == [
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


def test_model_candidate_handler_imports_remote_update_set_without_local_apply(
    tmp_path: Path,
) -> None:
    client = FakeModelClient()
    provider = RecordingModelProvider()
    handler = model_candidate_fulfillment_handler(
        client=client,
        config=ModelCandidateFulfillmentConfig(
            policy=_policy(),
            provider_policy=_provider_policy(),
            rags=_rags(),
            provider=provider,
            instance_url="https://dev205693.service-now.com",
            apply_update_set_changes=True,
            update_set_user_name="jedi.integration",
        ),
    )

    result = handler(_job())
    assert result.after_artifacts_persisted is not None

    result.after_artifacts_persisted(
        [
            FulfillmentPersistedArtifact(
                artifact_kind="implementation_candidate",
                path="db://artifact_blobs/2",
                sha256="b" * 64,
                artifact_id=2,
            ),
        ]
    )

    assert client.upserts == []
    assert len(client.imports) == 1
    assert all(upsert["table"] != "sys_user_preference" for upsert in client.upserts)
    assert all(upsert["table"] != "sys_dictionary" for upsert in client.upserts)
    assert all(fetch["table"] != "sys_update_xml" for fetch in client.fetches)
    work_note_fields = cast(dict[str, str], client.updated_fields[-1]["fields"])
    assert "retrieved Update Set handoff created" in work_note_fields["work_notes"]
    assert work_note_fields["state"] == "-7"
    assert work_note_fields["u_ai_status"] == "Ready for Testing"


def test_model_candidate_handler_fails_closed_for_invalid_model_response(
    tmp_path: Path,
) -> None:
    client = FakeModelClient()
    provider = RecordingModelProvider(
        response={
            "changes": [
                {
                    "table": "sys_user",
                    "operation": "update",
                    "fields": {"name": "bad"},
                }
            ],
            "test_plan": ["Bad response should not pass."],
            "rollback_notes": ["No-op."],
        }
    )
    handler = model_candidate_fulfillment_handler(
        client=client,
        config=ModelCandidateFulfillmentConfig(
            policy=_policy(),
            provider_policy=_provider_policy(),
            rags=_rags(),
            provider=provider,
            instance_url="https://dev205693.service-now.com",
        ),
    )

    try:
        handler(_job())
    except ValueError as exc:
        assert "table not allowed: sys_user" in str(exc)
    else:
        raise AssertionError("invalid model response was accepted")

    assert client.updated_fields == []
    assert list(tmp_path.rglob("*.json")) == []
