"""Deterministic change builders that derive catalog item and record producer candidate
changes solely from the normalized story intent, failing closed with
``ModelResponseError`` on any gap or unsafe request."""

from __future__ import annotations

from typing import Any

from jedi_devproject.catalog_client_script_generation import (
    CatalogClientScriptAction,
    render_catalog_client_script,
)
from jedi_devproject.catalog_item_generation import validated_reference_qualifier
from jedi_devproject.catalog_ui_policy_generation import catalog_ui_policy_condition_variables
from jedi_devproject.providers import ModelResponseError


def _catalog_item_changes_from_normalized_intent(
    intent: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not isinstance(intent, dict):
        raise ModelResponseError("catalog item candidate requires normalized intent")

    item_name = _required_intent_text(intent, "artifact_name", "catalog item name")
    item_short_description = _required_intent_text(
        intent,
        "catalog_item_short_description",
        "catalog item short description",
    )
    catalog = _required_intent_text(intent, "catalog_name", "catalog")
    category = _required_intent_text(intent, "category_name", "category")
    taxonomy = _required_intent_text(intent, "taxonomy_name", "taxonomy")
    topic = _required_intent_text(intent, "employee_center_topic", "Employee Center topic")
    raw_variables = intent.get("catalog_variables")
    if not isinstance(raw_variables, list) or not raw_variables:
        raise ModelResponseError("catalog item candidate requires normalized catalog variables")
    if intent.get("catalog_variable_set_creation"):
        raise ModelResponseError(
            "catalog item candidate must not create variable sets; "
            "attach existing variable sets only"
        )
    variable_set_names = _intent_variable_set_names(intent.get("catalog_variable_sets"))
    variable_groups = _intent_variable_groups(intent.get("catalog_variable_groups"))
    ui_policy_rules = _intent_catalog_ui_policy_rules(intent.get("catalog_ui_policies"))
    client_scripts = _intent_catalog_client_scripts(intent.get("catalog_client_scripts"))
    fulfillment_flow_name = _intent_fulfillment_flow_name(intent)

    changes: list[dict[str, Any]] = [
        {
            "table": "sc_cat_item",
            "operation": "insert",
            "fields": {
                "name": item_name,
                "short_description": item_short_description,
                "description": item_short_description,
                "catalog": catalog,
                "category": category,
                "taxonomy": taxonomy,
                "employee_center_topic": topic,
            },
            "sys_id": None,
            "rationale": "Create the standard catalog item from the normalized story intent.",
        }
    ]
    variable_names: list[str] = []
    for index, raw_variable in enumerate(raw_variables, start=1):
        if not isinstance(raw_variable, dict):
            raise ModelResponseError("catalog item variable intent must be an object")
        variable_name = _required_intent_text(raw_variable, "name", "catalog variable name")
        variable_names.append(variable_name)
        variable_type = _required_intent_text(
            raw_variable,
            "type",
            f"catalog variable type for {variable_name}",
        )
        fields: dict[str, Any] = {
            "name": variable_name,
            "question_text": _required_intent_text(
                raw_variable,
                "label",
                f"catalog variable label for {variable_name}",
            ),
            "type": variable_type,
            "mandatory": bool(raw_variable.get("mandatory", False)),
            "order": _optional_intent_order(raw_variable.get("order"), default=index * 100),
        }
        reference_table = _optional_intent_text(raw_variable.get("reference_table"))
        if variable_type == "reference":
            if reference_table is None:
                raise ModelResponseError(
                    f"reference catalog variable {variable_name} requires reference_table"
                )
            fields["reference"] = reference_table
        reference_qualifier = _optional_intent_text(raw_variable.get("reference_qualifier"))
        if reference_qualifier is not None:
            try:
                fields["reference_qualifier"] = validated_reference_qualifier(
                    reference_qualifier
                )
            except ValueError as error:
                raise ModelResponseError(
                    f"catalog variable {variable_name} reference qualifier rejected: {error}"
                ) from error
        default_value = _optional_intent_text(raw_variable.get("default_value"))
        if default_value is not None:
            fields["default_value"] = default_value
        help_text = _optional_intent_text(raw_variable.get("help_text"))
        if help_text is not None:
            fields["help_text"] = help_text
        changes.append(
            {
                "table": "item_option_new",
                "operation": "insert",
                "fields": fields,
                "sys_id": None,
                "rationale": (
                    f"Create the {variable_name} variable from the normalized story intent."
                ),
            }
        )

    declared_names = set(variable_names)
    for group in variable_groups:
        for member in group["variables"]:
            if member not in declared_names:
                raise ModelResponseError(
                    f"catalog variable group {group['title']} references "
                    f"unknown variable: {member}"
                )
    if variable_set_names:
        changes[0]["fields"]["variable_sets"] = variable_set_names
    if variable_groups:
        changes[0]["fields"]["variable_groups"] = variable_groups
    if fulfillment_flow_name is not None:
        changes[0]["fields"]["fulfillment_flow"] = fulfillment_flow_name

    changes.extend(
        [
            {
                "table": "sc_cat_item_category",
                "operation": "insert",
                "fields": {"catalog": catalog, "category": category},
                "sys_id": None,
                "rationale": "Place the catalog item in the requested catalog category.",
            },
            {
                "table": "m2m_connected_content",
                "operation": "insert",
                "fields": {
                    "taxonomy": taxonomy,
                    "topic": topic,
                    "employee_center_topic": topic,
                },
                "sys_id": None,
                "rationale": "Associate the catalog item with the requested Employee Center topic.",
            },
        ]
    )
    changes.extend(
        _catalog_ui_policy_changes(
            rules=ui_policy_rules,
            item_name=item_name,
            declared_names=declared_names,
        )
    )
    changes.extend(
        _catalog_client_script_changes(
            scripts=client_scripts,
            item_name=item_name,
            declared_names=declared_names,
        )
    )
    return changes


def _record_producer_changes_from_normalized_intent(
    intent: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Build deterministic record producer changes from the typed normalized intent.

    Mirrors the catalog item reconciliation: the model response is replaced by
    changes derived solely from the normalized story intent, and every gap or
    unsafe request fails closed with ``ModelResponseError``. The producer is
    always script-free; script-based mapping routes to manual review upstream
    and is rejected again here.
    """
    if not isinstance(intent, dict):
        raise ModelResponseError("record producer candidate requires normalized intent")
    if _optional_intent_text(intent.get("record_producer_script")) is not None:
        raise ModelResponseError(
            "record producer candidate must not carry a producer script; "
            "script-based mapping routes to manual review"
        )
    producer = intent.get("record_producer")
    if not isinstance(producer, dict):
        raise ModelResponseError(
            "record producer candidate requires normalized record producer intent"
        )
    name = _required_producer_intent_text(producer, "name", "record producer name")
    short_description = _required_producer_intent_text(
        producer, "short_description", "short description"
    )
    target_table = _required_producer_intent_text(producer, "target_table", "target table")
    catalog = _required_producer_intent_text(producer, "catalog", "catalog")
    category = _required_producer_intent_text(producer, "category", "category")
    raw_variables = producer.get("variables")
    if not isinstance(raw_variables, list) or not raw_variables:
        raise ModelResponseError("record producer candidate requires normalized variables")

    changes: list[dict[str, Any]] = [
        {
            "table": "sc_cat_item_producer",
            "operation": "insert",
            "fields": {
                "name": name,
                "short_description": short_description,
                "table_name": target_table,
                "catalog": catalog,
                "category": category,
            },
            "sys_id": None,
            "rationale": "Create the record producer from the normalized story intent.",
        }
    ]
    mapped_fields: set[str] = set()
    for index, raw_variable in enumerate(raw_variables, start=1):
        if not isinstance(raw_variable, dict):
            raise ModelResponseError("record producer variable intent must be an object")
        variable_name = _required_producer_intent_text(
            raw_variable, "name", "record producer variable name"
        )
        variable_type = _required_producer_intent_text(
            raw_variable,
            "type",
            f"record producer variable type for {variable_name}",
        )
        mapped_field = _optional_intent_text(raw_variable.get("field"))
        if mapped_field is None:
            raise ModelResponseError(
                f"record producer variable {variable_name} requires a target field mapping"
            )
        if mapped_field in mapped_fields:
            raise ModelResponseError(
                f"record producer maps target field {mapped_field} more than once"
            )
        mapped_fields.add(mapped_field)
        fields: dict[str, Any] = {
            "name": variable_name,
            "question_text": _required_producer_intent_text(
                raw_variable,
                "label",
                f"record producer variable label for {variable_name}",
            ),
            "type": variable_type,
            "mandatory": bool(raw_variable.get("mandatory", False)),
            "order": _optional_intent_order(raw_variable.get("order"), default=index * 100),
            "field": mapped_field,
            "map_to_field": True,
        }
        reference_table = _optional_intent_text(raw_variable.get("reference_table"))
        if variable_type == "reference":
            if reference_table is None:
                raise ModelResponseError(
                    f"reference record producer variable {variable_name} "
                    "requires reference_table"
                )
            fields["reference"] = reference_table
        reference_qualifier = _optional_intent_text(raw_variable.get("reference_qualifier"))
        if reference_qualifier is not None:
            try:
                fields["reference_qualifier"] = validated_reference_qualifier(
                    reference_qualifier
                )
            except ValueError as error:
                raise ModelResponseError(
                    f"record producer variable {variable_name} reference qualifier "
                    f"rejected: {error}"
                ) from error
        default_value = _optional_intent_text(raw_variable.get("default_value"))
        if default_value is not None:
            fields["default_value"] = default_value
        help_text = _optional_intent_text(raw_variable.get("help_text"))
        if help_text is not None:
            fields["help_text"] = help_text
        changes.append(
            {
                "table": "item_option_new",
                "operation": "insert",
                "fields": fields,
                "sys_id": None,
                "rationale": (
                    f"Create the {variable_name} variable mapped to {mapped_field} "
                    "from the normalized story intent."
                ),
            }
        )
    changes.append(
        {
            "table": "sc_cat_item_category",
            "operation": "insert",
            "fields": {"catalog": catalog, "category": category},
            "sys_id": None,
            "rationale": "Place the record producer in the requested catalog category.",
        }
    )
    return changes


def _required_producer_intent_text(intent: dict[str, Any], key: str, label: str) -> str:
    value = _optional_intent_text(intent.get(key))
    if value is None:
        raise ModelResponseError(f"record producer candidate missing normalized {label}")
    return value


def _catalog_ui_policy_changes(
    *,
    rules: list[dict[str, Any]],
    item_name: str,
    declared_names: set[str],
) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for index, rule in enumerate(rules, start=1):
        title = str(rule["title"])
        try:
            condition_variables = catalog_ui_policy_condition_variables(str(rule["condition"]))
        except ValueError as error:
            raise ModelResponseError(
                f"catalog variable rule {title} condition rejected: {error}"
            ) from error
        actions = list(rule["actions"])
        referenced = [
            *condition_variables,
            *[str(action["variable"]) for action in actions],
        ]
        for member in referenced:
            if member not in declared_names:
                raise ModelResponseError(
                    f"catalog variable rule {title} references unknown variable: {member}"
                )
        changes.append(
            {
                "table": "catalog_ui_policy",
                "operation": "insert",
                "fields": {
                    "short_description": title,
                    "catalog_item": item_name,
                    "catalog_conditions": str(rule["condition"]),
                    "reverse_if_false": bool(rule["reverse_if_false"]),
                    "on_load": True,
                    "order": index * 100,
                },
                "sys_id": None,
                "rationale": (
                    f"Apply the {title} variable behavior rule from the normalized story intent."
                ),
            }
        )
        for action in actions:
            changes.append(
                {
                    "table": "catalog_ui_policy_action",
                    "operation": "insert",
                    "fields": {
                        "ui_policy": title,
                        "catalog_item": item_name,
                        "variable": str(action["variable"]),
                        "visible": str(action["visible"]),
                        "mandatory": str(action["mandatory"]),
                        "disabled": str(action["disabled"]),
                        "cleared": bool(action["cleared"]),
                    },
                    "sys_id": None,
                    "rationale": (
                        f"Apply the {title} behavior to the {action['variable']} variable."
                    ),
                }
            )
    return changes


def _catalog_client_script_changes(
    *,
    scripts: list[dict[str, Any]],
    item_name: str,
    declared_names: set[str],
) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for script in scripts:
        name = str(script["name"])
        watched_variable = str(script["variable"])
        actions: list[CatalogClientScriptAction] = []
        for action in script["actions"]:
            try:
                actions.append(CatalogClientScriptAction.model_validate(action))
            except ValueError as error:
                raise ModelResponseError(
                    f"catalog client script {name} action rejected: {error}"
                ) from error
        referenced = [
            *([watched_variable] if watched_variable else []),
            *[action.variable for action in actions],
        ]
        for member in referenced:
            if member not in declared_names:
                raise ModelResponseError(
                    f"catalog client script {name} references unknown variable: {member}"
                )
        try:
            script_body = render_catalog_client_script(
                script_type=str(script["script_type"]),
                actions=actions,
                variable_name=watched_variable,
            )
        except ValueError as error:
            raise ModelResponseError(
                f"catalog client script {name} rejected: {error}"
            ) from error
        fields_written = list(dict.fromkeys(action.variable for action in actions))
        changes.append(
            {
                "table": "catalog_script_client",
                "operation": "insert",
                "fields": {
                    "cat_item": item_name,
                    "name": name,
                    "type": str(script["script_type"]),
                    "field": watched_variable,
                    "script": script_body,
                    "fields_written": fields_written,
                },
                "sys_id": None,
                "rationale": (
                    f"Create the {name} catalog client script from the normalized story intent."
                ),
            }
        )
    return changes


def _intent_variable_set_names(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ModelResponseError("catalog variable sets must be a list of set names")
    names = [str(item).strip() for item in value]
    if any(name == "" for name in names):
        raise ModelResponseError("catalog variable set names must not be empty")
    return names


def _intent_variable_groups(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ModelResponseError("catalog variable groups must be a list")
    groups: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ModelResponseError("catalog variable group intent must be an object")
        title = _optional_intent_text(item.get("title"))
        if title is None:
            raise ModelResponseError("catalog variable group intent missing title")
        raw_members = item.get("variables")
        if not isinstance(raw_members, list) or not raw_members:
            raise ModelResponseError(
                f"catalog variable group {title} requires member variables"
            )
        members = [str(member).strip() for member in raw_members]
        if any(member == "" for member in members):
            raise ModelResponseError(
                f"catalog variable group {title} requires member variables"
            )
        groups.append({"title": title, "variables": members})
    return groups


_CATALOG_UI_POLICY_TRISTATES = frozenset({"true", "false", "ignore"})


def _intent_catalog_ui_policy_rules(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ModelResponseError("catalog variable rules must be a list")
    rules: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ModelResponseError("catalog variable rule intent must be an object")
        title = _optional_intent_text(item.get("title"))
        if title is None:
            raise ModelResponseError("catalog variable rule intent missing title")
        condition = _optional_intent_text(item.get("condition"))
        if condition is None:
            raise ModelResponseError(f"catalog variable rule {title} missing condition")
        raw_actions = item.get("actions")
        if not isinstance(raw_actions, list) or not raw_actions:
            raise ModelResponseError(f"catalog variable rule {title} requires actions")
        actions: list[dict[str, Any]] = []
        for raw_action in raw_actions:
            if not isinstance(raw_action, dict):
                raise ModelResponseError(
                    f"catalog variable rule {title} action must be an object"
                )
            variable = _optional_intent_text(raw_action.get("variable"))
            if variable is None:
                raise ModelResponseError(
                    f"catalog variable rule {title} action missing variable"
                )
            action = {
                "variable": variable,
                "visible": str(raw_action.get("visible") or "ignore").strip().lower(),
                "mandatory": str(raw_action.get("mandatory") or "ignore").strip().lower(),
                "disabled": str(raw_action.get("disabled") or "ignore").strip().lower(),
                "cleared": bool(raw_action.get("cleared", False)),
            }
            for attribute in ("visible", "mandatory", "disabled"):
                if action[attribute] not in _CATALOG_UI_POLICY_TRISTATES:
                    raise ModelResponseError(
                        f"catalog variable rule {title} action {attribute} must be "
                        "true, false, or ignore"
                    )
            actions.append(action)
        rules.append(
            {
                "title": title,
                "condition": condition,
                "reverse_if_false": bool(item.get("reverse_if_false", True)),
                "actions": actions,
            }
        )
    return rules


def _intent_catalog_client_scripts(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ModelResponseError("catalog client scripts must be a list")
    scripts: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ModelResponseError("catalog client script intent must be an object")
        name = _optional_intent_text(item.get("name"))
        if name is None:
            raise ModelResponseError("catalog client script intent missing name")
        script_type = _optional_intent_text(item.get("script_type"))
        if script_type is None:
            raise ModelResponseError(f"catalog client script {name} missing script type")
        raw_actions = item.get("actions")
        if not isinstance(raw_actions, list) or not raw_actions:
            raise ModelResponseError(f"catalog client script {name} requires actions")
        actions: list[dict[str, Any]] = []
        for raw_action in raw_actions:
            if not isinstance(raw_action, dict):
                raise ModelResponseError(
                    f"catalog client script {name} action must be an object"
                )
            actions.append(
                {
                    "kind": str(raw_action.get("kind") or ""),
                    "variable": str(raw_action.get("variable") or ""),
                    "value": str(raw_action.get("value") or ""),
                }
            )
        scripts.append(
            {
                "name": name,
                "script_type": script_type,
                "variable": _optional_intent_text(item.get("variable")) or "",
                "actions": actions,
            }
        )
    return scripts


def _intent_fulfillment_flow_name(intent: dict[str, Any]) -> str | None:
    """Carry the attach-existing fulfillment flow name; fail closed otherwise.

    Upstream routing already refuses flow creation/modification and surfaces a
    nameless attachment request as a missing detail; this re-checks both so the
    candidate path stays fail-closed even if a packet bypasses routing.
    """
    attachment_requested = bool(intent.get("fulfillment_flow_attachment_requested"))
    if (
        _optional_intent_text(intent.get("fulfillment_flow")) is not None
        and not attachment_requested
    ):
        raise ModelResponseError(
            "catalog item candidate must not create or modify fulfillment flows; "
            "attach an existing flow only"
        )
    name = _optional_intent_text(intent.get("fulfillment_flow_name"))
    if attachment_requested and name is None:
        raise ModelResponseError(
            "catalog item candidate fulfillment flow attachment requires a flow name"
        )
    return name


def _required_intent_text(intent: dict[str, Any], key: str, label: str) -> str:
    value = _optional_intent_text(intent.get(key))
    if value is None:
        raise ModelResponseError(f"catalog item candidate missing normalized {label}")
    return value


def _optional_intent_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_intent_order(value: Any, *, default: int) -> int:
    if value is None:
        return default
    try:
        order = int(value)
    except (TypeError, ValueError):
        return default
    return order if order > 0 else default
