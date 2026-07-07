"""Branch-precedence pins for the free-text capability routing rule order.

The free-text routing chain in ``capability_routing`` is order-sensitive:
points gates run before forbidden-detail checks, forbidden-detail checks run
before the unsupported-capability gate, and matched rules must never fall
through to the terminal dictionary/form outcome. These tests pin that
precedence with stories that match more than one rule at once.
"""

from __future__ import annotations

from jedi_devproject.capabilities import Capability, SuitabilityOutcome
from jedi_devproject.capability_analysis import analyze_story_capabilities
from jedi_devproject.models import DataClassification, Story

_FORBIDDEN_BUSINESS_RULE_DESCRIPTION = (
    "Create a before update Business Rule on the Incident table. "
    "Condition: priority changes to 1 - Critical. Expected behavior: "
    "set work_notes to Priority escalated by automation. Fields read: "
    "priority. Fields written: work_notes. The rule must also copy the "
    "priority note onto a related record in another table."
)

_FORBIDDEN_BUSINESS_RULE_REASON = (
    "business rule generation includes forbidden behavior: cross-table writes"
)


def _story(
    *,
    short_description: str,
    description: str,
    acceptance_criteria: str,
    number: str = "STRY0010001",
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


def test_points_gate_wins_over_forbidden_detail_rule_when_both_match() -> None:
    assessment = analyze_story_capabilities(
        _story(
            short_description="Create Incident priority note Business Rule",
            description=_FORBIDDEN_BUSINESS_RULE_DESCRIPTION,
            acceptance_criteria="- The rule runs before update only.",
            story_points=8,
        )
    )

    assert assessment.outcome is SuitabilityOutcome.MANUAL_DEVELOPER_BUILD
    assert assessment.reasons == ["story points exceed full-maturity max: 8.0 > 5"]
    assert _FORBIDDEN_BUSINESS_RULE_REASON not in assessment.reasons


def test_forbidden_detail_rule_wins_over_unsupported_capability_gate() -> None:
    assessment = analyze_story_capabilities(
        _story(
            short_description="Create Incident priority note Business Rule",
            description=(
                f"{_FORBIDDEN_BUSINESS_RULE_DESCRIPTION} "
                "Only admins can update the copied record."
            ),
            acceptance_criteria="- The rule runs before update only.",
            story_points=3,
        )
    )

    assert assessment.outcome is SuitabilityOutcome.MANUAL_DEVELOPER_BUILD
    assert assessment.reasons == [_FORBIDDEN_BUSINESS_RULE_REASON]
    assert Capability.ACL_MODIFY in assessment.unsupported_capabilities


def test_mid_table_forbidden_rule_never_reaches_terminal_fallthrough() -> None:
    assessment = analyze_story_capabilities(
        _story(
            short_description="Create Incident priority note Business Rule",
            description=_FORBIDDEN_BUSINESS_RULE_DESCRIPTION,
            acceptance_criteria="- The rule runs before update only.",
            story_points=3,
        )
    )

    assert assessment.outcome is SuitabilityOutcome.MANUAL_DEVELOPER_BUILD
    assert assessment.reasons == [_FORBIDDEN_BUSINESS_RULE_REASON]
    assert "supported low-complexity dictionary/form request" not in assessment.reasons
    assert "supported table-local business rule generation request" not in assessment.reasons
