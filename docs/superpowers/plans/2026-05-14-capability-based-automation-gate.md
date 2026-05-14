# Capability-Based Automation Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace table-specific automation gating with capability-based suitability and add generic dictionary field plus form placement support for any discoverable ServiceNow table.

**Architecture:** Add a capability assessment layer that classifies stories into supported pipeline capabilities before implementation packet generation. Refactor the dictionary/form Update Set generation so table, field, and form placement intent are normalized data instead of `rm_story` assumptions. Keep model fulfillment as orchestration: analyze, generate candidate, import retrieved Update Set when supported, or write clear ServiceNow feedback when not supported.

**Tech Stack:** Python 3.13, Pydantic v2, pytest, ruff, mypy, ServiceNow Table API, ServiceNow retrieved Update Set XML importer.

---

## File Structure

- Create `src/jedi_devproject/capabilities.py`
  - Capability enums, normalized field/form intent models, assessment outcome model.
- Create `src/jedi_devproject/capability_analysis.py`
  - Deterministic story parser and suitability decision logic.
- Create `src/jedi_devproject/generic_dictionary_form.py`
  - Generic customer update generation for dictionary field, field label, and form layout placement.
- Modify `src/jedi_devproject/implementation_packet.py`
  - Include capability assessment and normalized intent in packets.
  - Stop using table allowlists as suitability blockers for supported capabilities.
- Modify `src/jedi_devproject/model_fulfillment.py`
  - Route by capability outcome: automated build, needs clarification, unsupported capability, manual developer build.
- Modify `src/jedi_devproject/update_set_handoff.py`
  - Delegate dictionary/form customer update generation to `generic_dictionary_form.py`.
- Modify `src/jedi_devproject/runtime.py`
  - Preserve failure reset behavior and support new feedback statuses.
- Modify tests:
  - `tests/test_capabilities.py`
  - `tests/test_capability_analysis.py`
  - `tests/test_generic_dictionary_form.py`
  - `tests/test_implementation_packet.py`
  - `tests/test_model_fulfillment.py`
  - `tests/test_update_set_handoff.py`
  - `tests/test_runtime.py`
  - `tests/test_project_docs.py`
- Modify docs:
  - `docs/operator-guide.md`
  - Add `docs/sprints/sprint-93-change-log.md`

## Task 1: Capability Models

**Files:**
- Create: `src/jedi_devproject/capabilities.py`
- Create: `tests/test_capabilities.py`

- [ ] **Step 1: Write failing capability model tests**

Add `tests/test_capabilities.py`:

```python
from jedi_devproject.capabilities import (
    Capability,
    FieldFormIntent,
    SuitabilityOutcome,
    StoryCapabilityAssessment,
)


def test_field_form_intent_derives_custom_field_name_from_label() -> None:
    intent = FieldFormIntent(
        target_table="incident",
        field_label="Antics",
        field_type="string",
        max_length=4000,
        placement_anchor="description",
        placement_position="below",
    )

    assert intent.field_name == "u_antics"


def test_assessment_for_supported_dictionary_form_is_automated() -> None:
    assessment = StoryCapabilityAssessment(
        story_number="STRY0010001",
        outcome=SuitabilityOutcome.AUTOMATED_BUILD,
        capabilities={
            Capability.DICTIONARY_FIELD_CREATE,
            Capability.FIELD_LABEL_CREATE,
            Capability.FORM_LAYOUT_PLACE_FIELD,
        },
        supported_capabilities={
            Capability.DICTIONARY_FIELD_CREATE,
            Capability.FIELD_LABEL_CREATE,
            Capability.FORM_LAYOUT_PLACE_FIELD,
        },
        intent=FieldFormIntent(
            target_table="incident",
            field_label="Antics",
            field_type="string",
            max_length=4000,
            placement_anchor="description",
            placement_position="below",
        ),
        reasons=["supported low-complexity dictionary/form request"],
        missing_details=[],
        unsupported_capabilities=set(),
        risk_score=0.18,
        confidence=0.82,
    )

    assert assessment.is_automated
    assert assessment.intent is not None
    assert assessment.intent.field_name == "u_antics"
    assert assessment.unsupported_capabilities == set()


def test_assessment_reports_unsupported_capability() -> None:
    assessment = StoryCapabilityAssessment(
        story_number="STRY0099999",
        outcome=SuitabilityOutcome.UNSUPPORTED_CAPABILITY,
        capabilities={Capability.FLOW_MODIFY},
        supported_capabilities={Capability.DICTIONARY_FIELD_CREATE},
        intent=None,
        reasons=["Flow Designer changes are not supported by this pipeline"],
        missing_details=[],
        unsupported_capabilities={Capability.FLOW_MODIFY},
        risk_score=0.65,
        confidence=0.7,
    )

    assert not assessment.is_automated
    assert assessment.unsupported_capability_names == ["flow_modify"]
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m pytest tests/test_capabilities.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'jedi_devproject.capabilities'`.

- [ ] **Step 3: Implement capability models**

Create `src/jedi_devproject/capabilities.py`:

