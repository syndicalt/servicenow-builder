from __future__ import annotations

from typing import Any

from jedi_devproject.business_rule_generation import business_rule_customer_updates
from jedi_devproject.catalog_item_generation import catalog_item_customer_updates
from jedi_devproject.client_script_generation import client_script_customer_updates
from jedi_devproject.models import CandidateChange
from jedi_devproject.script_include_generation import script_include_customer_updates
from jedi_devproject.ui_policy_generation import ui_policy_customer_updates


class CatalogReferenceClient:
    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        _ = (lookup, fields, limit)
        if table == "sc_catalog":
            return [{"sys_id": "catalog-sys-id", "title": "Service Catalog", "active": "true"}]
        if table == "sc_category":
            return [
                {
                    "sys_id": "category-sys-id",
                    "title": "Services",
                    "active": "true",
                    "sc_catalog": {
                        "value": "catalog-sys-id",
                        "display_value": "Service Catalog",
                    },
                }
            ]
        if table == "taxonomy":
            return [{"sys_id": "taxonomy-sys-id", "name": "Employee", "active": "true"}]
        if table == "topic":
            return [
                {
                    "sys_id": "topic-sys-id",
                    "name": "Access issues",
                    "topic_path": "Technology services / Software / Access issues",
                    "active": "true",
                    "taxonomy": {"value": "taxonomy-sys-id", "display_value": "Employee"},
                }
            ]
        if table == "taxonomy_content_configuration":
            return [{"sys_id": "content-type-sys-id", "name": "Catalog Item", "active": "true"}]
        return []


def test_reference_builders_still_render_structured_candidate_xml_shapes() -> None:
    business_rule_update = business_rule_customer_updates(
        changes=[
            CandidateChange(
                table="sys_script",
                operation="insert",
                fields={
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
                },
            )
        ],
        remote_update_set_sys_id="remote-sys-id",
    )[0]
    client_script_update = client_script_customer_updates(
        changes=[
            CandidateChange(
                table="sys_script_client",
                operation="insert",
                fields={
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
                },
            )
        ],
        remote_update_set_sys_id="remote-sys-id",
    )[0]
    script_include_update = script_include_customer_updates(
        changes=[
            CandidateChange(
                table="sys_script_include",
                operation="insert",
                fields={
                    "name": "JediIncidentUtils",
                    "api_name": "global.JediIncidentUtils",
                    "scope": "global",
                    "client_callable": False,
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
                },
            )
        ],
        remote_update_set_sys_id="remote-sys-id",
    )[0]
    ui_policy_updates = ui_policy_customer_updates(
        changes=[
            CandidateChange(
                table="sys_ui_policy",
                operation="insert",
                fields={
                    "short_description": "JEDI Incident Assignment Group Required",
                    "table": "incident",
                    "conditions": "category=software",
                    "reverse_if_false": True,
                    "run_scripts": False,
                },
            ),
            CandidateChange(
                table="sys_ui_policy_action",
                operation="insert",
                fields={
                    "policy_name": "JEDI Incident Assignment Group Required",
                    "table": "incident",
                    "field": "assignment_group",
                    "mandatory": "true",
                    "visible": "true",
                    "disabled": "ignore",
                },
            ),
        ],
        remote_update_set_sys_id="remote-sys-id",
    )
    catalog_updates = catalog_item_customer_updates(
        client=CatalogReferenceClient(),
        changes=[
            CandidateChange(
                table="sc_cat_item",
                operation="insert",
                fields={
                    "name": "Request Temporary Badge",
                    "short_description": "Request a temporary access badge for a visitor.",
                    "catalog": "Service Catalog",
                    "category": "Services",
                    "taxonomy": "Employee",
                    "employee_center_topic": "Technology services / Software / Access issues",
                },
            ),
            CandidateChange(
                table="item_option_new",
                operation="insert",
                fields={
                    "name": "visitor_name",
                    "question_text": "Visitor name",
                    "type": "single_line_text",
                    "mandatory": True,
                    "order": 100,
                },
            ),
            CandidateChange(
                table="sc_cat_item_category",
                operation="insert",
                fields={"catalog": "Service Catalog", "category": "Services"},
            ),
            CandidateChange(
                table="m2m_connected_content",
                operation="insert",
                fields={
                    "taxonomy": "Employee",
                    "topic": "Technology services / Software / Access issues",
                },
            ),
        ],
        remote_update_set_sys_id="remote-sys-id",
    )

    assert business_rule_update["type"] == "Business Rule"
    assert "<sys_script action=\"INSERT_OR_UPDATE\">" in business_rule_update["payload"]
    assert client_script_update["type"] == "Client Script"
    assert "<sys_script_client action=\"INSERT_OR_UPDATE\">" in client_script_update["payload"]
    assert script_include_update["type"] == "Script Include"
    assert "<sys_script_include action=\"INSERT_OR_UPDATE\">" in script_include_update["payload"]
    assert [update["type"] for update in ui_policy_updates] == [
        "UI Policy",
        "UI Policy Action",
    ]
    assert len(catalog_updates) == 4
    assert {update["type"] for update in catalog_updates} == {
        "Catalog Item",
        "Catalog Variable",
        "Catalog Item Category",
        "Connected Content",
    }
