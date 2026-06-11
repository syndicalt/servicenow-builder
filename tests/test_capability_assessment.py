from __future__ import annotations

from jedi_devproject.capabilities import (
    Capability,
    StoryCapabilityAssessment,
    SuitabilityOutcome,
)
from jedi_devproject.capability_assessment import (
    INTAKE_FEEDBACK_SCHEMA_VERSION,
    build_intake_feedback,
    intake_feedback_work_note,
)


def _assessment(
    *,
    outcome: SuitabilityOutcome,
    capabilities: set[Capability] | None = None,
    reasons: list[str] | None = None,
    missing_details: list[str] | None = None,
    unsupported_capabilities: set[Capability] | None = None,
    operator_feedback: list[str] | None = None,
    suggested_story: str | None = "Target artifact type: Dictionary Field",
) -> StoryCapabilityAssessment:
    return StoryCapabilityAssessment(
        story_number="STRY0010013",
        outcome=outcome,
        capabilities=capabilities or {Capability.DICTIONARY_FIELD_CREATE},
        supported_capabilities={Capability.DICTIONARY_FIELD_CREATE},
        reasons=reasons or [],
        missing_details=missing_details or [],
        unsupported_capabilities=unsupported_capabilities or set(),
        operator_feedback=operator_feedback or [],
        suggested_story=suggested_story,
        risk_score=0.4,
        confidence=0.65,
    )


def test_gate_passing_assessment_produces_no_intake_feedback() -> None:
    assessment = _assessment(
        outcome=SuitabilityOutcome.AUTOMATED_BUILD,
        operator_feedback=[],
        suggested_story=None,
    )

    assert build_intake_feedback(assessment) is None


def test_context_analysis_assessment_produces_no_intake_feedback() -> None:
    assessment = _assessment(
        outcome=SuitabilityOutcome.CONTEXT_ANALYSIS,
        reasons=["Code surface analysis first"],
    )

    assert build_intake_feedback(assessment) is None


def test_missing_detail_feedback_has_stable_codes_and_capability_guidance() -> None:
    assessment = _assessment(
        outcome=SuitabilityOutcome.NEEDS_CLARIFICATION,
        reasons=["story is missing required automation details"],
        missing_details=["field type", "target table"],
        operator_feedback=[
            "Add the missing automation details to the story: field type, target table."
        ],
    )

    feedback = build_intake_feedback(assessment)

    assert feedback is not None
    assert feedback.schema_version == INTAKE_FEEDBACK_SCHEMA_VERSION
    assert feedback.story_number == "STRY0010013"
    assert feedback.reason_codes == [
        "missing_detail:field_type",
        "missing_detail:target_table",
    ]
    assert feedback.suggested_story == "Target artifact type: Dictionary Field"
    assert (
        "Missing detail 'field type' blocks the Dictionary Field and Form Placement "
        "automated build path; add it to the story before resubmitting."
        in feedback.guidance
    )
    assert feedback.guidance[0].startswith("Add the missing automation details")


def test_unsupported_capability_and_point_limit_feedback_codes() -> None:
    assessment = _assessment(
        outcome=SuitabilityOutcome.MANUAL_DEVELOPER_BUILD,
        capabilities={Capability.FLOW_MODIFY},
        reasons=["story points exceed current automation max: 4.0 > 3"],
        unsupported_capabilities={Capability.FLOW_MODIFY},
        operator_feedback=["Split the request into smaller stories."],
    )

    feedback = build_intake_feedback(assessment)

    assert feedback is not None
    assert feedback.reason_codes == [
        "unsupported_capability:flow_modify",
        "story_points_exceed_current_automation_max",
    ]


def test_full_maturity_point_limit_feedback_code() -> None:
    assessment = _assessment(
        outcome=SuitabilityOutcome.MANUAL_DEVELOPER_BUILD,
        reasons=["story points exceed full-maturity max: 8.0 > 5"],
        operator_feedback=["Split the request into smaller stories."],
    )

    feedback = build_intake_feedback(assessment)

    assert feedback is not None
    assert feedback.reason_codes == ["story_points_exceed_full_maturity_max"]


def test_forbidden_behavior_and_fallback_feedback_codes() -> None:
    forbidden = _assessment(
        outcome=SuitabilityOutcome.MANUAL_DEVELOPER_BUILD,
        reasons=[
            "business rule generation includes forbidden behavior: "
            "cross-table updates, outbound integration calls"
        ],
        operator_feedback=["Rewrite the story without forbidden behavior."],
    )
    fallback = _assessment(
        outcome=SuitabilityOutcome.MANUAL_DEVELOPER_BUILD,
        reasons=["manual review requested"],
        operator_feedback=["Rewrite the story with explicit target artifact type."],
    )

    forbidden_feedback = build_intake_feedback(forbidden)
    fallback_feedback = build_intake_feedback(fallback)

    assert forbidden_feedback is not None
    assert forbidden_feedback.reason_codes == [
        "forbidden_behavior:cross_table_updates",
        "forbidden_behavior:outbound_integration_calls",
    ]
    assert fallback_feedback is not None
    assert fallback_feedback.reason_codes == ["gate_failure:manual_developer_build"]


def test_content_hash_is_deterministic_and_content_sensitive() -> None:
    assessment = _assessment(
        outcome=SuitabilityOutcome.NEEDS_CLARIFICATION,
        missing_details=["field type"],
        operator_feedback=["Add the missing automation details to the story: field type."],
    )
    changed = assessment.model_copy(update={"missing_details": ["target table"]})

    first = build_intake_feedback(assessment)
    second = build_intake_feedback(assessment)
    third = build_intake_feedback(changed)

    assert first is not None and second is not None and third is not None
    assert first.content_hash == second.content_hash
    assert first.content_hash != third.content_hash


def test_intake_work_note_includes_reason_codes_guidance_and_rewrite() -> None:
    assessment = _assessment(
        outcome=SuitabilityOutcome.NEEDS_CLARIFICATION,
        missing_details=["field type"],
        operator_feedback=["Add the missing automation details to the story: field type."],
        suggested_story="Target artifact type: Dictionary Field\nTarget table: rm_story",
    )

    feedback = build_intake_feedback(assessment)
    assert feedback is not None
    note = intake_feedback_work_note(feedback)

    assert "Intake automation assessment for STRY0010013" in note
    assert "missing_detail:field_type" in note
    assert "Add the missing automation details to the story: field type." in note
    assert "Suggested rewrite:\nTarget artifact type: Dictionary Field" in note


def test_intake_work_note_omits_rewrite_section_when_no_rewrite_exists() -> None:
    assessment = _assessment(
        outcome=SuitabilityOutcome.MANUAL_DEVELOPER_BUILD,
        reasons=["manual review requested"],
        operator_feedback=["Rewrite the story with explicit target artifact type."],
        suggested_story=None,
    )

    feedback = build_intake_feedback(assessment)
    assert feedback is not None
    note = intake_feedback_work_note(feedback)

    assert "gate_failure:manual_developer_build" in note
    assert "Suggested rewrite:" not in note
