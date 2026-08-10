import json
import math
from pathlib import Path
from typing import Any

import pytest

from jedi_devproject.artifacts import (
    ArtifactWriteError,
    _ensure_artifact_dto_payload_json_safe,
    write_candidate_artifact,
)
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


def test_candidate_artifact_writer_rejects_broken_symlink_escape(tmp_path: Path) -> None:
    candidate = generate_template_candidate(
        story=_story(),
        safety_result=evaluate_story(_story(), _policy()),
        rags=_rags(),
    )
    run_dir = tmp_path / "run-001"
    run_dir.mkdir()
    outside_path = tmp_path / "escape.json"
    artifact_link = run_dir / "STORY0010001.json"
    artifact_link.symlink_to(outside_path)

    with pytest.raises(ArtifactWriteError):
        write_candidate_artifact(tmp_path, run_id="run-001", candidate=candidate)

    assert artifact_link.is_symlink()
    assert not outside_path.exists()


def test_candidate_artifact_writer_rejects_path_traversal_run_id(tmp_path: Path) -> None:
    candidate = generate_template_candidate(
        story=_story(),
        safety_result=evaluate_story(_story(), _policy()),
        rags=_rags(),
    )

    with pytest.raises(ArtifactWriteError, match="unsafe artifact path component"):
        write_candidate_artifact(tmp_path / "artifacts", run_id="../escape", candidate=candidate)

    assert not (tmp_path / "escape" / "STORY0010001.json").exists()


def test_candidate_artifact_writer_rejects_non_finite_candidate_without_payload_leak(
    tmp_path: Path,
) -> None:
    candidate = generate_template_candidate(
        story=_story(),
        safety_result=evaluate_story(_story(), _policy()),
        rags=_rags(),
    ).model_copy(update={"confidence": math.nan})

    with pytest.raises(ArtifactWriteError) as exc_info:
        write_candidate_artifact(tmp_path, run_id="run-001", candidate=candidate)

    diagnostic = str(exc_info.value)
    assert diagnostic == "artifact DTO payload contains non-finite numeric values"
    assert exc_info.value.__cause__ is None
    assert "confidence" not in diagnostic
    assert "NaN" not in diagnostic
    assert "STORY0010001" not in diagnostic
    assert not (tmp_path / "run-001" / "STORY0010001.json").exists()


def test_candidate_artifact_writer_rejects_non_json_candidate_without_payload_leak(
    tmp_path: Path,
) -> None:
    class SecretBearingObject:
        def __str__(self) -> str:
            return "client_secret=candidate-secret"

    candidate = generate_template_candidate(
        story=_story(),
        safety_result=evaluate_story(_story(), _policy()),
        rags=_rags(),
    ).model_copy(update={"artifact_hash": SecretBearingObject()})

    with pytest.raises(ArtifactWriteError) as exc_info:
        write_candidate_artifact(tmp_path, run_id="run-001", candidate=candidate)

    diagnostic = str(exc_info.value)
    assert diagnostic == "artifact DTO payload contains non-JSON values"
    assert exc_info.value.__cause__ is None
    assert "artifact_hash" not in diagnostic
    assert "SecretBearingObject" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "candidate-secret" not in diagnostic
    assert not (tmp_path / "run-001" / "STORY0010001.json").exists()


def test_candidate_artifact_writer_rejects_string_subclass_candidate_without_payload_leak(
    tmp_path: Path,
) -> None:
    class HostileCandidateText(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=candidate-str-secret")

    candidate = generate_template_candidate(
        story=_story(),
        safety_result=evaluate_story(_story(), _policy()),
        rags=_rags(),
    ).model_copy(update={"artifact_hash": HostileCandidateText("candidate-secret")})

    with pytest.raises(ArtifactWriteError) as exc_info:
        write_candidate_artifact(tmp_path, run_id="run-001", candidate=candidate)

    diagnostic = str(exc_info.value)
    assert diagnostic == "artifact DTO payload contains non-JSON values"
    assert exc_info.value.__cause__ is None
    assert "artifact_hash" not in diagnostic
    assert "HostileCandidateText" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "candidate" not in diagnostic
    assert not (tmp_path / "run-001" / "STORY0010001.json").exists()


def test_artifact_dto_payload_rejects_container_subclasses_without_payload_leak() -> (
    None
):
    class HostileArtifactDict(dict[str, Any]):
        def items(self) -> Any:
            raise AssertionError("client_secret=artifact-dict-subclass-secret")

    class HostileArtifactList(list[Any]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=artifact-list-subclass-secret")

    class HostileArtifactTuple(tuple[Any, ...]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=artifact-tuple-subclass-secret")

    for value in (
        HostileArtifactDict({"secret": "hidden dict"}),
        HostileArtifactList(["hidden list"]),
        HostileArtifactTuple(("hidden tuple",)),
    ):
        with pytest.raises(TypeError) as exc_info:
            _ensure_artifact_dto_payload_json_safe(value)

        diagnostic = str(exc_info.value)
        assert diagnostic == "non-JSON artifact DTO payload value"
        assert "HostileArtifact" not in diagnostic
        assert "client_secret" not in diagnostic
        assert "subclass-secret" not in diagnostic
        assert "hidden" not in diagnostic


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
