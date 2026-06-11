from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

from pydantic import BaseModel, Field

from jedi_devproject.builder_maturity import (
    MaturityEvidenceProvider,
    baseline_builder_maturity_for_surface,
    builder_maturity_for_change_tables,
    score_builder_maturity,
)
from jedi_devproject.capabilities import Capability, SuitabilityOutcome
from jedi_devproject.capability_analysis import analyze_story_capabilities
from jedi_devproject.context_escalation import plan_context_escalation
from jedi_devproject.instance_discovery import (
    InstanceDiscoveryContext,
    ServiceNowSurfaceContextBundle,
)
from jedi_devproject.models import (
    CandidateChange,
    CandidateStatus,
    ProviderPolicy,
    RetrievalCitation,
    Story,
    UpdateSetCandidate,
    stable_artifact_hash,
)
from jedi_devproject.providers import (
    ModelProvider,
    ModelResponseError,
    ProviderBlocked,
    _validate_response,
)
from jedi_devproject.rag import SpecializedRags
from jedi_devproject.safety import AllowlistPolicy
from jedi_devproject.surface_planning import (
    SurfaceOperationKind,
    SurfaceOperationStatus,
    plan_surface_operations,
)

IMPLEMENTATION_PACKET_TASK = "generate_implementation_candidate"
MODEL_CONTEXT_RECORD_LIMIT = 25
MODEL_CONTEXT_SECTION_LIMIT = 3
AUTOMATED_HANDOFF_BUILDER_MATURITY_THRESHOLD = 0.75


class PacketStory(BaseModel):
    number: str
    short_description: str
    description: str
    acceptance_criteria: str | None = None
    story_points: float
    priority: int
    state: str
    affected_tables: list[str] = Field(default_factory=list)


class ImplementationPacket(BaseModel):
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


