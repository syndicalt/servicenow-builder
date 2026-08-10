import pytest

from jedi_devproject.capabilities import Capability
from jedi_devproject.packet_model import ImplementationPacket, PacketStory
from jedi_devproject.packet_validation import (
    _candidate_decision,
    _validate_implementation_contract,
    _validate_no_raw_xml,
    _validate_response_tables_match_capability,
)
from jedi_devproject.providers import ModelResponseError


def _packet(*, capabilities: list[str]) -> ImplementationPacket:
    return ImplementationPacket(
        task="generate_implementation_candidate",
        provider_id="approved-model",
        story=PacketStory(
            number="STRY0010001",
            short_description="Create triage rule",
            description="Create a safe incident triage business rule.",
            acceptance_criteria="The rule updates only the target incident record.",
            story_points=3,
            priority=3,
            state="Ready",
            affected_tables=["incident"],
        ),
        safety_decision="eligible",
        safety_reasons=[],
        risk_score=0.2,
        allowed_tables=["sys_script"],
        allowed_operations=["insert"],
        capability_assessment={"capabilities": capabilities},
        context_sections={},
        retrieval_citations=[],
        output_contract={},
    )


def test_candidate_decision_sanitizes_unsupported_safety_decision() -> None:
    with pytest.raises(ModelResponseError) as exc:
        _candidate_decision("manual_review\nclient_secret=packet-secret")

    error = str(exc.value)
    assert "unsupported safety decision" in error
    assert "packet-secret" not in error
    assert "\n" not in error
    assert "client_secret=***REDACTED***" in error


def test_table_capability_mismatch_sanitizes_model_table_names() -> None:
    packet = _packet(capabilities=[Capability.BUSINESS_RULE_GENERATE.value])

    with pytest.raises(ModelResponseError) as exc:
        _validate_response_tables_match_capability(
            packet=packet,
            response={
                "changes": [
                    {
                        "table": "sys_user\napi_key=table-secret",
                        "operation": "insert",
                        "fields": {},
                    }
                ]
            },
        )

    error = str(exc.value)
    assert "model response tables do not match assessed capability" in error
    assert "table-secret" not in error
    assert "\n" not in error
    assert "api_key=***REDACTED***" in error


def test_table_capability_mismatch_rejects_table_object_without_leak() -> None:
    class HostileTableName:
        def __str__(self) -> str:
            raise AssertionError("client_secret=response-table-secret")

    packet = _packet(capabilities=[Capability.BUSINESS_RULE_GENERATE.value])

    with pytest.raises(ModelResponseError) as exc:
        _validate_response_tables_match_capability(
            packet=packet,
            response={
                "changes": [
                    {
                        "table": HostileTableName(),
                        "operation": "insert",
                        "fields": {},
                    }
                ]
            },
        )

    error = str(exc.value)
    assert error == "model response table names must be exact strings"
    assert "HostileTableName" not in error
    assert "response-table-secret" not in error
    assert "client_secret" not in error


def test_raw_xml_validation_fails_closed_on_excessive_nesting() -> None:
    value: object = "safe"
    for _ in range(40):
        value = {"safe": value}

    with pytest.raises(ModelResponseError, match="model response nesting exceeds limit"):
        _validate_no_raw_xml(value)


def test_raw_xml_validation_fails_closed_on_excessive_nodes() -> None:
    value = [{"safe": index} for index in range(1100)]

    with pytest.raises(ModelResponseError, match="model response size exceeds scan limit"):
        _validate_no_raw_xml(value)


def test_raw_xml_validation_rejects_raw_xml_content_with_fixed_diagnostic() -> None:
    with pytest.raises(ModelResponseError) as exc:
        _validate_no_raw_xml({"notes": "<record_update>secret</record_update>"})

    error = str(exc.value)
    assert error == "model response must not include raw XML content"
    assert "secret" not in error


def test_raw_xml_validation_rejects_non_string_dict_key_without_leak() -> None:
    class HostileKey:
        def __str__(self) -> str:
            raise AssertionError("client_secret=raw-xml-key-secret")

    with pytest.raises(ModelResponseError) as exc:
        _validate_no_raw_xml({HostileKey(): "safe"})

    error = str(exc.value)
    assert error == "model response object keys must be exact strings"
    assert "HostileKey" not in error
    assert "raw-xml-key-secret" not in error
    assert "client_secret" not in error


def test_implementation_contract_rejects_too_many_changes() -> None:
    response = {
        "changes": [{"table": "sys_script", "operation": "insert", "fields": {}}]
        * 101,
        "test_plan": ["Confirm generated changes."],
        "rollback_notes": ["Back out generated changes."],
    }

    with pytest.raises(
        ModelResponseError,
        match="implementation response includes too many changes \\(max 100\\)",
    ):
        _validate_implementation_contract(response)


def test_implementation_contract_rejects_too_many_review_items() -> None:
    response = {
        "changes": [{"table": "sys_script", "operation": "insert", "fields": {}}],
        "test_plan": ["Confirm generated changes."] * 101,
        "rollback_notes": ["Back out generated changes."],
    }

    with pytest.raises(
        ModelResponseError,
        match="test_plan includes too many items \\(max 100\\)",
    ):
        _validate_implementation_contract(response)


def test_implementation_contract_rejects_non_string_review_items_without_echo() -> None:
    response = {
        "changes": [{"table": "sys_script", "operation": "insert", "fields": {}}],
        "test_plan": [{"client_secret": "review-secret"}],
        "rollback_notes": ["Back out generated changes."],
    }

    with pytest.raises(ModelResponseError) as exc:
        _validate_implementation_contract(response)

    error = str(exc.value)
    assert error == "test_plan items must be non-empty exact strings"
    assert "review-secret" not in error


def test_implementation_contract_rejects_oversized_review_items_without_echo() -> None:
    response = {
        "changes": [{"table": "sys_script", "operation": "insert", "fields": {}}],
        "test_plan": [f"Confirm generated changes. {'A' * 2100}"],
        "rollback_notes": ["Back out generated changes."],
    }

    with pytest.raises(ModelResponseError) as exc:
        _validate_implementation_contract(response)

    error = str(exc.value)
    assert error == "test_plan item exceeds length limit (max 2000)"
    assert "AAA" not in error


def test_implementation_contract_rejects_review_item_control_characters() -> None:
    response = {
        "changes": [{"table": "sys_script", "operation": "insert", "fields": {}}],
        "test_plan": ["Confirm generated changes.\nclient_secret=review-secret"],
        "rollback_notes": ["Back out generated changes."],
    }

    with pytest.raises(ModelResponseError) as exc:
        _validate_implementation_contract(response)

    error = str(exc.value)
    assert error == "test_plan items must not contain control characters"
    assert "review-secret" not in error
    assert "\n" not in error


def test_implementation_contract_rejects_unicode_control_review_items() -> None:
    response = {
        "changes": [{"table": "sys_script", "operation": "insert", "fields": {}}],
        "test_plan": ["Confirm generated changes.\u200bclient_secret=review-secret"],
        "rollback_notes": ["Back out generated changes."],
    }

    with pytest.raises(ModelResponseError) as exc:
        _validate_implementation_contract(response)

    error = str(exc.value)
    assert error == "test_plan items must not contain control characters"
    assert "review-secret" not in error
