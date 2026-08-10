"""Shared, import-light data layer for implementation packets: the packet task and
context-limit constants, the ``PacketStory`` and ``ImplementationPacket`` models, and the
pure dict compaction/elision helpers ``ImplementationPacket.to_model_payload`` uses to
bound the context shipped to the model."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from jedi_devproject.context_escalation import plan_context_escalation
from jedi_devproject.models import RetrievalCitation

IMPLEMENTATION_PACKET_TASK = "generate_implementation_candidate"
MODEL_CONTEXT_RECORD_LIMIT = 25
MODEL_CONTEXT_SECTION_LIMIT = 3
AUTOMATED_HANDOFF_BUILDER_MATURITY_THRESHOLD = 0.75


class PacketStory(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    number: str
    short_description: str
    description: str
    acceptance_criteria: str | None = None
    story_points: float
    priority: int
    state: str
    affected_tables: list[str] = Field(default_factory=list)


class ImplementationPacket(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    task: str
    provider_id: str
    story: PacketStory
    safety_decision: str
    safety_reasons: list[str]
    risk_score: float
    allowed_tables: list[str]
    allowed_operations: list[str]
    capability_assessment: dict[str, Any] = Field(default_factory=dict)
    normalized_intent: dict[str, Any] | None = None
    surface_operation_plan: dict[str, Any] | None = None
    instance_context: dict[str, Any] | None = None
    instance_context_bundle: dict[str, Any] | None = None
    context_dossier: dict[str, Any] = Field(default_factory=dict)
    context_sufficiency: dict[str, Any] = Field(default_factory=dict)
    context_sections: dict[str, str]
    retrieval_citations: list[RetrievalCitation]
    output_contract: dict[str, Any]

    def to_model_payload(self) -> dict[str, Any]:
        instance_context = (
            None
            if self.instance_context_bundle is not None
            else _compact_instance_context(self.instance_context)
        )
        instance_context_bundle = _compact_surface_context_bundle(self.instance_context_bundle)
        controls: dict[str, Any] = {
            "safety_decision": self.safety_decision,
            "safety_reasons": self.safety_reasons,
            "risk_score": self.risk_score,
            "allowed_tables": self.allowed_tables,
            "allowed_operations": self.allowed_operations,
            "capability_assessment": self.capability_assessment,
            "normalized_intent": self.normalized_intent,
            "surface_operation_plan": self.surface_operation_plan,
            "context_sufficiency": self.context_sufficiency,
            "context_escalation": plan_context_escalation(self.context_sufficiency).model_dump(
                mode="json"
            ),
        }
        elisions = _model_context_elisions(
            instance_context=instance_context,
            instance_context_bundle=instance_context_bundle,
        )
        if elisions:
            controls["model_context_elisions"] = elisions
        return {
            "task": self.task,
            "provider_id": self.provider_id,
            "story": self.story.model_dump(),
            "controls": controls,
            "instance_context": instance_context,
            "instance_context_bundle": instance_context_bundle,
            "context_dossier": _compact_context_dossier(self.context_dossier),
            "context": self.context_sections,
            "citations": [
                citation.model_dump(mode="json") for citation in self.retrieval_citations
            ],
            "output_contract": self.output_contract,
        }


def _compact_instance_context(context: dict[str, Any] | None) -> dict[str, Any] | None:
    if context is None:
        return None
    fields = list(context.get("fields", []))
    sections = list(context.get("form_sections", []))
    compacted = {
        **context,
        "fields": fields[:MODEL_CONTEXT_RECORD_LIMIT],
        "form_sections": [
            _compact_form_section(section)
            for section in sections[:MODEL_CONTEXT_SECTION_LIMIT]
            if isinstance(section, dict)
        ],
    }
    elisions: list[dict[str, Any]] = []
    if len(fields) > MODEL_CONTEXT_RECORD_LIMIT:
        elisions.append(_elision("fields", shown=MODEL_CONTEXT_RECORD_LIMIT, total=len(fields)))
    if len(sections) > MODEL_CONTEXT_SECTION_LIMIT:
        elisions.append(
            _elision(
                "form_sections",
                shown=MODEL_CONTEXT_SECTION_LIMIT,
                total=len(sections),
                elided_items=[
                    _form_section_label(section)
                    for section in sections[MODEL_CONTEXT_SECTION_LIMIT:]
                    if isinstance(section, dict)
                ],
            )
        )
    if elisions:
        compacted["elisions"] = elisions
    return compacted


def _compact_form_section(section: dict[str, Any]) -> dict[str, Any]:
    elements = list(section.get("elements", []))
    compacted = {**section, "elements": elements[:MODEL_CONTEXT_RECORD_LIMIT]}
    if len(elements) > MODEL_CONTEXT_RECORD_LIMIT:
        compacted["elisions"] = [
            _elision("elements", shown=MODEL_CONTEXT_RECORD_LIMIT, total=len(elements))
        ]
    return compacted


def _form_section_label(section: dict[str, Any]) -> str:
    return str(
        section.get("caption") or section.get("name") or section.get("sys_id") or "unnamed_section"
    )


def _compact_surface_context_bundle(
    bundle: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if bundle is None:
        return None
    required_surfaces = set(str(surface) for surface in bundle.get("required_surfaces", []))
    surfaces = [surface for surface in bundle.get("surfaces", []) if isinstance(surface, dict)]
    kept_surfaces = [
        surface for surface in surfaces if str(surface.get("surface")) in required_surfaces
    ]
    compacted = {
        **bundle,
        "table_context": _compact_instance_context(bundle.get("table_context")),
        "surfaces": [_compact_surface_context(surface) for surface in kept_surfaces],
    }
    if len(kept_surfaces) < len(surfaces):
        compacted["elisions"] = [
            _elision(
                "surfaces",
                shown=len(kept_surfaces),
                total=len(surfaces),
                elided_items=[
                    str(surface.get("surface"))
                    for surface in surfaces
                    if str(surface.get("surface")) not in required_surfaces
                ],
            )
        ]
    return compacted


def _compact_surface_context(surface: dict[str, Any]) -> dict[str, Any]:
    records = list(surface.get("records", []))
    citations = list(surface.get("citations", []))
    compacted = {
        **surface,
        "records": records[:MODEL_CONTEXT_RECORD_LIMIT],
        "citations": citations[:MODEL_CONTEXT_RECORD_LIMIT],
    }
    elisions: list[dict[str, Any]] = []
    if len(records) > MODEL_CONTEXT_RECORD_LIMIT:
        elisions.append(_elision("records", shown=MODEL_CONTEXT_RECORD_LIMIT, total=len(records)))
    if len(citations) > MODEL_CONTEXT_RECORD_LIMIT:
        elisions.append(
            _elision("citations", shown=MODEL_CONTEXT_RECORD_LIMIT, total=len(citations))
        )
    if elisions:
        compacted["elisions"] = elisions
    return compacted


def _elision(
    content: str,
    *,
    shown: int,
    total: int,
    elided_items: list[str] | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "content": content,
        "shown": shown,
        "total": total,
        "elided": total - shown,
    }
    if elided_items:
        entry["elided_items"] = elided_items
    return entry


def _model_context_elisions(
    *,
    instance_context: dict[str, Any] | None,
    instance_context_bundle: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Summarize every truncation the model payload applied, with locations.

    The summary mirrors the model payload exactly: the instance context only
    contributes when no surface context bundle is present, matching
    ``to_model_payload``.
    """
    if instance_context_bundle is not None:
        entries = [
            _located_elision(entry, "instance_context_bundle")
            for entry in instance_context_bundle.get("elisions", [])
        ]
        entries.extend(
            _instance_context_elisions(
                instance_context_bundle.get("table_context"),
                prefix="instance_context_bundle.table_context",
            )
        )
        for surface in instance_context_bundle.get("surfaces", []):
            prefix = f"instance_context_bundle.surfaces[{surface.get('surface')}]"
            entries.extend(
                _located_elision(entry, prefix) for entry in surface.get("elisions", [])
            )
        return entries
    return _instance_context_elisions(instance_context, prefix="instance_context")


def _instance_context_elisions(context: Any, *, prefix: str) -> list[dict[str, Any]]:
    if not isinstance(context, dict):
        return []
    entries = [_located_elision(entry, prefix) for entry in context.get("elisions", [])]
    for section in context.get("form_sections", []):
        section_prefix = f"{prefix}.form_sections[{_form_section_label(section)}]"
        entries.extend(
            _located_elision(entry, section_prefix) for entry in section.get("elisions", [])
        )
    return entries


def _located_elision(entry: dict[str, Any], prefix: str) -> dict[str, Any]:
    located = {key: value for key, value in entry.items() if key != "content"}
    return {"location": f"{prefix}.{entry['content']}", **located}


def _compact_context_dossier(dossier: dict[str, Any]) -> dict[str, Any]:
    if not dossier:
        return {}
    compacted = dict(dossier)
    bundle = compacted.get("instance_context_bundle")
    if isinstance(bundle, dict):
        compacted["instance_context_bundle"] = _compact_surface_context_bundle(bundle)
    context = compacted.get("instance_context")
    if isinstance(context, dict):
        compacted["instance_context"] = _compact_instance_context(context)
    return compacted
