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
    assert "<element>u_antics</element><position>3</position>" in updates[2]["payload"]


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
