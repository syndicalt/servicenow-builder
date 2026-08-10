from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from jedi_devproject.anthropic_provider import AnthropicHttpResponse
from jedi_devproject.artifact_handoff import ArtifactHandoffPlan
from jedi_devproject.cicd_update_sets import (
    CicdUpdateSetCapabilityResult,
    CicdUpdateSetProbe,
)
from jedi_devproject.container_smoke import ContainerLifecycleSmokePlan
from jedi_devproject.discovery.flows import ResolvedFulfillmentFlow
from jedi_devproject.external_build import ExternalBuildPipelineResult
from jedi_devproject.fulfillment_handler import BuildClaimFulfillmentConfig
from jedi_devproject.generic_dictionary_form import DictionaryFormIntent
from jedi_devproject.lifecycle_api import LifecycleWebhookResponse
from jedi_devproject.model_fulfillment import ModelCandidateFulfillmentConfig
from jedi_devproject.pipeline import PipelineInputs, PipelineResult
from jedi_devproject.rate_limit import RateLimitDecision
from jedi_devproject.runtime_worker import (
    RuntimeWorkerLoopSummary,
    RuntimeWorkerSettings,
)


def test_runtime_control_dto_validation_errors_do_not_echo_rejected_inputs() -> None:
    cases: list[tuple[type[BaseModel], Callable[[str], dict[str, Any]]]] = [
        (
            ContainerLifecycleSmokePlan,
            lambda secret: {
                "story_number": "STRY0010001",
                "event_id": "evt-001",
                "apply_enabled": secret,
                "event_payload": {"event_id": "evt-001"},
                "commands": ["POST /lifecycle/events"],
            },
        ),
        (
            ExternalBuildPipelineResult,
            lambda secret: {
                "story_number": "STRY0010001",
                "build_reference": "build-001",
                "status": secret,
                "candidate_artifact_path": Path("artifacts/candidate.json"),
                "build_actor_id": "svc-jedi",
                "failure_reasons": ["blocked"],
            },
        ),
        (
            RateLimitDecision,
            lambda secret: {"allowed": secret, "retry_after_seconds": 0},
        ),
        (
            LifecycleWebhookResponse,
            lambda secret: {
                "accepted": True,
                "event_id": "evt-001",
                "story_number": "STRY0010001",
                "should_evaluate": secret,
                "lifecycle_action": "enqueue",
                "job_id": "job-001",
                "reasons": [],
            },
        ),
        (
            RuntimeWorkerLoopSummary,
            lambda secret: {
                "iterations": secret,
                "completed": 0,
                "idle": 0,
                "failed": 0,
                "stopped_reason": "max_iterations",
            },
        ),
        (
            RuntimeWorkerSettings,
            lambda secret: {
                "runtime": secret,
                "max_iterations": 1,
            },
        ),
        (
            BuildClaimFulfillmentConfig,
            lambda secret: {"actor_id": "svc-jedi", "audit_root": None, "apply": secret},
        ),
        (
            ModelCandidateFulfillmentConfig,
            lambda secret: {
                "policy": secret,
                "provider_policy": secret,
                "rags": secret,
                "provider": object(),
                "instance_url": "https://example.service-now.com",
            },
        ),
        (
            ResolvedFulfillmentFlow,
            lambda secret: {
                "sys_id": "flow-sys-id",
                "name": "Fulfill Catalog Item",
                "trigger_type": 42,
                "rejected_secret": secret,
            },
        ),
        (
            DictionaryFormIntent,
            lambda secret: {
                "target_table": "incident",
                "field_label": "Vendor Reference",
                "field_name": "u_vendor_reference",
                "field_type": "reference",
                "reference_table": "core_company",
                "max_length": secret,
            },
        ),
        (
            AnthropicHttpResponse,
            lambda secret: {"status_code": secret, "json_body": {}, "headers": {}},
        ),
        (
            CicdUpdateSetProbe,
            lambda secret: {"action": "create", "status_code": secret},
        ),
        (
            CicdUpdateSetCapabilityResult,
            lambda secret: {"available": True, "probes": secret},
        ),
        (
            PipelineInputs,
            lambda secret: {
                "stories": secret,
                "policy": secret,
                "rags": secret,
                "artifact_root": Path("artifacts"),
                "run_id": "run-001",
            },
        ),
        (
            PipelineResult,
            lambda secret: {
                "metrics": secret,
                "candidates": [],
                "enrichment_results": [],
                "artifact_paths": [],
                "summary": {},
            },
        ),
        (
            ArtifactHandoffPlan,
            lambda secret: {
                "story_number": "STRY0010001",
                "artifact_kind": secret,
                "artifact_path": "artifacts/update-set.xml",
                "exposure": "internal_evidence",
                "attach_to_servicenow": False,
                "write_story_link": True,
                "required_before_ready_for_testing": False,
                "rationale": "Internal evidence only.",
            },
        ),
    ]

    for model_type, payload_factory in cases:
        secret = f"sprint-332-secret-{model_type.__name__}"

        with pytest.raises(ValidationError) as exc_info:
            model_type.model_validate(payload_factory(secret))

        diagnostic = str(exc_info.value)
        assert "input_value" not in diagnostic, model_type.__name__
        assert secret not in diagnostic, model_type.__name__
