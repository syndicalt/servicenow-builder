import json
from pathlib import Path

from jedi_devproject.models import DataClassification, Story
from jedi_devproject.pipeline import PipelineInputs, run_pipeline
from jedi_devproject.rag import Document, RagDomain, SpecializedRags
from jedi_devproject.safety import AllowlistPolicy, StoryType, evaluate_story

EXAMPLE_STORY_PATH = Path("examples/stories/content-only-help-text.json")


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
                source="examples/rag/servicenow-update-set-baseline",
                content="Portal update sets capture configuration updates.",
                version="example",
            ),
            Document(
                domain=RagDomain.INSTANCE_METADATA,
                source="examples/rag/sp_instance",
                content="sp_instance stores portal widget instance text.",
                version="example",
            ),
            Document(
                domain=RagDomain.PROJECT_CONTEXT,
                source="examples/rag/project-scope",
                content="Portal help text changes are in scope.",
                version="example",
            ),
            Document(
                domain=RagDomain.COMPLIANCE,
                source="examples/rag/compliance",
                content="Portal candidates must be generated without public AI endpoints.",
                version="example",
            ),
        ]
    )


def test_example_story_fixture_is_valid_and_complete() -> None:
    payload = json.loads(EXAMPLE_STORY_PATH.read_text(encoding="utf-8"))
    story = Story.model_validate(payload)

    assert story.number == "STORY-EXAMPLE-001"
    assert story.data_classification is DataClassification.PUBLIC
    assert story.description
    assert story.acceptance_criteria
    assert story.affected_tables == ["sp_instance"]


def test_example_story_is_eligible_for_template_generation() -> None:
    story = Story.model_validate(json.loads(EXAMPLE_STORY_PATH.read_text(encoding="utf-8")))

    result = evaluate_story(story, _policy())

    assert result.decision == "eligible"
    assert result.story_type is StoryType.CONTENT_ONLY


def test_example_story_generates_candidate_artifact(tmp_path: Path) -> None:
    story = Story.model_validate(json.loads(EXAMPLE_STORY_PATH.read_text(encoding="utf-8")))

    result = run_pipeline(
        PipelineInputs(
            stories=[story],
            policy=_policy(),
            rags=_rags(),
            artifact_root=tmp_path,
            run_id="example-run",
        )
    )

    assert result.summary["generated_candidates"] == 1
    assert result.artifact_paths[0].name == "STORY-EXAMPLE-001.json"
