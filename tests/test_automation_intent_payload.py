from __future__ import annotations

from jedi_devproject.automation_intent import (
    AutomationIntent,
    AutomationIntentSource,
    AutomationIntentType,
    parsed_automation_intent,
)
from jedi_devproject.capabilities import Capability


def _intent(*, required_instance_context: list[str] | None = None) -> AutomationIntent:
    return AutomationIntent(
        source=AutomationIntentSource.STRUCTURED,
        intent_type=AutomationIntentType.BUSINESS_RULE,
        capability=Capability.BUSINESS_RULE_GENERATE,
        required_instance_context=required_instance_context or [],
    )


def test_parsed_automation_intent_round_trips_a_dumped_intent() -> None:
    intent = _intent(required_instance_context=["table_schema", "business_rules"])
    parsed = parsed_automation_intent(intent.model_dump())
    assert parsed == intent
    assert parsed is not None
    assert parsed.required_instance_context == ["table_schema", "business_rules"]


def test_parsed_automation_intent_rejects_non_mapping_payloads() -> None:
    assert parsed_automation_intent(None) is None
    assert parsed_automation_intent("structured") is None
    assert parsed_automation_intent(["structured"]) is None


def test_parsed_automation_intent_rejects_payloads_that_do_not_validate() -> None:
    assert parsed_automation_intent({}) is None
    assert (
        parsed_automation_intent(
            {"source": "structured", "intent_type": "business_rule"}
        )
        is None
    )
    malformed = _intent().model_dump()
    malformed["required_instance_context"] = [1, 2]
    assert parsed_automation_intent(malformed) is None
    drifted = _intent().model_dump()
    drifted["not_a_known_field"] = "value"
    assert parsed_automation_intent(drifted) is None
