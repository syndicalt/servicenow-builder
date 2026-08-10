from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from jedi_devproject.update_set_apply import (
    PlannedFormLayoutChange,
    UpdateSetApplyRequest,
    UpdateSetApplyResult,
)
from jedi_devproject.update_set_handoff import (
    UpdateSetHandoffRequest,
    UpdateSetHandoffResult,
)
from jedi_devproject.writeback import (
    BuildClaimAuditEvent,
    ExternalBuildResult,
    StoryStateMapping,
    StoryWritebackPlan,
    StoryWritebackPolicy,
    WritebackAuditEvent,
)
from jedi_devproject.writeback_orchestration import (
    BuildClaimExecutionRequest,
    WritebackBatchResult,
    WritebackCapabilityResult,
    WritebackExecutionRequest,
    WritebackExecutionResult,
    WritebackJobRecord,
    WritebackVerificationResult,
)


def test_update_set_and_writeback_dto_validation_errors_do_not_echo_rejected_inputs() -> None:
    cases: list[tuple[type[BaseModel], dict[str, object], tuple[str, ...]]] = [
        (
            UpdateSetApplyRequest,
            {
                "update_set_sys_id": "secret-update-set",
                "integration_user_name": "secret.integration",
                "candidate": "secret-candidate",
            },
            ("secret-update-set", "secret.integration", "secret-candidate"),
        ),
        (
            UpdateSetApplyResult,
            {
                "applied_change_count": "secret-applied-count",
                "customer_update_count": 1,
            },
            ("secret-applied-count",),
        ),
        (
            PlannedFormLayoutChange,
            {
                "table_name": "secret-table",
                "element": "u_secret",
                "section_sys_id": "secret-section",
                "section_caption": "Secret Section",
                "position": "secret-position",
                "shifted_elements": [],
            },
            ("secret-table", "secret-position"),
        ),
        (
            UpdateSetHandoffRequest,
            {
                "story_sys_id": "secret-story-sys-id",
                "story_number": "STRY0010001",
                "candidate": "secret-candidate",
                "candidate_artifact_ref": "db://artifact_blobs/secret",
                "instance_url": "https://secret.example.invalid",
            },
            ("secret-story-sys-id", "secret-candidate", "db://artifact_blobs/secret"),
        ),
        (
            UpdateSetHandoffResult,
            {
                "update_set_sys_id": "secret-update-set-sys-id",
                "update_set_name": "Secret Update Set",
                "update_set_url": 123,
            },
            ("secret-update-set-sys-id", "Secret Update Set", "123"),
        ),
        (
            ExternalBuildResult,
            {
                "status": "secret-status",
                "build_reference": "secret-build-ref",
                "artifact_url": "db://artifact_blobs/secret",
            },
            ("secret-status", "secret-build-ref", "db://artifact_blobs/secret"),
        ),
        (
            StoryStateMapping,
            {"ready_for_testing": 123},
            ("123",),
        ),
        (
            StoryWritebackPolicy,
            {
                "state_transitions_enabled": True,
                "allowed_state_transitions": {"Ready": ["secret-state"]},
                "allowed_fields": {"state"},
                "secret_extra": "secret-policy-extra",
            },
            ("secret-state", "secret-policy-extra"),
        ),
        (
            StoryWritebackPlan,
            {
                "story_sys_id": "secret-story-sys-id",
                "story_number": "STRY0010001",
                "fields": {"work_notes": "secret-work-note"},
                "work_notes": "secret-work-note",
                "allowed": "secret-allowed",
            },
            ("secret-story-sys-id", "secret-work-note", "secret-allowed"),
        ),
        (
            WritebackAuditEvent,
            {
                "story_number": "STRY0010001",
                "build_reference": "secret-build-ref",
                "actor_type": "secret-actor-type",
                "actor_id": "secret-actor",
                "apply_requested": True,
                "applied": False,
                "allowed": False,
            },
            ("secret-build-ref", "secret-actor-type", "secret-actor"),
        ),
        (
            BuildClaimAuditEvent,
            {
                "story_number": "STRY0010001",
                "lifecycle_event_id": "secret-event",
                "actor_type": "secret-actor-type",
                "actor_id": "secret-actor",
                "apply_requested": True,
                "applied": False,
                "allowed": False,
            },
            ("secret-event", "secret-actor-type", "secret-actor"),
        ),
        (
            WritebackExecutionRequest,
            {
                "story_number": "STRY0010001",
                "build_reference": "secret-build-ref",
                "build_status": "secret-status",
                "from_state": "Ready",
            },
            ("secret-build-ref", "secret-status"),
        ),
        (
            BuildClaimExecutionRequest,
            {
                "story_number": "STRY0010001",
                "lifecycle_event_id": "secret-event",
                "from_state": "Ready",
                "actor_type": "secret-actor-type",
            },
            ("secret-event", "secret-actor-type"),
        ),
        (
            WritebackJobRecord,
            {
                "story_number": "STRY0010001",
                "build_reference": "secret-build-ref",
                "build_status": "secret-status",
                "from_state": "Ready",
            },
            ("secret-build-ref", "secret-status"),
        ),
        (
            WritebackExecutionResult,
            {
                "plan": "secret-plan",
                "allowed": False,
                "applied": False,
                "audit_path": "secret-audit-path",
            },
            ("secret-plan", "secret-audit-path"),
        ),
        (
            WritebackBatchResult,
            {
                "capability": "secret-capability",
                "results": [],
                "summary": {"secret-summary": 1},
            },
            ("secret-capability", "secret-summary"),
        ),
        (
            WritebackCapabilityResult,
            {
                "allowed": "secret-allowed",
                "ready_for_testing_state": "secret-state",
            },
            ("secret-allowed", "secret-state"),
        ),
        (
            WritebackVerificationResult,
            {
                "story_number": "STRY0010001",
                "verified": "secret-verified",
                "actual_fields": {"work_notes": "secret-work-note"},
            },
            ("secret-verified", "secret-work-note"),
        ),
    ]

    for model_class, values, secret_fragments in cases:
        with pytest.raises(ValidationError) as exc_info:
            model_class.model_validate(values)

        error_text = str(exc_info.value)
        assert "input_value" not in error_text
        for fragment in secret_fragments:
            assert fragment not in error_text
