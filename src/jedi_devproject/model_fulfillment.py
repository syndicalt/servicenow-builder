from __future__ import annotations

from typing import Any, Protocol, cast

from pydantic import BaseModel, ConfigDict

from jedi_devproject.capabilities import Capability, SuitabilityOutcome
from jedi_devproject.capability_analysis import analyze_story_capabilities
from jedi_devproject.enrichment import enrich_story
from jedi_devproject.fulfillment_worker import (
    FulfillmentArtifactRef,
    FulfillmentExecutionResult,
    FulfillmentHandler,
)
from jedi_devproject.implementation_packet import (
    build_implementation_packet,
    generate_implementation_update_set_candidate_from_packet,
)
from jedi_devproject.instance_discovery import (
    ServiceNowSurfaceContextBundle,
    SurfaceName,
    discover_servicenow_surface_context,
)
from jedi_devproject.models import CandidateStatus, ProviderPolicy, UpdateSetCandidate
from jedi_devproject.operational_store import FulfillmentJobRecord
from jedi_devproject.rag import SpecializedRags
from jedi_devproject.safety import AllowlistPolicy
from jedi_devproject.update_set_handoff import (
    UpdateSetHandoffRequest,
    create_update_set_handoff,
)
from jedi_devproject.writeback_orchestration import WritebackClient


class ModelFulfillmentClient(WritebackClient, Protocol):
    def fetch_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
    ) -> dict[str, Any] | None: ...

    def fetch_table_records(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...

    def upsert_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: dict[str, Any],
    ) -> dict[str, Any]: ...

    def import_update_set_xml(
        self,
        *,
        service_id: str,
        update_set_xml: str,
    ) -> dict[str, Any]: ...


class ModelCandidateFulfillmentConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    policy: AllowlistPolicy
    provider_policy: ProviderPolicy
    rags: SpecializedRags
    provider: Any
    instance_url: str
    apply_update_set_changes: bool = False
    update_set_user_name: str | None = None


def model_candidate_fulfillment_handler(
    *,
    client: ModelFulfillmentClient,
    config: ModelCandidateFulfillmentConfig,
) -> FulfillmentHandler:
    def handle(job: FulfillmentJobRecord) -> FulfillmentExecutionResult:
        stories = client.fetch_stories(sysparm_query=f"number={job.story_number}", limit=1)
        if not stories:
            raise RuntimeError(f"story not found: {job.story_number}")

        story = enrich_story(stories[0]).enriched_story
        surface_context_bundle = _surface_context_for_story(client=client, story=story)
        packet = build_implementation_packet(
            story=story,
            policy=config.policy,
            provider_policy=config.provider_policy,
            rags=config.rags,
            discovery_context=(
                surface_context_bundle.table_context if surface_context_bundle is not None else None
            ),
            surface_context_bundle=surface_context_bundle,
        )
        candidate = generate_implementation_update_set_candidate_from_packet(
            packet=packet,
            policy=config.policy,
            provider=config.provider,
        )
        business_rule_analysis = _business_rule_analysis_artifact(
            packet=packet,
            surface_context_bundle=surface_context_bundle,
        )

        return FulfillmentExecutionResult(
            message=f"Implementation candidate generated for {job.story_number}",
            artifacts=[
                *(
                    [
                        FulfillmentArtifactRef(
                            artifact_kind="instance_context_bundle",
                            schema_version="servicenow-surface-context-v1",
                            payload_json=surface_context_bundle.model_dump(mode="json"),
                        )
                    ]
                    if surface_context_bundle is not None
                    else []
                ),
                *(
                    [
                        FulfillmentArtifactRef(
                            artifact_kind="business_rule_analysis",
                            schema_version="business-rule-analysis-v1",
                            payload_json=business_rule_analysis,
                        )
                    ]
                    if business_rule_analysis is not None
                    else []
                ),
                FulfillmentArtifactRef(
                    artifact_kind="implementation_packet",
                    schema_version="implementation-packet-v1",
                    payload_json=packet.model_dump(mode="json"),
                ),
                FulfillmentArtifactRef(
                    artifact_kind="implementation_candidate",
                    schema_version="implementation-candidate-v1",
                    payload_json=candidate.model_dump(mode="json"),
                ),
            ],
            after_artifacts_persisted=lambda artifacts: _create_handoff_after_persist(
                client=client,
                story_sys_id=stories[0].sys_id,
                story_number=job.story_number,
                candidate=candidate,
                candidate_artifact_ref=_candidate_artifact_ref(artifacts),
                instance_url=config.instance_url,
                apply_update_set_changes=config.apply_update_set_changes,
                update_set_user_name=config.update_set_user_name,
            ),
        )

    return handle


