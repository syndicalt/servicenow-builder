"""Automation-outcome routing for story capability analysis."""

from __future__ import annotations

from typing import Any

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
from jedi_devproject.capability_assessment import (
    CURRENT_AUTOMATION_MAX_POINTS,
    FULL_MATURITY_MAX_AUTOMATED_POINTS,
    _assessment,
)
from jedi_devproject.catalog_item_generation import is_declarative_reference_qualifier
from jedi_devproject.intent_classifier import (
    _business_rule_forbidden_details,
    _client_script_forbidden_details,
    _code_surface_capability,
    _is_catalog_item_creation_request,
    _is_dictionary_form_request,
    _is_record_producer_request,
    _missing_details,
    _requested_capabilities,
    _script_include_forbidden_details,
    _ui_policy_forbidden_details,
)
from jedi_devproject.models import Story
from jedi_devproject.story_features import (
    _field_form_intent,
    _positive_requirement_text,
    _story_text,
    _target_table,
)

SUPPORTED_BASELINE_CAPABILITIES = {
    Capability.CATALOG_ITEM_CREATE,
    Capability.RECORD_PRODUCER_CREATE,
    Capability.CATALOG_UI_POLICY_GENERATE,
    Capability.CATALOG_CLIENT_SCRIPT_GENERATE,
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
    Capability.FORM_SECTION_REMOVE,
    Capability.CMDB_IRE_ANALYZE,
    Capability.CMDB_IRE_GENERATE,
}

# Catalog variable behavior (catalog UI policies and catalog client scripts) is
# only supported when the same story creates the catalog item, so the behavior
# can be validated against the item's own generated variables. Standalone
# changes target an existing catalog item, and there is no live-item discovery
# contract for that yet — they route to manual review with these stable codes.
CATALOG_UI_POLICY_EXISTING_ITEM_REASON_CODE = "catalog_ui_policy:existing_item_manual_review"
CATALOG_CLIENT_SCRIPT_EXISTING_ITEM_REASON_CODE = (
    "catalog_client_script:existing_item_manual_review"
)

_STANDALONE_CATALOG_BEHAVIOR_REASON_CODES: dict[Capability, str] = {
    Capability.CATALOG_UI_POLICY_GENERATE: CATALOG_UI_POLICY_EXISTING_ITEM_REASON_CODE,
    Capability.CATALOG_CLIENT_SCRIPT_GENERATE: CATALOG_CLIENT_SCRIPT_EXISTING_ITEM_REASON_CODE,
}

_STANDALONE_CATALOG_BEHAVIOR_REASON = (
    "standalone catalog variable behavior targets an existing catalog item; "
    "no live catalog item discovery contract exists yet"
)


# A record producer creates a record in a target table; a catalog item drives
# request fulfillment. A story asking for both at once is ambiguous about which
# artifact owns the variables and placement, so it routes to manual review with
# this stable code instead of guessing.
RECORD_PRODUCER_COMBINED_ITEM_REASON_CODE = (
    "record_producer:combined_with_catalog_item_manual_review"
)

_RECORD_PRODUCER_COMBINED_ITEM_REASON = (
    "story requests both a catalog item and a record producer; "
    "combined requests route to manual review"
)

# Record producers (like catalog items) are only generated from structured
# intent; free-text requests route to clarification with missing-detail
# feedback rather than guessing producer placement or field mappings.
_RECORD_PRODUCER_STRUCTURED_INTENT_REASON = (
    "record producer stories require structured intent for automated generation"
)


def _combined_item_and_producer_reasons(positive_text: str) -> list[str]:
    if _is_record_producer_request(positive_text) and _is_catalog_item_creation_request(
        positive_text
    ):
        return [
            RECORD_PRODUCER_COMBINED_ITEM_REASON_CODE,
            _RECORD_PRODUCER_COMBINED_ITEM_REASON,
        ]
    return []