```python
from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Capability(StrEnum):
    DICTIONARY_FIELD_CREATE = "dictionary_field_create"
    FIELD_LABEL_CREATE = "field_label_create"
    FORM_LAYOUT_PLACE_FIELD = "form_layout_place_field"
    CHOICE_VALUES_CREATE = "choice_values_create"
    ACL_MODIFY = "acl_modify"
    FLOW_MODIFY = "flow_modify"
    BUSINESS_RULE_CREATE = "business_rule_create"
    SCRIPT_INCLUDE_MODIFY = "script_include_modify"
    DATA_MIGRATION = "data_migration"
    INTEGRATION_MODIFY = "integration_modify"
    UNKNOWN = "unknown"


class SuitabilityOutcome(StrEnum):
    AUTOMATED_BUILD = "automated_build"
    NEEDS_CLARIFICATION = "needs_clarification"
    UNSUPPORTED_CAPABILITY = "unsupported_capability"
    MANUAL_DEVELOPER_BUILD = "manual_developer_build"


class FieldFormIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_table: str
    field_label: str
    field_type: str
    field_name: str | None = None
    max_length: int | None = None
    mandatory: bool = False
    default_value: str = ""
    placement_anchor: str | None = None
    placement_position: str = "below"

    @field_validator("target_table", "field_label", "field_type")
    @classmethod
    def require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned == "":
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("placement_position")
    @classmethod
    def validate_position(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"above", "below", "end"}:
            raise ValueError("placement_position must be above, below, or end")
        return cleaned

    @model_validator(mode="after")
    def normalize_field_name(self) -> FieldFormIntent:
        if self.field_name is not None and self.field_name.strip() != "":
            self.field_name = _normalize_field_name(self.field_name)
            return self
        self.field_name = _derive_custom_field_name(self.field_label)
        return self


class StoryCapabilityAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    story_number: str
    outcome: SuitabilityOutcome
    capabilities: set[Capability]
    supported_capabilities: set[Capability]
    intent: FieldFormIntent | None = None
    reasons: list[str] = Field(default_factory=list)
    missing_details: list[str] = Field(default_factory=list)
    unsupported_capabilities: set[Capability] = Field(default_factory=set)
    risk_score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)

    @property
    def is_automated(self) -> bool:
        return self.outcome is SuitabilityOutcome.AUTOMATED_BUILD

    @property
    def unsupported_capability_names(self) -> list[str]:
        return sorted(capability.value for capability in self.unsupported_capabilities)


def _normalize_field_name(value: str) -> str:
    cleaned = value.strip().lower()
    cleaned = re.sub(r"[^a-z0-9_]", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned.startswith("u_"):
        cleaned = f"u_{cleaned}"
    return cleaned


def _derive_custom_field_name(label: str) -> str:
    return _normalize_field_name(label)
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
python3 -m pytest tests/test_capabilities.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/jedi_devproject/capabilities.py tests/test_capabilities.py
git commit -m "Add capability assessment models"
```

## Task 2: Target-Agnostic Capability Analyzer

**Files:**
- Create: `src/jedi_devproject/capability_analysis.py`
- Create: `tests/test_capability_analysis.py`

- [ ] **Step 1: Write failing analyzer tests**

Add `tests/test_capability_analysis.py`:

```python
from jedi_devproject.capabilities import Capability, SuitabilityOutcome
from jedi_devproject.capability_analysis import analyze_story_capabilities
from jedi_devproject.models import DataClassification, Story


def _story(
    *,
    number: str = "STRY0010001",
    short_description: str,
    description: str,
    acceptance_criteria: str,
    story_points: float = 2,
) -> Story:
    return Story(
        sys_id="story-sys-id",
        number=number,
        short_description=short_description,
        description=description,
        acceptance_criteria=acceptance_criteria,
        story_points=story_points,
        priority=4,
        state="Ready",
        data_classification=DataClassification.PUBLIC,
    )


def test_incident_field_story_is_automated_dictionary_form() -> None:
    assessment = analyze_story_capabilities(
        _story(
            short_description="Add a New Field to the Incident Form",
            description=(
                "As an incident manager, I would like a new field added to the "
                "Incident form.\n\n- Field Name: Antics\n- Field Type: String\n"
                "- Length: 4000"
            ),
            acceptance_criteria=(
                "- A new field labeled Antics exists on the incident form.\n"
                "- The field is placed below the Description field.\n"
                "- All incident users are able to read and write to the Antics field."
            ),
        )
    )

    assert assessment.outcome is SuitabilityOutcome.AUTOMATED_BUILD
    assert assessment.intent is not None
    assert assessment.intent.target_table == "incident"
    assert assessment.intent.field_label == "Antics"
    assert assessment.intent.field_name == "u_antics"
    assert assessment.intent.field_type == "string"
    assert assessment.intent.max_length == 4000
    assert assessment.intent.placement_anchor == "description"
    assert assessment.intent.placement_position == "below"
    assert assessment.capabilities == {
        Capability.DICTIONARY_FIELD_CREATE,
        Capability.FIELD_LABEL_CREATE,
        Capability.FORM_LAYOUT_PLACE_FIELD,
    }


def test_story_field_story_remains_automated_dictionary_form() -> None:
    assessment = analyze_story_capabilities(
        _story(
            number="STRY0010013",
            short_description="Add AI Review Notes field to Story form",
            description=(
                "Add a new custom field to the rm_story table named u_ai_review_notes "
                "and place it on the Story form below Description."
            ),
            acceptance_criteria="The AI Review Notes field stores review notes.",
        )
    )

    assert assessment.outcome is SuitabilityOutcome.AUTOMATED_BUILD
    assert assessment.intent is not None
    assert assessment.intent.target_table == "rm_story"
    assert assessment.intent.field_name == "u_ai_review_notes"


def test_missing_target_table_needs_clarification() -> None:
    assessment = analyze_story_capabilities(
        _story(
            short_description="Add a new field",
            description="Add a new string field named Comments below Description.",
            acceptance_criteria="The field is visible on the form.",
        )
    )

    assert assessment.outcome is SuitabilityOutcome.NEEDS_CLARIFICATION
    assert "target table" in assessment.missing_details


def test_acl_requirement_is_unsupported_capability() -> None:
    assessment = analyze_story_capabilities(
        _story(
            short_description="Add restricted Incident field",
            description=(
                "Add a string field named Security Notes to the Incident form and "
                "create an ACL so only admins can write it."
            ),
            acceptance_criteria="Only admins can write Security Notes.",
        )
    )

    assert assessment.outcome is SuitabilityOutcome.UNSUPPORTED_CAPABILITY
    assert Capability.ACL_MODIFY in assessment.unsupported_capabilities


def test_high_point_story_routes_to_manual_developer_build() -> None:
    assessment = analyze_story_capabilities(
        _story(
            short_description="Add incident automation",
            description="Add a field to the Incident form and update assignment workflow.",
            acceptance_criteria="The workflow assigns incidents to the right group.",
            story_points=8,
        )
    )

    assert assessment.outcome is SuitabilityOutcome.MANUAL_DEVELOPER_BUILD
    assert "story points exceed max: 8.0 > 3" in assessment.reasons
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m pytest tests/test_capability_analysis.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'jedi_devproject.capability_analysis'`.

