"""Deterministic validation of model responses for implementation candidates: safety
decision mapping, the implementation contract checks, capability/table expectation
checks, and raw XML rejection."""

from __future__ import annotations

from typing import Any, Literal

from jedi_devproject.capabilities import Capability, SuitabilityOutcome
from jedi_devproject.packet_model import ImplementationPacket
from jedi_devproject.provider_response_normalization import MAX_PROVIDER_CANDIDATE_CHANGES
from jedi_devproject.providers import ModelResponseError, _safe_model_response_diagnostic
from jedi_devproject.unicode_controls import is_control_character

RAW_XML_SCAN_NODE_LIMIT = 1000
RAW_XML_SCAN_DEPTH_LIMIT = 32
RAW_XML_FIELD_NAMES = frozenset({"payload", "xml", "update_xml", "raw_xml"})
RAW_XML_TOKENS = ("<record_update", "<sys_update_xml", "<unload", "payload><![cdata")
MAX_IMPLEMENTATION_REVIEW_ITEMS = 100
MAX_IMPLEMENTATION_REVIEW_ITEM_CHARS = 2000


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
    raise ModelResponseError(
        "unsupported safety decision: "
        f"{_safe_model_response_diagnostic(value)}"
    )


def _validate_implementation_contract(response: dict[str, Any]) -> None:
    changes = response.get("changes")
    if not isinstance(changes, list) or not changes:
        raise ModelResponseError("changes must be a non-empty list")
    if len(changes) > MAX_PROVIDER_CANDIDATE_CHANGES:
        raise ModelResponseError(
            "implementation response includes too many changes "
            f"(max {MAX_PROVIDER_CANDIDATE_CHANGES})"
        )
    _validate_no_raw_xml(response)
    for field_name in ["test_plan", "rollback_notes"]:
        _validate_review_items(field_name=field_name, value=response.get(field_name))


def _validate_review_items(*, field_name: str, value: Any) -> None:
    if not isinstance(value, list) or not value:
        raise ModelResponseError(f"{field_name} must be a non-empty list")
    if len(value) > MAX_IMPLEMENTATION_REVIEW_ITEMS:
        raise ModelResponseError(
            f"{field_name} includes too many items "
            f"(max {MAX_IMPLEMENTATION_REVIEW_ITEMS})"
        )
    if any(type(item) is not str or item.strip() == "" for item in value):
        raise ModelResponseError(f"{field_name} items must be non-empty exact strings")
    if any(len(item) > MAX_IMPLEMENTATION_REVIEW_ITEM_CHARS for item in value):
        raise ModelResponseError(
            f"{field_name} item exceeds length limit "
            f"(max {MAX_IMPLEMENTATION_REVIEW_ITEM_CHARS})"
        )
    if any(_has_control_character(item) for item in value):
        raise ModelResponseError(f"{field_name} items must not contain control characters")


def _has_control_character(value: str) -> bool:
    return any(is_control_character(character) for character in value)


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
    actual_tables: set[str] = set()
    for change in changes:
        if not isinstance(change, dict):
            continue
        table = change.get("table")
        if table is None:
            continue
        if type(table) is not str:
            raise ModelResponseError("model response table names must be exact strings")
        table = table.strip()
        if table:
            actual_tables.add(table)
    unexpected = sorted(actual_tables - expected_tables)
    if unexpected:
        safe_unexpected = ", ".join(
            _safe_model_response_diagnostic(table) for table in unexpected
        )
        raise ModelResponseError(
            "model response tables do not match assessed capability: "
            f"{safe_unexpected}"
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
    scanned_nodes = 0
    stack: list[tuple[Any, int]] = [(value, 0)]
    while stack:
        item, depth = stack.pop()
        scanned_nodes += 1
        if scanned_nodes > RAW_XML_SCAN_NODE_LIMIT:
            raise ModelResponseError("model response size exceeds scan limit")
        if depth > RAW_XML_SCAN_DEPTH_LIMIT:
            raise ModelResponseError("model response nesting exceeds limit")
        if isinstance(item, dict):
            for key, child in item.items():
                if type(key) is not str:
                    raise ModelResponseError("model response object keys must be exact strings")
                if key.strip().lower() in RAW_XML_FIELD_NAMES:
                    raise ModelResponseError("model response must not include raw XML fields")
                stack.append((child, depth + 1))
            continue
        if isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)
            continue
        if type(item) is str and any(
            token in item.lower()
            for token in RAW_XML_TOKENS
        ):
            raise ModelResponseError("model response must not include raw XML content")
