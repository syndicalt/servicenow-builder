from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from jedi_devproject.fulfillment_worker import FulfillmentPersistedArtifact
from jedi_devproject.model_fulfillment import (
    ModelCandidateFulfillmentConfig,
    model_candidate_fulfillment_handler,
)
from jedi_devproject.models import (
    CandidateStatus,
    DataClassification,
    ProviderPolicy,
    ProviderStatus,
    Story,
)
from jedi_devproject.operational_store import FulfillmentJobRecord
from jedi_devproject.rag import Document, RagDomain, SpecializedRags
from jedi_devproject.safety import AllowlistPolicy, StoryType
from jedi_devproject.servicenow import StoryDictionaryField, StoryStateChoice


class FakeModelClient:
    def __init__(self, *, story: Story | None = None) -> None:
        self.story = story
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
        if self.story is not None:
            return [self.story]
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
        if table == "sys_db_object":
            target_table = lookup["name"]
            return [{"name": target_table, "label": target_table.replace("_", " ").title()}]
        if table == "sys_dictionary":
            return [
                {
                    "element": "description",
                    "column_label": "Description",
                    "internal_type": "string",
                    "max_length": "4000",
                }
            ]
        if table == "sys_ui_section":
            target_table = lookup["name"]
            return [
                {
                    "sys_id": f"{target_table}-main-section",
                    "name": target_table,
                    "caption": "",
                    "view": {"display_value": "Default view", "value": "default"},
                }
            ]
        if table == "sys_ui_element":
            return [{"sys_id": "description-element", "element": "description", "position": "2"}]
        if table == "sys_security_acl":
            return []
        if table == "sys_script":
            return []
        if table == "sys_script_client":
            return []
        if table == "sys_ui_policy":
            return []
        if table == "sys_hub_flow":
            return [{"sys_id": "flow-sys-id", "name": "Incident Triage", "active": "true"}]
        if table == "sys_script_include":
            return []
        if table == "cmdb_ci":
            return []
        if table == "sys_rest_message":
            return []
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
                },
                {
                    "table": "sys_ui_form",
                    "operation": "update",
                    "fields": {
                        "name": "rm_story",
                        "field_order": "u_ai_review_notes",
                        "placement_anchor": "description",
                        "placement_position": "below",
                    },
                },
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
                content=(
                    "Public PDI story context may be used for dev evaluation. "
                    "Incident field requests stay in the regulated review workflow."
                ),
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
        "instance_context_bundle",
        "implementation_packet",
        "implementation_candidate",
    ]
    assert result.artifacts[0].schema_version == "servicenow-surface-context-v1"
    assert result.artifacts[1].schema_version == "implementation-packet-v1"
    assert result.artifacts[2].schema_version == "implementation-candidate-v1"
    context_bundle = result.artifacts[0].payload_json
    packet = result.artifacts[1].payload_json
    candidate = result.artifacts[2].payload_json
    assert context_bundle is not None
    assert packet is not None
    assert candidate is not None
    assert context_bundle["target_table"] == "rm_story"
    assert packet["provider_id"] == "openai-chatgpt"
    assert packet["instance_context_bundle"]["target_table"] == "rm_story"
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
                artifact_kind="instance_context_bundle",
                path="db://artifact_blobs/0",
                sha256="0" * 64,
                artifact_id=0,
            ),
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
                artifact_kind="instance_context_bundle",
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
    assert len(client.imports) == 1
    assert all(upsert["table"] != "sys_user_preference" for upsert in client.upserts)
    assert all(upsert["table"] != "sys_dictionary" for upsert in client.upserts)
    assert all(fetch["table"] != "sys_update_xml" for fetch in client.fetches)
    work_note_fields = cast(dict[str, str], client.updated_fields[-1]["fields"])
    assert "retrieved Update Set handoff created" in work_note_fields["work_notes"]
    assert work_note_fields["state"] == "-7"
    assert work_note_fields["u_ai_status"] == "Ready for Testing"