def _surface_context_for_story(
    *,
    client: ModelFulfillmentClient,
    story: Any,
) -> ServiceNowSurfaceContextBundle | None:
    assessment = analyze_story_capabilities(story)
    target_table = (
        assessment.intent.target_table if assessment.intent is not None else assessment.target_table
    )
    if target_table is None:
        return None
    story_text = " ".join(
        str(value)
        for value in [
            story.short_description,
            story.description,
            story.acceptance_criteria or "",
        ]
        if value
    )
    return discover_servicenow_surface_context(
        client=client,
        target_table=target_table,
        story_text=story_text,
        public_doc_queries=_public_doc_queries(story_text),
        required_surfaces_override=cast(
            list[SurfaceName] | None,
            assessment.required_instance_context or None,
        ),
    )


def _business_rule_analysis_artifact(
    *,
    packet: Any,
    surface_context_bundle: ServiceNowSurfaceContextBundle | None,
) -> dict[str, Any] | None:
    if packet.safety_decision != SuitabilityOutcome.CONTEXT_ANALYSIS.value:
        return None
    if Capability.BUSINESS_RULE_ANALYZE.value not in packet.capability_assessment.get(
        "capabilities", []
    ):
        return None
    business_rules = None
    if surface_context_bundle is not None:
        business_rules = surface_context_bundle.surface("business_rules")
    records = business_rules.records if business_rules is not None else []
    return {
        "schema_version": "business-rule-analysis-v1",
        "story_number": packet.story.number,
        "target_table": (
            surface_context_bundle.target_table if surface_context_bundle is not None else "unknown"
        ),
        "existing_rule_count": len(records),
        "existing_rules": [
            {
                "name": record.name,
                "active": record.active,
                "summary": record.summary,
                "metadata": record.metadata,
            }
            for record in records
        ],
        "supported_generation": False,
        "unsupported_cases": ["business_rule_generation_not_enabled"],
        "required_instance_context": packet.capability_assessment.get(
            "required_instance_context", []
        ),
        "context_sufficiency": packet.context_sufficiency,
    }


def _public_doc_queries(story_text: str) -> list[str]:
    lowered = story_text.lower()
    if not any(token in lowered for token in ["documentation", "public docs", "docs"]):
        return []
    return ["ServiceNow public documentation for requested platform surfaces"]


def _create_handoff_after_persist(
    *,
    client: ModelFulfillmentClient,
    story_sys_id: str,
    story_number: str,
    candidate: Any,
    candidate_artifact_ref: str,
    instance_url: str,
    apply_update_set_changes: bool,
    update_set_user_name: str | None,
) -> None:
    _ = (apply_update_set_changes, update_set_user_name)
    if candidate.status is not CandidateStatus.READY_FOR_REVIEW:
        _write_manual_review_required(
            client=client,
            story_sys_id=story_sys_id,
            story_number=story_number,
            candidate=candidate,
            candidate_artifact_ref=candidate_artifact_ref,
        )
        return

    create_update_set_handoff(
        client=client,
        request=UpdateSetHandoffRequest(
            story_sys_id=story_sys_id,
            story_number=story_number,
            candidate=candidate,
            candidate_artifact_ref=candidate_artifact_ref,
            instance_url=instance_url,
        ),
    )


def _write_manual_review_required(
    *,
    client: ModelFulfillmentClient,
    story_sys_id: str,
    story_number: str,
    candidate: UpdateSetCandidate,
    candidate_artifact_ref: str,
) -> None:
    client.update_story_fields(
        story_sys_id,
        _manual_feedback_fields(
            story_number=story_number,
            candidate=candidate,
            candidate_artifact_ref=candidate_artifact_ref,
        ),
    )


def _manual_feedback_fields(
    *,
    story_number: str,
    candidate: UpdateSetCandidate,
    candidate_artifact_ref: str,
) -> dict[str, object]:
    reasons = _candidate_reasons(candidate)
    if any(reason.startswith("missing detail:") for reason in candidate.eligibility_reasons):
        status = "Needs Clarification"
    else:
        status = "Human Review Required"
    lead = (
        f"Business Rule analysis completed for {story_number}; it did not create a "
        if "business_rule_analysis:first" in candidate.eligibility_reasons
        else f"Automated implementation candidate for {story_number} did not create a "
    )
    return {
        "u_ai_status": status,
        "work_notes": (
            f"{lead}"
            "retrieved Update Set. "
            f"Candidate artifact: {candidate_artifact_ref}. "
            f"{_missing_context_note(candidate)}"
            f"Reasons: {reasons}."
        ),
    }


def _missing_context_note(candidate: UpdateSetCandidate) -> str:
    missing = [
        reason.removeprefix("context_insufficient:")
        for reason in candidate.eligibility_reasons
        if reason.startswith("context_insufficient:")
    ]
    if not missing:
        return ""
    return f"Missing ServiceNow context: {', '.join(missing)}. "


def _candidate_reasons(candidate: UpdateSetCandidate) -> str:
    if not candidate.eligibility_reasons:
        return f"candidate status is {candidate.status.value}"
    return "; ".join(candidate.eligibility_reasons)


def _candidate_artifact_ref(artifacts: list[Any]) -> str:
    for artifact in artifacts:
        if artifact.artifact_kind == "implementation_candidate":
            return str(artifact.path)
    raise RuntimeError("implementation candidate artifact was not persisted")
