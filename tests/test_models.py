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


def test_project_context_rejects_empty_name() -> None:
    with pytest.raises(ValidationError):
        ProjectContext(name=" ")


def test_retrieval_citation_rejects_confidence_outside_zero_to_one() -> None:
    with pytest.raises(ValidationError):
        RetrievalCitation(source="docs", content_hash="abc123", confidence=1.1)


def test_run_manifest_rejects_empty_run_id() -> None:
    with pytest.raises(ValidationError):
        RunManifest(run_id="")
