"""Context assembly for implementation packet building: context sufficiency scoring, the
context dossier handed to the model, read-only XML shape references, and builder maturity
context entries for the required surfaces."""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic_core import PydanticSerializationError

from jedi_devproject.builder_maturity import (
    MaturityEvidenceProvider,
    baseline_builder_maturity_for_surface,
    score_builder_maturity,
)
from jedi_devproject.instance_discovery import (
    InstanceDiscoveryContext,
    ServiceNowSurfaceContextBundle,
)
from jedi_devproject.models import Story
from jedi_devproject.packet_model import (
    PacketStory,
    _compact_instance_context,
    _compact_surface_context_bundle,
    _model_context_elisions,
)

CONTEXT_DOSSIER_DTO_NON_FINITE_DIAGNOSTIC = (
    "context dossier DTO payload contains non-finite numeric values"
)
CONTEXT_DOSSIER_DTO_NON_JSON_DIAGNOSTIC = (
    "context dossier DTO payload contains non-JSON values"
)


def _context_model_payload(
    model: BaseModel,
    *,
    diagnostic: str,
    non_json_diagnostic: str = CONTEXT_DOSSIER_DTO_NON_JSON_DIAGNOSTIC,
) -> dict[str, Any]:
    try:
        _ensure_context_dto_payload_json_safe(
            model.model_dump(mode="python", warnings=False)
        )
        json.dumps(
            model.model_dump(mode="json", warnings=False),
            sort_keys=True,
            allow_nan=False,
        )
    except PydanticSerializationError:
        raise ValueError(non_json_diagnostic) from None
    except ValueError:
        raise ValueError(diagnostic) from None
    except TypeError:
        raise ValueError(non_json_diagnostic) from None
    return model.model_dump(mode="json", warnings=False)


def _ensure_context_dto_payload_json_safe(value: Any) -> None:
    if (
        value is None
        or type(value) is str
        or type(value) is bool
        or type(value) is int
        or type(value) is date
        or isinstance(value, Enum)
    ):
        return
    if type(value) is float:
        if math.isfinite(value):
            return
        raise ValueError("non-finite context dossier DTO payload value")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("non-JSON context dossier DTO payload key")
            _ensure_context_dto_payload_json_safe(item)
        return
    if type(value) is list:
        for item in value:
            _ensure_context_dto_payload_json_safe(item)
        return
    if type(value) is tuple:
        for item in value:
            _ensure_context_dto_payload_json_safe(item)
        return
    raise TypeError("non-JSON context dossier DTO payload value")


def _context_sufficiency(
    *,
    discovery_context: InstanceDiscoveryContext | None,
    surface_context_bundle: ServiceNowSurfaceContextBundle | None = None,
) -> dict[str, Any]:
    if discovery_context is None:
        return {
            "status": "needs_retrieval",
            "score": 0.35,
            "missing_context": ["live_instance_context"],
            "evidence": [],
        }
    missing_context: list[str] = []
    required_surfaces = (
        surface_context_bundle.required_surfaces if surface_context_bundle is not None else []
    )
    requires_table_context = (
        surface_context_bundle is None
        or "table_schema" in required_surfaces
        or "form_layout" in required_surfaces
    )
    if requires_table_context and not discovery_context.table_exists:
        missing_context.append("target_table")
    if (
        surface_context_bundle is None or "form_layout" in required_surfaces
    ) and not discovery_context.supports_custom_fields:
        missing_context.append("custom_field_support")
    if (
        surface_context_bundle is None or "form_layout" in required_surfaces
    ) and not discovery_context.form_sections:
        missing_context.append("form_sections")
    if surface_context_bundle is not None:
        missing_context.extend(surface_context_bundle.missing_required_surfaces)
    status = "sufficient" if not missing_context else "insufficient"
    score = 0.95 if status == "sufficient" else 0.2
    return {
        "status": status,
        "score": score,
        "missing_context": missing_context,
        "evidence": (
            surface_context_bundle.evidence
            if surface_context_bundle is not None
            else discovery_context.evidence
        ),
    }


