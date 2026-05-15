from __future__ import annotations

import re

from jedi_devproject.capabilities import (
    Capability,
    FieldFormIntent,
    StoryCapabilityAssessment,
    SuitabilityOutcome,
    capability_profile,
)
from jedi_devproject.models import Story
from jedi_devproject.risk import RiskInput, calculate_risk_score

SUPPORTED_BASELINE_CAPABILITIES = {
    Capability.BUSINESS_RULE_ANALYZE,
    Capability.DICTIONARY_FIELD_CREATE,
    Capability.FIELD_LABEL_CREATE,
    Capability.FORM_LAYOUT_PLACE_FIELD,
}

MAX_AUTOMATED_POINTS = 3


def analyze_story_capabilities(
    story: Story,
    *,
    supported_capabilities: set[Capability] = SUPPORTED_BASELINE_CAPABILITIES,
) -> StoryCapabilityAssessment:
    text = _story_text(story)
    requested = _requested_capabilities(text)
    missing_details = _missing_details(text)
    unsupported = requested - supported_capabilities
    intent = _field_form_intent(story, text) if _is_dictionary_form_request(text) else None
    target_table = intent.target_table if intent is not None else _target_table(text)
    reasons: list[str] = []

    if story.story_points > MAX_AUTOMATED_POINTS:
        reasons.append(
            f"story points exceed max: {story.story_points:.1f} > {MAX_AUTOMATED_POINTS}"
        )
        return _assessment(
            story=story,
            outcome=SuitabilityOutcome.MANUAL_DEVELOPER_BUILD,
            requested=requested,
            supported=supported_capabilities,
            intent=intent,
            target_table=target_table,
            reasons=reasons,
            missing_details=missing_details,
            unsupported=unsupported,
        )

    if unsupported:
        reasons.append("request includes unsupported pipeline capabilities")
        return _assessment(
            story=story,
            outcome=SuitabilityOutcome.UNSUPPORTED_CAPABILITY,
            requested=requested,
            supported=supported_capabilities,
            intent=intent,
            target_table=target_table,
            reasons=reasons,
            missing_details=missing_details,
            unsupported=unsupported,
        )

    if missing_details:
        reasons.append("story is missing required automation details")
        return _assessment(
            story=story,
            outcome=SuitabilityOutcome.NEEDS_CLARIFICATION,
            requested=requested,
            supported=supported_capabilities,
            intent=intent,
            target_table=target_table,
            reasons=reasons,
            missing_details=missing_details,
            unsupported=unsupported,
        )

    if Capability.BUSINESS_RULE_ANALYZE in requested and not _is_dictionary_form_request(text):
        profile = capability_profile(Capability.BUSINESS_RULE_ANALYZE)
        reasons.extend(
            [
                "Business Rule analysis first",
                "business rule generation is not enabled yet",
            ]
        )
        return _assessment(
            story=story,
            outcome=SuitabilityOutcome.CONTEXT_ANALYSIS,
            requested=requested,
            supported=supported_capabilities,
            intent=intent,
            target_table=target_table,
            reasons=reasons,
            missing_details=[],
            unsupported=set(),
            required_instance_context=profile.required_instance_context,
        )

    reasons.append("supported low-complexity dictionary/form request")
    return _assessment(
        story=story,
        outcome=SuitabilityOutcome.AUTOMATED_BUILD,
        requested=requested,
        supported=supported_capabilities,
        intent=intent,
        target_table=target_table,
        reasons=reasons,
        missing_details=[],
        unsupported=set(),
    )


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
        risk_score=risk_score,
        confidence=confidence,
    )


def _story_text(story: Story) -> str:
    return " ".join(
        part
        for part in [story.short_description, story.description, story.acceptance_criteria or ""]
        if part
    ).lower()


def _requested_capabilities(text: str) -> set[Capability]:
    capabilities: set[Capability] = set()
    if _is_dictionary_form_request(text):
        capabilities.update(
            {
                Capability.DICTIONARY_FIELD_CREATE,
                Capability.FIELD_LABEL_CREATE,
                Capability.FORM_LAYOUT_PLACE_FIELD,
            }
        )
    if "acl" in text or "only admins" in text or "only admin" in text:
        capabilities.add(Capability.ACL_MODIFY)
    if "workflow" in text or "flow designer" in text:
        capabilities.add(Capability.FLOW_MODIFY)
    if "business rule" in text or "server script" in text:
        capabilities.add(Capability.BUSINESS_RULE_ANALYZE)
    if "script include" in text:
        capabilities.add(Capability.SCRIPT_INCLUDE_MODIFY)
    if "migrat" in text:
        capabilities.add(Capability.DATA_MIGRATION)
    if "integrat" in text or "api" in text:
        capabilities.add(Capability.INTEGRATION_MODIFY)
    if not capabilities:
        capabilities.add(Capability.UNKNOWN)
    return capabilities


