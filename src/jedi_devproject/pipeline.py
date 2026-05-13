from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from jedi_devproject.artifacts import write_candidate_artifact
from jedi_devproject.candidates import generate_template_candidate
from jedi_devproject.enrichment import StoryEnrichmentResult, enrich_story
from jedi_devproject.fulfillment import FulfillmentRoute, determine_fulfillment_route
from jedi_devproject.models import CandidateStatus, Story, UpdateSetCandidate
from jedi_devproject.planning import RunMetrics, collect_metrics
from jedi_devproject.rag import SpecializedRags
from jedi_devproject.safety import (
    AllowlistPolicy,
    EligibilityDecision,
    EligibilityResult,
    evaluate_story,
)


class PipelineInputs(BaseModel):
    stories: list[Story]
    policy: AllowlistPolicy
    rags: SpecializedRags
    artifact_root: Path
    run_id: str

    model_config = {"arbitrary_types_allowed": True}


class PipelineResult(BaseModel):
    metrics: RunMetrics
    candidates: list[UpdateSetCandidate]
    enrichment_results: list[StoryEnrichmentResult]
    artifact_paths: list[Path]
    summary: dict[str, Any]


def run_pipeline(inputs: PipelineInputs) -> PipelineResult:
    eligibility_results: list[EligibilityResult] = []
    enrichment_results: list[StoryEnrichmentResult] = []
    candidates: list[UpdateSetCandidate] = []
    artifact_paths: list[Path] = []

    for story in inputs.stories:
        enrichment_result = enrich_story(story)
        enrichment_results.append(enrichment_result)
        safety_result = evaluate_story(enrichment_result.enriched_story, inputs.policy)
        eligibility_results.append(safety_result)

        if safety_result.decision is not EligibilityDecision.ELIGIBLE:
            continue

        candidate = generate_template_candidate(
            story=enrichment_result.enriched_story,
            safety_result=safety_result,
            rags=inputs.rags,
        )
        candidates.append(candidate)

        if candidate.status is CandidateStatus.READY_FOR_REVIEW:
            artifact_paths.append(
                write_candidate_artifact(
                    inputs.artifact_root,
                    run_id=inputs.run_id,
                    candidate=candidate,
                )
            )

    metrics = collect_metrics(
        eligibility_results=eligibility_results,
        candidates=candidates,
    )
    fulfillment_routes = [determine_fulfillment_route(candidate) for candidate in candidates]
    summary = {
        "run_id": inputs.run_id,
        "stories_processed": len(inputs.stories),
        "eligible": metrics.eligible,
        "manual_review": metrics.manual_review,
        "rejected": metrics.rejected,
        "generated_candidates": metrics.generated_candidates,
        "artifact_count": len(artifact_paths),
        "enriched_stories": sum(1 for result in enrichment_results if result.inferred_tables),
        "enrichment_manual_review": sum(
            1
            for result, eligibility in zip(enrichment_results, eligibility_results, strict=True)
            if not result.inferred_tables
            and not result.original_story.affected_tables
            and eligibility.decision is EligibilityDecision.MANUAL_REVIEW
        ),
        "inferred_tables": sum(len(result.inferred_tables) for result in enrichment_results),
        "automated_development_candidates": sum(
            1 for route in fulfillment_routes if route is FulfillmentRoute.AUTOMATED_DEVELOPMENT
        ),
    }
    return PipelineResult(
        metrics=metrics,
        candidates=candidates,
        enrichment_results=enrichment_results,
        artifact_paths=artifact_paths,
        summary=summary,
    )
