"""Deterministic catalog UI policy generation for generated catalog items.

This module renders ``catalog_ui_policy`` and ``catalog_ui_policy_action``
customer-update payloads for the same declarative subset the form-level
:mod:`jedi_devproject.ui_policy_generation` module allows: declarative
conditions on variable values and visible/mandatory/read-only/cleared actions.
``run_scripts`` and policy scripts are rejected, and every referenced variable
must be one of the catalog item's OWN generated variables — references to
anything else fail closed.

Evidence assumptions about the XML shape (UAT confirmation pending):

- ``catalog_ui_policy`` extends ``sys_ui_policy``. The condition lives in
  ``catalog_conditions`` using the platform's ``IO:<variable sys_id>`` encoded
  query convention, the policy attaches to the item via ``catalog_item``, and
  ``applies_catalog``/``applies_req_item`` scope it to ordering and requested
  item views (``applies_sc_task``/``applies_target_record`` stay false).
- ``catalog_ui_policy_action`` extends ``sys_ui_policy_action``. It targets the
  variable via ``catalog_variable`` (``IO:<variable sys_id>``) and also carries
  the variable name in the legacy ``variable`` column.

These shapes follow ServiceNow conventions for exported catalog UI policies
but have not yet been confirmed against a real exported update set. That is by
design: this surface starts at builder-maturity baseline 0.30 (candidate
generation only, no automated handoff) until UAT evidence confirms the shape.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from jedi_devproject.models import CandidateChange
from jedi_devproject.ui_policy_generation import _validate_safe_text
from jedi_devproject.validation_helpers import bool_text, bool_value, slug, stable_record_sys_id
from jedi_devproject.xml_builder import (
    SYS_SCOPE_GLOBAL,
    bool_element,
    container_element,
    record_update,
    text_element,
)

CATALOG_UI_POLICY_TABLES = frozenset({"catalog_ui_policy", "catalog_ui_policy_action"})
CATALOG_UI_POLICY_FIELD_NON_JSON_DIAGNOSTIC = (
    "Catalog UI Policy generation field contains non-JSON value"
)

_CONDITION_OPERATORS = ("ISNOTEMPTY", "ISEMPTY", "!=", "=")
_UNARY_CONDITION_OPERATORS = frozenset({"ISEMPTY", "ISNOTEMPTY"})
_CONDITION_PATTERN = re.compile(
    r"^(?P<variable>[a-z][a-z0-9_]*)"
    r"(?P<operator>ISNOTEMPTY|ISEMPTY|!=|=)"
    r"(?P<value>.*)$"
)


class CatalogUiPolicyCondition(BaseModel):
    """One declarative condition term against an item variable's value."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    join: str = "AND"
    variable: str
    operator: str
    value: str = ""

    @field_validator("join")
    @classmethod
    def validate_join(cls, value: str) -> str:
        if value not in {"AND", "OR"}:
            raise ValueError("catalog UI policy condition join must be AND or OR")
        return value


def parse_catalog_ui_policy_conditions(conditions: str) -> list[CatalogUiPolicyCondition]:
    """Parse a declarative variable condition string, failing closed otherwise.

    Grammar (anything else raises ``ValueError``)::

        conditions := condition ( ("^" | "^OR") condition )*
        condition  := variable ("=" | "!=") value | variable ("ISEMPTY" | "ISNOTEMPTY")
        variable   := [a-z][a-z0-9_]*   (a catalog item variable name)
        value      := non-empty text without forbidden tokens
    """
    cleaned = conditions.strip()
    if not cleaned:
        raise ValueError("catalog UI policy requires a condition")
    _validate_safe_text(cleaned)
    parsed: list[CatalogUiPolicyCondition] = []
    for index, raw_condition in enumerate(cleaned.split("^")):
        condition = raw_condition
        join = "AND"
        if index > 0 and condition.startswith("OR"):
            join = "OR"
            condition = condition[2:]
        match = _CONDITION_PATTERN.fullmatch(condition)
        if match is None:
            raise ValueError(
                "catalog UI policy condition is not a declarative "
                f"variable-operator-value term: {raw_condition}"
            )
        operator = match.group("operator")
        value = match.group("value")
        if operator in _UNARY_CONDITION_OPERATORS and value:
            raise ValueError(
                f"catalog UI policy condition operator {operator} must not carry a value"
            )
        if operator not in _UNARY_CONDITION_OPERATORS and not value:
            raise ValueError(
                f"catalog UI policy condition is missing a value: {raw_condition}"
            )
        parsed.append(
            CatalogUiPolicyCondition(
                join=join,
                variable=match.group("variable"),
                operator=operator,
                value=value,
            )
        )
    return parsed


