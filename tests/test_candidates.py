import json
from pathlib import Path

import pytest

from jedi_devproject.artifacts import ArtifactWriteError, write_candidate_artifact
from jedi_devproject.candidates import generate_template_candidate
from jedi_devproject.models import CandidateStatus, DataClassification, Story
from jedi_devproject.rag import Document, RagDomain, SpecializedRags
from jedi_devproject.safety import AllowlistPolicy, StoryType, evaluate_story


def _story(
    description: str = "Change portal help text from Submit to Send.",
    short_description: str = "Update portal help text",
) -> Story:
    return Story(
        sys_id="abc123",
        number="STORY0010001",
        short_description=short_description,
        description=description,
        story_points=2,
        priority=3,
        state="Ready",
        data_classification=DataClassification.PUBLIC,
        acceptance_criteria="The portal shows Send instead of Submit.",
        affected_tables=["sp_instance"],
    )


def _policy() -> AllowlistPolicy:
    return AllowlistPolicy(
        story_types={StoryType.CONTENT_ONLY},
        tables={"sp_instance"},
        operations={"update"},
        max_points=3,
    )


def _rags() -> SpecializedRags:
    return SpecializedRags.from_documents(
        [
            Document(
                domain=RagDomain.SERVICENOW_PLATFORM,
                source="servicenow-docs/update-sets",
                content="Portal update sets capture configuration updates.",
                version="washington",
            ),
            Document(
                domain=RagDomain.INSTANCE_METADATA,
                source="instance/sp_instance",
                content="sp_instance stores portal widget instance text.",
                version="snapshot-1",
            ),
            Document(
                domain=RagDomain.PROJECT_CONTEXT,
                source="project/scope",
                content="Portal help text changes are in scope.",
                version="sprint-4",
            ),
            Document(
                domain=RagDomain.COMPLIANCE,
                source="policy/model-use",
                content="Portal candidates must be generated without public AI endpoints.",
                version="2026-05",
            ),
        ]
    )


def test_eligible_content_story_generates_reviewable_candidate() -> None:
    story = _story()
    safety_result = evaluate_story(story, _policy())

    candidate = generate_template_candidate(story=story, safety_result=safety_result, rags=_rags())

    assert candidate.status is CandidateStatus.READY_FOR_REVIEW
    assert candidate.eligibility_decision == "eligible"
    assert candidate.confidence > 0.85
    assert candidate.changes[0].table == "sp_instance"
    assert candidate.changes[0].operation == "update"
    assert candidate.retrieval_citations
    assert candidate.assumptions
    assert candidate.reviewer_notes
    assert candidate.artifact_hash


def test_unsupported_story_type_routes_to_manual_build_candidate() -> None:
    story = _story(
        short_description="Adjust workflow behavior",
        description="Adjust workflow behavior for request routing.",
    )
    safety_result = evaluate_story(story, _policy())

    candidate = generate_template_candidate(story=story, safety_result=safety_result, rags=_rags())

    assert candidate.status is CandidateStatus.MANUAL_BUILD
    assert candidate.eligibility_decision == "manual_review"
    assert candidate.changes == []
    assert "Template generation skipped" in candidate.reviewer_notes[0]


def test_candidate_artifact_writer_refuses_to_overwrite_existing_run_file(tmp_path: Path) -> None:
    candidate = generate_template_candidate(
        story=_story(),
        safety_result=evaluate_story(_story(), _policy()),
        rags=_rags(),
    )

    first_path = write_candidate_artifact(tmp_path, run_id="run-001", candidate=candidate)

    with pytest.raises(ArtifactWriteError):
        write_candidate_artifact(tmp_path, run_id="run-001", candidate=candidate)

    payload = json.loads(first_path.read_text(encoding="utf-8"))
    assert payload["story_number"] == "STORY0010001"


def test_dictionary_form_story_generates_controlled_candidate() -> None:
    story = Story(
        sys_id="abc123",
        number="STRY0010013",
        short_description="Add AI Review Notes field to Story form",
        description=(
            "Add a new custom field to the rm_story table named u_ai_review_notes. "
            "Field label: AI Review Notes. Field type: String. Max length: 8000. "
            "Mandatory: No. Add it to the Story form below Description."
        ),
        story_points=3,
        priority=4,
        state="Ready",
        data_classification=DataClassification.PUBLIC,
        acceptance_criteria="The AI Review Notes field is visible and saves on rm_story.",
        affected_tables=["sys_dictionary", "sys_ui_form"],
    )
    policy = AllowlistPolicy(
        story_types={StoryType.DICTIONARY_FORM},
        tables={"sys_dictionary", "sys_ui_form"},
        operations={"insert", "update"},
        max_points=3,
    )
    safety_result = evaluate_story(story, policy, proposed_operation="insert")

    candidate = generate_template_candidate(story=story, safety_result=safety_result, rags=_rags())

    assert candidate.status is CandidateStatus.READY_FOR_REVIEW
    assert candidate.changes[0].table == "sys_dictionary"
    assert candidate.changes[0].operation == "insert"
    assert candidate.changes[0].fields["name"] == "rm_story"
    assert candidate.changes[0].fields["element"] == "u_ai_review_notes"
    assert candidate.changes[1].table == "sys_ui_form"
    assert "form layout" in candidate.reviewer_notes[0].lower()
    assert candidate.risk_score == 0.12
