from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from jedi_devproject.artifacts import (
    build_claim_audit_artifact_path,
    write_build_claim_audit_artifact,
    write_writeback_audit_artifact,
    writeback_audit_artifact_path,
)
from jedi_devproject.cli_io import load_json_list
from jedi_devproject.models import Story
from jedi_devproject.servicenow import StoryDictionaryField, StoryStateChoice
from jedi_devproject.work_note_safety import WORK_NOTE_TRUNCATION_MARKER
from jedi_devproject.writeback import (
    MAX_EXTERNAL_BUILD_WORK_NOTE_VALUE_CHARS,
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
    structured_writeback_field_value,
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
    model_config = ConfigDict(hide_input_in_errors=True)

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
    model_config = ConfigDict(hide_input_in_errors=True)

    story_number: str
    story_sys_id: str | None = None
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
    model_config = ConfigDict(hide_input_in_errors=True)

    story_number: str
    build_reference: str
    artifact_url: str | None = None
    build_status: ExternalBuildStatus = ExternalBuildStatus.SUCCEEDED
    from_state: str


class WritebackExecutionResult(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    plan: StoryWritebackPlan
    allowed: bool
    applied: bool
    idempotent: bool = False
    audit_path: Path | None = None
    reasons: list[str] = Field(default_factory=list)


class WritebackBatchResult(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    capability: WritebackCapabilityResult
    results: list[WritebackExecutionResult] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)


class WritebackCapabilityResult(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    allowed: bool
    ready_for_testing_state: str | None = None
    missing_fields: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class WritebackVerificationResult(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    story_number: str
    verified: bool
    expected_state: str | None = None
    actual_fields: dict[str, str | None] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)


MAX_WRITEBACK_BATCH_REPORT_DIAGNOSTIC_DEPTH = 32
WRITEBACK_BATCH_REPORT_CIRCULAR_REFERENCE_MARKER = "[circular reference]"
WRITEBACK_BATCH_REPORT_MAX_DEPTH_MARKER = "[max depth exceeded]"
WRITEBACK_BATCH_REPORT_NON_JSON_KEY_MARKER = "[non-json key]"
WRITEBACK_BATCH_REPORT_NON_JSON_VALUE_MARKER = "[non-json value]"
WRITEBACK_STATE_CHOICES_NON_JSON_DIAGNOSTIC = (
    "writeback state choices contain non-JSON value"
)
WRITEBACK_DICTIONARY_FIELDS_NON_JSON_DIAGNOSTIC = (
    "writeback dictionary fields contain non-JSON value"
)
WRITEBACK_STORIES_NON_JSON_DIAGNOSTIC = "writeback stories contain non-JSON value"


def evaluate_writeback_capability(client: WritebackClient) -> WritebackCapabilityResult:
    state_mapping = build_state_mapping_from_choices(
        [choice.model_dump() for choice in _writeback_state_choices(client)]
    )
    dictionary_fields = _writeback_dictionary_fields(client.fetch_story_dictionary_fields())
    available_fields = {field.element for field in dictionary_fields}
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
    stories = _writeback_stories(
        client.fetch_stories(sysparm_query=f"number={story_number}", limit=1)
    )
    if not stories:
        return WritebackVerificationResult(
            story_number=story_number,
            verified=False,
            reasons=["story_not_found"],
        )

    state_mapping = build_state_mapping_from_choices(
        [choice.model_dump() for choice in _writeback_state_choices(client)]
    )
    if state_mapping is None:
        return WritebackVerificationResult(
            story_number=stories[0].number,
            verified=False,
            reasons=["ready_for_testing_state_not_found"],
        )

    story = stories[0]
    raw_actual_fields = {
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
        "u_ai_build_reference": structured_writeback_field_value(build_reference),
        "u_ai_candidate_artifact": (
            structured_writeback_field_value(artifact_url)
            if artifact_url is not None
            else None
        ),
    }
    reasons = [
        f"{field}_mismatch"
        for field, expected_value in expected_fields.items()
        if raw_actual_fields.get(field) != expected_value
    ]
    return WritebackVerificationResult(
        story_number=story.number,
        verified=not reasons,
        expected_state=state_mapping.ready_for_testing,
        actual_fields=_diagnostic_actual_fields(raw_actual_fields),
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
    payload = load_json_list(path, "writeback job file")
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
        "execution_id": _diagnostic_report_value(execution_id),
        "actor_id": _diagnostic_report_value(actor_id),
        "capability": _diagnostic_report_value(
            batch.capability.model_dump(mode="python", warnings=False)
        ),
        "summary": _diagnostic_report_value(batch.summary),
        "results": [
            {
                "story_number": _diagnostic_report_value(result.plan.story_number),
                "allowed": _diagnostic_report_value(result.allowed),
                "applied": _diagnostic_report_value(result.applied),
                "idempotent": _diagnostic_report_value(result.idempotent),
                "audit_path": (
                    _diagnostic_report_value(str(result.audit_path))
                    if result.audit_path
                    else None
                ),
                "reasons": _diagnostic_report_value(result.reasons or result.plan.reasons),
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
    stories = _writeback_stories(
        client.fetch_stories(
            sysparm_query=f"number={request.story_number}",
            limit=1,
        )
    )
    if not stories:
        return _blocked_result("story_not_found")

    story = stories[0].model_copy(update={"state": request.from_state})
    state_mapping = build_state_mapping_from_choices(
        [choice.model_dump() for choice in _writeback_state_choices(client)]
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
    stories = _writeback_stories(
        client.fetch_stories(
            sysparm_query=(
                f"sys_id={request.story_sys_id}"
                if request.story_sys_id
                else f"number={request.story_number}"
            ),
            limit=1,
        ),
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


def _writeback_state_choices(client: WritebackClient) -> list[StoryStateChoice]:
    choices = client.fetch_story_state_choices()
    if type(choices) is not list:
        raise ValueError(WRITEBACK_STATE_CHOICES_NON_JSON_DIAGNOSTIC)
    for choice in choices:
        if type(choice) is not StoryStateChoice:
            raise ValueError(WRITEBACK_STATE_CHOICES_NON_JSON_DIAGNOSTIC)
    return choices


def _writeback_dictionary_fields(fields: object) -> list[StoryDictionaryField]:
    if type(fields) is not list:
        raise ValueError(WRITEBACK_DICTIONARY_FIELDS_NON_JSON_DIAGNOSTIC)
    for field in fields:
        if type(field) is not StoryDictionaryField:
            raise ValueError(WRITEBACK_DICTIONARY_FIELDS_NON_JSON_DIAGNOSTIC)
    return fields


def _writeback_stories(stories: object) -> list[Story]:
    if type(stories) is not list:
        raise ValueError(WRITEBACK_STORIES_NON_JSON_DIAGNOSTIC)
    for story in stories:
        if type(story) is not Story:
            raise ValueError(WRITEBACK_STORIES_NON_JSON_DIAGNOSTIC)
    return stories


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


def _diagnostic_actual_fields(
    actual_fields: dict[str, str | None],
) -> dict[str, str | None]:
    return {
        field: structured_writeback_field_value(value) if value is not None else None
        for field, value in actual_fields.items()
    }


def _diagnostic_report_value(value: Any) -> Any:
    return _diagnostic_report_node(value, depth=0, seen_container_ids=set())


def _diagnostic_report_node(
    value: Any,
    *,
    depth: int,
    seen_container_ids: set[int],
) -> Any:
    if type(value) is str:
        return structured_writeback_field_value(value)
    if value is None or type(value) is bool or type(value) is int:
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        return WRITEBACK_BATCH_REPORT_NON_JSON_VALUE_MARKER
    if (
        depth >= MAX_WRITEBACK_BATCH_REPORT_DIAGNOSTIC_DEPTH
        and type(value) in (dict, list, tuple)
    ):
        return WRITEBACK_BATCH_REPORT_MAX_DEPTH_MARKER
    if type(value) is list:
        container_id = id(value)
        if container_id in seen_container_ids:
            return WRITEBACK_BATCH_REPORT_CIRCULAR_REFERENCE_MARKER
        seen_container_ids.add(container_id)
        try:
            return [
                _diagnostic_report_node(
                    item,
                    depth=depth + 1,
                    seen_container_ids=seen_container_ids,
                )
                for item in value
            ]
        finally:
            seen_container_ids.remove(container_id)
    if type(value) is tuple:
        container_id = id(value)
        if container_id in seen_container_ids:
            return WRITEBACK_BATCH_REPORT_CIRCULAR_REFERENCE_MARKER
        seen_container_ids.add(container_id)
        try:
            return [
                _diagnostic_report_node(
                    item,
                    depth=depth + 1,
                    seen_container_ids=seen_container_ids,
                )
                for item in value
            ]
        finally:
            seen_container_ids.remove(container_id)
    if type(value) is dict:
        container_id = id(value)
        if container_id in seen_container_ids:
            return WRITEBACK_BATCH_REPORT_CIRCULAR_REFERENCE_MARKER
        seen_container_ids.add(container_id)
        try:
            projected: dict[str, Any] = {}
            for key, item in value.items():
                projected[
                    _deduplicated_diagnostic_report_key(
                        projected,
                        _diagnostic_report_key(key),
                    )
                ] = _diagnostic_report_node(
                    item,
                    depth=depth + 1,
                    seen_container_ids=seen_container_ids,
                )
            return projected
        finally:
            seen_container_ids.remove(container_id)
    return WRITEBACK_BATCH_REPORT_NON_JSON_VALUE_MARKER


def _diagnostic_report_key(key: object) -> str:
    if type(key) is str:
        return structured_writeback_field_value(key) or "[empty key]"
    return WRITEBACK_BATCH_REPORT_NON_JSON_KEY_MARKER


def _deduplicated_diagnostic_report_key(
    existing: dict[str, Any],
    rendered_key: str,
) -> str:
    if rendered_key not in existing:
        return rendered_key
    duplicate_count = 2
    while True:
        candidate = _duplicate_diagnostic_report_key(
            rendered_key,
            duplicate_count=duplicate_count,
        )
        if candidate not in existing:
            return candidate
        duplicate_count += 1


def _duplicate_diagnostic_report_key(rendered_key: str, *, duplicate_count: int) -> str:
    suffix = f" [duplicate {duplicate_count}]"
    if len(rendered_key) + len(suffix) <= MAX_EXTERNAL_BUILD_WORK_NOTE_VALUE_CHARS:
        return f"{rendered_key}{suffix}"
    prefix_budget = (
        MAX_EXTERNAL_BUILD_WORK_NOTE_VALUE_CHARS
        - len(WORK_NOTE_TRUNCATION_MARKER)
        - len(suffix)
    )
    return rendered_key[:prefix_budget].rstrip() + WORK_NOTE_TRUNCATION_MARKER + suffix


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
    dictionary_fields: object,
    state_mapping_found: bool,
) -> set[str]:
    available_fields = {field.element for field in _writeback_dictionary_fields(dictionary_fields)}
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
