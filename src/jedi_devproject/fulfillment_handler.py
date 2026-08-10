from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from jedi_devproject.artifacts import artifact_sha256_file, write_json_artifact_once
from jedi_devproject.capability_analysis import analyze_story_capabilities
from jedi_devproject.capability_assessment import (
    INTAKE_FEEDBACK_SCHEMA_VERSION,
    IntakeFeedback,
    build_intake_feedback,
    intake_feedback_work_note,
)
from jedi_devproject.enrichment import enrich_story
from jedi_devproject.fulfillment_worker import (
    FulfillmentArtifactRef,
    FulfillmentExecutionResult,
)
from jedi_devproject.models import Story
from jedi_devproject.operational_store import FulfillmentJobRecord
from jedi_devproject.writeback import ActorType, StoryWritebackPolicy
from jedi_devproject.writeback_orchestration import (
    BuildClaimExecutionRequest,
    WritebackClient,
    WritebackExecutionResult,
    execute_build_claim,
)

_LOGGER = logging.getLogger(__name__)

INTAKE_FEEDBACK_ARTIFACT_KIND = "intake_feedback"
INTAKE_STORY_FETCH_NON_JSON_DIAGNOSTIC = (
    "intake story fetch contains non-JSON value"
)


class BuildClaimFulfillmentConfig(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        hide_input_in_errors=True,
    )

    actor_id: str | None
    audit_root: Path | None
    apply: bool = True
    from_state: str = "Ready"
    claim_state: str = "Work in Progress"
    actor_type: ActorType = ActorType.SERVICE
    candidate_artifact_url: str | None = None
    intake_feedback_enabled: bool = True


class FulfillmentBlocked(RuntimeError):
    def __init__(self, reasons: list[str]) -> None:
        self.reasons = reasons
        super().__init__(", ".join(reasons))


def build_claim_fulfillment_handler(
    *,
    client: WritebackClient,
    config: BuildClaimFulfillmentConfig,
) -> Callable[[FulfillmentJobRecord], FulfillmentExecutionResult]:
    def handle(job: FulfillmentJobRecord) -> FulfillmentExecutionResult:
        result = execute_build_claim(
            client,
            BuildClaimExecutionRequest(
                story_number=job.story_number,
                story_sys_id=job.story_sys_id,
                lifecycle_event_id=job.event_id,
                candidate_artifact_url=config.candidate_artifact_url,
                from_state=config.from_state,
                claim_state=config.claim_state,
                apply=config.apply,
                confirm_story_number=job.story_number if config.apply else None,
                actor_type=config.actor_type,
                actor_id=config.actor_id,
                execution_id=job.job_id,
                audit_root=config.audit_root,
            ),
        )
        _raise_if_blocked(result)
        return FulfillmentExecutionResult(
            message=_message_for_result(result),
            artifacts=_intake_feedback_artifacts(client=client, config=config, job=job),
        )

    return handle


def _intake_feedback_artifacts(
    *,
    client: WritebackClient,
    config: BuildClaimFulfillmentConfig,
    job: FulfillmentJobRecord,
) -> list[FulfillmentArtifactRef]:
    """Run the intake-time capability assessment before model fulfillment.

    Runs as part of the build-claim stage (the first fulfillment stage), so the
    requester receives rewrite guidance before full fulfillment is attempted.
    Fail-open by design: any error here is logged and recorded but never blocks the
    normal fulfillment path.
    """
    if not config.intake_feedback_enabled:
        return []
    try:
        return _assess_intake_feedback(client=client, config=config, job=job)
    except Exception:
        _LOGGER.exception(
            "intake feedback assessment failed for story %s (event %s); "
            "continuing fulfillment",
            job.story_number,
            job.event_id,
        )
        return []


def _assess_intake_feedback(
    *,
    client: WritebackClient,
    config: BuildClaimFulfillmentConfig,
    job: FulfillmentJobRecord,
) -> list[FulfillmentArtifactRef]:
    stories = _intake_stories(
        client.fetch_stories(sysparm_query=_intake_story_query(job), limit=1)
    )
    if not stories:
        return []
    story = enrich_story(stories[0]).enriched_story
    feedback = build_intake_feedback(analyze_story_capabilities(story))
    if feedback is None:
        return []
    if not config.apply or config.audit_root is None or not config.actor_id:
        return [_intake_payload_artifact(feedback)]

    marker_path = _intake_feedback_artifact_path(config.audit_root, feedback=feedback)
    if marker_path.exists():
        return [_intake_path_artifact(marker_path)]

    client.update_story_fields(stories[0].sys_id, _intake_note_fields(feedback))
    written_path = write_json_artifact_once(
        config.audit_root,
        filename=marker_path.name,
        payload={
            "feedback": feedback.model_dump(mode="json"),
            "delivered_fields": ["work_notes"],
            "lifecycle_event_id": job.event_id,
            "job_id": job.job_id,
            "actor_id": config.actor_id,
        },
    )
    return [_intake_path_artifact(written_path)]


def _intake_story_query(job: FulfillmentJobRecord) -> str:
    if job.story_sys_id:
        return f"sys_id={job.story_sys_id}"
    return f"number={job.story_number}"


def _intake_stories(stories: object) -> list[Story]:
    if type(stories) is not list:
        raise ValueError(INTAKE_STORY_FETCH_NON_JSON_DIAGNOSTIC)
    for story in stories:
        if type(story) is not Story:
            raise ValueError(INTAKE_STORY_FETCH_NON_JSON_DIAGNOSTIC)
    return stories


def _intake_note_fields(feedback: IntakeFeedback) -> dict[str, object]:
    fields: dict[str, object] = {"work_notes": intake_feedback_work_note(feedback)}
    disallowed = sorted(set(fields) - StoryWritebackPolicy().allowed_fields)
    if disallowed:
        raise RuntimeError(
            f"intake feedback fields are not allowlisted: {', '.join(disallowed)}"
        )
    return fields


def _intake_feedback_artifact_path(root: Path, *, feedback: IntakeFeedback) -> Path:
    return root / (
        f"{feedback.story_number}-intake-feedback-{feedback.content_hash[:16]}.json"
    )


def _intake_payload_artifact(feedback: IntakeFeedback) -> FulfillmentArtifactRef:
    return FulfillmentArtifactRef(
        artifact_kind=INTAKE_FEEDBACK_ARTIFACT_KIND,
        schema_version=INTAKE_FEEDBACK_SCHEMA_VERSION,
        payload_json=feedback.model_dump(mode="json"),
    )


def _intake_path_artifact(path: Path) -> FulfillmentArtifactRef:
    return FulfillmentArtifactRef(
        artifact_kind=INTAKE_FEEDBACK_ARTIFACT_KIND,
        path=str(path),
        sha256=artifact_sha256_file(path),
    )


def _raise_if_blocked(result: WritebackExecutionResult) -> None:
    reasons = result.reasons or result.plan.reasons
    if not result.allowed:
        raise FulfillmentBlocked(reasons)
    if reasons and not result.idempotent:
        raise FulfillmentBlocked(reasons)


def _message_for_result(result: WritebackExecutionResult) -> str:
    if result.idempotent:
        return f"Build claim already recorded for {result.plan.story_number}"
    if result.applied:
        return f"Build claim applied for {result.plan.story_number}"
    return f"Build claim planned for {result.plan.story_number}"
