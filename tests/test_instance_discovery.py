from jedi_devproject.instance_discovery import (
    DiscoveredField,
    DiscoveredFormElement,
    DiscoveredFormSection,
    InstanceDiscoveryContext,
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
