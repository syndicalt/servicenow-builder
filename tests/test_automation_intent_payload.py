from __future__ import annotations

from jedi_devproject.automation_intent import (
    AutomationIntent,
    AutomationIntentSource,
    AutomationIntentType,
    intent_required_instance_context,
)
from jedi_devproject.capabilities import Capability


def _intent(*, required_instance_context: list[str] | None = None) -> AutomationIntent:
    return AutomationIntent(
        source=AutomationIntentSource.STRUCTURED,
        intent_type=AutomationIntentType.BUSINESS_RULE,
        capability=Capability.BUSINESS_RULE_GENERATE,
        required_instance_context=required_instance_context or [],
    )


def test_intent_required_instance_context_reads_a_dumped_intent() -> None:
    payload = _intent(
        required_instance_context=["table_schema", "business_rules"]
    ).model_dump()
    assert intent_required_instance_context(payload) == ["table_schema", "business_rules"]


def test_intent_required_instance_context_survives_unrelated_schema_drift() -> None:
    # The surface override is a context-gating input: a payload written by a
    # different schema revision must not silently lose a valid override just
    # because an unrelated field drifted.
    drifted = _intent(required_instance_context=["business_rules"]).model_dump()
    drifted["field_from_a_newer_schema_revision"] = "value"
    del drifted["source"]
    assert intent_required_instance_context(drifted) == ["business_rules"]


def test_intent_required_instance_context_coerces_non_string_items() -> None:
    payload = _intent().model_dump()
    payload["required_instance_context"] = ["table_schema", 7]
    assert intent_required_instance_context(payload) == ["table_schema", "7"]


def test_intent_required_instance_context_rejects_non_mapping_payloads() -> None:
    assert intent_required_instance_context(None) is None
    assert intent_required_instance_context("structured") is None
    assert intent_required_instance_context(["structured"]) is None


def test_intent_required_instance_context_rejects_non_list_field() -> None:
    assert intent_required_instance_context({}) is None
    payload = _intent().model_dump()
    payload["required_instance_context"] = "table_schema"
    assert intent_required_instance_context(payload) is None
