"""Surface aggregation: required-surface routing and the discovery context bundle."""

from __future__ import annotations

import math
import re

from jedi_devproject.discovery.catalog import (
    _catalog_categories_surface,
    _catalog_definitions_surface,
    _catalog_variable_sets_surface,
    _employee_center_connected_content_surface,
    _employee_center_topics_surface,
)
from jedi_devproject.discovery.cmdb import (
    _cmdb_class_hierarchy_surface,
    _cmdb_data_sources_surface,
    _cmdb_ire_identification_rules_surface,
    _cmdb_ire_reconciliation_rules_surface,
)
from jedi_devproject.discovery.fetch import _table_surface
from jedi_devproject.discovery.flows import _flow_surfaces
from jedi_devproject.discovery.models import (
    EMPTY_REQUIRED_SURFACE_IS_SUFFICIENT,
    InstanceDiscoveryClient,
    ServiceNowSurfaceContext,
    ServiceNowSurfaceContextBundle,
    ServiceNowSurfaceRecord,
    SurfaceName,
)
from jedi_devproject.discovery.schema_form import discover_dictionary_form_context
from jedi_devproject.rag import RetrievalResult
from jedi_devproject.requirement_text import positive_requirement_text

PUBLIC_DOC_CITATION_NON_JSON_DIAGNOSTIC = (
    "public documentation citation contains non-JSON value"
)
PUBLIC_DOC_CONTENT_NON_JSON_DIAGNOSTIC = (
    "public documentation content contains non-JSON value"
)
PUBLIC_DOC_QUERY_NON_JSON_DIAGNOSTIC = (
    "public documentation query contains non-JSON value"
)
PUBLIC_DOC_CONFIDENCE_UNSAFE_DIAGNOSTIC = (
    "public documentation citation confidence is unsafe"
)


