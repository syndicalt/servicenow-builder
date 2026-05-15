from __future__ import annotations

import re

from jedi_devproject.automation_intent import (
    AutomationIntent,
    AutomationIntentType,
    extract_automation_intent,
)
from jedi_devproject.capabilities import (
    Capability,
    FieldFormIntent,
    StoryCapabilityAssessment,
    SuitabilityOutcome,
    capability_profile,
)
from jedi_devproject.models import Story
from jedi_devproject.requirement_text import positive_requirement_text
from jedi_devproject.risk import RiskInput, calculate_risk_score

SUPPORTED_BASELINE_CAPABILITIES = {
    Capability.BUSINESS_RULE_ANALYZE,
    Capability.BUSINESS_RULE_GENERATE,
    Capability.CLIENT_SCRIPT_ANALYZE,
    Capability.CLIENT_SCRIPT_GENERATE,
    Capability.SCRIPT_INCLUDE_ANALYZE,
    Capability.SCRIPT_INCLUDE_GENERATE,
    Capability.UI_POLICY_GENERATE,
    Capability.DICTIONARY_FIELD_CREATE,
    Capability.FIELD_LABEL_CREATE,
    Capability.FORM_LAYOUT_PLACE_FIELD,
}

FULL_MATURITY_MAX_AUTOMATED_POINTS = 5
CURRENT_AUTOMATION_MAX_POINTS = 3