def _standalone_catalog_behavior_reasons(requested: set[Capability]) -> list[str]:
    codes = [
        code
        for capability, code in _STANDALONE_CATALOG_BEHAVIOR_REASON_CODES.items()
        if capability in requested
    ]
    if not codes:
        return []
    return [*sorted(codes), _STANDALONE_CATALOG_BEHAVIOR_REASON]


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

    standalone_catalog_behavior_reasons = _standalone_catalog_behavior_reasons(requested)
    if standalone_catalog_behavior_reasons:
        # Free-text stories never create a catalog item (catalog items require
        # structured intent), so any catalog policy/script request here targets
        # an existing item and routes to manual review.
        reasons.extend(standalone_catalog_behavior_reasons)
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

    combined_item_and_producer_reasons = _combined_item_and_producer_reasons(positive_text)
    if combined_item_and_producer_reasons:
        reasons.extend(combined_item_and_producer_reasons)
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

    if Capability.CMDB_IRE_ANALYZE in requested:
        profile = capability_profile(Capability.CMDB_IRE_GENERATE)
        reasons.extend(
            [
                "supported CMDB IRE identifier and reconciliation candidate request",
                "CMDB IRE retrieved Update Set handoff requires XML shape evidence",
            ]
        )
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

    if Capability.RECORD_PRODUCER_CREATE in requested:
        reasons.append(_RECORD_PRODUCER_STRUCTURED_INTENT_REASON)
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

    if Capability.FORM_SECTION_REMOVE in requested:
        profile = capability_profile(Capability.FORM_SECTION_REMOVE)
        reasons.append("supported form section removal request")
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
    Capability.CATALOG_ITEM_CREATE: "supported standard catalog item generation request",
    Capability.RECORD_PRODUCER_CREATE: "supported record producer generation request",
    Capability.BUSINESS_RULE_GENERATE: "supported table-local business rule generation request",
    Capability.CLIENT_SCRIPT_GENERATE: "supported table-local client script generation request",
    Capability.SCRIPT_INCLUDE_GENERATE: "supported utility script include generation request",
    Capability.UI_POLICY_GENERATE: "supported declarative ui policy generation request",
    Capability.DICTIONARY_FIELD_CREATE: "supported low-complexity dictionary/form request",
    Capability.FORM_SECTION_REMOVE: "supported form section removal request",
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

    if automation_intent.intent_type in {
        AutomationIntentType.CATALOG_UI_POLICY,
        AutomationIntentType.CATALOG_CLIENT_SCRIPT,
    }:
        # Standalone catalog variable behavior targets an existing catalog
        # item; supported behavior rides along the story that creates the item.
        reasons.extend(_standalone_catalog_behavior_reasons({automation_intent.capability}))
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

    if automation_intent.intent_type in {
        AutomationIntentType.CATALOG_ITEM,
        AutomationIntentType.RECORD_PRODUCER,
    }:
        combined_reasons = _combined_item_and_producer_reasons(
            _positive_requirement_text(_story_text(story))
        )
        if combined_reasons:
            reasons.extend(combined_reasons)
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

    if automation_intent.capability is Capability.FORM_SECTION_REMOVE:
        profile = capability_profile(Capability.FORM_SECTION_REMOVE)
        reasons.append(AUTOMATED_INTENT_REASONS[Capability.FORM_SECTION_REMOVE])
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
            required_instance_context=profile.required_instance_context,
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
    if automation_intent.intent_type is AutomationIntentType.CATALOG_ITEM:
        capabilities = {Capability.CATALOG_ITEM_CREATE}
        if automation_intent.catalog_ui_policies:
            capabilities.add(Capability.CATALOG_UI_POLICY_GENERATE)
        if automation_intent.catalog_client_scripts:
            capabilities.add(Capability.CATALOG_CLIENT_SCRIPT_GENERATE)
        return capabilities
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
    if (
        automation_intent.intent_type is AutomationIntentType.CATALOG_ITEM
        and automation_intent.fulfillment_flow
        # Explicitly attaching an EXISTING flow is the supported convergence
        # path (fail-closed live resolution happens downstream); creating,
        # modifying, or ambiguously requesting a flow stays forbidden.
        and not automation_intent.fulfillment_flow_attachment_requested
    ):
        details.append("fulfillment flow or workflow creation")
    if automation_intent.intent_type is AutomationIntentType.CATALOG_ITEM:
        if automation_intent.catalog_variable_set_creation:
            details.append("variable set creation")
        if _has_non_declarative_reference_qualifier(automation_intent.catalog_variables):
            details.append("scripted or non-declarative reference qualifier")
    if automation_intent.intent_type is AutomationIntentType.RECORD_PRODUCER:
        # Record producers redirect to the produced record and never use
        # fulfillment flows: any fulfillment-flow request — including
        # attaching an existing flow — stays forbidden.
        if automation_intent.fulfillment_flow_attachment_requested:
            details.append("fulfillment flow attachment")
        elif automation_intent.fulfillment_flow:
            details.append("fulfillment flow or workflow creation")
        if automation_intent.record_producer_script:
            details.append("producer script")
        if _has_non_declarative_reference_qualifier(automation_intent.catalog_variables):
            details.append("scripted or non-declarative reference qualifier")
    return details


def _has_non_declarative_reference_qualifier(variables: list[dict[str, Any]]) -> bool:
    return any(
        str(variable.get("reference_qualifier") or "").strip()
        and not is_declarative_reference_qualifier(
            str(variable.get("reference_qualifier") or "")
        )
        for variable in variables
    )


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
