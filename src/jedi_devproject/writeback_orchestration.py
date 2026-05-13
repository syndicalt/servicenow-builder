from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, Field

from jedi_devproject.artifacts import (
    build_claim_audit_artifact_path,
    write_build_claim_audit_artifact,
    write_writeback_audit_artifact,
    writeback_audit_artifact_path,
)
from jedi_devproject.models import Story
from jedi_devproject.servicenow import StoryDictionaryField, StoryStateChoice
from jedi_devproject.writeback import (
    REQUIRED_STRUCTURED_WRITEBACK_FIELDS,
    ActorType,
    BuildClaimAuditEvent,
    ExternalBuildResult,
    ExternalBuildStatus,
    StoryWritebackPlan,
    StoryWritebackPolicy,
    WritebackAuditEvent,
    build_state_mapping_from_choices,
    plan_external_build_writeback,
    plan_story_build_claim_writeback,
    validate_writeback_fields,
)


class WritebackClient(Protocol):
    def fetch_stories(
        self,
        sysparm_query: str | None = None,
        *,
        limit: int = 100,
    ) -> list[Story]:
        """Fetch ServiceNow stories."""

    def fetch_story_state_choices(self) -> list[StoryStateChoice]:
        """Fetch active story state choices."""

    def fetch_story_dictionary_fields(self) -> list[StoryDictionaryField]:
        """Fetch active story dictionary fields."""

    def update_story_fields(self, story_sys_id: str, fields: dict[str, object]) -> object:
        """Update fields on a story."""


class WritebackExecutionRequest(BaseModel):
    story_number: str
    build_reference: str
    artifact_url: str | None = None
    build_status: ExternalBuildStatus = ExternalBuildStatus.SUCCEEDED
    from_state: str
    apply: bool = False
    confirm_story_number: str | None = None
    actor_type: ActorType = ActorType.SERVICE
    actor_id: str | None = None
    execution_id: str | None = None
    audit_root: Path | None = None


class BuildClaimExecutionRequest(BaseModel):
    story_number: str
    lifecycle_event_id: str
    candidate_artifact_url: str | None = None
    from_state: str
    claim_state: str = "Work in Progress"
    apply: bool = False
    confirm_story_number: str | None = None
    actor_type: ActorType = ActorType.SERVICE
    actor_id: str | None = None
    execution_id: str | None = None
    audit_root: Path | None = None


class WritebackJobRecord(BaseModel):
    story_number: str
    build_reference: str
    artifact_url: str | None = None
    build_status: ExternalBuildStatus = ExternalBuildStatus.SUCCEEDED
    from_state: str


class WritebackExecutionResult(BaseModel):
    plan: StoryWritebackPlan
    allowed: bool
    applied: bool
    idempotent: bool = False
    audit_path: Path | None = None
    reasons: list[str] = Field(default_factory=list)


class WritebackBatchResult(BaseModel):
    capability: WritebackCapabilityResult
    results: list[WritebackExecutionResult] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)


class WritebackCapabilityResult(BaseModel):
    allowed: bool
    ready_for_testing_state: str | None = None
    missing_fields: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class WritebackVerificationResult(BaseModel):
    story_number: str
    verified: bool
    expected_state: str | None = None
    actual_fields: dict[str, str | None] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)


def evaluate_writeback_capability(client: WritebackClient) -> WritebackCapabilityResult:
    state_mapping = build_state_mapping_from_choices(
        [choice.model_dump() for choice in client.fetch_story_state_choices()]
    )
    available_fields = {
        field.element for field in client.fetch_story_dictionary_fields()
    }
    if state_mapping is not None:
        available_fields.add("state")
    missing_fields = sorted(REQUIRED_STRUCTURED_WRITEBACK_FIELDS - available_fields)
    reasons: list[str] = []
    if state_mapping is None:
        reasons.append("ready_for_testing_state_not_found")
    if missing_fields:
        reasons.append("missing_required_writeback_fields")

    return WritebackCapabilityResult(
        allowed=not reasons,
        ready_for_testing_state=(
            state_mapping.ready_for_testing if state_mapping is not None else None
        ),
        missing_fields=missing_fields,
        reasons=reasons,
    )


