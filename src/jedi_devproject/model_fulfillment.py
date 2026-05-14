from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict

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
from jedi_devproject.models import ProviderPolicy
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
        packet = build_implementation_packet(
            story=story,
            policy=config.policy,
            provider_policy=config.provider_policy,
            rags=config.rags,
        )
        candidate = generate_implementation_update_set_candidate_from_packet(
            packet=packet,
            policy=config.policy,
            provider=config.provider,
        )

        return FulfillmentExecutionResult(
            message=f"Implementation candidate generated for {job.story_number}",
            artifacts=[
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


def _candidate_artifact_ref(artifacts: list[Any]) -> str:
    for artifact in artifacts:
        if artifact.artifact_kind == "implementation_candidate":
            return str(artifact.path)
    raise RuntimeError("implementation candidate artifact was not persisted")