- [ ] **Step 3: Implement deterministic analyzer**

Create `src/jedi_devproject/capability_analysis.py`:

```python
from __future__ import annotations

import re

from jedi_devproject.capabilities import (
    Capability,
    FieldFormIntent,
    StoryCapabilityAssessment,
    SuitabilityOutcome,
)
from jedi_devproject.models import Story
from jedi_devproject.risk import RiskInput, calculate_risk_score

SUPPORTED_BASELINE_CAPABILITIES = {
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
    reasons: list[str] = []

    if story.story_points > MAX_AUTOMATED_POINTS:
        reasons.append(f"story points exceed max: {story.story_points:.1f} > {MAX_AUTOMATED_POINTS}")
        return _assessment(
            story=story,
            outcome=SuitabilityOutcome.MANUAL_DEVELOPER_BUILD,
            requested=requested,
            supported=supported_capabilities,
            intent=intent,
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
            reasons=reasons,
            missing_details=missing_details,
            unsupported=unsupported,
        )

    reasons.append("supported low-complexity dictionary/form request")
    return _assessment(
        story=story,
        outcome=SuitabilityOutcome.AUTOMATED_BUILD,
        requested=requested,
        supported=supported_capabilities,
        intent=intent,
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
    reasons: list[str],
    missing_details: list[str],
    unsupported: set[Capability],
) -> StoryCapabilityAssessment:
    target_table = intent.target_table if intent is not None else "unknown"
    field_name = intent.field_name if intent is not None else None
    risk_score = calculate_risk_score(
        RiskInput(
            story_type="dictionary_form" if intent is not None else "unknown",
            affected_tables=sorted(capability.value for capability in requested),
            target_table=target_table,
            field_name=field_name,
        )
    )
    confidence = 0.82 if outcome is SuitabilityOutcome.AUTOMATED_BUILD else 0.5
    return StoryCapabilityAssessment(
        story_number=story.number,
        outcome=outcome,
        capabilities=requested,
        supported_capabilities=supported,
        intent=intent,
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
    if "business rule" in text:
        capabilities.add(Capability.BUSINESS_RULE_CREATE)
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
    if _is_dictionary_form_request(text) and _field_label(text) is None and _field_name(text) is None:
        missing.append("field label or field name")
    if _is_dictionary_form_request(text) and _field_type(text) is None:
        missing.append("field type")
    return missing


def _is_dictionary_form_request(text: str) -> bool:
    return ("field" in text or "column" in text) and "form" in text


def _field_form_intent(story: Story, text: str) -> FieldFormIntent | None:
    target_table = _target_table(text)
    field_label = _field_label(text)
    field_name = _field_name(text)
    field_type = _field_type(text)
    if target_table is None or field_type is None or (field_label is None and field_name is None):
        return None
    return FieldFormIntent(
        target_table=target_table,
        field_label=field_label or field_name.replace("u_", "").replace("_", " ").title(),
        field_name=field_name,
        field_type=field_type,
        max_length=_max_length(text),
        placement_anchor=_placement_anchor(text),
        placement_position=_placement_position(text),
        mandatory="mandatory" in text or "required" in text,
        default_value=str(story.additional_context.get("default_value", "")),
    )


def _target_table(text: str) -> str | None:
    if "incident" in text:
        return "incident"
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
    match = re.search(r"field labeled ([a-zA-Z0-9 _-]+?)(?: exists| is| on| below|\\.|\\n|$)", text)
    if match:
        return _title_label(match.group(1))
    match = re.search(r"field name: ([a-zA-Z0-9 _-]+)", text)
    if match:
        return _title_label(match.group(1))
    match = re.search(r"field named ([a-zA-Z0-9 _-]+?)(?: and| to| on| below|\\.|\\n|$)", text)
    if match:
        return _title_label(match.group(1))
    return None


def _field_name(text: str) -> str | None:
    match = re.search(r"\\b(u_[a-zA-Z0-9_]+)\\b", text)
    return match.group(1).lower() if match else None


def _field_type(text: str) -> str | None:
    match = re.search(r"field type: ([a-zA-Z0-9 _-]+)", text)
    if match:
        return _normalize_field_type(match.group(1))
    for candidate in ["string", "integer", "boolean", "date", "datetime", "journal"]:
        if candidate in text:
            return _normalize_field_type(candidate)
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


def _placement_anchor(text: str) -> str | None:
    if "below description" in text or "below the description" in text:
        return "description"
    match = re.search(r"below ([a-zA-Z0-9_ ]+?)(?: field|\\.|\\n|$)", text)
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
    return " ".join(word.capitalize() for word in value.strip(" .:-").split())
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
python3 -m pytest tests/test_capability_analysis.py tests/test_capabilities.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/jedi_devproject/capability_analysis.py tests/test_capability_analysis.py
git commit -m "Add target-agnostic capability analyzer"
```

## Task 3: Packet Integration

**Files:**
- Modify: `src/jedi_devproject/implementation_packet.py`
- Test: `tests/test_implementation_packet.py`

- [ ] **Step 1: Write failing packet tests**

Append to `tests/test_implementation_packet.py`:

```python
def test_build_implementation_packet_includes_capability_assessment_for_incident_field() -> None:
    story = _story().model_copy(
        update={
            "number": "STRY0010001",
            "short_description": "Add a New Field to the Incident Form",
            "description": (
                "As an incident manager, I would like a new field added to the "
                "Incident form.\n\n- Field Name: Antics\n- Field Type: String\n"
                "- Length: 4000"
            ),
            "acceptance_criteria": (
                "- A new field labeled Antics exists on the incident form.\n"
                "- The field is placed below the Description field."
            ),
            "affected_tables": [],
        }
    )

    packet = build_implementation_packet(
        story=story,
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
    )

    assert packet.safety_decision == "automated_build"
    assert packet.capability_assessment["outcome"] == "automated_build"
    assert packet.normalized_intent == {
        "target_table": "incident",
        "field_label": "Antics",
        "field_name": "u_antics",
        "field_type": "string",
        "max_length": 4000,
        "mandatory": False,
        "default_value": "",
        "placement_anchor": "description",
        "placement_position": "below",
    }
    assert packet.output_contract["capabilities"] == [
        "dictionary_field_create",
        "field_label_create",
        "form_layout_place_field",
    ]
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
python3 -m pytest tests/test_implementation_packet.py::test_build_implementation_packet_includes_capability_assessment_for_incident_field -q
```

