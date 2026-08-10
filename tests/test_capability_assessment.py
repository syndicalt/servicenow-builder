from __future__ import annotations

import math
from typing import Any

import pytest

from jedi_devproject.automation_intent import (
    AutomationIntent,
    AutomationIntentSource,
    AutomationIntentType,
)
from jedi_devproject.capabilities import (
    Capability,
    StoryCapabilityAssessment,
    SuitabilityOutcome,
)
from jedi_devproject.capability_assessment import (
    INTAKE_FEEDBACK_SCHEMA_VERSION,
    IntakeFeedback,
    _automation_intent_payload,
    _ensure_capability_payload_json_safe,
    _intake_content_hash,
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


def test_intake_feedback_hash_rejects_non_finite_guidance_without_payload_leak() -> None:
    assessment = StoryCapabilityAssessment.model_validate(
        {
            "story_number": "STRY0010013",
            "outcome": SuitabilityOutcome.NEEDS_CLARIFICATION,
            "capabilities": [Capability.DICTIONARY_FIELD_CREATE],
            "supported_capabilities": [Capability.DICTIONARY_FIELD_CREATE],
            "reasons": ["story is missing required automation details"],
            "missing_details": [],
            "unsupported_capabilities": [],
            "operator_feedback": ["Add missing field details."],
            "suggested_story": "Target artifact type: Dictionary Field",
            "risk_score": 0.4,
            "confidence": 0.65,
        }
    )

    with pytest.raises(ValueError) as exc_info:
        _intake_content_hash(
            story_number=assessment.story_number,
            outcome=assessment.outcome,
            reason_codes=["missing_detail:field_type"],
            guidance=[float("nan"), "client_secret=do-not-echo-this"],  # type: ignore[list-item]
            suggested_story=assessment.suggested_story,
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "intake feedback hash payload contains non-finite numeric values"
    assert "guidance" not in diagnostic
    assert "NaN" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "do-not-echo-this" not in diagnostic
    assert exc_info.value.__cause__ is None


def test_intake_feedback_hash_rejects_non_json_guidance_without_payload_leak() -> None:
    class SecretBearingObject:
        def __str__(self) -> str:
            return "client_secret=intake-secret"

    assessment = StoryCapabilityAssessment.model_validate(
        {
            "story_number": "STRY0010013",
            "outcome": SuitabilityOutcome.NEEDS_CLARIFICATION,
            "capabilities": [Capability.DICTIONARY_FIELD_CREATE],
            "supported_capabilities": [Capability.DICTIONARY_FIELD_CREATE],
            "reasons": ["story is missing required automation details"],
            "missing_details": [],
            "unsupported_capabilities": [],
            "operator_feedback": ["Add missing field details."],
            "suggested_story": "Target artifact type: Dictionary Field",
            "risk_score": 0.4,
            "confidence": 0.65,
        }
    )

    with pytest.raises(ValueError) as exc_info:
        _intake_content_hash(
            story_number=assessment.story_number,
            outcome=assessment.outcome,
            reason_codes=["missing_detail:field_type"],
            guidance=[SecretBearingObject(), "client_secret=do-not-echo-this"],  # type: ignore[list-item]
            suggested_story=assessment.suggested_story,
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "intake feedback hash payload contains non-JSON values"
    assert "guidance" not in diagnostic
    assert "SecretBearingObject" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "intake-secret" not in diagnostic
    assert "do-not-echo-this" not in diagnostic
    assert exc_info.value.__cause__ is None


def test_build_intake_feedback_rejects_non_finite_guidance_without_payload_leak() -> None:
    assessment = StoryCapabilityAssessment.model_construct(
        story_number="STRY0010013",
        outcome=SuitabilityOutcome.NEEDS_CLARIFICATION,
        capabilities={Capability.DICTIONARY_FIELD_CREATE},
        supported_capabilities={Capability.DICTIONARY_FIELD_CREATE},
        reasons=["story is missing required automation details"],
        missing_details=[],
        unsupported_capabilities=set(),
        operator_feedback=[float("nan"), "client_secret=do-not-echo-this"],
        suggested_story="Target artifact type: Dictionary Field",
        risk_score=0.4,
        confidence=0.65,
    )

    with pytest.raises(ValueError) as exc_info:
        build_intake_feedback(assessment)

    diagnostic = str(exc_info.value)
    assert diagnostic == "intake feedback hash payload contains non-finite numeric values"
    assert "operator_feedback" not in diagnostic
    assert "NaN" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "do-not-echo-this" not in diagnostic
    assert exc_info.value.__cause__ is None


def test_automation_intent_payload_rejects_non_finite_numeric_value_without_leak() -> None:
    intent = AutomationIntent.model_construct(
        source=AutomationIntentSource.STRUCTURED,
        intent_type=AutomationIntentType.DICTIONARY_FORM,
        capability=Capability.DICTIONARY_FIELD_CREATE,
        target_table="incident",
        field_label="client_secret=do-not-echo-this",
        field_name="u_jedi_test",
        field_type="string",
        max_length=math.nan,
        missing_details=[],
    )

    with pytest.raises(ValueError) as exc_info:
        _automation_intent_payload(intent)

    diagnostic = str(exc_info.value)
    assert diagnostic == "automation intent payload contains non-finite numeric values"
    assert "max_length" not in diagnostic
    assert "NaN" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "do-not-echo-this" not in diagnostic
    assert exc_info.value.__cause__ is None


def test_automation_intent_payload_rejects_non_json_value_without_leak() -> None:
    class SecretBearingObject:
        def __str__(self) -> str:
            return "client_secret=intent-secret"

    intent = AutomationIntent.model_construct(
        source=AutomationIntentSource.STRUCTURED,
        intent_type=AutomationIntentType.CATALOG_ITEM,
        capability=Capability.CATALOG_ITEM_CREATE,
        target_table="sc_cat_item",
        field_label="client_secret=do-not-echo-this",
        catalog_variables=[{"name": "requested_for", "default": SecretBearingObject()}],
        missing_details=[],
    )

    with pytest.raises(ValueError) as exc_info:
        _automation_intent_payload(intent)

    diagnostic = str(exc_info.value)
    assert diagnostic == "automation intent payload contains non-JSON values"
    assert "catalog_variables" not in diagnostic
    assert "SecretBearingObject" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "intent-secret" not in diagnostic
    assert "do-not-echo-this" not in diagnostic
    assert exc_info.value.__cause__ is None


def test_automation_intent_payload_rejects_string_subclass_without_leak() -> None:
    class HostileIntentText(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=intent-str-secret")

    intent = AutomationIntent.model_construct(
        source=AutomationIntentSource.STRUCTURED,
        intent_type=AutomationIntentType.CATALOG_ITEM,
        capability=Capability.CATALOG_ITEM_CREATE,
        target_table="sc_cat_item",
        field_label="client_secret=do-not-echo-this",
        catalog_variables=[
            {"name": "requested_for", "default": HostileIntentText("intent-secret")}
        ],
        missing_details=[],
    )

    with pytest.raises(ValueError) as exc_info:
        _automation_intent_payload(intent)

    diagnostic = str(exc_info.value)
    assert diagnostic == "automation intent payload contains non-JSON values"
    assert "catalog_variables" not in diagnostic
    assert "HostileIntentText" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "intent-secret" not in diagnostic
    assert "do-not-echo-this" not in diagnostic
    assert exc_info.value.__cause__ is None


def test_capability_payload_rejects_scalar_subclasses_without_payload_leak() -> None:
    class HostileCapabilityOrder(int):
        def __str__(self) -> str:
            raise AssertionError("client_secret=capability-int-subclass-secret")

    class HostileCapabilityScore(float):
        def __str__(self) -> str:
            raise AssertionError("client_secret=capability-float-subclass-secret")

    for value in (HostileCapabilityOrder(3), HostileCapabilityScore(0.65)):
        with pytest.raises(TypeError) as exc_info:
            _ensure_capability_payload_json_safe(value)

        diagnostic = str(exc_info.value)
        assert diagnostic == "non-JSON capability payload value"
        assert "HostileCapability" not in diagnostic
        assert "client_secret" not in diagnostic
        assert "subclass-secret" not in diagnostic


def test_capability_payload_rejects_container_subclasses_without_payload_leak() -> None:
    class HostileCapabilityDict(dict[str, Any]):
        def items(self) -> Any:
            raise AssertionError("client_secret=capability-dict-subclass-secret")

    class HostileCapabilityList(list[Any]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=capability-list-subclass-secret")

    class HostileCapabilityTuple(tuple[Any, ...]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=capability-tuple-subclass-secret")

    for value in (
        HostileCapabilityDict({"secret": "hidden dict"}),
        HostileCapabilityList(["hidden list"]),
        HostileCapabilityTuple(("hidden tuple",)),
    ):
        with pytest.raises(TypeError) as exc_info:
            _ensure_capability_payload_json_safe(value)

        diagnostic = str(exc_info.value)
        assert diagnostic == "non-JSON capability payload value"
        assert "HostileCapability" not in diagnostic
        assert "client_secret" not in diagnostic
        assert "subclass-secret" not in diagnostic
        assert "hidden" not in diagnostic


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


def test_intake_work_note_redacts_and_normalizes_untrusted_values() -> None:
    feedback = IntakeFeedback(
        story_number="STRY0010013\nclient_secret=story-secret",
        outcome=SuitabilityOutcome.NEEDS_CLARIFICATION,
        reason_codes=["missing_detail:field_type\napi_key=reason-secret"],
        guidance=["Add the missing detail.\nclient_secret=guidance-secret"],
        suggested_story="Target table: rm_story\nclient_secret=rewrite-secret",
        content_hash="a" * 64,
    )

    note = intake_feedback_work_note(feedback)

    assert "story-secret" not in note
    assert "reason-secret" not in note
    assert "guidance-secret" not in note
    assert "rewrite-secret" not in note
    assert "client_secret=***REDACTED***" in note
    assert "api_key=***REDACTED***" in note
    assert "Suggested rewrite:\nTarget table: rm_story client_secret=" in note


def test_intake_work_note_bounds_untrusted_values() -> None:
    feedback = IntakeFeedback(
        story_number=f"STRY0010013 {'A' * 2200}",
        outcome=SuitabilityOutcome.NEEDS_CLARIFICATION,
        reason_codes=[f"missing_detail:field_type {'B' * 2200}"],
        guidance=[f"Add the missing detail. {'C' * 2200}"],
        suggested_story=f"Target table: rm_story {'D' * 2200}",
        content_hash="a" * 64,
    )

    note = intake_feedback_work_note(feedback)

    assert note.count("...[truncated]") == 4
    assert len(note) < 2400


def test_intake_work_note_bounds_reason_and_guidance_collections() -> None:
    feedback = IntakeFeedback(
        story_number="STRY0010013",
        outcome=SuitabilityOutcome.NEEDS_CLARIFICATION,
        reason_codes=[f"missing_detail:field_{index}" for index in range(70)],
        guidance=[f"Guidance item {index}" for index in range(70)],
        suggested_story=None,
        content_hash="a" * 64,
    )

    note = intake_feedback_work_note(feedback)

    assert "missing_detail:field_0" in note
    assert "missing_detail:field_49" in note
    assert "missing_detail:field_50" not in note
    assert "intake reason codes omitted: 20 entries" in note
    assert "Guidance item 49" in note
    assert "Guidance item 50" not in note
    assert "intake guidance items omitted: 20 entries" in note
