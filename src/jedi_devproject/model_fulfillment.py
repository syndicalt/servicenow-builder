from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from jedi_devproject.artifacts import write_candidate_artifact, write_json_artifact_once
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
from jedi_devproject.writeback_orchestration import WritebackClient


class ModelCandidateFulfillmentConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    artifact_root: Path
    policy: AllowlistPolicy
    provider_policy: ProviderPolicy
    rags: SpecializedRags
    provider: Any


def model_candidate_fulfillment_handler(
    *,
    client: WritebackClient,
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

        packet_path = write_json_artifact_once(
            config.artifact_root / "implementation-packets",
            filename=f"{job.job_id}.json",
            payload=packet.model_dump(mode="json"),
        )
        candidate_path = write_candidate_artifact(
            config.artifact_root / "implementation-candidates",
            run_id=job.job_id,
            candidate=candidate,
        )

        client.update_story_fields(
            stories[0].sys_id,
            {
                "work_notes": (
                    f"Implementation candidate generated for {job.story_number}. "
                    f"Packet: {packet_path}. Candidate: {candidate_path}."
                )
            },
        )

        return FulfillmentExecutionResult(
            message=f"Implementation candidate generated for {job.story_number}",
            artifacts=[
                _artifact_ref("implementation_packet", packet_path),
                _artifact_ref("implementation_candidate", candidate_path),
            ],
        )

    return handle


def _artifact_ref(artifact_kind: str, path: Path) -> FulfillmentArtifactRef:
    return FulfillmentArtifactRef(
        artifact_kind=artifact_kind,
        path=str(path),
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )
