from __future__ import annotations

import hashlib
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from jedi_devproject.models import CandidateChange
from jedi_devproject.validation_helpers import bool_text, bool_value, slug
from jedi_devproject.xml_builder import (
    SYS_SCOPE_GLOBAL,
    bool_element,
    container_element,
    record_update,
    text_element,
)

UI_POLICY_FIELD_NON_JSON_DIAGNOSTIC = "UI Policy generation field contains non-JSON value"


class UiPolicyActionIntent(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    policy_name: str = ""
    target_table: str
    field: str
    mandatory: str = "ignore"
    visible: str = "ignore"
    disabled: str = "ignore"
    cleared: bool = False

    @field_validator("target_table", "field")
    @classmethod
    def require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned == "":
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("mandatory", "visible", "disabled")
    @classmethod
    def validate_tristate(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"true", "false", "ignore"}:
            raise ValueError("UI Policy action values must be true, false, or ignore")
        return cleaned


class UiPolicyIntent(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    target_table: str
    policy_name: str
    conditions: str
    reverse_if_false: bool
    run_scripts: bool = False
    active: bool = True
    on_load: bool = False
    order: int = 100
    description: str = ""
    view: str = ""
    script_true: str = ""
    script_false: str = ""
    actions: list[UiPolicyActionIntent]

    @field_validator("target_table", "policy_name", "conditions")
    @classmethod
    def require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned == "":
            raise ValueError("must not be empty")
        return cleaned

    @model_validator(mode="after")
    def validate_ui_policy_boundary(self) -> UiPolicyIntent:
        if self.run_scripts:
            raise ValueError("UI Policy run_scripts must be false")
        if self.script_true.strip() or self.script_false.strip():
            raise ValueError("UI Policy scripts are not supported")
        if not self.actions:
            raise ValueError("UI Policy handoff requires at least one action")
        _validate_safe_text(self.conditions, self.description)
        for action in self.actions:
            if action.target_table != self.target_table:
                raise ValueError("UI Policy action table must match policy table")
            if action.policy_name and action.policy_name != self.policy_name:
                raise ValueError("UI Policy action policy_name must match policy")
        return self


def ui_policy_customer_updates(
    *,
    changes: list[CandidateChange],
    remote_update_set_sys_id: str,
) -> list[dict[str, Any]]:
    intent = _ui_policy_intent(changes)
    policy_update_name = (
        f"sys_ui_policy_{intent.target_table}_"
        f"{slug(intent.policy_name, default='generated_ui_policy')}"
    )
    policy_sys_id = _stable_sys_id(policy_update_name)
    updates: list[dict[str, Any]] = [
        {
            "name": policy_update_name,
            "remote_update_set": remote_update_set_sys_id,
            "action": "INSERT_OR_UPDATE",
            "type": "UI Policy",
            "target_name": intent.policy_name,
            "payload": _ui_policy_payload(
                intent=intent,
                update_name=policy_update_name,
                sys_id=policy_sys_id,
            ),
            "application": "global",
        }
    ]
    for action in intent.actions:
        action_update_name = (
            f"sys_ui_policy_action_{intent.target_table}_"
            f"{slug(action.field, default='generated_ui_policy')}_"
            f"{_action_suffix(action)}"
        )
        updates.append(
            {
                "name": action_update_name,
                "remote_update_set": remote_update_set_sys_id,
                "action": "INSERT_OR_UPDATE",
                "type": "UI Policy Action",
                "target_name": f"{intent.policy_name}.{action.field}",
                "payload": _ui_policy_action_payload(
                    action=action,
                    policy_name=intent.policy_name,
                    policy_sys_id=policy_sys_id,
                    update_name=action_update_name,
                    sys_id=_stable_sys_id(action_update_name),
                ),
                "application": "global",
            }
        )
    return updates


def _ui_policy_intent(changes: list[CandidateChange]) -> UiPolicyIntent:
    unexpected_tables = sorted(
        {change.table for change in changes}
        - {"sys_ui_policy", "sys_ui_policy_action"}
    )
    if unexpected_tables:
        raise ValueError(
            "UI Policy handoff received unsupported tables: "
            f"{', '.join(unexpected_tables)}"
        )
    policy_changes = [change for change in changes if change.table == "sys_ui_policy"]
    if not policy_changes:
        raise ValueError("UI Policy handoff requires a sys_ui_policy change")
    if len(policy_changes) != 1:
        raise ValueError("UI Policy handoff requires exactly one sys_ui_policy change")
    policy_change = policy_changes[0]
    action_changes = [change for change in changes if change.table == "sys_ui_policy_action"]
    if not action_changes:
        raise ValueError("UI Policy handoff requires at least one sys_ui_policy_action change")
    if policy_change.operation != "insert":
        raise ValueError("UI Policy handoff supports policy insert only")
    policy_fields = dict(policy_change.fields)
    policy_name = _ui_policy_first_text(
        policy_fields.get("short_description"),
        policy_fields.get("policy_name"),
        policy_fields.get("name"),
    )
    target_table = _ui_policy_first_text(
        policy_fields.get("table"),
        policy_fields.get("target_table"),
    )
    actions = [
        _ui_policy_action_intent(
            change,
            policy_name=policy_name,
            policy_target_table=target_table,
        )
        for change in action_changes
    ]
    return UiPolicyIntent(
        target_table=target_table,
        policy_name=policy_name,
        conditions=_ui_policy_first_text(
            policy_fields.get("conditions"),
            policy_fields.get("condition"),
        ),
        reverse_if_false=bool_value(
            _ui_policy_first_text(policy_fields.get("reverse_if_false"))
        ),
        run_scripts=bool_value(_ui_policy_first_text(policy_fields.get("run_scripts"))),
        active=bool_value(_ui_policy_first_text(policy_fields.get("active")), default=True),
        on_load=bool_value(_ui_policy_first_text(policy_fields.get("on_load"))),
        order=_int_value(policy_fields.get("order"), default=100),
        description=_ui_policy_first_text(policy_fields.get("description")),
        view=_ui_policy_first_text(policy_fields.get("view")),
        script_true=_ui_policy_first_text(policy_fields.get("script_true")),
        script_false=_ui_policy_first_text(policy_fields.get("script_false")),
        actions=actions,
    )


def _ui_policy_action_intent(
    change: CandidateChange,
    *,
    policy_name: str,
    policy_target_table: str,
) -> UiPolicyActionIntent:
    if change.operation != "insert":
        raise ValueError("UI Policy handoff supports action insert only")
    fields = dict(change.fields)
    disabled_value = fields.get("disabled")
    if _ui_policy_first_text(disabled_value).strip().lower() in {"", "ignore"}:
        disabled_value = fields.get("read_only", disabled_value)
    return UiPolicyActionIntent(
        policy_name=_ui_policy_first_text(
            fields.get("policy_name"),
            fields.get("ui_policy_name"),
            policy_name,
        ),
        target_table=_ui_policy_first_text(
            fields.get("table"),
            fields.get("target_table"),
            policy_target_table,
        ),
        field=_ui_policy_first_text(fields.get("field"), fields.get("field_name")),
        mandatory=_tristate(fields.get("mandatory")),
        visible=_tristate(fields.get("visible")),
        disabled=_tristate(disabled_value),
        cleared=bool_value(
            _ui_policy_first_text(fields.get("cleared", fields.get("clear_value")))
        ),
    )


def _ui_policy_payload(*, intent: UiPolicyIntent, update_name: str, sys_id: str) -> str:
    return record_update(
        container_element(
            "sys_ui_policy",
            bool_element("active", intent.active),
            text_element("conditions", intent.conditions),
            text_element("description", intent.description),
            "<global>true</global>",
            "<inherit>false</inherit>",
            "<isolate_script>true</isolate_script>",
            bool_element("on_load", intent.on_load),
            text_element("order", str(intent.order)),
            bool_element("reverse_if_false", intent.reverse_if_false),
            "<run_scripts>false</run_scripts>",
            "<script_false/>",
            "<script_true/>",
            text_element("short_description", intent.policy_name),
            "<sys_class_name>sys_ui_policy</sys_class_name>",
            text_element("sys_id", sys_id),
            SYS_SCOPE_GLOBAL,
            text_element("sys_update_name", update_name),
            text_element("table", intent.target_table),
            "<ui_type>10</ui_type>",
            text_element("view", intent.view),
            action="INSERT_OR_UPDATE",
        )
    )


def _ui_policy_action_payload(
    *,
    action: UiPolicyActionIntent,
    policy_name: str,
    policy_sys_id: str,
    update_name: str,
    sys_id: str,
) -> str:
    return record_update(
        container_element(
            "sys_ui_policy_action",
            bool_element("cleared", action.cleared),
            text_element("disabled", action.disabled),
            text_element("field", action.field),
            text_element("mandatory", action.mandatory),
            "<sys_class_name>sys_ui_policy_action</sys_class_name>",
            text_element("sys_id", sys_id),
            SYS_SCOPE_GLOBAL,
            text_element("sys_update_name", update_name),
            text_element("table", action.target_table),
            text_element("ui_policy", policy_sys_id, display_value=policy_name),
            text_element("visible", action.visible),
            action="INSERT_OR_UPDATE",
        )
    )


FORBIDDEN_TEXT_TOKENS = [
    "script",
    "g_form",
    "document.",
    "window.",
    "GlideAjax",
    "http://",
    "https://",
    "credential",
    "password",
    "token",
    "api_key",
    "endpoint",
]


def _validate_safe_text(*values: str) -> None:
    text = " ".join(values).lower()
    for token in FORBIDDEN_TEXT_TOKENS:
        if token.lower() in text:
            raise ValueError(f"forbidden UI Policy token: {token}")


def _action_suffix(action: UiPolicyActionIntent) -> str:
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


def _stable_sys_id(value: str) -> str:
    return hashlib.md5(value.encode("utf-8"), usedforsecurity=False).hexdigest()


def _int_value(value: Any, *, default: int) -> int:
    try:
        return int(_ui_policy_first_text(value).strip())
    except ValueError:
        return default


def _tristate(value: Any) -> str:
    if isinstance(value, bool):
        return bool_text(value)
    text = _ui_policy_first_text(value, "ignore").strip().lower()
    if text in {"", "none", "leave alone"}:
        return "ignore"
    return text


def _ui_policy_first_text(*values: Any) -> str:
    for value in values:
        text = _ui_policy_field_text(value)
        if text:
            return text
    return ""


def _ui_policy_field_text(value: Any) -> str:
    if value is None:
        return ""
    if type(value) is str:
        return value
    if type(value) is bool or type(value) is int:
        return str(value)
    raise ValueError(UI_POLICY_FIELD_NON_JSON_DIAGNOSTIC)
