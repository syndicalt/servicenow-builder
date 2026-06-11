from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from jedi_devproject.models import CandidateChange
from jedi_devproject.validation_helpers import single_insert_change, slug, string_list
from jedi_devproject.xml_builder import (
    SYS_SCOPE_GLOBAL,
    container_element,
    record_update,
    text_element,
)


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
    change = single_insert_change(changes, table="sys_script_client", label="Client Script")
    intent = _client_script_intent(change)
    update_name = (
        f"sys_script_client_{intent.target_table}_"
        f"{slug(intent.script_name, default='generated_client_script')}"
    )
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
    fields = dict(change.fields)
    return ClientScriptIntent(
        target_table=str(fields.get("table") or fields.get("target_table") or ""),
        script_name=str(fields.get("name") or fields.get("script_name") or ""),
        script_type=str(fields.get("type") or fields.get("client_script_type") or ""),
        field_name=str(fields.get("field") or fields.get("field_name") or ""),
        script=str(fields.get("script") or fields.get("script_body") or ""),
        fields_read=string_list(fields.get("fields_read"), ignore_none_token=True),
        fields_written=string_list(fields.get("fields_written"), ignore_none_token=True),
        messages_shown=string_list(fields.get("messages_shown"), ignore_none_token=True),
    )


def _client_script_payload(*, intent: ClientScriptIntent, update_name: str) -> str:
    return record_update(
        container_element(
            "sys_script_client",
            "<active>true</active>",
            text_element("field", intent.field_name),
            text_element("name", intent.script_name),
            text_element("script", intent.script),
            "<sys_class_name>sys_script_client</sys_class_name>",
            SYS_SCOPE_GLOBAL,
            text_element("sys_update_name", update_name),
            text_element("table", intent.target_table),
            text_element("type", intent.script_type),
            "<ui_type>10</ui_type>",
            action="INSERT_OR_UPDATE",
        )
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
    written_fields.update(
        re.findall(r"\bg_form\.clearValue\(\s*['\"]([a-zA-Z0-9_]+)['\"]", script)
    )
    undeclared = sorted(written_fields - declared)
    if undeclared:
        raise ValueError(f"Client Script writes undeclared field: {undeclared[0]}")