Expected: FAIL with an attribute error for `capability_assessment` or mismatched `safety_decision`.

- [ ] **Step 3: Modify packet models and builder**

In `src/jedi_devproject/implementation_packet.py`:

Add imports:

```python
from jedi_devproject.capability_analysis import analyze_story_capabilities
from jedi_devproject.capabilities import SuitabilityOutcome
```

Add fields to `ImplementationPacket`:

```python
    capability_assessment: dict[str, Any] = Field(default_factory=dict)
    normalized_intent: dict[str, Any] | None = None
```

Update `build_implementation_packet()` so it computes assessment before safety:

```python
    assessment = analyze_story_capabilities(story)
    safety_decision = assessment.outcome.value
    safety_reasons = assessment.reasons + [
        f"missing detail: {detail}" for detail in assessment.missing_details
    ] + [
        f"unsupported capability: {capability.value}"
        for capability in sorted(assessment.unsupported_capabilities, key=lambda item: item.value)
    ]
```

Use these values in the returned packet:

```python
        safety_decision=safety_decision,
        safety_reasons=safety_reasons,
        risk_score=assessment.risk_score,
        capability_assessment=assessment.model_dump(mode="json"),
        normalized_intent=(
            assessment.intent.model_dump(mode="json") if assessment.intent is not None else None
        ),
        allowed_tables=sorted(policy.tables),
        allowed_operations=sorted(policy.operations),
```

Update `to_model_payload()` controls:

```python
                "capability_assessment": self.capability_assessment,
                "normalized_intent": self.normalized_intent,
```

Update `output_contract` creation:

```python
            "capabilities": sorted(capability.value for capability in assessment.capabilities),
            "must_follow_normalized_intent": True,
```

- [ ] **Step 4: Keep legacy tests passing**

If existing tests assert `packet.safety_decision == "eligible"`, update them to assert the new `automated_build` outcome for automatable dictionary/form work. If a test is specifically about legacy safety, move that assertion to `tests/test_safety.py` instead of packet tests.

Run:

```bash
python3 -m pytest tests/test_implementation_packet.py tests/test_safety.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/jedi_devproject/implementation_packet.py tests/test_implementation_packet.py
git commit -m "Include capability assessment in implementation packets"
```

## Task 4: Candidate Generation Uses Capability Outcome

**Files:**
- Modify: `src/jedi_devproject/implementation_packet.py`
- Test: `tests/test_implementation_packet.py`

- [ ] **Step 1: Write failing candidate tests**

Append to `tests/test_implementation_packet.py`:

```python
def test_generate_candidate_invokes_model_for_automated_capability_outcome() -> None:
    story = _story().model_copy(
        update={
            "number": "STRY0010001",
            "short_description": "Add a New Field to the Incident Form",
            "description": (
                "As an incident manager, I would like a new field added to the "
                "Incident form.\n\n- Field Name: Antics\n- Field Type: String\n"
                "- Length: 4000"
            ),
            "acceptance_criteria": (
                "- A new field labeled Antics exists on the incident form.\n"
                "- The field is placed below the Description field."
            ),
            "affected_tables": [],
        }
    )
    provider = RecordingImplementationProvider(
        {
            "changes": [
                {
                    "table": "sys_dictionary",
                    "operation": "insert",
                    "fields": {
                        "name": "incident",
                        "element": "u_antics",
                        "column_label": "Antics",
                        "internal_type": "string",
                        "max_length": 4000,
                    },
                },
                {
                    "table": "sys_ui_form",
                    "operation": "update",
                    "fields": {
                        "name": "incident",
                        "field_order": "u_antics",
                        "placement_anchor": "description",
                        "placement_position": "below",
                    },
                },
            ],
            "test_plan": ["Confirm Antics exists on Incident below Description."],
            "rollback_notes": ["Remove incident.u_antics and form placement."],
        }
    )

    candidate = generate_implementation_update_set_candidate(
        story=story,
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        provider=provider,
    )

    assert candidate.status is CandidateStatus.READY_FOR_REVIEW
    assert candidate.changes[0].fields["name"] == "incident"
    assert candidate.changes[0].fields["element"] == "u_antics"
    assert provider.payloads


def test_generate_candidate_skips_model_for_needs_clarification() -> None:
    story = _story().model_copy(
        update={
            "short_description": "Add a new field",
            "description": "Add a string field named Comments below Description.",
            "acceptance_criteria": "The field is visible on the form.",
            "affected_tables": [],
        }
    )
    provider = RecordingImplementationProvider({"changes": [], "test_plan": [], "rollback_notes": []})

    candidate = generate_implementation_update_set_candidate(
        story=story,
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        provider=provider,
    )

    assert candidate.status is CandidateStatus.MANUAL_BUILD
    assert "missing detail: target table" in candidate.eligibility_reasons
    assert provider.payloads == []
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m pytest tests/test_implementation_packet.py::test_generate_candidate_invokes_model_for_automated_capability_outcome tests/test_implementation_packet.py::test_generate_candidate_skips_model_for_needs_clarification -q
```

Expected: first test FAILS because current code only invokes model for `eligible`, second may pass or fail depending on packet changes.

- [ ] **Step 3: Update candidate generation condition**

In `generate_implementation_update_set_candidate_from_packet()`:

```python
    if packet.safety_decision != SuitabilityOutcome.AUTOMATED_BUILD.value:
        return _manual_review_candidate(packet=packet)
```

Update `_candidate_decision()` to treat `automated_build` as eligible:

```python
    if value == "automated_build":
        return "eligible"
```

