from __future__ import annotations

from typing import Any

from jedi_devproject.generic_dictionary_form import (
    DictionaryFormIntent,
    dictionary_form_customer_updates,
)


class FakeMetadataClient:
    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        _ = (fields, limit)
        if table == "sys_ui_section" and lookup == {"name": "incident"}:
            return [
                {
                    "sys_id": "incident-main-section",
                    "name": "incident",
                    "caption": "",
                    "view": {"display_value": "Default view", "value": "default"},
                    "sys_user": "",
                }
            ]
        if table == "sys_ui_element" and lookup == {
            "name": "incident",
            "sys_ui_section": "incident-main-section",
        }:
            return [
                {
                    "sys_id": "short-description-element",
                    "element": "short_description",
                    "position": "1",
                },
                {"sys_id": "description-element", "element": "description", "position": "2"},
            ]
        return []


def test_generic_dictionary_form_updates_incident_field_and_form() -> None:
    updates = dictionary_form_customer_updates(
        client=FakeMetadataClient(),
        intent=DictionaryFormIntent(
            target_table="incident",
            field_label="Antics",
            field_name="u_antics",
            field_type="string",
            max_length=4000,
            mandatory=False,
            default_value="",
            placement_anchor="description",
            placement_position="below",
        ),
        remote_update_set_sys_id="remote-sys-id",
    )

    assert [update["name"] for update in updates] == [
        "sys_dictionary_incident_u_antics",
        "sys_documentation_incident_u_antics_en",
        "sys_ui_section_incident-main-section",
    ]
    assert updates[0]["target_name"] == "Incident.Antics"
    assert "<name>incident</name>" in updates[0]["payload"]
    assert "<element>u_antics</element>" in updates[0]["payload"]
    assert "<max_length>4000</max_length>" in updates[0]["payload"]
    assert "<label>Antics</label>" in updates[1]["payload"]
    assert updates[2]["type"] == "Form Layout"
    assert '<sys_ui_section caption="" section_id="incident-main-section"' in updates[2]["payload"]
    assert 'table="incident" version="3" view=""' in updates[2]["payload"]
    assert '<sys_ui_section action="INSERT_OR_UPDATE">' in updates[2]["payload"]
    assert (
        '<sys_ui_section caption="NULL" display_value="" name="incident" '
        'sys_domain="global" view="Default view">incident-main-section</sys_ui_section>'
    ) in updates[2]["payload"]
    assert "<element>u_antics</element><position>3</position>" in updates[2]["payload"]


def test_generic_dictionary_form_updates_reference_field_metadata() -> None:
    class ProblemMetadataClient(FakeMetadataClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            if table == "sys_ui_section" and lookup == {"name": "problem"}:
                return [
                    {
                        "sys_id": "problem-main-section",
                        "name": "problem",
                        "caption": "",
                        "view": {"display_value": "Default view", "value": "default"},
                        "sys_user": "",
                    }
                ]
            if table == "sys_ui_element" and lookup == {
                "name": "problem",
                "sys_ui_section": "problem-main-section",
            }:
                return [
                    {
                        "sys_id": "description-element",
                        "element": "description",
                        "position": "8",
                    }
                ]
            return super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )

    updates = dictionary_form_customer_updates(
        client=ProblemMetadataClient(),
        intent=DictionaryFormIntent(
            target_table="problem",
            field_label="Vendor Reference",
            field_name="u_vendor_reference",
            field_type="reference",
            reference_table="core_company",
            reference_qualifier="vendor=true",
            placement_anchor="description",
            placement_position="below",
        ),
        remote_update_set_sys_id="remote-sys-id",
    )

    assert "<element>u_vendor_reference</element>" in updates[0]["payload"]
    assert (
        '<internal_type display_value="Reference">reference</internal_type>'
        in updates[0]["payload"]
    )
    assert "<reference>core_company</reference>" in updates[0]["payload"]
    assert "<use_reference_qualifier>simple</use_reference_qualifier>" in updates[0]["payload"]
    assert "<reference_qual>vendor=true</reference_qual>" in updates[0]["payload"]
    assert (
        "<reference_qual_condition>vendor=true</reference_qual_condition>" in updates[0]["payload"]
    )
    assert "<element>u_vendor_reference</element><position>9</position>" in updates[2]["payload"]


def test_generic_dictionary_form_rejects_reference_field_without_reference_table() -> None:
    try:
        DictionaryFormIntent(
            target_table="problem",
            field_label="Vendor Reference",
            field_name="u_vendor_reference",
            field_type="reference",
        )
    except ValueError as exc:
        assert "reference_table is required for reference fields" in str(exc)
    else:
        raise AssertionError("reference field without reference_table was accepted")


def test_generic_dictionary_form_ignores_non_default_reference_views_without_display() -> None:
    class ViewMetadataClient(FakeMetadataClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            if table == "sys_ui_section" and lookup == {"name": "incident"}:
                return [
                    {
                        "sys_id": "default-section",
                        "name": "incident",
                        "caption": "",
                        "view": {"display_value": "Default view", "value": "default"},
                        "sys_user": "",
                    },
                    {
                        "sys_id": "workspace-section",
                        "name": "incident",
                        "caption": "",
                        "view": {"display_value": "", "value": "workspace-view-sys-id"},
                        "sys_user": "",
                    },
                ]
            if table == "sys_ui_element":
                return [
                    {"sys_id": "description-element", "element": "description", "position": "2"}
                ]
            return super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )

    updates = dictionary_form_customer_updates(
        client=ViewMetadataClient(),
        intent=DictionaryFormIntent(
            target_table="incident",
            field_label="Antics",
            field_name="u_antics",
            field_type="string",
            placement_anchor="description",
            placement_position="below",
        ),
        remote_update_set_sys_id="remote-sys-id",
    )

    assert [update["name"] for update in updates if update["type"] == "Form Layout"] == [
        "sys_ui_section_default-section"
    ]


def test_generic_dictionary_form_fails_when_anchor_missing() -> None:
    try:
        dictionary_form_customer_updates(
            client=FakeMetadataClient(),
            intent=DictionaryFormIntent(
                target_table="incident",
                field_label="Antics",
                field_name="u_antics",
                field_type="string",
                max_length=4000,
                placement_anchor="caller_id",
                placement_position="below",
            ),
            remote_update_set_sys_id="remote-sys-id",
        )
    except ValueError as exc:
        assert "form placement anchor not found: caller_id" in str(exc)
    else:
        raise AssertionError("missing anchor was accepted")