def verify_writeback(
    client: WritebackClient,
    *,
    story_number: str,
    build_reference: str,
    artifact_url: str | None,
) -> WritebackVerificationResult:
    stories = client.fetch_stories(sysparm_query=f"number={story_number}", limit=1)
    if not stories:
        return WritebackVerificationResult(
            story_number=story_number,
            verified=False,
            reasons=["story_not_found"],
        )

    state_mapping = build_state_mapping_from_choices(
        [choice.model_dump() for choice in client.fetch_story_state_choices()]
    )
    if state_mapping is None:
        return WritebackVerificationResult(
            story_number=stories[0].number,
            verified=False,
            reasons=["ready_for_testing_state_not_found"],
        )

    story = stories[0]
    actual_fields = {
        "state": story.state,
        "u_ai_status": story.additional_context.get("u_ai_status"),
        "u_ai_build_reference": story.additional_context.get("u_ai_build_reference"),
        "u_ai_candidate_artifact": story.additional_context.get(
            "u_ai_candidate_artifact"
        ),
    }
    expected_fields = {
        "state": state_mapping.ready_for_testing,
        "u_ai_status": "Ready for Testing",
        "u_ai_build_reference": build_reference,
        "u_ai_candidate_artifact": artifact_url,
    }
    reasons = [
        f"{field}_mismatch"
        for field, expected_value in expected_fields.items()
        if actual_fields.get(field) != expected_value
    ]
    return WritebackVerificationResult(
        story_number=story.number,
        verified=not reasons,
        expected_state=state_mapping.ready_for_testing,
        actual_fields=actual_fields,
        reasons=reasons,
    )


def load_writeback_requests(
    path: Path,
    *,
    apply: bool,
    actor_type: ActorType,
    actor_id: str,
    execution_id: str | None,
    audit_root: Path,
) -> list[WritebackExecutionRequest]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    jobs = [WritebackJobRecord.model_validate(item) for item in payload]
    if not jobs:
        raise ValueError("writeback job file must contain at least one writeback job")

    return [
        WritebackExecutionRequest(
            story_number=job.story_number,
            build_reference=job.build_reference,
            artifact_url=job.artifact_url,
            build_status=job.build_status,
            from_state=job.from_state,
            apply=apply,
            confirm_story_number=job.story_number,
            actor_type=actor_type,
            actor_id=actor_id,
            execution_id=execution_id,
            audit_root=audit_root,
        )
        for job in jobs
    ]


def build_writeback_batch_report(
    batch: WritebackBatchResult,
    *,
    execution_id: str | None,
    actor_id: str,
) -> dict[str, Any]:
    return {
        "execution_id": execution_id,
        "actor_id": actor_id,
        "capability": batch.capability.model_dump(mode="json"),
        "summary": batch.summary,
        "results": [
            {
                "story_number": result.plan.story_number,
                "allowed": result.allowed,
                "applied": result.applied,
                "idempotent": result.idempotent,
                "audit_path": str(result.audit_path) if result.audit_path else None,
                "reasons": result.reasons or result.plan.reasons,
            }
            for result in batch.results
        ],
    }


def run_writeback_batch(
    client: WritebackClient,
    requests: list[WritebackExecutionRequest],
) -> WritebackBatchResult:
    capability = evaluate_writeback_capability(client)
    if not capability.allowed:
        results = [_blocked_batch_result(request) for request in requests]
        return WritebackBatchResult(
            capability=capability,
            results=results,
            summary=_batch_summary(results),
        )

    results = [execute_writeback(client, request) for request in requests]
    return WritebackBatchResult(
        capability=capability,
        results=results,
        summary=_batch_summary(results),
    )