Keep support for `"eligible"` so older tests or artifacts can still parse during migration.

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
python3 -m pytest tests/test_implementation_packet.py tests/test_model_fulfillment.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/jedi_devproject/implementation_packet.py tests/test_implementation_packet.py
git commit -m "Route model invocation by capability outcome"
```

## Task 5: Generic Dictionary/Form Customer Updates

**Files:**
- Create: `src/jedi_devproject/generic_dictionary_form.py`
- Create: `tests/test_generic_dictionary_form.py`
- Modify: `src/jedi_devproject/update_set_handoff.py`
- Modify: `tests/test_update_set_handoff.py`

- [ ] **Step 1: Write failing generic builder tests**

Create `tests/test_generic_dictionary_form.py`:

```python
from typing import Any

from jedi_devproject.generic_dictionary_form import (
    DictionaryFormIntent,
    dictionary_form_customer_updates,
)


class FakeMetadataClient:
    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if table == "sys_ui_section" and lookup == {"name": "incident"}:
            return [
                {
                    "sys_id": "incident-main-section",
                    "name": "incident",
                    "caption": "",
                    "view": {"display_value": "Default view", "value": "default"},
                    "sys_user": "",
                }
            ]
        if table == "sys_ui_element" and lookup == {
            "name": "incident",
            "sys_ui_section": "incident-main-section",
        }:
            return [
                {"sys_id": "short-description-element", "element": "short_description", "position": "1"},
                {"sys_id": "description-element", "element": "description", "position": "2"},
            ]
        return []


def test_generic_dictionary_form_updates_incident_field_and_form() -> None:
    updates = dictionary_form_customer_updates(
        client=FakeMetadataClient(),
        intent=DictionaryFormIntent(
            target_table="incident",
            field_label="Antics",
            field_name="u_antics",
            field_type="string",
            max_length=4000,
            mandatory=False,
            default_value="",
            placement_anchor="description",
            placement_position="below",
        ),
        remote_update_set_sys_id="remote-sys-id",
    )

    assert [update["name"] for update in updates] == [
        "sys_dictionary_incident_u_antics",
        "sys_documentation_incident_u_antics_en",
        "sys_ui_section_incident-main-section",
    ]
    assert updates[0]["target_name"] == "Incident.Antics"
    assert "<name>incident</name>" in updates[0]["payload"]
    assert "<element>u_antics</element>" in updates[0]["payload"]
    assert "<max_length>4000</max_length>" in updates[0]["payload"]
    assert "<label>Antics</label>" in updates[1]["payload"]
    assert "<element>u_antics</element><position>3</position>" in updates[2]["payload"]


def test_generic_dictionary_form_fails_when_anchor_missing() -> None:
    try:
        dictionary_form_customer_updates(
            client=FakeMetadataClient(),
            intent=DictionaryFormIntent(
                target_table="incident",
                field_label="Antics",
                field_name="u_antics",
                field_type="string",
                max_length=4000,
                placement_anchor="caller_id",
                placement_position="below",
            ),
            remote_update_set_sys_id="remote-sys-id",
        )
    except ValueError as exc:
        assert "form placement anchor not found: caller_id" in str(exc)
    else:
        raise AssertionError("missing anchor was accepted")
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
python3 -m pytest tests/test_generic_dictionary_form.py -q
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement generic builder**

Create `src/jedi_devproject/generic_dictionary_form.py` by moving the table-neutral XML construction from `update_set_handoff.py` into this module. The public API must be:

```python
from __future__ import annotations

from html import escape
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict


class DictionaryFormMetadataClient(Protocol):
    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...


class DictionaryFormIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_table: str
    field_label: str
    field_name: str
    field_type: str
    max_length: int | None = None
    mandatory: bool = False
    default_value: str = ""
    placement_anchor: str | None = None
    placement_position: str = "below"


def dictionary_form_customer_updates(
    *,
    client: DictionaryFormMetadataClient,
    intent: DictionaryFormIntent,
    remote_update_set_sys_id: str,
) -> list[dict[str, Any]]:
    return [
        _dictionary_update(intent, remote_update_set_sys_id),
        _documentation_update(intent, remote_update_set_sys_id),
        *_form_updates(client=client, intent=intent, remote_update_set_sys_id=remote_update_set_sys_id),
    ]
```

Implement helpers with current XML style from `update_set_handoff.py`, replacing hardcoded `rm_story`, `u_ai_review_notes`, and Story labels with `intent.target_table`, `intent.field_name`, and `intent.field_label`. Target name can be `f"{_table_label(intent.target_table)}.{intent.field_label}"`, where `_table_label("incident") == "Incident"` and `_table_label("rm_story") == "Story"`.

- [ ] **Step 4: Refactor handoff to call generic builder**

In `src/jedi_devproject/update_set_handoff.py`, replace dictionary/form helper internals with:

```python
from jedi_devproject.generic_dictionary_form import (
    DictionaryFormIntent,
    dictionary_form_customer_updates,
)
```

In `_customer_updates_for_candidate()`, collect one dictionary change and one form change into a normalized `DictionaryFormIntent`. Use:

```python
intent = _dictionary_form_intent(candidate.changes)
updates.extend(
    dictionary_form_customer_updates(
        client=client,
        intent=intent,
        remote_update_set_sys_id=remote_update_set_sys_id,
    )
)
```

`_dictionary_form_intent()` must:

- Read dictionary fields: `name`, `element`, `column_label`, `internal_type`, `max_length`, `mandatory`, `default_value`.
- Read form fields: `name`, `field_order`, `placement_anchor`, `placement_position`.
- Require both changes to target the same table.
- Raise `ValueError("dictionary/form handoff requires a sys_dictionary change")` when missing dictionary change.
- Raise `ValueError("dictionary/form handoff requires a sys_ui_form change")` when missing form change.

- [ ] **Step 5: Run tests and verify pass**

Run:

```bash
python3 -m pytest tests/test_generic_dictionary_form.py tests/test_update_set_handoff.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/jedi_devproject/generic_dictionary_form.py src/jedi_devproject/update_set_handoff.py tests/test_generic_dictionary_form.py tests/test_update_set_handoff.py
git commit -m "Generalize dictionary form update generation"
```

