"""Deterministic catalog client script generation for generated catalog items.

This module renders ``catalog_script_client`` customer-update payloads with the
same g_form-only safety contract as the form-level
:mod:`jedi_devproject.client_script_generation` module: onLoad/onChange/onSubmit
types only, g_form get/set/clear APIs only, the shared forbidden-token list
(DOM access, fetch/XHR, GlideAjax, external URLs, credentials), an onChange
script must name its watched variable, and declared ``fields_written`` must
match the script's writes. On top of that contract, every variable a catalog
script reads, writes, or watches must be one of the catalog item's OWN
generated variables — anything else fails closed.

Script bodies are never free-form: :func:`render_catalog_client_script`
deterministically renders a canonical g_form-only script from declarative
set/clear actions, and the rendered output is still validated through the
shared client-script validators (defense in depth).

Evidence assumptions about the XML shape (UAT confirmation pending):

- ``catalog_script_client`` extends ``sys_script_client``. It attaches to the
  item via ``cat_item``, scopes via ``applies_catalog``/``applies_req_item``
  (``applies_sc_task``/``applies_target_record`` stay false), and for onChange
  carries the watched variable name in the inherited ``field`` column.
- Whether current-release imports additionally require a ``cat_variable``
  reference (``IO:<variable sys_id>``) must be confirmed against a real
  exported update set during UAT.

These shapes follow ServiceNow conventions but are unconfirmed; the surface
starts at builder-maturity baseline 0.30 (candidate generation only, no
automated handoff) until UAT evidence confirms the shape.
"""

from __future__ import annotations

from collections.abc import Collection, Sequence
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from jedi_devproject.client_script_generation import (
    ClientScriptIntent,
    _validate_field_writes,
    _validate_script_safety,
)
from jedi_devproject.models import CandidateChange
from jedi_devproject.validation_helpers import slug, stable_record_sys_id, string_list
from jedi_devproject.xml_builder import (
    SYS_SCOPE_GLOBAL,
    container_element,
    record_update,
    text_element,
)

CATALOG_CLIENT_SCRIPT_TABLE = "catalog_script_client"