def build_implementation_packet(
    *,
    story: Story,
    policy: AllowlistPolicy,
    provider_policy: ProviderPolicy,
    rags: SpecializedRags,
    discovery_context: InstanceDiscoveryContext | None = None,
    surface_context_bundle: ServiceNowSurfaceContextBundle | None = None,
    maturity_provider: MaturityEvidenceProvider | None = None,
) -> ImplementationPacket:
    assessment = analyze_story_capabilities(story)
    safety_reasons = [
        *assessment.reasons,
        *[f"missing detail: {detail}" for detail in assessment.missing_details],
        *[
            f"unsupported capability: {capability.value}"
            for capability in sorted(
                assessment.unsupported_capabilities,
                key=lambda item: item.value,
            )
        ],
    ]
    query = " ".join(
        text
        for text in [
            story.short_description,
            story.description,
            story.acceptance_criteria or "",
            " ".join(story.affected_tables),
        ]
        if text
    )
    retrieved = rags.retrieve_required_context(query)
    context_sections = {
        domain.value: "\n".join(result.content for result in results)
        for domain, results in retrieved.items()
    }
    citations = [result.citation for results in retrieved.values() for result in results]
    surface_operation_plan = plan_surface_operations(assessment.automation_intent)
    surface_operation_plan_payload = (
        surface_operation_plan.model_dump(mode="json")
        if surface_operation_plan.operations
        else None
    )
    context_sufficiency = _context_sufficiency(
        discovery_context=discovery_context,
        surface_context_bundle=surface_context_bundle,
    )

    return ImplementationPacket(
        task=IMPLEMENTATION_PACKET_TASK,
        provider_id=provider_policy.provider_id,
        story=PacketStory(
            number=story.number,
            short_description=story.short_description,
            description=story.description,
            acceptance_criteria=story.acceptance_criteria,
            story_points=story.story_points,
            priority=story.priority,
            state=story.state,
            affected_tables=story.affected_tables,
        ),
        safety_decision=assessment.outcome.value,
        safety_reasons=safety_reasons,
        risk_score=assessment.risk_score,
        allowed_tables=sorted(policy.tables),
        allowed_operations=sorted(policy.operations),
        capability_assessment=assessment.model_dump(mode="json"),
        normalized_intent=(
            assessment.automation_intent
            if assessment.automation_intent is not None
            else (
                assessment.intent.model_dump(mode="json")
                if assessment.intent is not None
                else None
            )
        ),
        surface_operation_plan=surface_operation_plan_payload,
        instance_context=(
            discovery_context.model_dump(mode="json") if discovery_context is not None else None
        ),
        instance_context_bundle=(
            surface_context_bundle.model_dump(mode="json")
            if surface_context_bundle is not None
            else None
        ),
        context_dossier=_context_dossier(
            story=story,
            assessment=assessment.model_dump(mode="json"),
            discovery_context=discovery_context,
            surface_context_bundle=surface_context_bundle,
            context_sufficiency=context_sufficiency,
            surface_operation_plan=surface_operation_plan_payload,
            maturity_provider=maturity_provider,
        ),
        context_sufficiency=context_sufficiency,
        context_sections=context_sections,
        retrieval_citations=citations,
        output_contract={
            "format": "structured_candidate_change_only",
            "must_return_manual_review_when_uncertain": True,
            "must_not_invent_tables_fields_sys_ids": True,
            "must_not_output_raw_xml": True,
            "xml_shape_references_are_read_only": True,
            "must_include_test_plan": True,
            "must_include_rollback_notes": True,
            "capabilities": sorted(capability.value for capability in assessment.capabilities),
            "must_follow_normalized_intent": True,
            "must_use_discovered_instance_context": True,
            "must_use_public_docs_only_with_citations": True,
            "must_not_treat_public_docs_as_instance_truth": True,
            "public_web_access_mode": (
                "worker_live_web"
                if surface_context_bundle is not None
                and surface_context_bundle.public_doc_results
                else "none"
            ),
        },
    )


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
        discovery_context.model_dump(mode="json") if discovery_context is not None else None
    )
    bundle_payload = (
        surface_context_bundle.model_dump(mode="json")
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


def generate_implementation_candidate(
    *,
    story: Story,
    policy: AllowlistPolicy,
    provider_policy: ProviderPolicy,
    rags: SpecializedRags,
    provider: ModelProvider,
) -> dict[str, Any]:
    packet = _build_allowed_packet(
        story=story,
        policy=policy,
        provider_policy=provider_policy,
        rags=rags,
    )
    response = _normalize_placeholder_sys_ids(provider.generate(packet.to_model_payload()))
    _validate_response(
        response,
        allowed_tables=policy.tables,
        allowed_operations=policy.operations,
        allowed_sys_ids=set(),
    )
    _validate_implementation_contract(response)
    response = _reconcile_response_with_packet(packet=packet, response=response)
    _validate_response(
        response,
        allowed_tables=policy.tables,
        allowed_operations=policy.operations,
        allowed_sys_ids=set(),
    )
    _validate_implementation_contract(response)
    _validate_response_tables_match_capability(packet=packet, response=response)
    return response


def generate_implementation_update_set_candidate(
    *,
    story: Story,
    policy: AllowlistPolicy,
    provider_policy: ProviderPolicy,
    rags: SpecializedRags,
    provider: ModelProvider,
    classifier_gate: bool = True,
) -> UpdateSetCandidate:
    packet = _build_allowed_packet(
        story=story,
        policy=policy,
        provider_policy=provider_policy,
        rags=rags,
    )
    return generate_implementation_update_set_candidate_from_packet(
        packet=packet,
        policy=policy,
        provider=provider,
        classifier_gate=classifier_gate,
    )


def generate_implementation_update_set_candidate_from_packet(
    *,
    packet: ImplementationPacket,
    policy: AllowlistPolicy,
    provider: ModelProvider,
    classifier_gate: bool = True,
    maturity_provider: MaturityEvidenceProvider | None = None,
) -> UpdateSetCandidate:
    classifier_gate_disabled = not classifier_gate
    if (
        packet.safety_decision != SuitabilityOutcome.AUTOMATED_BUILD.value
        and not classifier_gate_disabled
    ):
        return _manual_review_candidate(packet=packet)
    context_plan = plan_context_escalation(packet.context_sufficiency)
    if not context_plan.should_call_model and not classifier_gate_disabled:
        return _manual_review_candidate(packet=packet)
    if _surface_operation_reasons(packet):
        return _manual_review_candidate(packet=packet)
    response = _normalize_placeholder_sys_ids(provider.generate(packet.to_model_payload()))
    _validate_response(
        response,
        allowed_tables=policy.tables,
        allowed_operations=policy.operations,
        allowed_sys_ids=set(),
    )
    _validate_implementation_contract(response)
    response = _reconcile_response_with_packet(packet=packet, response=response)
    _validate_response(
        response,
        allowed_tables=policy.tables,
        allowed_operations=policy.operations,
        allowed_sys_ids=set(),
    )
    _validate_implementation_contract(response)
    _validate_response_tables_match_capability(packet=packet, response=response)
    candidate = UpdateSetCandidate(
        story_number=packet.story.number,
        name=f"UPD_{packet.story.number}_LLM_Implementation",
        eligibility_decision=_candidate_decision(packet.safety_decision),
        eligibility_reasons=[
            *packet.safety_reasons,
            *(
                ["classifier gate disabled for exploratory model reasoning"]
                if classifier_gate_disabled
                else []
            ),
        ],
        confidence=0.75,
        risk_score=packet.risk_score,
        status=CandidateStatus.READY_FOR_REVIEW,
        changes=[CandidateChange.model_validate(change) for change in response.get("changes", [])],
        retrieval_citations=packet.retrieval_citations,
        assumptions=["Generated from a validated implementation packet."],
        reviewer_notes=[
            *[str(item) for item in response["test_plan"]],
            *[f"Rollback: {item}" for item in response["rollback_notes"]],
        ],
    )
    if packet.safety_decision != SuitabilityOutcome.AUTOMATED_BUILD.value:
        candidate = _route_candidate_to_manual_review(candidate)
    candidate = _route_candidate_by_builder_maturity(candidate, maturity_provider=maturity_provider)
    payload = candidate.model_dump(mode="json", exclude={"artifact_hash"})
    return candidate.model_copy(update={"artifact_hash": stable_artifact_hash(payload)})


def _route_candidate_to_manual_review(candidate: UpdateSetCandidate) -> UpdateSetCandidate:
    return candidate.model_copy(
        update={
            "eligibility_decision": "manual_review",
            "status": CandidateStatus.MANUAL_BUILD,
            "assumptions": [
                *candidate.assumptions,
                (
                    "Structured candidate preserved for review because classifier "
                    "gate bypass is exploratory."
                ),
            ],
            "reviewer_notes": [
                *candidate.reviewer_notes,
                "Automated handoff skipped because the classifier did not approve the story.",
            ],
        }
    )


def _route_candidate_by_builder_maturity(
    candidate: UpdateSetCandidate,
    *,
    maturity_provider: MaturityEvidenceProvider | None = None,
) -> UpdateSetCandidate:
    change_tables = {change.table for change in candidate.changes}
    scored = builder_maturity_for_change_tables(change_tables, provider=maturity_provider)
    maturity = scored.score
    evidence_notes = (
        [
            (
                "Builder maturity is evidence-adjusted from baseline "
                f"{scored.baseline:.2f} using {scored.evidence_samples} recorded "
                "fulfillment outcomes."
            )
        ]
        if scored.source == "evidence_adjusted"
        else []
    )
    if maturity >= AUTOMATED_HANDOFF_BUILDER_MATURITY_THRESHOLD:
        return candidate.model_copy(
            update={
                "confidence": min(candidate.confidence, maturity),
                "reviewer_notes": [*candidate.reviewer_notes, *evidence_notes],
            }
        )
    tables = ",".join(sorted(change_tables)) or "none"
    reason = f"builder maturity below automated handoff threshold: {tables}={maturity:.2f}"
    return candidate.model_copy(
        update={
            "eligibility_decision": "manual_review",
            "eligibility_reasons": [*candidate.eligibility_reasons, reason],
            "confidence": maturity,
            "status": CandidateStatus.MANUAL_BUILD,
            "assumptions": [
                *candidate.assumptions,
                (
                    "Structured candidate preserved for review; deterministic retrieved "
                    "Update Set handoff is blocked until the builder is mature."
                ),
            ],
            "reviewer_notes": [
                *candidate.reviewer_notes,
                (
                    "Automated handoff skipped because the deterministic builder maturity "
                    f"score is {maturity:.2f}."
                ),
                *evidence_notes,
            ],
        }
    )


def _normalize_placeholder_sys_ids(response: dict[str, Any]) -> dict[str, Any]:
    changes = response.get("changes")
    if not isinstance(changes, list):
        return response
    normalized_changes: list[Any] = []
    changed = False
    for change in changes:
        if not isinstance(change, dict):
            normalized_changes.append(change)
            continue
        normalized_change = dict(change)
        sys_id = normalized_change.get("sys_id")
        if _is_placeholder_sys_id(sys_id):
            normalized_change["sys_id"] = None
            changed = True
        normalized_changes.append(normalized_change)
    if not changed:
        return response
    return {**response, "changes": normalized_changes}


def _is_placeholder_sys_id(value: Any) -> bool:
    text = str(value or "").strip().lower()
    return text.startswith("[") and text.endswith("]") and "sys_id" in text


def _reconcile_response_with_packet(
    *,
    packet: ImplementationPacket,
    response: dict[str, Any],
) -> dict[str, Any]:
    if not _packet_has_capability(packet, Capability.CATALOG_ITEM_CREATE):
        return response
    return {
        **response,
        "changes": _catalog_item_changes_from_normalized_intent(packet.normalized_intent),
    }


def _packet_has_capability(packet: ImplementationPacket, capability: Capability) -> bool:
    capabilities = packet.capability_assessment.get("capabilities", [])
    return isinstance(capabilities, list) and capability.value in {
        str(item) for item in capabilities
    }


def _catalog_item_changes_from_normalized_intent(
    intent: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not isinstance(intent, dict):
        raise ModelResponseError("catalog item candidate requires normalized intent")

    item_name = _required_intent_text(intent, "artifact_name", "catalog item name")
    item_short_description = _required_intent_text(
        intent,
        "catalog_item_short_description",
        "catalog item short description",
    )
    catalog = _required_intent_text(intent, "catalog_name", "catalog")
    category = _required_intent_text(intent, "category_name", "category")
    taxonomy = _required_intent_text(intent, "taxonomy_name", "taxonomy")
    topic = _required_intent_text(intent, "employee_center_topic", "Employee Center topic")
    raw_variables = intent.get("catalog_variables")
    if not isinstance(raw_variables, list) or not raw_variables:
        raise ModelResponseError("catalog item candidate requires normalized catalog variables")

    changes: list[dict[str, Any]] = [
        {
            "table": "sc_cat_item",
            "operation": "insert",
            "fields": {
                "name": item_name,
                "short_description": item_short_description,
                "description": item_short_description,
                "catalog": catalog,
                "category": category,
                "taxonomy": taxonomy,
                "employee_center_topic": topic,
            },
            "sys_id": None,
            "rationale": "Create the standard catalog item from the normalized story intent.",
        }
    ]
    for index, raw_variable in enumerate(raw_variables, start=1):
        if not isinstance(raw_variable, dict):
            raise ModelResponseError("catalog item variable intent must be an object")
        variable_name = _required_intent_text(raw_variable, "name", "catalog variable name")
        variable_type = _required_intent_text(
            raw_variable,
            "type",
            f"catalog variable type for {variable_name}",
        )
        fields: dict[str, Any] = {
            "name": variable_name,
            "question_text": _required_intent_text(
                raw_variable,
                "label",
                f"catalog variable label for {variable_name}",
            ),
            "type": variable_type,
            "mandatory": bool(raw_variable.get("mandatory", False)),
            "order": _optional_intent_order(raw_variable.get("order"), default=index * 100),
        }
        reference_table = _optional_intent_text(raw_variable.get("reference_table"))
        if variable_type == "reference":
            if reference_table is None:
                raise ModelResponseError(
                    f"reference catalog variable {variable_name} requires reference_table"
                )
            fields["reference"] = reference_table
        reference_qualifier = _optional_intent_text(raw_variable.get("reference_qualifier"))
        if reference_qualifier is not None:
            fields["reference_qualifier"] = reference_qualifier
        default_value = _optional_intent_text(raw_variable.get("default_value"))
        if default_value is not None:
            fields["default_value"] = default_value
        help_text = _optional_intent_text(raw_variable.get("help_text"))
        if help_text is not None:
            fields["help_text"] = help_text
        changes.append(
            {
                "table": "item_option_new",
                "operation": "insert",
                "fields": fields,
                "sys_id": None,
                "rationale": (
                    f"Create the {variable_name} variable from the normalized story intent."
                ),
            }
        )

    changes.extend(
        [
            {
                "table": "sc_cat_item_category",
                "operation": "insert",
                "fields": {"catalog": catalog, "category": category},
                "sys_id": None,
                "rationale": "Place the catalog item in the requested catalog category.",
            },
            {
                "table": "m2m_connected_content",
                "operation": "insert",
                "fields": {
                    "taxonomy": taxonomy,
                    "topic": topic,
                    "employee_center_topic": topic,
                },
                "sys_id": None,
                "rationale": "Associate the catalog item with the requested Employee Center topic.",
            },
        ]
    )
    return changes


def _required_intent_text(intent: dict[str, Any], key: str, label: str) -> str:
    value = _optional_intent_text(intent.get(key))
    if value is None:
        raise ModelResponseError(f"catalog item candidate missing normalized {label}")
    return value


def _optional_intent_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_intent_order(value: Any, *, default: int) -> int:
    if value is None:
        return default
    try:
        order = int(value)
    except (TypeError, ValueError):
        return default
    return order if order > 0 else default


def _code_surface_capability(packet: ImplementationPacket) -> str | None:
    capabilities = set(packet.capability_assessment.get("capabilities", []))
    for capability in [
        Capability.BUSINESS_RULE_ANALYZE.value,
        Capability.CLIENT_SCRIPT_ANALYZE.value,
        Capability.SCRIPT_INCLUDE_ANALYZE.value,
    ]:
        if capability in capabilities:
            return capability
    return None


def _form_layout_capability(packet: ImplementationPacket) -> str | None:
    capabilities = set(packet.capability_assessment.get("capabilities", []))
    if Capability.FORM_SECTION_REMOVE.value in capabilities:
        return Capability.FORM_SECTION_REMOVE.value
    return None


def _manual_review_candidate(
    *,
    packet: ImplementationPacket,
) -> UpdateSetCandidate:
    context_plan = plan_context_escalation(packet.context_sufficiency)
    eligibility_reasons = [
        *packet.safety_reasons,
        *_surface_operation_reasons(packet),
        *context_plan.reasons,
    ]
    reviewer_notes = [
        "Model invocation skipped by deterministic safety or context gate.",
        *_automation_feedback_notes(packet),
    ]
    if packet.safety_decision == SuitabilityOutcome.CONTEXT_ANALYSIS.value:
        code_surface = _code_surface_capability(packet)
        if code_surface is not None:
            eligibility_reasons.insert(0, "code_surface_analysis:first")
            eligibility_reasons.insert(1, f"capability:{code_surface}")
            reviewer_notes = [
                "Code surface analysis completed without generation.",
                (
                    "Code surface generation is not enabled until a mutation profile "
                    "and validators are approved."
                ),
                *_automation_feedback_notes(packet),
            ]
        form_layout = _form_layout_capability(packet)
        if form_layout is not None:
            eligibility_reasons.insert(0, "form_layout_analysis:first")
            eligibility_reasons.insert(1, f"capability:{form_layout}")
            reviewer_notes = [
                "Form layout analysis completed without generation.",
                (
                    "Form section generation is not enabled until retrieved Update "
                    "Set XML shape evidence and validators are approved."
                ),
                *_automation_feedback_notes(packet),
            ]
        if Capability.CMDB_IRE_ANALYZE.value in set(
            packet.capability_assessment.get("capabilities", [])
        ):
            eligibility_reasons.insert(0, "cmdb_ire_analysis:first")
            eligibility_reasons.insert(1, f"capability:{Capability.CMDB_IRE_ANALYZE.value}")
            reviewer_notes = [
                "CMDB IRE analysis completed without generation.",
                (
                    "CMDB IRE mutation is not enabled until identification and "
                    "reconciliation rule validators are approved."
                ),
                *_automation_feedback_notes(packet),
            ]
    candidate = UpdateSetCandidate(
        story_number=packet.story.number,
        name=f"UPD_{packet.story.number}_Manual_Build",
        eligibility_decision=_candidate_decision(packet.safety_decision),
        eligibility_reasons=eligibility_reasons,
        confidence=0.0,
        risk_score=1.0,
        status=CandidateStatus.MANUAL_BUILD,
        retrieval_citations=packet.retrieval_citations,
        reviewer_notes=reviewer_notes,
    )
    payload = candidate.model_dump(mode="json", exclude={"artifact_hash"})
    return candidate.model_copy(update={"artifact_hash": stable_artifact_hash(payload)})


def _automation_feedback_notes(packet: ImplementationPacket) -> list[str]:
    assessment = packet.capability_assessment
    if not isinstance(assessment, dict):
        return []
    notes = [
        str(note).strip()
        for note in assessment.get("operator_feedback", [])
        if str(note).strip()
    ]
    suggested_story = assessment.get("suggested_story")
    if isinstance(suggested_story, str) and suggested_story.strip():
        notes.append(f"Suggested rewrite:\n{suggested_story.strip()}")
    return notes


def _surface_operation_reasons(packet: ImplementationPacket) -> list[str]:
    plan = packet.surface_operation_plan
    if not isinstance(plan, dict):
        return []
    operations = plan.get("operations")
    if not isinstance(operations, list):
        return []
    reasons: list[str] = []
    for operation in operations:
        if not isinstance(operation, dict):
            continue
        if operation.get("status") != SurfaceOperationStatus.UNSUPPORTED.value:
            continue
        kind = str(operation.get("kind") or SurfaceOperationKind.UNKNOWN.value)
        reasons.append(f"unsupported surface operation: {kind}")
        for code in operation.get("reason_codes") or []:
            reasons.append(f"surface operation reason: {code}")
    return reasons


def _build_allowed_packet(
    *,
    story: Story,
    policy: AllowlistPolicy,
    provider_policy: ProviderPolicy,
    rags: SpecializedRags,
) -> ImplementationPacket:
    if not provider_policy.allows(
        task=IMPLEMENTATION_PACKET_TASK,
        data_class=story.data_classification,
    ):
        raise ProviderBlocked(
            f"provider {provider_policy.provider_id} is not approved for "
            f"task={IMPLEMENTATION_PACKET_TASK} "
            f"data_class={story.data_classification.value}"
        )

    return build_implementation_packet(
        story=story,
        policy=policy,
        provider_policy=provider_policy,
        rags=rags,
    )


def _candidate_decision(value: str) -> Literal["eligible", "manual_review", "rejected"]:
    if value in {"eligible", SuitabilityOutcome.AUTOMATED_BUILD.value}:
        return "eligible"
    if value in {
        "manual_review",
        SuitabilityOutcome.NEEDS_CLARIFICATION.value,
        SuitabilityOutcome.CONTEXT_ANALYSIS.value,
        SuitabilityOutcome.UNSUPPORTED_CAPABILITY.value,
        SuitabilityOutcome.MANUAL_DEVELOPER_BUILD.value,
    }:
        return "manual_review"
    if value == "rejected":
        return "rejected"
    raise ModelResponseError(f"unsupported safety decision: {value}")


def _validate_implementation_contract(response: dict[str, Any]) -> None:
    changes = response.get("changes")
    if not isinstance(changes, list) or not changes:
        raise ModelResponseError("changes must be a non-empty list")
    _validate_no_raw_xml(response)
    for field_name in ["test_plan", "rollback_notes"]:
        value = response.get(field_name)
        if not isinstance(value, list) or not value:
            raise ModelResponseError(f"{field_name} must be a non-empty list")


def _validate_response_tables_match_capability(
    *,
    packet: ImplementationPacket,
    response: dict[str, Any],
) -> None:
    expected_tables = _expected_tables_for_packet(packet)
    if not expected_tables:
        return
    changes = response.get("changes")
    if not isinstance(changes, list):
        return
    actual_tables = {
        str(change.get("table") or "")
        for change in changes
        if isinstance(change, dict) and str(change.get("table") or "").strip()
    }
    unexpected = sorted(actual_tables - expected_tables)
    if unexpected:
        raise ModelResponseError(
            "model response tables do not match assessed capability: "
            f"{', '.join(unexpected)}"
        )


def _expected_tables_for_packet(packet: ImplementationPacket) -> set[str]:
    capabilities = set(str(item) for item in packet.capability_assessment.get("capabilities", []))
    if Capability.CMDB_IRE_GENERATE.value in capabilities:
        return {"cmdb_identifier", "cmdb_identifier_entry", "cmdb_reconciliation_definition"}
    if Capability.UI_POLICY_GENERATE.value in capabilities:
        return {"sys_ui_policy", "sys_ui_policy_action"}
    if Capability.CATALOG_ITEM_CREATE.value in capabilities:
        return {"sc_cat_item", "item_option_new", "sc_cat_item_category", "m2m_connected_content"}
    if Capability.BUSINESS_RULE_GENERATE.value in capabilities:
        return {"sys_script"}
    if Capability.CLIENT_SCRIPT_GENERATE.value in capabilities:
        return {"sys_script_client"}
    if Capability.SCRIPT_INCLUDE_GENERATE.value in capabilities:
        return {"sys_script_include"}
    if Capability.FORM_SECTION_REMOVE.value in capabilities:
        return {"sys_ui_section"}
    if {
        Capability.DICTIONARY_FIELD_CREATE.value,
        Capability.FORM_LAYOUT_PLACE_FIELD.value,
        Capability.FIELD_LABEL_CREATE.value,
    }.intersection(capabilities):
        return {"sys_dictionary", "sys_ui_form"}
    return set()


def _validate_no_raw_xml(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).strip().lower() in {"payload", "xml", "update_xml", "raw_xml"}:
                raise ModelResponseError("model response must not include raw XML fields")
            _validate_no_raw_xml(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_no_raw_xml(item)
        return
    if isinstance(value, str) and any(
        token in value.lower()
        for token in ["<record_update", "<sys_update_xml", "<unload", "payload><![cdata"]
    ):
        raise ModelResponseError("model response must not include raw XML content")