## Task 6: Model Fulfillment Feedback Outcomes

**Files:**
- Modify: `src/jedi_devproject/model_fulfillment.py`
- Test: `tests/test_model_fulfillment.py`

- [ ] **Step 1: Write failing feedback tests**

Add tests to `tests/test_model_fulfillment.py`:

```python
def test_model_fulfillment_writes_needs_clarification_feedback() -> None:
    client = FakeModelClient(
        story=Story(
            sys_id="story-sys-id",
            number="STRY0090001",
            short_description="Add a new field",
            description="Add a string field named Comments below Description.",
            acceptance_criteria="The field is visible on the form.",
            story_points=2,
            priority=4,
            state="Work in Progress",
            data_classification=DataClassification.PUBLIC,
        )
    )
    handler = model_candidate_fulfillment_handler(
        client=client,
        config=ModelCandidateFulfillmentConfig(
            policy=_policy(),
            provider_policy=_provider_policy(),
            rags=_rags(),
            provider=RecordingModelProvider(),
            instance_url="https://dev205693.service-now.com",
        ),
    )

    result = handler(_job().model_copy(update={"story_number": "STRY0090001"}))
    assert result.after_artifacts_persisted is not None
    result.after_artifacts_persisted(
        [
            FulfillmentPersistedArtifact(
                artifact_kind="implementation_candidate",
                path="db://artifact_blobs/90",
                sha256="c" * 64,
                artifact_id=90,
            )
        ]
    )

    assert client.imports == []
    assert client.updated_fields[-1]["fields"]["u_ai_status"] == "Needs Clarification"
    assert "target table" in client.updated_fields[-1]["fields"]["work_notes"]


def test_model_fulfillment_builds_incident_dictionary_form_candidate() -> None:
    client = FakeModelClient(
        story=Story(
            sys_id="story-sys-id",
            number="STRY0010001",
            short_description="Add a New Field to the Incident Form",
            description=(
                "As an incident manager, I would like a new field added to the "
                "Incident form.\n\n- Field Name: Antics\n- Field Type: String\n"
                "- Length: 4000"
            ),
            acceptance_criteria=(
                "- A new field labeled Antics exists on the incident form.\n"
                "- The field is placed below the Description field."
            ),
            story_points=2,
            priority=4,
            state="Work in Progress",
            data_classification=DataClassification.PUBLIC,
        )
    )
    provider = RecordingModelProvider(
        response={
            "changes": [
                {
                    "table": "sys_dictionary",
                    "operation": "insert",
                    "fields": {
                        "name": "incident",
                        "element": "u_antics",
                        "column_label": "Antics",
                        "internal_type": "string",
                        "max_length": 4000,
                    },
                },
                {
                    "table": "sys_ui_form",
                    "operation": "update",
                    "fields": {
                        "name": "incident",
                        "field_order": "u_antics",
                        "placement_anchor": "description",
                        "placement_position": "below",
                    },
                },
            ],
            "test_plan": ["Confirm Antics is visible below Description."],
            "rollback_notes": ["Remove incident.u_antics."],
        }
    )
    handler = model_candidate_fulfillment_handler(
        client=client,
        config=ModelCandidateFulfillmentConfig(
            policy=_policy(),
            provider_policy=_provider_policy(),
            rags=_rags(),
            provider=provider,
            instance_url="https://dev205693.service-now.com",
        ),
    )

    result = handler(_job().model_copy(update={"story_number": "STRY0010001"}))

    assert result.artifacts[1].payload_json is not None
    assert result.artifacts[1].payload_json["status"] == "Ready for Review"
    assert result.artifacts[1].payload_json["changes"][0]["fields"]["name"] == "incident"
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m pytest tests/test_model_fulfillment.py -q
```

Expected: FAIL until model fulfillment maps assessment outcomes to statuses and incident form metadata fakes exist.

- [ ] **Step 3: Implement feedback mapping**

In `src/jedi_devproject/model_fulfillment.py`, add:

```python
def _manual_feedback_fields(
    *,
    story_number: str,
    candidate: UpdateSetCandidate,
    candidate_artifact_ref: str,
) -> dict[str, object]:
    reasons = "; ".join(candidate.eligibility_reasons) or f"candidate status is {candidate.status.value}"
    if any(reason.startswith("missing detail:") for reason in candidate.eligibility_reasons):
        status = "Needs Clarification"
    elif any(reason.startswith("unsupported capability:") for reason in candidate.eligibility_reasons):
        status = "Human Review Required"
    else:
        status = "Human Review Required"
    return {
        "u_ai_status": status,
        "work_notes": (
            f"Automated implementation candidate for {story_number} did not create a retrieved "
            f"Update Set. Candidate artifact: {candidate_artifact_ref}. Reasons: {reasons}."
        ),
    }
```

