import json
from pathlib import Path

from jedi_devproject.models import DataClassification, Story
from jedi_devproject.pipeline import PipelineInputs, run_pipeline
from jedi_devproject.rag import Document, RagDomain, SpecializedRags
from jedi_devproject.safety import AllowlistPolicy, StoryType


def _story(
    *,
    number: str,
    short_description: str = "Update portal help text",
    description: str = "Change portal help text from Submit to Send.",
    affected_tables: list[str] | None = None,
) -> Story:
    return Story(
        sys_id=f"sys-{number}",
        number=number,
        short_description=short_description,
        description=description,
        story_points=2,
        priority=3,
        state="Ready",
        data_classification=DataClassification.PUBLIC,
        acceptance_criteria="Portal help text shows Send.",
        affected_tables=["sp_instance"] if affected_tables is None else affected_tables,
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
                version="sprint-10",
            ),
            Document(
                domain=RagDomain.COMPLIANCE,
                source="policy/model-use",
                content="Portal candidates must be generated without public AI endpoints.",
                version="2026-05",
            ),
        ]
    )


def test_pipeline_writes_candidates_and_summary(tmp_path: Path) -> None:
    result = run_pipeline(
        PipelineInputs(
            stories=[
                _story(number="STORY0010001"),
                _story(
                    number="STORY0010002",
                    description="Create a new ACL for request data.",
                ),
            ],
            policy=_policy(),
            rags=_rags(),
            artifact_root=tmp_path,
            run_id="run-001",
        )
    )

    assert result.metrics.eligible == 1
    assert result.metrics.rejected == 1
    assert result.metrics.generated_candidates == 1
    assert len(result.artifact_paths) == 1
    assert result.artifact_paths[0].name == "STORY0010001.json"
    assert result.summary == {
        "run_id": "run-001",
        "stories_processed": 2,
        "eligible": 1,
        "manual_review": 0,
        "rejected": 1,
        "generated_candidates": 1,
        "artifact_count": 1,
        "enriched_stories": 0,
        "enrichment_manual_review": 0,
        "inferred_tables": 0,
        "automated_development_candidates": 1,
    }
    assert json.loads(result.artifact_paths[0].read_text(encoding="utf-8"))[
        "story_number"
    ] == "STORY0010001"


def test_pipeline_safe_summary_does_not_include_sys_ids_or_secrets(tmp_path: Path) -> None:
    result = run_pipeline(
        PipelineInputs(
            stories=[_story(number="STORY0010001")],
            policy=_policy(),
            rags=_rags(),
            artifact_root=tmp_path,
            run_id="run-001",
        )
    )

    rendered = repr(result.summary)
    assert "sys-STORY0010001" not in rendered
    assert "secret" not in rendered.lower()


def test_pipeline_enriches_missing_affected_tables_before_safety(tmp_path: Path) -> None:
    result = run_pipeline(
        PipelineInputs(
            stories=[
                _story(
                    number="STORY0010001",
                    description="Change portal help text from Submit to Send.",
                    affected_tables=[],
                )
            ],
            policy=_policy(),
            rags=_rags(),
            artifact_root=tmp_path,
            run_id="run-001",
        )
    )

    assert result.metrics.eligible == 1
    assert result.metrics.generated_candidates == 1
    assert result.summary["enriched_stories"] == 1
    assert result.summary["inferred_tables"] == 1


def test_pipeline_keeps_ambiguous_unenriched_story_in_manual_review(tmp_path: Path) -> None:
    result = run_pipeline(
        PipelineInputs(
            stories=[
                _story(
                    number="STORY0010001",
                    short_description="Improve request handling",
                    description="Make request handling better for users.",
                    affected_tables=[],
                )
            ],
            policy=_policy(),
            rags=_rags(),
            artifact_root=tmp_path,
            run_id="run-001",
        )
    )

    assert result.metrics.manual_review == 1
    assert result.metrics.generated_candidates == 0
    assert result.summary["enrichment_manual_review"] == 1


def test_pipeline_generates_dictionary_form_candidate_after_enrichment(tmp_path: Path) -> None:
    result = run_pipeline(
        PipelineInputs(
            stories=[
                _story(
                    number="STRY0010013",
                    short_description="Add AI Review Notes field to Story form",
                    description=(
                        "Add a new custom field to the rm_story table named u_ai_review_notes "
                        "and place it on the Story form below Description."
                    ),
                    affected_tables=[],
                )
            ],
            policy=AllowlistPolicy(
                story_types={StoryType.DICTIONARY_FORM},
                tables={"sys_dictionary", "sys_ui_form"},
                operations={"insert", "update"},
                max_points=3,
            ),
            rags=_rags(),
            artifact_root=tmp_path,
            run_id="run-001",
        )
    )

    assert result.metrics.eligible == 1
    assert result.metrics.generated_candidates == 1
    assert result.summary["enriched_stories"] == 1
    assert result.summary["automated_development_candidates"] == 1
    assert result.candidates[0].changes[0].table == "sys_dictionary"
    assert result.candidates[0].changes[1].table == "sys_ui_form"
