from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import BaseModel, ValidationError

from jedi_devproject.alert_delivery import ExternalAlert
from jedi_devproject.builder_maturity import BuilderMaturityScore, MaturityEvidence
from jedi_devproject.context_escalation import ContextEscalationPlan
from jedi_devproject.fulfillment_worker import (
    FulfillmentArtifactRef,
    FulfillmentExecutionResult,
    FulfillmentPersistedArtifact,
    FulfillmentWorkerResult,
)
from jedi_devproject.runtime_worker import StaleJobRequeueReport


def test_operational_dto_validation_errors_do_not_echo_rejected_inputs() -> None:
    cases: list[tuple[type[BaseModel], dict[str, object], tuple[str, ...]]] = [
        (
            ExternalAlert,
            {
                "alert_id": "alert-secret",
                "severity": "critical",
                "job_id": "job-secret",
                "event_id": "evt-secret",
                "story_number": "STRY0010001",
                "status": "failed",
                "summary": "summary",
                "detail": "secret-alert-detail",
                "operator_action": "inspect",
                "created_at": "secret-created-at",
            },
            ("secret-created-at", "secret-alert-detail"),
        ),
        (
            MaturityEvidence,
            {
                "surface": "secret-surface",
                "samples": "secret-samples",
                "successes": 0,
                "failures": 0,
            },
            ("secret-surface", "secret-samples"),
        ),
        (
            BuilderMaturityScore,
            {
                "surface": "catalog_definitions",
                "baseline": 0.6,
                "score": 0.7,
                "source": "secret-source",
            },
            ("secret-source",),
        ),
        (
            ContextEscalationPlan,
            {
                "action": "secret-action",
                "should_retrieve": False,
                "should_call_model": False,
                "reasons": ["secret-reason"],
            },
            ("secret-action", "secret-reason"),
        ),
        (
            FulfillmentArtifactRef,
            {
                "artifact_kind": "candidate",
                "payload_json": "secret-payload",
            },
            ("secret-payload",),
        ),
        (
            FulfillmentPersistedArtifact,
            {
                "artifact_kind": "candidate",
                "path": "db://artifact_blobs/secret",
                "sha256": 123,
            },
            ("db://artifact_blobs/secret", "123"),
        ),
        (
            FulfillmentExecutionResult,
            {
                "message": "secret-message",
                "artifacts": ["secret-artifact"],
            },
            ("secret-message", "secret-artifact"),
        ),
        (
            FulfillmentWorkerResult,
            {
                "status": "failed",
                "job_id": "job-secret",
                "story_number": "STRY0010001",
                "message": None,
                "error_message": 123,
            },
            ("job-secret", "123"),
        ),
        (
            StaleJobRequeueReport,
            {
                "enabled": True,
                "requeued_at": datetime(2026, 5, 13, 17, 0, tzinfo=UTC),
                "stale_before": "secret-stale-before",
                "stale_after_seconds": 3600,
                "requeued_count": 1,
                "job_ids": ["secret-job-id"],
            },
            ("secret-stale-before", "secret-job-id"),
        ),
    ]

    for model_class, values, secret_fragments in cases:
        with pytest.raises(ValidationError) as exc_info:
            model_class.model_validate(values)

        error_text = str(exc_info.value)
        assert "input_value" not in error_text
        for fragment in secret_fragments:
            assert fragment not in error_text
