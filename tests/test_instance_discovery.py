from typing import Any

from jedi_devproject.instance_discovery import (
    DiscoveredField,
    DiscoveredFormElement,
    DiscoveredFormSection,
    InstanceDiscoveryContext,
    ServiceNowSurfaceContextBundle,
    discover_dictionary_form_context,
    discover_servicenow_surface_context,
)


def test_instance_discovery_context_records_table_fields_and_form_anchor() -> None:
    context = InstanceDiscoveryContext(
        target_table="incident",
        table_label="Incident",
        table_exists=True,
        supports_custom_fields=True,
        fields=[
            DiscoveredField(
                element="description",
                column_label="Description",
                internal_type="string",
                max_length=4000,
                inherited=False,
            )
        ],
        form_sections=[
            DiscoveredFormSection(
                sys_id="incident-main-section",
                name="incident",
                caption="",
                view_name="Default view",
                elements=[
                    DiscoveredFormElement(
                        sys_id="description-element",
                        element="description",
                        position=2,
                    )
                ],
            )
        ],
        acl_indicators=[],
        evidence=["sys_db_object:incident", "sys_dictionary:incident.description"],
    )

    assert context.anchor_exists("description")
    assert not context.field_exists("u_antics")
    assert context.primary_section().sys_id == "incident-main-section"


class FakeDiscoveryClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        self.calls.append({"table": table, "lookup": lookup, "fields": fields, "limit": limit})
        if table == "sys_db_object" and lookup == {"name": "incident"}:
            return [{"name": "incident", "label": "Incident", "is_extendable": "true"}]
        if table == "sys_db_object" and lookup == {"name": "sc_cat_item"}:
            return [{"name": "sc_cat_item", "label": "Catalog Item", "is_extendable": "true"}]
        if table == "sys_dictionary" and lookup == {"name": "incident"}:
            return [
                {
                    "element": "description",
                    "column_label": "Description",
                    "internal_type": "string",
                    "max_length": "4000",
                }
            ]
        if table == "sys_dictionary" and lookup == {"name": "sc_cat_item"}:
            return [
                {
                    "element": "name",
                    "column_label": "Name",
                    "internal_type": "translated_text",
                    "max_length": "255",
                }
            ]
        if table == "sys_ui_section" and lookup == {"name": "incident"}:
            return [
                {
                    "sys_id": "incident-main-section",
                    "name": "incident",
                    "caption": "",
                    "view": {"display_value": "Default view", "value": "default"},
                }
            ]
        if table == "sys_ui_section" and lookup == {"name": "sc_cat_item"}:
            return []
        if table == "sys_ui_element" and lookup == {
            "name": "incident",
            "sys_ui_section": "incident-main-section",
        }:
            return [{"sys_id": "description-element", "element": "description", "position": "2"}]
        if table == "sys_security_acl" and lookup == {"name": "sc_cat_item"}:
            return []
        if table == "sys_security_acl" and lookup == {"name": "incident"}:
            return []
        if table == "sys_script" and lookup == {"collection": "incident"}:
            return [
                {
                    "sys_id": "business-rule-sys-id",
                    "name": "Incident State Guard",
                    "active": "true",
                    "when": "before",
                    "script": "var token = 'secret-value'; gs.info(token);",
                }
            ]
        if table == "sys_script_client" and lookup == {"table": "incident"}:
            return [
                {
                    "sys_id": "client-script-sys-id",
                    "name": "Incident Client Guard",
                    "active": "true",
                    "type": "onChange",
                    "script": "g_form.setValue('u_token', 'secret-value');",
                }
            ]
        if table == "sys_ui_policy" and lookup == {"table": "incident"}:
            return [
                {
                    "sys_id": "ui-policy-sys-id",
                    "short_description": "Make field visible",
                    "active": "true",
                }
            ]
        if table == "sys_hub_flow" and lookup == {}:
            return [{"sys_id": "flow-sys-id", "name": "Incident Triage", "active": "true"}]
        if table == "sys_hub_trigger_instance" and lookup == {"flow": "flow-sys-id"}:
            return [
                {
                    "sys_id": "trigger-sys-id",
                    "name": "Incident record trigger",
                    "flow": "flow-sys-id",
                    "trigger_type": "record",
                    "trigger_definition": "trigger-definition-sys-id",
                    "display_text": "When Incident is created or updated",
                }
            ]
        if table == "sys_hub_action_instance" and lookup == {"flow": "flow-sys-id"}:
            return [
                {
                    "sys_id": "action-sys-id",
                    "flow": "flow-sys-id",
                    "order": "100",
                    "action_type": "action-type-sys-id",
                    "display_text": "Set assignment group",
                }
            ]
        if table == "sys_hub_flow_logic_instance_v2" and lookup == {"flow": "flow-sys-id"}:
            return [
                {
                    "sys_id": "logic-sys-id",
                    "flow": "flow-sys-id",
                    "order": "200",
                    "logic_definition": "if-definition-sys-id",
                    "display_text": "If category is software",
                }
            ]
        if table == "sys_hub_trigger_input" and lookup == {"model": "trigger-definition-sys-id"}:
            return [
                {
                    "sys_id": "trigger-input-sys-id",
                    "model": "trigger-definition-sys-id",
                    "element": "table",
                    "column_label": "Table",
                    "internal_type": "string",
                }
            ]
        if table == "sys_hub_trigger_output" and lookup == {"model": "trigger-definition-sys-id"}:
            return [
                {
                    "sys_id": "trigger-output-sys-id",
                    "model": "trigger-definition-sys-id",
                    "element": "current",
                    "column_label": "Current record",
                    "internal_type": "reference",
                }
            ]
        if table == "sys_hub_action_input" and lookup == {"model": "action-type-sys-id"}:
            return [
                {
                    "sys_id": "action-input-sys-id",
                    "model": "action-type-sys-id",
                    "element": "assignment_group",
                    "column_label": "Assignment group",
                    "internal_type": "reference",
                    "reference": "sys_user_group",
                }
            ]
        if table == "sys_hub_action_output" and lookup == {"model": "action-type-sys-id"}:
            return [
                {
                    "sys_id": "action-output-sys-id",
                    "model": "action-type-sys-id",
                    "element": "updated_record",
                    "column_label": "Updated record",
                    "internal_type": "reference",
                }
            ]
        if table == "sys_script_include" and lookup == {}:
            return [{"sys_id": "script-include-sys-id", "name": "IncidentUtils", "active": "true"}]
        if table == "cmdb_ci" and lookup == {"sys_class_name": "cmdb_ci_discovery"}:
            return [
                {
                    "sys_id": "discovery-map-sys-id",
                    "name": "Incident Discovery Map",
                    "sys_class_name": "cmdb_ci_discovery",
                }
            ]
        if table == "sys_rest_message" and lookup == {}:
            return [
                {
                    "sys_id": "rest-message-sys-id",
                    "name": "Incident Integration",
                    "rest_endpoint": "https://api.example.invalid/path?token=secret-value",
                }
            ]
        if table == "sc_catalog" and lookup == {}:
            return [
                {
                    "sys_id": "service-catalog-sys-id",
                    "title": "Service Catalog",
                    "active": "true",
                }
            ]
        if table == "sc_category" and lookup == {}:
            return [
                {
                    "sys_id": "services-category-sys-id",
                    "title": "Services",
                    "active": "true",
                    "sc_catalog": {
                        "value": "service-catalog-sys-id",
                        "display_value": "Service Catalog",
                    },
                }
            ]
        if table == "topic" and lookup == {}:
            return [
                {
                    "sys_id": "access-topic-sys-id",
                    "name": "Access issues",
                    "topic_path": "Technology services / Software / Access issues",
                    "active": "true",
                    "taxonomy": {"value": "employee-taxonomy-sys-id", "display_value": "Employee"},
                }
            ]
        if table == "taxonomy" and lookup == {}:
            return [
                {
                    "sys_id": "employee-taxonomy-sys-id",
                    "name": "Employee",
                    "active": "true",
                }
            ]
        if table == "taxonomy_content_configuration" and lookup == {}:
            return [
                {
                    "sys_id": "catalog-item-content-type-sys-id",
                    "name": "Catalog Item",
                    "active": "true",
                }
            ]
        if table == "m2m_connected_content" and lookup == {}:
            return [
                {
                    "sys_id": "connected-content-sys-id",
                    "topic": {"value": "access-topic-sys-id"},
                    "catalog_item": {"value": "existing-catalog-item-sys-id"},
                    "content_type": {"value": "catalog-item-content-type-sys-id"},
                }
            ]
        return []


def test_discover_dictionary_form_context_fetches_target_instance_state() -> None:
    client = FakeDiscoveryClient()

    context = discover_dictionary_form_context(client=client, target_table="incident")

    assert context.target_table == "incident"
    assert context.table_label == "Incident"
    assert context.table_exists
    assert context.supports_custom_fields
    assert context.field_exists("description")
    assert context.anchor_exists("description")
    assert [call["table"] for call in client.calls] == [
        "sys_db_object",
        "sys_dictionary",
        "sys_ui_section",
        "sys_ui_element",
        "sys_security_acl",
    ]


def test_discover_servicenow_surface_context_collects_related_platform_surfaces() -> None:
    client = FakeDiscoveryClient()

    bundle = discover_servicenow_surface_context(
        client=client,
        target_table="incident",
        story_text=(
            "Add a field to Incident and check related business rules, client scripts, "
            "UI policies, flows, Script Includes, discovery maps, integrations, "
            "and public documentation."
        ),
        public_doc_queries=["ServiceNow business rule documentation"],
    )

    assert isinstance(bundle, ServiceNowSurfaceContextBundle)
    assert bundle.target_table == "incident"
    assert bundle.context_sufficient is True
    assert bundle.required_surfaces == [
        "table_schema",
        "form_layout",
        "business_rules",
        "client_scripts",
        "ui_policies",
        "flows",
        "flow_graph",
        "script_includes",
        "cmdb_discovery_maps",
        "integration_surfaces",
        "public_docs",
    ]
    assert bundle.surface_record_count("business_rules") == 1
    assert bundle.surface_record_count("client_scripts") == 1
    assert bundle.surface_record_count("ui_policies") == 1
    assert bundle.surface_record_count("flows") == 1
    assert bundle.surface_record_count("flow_graph") == 7
    assert bundle.surface_record_count("script_includes") == 1
    assert bundle.surface_record_count("cmdb_discovery_maps") == 1
    assert bundle.surface_record_count("integration_surfaces") == 1
    assert bundle.surface_record_count("public_docs") == 1
    assert "sys_script:incident" in bundle.evidence
    assert "public_docs:ServiceNow business rule documentation" in bundle.evidence
    assert "business-rule-sys-id" not in bundle.model_dump_json()
    assert "secret-value" not in bundle.model_dump_json()
    assert "token=" not in bundle.model_dump_json()

    business_rules = bundle.surface("business_rules")
    assert business_rules.confidence == 0.95
    assert business_rules.citations[0]["source_table"] == "sys_script"
    assert business_rules.citations[0]["query"] == "collection=incident"
    assert business_rules.records[0].metadata["script"] == "[redacted_script_body]"

    integrations = bundle.surface("integration_surfaces")
    assert integrations.records[0].metadata["rest_endpoint"] == (
        "https://api.example.invalid/path?[redacted_query]"
    )


def test_discover_servicenow_surface_context_collects_catalog_employee_center_surfaces() -> None:
    client = FakeDiscoveryClient()

    bundle = discover_servicenow_surface_context(
        client=client,
        target_table="sc_cat_item",
        story_text=(
            "Target artifact type: Catalog Item. Catalog Service Catalog. "
            "Category Services. Employee Center topic Access issues."
        ),
        public_doc_queries=[],
        required_surfaces_override=[
            "catalog_definitions",
            "catalog_categories",
            "employee_center_topics",
            "employee_center_connected_content",
        ],
    )

    assert bundle.required_surfaces == [
        "catalog_definitions",
        "catalog_categories",
        "employee_center_topics",
        "employee_center_connected_content",
    ]
    assert bundle.missing_required_surfaces == []
    catalogs = bundle.surface("catalog_definitions")
    assert catalogs.source_table == "sc_catalog"
    assert catalogs.records[0].name == "Service Catalog"
    categories = bundle.surface("catalog_categories")
    assert categories.records[0].metadata["sc_catalog"] == "service-catalog-sys-id"
    topics = bundle.surface("employee_center_topics")
    assert topics.records[0].name == "Technology services / Software / Access issues"
    assert topics.records[0].metadata["taxonomy"] == "employee-taxonomy-sys-id"
    connected_content = bundle.surface("employee_center_connected_content")
    assert connected_content.records[0].name == "Catalog Item"
    assert connected_content.records[0].metadata["sys_id"] == "catalog-item-content-type-sys-id"
    assert any(call["table"] == "taxonomy" for call in client.calls)


