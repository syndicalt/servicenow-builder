from typing import Any, cast

import pytest
from pydantic import ValidationError

from jedi_devproject.models import (
    CandidateStatus,
    DataClassification,
    ProjectContext,
    ProviderPolicy,
    ProviderStatus,
    RetrievalCitation,
    RunManifest,
    Story,
    UpdateSetCandidate,
    stable_artifact_hash,
)


def test_story_accepts_valid_minimal_input() -> None:
    story = Story(
        sys_id="abc123",
        number="STORY0010001",
        short_description="Update portal help text",
        description="Change the help text on the intake portal.",
        story_points=2,
        priority=3,
        state="Ready",
        data_classification=DataClassification.PUBLIC,
    )

    assert story.number == "STORY0010001"
    assert story.story_points == 2
    assert story.data_classification is DataClassification.PUBLIC


def test_story_rejects_missing_sys_id() -> None:
    with pytest.raises(ValidationError) as exc:
        Story(
            sys_id="",
            number="STORY0010001",
            short_description="Update portal help text",
            description="Change the help text on the intake portal.",
            story_points=2,
            priority=3,
            state="Ready",
            data_classification=DataClassification.PUBLIC,
        )

    assert "sys_id" in str(exc.value)


def test_story_rejects_missing_number() -> None:
    with pytest.raises(ValidationError) as exc:
        Story(
            sys_id="abc123",
            number=" ",
            short_description="Update portal help text",
            description="Change the help text on the intake portal.",
            story_points=2,
            priority=3,
            state="Ready",
            data_classification=DataClassification.PUBLIC,
        )

    assert "number" in str(exc.value)


def test_story_rejects_unknown_data_classification() -> None:
    with pytest.raises(ValidationError):
        Story(
            sys_id="abc123",
            number="STORY0010001",
            short_description="Update portal help text",
            description="Change the help text on the intake portal.",
            story_points=2,
            priority=3,
            state="Ready",
            data_classification=cast(Any, "secret"),
        )


@pytest.mark.parametrize(
    ("model_class", "values", "sensitive_parts"),
    [
        (
            Story,
            {
                "sys_id": "story-sys-id",
                "number": "STRY0010013",
                "short_description": "Build secret workflow",
                "description": "Story description includes protected context.",
                "story_points": "secret-points",
                "priority": 3,
                "state": "Ready",
                "data_classification": DataClassification.PUBLIC,
            },
            ("secret-points",),
        ),
        (
            UpdateSetCandidate,
            {
                "story_number": "STRY0010013",
                "name": "candidate",
                "eligibility_decision": "eligible",
                "eligibility_reasons": ["reason includes protected context"],
                "confidence": "secret-confidence",
                "risk_score": 0.1,
                "status": CandidateStatus.DRAFT,
            },
            ("secret-confidence",),
        ),
        (
            RetrievalCitation,
            {
                "source": "meeting-notes",
                "content_hash": "hash",
                "confidence": "secret-confidence",
            },
            ("secret-confidence",),
        ),
    ],
)
def test_core_model_validation_errors_do_not_echo_rejected_inputs(
    model_class: type[Any],
    values: dict[str, Any],
    sensitive_parts: tuple[str, ...],
) -> None:
    with pytest.raises(ValidationError) as exc:
        model_class.model_validate(values)

    message = str(exc.value)
    assert "input_value" not in message
    for sensitive_part in sensitive_parts:
        assert sensitive_part not in message


def test_candidate_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        UpdateSetCandidate(
            story_number="STORY0010001",
            name="UPD_STORY0010001_Update_Help_Text",
            eligibility_decision="eligible",
            eligibility_reasons=["content-only story type"],
            confidence=0.91,
            risk_score=0.1,
            status=cast(Any, "Imported"),
        )


def test_candidate_status_transitions_are_explicit() -> None:
    candidate = UpdateSetCandidate(
        story_number="STORY0010001",
        name="UPD_STORY0010001_Update_Help_Text",
        eligibility_decision="eligible",
        eligibility_reasons=["content-only story type"],
        confidence=0.91,
        risk_score=0.1,
        status=CandidateStatus.DRAFT,
    )

    assert candidate.can_transition_to(CandidateStatus.READY_FOR_REVIEW)
    assert not candidate.can_transition_to(CandidateStatus.APPROVED_FOR_EXPORT)


def test_rejected_candidate_cannot_transition_to_approved_without_new_revision() -> None:
    candidate = UpdateSetCandidate(
        story_number="STORY0010001",
        name="UPD_STORY0010001_Update_Help_Text",
        eligibility_decision="rejected",
        eligibility_reasons=["unsupported table"],
        confidence=0.2,
        risk_score=0.8,
        status=CandidateStatus.REJECTED,
    )

    assert not candidate.can_transition_to(CandidateStatus.APPROVED_FOR_EXPORT)


