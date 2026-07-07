"""Deterministic validation of model responses for implementation candidates: safety
decision mapping, the implementation contract checks, capability/table expectation
checks, and raw XML rejection."""

from __future__ import annotations

from typing import Any, Literal

from jedi_devproject.capabilities import Capability, SuitabilityOutcome
from jedi_devproject.packet_model import ImplementationPacket
from jedi_devproject.providers import ModelResponseError


def _candidate_decision(value: str) -> Literal["eligible", "manual_review", "rejected"]:
    if value in {"eligible", SuitabilityOutcome.AUTOMATED_BUILD.value}:
        return "eligible"
    if value in {
        "manual_review",
        SuitabilityOutcome.NEEDS_CLARIFICATION.value,
        SuitabilityOutcome.CONTEXT_ANALYSIS.value,
        SuitabilityOutcome.UNSUPPORTED_CAPABILITY.value,
        SuitabilityOutcome.MANUAL_DEVELOPER_BUILD.value,
    }:
        return "manual_review"
    if value == "rejected":
        return "rejected"
    raise ModelResponseError(f"unsupported safety decision: {value}")


def _validate_implementation_contract(response: dict[str, Any]) -> None:
    changes = response.get("changes")
    if not isinstance(changes, list) or not changes:
        raise ModelResponseError("changes must be a non-empty list")
    _validate_no_raw_xml(response)
    for field_name in ["test_plan", "rollback_notes"]:
        value = response.get(field_name)
        if not isinstance(value, list) or not value:
            raise ModelResponseError(f"{field_name} must be a non-empty list")


def _validate_response_tables_match_capability(
    *,
    packet: ImplementationPacket,
    response: dict[str, Any],
) -> None:
    expected_tables = _expected_tables_for_packet(packet)
    if not expected_tables:
        return
    changes = response.get("changes")
    if not isinstance(changes, list):
        return
    actual_tables = {
        str(change.get("table") or "")
        for change in changes
        if isinstance(change, dict) and str(change.get("table") or "").strip()
    }
    unexpected = sorted(actual_tables - expected_tables)
    if unexpected:
        raise ModelResponseError(
            "model response tables do not match assessed capability: "
            f"{', '.join(unexpected)}"
        )


def _expected_tables_for_packet(packet: ImplementationPacket) -> set[str]:
    capabilities = set(str(item) for item in packet.capability_assessment.get("capabilities", []))
    if Capability.CMDB_IRE_GENERATE.value in capabilities:
        return {"cmdb_identifier", "cmdb_identifier_entry", "cmdb_reconciliation_definition"}
    if Capability.UI_POLICY_GENERATE.value in capabilities:
        return {"sys_ui_policy", "sys_ui_policy_action"}
    if Capability.RECORD_PRODUCER_CREATE.value in capabilities:
        return {"sc_cat_item_producer", "item_option_new", "sc_cat_item_category"}
    if Capability.CATALOG_ITEM_CREATE.value in capabilities:
        expected = {
            "sc_cat_item",
            "item_option_new",
            "sc_cat_item_category",
            "m2m_connected_content",
        }
        if Capability.CATALOG_UI_POLICY_GENERATE.value in capabilities:
            expected |= {"catalog_ui_policy", "catalog_ui_policy_action"}
        if Capability.CATALOG_CLIENT_SCRIPT_GENERATE.value in capabilities:
            expected |= {"catalog_script_client"}
        return expected
    if Capability.BUSINESS_RULE_GENERATE.value in capabilities:
        return {"sys_script"}
    if Capability.CLIENT_SCRIPT_GENERATE.value in capabilities:
        return {"sys_script_client"}
    if Capability.SCRIPT_INCLUDE_GENERATE.value in capabilities:
        return {"sys_script_include"}
    if Capability.FORM_SECTION_REMOVE.value in capabilities:
        return {"sys_ui_section"}
    if {
        Capability.DICTIONARY_FIELD_CREATE.value,
        Capability.FORM_LAYOUT_PLACE_FIELD.value,
        Capability.FIELD_LABEL_CREATE.value,
    }.intersection(capabilities):
        return {"sys_dictionary", "sys_ui_form"}
    return set()


def _validate_no_raw_xml(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).strip().lower() in {"payload", "xml", "update_xml", "raw_xml"}:
                raise ModelResponseError("model response must not include raw XML fields")
            _validate_no_raw_xml(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_no_raw_xml(item)
        return
    if isinstance(value, str) and any(
        token in value.lower()
        for token in ["<record_update", "<sys_update_xml", "<unload", "payload><![cdata"]
    ):
        raise ModelResponseError("model response must not include raw XML content")