def test_surface_context_ignores_forbidden_boundaries_as_requested_surfaces() -> None:
    client = FakeDiscoveryClient()

    bundle = discover_servicenow_surface_context(
        client=client,
        target_table="incident",
        story_text=(
            "Target artifact type: UI Policy\n"
            "Target table: incident\n"
            "Condition: category is software\n"
            "Actions: Make assignment_group mandatory and visible.\n"
            "Fields read: category\n"
            "Fields written / affected: assignment_group\n"
            "Reverse if false: true\n"
            "Run scripts: false\n"
            "Forbidden behavior: Do not use Client Script, Business Rule, "
            "Script Include, Flow, ACL, integration calls, credentials, or "
            "cross-table behavior."
        ),
        public_doc_queries=[],
    )

    assert bundle.context_sufficient is True
    assert bundle.required_surfaces == ["table_schema", "form_layout", "ui_policies"]
    assert "flow_graph" not in bundle.missing_required_surfaces


def test_surface_context_does_not_require_cmdb_discovery_for_cmdb_ci_field_reads() -> None:
    client = FakeDiscoveryClient()

    bundle = discover_servicenow_surface_context(
        client=client,
        target_table="incident",
        story_text=(
            "Target artifact type: Client Script\n"
            "Target table: incident\n"
            "Client script type: onChange\n"
            "Target field: category\n"
            "Condition: category changes to software and cmdb_ci is empty\n"
            "Actions: Show an informational message reminding the fulfiller to "
            "select the affected Configuration item.\n"
            "Fields read: category, cmdb_ci\n"
            "Fields written / affected: none\n"
            "Forbidden behavior: Do not use GlideAjax, document APIs, window "
            "APIs, browser storage, external calls, credentials, form submit, "
            "or unrelated field writes."
        ),
        public_doc_queries=[],
    )

    assert bundle.context_sufficient is True
    assert bundle.required_surfaces == ["table_schema", "form_layout", "client_scripts"]
    assert "cmdb_discovery_maps" not in bundle.missing_required_surfaces


def test_required_flow_graph_context_collects_graph_records_with_citations() -> None:
    client = FakeDiscoveryClient()

    bundle = discover_servicenow_surface_context(
        client=client,
        target_table="incident",
        story_text="Update the Incident Flow Designer flow for triage.",
        public_doc_queries=[],
        required_surfaces_override=["table_schema", "form_layout", "flows", "flow_graph"],
    )

    assert bundle.context_sufficient is True
    assert bundle.missing_required_surfaces == []
    assert bundle.surface_record_count("flows") == 1
    assert bundle.surface_record_count("flow_graph") == 7

    graph = bundle.surface("flow_graph")
    assert graph.required is True
    assert graph.confidence == 0.95
    assert graph.source_table == "sys_hub_flow_graph"
    assert {record.source_table for record in graph.records} == {
        "sys_hub_trigger_instance",
        "sys_hub_action_instance",
        "sys_hub_flow_logic_instance_v2",
        "sys_hub_trigger_input",
        "sys_hub_trigger_output",
        "sys_hub_action_input",
        "sys_hub_action_output",
    }
    assert {citation["source_table"] for citation in graph.citations} == {
        "sys_hub_trigger_instance",
        "sys_hub_action_instance",
        "sys_hub_flow_logic_instance_v2",
        "sys_hub_trigger_input",
        "sys_hub_trigger_output",
        "sys_hub_action_input",
        "sys_hub_action_output",
    }
    assert "sys_hub_action_instance:Incident Triage" in graph.evidence
    assert "sys_hub_action_input:action-type-sys-id" in graph.evidence
    assert "secret-value" not in bundle.model_dump_json()


