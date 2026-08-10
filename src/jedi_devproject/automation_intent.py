from __future__ import annotations

import re
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from jedi_devproject.capabilities import Capability, capability_profile
from jedi_devproject.models import Story
from jedi_devproject.story_features import (
    explicit_reference_qualifier,
    looks_like_reference_qualifier_attempt,
)


class AutomationIntentSource(StrEnum):
    STRUCTURED = "structured"
    LEGACY_TEXT = "legacy_text"
    UNKNOWN = "unknown"


class AutomationIntentType(StrEnum):
    CATALOG_ITEM = "catalog_item"
    RECORD_PRODUCER = "record_producer"
    CATALOG_UI_POLICY = "catalog_ui_policy"
    CATALOG_CLIENT_SCRIPT = "catalog_client_script"
    DICTIONARY_FORM = "dictionary_form"
    FORM_SECTION = "form_section"
    BUSINESS_RULE = "business_rule"
    CLIENT_SCRIPT = "client_script"
    SCRIPT_INCLUDE = "script_include"
    UI_POLICY = "ui_policy"
    FLOW = "flow"
    ACL = "acl"
    INTEGRATION = "integration"
    DATA_MIGRATION = "data_migration"
    UNKNOWN = "unknown"


class CatalogVariableGroupIntent(BaseModel):
    """A titled container section grouping a catalog item's own new variables."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    title: str
    variables: list[str] = Field(default_factory=list)


class RecordProducerIntent(BaseModel):
    """A complete, typed record producer request: producer, mapped variables, placement.

    Only populated when every required detail is present; incomplete stories
    keep this ``None`` and surface the gaps as missing details instead. Each
    variable dict carries a ``field`` key naming the target-table field the
    variable maps to (``item_option_new.map_to_field``); script-based mapping
    is never represented here.
    """

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    name: str
    short_description: str
    target_table: str
    catalog: str
    category: str
    variables: list[dict[str, Any]] = Field(default_factory=list)


class CatalogUiPolicyActionRuleIntent(BaseModel):
    """One declarative effect a catalog UI policy applies to an item variable."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    variable: str
    visible: str = "ignore"
    mandatory: str = "ignore"
    disabled: str = "ignore"
    cleared: bool = False


class CatalogUiPolicyRuleIntent(BaseModel):
    """A declarative variable behavior rule on the catalog item's own variables."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    title: str
    condition: str
    reverse_if_false: bool = True
    actions: list[CatalogUiPolicyActionRuleIntent] = Field(default_factory=list)


class CatalogClientScriptActionIntent(BaseModel):
    """One declarative g_form effect: set a variable's value or clear it."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    kind: str
    variable: str
    value: str = ""


