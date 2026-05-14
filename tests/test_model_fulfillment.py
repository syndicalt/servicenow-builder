from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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
        return []

    def fetch_story_dictionary_fields(self) -> list[StoryDictionaryField]:
        return []

    def update_story_fields(self, story_sys_id: str, fields: dict[str, object]) -> None:
        self.updated_fields.append({"story_sys_id": story_sys_id, "fields": fields})


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


def test_model_candidate_handler_writes_packet_candidate_work_note_and_artifact_refs(
    tmp_path: Path,
) -> None:
    client = FakeModelClient()
    provider = RecordingModelProvider()
    handler = model_candidate_fulfillment_handler(
        client=client,
        config=ModelCandidateFulfillmentConfig(
            artifact_root=tmp_path,
            policy=_policy(),
            provider_policy=_provider_policy(),
            rags=_rags(),
            provider=provider,
        ),
    )

    result = handler(_job())

    assert result.message == "Implementation candidate generated for STRY0010013"
    assert [artifact.artifact_kind for artifact in result.artifacts] == [
        "implementation_packet",
        "implementation_candidate",
    ]
    packet_path = Path(result.artifacts[0].path)
    candidate_path = Path(result.artifacts[1].path)
    assert packet_path.exists()
    assert candidate_path.exists()
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    assert packet["provider_id"] == "openai-chatgpt"
    assert packet["story"]["number"] == "STRY0010013"
    assert "story-sys-id" not in packet_path.read_text(encoding="utf-8")
    assert candidate["status"] == "Ready for Review"
    assert candidate["changes"][0]["fields"]["element"] == "u_ai_review_notes"
    assert provider.payloads[0]["task"] == "generate_implementation_candidate"
    assert client.updated_fields == [
        {
            "story_sys_id": "story-sys-id",
            "fields": {
                "work_notes": (
                    "Implementation candidate generated for STRY0010013. "
                    f"Packet: {packet_path}. Candidate: {candidate_path}."
                )
            },
        }
    ]


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
            artifact_root=tmp_path,
            policy=_policy(),
            provider_policy=_provider_policy(),
            rags=_rags(),
            provider=provider,
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
