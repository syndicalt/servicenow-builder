from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from jedi_devproject.capabilities import Capability, capability_profile
from jedi_devproject.models import Story


class AutomationIntentSource(StrEnum):
    STRUCTURED = "structured"
    LEGACY_TEXT = "legacy_text"
    UNKNOWN = "unknown"


class AutomationIntentType(StrEnum):
    DICTIONARY_FORM = "dictionary_form"
    BUSINESS_RULE = "business_rule"
    CLIENT_SCRIPT = "client_script"
    SCRIPT_INCLUDE = "script_include"
    UI_POLICY = "ui_policy"
    FLOW = "flow"
    ACL = "acl"
    INTEGRATION = "integration"
    DATA_MIGRATION = "data_migration"
    UNKNOWN = "unknown"


class AutomationIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: AutomationIntentSource
    intent_type: AutomationIntentType
    capability: Capability
    target_table: str | None = None
    artifact_name: str | None = None
    condition: str | None = None
    expected_behavior: str | None = None
    fields_read: list[str] = Field(default_factory=list)
    fields_written: list[str] = Field(default_factory=list)
    fields_affected: list[str] = Field(default_factory=list)
    trigger_timing: str | None = None
    trigger_operations: list[str] = Field(default_factory=list)
    client_script_type: str | None = None
    target_field: str | None = None
    script_include_scope: str | None = None
    client_callable: bool | None = None
    tables_read: list[str] = Field(default_factory=list)
    tables_written: list[str] = Field(default_factory=list)
    reverse_if_false: bool | None = None
    run_scripts: bool | None = None
    field_label: str | None = None
    field_name: str | None = None
    field_type: str | None = None
    reference_table: str | None = None
    reference_qualifier: str | None = None
    max_length: int | None = None
    placement_anchor: str | None = None
    placement_position: str | None = None
    forbidden_behavior: list[str] = Field(default_factory=list)
    provided_fields: list[str] = Field(default_factory=list)
    required_instance_context: list[str] = Field(default_factory=list)
    missing_details: list[str] = Field(default_factory=list)

    @property
    def is_structured(self) -> bool:
        return self.source is AutomationIntentSource.STRUCTURED


ARTIFACT_TYPE_ALIASES: dict[str, tuple[AutomationIntentType, Capability]] = {
    "dictionary form": (
        AutomationIntentType.DICTIONARY_FORM,
        Capability.DICTIONARY_FIELD_CREATE,
    ),
    "dictionary field": (
        AutomationIntentType.DICTIONARY_FORM,
        Capability.DICTIONARY_FIELD_CREATE,
    ),
    "dictionary field and form placement": (
        AutomationIntentType.DICTIONARY_FORM,
        Capability.DICTIONARY_FIELD_CREATE,
    ),
    "field and form placement": (
        AutomationIntentType.DICTIONARY_FORM,
        Capability.DICTIONARY_FIELD_CREATE,
    ),
    "form field": (
        AutomationIntentType.DICTIONARY_FORM,
        Capability.DICTIONARY_FIELD_CREATE,
    ),
    "field": (
        AutomationIntentType.DICTIONARY_FORM,
        Capability.DICTIONARY_FIELD_CREATE,
    ),
    "business rule": (
        AutomationIntentType.BUSINESS_RULE,
        Capability.BUSINESS_RULE_GENERATE,
    ),
    "client script": (
        AutomationIntentType.CLIENT_SCRIPT,
        Capability.CLIENT_SCRIPT_GENERATE,
    ),
    "script include": (
        AutomationIntentType.SCRIPT_INCLUDE,
        Capability.SCRIPT_INCLUDE_GENERATE,
    ),
    "ui policy": (
        AutomationIntentType.UI_POLICY,
        Capability.UI_POLICY_GENERATE,
    ),
    "flow": (AutomationIntentType.FLOW, Capability.FLOW_MODIFY),
    "flow designer": (AutomationIntentType.FLOW, Capability.FLOW_MODIFY),
    "acl": (AutomationIntentType.ACL, Capability.ACL_MODIFY),
    "integration": (AutomationIntentType.INTEGRATION, Capability.INTEGRATION_MODIFY),
    "data migration": (AutomationIntentType.DATA_MIGRATION, Capability.DATA_MIGRATION),
}