Update `_write_manual_review_required()` to call this helper.

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
python3 -m pytest tests/test_model_fulfillment.py tests/test_runtime.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/jedi_devproject/model_fulfillment.py tests/test_model_fulfillment.py
git commit -m "Write capability outcome feedback to stories"
```

## Task 7: Runtime UAT Coverage for STRY0010001

**Files:**
- Modify: `tests/test_runtime.py`

- [ ] **Step 1: Add runtime test for incident UAT path**

Add a test to `tests/test_runtime.py` using the existing `RecordingTransport` and `FakeRuntimeStore` patterns:

```python
def test_process_one_runtime_fulfillment_generates_incident_update_set_candidate(
    tmp_path: Path,
) -> None:
    store = FakeRuntimeStore(
        claimed_job=_job().model_copy(update={"story_number": "STRY0010001"})
    )
    incident_story = {
        "sys_id": "incident-story-sys-id",
        "number": "STRY0010001",
        "short_description": "Add a New Field to the Incident Form",
        "description": (
            "As an incident manager, I would like a new field added to the "
            "Incident form.\n\n- Field Name: Antics\n- Field Type: String\n"
            "- Length: 4000"
        ),
        "acceptance_criteria": (
            "- A new field labeled Antics exists on the incident form.\n"
            "- The field is placed below the Description field."
        ),
        "story_points": "2",
        "priority": "4",
        "state": "Work in Progress",
    }
    transport = RecordingTransport(
        [
            HttpResponse(status_code=200, json_body={"access_token": "token-123"}),
            HttpResponse(status_code=200, json_body={"result": [incident_story]}),
            HttpResponse(
                status_code=200,
                json_body={
                    "output_text": (
                        '{"changes":[{"table":"sys_dictionary","operation":"insert",'
                        '"fields":[{"name":"name","value":"incident"},'
                        '{"name":"element","value":"u_antics"},'
                        '{"name":"column_label","value":"Antics"},'
                        '{"name":"internal_type","value":"string"},'
                        '{"name":"max_length","value":4000}]},'
                        '{"table":"sys_ui_form","operation":"update",'
                        '"fields":[{"name":"name","value":"incident"},'
                        '{"name":"field_order","value":"u_antics"},'
                        '{"name":"placement_anchor","value":"description"},'
                        '{"name":"placement_position","value":"below"}]}],'
                        '"test_plan":["Confirm Antics below Description."],'
                        '"rollback_notes":["Remove incident.u_antics."]}'
                    )
                },
            ),
            HttpResponse(
                status_code=200,
                json_body={"result": [{"operation_uri": "/api/1860704/jedi_update_set_import"}]},
            ),
            HttpResponse(status_code=201, json_body={"result": {"status": "imported"}}),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "sys_id": "incident-remote-update-set",
                            "name": "JEDI STRY0010001 - AI Candidate",
                        }
                    ]
                },
            ),
            HttpResponse(
                status_code=200,
                json_body={
                    "result": [
                        {
                            "label": "Ready for Testing",
                            "value": "-7",
                            "sequence": "300",
                            "inactive": "false",
                        }
                    ]
                },
            ),
            HttpResponse(status_code=200, json_body={"result": {"sys_id": "incident-story-sys-id"}}),
        ]
    )

    result = process_one_runtime_fulfillment(
        settings=_settings_with_openai(tmp_path, apply=True),
        store_factory=lambda _database_url: store,
        transport=transport,
    )

    assert result.status == "completed"
    assert "incident" in transport.requests[3].body["update_set_xml"]
    assert "u_antics" in transport.requests[3].body["update_set_xml"]
    assert transport.requests[-1].body["state"] == "-7"
    assert transport.requests[-1].body["u_ai_status"] == "Ready for Testing"
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
python3 -m pytest tests/test_runtime.py::test_process_one_runtime_fulfillment_generates_incident_update_set_candidate -q
```

Expected: FAIL until prior tasks are complete because the current runtime still routes `STRY0010001` to manual-review feedback instead of retrieved Update Set handoff.

- [ ] **Step 3: Adjust fakes for generic form metadata**

Add ServiceNow metadata responses before importer POST if the runtime path fetches `sys_ui_section` and `sys_ui_element`:

```python
HttpResponse(
    status_code=200,
    json_body={
        "result": [
            {
                "sys_id": "incident-main-section",
                "name": "incident",
                "caption": "",
                "view": {"display_value": "Default view", "value": "default"},
                "sys_user": "",
            }
        ]
    },
),
HttpResponse(
    status_code=200,
    json_body={
        "result": [
            {"sys_id": "number-element", "element": "number", "position": "1"},
            {"sys_id": "description-element", "element": "description", "position": "2"},
        ]
    },
),
```

Assert the request sequence by URL suffix instead of fixed indexes. Use:

```python
posted_xml_requests = [
    request
    for request in transport.requests
    if request.method == "POST" and request.url.endswith("/api/1860704/jedi_update_set_import")
]
assert len(posted_xml_requests) == 1
assert "incident" in posted_xml_requests[0].body["update_set_xml"]
assert "u_antics" in posted_xml_requests[0].body["update_set_xml"]
```

- [ ] **Step 4: Run runtime tests**

Run:

```bash
python3 -m pytest tests/test_runtime.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_runtime.py
git commit -m "Cover incident dictionary form runtime path"
```

## Task 8: Docs and Sprint Log

**Files:**
- Modify: `docs/operator-guide.md`
- Create: `docs/sprints/sprint-93-change-log.md`
- Modify: `tests/test_project_docs.py`

- [ ] **Step 1: Write failing docs tests**

Append to `tests/test_project_docs.py`:

```python
def test_operator_guide_documents_capability_based_gate() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "capability-based automation gate" in guide
    assert "table names are metadata" in guide
    assert "`dictionary_field_create`" in guide
    assert "`form_layout_place_field`" in guide
    assert "STRY0010001" in guide


def test_sprint_ninety_three_change_log_documents_generic_dictionary_form() -> None:
    change_log = Path("docs/sprints/sprint-93-change-log.md").read_text(encoding="utf-8")

    assert "STRY0010001" in change_log
    assert "incident" in change_log
    assert "u_antics" in change_log
    assert "capability-based" in change_log
    assert "generic dictionary field creation plus form placement" in change_log
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m pytest tests/test_project_docs.py::test_operator_guide_documents_capability_based_gate tests/test_project_docs.py::test_sprint_ninety_three_change_log_documents_generic_dictionary_form -q
```

Expected: FAIL because docs are not updated.

- [ ] **Step 3: Update operator guide**

Add this section to `docs/operator-guide.md` near the ChatGPT implementation adapter section:

```markdown
## Capability-Based Automation Gate

The automation gate is capability-based, not table-based. Table names are metadata for risk, discovery, and validation; they are not allowlist gates by themselves.

The baseline supported implementation capability is generic dictionary field creation plus form placement:

- `dictionary_field_create`
- `field_label_create`
- `form_layout_place_field`

For example, `STRY0010001` is expected to classify as an automated Incident dictionary/form change for `incident.u_antics` when the story describes the target table, field label, string type, length, and placement below Description.

Stories that are clear but require unsupported capabilities such as `acl_modify`, `flow_modify`, `business_rule_create`, `data_migration`, or `integration_modify` receive human-review feedback naming the missing capability. Stories missing required details receive clarification feedback.
```

- [ ] **Step 4: Add sprint log**

Create `docs/sprints/sprint-93-change-log.md`:

```markdown
# Sprint 93 Change Log