def test_model_candidate_handler_builds_incident_candidate_after_instance_discovery(
    tmp_path: Path,
) -> None:
    client = FakeModelClient(
        story=Story(
            sys_id="story-sys-id",
            number="STRY0010001",
            short_description="Add a New Field to the Incident Form",
            description=(
                "As an incident manager, I would like a new field added to the "
                "Incident form.\n\n- Field Name: Antics\n- Field Type: String\n"
                "- Length: 4000"
            ),
            acceptance_criteria=(
                "- A new field labeled Antics exists on the incident form.\n"
                "- The field is placed below the Description field.\n"
                "- All incident users are able to read and write to the Antics field."
            ),
            story_points=2,
            priority=4,
            state="Work in Progress",
            data_classification=DataClassification.PUBLIC,
        )
    )
    provider = RecordingModelProvider(
        response={
            "changes": [
                {
                    "table": "sys_dictionary",
                    "operation": "insert",
                    "fields": {
                        "name": "incident",
                        "element": "u_antics",
                        "column_label": "Antics",
                        "internal_type": "string",
                        "max_length": "4000",
                    },
                },
                {
                    "table": "sys_ui_form",
                    "operation": "update",
                    "fields": {
                        "name": "incident",
                        "field_order": "u_antics",
                        "placement_anchor": "description",
                        "placement_position": "below",
                    },
                },
            ],
            "test_plan": ["Confirm Antics is visible below Description on the Incident form."],
            "rollback_notes": ["Remove incident.u_antics and its form placement."],
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

    result = handler(_job().model_copy(update={"story_number": "STRY0010001"}))

    assert result.artifacts[1].payload_json is not None
    assert result.artifacts[2].payload_json is not None
    candidate = result.artifacts[2].payload_json
    assert candidate["status"] == CandidateStatus.READY_FOR_REVIEW.value
    assert candidate["changes"][0]["fields"]["name"] == "incident"
    assert candidate["changes"][0]["fields"]["element"] == "u_antics"
    assert provider.payloads
    assert provider.payloads[0]["instance_context"]["target_table"] == "incident"
    assert {fetch["table"] for fetch in client.fetches} >= {
        "sys_db_object",
        "sys_dictionary",
        "sys_ui_section",
        "sys_ui_element",
        "sys_security_acl",
    }
    assert result.after_artifacts_persisted is not None


def test_model_candidate_handler_blocks_model_when_required_surface_context_missing() -> None:
    class MissingFlowClient(FakeModelClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, object]]:
            if table == "sys_hub_flow":
                self.fetches.append(
                    {"table": table, "lookup": lookup, "fields": fields, "limit": limit}
                )
                return []
            return super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )

    client = MissingFlowClient(
        story=Story(
            sys_id="story-sys-id",
            number="STRY0010106",
            short_description="Add a New Field to the Incident Form after checking Flow",
            description=(
                "As an incident manager, I would like a new field added to the "
                "Incident form, but first inspect the Incident Flow for triage "
                "dependencies.\n\n- Field Name: Escalation Notes\n"
                "- Field Type: String\n- Length: 4000"
            ),
            acceptance_criteria="The field exists and does not conflict with Flow logic.",
            story_points=2,
            priority=4,
            state="Work in Progress",
            data_classification=DataClassification.PUBLIC,
        )
    )
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

    result = handler(_job().model_copy(update={"story_number": "STRY0010106"}))

    assert provider.payloads == []
    assert [artifact.artifact_kind for artifact in result.artifacts] == [
        "instance_context_bundle",
        "implementation_packet",
        "implementation_candidate",
    ]
    assert result.artifacts[0].payload_json is not None
    assert result.artifacts[0].payload_json["missing_required_surfaces"] == ["flows"]
    assert result.artifacts[2].payload_json is not None
    assert result.artifacts[2].payload_json["status"] == CandidateStatus.MANUAL_BUILD.value
    assert "context_insufficient:flows" in result.artifacts[2].payload_json["eligibility_reasons"]


def test_model_fulfillment_writes_needs_clarification_feedback() -> None:
    client = FakeModelClient(
        story=Story(
            sys_id="story-sys-id",
            number="STRY0090001",
            short_description="Add a new field",
            description="Add a string field named Comments below Description.",
            acceptance_criteria="The field is visible on the form.",
            story_points=2,
            priority=4,
            state="Work in Progress",
            data_classification=DataClassification.PUBLIC,
        )
    )
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

    result = handler(_job().model_copy(update={"story_number": "STRY0090001"}))
    assert result.after_artifacts_persisted is not None
    result.after_artifacts_persisted(
        [
            FulfillmentPersistedArtifact(
                artifact_kind="implementation_candidate",
                path="db://artifact_blobs/90",
                sha256="c" * 64,
                artifact_id=90,
            )
        ]
    )

    assert provider.payloads == []
    assert client.imports == []
    feedback_fields = cast(dict[str, str], client.updated_fields[-1]["fields"])
    assert feedback_fields["u_ai_status"] == "Needs Clarification"
    assert "target table" in feedback_fields["work_notes"]


def test_model_fulfillment_work_note_names_missing_surface_context() -> None:
    candidate = cast(
        Any,
        type(
            "Candidate",
            (),
            {
                "eligibility_reasons": ["context_insufficient:flows"],
                "status": CandidateStatus.MANUAL_BUILD,
            },
        )(),
    )

    fields = cast(
        dict[str, str],
        __import__(
            "jedi_devproject.model_fulfillment",
            fromlist=["_manual_feedback_fields"],
        )._manual_feedback_fields(
            story_number="STRY0010106",
            candidate=candidate,
            candidate_artifact_ref="db://artifact_blobs/99",
        ),
    )

    assert fields["u_ai_status"] == "Human Review Required"
    assert "Missing ServiceNow context: flows" in fields["work_notes"]


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
