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
            return [
                {
                    "sys_id": "business-rule-sys-id",
                    "name": "Incident Priority Watch",
                    "active": "true",
                    "when": "before",
                    "action_insert": "false",
                    "action_update": "true",
                    "filter_condition": "priority changes",
                    "script": "current.work_notes = 'secret-value';",
                }
            ]
        if table == "sys_script_client":
            return [
                {
                    "sys_id": "client-script-sys-id",
                    "name": "Incident Category Guard",
                    "active": "true",
                    "type": "onChange",
                    "script": "g_form.setValue('u_token', 'secret-value');",
                }
            ]
        if table == "sys_ui_policy":
            return []
        if table == "sys_hub_flow":
            return [{"sys_id": "flow-sys-id", "name": "Incident Triage", "active": "true"}]
        if table == "sys_hub_trigger_instance" and lookup == {"flow": "flow-sys-id"}:
            return [
                {
                    "sys_id": "trigger-sys-id",
                    "name": "Incident record trigger",
                    "flow": "flow-sys-id",
                    "trigger_type": "record",
                    "trigger_definition": "trigger-definition-sys-id",
                    "display_text": "When Incident is created or updated",
                }
            ]
        if table == "sys_hub_action_instance" and lookup == {"flow": "flow-sys-id"}:
            return [
                {
                    "sys_id": "action-sys-id",
                    "flow": "flow-sys-id",
                    "order": "100",
                    "action_type": "action-type-sys-id",
                    "display_text": "Set assignment group",
                }
            ]
        if table == "sys_hub_flow_logic_instance_v2" and lookup == {"flow": "flow-sys-id"}:
            return [
                {
                    "sys_id": "logic-sys-id",
                    "flow": "flow-sys-id",
                    "order": "200",
                    "logic_definition": "if-definition-sys-id",
                    "display_text": "If category is software",
                }
            ]
        if table == "sys_hub_trigger_input" and lookup == {"model": "trigger-definition-sys-id"}:
            return [
                {
                    "sys_id": "trigger-input-sys-id",
                    "model": "trigger-definition-sys-id",
                    "element": "table",
                    "column_label": "Table",
                    "internal_type": "string",
                }
            ]
        if table == "sys_hub_trigger_output" and lookup == {"model": "trigger-definition-sys-id"}:
            return [
                {
                    "sys_id": "trigger-output-sys-id",
                    "model": "trigger-definition-sys-id",
                    "element": "current",
                    "column_label": "Current record",
                    "internal_type": "reference",
                }
            ]
        if table == "sys_hub_action_input" and lookup == {"model": "action-type-sys-id"}:
            return [
                {
                    "sys_id": "action-input-sys-id",
                    "model": "action-type-sys-id",
                    "element": "assignment_group",
                    "column_label": "Assignment group",
                    "internal_type": "reference",
                    "reference": "sys_user_group",
                }
            ]
        if table == "sys_hub_action_output" and lookup == {"model": "action-type-sys-id"}:
            return [
                {
                    "sys_id": "action-output-sys-id",
                    "model": "action-type-sys-id",
                    "element": "updated_record",
                    "column_label": "Updated record",
                    "internal_type": "reference",
                }
            ]
        if table == "sys_script_include":
            return [
                {
                    "sys_id": "script-include-sys-id",
                    "name": "AssignmentUtils",
                    "active": "true",
                    "api_name": "global.AssignmentUtils",
                    "script": "var password = 'secret-value';",
                }
            ]
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
        tables={
            "sys_dictionary",
            "sys_ui_form",
            "sys_script",
            "sys_script_client",
            "sys_script_include",
            "sys_ui_policy",
            "sys_ui_policy_action",
        },
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
    assert provider.payloads[0]["instance_context"] is None
    assert provider.payloads[0]["instance_context_bundle"]["target_table"] == "incident"
    assert {fetch["table"] for fetch in client.fetches} >= {
        "sys_db_object",
        "sys_dictionary",
        "sys_ui_section",
        "sys_ui_element",
        "sys_security_acl",
    }
    assert result.after_artifacts_persisted is not None


