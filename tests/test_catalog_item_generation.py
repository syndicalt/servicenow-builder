from __future__ import annotations

from typing import Any

import pytest

from jedi_devproject.catalog_item_generation import (
    CATALOG_ITEM_FIELD_NON_JSON_DIAGNOSTIC,
    CATALOG_ITEM_METADATA_MISSING_DIAGNOSTIC,
    CatalogItemIntent,
    CatalogVariableGroup,
    CatalogVariableIntent,
    catalog_item_customer_updates,
    validated_reference_qualifier,
)
from jedi_devproject.models import CandidateChange


class FakeCatalogMetadataClient:
    def __init__(
        self,
        *,
        duplicate_topic: bool = False,
        variable_set_titles: tuple[str, ...] = ("Common Visitor Questions",),
        duplicate_variable_set: bool = False,
        flow_names: tuple[str, ...] = ("Badge Access Fulfillment",),
        flow_active: bool = True,
        flow_trigger_display: str = "Record Created",
    ) -> None:
        self.duplicate_topic = duplicate_topic
        self.variable_set_titles = variable_set_titles
        self.duplicate_variable_set = duplicate_variable_set
        self.flow_names = flow_names
        self.flow_active = flow_active
        self.flow_trigger_display = flow_trigger_display
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
        if table == "item_option_new_set" and lookup == {}:
            records = [
                {
                    "sys_id": f"variable-set-sys-id-{index}",
                    "title": title,
                    "internal_name": title.lower().replace(" ", "_"),
                    "active": "true",
                }
                for index, title in enumerate(self.variable_set_titles, start=1)
            ]
            if self.duplicate_variable_set and records:
                records.append({**records[0], "sys_id": "duplicate-variable-set-sys-id"})
            return records
        if table == "sys_hub_flow" and lookup == {}:
            return [
                {
                    "sys_id": f"flow-sys-id-{index}",
                    "name": name,
                    "internal_name": name.lower().replace(" ", "_"),
                    "active": "true" if self.flow_active else "false",
                    "status": "published",
                    "type": "flow",
                }
                for index, name in enumerate(self.flow_names, start=1)
            ]
        if table == "sys_hub_trigger_instance":
            return [
                {
                    "sys_id": "flow-trigger-sys-id",
                    "trigger_type": {
                        "value": "trigger-type-sys-id",
                        "display_value": self.flow_trigger_display,
                    },
                    "trigger_definition": "",
                    "display_text": "",
                }
            ]
        return []


def _catalog_changes(
    *,
    variable_type: str = "reference",
    reference_qualifier: str = "active=true",
    item_fields: dict[str, object] | None = None,
) -> list[CandidateChange]:
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
                **(item_fields or {}),
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
                "reference_qualifier": reference_qualifier,
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


def test_catalog_item_customer_updates_rejects_non_json_item_field_without_leak() -> None:
    class SecretBearingCatalogField:
        def __str__(self) -> str:
            return "leaked-catalog-item-secret"

    client = FakeCatalogMetadataClient()

    with pytest.raises(ValueError) as exc_info:
        catalog_item_customer_updates(
            client=client,
            changes=_catalog_changes(item_fields={"name": SecretBearingCatalogField()}),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )

    message = str(exc_info.value)
    assert message == CATALOG_ITEM_FIELD_NON_JSON_DIAGNOSTIC
    assert "leaked-catalog-item-secret" not in message
    assert "SecretBearingCatalogField" not in message
    assert client.fetches == []


def test_catalog_item_customer_updates_rejects_string_subclass_item_field_without_leak() -> None:
    class SecretBearingCatalogFieldText(str):
        def strip(self, chars: str | None = None) -> str:
            raise RuntimeError("client_secret=catalog-item-strip-secret")

        def lower(self) -> str:
            raise RuntimeError("client_secret=catalog-item-lower-secret")

    client = FakeCatalogMetadataClient()

    with pytest.raises(ValueError) as exc_info:
        catalog_item_customer_updates(
            client=client,
            changes=_catalog_changes(
                item_fields={"name": SecretBearingCatalogFieldText("Request Temporary Badge")}
            ),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )

    message = str(exc_info.value)
    assert message == CATALOG_ITEM_FIELD_NON_JSON_DIAGNOSTIC
    assert "SecretBearingCatalogFieldText" not in message
    assert "client_secret" not in message
    assert "catalog-item-strip-secret" not in message
    assert "catalog-item-lower-secret" not in message
    assert client.fetches == []