def test_required_form_section_context_collects_section_records() -> None:
    bundle = discover_servicenow_surface_context(
        client=FakeDiscoveryClient(),
        target_table="incident",
        story_text="Remove tabs from the Incident form.",
        public_doc_queries=[],
        required_surfaces_override=["form_sections", "form_layout"],
    )

    assert bundle.context_sufficient is True
    assert bundle.required_surfaces == ["form_sections", "form_layout"]
    assert bundle.surface_record_count("form_sections") == 1
    assert bundle.surface("form_sections").required is True
    assert bundle.surface("form_sections").records[0].metadata == {
        "caption": "",
        "view_name": "Default view",
        "element_count": "1",
    }


def test_required_flow_graph_context_fails_closed_when_graph_is_incomplete() -> None:
    class IncompleteFlowGraphClient(FakeDiscoveryClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            if table == "sys_hub_flow" and lookup == {}:
                self.calls.append(
                    {"table": table, "lookup": lookup, "fields": fields, "limit": limit}
                )
                return [{"sys_id": "flow-sys-id", "name": "Incident Triage", "active": "true"}]
            if table in {
                "sys_hub_trigger_instance",
                "sys_hub_action_instance",
                "sys_hub_flow_logic_instance_v2",
                "sys_hub_trigger_input",
                "sys_hub_trigger_output",
                "sys_hub_action_input",
                "sys_hub_action_output",
            }:
                self.calls.append(
                    {"table": table, "lookup": lookup, "fields": fields, "limit": limit}
                )
                return []
            return super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )

    bundle = discover_servicenow_surface_context(
        client=IncompleteFlowGraphClient(),
        target_table="incident",
        story_text="Update the Incident Flow Designer flow for triage.",
        public_doc_queries=[],
        required_surfaces_override=["table_schema", "form_layout", "flows", "flow_graph"],
    )

    assert bundle.context_sufficient is False
    assert "flow_graph" in bundle.missing_required_surfaces
    assert bundle.surface("flow_graph").confidence == 0.0


def test_discover_servicenow_surface_context_marks_required_missing_surface() -> None:
    class MissingFlowClient(FakeDiscoveryClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            if table == "sys_hub_flow":
                self.calls.append(
                    {"table": table, "lookup": lookup, "fields": fields, "limit": limit}
                )
                return []
            return super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )

    bundle = discover_servicenow_surface_context(
        client=MissingFlowClient(),
        target_table="incident",
        story_text="Update the Incident Flow for triage.",
        public_doc_queries=[],
    )

    assert bundle.context_sufficient is False
    assert "flows" in bundle.missing_required_surfaces
    assert bundle.surface("flows").confidence == 0.0


def test_empty_required_ui_policy_context_is_sufficient_when_query_succeeds() -> None:
    class EmptyUiPolicyClient(FakeDiscoveryClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            if table == "sys_ui_policy":
                self.calls.append(
                    {"table": table, "lookup": lookup, "fields": fields, "limit": limit}
                )
                return []
            return super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )

    bundle = discover_servicenow_surface_context(
        client=EmptyUiPolicyClient(),
        target_table="incident",
        story_text="Create a UI Policy on the Incident table.",
        public_doc_queries=[],
        required_surfaces_override=["table_schema", "form_layout", "ui_policies"],
    )

    assert bundle.context_sufficient is True
    assert bundle.missing_required_surfaces == []
    assert bundle.surface_record_count("ui_policies") == 0


def test_script_include_only_context_does_not_require_table_schema_or_form_layout() -> None:
    class GlobalScriptIncludeClient(FakeDiscoveryClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            if table in {"sys_db_object", "sys_dictionary", "sys_ui_section"} and lookup == {
                "name": "global"
            }:
                self.calls.append(
                    {"table": table, "lookup": lookup, "fields": fields, "limit": limit}
                )
                return []
            return super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )

    bundle = discover_servicenow_surface_context(
        client=GlobalScriptIncludeClient(),
        target_table="global",
        story_text="Create a Script Include named JediIncidentUtils in Global scope.",
        public_doc_queries=[],
        required_surfaces_override=["script_includes"],
    )

    assert bundle.context_sufficient is True
    assert bundle.required_surfaces == ["script_includes"]
    assert bundle.missing_required_surfaces == []
    assert bundle.surface("table_schema").required is False
    assert bundle.surface("form_layout").required is False
    assert bundle.surface("script_includes").required is True