def analyze_story_capabilities(
    story: Story,
    *,
    supported_capabilities: set[Capability] = SUPPORTED_BASELINE_CAPABILITIES,
) -> StoryCapabilityAssessment:
    automation_intent = extract_automation_intent(story)
    if automation_intent.is_structured:
        return _assess_automation_intent(
            story=story,
            automation_intent=automation_intent,
            supported_capabilities=supported_capabilities,
        )

    text = _story_text(story)
    positive_text = _positive_requirement_text(text)
    requested = _requested_capabilities(positive_text)
    missing_details = _missing_details(positive_text)
    unsupported = requested - supported_capabilities
    intent = _field_form_intent(story, text) if _is_dictionary_form_request(positive_text) else None
    target_table = intent.target_table if intent is not None else _target_table(positive_text)
    reasons: list[str] = []

    if story.story_points > FULL_MATURITY_MAX_AUTOMATED_POINTS:
        reasons.append(
            "story points exceed full-maturity max: "
            f"{story.story_points:.1f} > {FULL_MATURITY_MAX_AUTOMATED_POINTS}"
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

    if story.story_points > CURRENT_AUTOMATION_MAX_POINTS:
        reasons.append(
            "story points exceed current automation max: "
            f"{story.story_points:.1f} > {CURRENT_AUTOMATION_MAX_POINTS}"
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

    forbidden_business_rule_details = _business_rule_forbidden_details(positive_text)
    if Capability.BUSINESS_RULE_GENERATE in requested and forbidden_business_rule_details:
        reasons.append(
            "business rule generation includes forbidden behavior: "
            f"{', '.join(forbidden_business_rule_details)}"
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

    forbidden_client_script_details = _client_script_forbidden_details(positive_text)
    if Capability.CLIENT_SCRIPT_GENERATE in requested and forbidden_client_script_details:
        reasons.append(
            "client script generation includes forbidden behavior: "
            f"{', '.join(forbidden_client_script_details)}"
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

    forbidden_script_include_details = _script_include_forbidden_details(positive_text)
    if Capability.SCRIPT_INCLUDE_GENERATE in requested and forbidden_script_include_details:
        reasons.append(
            "script include generation includes forbidden behavior: "
            f"{', '.join(forbidden_script_include_details)}"
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

    forbidden_ui_policy_details = _ui_policy_forbidden_details(positive_text)
    if Capability.UI_POLICY_GENERATE in requested and forbidden_ui_policy_details:
        reasons.append(
            "ui policy generation includes forbidden behavior: "
            f"{', '.join(forbidden_ui_policy_details)}"
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

    code_surface_capability = _code_surface_capability(requested)
    if code_surface_capability is not None and not _is_dictionary_form_request(positive_text):
        profile = capability_profile(code_surface_capability)
        code_surface_label = code_surface_capability.value.removesuffix("_analyze").replace(
            "_", " "
        )
        reasons.extend(
            [
                "Code surface analysis first",
                f"{code_surface_label} generation is not enabled yet",
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

    if Capability.BUSINESS_RULE_GENERATE in requested:
        profile = capability_profile(Capability.BUSINESS_RULE_GENERATE)
        reasons.append("supported table-local business rule generation request")
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
            required_instance_context=profile.required_instance_context,
        )

    if Capability.CLIENT_SCRIPT_GENERATE in requested:
        profile = capability_profile(Capability.CLIENT_SCRIPT_GENERATE)
        reasons.append("supported table-local client script generation request")
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
            required_instance_context=profile.required_instance_context,
        )

    if Capability.SCRIPT_INCLUDE_GENERATE in requested:
        profile = capability_profile(Capability.SCRIPT_INCLUDE_GENERATE)
        reasons.append("supported utility script include generation request")
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
            required_instance_context=profile.required_instance_context,
        )

    if Capability.UI_POLICY_GENERATE in requested:
        profile = capability_profile(Capability.UI_POLICY_GENERATE)
        reasons.append("supported declarative ui policy generation request")
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


AUTOMATED_INTENT_REASONS = {
    Capability.BUSINESS_RULE_GENERATE: "supported table-local business rule generation request",
    Capability.CLIENT_SCRIPT_GENERATE: "supported table-local client script generation request",
    Capability.SCRIPT_INCLUDE_GENERATE: "supported utility script include generation request",
    Capability.UI_POLICY_GENERATE: "supported declarative ui policy generation request",
    Capability.DICTIONARY_FIELD_CREATE: "supported low-complexity dictionary/form request",
}


def _assess_automation_intent(
    *,
    story: Story,
    automation_intent: AutomationIntent,
    supported_capabilities: set[Capability],
) -> StoryCapabilityAssessment:
    requested = _capabilities_for_automation_intent(automation_intent)
    unsupported = requested - supported_capabilities
    field_form_intent = _field_form_intent_from_automation_intent(story, automation_intent)
    target_table = (
        field_form_intent.target_table
        if field_form_intent is not None
        else automation_intent.target_table
    )
    reasons: list[str] = []

    if story.story_points > FULL_MATURITY_MAX_AUTOMATED_POINTS:
        reasons.append(
            "story points exceed full-maturity max: "
            f"{story.story_points:.1f} > {FULL_MATURITY_MAX_AUTOMATED_POINTS}"
        )
        return _assessment(
            story=story,
            outcome=SuitabilityOutcome.MANUAL_DEVELOPER_BUILD,
            requested=requested,
            supported=supported_capabilities,
            intent=field_form_intent,
            target_table=target_table,
            reasons=reasons,
            missing_details=automation_intent.missing_details,
            unsupported=unsupported,
            automation_intent=automation_intent,
        )

    if story.story_points > CURRENT_AUTOMATION_MAX_POINTS:
        reasons.append(
            "story points exceed current automation max: "
            f"{story.story_points:.1f} > {CURRENT_AUTOMATION_MAX_POINTS}"
        )
        return _assessment(
            story=story,
            outcome=SuitabilityOutcome.MANUAL_DEVELOPER_BUILD,
            requested=requested,
            supported=supported_capabilities,
            intent=field_form_intent,
            target_table=target_table,
            reasons=reasons,
            missing_details=automation_intent.missing_details,
            unsupported=unsupported,
            automation_intent=automation_intent,
        )

    forbidden_details = _automation_intent_forbidden_details(automation_intent)
    if forbidden_details:
        reasons.append(
            f"{automation_intent.intent_type.value.replace('_', ' ')} generation "
            f"includes forbidden behavior: {', '.join(forbidden_details)}"
        )
        return _assessment(
            story=story,
            outcome=SuitabilityOutcome.MANUAL_DEVELOPER_BUILD,
            requested=requested,
            supported=supported_capabilities,
            intent=field_form_intent,
            target_table=target_table,
            reasons=reasons,
            missing_details=automation_intent.missing_details,
            unsupported=unsupported,
            automation_intent=automation_intent,
        )

    if unsupported:
        reasons.append("request includes unsupported pipeline capabilities")
        return _assessment(
            story=story,
            outcome=SuitabilityOutcome.UNSUPPORTED_CAPABILITY,
            requested=requested,
            supported=supported_capabilities,
            intent=field_form_intent,
            target_table=target_table,
            reasons=reasons,
            missing_details=automation_intent.missing_details,
            unsupported=unsupported,
            automation_intent=automation_intent,
        )

    if automation_intent.missing_details:
        reasons.append("story is missing required automation details")
        return _assessment(
            story=story,
            outcome=SuitabilityOutcome.NEEDS_CLARIFICATION,
            requested=requested,
            supported=supported_capabilities,
            intent=field_form_intent,
            target_table=target_table,
            reasons=reasons,
            missing_details=automation_intent.missing_details,
            unsupported=unsupported,
            automation_intent=automation_intent,
        )

    reasons.append(
        AUTOMATED_INTENT_REASONS.get(
            automation_intent.capability,
            "supported structured automation request",
        )
    )
    return _assessment(
        story=story,
        outcome=SuitabilityOutcome.AUTOMATED_BUILD,
        requested=requested,
        supported=supported_capabilities,
        intent=field_form_intent,
        target_table=target_table,
        reasons=reasons,
        missing_details=[],
        unsupported=set(),
        required_instance_context=automation_intent.required_instance_context,
        automation_intent=automation_intent,
    )


def _capabilities_for_automation_intent(automation_intent: AutomationIntent) -> set[Capability]:
    if automation_intent.intent_type is AutomationIntentType.DICTIONARY_FORM:
        return {
            Capability.DICTIONARY_FIELD_CREATE,
            Capability.FIELD_LABEL_CREATE,
            Capability.FORM_LAYOUT_PLACE_FIELD,
        }
    return {automation_intent.capability}


def _automation_intent_forbidden_details(automation_intent: AutomationIntent) -> list[str]:
    details: list[str] = []
    if (
        automation_intent.intent_type is AutomationIntentType.UI_POLICY
        and automation_intent.run_scripts is True
    ):
        details.append("run scripts")
    if (
        automation_intent.intent_type is AutomationIntentType.SCRIPT_INCLUDE
        and automation_intent.client_callable is True
    ):
        details.append("client callable Script Includes")
    return details


def _field_form_intent_from_automation_intent(
    story: Story,
    automation_intent: AutomationIntent,
) -> FieldFormIntent | None:
    if automation_intent.intent_type is not AutomationIntentType.DICTIONARY_FORM:
        return None
    if automation_intent.target_table is None or automation_intent.field_type is None:
        return None
    if automation_intent.field_label is None and automation_intent.field_name is None:
        return None
    field_label = automation_intent.field_label
    if field_label is None and automation_intent.field_name is not None:
        field_label = automation_intent.field_name.replace("u_", "").replace("_", " ").title()
    if field_label is None:
        return None
    return FieldFormIntent(
        target_table=automation_intent.target_table,
        field_label=field_label,
        field_name=automation_intent.field_name,
        field_type=automation_intent.field_type,
        reference_table=automation_intent.reference_table,
        reference_qualifier=automation_intent.reference_qualifier,
        max_length=automation_intent.max_length,
        placement_anchor=automation_intent.placement_anchor,
        placement_position=automation_intent.placement_position or "end",
        mandatory=False,
        default_value=str(story.additional_context.get("default_value", "")),
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
        risk_score=risk_score,
        confidence=confidence,
    )


def _story_text(story: Story) -> str:
    return " ".join(
        part
        for part in [story.short_description, story.description, story.acceptance_criteria or ""]
        if part
    ).lower()


def _positive_requirement_text(text: str) -> str:
    return positive_requirement_text(text)


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
    if _is_business_rule_generation_request(text):
        capabilities.add(Capability.BUSINESS_RULE_GENERATE)
    elif "business rule" in text or "server script" in text:
        capabilities.add(Capability.BUSINESS_RULE_ANALYZE)
    if _is_client_script_generation_request(text):
        capabilities.add(Capability.CLIENT_SCRIPT_GENERATE)
    elif "client script" in text or "onchange" in text or "onsubmit" in text or "onload" in text:
        capabilities.add(Capability.CLIENT_SCRIPT_ANALYZE)
    if _is_script_include_generation_request(text):
        capabilities.add(Capability.SCRIPT_INCLUDE_GENERATE)
    elif "script include" in text:
        capabilities.add(Capability.SCRIPT_INCLUDE_ANALYZE)
    if _is_ui_policy_generation_request(text):
        capabilities.add(Capability.UI_POLICY_GENERATE)
    if "migrat" in text:
        capabilities.add(Capability.DATA_MIGRATION)
    if _is_integration_request(text):
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
    if _is_business_rule_generation_request(text):
        missing.extend(_missing_business_rule_generation_details(text))
    elif _is_business_rule_request(text) and _target_table(text) is None:
        missing.append("target table")
    if _is_client_script_generation_request(text):
        missing.extend(_missing_client_script_generation_details(text))
    elif _is_client_script_request(text) and _target_table(text) is None:
        missing.append("target table")
    if _is_script_include_generation_request(text):
        missing.extend(_missing_script_include_generation_details(text))
    if _is_ui_policy_generation_request(text):
        missing.extend(_missing_ui_policy_generation_details(text))
    return missing


def _is_business_rule_request(text: str) -> bool:
    return "business rule" in text or "server script" in text


def _is_business_rule_generation_request(text: str) -> bool:
    if not _is_business_rule_request(text):
        return False
    if any(token in text for token in ["analyze", "analysis", "existing", "determine whether"]):
        return False
    return any(token in text for token in ["create", "add", "generate", "implement", "build"])


def _missing_business_rule_generation_details(text: str) -> list[str]:
    checks = [
        ("target table", _target_table(text) is not None),
        ("trigger timing", "before" in text or "after" in text),
        ("trigger operations", "insert" in text or "update" in text),
        ("explicit condition", "condition:" in text or "when " in text),
        ("expected behavior", "expected behavior:" in text or "set " in text),
        ("fields read", _has_business_rule_fields_read_detail(text)),
        ("fields written", _has_business_rule_fields_written_detail(text)),
    ]
    return [label for label, present in checks if not present]


def _has_business_rule_fields_read_detail(text: str) -> bool:
    return "fields read:" in text or (
        ("condition:" in text or "when " in text)
        and any(field in text for field in _mentioned_service_now_fields(text))
    )


def _has_business_rule_fields_written_detail(text: str) -> bool:
    return (
        "fields written:" in text
        or re.search(r"\bwrites? only [a-zA-Z0-9_]+", text) is not None
        or re.search(r"\bset field [a-zA-Z0-9_]+", text) is not None
        or re.search(r"\bset [a-zA-Z0-9_]+ to\b", text) is not None
    )


def _mentioned_service_now_fields(text: str) -> set[str]:
    field_pattern = r"\b[a-z][a-z0-9]*_[a-z0-9_]+\b|\bcategory\b|\bstate\b|\bpriority\b"
    return set(re.findall(field_pattern, text))


def _business_rule_forbidden_details(text: str) -> list[str]:
    if not _is_business_rule_generation_request(text):
        return []
    forbidden_patterns = {
        "delete rules": ["delete rule", "delete business rule", "on delete"],
        "async/display rules": ["async", "display business rule"],
        "scheduled jobs": ["scheduled job", "schedule"],
        "outbound calls": ["rest", "soap", "endpoint", "api call", "http://", "https://"],
        "credentials": ["credential", "password", "token", "api key", "secret"],
        "cross-table writes": ["gliderecord", "another table", "other table", "cross-table"],
    }
    return [
        label
        for label, tokens in forbidden_patterns.items()
        if any(token in text for token in tokens)
    ]


def _is_client_script_request(text: str) -> bool:
    return "client script" in text or "onchange" in text or "onsubmit" in text or "onload" in text


def _is_client_script_generation_request(text: str) -> bool:
    if not _is_client_script_request(text):
        return False
    if any(token in text for token in ["analyze", "analysis", "existing", "determine whether"]):
        return False
    return any(token in text for token in ["create", "add", "generate", "implement", "build"])


def _missing_client_script_generation_details(text: str) -> list[str]:
    checks = [
        ("target table", _target_table(text) is not None),
        ("client script type", any(token in text for token in ["onchange", "onload", "onsubmit"])),
        ("explicit condition", "condition:" in text or "when " in text),
        ("expected behavior", "expected behavior:" in text or "show " in text or "set " in text),
        ("fields read", _has_field_detail(text, "read")),
        ("fields written", _has_field_detail(text, "written")),
    ]
    if "onchange" in text and _client_script_target_field(text) is None:
        checks.append(("target field", False))
    return [label for label, present in checks if not present]


def _has_field_detail(text: str, action: str) -> bool:
    return bool(
        re.search(rf"\bfields?\s+{action}\b", text)
        or re.search(rf"\bscript\s+{action}s?\b", text)
    )


def _client_script_forbidden_details(text: str) -> list[str]:
    if not _is_client_script_generation_request(text):
        return []
    forbidden_patterns = {
        "DOM manipulation outside g_form APIs": ["document.", "window.", "dom"],
        "browser storage": ["localstorage", "sessionstorage"],
        "external calls": ["fetch", "xmlhttprequest", "endpoint", "api call", "http://", "https://"],
        "GlideAjax dependency creation": ["glideajax"],
        "credentials": ["credential", "password", "token", "api key", "secret"],
    }
    return [
        label
        for label, tokens in forbidden_patterns.items()
        if any(token in text for token in tokens)
    ]


def _client_script_target_field(text: str) -> str | None:
    match = re.search(r"for the ([a-zA-Z0-9_]+) field", text)
    if match:
        return match.group(1).lower()
    match = re.search(r"onchange .*? ([a-zA-Z0-9_]+) field", text)
    if match:
        return match.group(1).lower()
    return None


def _is_integration_request(text: str) -> bool:
    return any(
        token in text
        for token in [
            "integrat",
            "rest api",
            "api call",
            "external api",
            "outbound api",
            "endpoint",
        ]
    )


def _is_script_include_generation_request(text: str) -> bool:
    if "script include" not in text:
        return False
    if any(token in text for token in ["analyze", "analysis", "existing", "determine whether"]):
        return False
    return any(token in text for token in ["create", "add", "generate", "implement", "build"])


def _is_ui_policy_generation_request(text: str) -> bool:
    if "ui policy" not in text and "ui policies" not in text:
        return False
    if any(token in text for token in ["analyze", "analysis", "existing", "determine whether"]):
        return False
    return any(token in text for token in ["create", "add", "generate", "implement", "build"])


def _missing_ui_policy_generation_details(text: str) -> list[str]:
    checks = [
        ("target table", _target_table(text) is not None),
        ("condition", "condition:" in text or "when " in text or "condition is" in text),
        (
            "expected behavior",
            "expected behavior:" in text
            or "mandatory" in text
            or "visible" in text
            or "read only" in text,
        ),
        ("fields read", "fields read:" in text or "category" in text),
        (
            "fields affected",
            "fields affected:" in text
            or "field affected:" in text
            or "actions:" in text
            or "assignment_group" in text
            or "assignment group" in text,
        ),
        (
            "reverse if false decision",
            "reverse if false:" in text
            or "reverse if false is enabled" in text
            or "condition is false" in text
            or "policy must reverse" in text,
        ),
    ]
    return [label for label, present in checks if not present]


def _ui_policy_forbidden_details(text: str) -> list[str]:
    if not _is_ui_policy_generation_request(text):
        return []
    forbidden_patterns = {
        "run scripts": ["run scripts: true", "run script: true", "advanced script"],
        "Client Script behavior": ["client script", "g_form", "glideajax"],
        "Business Rule creation": ["business rule"],
        "Script Include creation": ["script include"],
        "Flow creation": [" flow ", "flow designer"],
        "ACL changes": [" acl", " role"],
        "integration calls": ["rest", "soap", "endpoint", "api call", "http://", "https://"],
        "credentials": ["credential", "password", "token", "api key", "secret"],
        "cross-table behavior": ["another table", "other table", "cross-table"],
    }
    return [
        label
        for label, tokens in forbidden_patterns.items()
        if any(token in text for token in tokens)
    ]


def _missing_script_include_generation_details(text: str) -> list[str]:
    checks = [
        ("script include name", _script_include_name(text) is not None),
        ("scope", "scope" in text or "global" in text),
        ("client callable decision", "client callable:" in text or "not client callable" in text),
        ("expected behavior", "expected server-side behavior:" in text),
        ("tables read", "tables read:" in text),
        ("tables written", "tables written:" in text),
        ("fields read", "fields read:" in text),
        ("fields written", "fields written:" in text),
    ]
    return [label for label, present in checks if not present]


def _script_include_forbidden_details(text: str) -> list[str]:
    if not _is_script_include_generation_request(text):
        return []
    forbidden_patterns = {
        "client callable Script Includes": ["client callable: true"],
        "global privilege escalation": ["privilege escalation", "elevated privilege"],
        "cross-scope access changes": ["cross-scope", "cross scope"],
        "security changes": [" acl", " role", "system property"],
        "outbound calls": ["rest", "soap", "endpoint", "api call", "http://", "https://"],
        "credentials": ["credential", "password", "token", "api key", "secret"],
        "broad GlideRecord mutation": ["deleterecord", "deletemultiple", "updatemultiple"],
        "caller creation": ["business rule", "client script", "flow", "scheduled job"],
    }
    return [
        label
        for label, tokens in forbidden_patterns.items()
        if any(token in text for token in tokens)
    ]


def _script_include_name(text: str) -> str | None:
    match = re.search(r"script include named ([a-zA-Z][a-zA-Z0-9_]*)", text)
    if match:
        return match.group(1)
    return None


def _code_surface_capability(requested: set[Capability]) -> Capability | None:
    for capability in [
        Capability.BUSINESS_RULE_ANALYZE,
        Capability.CLIENT_SCRIPT_ANALYZE,
        Capability.SCRIPT_INCLUDE_ANALYZE,
    ]:
        if capability in requested:
            return capability
    return None


def _is_dictionary_form_request(text: str) -> bool:
    if (
        _is_business_rule_request(text)
        or _is_client_script_request(text)
        or "script include" in text
        or "ui policy" in text
        or "ui policies" in text
    ):
        return False
    return ("field" in text or "column" in text) and re.search(r"\bform\b", text) is not None


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
    if "script include" in text:
        return "global"
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
