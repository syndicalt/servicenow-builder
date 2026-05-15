from __future__ import annotations

import re
from html import escape
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from jedi_devproject.models import CandidateChange


class ScriptIncludeIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    api_name: str
    scope: str
    client_callable: bool = False
    active: bool = True
    description: str = ""
    script: str
    public_methods: list[str]
    tables_read: list[str]
    tables_written: list[str]
    fields_read: list[str]
    fields_written: list[str]

    @field_validator("name", "api_name", "scope", "script")
    @classmethod
    def require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned == "":
            raise ValueError("must not be empty")
        return cleaned

    @model_validator(mode="after")
    def validate_script_include_boundary(self) -> ScriptIncludeIntent:
        if self.client_callable:
            raise ValueError("client callable Script Includes are not supported")
        if self.scope.strip().lower() != "global":
            raise ValueError("Script Include scope must be global until scoped XML is supported")
        _validate_identifier(self.name)
        if self.api_name != f"global.{self.name}":
            raise ValueError("Script Include api_name must be global.<Script Include name>")
        if not [method.strip() for method in self.public_methods if method.strip()]:
            raise ValueError("Script Include public_methods must name at least one method")
        if self.tables_written or self.fields_written:
            raise ValueError("Script Include writes are not supported in the current profile")
        _validate_script_safety(script=self.script, name=self.name)
        return self


def script_include_customer_updates(
    *,
    changes: list[CandidateChange],
    remote_update_set_sys_id: str,
) -> list[dict[str, Any]]:
    if len(changes) != 1:
        raise ValueError("Script Include handoff requires exactly one sys_script_include change")
    intent = _script_include_intent(changes[0])
    update_name = f"sys_script_include_{_slug(intent.name)}"
    return [
        {
            "name": update_name,
            "remote_update_set": remote_update_set_sys_id,
            "action": "INSERT_OR_UPDATE",
            "type": "Script Include",
            "target_name": intent.name,
            "payload": _script_include_payload(intent=intent, update_name=update_name),
            "application": "global",
        }
    ]


def _script_include_intent(change: CandidateChange) -> ScriptIncludeIntent:
    if change.table != "sys_script_include":
        raise ValueError("Script Include handoff requires a sys_script_include change")
    if change.operation != "insert":
        raise ValueError("Script Include handoff supports insert only")
    fields = dict(change.fields)
    script = str(fields.get("script") or fields.get("script_body") or "")
    name = str(fields.get("name") or fields.get("script_include_name") or "")
    return ScriptIncludeIntent(
        name=name,
        api_name=str(fields.get("api_name") or f"global.{name}"),
        scope=str(fields.get("scope") or "global"),
        client_callable=_bool_value(fields.get("client_callable")),
        active=_bool_value(fields.get("active"), default=True),
        description=str(fields.get("description") or ""),
        script=script,
        public_methods=(
            _string_list(fields.get("public_methods")) or _public_methods_from_script(script)
        ),
        tables_read=_string_list(fields.get("tables_read")),
        tables_written=_string_list(fields.get("tables_written")),
        fields_read=_string_list(fields.get("fields_read")),
        fields_written=_string_list(fields.get("fields_written")),
    )


def _script_include_payload(*, intent: ScriptIncludeIntent, update_name: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<record_update>"
        '<sys_script_include action="INSERT_OR_UPDATE">'
        f"<access>public</access>"
        f"<active>{_bool_text(intent.active)}</active>"
        f"<api_name>{escape(intent.api_name)}</api_name>"
        f"<client_callable>{_bool_text(intent.client_callable)}</client_callable>"
        f"<description>{escape(intent.description)}</description>"
        f"<name>{escape(intent.name)}</name>"
        f"<script>{escape(intent.script)}</script>"
        "<sys_class_name>sys_script_include</sys_class_name>"
        '<sys_scope display_value="Global">global</sys_scope>'
        f"<sys_update_name>{escape(update_name)}</sys_update_name>"
        "</sys_script_include>"
        "</record_update>"
    )


FORBIDDEN_SCRIPT_TOKENS = [
    "GlideRecord(",
    "deleteRecord",
    "deleteMultiple",
    "updateMultiple",
    "setWorkflow(false)",
    "gs.eventQueue",
    "sn_ws",
    "RESTMessageV2",
    "SOAPMessageV2",
    "GlideCredential",
    "http://",
    "https://",
    "password",
    "token",
    "api_key",
    "endpoint",
]


def _validate_script_safety(*, script: str, name: str) -> None:
    if name not in script:
        raise ValueError("Script Include script must define the requested name")
    for token in FORBIDDEN_SCRIPT_TOKENS:
        if token.lower() in script.lower():
            raise ValueError(f"forbidden Script Include token: {token}")


def _validate_identifier(value: str) -> None:
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", value) is None:
        raise ValueError("Script Include name must be a valid identifier")


def _public_methods_from_script(script: str) -> list[str]:
    methods = {
        match
        for match in re.findall(r"\b([A-Za-z][A-Za-z0-9_]*)\s*:\s*function\s*\(", script)
        if match not in {"initialize", "type"}
    }
    return sorted(methods)


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower()).strip("_")
    return cleaned or "generated_script_include"


def _bool_value(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes"}


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    text = str(value or "").strip()
    if not text or text.lower() == "none":
        return []
    return [item.strip() for item in text.split(",") if item.strip()]
