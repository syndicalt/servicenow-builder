"""Assessment construction, maturity thresholds, and operator feedback."""

from __future__ import annotations

from jedi_devproject.automation_intent import AutomationIntent
from jedi_devproject.capabilities import (
    Capability,
    FieldFormIntent,
    StoryCapabilityAssessment,
    SuitabilityOutcome,
)
from jedi_devproject.models import Story
from jedi_devproject.risk import RiskInput, calculate_risk_score

FULL_MATURITY_MAX_AUTOMATED_POINTS = 5
CURRENT_AUTOMATION_MAX_POINTS = 3


def _assessment(
    *,
    story: Story,
    outcome: SuitabilityOutcome,
    requested: set[Capability],
    supported: set[Capability],
    intent: FieldFormIntent | None,
    target_table: str | None,
    reasons: list[str],
    missing_details: list[str],
    unsupported: set[Capability],
    required_instance_context: list[str] | None = None,
    automation_intent: AutomationIntent | None = None,
) -> StoryCapabilityAssessment:
    risk_target_table = target_table or "unknown"
    field_name = intent.field_name if intent is not None else None
    risk_score = calculate_risk_score(
        RiskInput(
            story_type="dictionary_form" if intent is not None else "unknown",
            affected_tables=sorted(capability.value for capability in requested),
            target_table=risk_target_table,
            field_name=field_name,
        )
    )
    confidence = 0.82 if outcome is SuitabilityOutcome.AUTOMATED_BUILD else 0.65
    operator_feedback, suggested_story = _automation_feedback(
        story=story,
        outcome=outcome,
        requested=requested,
        reasons=reasons,
        missing_details=missing_details,
        unsupported=unsupported,
        target_table=target_table,
    )
    return StoryCapabilityAssessment(
        story_number=story.number,
        outcome=outcome,
        capabilities=requested,
        supported_capabilities=supported,
        intent=intent,
        target_table=target_table,
        required_instance_context=required_instance_context or [],
        reasons=reasons,
        missing_details=missing_details,
        unsupported_capabilities=unsupported,
        automation_intent=(
            automation_intent.model_dump(mode="json") if automation_intent is not None else None
        ),
        operator_feedback=operator_feedback,
        suggested_story=suggested_story,
        risk_score=risk_score,
        confidence=confidence,
    )


def _automation_feedback(
    *,
    story: Story,
    outcome: SuitabilityOutcome,
    requested: set[Capability],
    reasons: list[str],
    missing_details: list[str],
    unsupported: set[Capability],
    target_table: str | None,
) -> tuple[list[str], str | None]:
    if outcome is SuitabilityOutcome.AUTOMATED_BUILD:
        return [], None
    feedback: list[str] = []
    if missing_details:
        feedback.append(
            "Add the missing automation details to the story: "
            f"{', '.join(missing_details)}."
        )
    if unsupported:
        feedback.append(
            "The current request includes capabilities outside the automated build "
            f"pipeline: {', '.join(sorted(item.value for item in unsupported))}."
        )
    if any(reason.startswith("story points exceed") for reason in reasons):
        feedback.append(
            "Split the request into smaller stories at or below the current automation "
            f"limit of {CURRENT_AUTOMATION_MAX_POINTS} points."
        )
    if not feedback:
        feedback.append(
            "Rewrite the story with explicit target artifact type, scope, expected "
            "behavior, test evidence, and any no-auto-mutation constraints."
        )
    return feedback, _suggested_story_rewrite(
        story=story,
        requested=requested,
        missing_details=missing_details,
        target_table=target_table,
    )


def _suggested_story_rewrite(
    *,
    story: Story,
    requested: set[Capability],
    missing_details: list[str],
    target_table: str | None,
) -> str:
    artifact_type = _suggested_artifact_type(requested)
    table_line = target_table or "<target table or ServiceNow surface>"
    missing_line = ", ".join(missing_details) if missing_details else "none"
    source_story = " ".join(
        part
        for part in [story.short_description, story.description, story.acceptance_criteria or ""]
        if part
    ).strip()
    return (
        f"Target artifact type: {artifact_type}\n"
        f"Target table: {table_line}\n"
        f"Requested change: {source_story}\n"
        "Decision needed: State whether this should be an automated build, "
        "analysis-only recommendation, or manual developer build.\n"
        "Required details: target surface, fields or records read, fields or records "
        "changed, constraints, expected behavior, test evidence, and rollback expectation.\n"
        f"Missing from current story: {missing_line}.\n"
        "Acceptance criteria: Provide concrete Given/When/Then criteria that can be "
        "verified in ServiceNow after the candidate is produced."
    )


def _suggested_artifact_type(requested: set[Capability]) -> str:
    if not requested or Capability.UNKNOWN in requested:
        return "<supported ServiceNow artifact type>"
    labels = {
        Capability.CATALOG_ITEM_CREATE: "Catalog Item",
        Capability.BUSINESS_RULE_ANALYZE: "Business Rule Analysis",
        Capability.BUSINESS_RULE_GENERATE: "Business Rule",
        Capability.CLIENT_SCRIPT_ANALYZE: "Client Script Analysis",
        Capability.CLIENT_SCRIPT_GENERATE: "Client Script",
        Capability.SCRIPT_INCLUDE_ANALYZE: "Script Include Analysis",
        Capability.SCRIPT_INCLUDE_GENERATE: "Script Include",
        Capability.UI_POLICY_GENERATE: "UI Policy",
        Capability.DICTIONARY_FIELD_CREATE: "Dictionary Field and Form Placement",
        Capability.FIELD_LABEL_CREATE: "Dictionary Field and Form Placement",
        Capability.FORM_LAYOUT_PLACE_FIELD: "Dictionary Field and Form Placement",
        Capability.FORM_SECTION_REMOVE: "Form Section Removal",
        Capability.CMDB_IRE_ANALYZE: "CMDB IRE Analysis",
        Capability.CMDB_IRE_GENERATE: "CMDB IRE Rules",
        Capability.CHOICE_VALUES_CREATE: "Choice Values",
        Capability.ACL_MODIFY: "ACL",
        Capability.FLOW_MODIFY: "Flow Designer",
        Capability.BUSINESS_RULE_CREATE: "Business Rule",
        Capability.SCRIPT_INCLUDE_MODIFY: "Script Include",
        Capability.DATA_MIGRATION: "Data Migration",
        Capability.INTEGRATION_MODIFY: "Integration",
    }
    return ", ".join(
        dict.fromkeys(labels.get(capability, capability.value) for capability in sorted(requested))
    )
