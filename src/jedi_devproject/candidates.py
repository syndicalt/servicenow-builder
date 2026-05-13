from __future__ import annotations

from jedi_devproject.models import (
    CandidateChange,
    CandidateStatus,
    Story,
    UpdateSetCandidate,
    stable_artifact_hash,
)
from jedi_devproject.rag import SpecializedRags
from jedi_devproject.risk import RiskInput, calculate_risk_score
from jedi_devproject.safety import EligibilityDecision, EligibilityResult, StoryType


def generate_template_candidate(
    *,
    story: Story,
    safety_result: EligibilityResult,
    rags: SpecializedRags,
) -> UpdateSetCandidate:
    if safety_result.decision is not EligibilityDecision.ELIGIBLE:
        return _manual_candidate(story=story, safety_result=safety_result)

    if safety_result.story_type is not StoryType.CONTENT_ONLY:
        if safety_result.story_type is StoryType.DICTIONARY_FORM:
            return _dictionary_form_candidate(story=story, safety_result=safety_result)
        return _manual_candidate(story=story, safety_result=safety_result)

    context = rags.retrieve_required_context("portal")
    citations = [result.citation for results in context.values() for result in results]
    candidate = UpdateSetCandidate(
        story_number=story.number,
        name=f"UPD_{story.number}_Content_Update",
        eligibility_decision="eligible",
        eligibility_reasons=safety_result.reasons,
        changes=[
            CandidateChange(
                table=story.affected_tables[0],
                operation="update",
                fields={"description": story.description},
                rationale="Template-only content update candidate for reviewer validation.",
            )
        ],
        confidence=0.9,
        risk_score=0.1,
        status=CandidateStatus.READY_FOR_REVIEW,
        retrieval_citations=citations,
        assumptions=["Story describes a content-only text change."],
        reviewer_notes=[
            "Review the proposed content field mapping before export.",
            "Validate in a ServiceNow development or sandbox instance only.",
        ],
    )
    return _with_artifact_hash(candidate)


def _manual_candidate(*, story: Story, safety_result: EligibilityResult) -> UpdateSetCandidate:
    candidate = UpdateSetCandidate(
        story_number=story.number,
        name=f"UPD_{story.number}_Manual_Build",
        eligibility_decision=safety_result.decision.value,
        eligibility_reasons=safety_result.reasons,
        confidence=0.0,
        risk_score=1.0,
        status=CandidateStatus.MANUAL_BUILD,
        reviewer_notes=["Template generation skipped; route this story to manual build."],
    )
    return _with_artifact_hash(candidate)


def _dictionary_form_candidate(
    *,
    story: Story,
    safety_result: EligibilityResult,
) -> UpdateSetCandidate:
    candidate = UpdateSetCandidate(
        story_number=story.number,
        name=f"UPD_{story.number}_AI_Review_Notes_Field",
        eligibility_decision="eligible",
        eligibility_reasons=safety_result.reasons,
        changes=[
            CandidateChange(
                table="sys_dictionary",
                operation="insert",
                fields={
                    "name": "rm_story",
                    "element": "u_ai_review_notes",
                    "column_label": "AI Review Notes",
                    "internal_type": "string",
                    "max_length": "8000",
                    "mandatory": "false",
                },
                rationale="Create the AI Review Notes field on rm_story.",
            ),
            CandidateChange(
                table="sys_ui_form",
                operation="update",
                fields={
                    "table": "rm_story",
                    "field": "u_ai_review_notes",
                    "position_hint": "Notes section below Description",
                },
                rationale="Place the new field on the Story form for reviewer validation.",
            ),
        ],
        confidence=0.82,
        risk_score=calculate_risk_score(
            RiskInput(
                story_type="dictionary_form",
                affected_tables=["sys_dictionary", "sys_ui_form"],
                target_table="rm_story",
                field_name="u_ai_review_notes",
                mandatory=False,
                has_default=False,
            )
        ),
        status=CandidateStatus.READY_FOR_REVIEW,
        assumptions=[
            "The requested field is rm_story.u_ai_review_notes.",
            "The form placement target is the Story form Notes section below Description.",
        ],
        reviewer_notes=[
            "Review the dictionary field and form layout records before export.",
            "Confirm max length 8000 is acceptable for the target instance.",
        ],
    )
    return _with_artifact_hash(candidate)


def _with_artifact_hash(candidate: UpdateSetCandidate) -> UpdateSetCandidate:
    payload = candidate.model_dump(mode="json", exclude={"artifact_hash"})
    return candidate.model_copy(update={"artifact_hash": stable_artifact_hash(payload)})
