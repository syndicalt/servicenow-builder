from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from jedi_devproject.capabilities import (
    CapabilityProfile,
    FieldFormIntent,
    StoryCapabilityAssessment,
)
from jedi_devproject.capability_assessment import IntakeFeedback
from jedi_devproject.planning import RepointingSuggestion, RunMetrics
from jedi_devproject.review import ReviewEvent, ReviewResult, ReviewSettings
from jedi_devproject.safety import AllowlistPolicy, EligibilityResult
from jedi_devproject.surface_planning import SurfaceOperation, SurfaceOperationPlan


def test_capability_planning_dto_validation_errors_do_not_echo_rejected_inputs() -> None:
    cases: list[tuple[type[BaseModel], dict[str, object], tuple[str, ...]]] = [
        (
            FieldFormIntent,
            {
                "target_table": "incident",
                "field_label": "Secret Field",
                "field_type": "string",
                "placement_position": "secret-position",
            },
            ("Secret Field", "secret-position"),
        ),
        (
            CapabilityProfile,
            {
                "capability": "secret-capability",
                "status": "enabled",
                "supported_artifacts": ["secret-artifact"],
                "required_instance_context": [],
                "deterministic_validators": [],
                "unsupported_cases": [],
                "uat_story_shape": [],
                "researcher": "researcher",
                "build_pipeline": "pipeline",
                "current_max_story_points": 3,
                "target_max_story_points": 5,
            },
            ("secret-capability", "secret-artifact"),
        ),
        (
            StoryCapabilityAssessment,
            {
                "story_number": "STRY0010001",
                "outcome": "secret-outcome",
                "capabilities": ["dictionary_field_create"],
                "supported_capabilities": ["dictionary_field_create"],
                "operator_feedback": ["secret-feedback"],
                "risk_score": 0.2,
                "confidence": 0.8,
            },
            ("secret-outcome", "secret-feedback"),
        ),
        (
            IntakeFeedback,
            {
                "story_number": "STRY0010001",
                "outcome": "secret-outcome",
                "reason_codes": ["secret-reason"],
                "guidance": ["secret-guidance"],
                "suggested_story": "secret-suggested-story",
                "content_hash": "secret-hash",
            },
            ("secret-outcome", "secret-guidance", "secret-suggested-story"),
        ),
        (
            SurfaceOperation,
            {
                "kind": "secret-kind",
                "status": "unsupported",
                "targets": ["secret-target"],
            },
            ("secret-kind", "secret-target"),
        ),
        (
            SurfaceOperationPlan,
            {
                "surface": "secret-surface",
                "target_table": "secret-table",
                "operations": [],
            },
            ("secret-surface", "secret-table"),
        ),
        (
            AllowlistPolicy,
            {
                "story_types": {"dictionary_form"},
                "tables": {"secret-table"},
                "operations": {"update"},
                "max_points": "secret-max-points",
            },
            ("secret-table", "secret-max-points"),
        ),
        (
            EligibilityResult,
            {
                "decision": "secret-decision",
                "story_type": "dictionary_form",
                "reasons": ["secret-reason"],
            },
            ("secret-decision", "secret-reason"),
        ),
        (
            ReviewSettings,
            {"xml_export_enabled": "secret-export-enabled"},
            ("secret-export-enabled",),
        ),
        (
            ReviewEvent,
            {
                "story_number": "STRY0010001",
                "reviewer_id": "secret-reviewer",
                "reason": "secret-review-reason",
                "status_before": "ready_for_review",
                "status_after": "approved_for_export",
                "decided_at": "secret-decided-at",
            },
            ("secret-reviewer", "secret-review-reason", "secret-decided-at"),
        ),
        (
            ReviewResult,
            {
                "candidate": "secret-candidate",
                "event": "secret-event",
            },
            ("secret-candidate", "secret-event"),
        ),
        (
            RepointingSuggestion,
            {
                "story_number": "STRY0010001",
                "original_points": "secret-original-points",
                "suggested_points": 3,
                "evidence": ["secret-evidence"],
            },
            ("secret-original-points", "secret-evidence"),
        ),
        (
            RunMetrics,
            {
                "eligible": "secret-eligible",
                "manual_review": 0,
                "rejected": 0,
                "generated_candidates": 0,
            },
            ("secret-eligible",),
        ),
    ]

    for model_class, values, secret_fragments in cases:
        with pytest.raises(ValidationError) as exc_info:
            model_class.model_validate(values)

        error_text = str(exc_info.value)
        assert "input_value" not in error_text
        for fragment in secret_fragments:
            assert fragment not in error_text
