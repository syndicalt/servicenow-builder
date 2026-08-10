from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from jedi_devproject.models import Story


class EligibilityDecision(StrEnum):
    ELIGIBLE = "eligible"
    MANUAL_REVIEW = "manual_review"
    REJECTED = "rejected"


class StoryType(StrEnum):
    CONTENT_ONLY = "content_only"
    DICTIONARY_FORM = "dictionary_form"
    UNKNOWN = "unknown"


class AllowlistPolicy(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    story_types: set[StoryType]
    tables: set[str]
    operations: set[str]
    max_points: float = 3


class EligibilityResult(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    decision: EligibilityDecision
    story_type: StoryType
    reasons: list[str] = Field(default_factory=list)


REJECTION_PATTERNS = {
    "acl": "security control change",
    "role": "role or group change",
    "group": "role or group change",
    "integrat": "external integration",
    "migrat": "data migration",
    "credential": "credential handling",
    "delete": "destructive delete",
}

CONTENT_PATTERNS = ("text", "label", "help", "copy", "message", "content")


def evaluate_story(
    story: Story,
    policy: AllowlistPolicy,
    *,
    proposed_operation: str = "update",
) -> EligibilityResult:
    text = f"{story.short_description} {story.description}".lower()
    rejection_reasons = _rejection_reasons(text)
    story_type = _classify_story_type(text)
    reasons: list[str] = []

    if rejection_reasons:
        return EligibilityResult(
            decision=EligibilityDecision.REJECTED,
            story_type=story_type,
            reasons=rejection_reasons,
        )

    if story.story_points > policy.max_points:
        reasons.append(f"story points exceed max: {story.story_points:.1f} > {policy.max_points:g}")

    if not story.acceptance_criteria or story.acceptance_criteria.strip() == "":
        reasons.append("missing acceptance criteria")

    if not story.affected_tables:
        reasons.append("missing affected tables")

    if story_type not in policy.story_types:
        reasons.append(f"story type not allowed: {story_type.value}")
    else:
        reasons.append(f"story type allowed: {story_type.value}")

    if proposed_operation not in policy.operations:
        reasons.append(f"operation not allowed: {proposed_operation}")
    else:
        reasons.append(f"operation allowed: {proposed_operation}")

    for table in story.affected_tables:
        if table in policy.tables:
            reasons.append(f"table allowed: {table}")
        else:
            reasons.append(f"table not allowed: {table}")

    manual_review_prefixes = (
        "story points exceed",
        "missing",
        "story type not",
        "table not",
        "operation not",
    )
    if any(reason.startswith(manual_review_prefixes) for reason in reasons):
        return EligibilityResult(
            decision=EligibilityDecision.MANUAL_REVIEW,
            story_type=story_type,
            reasons=reasons,
        )

    return EligibilityResult(
        decision=EligibilityDecision.ELIGIBLE,
        story_type=story_type,
        reasons=reasons,
    )


def _rejection_reasons(text: str) -> list[str]:
    return [reason for pattern, reason in REJECTION_PATTERNS.items() if pattern in text]


def _classify_story_type(text: str) -> StoryType:
    if _is_dictionary_form_story(text):
        return StoryType.DICTIONARY_FORM

    if any(pattern in text for pattern in CONTENT_PATTERNS):
        return StoryType.CONTENT_ONLY
    return StoryType.UNKNOWN


def _is_dictionary_form_story(text: str) -> bool:
    has_field_signal = "field" in text or "column" in text or "u_" in text
    has_form_signal = "form" in text or "place" in text
    has_table_signal = "table" in text or "rm_story" in text
    return has_field_signal and has_form_signal and has_table_signal
