from __future__ import annotations

import hashlib
import re
from html import escape
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from jedi_devproject.models import CandidateChange


class UiPolicyActionIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
    model_config = ConfigDict(extra="forbid")

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
    policy_update_name = f"sys_ui_policy_{intent.target_table}_{_slug(intent.policy_name)}"
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
            f"sys_ui_policy_action_{intent.target_table}_{_slug(action.field)}_"
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
    policy_name = str(
        policy_fields.get("short_description")
        or policy_fields.get("policy_name")
        or policy_fields.get("name")
        or ""
    )
    target_table = str(policy_fields.get("table") or policy_fields.get("target_table") or "")
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
        conditions=str(policy_fields.get("conditions") or policy_fields.get("condition") or ""),
        reverse_if_false=_bool_value(policy_fields.get("reverse_if_false")),
        run_scripts=_bool_value(policy_fields.get("run_scripts")),
        active=_bool_value(policy_fields.get("active"), default=True),
        on_load=_bool_value(policy_fields.get("on_load")),
        order=_int_value(policy_fields.get("order"), default=100),
        description=str(policy_fields.get("description") or ""),
        view=str(policy_fields.get("view") or ""),
        script_true=str(policy_fields.get("script_true") or ""),
        script_false=str(policy_fields.get("script_false") or ""),
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
    if str(disabled_value if disabled_value is not None else "").strip().lower() in {"", "ignore"}:
        disabled_value = fields.get("read_only", disabled_value)
    return UiPolicyActionIntent(
        policy_name=str(fields.get("policy_name") or fields.get("ui_policy_name") or policy_name),
        target_table=str(fields.get("table") or fields.get("target_table") or policy_target_table),
        field=str(fields.get("field") or fields.get("field_name") or ""),
        mandatory=_tristate(fields.get("mandatory")),
        visible=_tristate(fields.get("visible")),
        disabled=_tristate(disabled_value),
        cleared=_bool_value(fields.get("cleared", fields.get("clear_value"))),
    )


def _ui_policy_payload(*, intent: UiPolicyIntent, update_name: str, sys_id: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<record_update>"
        '<sys_ui_policy action="INSERT_OR_UPDATE">'
        f"<active>{_bool_text(intent.active)}</active>"
        f"<conditions>{escape(intent.conditions)}</conditions>"
        f"<description>{escape(intent.description)}</description>"
        "<global>true</global>"
        "<inherit>false</inherit>"
        "<isolate_script>true</isolate_script>"
        f"<on_load>{_bool_text(intent.on_load)}</on_load>"
        f"<order>{intent.order}</order>"
        f"<reverse_if_false>{_bool_text(intent.reverse_if_false)}</reverse_if_false>"
        "<run_scripts>false</run_scripts>"
        "<script_false/>"
        "<script_true/>"
        f"<short_description>{escape(intent.policy_name)}</short_description>"
        "<sys_class_name>sys_ui_policy</sys_class_name>"
        f"<sys_id>{escape(sys_id)}</sys_id>"
        '<sys_scope display_value="Global">global</sys_scope>'
        f"<sys_update_name>{escape(update_name)}</sys_update_name>"
        f"<table>{escape(intent.target_table)}</table>"
        "<ui_type>10</ui_type>"
        f"<view>{escape(intent.view)}</view>"
        "</sys_ui_policy>"
        "</record_update>"
    )


def _ui_policy_action_payload(
    *,
    action: UiPolicyActionIntent,
    policy_name: str,
    policy_sys_id: str,
    update_name: str,
    sys_id: str,
) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<record_update>"
        '<sys_ui_policy_action action="INSERT_OR_UPDATE">'
        f"<cleared>{_bool_text(action.cleared)}</cleared>"
        f"<disabled>{escape(action.disabled)}</disabled>"
        f"<field>{escape(action.field)}</field>"
        f"<mandatory>{escape(action.mandatory)}</mandatory>"
        "<sys_class_name>sys_ui_policy_action</sys_class_name>"
        f"<sys_id>{escape(sys_id)}</sys_id>"
        '<sys_scope display_value="Global">global</sys_scope>'
        f"<sys_update_name>{escape(update_name)}</sys_update_name>"
        f"<table>{escape(action.target_table)}</table>"
        f'<ui_policy display_value="{escape(policy_name)}">{escape(policy_sys_id)}</ui_policy>'
        f"<visible>{escape(action.visible)}</visible>"
        "</sys_ui_policy_action>"
        "</record_update>"
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


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower()).strip("_")
    return cleaned or "generated_ui_policy"


def _stable_sys_id(value: str) -> str:
    return hashlib.md5(value.encode("utf-8"), usedforsecurity=False).hexdigest()


def _bool_value(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes"}


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _int_value(value: Any, *, default: int) -> int:
    try:
        return int(str(value).strip())
    except ValueError:
        return default


def _tristate(value: Any) -> str:
    if isinstance(value, bool):
        return _bool_text(value)
    text = str(value if value is not None else "ignore").strip().lower()
    if text in {"", "none", "leave alone"}:
        return "ignore"
    return text
