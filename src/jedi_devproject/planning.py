from __future__ import annotations

from pydantic import BaseModel

from jedi_devproject.models import Story, UpdateSetCandidate
from jedi_devproject.safety import EligibilityDecision, EligibilityResult


class RepointingSuggestion(BaseModel):
    story_number: str
    original_points: float
    suggested_points: float
    evidence: list[str]


class RunMetrics(BaseModel):
    eligible: int
    manual_review: int
    rejected: int
    generated_candidates: int


def score_story(
    story: Story,
    *,
    strategic_alignment: float | None,
    recency: float | None,
) -> float:
    business_value = story.business_value or 0
    urgency = 6 - story.priority
    alignment = strategic_alignment or 0
    recency_value = recency or 0
    effort = story.effort_estimate if story.effort_estimate is not None else story.story_points
    risk = story.risk or 0

    numerator = (
        (0.4 * business_value)
        + (0.3 * urgency)
        + (0.2 * alignment)
        + (0.1 * recency_value)
    )
    return numerator / (effort + risk + 0.1)


def suggest_repointing(story: Story) -> RepointingSuggestion:
    text = f"{story.short_description} {story.description}".lower()
    evidence: list[str] = []
    suggested_points = story.story_points

    if "integrat" in text or "api" in text:
        suggested_points = max(suggested_points, 5)
        evidence.append("integration complexity signal")

    if not evidence:
        evidence.append("no deterministic complexity signal")

    return RepointingSuggestion(
        story_number=story.number,
        original_points=story.story_points,
        suggested_points=suggested_points,
        evidence=evidence,
    )


def collect_metrics(
    *,
    eligibility_results: list[EligibilityResult],
    candidates: list[UpdateSetCandidate],
) -> RunMetrics:
    return RunMetrics(
        eligible=_count(eligibility_results, EligibilityDecision.ELIGIBLE),
        manual_review=_count(eligibility_results, EligibilityDecision.MANUAL_REVIEW),
        rejected=_count(eligibility_results, EligibilityDecision.REJECTED),
        generated_candidates=len(candidates),
    )


def _count(results: list[EligibilityResult], decision: EligibilityDecision) -> int:
    return sum(1 for result in results if result.decision is decision)