STRUCTURED_KEY_ALIASES = {
    "target artifact type": "artifact_type",
    "artifact type": "artifact_type",
    "target table": "target_table",
    "table": "target_table",
    "artifact name": "artifact_name",
    "name": "artifact_name",
    "business rule name": "artifact_name",
    "script include name": "artifact_name",
    "field label": "field_label",
    "field name": "field_name",
    "field type": "field_type",
    "reference table": "reference_table",
    "reference qualifier": "reference_qualifier",
    "max length": "max_length",
    "length": "max_length",
    "placement": "placement",
    "placement anchor": "placement_anchor",
    "placement position": "placement_position",
    "condition": "condition",
    "actions": "expected_behavior",
    "expected behavior": "expected_behavior",
    "expected server-side behavior": "expected_behavior",
    "trigger timing": "trigger_timing",
    "trigger operations": "trigger_operations",
    "client script type": "client_script_type",
    "target field": "target_field",
    "scope": "scope",
    "client callable": "client_callable",
    "tables read": "tables_read",
    "tables written": "tables_written",
    "fields read": "fields_read",
    "fields written": "fields_written",
    "fields affected": "fields_affected",
    "field affected": "fields_affected",
    "fields written / affected": "fields_written_affected",
    "reverse if false": "reverse_if_false",
    "reverse behavior": "reverse_behavior",
    "run scripts": "run_scripts",
    "forbidden behavior": "forbidden_behavior",
}


def extract_automation_intent(story: Story) -> AutomationIntent:
    structured_fields = _structured_story_fields(story.description)
    if "artifact_type" not in structured_fields:
        return AutomationIntent(
            source=AutomationIntentSource.UNKNOWN,
            intent_type=AutomationIntentType.UNKNOWN,
            capability=Capability.UNKNOWN,
        )
    return _intent_from_structured_fields(structured_fields)


def _intent_from_structured_fields(fields: dict[str, str]) -> AutomationIntent:
    intent_type, capability = _artifact_type(fields.get("artifact_type", ""))
    fields_read = _field_list(fields.get("fields_read"))
    fields_written = _field_list(fields.get("fields_written"))
    fields_affected = _field_list(fields.get("fields_affected"))
    if "fields_written_affected" in fields:
        combined = _field_list(fields.get("fields_written_affected"))
        fields_written = combined
        fields_affected = combined
    target_table = _clean_text(fields.get("target_table"))
    artifact_name = _clean_text(fields.get("artifact_name"))
    intent = AutomationIntent(
        source=AutomationIntentSource.STRUCTURED,
        intent_type=intent_type,
        capability=capability,
        target_table=target_table,
        artifact_name=artifact_name,
        condition=_clean_text(fields.get("condition")),
        expected_behavior=_clean_text(fields.get("expected_behavior")),
        fields_read=fields_read,
        fields_written=fields_written,
        fields_affected=fields_affected,
        trigger_timing=_clean_text(fields.get("trigger_timing")),
        trigger_operations=_field_list(fields.get("trigger_operations")),
        client_script_type=_normalize_script_type(fields.get("client_script_type")),
        target_field=_clean_field_name(fields.get("target_field")),
        script_include_scope=_clean_text(fields.get("scope")),
        client_callable=_optional_bool(fields.get("client_callable")),
        tables_read=_field_list(fields.get("tables_read")),
        tables_written=_field_list(fields.get("tables_written")),
        reverse_if_false=_reverse_if_false(fields),
        run_scripts=_optional_bool(fields.get("run_scripts")),
        field_label=_clean_text(fields.get("field_label")),
        field_name=_clean_field_name(fields.get("field_name")),
        field_type=_clean_text(fields.get("field_type")),
        reference_table=_clean_field_name(fields.get("reference_table")),
        reference_qualifier=_clean_text(fields.get("reference_qualifier")),
        max_length=_optional_int(fields.get("max_length")),
        placement_anchor=_placement_anchor(
            fields.get("placement_anchor") or fields.get("placement")
        ),
        placement_position=_placement_position(
            fields.get("placement_position") or fields.get("placement")
        ),
        forbidden_behavior=_forbidden_behavior(fields.get("forbidden_behavior")),
        provided_fields=sorted(fields),
        required_instance_context=_required_context(capability),
    )
    return intent.model_copy(update={"missing_details": _missing_details(intent, fields)})