def test_catalog_item_customer_updates_rejects_list_subclass_item_field_without_leak() -> None:
    class SecretBearingCatalogList(list[str]):
        def __iter__(self) -> Any:
            raise RuntimeError("client_secret=catalog-item-list-secret")

    client = FakeCatalogMetadataClient()

    with pytest.raises(ValueError) as exc_info:
        catalog_item_customer_updates(
            client=client,
            changes=_catalog_changes(
                item_fields={
                    "variable_sets": SecretBearingCatalogList(
                        ["Common Visitor Questions"],
                    ),
                },
            ),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )

    message = str(exc_info.value)
    assert message == CATALOG_ITEM_FIELD_NON_JSON_DIAGNOSTIC
    assert exc_info.value.__cause__ is None
    assert "SecretBearingCatalogList" not in message
    assert "client_secret" not in message
    assert "catalog-item-list-secret" not in message
    assert client.fetches == []


def test_catalog_item_customer_updates_rejects_dict_subclass_metadata_without_leak() -> None:
    class SecretBearingCatalogReference(dict[str, str]):
        def get(self, key: str, default: Any = None) -> Any:
            raise RuntimeError("client_secret=catalog-reference-secret")

    class HostileCategoryClient(FakeCatalogMetadataClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            records = super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )
            if table == "sc_category" and lookup == {}:
                return [
                    {
                        **records[0],
                        "sc_catalog": SecretBearingCatalogReference(
                            {
                                "value": "service-catalog-sys-id",
                                "display_value": "Service Catalog",
                            },
                        ),
                    }
                ]
            return records

    with pytest.raises(ValueError) as exc_info:
        catalog_item_customer_updates(
            client=HostileCategoryClient(),
            changes=_catalog_changes(),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )

    message = str(exc_info.value)
    assert message == CATALOG_ITEM_FIELD_NON_JSON_DIAGNOSTIC
    assert exc_info.value.__cause__ is None
    assert "SecretBearingCatalogReference" not in message
    assert "client_secret" not in message
    assert "catalog-reference-secret" not in message


def test_catalog_item_customer_updates_rejects_metadata_record_collection_subclass() -> None:
    class SecretBearingCatalogRecords(list[dict[str, Any]]):
        def __iter__(self) -> Any:
            raise RuntimeError("client_secret=catalog-records-iter-secret")

    class HostileCatalogClient(FakeCatalogMetadataClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            records = super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )
            if table == "sc_catalog" and lookup == {}:
                return SecretBearingCatalogRecords(records)
            return records

    with pytest.raises(ValueError) as exc_info:
        catalog_item_customer_updates(
            client=HostileCatalogClient(),
            changes=_catalog_changes(),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )

    message = str(exc_info.value)
    assert message == CATALOG_ITEM_FIELD_NON_JSON_DIAGNOSTIC
    assert exc_info.value.__cause__ is None
    assert "SecretBearingCatalogRecords" not in message
    assert "client_secret" not in message
    assert "catalog-records-iter-secret" not in message


def test_catalog_item_customer_updates_rejects_metadata_record_subclass() -> None:
    class SecretBearingCatalogRecord(dict[str, Any]):
        def get(self, key: object, default: Any = None) -> Any:
            raise RuntimeError("client_secret=catalog-record-get-secret")

    class HostileCatalogClient(FakeCatalogMetadataClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            records = super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )
            if table == "sc_catalog" and lookup == {}:
                return [SecretBearingCatalogRecord(records[0])]
            return records

    with pytest.raises(ValueError) as exc_info:
        catalog_item_customer_updates(
            client=HostileCatalogClient(),
            changes=_catalog_changes(),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )

    message = str(exc_info.value)
    assert message == CATALOG_ITEM_FIELD_NON_JSON_DIAGNOSTIC
    assert exc_info.value.__cause__ is None
    assert "SecretBearingCatalogRecord" not in message
    assert "client_secret" not in message
    assert "catalog-record-get-secret" not in message