def test_provider_policy_rejects_disallowed_task_and_data_class() -> None:
    policy = ProviderPolicy(
        provider_id="rules-only",
        deployment_boundary="local-dev",
        authorization_level="rules-only",
        allowed_data_classes={DataClassification.PUBLIC},
        allowed_tasks={"classify_story"},
        max_context_policy="no model context",
        retention_policy="no external retention",
        status=ProviderStatus.APPROVED,
    )

    assert policy.allows(task="classify_story", data_class=DataClassification.PUBLIC)
    assert not policy.allows(task="generate_candidate", data_class=DataClassification.PUBLIC)
    assert not policy.allows(task="classify_story", data_class=DataClassification.CUI)


def test_stable_artifact_hash_is_order_independent_for_mapping_keys() -> None:
    left = stable_artifact_hash({"story": "STORY0010001", "status": "Draft"})
    right = stable_artifact_hash({"status": "Draft", "story": "STORY0010001"})

    assert left == right
    assert len(left) == 64


def test_stable_artifact_hash_rejects_non_finite_values_without_payload_leak() -> None:
    with pytest.raises(ValueError) as exc_info:
        stable_artifact_hash(
            {
                "safe_score": 1.0,
                "bad_score": float("nan"),
                "client_secret": "hash-secret",
            }
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "artifact hash payload contains non-finite numeric values"
    assert "bad_score" not in diagnostic
    assert "NaN" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "hash-secret" not in diagnostic
    assert exc_info.value.__cause__ is None


def test_stable_artifact_hash_rejects_non_json_values_without_payload_leak() -> None:
    class StringifiesSecret:
        def __str__(self) -> str:
            return "hash-secret"

    with pytest.raises(ValueError) as exc_info:
        stable_artifact_hash(
            {
                "safe_score": 1.0,
                "unsafe_object": StringifiesSecret(),
                "client_secret": "hash-secret",
            }
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "artifact hash payload contains non-JSON values"
    assert "unsafe_object" not in diagnostic
    assert "StringifiesSecret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "hash-secret" not in diagnostic
    assert exc_info.value.__cause__ is None


def test_stable_artifact_hash_rejects_string_subclass_values_without_payload_leak() -> None:
    class HostileHashText(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=hash-str-secret")

    with pytest.raises(ValueError) as exc_info:
        stable_artifact_hash(
            {
                "safe_score": 1.0,
                "unsafe_text": HostileHashText("hash-secret"),
                "client_secret": "hash-secret",
            }
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "artifact hash payload contains non-JSON values"
    assert "unsafe_text" not in diagnostic
    assert "HostileHashText" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "hash-secret" not in diagnostic
    assert exc_info.value.__cause__ is None


def test_stable_artifact_hash_rejects_scalar_subclass_values_without_payload_leak() -> None:
    class HostileHashOrder(int):
        def __str__(self) -> str:
            raise AssertionError("client_secret=hash-scalar-secret")

    with pytest.raises(ValueError) as exc_info:
        stable_artifact_hash(
            {
                "safe_score": 1.0,
                "unsafe_order": HostileHashOrder(3),
                "client_secret": "hash-secret",
            }
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "artifact hash payload contains non-JSON values"
    assert "unsafe_order" not in diagnostic
    assert "HostileHashOrder" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "hash-secret" not in diagnostic
    assert exc_info.value.__cause__ is None


def test_stable_artifact_hash_rejects_container_subclasses_without_payload_leak() -> None:
    class HostileHashDict(dict[str, Any]):
        def items(self) -> Any:
            raise AssertionError("client_secret=hash-dict-subclass-secret")

    class HostileHashList(list[Any]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=hash-list-subclass-secret")

    for value in (
        HostileHashDict({"secret": "hidden dict"}),
        {"items": HostileHashList(["hidden list"])},
    ):
        with pytest.raises(ValueError) as exc_info:
            stable_artifact_hash(value)

        diagnostic = str(exc_info.value)
        assert diagnostic == "artifact hash payload contains non-JSON values"
        assert "HostileHash" not in diagnostic
        assert "client_secret" not in diagnostic
        assert "subclass-secret" not in diagnostic
        assert "hidden" not in diagnostic
        assert exc_info.value.__cause__ is None


def test_project_context_rejects_empty_name() -> None:
    with pytest.raises(ValidationError):
        ProjectContext(name=" ")


def test_retrieval_citation_rejects_confidence_outside_zero_to_one() -> None:
    with pytest.raises(ValidationError):
        RetrievalCitation(source="docs", content_hash="abc123", confidence=1.1)


def test_run_manifest_rejects_empty_run_id() -> None:
    with pytest.raises(ValidationError):
        RunManifest(run_id="")
