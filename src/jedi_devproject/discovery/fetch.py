"""Shared fetch, normalization, and redaction plumbing for discovery surfaces.

Redaction behavior here is a compliance control; do not alter it.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit, urlunsplit

from jedi_devproject.discovery.models import (
    InstanceDiscoveryClient,
    ServiceNowSurfaceContext,
    ServiceNowSurfaceRecord,
    SurfaceName,
)


def _records_surface(
    *,
    surface: SurfaceName,
    source_table: str,
    records: list[dict[str, Any]],
    lookup: dict[str, str],
    required: bool,
    evidence: str,
) -> ServiceNowSurfaceContext:
    return ServiceNowSurfaceContext(
        surface=surface,
        source_table=source_table,
        required=required,
        records=[
            ServiceNowSurfaceRecord(
                source_table=source_table,
                name=_record_name(record),
                active=_optional_bool(record.get("active")),
                summary=_record_summary(record),
                metadata=_record_metadata(record, exclude={"sys_id", "name", "active"}),
            )
            for record in records
        ],
        evidence=[evidence],
        confidence=0.95 if records else 0.0,
        citations=[
            {
                "source_table": source_table,
                "query": _query_string(lookup),
                "record_count": str(len(records)),
            }
        ],
    )


def _table_surface(
    *,
    client: InstanceDiscoveryClient,
    surface: SurfaceName,
    source_table: str,
    lookup: dict[str, str],
    fields: list[str],
    required: bool,
    evidence: str,
    limit: int = 100,
) -> ServiceNowSurfaceContext:
    records = client.fetch_table_records(
        table=source_table,
        lookup=lookup,
        fields=fields,
        limit=limit,
    )
    return ServiceNowSurfaceContext(
        surface=surface,
        source_table=source_table,
        required=required,
        records=[
            ServiceNowSurfaceRecord(
                source_table=source_table,
                name=_record_name(record),
                active=_optional_bool(record.get("active")),
                summary=_record_summary(record),
                metadata=_record_metadata(record, exclude={"sys_id", "name", "active"}),
            )
            for record in records
        ],
        evidence=[evidence],
        confidence=0.95 if records else 0.0,
        citations=[
            {
                "source_table": source_table,
                "query": _query_string(lookup),
                "record_count": str(len(records)),
            }
        ],
    )


def _empty_surface(
    *,
    surface: SurfaceName,
    source_table: str,
    required: bool,
) -> ServiceNowSurfaceContext:
    return ServiceNowSurfaceContext(
        surface=surface,
        source_table=source_table,
        required=required,
        records=[],
        evidence=[],
        confidence=0.0,
        citations=[],
    )


def _unique_record_values(
    records: list[dict[str, Any]],
    *,
    fields: list[str],
) -> list[str]:
    values: list[str] = []
    for record in records:
        for field_name in fields:
            value = _display_or_value(record.get(field_name)).strip()
            if value and value not in values:
                values.append(value)
    return values


def _display_or_value(value: object) -> str:
    if isinstance(value, dict):
        return str(value.get("display_value") or value.get("value") or "")
    return str(value or "")


def _reference_value(value: object) -> str:
    if isinstance(value, dict):
        return str(value.get("value") or value.get("display_value") or "")
    return str(value or "")


def _optional_int(value: object) -> int | None:
    text = str(value or "").strip()
    return int(text) if text.isdigit() else None


def _optional_bool(value: object) -> bool | None:
    text = str(value or "").strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def _record_name(record: dict[str, Any]) -> str:
    for field_name in [
        "topic_path",
        "title",
        "name",
        "short_description",
        "display_text",
        "column_label",
        "element",
    ]:
        value = str(record.get(field_name) or "").strip()
        if value:
            return value
    return "unnamed"


def _record_summary(record: dict[str, Any]) -> str:
    for field_name in ["short_description", "description", "type", "when", "rest_endpoint"]:
        value = str(record.get(field_name) or "").strip()
        if value:
            if field_name == "rest_endpoint":
                return _redact_url(value)
            return value
    return ""


def _record_metadata(
    record: dict[str, Any],
    *,
    exclude: set[str],
) -> dict[str, str]:
    return {
        key: _minimize_metadata_value(key=key, value=value)
        for key, value in record.items()
        if key not in exclude and key != "sys_id"
    }


def _query_string(lookup: dict[str, str]) -> str:
    return "^".join(f"{key}={value}" for key, value in lookup.items())


def _minimize_metadata_value(*, key: str, value: Any) -> str:
    if key in {"script", "condition", "operation_script"}:
        return "[redacted_script_body]"
    if key in {
        "sc_catalog",
        "taxonomy",
        "parent_topic",
        "topic",
        "catalog_item",
        "content_type",
    } and isinstance(value, dict):
        return str(value.get("value") or value.get("display_value") or "")
    text = _display_or_value(value)
    if key in {"rest_endpoint", "endpoint", "url"}:
        return _redact_url(text)
    return text


def _redact_url(value: str) -> str:
    try:
        parts = urlsplit(value)
    except ValueError:
        return "[redacted_url]"
    query = "[redacted_query]" if parts.query else ""
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))