def discover_servicenow_surface_context(
    *,
    client: InstanceDiscoveryClient,
    target_table: str,
    story_text: str,
    public_doc_queries: list[str],
    public_doc_results: list[RetrievalResult] | None = None,
    required_surfaces_override: list[SurfaceName] | None = None,
) -> ServiceNowSurfaceContextBundle:
    table_context = discover_dictionary_form_context(client=client, target_table=target_table)
    required_surfaces = required_surfaces_override or _required_surfaces(story_text)
    surfaces = [
        ServiceNowSurfaceContext(
            surface="table_schema",
            source_table="sys_dictionary",
            required="table_schema" in required_surfaces,
            records=[
                ServiceNowSurfaceRecord(
                    source_table="sys_dictionary",
                    name=field.element,
                    active=True,
                    summary=field.column_label,
                    metadata={"internal_type": field.internal_type},
                )
                for field in table_context.fields
            ],
            evidence=[f"sys_dictionary:{target_table}"],
            confidence=1.0 if table_context.fields else 0.0,
            citations=[
                {
                    "source_table": "sys_dictionary",
                    "query": f"name={target_table}",
                    "record_count": str(len(table_context.fields)),
                }
            ],
        ),
        ServiceNowSurfaceContext(
            surface="form_layout",
            source_table="sys_ui_section",
            required="form_layout" in required_surfaces,
            records=[
                ServiceNowSurfaceRecord(
                    source_table="sys_ui_section",
                    name=section.name,
                    active=True,
                    summary=section.caption,
                    metadata={"view_name": section.view_name},
                )
                for section in table_context.form_sections
            ],
            evidence=[f"sys_ui_section:{target_table}"],
            confidence=1.0 if table_context.form_sections else 0.0,
            citations=[
                {
                    "source_table": "sys_ui_section",
                    "query": f"name={target_table}",
                    "record_count": str(len(table_context.form_sections)),
                }
            ],
        ),
        _table_surface(
            client=client,
            surface="business_rules",
            source_table="sys_script",
            lookup={"collection": target_table},
            fields=["name", "active", "when"],
            required="business_rules" in required_surfaces,
            evidence=f"sys_script:{target_table}",
        ),
        _table_surface(
            client=client,
            surface="client_scripts",
            source_table="sys_script_client",
            lookup={"table": target_table},
            fields=["name", "active", "type"],
            required="client_scripts" in required_surfaces,
            evidence=f"sys_script_client:{target_table}",
        ),
        _table_surface(
            client=client,
            surface="ui_policies",
            source_table="sys_ui_policy",
            lookup={"table": target_table},
            fields=["short_description", "active"],
            required="ui_policies" in required_surfaces,
            evidence=f"sys_ui_policy:{target_table}",
        ),
        *_flow_surfaces(client=client, required_surfaces=required_surfaces),
        _table_surface(
            client=client,
            surface="script_includes",
            source_table="sys_script_include",
            lookup={},
            fields=["name", "active"],
            required="script_includes" in required_surfaces,
            evidence="sys_script_include:active",
            limit=25,
        ),
        _table_surface(
            client=client,
            surface="cmdb_discovery_maps",
            source_table="cmdb_ci",
            lookup={"sys_class_name": "cmdb_ci_discovery"},
            fields=["name", "sys_class_name"],
            required="cmdb_discovery_maps" in required_surfaces,
            evidence="cmdb_ci:cmdb_ci_discovery",
            limit=25,
        ),
        _cmdb_ire_identification_rules_surface(
            client=client,
            required="cmdb_ire_identification_rules" in required_surfaces,
        ),
        _cmdb_ire_reconciliation_rules_surface(
            client=client,
            required="cmdb_ire_reconciliation_rules" in required_surfaces,
        ),
        _cmdb_data_sources_surface(
            client=client,
            required="cmdb_data_sources" in required_surfaces,
        ),
        _cmdb_class_hierarchy_surface(
            client=client,
            target_table=target_table,
            required="cmdb_class_hierarchy" in required_surfaces,
        ),
        _table_surface(
            client=client,
            surface="integration_surfaces",
            source_table="sys_rest_message",
            lookup={},
            fields=["name", "rest_endpoint"],
            required="integration_surfaces" in required_surfaces,
            evidence="sys_rest_message",
            limit=25,
        ),
        _public_docs_surface(
            public_doc_queries=public_doc_queries,
            public_doc_results=public_doc_results or [],
            required="public_docs" in required_surfaces,
        ),
        ServiceNowSurfaceContext(
            surface="form_sections",
            source_table="sys_ui_section",
            required="form_sections" in required_surfaces,
            records=[
                ServiceNowSurfaceRecord(
                    source_table="sys_ui_section",
                    name=section.name,
                    active=True,
                    summary=section.caption,
                    metadata={
                        "caption": section.caption,
                        "view_name": section.view_name,
                        "element_count": str(len(section.elements)),
                    },
                )
                for section in table_context.form_sections
            ],
            evidence=[f"sys_ui_section:{target_table}"],
            confidence=1.0 if table_context.form_sections else 0.0,
            citations=[
                {
                    "source_table": "sys_ui_section",
                    "query": f"name={target_table}",
                    "record_count": str(len(table_context.form_sections)),
                }
            ],
        ),
        _catalog_definitions_surface(
            client=client,
            required="catalog_definitions" in required_surfaces,
        ),
        _catalog_categories_surface(
            client=client,
            required="catalog_categories" in required_surfaces,
        ),
        _catalog_variable_sets_surface(
            client=client,
            required="catalog_variable_sets" in required_surfaces,
        ),
        _employee_center_topics_surface(
            client=client,
            required="employee_center_topics" in required_surfaces,
        ),
        _employee_center_connected_content_surface(
            client=client,
            required="employee_center_connected_content" in required_surfaces,
        ),
    ]
    missing_required_surfaces = [
        context.surface
        for context in surfaces
        if context.required
        and (not context.records or context.confidence <= 0.0)
        and context.surface not in EMPTY_REQUIRED_SURFACE_IS_SUFFICIENT
    ]
    evidence = [
        *table_context.evidence,
        *[item for context in surfaces for item in context.evidence],
    ]
    return ServiceNowSurfaceContextBundle(
        target_table=target_table,
        required_surfaces=required_surfaces,
        surfaces=surfaces,
        table_context=table_context,
        public_doc_queries=[
            _public_doc_query_text(query) for query in public_doc_queries
        ],
        public_doc_results=public_doc_results or [],
        missing_required_surfaces=missing_required_surfaces,
        evidence=evidence,
    )


def _public_docs_surface(
    *,
    public_doc_queries: list[str],
    public_doc_results: list[RetrievalResult],
    required: bool,
) -> ServiceNowSurfaceContext:
    return ServiceNowSurfaceContext(
        surface="public_docs",
        source_table="public_web",
        required=required,
        records=[
            ServiceNowSurfaceRecord(
                source_table="public_web",
                name=_public_doc_citation_text(result, "source"),
                active=True,
                summary=_public_doc_content(result),
                metadata={
                    "content_hash": _public_doc_citation_text(result, "content_hash"),
                    "version": _public_doc_citation_version(result),
                    "confidence": _public_doc_citation_confidence(result),
                    "excerpt_chars": str(len(_public_doc_content(result))),
                },
            )
            for result in public_doc_results
        ],
        evidence=[
            f"public_docs:{_public_doc_query_text(query)}"
            for query in public_doc_queries
        ]
        + [
            f"public_web:{_public_doc_citation_text(result, 'content_hash')}"
            for result in public_doc_results
        ],
        confidence=0.8 if public_doc_results else 0.0,
        citations=[
            {
                "source": _public_doc_citation_text(result, "source"),
                "content_hash": _public_doc_citation_text(result, "content_hash"),
                "version": _public_doc_citation_version(result),
                "confidence": _public_doc_citation_confidence(result),
            }
            for result in public_doc_results
        ],
    )


