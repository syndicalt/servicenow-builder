"""Worker-side fulfillment wiring: claim/model handlers and one-shot job processing."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from jedi_devproject.fulfillment_handler import (
    BuildClaimFulfillmentConfig,
    build_claim_fulfillment_handler,
)
from jedi_devproject.fulfillment_worker import (
    FulfillmentExecutionResult,
    FulfillmentHandler,
    FulfillmentWorkerResult,
    process_one_fulfillment_job,
)
from jedi_devproject.implementation_packet import IMPLEMENTATION_PACKET_TASK
from jedi_devproject.model_fulfillment import (
    ModelCandidateFulfillmentConfig,
    model_candidate_fulfillment_handler,
)
from jedi_devproject.models import DataClassification, ProviderPolicy, ProviderStatus
from jedi_devproject.openai_provider import OpenAIProviderSettings, OpenAIResponsesProvider
from jedi_devproject.operational_store import FulfillmentJobRecord
from jedi_devproject.rag import (
    Document,
    PublicWebAccessConfig,
    PublicWebRetriever,
    RagDomain,
    SpecializedRags,
)
from jedi_devproject.runtime_config import (
    JEDI_MODEL_PROVIDER_CONTROL_ERROR,
    JEDI_MODEL_PROVIDER_UNSUPPORTED_ERROR,
    MAX_MODEL_PROVIDER_CHARS,
    RuntimeConfigError,
    RuntimeSettings,
    _direct_optional_runtime_setting_text,
    _runtime_setting_text,
    validate_runtime_settings,
)
from jedi_devproject.runtime_redaction import _redacting_handler, _runtime_secret_values
from jedi_devproject.runtime_servicenow import (
    SplitServiceNowClient,
    _servicenow_development_client_from_settings,
    _servicenow_failure_notifier,
    _servicenow_pm_and_dev_settings_match,
    _servicenow_story_client_from_settings,
)
from jedi_devproject.runtime_store import DEFAULT_STORE_FACTORY, StoreFactory
from jedi_devproject.safety import AllowlistPolicy, StoryType
from jedi_devproject.servicenow import HttpTransport, UrllibTransport
from jedi_devproject.url_query_safety import has_whitespace_or_control_character


def _runtime_handler(
    *,
    settings: RuntimeSettings,
    client: Any,
    claim_handler: FulfillmentHandler,
    transport: HttpTransport,
) -> FulfillmentHandler:
    model_provider = _direct_optional_runtime_setting_text(
        settings.model_provider,
        name="JEDI_MODEL_PROVIDER",
    )
    public_web_access = _runtime_setting_text(
        settings.public_web_access,
        name="JEDI_PUBLIC_WEB_ACCESS",
    )
    if model_provider is None:
        return claim_handler
    if len(model_provider) > MAX_MODEL_PROVIDER_CHARS:
        raise RuntimeConfigError(
            f"JEDI_MODEL_PROVIDER must be <= {MAX_MODEL_PROVIDER_CHARS} characters"
        )
    if has_whitespace_or_control_character(model_provider):
        raise RuntimeConfigError(JEDI_MODEL_PROVIDER_CONTROL_ERROR)
    if model_provider != "openai":
        raise RuntimeConfigError(JEDI_MODEL_PROVIDER_UNSUPPORTED_ERROR)
    openai_api_key = _direct_optional_runtime_setting_text(
        settings.openai_api_key,
        name="OPENAI_API_KEY",
    )
    openai_model = _direct_optional_runtime_setting_text(
        settings.openai_model,
        name="OPENAI_MODEL",
    )
    if not openai_api_key:
        raise RuntimeConfigError("OPENAI_API_KEY is required when JEDI_MODEL_PROVIDER=openai")
    if not openai_model:
        raise RuntimeConfigError("OPENAI_MODEL is required when JEDI_MODEL_PROVIDER=openai")

    model_handler = model_candidate_fulfillment_handler(
        client=client,
        config=ModelCandidateFulfillmentConfig(
            policy=_default_model_allowlist_policy(),
            provider_policy=_default_openai_provider_policy(),
            rags=_default_runtime_rags(),
            provider=OpenAIResponsesProvider(
                settings=_openai_provider_settings_from_values(
                    api_key=openai_api_key,
                    model=openai_model,
                ),
                transport=transport,
            ),
            instance_url=settings.servicenow_dev_instance_url or settings.servicenow_instance_url,
            apply_update_set_changes=settings.update_set_apply,
            update_set_user_name=settings.update_set_user_name,
            classifier_gate=settings.classifier_gate,
            public_doc_retriever=(
                PublicWebRetriever(
                    config=PublicWebAccessConfig(
                        allowed_domains=settings.public_web_allowed_domains,
                        timeout_seconds=settings.public_web_timeout_seconds,
                        max_response_bytes=settings.public_web_max_response_bytes,
                        max_excerpt_chars=settings.public_web_max_excerpt_chars,
                        max_results=settings.public_web_max_results,
                    )
                )
                if public_web_access == "worker"
                else None
            ),
            public_doc_urls=settings.public_web_doc_urls,
        ),
    )

    def handle(job: FulfillmentJobRecord) -> FulfillmentExecutionResult:
        # Generate the candidate first; only record the build claim after the model
        # stage succeeds. This prevents a story state transition (Ready -> Work in
        # Progress) from being left in place when candidate generation fails.
        model_result = model_handler(job)
        claim_result = claim_handler(job)
        return FulfillmentExecutionResult(
            message=model_result.message,
            artifacts=[*claim_result.artifacts, *model_result.artifacts],
            after_artifacts_persisted=model_result.after_artifacts_persisted,
        )

    return handle


def _openai_provider_settings_from_runtime(
    settings: RuntimeSettings,
) -> OpenAIProviderSettings:
    openai_api_key = _direct_optional_runtime_setting_text(
        settings.openai_api_key,
        name="OPENAI_API_KEY",
    )
    openai_model = _direct_optional_runtime_setting_text(
        settings.openai_model,
        name="OPENAI_MODEL",
    )
    return _openai_provider_settings_from_values(
        api_key=openai_api_key or "",
        model=openai_model or "",
    )


def _openai_provider_settings_from_values(
    *,
    api_key: str,
    model: str,
) -> OpenAIProviderSettings:
    try:
        return OpenAIProviderSettings(
            api_key=api_key,
            model=model,
        )
    except ValidationError as exc:
        invalid_fields = _openai_runtime_error_fields(exc)
        raise RuntimeConfigError(
            "Invalid OpenAI provider runtime settings: "
            f"{', '.join(invalid_fields)}"
        ) from None


def _openai_runtime_error_fields(exc: ValidationError) -> list[str]:
    field_names: list[str] = []
    for error in exc.errors():
        location = error.get("loc", ())
        if not location:
            continue
        field = location[0]
        if type(field) is not str:
            field_names.append("OPENAI_PROVIDER_SETTINGS")
            continue
        if field == "api_key":
            field_names.append("OPENAI_API_KEY")
        elif field == "model":
            field_names.append("OPENAI_MODEL")
        elif field == "base_url":
            field_names.append("OPENAI_BASE_URL")
        else:
            field_names.append("OPENAI_PROVIDER_SETTINGS")
    return sorted(set(field_names)) or ["OPENAI_PROVIDER_SETTINGS"]


def process_one_runtime_fulfillment(
    *,
    settings: RuntimeSettings,
    store_factory: StoreFactory = DEFAULT_STORE_FACTORY,
    transport: HttpTransport | None = None,
) -> FulfillmentWorkerResult:
    validate_runtime_settings(settings, require_admin_auth=False)
    if settings.runtime_role == "api":
        raise RuntimeConfigError("JEDI_RUNTIME_ROLE=api cannot run runtime fulfillment")
    request_transport = transport or UrllibTransport()
    story_client = _servicenow_story_client_from_settings(
        settings=settings,
        transport=request_transport,
    )
    development_client = (
        story_client
        if _servicenow_pm_and_dev_settings_match(settings)
        else _servicenow_development_client_from_settings(
            settings=settings,
            transport=request_transport,
        )
    )
    servicenow_client = SplitServiceNowClient(
        story_client=story_client,
        development_client=development_client,
    )
    with store_factory(settings.database_url) as store:
        claim_handler = build_claim_fulfillment_handler(
            client=story_client,
            config=BuildClaimFulfillmentConfig(
                actor_id=settings.worker_id,
                audit_root=settings.audit_root,
                apply=settings.build_claim_apply,
                from_state=settings.build_claim_from_state,
                claim_state=settings.build_claim_state,
            ),
        )
        handler = _runtime_handler(
            settings=settings,
            client=servicenow_client,
            claim_handler=claim_handler,
            transport=request_transport,
        )
        return process_one_fulfillment_job(
            store=store,
            worker_id=settings.worker_id,
            handler=_redacting_handler(
                handler=handler,
                secret_values=_runtime_secret_values(settings),
            ),
            failure_notifier=_servicenow_failure_notifier(
                client=story_client,
                secret_values=_runtime_secret_values(settings),
            ),
        )


def _default_model_allowlist_policy() -> AllowlistPolicy:
    return AllowlistPolicy(
        story_types={StoryType.DICTIONARY_FORM},
        tables={
            "sys_dictionary",
            "sys_ui_form",
            "sys_script",
            "sys_script_client",
            "sys_script_include",
            "sys_ui_policy",
            "sys_ui_policy_action",
            "sys_ui_section",
            "sc_cat_item",
            "item_option_new",
            "sc_cat_item_category",
            "m2m_connected_content",
            "cmdb_identifier",
            "cmdb_identifier_entry",
            "cmdb_reconciliation_definition",
            "sys_object_source",
        },
        operations={"delete", "insert", "update"},
        max_points=3,
    )


def _default_openai_provider_policy() -> ProviderPolicy:
    return ProviderPolicy(
        provider_id="openai-chatgpt",
        deployment_boundary="railway-dev-pdi",
        authorization_level="explicit-dev-evaluation",
        allowed_data_classes={DataClassification.PUBLIC},
        allowed_tasks={IMPLEMENTATION_PACKET_TASK},
        max_context_policy="implementation-packet-v1",
        retention_policy="dev-evaluation-no-training",
        status=ProviderStatus.APPROVED,
    )


def _default_runtime_rags() -> SpecializedRags:
    return SpecializedRags.from_documents(
        [
            Document(
                domain=RagDomain.SERVICENOW_PLATFORM,
                source="runtime/default-servicenow-dictionary-form",
                content=(
                    "rm_story dictionary field work uses sys_dictionary. "
                    "Story form placement uses sys_ui_form."
                ),
                version="runtime-v1",
            ),
            Document(
                domain=RagDomain.INSTANCE_METADATA,
                source="runtime/default-rm-story-metadata",
                content=(
                    "rm_story supports customer-owned custom fields prefixed with u_. "
                    "u_ai_review_notes is the AI Review Notes field."
                ),
                version="runtime-v1",
            ),
            Document(
                domain=RagDomain.PROJECT_CONTEXT,
                source="runtime/default-project-context",
                content=(
                    "AI Review Notes supports implementation review and automated "
                    "fulfillment auditability."
                ),
                version="runtime-v1",
            ),
            Document(
                domain=RagDomain.COMPLIANCE,
                source="runtime/default-compliance-boundary",
                content=(
                    "Only public PDI story context may be sent to the configured "
                    "OpenAI provider during dev evaluation."
                ),
                version="runtime-v1",
            ),
        ]
    )
