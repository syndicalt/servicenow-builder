from __future__ import annotations

import re
from html import escape
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from jedi_devproject.models import CandidateChange


class BusinessRuleIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
    if len(changes) != 1:
        raise ValueError("Business Rule handoff requires exactly one sys_script change")
    intent = _business_rule_intent(changes[0])
    update_name = f"sys_script_{intent.target_table}_{_slug(intent.rule_name)}"
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
    if change.table != "sys_script":
        raise ValueError("Business Rule handoff requires a sys_script change")
    if change.operation != "insert":
        raise ValueError("Business Rule handoff supports insert only")
    fields = dict(change.fields)
    script = str(
        fields.get("script") or fields.get("action_script") or fields.get("script_body") or ""
    )
    return BusinessRuleIntent(
        target_table=str(fields.get("collection") or fields.get("table") or ""),
        rule_name=str(fields.get("name") or ""),
        when=str(fields.get("when") or ""),
        action_insert=_bool_value(fields.get("action_insert")) or _bool_value(fields.get("insert")),
        action_update=_bool_value(fields.get("action_update")) or _bool_value(fields.get("update")),
        filter_condition=str(fields.get("filter_condition") or fields.get("condition") or ""),
        script=script,
        fields_read=_string_list(fields.get("fields_read")),
        fields_written=(
            _string_list(fields.get("fields_written")) or _written_fields_from_script(script)
        ),
    )


def _business_rule_payload(*, intent: BusinessRuleIntent, update_name: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<record_update>"
        '<sys_script action="INSERT_OR_UPDATE">'
        "<active>true</active>"
        f"<action_insert>{_bool_text(intent.action_insert)}</action_insert>"
        f"<action_update>{_bool_text(intent.action_update)}</action_update>"
        "<action_delete>false</action_delete>"
        "<action_query>false</action_query>"
        "<advanced>true</advanced>"
        f"<collection>{escape(intent.target_table)}</collection>"
        f"<filter_condition>{escape(intent.filter_condition)}</filter_condition>"
        f"<name>{escape(intent.rule_name)}</name>"
        "<order>100</order>"
        f"<script>{escape(intent.script)}</script>"
        "<sys_class_name>sys_script</sys_class_name>"
        '<sys_scope display_value="Global">global</sys_scope>'
        f"<sys_update_name>{escape(update_name)}</sys_update_name>"
        f"<when>{escape(intent.when)}</when>"
        "</sys_script>"
        "</record_update>"
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
    for token in FORBIDDEN_SCRIPT_TOKENS:
        if token.lower() in script.lower():
            raise ValueError(f"forbidden Business Rule script token: {token}")


def _validate_field_writes(*, script: str, fields_written: list[str]) -> None:
    declared = {field.strip() for field in fields_written if field.strip()}
    if not declared:
        raise ValueError("Business Rule fields_written must name at least one field")
    written_fields = set(re.findall(r"\bcurrent\.([a-zA-Z0-9_]+)\s*=(?!=)", script))
    written_fields.update(
        re.findall(r"\bcurrent\.setValue\(\s*['\"]([a-zA-Z0-9_]+)['\"]", script)
    )
    written_fields.update(
        re.findall(r"\bcurrent\[\s*['\"]([a-zA-Z0-9_]+)['\"]\s*\]\s*=(?!=)", script)
    )
    undeclared = sorted(written_fields - declared)
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


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower()).strip("_")
    return cleaned or "generated_business_rule"


def _bool_value(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    text = str(value or "").strip()
    if not text:
        return []
    return [item.strip() for item in text.split(",") if item.strip()]