def execute_writeback(
    client: WritebackClient,
    request: WritebackExecutionRequest,
) -> WritebackExecutionResult:
    stories = client.fetch_stories(
        sysparm_query=f"number={request.story_number}",
        limit=1,
    )
    if not stories:
        return _blocked_result("story_not_found")

    story = stories[0].model_copy(update={"state": request.from_state})
    state_mapping = build_state_mapping_from_choices(
        [choice.model_dump() for choice in client.fetch_story_state_choices()]
    )
    if state_mapping is None:
        return _blocked_result("ready_for_testing_state_not_found", story=story)

    if _remote_writeback_already_applied(
        story=stories[0],
        target_state=state_mapping.ready_for_testing,
        build_reference=request.build_reference,
    ):
        plan = StoryWritebackPlan(
            story_sys_id=stories[0].sys_id,
            story_number=stories[0].number,
            work_notes="",
            allowed=True,
        )
        return WritebackExecutionResult(
            plan=plan,
            allowed=True,
            applied=False,
            idempotent=True,
            reasons=["remote_writeback_already_applied"],
        )

    plan = plan_external_build_writeback(
        story=story,
        build_result=ExternalBuildResult(
            status=request.build_status,
            build_reference=request.build_reference,
            artifact_url=request.artifact_url,
        ),
        state_mapping=state_mapping,
        policy=StoryWritebackPolicy(
            state_transitions_enabled=True,
            allowed_state_transitions={request.from_state: {state_mapping.ready_for_testing}},
        ),
    )
    plan = validate_writeback_fields(
        plan,
        available_fields=_available_writeback_fields(
            dictionary_fields=client.fetch_story_dictionary_fields(),
            state_mapping_found=state_mapping is not None,
        ),
    )
    if not plan.allowed:
        return WritebackExecutionResult(
            plan=plan,
            allowed=False,
            applied=False,
            reasons=plan.reasons,
        )
    if not request.apply:
        return WritebackExecutionResult(plan=plan, allowed=True, applied=False)
    if request.confirm_story_number != plan.story_number:
        return WritebackExecutionResult(
            plan=plan,
            allowed=True,
            applied=False,
            reasons=["confirmation_mismatch"],
        )
    if not request.actor_id or request.audit_root is None:
        return WritebackExecutionResult(
            plan=plan,
            allowed=True,
            applied=False,
            reasons=["actor_identity_required"],
        )

    event = WritebackAuditEvent(
        story_number=plan.story_number,
        build_reference=request.build_reference,
        actor_type=request.actor_type,
        actor_id=request.actor_id,
        run_id=request.execution_id,
        apply_requested=True,
        applied=True,
        allowed=plan.allowed,
        fields=plan.fields,
        reasons=plan.reasons,
    )
    audit_path = writeback_audit_artifact_path(request.audit_root, event=event)
    if audit_path.exists():
        return WritebackExecutionResult(
            plan=plan,
            allowed=True,
            applied=False,
            idempotent=True,
            audit_path=audit_path,
            reasons=["writeback_already_recorded"],
        )

    fields_to_apply: dict[str, object] = dict(plan.fields)
    fields_to_apply["work_notes"] = plan.work_notes
    client.update_story_fields(plan.story_sys_id, fields_to_apply)
    written_audit_path = write_writeback_audit_artifact(
        request.audit_root,
        event=event,
    )
    return WritebackExecutionResult(
        plan=plan,
        allowed=True,
        applied=True,
        audit_path=written_audit_path,
    )


