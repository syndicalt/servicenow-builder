from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from jedi_devproject.models import ProviderPolicy, RetrievalCitation, Story
from jedi_devproject.providers import (
    ModelProvider,
    ModelResponseError,
    ProviderBlocked,
    _validate_response,
)
from jedi_devproject.rag import SpecializedRags
from jedi_devproject.risk import RiskInput, calculate_risk_score
from jedi_devproject.safety import AllowlistPolicy, evaluate_story

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
            },
            "context": self.context_sections,
            "citations": [
                citation.model_dump(mode="json")
                for citation in self.retrieval_citations
            ],
            "output_contract": self.output_contract,
        }


def build_implementation_packet(
    *,
    story: Story,
    policy: AllowlistPolicy,
    provider_policy: ProviderPolicy,
    rags: SpecializedRags,
) -> ImplementationPacket:
    safety = evaluate_story(story, policy)
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
    citations = [
        result.citation
        for results in retrieved.values()
        for result in results
    ]

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
        safety_decision=safety.decision,
        safety_reasons=safety.reasons,
        risk_score=calculate_risk_score(
            RiskInput(
                story_type=safety.story_type.value if safety.story_type else "unknown",
                affected_tables=story.affected_tables,
                target_table=str(story.additional_context.get("target_table", "rm_story")),
                field_name=str(
                    story.additional_context.get("field_name", "u_ai_review_notes")
                ),
            )
        ),
        allowed_tables=sorted(policy.tables),
        allowed_operations=sorted(policy.operations),
        context_sections=context_sections,
        retrieval_citations=citations,
        output_contract={
            "format": "structured_update_set_candidate",
            "must_return_manual_review_when_uncertain": True,
            "must_not_invent_tables_fields_sys_ids": True,
            "must_include_test_plan": True,
            "must_include_rollback_notes": True,
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
    if not provider_policy.allows(
        task=IMPLEMENTATION_PACKET_TASK,
        data_class=story.data_classification,
    ):
        raise ProviderBlocked(
            f"provider {provider_policy.provider_id} is not approved for "
            f"task={IMPLEMENTATION_PACKET_TASK} "
            f"data_class={story.data_classification.value}"
        )

    packet = build_implementation_packet(
        story=story,
        policy=policy,
        provider_policy=provider_policy,
        rags=rags,
    )
    response = provider.generate(packet.to_model_payload())
    _validate_response(
        response,
        allowed_tables=policy.tables,
        allowed_operations=policy.operations,
        allowed_sys_ids=set(),
    )
    _validate_implementation_contract(response)
    return response


def _validate_implementation_contract(response: dict[str, Any]) -> None:
    for field_name in ["test_plan", "rollback_notes"]:
        value = response.get(field_name)
        if not isinstance(value, list) or not value:
            raise ModelResponseError(f"{field_name} must be a non-empty list")