def _structured_story_fields(description: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw_line in _strip_html(description).splitlines():
        line = raw_line.strip().lstrip("-* ").strip()
        if ":" not in line:
            continue
        raw_key, raw_value = line.split(":", 1)
        key = re.sub(r"\s+", " ", raw_key.strip().lower())
        normalized_key = STRUCTURED_KEY_ALIASES.get(key)
        if normalized_key is None:
            continue
        value = raw_value.strip()
        if value:
            fields[normalized_key] = value
    return fields


def _artifact_type(raw_value: str) -> tuple[AutomationIntentType, Capability]:
    cleaned = _clean_text(raw_value)
    if cleaned is None:
        return AutomationIntentType.UNKNOWN, Capability.UNKNOWN
    normalized = cleaned.lower().replace("-", " ")
    return ARTIFACT_TYPE_ALIASES.get(
        normalized,
        (AutomationIntentType.UNKNOWN, Capability.UNKNOWN),
    )


def _required_context(capability: Capability) -> list[str]:
    if capability is Capability.UNKNOWN:
        return []
    if capability is Capability.DICTIONARY_FIELD_CREATE:
        return capability_profile(Capability.DICTIONARY_FIELD_CREATE).required_instance_context
    if capability in {
        Capability.ACL_MODIFY,
        Capability.DATA_MIGRATION,
        Capability.INTEGRATION_MODIFY,
    }:
        return []
    return capability_profile(capability).required_instance_context


def _missing_details(intent: AutomationIntent, fields: dict[str, str]) -> list[str]:
    has_target_table = (
        bool(intent.target_table)
        or intent.intent_type is AutomationIntentType.SCRIPT_INCLUDE
    )
    common_missing = [
        label
        for label, present in [("target table", has_target_table)]
        if not present
    ]
    if intent.intent_type is AutomationIntentType.CLIENT_SCRIPT:
        return [
            *common_missing,
            *[
                label
                for label, present in [
                    ("client script type", bool(intent.client_script_type)),
                    ("target field", bool(intent.target_field)),
                    ("condition", bool(intent.condition)),
                    ("expected behavior", bool(intent.expected_behavior)),
                    ("fields read", "fields_read" in fields),
                    (
                        "fields written",
                        "fields_written" in fields or "fields_written_affected" in fields,
                    ),
                ]
                if not present
            ],
        ]
    if intent.intent_type is AutomationIntentType.UI_POLICY:
        return [
            *common_missing,
            *[
                label
                for label, present in [
                    ("condition", bool(intent.condition)),
                    ("expected behavior", bool(intent.expected_behavior)),
                    ("fields read", "fields_read" in fields),
                    (
                        "fields affected",
                        "fields_affected" in fields or "fields_written_affected" in fields,
                    ),
                    ("reverse if false decision", intent.reverse_if_false is not None),
                ]
                if not present
            ],
        ]
    if intent.intent_type is AutomationIntentType.BUSINESS_RULE:
        return [
            *common_missing,
            *[
                label
                for label, present in [
                    ("trigger timing", bool(intent.trigger_timing)),
                    ("trigger operations", bool(intent.trigger_operations)),
                    ("condition", bool(intent.condition)),
                    ("expected behavior", bool(intent.expected_behavior)),
                    ("fields read", "fields_read" in fields),
                    ("fields written", "fields_written" in fields),
                ]
                if not present
            ],
        ]
    if intent.intent_type is AutomationIntentType.SCRIPT_INCLUDE:
        return [
            label
            for label, present in [
                ("script include name", bool(intent.artifact_name)),
                ("scope", bool(intent.script_include_scope)),
                ("client callable decision", intent.client_callable is not None),
                ("expected behavior", bool(intent.expected_behavior)),
                ("tables read", "tables_read" in fields),
                ("tables written", "tables_written" in fields),
                ("fields read", "fields_read" in fields),
                (
                    "fields written",
                    "fields_written" in fields or "fields_written_affected" in fields,
                ),
            ]
            if not present
        ]
    if intent.intent_type is AutomationIntentType.DICTIONARY_FORM:
        return [
            label
            for label, present in [
                ("target table", bool(intent.target_table)),
                ("field label or field name", bool(intent.field_label or intent.field_name)),
                ("field type", bool(intent.field_type)),
            ]
            if not present
        ]
    return []


def _field_list(raw_value: str | None) -> list[str]:
    cleaned = _clean_text(raw_value)
    if cleaned is None:
        return []
    if cleaned.lower() in {"none", "n/a", "not applicable"}:
        return []
    values = re.split(r",|\band\b", cleaned)
    return [
        _clean_field_name(value)
        for value in values
        if _clean_field_name(value)
    ]


def _forbidden_behavior(raw_value: str | None) -> list[str]:
    cleaned = _clean_text(raw_value)
    if cleaned is None:
        return []
    cleaned = re.sub(r"^do not use\s+", "", cleaned, flags=re.IGNORECASE)
    return [
        item.strip().rstrip(".")
        for item in re.split(r",|\bor\b", cleaned)
        if item.strip().rstrip(".")
    ]


def _reverse_if_false(fields: dict[str, str]) -> bool | None:
    explicit = _optional_bool(fields.get("reverse_if_false"))
    if explicit is not None:
        return explicit
    reverse_behavior = _clean_text(fields.get("reverse_behavior"))
    if reverse_behavior is None or reverse_behavior.lower() in {"not applicable", "n/a"}:
        return None
    if "enabled" in reverse_behavior.lower() or "true" in reverse_behavior.lower():
        return True
    if "disabled" in reverse_behavior.lower() or "false" in reverse_behavior.lower():
        return False
    return None


def _normalize_script_type(raw_value: str | None) -> str | None:
    cleaned = _clean_text(raw_value)
    if cleaned is None:
        return None
    normalized = cleaned.lower().replace(" ", "")
    return {
        "onchange": "onchange",
        "onload": "onload",
        "onsubmit": "onsubmit",
    }.get(normalized, cleaned.lower())


def _optional_bool(raw_value: str | None) -> bool | None:
    cleaned = _clean_text(raw_value)
    if cleaned is None:
        return None
    lowered = cleaned.lower()
    if lowered in {"true", "yes", "1", "enabled"}:
        return True
    if lowered in {"false", "no", "0", "disabled"}:
        return False
    return None


def _optional_int(raw_value: str | None) -> int | None:
    cleaned = _clean_text(raw_value)
    if cleaned is None:
        return None
    match = re.search(r"\d+", cleaned)
    return int(match.group(0)) if match else None


def _placement_anchor(raw_value: str | None) -> str | None:
    cleaned = _clean_text(raw_value)
    if cleaned is None:
        return None
    lowered = cleaned.lower()
    if lowered.startswith(("after ", "before ", "below ", "above ")):
        cleaned = re.sub(r"^(?:after|before|below|above)\s+", "", cleaned, flags=re.IGNORECASE)
    match = re.search(r"(?:below|above)\s+([a-zA-Z0-9_ ]+)", cleaned)
    if match:
        return _clean_field_name(match.group(1).replace(" field", ""))
    return _clean_field_name(cleaned.replace(" field", ""))


def _placement_position(raw_value: str | None) -> str | None:
    cleaned = _clean_text(raw_value)
    if cleaned is None:
        return None
    if "after" in cleaned.lower():
        return "below"
    if "before" in cleaned.lower():
        return "above"
    if "above" in cleaned.lower():
        return "above"
    if "below" in cleaned.lower():
        return "below"
    return "end"


def _clean_text(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    cleaned = re.sub(r"\s+", " ", raw_value).strip(" .:-")
    return cleaned or None


def _clean_field_name(raw_value: str | None) -> str:
    cleaned = _clean_text(raw_value)
    if cleaned is None:
        return ""
    return cleaned.lower().replace(" ", "_")


def _strip_html(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value)
