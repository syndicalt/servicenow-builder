from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from jedi_devproject.capabilities import SuitabilityOutcome
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

IMPLEMENTATION_PACKET_TASK = "generate_implementation_candidate"


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
    instance_context: dict[str, Any] | None = None
    instance_context_bundle: dict[str, Any] | None = None
    context_sufficiency: dict[str, Any] = Field(default_factory=dict)
    context_sections: dict[str, str]
    retrieval_citations: list[RetrievalCitation]
    output_contract: dict[str, Any]

    def to_model_payload(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "provider_id": self.provider_id,
            "story": self.story.model_dump(),
            "controls": {
                "safety_decision": self.safety_decision,
                "safety_reasons": self.safety_reasons,
                "risk_score": self.risk_score,
                "allowed_tables": self.allowed_tables,
                "allowed_operations": self.allowed_operations,
                "capability_assessment": self.capability_assessment,
                "normalized_intent": self.normalized_intent,
                "context_sufficiency": self.context_sufficiency,
                "context_escalation": plan_context_escalation(self.context_sufficiency).model_dump(
                    mode="json"
                ),
            },
            "instance_context": self.instance_context,
            "instance_context_bundle": self.instance_context_bundle,
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
            assessment.intent.model_dump(mode="json") if assessment.intent is not None else None
        ),
        instance_context=(
            discovery_context.model_dump(mode="json") if discovery_context is not None else None
        ),
        instance_context_bundle=(
            surface_context_bundle.model_dump(mode="json")
            if surface_context_bundle is not None
            else None
        ),
        context_sufficiency=_context_sufficiency(
            discovery_context=discovery_context,
            surface_context_bundle=surface_context_bundle,
        ),
        context_sections=context_sections,
        retrieval_citations=citations,
        output_contract={
            "format": "structured_update_set_candidate",
            "must_return_manual_review_when_uncertain": True,
            "must_not_invent_tables_fields_sys_ids": True,
            "must_include_test_plan": True,
            "must_include_rollback_notes": True,
            "capabilities": sorted(capability.value for capability in assessment.capabilities),
            "must_follow_normalized_intent": True,
            "must_use_discovered_instance_context": True,
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
    if not discovery_context.table_exists:
        missing_context.append("target_table")
    if not discovery_context.supports_custom_fields:
        missing_context.append("custom_field_support")
    if not discovery_context.form_sections:
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
    return response


def generate_implementation_update_set_candidate(
    *,
    story: Story,
    policy: AllowlistPolicy,
    provider_policy: ProviderPolicy,
    rags: SpecializedRags,
    provider: ModelProvider,
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
    )


def generate_implementation_update_set_candidate_from_packet(
    *,
    packet: ImplementationPacket,
    policy: AllowlistPolicy,
    provider: ModelProvider,
) -> UpdateSetCandidate:
    if packet.safety_decision != SuitabilityOutcome.AUTOMATED_BUILD.value:
        return _manual_review_candidate(packet=packet)
    context_plan = plan_context_escalation(packet.context_sufficiency)
    if not context_plan.should_call_model:
        return _manual_review_candidate(packet=packet)
    response = _normalize_placeholder_sys_ids(provider.generate(packet.to_model_payload()))
    _validate_response(
        response,
        allowed_tables=policy.tables,
        allowed_operations=policy.operations,
        allowed_sys_ids=set(),
    )
    _validate_implementation_contract(response)
    candidate = UpdateSetCandidate(
        story_number=packet.story.number,
        name=f"UPD_{packet.story.number}_LLM_Implementation",
        eligibility_decision=_candidate_decision(packet.safety_decision),
        eligibility_reasons=packet.safety_reasons,
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
    payload = candidate.model_dump(mode="json", exclude={"artifact_hash"})
    return candidate.model_copy(update={"artifact_hash": stable_artifact_hash(payload)})


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


def _manual_review_candidate(
    *,
    packet: ImplementationPacket,
) -> UpdateSetCandidate:
    context_plan = plan_context_escalation(packet.context_sufficiency)
    eligibility_reasons = [*packet.safety_reasons, *context_plan.reasons]
    reviewer_notes = ["Model invocation skipped by deterministic safety or context gate."]
    if packet.safety_decision == SuitabilityOutcome.CONTEXT_ANALYSIS.value:
        eligibility_reasons.insert(0, "business_rule_analysis:first")
        reviewer_notes = [
            "Business Rule analysis completed without generation.",
            (
                "Business Rule generation is not enabled until a mutation profile "
                "and validators are approved."
            ),
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
    for field_name in ["test_plan", "rollback_notes"]:
        value = response.get(field_name)
        if not isinstance(value, list) or not value:
            raise ModelResponseError(f"{field_name} must be a non-empty list")
