from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from jedi_devproject.bootstrap_fields import (
    BootstrapApplyResult,
    BootstrapFieldPlan,
    BootstrapFieldSpec,
)
from jedi_devproject.bootstrap_lifecycle import (
    LifecycleBusinessRuleSpec,
    LifecycleRestMessageSpec,
    LifecycleWebhookApplyResult,
    LifecycleWebhookBootstrapSpec,
    LifecycleWebhookVerificationResult,
)
from jedi_devproject.bootstrap_update_set_importer import (
    UpdateSetImporterApplyResult,
    UpdateSetImporterBootstrapSpec,
    UpdateSetImporterDefinitionSpec,
    UpdateSetImporterOperationSpec,
)
from jedi_devproject.enrichment import StoryEnrichmentResult
from jedi_devproject.risk import RiskInput


def test_bootstrap_legacy_dto_validation_errors_do_not_echo_rejected_inputs() -> None:
    cases: list[tuple[type[BaseModel], Callable[[str], dict[str, Any]]]] = [
        (
            BootstrapFieldSpec,
            lambda secret: {
                "element": "u_ai_status",
                "column_label": "AI Status",
                "internal_type": "string",
                "max_length": secret,
            },
        ),
        (
            BootstrapFieldPlan,
            lambda secret: {
                "table": "rm_story",
                "missing_fields": ["u_ai_status"],
                "fields_to_create": secret,
                "form_layout_changes": [],
                "requires_apply_confirmation": True,
            },
        ),
        (
            BootstrapApplyResult,
            lambda secret: {
                "applied": secret,
                "created_fields": [],
                "form_layout_changes": [],
                "reasons": [],
            },
        ),
        (
            LifecycleWebhookApplyResult,
            lambda secret: {
                "applied": secret,
                "upserted_records": [],
                "reasons": [],
            },
        ),
        (
            LifecycleWebhookVerificationResult,
            lambda secret: {
                "verified": secret,
                "matched_records": [],
                "missing_records": [],
                "mismatched_fields": {},
                "reasons": [],
            },
        ),
        (
            LifecycleBusinessRuleSpec,
            lambda secret: {
                "name": "Jedi lifecycle emitter",
                "table": "rm_story",
                "when": "after",
                "action": "update",
                "active": secret,
                "condition": "current.state.changes()",
                "script": "gs.info('emit');",
            },
        ),
        (
            LifecycleRestMessageSpec,
            lambda secret: {
                "name": "Jedi lifecycle API",
                "method_name": "post_event",
                "endpoint_url": "https://jedi.example.test/lifecycle/events",
                "http_method": "POST",
                "authentication": "none",
                "content_type": {"rejected": secret},
            },
        ),
        (
            LifecycleWebhookBootstrapSpec,
            lambda secret: {
                "rest_message": secret,
                "business_rule": secret,
            },
        ),
        (
            UpdateSetImporterApplyResult,
            lambda secret: {
                "applied": secret,
                "upserted_records": [],
                "reasons": [],
            },
        ),
        (
            UpdateSetImporterDefinitionSpec,
            lambda secret: {
                "name": "Jedi Update Set Import API",
                "service_id": "jedi_update_set_import",
                "active": secret,
                "consumes": "application/json",
                "produces": "application/json",
                "short_description": "Import retrieved update sets.",
            },
        ),
        (
            UpdateSetImporterOperationSpec,
            lambda secret: {
                "name": "import_update_set_xml",
                "http_method": "POST",
                "active": True,
                "consumes": "application/json",
                "produces": "application/json",
                "requires_authentication": secret,
                "requires_acl_authorization": True,
                "short_description": "Import reviewed Update Set XML.",
                "operation_script": "(function process(){})();",
            },
        ),
        (
            UpdateSetImporterBootstrapSpec,
            lambda secret: {
                "definition": secret,
                "operation": secret,
            },
        ),
        (
            StoryEnrichmentResult,
            lambda secret: {
                "original_story": secret,
                "enriched_story": secret,
                "inferred_tables": [],
                "confidence": 0.0,
                "evidence": [],
            },
        ),
        (
            RiskInput,
            lambda secret: {
                "story_type": "dictionary_form",
                "mandatory": secret,
            },
        ),
    ]

    for model_type, payload_factory in cases:
        secret = f"sprint-333-secret-{model_type.__name__}"

        with pytest.raises(ValidationError) as exc_info:
            model_type.model_validate(payload_factory(secret))

        diagnostic = str(exc_info.value)
        assert "input_value" not in diagnostic, model_type.__name__
        assert secret not in diagnostic, model_type.__name__
