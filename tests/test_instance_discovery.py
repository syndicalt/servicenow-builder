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
        if table == "sys_dictionary" and lookup == {"name": "incident"}:
            return [
                {
                    "element": "description",
                    "column_label": "Description",
                    "internal_type": "string",
                    "max_length": "4000",
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
        if table == "sys_ui_element" and lookup == {
            "name": "incident",
            "sys_ui_section": "incident-main-section",
        }:
            return [{"sys_id": "description-element", "element": "description", "position": "2"}]
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
        "script_includes",
        "cmdb_discovery_maps",
        "integration_surfaces",
        "public_docs",
    ]
    assert bundle.surface_record_count("business_rules") == 1
    assert bundle.surface_record_count("client_scripts") == 1
    assert bundle.surface_record_count("ui_policies") == 1
    assert bundle.surface_record_count("flows") == 1
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
