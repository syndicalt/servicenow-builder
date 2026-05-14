from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from jedi_devproject.fulfillment_worker import FulfillmentExecutionResult
from jedi_devproject.operational_store import FulfillmentJobRecord
from jedi_devproject.writeback import ActorType
from jedi_devproject.writeback_orchestration import (
    BuildClaimExecutionRequest,
    WritebackClient,
    WritebackExecutionResult,
    execute_build_claim,
)


class BuildClaimFulfillmentConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    actor_id: str | None
    audit_root: Path | None
    apply: bool = True
    from_state: str = "Ready"
    claim_state: str = "Work in Progress"
    actor_type: ActorType = ActorType.SERVICE
    candidate_artifact_url: str | None = None


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
        return FulfillmentExecutionResult(message=_message_for_result(result))

    return handle


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