def _context_dossier(
    *,
    story: Story,
    assessment: dict[str, Any],
    discovery_context: InstanceDiscoveryContext | None,
    surface_context_bundle: ServiceNowSurfaceContextBundle | None,
    context_sufficiency: dict[str, Any],
    surface_operation_plan: dict[str, Any] | None,
    maturity_provider: MaturityEvidenceProvider | None,
) -> dict[str, Any]:
    target_table = (
        surface_context_bundle.target_table
        if surface_context_bundle is not None
        else discovery_context.target_table
        if discovery_context is not None
        else (story.affected_tables[0] if story.affected_tables else "")
    )
    required_surfaces = (
        surface_context_bundle.required_surfaces if surface_context_bundle is not None else []
    )
    instance_context_payload = (
        _context_model_payload(
            discovery_context,
            diagnostic=CONTEXT_DOSSIER_DTO_NON_FINITE_DIAGNOSTIC,
        )
        if discovery_context is not None
        else None
    )
    bundle_payload = (
        _context_model_payload(
            surface_context_bundle,
            diagnostic=CONTEXT_DOSSIER_DTO_NON_FINITE_DIAGNOSTIC,
        )
        if surface_context_bundle is not None
        else None
    )
    dossier = {
        "story": PacketStory(
            number=story.number,
            short_description=story.short_description,
            description=story.description,
            acceptance_criteria=story.acceptance_criteria,
            story_points=story.story_points,
            priority=story.priority,
            state=story.state,
            affected_tables=story.affected_tables,
        ).model_dump(),
        "target": {
            "table": target_table,
            "required_surfaces": list(required_surfaces),
        },
        "capability_assessment": assessment,
        "surface_operation_plan": surface_operation_plan,
        "context_sufficiency": context_sufficiency,
        "instance_context": instance_context_payload,
        "instance_context_bundle": bundle_payload,
        "xml_shape_references": _xml_shape_references(
            required_surfaces=required_surfaces,
            surface_operation_plan=surface_operation_plan,
        ),
        "builder_maturity": _builder_maturity_context(
            required_surfaces=required_surfaces,
            maturity_provider=maturity_provider,
        ),
    }
    elisions = _model_context_elisions(
        instance_context=(
            None
            if bundle_payload is not None
            else _compact_instance_context(instance_context_payload)
        ),
        instance_context_bundle=_compact_surface_context_bundle(bundle_payload),
    )
    if elisions:
        dossier["model_context_elisions"] = elisions
    return dossier


def _xml_shape_references(
    *,
    required_surfaces: Sequence[str],
    surface_operation_plan: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    planned_kinds = {
        str(operation.get("kind"))
        for operation in (surface_operation_plan or {}).get("operations", [])
        if isinstance(operation, dict)
    }
    if "form_layout" in required_surfaces or "form_layout.section.remove" in planned_kinds:
        references.append(
            {
                "surface": "form_layout",
                "record_type": "sys_ui_section",
                "operation": "delete",
                "required_records": ["sys_ui_section", "sys_ui_element"],
                "important_fields": [
                    "sys_id",
                    "caption",
                    "name",
                    "view",
                    "sys_update_name",
                ],
                "notes": (
                    "Reference only. Use this to reason about structured changes; "
                    "do not output raw XML."
                ),
            }
        )
    return references


def _builder_maturity_context(
    *,
    required_surfaces: Sequence[str],
    maturity_provider: MaturityEvidenceProvider | None,
) -> list[dict[str, Any]]:
    surfaces = list(dict.fromkeys(required_surfaces))
    if not surfaces:
        return []
    notes = "Builder maturity adjusts confidence and routing; it does not suppress reasoning."
    entries: list[dict[str, Any]] = []
    for surface in surfaces:
        if maturity_provider is None:
            entries.append(
                {
                    "surface": surface,
                    "score": baseline_builder_maturity_for_surface(surface),
                    "notes": notes,
                }
            )
            continue
        scored = score_builder_maturity(
            surface=surface,
            evidence=maturity_provider.maturity_evidence_for_surface(surface),
        )
        entry: dict[str, Any] = {
            "surface": surface,
            "score": scored.score,
            "score_source": scored.source,
            "notes": notes,
        }
        if scored.source == "evidence_adjusted":
            entry["evidence_samples"] = scored.evidence_samples
        entries.append(entry)
    return entries
