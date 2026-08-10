from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from jedi_devproject.models import CandidateChange
from jedi_devproject.validation_helpers import bool_value, single_insert_change, slug
from jedi_devproject.xml_builder import (
    SYS_SCOPE_GLOBAL,
    bool_element,
    container_element,
    record_update,
    text_element,
)

BUSINESS_RULE_FIELD_NON_JSON_DIAGNOSTIC = (
    "Business Rule generation field contains non-JSON value"
)


class BusinessRuleIntent(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    target_table: str
    rule_name: str
    when: str
    action_insert: bool = False
    action_update: bool = False
    filter_condition: str
    script: str
    fields_read: list[str]
    fields_written: list[str]

    @field_validator("target_table", "rule_name", "filter_condition", "script")
    @classmethod
    def require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned == "":
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("when")
    @classmethod
    def validate_when(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"before", "after"}:
            raise ValueError("Business Rule timing must be before or after")
        return cleaned

    @model_validator(mode="after")
    def require_supported_operation(self) -> BusinessRuleIntent:
        if not self.action_insert and not self.action_update:
            raise ValueError("Business Rule must run on insert or update")
        _validate_script_safety(self.script)
        _validate_field_writes(script=self.script, fields_written=self.fields_written)
        return self


def business_rule_customer_updates(
    *,
    changes: list[CandidateChange],
    remote_update_set_sys_id: str,
) -> list[dict[str, Any]]:
    change = single_insert_change(changes, table="sys_script", label="Business Rule")
    intent = _business_rule_intent(change)
    update_name = (
        f"sys_script_{intent.target_table}_"
        f"{slug(intent.rule_name, default='generated_business_rule')}"
    )
    return [
        {
            "name": update_name,
            "remote_update_set": remote_update_set_sys_id,
            "action": "INSERT_OR_UPDATE",
            "type": "Business Rule",
            "target_name": intent.rule_name,
            "payload": _business_rule_payload(intent=intent, update_name=update_name),
            "application": "global",
        }
    ]


def _business_rule_intent(change: CandidateChange) -> BusinessRuleIntent:
    fields = dict(change.fields)
    script = _business_rule_first_text(
        fields.get("script"),
        fields.get("action_script"),
        fields.get("script_body"),
    )
    operation_text = (
        f"{_business_rule_first_text(fields.get('action'))} "
        f"{_business_rule_first_text(fields.get('rationale'))} "
        f"{change.rationale or ''}"
    )
    return BusinessRuleIntent(
        target_table=_business_rule_first_text(
            fields.get("collection"),
            fields.get("table"),
        ),
        rule_name=_business_rule_first_text(fields.get("name")),
        when=_business_rule_first_text(fields.get("when")),
        action_insert=(
            bool_value(_business_rule_first_text(fields.get("action_insert")))
            or bool_value(_business_rule_first_text(fields.get("insert")))
            or bool_value(_business_rule_first_text(fields.get("operation_insert")))
            or _operation_mentions(operation_text, "insert")
        ),
        action_update=(
            bool_value(_business_rule_first_text(fields.get("action_update")))
            or bool_value(_business_rule_first_text(fields.get("update")))
            or bool_value(_business_rule_first_text(fields.get("operation_update")))
            or _operation_mentions(operation_text, "update")
        ),
        filter_condition=_business_rule_first_text(
            fields.get("filter_condition"),
            fields.get("condition"),
            fields.get("conditions"),
            fields.get("filter"),
        ),
        script=script,
        fields_read=_business_rule_string_list(fields.get("fields_read")),
        fields_written=(
            _business_rule_string_list(fields.get("fields_written"))
            or _written_fields_from_script(script)
        ),
    )


def _business_rule_payload(*, intent: BusinessRuleIntent, update_name: str) -> str:
    return record_update(
        container_element(
            "sys_script",
            "<active>true</active>",
            bool_element("action_insert", intent.action_insert),
            bool_element("action_update", intent.action_update),
            "<action_delete>false</action_delete>",
            "<action_query>false</action_query>",
            "<advanced>true</advanced>",
            text_element("collection", intent.target_table),
            text_element("filter_condition", intent.filter_condition),
            text_element("name", intent.rule_name),
            "<order>100</order>",
            text_element("script", intent.script),
            "<sys_class_name>sys_script</sys_class_name>",
            SYS_SCOPE_GLOBAL,
            text_element("sys_update_name", update_name),
            text_element("when", intent.when),
            action="INSERT_OR_UPDATE",
        )
    )


FORBIDDEN_SCRIPT_TOKENS = [
    "GlideRecord",
    "deleteRecord",
    "deleteMultiple",
    "updateMultiple",
    "setWorkflow(false)",
    "gs.eventQueue",
    "sn_ws",
    "RESTMessageV2",
    "SOAPMessageV2",
    "GlideCredential",
    "password",
    "token",
    "api_key",
    "http://",
    "https://",
]


def _validate_script_safety(script: str) -> None:
    if re.search(r"\b(?:var|let|const)\s+fields_written\b", script, flags=re.IGNORECASE):
        raise ValueError("Business Rule script must not declare fields_written")
    for token in FORBIDDEN_SCRIPT_TOKENS:
        if token.lower() in script.lower():
            raise ValueError(f"forbidden Business Rule script token: {token}")


def _validate_field_writes(*, script: str, fields_written: list[str]) -> None:
    declared = {field.strip() for field in fields_written if field.strip()}
    if not declared:
        raise ValueError("Business Rule fields_written must name at least one field")
    undeclared = sorted(set(_written_fields_from_script(script)) - declared)
    if undeclared:
        raise ValueError(f"Business Rule writes undeclared field: {undeclared[0]}")


def _written_fields_from_script(script: str) -> list[str]:
    written_fields = set(re.findall(r"\bcurrent\.([a-zA-Z0-9_]+)\s*=(?!=)", script))
    written_fields.update(
        re.findall(r"\bcurrent\.setValue\(\s*['\"]([a-zA-Z0-9_]+)['\"]", script)
    )
    written_fields.update(
        re.findall(r"\bcurrent\[\s*['\"]([a-zA-Z0-9_]+)['\"]\s*\]\s*=(?!=)", script)
    )
    return sorted(written_fields)


def _operation_mentions(text: str, operation: str) -> bool:
    return re.search(rf"\b{re.escape(operation)}\b", text, flags=re.IGNORECASE) is not None


def _business_rule_string_list(value: Any) -> list[str]:
    if type(value) is list:
        return [text for item in value if (text := _business_rule_field_text(item).strip())]
    text = _business_rule_field_text(value).strip()
    if not text:
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def _business_rule_first_text(*values: Any) -> str:
    for value in values:
        text = _business_rule_field_text(value)
        if text:
            return text
    return ""


def _business_rule_field_text(value: Any) -> str:
    if value is None:
        return ""
    if type(value) is str:
        return value
    if type(value) is bool or type(value) is int:
        return str(value)
    raise ValueError(BUSINESS_RULE_FIELD_NON_JSON_DIAGNOSTIC)