def _missing_details(text: str) -> list[str]:
    missing: list[str] = []
    if _is_dictionary_form_request(text) and _target_table(text) is None:
        missing.append("target table")
    if (
        _is_dictionary_form_request(text)
        and _field_label(text) is None
        and _field_name(text) is None
    ):
        missing.append("field label or field name")
    if _is_dictionary_form_request(text) and _field_type(text) is None:
        missing.append("field type")
    if _is_business_rule_request(text) and _target_table(text) is None:
        missing.append("target table")
    return missing


def _is_business_rule_request(text: str) -> bool:
    return "business rule" in text or "server script" in text


def _is_dictionary_form_request(text: str) -> bool:
    return ("field" in text or "column" in text) and "form" in text


def _field_form_intent(story: Story, text: str) -> FieldFormIntent | None:
    target_table = _target_table(text)
    field_label = _field_label(text)
    field_name = _field_name(text)
    field_type = _field_type(text)
    if target_table is None or field_type is None or (field_label is None and field_name is None):
        return None
    if field_label is None:
        if field_name is None:
            return None
        normalized_label = field_name.replace("u_", "").replace("_", " ").title()
    else:
        normalized_label = field_label
    return FieldFormIntent(
        target_table=target_table,
        field_label=normalized_label,
        field_name=field_name,
        field_type=field_type,
        reference_table=_reference_table(text),
        reference_qualifier=_reference_qualifier(text),
        max_length=_max_length(text),
        placement_anchor=_placement_anchor(text),
        placement_position=_placement_position(text),
        mandatory="mandatory" in text or "required" in text,
        default_value=str(story.additional_context.get("default_value", "")),
    )


def _target_table(text: str) -> str | None:
    if "incident" in text:
        return "incident"
    if "problem" in text:
        return "problem"
    if "rm_story" in text or "story form" in text or "story table" in text:
        return "rm_story"
    match = re.search(r"table named ([a-zA-Z0-9_]+)", text)
    if match:
        return match.group(1).lower()
    match = re.search(r"to the ([a-zA-Z0-9_]+) form", text)
    if match:
        return match.group(1).lower()
    return None


def _field_label(text: str) -> str | None:
    match = re.search(r"field labeled ([a-zA-Z0-9 _-]+?)(?: exists| is| on| below|\.|\n|$)", text)
    if match:
        return _title_label(match.group(1))
    match = re.search(r"field name: ([a-zA-Z0-9 _-]+)", text)
    if match:
        return _title_label(match.group(1))
    match = re.search(r"field named ([a-zA-Z0-9 _-]+?)(?: and| to| on| below|\.|\n|$)", text)
    if match:
        return _title_label(match.group(1))
    return None


def _field_name(text: str) -> str | None:
    match = re.search(r"\b(u_[a-zA-Z0-9_]+)\b", text)
    return match.group(1).lower() if match else None


def _field_type(text: str) -> str | None:
    match = re.search(r"field type: ([a-zA-Z0-9 _-]+)", text)
    if match:
        return _normalize_field_type(match.group(1))
    for candidate in ["reference", "string", "integer", "boolean", "date", "datetime", "journal"]:
        if candidate in text:
            return _normalize_field_type(candidate)
    if "characters" in text:
        return "string"
    if "custom field" in text:
        return "string"
    return None


def _normalize_field_type(value: str) -> str:
    cleaned = value.strip().lower().replace(" ", "_").replace("-", "_")
    if cleaned in {"date_time", "datetime"}:
        return "glide_date_time"
    if cleaned in {"journal", "journal_input"}:
        return "journal_input"
    return cleaned


def _max_length(text: str) -> int | None:
    match = re.search(r"length: ([0-9]+)", text)
    if match:
        return int(match.group(1))
    return None


def _reference_table(text: str) -> str | None:
    patterns = [
        r"reference the ([a-zA-Z0-9_]+) table",
        r"references ([a-zA-Z0-9_]+)(?: table|\.|\n| |$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            candidate = match.group(1).lower()
            if candidate != "field":
                return candidate
    return None


def _reference_qualifier(text: str) -> str | None:
    match = re.search(
        r"(?:reference qualifier of|where|only allow .* where) ([a-zA-Z0-9_]+=[^\\.\\n ]+)", text
    )
    if match:
        return match.group(1)
    return None


def _placement_anchor(text: str) -> str | None:
    if "below description" in text or "below the description" in text:
        return "description"
    match = re.search(r"below ([a-zA-Z0-9_ ]+?)(?: field|\.|\n|$)", text)
    if match:
        return match.group(1).strip().lower().replace(" ", "_")
    return None


def _placement_position(text: str) -> str:
    if "above " in text:
        return "above"
    if "below " in text:
        return "below"
    return "end"


def _title_label(value: str) -> str:
    cleaned = value.strip(" .:-")
    if cleaned.lower().startswith("u_"):
        cleaned = cleaned[2:]
    cleaned = cleaned.replace("_", " ")
    return " ".join(word.capitalize() for word in cleaned.split())