def catalog_ui_policy_condition_variables(conditions: str) -> list[str]:
    """Variable names referenced by a declarative condition (parse-validated)."""
    return [condition.variable for condition in parse_catalog_ui_policy_conditions(conditions)]


class CatalogUiPolicyActionIntent(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    policy_name: str = ""
    variable: str
    mandatory: str = "ignore"
    visible: str = "ignore"
    disabled: str = "ignore"
    cleared: bool = False

    @field_validator("variable")
    @classmethod
    def require_variable(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned == "":
            raise ValueError("catalog UI policy action requires a variable")
        return cleaned

    @field_validator("mandatory", "visible", "disabled")
    @classmethod
    def validate_tristate(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"true", "false", "ignore"}:
            raise ValueError("catalog UI policy action values must be true, false, or ignore")
        return cleaned

    @model_validator(mode="after")
    def require_effect(self) -> CatalogUiPolicyActionIntent:
        if (
            self.mandatory == "ignore"
            and self.visible == "ignore"
            and self.disabled == "ignore"
            and not self.cleared
        ):
            raise ValueError(
                "catalog UI policy action must set visible, mandatory, read-only, or cleared"
            )
        return self


class CatalogUiPolicyIntent(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    catalog_item_name: str
    policy_name: str
    conditions: str
    reverse_if_false: bool = True
    run_scripts: bool = False
    active: bool = True
    on_load: bool = True
    order: int = 100
    script_true: str = ""
    script_false: str = ""
    actions: list[CatalogUiPolicyActionIntent]

    @field_validator("catalog_item_name", "policy_name", "conditions")
    @classmethod
    def require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned == "":
            raise ValueError("must not be empty")
        return cleaned

    @model_validator(mode="after")
    def validate_catalog_ui_policy_boundary(self) -> CatalogUiPolicyIntent:
        if self.run_scripts:
            raise ValueError("catalog UI policy run_scripts must be false")
        if self.script_true.strip() or self.script_false.strip():
            raise ValueError("catalog UI policy scripts are not supported")
        if not self.actions:
            raise ValueError("catalog UI policy requires at least one action")
        _validate_safe_text(self.policy_name)
        for action in self.actions:
            if action.policy_name and action.policy_name != self.policy_name:
                raise ValueError("catalog UI policy action policy_name must match policy")
        return self


def catalog_ui_policy_customer_updates(
    *,
    changes: list[CandidateChange],
    remote_update_set_sys_id: str,
    catalog_item_name: str,
    catalog_item_sys_id: str,
    variable_sys_ids: Mapping[str, str],
) -> list[dict[str, Any]]:
    """Render customer updates for catalog UI policies on a generated item.

    ``variable_sys_ids`` maps the catalog item's OWN generated variable names
    to their deterministic sys_ids; every condition and action variable must
    resolve through it or the build fails closed.
    """
    intents = _catalog_ui_policy_intents(changes, catalog_item_name=catalog_item_name)
    updates: list[dict[str, Any]] = []
    for intent in intents:
        parsed_conditions = parse_catalog_ui_policy_conditions(intent.conditions)
        for condition in parsed_conditions:
            _require_item_variable(
                condition.variable,
                variable_sys_ids=variable_sys_ids,
                context="condition",
            )
        for action in intent.actions:
            _require_item_variable(
                action.variable,
                variable_sys_ids=variable_sys_ids,
                context="action",
            )
        policy_update_name = (
            f"catalog_ui_policy_{slug(catalog_item_name, default='catalog_item')}_"
            f"{slug(intent.policy_name, default='generated_catalog_ui_policy')}"
        )
        policy_sys_id = stable_record_sys_id(
            "catalog_ui_policy", catalog_item_name, intent.policy_name
        )
        updates.append(
            {
                "name": policy_update_name,
                "remote_update_set": remote_update_set_sys_id,
                "action": "INSERT_OR_UPDATE",
                "type": "Catalog UI Policy",
                "target_name": f"{catalog_item_name}.{intent.policy_name}",
                "payload": _catalog_ui_policy_payload(
                    intent=intent,
                    catalog_conditions=_render_catalog_conditions(
                        parsed_conditions,
                        variable_sys_ids=variable_sys_ids,
                    ),
                    catalog_item_sys_id=catalog_item_sys_id,
                    policy_sys_id=policy_sys_id,
                    update_name=policy_update_name,
                ),
                "application": "global",
            }
        )
        for action in intent.actions:
            action_update_name = (
                f"catalog_ui_policy_action_{slug(catalog_item_name, default='catalog_item')}_"
                f"{slug(intent.policy_name, default='generated_catalog_ui_policy')}_"
                f"{slug(action.variable, default='variable')}_{_action_suffix(action)}"
            )
            updates.append(
                {
                    "name": action_update_name,
                    "remote_update_set": remote_update_set_sys_id,
                    "action": "INSERT_OR_UPDATE",
                    "type": "Catalog UI Policy Action",
                    "target_name": f"{intent.policy_name}.{action.variable}",
                    "payload": _catalog_ui_policy_action_payload(
                        intent=intent,
                        action=action,
                        catalog_item_sys_id=catalog_item_sys_id,
                        policy_sys_id=policy_sys_id,
                        variable_sys_id=variable_sys_ids[action.variable],
                        update_name=action_update_name,
                        sys_id=stable_record_sys_id(
                            "catalog_ui_policy_action",
                            catalog_item_name,
                            intent.policy_name,
                            action.variable,
                        ),
                    ),
                    "application": "global",
                }
            )
    return updates


def _catalog_ui_policy_intents(
    changes: list[CandidateChange],
    *,
    catalog_item_name: str,
) -> list[CatalogUiPolicyIntent]:
    unexpected_tables = sorted({change.table for change in changes} - CATALOG_UI_POLICY_TABLES)
    if unexpected_tables:
        raise ValueError(
            "Catalog UI Policy handoff received unsupported tables: "
            f"{', '.join(unexpected_tables)}"
        )
    policy_changes = [change for change in changes if change.table == "catalog_ui_policy"]
    if not policy_changes:
        raise ValueError("Catalog UI Policy handoff requires a catalog_ui_policy change")
    action_changes = [change for change in changes if change.table == "catalog_ui_policy_action"]
    if not action_changes:
        raise ValueError(
            "Catalog UI Policy handoff requires at least one catalog_ui_policy_action change"
        )
    titles: list[str] = []
    for change in policy_changes:
        if change.operation != "insert":
            raise ValueError("Catalog UI Policy handoff supports policy insert only")
        title = _policy_title(dict(change.fields))
        if title in titles:
            raise ValueError(f"Catalog UI Policy handoff received a duplicate policy: {title}")
        titles.append(title)
    actions_by_title: dict[str, list[CatalogUiPolicyActionIntent]] = {title: [] for title in titles}
    for change in action_changes:
        if change.operation != "insert":
            raise ValueError("Catalog UI Policy handoff supports action insert only")
        fields = dict(change.fields)
        title = _catalog_ui_policy_first_text(
            fields.get("ui_policy")
            if fields.get("ui_policy") is not None
            else fields.get("policy"),
            fields.get("policy_name"),
        ).strip()
        if not title:
            if len(titles) != 1:
                raise ValueError(
                    "Catalog UI Policy action must name its policy when "
                    "multiple policies are generated"
                )
            title = titles[0]
        if title not in actions_by_title:
            raise ValueError(f"Catalog UI Policy action references unknown policy: {title}")
        actions_by_title[title].append(_catalog_ui_policy_action_intent(fields, policy_name=title))
    intents: list[CatalogUiPolicyIntent] = []
    for change in policy_changes:
        fields = dict(change.fields)
        title = _policy_title(fields)
        intents.append(
            CatalogUiPolicyIntent(
                catalog_item_name=catalog_item_name,
                policy_name=title,
                conditions=_catalog_ui_policy_first_text(
                    fields.get("catalog_conditions")
                    if fields.get("catalog_conditions") is not None
                    else fields.get("conditions"),
                    fields.get("condition"),
                ),
                reverse_if_false=bool_value(
                    _catalog_ui_policy_first_text(fields.get("reverse_if_false")),
                    default=True,
                ),
                run_scripts=bool_value(
                    _catalog_ui_policy_first_text(fields.get("run_scripts"))
                ),
                active=bool_value(
                    _catalog_ui_policy_first_text(fields.get("active")),
                    default=True,
                ),
                on_load=bool_value(
                    _catalog_ui_policy_first_text(fields.get("on_load")),
                    default=True,
                ),
                order=_catalog_ui_policy_optional_int(fields.get("order")) or 100,
                script_true=_catalog_ui_policy_first_text(fields.get("script_true")),
                script_false=_catalog_ui_policy_first_text(fields.get("script_false")),
                actions=actions_by_title[title],
            )
        )
    return intents


def _policy_title(fields: dict[str, Any]) -> str:
    return _catalog_ui_policy_first_text(
        fields.get("short_description")
        if fields.get("short_description") is not None
        else fields.get("policy_name"),
        fields.get("name"),
    ).strip()


def _catalog_ui_policy_action_intent(
    fields: dict[str, Any],
    *,
    policy_name: str,
) -> CatalogUiPolicyActionIntent:
    disabled_value = fields.get("disabled")
    if _catalog_ui_policy_first_text(disabled_value).strip().lower() in {"", "ignore"}:
        disabled_value = fields.get("read_only", disabled_value)
    return CatalogUiPolicyActionIntent(
        policy_name=policy_name,
        variable=_catalog_ui_policy_first_text(fields.get("variable"), fields.get("field")),
        mandatory=_catalog_ui_policy_tristate(fields.get("mandatory")),
        visible=_catalog_ui_policy_tristate(fields.get("visible")),
        disabled=_catalog_ui_policy_tristate(disabled_value),
        cleared=bool_value(
            _catalog_ui_policy_first_text(fields.get("cleared", fields.get("clear_value")))
        ),
    )


def _catalog_ui_policy_tristate(value: Any) -> str:
    if isinstance(value, bool):
        return bool_text(value)
    text = _catalog_ui_policy_first_text(value, "ignore").strip().lower()
    if text in {"", "none", "leave alone"}:
        return "ignore"
    return text


def _catalog_ui_policy_optional_int(value: Any) -> int | None:
    text = _catalog_ui_policy_field_text(value).strip()
    return int(text) if text.isdigit() else None


def _catalog_ui_policy_first_text(*values: Any) -> str:
    for value in values:
        text = _catalog_ui_policy_field_text(value)
        if text:
            return text
    return ""


def _catalog_ui_policy_field_text(value: Any) -> str:
    if value is None:
        return ""
    if type(value) is str:
        return value
    if type(value) is bool or type(value) is int:
        return str(value)
    raise ValueError(CATALOG_UI_POLICY_FIELD_NON_JSON_DIAGNOSTIC)


def _require_item_variable(
    variable: str,
    *,
    variable_sys_ids: Mapping[str, str],
    context: str,
) -> None:
    if variable not in variable_sys_ids:
        raise ValueError(
            f"catalog UI policy {context} references a variable that is not "
            f"one of the catalog item's own variables: {variable}"
        )


def _render_catalog_conditions(
    conditions: list[CatalogUiPolicyCondition],
    *,
    variable_sys_ids: Mapping[str, str],
) -> str:
    parts: list[str] = []
    for index, condition in enumerate(conditions):
        prefix = "" if index == 0 else ("^OR" if condition.join == "OR" else "^")
        parts.append(
            f"{prefix}IO:{variable_sys_ids[condition.variable]}"
            f"{condition.operator}{condition.value}"
        )
    return "".join(parts) + "^EQ"


def _catalog_ui_policy_payload(
    *,
    intent: CatalogUiPolicyIntent,
    catalog_conditions: str,
    catalog_item_sys_id: str,
    policy_sys_id: str,
    update_name: str,
) -> str:
    return record_update(
        container_element(
            "catalog_ui_policy",
            bool_element("active", intent.active),
            "<applies_catalog>true</applies_catalog>",
            "<applies_req_item>true</applies_req_item>",
            "<applies_sc_task>false</applies_sc_task>",
            "<applies_target_record>false</applies_target_record>",
            "<applies_to>item</applies_to>",
            text_element("catalog_conditions", catalog_conditions),
            text_element(
                "catalog_item",
                catalog_item_sys_id,
                display_value=intent.catalog_item_name,
            ),
            bool_element("on_load", intent.on_load),
            text_element("order", str(intent.order)),
            bool_element("reverse_if_false", intent.reverse_if_false),
            "<run_scripts>false</run_scripts>",
            "<script_false/>",
            "<script_true/>",
            text_element("short_description", intent.policy_name),
            "<sys_class_name>catalog_ui_policy</sys_class_name>",
            text_element("sys_id", policy_sys_id),
            SYS_SCOPE_GLOBAL,
            text_element("sys_update_name", update_name),
            action="INSERT_OR_UPDATE",
        ),
        table="catalog_ui_policy",
    )


def _catalog_ui_policy_action_payload(
    *,
    intent: CatalogUiPolicyIntent,
    action: CatalogUiPolicyActionIntent,
    catalog_item_sys_id: str,
    policy_sys_id: str,
    variable_sys_id: str,
    update_name: str,
    sys_id: str,
) -> str:
    return record_update(
        container_element(
            "catalog_ui_policy_action",
            text_element(
                "catalog_item",
                catalog_item_sys_id,
                display_value=intent.catalog_item_name,
            ),
            text_element(
                "catalog_variable",
                f"IO:{variable_sys_id}",
                display_value=action.variable,
            ),
            bool_element("cleared", action.cleared),
            text_element("disabled", action.disabled),
            text_element("mandatory", action.mandatory),
            "<sys_class_name>catalog_ui_policy_action</sys_class_name>",
            text_element("sys_id", sys_id),
            SYS_SCOPE_GLOBAL,
            text_element("sys_update_name", update_name),
            text_element("ui_policy", policy_sys_id, display_value=intent.policy_name),
            text_element("variable", action.variable),
            text_element("visible", action.visible),
            action="INSERT_OR_UPDATE",
        ),
        table="catalog_ui_policy_action",
    )


def _action_suffix(action: CatalogUiPolicyActionIntent) -> str:
    labels: list[str] = []
    if action.mandatory != "ignore":
        labels.append("required" if action.mandatory == "true" else "not_required")
    if action.visible != "ignore":
        labels.append("visible" if action.visible == "true" else "hidden")
    if action.disabled != "ignore":
        labels.append("read_only" if action.disabled == "true" else "editable")
    if action.cleared:
        labels.append("cleared")
    return "_".join(labels) or "action"
