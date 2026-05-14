from typing import Any

from jedi_devproject.instance_discovery import (
    DiscoveredField,
    DiscoveredFormElement,
    DiscoveredFormSection,
    InstanceDiscoveryContext,
    discover_dictionary_form_context,
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
