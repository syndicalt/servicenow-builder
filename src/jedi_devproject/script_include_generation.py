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

SCRIPT_INCLUDE_FIELD_NON_JSON_DIAGNOSTIC = (
    "Script Include generation field contains non-JSON value"
)


class ScriptIncludeIntent(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

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
    change = single_insert_change(changes, table="sys_script_include", label="Script Include")
    intent = _script_include_intent(change)
    update_name = f"sys_script_include_{slug(intent.name, default='generated_script_include')}"
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
    fields = dict(change.fields)
    script = _script_include_first_text(fields.get("script"), fields.get("script_body"))
    name = _script_include_first_text(fields.get("name"), fields.get("script_include_name"))
    return ScriptIncludeIntent(
        name=name,
        api_name=_script_include_first_text(fields.get("api_name"), f"global.{name}"),
        scope=_script_include_first_text(fields.get("scope"), "global"),
        client_callable=bool_value(_script_include_first_text(fields.get("client_callable"))),
        active=bool_value(_script_include_first_text(fields.get("active")), default=True),
        description=_script_include_first_text(fields.get("description")),
        script=script,
        public_methods=(
            _script_include_string_list(
                fields.get("public_methods"),
                ignore_none_token=True,
            )
            or _public_methods_from_script(script)
        ),
        tables_read=_script_include_string_list(
            fields.get("tables_read"),
            ignore_none_token=True,
        ),
        tables_written=_script_include_string_list(
            fields.get("tables_written"),
            ignore_none_token=True,
        ),
        fields_read=_script_include_string_list(
            fields.get("fields_read"),
            ignore_none_token=True,
        ),
        fields_written=_script_include_string_list(
            fields.get("fields_written"),
            ignore_none_token=True,
        ),
    )


def _script_include_payload(*, intent: ScriptIncludeIntent, update_name: str) -> str:
    return record_update(
        container_element(
            "sys_script_include",
            "<access>public</access>",
            bool_element("active", intent.active),
            text_element("api_name", intent.api_name),
            bool_element("client_callable", intent.client_callable),
            text_element("description", intent.description),
            text_element("name", intent.name),
            text_element("script", intent.script),
            "<sys_class_name>sys_script_include</sys_class_name>",
            SYS_SCOPE_GLOBAL,
            text_element("sys_update_name", update_name),
            action="INSERT_OR_UPDATE",
        )
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


def _script_include_string_list(
    value: Any,
    *,
    ignore_none_token: bool = False,
) -> list[str]:
    if type(value) is list:
        return [text for item in value if (text := _script_include_field_text(item).strip())]
    text = "" if value is None else _script_include_field_text(value).strip()
    if not text or (ignore_none_token and text.lower() == "none"):
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def _script_include_first_text(*values: Any) -> str:
    for value in values:
        text = _script_include_field_text(value)
        if text:
            return text
    return ""


def _script_include_field_text(value: Any) -> str:
    if value is None:
        return ""
    if type(value) is str:
        return value
    if type(value) is bool or type(value) is int:
        return str(value)
    raise ValueError(SCRIPT_INCLUDE_FIELD_NON_JSON_DIAGNOSTIC)


def _public_methods_from_script(script: str) -> list[str]:
    methods = {
        match
        for match in re.findall(r"\b([A-Za-z][A-Za-z0-9_]*)\s*:\s*function\s*\(", script)
        if match not in {"initialize", "type"}
    }
    return sorted(methods)
