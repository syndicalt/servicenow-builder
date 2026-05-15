from __future__ import annotations

import re
from html import escape
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from jedi_devproject.models import CandidateChange


class ClientScriptIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_table: str
    script_name: str
    script_type: str
    field_name: str = ""
    script: str
    fields_read: list[str]
    fields_written: list[str]
    messages_shown: list[str]

    @field_validator("target_table", "script_name", "script")
    @classmethod
    def require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned == "":
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("script_type")
    @classmethod
    def validate_script_type(cls, value: str) -> str:
        cleaned = value.strip()
        normalized = cleaned.lower()
        if normalized not in {"onload", "onchange", "onsubmit"}:
            raise ValueError("Client Script type must be onLoad, onChange, or onSubmit")
        return {
            "onload": "onLoad",
            "onchange": "onChange",
            "onsubmit": "onSubmit",
        }[normalized]

    @model_validator(mode="after")
    def validate_client_script_boundary(self) -> ClientScriptIntent:
        if self.script_type == "onChange" and self.field_name.strip() == "":
            raise ValueError("onChange Client Script requires a field")
        _validate_script_safety(self.script)
        _validate_field_writes(script=self.script, fields_written=self.fields_written)
        return self


def client_script_customer_updates(
    *,
    changes: list[CandidateChange],
    remote_update_set_sys_id: str,
) -> list[dict[str, Any]]:
    if len(changes) != 1:
        raise ValueError("Client Script handoff requires exactly one sys_script_client change")
    intent = _client_script_intent(changes[0])
    update_name = f"sys_script_client_{intent.target_table}_{_slug(intent.script_name)}"
    return [
        {
            "name": update_name,
            "remote_update_set": remote_update_set_sys_id,
            "action": "INSERT_OR_UPDATE",
            "type": "Client Script",
            "target_name": intent.script_name,
            "payload": _client_script_payload(intent=intent, update_name=update_name),
            "application": "global",
        }
    ]


def _client_script_intent(change: CandidateChange) -> ClientScriptIntent:
    if change.table != "sys_script_client":
        raise ValueError("Client Script handoff requires a sys_script_client change")
    if change.operation != "insert":
        raise ValueError("Client Script handoff supports insert only")
    fields = dict(change.fields)
    return ClientScriptIntent(
        target_table=str(fields.get("table") or fields.get("target_table") or ""),
        script_name=str(fields.get("name") or fields.get("script_name") or ""),
        script_type=str(fields.get("type") or fields.get("client_script_type") or ""),
        field_name=str(fields.get("field") or fields.get("field_name") or ""),
        script=str(fields.get("script") or fields.get("script_body") or ""),
        fields_read=_string_list(fields.get("fields_read")),
        fields_written=_string_list(fields.get("fields_written")),
        messages_shown=_string_list(fields.get("messages_shown")),
    )


def _client_script_payload(*, intent: ClientScriptIntent, update_name: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<record_update>"
        '<sys_script_client action="INSERT_OR_UPDATE">'
        "<active>true</active>"
        f"<field>{escape(intent.field_name)}</field>"
        f"<name>{escape(intent.script_name)}</name>"
        f"<script>{escape(intent.script)}</script>"
        "<sys_class_name>sys_script_client</sys_class_name>"
        '<sys_scope display_value="Global">global</sys_scope>'
        f"<sys_update_name>{escape(update_name)}</sys_update_name>"
        f"<table>{escape(intent.target_table)}</table>"
        f"<type>{escape(intent.script_type)}</type>"
        "<ui_type>10</ui_type>"
        "</sys_script_client>"
        "</record_update>"
    )


FORBIDDEN_SCRIPT_TOKENS = [
    "document.",
    "window.",
    "XMLHttpRequest",
    "fetch",
    "localStorage",
    "sessionStorage",
    "GlideAjax",
    "http://",
    "https://",
    "password",
    "token",
    "api_key",
    "endpoint",
]


def _validate_script_safety(script: str) -> None:
    for token in FORBIDDEN_SCRIPT_TOKENS:
        if token.lower() in script.lower():
            raise ValueError(f"forbidden Client Script token: {token}")
    if "g_form" not in script:
        raise ValueError("Client Script must use g_form APIs")


def _validate_field_writes(*, script: str, fields_written: list[str]) -> None:
    declared = {field.strip() for field in fields_written if field.strip()}
    written_fields = set(
        re.findall(r"\bg_form\.setValue\(\s*['\"]([a-zA-Z0-9_]+)['\"]", script)
    )
    undeclared = sorted(written_fields - declared)
    if undeclared:
        raise ValueError(f"Client Script writes undeclared field: {undeclared[0]}")


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower()).strip("_")
    return cleaned or "generated_client_script"


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    text = str(value or "").strip()
    if not text:
        return []
    if text.lower() == "none":
        return []
    return [item.strip() for item in text.split(",") if item.strip()]
