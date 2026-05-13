from jedi_devproject.implementation_packet import (
    IMPLEMENTATION_PACKET_TASK,
    build_implementation_packet,
    generate_implementation_candidate,
)
from jedi_devproject.models import (
    DataClassification,
    ProviderPolicy,
    ProviderStatus,
    Story,
)
from jedi_devproject.providers import ModelResponseError
from jedi_devproject.rag import Document, RagDomain, SpecializedRags
from jedi_devproject.safety import AllowlistPolicy, StoryType


class RecordingImplementationProvider:
    def __init__(self, response: dict[str, object] | None = None) -> None:
        self.response = response or {
            "changes": [
                {
                    "table": "sys_dictionary",
                    "operation": "insert",
                    "fields": {
                        "name": "rm_story",
                        "element": "u_ai_review_notes",
                    },
                }
            ],
            "test_plan": ["Confirm field appears on Story form."],
            "rollback_notes": ["Remove field from form and dictionary."],
        }
        self.payloads: list[dict[str, object]] = []

    def generate(self, payload: dict[str, object]) -> dict[str, object]:
        self.payloads.append(payload)
        return self.response


def _story() -> Story:
    return Story(
        sys_id="story-sys-id",
        number="STRY0010013",
        short_description="Add AI Review Notes field to Story form",
        description=(
            "Add u_ai_review_notes to rm_story and place it on the Story form "
            "for reviewer notes."
        ),
        acceptance_criteria=(
            "The AI Review Notes field is visible on the Story form and stores "
            "up to 8000 characters."
        ),
        story_points=3,
        priority=4,
        state="Ready",
        data_classification=DataClassification.PUBLIC,
        affected_tables=["sys_dictionary", "sys_ui_form"],
    )


def _rags() -> SpecializedRags:
    return SpecializedRags.from_documents(
        [
            Document(
                domain=RagDomain.SERVICENOW_PLATFORM,
                source="servicenow/docs/dictionary-form",
                content="Dictionary form field work uses sys_dictionary and sys_ui_form.",
                version="test",
            ),
            Document(
                domain=RagDomain.INSTANCE_METADATA,
                source="instance/rm_story",
                content="rm_story supports custom fields prefixed with u_.",
                version="test",
            ),
            Document(
                domain=RagDomain.PROJECT_CONTEXT,
                source="project/story-scope",
                content="AI review notes support human review of implementation candidates.",
                version="test",
            ),
            Document(
                domain=RagDomain.COMPLIANCE,
                source="compliance/model-boundary",
                content="No public AI endpoint may receive story context.",
                version="test",
            ),
        ]
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
        provider_id="now-assist-native",
        deployment_boundary="servicenow-federal-boundary",
        authorization_level="fedramp-aligned-evaluation",
        allowed_data_classes={DataClassification.PUBLIC},
        allowed_tasks={IMPLEMENTATION_PACKET_TASK},
        max_context_policy="implementation-packet-v1",
        retention_policy="customer-boundary",
        status=ProviderStatus.APPROVED,
    )


def test_build_implementation_packet_contains_grounded_context_and_controls() -> None:
    packet = build_implementation_packet(
        story=_story(),
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
    )

    assert packet.task == IMPLEMENTATION_PACKET_TASK
    assert packet.provider_id == "now-assist-native"
    assert packet.story.number == "STRY0010013"
    assert packet.allowed_tables == ["sys_dictionary", "sys_ui_form"]
    assert packet.allowed_operations == ["insert", "update"]
    assert packet.risk_score < 0.2
    assert packet.safety_decision == "eligible"
    assert len(packet.retrieval_citations) >= 4
    assert "No public AI endpoint" in packet.context_sections["compliance"]
    assert "story-sys-id" not in packet.model_dump_json()


def test_implementation_packet_payload_is_model_ready_and_minimized() -> None:
    packet = build_implementation_packet(
        story=_story(),
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
    )

    payload = packet.to_model_payload()

    assert payload["task"] == IMPLEMENTATION_PACKET_TASK
    assert payload["story"]["number"] == "STRY0010013"
    assert "sys_id" not in payload["story"]
    assert payload["controls"]["allowed_tables"] == ["sys_dictionary", "sys_ui_form"]
    assert payload["output_contract"]["must_return_manual_review_when_uncertain"] is True


def test_generate_implementation_candidate_sends_packet_to_approved_provider() -> None:
    provider = RecordingImplementationProvider()

    response = generate_implementation_candidate(
        story=_story(),
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        provider=provider,
    )

    assert response["changes"][0]["table"] == "sys_dictionary"
    assert provider.payloads[0]["task"] == IMPLEMENTATION_PACKET_TASK
    assert "story-sys-id" not in repr(provider.payloads[0])


def test_generate_implementation_candidate_rejects_missing_test_plan() -> None:
    provider = RecordingImplementationProvider(
        {
            "changes": [
                {
                    "table": "sys_dictionary",
                    "operation": "insert",
                    "fields": {
                        "name": "rm_story",
                        "element": "u_ai_review_notes",
                    },
                }
            ],
            "rollback_notes": ["Remove field from form and dictionary."],
        }
    )

    try:
        generate_implementation_candidate(
            story=_story(),
            policy=_policy(),
            provider_policy=_provider_policy(),
            rags=_rags(),
            provider=provider,
        )
    except ModelResponseError as exc:
        assert "test_plan must be a non-empty list" in str(exc)
    else:
        raise AssertionError("missing test_plan was accepted")


def test_generate_implementation_candidate_rejects_missing_rollback_notes() -> None:
    provider = RecordingImplementationProvider(
        {
            "changes": [
                {
                    "table": "sys_dictionary",
                    "operation": "insert",
                    "fields": {
                        "name": "rm_story",
                        "element": "u_ai_review_notes",
                    },
                }
            ],
            "test_plan": ["Confirm field appears on Story form."],
        }
    )

    try:
        generate_implementation_candidate(
            story=_story(),
            policy=_policy(),
            provider_policy=_provider_policy(),
            rags=_rags(),
            provider=provider,
        )
    except ModelResponseError as exc:
        assert "rollback_notes must be a non-empty list" in str(exc)
    else:
        raise AssertionError("missing rollback_notes was accepted")