class CatalogClientScriptAction(BaseModel):
    """One declarative g_form effect: set a variable's value or clear it."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["set_value", "clear_value"]
    variable: str
    value: str = ""

    @field_validator("variable")
    @classmethod
    def require_variable(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned == "":
            raise ValueError("catalog client script action requires a variable")
        return cleaned

    @model_validator(mode="after")
    def validate_action_shape(self) -> CatalogClientScriptAction:
        if self.kind == "set_value" and self.value.strip() == "":
            raise ValueError("catalog client script set_value action requires a value")
        if self.kind == "clear_value" and self.value.strip() != "":
            raise ValueError("catalog client script clear_value action must not carry a value")
        return self


def render_catalog_client_script(
    *,
    script_type: str,
    actions: Sequence[CatalogClientScriptAction],
    variable_name: str = "",
) -> str:
    """Render the canonical g_form-only script for declarative actions.

    The output is validated through the shared client-script validators before
    it is returned, so a rendered script can never carry forbidden tokens even
    if an action value smuggles one in.
    """
    normalized_type = ClientScriptIntent.validate_script_type(script_type)
    if not actions:
        raise ValueError("catalog client script requires at least one action")
    statements = [_action_statement(action) for action in actions]
    if normalized_type == "onLoad":
        body = "\n".join(f"    {statement}" for statement in statements)
        script = f"function onLoad() {{\n{body}\n}}"
    elif normalized_type == "onChange":
        if not variable_name.strip():
            raise ValueError("onChange catalog client script requires a variable")
        body = "\n".join(f"    {statement}" for statement in statements)
        script = (
            "function onChange(control, oldValue, newValue, isLoading, isTemplate) {\n"
            "    if (isLoading) {\n"
            "        return;\n"
            "    }\n"
            f"{body}\n"
            "}"
        )
    else:
        body = "\n".join(f"    {statement}" for statement in statements)
        script = f"function onSubmit() {{\n{body}\n    return true;\n}}"
    _validate_script_safety(script)
    _validate_field_writes(
        script=script,
        fields_written=[action.variable for action in actions],
    )
    return script


def _action_statement(action: CatalogClientScriptAction) -> str:
    if action.kind == "clear_value":
        return f"g_form.clearValue('{_script_literal(action.variable)}');"
    return (
        f"g_form.setValue('{_script_literal(action.variable)}', "
        f"'{_script_literal(action.value)}');"
    )


def _script_literal(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    if "\n" in escaped or "\r" in escaped:
        raise ValueError("catalog client script values must be single-line text")
    return escaped


class CatalogClientScriptIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    catalog_item_name: str
    script_name: str
    script_type: str
    variable_name: str = ""
    script: str
    fields_read: list[str]
    fields_written: list[str]

    @field_validator("catalog_item_name", "script_name", "script")
    @classmethod
    def require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned == "":
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("script_type")
    @classmethod
    def validate_script_type(cls, value: str) -> str:
        return ClientScriptIntent.validate_script_type(value)

    @model_validator(mode="after")
    def validate_catalog_client_script_boundary(self) -> CatalogClientScriptIntent:
        if self.script_type == "onChange" and self.variable_name.strip() == "":
            raise ValueError("onChange catalog client script requires a variable")
        _validate_script_safety(self.script)
        _validate_field_writes(script=self.script, fields_written=self.fields_written)
        return self


def catalog_client_script_customer_updates(
    *,
    changes: list[CandidateChange],
    remote_update_set_sys_id: str,
    catalog_item_name: str,
    catalog_item_sys_id: str,
    item_variable_names: Collection[str],
) -> list[dict[str, Any]]:
    """Render customer updates for catalog client scripts on a generated item.

    ``item_variable_names`` is the set of the catalog item's OWN generated
    variable names; every variable the script reads, writes, or watches must
    be a member or the build fails closed.
    """
    intents = [
        _catalog_client_script_intent(change, catalog_item_name=catalog_item_name)
        for change in changes
    ]
    seen_names: set[str] = set()
    updates: list[dict[str, Any]] = []
    for intent in intents:
        if intent.script_name in seen_names:
            raise ValueError(
                f"Catalog Client Script handoff received a duplicate script: "
                f"{intent.script_name}"
            )
        seen_names.add(intent.script_name)
        _validate_item_variables(intent, item_variable_names=item_variable_names)
        update_name = (
            f"catalog_script_client_{slug(catalog_item_name, default='catalog_item')}_"
            f"{slug(intent.script_name, default='generated_catalog_client_script')}"
        )
        updates.append(
            {
                "name": update_name,
                "remote_update_set": remote_update_set_sys_id,
                "action": "INSERT_OR_UPDATE",
                "type": "Catalog Client Script",
                "target_name": f"{catalog_item_name}.{intent.script_name}",
                "payload": _catalog_client_script_payload(
                    intent=intent,
                    catalog_item_sys_id=catalog_item_sys_id,
                    script_sys_id=stable_record_sys_id(
                        "catalog_script_client",
                        catalog_item_name,
                        intent.script_name,
                    ),
                    update_name=update_name,
                ),
                "application": "global",
            }
        )
    return updates


def _catalog_client_script_intent(
    change: CandidateChange,
    *,
    catalog_item_name: str,
) -> CatalogClientScriptIntent:
    if change.table != CATALOG_CLIENT_SCRIPT_TABLE:
        raise ValueError(
            f"Catalog Client Script handoff requires {CATALOG_CLIENT_SCRIPT_TABLE} "
            f"changes only: {change.table}"
        )
    if change.operation != "insert":
        raise ValueError("Catalog Client Script handoff supports insert only")
    fields = dict(change.fields)
    return CatalogClientScriptIntent(
        catalog_item_name=catalog_item_name,
        script_name=str(fields.get("name") or fields.get("script_name") or ""),
        script_type=str(fields.get("type") or fields.get("client_script_type") or ""),
        variable_name=str(
            fields.get("field") or fields.get("variable") or fields.get("field_name") or ""
        ),
        script=str(fields.get("script") or fields.get("script_body") or ""),
        fields_read=string_list(fields.get("fields_read"), ignore_none_token=True),
        fields_written=string_list(fields.get("fields_written"), ignore_none_token=True),
    )


def _validate_item_variables(
    intent: CatalogClientScriptIntent,
    *,
    item_variable_names: Collection[str],
) -> None:
    members = set(item_variable_names)
    referenced = [
        *([intent.variable_name] if intent.variable_name.strip() else []),
        *intent.fields_read,
        *intent.fields_written,
    ]
    for variable in referenced:
        if variable not in members:
            raise ValueError(
                "catalog client script references a variable that is not one of "
                f"the catalog item's own variables: {variable}"
            )


def _catalog_client_script_payload(
    *,
    intent: CatalogClientScriptIntent,
    catalog_item_sys_id: str,
    script_sys_id: str,
    update_name: str,
) -> str:
    return record_update(
        container_element(
            "catalog_script_client",
            "<active>true</active>",
            "<applies_catalog>true</applies_catalog>",
            "<applies_req_item>true</applies_req_item>",
            "<applies_sc_task>false</applies_sc_task>",
            "<applies_target_record>false</applies_target_record>",
            text_element(
                "cat_item",
                catalog_item_sys_id,
                display_value=intent.catalog_item_name,
            ),
            text_element("field", intent.variable_name),
            text_element("name", intent.script_name),
            text_element("script", intent.script),
            "<sys_class_name>catalog_script_client</sys_class_name>",
            text_element("sys_id", script_sys_id),
            SYS_SCOPE_GLOBAL,
            text_element("sys_update_name", update_name),
            text_element("type", intent.script_type),
            "<ui_type>10</ui_type>",
            action="INSERT_OR_UPDATE",
        ),
        table="catalog_script_client",
    )