def test_catalog_item_customer_updates_rejects_ambiguous_employee_center_topic() -> None:
    client = FakeCatalogMetadataClient(duplicate_topic=True)

    with pytest.raises(ValueError, match="Employee Center topic is ambiguous"):
        catalog_item_customer_updates(
            client=client,
            changes=_catalog_changes(),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_catalog_item_customer_updates_rejects_matched_topic_missing_sys_id() -> None:
    class MissingTopicSysIdClient(FakeCatalogMetadataClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            records = super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )
            if table == "topic" and lookup == {}:
                return [{key: value for key, value in records[0].items() if key != "sys_id"}]
            return records

    with pytest.raises(ValueError) as exc_info:
        catalog_item_customer_updates(
            client=MissingTopicSysIdClient(),
            changes=_catalog_changes(),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )

    assert str(exc_info.value) == CATALOG_ITEM_METADATA_MISSING_DIAGNOSTIC


def test_catalog_item_customer_updates_rejects_hostile_scalar_subclass_metadata() -> None:
    class SecretBearingActiveFlag(int):
        def __str__(self) -> str:
            raise RuntimeError("client_secret=catalog-active-flag")

    class HostileActiveClient(FakeCatalogMetadataClient):
        def fetch_table_records(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: list[str] | None = None,
            limit: int = 100,
        ) -> list[dict[str, Any]]:
            records = super().fetch_table_records(
                table=table,
                lookup=lookup,
                fields=fields,
                limit=limit,
            )
            if table == "sc_catalog" and lookup == {}:
                return [{**records[0], "active": SecretBearingActiveFlag(1)}]
            return records

    with pytest.raises(ValueError) as exc_info:
        catalog_item_customer_updates(
            client=HostileActiveClient(),
            changes=_catalog_changes(),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )

    message = str(exc_info.value)
    assert message == CATALOG_ITEM_FIELD_NON_JSON_DIAGNOSTIC
    assert exc_info.value.__cause__ is None
    assert "SecretBearingActiveFlag" not in message
    assert "client_secret" not in message
    assert "catalog-active-flag" not in message


def test_catalog_item_customer_updates_rejects_unsupported_variable_type() -> None:
    client = FakeCatalogMetadataClient()

    with pytest.raises(ValueError, match="unsupported catalog variable type: list_collector"):
        catalog_item_customer_updates(
            client=client,
            changes=_catalog_changes(variable_type="list_collector"),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


@pytest.mark.parametrize(
    "qualifier",
    [
        "javascript:new VisitorFilter()",
        "gs.getUserID()",
        "current.assignment_group",
        "active=true;name=badge",
        "active=true^ORjavascript:gs.getUser()",
        "Active=true",
        "active=",
        "filtered to active groups",
        "nameDYNAMIC9d2c2b0c0a0a0b3400c54e853859f8c1",
    ],
)
def test_catalog_item_customer_updates_rejects_non_declarative_qualifiers(
    qualifier: str,
) -> None:
    client = FakeCatalogMetadataClient()

    with pytest.raises(ValueError, match="reference qualifier"):
        catalog_item_customer_updates(
            client=client,
            changes=_catalog_changes(reference_qualifier=qualifier),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_catalog_item_customer_updates_accepts_declarative_encoded_query_qualifiers() -> None:
    client = FakeCatalogMetadataClient()
    qualifier = "active=true^ORtype=catalog^manager.nameISNOTEMPTY^roleNOT INadmin,security_admin"

    updates = catalog_item_customer_updates(
        client=client,
        changes=_catalog_changes(reference_qualifier=qualifier),
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    combined_payload = "\n".join(str(update["payload"]) for update in updates)
    assert f"<reference_qual>{qualifier}</reference_qual>" in combined_payload
    assert f"<reference_qual_condition>{qualifier}</reference_qual_condition>" in combined_payload
    assert "<use_reference_qualifier>simple</use_reference_qualifier>" in combined_payload


def test_catalog_item_customer_updates_links_existing_variable_sets() -> None:
    client = FakeCatalogMetadataClient(
        variable_set_titles=("Common Visitor Questions", "Network Access"),
    )

    updates = catalog_item_customer_updates(
        client=client,
        changes=_catalog_changes(
            item_fields={"variable_sets": ["Common Visitor Questions", "Network Access"]},
        ),
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    assert [update["type"] for update in updates] == [
        "Catalog Item",
        "Catalog Variable",
        "Catalog Variable",
        "Catalog Item Category",
        "Connected Content",
        "Catalog Variable Set Link",
        "Catalog Variable Set Link",
    ]
    link_payloads = [
        str(update["payload"])
        for update in updates
        if update["type"] == "Catalog Variable Set Link"
    ]
    assert (
        '<variable_set display_value="Common Visitor Questions">'
        "variable-set-sys-id-1</variable_set>"
    ) in link_payloads[0]
    assert (
        '<variable_set display_value="Network Access">variable-set-sys-id-2</variable_set>'
    ) in link_payloads[1]
    assert '<record_update table="io_set_item">' in link_payloads[0]
    assert "<sys_class_name>io_set_item</sys_class_name>" in link_payloads[0]
    assert 'sc_cat_item display_value="Request Temporary Badge"' in link_payloads[0]
    assert any(fetch["table"] == "item_option_new_set" for fetch in client.fetches)


def test_catalog_item_customer_updates_parses_variable_sets_from_compact_text() -> None:
    client = FakeCatalogMetadataClient()

    updates = catalog_item_customer_updates(
        client=client,
        changes=_catalog_changes(item_fields={"variable_sets": "Common Visitor Questions"}),
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    assert [update["type"] for update in updates][-1] == "Catalog Variable Set Link"


def test_catalog_item_customer_updates_does_not_fetch_variable_sets_when_unused() -> None:
    client = FakeCatalogMetadataClient()

    catalog_item_customer_updates(
        client=client,
        changes=_catalog_changes(),
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    assert all(fetch["table"] != "item_option_new_set" for fetch in client.fetches)


def test_catalog_item_customer_updates_fails_closed_for_missing_variable_set() -> None:
    client = FakeCatalogMetadataClient(variable_set_titles=())

    with pytest.raises(ValueError, match="catalog variable set was not found"):
        catalog_item_customer_updates(
            client=client,
            changes=_catalog_changes(
                item_fields={"variable_sets": ["Common Visitor Questions"]},
            ),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_catalog_item_customer_updates_fails_closed_for_ambiguous_variable_set() -> None:
    client = FakeCatalogMetadataClient(duplicate_variable_set=True)

    with pytest.raises(ValueError, match="catalog variable set is ambiguous"):
        catalog_item_customer_updates(
            client=client,
            changes=_catalog_changes(
                item_fields={"variable_sets": ["Common Visitor Questions"]},
            ),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_catalog_item_customer_updates_attaches_existing_fulfillment_flow() -> None:
    client = FakeCatalogMetadataClient()

    updates = catalog_item_customer_updates(
        client=client,
        changes=_catalog_changes(
            item_fields={"fulfillment_flow": "Badge Access Fulfillment"},
        ),
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    item_payload = str(updates[0]["payload"])
    # Exact XML shape: the flow reference renders between description and
    # ignore_price on the sc_cat_item record only.
    assert (
        "</description>"
        '<flow_designer_flow display_value="Badge Access Fulfillment">'
        "flow-sys-id-1</flow_designer_flow>"
        "<ignore_price>true</ignore_price>"
    ) in item_payload
    other_payloads = "\n".join(str(update["payload"]) for update in updates[1:])
    assert "flow_designer_flow" not in other_payloads
    assert any(fetch["table"] == "sys_hub_flow" for fetch in client.fetches)
    assert any(
        fetch["table"] == "sys_hub_trigger_instance"
        and fetch["lookup"] == {"flow": "flow-sys-id-1"}
        for fetch in client.fetches
    )


def test_catalog_item_customer_updates_without_flow_stay_byte_identical() -> None:
    client = FakeCatalogMetadataClient()

    updates = catalog_item_customer_updates(
        client=client,
        changes=_catalog_changes(),
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    item_payload = str(updates[0]["payload"])
    assert "flow_designer_flow" not in item_payload
    assert "</description><ignore_price>true</ignore_price>" in item_payload
    assert all(fetch["table"] != "sys_hub_flow" for fetch in client.fetches)
    assert all(fetch["table"] != "sys_hub_trigger_instance" for fetch in client.fetches)


def test_catalog_item_customer_updates_fails_closed_for_missing_fulfillment_flow() -> None:
    client = FakeCatalogMetadataClient(flow_names=())

    with pytest.raises(ValueError, match="fulfillment_flow:not_found"):
        catalog_item_customer_updates(
            client=client,
            changes=_catalog_changes(
                item_fields={"fulfillment_flow": "Badge Access Fulfillment"},
            ),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_catalog_item_customer_updates_fails_closed_for_ambiguous_fulfillment_flow() -> None:
    client = FakeCatalogMetadataClient(
        flow_names=("Badge Access Fulfillment", "badge access fulfillment"),
    )

    with pytest.raises(ValueError, match="fulfillment_flow:ambiguous"):
        catalog_item_customer_updates(
            client=client,
            changes=_catalog_changes(
                item_fields={"fulfillment_flow": "Badge Access Fulfillment"},
            ),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_catalog_item_customer_updates_fails_closed_for_inactive_fulfillment_flow() -> None:
    client = FakeCatalogMetadataClient(flow_active=False)

    with pytest.raises(ValueError, match="fulfillment_flow:inactive"):
        catalog_item_customer_updates(
            client=client,
            changes=_catalog_changes(
                item_fields={"fulfillment_flow": "Badge Access Fulfillment"},
            ),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_catalog_item_customer_updates_fails_closed_for_non_record_triggered_flow() -> None:
    client = FakeCatalogMetadataClient(flow_trigger_display="Scheduled")

    with pytest.raises(ValueError, match="fulfillment_flow:not_record_triggered"):
        catalog_item_customer_updates(
            client=client,
            changes=_catalog_changes(
                item_fields={"fulfillment_flow": "Badge Access Fulfillment"},
            ),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def _grouped_catalog_changes(
    *,
    variable_groups: object,
) -> list[CandidateChange]:
    changes = _catalog_changes(item_fields={"variable_groups": variable_groups})
    changes.insert(
        3,
        CandidateChange(
            table="item_option_new",
            operation="insert",
            fields={
                "name": "start_date",
                "question_text": "Start date",
                "type": "date",
                "order": "300",
            },
            rationale="Collect the badge start date.",
        ),
    )
    changes.insert(
        4,
        CandidateChange(
            table="item_option_new",
            operation="insert",
            fields={
                "name": "end_date",
                "question_text": "End date",
                "type": "date",
                "order": "400",
            },
            rationale="Collect the badge end date.",
        ),
    )
    return changes


def test_catalog_item_customer_updates_groups_variables_in_titled_containers() -> None:
    client = FakeCatalogMetadataClient()

    updates = catalog_item_customer_updates(
        client=client,
        changes=_grouped_catalog_changes(
            variable_groups=[{"title": "Schedule", "variables": ["start_date", "end_date"]}],
        ),
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    variable_updates = [update for update in updates if update["type"] == "Catalog Variable"]
    payloads = [str(update["payload"]) for update in variable_updates]
    assert len(variable_updates) == 6
    # Ungrouped variables stay top-level in declaration order.
    assert "<variable_name>visitor_name</variable_name>" in payloads[0]
    assert "<variable_name>sponsor</variable_name>" in payloads[1]
    # The container opens at the group's first member and always closes.
    assert "<variable_name>schedule_container</variable_name>" in payloads[2]
    assert "<type>19</type>" in payloads[2]
    assert "<question_text>Schedule</question_text>" in payloads[2]
    assert "<variable_name>start_date</variable_name>" in payloads[3]
    assert "<variable_name>end_date</variable_name>" in payloads[4]
    assert "<variable_name>schedule_container_end</variable_name>" in payloads[5]
    assert "<type>20</type>" in payloads[5]
    assert "<question_text></question_text>" in payloads[5]
    # Order interleaves deterministically with the 100-increment scheme.
    assert [
        f"<order>{position * 100}</order>" in payload
        for position, payload in enumerate(payloads, start=1)
    ] == [True] * 6


def test_catalog_item_customer_updates_rejects_group_with_unknown_member() -> None:
    client = FakeCatalogMetadataClient()

    with pytest.raises(ValueError, match="references\\s+unknown variable: badge_color"):
        catalog_item_customer_updates(
            client=client,
            changes=_grouped_catalog_changes(
                variable_groups=[{"title": "Schedule", "variables": ["badge_color"]}],
            ),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_catalog_item_customer_updates_rejects_variable_in_two_groups() -> None:
    client = FakeCatalogMetadataClient()

    with pytest.raises(ValueError, match="assigned to more than one group"):
        catalog_item_customer_updates(
            client=client,
            changes=_grouped_catalog_changes(
                variable_groups=[
                    {"title": "Schedule", "variables": ["start_date"]},
                    {"title": "Dates", "variables": ["start_date", "end_date"]},
                ],
            ),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_catalog_item_customer_updates_parses_groups_from_compact_text() -> None:
    client = FakeCatalogMetadataClient()

    updates = catalog_item_customer_updates(
        client=client,
        changes=_grouped_catalog_changes(variable_groups=";Schedule|start_date, end_date;"),
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    combined_payload = "\n".join(str(update["payload"]) for update in updates)
    assert "<variable_name>schedule_container</variable_name>" in combined_payload
    assert "<variable_name>schedule_container_end</variable_name>" in combined_payload


def test_catalog_item_customer_updates_accepts_typed_group_objects() -> None:
    client = FakeCatalogMetadataClient()

    updates = catalog_item_customer_updates(
        client=client,
        changes=_grouped_catalog_changes(
            variable_groups=[CatalogVariableGroup(title="Schedule", variables=["start_date"])],
        ),
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    combined_payload = "\n".join(str(update["payload"]) for update in updates)
    assert "<variable_name>schedule_container</variable_name>" in combined_payload


def test_catalog_item_customer_updates_rejects_non_object_group_entries() -> None:
    client = FakeCatalogMetadataClient()

    with pytest.raises(ValueError, match="catalog variable group must be an object"):
        catalog_item_customer_updates(
            client=client,
            changes=_grouped_catalog_changes(variable_groups=[42]),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_catalog_item_customer_updates_rejects_duplicate_group_titles() -> None:
    client = FakeCatalogMetadataClient()

    with pytest.raises(ValueError, match="group titles must be unique"):
        catalog_item_customer_updates(
            client=client,
            changes=_grouped_catalog_changes(
                variable_groups=[
                    {"title": "Schedule", "variables": ["start_date"]},
                    {"title": "schedule", "variables": ["end_date"]},
                ],
            ),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_catalog_item_customer_updates_rejects_colliding_container_names() -> None:
    client = FakeCatalogMetadataClient()

    with pytest.raises(ValueError, match="unique container names"):
        catalog_item_customer_updates(
            client=client,
            changes=_grouped_catalog_changes(
                variable_groups=[
                    {"title": "Schedule Info", "variables": ["start_date"]},
                    {"title": "Schedule_Info", "variables": ["end_date"]},
                ],
            ),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_catalog_item_customer_updates_rejects_container_variable_name_collision() -> None:
    client = FakeCatalogMetadataClient()
    changes = _grouped_catalog_changes(
        variable_groups=[{"title": "Schedule", "variables": ["start_date"]}],
    )
    changes[4] = CandidateChange(
        table="item_option_new",
        operation="insert",
        fields={
            "name": "schedule_container",
            "question_text": "Schedule container",
            "type": "single_line_text",
            "order": "400",
        },
        rationale="Collides with the generated container name.",
    )

    with pytest.raises(ValueError, match="container names collide with variables"):
        catalog_item_customer_updates(
            client=client,
            changes=changes,
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_catalog_item_customer_updates_rejects_duplicate_variable_set_names() -> None:
    client = FakeCatalogMetadataClient()

    with pytest.raises(ValueError, match="variable set names must be unique"):
        catalog_item_customer_updates(
            client=client,
            changes=_catalog_changes(
                item_fields={
                    "variable_sets": ["Common Visitor Questions", "common visitor questions"],
                },
            ),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_catalog_item_customer_updates_requires_insertable_catalog_item_change() -> None:
    client = FakeCatalogMetadataClient()
    changes = _catalog_changes()

    with pytest.raises(ValueError, match="requires one sc_cat_item change"):
        catalog_item_customer_updates(
            client=client,
            changes=changes[1:],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )

    update_change = changes[0].model_copy(update={"operation": "update"})
    with pytest.raises(ValueError, match="supports insert only"):
        catalog_item_customer_updates(
            client=client,
            changes=[update_change, *changes[1:]],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_catalog_item_customer_updates_requires_insertable_variable_changes() -> None:
    client = FakeCatalogMetadataClient()
    changes = _catalog_changes()
    changes[1] = changes[1].model_copy(update={"operation": "update"})

    with pytest.raises(ValueError, match="variable handoff supports insert only"):
        catalog_item_customer_updates(
            client=client,
            changes=changes,
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_catalog_variable_intent_requires_reference_table_and_labels() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        CatalogVariableIntent(name="visitor_name", label="  ", variable_type="single_line_text")
    with pytest.raises(ValueError, match="require reference_table"):
        CatalogVariableIntent(name="sponsor", label="Sponsor", variable_type="reference")


def test_catalog_variable_intent_reference_qualifier_error_does_not_retain_cause() -> None:
    with pytest.raises(ValueError, match="reference qualifier rejected for sponsor") as exc:
        CatalogVariableIntent(
            name="sponsor",
            label="Sponsor",
            variable_type="reference",
            reference_table="sys_user",
            reference_qualifier="javascript:gs.getUser()",
        )
    assert exc.value.__cause__ is None


def test_catalog_item_intent_requires_unique_named_variables() -> None:
    variable = CatalogVariableIntent(
        name="visitor_name",
        label="Visitor name",
        variable_type="single_line_text",
    )
    intent_kwargs: dict[str, object] = {
        "name": "Request Temporary Badge",
        "short_description": "Request a temporary access badge.",
        "catalog": "Service Catalog",
        "category": "Services",
        "taxonomy": "Employee",
        "employee_center_topic": "Technology services / Software / Access issues",
    }
    with pytest.raises(ValueError, match="requires at least one variable"):
        CatalogItemIntent(**intent_kwargs, variables=[])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="variable names must be unique"):
        CatalogItemIntent(**intent_kwargs, variables=[variable, variable])  # type: ignore[arg-type]


def _behavior_changes() -> list[CandidateChange]:
    return [
        CandidateChange(
            table="catalog_ui_policy",
            operation="insert",
            fields={
                "short_description": "Require sponsor",
                "catalog_conditions": "visitor_name=external",
                "reverse_if_false": "true",
            },
            rationale="Require the sponsor for external visitors.",
        ),
        CandidateChange(
            table="catalog_ui_policy_action",
            operation="insert",
            fields={
                "ui_policy": "Require sponsor",
                "variable": "sponsor",
                "mandatory": "true",
                "visible": "true",
            },
            rationale="Reveal and require the sponsor variable.",
        ),
        CandidateChange(
            table="catalog_script_client",
            operation="insert",
            fields={
                "name": "Populate visitor name",
                "type": "onLoad",
                "script": (
                    "function onLoad() {\n"
                    "    g_form.setValue('visitor_name', 'New visitor');\n"
                    "}"
                ),
                "fields_written": ["visitor_name"],
            },
            rationale="Populate the visitor name on load.",
        ),
    ]


def test_catalog_item_customer_updates_renders_variable_behavior_alongside_item() -> None:
    client = FakeCatalogMetadataClient()

    updates = catalog_item_customer_updates(
        client=client,
        changes=[*_catalog_changes(), *_behavior_changes()],
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    assert [update["type"] for update in updates] == [
        "Catalog Item",
        "Catalog Variable",
        "Catalog Variable",
        "Catalog Item Category",
        "Connected Content",
        "Catalog UI Policy",
        "Catalog UI Policy Action",
        "Catalog Client Script",
    ]
    item_payload = str(updates[0]["payload"])
    item_sys_id = item_payload.split("<sys_id>")[1].split("</sys_id>")[0]
    policy_payload = str(updates[5]["payload"])
    action_payload = str(updates[6]["payload"])
    script_payload = str(updates[7]["payload"])
    # Behavior records attach to the same deterministic catalog item sys_id.
    assert f">{item_sys_id}</catalog_item>" in policy_payload
    assert f">{item_sys_id}</cat_item>" in script_payload
    # The policy condition resolves the item's own variable to its IO: sys_id.
    visitor_payload = str(updates[1]["payload"])
    visitor_sys_id = visitor_payload.split("<sys_id>")[1].split("</sys_id>")[0]
    assert (
        f"<catalog_conditions>IO:{visitor_sys_id}=external^EQ</catalog_conditions>"
        in policy_payload
    )
    sponsor_payload = str(updates[2]["payload"])
    sponsor_sys_id = sponsor_payload.split("<sys_id>")[1].split("</sys_id>")[0]
    assert f"IO:{sponsor_sys_id}</catalog_variable>" in action_payload


def test_catalog_item_customer_updates_without_behavior_changes_stay_byte_identical() -> None:
    base_updates = catalog_item_customer_updates(
        client=FakeCatalogMetadataClient(),
        changes=_catalog_changes(),
        remote_update_set_sys_id="remote-update-set-sys-id",
    )
    combined_updates = catalog_item_customer_updates(
        client=FakeCatalogMetadataClient(),
        changes=[*_catalog_changes(), *_behavior_changes()],
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    # Adding behavior changes only appends updates; the item, variable,
    # category, and topic payloads stay byte-identical.
    assert combined_updates[: len(base_updates)] == base_updates


def test_catalog_item_customer_updates_rejects_behavior_on_unknown_variable() -> None:
    client = FakeCatalogMetadataClient()
    behavior = _behavior_changes()
    behavior[1] = behavior[1].model_copy(
        update={"fields": {**behavior[1].fields, "variable": "badge_color"}}
    )

    with pytest.raises(ValueError, match="not .* own variables: badge_color"):
        catalog_item_customer_updates(
            client=client,
            changes=[*_catalog_changes(), *behavior],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_catalog_item_customer_updates_rejects_script_writing_unknown_variable() -> None:
    client = FakeCatalogMetadataClient()
    behavior = _behavior_changes()[2:]
    behavior[0] = behavior[0].model_copy(
        update={
            "fields": {
                **behavior[0].fields,
                "script": (
                    "function onLoad() {\n"
                    "    g_form.setValue('badge_color', 'blue');\n"
                    "}"
                ),
                "fields_written": ["badge_color"],
            }
        }
    )

    with pytest.raises(ValueError, match="not one of .* own variables: badge_color"):
        catalog_item_customer_updates(
            client=client,
            changes=[*_catalog_changes(), *behavior],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_validated_reference_qualifier_normalizes_empty_and_enforces_bounds() -> None:
    assert validated_reference_qualifier("") == ""
    assert validated_reference_qualifier("   ") == ""
    with pytest.raises(ValueError, match="exceeds 255 characters"):
        validated_reference_qualifier("name=" + "a" * 256)
    with pytest.raises(ValueError, match="must not carry a value"):
        validated_reference_qualifier("activeISEMPTYtrue")


def test_catalog_variable_group_model_fails_closed_on_invalid_members() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        CatalogVariableGroup(title="  ", variables=["start_date"])
    with pytest.raises(ValueError, match="requires at least one member"):
        CatalogVariableGroup(title="Schedule", variables=[])
    with pytest.raises(ValueError, match="lists a member variable twice"):
        CatalogVariableGroup(title="Schedule", variables=["start_date", "start_date"])


def test_catalog_item_intent_rejects_blank_variable_set_names() -> None:
    with pytest.raises(ValueError, match="variable set names must not be empty"):
        CatalogItemIntent(
            name="Request Temporary Badge",
            short_description="Request a temporary access badge.",
            catalog="Service Catalog",
            category="Services",
            taxonomy="Employee",
            employee_center_topic="Technology services / Software / Access issues",
            variables=[
                CatalogVariableIntent(
                    name="visitor_name",
                    label="Visitor name",
                    variable_type="single_line_text",
                )
            ],
            variable_sets=["   "],
        )