def _public_doc_citation_text(
    result: RetrievalResult,
    field_name: str,
) -> str:
    value = getattr(result.citation, field_name)
    if type(value) is not str:
        raise ValueError(PUBLIC_DOC_CITATION_NON_JSON_DIAGNOSTIC)
    return value


def _public_doc_content(result: RetrievalResult) -> str:
    content = result.content
    if type(content) is not str:
        raise ValueError(PUBLIC_DOC_CONTENT_NON_JSON_DIAGNOSTIC)
    return content


def _public_doc_query_text(query: str) -> str:
    if type(query) is not str:
        raise ValueError(PUBLIC_DOC_QUERY_NON_JSON_DIAGNOSTIC)
    return query


def _public_doc_citation_confidence(result: RetrievalResult) -> str:
    confidence = result.citation.confidence
    if type(confidence) not in {int, float}:
        raise ValueError(PUBLIC_DOC_CONFIDENCE_UNSAFE_DIAGNOSTIC)
    if not math.isfinite(confidence) or confidence < 0 or confidence > 1:
        raise ValueError(PUBLIC_DOC_CONFIDENCE_UNSAFE_DIAGNOSTIC)
    return f"{confidence:.2f}"


def _public_doc_citation_version(result: RetrievalResult) -> str:
    version = result.citation.version
    if type(version) is str:
        return version
    return ""


def _required_surfaces(story_text: str) -> list[SurfaceName]:
    lowered = positive_requirement_text(story_text)
    surfaces: list[SurfaceName] = ["table_schema", "form_layout"]
    keyword_map: list[tuple[SurfaceName, tuple[str, ...]]] = [
        ("business_rules", (r"\bbusiness\s+rules?\b", r"\bserver\s+scripts?\b")),
        (
            "client_scripts",
            (r"\bclient\s+scripts?\b", r"\bonchange\b", r"\bonsubmit\b", r"\bonload\b"),
        ),
        (
            "ui_policies",
            (
                r"\bui\s+polic(?:y|ies)\b",
                r"\bvisible\b",
                r"\bmandatory\b",
                r"\bread-only\b",
            ),
        ),
        ("flows", (r"\bflows?\b", r"\bworkflows?\b", r"\bflow\s+designer\b")),
        ("flow_graph", (r"\bflows?\b", r"\bworkflows?\b", r"\bflow\s+designer\b")),
        ("script_includes", (r"\bscript\s+includes?\b", r"\butility\s+script\b")),
        (
            "cmdb_discovery_maps",
            (r"\bdiscovery(?:\s+map)?s?\b", r"\bcmdb\b"),
        ),
        (
            "cmdb_ire_identification_rules",
            (
                r"\bire\b",
                r"\bidentification\s+rules?\b",
                r"\bprimary\s+(?:unique\s+)?identifier\b",
                r"\bserial\s+number\b.*\breconciliation\b",
            ),
        ),
        (
            "cmdb_ire_reconciliation_rules",
            (
                r"\bire\b",
                r"\breconciliation\s+rules?\b",
                r"\breconciliation\s+runs?\b",
                r"\bserial\s+number\b.*\breconciliation\b",
            ),
        ),
        (
            "cmdb_data_sources",
            (
                r"\bsccm\b",
                r"\bintune\b",
                r"\bworkspace\s+one\b",
                r"\bazure\s+arc\b",
                r"\bdata\s+sources?\b",
            ),
        ),
        (
            "cmdb_class_hierarchy",
            (
                r"\bire\b",
                r"\bidentification\s+rules?\b",
                r"\breconciliation\s+rules?\b",
                r"\breconciliation\s+runs?\b",
                r"\bserial\s+number\b.*\breconciliation\b",
            ),
        ),
        ("integration_surfaces", (r"\bintegrations?\b", r"\brest\s+message\b", r"\bapi\b")),
        (
            "public_docs",
            (
                r"\bdocumentation\b",
                r"\bpublic\s+documentation\b",
                r"\bpublic\s+docs\b",
                r"\bdocs\b",
            ),
        ),
        (
            "catalog_definitions",
            (
                r"\bcatalog\s+items?\b",
                r"\brecord\s+producers?\b",
                r"\bservice\s+catalog\b",
                r"\bemployee\s+center\b",
            ),
        ),
        (
            "catalog_categories",
            (
                r"\bcatalog\s+items?\b",
                r"\brecord\s+producers?\b",
                r"\bservice\s+catalog\b",
                r"\bemployee\s+center\b",
            ),
        ),
        (
            "catalog_variable_sets",
            (r"\bvariable\s+sets?\b",),
        ),
        (
            "employee_center_topics",
            (r"\bemployee\s+center\b", r"\btopics?\b", r"\btaxonom(?:y|ies)\b"),
        ),
        (
            "employee_center_connected_content",
            (r"\bemployee\s+center\b", r"\bconnected\s+content\b", r"\btopics?\b"),
        ),
    ]
    for surface, patterns in keyword_map:
        if any(re.search(pattern, lowered) for pattern in patterns) and surface not in surfaces:
            surfaces.append(surface)
    return surfaces