class CatalogClientScriptSpecIntent(BaseModel):
    """A declarative catalog client script on the catalog item's own variables."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    name: str
    script_type: str
    variable: str = ""
    actions: list[CatalogClientScriptActionIntent] = Field(default_factory=list)


class AutomationIntent(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

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
    form_view: str | None = None
    form_sections: list[str] = Field(default_factory=list)
    catalog_item_short_description: str | None = None
    catalog_name: str | None = None
    category_name: str | None = None
    taxonomy_name: str | None = None
    employee_center_topic: str | None = None
    catalog_variables: list[dict[str, Any]] = Field(default_factory=list)
    catalog_variable_sets: list[str] = Field(default_factory=list)
    catalog_variable_groups: list[CatalogVariableGroupIntent] = Field(default_factory=list)
    catalog_variable_set_creation: bool = False
    catalog_ui_policies: list[CatalogUiPolicyRuleIntent] = Field(default_factory=list)
    catalog_client_scripts: list[CatalogClientScriptSpecIntent] = Field(default_factory=list)
    record_producer: RecordProducerIntent | None = None
    record_producer_script: str | None = None
    fulfillment_flow: str | None = None
    fulfillment_flow_name: str | None = None
    fulfillment_flow_attachment_requested: bool = False
    forbidden_behavior: list[str] = Field(default_factory=list)
    provided_fields: list[str] = Field(default_factory=list)
    required_instance_context: list[str] = Field(default_factory=list)
    missing_details: list[str] = Field(default_factory=list)

    @property
    def is_structured(self) -> bool:
        return self.source is AutomationIntentSource.STRUCTURED


def intent_required_instance_context(payload: object) -> list[str] | None:
    """Read ``required_instance_context`` from a serialized intent payload.

    Assessments carry the intent across module and artifact boundaries as the
    dict produced by ``AutomationIntent.model_dump()``. Field-scoped on
    purpose: the surface override must survive unrelated schema drift in
    persisted assessment payloads, so this validates only the field it
    consumes instead of the whole model. Returns ``None`` when the payload is
    not a mapping or the field is not a list, so consumers degrade to the same
    missing-intent path as before.
    """
    if not isinstance(payload, dict):
        return None
    value = payload.get("required_instance_context")
    if not isinstance(value, list):
        return None
    return [str(surface) for surface in value]


ARTIFACT_TYPE_ALIASES: dict[str, tuple[AutomationIntentType, Capability]] = {
    "catalog item": (
        AutomationIntentType.CATALOG_ITEM,
        Capability.CATALOG_ITEM_CREATE,
    ),
    "standard catalog item": (
        AutomationIntentType.CATALOG_ITEM,
        Capability.CATALOG_ITEM_CREATE,
    ),
    "record producer": (
        AutomationIntentType.RECORD_PRODUCER,
        Capability.RECORD_PRODUCER_CREATE,
    ),
    "catalog record producer": (
        AutomationIntentType.RECORD_PRODUCER,
        Capability.RECORD_PRODUCER_CREATE,
    ),
    "catalog ui policy": (
        AutomationIntentType.CATALOG_UI_POLICY,
        Capability.CATALOG_UI_POLICY_GENERATE,
    ),
    "catalog client script": (
        AutomationIntentType.CATALOG_CLIENT_SCRIPT,
        Capability.CATALOG_CLIENT_SCRIPT_GENERATE,
    ),
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
    "form section removal": (
        AutomationIntentType.FORM_SECTION,
        Capability.FORM_SECTION_REMOVE,
    ),
    "form section": (
        AutomationIntentType.FORM_SECTION,
        Capability.FORM_SECTION_REMOVE,
    ),
    "form tab removal": (
        AutomationIntentType.FORM_SECTION,
        Capability.FORM_SECTION_REMOVE,
    ),
    "form tabs": (
        AutomationIntentType.FORM_SECTION,
        Capability.FORM_SECTION_REMOVE,
    ),
    "form layout section removal": (
        AutomationIntentType.FORM_SECTION,
        Capability.FORM_SECTION_REMOVE,
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
    "catalog item name": "artifact_name",
    "record producer name": "artifact_name",
    "producer script": "record_producer_script",
    "record producer script": "record_producer_script",
    "short description": "catalog_item_short_description",
    "catalog item short description": "catalog_item_short_description",
    "catalog": "catalog_name",
    "category": "category_name",
    "taxonomy": "taxonomy_name",
    "employee center topic": "employee_center_topic",
    "topic": "employee_center_topic",
    "variables": "catalog_variables",
    "catalog variables": "catalog_variables",
    "variable sets": "catalog_variable_sets",
    "variable set": "catalog_variable_sets",
    "attach variable sets": "catalog_variable_sets",
    "variable groups": "catalog_variable_groups",
    "variable group": "catalog_variable_groups",
    "group variables": "catalog_variable_groups",
    "variable rules": "catalog_ui_policies",
    "variable rule": "catalog_ui_policies",
    "variable behavior rules": "catalog_ui_policies",
    "catalog ui policies": "catalog_ui_policies",
    "catalog ui policy rules": "catalog_ui_policies",
    "variable scripts": "catalog_client_scripts",
    "variable script": "catalog_client_scripts",
    "catalog client scripts": "catalog_client_scripts",
    "fulfillment flow": "fulfillment_flow",
    "fulfillment workflow": "fulfillment_flow",
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
    "view": "form_view",
    "form view": "form_view",
    "sections": "form_sections",
    "section": "form_sections",
    "tabs": "form_sections",
    "tab": "form_sections",
    "condition": "condition",
    "actions": "expected_behavior",
    "expected behavior": "expected_behavior",
    "expected server-side behavior": "expected_behavior",
    "timing": "trigger_timing",
    "when": "trigger_timing",
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
    intent_type, capability = _structured_artifact_type(fields)
    fields_read = _field_list(fields.get("fields_read"))
    fields_written = _field_list(fields.get("fields_written"))
    fields_affected = _field_list(fields.get("fields_affected"))
    if "fields_written_affected" in fields:
        combined = _field_list(fields.get("fields_written_affected"))
        fields_written = combined
        fields_affected = combined
    target_table = _clean_text(fields.get("target_table"))
    artifact_name = _clean_text(fields.get("artifact_name"))
    catalog_variable_sets, catalog_variable_set_creation = _catalog_variable_sets(
        fields.get("catalog_variable_sets")
    )
    fulfillment_flow = _clean_text(fields.get("fulfillment_flow"))
    fulfillment_flow_name, fulfillment_flow_attachment_requested = _fulfillment_flow_attachment(
        fulfillment_flow
    )
    intent = AutomationIntent(
        source=AutomationIntentSource.STRUCTURED,
        intent_type=intent_type,
        capability=capability,
        target_table=(
            "sc_cat_item" if intent_type is AutomationIntentType.CATALOG_ITEM else target_table
        ),
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
        form_view=_clean_preserved_text(fields.get("form_view")),
        form_sections=_preserved_list(fields.get("form_sections")),
        catalog_item_short_description=_clean_preserved_text(
            fields.get("catalog_item_short_description")
        ),
        catalog_name=_clean_text(fields.get("catalog_name")),
        category_name=_clean_text(fields.get("category_name")),
        taxonomy_name=_clean_text(fields.get("taxonomy_name")),
        employee_center_topic=_clean_text(fields.get("employee_center_topic")),
        catalog_variables=_catalog_variables(fields.get("catalog_variables")),
        catalog_variable_sets=catalog_variable_sets,
        catalog_variable_groups=_catalog_variable_groups(fields.get("catalog_variable_groups")),
        catalog_variable_set_creation=catalog_variable_set_creation,
        catalog_ui_policies=_catalog_ui_policy_rules(fields.get("catalog_ui_policies")),
        catalog_client_scripts=_catalog_client_script_specs(
            fields.get("catalog_client_scripts")
        ),
        record_producer_script=_clean_preserved_text(fields.get("record_producer_script")),
        fulfillment_flow=fulfillment_flow,
        fulfillment_flow_name=fulfillment_flow_name,
        fulfillment_flow_attachment_requested=fulfillment_flow_attachment_requested,
        forbidden_behavior=_forbidden_behavior(fields.get("forbidden_behavior")),
        provided_fields=sorted(fields),
        required_instance_context=_required_context(capability),
    )
    intent = intent.model_copy(update={"missing_details": _missing_details(intent, fields)})
    if intent.intent_type is AutomationIntentType.RECORD_PRODUCER:
        intent = intent.model_copy(update={"record_producer": _record_producer_intent(intent)})
    return intent


def _record_producer_intent(intent: AutomationIntent) -> RecordProducerIntent | None:
    """Build the typed record producer intent only when every detail is present."""
    if intent.missing_details:
        return None
    return RecordProducerIntent(
        name=intent.artifact_name or "",
        short_description=intent.catalog_item_short_description or "",
        target_table=intent.target_table or "",
        catalog=intent.catalog_name or "",
        category=intent.category_name or "",
        variables=[dict(variable) for variable in intent.catalog_variables],
    )


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


def _structured_artifact_type(fields: dict[str, str]) -> tuple[AutomationIntentType, Capability]:
    raw_artifact_type = fields.get("artifact_type", "")
    cleaned = _clean_text(raw_artifact_type)
    normalized = "" if cleaned is None else cleaned.lower().replace("-", " ")
    if normalized in {"form section", "form tabs"}:
        if _structured_form_section_removal_action(fields):
            return AutomationIntentType.FORM_SECTION, Capability.FORM_SECTION_REMOVE
        return AutomationIntentType.FORM_SECTION, Capability.UNKNOWN
    return _artifact_type(raw_artifact_type)


def _structured_form_section_removal_action(fields: dict[str, str]) -> bool:
    action = _clean_text(fields.get("expected_behavior"))
    if action is None:
        return False
    lowered = action.lower()
    if re.search(r"\b(?:do not|don't|should not|must not)\s+(?:remove|hide)\b", lowered):
        return False
    return bool(
        re.search(
            r"\b(?:remove|hide)\b|\bhidden\b|\bnot\s+display\b|"
            r"\bwill\s+not\s+display\b|\bdo\s+not\s+display\b",
            lowered,
        )
    )


def _required_context(capability: Capability) -> list[str]:
    if capability is Capability.UNKNOWN:
        return []
    if capability is Capability.DICTIONARY_FIELD_CREATE:
        return capability_profile(Capability.DICTIONARY_FIELD_CREATE).required_instance_context
    if capability is Capability.FORM_SECTION_REMOVE:
        return capability_profile(Capability.FORM_SECTION_REMOVE).required_instance_context
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
    if intent.intent_type is AutomationIntentType.CATALOG_ITEM:
        declared_variable_names = {
            str(variable.get("name") or "") for variable in intent.catalog_variables
        }
        return [
            label
            for label, present in [
                ("catalog item name", bool(intent.artifact_name)),
                (
                    "catalog item short description",
                    bool(intent.catalog_item_short_description),
                ),
                ("catalog", bool(intent.catalog_name)),
                ("category", bool(intent.category_name)),
                ("taxonomy", bool(intent.taxonomy_name)),
                ("Employee Center topic", bool(intent.employee_center_topic)),
                ("variables", bool(intent.catalog_variables)),
                (
                    "variable sets",
                    "catalog_variable_sets" not in fields
                    or bool(intent.catalog_variable_sets)
                    or intent.catalog_variable_set_creation,
                ),
                (
                    "variable groups",
                    "catalog_variable_groups" not in fields
                    or bool(intent.catalog_variable_groups),
                ),
                (
                    "variable group members",
                    all(
                        member in declared_variable_names
                        for group in intent.catalog_variable_groups
                        for member in group.variables
                    ),
                ),
                (
                    "variable rules",
                    "catalog_ui_policies" not in fields or bool(intent.catalog_ui_policies),
                ),
                (
                    "variable rule members",
                    all(
                        member in declared_variable_names
                        for rule in intent.catalog_ui_policies
                        for member in _ui_policy_rule_variables(rule)
                    ),
                ),
                (
                    "variable scripts",
                    "catalog_client_scripts" not in fields
                    or bool(intent.catalog_client_scripts),
                ),
                (
                    "variable script members",
                    all(
                        member in declared_variable_names
                        for spec in intent.catalog_client_scripts
                        for member in _client_script_spec_variables(spec)
                    ),
                ),
                (
                    "fulfillment flow name",
                    not intent.fulfillment_flow_attachment_requested
                    or bool(intent.fulfillment_flow_name),
                ),
            ]
            if not present
        ]
    if intent.intent_type is AutomationIntentType.RECORD_PRODUCER:
        return [
            label
            for label, present in [
                ("record producer name", bool(intent.artifact_name)),
                ("short description", bool(intent.catalog_item_short_description)),
                ("target table", bool(intent.target_table)),
                ("catalog", bool(intent.catalog_name)),
                ("category", bool(intent.category_name)),
                ("variables", bool(intent.catalog_variables)),
                (
                    "variable field mappings",
                    not intent.catalog_variables
                    or all(
                        str(variable.get("field") or "").strip()
                        for variable in intent.catalog_variables
                    ),
                ),
            ]
            if not present
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
                    (
                        "fields written",
                        "fields_written" in fields or "fields_written_affected" in fields,
                    ),
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
    if intent.intent_type is AutomationIntentType.FORM_SECTION:
        return [
            label
            for label, present in [
                ("target table", bool(intent.target_table)),
                ("sections", bool(intent.form_sections)),
            ]
            if not present
        ]
    return []


def _catalog_variables(raw_value: str | None) -> list[dict[str, Any]]:
    cleaned = _clean_text(raw_value)
    if cleaned is None:
        return []
    variables: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for raw_entry in cleaned.split(";"):
        entry = raw_entry.strip()
        if not entry:
            continue
        variable = _catalog_variable(entry)
        name = str(variable.get("name") or "")
        if not name or name in seen_names:
            continue
        seen_names.add(name)
        variables.append(variable)
    return variables


def _catalog_variable_sets(raw_value: str | None) -> tuple[list[str], bool]:
    """Parse attached variable-set names; flag explicit set-creation requests.

    Creating new variable sets is unsupported, so any entry that asks to
    create/build/define a set raises the creation flag (routed to manual
    review) instead of contributing a name.
    """
    cleaned = _clean_preserved_text(raw_value)
    if cleaned is None:
        return [], False
    names: list[str] = []
    creation_requested = False
    for raw_entry in re.split(r"[;,]", cleaned):
        entry = raw_entry.strip(" .")
        if not entry:
            continue
        if re.search(r"\b(?:create|build|define)\b", entry, re.IGNORECASE):
            creation_requested = True
            continue
        if entry.casefold() not in {name.casefold() for name in names}:
            names.append(entry)
    return names, creation_requested


_FULFILLMENT_FLOW_ATTACH_WITH_NAME_PATTERN = re.compile(
    r"attach\s+(?:the\s+|an\s+)?existing\s+flow\s+"
    r"(?:\"(?P<double_quoted>[^\"]+)\"|'(?P<single_quoted>[^']+)'|(?P<name>\S.*?))"
    r"\s+as\s+the\s+fulfillment\s+flow",
    re.IGNORECASE,
)
_FULFILLMENT_FLOW_ATTACH_WITHOUT_NAME_PATTERN = re.compile(
    r"attach\s+(?:the\s+|an\s+)?existing\s+flow\s+as\s+the\s+fulfillment\s+flow",
    re.IGNORECASE,
)


def _fulfillment_flow_attachment(raw_value: str | None) -> tuple[str | None, bool]:
    """Extract an explicit attach-existing-flow request from the structured field.

    Only the explicit "attach the existing flow <name> as the fulfillment
    flow" phrasing yields a flow name. The same phrasing without a name still
    counts as an attachment request and surfaces as a missing detail instead.
    Anything else — create/modify requests or ambiguous "with a fulfillment
    flow" prose — yields no attachment, so the raw value keeps routing to
    manual review as forbidden behavior exactly as before.
    """
    if raw_value is None:
        return None, False
    if _FULFILLMENT_FLOW_ATTACH_WITHOUT_NAME_PATTERN.fullmatch(raw_value):
        return None, True
    match = _FULFILLMENT_FLOW_ATTACH_WITH_NAME_PATTERN.fullmatch(raw_value)
    if match is None:
        return None, False
    name = next(
        (
            value
            for value in (
                match.group("double_quoted"),
                match.group("single_quoted"),
                match.group("name"),
            )
            if value
        ),
        "",
    ).strip()
    return (name or None), True


def _catalog_variable_groups(raw_value: str | None) -> list[CatalogVariableGroupIntent]:
    """Parse ``Title|member_one,member_two; ...`` entries into typed groups.

    Parsing is all-or-nothing: a malformed or duplicate entry discards every
    group so the gap surfaces as a missing detail instead of silently dropping
    part of the stated grouping.
    """
    cleaned = _clean_preserved_text(raw_value)
    if cleaned is None:
        return []
    groups: list[CatalogVariableGroupIntent] = []
    seen_titles: set[str] = set()
    for raw_entry in cleaned.split(";"):
        entry = raw_entry.strip()
        if not entry:
            continue
        title, separator, raw_members = entry.partition("|")
        title = title.strip(" .")
        members = [
            member
            for member in (_clean_field_name(part) for part in raw_members.split(","))
            if member
        ]
        if not title or not separator or not members or title.casefold() in seen_titles:
            return []
        seen_titles.add(title.casefold())
        groups.append(CatalogVariableGroupIntent(title=title, variables=members))
    return groups


_CONDITION_VARIABLE_PATTERN = re.compile(r"(?:^|\^)(?:OR)?([a-z][a-z0-9_]*)")

_UI_POLICY_EFFECT_KEYS: dict[str, tuple[str, str]] = {
    "show": ("visible", "true"),
    "hide": ("visible", "false"),
    "require": ("mandatory", "true"),
    "optional": ("mandatory", "false"),
    "readonly": ("disabled", "true"),
    "read_only": ("disabled", "true"),
    "editable": ("disabled", "false"),
    "clear": ("cleared", "true"),
}


def _ui_policy_rule_variables(rule: CatalogUiPolicyRuleIntent) -> list[str]:
    return [
        *_CONDITION_VARIABLE_PATTERN.findall(rule.condition),
        *[action.variable for action in rule.actions],
    ]


def _client_script_spec_variables(spec: CatalogClientScriptSpecIntent) -> list[str]:
    return [
        *([spec.variable] if spec.variable else []),
        *[action.variable for action in spec.actions],
    ]


def _catalog_ui_policy_rules(raw_value: str | None) -> list[CatalogUiPolicyRuleIntent]:
    """Parse ``Title|condition|show=a,b|require=a|reverse=true; ...`` rules.

    Effect parts map declaratively: ``show``/``hide`` to visible,
    ``require``/``optional`` to mandatory, ``readonly``/``editable`` to
    read-only, and ``clear`` to cleared. Parsing is all-or-nothing: a
    malformed, conflicting, or duplicate entry discards every rule so the gap
    surfaces as a missing detail instead of silently dropping stated behavior.
    """
    cleaned = _clean_preserved_text(raw_value)
    if cleaned is None:
        return []
    rules: list[CatalogUiPolicyRuleIntent] = []
    seen_titles: set[str] = set()
    for raw_entry in cleaned.split(";"):
        entry = raw_entry.strip()
        if not entry:
            continue
        parts = [part.strip() for part in entry.split("|")]
        if len(parts) < 3:
            return []
        title = parts[0].strip(" .")
        condition = parts[1]
        if not title or not condition or title.casefold() in seen_titles:
            return []
        reverse_if_false = True
        effects: dict[str, dict[str, str]] = {}
        for part in parts[2:]:
            key, separator, raw_part_value = part.partition("=")
            normalized_key = key.strip().lower().replace(" ", "_")
            value = raw_part_value.strip()
            if not separator or not value:
                return []
            if normalized_key == "reverse":
                parsed_reverse = _optional_bool(value)
                if parsed_reverse is None:
                    return []
                reverse_if_false = parsed_reverse
                continue
            effect = _UI_POLICY_EFFECT_KEYS.get(normalized_key)
            if effect is None:
                return []
            attribute, effect_value = effect
            for raw_member in value.split(","):
                member = _clean_field_name(raw_member)
                if not member:
                    return []
                action = effects.setdefault(member, {})
                if action.get(attribute, effect_value) != effect_value:
                    return []
                action[attribute] = effect_value
        if not effects:
            return []
        seen_titles.add(title.casefold())
        rules.append(
            CatalogUiPolicyRuleIntent(
                title=title,
                condition=condition,
                reverse_if_false=reverse_if_false,
                actions=[
                    CatalogUiPolicyActionRuleIntent(
                        variable=member,
                        visible=action.get("visible", "ignore"),
                        mandatory=action.get("mandatory", "ignore"),
                        disabled=action.get("disabled", "ignore"),
                        cleared=action.get("cleared") == "true",
                    )
                    for member, action in effects.items()
                ],
            )
        )
    return rules


def _catalog_client_script_specs(raw_value: str | None) -> list[CatalogClientScriptSpecIntent]:
    """Parse ``name|type|[watched variable]|set=var=value|clear=var; ...`` scripts.

    Script bodies are never carried as free text: only declarative ``set`` and
    ``clear`` actions are accepted, and the deterministic builder renders the
    canonical g_form-only script from them. Parsing is all-or-nothing so a
    malformed entry surfaces as a missing detail.
    """
    cleaned = _clean_preserved_text(raw_value)
    if cleaned is None:
        return []
    specs: list[CatalogClientScriptSpecIntent] = []
    seen_names: set[str] = set()
    for raw_entry in cleaned.split(";"):
        entry = raw_entry.strip()
        if not entry:
            continue
        parts = [part.strip() for part in entry.split("|")]
        if len(parts) < 3:
            return []
        name = _clean_field_name(parts[0])
        script_type = _catalog_client_script_type(parts[1])
        if not name or script_type is None or name in seen_names:
            return []
        action_parts = parts[2:]
        watched_variable = ""
        if script_type == "onChange":
            watched_variable = _clean_field_name(action_parts[0])
            if not watched_variable or "=" in action_parts[0]:
                return []
            action_parts = action_parts[1:]
        actions: list[CatalogClientScriptActionIntent] = []
        for part in action_parts:
            key, separator, raw_part_value = part.partition("=")
            normalized_key = key.strip().lower()
            value = raw_part_value.strip()
            if not separator or not value:
                return []
            if normalized_key == "set":
                variable, value_separator, set_value = value.partition("=")
                member = _clean_field_name(variable)
                if not member or not value_separator or not set_value.strip():
                    return []
                actions.append(
                    CatalogClientScriptActionIntent(
                        kind="set_value",
                        variable=member,
                        value=set_value.strip(),
                    )
                )
            elif normalized_key == "clear":
                member = _clean_field_name(value)
                if not member:
                    return []
                actions.append(
                    CatalogClientScriptActionIntent(kind="clear_value", variable=member)
                )
            else:
                return []
        if not actions:
            return []
        seen_names.add(name)
        specs.append(
            CatalogClientScriptSpecIntent(
                name=name,
                script_type=script_type,
                variable=watched_variable,
                actions=actions,
            )
        )
    return specs


def _catalog_client_script_type(raw_value: str) -> str | None:
    normalized = raw_value.strip().lower().replace(" ", "")
    return {
        "onload": "onLoad",
        "onchange": "onChange",
        "onsubmit": "onSubmit",
    }.get(normalized)


def _catalog_variable(entry: str) -> dict[str, Any]:
    parts = [part.strip() for part in entry.split("|") if part.strip()]
    if len(parts) < 3:
        return {}
    variable_type = _normalize_catalog_variable_type(parts[2])
    variable: dict[str, Any] = {
        "name": _clean_field_name(parts[0]) or parts[0],
        "label": parts[1],
        "type": variable_type,
        "mandatory": False,
    }
    for part in parts[3:]:
        key, separator, raw_part_value = part.partition("=")
        normalized_key = key.strip().lower().replace(" ", "_")
        cleaned_value = raw_part_value.strip() if separator else part.strip()
        if separator and normalized_key in {"mandatory", "required"}:
            variable["mandatory"] = _bool_text_value(cleaned_value)
        elif separator and normalized_key == "order":
            order = _optional_int(cleaned_value)
            if order is not None:
                variable["order"] = order
        elif separator and normalized_key in {"help", "help_text"}:
            variable["help_text"] = cleaned_value
        elif separator and normalized_key in {"default", "default_value"}:
            variable["default_value"] = cleaned_value
        elif separator and normalized_key in {"reference", "reference_table", "ref_table"}:
            variable["reference_table"] = _clean_field_name(cleaned_value) or cleaned_value
        elif separator and normalized_key in {
            "reference_qualifier",
            "reference_qual",
            "qualifier",
        }:
            variable["reference_qualifier"] = cleaned_value
        elif separator and normalized_key in {"map", "map_to", "maps_to", "map_to_field", "field"}:
            variable["field"] = _clean_field_name(cleaned_value)
        elif variable_type == "reference" and "reference_table" not in variable:
            variable["reference_table"] = _clean_field_name(cleaned_value) or cleaned_value
        elif variable_type == "reference" and "reference_qualifier" not in variable:
            qualifier = _explicit_catalog_reference_qualifier(part.strip())
            if qualifier is not None:
                variable["reference_qualifier"] = qualifier
    return variable


def _explicit_catalog_reference_qualifier(part: str) -> str | None:
    """Carry a qualifier only when the story states one explicitly.

    An explicit declarative filter maps to its encoded query. Text that looks
    like an attempted qualifier or script is carried through unchanged so the
    deterministic gate rejects it into manual review. Ambiguous prose is
    omitted entirely — a qualifier is never invented.
    """
    explicit = explicit_reference_qualifier(part)
    if explicit is not None:
        return explicit
    if looks_like_reference_qualifier_attempt(part):
        return part
    return None


def _normalize_catalog_variable_type(value: str) -> str:
    cleaned = value.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "single_line": "single_line_text",
        "string": "single_line_text",
        "text": "single_line_text",
        "multi_line": "multi_line_text",
        "multiline": "multi_line_text",
        "yes/no": "yes_no",
        "boolean": "yes_no",
    }
    return aliases.get(cleaned, cleaned)


def _bool_text_value(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "required", "mandatory"}


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


def _preserved_list(raw_value: str | None) -> list[str]:
    cleaned = _clean_text(raw_value)
    if cleaned is None:
        return []
    if cleaned.lower() in {"none", "n/a", "not applicable"}:
        return []
    return [
        item.strip()
        for item in re.split(r",|\band\b", cleaned)
        if item.strip()
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


def _clean_preserved_text(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    cleaned = re.sub(r"\s+", " ", raw_value).strip()
    return cleaned or None


def _clean_field_name(raw_value: str | None) -> str:
    cleaned = _clean_text(raw_value)
    if cleaned is None:
        return ""
    return cleaned.lower().replace(" ", "_")


def _strip_html(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value)