def execute_build_claim(
    client: WritebackClient,
    request: BuildClaimExecutionRequest,
) -> WritebackExecutionResult:
    stories = client.fetch_stories(
        sysparm_query=f"number={request.story_number}",
        limit=1,
    )
    if not stories:
        return _blocked_result("story_not_found")

    story = stories[0]
    if story.state != request.from_state:
        return _blocked_result("fresh_story_state_mismatch", story=story)

    plan = plan_story_build_claim_writeback(
        story=story,
        lifecycle_event_id=request.lifecycle_event_id,
        candidate_artifact_url=request.candidate_artifact_url,
        claim_state=request.claim_state,
        policy=StoryWritebackPolicy(
            state_transitions_enabled=True,
            allowed_state_transitions={request.from_state: {request.claim_state}},
        ),
    )
    plan = _validate_claim_writeback_fields(
        plan,
        available_fields=_available_writeback_fields(
            dictionary_fields=client.fetch_story_dictionary_fields(),
            state_mapping_found=True,
        ),
    )
    if not plan.allowed:
        return WritebackExecutionResult(
            plan=plan,
            allowed=False,
            applied=False,
            reasons=plan.reasons,
        )
    if not request.apply:
        return WritebackExecutionResult(plan=plan, allowed=True, applied=False)
    if request.confirm_story_number != plan.story_number:
        return WritebackExecutionResult(
            plan=plan,
            allowed=True,
            applied=False,
            reasons=["confirmation_mismatch"],
        )
    if not request.actor_id or request.audit_root is None:
        return WritebackExecutionResult(
            plan=plan,
            allowed=True,
            applied=False,
            reasons=["actor_identity_required"],
        )

    event = BuildClaimAuditEvent(
        story_number=plan.story_number,
        lifecycle_event_id=request.lifecycle_event_id,
        actor_type=request.actor_type,
        actor_id=request.actor_id,
        run_id=request.execution_id,
        apply_requested=True,
        applied=True,
        allowed=plan.allowed,
        fields=plan.fields,
        reasons=plan.reasons,
    )
    audit_path = build_claim_audit_artifact_path(request.audit_root, event=event)
    if audit_path.exists():
        return WritebackExecutionResult(
            plan=plan,
            allowed=True,
            applied=False,
            idempotent=True,
            audit_path=audit_path,
            reasons=["build_claim_already_recorded"],
        )

    fields_to_apply: dict[str, object] = dict(plan.fields)
    fields_to_apply["work_notes"] = plan.work_notes
    client.update_story_fields(plan.story_sys_id, fields_to_apply)
    written_audit_path = write_build_claim_audit_artifact(
        request.audit_root,
        event=event,
    )
    return WritebackExecutionResult(
        plan=plan,
        allowed=True,
        applied=True,
        audit_path=written_audit_path,
    )


def _blocked_result(
    reason: str,
    *,
    story: Story | None = None,
) -> WritebackExecutionResult:
    plan = StoryWritebackPlan(
        story_sys_id=story.sys_id if story else "",
        story_number=story.number if story else "",
        work_notes="",
        allowed=False,
        reasons=[reason],
    )
    return WritebackExecutionResult(
        plan=plan,
        allowed=False,
        applied=False,
        reasons=[reason],
    )


def _remote_writeback_already_applied(
    *,
    story: Story,
    target_state: str,
    build_reference: str,
) -> bool:
    return (
        story.state == target_state
        and story.additional_context.get("u_ai_build_reference") == build_reference
    )


def _blocked_batch_result(
    request: WritebackExecutionRequest,
) -> WritebackExecutionResult:
    plan = StoryWritebackPlan(
        story_sys_id="",
        story_number=request.story_number,
        work_notes="",
        allowed=False,
        reasons=["writeback_capability_failed"],
    )
    return WritebackExecutionResult(
        plan=plan,
        allowed=False,
        applied=False,
        reasons=["writeback_capability_failed"],
    )


def _available_writeback_fields(
    *,
    dictionary_fields: list[StoryDictionaryField],
    state_mapping_found: bool,
) -> set[str]:
    available_fields = {field.element for field in dictionary_fields}
    if state_mapping_found:
        available_fields.add("state")
    return available_fields


def _validate_claim_writeback_fields(
    plan: StoryWritebackPlan,
    *,
    available_fields: set[str],
) -> StoryWritebackPlan:
    required_fields = {"state", "u_ai_status"} & set(plan.fields)
    if "u_ai_candidate_artifact" in plan.fields:
        required_fields.add("u_ai_candidate_artifact")
    missing_fields = sorted(required_fields - available_fields)
    if not missing_fields:
        return plan
    return plan.model_copy(
        update={
            "allowed": False,
            "reasons": [
                *plan.reasons,
                f"Required build claim fields are missing: {', '.join(missing_fields)}",
            ],
        }
    )


def _batch_summary(results: list[WritebackExecutionResult]) -> dict[str, int]:
    return {
        "total": len(results),
        "allowed": sum(1 for result in results if result.allowed),
        "applied": sum(1 for result in results if result.applied),
        "idempotent": sum(1 for result in results if result.idempotent),
        "blocked": sum(1 for result in results if not result.allowed),
    }
