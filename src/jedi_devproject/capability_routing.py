"""Automation-outcome routing for story capability analysis."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
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


@dataclass(frozen=True)
class _RoutingContext:
    """Inputs shared by every routing rule, computed once per story.

    ``automation_intent`` is set only on the structured-intent path; free-text
    routing leaves it ``None``.
    """

    story: Story
    requested: set[Capability]
    positive_text: str
    intent: FieldFormIntent | None
    target_table: str | None
    missing_details: list[str]
    unsupported: set[Capability]
    supported_capabilities: set[Capability]
    automation_intent: AutomationIntent | None = None


@dataclass(frozen=True)
class _RuleResult:
    """A matched rule's routing decision.

    ``missing_details`` and ``unsupported`` default to ``None``, meaning the
    assessment keeps the context-computed values; rules that resolve the story
    (automated build / context analysis) override them explicitly.
    """

    outcome: SuitabilityOutcome
    reasons: tuple[str, ...]
    missing_details: list[str] | None = None
    unsupported: set[Capability] | None = None
    required_instance_context: list[str] | None = None


_RuleMatcher = Callable[[_RoutingContext], "_RuleResult | None"]


def _points_gate_rule(max_points: int, label: str) -> _RuleMatcher:
    def _match(context: _RoutingContext) -> _RuleResult | None:
        if context.story.story_points > max_points:
            return _RuleResult(
                outcome=SuitabilityOutcome.MANUAL_DEVELOPER_BUILD,
                reasons=(
                    f"story points exceed {label}: "
                    f"{context.story.story_points:.1f} > {max_points}",
                ),
            )
        return None

    return _match


def _match_standalone_catalog_behavior(context: _RoutingContext) -> _RuleResult | None:
    # Free-text stories never create a catalog item (catalog items require
    # structured intent), so any catalog policy/script request here targets
    # an existing item and routes to manual review.
    codes = _standalone_catalog_behavior_reasons(context.requested)
    if codes:
        return _RuleResult(outcome=SuitabilityOutcome.MANUAL_DEVELOPER_BUILD, reasons=tuple(codes))
    return None


def _match_combined_item_and_producer(context: _RoutingContext) -> _RuleResult | None:
    combined = _combined_item_and_producer_reasons(context.positive_text)
    if combined:
        return _RuleResult(
            outcome=SuitabilityOutcome.MANUAL_DEVELOPER_BUILD, reasons=tuple(combined)
        )
    return None


def _match_cmdb_ire_analysis(context: _RoutingContext) -> _RuleResult | None:
    if Capability.CMDB_IRE_ANALYZE not in context.requested:
        return None
    profile = capability_profile(Capability.CMDB_IRE_GENERATE)
    return _RuleResult(
        outcome=SuitabilityOutcome.AUTOMATED_BUILD,
        reasons=(
            "supported CMDB IRE identifier and reconciliation candidate request",
            "CMDB IRE retrieved Update Set handoff requires XML shape evidence",
        ),
        missing_details=[],
        unsupported=set(),
        required_instance_context=profile.required_instance_context,
    )


def _forbidden_generation_rule(
    capability: Capability,
    label: str,
    forbidden_details: Callable[[str], list[str]],
) -> _RuleMatcher:
    def _match(context: _RoutingContext) -> _RuleResult | None:
        details = forbidden_details(context.positive_text)
        if capability in context.requested and details:
            return _RuleResult(
                outcome=SuitabilityOutcome.MANUAL_DEVELOPER_BUILD,
                reasons=(
                    f"{label} generation includes forbidden behavior: {', '.join(details)}",
                ),
            )
        return None

    return _match


def _match_unsupported_capabilities(context: _RoutingContext) -> _RuleResult | None:
    if not context.unsupported:
        return None
    return _RuleResult(
        outcome=SuitabilityOutcome.UNSUPPORTED_CAPABILITY,
        reasons=("request includes unsupported pipeline capabilities",),
    )


def _match_record_producer_structured_intent(context: _RoutingContext) -> _RuleResult | None:
    if Capability.RECORD_PRODUCER_CREATE not in context.requested:
        return None
    reasons = [_RECORD_PRODUCER_STRUCTURED_INTENT_REASON]
    if context.missing_details:
        reasons.append("story is missing required automation details")
    return _RuleResult(outcome=SuitabilityOutcome.NEEDS_CLARIFICATION, reasons=tuple(reasons))


def _match_missing_details(context: _RoutingContext) -> _RuleResult | None:
    if not context.missing_details:
        return None
    return _RuleResult(
        outcome=SuitabilityOutcome.NEEDS_CLARIFICATION,
        reasons=("story is missing required automation details",),
    )


def _match_code_surface_analysis(context: _RoutingContext) -> _RuleResult | None:
    capability = _code_surface_capability(context.requested)
    if capability is None or _is_dictionary_form_request(context.positive_text):
        return None
    profile = capability_profile(capability)
    label = capability.value.removesuffix("_analyze").replace("_", " ")
    return _RuleResult(
        outcome=SuitabilityOutcome.CONTEXT_ANALYSIS,
        reasons=("Code surface analysis first", f"{label} generation is not enabled yet"),
        missing_details=[],
        unsupported=set(),
        required_instance_context=profile.required_instance_context,
    )


def _supported_generation_rule(capability: Capability) -> _RuleMatcher:
    """Route a supported generation request to an automated build.

    The reason string comes from ``AUTOMATED_INTENT_REASONS`` so free-text and
    structured routing report identical wording per capability.
    """

    def _match(context: _RoutingContext) -> _RuleResult | None:
        if capability not in context.requested:
            return None
        profile = capability_profile(capability)
        return _RuleResult(
            outcome=SuitabilityOutcome.AUTOMATED_BUILD,
            reasons=(AUTOMATED_INTENT_REASONS[capability],),
            missing_details=[],
            unsupported=set(),
            required_instance_context=profile.required_instance_context,
        )

    return _match


# Ordered free-text routing rules, evaluated top to bottom; the first match
# wins. Order is load-bearing: points gates run before everything, manual-
# review gates (standalone catalog behavior, combined item+producer, forbidden
# details) run before the unsupported/clarification gates, and those run
# before supported-generation routing. A story matching no rule falls through
# to the terminal dictionary/form outcome in ``analyze_story_capabilities``.
_FREE_TEXT_RULES: tuple[tuple[str, _RuleMatcher], ...] = (
    (
        "story_points_exceed_full_maturity_max",
        _points_gate_rule(FULL_MATURITY_MAX_AUTOMATED_POINTS, "full-maturity max"),
    ),
    (
        "story_points_exceed_current_automation_max",
        _points_gate_rule(CURRENT_AUTOMATION_MAX_POINTS, "current automation max"),
    ),
    ("standalone_catalog_behavior", _match_standalone_catalog_behavior),
    ("combined_item_and_producer", _match_combined_item_and_producer),
    ("cmdb_ire_analysis", _match_cmdb_ire_analysis),
    (
        "business_rule_forbidden_behavior",
        _forbidden_generation_rule(
            Capability.BUSINESS_RULE_GENERATE, "business rule", _business_rule_forbidden_details
        ),
    ),
    (
        "client_script_forbidden_behavior",
        _forbidden_generation_rule(
            Capability.CLIENT_SCRIPT_GENERATE, "client script", _client_script_forbidden_details
        ),
    ),
    (
        "script_include_forbidden_behavior",
        _forbidden_generation_rule(
            Capability.SCRIPT_INCLUDE_GENERATE,
            "script include",
            _script_include_forbidden_details,
        ),
    ),
    (
        "ui_policy_forbidden_behavior",
        _forbidden_generation_rule(
            Capability.UI_POLICY_GENERATE, "ui policy", _ui_policy_forbidden_details
        ),
    ),
    ("unsupported_capabilities", _match_unsupported_capabilities),
    ("record_producer_structured_intent", _match_record_producer_structured_intent),
    ("missing_details", _match_missing_details),
    ("code_surface_analysis", _match_code_surface_analysis),
    ("business_rule_generation", _supported_generation_rule(Capability.BUSINESS_RULE_GENERATE)),
    ("client_script_generation", _supported_generation_rule(Capability.CLIENT_SCRIPT_GENERATE)),
    ("script_include_generation", _supported_generation_rule(Capability.SCRIPT_INCLUDE_GENERATE)),
    ("ui_policy_generation", _supported_generation_rule(Capability.UI_POLICY_GENERATE)),
    ("form_section_removal", _supported_generation_rule(Capability.FORM_SECTION_REMOVE)),
)


def _first_matching_rule_assessment(
    context: _RoutingContext,
    rules: tuple[tuple[str, _RuleMatcher], ...],
) -> StoryCapabilityAssessment | None:
    """Evaluate ordered rules and build the assessment for the first match."""
    for _name, matcher in rules:
        result = matcher(context)
        if result is None:
            continue
        return _assessment(
            story=context.story,
            outcome=result.outcome,
            requested=context.requested,
            supported=context.supported_capabilities,
            intent=context.intent,
            target_table=context.target_table,
            reasons=list(result.reasons),
            missing_details=(
                context.missing_details
                if result.missing_details is None
                else result.missing_details
            ),
            unsupported=context.unsupported if result.unsupported is None else result.unsupported,
            required_instance_context=result.required_instance_context,
            automation_intent=context.automation_intent,
        )
    return None


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
    intent = _field_form_intent(story, text) if _is_dictionary_form_request(positive_text) else None
    context = _RoutingContext(
        story=story,
        requested=requested,
        positive_text=positive_text,
        intent=intent,
        target_table=intent.target_table if intent is not None else _target_table(positive_text),
        missing_details=_missing_details(positive_text),
        unsupported=requested - supported_capabilities,
        supported_capabilities=supported_capabilities,
    )

    matched = _first_matching_rule_assessment(context, _FREE_TEXT_RULES)
    if matched is not None:
        return matched

    # Terminal fallthrough, deliberately outside the rule table: a free-text
    # story that clears every gate above is a supported low-complexity
    # dictionary/form request.
    return _assessment(
        story=story,
        outcome=SuitabilityOutcome.AUTOMATED_BUILD,
        requested=requested,
        supported=supported_capabilities,
        intent=intent,
        target_table=context.target_table,
        reasons=["supported low-complexity dictionary/form request"],
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


def _match_intent_standalone_catalog_behavior(context: _RoutingContext) -> _RuleResult | None:
    automation_intent = context.automation_intent
    if automation_intent is None or automation_intent.intent_type not in {
        AutomationIntentType.CATALOG_UI_POLICY,
        AutomationIntentType.CATALOG_CLIENT_SCRIPT,
    }:
        return None
    # Standalone catalog variable behavior targets an existing catalog
    # item; supported behavior rides along the story that creates the item.
    return _RuleResult(
        outcome=SuitabilityOutcome.MANUAL_DEVELOPER_BUILD,
        reasons=tuple(_standalone_catalog_behavior_reasons({automation_intent.capability})),
    )


def _match_intent_combined_item_and_producer(context: _RoutingContext) -> _RuleResult | None:
    automation_intent = context.automation_intent
    if automation_intent is None or automation_intent.intent_type not in {
        AutomationIntentType.CATALOG_ITEM,
        AutomationIntentType.RECORD_PRODUCER,
    }:
        return None
    combined = _combined_item_and_producer_reasons(context.positive_text)
    if combined:
        return _RuleResult(
            outcome=SuitabilityOutcome.MANUAL_DEVELOPER_BUILD, reasons=tuple(combined)
        )
    return None


def _match_intent_forbidden_details(context: _RoutingContext) -> _RuleResult | None:
    automation_intent = context.automation_intent
    details = (
        _automation_intent_forbidden_details(automation_intent)
        if automation_intent is not None
        else []
    )
    if automation_intent is None or not details:
        return None
    return _RuleResult(
        outcome=SuitabilityOutcome.MANUAL_DEVELOPER_BUILD,
        reasons=(
            f"{automation_intent.intent_type.value.replace('_', ' ')} generation "
            f"includes forbidden behavior: {', '.join(details)}",
        ),
    )


# Ordered structured-intent routing rules; same first-match-wins evaluation and
# ordering constraints as ``_FREE_TEXT_RULES``. A story matching no rule falls
# through to the terminal supported-automation outcome in
# ``_assess_automation_intent``.
_STRUCTURED_INTENT_RULES: tuple[tuple[str, _RuleMatcher], ...] = (
    (
        "story_points_exceed_full_maturity_max",
        _points_gate_rule(FULL_MATURITY_MAX_AUTOMATED_POINTS, "full-maturity max"),
    ),
    (
        "story_points_exceed_current_automation_max",
        _points_gate_rule(CURRENT_AUTOMATION_MAX_POINTS, "current automation max"),
    ),
    ("standalone_catalog_behavior", _match_intent_standalone_catalog_behavior),
    ("combined_item_and_producer", _match_intent_combined_item_and_producer),
    ("forbidden_intent_details", _match_intent_forbidden_details),
    ("unsupported_capabilities", _match_unsupported_capabilities),
    ("missing_details", _match_missing_details),
    ("form_section_removal", _supported_generation_rule(Capability.FORM_SECTION_REMOVE)),
)


def _assess_automation_intent(
    *,
    story: Story,
    automation_intent: AutomationIntent,
    supported_capabilities: set[Capability],
) -> StoryCapabilityAssessment:
    requested = _capabilities_for_automation_intent(automation_intent)
    field_form_intent = _field_form_intent_from_automation_intent(story, automation_intent)
    context = _RoutingContext(
        story=story,
        requested=requested,
        positive_text=_positive_requirement_text(_story_text(story)),
        intent=field_form_intent,
        target_table=(
            field_form_intent.target_table
            if field_form_intent is not None
            else automation_intent.target_table
        ),
        missing_details=automation_intent.missing_details,
        unsupported=requested - supported_capabilities,
        supported_capabilities=supported_capabilities,
        automation_intent=automation_intent,
    )

    matched = _first_matching_rule_assessment(context, _STRUCTURED_INTENT_RULES)
    if matched is not None:
        return matched

    # Terminal fallthrough, deliberately outside the rule table: a structured
    # intent that clears every gate above is a supported automation request.
    return _assessment(
        story=story,
        outcome=SuitabilityOutcome.AUTOMATED_BUILD,
        requested=requested,
        supported=supported_capabilities,
        intent=field_form_intent,
        target_table=context.target_table,
        reasons=[
            AUTOMATED_INTENT_REASONS.get(
                automation_intent.capability,
                "supported structured automation request",
            )
        ],
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
