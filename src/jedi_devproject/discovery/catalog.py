"""Service catalog and Employee Center discovery surfaces."""

from __future__ import annotations

from jedi_devproject.discovery.fetch import (
    _display_or_value,
    _empty_surface,
    _optional_bool,
    _record_name,
    _reference_value,
    _surface_records,
    _table_surface,
)
from jedi_devproject.discovery.models import (
    InstanceDiscoveryClient,
    ServiceNowSurfaceContext,
    ServiceNowSurfaceRecord,
)


def _catalog_definitions_surface(
    *,
    client: InstanceDiscoveryClient,
    required: bool,
) -> ServiceNowSurfaceContext:
    if not required:
        return _empty_surface(
            surface="catalog_definitions",
            source_table="sc_catalog",
            required=False,
        )
    return _table_surface(
        client=client,
        surface="catalog_definitions",
        source_table="sc_catalog",
        lookup={},
        fields=["sys_id", "title", "active"],
        required=True,
        evidence="sc_catalog:active",
        limit=100,
    )


def _catalog_categories_surface(
    *,
    client: InstanceDiscoveryClient,
    required: bool,
) -> ServiceNowSurfaceContext:
    if not required:
        return _empty_surface(
            surface="catalog_categories",
            source_table="sc_category",
            required=False,
        )
    return _table_surface(
        client=client,
        surface="catalog_categories",
        source_table="sc_category",
        lookup={},
        fields=["sys_id", "title", "active", "sc_catalog"],
        required=True,
        evidence="sc_category:active",
        limit=250,
    )


def _catalog_variable_sets_surface(
    *,
    client: InstanceDiscoveryClient,
    required: bool,
) -> ServiceNowSurfaceContext:
    """Existing shared variable sets (item_option_new_set) available to attach.

    The capability only attaches existing sets; when this surface is required
    and empty, the bundle reports it missing and the story fails closed to
    manual review instead of inventing or creating a set.
    """
    if not required:
        return _empty_surface(
            surface="catalog_variable_sets",
            source_table="item_option_new_set",
            required=False,
        )
    return _table_surface(
        client=client,
        surface="catalog_variable_sets",
        source_table="item_option_new_set",
        lookup={},
        fields=["sys_id", "title", "internal_name", "active"],
        required=True,
        evidence="item_option_new_set:active",
        limit=250,
    )


def _employee_center_topics_surface(
    *,
    client: InstanceDiscoveryClient,
    required: bool,
) -> ServiceNowSurfaceContext:
    if not required:
        return _empty_surface(
            surface="employee_center_topics",
            source_table="topic",
            required=False,
        )
    taxonomy_records = _surface_records(
        client.fetch_table_records(
            table="taxonomy",
            lookup={},
            fields=["sys_id", "name", "active"],
            limit=100,
        )
    )
    topic_records = _surface_records(
        client.fetch_table_records(
            table="topic",
            lookup={},
            fields=["sys_id", "name", "topic_path", "active", "taxonomy", "parent_topic"],
            limit=250,
        )
    )
    records = [
        ServiceNowSurfaceRecord(
            source_table="topic",
            name=_record_name(record),
            active=_optional_bool(record.get("active")),
            summary=_display_or_value(record.get("name")),
            metadata={
                "taxonomy": _reference_value(record.get("taxonomy")),
                "parent_topic": _reference_value(record.get("parent_topic")),
            },
        )
        for record in topic_records
    ]
    return ServiceNowSurfaceContext(
        surface="employee_center_topics",
        source_table="topic",
        required=required,
        records=records,
        evidence=["taxonomy:active", "topic:active"],
        confidence=0.95 if records and taxonomy_records else 0.0,
        citations=[
            {
                "source_table": "taxonomy",
                "query": "",
                "record_count": str(len(taxonomy_records)),
            },
            {
                "source_table": "topic",
                "query": "",
                "record_count": str(len(topic_records)),
            },
        ],
    )


def _employee_center_connected_content_surface(
    *,
    client: InstanceDiscoveryClient,
    required: bool,
) -> ServiceNowSurfaceContext:
    if not required:
        return _empty_surface(
            surface="employee_center_connected_content",
            source_table="taxonomy_content_configuration",
            required=False,
        )
    content_types = _surface_records(
        client.fetch_table_records(
            table="taxonomy_content_configuration",
            lookup={},
            fields=["sys_id", "name", "active"],
            limit=100,
        )
    )
    connected_content = _surface_records(
        client.fetch_table_records(
            table="m2m_connected_content",
            lookup={},
            fields=["sys_id", "topic", "catalog_item", "content_type"],
            limit=100,
        )
    )
    catalog_item_types = [
        record
        for record in content_types
        if _record_name(record).strip().lower() == "catalog item"
        and _optional_bool(record.get("active")) is not False
    ]
    records = [
        ServiceNowSurfaceRecord(
            source_table="taxonomy_content_configuration",
            name=_record_name(record),
            active=_optional_bool(record.get("active")),
            summary="Employee Center connected content type.",
            metadata={"sys_id": _display_or_value(record.get("sys_id"))},
        )
        for record in catalog_item_types
    ]
    return ServiceNowSurfaceContext(
        surface="employee_center_connected_content",
        source_table="taxonomy_content_configuration",
        required=required,
        records=records,
        evidence=["taxonomy_content_configuration:active", "m2m_connected_content"],
        confidence=0.95 if records else 0.0,
        citations=[
            {
                "source_table": "taxonomy_content_configuration",
                "query": "",
                "record_count": str(len(content_types)),
            },
            {
                "source_table": "m2m_connected_content",
                "query": "",
                "record_count": str(len(connected_content)),
            },
        ],
    )
