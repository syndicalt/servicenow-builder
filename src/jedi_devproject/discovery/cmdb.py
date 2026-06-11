"""CMDB IRE, data source, and class hierarchy discovery surfaces."""

from __future__ import annotations

from jedi_devproject.discovery.fetch import (
    _display_or_value,
    _empty_surface,
    _optional_bool,
    _record_metadata,
    _record_name,
    _records_surface,
    _table_surface,
)
from jedi_devproject.discovery.models import (
    InstanceDiscoveryClient,
    ServiceNowSurfaceContext,
    ServiceNowSurfaceRecord,
)


def _cmdb_ire_identification_rules_surface(
    *,
    client: InstanceDiscoveryClient,
    required: bool,
) -> ServiceNowSurfaceContext:
    if not required:
        return _empty_surface(
            surface="cmdb_ire_identification_rules",
            source_table="cmdb_identifier",
            required=False,
        )
    identifier_records = client.fetch_table_records(
        table="cmdb_identifier",
        lookup={},
        fields=["sys_id", "name", "applies_to", "active"],
        limit=250,
    )
    entry_records = client.fetch_table_records(
        table="cmdb_identifier_entry",
        lookup={},
        fields=["sys_id", "identifier", "priority", "attributes", "active"],
        limit=500,
    )
    records = [
        ServiceNowSurfaceRecord(
            source_table="cmdb_identifier",
            name=_record_name(record),
            active=_optional_bool(record.get("active")),
            summary=_display_or_value(record.get("applies_to")),
            metadata=_record_metadata(record, exclude={"sys_id", "name", "active"}),
        )
        for record in identifier_records
    ]
    records.extend(
        ServiceNowSurfaceRecord(
            source_table="cmdb_identifier_entry",
            name=_record_name(record),
            active=_optional_bool(record.get("active")),
            summary=_display_or_value(record.get("attributes")),
            metadata=_record_metadata(record, exclude={"sys_id", "name", "active"}),
        )
        for record in entry_records
    )
    return ServiceNowSurfaceContext(
        surface="cmdb_ire_identification_rules",
        source_table="cmdb_identifier",
        required=True,
        records=records,
        evidence=["cmdb_identifier", "cmdb_identifier_entry"],
        confidence=0.95 if records else 0.0,
        citations=[
            {
                "source_table": "cmdb_identifier",
                "query": "",
                "record_count": str(len(identifier_records)),
            },
            {
                "source_table": "cmdb_identifier_entry",
                "query": "",
                "record_count": str(len(entry_records)),
            },
        ],
    )


def _cmdb_ire_reconciliation_rules_surface(
    *,
    client: InstanceDiscoveryClient,
    required: bool,
) -> ServiceNowSurfaceContext:
    if not required:
        return _empty_surface(
            surface="cmdb_ire_reconciliation_rules",
            source_table="cmdb_reconciliation_definition",
            required=False,
        )
    return _table_surface(
        client=client,
        surface="cmdb_ire_reconciliation_rules",
        source_table="cmdb_reconciliation_definition",
        lookup={},
        fields=["sys_id", "name", "applies_to", "data_source", "active"],
        required=True,
        evidence="cmdb_reconciliation_definition",
        limit=250,
    )


def _cmdb_data_sources_surface(
    *,
    client: InstanceDiscoveryClient,
    required: bool,
) -> ServiceNowSurfaceContext:
    if not required:
        return _empty_surface(
            surface="cmdb_data_sources",
            source_table="sys_object_source",
            required=False,
        )
    return _table_surface(
        client=client,
        surface="cmdb_data_sources",
        source_table="sys_object_source",
        lookup={},
        fields=["sys_id", "source_name", "target_sys_class_name", "name"],
        required=True,
        evidence="sys_object_source",
        limit=250,
    )


def _cmdb_class_hierarchy_surface(
    *,
    client: InstanceDiscoveryClient,
    target_table: str,
    required: bool,
) -> ServiceNowSurfaceContext:
    if not required:
        return _empty_surface(
            surface="cmdb_class_hierarchy",
            source_table="sys_db_object",
            required=False,
        )
    records = client.fetch_table_records(
        table="sys_db_object",
        lookup={},
        fields=["sys_id", "name", "label", "super_class"],
        limit=500,
    )
    cmdb_records = [
        record
        for record in records
        if _display_or_value(record.get("name")).startswith("cmdb_")
        or _display_or_value(record.get("name")) == target_table
    ]
    return _records_surface(
        surface="cmdb_class_hierarchy",
        source_table="sys_db_object",
        records=cmdb_records,
        lookup={},
        required=True,
        evidence=f"sys_db_object:cmdb_class_hierarchy:{target_table}",
    )
