from __future__ import annotations

from typing import Any

from jedi_devproject.builder_maturity import (
    CATALOG_FULFILLMENT_FLOW_SURFACE,
    MaturityEvidenceProvider,
    builder_maturity_for_change_tables,
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
    Story,
    UpdateSetCandidate,
    stable_artifact_hash,
)
from jedi_devproject.packet_context import _context_dossier, _context_sufficiency
from jedi_devproject.packet_intent_changes import (
    _catalog_item_changes_from_normalized_intent,
    _record_producer_changes_from_normalized_intent,
)
from jedi_devproject.packet_model import (
    AUTOMATED_HANDOFF_BUILDER_MATURITY_THRESHOLD,
    IMPLEMENTATION_PACKET_TASK,
    ImplementationPacket,
    PacketStory,
)
from jedi_devproject.packet_validation import (
    _candidate_decision,
    _validate_implementation_contract,
    _validate_response_tables_match_capability,
)
from jedi_devproject.providers import (
    ModelProvider,
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

__all__ = [
    "AUTOMATED_HANDOFF_BUILDER_MATURITY_THRESHOLD",
    "IMPLEMENTATION_PACKET_TASK",
    "ImplementationPacket",
    "PacketStory",
    "build_implementation_packet",
    "generate_implementation_candidate",
    "generate_implementation_update_set_candidate",
    "generate_implementation_update_set_candidate_from_packet",
]


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
    scored = builder_maturity_for_change_tables(
        change_tables,
        provider=maturity_provider,
        extra_surfaces=_extra_maturity_surfaces(candidate),
    )
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


def _extra_maturity_surfaces(candidate: UpdateSetCandidate) -> tuple[str, ...]:
    """Field-level maturity surfaces the change tables alone cannot express.

    Attaching a fulfillment flow only adds a reference field on the
    sc_cat_item change, so the conservative ``catalog_fulfillment_flows``
    surface (XML shape UAT-unconfirmed) is added here to keep those candidates
    in manual review until evidence accrues.
    """
    if any(
        change.table == "sc_cat_item"
        and str(change.fields.get("fulfillment_flow") or "").strip()
        for change in candidate.changes
    ):
        return (CATALOG_FULFILLMENT_FLOW_SURFACE,)
    return ()


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
    if _packet_has_capability(packet, Capability.RECORD_PRODUCER_CREATE):
        return {
            **response,
            "changes": _record_producer_changes_from_normalized_intent(
                packet.normalized_intent
            ),
        }
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