## Goal

Replace table-specific automation gating with capability-based suitability and add generic dictionary field creation plus form placement as the baseline capability.

## Changes

- Added capability assessment models and target-agnostic deterministic analysis.
- Classified `STRY0010001` as automatable dictionary/form work for `incident.u_antics`.
- Preserved `STRY0010013` as automatable dictionary/form work for `rm_story.u_ai_review_notes`.
- Generalized dictionary, documentation, and form layout customer update generation beyond `rm_story`.
- Kept retrieved Update Set handoff as the review surface.

## Tests

- Added analyzer coverage for automated, needs-clarification, unsupported-capability, and manual-developer-build outcomes.
- Added generic dictionary/form builder coverage for Incident form placement below Description.
- Added runtime coverage for the Incident UAT path.

## Decision

The gate now evaluates whether the pipeline supports the requested capability and whether the story is clear and low-complexity enough. Table names affect risk and metadata lookup, not baseline eligibility.
```

- [ ] **Step 5: Run docs tests**

Run:

```bash
python3 -m pytest tests/test_project_docs.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add docs/operator-guide.md docs/sprints/sprint-93-change-log.md tests/test_project_docs.py
git commit -m "Document capability-based automation gate"
```

## Task 9: Full Verification, Deploy, and UAT

**Files:**
- No code changes unless verification exposes a defect.

- [ ] **Step 1: Run full quality gate**

Run:

```bash
python3 -m ruff format src tests
python3 -m ruff check .
python3 -m mypy src tests
python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90
```

Expected:

- ruff format completes without uncommitted unwanted churn beyond touched files.
- ruff check passes.
- mypy passes.
- pytest passes.
- coverage remains at or above 90%.

- [ ] **Step 2: Commit formatting or verification fixes**

If Step 1 changed source or test files:

```bash
git status --short
git add src tests docs
git commit -m "Stabilize capability gate verification"
```

If Step 1 did not change files, skip this commit.

- [ ] **Step 3: Push**

Run:

```bash
git push origin master
```

Expected: push succeeds.

- [ ] **Step 4: Deploy worker**

Run:

```bash
railway deployment up --service jedi-devproject-worker --environment jedi --message "capability gate generic dictionary form" --ci
```

Expected: Railway deploy completes.

- [ ] **Step 5: Restage UAT story**

Move `STRY0010001` Draft to Ready in ServiceNow. Use the existing OAuth client pattern:

```bash
python3 - <<'PY'
from pathlib import Path
from jedi_devproject.servicenow import UrllibTransport, servicenow_client_from_env

client = servicenow_client_from_env(Path(".env"), transport=UrllibTransport())
records = client.fetch_table_records(
    table="rm_story",
    lookup={"number": "STRY0010001"},
    fields=["sys_id", "number", "state"],
    limit=1,
)
story_sys_id = str(records[0]["sys_id"])
client.update_story_fields(story_sys_id, {"state": "-6"})
client.update_story_fields(story_sys_id, {"state": "1"})
print({"story": "STRY0010001", "sys_id": story_sys_id, "restaged": True})
PY
```

Expected: the script prints `restaged=True`.

- [ ] **Step 6: Verify live UAT result**

Check ServiceNow:

```bash
python3 - <<'PY'
from pathlib import Path
from jedi_devproject.servicenow import UrllibTransport, servicenow_client_from_env

client = servicenow_client_from_env(Path(".env"), transport=UrllibTransport())
story = client.fetch_table_records(
    table="rm_story",
    lookup={"number": "STRY0010001"},
    fields=["sys_id", "number", "state", "u_ai_status"],
    limit=1,
)[0]
sets = client.fetch_table_records(
    table="sys_remote_update_set",
    lookup={"name": "JEDI STRY0010001 - AI Candidate"},
    fields=["sys_id", "name", "state", "remote_sys_id"],
    limit=5,
)
print({"story": story, "retrieved_update_sets": sets})
PY
```

Expected:

- story `u_ai_status` is `Ready for Testing`
- story state is the Ready for Testing value
- a retrieved Update Set named `JEDI STRY0010001 - AI Candidate` exists
- retrieved customer updates include `sys_dictionary_incident_u_antics`, `sys_documentation_incident_u_antics_en`, and a form layout customer update

- [ ] **Step 7: Document live evidence**

Append live UAT evidence to `docs/sprints/sprint-93-change-log.md`:

```markdown
## Live UAT

`STRY0010001` was restaged from Draft to Ready after deploying the capability-based gate. The worker generated a retrieved Update Set handoff for `incident.u_antics`, moved the story to Ready for Testing, and wrote the retrieved Update Set link back to the story.
```

Replace the generic sentence with exact sys_ids and timestamps from Step 6.

- [ ] **Step 8: Verify docs and commit live evidence**

Run:

```bash
python3 -m pytest tests/test_project_docs.py -q
git add docs/sprints/sprint-93-change-log.md
git commit -m "Document STRY0010001 capability gate UAT"
git push origin master
```

Expected: docs tests pass and commit pushes.

## Self-Review

- Spec coverage:
  - Capability taxonomy: Tasks 1 and 2.
  - Target-agnostic suitability: Task 2.
  - Generic dictionary/form baseline: Task 5.
  - Packet and fulfillment routing: Tasks 3, 4, and 6.
  - Feedback outcomes: Task 6.
  - Runtime and UAT: Tasks 7 and 9.
  - Documentation: Task 8.
- Placeholder scan:
  - This plan contains no `TBD`, `TODO`, or unspecified implementation steps.
  - Each code task includes target files, concrete test snippets, commands, and expected results.
- Type consistency:
  - `Capability`, `SuitabilityOutcome`, `FieldFormIntent`, and `StoryCapabilityAssessment` are introduced in Task 1 and reused consistently.
  - `analyze_story_capabilities()` is introduced in Task 2 and consumed by packet generation in Task 3.
  - `DictionaryFormIntent` and `dictionary_form_customer_updates()` are introduced in Task 5 and consumed by `update_set_handoff.py`.
