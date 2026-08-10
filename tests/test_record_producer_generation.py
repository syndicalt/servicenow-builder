from __future__ import annotations

from typing import Any

import pytest

from jedi_devproject.catalog_item_generation import catalog_item_customer_updates
from jedi_devproject.models import CandidateChange
from jedi_devproject.record_producer_generation import (
    RECORD_PRODUCER_FIELD_NON_JSON_DIAGNOSTIC,
    RECORD_PRODUCER_SCRIPT_REASON_CODE,
    RecordProducerIntent,
    RecordProducerVariableIntent,
    record_producer_customer_updates,
)

PRODUCER_SYS_ID = "9340f37f19b8c4c0e368a28f8481d833"
SUMMARY_VARIABLE_SYS_ID = "a40025a2bbebc755900045d417d94a60"
CALLER_VARIABLE_SYS_ID = "f049ab0f595d0c0f135b858f06e7906b"
CATEGORY_RELATION_SYS_ID = "c6e28903e529e3fa93b3b8ce8f66d8ba"


class FakeRecordProducerMetadataClient:
    def __init__(
        self,
        *,
        table_exists: bool = True,
        dictionary_elements: tuple[str, ...] = (
            "short_description",
            "description",
            "caller_id",
        ),
        catalog_titles: tuple[str, ...] = ("Service Catalog",),
        duplicate_category: bool = False,
    ) -> None:
        self.table_exists = table_exists
        self.dictionary_elements = dictionary_elements
        self.catalog_titles = catalog_titles
        self.duplicate_category = duplicate_category
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
        if table == "sys_db_object":
            if not self.table_exists:
                return []
            return [{"name": lookup.get("name", ""), "label": "Incident"}]
        if table == "sys_dictionary":
            return [{"element": element} for element in self.dictionary_elements]
        if table == "sc_catalog" and lookup == {}:
            return [
                {
                    "sys_id": "service-catalog-sys-id",
                    "title": title,
                    "active": "true",
                }
                for title in self.catalog_titles
            ]
        if table == "sc_category" and lookup == {}:
            records = [
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
            if self.duplicate_category:
                records.append({**records[0], "sys_id": "duplicate-services-category-sys-id"})
            return records
        return []


def _producer_changes(
    *,
    producer_fields: dict[str, object] | None = None,
) -> list[CandidateChange]:
    return [
        CandidateChange(
            table="sc_cat_item_producer",
            operation="insert",
            fields={
                "name": "Report Security Incident",
                "short_description": "Report a security incident for triage.",
                "description": "Use this producer to open a security incident record.",
                "table_name": "incident",
                "catalog": "Service Catalog",
                "category": "Services",
                **(producer_fields or {}),
            },
            rationale="Create the record producer.",
        ),
        CandidateChange(
            table="item_option_new",
            operation="insert",
            fields={
                "name": "summary",
                "question_text": "Summary",
                "type": "single_line_text",
                "mandatory": "true",
                "order": "100",
                "field": "short_description",
            },
            rationale="Collect the incident summary.",
        ),
        CandidateChange(
            table="item_option_new",
            operation="insert",
            fields={
                "name": "caller",
                "question_text": "Caller",
                "type": "reference",
                "reference": "sys_user",
                "reference_qualifier": "active=true",
                "order": "200",
                "field": "caller_id",
            },
            rationale="Collect the affected caller.",
        ),
        CandidateChange(
            table="sc_cat_item_category",
            operation="insert",
            fields={"catalog": "Service Catalog", "category": "Services"},
            rationale="Place the producer in the Services category.",
        ),
    ]


def test_record_producer_customer_updates_builds_producer_variables_and_category() -> None:
    client = FakeRecordProducerMetadataClient()

    updates = record_producer_customer_updates(
        client=client,
        changes=_producer_changes(),
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    assert [update["type"] for update in updates] == [
        "Record Producer",
        "Record Producer Variable",
        "Record Producer Variable",
        "Record Producer Category",
    ]
    assert all(
        update["remote_update_set"] == "remote-update-set-sys-id" for update in updates
    )
    assert updates[0]["payload"] == (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<record_update table="sc_cat_item_producer">'
        '<sc_cat_item_producer action="INSERT_OR_UPDATE">'
        "<active>true</active>"
        '<category display_value="Services">services-category-sys-id</category>'
        "<description><![CDATA["
        "Use this producer to open a security incident record."
        "]]></description>"
        "<name>Report Security Incident</name>"
        "<sc_catalogs>service-catalog-sys-id</sc_catalogs>"
        "<script><![CDATA[]]></script>"
        "<short_description>Report a security incident for triage.</short_description>"
        "<sys_class_name>sc_cat_item_producer</sys_class_name>"
        f"<sys_id>{PRODUCER_SYS_ID}</sys_id>"
        '<sys_scope display_value="Global">global</sys_scope>'
        f"<sys_update_name>sc_cat_item_producer_{PRODUCER_SYS_ID}</sys_update_name>"
        "<table_name>incident</table_name>"
        "</sc_cat_item_producer>"
        "</record_update>"
    )
    assert updates[1]["payload"] == (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<record_update table="item_option_new">'
        '<item_option_new action="INSERT_OR_UPDATE">'
        "<active>true</active>"
        f'<cat_item display_value="Report Security Incident">{PRODUCER_SYS_ID}</cat_item>'
        "<default_value></default_value>"
        "<field>short_description</field>"
        "<help_text></help_text>"
        "<mandatory>true</mandatory>"
        "<map_to_field>true</map_to_field>"
        "<name>summary</name>"
        "<order>100</order>"
        "<question_text>Summary</question_text>"
        "<show_help>true</show_help>"
        "<sys_class_name>item_option_new</sys_class_name>"
        f"<sys_id>{SUMMARY_VARIABLE_SYS_ID}</sys_id>"
        '<sys_scope display_value="Global">global</sys_scope>'
        f"<sys_update_name>item_option_new_{SUMMARY_VARIABLE_SYS_ID}</sys_update_name>"
        "<type>6</type>"
        "<variable_name>summary</variable_name>"
        "<visible_bundle>true</visible_bundle>"
        "<visible_standalone>true</visible_standalone>"
        "<visible_summary>true</visible_summary>"
        "</item_option_new>"
        "</record_update>"
    )
    caller_payload = str(updates[2]["payload"])
    assert "<field>caller_id</field>" in caller_payload
    assert "<map_to_field>true</map_to_field>" in caller_payload
    assert "<reference>sys_user</reference>" in caller_payload
    assert "<reference_qual>active=true</reference_qual>" in caller_payload
    assert "<reference_qual_condition>active=true</reference_qual_condition>" in caller_payload
    assert "<use_reference_qualifier>simple</use_reference_qualifier>" in caller_payload
    assert "<type>8</type>" in caller_payload
    assert f"<sys_id>{CALLER_VARIABLE_SYS_ID}</sys_id>" in caller_payload
    assert updates[3]["payload"] == (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<record_update table="sc_cat_item_category">'
        '<sc_cat_item_category action="INSERT_OR_UPDATE">'
        f'<sc_cat_item display_value="Report Security Incident">{PRODUCER_SYS_ID}</sc_cat_item>'
        '<sc_category display_value="Services">services-category-sys-id</sc_category>'
        "<sys_class_name>sc_cat_item_category</sys_class_name>"
        f"<sys_id>{CATEGORY_RELATION_SYS_ID}</sys_id>"
        '<sys_scope display_value="Global">global</sys_scope>'
        f"<sys_update_name>sc_cat_item_category_{CATEGORY_RELATION_SYS_ID}</sys_update_name>"
        "</sc_cat_item_category>"
        "</record_update>"
    )
    assert any(fetch["table"] == "sys_db_object" for fetch in client.fetches)
    assert any(fetch["table"] == "sys_dictionary" for fetch in client.fetches)


def test_record_producer_customer_updates_fails_closed_for_missing_target_table() -> None:
    client = FakeRecordProducerMetadataClient(table_exists=False)

    with pytest.raises(ValueError, match="target table was not found: incident"):
        record_producer_customer_updates(
            client=client,
            changes=_producer_changes(),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_record_producer_customer_updates_fails_closed_for_unknown_mapped_field() -> None:
    client = FakeRecordProducerMetadataClient(
        dictionary_elements=("short_description", "description"),
    )

    with pytest.raises(ValueError, match="mapped field was not found on incident: caller_id"):
        record_producer_customer_updates(
            client=client,
            changes=_producer_changes(),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_record_producer_customer_updates_rejects_producer_script_with_stable_code() -> None:
    client = FakeRecordProducerMetadataClient()

    with pytest.raises(ValueError, match=RECORD_PRODUCER_SCRIPT_REASON_CODE):
        record_producer_customer_updates(
            client=client,
            changes=_producer_changes(
                producer_fields={"script": "current.short_description = producer.summary;"},
            ),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_record_producer_customer_updates_rejects_non_json_producer_field_without_leak() -> None:
    class SecretBearingProducerField:
        def __str__(self) -> str:
            return "leaked-record-producer-secret"

    client = FakeRecordProducerMetadataClient()

    with pytest.raises(ValueError) as exc_info:
        record_producer_customer_updates(
            client=client,
            changes=_producer_changes(
                producer_fields={"name": SecretBearingProducerField()},
            ),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )

    message = str(exc_info.value)
    assert message == RECORD_PRODUCER_FIELD_NON_JSON_DIAGNOSTIC
    assert "leaked-record-producer-secret" not in message
    assert "SecretBearingProducerField" not in message
    assert client.fetches == []


def test_record_producer_customer_updates_rejects_string_subclass_field_without_leak() -> None:
    class SecretBearingProducerText(str):
        def strip(self, chars: str | None = None) -> str:
            raise RuntimeError("client_secret=record-producer-string-subclass")

    client = FakeRecordProducerMetadataClient()

    with pytest.raises(ValueError) as exc_info:
        record_producer_customer_updates(
            client=client,
            changes=_producer_changes(
                producer_fields={"table_name": SecretBearingProducerText("incident")},
            ),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )

    message = str(exc_info.value)
    assert message == RECORD_PRODUCER_FIELD_NON_JSON_DIAGNOSTIC
    assert "record-producer-string-subclass" not in message
    assert "SecretBearingProducerText" not in message
    assert client.fetches == []


def test_record_producer_customer_updates_rejects_scalar_subclass_field_without_leak() -> None:
    class SecretBearingProducerOrder(int):
        def __str__(self) -> str:
            raise RuntimeError("client_secret=record-producer-scalar")

    client = FakeRecordProducerMetadataClient()

    with pytest.raises(ValueError) as exc_info:
        record_producer_customer_updates(
            client=client,
            changes=_producer_changes(
                producer_fields={
                    "name": SecretBearingProducerOrder(1),
                    "artifact_name": "Report Security Incident",
                },
            ),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )

    message = str(exc_info.value)
    assert message == RECORD_PRODUCER_FIELD_NON_JSON_DIAGNOSTIC
    assert exc_info.value.__cause__ is None
    assert "record-producer-scalar" not in message
    assert "SecretBearingProducerOrder" not in message
    assert client.fetches == []


def test_record_producer_customer_updates_rejects_metadata_record_collection_subclass() -> None:
    class SecretBearingProducerRecords(list[dict[str, Any]]):
        def __iter__(self) -> Any:
            raise RuntimeError("client_secret=record-producer-records-iter")

    class HostileDictionaryClient(FakeRecordProducerMetadataClient):
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
            if table == "sys_dictionary":
                return SecretBearingProducerRecords(records)
            return records

    with pytest.raises(ValueError) as exc_info:
        record_producer_customer_updates(
            client=HostileDictionaryClient(),
            changes=_producer_changes(),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )

    message = str(exc_info.value)
    assert message == RECORD_PRODUCER_FIELD_NON_JSON_DIAGNOSTIC
    assert exc_info.value.__cause__ is None
    assert "SecretBearingProducerRecords" not in message
    assert "client_secret" not in message
    assert "record-producer-records-iter" not in message


def test_record_producer_customer_updates_rejects_metadata_record_subclass() -> None:
    class SecretBearingProducerRecord(dict[str, Any]):
        def get(self, key: object, default: Any = None) -> Any:
            raise RuntimeError("client_secret=record-producer-record-get")

    class HostileDictionaryClient(FakeRecordProducerMetadataClient):
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
            if table == "sys_dictionary":
                return [SecretBearingProducerRecord(records[0])]
            return records

    with pytest.raises(ValueError) as exc_info:
        record_producer_customer_updates(
            client=HostileDictionaryClient(),
            changes=_producer_changes(),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )

    message = str(exc_info.value)
    assert message == RECORD_PRODUCER_FIELD_NON_JSON_DIAGNOSTIC
    assert exc_info.value.__cause__ is None
    assert "SecretBearingProducerRecord" not in message
    assert "client_secret" not in message
    assert "record-producer-record-get" not in message


def test_record_producer_customer_updates_fails_closed_for_ambiguous_category() -> None:
    client = FakeRecordProducerMetadataClient(duplicate_category=True)

    with pytest.raises(ValueError, match="category is ambiguous under catalog: Services"):
        record_producer_customer_updates(
            client=client,
            changes=_producer_changes(),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_record_producer_customer_updates_fails_closed_for_missing_catalog() -> None:
    client = FakeRecordProducerMetadataClient(catalog_titles=())

    with pytest.raises(ValueError, match="catalog was not found: Service Catalog"):
        record_producer_customer_updates(
            client=client,
            changes=_producer_changes(),
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_record_producer_customer_updates_requires_insertable_producer_change() -> None:
    client = FakeRecordProducerMetadataClient()
    changes = _producer_changes()

    with pytest.raises(ValueError, match="requires one sc_cat_item_producer change"):
        record_producer_customer_updates(
            client=client,
            changes=changes[1:],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )

    update_change = changes[0].model_copy(update={"operation": "update"})
    with pytest.raises(ValueError, match="Record Producer handoff supports insert only"):
        record_producer_customer_updates(
            client=client,
            changes=[update_change, *changes[1:]],
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_record_producer_customer_updates_requires_insertable_variable_changes() -> None:
    client = FakeRecordProducerMetadataClient()
    changes = _producer_changes()
    changes[1] = changes[1].model_copy(update={"operation": "update"})

    with pytest.raises(ValueError, match="variable handoff supports insert only"):
        record_producer_customer_updates(
            client=client,
            changes=changes,
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_record_producer_customer_updates_requires_field_mapping_on_every_variable() -> None:
    client = FakeRecordProducerMetadataClient()
    changes = _producer_changes()
    unmapped_fields = {
        key: value for key, value in changes[1].fields.items() if key != "field"
    }
    changes[1] = changes[1].model_copy(update={"fields": unmapped_fields})

    with pytest.raises(ValueError, match="variable summary requires a target field mapping"):
        record_producer_customer_updates(
            client=client,
            changes=changes,
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_record_producer_customer_updates_rejects_implausible_mapped_field_name() -> None:
    client = FakeRecordProducerMetadataClient()
    changes = _producer_changes()
    changes[1] = changes[1].model_copy(
        update={"fields": {**changes[1].fields, "field": "Short Description!"}}
    )

    with pytest.raises(ValueError, match="mapped field is not a valid field name"):
        record_producer_customer_updates(
            client=client,
            changes=changes,
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_record_producer_customer_updates_rejects_duplicate_field_mappings() -> None:
    client = FakeRecordProducerMetadataClient()
    changes = _producer_changes()
    changes[2] = changes[2].model_copy(
        update={"fields": {**changes[2].fields, "field": "short_description"}}
    )

    with pytest.raises(ValueError, match="maps a target field more than once"):
        record_producer_customer_updates(
            client=client,
            changes=changes,
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_record_producer_customer_updates_rejects_non_declarative_qualifier() -> None:
    client = FakeRecordProducerMetadataClient()
    changes = _producer_changes()
    changes[2] = changes[2].model_copy(
        update={
            "fields": {**changes[2].fields, "reference_qualifier": "javascript:gs.getUser()"}
        }
    )

    with pytest.raises(ValueError, match="reference qualifier rejected for caller"):
        record_producer_customer_updates(
            client=client,
            changes=changes,
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_record_producer_variable_intent_normalizes_and_validates_mapped_field() -> None:
    variable = RecordProducerVariableIntent(
        name="summary",
        label="Summary",
        variable_type="single_line_text",
        mapped_field="  short_description  ",
    )
    assert variable.mapped_field == "short_description"

    with pytest.raises(ValueError, match="requires a target field mapping"):
        RecordProducerVariableIntent(
            name="summary",
            label="Summary",
            variable_type="single_line_text",
            mapped_field="   ",
        )


def test_record_producer_customer_updates_requires_target_table_text() -> None:
    client = FakeRecordProducerMetadataClient()
    changes = _producer_changes(producer_fields={"table_name": "   "})

    with pytest.raises(ValueError, match="must not be empty"):
        record_producer_customer_updates(
            client=client,
            changes=changes,
            remote_update_set_sys_id="remote-update-set-sys-id",
        )


def test_record_producer_intent_requires_unique_variables_and_mappings() -> None:
    variable = RecordProducerVariableIntent(
        name="summary",
        label="Summary",
        variable_type="single_line_text",
        mapped_field="short_description",
    )
    intent_kwargs: dict[str, object] = {
        "name": "Report Security Incident",
        "short_description": "Report a security incident.",
        "table_name": "incident",
        "catalog": "Service Catalog",
        "category": "Services",
    }
    with pytest.raises(ValueError, match="requires at least one variable"):
        RecordProducerIntent(**intent_kwargs, variables=[])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="variable names must be unique"):
        RecordProducerIntent(**intent_kwargs, variables=[variable, variable])  # type: ignore[arg-type]
    second = variable.model_copy(update={"name": "details"})
    with pytest.raises(ValueError, match="more than once: short_description"):
        RecordProducerIntent(**intent_kwargs, variables=[variable, second])  # type: ignore[arg-type]


# Locks the exact bytes of a catalog variable payload produced through the
# shared item_option_new builder: reusing it for record producers must leave
# non-producer payloads byte-identical.
_CATALOG_VARIABLE_PAYLOAD_GOLDEN = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<record_update table="item_option_new">'
    '<item_option_new action="INSERT_OR_UPDATE">'
    "<active>true</active>"
    '<cat_item display_value="Request Temporary Badge">'
    "952cf428d9db45f42351330780095254</cat_item>"
    "<default_value></default_value>"
    "<help_text></help_text>"
    "<mandatory>true</mandatory>"
    "<name>visitor_name</name>"
    "<order>100</order>"
    "<question_text>Visitor name</question_text>"
    "<show_help>true</show_help>"
    "<sys_class_name>item_option_new</sys_class_name>"
    "<sys_id>1b72ea417113c9de59561298722945e2</sys_id>"
    '<sys_scope display_value="Global">global</sys_scope>'
    "<sys_update_name>item_option_new_1b72ea417113c9de59561298722945e2</sys_update_name>"
    "<type>6</type>"
    "<variable_name>visitor_name</variable_name>"
    "<visible_bundle>true</visible_bundle>"
    "<visible_standalone>true</visible_standalone>"
    "<visible_summary>true</visible_summary>"
    "</item_option_new>"
    "</record_update>"
)


class _MinimalCatalogClient:
    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if table == "sc_catalog":
            return [
                {"sys_id": "service-catalog-sys-id", "title": "Service Catalog", "active": "true"}
            ]
        if table == "sc_category":
            return [
                {
                    "sys_id": "services-category-sys-id",
                    "title": "Services",
                    "active": "true",
                    "sc_catalog": {"value": "service-catalog-sys-id"},
                }
            ]
        if table == "taxonomy":
            return [
                {"sys_id": "employee-taxonomy-sys-id", "name": "Employee", "active": "true"}
            ]
        if table == "topic":
            return [
                {
                    "sys_id": "access-topic-sys-id",
                    "name": "Access issues",
                    "topic_path": "Technology services / Software / Access issues",
                    "active": "true",
                    "taxonomy": {"value": "employee-taxonomy-sys-id"},
                }
            ]
        if table == "taxonomy_content_configuration":
            return [
                {
                    "sys_id": "catalog-item-content-type-sys-id",
                    "name": "Catalog Item",
                    "active": "true",
                }
            ]
        return []


def test_catalog_item_variable_payload_stays_byte_identical_with_shared_builder() -> None:
    updates = catalog_item_customer_updates(
        client=_MinimalCatalogClient(),
        changes=[
            CandidateChange(
                table="sc_cat_item",
                operation="insert",
                fields={
                    "name": "Request Temporary Badge",
                    "short_description": "Request a temporary access badge for a visitor.",
                    "description": (
                        "Use this item when a visitor needs temporary building access."
                    ),
                    "catalog": "Service Catalog",
                    "category": "Services",
                    "taxonomy": "Employee",
                    "employee_center_topic": (
                        "Technology services / Software / Access issues"
                    ),
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
        ],
        remote_update_set_sys_id="remote-update-set-sys-id",
    )

    assert updates[1]["payload"] == _CATALOG_VARIABLE_PAYLOAD_GOLDEN
