from __future__ import annotations

from typing import Any

import pytest

from jedi_devproject.catalog_item_generation import catalog_item_customer_updates
from jedi_devproject.models import CandidateChange


class FakeCatalogMetadataClient:
    def __init__(self, *, duplicate_topic: bool = False) -> None:
        self.duplicate_topic = duplicate_topic
        self.fetches: list[dict[str, object]] = []

    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        self.fetches.append({"table": table, "lookup": lookup, "fields": fields, "limit": limit})
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
        if table == "taxonomy" and lookup == {}:
            return [
                {
                    "sys_id": "employee-taxonomy-sys-id",
                    "name": "Employee",
                    "active": "true",
                }
            ]
        if table == "topic" and lookup == {}:
            records = [
                {
                    "sys_id": "access-topic-sys-id",
                    "name": "Access issues",
                    "topic_path": "Technology services / Software / Access issues",
                    "active": "true",
                    "taxonomy": {
                        "value": "employee-taxonomy-sys-id",
                        "display_value": "Employee",
                    },
                }
            ]
            if self.duplicate_topic:
                records.append({**records[0], "sys_id": "duplicate-access-topic-sys-id"})
            return records
        if table == "taxonomy_content_configuration" and lookup == {}:
            return [
                {
                    "sys_id": "catalog-item-content-type-sys-id",
                    "name": "Catalog Item",
                    "active": "true",
                }
            ]
        return []


def _catalog_changes(*, variable_type: str = "reference") -> list[CandidateChange]:
    return [
        CandidateChange(
            table="sc_cat_item",
            operation="insert",
            fields={
                "name": "Request Temporary Badge",
                "short_description": "Request a temporary access badge for a visitor.",
                "description": "Use this item when a visitor needs temporary building access.",
                "catalog": "Service Catalog",
                "category": "Services",
                "taxonomy": "Employee",
                "employee_center_topic": "Technology services / Software / Access issues",
            },
            rationale="Create the standard catalog item.",
        ),
        CandidateChange(
            table="item_option_new",
            operation="insert",
            fields={
                "name": "visitor_name",
                "question_text": "Visitor name",
                "type": "single_line_text",
                "mandatory": "true",
                "order": "100",
            },
            rationale="Collect the visitor name.",
        ),
        CandidateChange(
            table="item_option_new",
            operation="insert",
            fields={
                "name": "sponsor",
                "question_text": "Sponsor",
                "type": variable_type,
                "reference": "sys_user",
                "reference_qualifier": "active=true",
                "mandatory": "true",
                "order": "200",
            },
            rationale="Collect the sponsoring employee.",
        ),
        CandidateChange(
            table="sc_cat_item_category",
            operation="insert",
            fields={"catalog": "Service Catalog", "category": "Services"},
            rationale="Place the item in the Services catalog category.",
        ),
        CandidateChange(
            table="m2m_connected_content",
            operation="insert",
            fields={
                "taxonomy": "Employee",
                "topic": "Technology services / Software / Access issues",
            },
            rationale="Associate the item to the Employee Center topic.",
        ),
    ]


def test_catalog_item_customer_updates_builds_item_variables_category_and_topic_payloads() -> None:
    client = FakeCatalogMetadataClient()

    updates = catalog_item_customer_updates(
        client=client,
        changes=_catalog_changes(),
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    assert [update["type"] for update in updates] == [
        "Catalog Item",
        "Catalog Variable",
        "Catalog Variable",
        "Catalog Item Category",
        "Connected Content",
    ]
    combined_payload = "\n".join(str(update["payload"]) for update in updates)
    assert "<name>Request Temporary Badge</name>" in combined_payload
    assert (
        "<short_description>Request a temporary access badge for a visitor.</short_description>"
        in combined_payload
    )
    assert (
        '<category display_value="Services">services-category-sys-id</category>'
        in combined_payload
    )
    assert "<sc_catalogs>service-catalog-sys-id</sc_catalogs>" in combined_payload
    assert "<variable_name>visitor_name</variable_name>" in combined_payload
    assert "<question_text>Visitor name</question_text>" in combined_payload
    assert "<visible_standalone>true</visible_standalone>" in combined_payload
    assert "<visible_bundle>true</visible_bundle>" in combined_payload
    assert "<visible_summary>true</visible_summary>" in combined_payload
    assert "<type>6</type>" in combined_payload
    assert "<variable_name>sponsor</variable_name>" in combined_payload
    assert "<reference>sys_user</reference>" in combined_payload
    assert "<reference_qual>active=true</reference_qual>" in combined_payload
    assert "<type>8</type>" in combined_payload
    assert "<sc_cat_item>request_temporary_badge" not in combined_payload
    assert (
        '<sc_category display_value="Services">services-category-sys-id</sc_category>'
        in combined_payload
    )
    assert (
        '<topic display_value="Technology services / Software / Access issues">'
        "access-topic-sys-id</topic>"
        in combined_payload
    )
    assert (
        '<content_type display_value="Catalog Item">'
        "catalog-item-content-type-sys-id</content_type>"
        in combined_payload
    )
    assert any(fetch["table"] == "taxonomy_content_configuration" for fetch in client.fetches)


def test_catalog_item_customer_updates_rejects_ambiguous_employee_center_topic() -> None:
    client = FakeCatalogMetadataClient(duplicate_topic=True)

    with pytest.raises(ValueError, match="Employee Center topic is ambiguous"):
        catalog_item_customer_updates(
            client=client,
            changes=_catalog_changes(),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_catalog_item_customer_updates_rejects_unsupported_variable_type() -> None:
    client = FakeCatalogMetadataClient()

    with pytest.raises(ValueError, match="unsupported catalog variable type: list_collector"):
        catalog_item_customer_updates(
            client=client,
            changes=_catalog_changes(variable_type="list_collector"),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )
