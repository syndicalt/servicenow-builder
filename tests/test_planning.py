from jedi_devproject.models import CandidateStatus, DataClassification, Story, UpdateSetCandidate
from jedi_devproject.planning import collect_metrics, score_story, suggest_repointing
from jedi_devproject.safety import EligibilityDecision, EligibilityResult, StoryType


def _story(
    *,
    business_value: float | None = 8,
    risk: float | None = 1,
    effort_estimate: float | None = 2,
    story_points: float = 2,
    description: str = "Update portal help text.",
) -> Story:
    return Story(
        sys_id="abc123",
        number="STORY0010001",
        short_description="Update portal help text",
        description=description,
        story_points=story_points,
        priority=2,
        state="Ready",
        data_classification=DataClassification.PUBLIC,
        acceptance_criteria="Portal help text is updated.",
        business_value=business_value,
        risk=risk,
        effort_estimate=effort_estimate,
    )


def test_priority_score_uses_documented_formula() -> None:
    score = score_story(_story(), strategic_alignment=7, recency=5)

    expected = ((0.4 * 8) + (0.3 * 4) + (0.2 * 7) + (0.1 * 5)) / (2 + 1 + 0.1)
    assert score == expected


def test_missing_scoring_fields_degrade_to_zero_value_and_story_points_effort() -> None:
    score = score_story(
        _story(business_value=None, risk=None, effort_estimate=None, story_points=3),
        strategic_alignment=None,
        recency=None,
    )

    expected = ((0.4 * 0) + (0.3 * 4) + (0.2 * 0) + (0.1 * 0)) / (3 + 0 + 0.1)
    assert score == expected


def test_repointing_suggestion_never_mutates_original_story_points() -> None:
    story = _story(description="Integrate with downstream API.", story_points=2)

    suggestion = suggest_repointing(story)

    assert story.story_points == 2
    assert suggestion.original_points == 2
    assert suggestion.suggested_points == 5
    assert "integration complexity signal" in suggestion.evidence


def test_metrics_report_counts_decisions_and_generated_candidates() -> None:
    metrics = collect_metrics(
        eligibility_results=[
            EligibilityResult(
                decision=EligibilityDecision.ELIGIBLE,
                story_type=StoryType.CONTENT_ONLY,
                reasons=[],
            ),
            EligibilityResult(
                decision=EligibilityDecision.MANUAL_REVIEW,
                story_type=StoryType.UNKNOWN,
                reasons=[],
            ),
            EligibilityResult(
                decision=EligibilityDecision.REJECTED,
                story_type=StoryType.UNKNOWN,
                reasons=[],
            ),
        ],
        candidates=[
            UpdateSetCandidate(
                story_number="STORY0010001",
                name="UPD_STORY0010001_Content_Update",
                eligibility_decision="eligible",
                eligibility_reasons=[],
                confidence=0.9,
                risk_score=0.1,
                status=CandidateStatus.READY_FOR_REVIEW,
            )
        ],
    )

    assert metrics.eligible == 1
    assert metrics.manual_review == 1
    assert metrics.rejected == 1
    assert metrics.generated_candidates == 1