def test_model_candidate_handler_fetches_story_by_sys_id_when_job_has_sys_id() -> None:
    class DuplicateNumberClient(FakeModelClient):
        def fetch_stories(
            self,
            sysparm_query: str | None = None,
            *,
            limit: int = 100,
        ) -> list[Story]:
            self.fetches.append({"table": "rm_story", "lookup": {"query": sysparm_query}})
            if sysparm_query == "sys_id=correct-story-sys-id":
                return [
                    Story(
                        sys_id="correct-story-sys-id",
                        number="STRY0010013",
                        short_description="Create Incident duplicate-safe Client Script",
                        description=(
                            "Create an onChange Client Script on the Incident table for "
                            "the category field. Condition: category changes to software. "
                            "Expected behavior: show an info message. Fields read: category. "
                            "Fields written: none."
                        ),
                        acceptance_criteria="Changing category to software shows the message.",
                        story_points=3,
                        priority=4,
                        state="Work in Progress",
                        data_classification=DataClassification.PUBLIC,
                    )
                ]
            if sysparm_query == "number=STRY0010013":
                return [
                    Story(
                        sys_id="wrong-story-sys-id",
                        number="STRY0010013",
                        short_description="Old unrelated story",
                        description="Old unrelated story that should not be selected.",
                        story_points=3,
                        priority=4,
                        state="Work in Progress",
                        data_classification=DataClassification.PUBLIC,
                    )
                ]
            return []

    client = DuplicateNumberClient()
    provider = RecordingModelProvider(
        response={
            "changes": [
                {
                    "table": "sys_script_client",
                    "operation": "insert",
                    "fields": {
                        "name": "JEDI Duplicate Safe Client Script",
                        "table": "incident",
                        "type": "onChange",
                        "field": "category",
                        "script": (
                            "function onChange(control, oldValue, newValue, isLoading) {"
                            "g_form.addInfoMessage('ok');}"
                        ),
                        "fields_read": ["category"],
                        "fields_written": [],
                    },
                }
            ],
            "test_plan": ["Change category to Software."],
            "rollback_notes": ["Delete the generated Client Script."],
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

    result = handler(
        _job().model_copy(
            update={
                "story_number": "STRY0010013",
                "story_sys_id": "correct-story-sys-id",
            }
        )
    )

    assert result.artifacts[-1].payload_json is not None
    assert result.artifacts[-1].payload_json["changes"][0]["fields"]["name"] == (
        "JEDI Duplicate Safe Client Script"
    )
    assert client.fetches[0]["lookup"] == {"query": "sys_id=correct-story-sys-id"}
    assert all(fetch["lookup"] != {"query": "number=STRY0010013"} for fetch in client.fetches)


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
    assert result.artifacts[0].payload_json["missing_required_surfaces"] == [
        "flows",
        "flow_graph",
    ]
    assert result.artifacts[2].payload_json is not None
    assert result.artifacts[2].payload_json["status"] == CandidateStatus.MANUAL_BUILD.value
    assert "context_insufficient:flows" in result.artifacts[2].payload_json["eligibility_reasons"]
    assert (
        "context_insufficient:flow_graph"
        in result.artifacts[2].payload_json["eligibility_reasons"]
    )


def test_model_candidate_handler_emits_flow_preflight_guidance_artifact() -> None:
    client = FakeModelClient(
        story=Story(
            sys_id="story-sys-id",
            number="STRY0010117",
            short_description="Update Incident Triage Flow",
            description=(
                "Update the Incident Triage Flow Designer flow so new high-impact "
                "incidents post a triage work note before assignment routing."
            ),
            acceptance_criteria=(
                "The existing Flow Designer graph is retrieved for review. "
                "If automated Flow generation is not supported, the worker records "
                "explicit routing guidance instead of creating a retrieved Update Set."
            ),
            story_points=3,
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

    result = handler(_job().model_copy(update={"story_number": "STRY0010117"}))

    assert provider.payloads == []
    assert [artifact.artifact_kind for artifact in result.artifacts] == [
        "instance_context_bundle",
        "flow_preflight_guidance",
        "implementation_packet",
        "implementation_candidate",
    ]
    guidance = result.artifacts[1].payload_json
    candidate = result.artifacts[3].payload_json
    assert guidance is not None
    assert candidate is not None
    assert result.artifacts[1].schema_version == "flow-preflight-guidance-v1"
    assert guidance["schema_version"] == "flow-preflight-guidance-v1"
    assert guidance["story_number"] == "STRY0010117"
    assert guidance["capability"] == "flow_modify"
    assert guidance["readiness_contract_version"] == "flow-builder-readiness-v1"
    assert guidance["ready_for_runtime_generation"] is False
    assert guidance["ready_for_retrieved_update_set_handoff"] is False
    assert guidance["unsupported_reason_codes"] == [
        "flow_builder_not_implemented",
        "runtime_generation_disabled",
        "retrieved_update_set_handoff_disabled",
    ]
    assert guidance["unsupported_reason_guidance"][0]["operator_action"] == (
        "route_to_human_review"
    )
    assert "Flow Designer automation is context/preflight-only" in (
        guidance["unsupported_reason_guidance"][0]["work_note"]
    )
    assert candidate["status"] == CandidateStatus.MANUAL_BUILD.value
    assert "unsupported capability: flow_modify" in candidate["eligibility_reasons"]

    assert result.after_artifacts_persisted is not None
    result.after_artifacts_persisted(
        [
            FulfillmentPersistedArtifact(
                artifact_kind="instance_context_bundle",
                path="db://artifact_blobs/1170",
                sha256="1" * 64,
                artifact_id=1170,
            ),
            FulfillmentPersistedArtifact(
                artifact_kind="flow_preflight_guidance",
                path="db://artifact_blobs/1171",
                sha256="2" * 64,
                artifact_id=1171,
            ),
            FulfillmentPersistedArtifact(
                artifact_kind="implementation_packet",
                path="db://artifact_blobs/1172",
                sha256="3" * 64,
                artifact_id=1172,
            ),
            FulfillmentPersistedArtifact(
                artifact_kind="implementation_candidate",
                path="db://artifact_blobs/1173",
                sha256="4" * 64,
                artifact_id=1173,
            ),
        ]
    )

    feedback_fields = cast(dict[str, str], client.updated_fields[-1]["fields"])
    assert feedback_fields["u_ai_status"] == "Human Review Required"
    assert "Flow preflight guidance artifact: db://artifact_blobs/1171." in (
        feedback_fields["work_notes"]
    )
    assert "Flow Designer automation is context/preflight-only" in (
        feedback_fields["work_notes"]
    )


def test_model_candidate_handler_runs_code_surface_analysis_without_model_or_update_set() -> None:
    client = FakeModelClient(
        story=Story(
            sys_id="story-sys-id",
            number="STRY0010112",
            short_description="Analyze Incident Business Rule for priority stamping",
            description=(
                "Analyze whether the incident table needs a before update Business Rule "
                "to set u_priority_stamp when priority changes."
            ),
            acceptance_criteria=(
                "Existing Incident Business Rules are retrieved and generation is not "
                "attempted until the capability is approved."
            ),
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

    result = handler(_job().model_copy(update={"story_number": "STRY0010112"}))

    assert provider.payloads == []
    assert client.imports == []
    assert [artifact.artifact_kind for artifact in result.artifacts] == [
        "instance_context_bundle",
        "code_surface_analysis",
        "implementation_packet",
        "implementation_candidate",
    ]
    context_bundle = result.artifacts[0].payload_json
    analysis = result.artifacts[1].payload_json
    candidate = result.artifacts[3].payload_json
    assert context_bundle is not None
    assert analysis is not None
    assert candidate is not None
    assert context_bundle["target_table"] == "incident"
    assert context_bundle["required_surfaces"] == ["table_schema", "business_rules"]
    assert context_bundle["surfaces"][2]["source_table"] == "sys_script"
    assert "business-rule-sys-id" not in str(context_bundle)
    assert "secret-value" not in str(context_bundle)
    assert analysis["capability"] == "business_rule_analyze"
    assert analysis["surface"] == "business_rules"
    assert analysis["source_table"] == "sys_script"
    assert analysis["target_table"] == "incident"
    assert analysis["existing_record_count"] == 1
    assert analysis["supported_generation"] is False
    assert "business rule generation" in analysis["unsupported_cases"]
    assert candidate["status"] == CandidateStatus.MANUAL_BUILD.value
    assert "code_surface_analysis:first" in candidate["eligibility_reasons"]

    assert result.after_artifacts_persisted is not None
    result.after_artifacts_persisted(
        [
            FulfillmentPersistedArtifact(
                artifact_kind="instance_context_bundle",
                path="db://artifact_blobs/100",
                sha256="1" * 64,
                artifact_id=100,
            ),
            FulfillmentPersistedArtifact(
                artifact_kind="code_surface_analysis",
                path="db://artifact_blobs/101",
                sha256="2" * 64,
                artifact_id=101,
            ),
            FulfillmentPersistedArtifact(
                artifact_kind="implementation_packet",
                path="db://artifact_blobs/102",
                sha256="3" * 64,
                artifact_id=102,
            ),
            FulfillmentPersistedArtifact(
                artifact_kind="implementation_candidate",
                path="db://artifact_blobs/103",
                sha256="4" * 64,
                artifact_id=103,
            ),
        ]
    )

    feedback_fields = cast(dict[str, str], client.updated_fields[-1]["fields"])
    assert feedback_fields["u_ai_status"] == "Human Review Required"
    assert "Code surface analysis completed" in feedback_fields["work_notes"]
    assert "db://artifact_blobs/103" in feedback_fields["work_notes"]


def test_model_candidate_handler_generates_business_rule_update_set_handoff() -> None:
    client = FakeModelClient(
        story=Story(
            sys_id="story-sys-id",
            number="STRY0010116",
            short_description="Create Incident priority note Business Rule",
            description=(
                "Create a before update Business Rule on the Incident table. "
                "Condition: priority changes to 1 - Critical. Expected behavior: "
                "set work_notes to Priority escalated by automation. Fields read: "
                "priority. Fields written: work_notes."
            ),
            acceptance_criteria=(
                "Updating an Incident priority to 1 - Critical adds a work note. "
                "Rollback removes the generated Business Rule."
            ),
            story_points=3,
            priority=4,
            state="Work in Progress",
            data_classification=DataClassification.PUBLIC,
        )
    )
    provider = RecordingModelProvider(
        response={
            "changes": [
                {
                    "table": "sys_script",
                    "operation": "insert",
                    "fields": {
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
                }
            ],
            "test_plan": ["Update Incident priority to Critical and confirm work note."],
            "rollback_notes": ["Delete the generated Business Rule."],
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

    result = handler(_job().model_copy(update={"story_number": "STRY0010116"}))

    assert provider.payloads[0]["controls"]["capability_assessment"]["capabilities"] == [
        "business_rule_generate"
    ]
    assert [artifact.artifact_kind for artifact in result.artifacts] == [
        "instance_context_bundle",
        "implementation_packet",
        "implementation_candidate",
    ]
    candidate = result.artifacts[2].payload_json
    assert candidate is not None
    assert candidate["status"] == CandidateStatus.READY_FOR_REVIEW.value
    assert candidate["changes"][0]["table"] == "sys_script"

    assert result.after_artifacts_persisted is not None
    result.after_artifacts_persisted(
        [
            FulfillmentPersistedArtifact(
                artifact_kind="implementation_candidate",
                path="db://artifact_blobs/116",
                sha256="6" * 64,
                artifact_id=116,
            )
        ]
    )

    imported_xml = client.imports[0]["update_set_xml"]
    assert "sys_script_incident_jedi_incident_priority_note" in imported_xml
    assert "<collection>incident</collection>" in imported_xml
    updated_fields = cast(dict[str, str], client.updated_fields[-1]["fields"])
    assert updated_fields["u_ai_status"] == "Ready for Testing"


def test_model_candidate_handler_runs_client_script_analysis() -> None:
    client = FakeModelClient(
        story=Story(
            sys_id="story-sys-id",
            number="STRY0010113",
            short_description="Analyze Incident Client Script for category behavior",
            description=(
                "Analyze whether the incident table needs an onChange Client Script "
                "for category behavior."
            ),
            acceptance_criteria="Existing Incident Client Scripts are retrieved.",
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

    result = handler(_job().model_copy(update={"story_number": "STRY0010113"}))

    assert provider.payloads == []
    assert client.imports == []
    analysis = result.artifacts[1].payload_json
    candidate = result.artifacts[3].payload_json
    assert analysis is not None
    assert candidate is not None
    assert result.artifacts[1].artifact_kind == "code_surface_analysis"
    assert result.artifacts[1].schema_version == "code-surface-analysis-v1"
    assert analysis["capability"] == "client_script_analyze"
    assert analysis["surface"] == "client_scripts"
    assert analysis["source_table"] == "sys_script_client"
    assert analysis["target_table"] == "incident"
    assert analysis["existing_record_count"] == 1
    assert "client-script-sys-id" not in str(analysis)
    assert "secret-value" not in str(analysis)
    assert "code_surface_analysis:first" in candidate["eligibility_reasons"]


def test_model_candidate_handler_generates_client_script_update_set_handoff() -> None:
    client = FakeModelClient(
        story=Story(
            sys_id="story-sys-id",
            number="STRY0010118",
            short_description="Create Incident category onChange Client Script",
            description=(
                "Create an onChange Client Script on the Incident table for the "
                "category field. Condition: category changes to software. Expected "
                "behavior: show an info message telling the user to confirm the "
                "configuration item. Fields read: category. Fields written: none. "
                "Messages shown: Confirm the CI before saving."
            ),
            acceptance_criteria=(
                "Changing Incident category to software shows the message. "
                "Rollback removes the generated Client Script."
            ),
            story_points=3,
            priority=4,
            state="Work in Progress",
            data_classification=DataClassification.PUBLIC,
        )
    )
    provider = RecordingModelProvider(
        response={
            "changes": [
                {
                    "table": "sys_script_client",
                    "operation": "insert",
                    "fields": {
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
                }
            ],
            "test_plan": ["Change Incident category to Software and confirm the message."],
            "rollback_notes": ["Delete the generated Client Script."],
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

    result = handler(_job().model_copy(update={"story_number": "STRY0010118"}))

    assert provider.payloads[0]["controls"]["capability_assessment"]["capabilities"] == [
        "client_script_generate"
    ]
    candidate = result.artifacts[2].payload_json
    assert candidate is not None
    assert candidate["status"] == CandidateStatus.READY_FOR_REVIEW.value
    assert candidate["changes"][0]["table"] == "sys_script_client"

    assert result.after_artifacts_persisted is not None
    result.after_artifacts_persisted(
        [
            FulfillmentPersistedArtifact(
                artifact_kind="implementation_candidate",
                path="db://artifact_blobs/118",
                sha256="8" * 64,
                artifact_id=118,
            )
        ]
    )

    imported_xml = client.imports[0]["update_set_xml"]
    assert "sys_script_client_incident_jedi_incident_category_ci_message" in imported_xml
    assert "<table>incident</table>" in imported_xml
    updated_fields = cast(dict[str, str], client.updated_fields[-1]["fields"])
    assert updated_fields["u_ai_status"] == "Ready for Testing"


def test_model_candidate_handler_runs_script_include_analysis_without_target_table() -> None:
    client = FakeModelClient(
        story=Story(
            sys_id="story-sys-id",
            number="STRY0010114",
            short_description="Analyze AssignmentUtils Script Include",
            description=(
                "Analyze the AssignmentUtils Script Include to determine whether "
                "shared assignment helper logic already exists."
            ),
            acceptance_criteria="Existing Script Includes are retrieved for review.",
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

    result = handler(_job().model_copy(update={"story_number": "STRY0010114"}))

    assert provider.payloads == []
    assert client.imports == []
    context_bundle = result.artifacts[0].payload_json
    analysis = result.artifacts[1].payload_json
    candidate = result.artifacts[3].payload_json
    assert context_bundle is not None
    assert analysis is not None
    assert candidate is not None
    assert context_bundle["target_table"] == "global"
    assert context_bundle["required_surfaces"] == ["script_includes"]
    assert analysis["capability"] == "script_include_analyze"
    assert analysis["surface"] == "script_includes"
    assert analysis["source_table"] == "sys_script_include"
    assert analysis["target_table"] == "global"
    assert analysis["existing_record_count"] == 1
    assert "script-include-sys-id" not in str(analysis)
    assert "secret-value" not in str(analysis)
    assert "code_surface_analysis:first" in candidate["eligibility_reasons"]


def test_model_candidate_handler_generates_script_include_update_set_handoff() -> None:
    client = FakeModelClient(
        story=Story(
            sys_id="story-sys-id",
            number="STRY0010120",
            short_description="Create JediIncidentUtils Script Include",
            description=(
                "Create a Script Include named JediIncidentUtils in Global scope. "
                "Client callable: false. Expected server-side behavior: provide a "
                "normalizeCategory(category) function that returns the category "
                "lowercased. Tables read: none. Tables written: none. Fields read: "
                "none. Fields written: none."
            ),
            acceptance_criteria=(
                "Calling normalizeCategory('Software') returns software. "
                "Rollback removes the generated Script Include."
            ),
            story_points=3,
            priority=4,
            state="Work in Progress",
            data_classification=DataClassification.PUBLIC,
        )
    )
    provider = RecordingModelProvider(
        response={
            "changes": [
                {
                    "table": "sys_script_include",
                    "operation": "insert",
                    "fields": {
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
                }
            ],
            "test_plan": ["Call normalizeCategory('Software') and confirm software."],
            "rollback_notes": ["Delete the generated Script Include."],
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

    result = handler(_job().model_copy(update={"story_number": "STRY0010120"}))

    assert provider.payloads[0]["controls"]["capability_assessment"]["capabilities"] == [
        "script_include_generate"
    ]
    candidate = result.artifacts[2].payload_json
    assert candidate is not None
    assert candidate["status"] == CandidateStatus.READY_FOR_REVIEW.value
    assert candidate["changes"][0]["table"] == "sys_script_include"

    assert result.after_artifacts_persisted is not None
    result.after_artifacts_persisted(
        [
            FulfillmentPersistedArtifact(
                artifact_kind="implementation_candidate",
                path="db://artifact_blobs/120",
                sha256="0" * 64,
                artifact_id=120,
            )
        ]
    )

    imported_xml = client.imports[0]["update_set_xml"]
    assert "sys_script_include_jediincidentutils" in imported_xml
    assert "<api_name>global.JediIncidentUtils</api_name>" in imported_xml
    updated_fields = cast(dict[str, str], client.updated_fields[-1]["fields"])
    assert updated_fields["u_ai_status"] == "Ready for Testing"


def test_model_candidate_handler_generates_structured_script_include_from_uat_story() -> None:
    client = FakeModelClient(
        story=Story(
            sys_id="story-sys-id",
            number="STRY0010023",
            short_description="JEDI UAT: Add Incident text normalization Script Include",
            description=(
                "Target artifact type: Script Include\n"
                "Target table: global\n"
                "Artifact name: JediUatIncidentTextUtils\n"
                "API name: global.JediUatIncidentTextUtils\n"
                "Scope: global\n"
                "Client callable: false\n"
                "Public methods: normalizeText(value)\n"
                "Expected server-side behavior: normalizeText returns an empty string "
                "for null or undefined input and returns the trimmed string value for "
                "other input.\n"
                "Tables read: none\n"
                "Tables written: none\n"
                "Fields read: none\n"
                "Fields written / affected: none\n"
                "Reverse behavior: Not applicable\n"
                "Forbidden behavior: Do not use GlideRecord, outbound calls, credentials, "
                "security changes, caller creation, or client callable behavior.\n"
                "Rollback expectation: Delete the generated Script Include through the "
                "retrieved Update Set review process."
            ),
            acceptance_criteria=(
                "A Script Include named JediUatIncidentTextUtils is created in the "
                "global scope. It exposes normalizeText(value) and performs no table writes."
            ),
            story_points=3,
            priority=4,
            state="Work in Progress",
            data_classification=DataClassification.PUBLIC,
        )
    )
    provider = RecordingModelProvider(
        response={
            "changes": [
                {
                    "table": "sys_script_include",
                    "operation": "insert",
                    "fields": {
                        "name": "JediUatIncidentTextUtils",
                        "access": "public",
                        "client_callable": False,
                        "active": True,
                        "description": "Utility helpers for Incident text normalization.",
                        "script": (
                            "var JediUatIncidentTextUtils = Class.create();\n"
                            "JediUatIncidentTextUtils.prototype = {\n"
                            "    initialize: function() {},\n"
                            "    normalizeText: function(value) {\n"
                            "        if (value === null || typeof value === 'undefined') {\n"
                            "            return '';\n"
                            "        }\n"
                            "        return String(value).trim();\n"
                            "    },\n"
                            "    type: 'JediUatIncidentTextUtils'\n"
                            "};"
                        ),
                        "public_methods": ["normalizeText(value)"],
                        "tables_read": [],
                        "tables_written": [],
                        "fields_read": [],
                        "fields_written": [],
                    },
                }
            ],
            "test_plan": ["Call normalizeText(' test ') and confirm test."],
            "rollback_notes": ["Delete the generated Script Include."],
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

    result = handler(_job().model_copy(update={"story_number": "STRY0010023"}))

    payload = provider.payloads[0]
    assert payload["controls"]["capability_assessment"]["capabilities"] == [
        "script_include_generate"
    ]
    assert payload["instance_context_bundle"]["required_surfaces"] == ["script_includes"]
    assert payload["controls"]["normalized_intent"]["missing_details"] == []
    candidate = result.artifacts[2].payload_json
    assert candidate is not None
    assert candidate["status"] == CandidateStatus.READY_FOR_REVIEW.value
    assert candidate["changes"][0]["table"] == "sys_script_include"

    assert result.after_artifacts_persisted is not None
    result.after_artifacts_persisted(
        [
            FulfillmentPersistedArtifact(
                artifact_kind="implementation_candidate",
                path="db://artifact_blobs/174",
                sha256="9" * 64,
                artifact_id=174,
            )
        ]
    )

    imported_xml = client.imports[0]["update_set_xml"]
    assert "<api_name>global.JediUatIncidentTextUtils</api_name>" in imported_xml
    assert "sys_script_include_jediuatincidenttextutils" in imported_xml


def test_model_candidate_handler_scopes_incomplete_structured_script_include_context() -> None:
    client = FakeModelClient(
        story=Story(
            sys_id="story-sys-id",
            number="STRY0010993",
            short_description="JEDI UAT: Incomplete Incident Script Include",
            description=(
                "Target artifact type: Script Include\n"
                "Target table: global\n"
                "Artifact name: JediIncompleteTextUtils\n"
                "Scope: global\n"
                "Client callable: false\n"
                "Expected server-side behavior: normalizeText trims text.\n"
                "Tables read: none\n"
                "Tables written: none\n"
                "Fields read: none"
            ),
            acceptance_criteria="Delivery is a retrieved Update Set.",
            story_points=3,
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

    result = handler(_job().model_copy(update={"story_number": "STRY0010993"}))

    assert provider.payloads == []
    context_bundle = result.artifacts[0].payload_json
    candidate = result.artifacts[2].payload_json
    assert context_bundle is not None
    assert context_bundle["required_surfaces"] == ["script_includes"]
    assert candidate is not None
    assert "missing detail: fields written" in candidate["eligibility_reasons"]
    assert "context_insufficient:form_sections" not in candidate["eligibility_reasons"]
    assert "context_insufficient:form_layout" not in candidate["eligibility_reasons"]


def test_model_candidate_handler_generates_ui_policy_update_set_handoff() -> None:
    client = FakeModelClient(
        story=Story(
            sys_id="story-sys-id",
            number="STRY0010123",
            short_description="Create Incident assignment group UI Policy",
            description=(
                "Create a UI Policy on the Incident table. Condition: category is "
                "software. Expected behavior: make the assignment_group field "
                "mandatory and visible. Fields read: category. Fields affected: "
                "assignment_group. Reverse if false: true."
            ),
            acceptance_criteria=(
                "When Incident category is software, Assignment group is mandatory. "
                "Rollback removes the generated UI Policy and UI Policy Action."
            ),
            story_points=3,
            priority=4,
            state="Work in Progress",
            data_classification=DataClassification.PUBLIC,
        )
    )
    provider = RecordingModelProvider(
        response={
            "changes": [
                {
                    "table": "sys_ui_policy",
                    "operation": "insert",
                    "fields": {
                        "short_description": "JEDI Incident Assignment Group Required",
                        "table": "incident",
                        "conditions": "category=software",
                        "reverse_if_false": True,
                        "run_scripts": False,
                        "active": True,
                        "on_load": False,
                        "order": 100,
                    },
                },
                {
                    "table": "sys_ui_policy_action",
                    "operation": "insert",
                    "fields": {
                        "policy_name": "JEDI Incident Assignment Group Required",
                        "table": "incident",
                        "field": "assignment_group",
                        "mandatory": "true",
                        "visible": "true",
                        "disabled": "ignore",
                        "cleared": False,
                    },
                },
            ],
            "test_plan": ["Set category to Software and confirm Assignment group is mandatory."],
            "rollback_notes": ["Delete the generated UI Policy and action."],
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

    result = handler(_job().model_copy(update={"story_number": "STRY0010123"}))

    assert provider.payloads[0]["controls"]["capability_assessment"]["capabilities"] == [
        "ui_policy_generate"
    ]
    assert provider.payloads[0]["controls"]["capability_assessment"][
        "required_instance_context"
    ] == ["table_schema", "form_layout", "ui_policies"]
    candidate = result.artifacts[2].payload_json
    assert candidate is not None
    assert candidate["status"] == CandidateStatus.READY_FOR_REVIEW.value
    assert candidate["changes"][0]["table"] == "sys_ui_policy"
    assert candidate["changes"][1]["table"] == "sys_ui_policy_action"

    assert result.after_artifacts_persisted is not None
    result.after_artifacts_persisted(
        [
            FulfillmentPersistedArtifact(
                artifact_kind="implementation_candidate",
                path="db://artifact_blobs/123",
                sha256="3" * 64,
                artifact_id=123,
            )
        ]
    )

    imported_xml = client.imports[0]["update_set_xml"]
    assert "sys_ui_policy_incident_jedi_incident_assignment_group_required" in imported_xml
    assert "sys_ui_policy_action_incident_assignment_group_required" in imported_xml
    updated_fields = cast(dict[str, str], client.updated_fields[-1]["fields"])
    assert updated_fields["u_ai_status"] == "Ready for Testing"


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
