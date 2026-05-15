from __future__ import annotations

import pytest

from jedi_devproject.business_rule_generation import business_rule_customer_updates
from jedi_devproject.client_script_generation import client_script_customer_updates
from jedi_devproject.models import CandidateChange
from jedi_devproject.script_include_generation import script_include_customer_updates


def _business_rule_change(**field_overrides: object) -> CandidateChange:
    fields: dict[str, object] = {
        "name": "JEDI Incident Priority Note",
        "collection": "incident",
        "when": "before",
        "action_update": True,
        "filter_condition": "priority changes to 1",
        "script": (
            "if (current.priority.changesTo('1')) {\n"
            "    current.work_notes = 'Priority escalated by automation.';\n"
            "}"
        ),
        "fields_read": ["priority"],
        "fields_written": ["work_notes"],
    }
    fields.update(field_overrides)
    return CandidateChange(
        table="sys_script",
        operation="insert",
        fields=fields,
        rationale="Add the requested table-local Business Rule.",
    )


def _client_script_change(**field_overrides: object) -> CandidateChange:
    fields: dict[str, object] = {
        "name": "JEDI Incident Category CI Message",
        "table": "incident",
        "type": "onChange",
        "field": "category",
        "script": (
            "function onChange(control, oldValue, newValue, isLoading) {\n"
            "    if (isLoading || newValue !== 'software') {\n"
            "        return;\n"
            "    }\n"
            "    g_form.addInfoMessage('Confirm the CI before saving.');\n"
            "}"
        ),
        "fields_read": ["category"],
        "fields_written": [],
        "messages_shown": ["Confirm the CI before saving."],
    }
    fields.update(field_overrides)
    return CandidateChange(
        table="sys_script_client",
        operation="insert",
        fields=fields,
        rationale="Add the requested table-local Client Script.",
    )


def _script_include_change(**field_overrides: object) -> CandidateChange:
    fields: dict[str, object] = {
        "name": "JediIncidentUtils",
        "api_name": "global.JediIncidentUtils",
        "scope": "global",
        "client_callable": False,
        "active": True,
        "description": "Utility helpers for Incident automation.",
        "script": (
            "var JediIncidentUtils = Class.create();\n"
            "JediIncidentUtils.prototype = {\n"
            "    initialize: function() {},\n"
            "    normalizeCategory: function(category) {\n"
            "        return String(category || '').toLowerCase();\n"
            "    },\n"
            "    type: 'JediIncidentUtils'\n"
            "};"
        ),
        "public_methods": ["normalizeCategory(category)"],
        "tables_read": [],
        "tables_written": [],
        "fields_read": [],
        "fields_written": [],
    }
    fields.update(field_overrides)
    return CandidateChange(
        table="sys_script_include",
        operation="insert",
        fields=fields,
        rationale="Add the requested server-side utility Script Include.",
    )


def test_business_rule_validator_rejects_undeclared_set_value_write() -> None:
    change = _business_rule_change(
        script=(
            "if (current.priority.changesTo('1')) {\n"
            "    current.setValue('impact', '1');\n"
            "}"
        )
    )

    with pytest.raises(ValueError, match="Business Rule writes undeclared field: impact"):
        business_rule_customer_updates(
            changes=[change],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_client_script_validator_rejects_undeclared_clear_value_write() -> None:
    change = _client_script_change(
        script=(
            "function onChange(control, oldValue, newValue, isLoading) {\n"
            "    if (isLoading) {\n"
            "        return;\n"
            "    }\n"
            "    g_form.clearValue('assignment_group');\n"
            "}"
        )
    )

    with pytest.raises(ValueError, match="Client Script writes undeclared field: assignment_group"):
        client_script_customer_updates(
            changes=[change],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_script_include_validator_rejects_non_global_scope_until_scoped_xml_is_supported() -> None:
    change = _script_include_change(
        api_name="x_jedi_app.JediIncidentUtils",
        scope="x_jedi_app",
    )

    with pytest.raises(ValueError, match="Script Include scope must be global"):
        script_include_customer_updates(
            changes=[change],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_script_include_validator_requires_public_methods() -> None:
    change = _script_include_change(public_methods=[])

    with pytest.raises(
        ValueError,
        match="Script Include public_methods must name at least one method",
    ):
        script_include_customer_updates(
            changes=[change],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_script_include_validator_rejects_declared_writes_for_utility_only_profile() -> None:
    change = _script_include_change(tables_written=["incident"], fields_written=["category"])

    with pytest.raises(ValueError, match="Script Include writes are not supported"):
        script_include_customer_updates(
            changes=[change],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )
