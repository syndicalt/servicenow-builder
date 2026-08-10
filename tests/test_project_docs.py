from pathlib import Path


def test_development_guide_documents_one_verify_command() -> None:
    guide = Path("docs/development.md").read_text(encoding="utf-8")

    assert "python3 -m ruff check src tests" in guide
    assert "python3 -m mypy src tests" in guide
    assert "python3 -m pytest --cov=jedi_devproject" in guide
    assert "--cov-fail-under=90" in guide


def test_operator_guide_documents_plan_writeback_dry_run() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "plan-writeback" in guide
    assert "verify-writeback" in guide
    assert "dry-run" in guide
    assert "Ready for Testing" in guide
    assert "does not apply" in guide
    assert "structured writeback fields" in guide
    assert "--apply" in guide
    assert "--confirm-story-number" in guide
    assert "--actor-id" in guide
    assert "--actor-type" in guide
    assert "--audit-root" in guide
    assert "check-writeback-capability" in guide
    assert "lifecycle manifest" in guide
    assert "record-lifecycle-manifest" in guide
    assert "--manifest-root" in guide
    assert "--packet-path" in guide
    assert "--candidate-path" in guide


def test_operator_guide_documents_implementation_packet_artifact() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "build-implementation-packet" in guide
    assert "--story-number" in guide
    assert "implementation packet" in guide
    assert "Now Assist" in guide
    assert "does not call a model" in guide
    assert "sys_id" in guide


def test_operator_guide_documents_implementation_candidate_artifact() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "build-implementation-candidate" in guide
    assert "--provider-response-file" in guide
    assert "validated implementation candidate" in guide
    assert "write-once" in guide


def test_operator_guide_documents_artifact_handoff_contract() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Artifact Handoff Contract" in guide
    assert "implementation packet" in guide
    assert "implementation candidate" in guide
    assert "internal audit evidence" in guide
    assert "Approved Update Set XML" in guide
    assert "Test Evidence Bundle" in guide
    assert "attach" in guide
    assert "plan-artifact-handoff" in guide
    assert "handoff report" in guide
    assert "SHA-256" in guide
    assert "write-artifact-handoff-summary" in guide
    assert "attach-delivery-artifacts" in guide
    assert "run-delivery-artifact-smoke" in guide
    assert "attachment audit" in guide
    assert "attachment sys_ids" in guide
    assert "delivery_contract" in guide
    assert "reviewed_export" in guide
    assert "smoke_placeholder" in guide
    assert "review-delivery-artifact" in guide
    assert "--reviewer-id" in guide
    assert "run-reviewed-delivery-smoke" in guide
    assert "reviewed-delivery-lifecycle-manifests" in guide
    assert "artifact_hash_mismatch" in guide
    assert "Dry-run attachment planning also verifies" in guide
    assert "artifact_missing" in guide
    assert "sys_update_xml" in guide


def test_operator_guide_documents_external_build_pipeline_contract() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "External Build Pipeline Contract" in guide
    assert "ExternalBuildPipelineResult" in guide
    assert "writeback_job_from_build_result" in guide
    assert "reviewed_delivery_jobs_from_build_result" in guide
    assert "candidate_artifact_path" in guide
    assert "reviewed_update_set_xml_path" in guide
    assert "test_evidence_path" in guide
    assert "story_sys_id" in guide


def test_readme_documents_controlled_story_writeback_scope() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "Controlled ServiceNow story writeback" in readme
    assert "execute_writeback" in readme
    assert "run_writeback_batch" in readme
    assert "Direct Update Set imports" in readme


def test_readme_documents_llm_implementation_packet_architecture() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "LLM implementation packet" in readme
    assert "rules are gates" in readme
    assert "Now Assist" in readme
    assert "generate_implementation_candidate" in readme


def test_readme_documents_postgres_operational_store() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "PostgreSQL operational state" in readme
    assert "DB-backed JSON artifacts" in readme


def test_operator_guide_documents_postgres_operational_store() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Operational Store" in guide
    assert "durable operational state" in guide
    assert "PostgreSQL" in guide
    assert "SELECT ... FOR UPDATE SKIP LOCKED" in guide
    assert "lifecycle_events" in guide
    assert "fulfillment_jobs" in guide
    assert "job_events" in guide
    assert "artifact_blobs" in guide
    assert "artifact_refs" in guide
    assert "DB-backed artifacts" in guide


def test_system_architecture_doc_includes_workflow_and_data_flow_diagrams() -> None:
    architecture = Path("docs/system-architecture.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")
    security_flow = Path("docs/security/data-flow.md").read_text(encoding="utf-8")

    assert "## Runtime Components" in architecture
    assert "## Deployment Topology" in architecture
    assert "## Lifecycle Workflow" in architecture
    assert "## Fulfillment Pipeline" in architecture
    assert "## Data Flow" in architecture
    assert "## Failure Handling" in architecture
    assert "```mermaid" in architecture
    assert "sequenceDiagram" in architecture
    assert "flowchart TD" in architecture
    assert "flowchart LR" in architecture
    assert "ServiceNow Instance" in architecture
    assert "PostgreSQL operational store" in architecture
    assert "instance_context_bundle" in architecture
    assert "implementation_packet" in architecture
    assert "sys_remote_update_set" in architecture
    assert "cmdb_ire_analyze" in architecture
    assert "Split ServiceNow Instances" in architecture
    assert "SERVICENOW_PM_INSTANCE_URL" in architecture
    assert "SERVICENOW_DEV_INSTANCE_URL" in architecture
    assert "docs/system-architecture.md" in readme
    assert "docs/system-architecture.md" in guide
    assert "docs/system-architecture.md" in security_flow


def test_operator_guide_documents_lifecycle_webhook_api() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Lifecycle Webhook API" in guide
    assert "POST /lifecycle/events" in guide
    assert "202 Accepted" in guide
    assert "does not execute fulfillment inline" in guide
    assert "DATABASE_URL" in guide


def test_operator_guide_documents_authenticated_lifecycle_webhook() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Lifecycle Webhook Authentication" in guide
    assert "JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE" in guide
    assert "hmac_sha256" in guide
    assert "X-JEDI-Webhook-Timestamp" in guide
    assert "X-JEDI-Webhook-Signature" in guide
    assert "<timestamp>.<raw request body>" in guide
    assert "sha256-base64=<base64 hmac>" in guide
    assert "GlideCertificateEncryption.generateMac()" in guide
    assert "replay window" in guide


def test_operator_guide_documents_artifact_retrieval_api() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Artifact Retrieval API" in guide
    assert "JEDI_ADMIN_API_TOKEN" in guide
    assert "Authorization: Bearer" in guide
    assert "GET /artifacts/{artifact_id}" in guide
    assert "GET /jobs/{job_id}/artifacts" in guide
    assert "unauthenticated artifact reads are rejected" in guide


def test_operator_guide_documents_fulfillment_worker() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Fulfillment Worker" in guide
    assert "process_one_fulfillment_job" in guide
    assert "build_claim_fulfillment_handler" in guide
    assert "complete_fulfillment_job" in guide
    assert "fail_fulfillment_job" in guide
    assert "outside the webhook request" in guide


def test_operator_guide_documents_runtime_wiring() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime Wiring" in guide
    assert "load_runtime_settings" in guide
    assert "create_runtime_api" in guide
    assert "process_one_runtime_fulfillment" in guide
    assert "run_loop" in guide
    assert "Automated fulfillment failed" in guide
    assert "DATABASE_URL" in guide


def test_operator_guide_documents_chatgpt_implementation_adapter() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ChatGPT Implementation Adapter" in guide
    assert "OpenAIResponsesProvider" in guide
    assert "JEDI_MODEL_PROVIDER=openai" in guide
    assert "OPENAI_API_KEY" in guide
    assert "OPENAI_MODEL" in guide
    assert "Responses API" in guide
    assert "strict JSON schema" in guide
    assert "name/value" in guide
    assert "fail closed" in guide
    assert "sys_remote_update_set" in guide
    assert "remote_update_set" in guide
    assert "JEDI <story number> - AI Candidate" in guide
    assert "preview, scan, resolve, and commit" in guide


def test_sprint_seventy_eight_change_log_documents_openai_runtime_wiring() -> None:
    change_log = Path("docs/sprints/sprint-78-change-log.md").read_text(encoding="utf-8")

    assert "JEDI_MODEL_PROVIDER=openai" in change_log
    assert "OPENAI_API_KEY" in change_log
    assert "model_candidate_fulfillment_handler" in change_log
    assert "implementation_packet" in change_log
    assert "implementation_candidate" in change_log
    assert "no ServiceNow mutation" in change_log


def test_sprint_seventy_nine_change_log_documents_worker_runtime() -> None:
    change_log = Path("docs/sprints/sprint-79-change-log.md").read_text(encoding="utf-8")

    assert "JEDI_BUILD_CLAIM_APPLY=true" in change_log
    assert "Dockerfile.worker" in change_log
    assert "JEDI_WORKER_MAX_ITERATIONS" in change_log
    assert "JEDI_WORKER_IDLE_SLEEP_SECONDS" in change_log
    assert "JEDI_WORKER_STOP_ON_FAILURE" in change_log
    assert "JEDI_BUILD_CLAIM_FROM_STATE" in change_log
    assert "JEDI_BUILD_CLAIM_STATE" in change_log
    assert "jedi-devproject-worker" in change_log


def test_sprint_sixty_eight_change_log_documents_operational_store() -> None:
    change_log = Path("docs/sprints/sprint-68-change-log.md").read_text(encoding="utf-8")

    assert "operational_store" in change_log
    assert "claim_next_fulfillment_job" in change_log
    assert "locked_by" in change_log
    assert "artifact_refs" in change_log
    assert "PostgreSQL" in change_log


def test_sprint_sixty_nine_change_log_documents_postgres_retarget() -> None:
    change_log = Path("docs/sprints/sprint-69-change-log.md").read_text(encoding="utf-8")

    assert "PostgresOperationalStore" in change_log
    assert "psycopg" in change_log
    assert "0001_operational_store.sql" in change_log
    assert "JSONB" in change_log
    assert "SELECT ... FOR UPDATE SKIP LOCKED" in change_log


def test_sprint_seventy_change_log_documents_lifecycle_webhook_api() -> None:
    change_log = Path("docs/sprints/sprint-70-change-log.md").read_text(encoding="utf-8")

    assert "Lifecycle Webhook API" in change_log
    assert "create_lifecycle_api" in change_log
    assert "POST /lifecycle/events" in change_log
    assert "202 Accepted" in change_log
    assert "non-blocking" in change_log


def test_sprint_seventy_one_change_log_documents_fulfillment_worker() -> None:
    change_log = Path("docs/sprints/sprint-71-change-log.md").read_text(encoding="utf-8")

    assert "fulfillment_worker" in change_log
    assert "process_one_fulfillment_job" in change_log
    assert "complete_fulfillment_job" in change_log
    assert "fail_fulfillment_job" in change_log
    assert "outside the webhook request" in change_log


def test_sprint_seventy_two_change_log_documents_build_claim_handler() -> None:
    change_log = Path("docs/sprints/sprint-72-change-log.md").read_text(encoding="utf-8")

    assert "fulfillment_handler" in change_log
    assert "build_claim_fulfillment_handler" in change_log
    assert "execute_build_claim" in change_log
    assert "FulfillmentBlocked" in change_log
    assert "Work in Progress" in change_log


def test_sprint_seventy_three_change_log_documents_runtime_wiring() -> None:
    change_log = Path("docs/sprints/sprint-73-change-log.md").read_text(encoding="utf-8")

    assert "runtime" in change_log
    assert "load_runtime_settings" in change_log
    assert "create_runtime_api" in change_log
    assert "process_one_runtime_fulfillment" in change_log
    assert "DATABASE_URL" in change_log


def test_sprint_seventy_five_change_log_documents_container_smoke() -> None:
    change_log = Path("docs/sprints/sprint-75-change-log.md").read_text(encoding="utf-8")

    assert "container_smoke" in change_log
    assert "plan_container_lifecycle_smoke" in change_log
    assert "Draft" in change_log
    assert "Ready" in change_log
    assert "apply disabled" in change_log


def test_sprint_seventy_six_change_log_documents_public_lifecycle_bootstrap() -> None:
    change_log = Path("docs/sprints/sprint-76-change-log.md").read_text(encoding="utf-8")

    assert "rest_endpoint" in change_log
    assert "sys_rest_message_fn.rest_message" in change_log
    assert "jedi-devproject-0-jedi.up.railway.app/lifecycle/events" in change_log


def test_sprint_seventy_seven_change_log_documents_worker_failure_notes() -> None:
    change_log = Path("docs/sprints/sprint-77-change-log.md").read_text(encoding="utf-8")

    assert "failure_notifier" in change_log
    assert "Automated fulfillment failed" in change_log
    assert "run_loop" in change_log
    assert "OpenAIResponsesProvider" in change_log
    assert "name/value pairs" in change_log
    assert "no_authentication" in change_log


def test_sprint_twenty_nine_change_log_documents_packet_cli() -> None:
    change_log = Path("docs/sprints/sprint-29-change-log.md").read_text(encoding="utf-8")

    assert "build-implementation-packet" in change_log
    assert "reviewable implementation packet artifact" in change_log
    assert "read-only PDI story fetch" in change_log
    assert "no_stories_found" in change_log
    assert "Now Assist" in change_log
    assert "no model call" in change_log


def test_sprint_thirty_change_log_documents_model_contract_hardening() -> None:
    change_log = Path("docs/sprints/sprint-30-change-log.md").read_text(encoding="utf-8")

    assert "implementation output contract" in change_log
    assert "test_plan" in change_log
    assert "rollback_notes" in change_log
    assert "ModelResponseError" in change_log


def test_sprint_thirty_one_change_log_documents_candidate_handoff() -> None:
    change_log = Path("docs/sprints/sprint-31-change-log.md").read_text(encoding="utf-8")

    assert "UpdateSetCandidate" in change_log
    assert "generate_implementation_update_set_candidate" in change_log
    assert "artifact_hash" in change_log
    assert "reviewable handoff" in change_log
    assert "manual-review" in change_log


def test_sprint_thirty_two_change_log_documents_candidate_cli() -> None:
    change_log = Path("docs/sprints/sprint-32-change-log.md").read_text(encoding="utf-8")

    assert "build-implementation-candidate" in change_log
    assert "provider response file" in change_log
    assert "PDI story source" in change_log
    assert "write-once candidate artifact" in change_log
    assert "unsafe provider response" in change_log


def test_sprint_thirty_three_change_log_documents_candidate_batch_runner() -> None:
    change_log = Path("docs/sprints/sprint-33-change-log.md").read_text(encoding="utf-8")

    assert "run-implementation-candidates" in change_log
    assert "implementation candidate jobs file" in change_log
    assert "no_jobs" in change_log
    assert "safe summary" in change_log


def test_sprint_thirty_four_change_log_documents_candidate_batch_reports() -> None:
    change_log = Path("docs/sprints/sprint-34-change-log.md").read_text(encoding="utf-8")

    assert "candidate batch report" in change_log
    assert "--batch-report-root" in change_log
    assert "per-story outcome" in change_log
    assert "ServiceNow sys_id" in change_log


def test_sprint_thirty_five_change_log_documents_failure_isolation() -> None:
    change_log = Path("docs/sprints/sprint-35-change-log.md").read_text(encoding="utf-8")

    assert "failure isolation" in change_log
    assert "blocked outcome" in change_log
    assert "continues processing" in change_log
    assert "nonzero" in change_log


def test_sprint_thirty_six_change_log_documents_lifecycle_smoke_runner() -> None:
    change_log = Path("docs/sprints/sprint-36-change-log.md").read_text(encoding="utf-8")

    assert "run-lifecycle-smoke" in change_log
    assert "dry-run lifecycle" in change_log
    assert "writeback plan" in change_log
    assert "does not mutate ServiceNow" in change_log


def test_sprint_thirty_seven_change_log_documents_bootstrap_planning() -> None:
    change_log = Path("docs/sprints/sprint-37-change-log.md").read_text(encoding="utf-8")

    assert "plan-bootstrap-fields" in change_log
    assert "u_ai_status" in change_log
    assert "does not create state" in change_log
    assert "no form layout" in change_log


def test_sprint_thirty_eight_change_log_documents_bootstrap_apply() -> None:
    change_log = Path("docs/sprints/sprint-38-change-log.md").read_text(encoding="utf-8")

    assert "apply-bootstrap-fields" in change_log
    assert "confirm-table" in change_log
    assert "confirm-fields" in change_log
    assert "no form layout" in change_log


def test_sprint_zero_governance_documents_are_present() -> None:
    expected_paths = [
        Path("docs/adr/0001-test-first-no-hacks.md"),
        Path("docs/adr/0002-fedramp-aligned-boundary.md"),
        Path("docs/policies/local-regulated-data.md"),
    ]

    for path in expected_paths:
        assert path.exists(), f"Missing governance document: {path}"


def test_sprint_zero_change_log_documents_baseline_changes() -> None:
    change_log = Path("docs/sprints/sprint-0-change-log.md").read_text(encoding="utf-8")

    assert "Python package baseline" in change_log
    assert "90% coverage gate" in change_log
    assert "FedRAMP-aligned boundary ADR" in change_log
    assert "Local regulated data policy" in change_log


def test_sprint_plan_documents_extended_roadmap_completion() -> None:
    sprint_plan = Path("SPRINTS.md").read_text(encoding="utf-8")

    assert "Implemented Extension Sprints" in sprint_plan
    assert "Sprint 27" in sprint_plan
    assert "Controlled story writeback" in sprint_plan
    assert "Current MVP roadmap status: implemented" in sprint_plan


def test_sprint_plan_documents_delivery_lifecycle_roadmap_through_sprint_56() -> None:
    sprint_plan = Path("SPRINTS.md").read_text(encoding="utf-8")

    assert "Sprint 28" in sprint_plan
    assert "Sprint 69" in sprint_plan
    assert "LLM implementation packet" in sprint_plan
    assert "Artifact handoff" in sprint_plan
    assert "Reviewed delivery lifecycle manifest" in sprint_plan
    assert "Next Roadmap Focus" in sprint_plan
    assert "PostgreSQL operational store retarget" in sprint_plan
    assert "public API and worker runtime" in sprint_plan
    assert "SELECT ... FOR UPDATE SKIP LOCKED" in sprint_plan


def test_sprint_plan_documents_mvp_baseline_and_post_mvp_backlog() -> None:
    sprint_plan = Path("SPRINTS.md").read_text(encoding="utf-8")

    assert "MVP Baseline: Complete Through Sprint 101" in sprint_plan
    assert "Sprint 101" in sprint_plan
    assert "Read-only admin console" in sprint_plan
    assert "Post-MVP Sprint Backlog" in sprint_plan
    assert "Admin auth strategy boundary" in sprint_plan
    assert "Confidence-based context retrieval worker" in sprint_plan


def test_production_hardening_backlog_documents_review_targets() -> None:
    backlog = Path("docs/production-hardening-backlog.md").read_text(encoding="utf-8")

    assert "Sprint 101 Cut Line" in backlog
    assert "Production Hardening Backlog" in backlog
    assert "Admin auth strategy boundary" in backlog
    assert "Authenticated inbound lifecycle webhook" in backlog
    assert "Slop review" in backlog
    assert "Security review" in backlog
    assert "No new mutation surface" in backlog


def test_sprint_one_hundred_three_change_log_documents_webhook_auth() -> None:
    change_log = Path("docs/sprints/sprint-103-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 103 Change Log" in change_log
    assert "hmac_sha256" in change_log
    assert "JEDI_LIFECYCLE_WEBHOOK_SECRET" in change_log
    assert "replay-window enforcement" in change_log
    assert "development-only" in change_log


def test_sprint_one_hundred_four_change_log_documents_signed_servicenow_emitter() -> None:
    change_log = Path("docs/sprints/sprint-104-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 104 Change Log" in change_log
    assert "sha256-base64=<mac>" in change_log
    assert "--hmac-secret-property-name" in change_log
    assert "GlideCertificateEncryption.generateMac()" in change_log
    assert "Kept the secret value out" in change_log


def test_sprint_one_hundred_five_change_log_documents_hmac_cutover() -> None:
    change_log = Path("docs/sprints/sprint-105-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 105 Change Log" in change_log
    assert "x_jedi.lifecycle.webhook.secret" in change_log
    assert "JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE=hmac_sha256" in change_log
    assert "unsigned `POST /lifecycle/events` returned `401`" in change_log
    assert "signed `sha256-base64` `POST /lifecycle/events` returned `202`" in change_log
    assert "it is not recorded" in change_log


def test_operator_guide_documents_health_and_readiness_probes() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "GET /health" in guide
    assert "GET /ready" in guide
    assert "liveness probe" in guide
    assert "readiness probe" in guide
    assert "operational_store" in guide
    assert "without returning exception text" in guide


def test_operator_guide_documents_surface_investigation_before_model_calls() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "instance_context_bundle" in guide
    assert "Business Rules" in guide
    assert "Client Scripts" in guide
    assert "Flow Designer records" in guide
    assert "CMDB/discovery indicators" in guide
    assert "provider is not called" in guide
    assert "JEDI_PUBLIC_WEB_ACCESS=worker" in guide
    assert "HTTPS" in guide


def test_sprint_one_hundred_six_change_log_documents_surface_investigator() -> None:
    change_log = Path("docs/sprints/sprint-106-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 106 Change Log" in change_log
    assert "ServiceNowSurfaceContextBundle" in change_log
    assert "Business Rules" in change_log
    assert "Flow Designer records" in change_log
    assert "missing required Flow context blocks provider invocation" in change_log
    assert "does not perform live public internet calls" in change_log


def test_operator_guide_documents_surface_evidence_quality_controls() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "confidence score" in guide
    assert "source table, query, and retrieved record count" in guide
    assert "script bodies and conditions are replaced with redaction markers" in guide
    assert "endpoint query strings are redacted" in guide
    assert "work note names the missing surface context directly" in guide


def test_sprint_one_hundred_seven_change_log_documents_evidence_quality() -> None:
    change_log = Path("docs/sprints/sprint-107-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 107 Change Log" in change_log
    assert "confidence scores" in change_log
    assert "source table, query, and retrieved record count" in change_log
    assert "Redacted script-like fields" in change_log
    assert "Missing ServiceNow context: flows" in change_log


def test_operator_guide_documents_production_runtime_secret_posture() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Production Runtime Fail-Closed Checklist" in guide
    assert "validate_runtime_settings()" in guide
    assert "JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE=hmac_sha256" in guide
    assert "JEDI_LIFECYCLE_WEBHOOK_SECRET" in guide
    assert "JEDI_ADMIN_AUTH_MODE=dev_basic" in guide
    assert "rejected in production" in guide
    assert "JEDI_MODEL_PROVIDER=openai" in guide
    assert "OPENAI_API_KEY" in guide
    assert "OPENAI_MODEL" in guide
    assert "Secret Inventory" in guide
    assert "x_jedi.lifecycle.webhook.secret" in guide


def test_production_hardening_backlog_reflects_completed_sprints_through_108() -> None:
    backlog = Path("docs/production-hardening-backlog.md").read_text(encoding="utf-8")

    assert "Sprint 106 | ServiceNow surface investigation" in backlog
    assert "Sprint 107 | Surface evidence hardening" in backlog
    assert "Sprint 108 | Runtime configuration and secret posture review" in backlog
    assert "Startup/runtime checks fail closed" in backlog
    assert "Sprint 109 | Observability and audit event quality" in backlog


def test_sprint_one_hundred_eight_change_log_documents_secret_posture() -> None:
    change_log = Path("docs/sprints/sprint-108-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 108 Change Log" in change_log
    assert "validate_runtime_settings()" in change_log
    assert "hmac_sha256" in change_log
    assert "dev_basic" in change_log
    assert "JEDI_MODEL_PROVIDER=openai" in change_log
    assert "563" not in change_log


def test_operator_guide_documents_audit_correlation_shape() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Audit Correlation" in guide
    assert "correlation_id" in guide
    assert "lifecycle event -> fulfillment job -> job events -> artifact refs" in guide
    assert "admin job and lifecycle event views include the correlation id" in guide
    assert "diagnostic database URL passwords are redacted" in guide


def test_sprint_one_hundred_nine_change_log_documents_audit_correlation() -> None:
    change_log = Path("docs/sprints/sprint-109-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 109 Change Log" in change_log
    assert "correlation_id" in change_log
    assert "admin JSON endpoints" in change_log
    assert "admin console" in change_log
    assert "diagnostic database URL passwords" in change_log


def test_operator_guide_documents_rate_limit_and_payload_bounds() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Rate Limits and Payload Bounds" in guide
    assert "JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES" in guide
    assert "JEDI_ADMIN_MAX_BODY_BYTES" in guide
    assert "JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS" in guide
    assert "JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS" in guide
    assert "429" in guide
    assert "413" in guide
    assert "per-process MVP control" in guide
    assert "edge, WAF, or API gateway" in guide


def test_sprint_one_hundred_ten_change_log_documents_abuse_controls() -> None:
    change_log = Path("docs/sprints/sprint-110-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 110 Change Log" in change_log
    assert "request body size" in change_log
    assert "InMemoryRateLimiter" in change_log
    assert "429" in change_log
    assert "413" in change_log
    assert "per-process" in change_log


def test_capability_extension_adr_documents_registry_contract() -> None:
    adr = Path("docs/adr/0006-capability-extension-architecture.md").read_text(encoding="utf-8")

    assert "Capability Extension Architecture" in adr
    assert "CapabilityProfile" in adr
    assert "capability registry" in adr
    assert "required_instance_context" in adr
    assert "required context surfaces" in adr
    assert "deterministic validators" in adr
    assert "validators" in adr
    assert "unsupported cases" in adr
    assert "UAT story shape" in adr
    assert "retrieved Update Set" in adr
    assert "Retrieved Update Set preview/commit remains" in adr
    assert "Business Rule analysis first" in adr
    assert "Business Rule generation" in adr
    assert "Flow Designer remains context-only" in adr


def test_operator_guide_documents_capability_extension_model() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Capability Extension Model" in guide
    assert "Capability Extension Contract" in guide
    assert "CapabilityProfile" in guide
    assert "capability registry" in guide
    assert "required_instance_context" in guide
    assert "required context surfaces" in guide
    assert "deterministic validators" in guide
    assert "output validators" in guide
    assert "Business Rule analysis first" in guide
    assert "Business Rule generation" in guide
    assert "Flow Designer context-only review" in guide
    assert "human review" in guide


def test_production_backlog_moves_capability_implementation_to_sprint_112() -> None:
    backlog = Path("docs/production-hardening-backlog.md").read_text(encoding="utf-8")

    assert "Sprint 111 | Capability backlog design" in backlog
    assert "ADR names the extension contract" in backlog
    assert "ADR 0006" in backlog
    assert "CapabilityProfile" in backlog
    assert "Sprint 112 | Business Rule analysis capability" in backlog
    assert "context-only first implementation" in backlog
    assert "No new mutation surface" in backlog


def test_sprint_one_hundred_eleven_change_log_documents_capability_design() -> None:
    change_log = Path("docs/sprints/sprint-111-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 111 Change Log" in change_log
    assert "Capability backlog design" in change_log
    assert "ADR 0006" in change_log
    assert "CapabilityProfile" in change_log
    assert "capability registry" in change_log
    assert "Business Rule analysis first" in change_log
    assert "Business Rule generation" in change_log
    assert "Flow Designer remains context-only" in change_log
    assert "Flow Designer context-only" in change_log
    assert "No new mutation surface" in change_log
    assert "no new mutation surface" in change_log


def test_operator_guide_documents_code_surface_analysis_capability() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Code Surface Analysis Capability" in guide
    assert "business_rule_analyze" in guide
    assert "client_script_analyze" in guide
    assert "script_include_analyze" in guide
    assert "sys_script" in guide
    assert "sys_script_client" in guide
    assert "sys_script_include" in guide
    assert "code-surface-analysis-v1" in guide
    assert "does not create a retrieved Update Set" in guide
    assert "does not call the model" in guide


def test_sprint_one_hundred_twelve_change_log_documents_business_rule_analysis() -> None:
    change_log = Path("docs/sprints/sprint-112-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 112 Change Log" in change_log
    assert "Business Rule analysis capability" in change_log
    assert "business_rule_analyze" in change_log
    assert "CapabilityProfile" in change_log
    assert "sys_script" in change_log
    assert "code-surface-analysis-v1" in change_log
    assert "No new mutation surface" in change_log


def test_sprint_one_hundred_thirteen_change_log_documents_code_surface_analysis() -> None:
    change_log = Path("docs/sprints/sprint-113-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 113 Change Log" in change_log
    assert "Code surface analysis capability" in change_log
    assert "client_script_analyze" in change_log
    assert "script_include_analyze" in change_log
    assert "code-surface-analysis-v1" in change_log
    assert "No new mutation surface" in change_log


def test_business_rule_generation_profile_adr_documents_mutation_boundary() -> None:
    adr = Path("docs/adr/0007-business-rule-generation-profile.md").read_text(encoding="utf-8")

    assert "ADR 0007: Business Rule Generation Profile" in adr
    assert "business_rule_generate" in adr
    assert "table-local" in adr
    assert "before/after" in adr
    assert "insert/update" in adr
    assert "explicit condition" in adr
    assert "sys_script" in adr
    assert "sys_update_xml" in adr
    assert "Retrieved Update Set preview/commit remains" in adr
    assert "forbidden cases" in adr
    assert "deterministic validators" in adr
    assert "UAT story shape" in adr
    assert "No runtime generation is enabled" in adr


def test_operator_guide_documents_business_rule_generation_profile_boundary() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Business Rule Generation Capability" in guide
    assert "business_rule_generate" in guide
    assert "sys_script" in guide
    assert "sys_update_xml" in guide
    assert "table-local" in guide
    assert "no outbound REST" in guide
    assert "no cross-table writes" in guide
    assert "current_max_story_points=3" in guide


def test_sprint_one_hundred_fourteen_change_log_documents_generation_profile_design() -> None:
    change_log = Path("docs/sprints/sprint-114-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 114 Change Log" in change_log
    assert "Business Rule generation profile design" in change_log
    assert "ADR 0007" in change_log
    assert "business_rule_generate" in change_log
    assert "deterministic validators" in change_log
    assert "No runtime generation is enabled" in change_log


def test_production_backlog_moves_business_rule_generation_after_foundation() -> None:
    backlog = Path("docs/production-hardening-backlog.md").read_text(encoding="utf-8")

    assert "Sprint 114 | Business Rule generation profile design" in backlog
    assert "ADR 0007" in backlog
    assert "Sprint 115 | Generation foundation and maturity model" in backlog
    assert "Sprint 116 | Business Rule generation implementation" in backlog
    assert "business_rule_generate" in backlog
    assert "No runtime generation is enabled" in backlog


def test_operator_guide_documents_capability_maturity_target() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Capability Maturity Model" in guide
    assert "current_max_story_points" in guide
    assert "target_max_story_points" in guide
    assert "5 story points" in guide
    assert "researcher" in guide
    assert "build_pipeline" in guide


def test_sprint_one_hundred_fifteen_change_log_documents_generation_foundation() -> None:
    change_log = Path("docs/sprints/sprint-115-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 115 Change Log" in change_log
    assert "generation foundation" in change_log
    assert "current_max_story_points" in change_log
    assert "target_max_story_points" in change_log
    assert "business_rule_generate" in change_log
    assert "client_script_generate" in change_log
    assert "script_include_generate" in change_log
    assert "5 story points" in change_log


def test_production_backlog_documents_maturity_foundation_before_surface_generation() -> None:
    backlog = Path("docs/production-hardening-backlog.md").read_text(encoding="utf-8")

    assert "Sprint 115 | Generation foundation and maturity model" in backlog
    assert "current_max_story_points" in backlog
    assert "target_max_story_points" in backlog
    assert "Sprint 116 | Business Rule generation implementation" in backlog


def test_operator_guide_documents_enabled_business_rule_generation_boundary() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Business Rule Generation Capability" in guide
    assert "business_rule_generate" in guide
    assert "current_max_story_points=3" in guide
    assert "target_max_story_points=5" in guide
    assert "Retrieved Update Set preview/commit remains" in guide
    assert "GlideRecord" in guide
    assert "forbidden" in guide


def test_sprint_one_hundred_sixteen_change_log_documents_business_rule_generation() -> None:
    change_log = Path("docs/sprints/sprint-116-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 116 Change Log" in change_log
    assert "Business Rule generation implementation" in change_log
    assert "business_rule_generate" in change_log
    assert "sys_script" in change_log
    assert "current_max_story_points=3" in change_log
    assert "target_max_story_points=5" in change_log
    assert "retrieved Update Set" in change_log
    assert "forbidden Business Rule script" in change_log


def test_client_script_generation_profile_adr_documents_mutation_boundary() -> None:
    adr = Path("docs/adr/0008-client-script-generation-profile.md").read_text(encoding="utf-8")

    assert "ADR 0008: Client Script Generation Profile" in adr
    assert "client_script_generate" in adr
    assert "sys_script_client" in adr
    assert "g_form" in adr
    assert "onLoad" in adr
    assert "onChange" in adr
    assert "onSubmit" in adr
    assert "No runtime generation is enabled" in adr
    assert "forbidden cases" in adr
    assert "deterministic validators" in adr
    assert "UAT story shape" in adr


def test_operator_guide_documents_client_script_generation_profile_design() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Client Script Generation Capability" in guide
    assert "client_script_generate" in guide
    assert "sys_script_client" in guide
    assert "g_form" in guide
    assert "Client Script Generation Profile Design" in guide
    assert "DOM manipulation outside g_form APIs" in guide
    assert "GlideAjax dependency creation" in guide


def test_sprint_one_hundred_seventeen_change_log_documents_client_script_design() -> None:
    change_log = Path("docs/sprints/sprint-117-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 117 Change Log" in change_log
    assert "Client Script generation profile design" in change_log
    assert "ADR 0008" in change_log
    assert "client_script_generate" in change_log
    assert "sys_script_client" in change_log
    assert "No runtime generation is enabled" in change_log


def test_production_backlog_moves_client_script_generation_after_design() -> None:
    backlog = Path("docs/production-hardening-backlog.md").read_text(encoding="utf-8")

    assert "Sprint 117 | Client Script generation profile design" in backlog
    assert "Sprint 118 | Client Script generation implementation" in backlog
    assert "ADR 0008" in backlog
    assert "client_script_generate" in backlog


def test_operator_guide_documents_enabled_client_script_generation_boundary() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Client Script Generation Capability" in guide
    assert "client_script_generate" in guide
    assert "current_max_story_points=3" in guide
    assert "target_max_story_points=5" in guide
    assert "Retrieved Update Set preview/commit remains" in guide
    assert "forbidden Client Script" in guide


def test_sprint_one_hundred_eighteen_change_log_documents_client_script_generation() -> None:
    change_log = Path("docs/sprints/sprint-118-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 118 Change Log" in change_log
    assert "Client Script generation implementation" in change_log
    assert "client_script_generate" in change_log
    assert "sys_script_client" in change_log
    assert "current_max_story_points=3" in change_log
    assert "target_max_story_points=5" in change_log
    assert "retrieved Update Set" in change_log
    assert "forbidden Client Script" in change_log


def test_script_include_generation_profile_adr_documents_mutation_boundary() -> None:
    adr = Path("docs/adr/0009-script-include-generation-profile.md").read_text(encoding="utf-8")

    assert "ADR 0009: Script Include Generation Profile" in adr
    assert "script_include_generate" in adr
    assert "sys_script_include" in adr
    assert "server-side utility" in adr
    assert "No runtime generation is enabled" in adr
    assert "forbidden cases" in adr
    assert "deterministic validators" in adr
    assert "UAT story shape" in adr


def test_operator_guide_documents_script_include_generation_profile_design() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Script Include Generation Capability" in guide
    assert "script_include_generate" in guide
    assert "sys_script_include" in guide
    assert "Script Include Generation Profile Design" in guide
    assert "global privilege escalation" in guide
    assert "cross-scope access changes" in guide


def test_sprint_one_hundred_nineteen_change_log_documents_script_include_design() -> None:
    change_log = Path("docs/sprints/sprint-119-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 119 Change Log" in change_log
    assert "Script Include generation profile design" in change_log
    assert "ADR 0009" in change_log
    assert "script_include_generate" in change_log
    assert "sys_script_include" in change_log
    assert "No runtime generation is enabled" in change_log


def test_production_backlog_moves_script_include_generation_after_design() -> None:
    backlog = Path("docs/production-hardening-backlog.md").read_text(encoding="utf-8")

    assert "Sprint 119 | Script Include generation profile design" in backlog
    assert "Sprint 120 | Script Include generation implementation" in backlog
    assert "ADR 0009" in backlog
    assert "script_include_generate" in backlog


def test_operator_guide_documents_enabled_script_include_generation_boundary() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Script Include Generation Capability" in guide
    assert "script_include_generate" in guide
    assert "current_max_story_points=3" in guide
    assert "target_max_story_points=5" in guide
    assert "client callable Script Includes are not supported" in guide
    assert "forbidden Script Include" in guide


def test_sprint_one_hundred_twenty_change_log_documents_script_include_generation() -> None:
    change_log = Path("docs/sprints/sprint-120-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 120 Change Log" in change_log
    assert "Script Include generation implementation" in change_log
    assert "script_include_generate" in change_log
    assert "sys_script_include" in change_log
    assert "current_max_story_points=3" in change_log
    assert "target_max_story_points=5" in change_log
    assert "retrieved Update Set" in change_log
    assert "forbidden Script Include" in change_log


def test_sprint_121_change_log_documents_generation_validator_hardening() -> None:
    change_log = Path("docs/sprints/sprint-121-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 121 Change Log" in change_log
    assert "generation validator hardening" in change_log
    assert "current.setValue" in change_log
    assert "g_form.clearValue" in change_log
    assert "global-only Script Include" in change_log


def test_ui_policy_generation_profile_adr_documents_mutation_boundary() -> None:
    adr = Path("docs/adr/0010-ui-policy-generation-profile.md").read_text(encoding="utf-8")

    assert "ADR 0010: UI Policy Generation Profile" in adr
    assert "ui_policy_generate" in adr
    assert "sys_ui_policy" in adr
    assert "sys_ui_policy_action" in adr
    assert "No runtime generation is enabled" in adr
    assert "forbidden cases" in adr
    assert "deterministic validators" in adr
    assert "UAT story shape" in adr


def test_operator_guide_documents_ui_policy_generation_profile_design() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "UI Policy Generation Capability" in guide
    assert "ui_policy_generate" in guide
    assert "sys_ui_policy" in guide
    assert "sys_ui_policy_action" in guide
    assert "UI Policy Generation Profile Design" in guide
    assert "current_max_story_points=3" in guide
    assert "target_max_story_points=5" in guide
    assert "run scripts" in guide


def test_sprint_122_change_log_documents_ui_policy_generation_design() -> None:
    change_log = Path("docs/sprints/sprint-122-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 122 Change Log" in change_log
    assert "UI Policy generation profile design" in change_log
    assert "ADR 0010" in change_log
    assert "ui_policy_generate" in change_log
    assert "sys_ui_policy_action" in change_log
    assert "No runtime generation is enabled" in change_log


def test_production_backlog_moves_ui_policy_generation_after_validator_hardening() -> None:
    backlog = Path("docs/production-hardening-backlog.md").read_text(encoding="utf-8")

    assert "Sprint 121 | Generation validator hardening" in backlog
    assert "Sprint 122 | UI Policy generation profile design" in backlog
    assert "Sprint 123 | UI Policy generation implementation" in backlog
    assert "ADR 0010" in backlog
    assert "ui_policy_generate" in backlog


def test_sprint_123_change_log_documents_ui_policy_generation_implementation() -> None:
    change_log = Path("docs/sprints/sprint-123-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 123 Change Log" in change_log
    assert "UI Policy generation implementation" in change_log
    assert "ui_policy_generate" in change_log
    assert "sys_ui_policy" in change_log
    assert "sys_ui_policy_action" in change_log
    assert "current_max_story_points=3" in change_log
    assert "target_max_story_points=5" in change_log
    assert "retrieved Update Set" in change_log
    assert "forbidden UI Policy" in change_log


def test_flow_designer_generation_profile_adr_documents_graph_boundary() -> None:
    adr = Path("docs/adr/0011-flow-designer-generation-profile.md").read_text(encoding="utf-8")

    assert "ADR 0011: Flow Designer Generation Profile" in adr
    assert "flow_modify" in adr
    assert "sys_hub_flow" in adr
    assert "sys_hub_trigger_instance" in adr
    assert "sys_hub_action_instance" in adr
    assert "No runtime generation is enabled" in adr
    assert "flow graph" in adr
    assert "deterministic validators" in adr
    assert "UAT story shape" in adr


def test_operator_guide_documents_flow_designer_generation_profile_design() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Flow Designer Generation Capability" in guide
    assert "flow_modify" in guide
    assert "sys_hub_flow" in guide
    assert "flow graph" in guide
    assert "current_max_story_points=0" in guide
    assert "target_max_story_points=5" in guide
    assert "No runtime generation is enabled" in guide


def test_sprint_124_change_log_documents_flow_designer_generation_design() -> None:
    change_log = Path("docs/sprints/sprint-124-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 124 Change Log" in change_log
    assert "Flow Designer generation profile design" in change_log
    assert "ADR 0011" in change_log
    assert "flow_modify" in change_log
    assert "sys_hub_flow" in change_log
    assert "No runtime generation is enabled" in change_log


def test_flow_designer_docs_document_read_only_flow_graph_retrieval() -> None:
    adr = Path("docs/adr/0011-flow-designer-generation-profile.md").read_text(encoding="utf-8")
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    for text in [adr, guide]:
        assert "flow_graph" in text
        assert "sys_hub_trigger_input" in text
        assert "sys_hub_trigger_output" in text
        assert "sys_hub_action_input" in text
        assert "sys_hub_action_output" in text
        assert "read-only" in text
        assert "fails closed" in text
        assert "No runtime generation is enabled" in text


def test_sprint_125_change_log_documents_flow_graph_retrieval_hardening() -> None:
    change_log = Path("docs/sprints/sprint-125-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 125 Change Log" in change_log
    assert "Flow graph retrieval hardening" in change_log
    assert "flow_graph" in change_log
    assert "sys_hub_trigger_instance" in change_log
    assert "sys_hub_action_instance" in change_log
    assert "sys_hub_flow_logic_instance_v2" in change_log
    assert "sys_hub_action_input" in change_log
    assert "No runtime generation is enabled" in change_log


def test_sprint_1006_documents_flow_graph_discovery_record_collection_guard() -> None:
    change_log = Path("docs/sprints/sprint-1006-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Flow graph discovery record collection guard" in change_log
    assert "`resolve_fulfillment_flow()`" in change_log
    assert "`_flow_surfaces()`" in change_log
    assert "`_fetch_flow_graph_records()`" in change_log
    assert "discovery text metadata contains non-JSON value" in change_log
    assert "1 failing-first Flow graph record collection subclass assertion" in change_log
    assert "Flow graph discovery record collections are exact containers" in operator_guide
    assert "`sys_hub_trigger_instance`" in operator_guide
    assert "before fulfillment-flow matching, graph completeness checks" in operator_guide
    assert (
        "`test_required_flow_graph_context_rejects_record_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_required_flow_graph_context_rejects_record_subclass_without_leak`"
        in change_log
    )


def test_flow_designer_docs_document_graph_diff_validation_only() -> None:
    adr = Path("docs/adr/0011-flow-designer-generation-profile.md").read_text(encoding="utf-8")
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    for text in [adr, guide]:
        assert "sys_hub_flow_graph_diff" in text
        assert "add_action" in text
        assert "update_condition" in text
        assert "validation-only" in text
        assert "raw XML" in text
        assert "unretrieved node" in text
        assert "No runtime generation is enabled" in text


def test_sprint_126_change_log_documents_flow_graph_diff_contract() -> None:
    change_log = Path("docs/sprints/sprint-126-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 126 Change Log" in change_log
    assert "Flow graph diff contract" in change_log
    assert "sys_hub_flow_graph_diff" in change_log
    assert "add_action" in change_log
    assert "update_condition" in change_log
    assert "validation-only" in change_log
    assert "retrieved Update Set handoff" in change_log


def test_flow_designer_docs_document_builder_preflight_design_only() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")
    adr = Path("docs/adr/0011-flow-designer-generation-profile.md").read_text(encoding="utf-8")

    for text in [guide, adr]:
        assert "Flow Designer builder preflight" in text
        assert "retrieved_graph_hash_matches_existing_graph_hash" in text
        assert "xml_shape_repository_available" in text
        assert "Flow Designer builder is design-only" in text
        assert "runtime generation remains disabled" in text


def test_sprint_127_change_log_documents_flow_builder_design() -> None:
    change_log = Path("docs/sprints/sprint-127-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 127 Change Log" in change_log
    assert "Flow builder preflight design" in change_log
    assert "runtime generation remains disabled" in change_log
    assert "retrieved_graph_hash_matches_existing_graph_hash" in change_log
    assert "xml_shape_repository_available" in change_log
    assert "retrieved Update Set handoff remains disabled" in change_log


def test_flow_designer_docs_document_xml_shape_repository() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")
    adr = Path("docs/adr/0011-flow-designer-generation-profile.md").read_text(encoding="utf-8")

    for text in [guide, adr]:
        assert "flow-xml-shapes-v1" in text
        assert "Flow XML shape repository" in text
        assert "sys_hub_action_instance" in text
        assert "sys_hub_flow_logic_instance_v2" in text
        assert "review metadata only" in text
        assert "no Flow XML builder" in text


def test_sprint_128_change_log_documents_flow_xml_shape_repository() -> None:
    change_log = Path("docs/sprints/sprint-128-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 128 Change Log" in change_log
    assert "Flow XML shape repository" in change_log
    assert "flow-xml-shapes-v1" in change_log
    assert "sys_hub_flow" in change_log
    assert "sys_hub_action_instance" in change_log
    assert "sys_hub_flow_logic_instance_v2" in change_log
    assert "no Flow XML builder" in change_log


def test_flow_designer_docs_document_xml_shape_evidence_validation() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")
    adr = Path("docs/adr/0011-flow-designer-generation-profile.md").read_text(encoding="utf-8")

    for text in [guide, adr]:
        assert "Flow XML shape evidence validator" in text
        assert "validate_flow_xml_shape_evidence" in text
        assert "xml_shape_evidence_validator_available" in text
        assert "review samples" in text
        assert "still no Flow XML builder" in text


def test_sprint_129_change_log_documents_flow_xml_shape_evidence_validation() -> None:
    change_log = Path("docs/sprints/sprint-129-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 129 Change Log" in change_log
    assert "Flow XML shape evidence validator" in change_log
    assert "validate_flow_xml_shape_evidence" in change_log
    assert "missing required field" in change_log
    assert "forbidden field" in change_log
    assert "no Flow XML builder" in change_log


def test_flow_designer_docs_document_customer_update_strategy() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")
    adr = Path("docs/adr/0011-flow-designer-generation-profile.md").read_text(encoding="utf-8")

    for text in [guide, adr]:
        assert "flow-customer-update-strategy-v1" in text
        assert "Flow customer update strategy" in text
        assert "table_sys_id" in text
        assert "rollback strategy" in text
        assert "still no Flow XML builder" in text


def test_sprint_130_change_log_documents_flow_customer_update_strategy() -> None:
    change_log = Path("docs/sprints/sprint-130-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 130 Change Log" in change_log
    assert "Flow customer update strategy" in change_log
    assert "flow-customer-update-strategy-v1" in change_log
    assert "table_sys_id" in change_log
    assert "rollback_customer_update_strategy_defined" in change_log
    assert "no Flow XML builder" in change_log


def test_flow_designer_docs_document_snapshot_update_strategy() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")
    adr = Path("docs/adr/0011-flow-designer-generation-profile.md").read_text(encoding="utf-8")

    for text in [guide, adr]:
        assert "flow-snapshot-update-strategy-v1" in text
        assert "Flow snapshot update strategy" in text
        assert "latest_snapshot" in text
        assert "snapshot table mutation is not supported" in text
        assert "still no Flow XML builder" in text


def test_sprint_131_change_log_documents_flow_snapshot_update_strategy() -> None:
    change_log = Path("docs/sprints/sprint-131-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 131 Change Log" in change_log
    assert "Flow snapshot update strategy" in change_log
    assert "flow-snapshot-update-strategy-v1" in change_log
    assert "latest_snapshot" in change_log
    assert "snapshot table mutation is not supported" in change_log
    assert "no Flow XML builder" in change_log


def test_flow_designer_docs_document_preview_commit_review_strategy() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")
    adr = Path("docs/adr/0011-flow-designer-generation-profile.md").read_text(encoding="utf-8")

    for text in [guide, adr]:
        assert "flow-preview-commit-review-strategy-v1" in text
        assert "Flow preview/commit review strategy" in text
        assert "retrieved_update_set_preview_commit" in text
        assert "auto-commit is not supported" in text
        assert "still no Flow XML builder" in text


def test_sprint_132_change_log_documents_flow_preview_commit_review_strategy() -> None:
    change_log = Path("docs/sprints/sprint-132-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 132 Change Log" in change_log
    assert "Flow preview/commit review strategy" in change_log
    assert "flow-preview-commit-review-strategy-v1" in change_log
    assert "retrieved_update_set_preview_commit" in change_log
    assert "auto-commit is not supported" in change_log
    assert "no Flow XML builder" in change_log


def test_flow_designer_docs_document_builder_readiness_contract() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")
    adr = Path("docs/adr/0011-flow-designer-generation-profile.md").read_text(encoding="utf-8")

    for text in [guide, adr]:
        assert "flow-builder-readiness-v1" in text
        assert "Flow builder readiness contract" in text
        assert "missing_evidence" in text
        assert "Flow Designer builder is not implemented" in text
        assert "still no Flow XML builder" in text


def test_sprint_133_change_log_documents_flow_builder_readiness_contract() -> None:
    change_log = Path("docs/sprints/sprint-133-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 133 Change Log" in change_log
    assert "Flow builder readiness contract" in change_log
    assert "flow-builder-readiness-v1" in change_log
    assert "missing_evidence" in change_log
    assert "Flow Designer builder is not implemented" in change_log
    assert "no Flow XML builder" in change_log


def test_flow_designer_docs_document_builder_plan_readiness_wiring() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")
    adr = Path("docs/adr/0011-flow-designer-generation-profile.md").read_text(encoding="utf-8")

    for text in [guide, adr]:
        assert "Flow builder plan readiness wiring" in text
        assert "readiness_contract_version" in text
        assert "missing_builder_evidence" in text
        assert "ready_for_runtime_generation=false" in text
        assert "still no Flow XML builder" in text


def test_sprint_134_change_log_documents_flow_builder_plan_readiness_wiring() -> None:
    change_log = Path("docs/sprints/sprint-134-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 134 Change Log" in change_log
    assert "Flow builder plan readiness wiring" in change_log
    assert "readiness_contract_version" in change_log
    assert "missing_builder_evidence" in change_log
    assert "ready_for_runtime_generation=false" in change_log
    assert "no Flow XML builder" in change_log


def test_flow_designer_docs_document_unsupported_reason_codes() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")
    adr = Path("docs/adr/0011-flow-designer-generation-profile.md").read_text(encoding="utf-8")

    for text in [guide, adr]:
        assert "Flow unsupported reason codes" in text
        assert "unsupported_reason_codes" in text
        assert "flow_builder_not_implemented" in text
        assert "runtime_generation_disabled" in text
        assert "retrieved_update_set_handoff_disabled" in text


def test_sprint_135_change_log_documents_flow_unsupported_reason_codes() -> None:
    change_log = Path("docs/sprints/sprint-135-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 135 Change Log" in change_log
    assert "Flow unsupported reason codes" in change_log
    assert "unsupported_reason_codes" in change_log
    assert "flow_builder_not_implemented" in change_log
    assert "no Flow XML builder" in change_log


def test_flow_designer_docs_document_unsupported_reason_guidance() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")
    adr = Path("docs/adr/0011-flow-designer-generation-profile.md").read_text(encoding="utf-8")

    for text in [guide, adr]:
        assert "Flow unsupported reason guidance" in text
        assert "unsupported_reason_guidance" in text
        assert "route_to_human_review" in text
        assert "work note" in text
        assert "still no Flow XML builder" in text


def test_sprint_136_change_log_documents_flow_unsupported_reason_guidance() -> None:
    change_log = Path("docs/sprints/sprint-136-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 136 Change Log" in change_log
    assert "Flow unsupported reason guidance" in change_log
    assert "unsupported_reason_guidance" in change_log
    assert "route_to_human_review" in change_log
    assert "no Flow XML builder" in change_log


def test_flow_designer_docs_document_preflight_guidance_artifact() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")
    adr = Path("docs/adr/0011-flow-designer-generation-profile.md").read_text(encoding="utf-8")

    for text in [guide, adr]:
        assert "Flow preflight guidance artifact" in text
        assert "flow_preflight_guidance" in text
        assert "flow-preflight-guidance-v1" in text
        assert "route_to_human_review" in text
        assert "no Flow XML builder" in text


def test_sprint_137_change_log_documents_flow_preflight_guidance_artifact() -> None:
    change_log = Path("docs/sprints/sprint-137-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 137 Change Log" in change_log
    assert "Flow preflight guidance artifact" in change_log
    assert "flow_preflight_guidance" in change_log
    assert "flow-preflight-guidance-v1" in change_log
    assert "no Flow XML builder" in change_log


def test_flow_designer_docs_document_preflight_guidance_work_note() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Flow preflight guidance work note" in guide
    assert "Flow preflight guidance artifact" in guide
    assert "Human Review Required" in guide
    assert "route_to_human_review" in guide
    assert "no retrieved Update Set" in guide


def test_sprint_138_change_log_documents_flow_preflight_guidance_work_note() -> None:
    change_log = Path("docs/sprints/sprint-138-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 138 Change Log" in change_log
    assert "Flow preflight guidance work note" in change_log
    assert "flow_preflight_guidance" in change_log
    assert "Human Review Required" in change_log
    assert "no Flow XML builder" in change_log


def test_sprint_139_change_log_documents_supported_artifact_test_hardening() -> None:
    change_log = Path("docs/sprints/sprint-139-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 139 Change Log" in change_log
    assert "supported ServiceNow artifact testing" in change_log
    assert "model payload compaction" in change_log
    assert "Script Include" in change_log
    assert "live UAT matrix" in change_log


def test_production_backlog_moves_flow_designer_after_ui_policy_generation() -> None:
    backlog = Path("docs/production-hardening-backlog.md").read_text(encoding="utf-8")

    assert "Sprint 124 | Flow Designer generation profile design" in backlog
    assert "Sprint 125 | Flow graph retrieval hardening" in backlog
    assert "Sprint 126 | Flow graph diff contract validation" in backlog
    assert "Sprint 127 | Flow builder preflight design" in backlog
    assert "Sprint 128 | Flow XML shape repository" in backlog
    assert "Sprint 129 | Flow XML shape evidence validation" in backlog
    assert "Sprint 130 | Flow customer update strategy" in backlog
    assert "Sprint 131 | Flow snapshot update strategy" in backlog
    assert "Sprint 132 | Flow preview/commit review strategy" in backlog
    assert "Sprint 133 | Flow builder readiness contract" in backlog
    assert "Sprint 134 | Flow builder plan readiness wiring" in backlog
    assert "Sprint 135 | Flow unsupported reason codes" in backlog
    assert "Sprint 136 | Flow unsupported reason guidance" in backlog
    assert "Sprint 137 | Flow preflight guidance artifact" in backlog
    assert "Sprint 138 | Flow preflight guidance work note" in backlog
    assert "Sprint 139 | Supported artifact UAT hardening" in backlog
    assert "ADR 0011" in backlog
    assert "flow_modify" in backlog


def test_admin_auth_config_documents_oidc_and_servicenow_oauth() -> None:
    config = Path("docs/admin-auth-config.md").read_text(encoding="utf-8")

    assert "JEDI_ADMIN_AUTH_MODE" in config
    assert "dev_basic" in config
    assert "oidc" in config
    assert "servicenow_oauth" in config
    assert "OIDC Configuration" in config
    assert "ServiceNow OAuth Configuration" in config
    assert "authorization code grant" in config
    assert "SSO" in config
    assert "Do not rely on a ServiceNow browser session cookie" in config


def test_admin_auth_strategy_adr_documents_sso_decision() -> None:
    adr = Path("docs/adr/0005-admin-auth-strategy.md").read_text(encoding="utf-8")

    assert "ServiceNow role-backed browser authentication" in adr
    assert "SSO" in adr
    assert "customer IdP OIDC" in adr
    assert "ServiceNow OAuth authorization code" in adr
    assert "dev_basic" in adr


def test_sprint_one_change_log_documents_schema_work() -> None:
    change_log = Path("docs/sprints/sprint-1-change-log.md").read_text(encoding="utf-8")

    assert "Core Pydantic schemas" in change_log
    assert "Provider policy registry contract" in change_log
    assert "Update Set candidate status transitions" in change_log
    assert "Stable artifact hashing" in change_log


def test_sprint_two_change_log_documents_safety_gates() -> None:
    change_log = Path("docs/sprints/sprint-2-change-log.md").read_text(encoding="utf-8")

    assert "Rules-first story classification" in change_log
    assert "Safety gate engine" in change_log
    assert "Operation allowlist enforcement" in change_log
    assert "Fail-closed rejection patterns" in change_log


def test_sprint_three_change_log_documents_rag_boundaries() -> None:
    change_log = Path("docs/sprints/sprint-3-change-log.md").read_text(encoding="utf-8")

    assert "Specialized RAG boundaries" in change_log
    assert "Local deterministic retrieval" in change_log
    assert "Compliance context blocking" in change_log
    assert "Cross-domain isolation" in change_log


def test_sprint_four_change_log_documents_template_generation() -> None:
    change_log = Path("docs/sprints/sprint-4-change-log.md").read_text(encoding="utf-8")

    assert "Template-only candidate generation" in change_log
    assert "Write-once artifact writer" in change_log
    assert "Manual-build routing" in change_log
    assert "Stable candidate artifact hash" in change_log


def test_sprint_five_change_log_documents_provider_gate() -> None:
    change_log = Path("docs/sprints/sprint-5-change-log.md").read_text(encoding="utf-8")

    assert "Provider adapter contract" in change_log
    assert "Policy enforcement before prompt construction" in change_log
    assert "Minimized story payload" in change_log
    assert "Model response validation" in change_log


def test_sprint_six_change_log_documents_planning_metrics() -> None:
    change_log = Path("docs/sprints/sprint-6-change-log.md").read_text(encoding="utf-8")

    assert "Priority scoring" in change_log
    assert "Repointing suggestions" in change_log
    assert "Run metrics" in change_log
    assert "Non-mutating story estimates" in change_log


def test_sprint_seven_change_log_documents_review_workflow() -> None:
    change_log = Path("docs/sprints/sprint-7-change-log.md").read_text(encoding="utf-8")

    assert "Review workflow" in change_log
    assert "Named reviewer approval" in change_log
    assert "Export preflight" in change_log
    assert "XML export defaults off" in change_log


def test_sprint_eight_change_log_documents_servicenow_oauth() -> None:
    change_log = Path("docs/sprints/sprint-8-change-log.md").read_text(encoding="utf-8")

    assert "OAuth client credentials" in change_log
    assert "Read-only Table API client" in change_log
    assert "No live PDI calls in default tests" in change_log
    assert "Secret redaction" in change_log


def test_sprint_nine_readiness_documents_are_present() -> None:
    expected_paths = [
        Path("docs/security/threat-model.md"),
        Path("docs/security/data-flow.md"),
        Path("docs/security/control-mapping.md"),
        Path("docs/operator-guide.md"),
        Path("docs/risk-register.md"),
        Path("docs/sprints/sprint-9-change-log.md"),
    ]

    for path in expected_paths:
        assert path.exists(), f"Missing Sprint 9 document: {path}"


def test_sprint_nine_change_log_documents_hardening() -> None:
    change_log = Path("docs/sprints/sprint-9-change-log.md").read_text(encoding="utf-8")

    assert "Threat model" in change_log
    assert "Data flow" in change_log
    assert "Security control mapping" in change_log
    assert "No public model provider enabled by default" in change_log


def test_sprint_ten_change_log_documents_pipeline_slice() -> None:
    change_log = Path("docs/sprints/sprint-10-change-log.md").read_text(encoding="utf-8")

    assert "End-to-end local pipeline" in change_log
    assert "run-local CLI" in change_log
    assert "Safe summary output" in change_log
    assert "Missing affected tables route to manual review" in change_log


def test_sprint_eleven_change_log_documents_live_pdi_mode() -> None:
    change_log = Path("docs/sprints/sprint-11-change-log.md").read_text(encoding="utf-8")

    assert "Live PDI pipeline mode" in change_log
    assert "Configurable sysparm query" in change_log
    assert "Module entrypoint" in change_log
    assert "manual review" in change_log


def test_example_story_change_log_documents_fixture() -> None:
    change_log = Path("docs/sprints/example-story-change-log.md").read_text(encoding="utf-8")

    assert "Synthetic content-only story" in change_log
    assert "acceptance criteria" in change_log
    assert "affected table metadata" in change_log
    assert "generated candidate artifact" in change_log


def test_sprint_twelve_change_log_documents_enrichment() -> None:
    change_log = Path("docs/sprints/sprint-12-change-log.md").read_text(encoding="utf-8")

    assert "Context enrichment" in change_log
    assert "affected table inference" in change_log
    assert "evidence" in change_log
    assert "enrichment_manual_review" in change_log


def test_sprint_thirteen_change_log_documents_dictionary_form_candidate() -> None:
    change_log = Path("docs/sprints/sprint-13-change-log.md").read_text(encoding="utf-8")

    assert "dictionary/form candidate" in change_log
    assert "sys_dictionary" in change_log
    assert "sys_ui_form" in change_log
    assert "STRY0010013" in change_log


def test_risk_model_architecture_decision_is_documented() -> None:
    adr = Path("docs/adr/0003-risk-model-architecture.md").read_text(encoding="utf-8")

    assert "Deterministic risk rubric first" in adr
    assert "specialized risk model" in adr
    assert "deferred" in adr
    assert "reviewer outcome data" in adr


def test_spm_sidecar_architecture_decision_is_documented() -> None:
    adr = Path("docs/adr/0004-spm-sidecar-work-surface.md").read_text(encoding="utf-8")

    assert "ServiceNow remains the canonical work surface" in adr
    assert "Demand Management" in adr
    assert "Agile Development 2.0" in adr
    assert "Ready for Testing" in adr
    assert "external build pipeline" in adr


def test_sprint_fourteen_change_log_documents_spm_workflow_alignment() -> None:
    change_log = Path("docs/sprints/sprint-14-change-log.md").read_text(encoding="utf-8")

    assert "SPM/PPM workflow research" in change_log
    assert "ServiceNow work surface" in change_log
    assert "structured writeback" in change_log
    assert "Ready for Testing" in change_log


def test_sprint_fifteen_change_log_documents_writeback_boundary() -> None:
    change_log = Path("docs/sprints/sprint-15-change-log.md").read_text(encoding="utf-8")

    assert "writeback planner" in change_log
    assert "external build result" in change_log
    assert "Ready for Testing" in change_log
    assert "PATCH primitive" in change_log
    assert "policy-gated" in change_log


def test_sprint_sixteen_change_log_documents_state_discovery() -> None:
    change_log = Path("docs/sprints/sprint-16-change-log.md").read_text(encoding="utf-8")

    assert "sys_choice" in change_log
    assert "Ready for Testing" in change_log
    assert "instance state mapping" in change_log
    assert "fails closed" in change_log


def test_sprint_seventeen_change_log_documents_dry_run_writeback_cli() -> None:
    change_log = Path("docs/sprints/sprint-17-change-log.md").read_text(encoding="utf-8")

    assert "plan-writeback" in change_log
    assert "dry-run" in change_log
    assert "no ServiceNow mutation" in change_log
    assert "Ready for Testing" in change_log


def test_sprint_eighteen_change_log_documents_writeback_field_discovery() -> None:
    change_log = Path("docs/sprints/sprint-18-change-log.md").read_text(encoding="utf-8")

    assert "sys_dictionary" in change_log
    assert "structured writeback fields" in change_log
    assert "fails closed" in change_log
    assert "plan-writeback" in change_log


def test_sprint_nineteen_change_log_documents_confirmed_apply_gate() -> None:
    change_log = Path("docs/sprints/sprint-19-change-log.md").read_text(encoding="utf-8")

    assert "confirmed apply" in change_log
    assert "--apply" in change_log
    assert "--confirm-story-number" in change_log
    assert "dry-run default" in change_log


def test_sprint_twenty_change_log_documents_writeback_audit_artifact() -> None:
    change_log = Path("docs/sprints/sprint-20-change-log.md").read_text(encoding="utf-8")

    assert "writeback audit artifact" in change_log
    assert "--actor-id" in change_log
    assert "service principal" in change_log
    assert "--audit-root" in change_log
    assert "write-once" in change_log


def test_sprint_twenty_one_change_log_documents_writeback_orchestration_boundary() -> None:
    change_log = Path("docs/sprints/sprint-21-change-log.md").read_text(encoding="utf-8")

    assert "execute_writeback" in change_log
    assert "service actor" in change_log
    assert "CLI adapter" in change_log
    assert "orchestration boundary" in change_log


def test_sprint_twenty_two_change_log_documents_writeback_idempotency() -> None:
    change_log = Path("docs/sprints/sprint-22-change-log.md").read_text(encoding="utf-8")

    assert "idempotency" in change_log
    assert "writeback audit artifact" in change_log
    assert "retry" in change_log
    assert "no-op" in change_log
    assert "remote writeback" in change_log


def test_sprint_twenty_three_change_log_documents_writeback_capability_preflight() -> None:
    change_log = Path("docs/sprints/sprint-23-change-log.md").read_text(encoding="utf-8")

    assert "writeback capability preflight" in change_log
    assert "check-writeback-capability" in change_log
    assert "Ready for Testing" in change_log
    assert "required structured fields" in change_log


def test_sprint_twenty_four_change_log_documents_batch_writeback_orchestration() -> None:
    change_log = Path("docs/sprints/sprint-24-change-log.md").read_text(encoding="utf-8")

    assert "batch writeback orchestration" in change_log
    assert "capability preflight once" in change_log
    assert "fail closed" in change_log
    assert "summary" in change_log


def test_sprint_twenty_five_change_log_documents_writeback_job_file_ingestion() -> None:
    change_log = Path("docs/sprints/sprint-25-change-log.md").read_text(encoding="utf-8")

    assert "writeback job file" in change_log
    assert "run-writeback-batch" in change_log
    assert "typed job records" in change_log
    assert "empty job file" in change_log


def test_sprint_twenty_six_change_log_documents_batch_report_artifact() -> None:
    change_log = Path("docs/sprints/sprint-26-change-log.md").read_text(encoding="utf-8")

    assert "batch report artifact" in change_log
    assert "no ServiceNow sys_ids" in change_log
    assert "write-once" in change_log
    assert "run-writeback-batch" in change_log


def test_sprint_twenty_seven_change_log_documents_manifest_alignment() -> None:
    change_log = Path("docs/sprints/sprint-27-change-log.md").read_text(encoding="utf-8")

    assert "manifest alignment" in change_log
    assert "Controlled ServiceNow story writeback" in change_log
    assert "Direct Update Set imports" in change_log
    assert "execute_writeback" in change_log


def test_sprint_twenty_eight_change_log_documents_implementation_packet() -> None:
    change_log = Path("docs/sprints/sprint-28-change-log.md").read_text(encoding="utf-8")

    assert "LLM implementation packet" in change_log
    assert "Now Assist" in change_log
    assert "deterministic gates" in change_log
    assert "generate_implementation_candidate" in change_log


def test_sprint_thirty_nine_change_log_documents_live_writeback_verification() -> None:
    change_log = Path("docs/sprints/sprint-39-change-log.md").read_text(encoding="utf-8")

    assert "verify-writeback" in change_log
    assert "STRY0010013" in change_log
    assert "remote_writeback_already_applied" in change_log
    assert "build-writeback-apply-20260513-001" in change_log


def test_sprint_forty_change_log_documents_lifecycle_manifest() -> None:
    change_log = Path("docs/sprints/sprint-40-change-log.md").read_text(encoding="utf-8")

    assert "lifecycle manifest" in change_log
    assert "record-lifecycle-manifest" in change_log
    assert "implementation_packet" in change_log
    assert "implementation_candidate" in change_log
    assert "writeback" in change_log


def test_sprint_forty_one_change_log_documents_apply_manifest() -> None:
    change_log = Path("docs/sprints/sprint-41-change-log.md").read_text(encoding="utf-8")

    assert "plan-writeback --apply" in change_log
    assert "--manifest-root" in change_log
    assert "verify_writeback" in change_log
    assert "writeback_audit" in change_log


def test_sprint_forty_two_change_log_documents_artifact_handoff_contract() -> None:
    change_log = Path("docs/sprints/sprint-42-change-log.md").read_text(encoding="utf-8")

    assert "artifact handoff" in change_log
    assert "Approved Update Set XML" in change_log
    assert "Test Evidence Bundle" in change_log
    assert "internal audit evidence" in change_log


def test_sprint_forty_three_change_log_documents_handoff_report() -> None:
    change_log = Path("docs/sprints/sprint-43-change-log.md").read_text(encoding="utf-8")

    assert "plan-artifact-handoff" in change_log
    assert "handoff report" in change_log
    assert "attach_to_servicenow" in change_log
    assert "delivery_evidence" in change_log


def test_sprint_forty_four_change_log_documents_handoff_hashing() -> None:
    change_log = Path("docs/sprints/sprint-44-change-log.md").read_text(encoding="utf-8")

    assert "SHA-256" in change_log
    assert "missing" in change_log
    assert "fail closed" in change_log
    assert "handoff report" in change_log


def test_sprint_forty_five_change_log_documents_handoff_summary_writeback() -> None:
    change_log = Path("docs/sprints/sprint-45-change-log.md").read_text(encoding="utf-8")

    assert "write-artifact-handoff-summary" in change_log
    assert "work_notes" in change_log
    assert "dry-run" in change_log
    assert "does not attach" in change_log


def test_sprint_forty_six_change_log_documents_delivery_attachment_gate() -> None:
    change_log = Path("docs/sprints/sprint-46-change-log.md").read_text(encoding="utf-8")

    assert "attach-delivery-artifacts" in change_log
    assert "Attachment API" in change_log
    assert "dry-run" in change_log
    assert "Approved Update Set XML" in change_log


def test_sprint_forty_seven_change_log_documents_delivery_smoke() -> None:
    change_log = Path("docs/sprints/sprint-47-change-log.md").read_text(encoding="utf-8")

    assert "run-delivery-artifact-smoke" in change_log
    assert "placeholder" in change_log
    assert "Update Set XML" in change_log
    assert "does not call ServiceNow" in change_log


def test_sprint_forty_eight_change_log_documents_attachment_audit() -> None:
    change_log = Path("docs/sprints/sprint-48-change-log.md").read_text(encoding="utf-8")

    assert "attach-delivery-artifacts" in change_log
    assert "attachment audit" in change_log
    assert "write-once" in change_log
    assert "attachment sys_ids" in change_log
    assert "story_sys_id" in change_log


def test_sprint_forty_nine_change_log_documents_delivery_contract_gate() -> None:
    change_log = Path("docs/sprints/sprint-49-change-log.md").read_text(encoding="utf-8")

    assert "delivery_contract" in change_log
    assert "reviewed_export" in change_log
    assert "smoke_placeholder" in change_log
    assert "approved_for_delivery" in change_log
    assert "fail closed" in change_log


def test_sprint_fifty_change_log_documents_reviewed_delivery_job_writer() -> None:
    change_log = Path("docs/sprints/sprint-50-change-log.md").read_text(encoding="utf-8")

    assert "review-delivery-artifact" in change_log
    assert "reviewer_id" in change_log
    assert "artifact_sha256" in change_log
    assert "reviewed_export" in change_log
    assert "write-once" in change_log


def test_sprint_fifty_one_change_log_documents_reviewed_delivery_smoke() -> None:
    change_log = Path("docs/sprints/sprint-51-change-log.md").read_text(encoding="utf-8")

    assert "run-reviewed-delivery-smoke" in change_log
    assert "reviewed delivery" in change_log
    assert "reviewed_export" in change_log
    assert "attach_to_servicenow=1" in change_log
    assert "does not call ServiceNow" in change_log


def test_sprint_fifty_two_change_log_documents_attachment_hash_gate() -> None:
    change_log = Path("docs/sprints/sprint-52-change-log.md").read_text(encoding="utf-8")

    assert "artifact_sha256" in change_log
    assert "attach-delivery-artifacts" in change_log
    assert "artifact_hash_mismatch" in change_log
    assert "before ServiceNow" in change_log
    assert "attachment audit" in change_log


def test_sprint_fifty_three_change_log_documents_dry_run_hash_preflight() -> None:
    change_log = Path("docs/sprints/sprint-53-change-log.md").read_text(encoding="utf-8")

    assert "dry-run" in change_log
    assert "artifact_hash_mismatch" in change_log
    assert "before apply-only validation" in change_log
    assert "does not call ServiceNow" in change_log


def test_sprint_fifty_four_change_log_documents_missing_artifact_preflight() -> None:
    change_log = Path("docs/sprints/sprint-54-change-log.md").read_text(encoding="utf-8")

    assert "artifact_missing" in change_log
    assert "dry-run" in change_log
    assert "traceback" in change_log
    assert "before ServiceNow" in change_log


def test_sprint_fifty_five_change_log_documents_update_set_xml_marker_gate() -> None:
    change_log = Path("docs/sprints/sprint-55-change-log.md").read_text(encoding="utf-8")

    assert "sys_update_xml" in change_log
    assert "review-delivery-artifact" in change_log
    assert "reviewed_export_artifact_required" in change_log
    assert "empty" in change_log


def test_sprint_fifty_six_change_log_documents_reviewed_delivery_lifecycle_manifest() -> None:
    change_log = Path("docs/sprints/sprint-56-change-log.md").read_text(encoding="utf-8")

    assert "reviewed-delivery-lifecycle-manifests" in change_log
    assert "delivery_attachment_plan" in change_log
    assert "artifact_handoff_report" in change_log
    assert "reviewed_delivery_job" in change_log
    assert "sys_id" in change_log


def test_sprint_fifty_seven_change_log_documents_roadmap_refresh() -> None:
    change_log = Path("docs/sprints/sprint-57-change-log.md").read_text(encoding="utf-8")

    assert "SPRINTS.md" in change_log
    assert "Sprint 56" in change_log
    assert "Next Roadmap Focus" in change_log
    assert "External build pipeline contract" in change_log


def test_sprint_fifty_eight_change_log_documents_external_build_contract() -> None:
    change_log = Path("docs/sprints/sprint-58-change-log.md").read_text(encoding="utf-8")

    assert "ExternalBuildPipelineResult" in change_log
    assert "writeback_job_from_build_result" in change_log
    assert "reviewed_delivery_jobs_from_build_result" in change_log
    assert "successful builds require reviewed delivery outputs" in change_log
    assert "story_sys_id" in change_log


def test_operator_guide_documents_lifecycle_event_contract() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Lifecycle Event Contract" in guide
    assert "LifecycleStateChangeEvent" in guide
    assert "story_state_changed" in guide
    assert "Draft" in guide
    assert "Ready" in guide
    assert "Work in Progress" in guide
    assert "Business Rule" in guide
    assert "Scripted REST API" in guide
    assert "story_sys_id" in guide


def test_spm_sidecar_adr_documents_event_driven_story_ready_trigger() -> None:
    adr = Path("docs/adr/0004-spm-sidecar-work-surface.md").read_text(encoding="utf-8")

    assert "Draft to Ready" in adr
    assert "lifecycle event" in adr
    assert "Work in Progress" in adr
    assert "ServiceNow remains the canonical work surface" in adr


def test_sprint_fifty_nine_change_log_documents_lifecycle_event_contract() -> None:
    change_log = Path("docs/sprints/sprint-59-change-log.md").read_text(encoding="utf-8")

    assert "LifecycleStateChangeEvent" in change_log
    assert "Draft to Ready" in change_log
    assert "Work in Progress" in change_log
    assert "Business Rule" in change_log
    assert "Scripted REST API" in change_log
    assert "no ServiceNow mutation" in change_log


def test_operator_guide_documents_lifecycle_event_processor_cli() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "process-lifecycle-event" in guide
    assert "--event-file" in guide
    assert "--plan-root" in guide
    assert "lifecycle-event-plans" in guide
    assert "write-once" in guide


def test_sprint_sixty_change_log_documents_lifecycle_event_processor() -> None:
    change_log = Path("docs/sprints/sprint-60-change-log.md").read_text(encoding="utf-8")

    assert "process-lifecycle-event" in change_log
    assert "lifecycle-event-plans" in change_log
    assert "Draft to Ready" in change_log
    assert "Work in Progress" in change_log
    assert "invalid_lifecycle_event" in change_log
    assert "no ServiceNow mutation" in change_log


def test_operator_guide_documents_build_claim_writeback_planner() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Build Claim Writeback" in guide
    assert "plan_story_build_claim_writeback" in guide
    assert "Ready" in guide
    assert "Work in Progress" in guide
    assert "Build In Progress" in guide
    assert "allowlisted" in guide


def test_sprint_sixty_one_change_log_documents_build_claim_planner() -> None:
    change_log = Path("docs/sprints/sprint-61-change-log.md").read_text(encoding="utf-8")

    assert "plan_story_build_claim_writeback" in change_log
    assert "Ready to Work in Progress" in change_log
    assert "Build In Progress" in change_log
    assert "State transitions are disabled" in change_log
    assert "not live apply" in change_log


def test_operator_guide_documents_build_claim_execution_boundary() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "execute_build_claim" in guide
    assert "BuildClaimExecutionRequest" in guide
    assert "fresh story" in guide
    assert "build claim audit" in guide
    assert "build_claim_already_recorded" in guide


def test_sprint_sixty_two_change_log_documents_build_claim_execution() -> None:
    change_log = Path("docs/sprints/sprint-62-change-log.md").read_text(encoding="utf-8")

    assert "execute_build_claim" in change_log
    assert "BuildClaimExecutionRequest" in change_log
    assert "fresh story" in change_log
    assert "build claim audit" in change_log
    assert "fresh_story_state_mismatch" in change_log
    assert "Work in Progress" in change_log


def test_operator_guide_documents_lifecycle_business_rule_bootstrap() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "plan-lifecycle-business-rule" in guide
    assert "Business Rule first" in guide
    assert "Flow" in guide
    assert "--draft-state-value" in guide
    assert "--ready-state-value" in guide
    assert "reviewable ServiceNow script artifact" in guide
    assert "does not install" in guide


def test_sprint_sixty_three_change_log_documents_business_rule_bootstrap() -> None:
    change_log = Path("docs/sprints/sprint-63-change-log.md").read_text(encoding="utf-8")

    assert "Business Rule first" in change_log
    assert "plan-lifecycle-business-rule" in change_log
    assert "rm_story" in change_log
    assert "Draft to Ready" in change_log
    assert "story_state_changed" in change_log
    assert "story_sys_id" in change_log


def test_operator_guide_documents_lifecycle_rest_message_bootstrap() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Outbound REST Message" in guide
    assert "rest_message" in guide
    assert "business_rule" in guide
    assert "Jedi DevProject Lifecycle Event API" in guide
    assert "Business Rule references the named REST Message" in guide
    assert "endpoint URL out of the Business Rule script" in guide


def test_sprint_sixty_four_change_log_documents_lifecycle_rest_message_bundle() -> None:
    change_log = Path("docs/sprints/sprint-64-change-log.md").read_text(encoding="utf-8")

    assert "Lifecycle webhook bootstrap bundle" in change_log
    assert "Outbound REST Message" in change_log
    assert "rest_message" in change_log
    assert "business_rule" in change_log
    assert "endpoint URL out of the Business Rule script" in change_log
    assert "configured_in_servicenow" in change_log


def test_operator_guide_documents_lifecycle_servicenow_record_plan() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "servicenow_records" in guide
    assert "sys_rest_message" in guide
    assert "sys_rest_message_fn" in guide
    assert "sys_script" in guide
    assert "insert_or_update" in guide
    assert "does not apply those records" in guide


def test_sprint_sixty_five_change_log_documents_lifecycle_record_plan() -> None:
    change_log = Path("docs/sprints/sprint-65-change-log.md").read_text(encoding="utf-8")

    assert "servicenow_records" in change_log
    assert "sys_rest_message" in change_log
    assert "sys_rest_message_fn" in change_log
    assert "sys_script" in change_log
    assert "insert_or_update" in change_log
    assert "no live ServiceNow apply" in change_log


def test_operator_guide_documents_lifecycle_webhook_apply() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "apply-lifecycle-webhook" in guide
    assert "--confirm-records" in guide
    assert "--confirm-table rm_story" in guide
    assert "lifecycle webhook audit" in guide
    assert "insert_or_update" in guide


def test_sprint_sixty_six_change_log_documents_lifecycle_apply() -> None:
    change_log = Path("docs/sprints/sprint-66-change-log.md").read_text(encoding="utf-8")

    assert "apply-lifecycle-webhook" in change_log
    assert "upsert_table_record" in change_log
    assert "sys_rest_message" in change_log
    assert "sys_rest_message_fn" in change_log
    assert "sys_script" in change_log
    assert "lifecycle_webhook_confirmation_required" in change_log


def test_operator_guide_documents_lifecycle_webhook_verification() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "verify-lifecycle-webhook" in guide
    assert "read-only" in guide
    assert "record_missing" in guide
    assert "field_mismatch" in guide
    assert "verification report" in guide


def test_sprint_sixty_seven_change_log_documents_lifecycle_verification() -> None:
    change_log = Path("docs/sprints/sprint-67-change-log.md").read_text(encoding="utf-8")

    assert "verify_lifecycle_webhook_records" in change_log
    assert "verify-lifecycle-webhook" in change_log
    assert "record_missing" in change_log
    assert "field_mismatch" in change_log
    assert "read-only" in change_log


def test_operator_guide_documents_cicd_update_set_capability_probe() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "check-cicd-update-set-capability" in guide
    assert "/api/sn_cicd/update_set/create" in guide
    assert "/api/sn_cicd/update_set/retrieve" in guide
    assert "read-only" in guide
    assert "update_set_name" in guide
    assert "update_set_id" in guide
    assert "does not prove that generated XML can be imported directly" in guide


def test_sprint_eighty_seven_change_log_documents_cicd_capability_probe() -> None:
    change_log = Path("docs/sprints/sprint-87-change-log.md").read_text(encoding="utf-8")

    assert "CI/CD Update Set API" in change_log
    assert "check-cicd-update-set-capability" in change_log
    assert "ServiceNowClient.probe_cicd_update_set_endpoint" in change_log
    assert "raw XML import API" in change_log
    assert "reviewed ServiceNow-side importer" in change_log


def test_operator_guide_documents_cicd_update_set_lifecycle_methods() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "retrieve_cicd_update_set()" in guide
    assert "preview_cicd_update_set()" in guide
    assert "commit_cicd_update_set()" in guide
    assert "fetch_cicd_progress()" in guide
    assert "/api/sn_cicd/update_set/preview/{remote_update_set_id}" in guide
    assert "/api/sn_cicd/update_set/commit/{remote_update_set_id}" in guide
    assert "not wired into automated fulfillment yet" in guide


def test_sprint_eighty_eight_change_log_documents_cicd_lifecycle_methods() -> None:
    change_log = Path("docs/sprints/sprint-88-change-log.md").read_text(encoding="utf-8")

    assert "retrieve_cicd_update_set()" in change_log
    assert "preview_cicd_update_set()" in change_log
    assert "commit_cicd_update_set()" in change_log
    assert "fetch_cicd_progress()" in change_log
    assert "force_commit=false" in change_log
    assert "build/source ServiceNow instance" in change_log


def test_operator_guide_documents_update_set_importer_bootstrap() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "plan-update-set-importer" in guide
    assert "apply-update-set-importer" in guide
    assert "verify-update-set-importer" in guide
    assert "sysparm_target=sys_remote_update_set" in guide
    assert "jedi_update_set_import" in guide
    assert "/api/<namespace>/jedi_update_set_import" in guide
    assert "discovered platform state" in guide
    assert "GlideUpdateManager2().loadXML(xmlPayload)" in guide
    assert "does not send XML, preview, commit" in guide
    assert "JEDI XML Import Smoke 20260514 002" in guide
    assert "64c3e9d1b27a42479620114da017857a" in guide
    assert "zero `sys_update_xml` rows" in guide
    assert "JEDI XML Import Customer Updates Smoke 20260514 001" in guide
    assert "22221e3514c94fa3bde48148b0053e6f" in guide
    assert "sys_dictionary_rm_story_u_jedi_import_smoke_notes" in guide
    assert "d240c02ec330c710913fbf12b4013170" in guide
    assert "No commit was run" in guide


def test_sprint_eighty_nine_change_log_documents_update_set_importer() -> None:
    change_log = Path("docs/sprints/sprint-89-change-log.md").read_text(encoding="utf-8")

    assert "build_update_set_importer_bootstrap_spec()" in change_log
    assert "sys_ws_definition" in change_log
    assert "sys_ws_operation" in change_log
    assert "apply-update-set-importer" in change_log
    assert "verify-update-set-importer" in change_log
    assert "GlideUpdateManager2().loadXML(xmlPayload)" in change_log
    assert "Do not automate `upload.do`" in change_log
    assert "400 update_set_xml_required" in change_log
    assert "JEDI XML Import Smoke 20260514 002" in change_log
    assert "64c3e9d1b27a42479620114da017857a" in change_log
    assert "JEDI XML Import Customer Updates Smoke 20260514 001" in change_log
    assert "22221e3514c94fa3bde48148b0053e6f" in change_log
    assert "sys_documentation_rm_story_u_jedi_import_smoke_notes_en" in change_log
    assert "zero preview problems" in change_log


def test_operator_guide_documents_importer_backed_model_handoff() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "posts it to the ServiceNow-side importer `jedi_update_set_import`" in guide
    assert "looks up the retrieved update set by `remote_sys_id`" in guide
    assert "direct `sys_remote_update_set.do?sys_id=...` link" in guide
    assert "the importer endpoint is missing" in guide


def test_sprint_ninety_change_log_documents_importer_backed_handoff() -> None:
    change_log = Path("docs/sprints/sprint-90-change-log.md").read_text(encoding="utf-8")

    assert "import_update_set_xml" in change_log
    assert "jedi_update_set_import" in change_log
    assert "remote_sys_id" in change_log
    assert "no Table API upserts" in change_log
    assert "Direct Table API writes to `sys_update_xml`" in change_log
    assert "ca51627e2d96dbc3f5c418bfd34821b2" in change_log
    assert "sys_dictionary_rm_story_u_ai_review_notes" in change_log
    assert "sys_ui_section_8757b94d7f0000011c1ae8aa30062c20" in change_log
    assert "sys_documentation_rm_story_u_ai_review_notes_en" in change_log
    assert "state reported as `committed`" in change_log


def test_operator_guide_documents_ready_for_testing_after_handoff() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "discovers the active `Ready for Testing` state choice" in guide
    assert "`u_ai_status=Ready for Testing`" in guide
    assert "does not mean the retrieved Update Set has been approved or committed" in guide
    assert "active `Ready for Testing` state choice cannot be discovered" in guide


def test_sprint_ninety_one_change_log_documents_ready_for_testing_handoff() -> None:
    change_log = Path("docs/sprints/sprint-91-change-log.md").read_text(encoding="utf-8")

    assert "Ready for Testing" in change_log
    assert "state=-7" in change_log
    assert "u_ai_status=Ready for Testing" in change_log
    assert "sys_choice" in change_log
    assert (
        "does not replace the retrieved Update Set preview/commit approval boundary" in change_log
    )


def test_operator_guide_documents_manual_build_and_failure_state_handling() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "`u_ai_status=Human Review Required`" in guide
    assert "does not create a retrieved Update Set" in guide
    assert "active `Draft` state choice" in guide
    assert "`u_ai_status=Automation Failed`" in guide
    assert "does not leave the story in Work in Progress" in guide


def test_sprint_ninety_two_change_log_documents_uat_failure_handling() -> None:
    change_log = Path("docs/sprints/sprint-92-change-log.md").read_text(encoding="utf-8")

    assert "STRY0010001" in change_log
    assert "candidate is not ready for Update Set handoff" in change_log
    assert "Manual Build" in change_log
    assert "u_ai_status=Human Review Required" in change_log
    assert "u_ai_status=Automation Failed" in change_log
    assert "state=-6" in change_log


def test_capability_gate_design_requires_instance_discovery_workers() -> None:
    design = Path(
        "docs/superpowers/specs/2026-05-14-capability-based-automation-gate-design.md"
    ).read_text(encoding="utf-8")

    assert "Instance Discovery Workers" in design
    assert "target table metadata" in design
    assert "form sections/elements/views" in design
    assert "dynamic RAG" in design
    assert "LLM must not guess instance state" in design


def test_capability_gate_plan_sequences_instance_discovery_before_build() -> None:
    plan = Path("docs/superpowers/plans/2026-05-14-capability-based-automation-gate.md").read_text(
        encoding="utf-8"
    )

    assert "Task 3: Instance Discovery Models" in plan
    assert "Task 4: ServiceNow Instance Discovery Client" in plan
    assert "Task 5: Discovery-Backed Packet Integration" in plan
    assert "dynamic instance context" in plan
    assert "No model call should happen before discovery" in plan


def test_operator_guide_documents_capability_based_gate() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "capability-based automation gate" in guide
    assert "table names are metadata" in guide
    assert "`dictionary_field_create`" in guide
    assert "`form_layout_place_field`" in guide
    assert "`form_section_remove`" in guide
    assert "form-layout-analysis-v1" in guide
    assert "STRY0010001" in guide


def test_sprint_one_fifty_three_change_log_documents_form_section_context() -> None:
    change_log = Path("docs/sprints/sprint-153-change-log.md").read_text(encoding="utf-8")

    assert "`form_section_remove`" in change_log
    assert "dmn_demand" in change_log
    assert "`form_sections`" in change_log
    assert "form-layout-analysis-v1" in change_log
    assert "Enabled deterministic retrieved Update Set handoff" in change_log


def test_sprint_one_fifty_four_change_log_documents_form_section_gate_hardening() -> None:
    change_log = Path("docs/sprints/sprint-154-change-log.md").read_text(encoding="utf-8")
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "`Form Section`" in change_log
    assert "`Form Section Removal`" in change_log
    assert "rename/add/reorder" in change_log
    assert "not treated as deletion requests" in guide


def test_sprint_one_fifty_five_change_log_documents_surface_operation_planner() -> None:
    change_log = Path("docs/sprints/sprint-155-change-log.md").read_text(encoding="utf-8")
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "`surface_planning`" in change_log
    assert "`form_layout.section.remove`" in change_log
    assert "`form_layout.section.rename`" in change_log
    assert "surface-operation planning boundary" in guide
    assert "Builder maturity only affects confidence and fulfillment routing" in guide


def test_sprint_one_fifty_six_change_log_documents_context_dossier_boundary() -> None:
    change_log = Path("docs/sprints/sprint-156-change-log.md").read_text(encoding="utf-8")
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "`context_dossier`" in change_log
    assert "`structured_candidate_change_only`" in change_log
    assert "read-only XML shape references" in guide
    assert "raw XML fields or raw Update Set XML content" in guide
    assert "builder maturity is below the automated handoff threshold" in guide


def test_sprint_one_fifty_seven_change_log_documents_general_rewrite_feedback() -> None:
    change_log = Path("docs/sprints/sprint-157-change-log.md").read_text(encoding="utf-8")
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "general automation feedback" in change_log
    assert "`suggested_story`" in change_log
    assert "Suggested rewrite:" in guide
    assert "capability-agnostic" in guide
    assert "target artifact type" in guide


def test_sprint_one_fifty_eight_change_log_documents_classifier_gate_control() -> None:
    change_log = Path("docs/sprints/sprint-158-change-log.md").read_text(encoding="utf-8")
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "`JEDI_CLASSIFIER_GATE=<true|false>`" in change_log
    assert "defaults to `true`" in guide
    assert "`JEDI_CLASSIFIER_GATE=false`" in guide
    assert "exploratory structured reasoning" in guide
    assert "do not create retrieved Update Set handoffs" in change_log


def test_sprint_one_fifty_nine_change_log_documents_cmdb_ire_analysis() -> None:
    change_log = Path("docs/sprints/sprint-159-change-log.md").read_text(encoding="utf-8")
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "`cmdb_ire_analyze`" in change_log
    assert "`cmdb_ire_identification_rules`" in change_log
    assert "`cmdb_ire_reconciliation_rules`" in change_log
    assert "cmdb-ire-analysis-v1" in change_log
    assert "CMDB IRE Analysis Capability" in guide
    assert "cmdb_identifier" in guide
    assert "cmdb_reconciliation_definition" in guide
    assert "cmdb_ire_generate" in guide
    assert "retrieved Update Set handoff remains disabled" in guide


def test_sprint_one_sixty_change_log_documents_split_servicenow_runtime() -> None:
    change_log = Path("docs/sprints/sprint-160-change-log.md").read_text(encoding="utf-8")
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")
    architecture = Path("docs/system-architecture.md").read_text(encoding="utf-8")

    assert "separate story/source and development/target instances" in change_log
    assert "`SERVICENOW_PM_INSTANCE_URL`" in change_log
    assert "`SERVICENOW_DEV_INSTANCE_URL`" in change_log
    assert "single-instance compatibility fallback" in change_log
    assert "story status updates" in guide
    assert "retrieved Update Set imports use the DEV client" in guide
    assert "Split ServiceNow Instances" in architecture


def test_sprint_one_sixty_one_change_log_documents_roadmap_items_four_five_six() -> None:
    change_log = Path("docs/sprints/sprint-161-change-log.md").read_text(encoding="utf-8")

    assert "Sprint 161 Change Log" in change_log
    assert "`enabled` now means" in change_log
    assert "`ui_policy_generate`" in change_log
    assert "`cmdb_ire_generate`" in change_log
    assert "JEDI_PUBLIC_WEB_ACCESS=worker" in change_log


def test_sprint_ninety_three_change_log_documents_generic_dictionary_form() -> None:
    change_log = Path("docs/sprints/sprint-93-change-log.md").read_text(encoding="utf-8")

    assert "STRY0010001" in change_log
    assert "incident" in change_log
    assert "u_antics" in change_log
    assert "capability-based" in change_log
    assert "generic dictionary field creation plus form placement" in change_log


def test_sprint_one_forty_change_log_documents_sys_id_lifecycle_lookup() -> None:
    change_log = Path("docs/sprints/sprint-140-change-log.md").read_text(encoding="utf-8")
    backlog = Path("docs/production-hardening-backlog.md").read_text(encoding="utf-8")

    assert "duplicate `rm_story.number` values" in change_log
    assert "story_sys_id" in change_log
    assert "current.getUniqueValue()" in change_log
    assert "Failure writeback" in change_log
    assert "Sprint 140: Sys_id-backed lifecycle lookup" in backlog


def test_sprint_one_forty_one_change_log_documents_parser_hardening() -> None:
    change_log = Path("docs/sprints/sprint-141-change-log.md").read_text(encoding="utf-8")
    backlog = Path("docs/production-hardening-backlog.md").read_text(encoding="utf-8")

    assert "negative safety instructions" in change_log
    assert "operation_insert" in change_log
    assert "`conditions`" in change_log
    assert "Script Include stories" in change_log
    assert "supported-artifact UAT matrix" in change_log
    assert "dictionary `read_only=true` prevents the worker" in change_log
    assert "`current.<field>`" in change_log
    assert "dictionary-writable by design" in Path("docs/operator-guide.md").read_text(
        encoding="utf-8"
    )
    assert "Sprint 141: Supported artifact UAT parser hardening" in backlog


def test_sprint_one_forty_two_change_log_documents_business_rule_gate_inference() -> None:
    change_log = Path("docs/sprints/sprint-142-change-log.md").read_text(encoding="utf-8")
    backlog = Path("docs/production-hardening-backlog.md").read_text(encoding="utf-8")

    assert "STRY0010021" in change_log
    assert "`Fields read:`" in change_log
    assert "`set field ...`" in change_log
    assert "not cross-table writes" in change_log
    assert "Sprint 142: Business Rule gate inference hardening" in backlog


def test_sprint_one_forty_three_change_log_documents_script_metadata_separation() -> None:
    change_log = Path("docs/sprints/sprint-143-change-log.md").read_text(encoding="utf-8")
    backlog = Path("docs/production-hardening-backlog.md").read_text(encoding="utf-8")

    assert "STRY0010021" in change_log
    assert "fields_written" in change_log
    assert "candidate metadata" in change_log
    assert "`filter`" in change_log
    assert "sys_script.script" in change_log
    assert "Sprint 143: Business Rule script metadata separation" in backlog


def test_sprint_one_forty_four_change_log_documents_structured_ui_policy_gate() -> None:
    change_log = Path("docs/sprints/sprint-144-change-log.md").read_text(encoding="utf-8")
    backlog = Path("docs/production-hardening-backlog.md").read_text(encoding="utf-8")

    assert "STRY0010024" in change_log
    assert "`Run scripts: false`" in change_log
    assert "shared requirement-text parsing" in change_log
    assert "`flow_graph`" in change_log
    assert "`ui_policy_generate`" in change_log
    assert "missing action table" in change_log
    assert "Sprint 144: Structured UI Policy gate hardening" in backlog


def test_sprint_one_forty_five_change_log_documents_typed_intent_architecture() -> None:
    change_log = Path("docs/sprints/sprint-145-change-log.md").read_text(encoding="utf-8")
    backlog = Path("docs/production-hardening-backlog.md").read_text(encoding="utf-8")
    spec = Path("docs/superpowers/specs/2026-05-15-typed-intent-architecture-design.md").read_text(
        encoding="utf-8"
    )
    plan = Path("docs/superpowers/plans/2026-05-15-typed-intent-architecture.md").read_text(
        encoding="utf-8"
    )

    assert "STRY0010022" in change_log
    assert "AutomationIntent" in change_log
    assert "`normalized_intent`" in change_log
    assert "`cmdb_discovery_maps`" in change_log
    assert "Sprint 145: Typed intent architecture" in backlog
    assert "typed `AutomationIntent`" in spec
    assert "Implementation Plan" in plan


def test_sprint_one_forty_six_change_log_documents_dictionary_form_intent_aliases() -> None:
    change_log = Path("docs/sprints/sprint-146-change-log.md").read_text(encoding="utf-8")
    backlog = Path("docs/production-hardening-backlog.md").read_text(encoding="utf-8")

    assert "STRY0010020" in change_log
    assert "Dictionary field and form placement" in change_log
    assert "`Placement anchor:`" in change_log
    assert "`Placement position:`" in change_log
    assert "`dictionary_field_create`" in change_log
    assert "Sprint 146: Dictionary/form typed intent alias hardening" in backlog


def test_sprint_one_forty_seven_change_log_documents_script_include_hardening() -> None:
    change_log = Path("docs/sprints/sprint-147-change-log.md").read_text(encoding="utf-8")
    backlog = Path("docs/production-hardening-backlog.md").read_text(encoding="utf-8")

    assert "STRY0010023" in change_log
    assert "`Fields written / affected: none`" in change_log
    assert "`script_includes`" in change_log
    assert "`form_layout`" in change_log
    assert "`script_include_generate`" in change_log
    assert "`api_name`" in change_log
    assert "`global.<Script Include name>`" in change_log
    assert "at least one concrete ServiceNow change" in change_log
    assert "Empty candidate changes" in change_log
    assert "Sprint 147: Script Include structured story hardening" in backlog


def test_sprint_one_forty_eight_change_log_documents_business_rule_hardening() -> None:
    change_log = Path("docs/sprints/sprint-148-change-log.md").read_text(encoding="utf-8")
    backlog = Path("docs/production-hardening-backlog.md").read_text(encoding="utf-8")

    assert "STRY0010021" in change_log
    assert "`Timing: before`" in change_log
    assert "`Trigger timing:`" in change_log
    assert "`Fields written / affected:`" in change_log
    assert "`business_rule_generate`" in change_log
    assert "`sys_script`" in change_log
    assert "Sprint 148: Business Rule structured story hardening" in backlog


def test_sprint_1007_documents_employee_center_discovery_record_collection_guard() -> None:
    change_log = Path("docs/sprints/sprint-1007-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Employee Center discovery record collection guard" in change_log
    assert "`_employee_center_topics_surface()`" in change_log
    assert "`_employee_center_connected_content_surface()`" in change_log
    assert "`_surface_records()`" in change_log
    assert "discovery text metadata contains non-JSON value" in change_log
    assert (
        "1 failing-first Employee Center topic record collection subclass assertion"
        in change_log
    )
    assert (
        "Catalog and Employee Center surface discovery record collections are exact containers"
        in operator_guide
    )
    assert "`taxonomy_content_configuration`" in operator_guide
    assert "before topic" in operator_guide
    assert "iteration, content-type filtering" in operator_guide
    assert (
        "`test_employee_center_topics_rejects_record_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_employee_center_topics_rejects_record_subclass_without_leak`"
        in change_log
    )


def test_sprint_one_sixty_four_change_log_documents_architecture_hardening() -> None:
    change_log = Path("docs/sprints/sprint-164-change-log.md").read_text(encoding="utf-8")

    assert "fable-findings.md" in change_log
    assert "test_capability_registration.py" in change_log
    assert "`packet_model.py`" in change_log
    assert "`packet_validation.py`" in change_log
    assert "`packet_intent_changes.py`" in change_log
    assert "`_FREE_TEXT_RULES`" in change_log
    assert "`IMPLEMENTATION_SYSTEM_PROMPT`" in change_log
    assert "intent_required_instance_context" in change_log
    assert "adversarial review" in change_log
    assert "coverage 93.77%" in change_log


def test_sprint_one_sixty_five_change_log_documents_runtime_hardening() -> None:
    change_log = Path("docs/sprints/sprint-165-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "JEDI_LIFECYCLE_WEBHOOK_SECRET" in change_log
    assert "JEDI_PUBLIC_WEB_DOC_URLS" in change_log
    assert "JEDI_UPDATE_SET_USER_NAME" in change_log
    assert "sensitive query values" in change_log
    assert "1308 passed, 93.81% coverage" in change_log
    assert "Admin diagnostic surfaces redact" in operator_guide


def test_sprint_one_sixty_six_change_log_documents_audit_endpoint_hardening() -> None:
    change_log = Path("docs/sprints/sprint-166-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "GET /jobs/{job_id}/events" in change_log
    assert "correlation_id" in change_log
    assert "job event diagnostic messages" in change_log
    assert "64 passed" in change_log
    assert "1312 passed, 93.82% coverage" in change_log
    assert "GET /jobs/{job_id}/events" in operator_guide
    assert "Job event diagnostic messages are redacted" in operator_guide
    assert "correlation_id" in operator_guide


def test_sprint_one_sixty_seven_change_log_documents_admin_body_bounds() -> None:
    change_log = Path("docs/sprints/sprint-167-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "JEDI_ADMIN_MAX_BODY_BYTES" in change_log
    assert "admin request payload is too large" in change_log
    assert "/artifacts/*" in change_log
    assert "/jobs/*" in change_log
    assert "66 passed" in change_log
    assert "1315 passed, 93.79% coverage" in change_log
    assert "JEDI_ADMIN_MAX_BODY_BYTES" in operator_guide
    assert "edge, WAF, or API gateway" in operator_guide


def test_sprint_one_sixty_eight_change_log_documents_readiness_probe() -> None:
    change_log = Path("docs/sprints/sprint-168-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "GET /ready" in change_log
    assert "operational-store readiness" in change_log
    assert "status=unready" in change_log
    assert "68 passed" in change_log
    assert "1319 passed, 93.79% coverage" in change_log
    assert "GET /ready" in operator_guide
    assert "status=ready" in operator_guide


def test_operator_guide_documents_operational_alert_projection() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "GET /admin/alerts" in guide
    assert "Operational Alerts" in guide
    assert "read-only projection" in guide
    assert "failed and rejected fulfillment jobs" in guide
    assert "correlation_id" in guide
    assert "redacted" in guide
    assert "ServiceNow work notes" in guide


def test_sprint_one_sixty_nine_change_log_documents_operational_alerts() -> None:
    change_log = Path("docs/sprints/sprint-169-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "GET /admin/alerts" in change_log
    assert "Operational Alerts" in change_log
    assert "failed and rejected fulfillment jobs" in change_log
    assert "redacted" in change_log
    assert "72 passed" in change_log
    assert "1325 passed, 93.79% coverage" in change_log
    assert "GET /admin/alerts" in operator_guide


def test_operator_guide_documents_stale_running_job_alerts() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "stale running jobs" in guide
    assert "JEDI_RUNNING_JOB_STALE_AFTER_SECONDS" in guide
    assert "default 3600" in guide
    assert "Stale running job detection is non-mutating" in guide
    assert "does not fail, retry, unlock, or requeue work" in guide
    assert "worker logs" in guide


def test_sprint_one_seventy_change_log_documents_stale_job_alerts() -> None:
    change_log = Path("docs/sprints/sprint-170-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "JEDI_RUNNING_JOB_STALE_AFTER_SECONDS" in change_log
    assert "stale running jobs" in change_log
    assert "non-mutating" in change_log
    assert "76 passed" in change_log
    assert "1331 passed, 93.83% coverage" in change_log
    assert "GET /admin/alerts" in operator_guide


def test_operator_guide_documents_worker_side_stale_recovery() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Worker-side stale recovery is separate and disabled by default" in guide
    assert "requeue_stale_running_jobs()" in guide
    assert "FOR UPDATE SKIP LOCKED" in guide
    assert "clears `locked_by`, `locked_at`, and `last_error`" in guide
    assert "preserves `attempt_count`" in guide
    assert "JEDI_STALE_JOB_REQUEUE_ENABLED=false" in guide
    assert "JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS=3600" in guide
    assert "JEDI_STALE_JOB_REQUEUE_BATCH_SIZE=10" in guide
    assert "must be greater than zero" in guide
    assert "Invalid values fail worker settings loading" in guide


def test_sprint_one_seventy_one_change_log_documents_stale_recovery() -> None:
    change_log = Path("docs/sprints/sprint-171-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "requeue_stale_running_jobs" in change_log
    assert "FOR UPDATE SKIP LOCKED" in change_log
    assert "JEDI_STALE_JOB_REQUEUE_ENABLED" in change_log
    assert "10 passed" in change_log
    assert "37 passed" in change_log
    assert "1338 passed, 93.85% coverage" in change_log
    assert "JEDI_STALE_JOB_REQUEUE_ENABLED=false" in operator_guide


def test_sprint_one_seventy_two_change_log_documents_recovery_setting_validation() -> None:
    change_log = Path("docs/sprints/sprint-172-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "JEDI_STALE_JOB_REQUEUE_BATCH_SIZE" in change_log
    assert "JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS" in change_log
    assert "fail worker settings loading" in change_log
    assert "12 passed" in change_log
    assert "1341 passed, 93.86% coverage" in change_log
    assert "Invalid values fail worker settings loading" in operator_guide


def test_operator_guide_documents_external_alert_delivery_posture() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "External Alert Delivery" in guide
    assert "External alert delivery is disabled by default" in guide
    assert "failed worker iterations" in guide
    assert "stale-job recovery alerts" in guide
    assert "rejected-job alerts" in guide
    assert "zero-requeue stale recovery sweeps" in guide
    assert "JEDI_ALERT_WEBHOOK_ENABLED=false" in guide
    assert "JEDI_ALERT_WEBHOOK_URL=<https webhook URL>" in guide
    assert "JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS=3" in guide
    assert "JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES=16384" in guide
    assert "must use HTTPS" in guide
    assert "refuses unsafe URLs and oversized payloads before sending" in guide
    assert "redacts sensitive response values" in guide
    assert "best-effort" in guide
    assert "alert_failures" in guide
    assert "log a warning with diagnostic redaction" in guide
    assert "Alert sink response redaction" in guide
    assert "plain diagnostic strings" in guide
    assert "warning" in guide
    assert "diagnostic redaction" in guide
    assert "Idempotency-Key: <alert_id>" in guide
    assert "X-JEDI-Alert-ID: <alert_id>" in guide
    assert "X-JEDI-Correlation-ID: <correlation_id, only when present>" in guide
    assert "dedupe key" in guide
    assert "ASCII control characters" in guide
    assert "prevent header injection" in guide


def test_sprint_one_seventy_three_change_log_documents_alert_delivery_foundation() -> None:
    change_log = Path("docs/sprints/sprint-173-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "alert_delivery.py" in change_log
    assert "JEDI_ALERT_WEBHOOK_ENABLED" in change_log
    assert "HTTPS" in change_log
    assert "oversized payloads" in change_log
    assert "4 passed" in change_log
    assert "1350 passed, 93.87% coverage" in change_log
    assert "External Alert Delivery" in operator_guide


def test_sprint_one_seventy_four_change_log_documents_worker_alert_emission() -> None:
    change_log = Path("docs/sprints/sprint-174-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "worker_failure_alert" in change_log
    assert "alert_emitter" in change_log
    assert "alerts_emitted" in change_log
    assert "alert_failures" in change_log
    assert "best-effort" in change_log
    assert "5 passed" in change_log
    assert "1355 passed, 93.87% coverage" in change_log
    assert "failed worker iterations" in operator_guide


def test_sprint_one_seventy_five_change_log_documents_stale_requeue_alerts() -> None:
    change_log = Path("docs/sprints/sprint-175-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "stale_requeue_alert" in change_log
    assert "stale_job_requeue_alert_emitter" in change_log
    assert "alerts_emitted" in change_log
    assert "alert_failures" in change_log
    assert "Empty stale recovery sweeps do not emit external alerts" in change_log
    assert "warning-severity" in change_log
    assert "1360 passed, 93.88% coverage" in change_log
    assert "stale-job recovery alerts" in operator_guide


def test_sprint_one_seventy_six_change_log_documents_rejected_job_alerts() -> None:
    change_log = Path("docs/sprints/sprint-176-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "rejected_job_alert" in change_log
    assert "rejected_job_notifier" in change_log
    assert "JEDI_ALERT_WEBHOOK_ENABLED" in change_log
    assert "alert_transport" in change_log
    assert "diagnostic redaction" in change_log
    assert "client_secret=value" in change_log
    assert "1366 passed, 93.88% coverage" in change_log
    assert "rejected-job alerts" in operator_guide


def test_sprint_one_seventy_seven_change_log_documents_alert_idempotency_headers() -> None:
    change_log = Path("docs/sprints/sprint-177-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Idempotency-Key" in change_log
    assert "X-JEDI-Alert-ID" in change_log
    assert "X-JEDI-Correlation-ID" in change_log
    assert "dedupe key" in change_log
    assert "8 passed" in change_log
    assert "1368 passed, 93.89% coverage" in change_log
    assert "Idempotency-Key: <alert_id>" in operator_guide


def test_sprint_one_seventy_eight_change_log_documents_alert_header_safety() -> None:
    change_log = Path("docs/sprints/sprint-178-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "header injection defense" in change_log
    assert "ASCII control characters" in change_log
    assert "before transport invocation" in change_log
    assert "13 passed" in change_log
    assert "1374 passed, 93.89% coverage" in change_log
    assert "prevent header injection" in operator_guide


def test_sprint_one_seventy_nine_change_log_documents_worker_alert_failure_logs() -> None:
    change_log = Path("docs/sprints/sprint-179-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "worker alert failure observability" in change_log
    assert "worker-failure alert delivery" in change_log
    assert "stale-requeue alert delivery" in change_log
    assert "alert_failures" in change_log
    assert "client_secret=value" in change_log
    assert "1375 passed, 93.90% coverage" in change_log
    assert "log a warning with diagnostic redaction" in operator_guide


def test_sprint_one_eighty_change_log_documents_maintenance_failure_isolation() -> None:
    change_log = Path("docs/sprints/sprint-180-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "worker maintenance failure isolation" in change_log
    assert "prune_failures" in change_log
    assert "stale_job_recovery_failures" in change_log
    assert "redacted warning logs" in change_log
    assert "1378 passed, 93.90% coverage" in change_log
    assert "Maintenance failures are isolated from fulfillment processing" in operator_guide
    assert "prune_failures" in operator_guide
    assert "stale_job_recovery_failures" in operator_guide


def test_sprint_one_eighty_one_change_log_documents_alert_response_redaction() -> None:
    change_log = Path("docs/sprints/sprint-181-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "alert webhook response diagnostic redaction" in change_log
    assert "recursively redacted" in change_log
    assert "client_secret=value" in change_log
    assert "URL passwords" in change_log
    assert "13 passed" in change_log
    assert "1379 passed, 93.88% coverage" in change_log
    assert "Alert sink response redaction" in operator_guide


def test_sprint_one_eighty_two_change_log_documents_shared_alert_response_redaction() -> None:
    change_log = Path("docs/sprints/sprint-182-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "shared sensitive-key alert response redaction" in change_log
    assert "shared runtime sensitive-key vocabulary" in change_log
    assert "api_key" in change_log
    assert "id_token" in change_log
    assert "signature" in change_log
    assert "13 passed" in change_log
    assert "1380 passed, 93.88% coverage" in change_log
    assert (
        "Structured response redaction uses the shared sensitive-key vocabulary" in operator_guide
    )
    assert "sink-specific error payloads cannot leak common credential names" in operator_guide


def test_sprint_one_eighty_three_change_log_documents_alert_url_credential_rejection() -> None:
    change_log = Path("docs/sprints/sprint-183-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "alert webhook URL credential rejection" in change_log
    assert "embedded URL credentials" in change_log
    assert "before invoking transport" in change_log
    assert "14 passed" in change_log
    assert "1382 passed, 93.89% coverage" in change_log
    assert "must not include embedded URL credentials" in operator_guide
    assert "refuses unsafe URLs and oversized payloads before sending" in operator_guide


def test_sprint_one_eighty_four_change_log_documents_alert_url_startup_validation() -> None:
    change_log = Path("docs/sprints/sprint-184-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "startup validation for alert webhook URL credentials" in change_log
    assert "JEDI_ALERT_WEBHOOK_URL" in change_log
    assert "fails before the API or worker starts" in change_log
    assert "3 passed" in change_log
    assert "1384 passed, 93.90% coverage" in change_log
    assert "Runtime startup validation rejects missing, non-HTTPS" in operator_guide
    assert "before the API or worker starts" in operator_guide


def test_sprint_one_eighty_five_change_log_documents_shared_alert_url_validator() -> None:
    change_log = Path("docs/sprints/sprint-185-change-log.md").read_text(encoding="utf-8")

    assert "shared alert webhook URL validator" in change_log
    assert "validate_alert_webhook_url()" in change_log
    assert "emit_alert_webhook()" in change_log
    assert "runtime startup validation" in change_log
    assert "removing validation drift" in change_log
    assert "21 passed" in change_log
    assert "1389 passed, 93.90% coverage" in change_log


def test_sprint_one_eighty_six_change_log_documents_alert_url_sensitive_query_rejection() -> None:
    change_log = Path("docs/sprints/sprint-186-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "alert webhook URL sensitive-query rejection" in change_log
    assert "SENSITIVE_QUERY_KEYS" in change_log
    assert "validate_alert_webhook_url()" in change_log
    assert "production startup validation" in change_log
    assert "9 passed" in change_log
    assert "1393 passed, 93.90% coverage" in change_log
    assert "must not include sensitive query parameters" in operator_guide
    assert "sensitive-query alert webhook URLs before the API or worker starts" in operator_guide


def test_sprint_one_eighty_seven_change_log_documents_alert_url_fragment_rejection() -> None:
    change_log = Path("docs/sprints/sprint-187-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "alert webhook URL fragment rejection" in change_log
    assert "validate_alert_webhook_url()" in change_log
    assert "JEDI_ALERT_WEBHOOK_URL" in change_log
    assert "hide operator intent" in change_log
    assert "10 passed" in change_log
    assert "1396 passed, 93.91% coverage" in change_log
    assert "must not include URL fragments" in operator_guide
    assert "fragmented, and sensitive-query alert webhook URLs" in operator_guide


def test_sprint_one_eighty_eight_change_log_documents_servicenow_shared_redaction() -> None:
    change_log = Path("docs/sprints/sprint-188-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow structured redaction vocabulary" in change_log
    assert "servicenow.redact_secrets()" in change_log
    assert "SENSITIVE_QUERY_KEYS" in change_log
    assert "api_key" in change_log
    assert "id_token" in change_log
    assert "5 passed" in change_log
    assert "1398 passed, 93.91% coverage" in change_log
    assert (
        "ServiceNow API diagnostic redaction uses the same shared sensitive-key vocabulary"
        in operator_guide
    )
    assert "ServiceNow request/response diagnostics mask structured keys" in operator_guide


def test_sprint_one_eighty_nine_change_log_documents_servicenow_string_redaction() -> None:
    change_log = Path("docs/sprints/sprint-189-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "shared diagnostic string redaction for ServiceNow API errors" in change_log
    assert "diagnostic_redaction" in change_log
    assert "runtime_redaction._redact_diagnostic_text()" in change_log
    assert "servicenow.redact_secrets()" in change_log
    assert "api_key=value" in change_log
    assert "5 passed" in change_log
    assert "1400 passed, 93.91% coverage" in change_log
    assert "Plain diagnostic strings inside ServiceNow" in operator_guide
    assert "URL passwords, sensitive query parameters, and assignment" in operator_guide


def test_sprint_one_ninety_change_log_documents_sanitized_body_bytes_redaction() -> None:
    change_log = Path("docs/sprints/sprint-190-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "sanitized ServiceNow request body byte redaction" in change_log
    assert "HttpRequest.sanitized()" in change_log
    assert 'b"***REDACTED***"' in change_log
    assert "transport behavior remains unchanged" in change_log
    assert "3 passed" in change_log
    assert "1402 passed, 93.91% coverage" in change_log
    assert "replace raw" in operator_guide
    assert "body_bytes" in operator_guide
    assert "diagnostic representations" in operator_guide


def test_sprint_one_ninety_one_change_log_documents_sanitized_url_redaction() -> None:
    change_log = Path("docs/sprints/sprint-191-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "sanitized ServiceNow request URL redaction" in change_log
    assert "HttpRequest.sanitized()" in change_log
    assert "request `url`" in change_log
    assert "URL passwords" in change_log
    assert "non-sensitive query parameters" in change_log
    assert "3 passed" in change_log
    assert "1404 passed, 93.91% coverage" in change_log
    assert "Sanitized request URLs mask URL passwords" in operator_guide
    assert "preserving non-sensitive query parameters" in operator_guide


def test_sprint_one_ninety_two_change_log_documents_authorization_scheme_redaction() -> None:
    change_log = Path("docs/sprints/sprint-192-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "authorization scheme diagnostic redaction" in change_log
    assert "Authorization: Bearer <token>" in change_log
    assert "Authorization: Basic <token>" in change_log
    assert "Preserved the authorization scheme" in change_log
    assert "3 passed" in change_log
    assert "1406 passed, 93.92% coverage" in change_log
    assert "Authorization: Bearer <token>" in operator_guide
    assert "preserve the scheme for debugging" in operator_guide


def test_sprint_one_ninety_three_change_log_documents_malformed_url_redaction() -> None:
    change_log = Path("docs/sprints/sprint-193-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "malformed diagnostic URL fail-closed redaction" in change_log
    assert "quote-wrapped sensitive assignments" in change_log
    assert "bad-port URL handling" in change_log
    assert "***REDACTED***" in change_log
    assert "5 passed" in change_log
    assert "1409 passed, 93.92% coverage" in change_log
    assert "Malformed diagnostic URLs" in operator_guide
    assert "replaced with a redaction marker" in operator_guide


def test_sprint_one_ninety_four_change_log_documents_all_userinfo_url_redaction() -> None:
    change_log = Path("docs/sprints/sprint-194-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "all-userinfo diagnostic URL redaction" in change_log
    assert "entire URL userinfo component" in change_log
    assert "username-only userinfo" in change_log
    assert "operational alerts" in change_log
    assert "10 passed" in change_log
    assert "1411 passed, 93.92% coverage" in change_log
    assert "Diagnostic URL redaction masks the entire URL userinfo component" in operator_guide
    assert "https://api-token@example.gov/path" in operator_guide


def test_sprint_one_ninety_five_change_log_documents_encoded_query_key_redaction() -> None:
    change_log = Path("docs/sprints/sprint-195-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "encoded sensitive query-key diagnostic redaction" in change_log
    assert "decode query key names" in change_log
    assert "client%5Fsecret=encoded-secret" in change_log
    assert "Preserved original query key spelling" in change_log
    assert "8 passed" in change_log
    assert "1413 passed, 93.92% coverage" in change_log
    assert "decodes percent-encoded key names" in operator_guide
    assert "client%5Fsecret=value" in operator_guide


def test_sprint_one_ninety_six_change_log_documents_semicolon_query_redaction() -> None:
    change_log = Path("docs/sprints/sprint-196-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "semicolon-separated sensitive query redaction" in change_log
    assert "`&` and `;` query separators" in change_log
    assert "sysparm_limit=1;client%5Fsecret=encoded-secret" in change_log
    assert "Preserved original query separators" in change_log
    assert "9 passed" in change_log
    assert "1415 passed, 93.92% coverage" in change_log
    assert "semicolon-separated parameters" in operator_guide
    assert "sysparm_limit=1;client%5Fsecret=value" in operator_guide


def test_sprint_one_ninety_seven_change_log_documents_hyphenated_sensitive_keys() -> None:
    change_log = Path("docs/sprints/sprint-197-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "hyphenated sensitive-key redaction" in change_log
    assert "shared sensitive-key normalization helper" in change_log
    assert "api-key=value" in change_log
    assert "client-secret=value" in change_log
    assert "22 passed" in change_log
    assert "1420 passed, 93.92% coverage" in change_log
    assert "normalizes hyphenated and underscored spellings" in operator_guide
    assert "api-key=value" in operator_guide


def test_sprint_one_ninety_eight_change_log_documents_quote_aware_assignments() -> None:
    change_log = Path("docs/sprints/sprint-198-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "quote-aware sensitive assignment redaction" in change_log
    assert "quoted with embedded spaces" in change_log
    assert "single-quoted and double-quoted values" in change_log
    assert "10 passed" in change_log
    assert "1422 passed, 93.92% coverage" in change_log
    assert 'client_secret="quoted value with spaces"' in operator_guide


def test_sprint_one_ninety_nine_change_log_documents_x_prefixed_sensitive_keys() -> None:
    change_log = Path("docs/sprints/sprint-199-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "vendor-style `x-*` sensitive-key redaction" in change_log
    assert "`x-api-key` and `x-client-secret`" in change_log
    assert "x_api_key" in change_log
    assert "27 passed" in change_log
    assert "1427 passed, 93.92% coverage" in change_log
    assert "x-api-key=value" in operator_guide
    assert "x-client-secret=value" in operator_guide


def test_sprint_two_hundred_change_log_documents_camel_case_sensitive_keys() -> None:
    change_log = Path("docs/sprints/sprint-200-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "camelCase sensitive-key redaction aliases" in change_log
    assert "`clientSecret=value` and `accessToken=value`" in change_log
    assert "camelCase-compatible aliases" in change_log
    assert "31 passed" in change_log
    assert "1432 passed, 93.92% coverage" in change_log
    assert "clientSecret=value" in operator_guide
    assert "accessToken=value" in operator_guide


def test_sprint_two_hundred_one_change_log_documents_cookie_redaction() -> None:
    change_log = Path("docs/sprints/sprint-201-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "cookie and Set-Cookie redaction" in change_log
    assert "`Cookie:` and `Set-Cookie:`" in change_log
    assert "line-bounded diagnostic header redaction" in change_log
    assert "cookie" in change_log
    assert "35 passed" in change_log
    assert "1437 passed, 93.92% coverage" in change_log
    assert "Cookie: JSESSIONID=value; route=node" in operator_guide
    assert "preserving following lines" in operator_guide


def test_sprint_two_hundred_two_change_log_documents_private_key_redaction() -> None:
    change_log = Path("docs/sprints/sprint-202-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "PEM and private-key redaction" in change_log
    assert "multiline PEM private-key blocks" in change_log
    assert "`private_key`, `privateKey`, and `ssh_private_key`" in change_log
    assert "38 passed" in change_log
    assert "1441 passed, 93.92% coverage" in change_log
    assert "PEM private-key blocks are redacted across diagnostic lines" in operator_guide
    assert "-----BEGIN PRIVATE KEY-----" in operator_guide


def test_sprint_two_hundred_three_change_log_documents_cloud_credential_redaction() -> None:
    change_log = Path("docs/sprints/sprint-203-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "cloud credential redaction aliases" in change_log
    assert "`aws_secret_access_key`, `awsSessionToken`, and `azureClientSecret`" in change_log
    assert "AWS and Azure credential aliases" in change_log
    assert "42 passed" in change_log
    assert "1446 passed, 93.92% coverage" in change_log
    assert "awsSecretAccessKey=value" in operator_guide
    assert "azureClientSecret=value" in operator_guide


def test_sprint_two_hundred_four_change_log_documents_alert_webhook_ssrf_guard() -> None:
    change_log = Path("docs/sprints/sprint-204-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "alert webhook local-target SSRF guard" in change_log
    assert "`localhost`" in change_log
    assert "IPv4 and IPv6 loopback targets" in change_log
    assert "169.254.169.254" in change_log
    assert "17 passed" in change_log
    assert "1451 passed, 93.92% coverage" in change_log
    assert "must not target obvious local or link-local SSRF destinations" in operator_guide
    assert "local-target, link-local-target" in operator_guide


def test_sprint_two_hundred_five_change_log_documents_localhost_subdomain_guard() -> None:
    change_log = Path("docs/sprints/sprint-205-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "delegated `.localhost` alert webhook target guard" in change_log
    assert "`alerts.localhost`" in change_log
    assert "hostname ending in `.localhost`" in change_log
    assert "18 passed" in change_log
    assert "1453 passed, 93.92% coverage" in change_log
    assert "delegated `.localhost` names such as `alerts.localhost`" in operator_guide


def test_sprint_two_hundred_six_change_log_documents_unspecified_webhook_address_guard() -> None:
    change_log = Path("docs/sprints/sprint-206-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "unspecified alert webhook address guard" in change_log
    assert "`0.0.0.0`" in change_log
    assert "`[::]`" in change_log
    assert "unspecified IP addresses are rejected" in change_log
    assert "20 passed" in change_log
    assert "1456 passed, 93.92% coverage" in change_log
    assert "unspecified bind addresses such as `0.0.0.0` or `[::]`" in operator_guide


def test_sprint_two_hundred_seven_change_log_documents_webhook_control_character_guard() -> None:
    change_log = Path("docs/sprints/sprint-207-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "alert webhook URL whitespace/control-character guard" in change_log
    assert "raw newline/control characters" in change_log
    assert "raw whitespace" in change_log
    assert "22 passed" in change_log
    assert "1461 passed, 93.92% coverage" in change_log
    assert "must not include raw whitespace or control characters" in operator_guide
    assert "whitespace/control-character" in operator_guide


def test_sprint_two_hundred_eight_change_log_documents_webhook_encoded_control_guard() -> None:
    change_log = Path("docs/sprints/sprint-208-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "alert webhook URL encoded-control-character guard" in change_log
    assert "percent-encoded CR/LF" in change_log
    assert "%0d%0a" in change_log
    assert "%20" in change_log
    assert "24 passed" in change_log
    assert "1466 passed, 93.93% coverage" in change_log
    assert "percent-encoded whitespace or control characters" in operator_guide
    assert "encoded-whitespace/control-character" in operator_guide


def test_sprint_two_hundred_nine_change_log_documents_legacy_numeric_ipv4_guard() -> None:
    change_log = Path("docs/sprints/sprint-209-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "alert webhook legacy numeric IPv4 SSRF guard" in change_log
    assert "`127.1`" in change_log
    assert "`2130706433`" in change_log
    assert "`0177.0.0.1`" in change_log
    assert "`0x7f000001`" in change_log
    assert "`2852039166`" in change_log
    assert "without DNS resolution" in change_log
    assert "33 passed" in change_log
    assert "1478 passed, 93.94% coverage" in change_log
    assert "legacy numeric loopback forms such as `127.1`" in operator_guide
    assert "legacy-numeric local-target" in operator_guide


def test_sprint_two_hundred_ten_change_log_documents_semicolon_query_guard() -> None:
    change_log = Path("docs/sprints/sprint-210-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "alert webhook semicolon query separator sensitive-key guard" in change_log
    assert "team=platform;token=secret" in change_log
    assert "semicolon-separated `client_secret`" in change_log
    assert "both `&` and `;` as query separators" in change_log
    assert "35 passed, 95.29% focused coverage" in change_log
    assert "1483 passed, 93.93% coverage" in change_log
    assert "team=platform;token=secret" in operator_guide
    assert "team=platform;client_secret=secret" in operator_guide


def test_sprint_two_hundred_eleven_change_log_documents_encoded_query_separator_guard() -> None:
    change_log = Path("docs/sprints/sprint-211-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "alert webhook encoded query separator sensitive-key guard" in change_log
    assert "team=platform%26token=secret" in change_log
    assert "team=platform%3Bclient_secret=secret" in change_log
    assert "note=fish%26chips" in change_log
    assert "38 passed, 95.56% focused coverage" in change_log
    assert "1489 passed, 93.93% coverage" in change_log
    assert "team=platform%26token=secret" in operator_guide
    assert "team=platform%3Bclient_secret=secret" in operator_guide
    assert "note=fish%26chips" in operator_guide


def test_sprint_two_hundred_twelve_documents_double_encoded_query_separator_guard() -> None:
    change_log = Path("docs/sprints/sprint-212-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "alert webhook double-encoded query separator sensitive-key guard" in change_log
    assert "team=platform%2526token=secret" in change_log
    assert "team=platform%253Bclient_secret=secret" in change_log
    assert "note=fish%2526chips" in change_log
    assert "bounded three-pass limit" in change_log
    assert "41 passed, 95.21% focused coverage" in change_log
    assert "1495 passed, 93.93% coverage" in change_log
    assert "team=platform%2526token=secret" in operator_guide
    assert "team=platform%253Bclient_secret=secret" in operator_guide
    assert "bounded to three decode passes" in operator_guide


def test_sprint_two_hundred_thirteen_change_log_documents_unicode_dot_host_guard() -> None:
    change_log = Path("docs/sprints/sprint-213-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "alert webhook Unicode-dot local-target guard" in change_log
    assert "localhost。" in change_log
    assert "127。0。0。1" in change_log
    assert "Unicode DNS dot aliases are canonicalized" in change_log
    assert "43 passed, 95.41% focused coverage" in change_log
    assert "1500 passed, 93.93% coverage" in change_log
    assert "Unicode-dot local names such as `localhost。`" in operator_guide
    assert "Unicode-dot loopback forms such as `127。0。0。1`" in operator_guide
    assert "unicode-dot local-target" in operator_guide


def test_sprint_two_hundred_fourteen_change_log_documents_public_web_url_guard() -> None:
    change_log = Path("docs/sprints/sprint-214-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "public documentation outbound URL guard" in change_log
    assert "https://doc-user:doc-secret@docs.servicenow.com/docs" in change_log
    assert "2130706433" in change_log
    assert "2852039166" in change_log
    assert "url_host_safety.py" in change_log
    assert "46 passed, 95.74% focused coverage" in change_log
    assert "1504 passed, 93.94% coverage" in change_log
    assert "credentialed documentation URLs" in operator_guide
    assert "legacy numeric local" in operator_guide
    assert "`2130706433`" in operator_guide
    assert "`2852039166`" in operator_guide
    assert "must not include embedded credentials" in operator_guide


def test_sprint_two_hundred_fifteen_change_log_documents_public_doc_url_content_guard() -> None:
    change_log = Path("docs/sprints/sprint-215-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "public documentation URL content guard" in change_log
    assert "token=doc-secret" in change_log
    assert "#section" in change_log
    assert "percent-encoded control characters" in change_log
    assert "JEDI_PUBLIC_WEB_DOC_URLS" in change_log
    assert "url_query_safety.py" in change_log
    assert "51 passed, 95.14% focused coverage" in change_log
    assert "1513 passed, 93.95% coverage" in change_log
    assert "fragmented" in operator_guide
    assert "encoded-whitespace/control-character" in operator_guide
    assert "sensitive-query" in operator_guide
    assert "sensitive query parameters such as `token` or `client_secret`" in operator_guide


def test_sprint_two_hundred_sixteen_documents_public_doc_private_host_guard() -> None:
    change_log = Path("docs/sprints/sprint-216-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "public documentation private-host startup guard" in change_log
    assert "`127.0.0.1`" in change_log
    assert "delegated `.localhost`" in change_log
    assert "`10.0.0.1`" in change_log
    assert "`169.254.169.254`" in change_log
    assert "`2130706433`" in change_log
    assert "`2852039166`" in change_log
    assert "is_non_public_hostname()" in change_log
    assert "52 passed, 94.55% focused coverage" in change_log
    assert "1521 passed, 93.96% coverage" in change_log
    assert "Production startup rejects public documentation URLs" in operator_guide
    assert "delegated `.localhost`" in operator_guide
    assert "legacy numeric local" in operator_guide


def test_sprint_two_hundred_seventeen_documents_admin_console_rate_limit() -> None:
    change_log = Path("docs/sprints/sprint-217-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "admin console rate-limit coverage" in change_log
    assert "repeated `/admin` HTML console requests" in change_log
    assert "repeated `/admin/artifacts/{artifact_id}`" in change_log
    assert "before Basic-auth credential checks" in change_log
    assert "4 passed" in change_log
    assert "1524 passed, 93.99% coverage" in change_log
    assert "All admin diagnostic surfaces share the same admin rate limiter" in operator_guide
    assert "HTML admin console at `/admin`" in operator_guide
    assert "Basic-auth artifact detail pages" in operator_guide
    assert "credential guessing" in operator_guide


def test_sprint_two_hundred_eighteen_documents_admin_artifact_payload_redaction() -> None:
    change_log = Path("docs/sprints/sprint-218-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "admin artifact payload redaction" in change_log
    assert "URL passwords" in change_log
    assert "structured `client_secret` values" in change_log
    assert "structured `api_key` values" in change_log
    assert "`GET /artifacts/{artifact_id}`" in change_log
    assert "`/admin/artifacts/{artifact_id}`" in change_log
    assert "2 passed" in change_log
    assert "1527 passed, 93.97% coverage" in change_log
    assert "Admin artifact payloads are diagnostic views" in operator_guide
    assert "recursively redact stored payload values" in operator_guide
    assert "artifact SHA-256 remains the provenance check" in operator_guide


def test_sprint_two_hundred_nineteen_documents_artifact_reference_path_redaction() -> None:
    change_log = Path("docs/sprints/sprint-219-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "admin artifact reference path redaction" in change_log
    assert "`GET /jobs/{job_id}/artifacts`" in change_log
    assert "URL credentials" in change_log
    assert "sensitive `client_secret` query value" in change_log
    assert "`db://artifact_blobs/1`" in change_log
    assert "2 passed" in change_log
    assert "1529 passed, 93.97% coverage" in change_log
    assert "Job artifact reference paths" in operator_guide
    assert "diagnostic strings" in operator_guide
    assert "redacted before returning them" in operator_guide


def test_sprint_two_hundred_twenty_documents_admin_response_headers() -> None:
    change_log = Path("docs/sprints/sprint-220-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "admin diagnostic response headers" in change_log
    assert "`Cache-Control: no-store`" in change_log
    assert "`Pragma: no-cache`" in change_log
    assert "`X-Content-Type-Options: nosniff`" in change_log
    assert "`/health` receives `nosniff` without forced `no-store`" in change_log
    assert "4 passed" in change_log
    assert "1534 passed, 93.96% coverage" in change_log
    assert "Admin diagnostic responses are non-cacheable" in operator_guide
    assert "Runtime responses also return `X-Content-Type-Options: nosniff`" in operator_guide
    assert (
        "liveness and readiness probes receive `nosniff` without forcing no-store" in operator_guide
    )


def test_sprint_two_hundred_twenty_one_documents_html_admin_browser_isolation() -> None:
    change_log = Path("docs/sprints/sprint-221-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "HTML admin console browser isolation headers" in change_log
    assert "`Content-Security-Policy`" in change_log
    assert "`X-Frame-Options: DENY`" in change_log
    assert "`Referrer-Policy: no-referrer`" in change_log
    assert "JSON admin diagnostics such as `/admin/jobs` do not receive the HTML CSP" in change_log
    assert "3 passed" in change_log
    assert "1538 passed, 93.94% coverage" in change_log
    assert "HTML admin console responses also use browser isolation headers" in operator_guide
    assert "`default-src 'none'`" in operator_guide
    assert "`frame-ancestors 'none'`" in operator_guide
    assert "JSON admin diagnostic endpoints do not receive the HTML CSP" in operator_guide


def test_sprint_two_hundred_twenty_two_documents_strict_transport_security() -> None:
    change_log = Path("docs/sprints/sprint-222-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "explicit Strict Transport Security response policy" in change_log
    assert "`JEDI_STRICT_TRANSPORT_SECURITY_ENABLED`" in change_log
    assert "`JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS`" in change_log
    assert "`Strict-Transport-Security` by default" in change_log
    assert "`Strict-Transport-Security: max-age=31536000; includeSubDomains`" in change_log
    assert "5 passed" in change_log
    assert "1543 passed, 93.95% coverage" in change_log
    assert "Strict Transport Security is explicit and deployment-controlled" in operator_guide
    assert "permanently HTTPS at the approved edge" in operator_guide
    assert "Public production roles require at least `31536000` seconds" in operator_guide


def test_sprint_two_hundred_twenty_three_documents_admin_vary_authorization() -> None:
    change_log = Path("docs/sprints/sprint-223-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "authenticated admin diagnostic cache variation" in change_log
    assert "`/admin/jobs` return `Vary: Authorization`" in change_log
    assert "HTML admin console returns `Vary: Authorization`" in change_log
    assert "public probes such as `/health` do not emit `Vary: Authorization`" in change_log
    assert "3 passed" in change_log
    assert "1547 passed, 93.91% coverage" in change_log
    assert "Authenticated admin diagnostic responses also return `Vary: Authorization`" in (
        operator_guide
    )
    assert "reusable for another credential context" in operator_guide
    assert "Public deployment probes such as `/health` do not emit" in operator_guide


def test_sprint_two_hundred_twenty_four_documents_admin_auth_failure_cache_controls() -> None:
    change_log = Path("docs/sprints/sprint-224-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "failed admin authentication cache controls" in change_log
    assert "failed Bearer-token admin API authentication" in change_log
    assert "`Expires: 0`" in change_log
    assert "`Vary: Authorization`" in change_log
    assert "preserving the `WWW-Authenticate` challenge" in change_log
    assert "2 passed" in change_log
    assert "1550 passed, 93.90% coverage" in change_log
    assert "`Cache-Control: no-store`, `Pragma: no-cache`, and `Expires: 0`" in (operator_guide)
    assert "failed admin authentication responses" in operator_guide


def test_sprint_two_hundred_twenty_five_documents_admin_robot_indexing_controls() -> None:
    change_log = Path("docs/sprints/sprint-225-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "admin diagnostic indexing controls" in change_log
    assert "`/admin/jobs` return `X-Robots-Tag: noindex, nofollow, noarchive`" in (change_log)
    assert "HTML admin console returns the same robot-indexing suppression header" in (change_log)
    assert "public probes such as `/health` do not emit the robots policy" in change_log
    assert "3 passed" in change_log
    assert "1554 passed, 93.90% coverage" in change_log
    assert "Admin diagnostic responses also return `X-Robots-Tag: noindex" in (operator_guide)
    assert "not an access-control mechanism" in operator_guide
    assert "enterprise search appliance" in operator_guide


def test_sprint_two_hundred_twenty_six_documents_html_admin_permissions_policy() -> None:
    change_log = Path("docs/sprints/sprint-226-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "HTML admin console Permissions Policy" in change_log
    assert "`Permissions-Policy` disabling camera" in change_log
    assert "`/admin/artifacts/{artifact_id}` returns the same browser capability policy" in (
        change_log
    )
    assert "`/admin/jobs` does not receive the HTML Permissions Policy" in change_log
    assert "3 passed" in change_log
    assert "1557 passed, 93.89% coverage" in change_log
    assert "a `Permissions-Policy` that disables browser capabilities" in operator_guide
    assert "camera, microphone, geolocation, payment, USB" in operator_guide
    assert (
        "JSON admin diagnostic endpoints do not receive the HTML CSP or HTML Permissions Policy"
        in operator_guide
    )


def test_sprint_two_hundred_twenty_seven_documents_runtime_request_id() -> None:
    change_log = Path("docs/sprints/sprint-227-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "bounded runtime request-id propagation" in change_log
    assert "runtime responses generate `X-JEDI-Request-ID`" in change_log
    assert "safe inbound `X-Request-ID` values are echoed" in change_log
    assert "overlong inbound request ids are not echoed" in change_log
    assert "printable ASCII request ids up to 128 characters" in change_log
    assert "3 passed" in change_log
    assert "1561 passed, 93.88% coverage" in change_log
    assert "Every runtime response returns `X-JEDI-Request-ID`" in operator_guide
    assert "no longer than 128 characters" in operator_guide
    assert "correlation metadata only" in operator_guide


def test_sprint_two_hundred_twenty_eight_documents_basic_auth_decode_bound() -> None:
    change_log = Path("docs/sprints/sprint-228-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "bounded Basic auth credential decoding" in change_log
    assert "rejected before base64 decoding" in change_log
    assert "8192-byte encoded credential limit" in change_log
    assert "malformed or oversized Basic auth values" in change_log
    assert "1 passed" in change_log
    assert "1563 passed, 93.88% coverage" in change_log
    assert "Development Basic auth is bounded before credential parsing" in operator_guide
    assert "larger than 8192 bytes before base64 decoding" in operator_guide
    assert "in addition to admin route body-size limits and rate limiting" in operator_guide


def test_sprint_two_hundred_twenty_nine_documents_bearer_token_compare_bound() -> None:
    change_log = Path("docs/sprints/sprint-229-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "bounded Bearer admin token comparison" in change_log
    assert "rejected before `secrets.compare_digest()` is called" in change_log
    assert "8192-byte token-value limit" in change_log
    assert "fail-closed rejected-token behavior" in change_log
    assert "1 passed" in change_log
    assert "1565 passed, 93.88% coverage" in change_log
    assert "Admin Bearer tokens are also bounded before credential comparison" in (operator_guide)
    assert "larger than 8192 bytes before calling constant-time comparison" in operator_guide
    assert "same rejected-token response" in operator_guide


def test_sprint_two_hundred_thirty_documents_admin_job_id_bounds() -> None:
    change_log = Path("docs/sprints/sprint-230-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "bounded admin job diagnostic identifiers" in change_log
    assert "rejected before operational-store lookup" in change_log
    assert "256-character printable ASCII boundary" in change_log
    assert "2 passed" in change_log
    assert "1568 passed, 93.89% coverage" in change_log
    assert "Admin job diagnostic path parameters are validated" in operator_guide
    assert "`/jobs/{job_id}/artifacts` and `/jobs/{job_id}/events`" in operator_guide
    assert "longer-than-256-character job identifiers" in operator_guide
    assert "decoded control characters into diagnostics" in operator_guide


def test_sprint_two_hundred_thirty_one_documents_admin_api_token_strength() -> None:
    change_log = Path("docs/sprints/sprint-231-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "configured admin API token startup strength" in change_log
    assert "`JEDI_ADMIN_API_TOKEN` shorter than 32 characters" in change_log
    assert "MIN_PRODUCTION_ADMIN_API_TOKEN_LENGTH = 32" in change_log
    assert "worker-only validation paths" in change_log
    assert "1 passed" in change_log
    assert "1570 passed, 93.89% coverage" in change_log
    assert (
        "Production startup validation rejects weak or malformed configured admin API tokens"
        in operator_guide
    )
    assert "`JEDI_ADMIN_API_TOKEN` is set while `JEDI_ENVIRONMENT=production`" in (operator_guide)
    assert "at least 32 characters" in operator_guide


def test_sprint_two_hundred_thirty_two_documents_admin_api_token_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-232-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "admin API token character hygiene" in change_log
    assert "`JEDI_ADMIN_API_TOKEN` values containing control characters" in change_log
    assert "must not contain whitespace or control characters" in change_log
    assert "worker-only validation paths" in change_log
    assert "1 passed" in change_log
    assert "1572 passed, 93.89% coverage" in change_log
    assert "weak or malformed configured admin API tokens" in operator_guide
    assert "must be at least 32 characters" in operator_guide
    assert "must not contain whitespace or control characters" in operator_guide
    assert "short or malformed production token value" in operator_guide


def test_sprint_two_hundred_thirty_three_documents_webhook_secret_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-233-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "HMAC lifecycle webhook secret character hygiene" in change_log
    assert "`JEDI_LIFECYCLE_WEBHOOK_SECRET` values containing control characters" in (change_log)
    assert "must not contain whitespace or control characters" in change_log
    assert "`JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE=hmac_sha256`" in change_log
    assert "1 passed" in change_log
    assert "1574 passed, 93.89% coverage" in change_log
    assert "Production startup validation also rejects malformed HMAC webhook secrets" in (
        operator_guide
    )
    assert "`JEDI_LIFECYCLE_WEBHOOK_SECRET` must be at least 32 characters" in (operator_guide)
    assert "must not contain whitespace or control characters" in operator_guide
    assert "newline, tab, or padded secret value" in operator_guide


def test_sprint_two_hundred_thirty_four_documents_openai_key_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-234-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "OpenAI provider credential character hygiene" in change_log
    assert "`OPENAI_API_KEY` values containing control characters" in change_log
    assert "must not contain whitespace or control characters" in change_log
    assert "`JEDI_MODEL_PROVIDER=openai`" in change_log
    assert "1 passed" in change_log
    assert "1576 passed, 93.90% coverage" in change_log
    assert "Production startup validation rejects malformed model provider configuration" in (
        operator_guide
    )
    assert (
        "When `JEDI_MODEL_PROVIDER=openai`, `OPENAI_API_KEY` and "
        "`OPENAI_MODEL` are required" in operator_guide
    )
    assert "must not contain whitespace or control characters" in operator_guide
    assert "newline, tab, or padded provider value" in operator_guide


def test_sprint_two_hundred_thirty_five_documents_openai_model_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-235-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "OpenAI model identifier character hygiene" in change_log
    assert "`OPENAI_MODEL` values containing control characters" in change_log
    assert "model identifiers must not contain whitespace or control characters" in change_log
    assert "`JEDI_MODEL_PROVIDER=openai`" in change_log
    assert "1 passed" in change_log
    assert "1578 passed, 93.90% coverage" in change_log
    assert "Production startup validation rejects malformed model provider configuration" in (
        operator_guide
    )
    assert "`OPENAI_API_KEY` and `OPENAI_MODEL` are required" in operator_guide
    assert "must not contain whitespace or control characters" in operator_guide
    assert "newline, tab, or padded provider value" in operator_guide


def test_sprint_two_hundred_thirty_six_documents_servicenow_url_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-236-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow instance URL transport hygiene" in change_log
    assert "non-HTTPS `SERVICENOW_DEV_INSTANCE_URL` values" in change_log
    assert "must use HTTPS" in change_log
    assert "embedded credentials, URL fragments" in change_log
    assert "1 passed" in change_log
    assert "1580 passed, 93.91% coverage" in change_log
    assert "Production startup validation rejects malformed ServiceNow instance URLs" in (
        operator_guide
    )
    assert "`SERVICENOW_INSTANCE_URL`, `SERVICENOW_PM_INSTANCE_URL`, and" in (operator_guide)
    assert "`SERVICENOW_DEV_INSTANCE_URL` values must use HTTPS" in operator_guide
    assert "non-TLS or ambiguous ServiceNow target" in operator_guide


def test_sprint_two_hundred_thirty_seven_documents_servicenow_oauth_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-237-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow OAuth credential character hygiene" in change_log
    assert "`SERVICENOW_DEV_CLIENT_SECRET` values containing control characters" in (change_log)
    assert "OAuth client IDs and secrets" in change_log
    assert "must not contain whitespace or control characters" in change_log
    assert "1 passed" in change_log
    assert "1582 passed, 93.91% coverage" in change_log
    assert "Production startup validation also rejects malformed ServiceNow OAuth credentials" in (
        operator_guide
    )
    assert "`SERVICENOW_CLIENT_ID`, `SERVICENOW_CLIENT_SECRET`" in operator_guide
    assert "`SERVICENOW_DEV_CLIENT_SECRET` values must not contain whitespace" in (operator_guide)
    assert "newline, tab, or padded OAuth credential value" in operator_guide


def test_sprint_two_hundred_thirty_eight_documents_database_url_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-238-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "PostgreSQL operational store URL enforcement" in change_log
    assert "non-PostgreSQL `DATABASE_URL` values" in change_log
    assert "`DATABASE_URL` must use a PostgreSQL scheme" in change_log
    assert "raw or encoded whitespace or control characters" in change_log
    assert "1 passed" in change_log
    assert "1584 passed, 93.92% coverage" in change_log
    assert "Production startup validation requires a PostgreSQL operational store" in (
        operator_guide
    )
    assert "`DATABASE_URL` must use a PostgreSQL scheme" in operator_guide
    assert "raw or encoded whitespace or control characters" in operator_guide
    assert "local file-backed, malformed, or ambiguous database URL" in operator_guide


def test_sprint_two_hundred_thirty_nine_documents_database_url_fragments() -> None:
    change_log = Path("docs/sprints/sprint-239-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "PostgreSQL operational store URL fragment hygiene" in change_log
    assert "URL fragments" in change_log
    assert "`DATABASE_URL`" in change_log
    assert "1 passed" in change_log
    assert "1586 passed, 93.92% coverage" in change_log
    assert "Production startup validation requires a PostgreSQL operational store" in (
        operator_guide
    )
    assert "must not include URL fragments" in operator_guide


def test_sprint_two_hundred_forty_documents_classifier_gate_production_guard() -> None:
    change_log = Path("docs/sprints/sprint-240-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Classifier gate production guard" in change_log
    assert "`JEDI_CLASSIFIER_GATE=false`" in change_log
    assert "development-only" in change_log
    assert "1 passed" in change_log
    assert "1588 passed, 93.92% coverage" in change_log
    assert "`JEDI_CLASSIFIER_GATE` defaults to `true`" in operator_guide
    assert "It is rejected in production startup validation" in operator_guide


def test_sprint_two_hundred_forty_one_documents_update_set_user_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-241-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Legacy Update Set operator identity hygiene" in change_log
    assert "`JEDI_UPDATE_SET_USER_NAME`" in change_log
    assert "whitespace or control characters" in change_log
    assert "1 passed" in change_log
    assert "1590 passed, 93.91% coverage" in change_log
    assert "Production startup validation rejects `JEDI_UPDATE_SET_USER_NAME`" in (operator_guide)
    assert "because the value is audit metadata" in operator_guide


def test_sprint_two_hundred_forty_two_documents_build_claim_state_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-242-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Build claim state value hygiene" in change_log
    assert "`JEDI_BUILD_CLAIM_FROM_STATE`" in change_log
    assert "`JEDI_BUILD_CLAIM_STATE`" in change_log
    assert "empty, padded, or control-character" in change_log
    assert "1 passed" in change_log
    assert "1592 passed, 93.92% coverage" in change_log
    assert "startup validation rejects empty, padded, or control-character build claim" in (
        operator_guide
    )


def test_sprint_two_hundred_forty_three_documents_worker_id_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-243-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Worker identity audit hygiene" in change_log
    assert "`JEDI_WORKER_ID`" in change_log
    assert "locked_by" in change_log
    assert "empty, padded, or control-character" in change_log
    assert "1 passed" in change_log
    assert "1594 passed, 93.92% coverage" in change_log
    assert "`JEDI_WORKER_ID` is stored in PostgreSQL lock and job-event metadata" in (
        operator_guide
    )
    assert "operational audit evidence remain printable and unambiguous" in operator_guide


def test_sprint_two_hundred_forty_four_documents_public_web_allowlist_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-244-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Public web allowlist domain hygiene" in change_log
    assert "`JEDI_PUBLIC_WEB_ALLOWED_DOMAINS`" in change_log
    assert "non-local hostnames without padding" in change_log
    assert "1 passed" in change_log
    assert "1596 passed, 93.93% coverage" in change_log
    assert "allowed domains must be non-local hostnames without padding" in operator_guide


def test_sprint_two_hundred_forty_five_documents_audit_root_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-245-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Audit root path hygiene" in change_log
    assert "`JEDI_AUDIT_ROOT`" in change_log
    assert "absolute path" in change_log
    assert "relative working directory" in change_log
    assert "1 passed" in change_log
    assert "1598 passed, 93.93% coverage" in change_log
    assert "requires an absolute `JEDI_AUDIT_ROOT` path" in operator_guide
    assert "must not depend on a relative working directory" in operator_guide


def test_sprint_two_hundred_forty_six_documents_retention_interval_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-246-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retention prune interval hygiene" in change_log
    assert "`JEDI_RETENTION_PRUNE_INTERVAL_SECONDS`" in change_log
    assert "greater than zero" in change_log
    assert "continuous retention maintenance loop" in change_log
    assert "1 passed" in change_log
    assert "1600 passed, 93.94% coverage" in change_log
    assert "`JEDI_RETENTION_PRUNE_INTERVAL_SECONDS` must be greater than zero" in (operator_guide)


def test_sprint_two_hundred_forty_seven_documents_worker_idle_sleep_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-247-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Worker idle sleep loop hygiene" in change_log
    assert "`JEDI_WORKER_IDLE_SLEEP_SECONDS=0`" in change_log
    assert "`JEDI_WORKER_MAX_ITERATIONS`" in change_log
    assert "tight polling loop" in change_log
    assert "1 passed" in change_log
    assert "1602 passed, 93.94% coverage" in change_log
    assert "`JEDI_WORKER_IDLE_SLEEP_SECONDS=0` is valid only for bounded smoke runs" in (
        operator_guide
    )
    assert "Unbounded workers must use a positive idle sleep interval" in operator_guide


def test_sprint_two_hundred_forty_eight_documents_worker_max_iteration_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-248-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Worker max iteration hygiene" in change_log
    assert "`JEDI_WORKER_MAX_ITERATIONS=0`" in change_log
    assert "greater than zero" in change_log
    assert "silently start and exit" in change_log
    assert "1 passed" in change_log
    assert "2 passed" in change_log
    assert "All checks passed!" in change_log
    assert "Success: no issues found in 174 source files" in change_log
    assert "322 passed" in change_log
    assert "1604 passed" in change_log
    assert "Total coverage: 93.94%" in change_log
    assert "`JEDI_WORKER_MAX_ITERATIONS` is optional" in operator_guide
    assert "When set, it must be greater than zero" in operator_guide


def test_sprint_two_hundred_forty_nine_documents_public_web_worker_limit_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-249-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Public web worker limit hygiene" in change_log
    assert "`JEDI_PUBLIC_WEB_ACCESS=worker`" in change_log
    assert "`JEDI_PUBLIC_WEB_TIMEOUT_SECONDS`" in change_log
    assert "`JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES`" in change_log
    assert "`JEDI_PUBLIC_WEB_MAX_EXCERPT_CHARS`" in change_log
    assert "`JEDI_PUBLIC_WEB_MAX_RESULTS`" in change_log
    assert "settings-load time" in change_log
    assert "empty public-documentation context" in change_log
    assert "2 passed" in change_log
    assert "1 passed" in change_log
    assert "All checks passed!" in change_log
    assert "Success: no issues found in 174 source files" in change_log
    assert "323 passed" in change_log
    assert "1606 passed" in change_log
    assert "Total coverage: 93.95%" in change_log
    assert "When worker public documentation retrieval is enabled" in operator_guide
    assert "must be greater than zero at settings-load time" in operator_guide


def test_sprint_two_hundred_fifty_documents_runtime_boolean_parsing_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-250-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime boolean parsing hygiene" in change_log
    assert "`JEDI_BUILD_CLAIM_APPLY`" in change_log
    assert "`JEDI_STRICT_TRANSPORT_SECURITY_ENABLED`" in change_log
    assert "`JEDI_ALERT_WEBHOOK_ENABLED`" in change_log
    assert "`JEDI_UPDATE_SET_APPLY`" in change_log
    assert "`JEDI_CLASSIFIER_GATE`" in change_log
    assert "strict boolean parsing" in change_log
    assert "silently treated as false" in change_log
    assert "10 passed" in change_log
    assert "All checks passed!" in change_log
    assert "Success: no issues found in 174 source files" in change_log
    assert "324 passed" in change_log
    assert "1612 passed" in change_log
    assert "Total coverage: 93.95%" in change_log
    assert "Runtime boolean environment values are strict" in operator_guide
    assert "`true`, `false`, `1`, `0`, `yes`, `no`, `on`, or `off`" in operator_guide
    assert "fail settings loading instead of being silently treated as false" in operator_guide


def test_sprint_two_hundred_fifty_one_documents_worker_boolean_parsing_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-251-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Worker boolean parsing hygiene" in change_log
    assert "`JEDI_WORKER_STOP_ON_FAILURE`" in change_log
    assert "`JEDI_STALE_JOB_REQUEUE_ENABLED`" in change_log
    assert "strict boolean parsing" in change_log
    assert "silently treated as false" in change_log
    assert "5 passed" in change_log
    assert "All checks passed!" in change_log
    assert "Success: no issues found in 174 source files" in change_log
    assert "325 passed" in change_log
    assert "1614 passed" in change_log
    assert "Total coverage: 93.95%" in change_log
    assert "Worker boolean environment values are strict" in operator_guide
    assert "`JEDI_WORKER_STOP_ON_FAILURE` and" in operator_guide
    assert "`JEDI_STALE_JOB_REQUEUE_ENABLED` accept only" in operator_guide
    assert "`true`, `false`, `1`, `0`, `yes`, `no`, `on`, or" in operator_guide
    assert "fail worker settings loading instead of being silently" in operator_guide


def test_sprint_two_hundred_fifty_two_documents_runtime_numeric_parsing_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-252-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime numeric parsing hygiene" in change_log
    assert "malformed integer values" in change_log
    assert "`JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS`" in change_log
    assert "`JEDI_PUBLIC_WEB_TIMEOUT_SECONDS`" in change_log
    assert "`RuntimeConfigError` with the setting name" in change_log
    assert "setting-specific diagnostics" in change_log
    assert "18 passed" in change_log
    assert "All checks passed!" in change_log
    assert "Success: no issues found in 174 source files" in change_log
    assert "326 passed" in change_log
    assert "1630 passed" in change_log
    assert "Total coverage: 93.95%" in change_log
    assert "Runtime numeric environment values are strict" in operator_guide
    assert "must parse as ASCII base-10 digits only" in operator_guide
    assert "must parse as finite numbers" in operator_guide
    assert "fail settings loading with the setting name" in operator_guide


def test_sprint_two_hundred_fifty_three_documents_worker_numeric_parsing_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-253-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Worker numeric parsing hygiene" in change_log
    assert "`JEDI_WORKER_MAX_ITERATIONS`" in change_log
    assert "`JEDI_STALE_JOB_REQUEUE_BATCH_SIZE`" in change_log
    assert "`JEDI_WORKER_IDLE_SLEEP_SECONDS`" in change_log
    assert "`JEDI_RETENTION_PRUNE_INTERVAL_SECONDS`" in change_log
    assert "`JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS`" in change_log
    assert "setting-specific errors" in change_log
    assert "stable diagnostics" in change_log
    assert "5 passed" in change_log
    assert "All checks passed!" in change_log
    assert "Success: no issues found in 174 source files" in change_log
    assert "327 passed" in change_log
    assert "1632 passed" in change_log
    assert "Total coverage: 93.95%" in change_log
    assert "Worker numeric environment values are strict" in operator_guide
    assert "`JEDI_WORKER_MAX_ITERATIONS` and" in operator_guide
    assert "`JEDI_STALE_JOB_REQUEUE_BATCH_SIZE` must parse as ASCII base-10 digits only" in (
        operator_guide
    )
    assert "`JEDI_WORKER_IDLE_SLEEP_SECONDS`" in operator_guide
    assert "Malformed values fail worker settings loading with the setting name" in (operator_guide)


def test_sprint_two_hundred_fifty_four_documents_runtime_enum_parsing_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-254-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime enum parsing hygiene" in change_log
    assert "`JEDI_ADMIN_AUTH_MODE`" in change_log
    assert "`JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE`" in change_log
    assert "`JEDI_PUBLIC_WEB_ACCESS`" in change_log
    assert "`RuntimeConfigError` with the setting name and allowed values" in change_log
    assert "7 passed" in change_log
    assert "success with 174 source files" in change_log
    assert "1636 passed with 93.96% total coverage" in change_log
    assert "Runtime enum environment values are strict" in operator_guide
    assert "`JEDI_ADMIN_AUTH_MODE` accepts only" in operator_guide
    assert "`JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE` accepts only" in operator_guide
    assert "`JEDI_PUBLIC_WEB_ACCESS` accepts only" in operator_guide
    assert "allowed values instead of surfacing raw model validation errors" in (operator_guide)


def test_sprint_two_hundred_fifty_five_documents_runtime_environment_mode_guard() -> None:
    change_log = Path("docs/sprints/sprint-255-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime Environment Mode Guard" in change_log
    assert "`JEDI_ENVIRONMENT`" in change_log
    assert "silently skipping production validation" in change_log
    assert "accepts only `development` or `production`" in change_log
    assert "`RuntimeConfigError` naming `JEDI_ENVIRONMENT`" in change_log
    assert "4 passed" in change_log
    assert "all checks passed" in change_log
    assert "success with 174 source files" in change_log
    assert "329 passed" in change_log
    assert "1639 passed with 93.96% total coverage" in change_log
    assert "`JEDI_ENVIRONMENT` is a strict runtime mode switch" in operator_guide
    assert "accepts only `development` or `production`" in operator_guide
    assert "stores the normalized lowercase value" in operator_guide
    assert "production startup validation cannot be bypassed" in operator_guide


def test_sprint_two_hundred_fifty_six_documents_non_finite_float_settings_guard() -> None:
    change_log = Path("docs/sprints/sprint-256-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Non-Finite Float Settings Guard" in change_log
    assert "`nan`, `inf`, and `-inf`" in change_log
    assert "`JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS`" in change_log
    assert "`JEDI_PUBLIC_WEB_TIMEOUT_SECONDS`" in change_log
    assert "`JEDI_WORKER_IDLE_SLEEP_SECONDS`" in change_log
    assert "`JEDI_RETENTION_PRUNE_INTERVAL_SECONDS`" in change_log
    assert "`JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS`" in change_log
    assert "setting-specific errors" in change_log
    assert "7 passed" in change_log
    assert "all checks passed" in change_log
    assert "success with 174 source files" in change_log
    assert "330 passed" in change_log
    assert "1643 passed with 93.97% total coverage" in change_log
    assert "must parse as finite numbers" in operator_guide
    assert "non-finite values such as `nan`, `inf`, and `-inf` are rejected" in (operator_guide)


def test_sprint_two_hundred_fifty_seven_documents_public_web_csv_padding_guard() -> None:
    change_log = Path("docs/sprints/sprint-257-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Public Web CSV Padding Guard" in change_log
    assert "`JEDI_PUBLIC_WEB_ALLOWED_DOMAINS`" in change_log
    assert "`JEDI_PUBLIC_WEB_DOC_URLS`" in change_log
    assert "silently normalized" in change_log
    assert "preserve non-empty entries verbatim" in change_log
    assert "8 passed" in change_log
    assert "all checks passed" in change_log
    assert "success with 174 source files" in change_log
    assert "331 passed" in change_log
    assert "1645 passed with 93.97% total coverage" in change_log
    assert "Comma-separated public-web allowlist" in operator_guide
    assert "preserve interior padding for" in operator_guide
    assert "fail production validation" in operator_guide
    assert "instead of being silently normalized" in operator_guide


def test_sprint_two_hundred_fifty_eight_documents_servicenow_http_error_bounds() -> None:
    change_log = Path("docs/sprints/sprint-258-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow HTTP Error Diagnostic Bounds" in change_log
    assert "large non-JSON HTTP error bodies" in change_log
    assert "large string values inside JSON HTTP error bodies" in change_log
    assert "recursive diagnostic bounding" in change_log
    assert "truncation marker" in change_log
    assert "14 passed" in change_log
    assert "all checks passed" in change_log
    assert "success with 174 source files" in change_log
    assert "332 passed" in change_log
    assert "1648 passed with 93.95% total coverage" in change_log
    assert "ServiceNow HTTP error diagnostics are bounded" in operator_guide
    assert "Plain-text error bodies and string values inside JSON error bodies" in (operator_guide)
    assert "unbounded operator diagnostics" in operator_guide


def test_sprint_two_hundred_fifty_nine_documents_servicenow_success_body_bound() -> None:
    change_log = Path("docs/sprints/sprint-259-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow Successful Response Body Bound" in change_log
    assert "large upstream success payloads" in change_log
    assert "oversized successful response bodies raise `ServiceNowApiError`" in change_log
    assert "10 MiB plus one sentinel byte" in change_log
    assert "6 passed" in change_log
    assert "7 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 174 source files" in change_log
    assert "333 passed" in change_log
    assert "1650 passed" in change_log
    assert "total coverage 93.95%" in change_log
    assert "Successful ServiceNow response bodies are also bounded" in operator_guide
    assert "10 MiB plus one sentinel byte" in operator_guide
    assert "rejects oversized successful responses" in operator_guide


def test_sprint_two_hundred_sixty_documents_servicenow_http_error_body_read_bound() -> None:
    change_log = Path("docs/sprints/sprint-260-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow HTTP Error Body Read Bound" in change_log
    assert "10 MiB plus one sentinel byte cap" in change_log
    assert "no longer calls `read(-1)`" in change_log
    assert "compact oversized-body diagnostic" in change_log
    assert "smaller JSON and non-JSON HTTP error responses" in change_log
    assert "6 passed" in change_log
    assert "7 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 2 source files" in change_log
    assert "no issues found in 174 source files" in change_log
    assert "334 passed" in change_log
    assert "1652 passed" in change_log
    assert "total coverage 93.95%" in change_log
    assert "ServiceNow HTTP error response reads are also bounded" in operator_guide
    assert "10 MiB plus one sentinel byte from HTTP error responses" in operator_guide
    assert "large upstream error cannot create unbounded memory pressure" in operator_guide


def test_sprint_two_hundred_sixty_one_documents_lifecycle_streaming_body_bound() -> None:
    change_log = Path("docs/sprints/sprint-261-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Lifecycle Webhook Streaming Body Bound" in change_log
    assert "bounded streaming helper instead of `request.body()`" in change_log
    assert "oversized lifecycle stream is rejected with `413`" in change_log
    assert "parse JSON from the already-bounded byte buffer" in change_log
    assert "one authoritative path" in change_log
    assert "4 passed" in change_log
    assert "5 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 2 source files" in change_log
    assert "no issues found in 174 source files" in change_log
    assert "335 passed" in change_log
    assert "1654 passed" in change_log
    assert "total coverage 93.96%" in change_log
    assert "receiver enforces this while streaming the request body" in operator_guide
    assert "before JSON parsing, HMAC validation" in operator_guide
    assert "operational-store writes" in operator_guide


def test_sprint_two_hundred_sixty_two_documents_admin_streaming_body_bound() -> None:
    change_log = Path("docs/sprints/sprint-262-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin Diagnostic Streaming Body Bound" in change_log
    assert "actual streamed request body" in change_log
    assert "without `Content-Length` returns `413`" in change_log
    assert "read and replay a bounded body" in change_log
    assert "before auth, artifact, job, or list handlers" in change_log
    assert "missing or misleading length headers" in change_log
    assert "4 passed" in change_log
    assert "5 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 2 source files" in change_log
    assert "no issues found in 174 source files" in change_log
    assert "336 passed" in change_log
    assert "1656 passed" in change_log
    assert "total coverage 93.96%" in change_log
    assert "validates" in operator_guide
    assert "both declared `Content-Length` and the actual streamed body" in operator_guide
    assert "do not bypass the cap" in operator_guide


def test_sprint_two_hundred_sixty_three_documents_attachment_upload_size_guard() -> None:
    change_log = Path("docs/sprints/sprint-263-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow Attachment Upload Size Guard" in change_log
    assert "10 MiB file-size cap" in change_log
    assert "before reading file contents into memory" in change_log
    assert "before any OAuth token request or Attachment API upload" in change_log
    assert "`MAX_ATTACHMENT_UPLOAD_BYTES`" in change_log
    assert "existing binary attachment upload behavior" in change_log
    assert "3 passed" in change_log
    assert "4 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 2 source files" in change_log
    assert "no issues found in 174 source files" in change_log
    assert "337 passed" in change_log
    assert "1658 passed" in change_log
    assert "total coverage 93.96%" in change_log
    assert "ServiceNow story attachment uploads are bounded before file contents are read" in (
        operator_guide
    )
    assert "larger than 10 MiB before OAuth token acquisition" in operator_guide
    assert "unbounded memory pressure during attachment handoff" in operator_guide


def test_sprint_two_hundred_sixty_four_documents_delivery_handoff_streaming_hashes() -> None:
    change_log = Path("docs/sprints/sprint-264-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Delivery Handoff Streaming Hashes" in change_log
    assert "streams files in bounded chunks" in change_log
    assert "`Path.read_bytes()`" in change_log
    assert "does not require a whole-file read" in change_log
    assert "reviewed delivery artifact job creation" in change_log
    assert "64-character SHA-256 output" in change_log
    assert "3 passed" in change_log
    assert "4 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 2 source files" in change_log
    assert "no issues found in 174 source files" in change_log
    assert "338 passed" in change_log
    assert "1660 passed" in change_log
    assert "total coverage 93.97%" in change_log
    assert "Delivery handoff SHA-256 values are calculated with streaming file reads" in (
        operator_guide
    )
    assert "hash artifacts in bounded chunks" in operator_guide
    assert "loading the entire artifact into memory" in operator_guide


def test_sprint_two_hundred_sixty_five_documents_xml_validation() -> None:
    change_log = Path("docs/sprints/sprint-265-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Reviewed Update Set XML Bounded Validation" in change_log
    assert "bounded binary scans instead of `Path.read_text()`" in change_log
    assert "whole-file text read" in change_log
    assert "smoke placeholder XML is rejected" in change_log
    assert "empty unload XML fails closed" in change_log
    assert "must contain a `sys_update_xml` customer update marker" in change_log
    assert "bounded scan window" in change_log
    assert "5 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 174 source files" in change_log
    assert "339 passed" in change_log
    assert "1662 passed" in change_log
    assert "total coverage 93.97%" in change_log
    assert "Reviewed Update Set XML validation is bounded" in operator_guide
    assert "without calling `Path.read_text()`" in operator_guide
    assert "loading the entire XML payload into memory" in operator_guide


def test_sprint_two_hundred_sixty_six_documents_shared_streaming_hashes() -> None:
    change_log = Path("docs/sprints/sprint-266-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Shared Streaming Artifact Hashes" in change_log
    assert "shared artifact SHA-256 helper" in change_log
    assert "streams files in bounded chunks" in change_log
    assert "`Path.read_bytes()`" in change_log
    assert "lifecycle manifest hashing" in change_log
    assert "intake feedback artifact hashing" in change_log
    assert "delivery attachment dry-run hash verification" in change_log
    assert "64-character SHA-256 output" in change_log
    assert "5 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 8 source files" in change_log
    assert "no issues found in 174 source files" in change_log
    assert "340 passed" in change_log
    assert "1666 passed" in change_log
    assert "total coverage 93.97%" in change_log
    assert "Artifact SHA-256 values are calculated with streaming file reads" in (operator_guide)
    assert "lifecycle manifest artifact references" in operator_guide
    assert "intake feedback artifact references" in operator_guide
    assert "delivery attachment hash verification" in operator_guide
    assert "shared artifact hash helper" in operator_guide


def test_sprint_two_hundred_sixty_seven_documents_bounded_cli_json_input() -> None:
    change_log = Path("docs/sprints/sprint-267-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Bounded CLI JSON Input" in change_log
    assert "shared CLI JSON input limit of 10 MiB" in change_log
    assert "bounded binary read" in change_log
    assert "`Path.read_text()`" in change_log
    assert "provider responses" in change_log
    assert "implementation candidate jobs" in change_log
    assert "sample stories" in change_log
    assert "writeback job files" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "4 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 4 source files" in change_log
    assert "no issues found in 175 source files" in change_log
    assert "341 passed" in change_log
    assert "1669 passed" in change_log
    assert "total coverage 94.00%" in change_log
    assert "CLI JSON input files are bounded before parsing" in operator_guide
    assert "shared JSON loader" in operator_guide
    assert "larger than 10 MiB" in operator_guide
    assert "`json_input_too_large`" in operator_guide


def test_sprint_two_hundred_sixty_eight_documents_bounded_env_file_input() -> None:
    change_log = Path("docs/sprints/sprint-268-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Bounded Env File Input" in change_log
    assert "shared `.env` input limit of 1 MiB" in change_log
    assert "ServiceNow, runtime, and worker configuration loading" in change_log
    assert "bounded binary read" in change_log
    assert "`Path.read_text()`" in change_log
    assert "comments, blank lines, malformed lines, quote stripping" in change_log
    assert "ServiceNow OAuth key loading" in change_log
    assert "1 test failed before implementation" in change_log
    assert "3 passed" in change_log
    assert "4 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 175 source files" in change_log
    assert "342 passed" in change_log
    assert "1671 passed" in change_log
    assert "total coverage 94.00%" in change_log
    assert "Local `.env` files are bounded before parsing" in operator_guide
    assert "larger than 1 MiB" in operator_guide
    assert "`dotenv_input_too_large`" in operator_guide
    assert "before credential parsing" in operator_guide


def test_sprint_two_hundred_sixty_nine_documents_bounded_project_config_toml() -> None:
    change_log = Path("docs/sprints/sprint-269-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Bounded Project Config TOML Input" in change_log
    assert "1 MiB project config TOML input cap" in change_log
    assert "`Path.read_text()`" in change_log
    assert "bounded binary read before UTF-8 decode and TOML parsing" in change_log
    assert "`project_config_too_large`" in change_log
    assert "servicenow_instance_url" in change_log
    assert "artifact_dir" in change_log
    assert "target_boundary" in change_log
    assert "1 test failed before implementation" in change_log
    assert "3 passed" in change_log
    assert "4 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 175 source files" in change_log
    assert "343 passed" in change_log
    assert "1673 passed" in change_log
    assert "total coverage 94.01%" in change_log
    assert "Project TOML configuration files are also bounded before parsing" in (operator_guide)
    assert "larger than 1 MiB" in operator_guide
    assert "`project_config_too_large`" in operator_guide


def test_sprint_two_hundred_seventy_documents_openai_diagnostic_bounds() -> None:
    change_log = Path("docs/sprints/sprint-270-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "OpenAI Provider Diagnostic Redaction Bounds" in change_log
    assert "shared diagnostic redactor" in change_log
    assert "configured OpenAI API key is removed" in change_log
    assert "capped at 4096 characters" in change_log
    assert "`...[truncated]`" in change_log
    assert "Structured OpenAI error `type` and `code` fields remain visible" in (change_log)
    assert "secret-bearing oversized OpenAI error details" in change_log
    assert "1 test failed before implementation" in change_log
    assert "7 passed" in change_log
    assert "8 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 175 source files" in change_log
    assert "344 passed" in change_log
    assert "1675 passed" in change_log
    assert "total coverage 94.00%" in change_log
    assert "OpenAI provider error diagnostics are redacted and bounded" in (operator_guide)
    assert "configured API key is removed" in operator_guide
    assert "capped at 4096 characters" in operator_guide
    assert "preserving structured OpenAI `type` and `code` fields" in operator_guide


def test_sprint_two_hundred_seventy_one_documents_anthropic_diagnostic_bounds() -> None:
    change_log = Path("docs/sprints/sprint-271-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Anthropic Provider Diagnostic Redaction Bounds" in change_log
    assert "shared diagnostic redactor" in change_log
    assert "configured Anthropic API key is removed" in change_log
    assert "free-form API error message text is capped" in change_log
    assert "`type` and `request_id` remain visible" in change_log
    assert "capped at 4096 characters" in change_log
    assert "`...[truncated]`" in change_log
    assert "secret-bearing oversized Anthropic error details" in change_log
    assert "1 test failed before implementation" in change_log
    assert "35 passed" in change_log
    assert "36 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 175 source files" in change_log
    assert "345 passed" in change_log
    assert "1677 passed" in change_log
    assert "total coverage 93.97%" in change_log
    assert "`ANTHROPIC_API_KEY`" in operator_guide
    assert "Anthropic provider error diagnostics follow the same boundary" in (operator_guide)
    assert "configured Anthropic API key is removed" in operator_guide
    assert "free-form message text is capped before structured metadata" in (operator_guide)
    assert "preserving structured Anthropic `type` and `request_id` fields" in (operator_guide)


def test_sprint_two_hundred_seventy_two_documents_anthropic_request_id_safety() -> None:
    change_log = Path("docs/sprints/sprint-272-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Anthropic Request ID Diagnostic Sanitization" in change_log
    assert "untrusted diagnostic data" in change_log
    assert "shared diagnostic redactor" in change_log
    assert "configured Anthropic API key" in change_log
    assert "replace control characters" in change_log
    assert "capped separately" in change_log
    assert "newline-bearing, cookie-shaped, secret-bearing" in change_log
    assert "1 test failed before implementation" in change_log
    assert "malformed upstream request id injected a newline" in change_log
    assert "36 passed" in change_log
    assert "37 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 175 source files" in change_log
    assert "346 passed" in change_log
    assert "1679 passed" in change_log
    assert "total coverage 93.96%" in change_log
    assert "upstream `request-id` header is treated as diagnostic data" in (operator_guide)
    assert "redacted, stripped of control characters, and bounded" in operator_guide


def test_sprint_two_hundred_seventy_three_documents_anthropic_stop_reason_safety() -> None:
    change_log = Path("docs/sprints/sprint-273-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Anthropic Stop Reason Diagnostic Sanitization" in change_log
    assert "untrusted successful-response metadata" in change_log
    assert "shared diagnostic redactor" in change_log
    assert "configured Anthropic API key" in change_log
    assert "replace control characters" in change_log
    assert "`...[truncated]`" in change_log
    assert "newline-bearing, secret-bearing, oversized" in change_log
    assert "1 test failed before implementation" in change_log
    assert "unexpected stop reason leaked the configured API key" in change_log
    assert "37 passed" in change_log
    assert "38 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 175 source files" in change_log
    assert "347 passed" in change_log
    assert "1681 passed" in change_log
    assert "total coverage 93.96%" in change_log
    assert "successful-response metadata is also treated as untrusted" in operator_guide
    assert "Unexpected `stop_reason` values are redacted" in operator_guide
    assert "malformed model metadata cannot inject log lines" in operator_guide


def test_sprint_two_hundred_seventy_four_documents_anthropic_retry_count_bound() -> None:
    change_log = Path("docs/sprints/sprint-274-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Anthropic Retry Count Bound" in change_log
    assert "bounded at construction time" in change_log
    assert "retry counts above five" in change_log
    assert "before any request can be sent" in change_log
    assert "`retry-after` handling remain intact" in change_log
    assert "30-second provider backoff cap" in change_log
    assert "unbounded `max_retries=6` value is rejected" in change_log
    assert "1 test failed before implementation" in change_log
    assert "`max_retries=6` was accepted" in change_log
    assert "38 passed" in change_log
    assert "39 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 175 source files" in change_log
    assert "348 passed" in change_log
    assert "1683 passed" in change_log
    assert "total coverage 93.96%" in change_log
    assert "Anthropic retry policy is bounded at provider construction" in (operator_guide)
    assert "above five" in operator_guide
    assert "unbounded synchronous retry loops" in operator_guide


def test_sprint_two_hundred_seventy_five_documents_provider_base_url_guard() -> None:
    change_log = Path("docs/sprints/sprint-275-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model Provider Base URL Control Character Guard" in change_log
    assert "OpenAI provider settings now reject `base_url` values" in change_log
    assert "Anthropic provider settings now reject `base_url` values" in change_log
    assert "before outbound request construction" in change_log
    assert "Custom model gateway endpoints remain supported" in change_log
    assert "newline-bearing provider base URLs" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "both adapters accepted newline-bearing provider base URLs" in change_log
    assert "47 passed" in change_log
    assert "48 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 5 source files" in change_log
    assert "no issues found in 175 source files" in change_log
    assert "349 passed" in change_log
    assert "1686 passed" in change_log
    assert "total coverage 93.95%" in change_log
    assert "OpenAI provider settings reject empty `api_key`, `model`, and `base_url` values" in (
        operator_guide
    )
    assert "raw or percent-encoded whitespace or control characters" in (operator_guide)
    assert "future gateway wiring" in operator_guide
    assert (
        "Anthropic provider settings also reject empty `api_key`, `model`, "
        "and `base_url` values" in operator_guide
    )
    assert "credential, model, and endpoint values must be non-empty single-token values" in (
        operator_guide
    )


def test_sprint_two_hundred_seventy_six_documents_provider_credential_guard() -> None:
    change_log = Path("docs/sprints/sprint-276-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model Provider Credential Control Character Guard" in change_log
    assert "OpenAI provider settings now reject `api_key` and `model`" in change_log
    assert "Anthropic provider settings now reject `api_key` and `model`" in change_log
    assert "before outbound request construction" in change_log
    assert "Existing provider `base_url` control-character guards remain intact" in (change_log)
    assert "newline-bearing provider credentials and model identifiers" in change_log
    assert "4 tests failed before implementation" in change_log
    assert "both adapters accepted newline-bearing provider credentials" in change_log
    assert "51 passed" in change_log
    assert "52 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 5 source files" in change_log
    assert "no issues found in 175 source files" in change_log
    assert "350 passed" in change_log
    assert "1691 passed" in change_log
    assert "total coverage 93.96%" in change_log
    assert "OpenAI provider settings reject empty `api_key`, `model`, and `base_url` values" in (
        operator_guide
    )
    assert "raw or percent-encoded whitespace or control characters" in (operator_guide)
    assert "malformed provider credentials, model identifiers, or endpoints" in (operator_guide)
    assert (
        "Anthropic provider settings also reject empty `api_key`, `model`, "
        "and `base_url` values" in operator_guide
    )
    assert "credential, model, and endpoint values must be non-empty single-token values" in (
        operator_guide
    )


def test_sprint_two_hundred_seventy_seven_documents_provider_empty_value_guard() -> None:
    change_log = Path("docs/sprints/sprint-277-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model Provider Empty Credential Guard" in change_log
    assert "OpenAI provider settings now reject empty `api_key` and `model`" in (change_log)
    assert "Anthropic provider settings now reject empty `api_key` and `model`" in (change_log)
    assert "before outbound request construction" in change_log
    assert "whitespace and control-character guards remain intact" in change_log
    assert "empty provider credentials and model identifiers" in change_log
    assert "4 tests failed before implementation" in change_log
    assert "both adapters accepted empty provider credentials" in change_log
    assert "55 passed" in change_log
    assert "56 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 5 source files" in change_log
    assert "no issues found in 175 source files" in change_log
    assert "351 passed" in change_log
    assert "1696 passed" in change_log
    assert "total coverage 93.96%" in change_log
    assert "OpenAI provider settings reject empty `api_key`, `model`, and `base_url` values" in (
        operator_guide
    )
    assert "missing or malformed provider credentials" in operator_guide
    assert (
        "Anthropic provider settings also reject empty `api_key`, `model`, "
        "and `base_url` values" in operator_guide
    )
    assert "non-empty single-token values suitable for transport construction" in (operator_guide)


def test_sprint_two_hundred_seventy_eight_documents_provider_empty_base_url_guard() -> None:
    change_log = Path("docs/sprints/sprint-278-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model Provider Empty Base URL Guard" in change_log
    assert "OpenAI provider settings now reject empty `base_url` values" in (change_log)
    assert "Anthropic provider settings now reject empty `base_url` values" in (change_log)
    assert "before outbound request construction" in change_log
    assert "empty credential/model and whitespace/control-character guards remain intact" in (
        change_log
    )
    assert "empty provider base URLs" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "both adapters accepted empty provider base URLs" in change_log
    assert "57 passed" in change_log
    assert "58 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 5 source files" in change_log
    assert "no issues found in 175 source files" in change_log
    assert "352 passed" in change_log
    assert "1699 passed" in change_log
    assert "total coverage 93.97%" in change_log
    assert "OpenAI provider settings reject empty `api_key`, `model`, and `base_url` values" in (
        operator_guide
    )
    assert "missing or malformed provider credentials, model identifiers, or endpoints" in (
        operator_guide
    )
    assert (
        "Anthropic provider settings also reject empty `api_key`, `model`, "
        "and `base_url` values" in operator_guide
    )
    assert "non-empty single-token values suitable for transport construction" in (operator_guide)


def test_sprint_two_hundred_seventy_nine_documents_provider_base_url_shape_guard() -> None:
    change_log = Path("docs/sprints/sprint-279-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model Provider Base URL Shape Guard" in change_log
    assert "shared model-provider base URL validator" in change_log
    assert "OpenAI and Anthropic adapters" in change_log
    assert "absolute HTTPS URLs with a hostname" in change_log
    assert "embedded credentials, query parameters, and fragments" in change_log
    assert "before outbound request construction" in change_log
    assert "empty-value and whitespace/control-character guards remain intact" in (change_log)
    assert "unsafe provider base URL shapes" in change_log
    assert "10 tests failed before implementation" in change_log
    assert "both adapters accepted unsafe provider base URL shapes" in change_log
    assert "67 passed" in change_log
    assert "68 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 6 source files" in change_log
    assert "no issues found in 176 source files" in change_log
    assert "353 passed" in change_log
    assert "1710 passed" in change_log
    assert "total coverage 93.97%" in change_log
    assert "Provider `base_url` values must be absolute HTTPS URLs" in operator_guide
    assert "no embedded credentials" in operator_guide
    assert "no query parameters" in operator_guide
    assert "no fragments" in operator_guide
    assert "missing or malformed provider credentials, model identifiers, or endpoints" in (
        operator_guide
    )


def test_sprint_two_hundred_eighty_documents_provider_encoded_url_control_guard() -> None:
    change_log = Path("docs/sprints/sprint-280-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model Provider Encoded URL Control Guard" in change_log
    assert "percent-encoded whitespace and control characters" in change_log
    assert "before URL parsing or outbound request construction" in change_log
    assert "encoded whitespace/control-character helper" in change_log
    assert "OpenAI and Anthropic provider settings" in change_log
    assert "encoded newline and tab sequences" in change_log
    assert "HTTPS, hostname, credential, query, and fragment guards remain intact" in (change_log)
    assert "encoded-control provider base URLs" in change_log
    assert "4 tests failed before implementation" in change_log
    assert "both adapters accepted encoded-control provider base URLs" in change_log
    assert "71 passed" in change_log
    assert "72 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 6 source files" in change_log
    assert "no issues found in 176 source files" in change_log
    assert "354 passed" in change_log
    assert "1715 passed" in change_log
    assert "total coverage 93.98%" in change_log
    assert "raw or percent-encoded whitespace or control characters" in (operator_guide)
    assert "Provider `base_url` values must be absolute HTTPS URLs" in operator_guide
    assert "no embedded credentials" in operator_guide
    assert "no query parameters" in operator_guide
    assert "no fragments" in operator_guide


def test_sprint_two_hundred_eighty_one_documents_provider_double_encoded_guard() -> None:
    change_log = Path("docs/sprints/sprint-281-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model Provider Double-Encoded URL Control Guard" in change_log
    assert "bounded multi-pass decoding" in change_log
    assert "existing three-pass limit" in change_log
    assert "OpenAI and Anthropic provider `base_url` settings" in change_log
    assert "double-encoded newline and tab sequences" in change_log
    assert "%250a" in change_log
    assert "%2509" in change_log
    assert "benign encoded values remain allowed" in change_log
    assert "single-encoded control-character" in change_log
    assert "double-encoded provider base URL controls" in change_log
    assert "4 tests failed and 4 passed before implementation" in change_log
    assert "accepted double-encoded provider base URL controls" in change_log
    assert "75 passed" in change_log
    assert "126 passed" in change_log
    assert "127 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 11 source files" in change_log
    assert "no issues found in 177 source files" in change_log
    assert "355 passed" in change_log
    assert "1723 passed" in change_log
    assert "total coverage 93.97%" in change_log
    assert "Encoded whitespace/control detection uses a bounded three-pass decode" in (
        operator_guide
    )
    assert "double-encoded newline and tab sequences cannot bypass" in operator_guide
    assert "provider endpoint guard" in operator_guide


def test_sprint_two_hundred_eighty_two_documents_provider_base_url_length_bound() -> None:
    change_log = Path("docs/sprints/sprint-282-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model Provider Base URL Length Bound" in change_log
    assert "`MAX_PROVIDER_BASE_URL_CHARS` bound of 2048 characters" in change_log
    assert "OpenAI and Anthropic provider `base_url` settings" in change_log
    assert "before decode, URL parsing, or outbound request construction" in (change_log)
    assert "encoded-control, HTTPS, hostname, credential, query, and fragment guards" in (
        change_log
    )
    assert "Custom provider gateways remain supported" in change_log
    assert "oversized provider base URLs" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "both adapters accepted oversized provider base URLs" in change_log
    assert "77 passed" in change_log
    assert "78 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 6 source files" in change_log
    assert "no issues found in 177 source files" in change_log
    assert "356 passed" in change_log
    assert "1726 passed" in change_log
    assert "total coverage 93.97%" in change_log
    assert "reject `base_url` values longer than 2048 characters" in operator_guide
    assert "custom anthropic gateways remain supported" in operator_guide.lower()
    assert "future gateway wiring" in operator_guide


def test_sprint_two_hundred_eighty_three_documents_provider_setting_length_bounds() -> None:
    change_log = Path("docs/sprints/sprint-283-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model Provider Credential and Model Length Bounds" in change_log
    assert "shared provider setting validators" in change_log
    assert "API keys and model identifiers" in change_log
    assert "`api_key` values now reject values longer than 4096 characters" in (change_log)
    assert "`model` values now reject values longer than 256 characters" in (change_log)
    assert "before transport construction" in change_log
    assert "before request construction" in change_log
    assert "OpenAI and Anthropic provider settings" in change_log
    assert "non-empty, single-token, and bounded credential/model validation" in (change_log)
    assert "base URL length, URL shape, encoded-control" in change_log
    assert "oversized provider API keys and model identifiers" in change_log
    assert "4 tests failed before implementation" in change_log
    assert "both adapters accepted oversized provider API keys" in change_log
    assert "81 passed" in change_log
    assert "85 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 7 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "357 passed" in change_log
    assert "1734 passed" in change_log
    assert "total coverage 93.98%" in change_log
    assert "reject `api_key` values longer than 4096 characters" in operator_guide
    assert "reject `model` values longer than 256 characters" in operator_guide
    assert "missing or malformed provider credentials, model identifiers, or endpoints" in (
        operator_guide
    )


def test_sprint_two_hundred_eighty_four_documents_anthropic_max_tokens_bound() -> None:
    change_log = Path("docs/sprints/sprint-284-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Anthropic Max Tokens Bound" in change_log
    assert "`MAX_ANTHROPIC_MAX_TOKENS` ceiling of 128000" in change_log
    assert "Direct `AnthropicProviderSettings` construction" in change_log
    assert "before request construction" in change_log
    assert "`ANTHROPIC_MAX_TOKENS` env parsing" in change_log
    assert "before returning provider settings" in change_log
    assert "non-numeric, and non-positive max-token validation remains intact" in (change_log)
    assert "oversized token budgets" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "direct and env-derived Anthropic settings accepted oversized" in (change_log)
    assert "58 passed" in change_log
    assert "59 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "358 passed" in change_log
    assert "1737 passed" in change_log
    assert "total coverage 93.98%" in change_log
    assert "Anthropic `max_tokens` is also bounded" in operator_guide
    assert "`ANTHROPIC_MAX_TOKENS` env parsing reject values above 128000" in (operator_guide)
    assert "before request construction" in operator_guide


def test_sprint_two_hundred_eighty_five_documents_anthropic_env_whitespace() -> None:
    change_log = Path("docs/sprints/sprint-285-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Anthropic Env Whitespace Fail-Closed" in change_log
    assert "rejects non-empty values with leading or trailing whitespace" in (change_log)
    assert "instead of silently trimming them" in change_log
    assert "`ANTHROPIC_API_KEY`" in change_log
    assert "`ANTHROPIC_MODEL`" in change_log
    assert "`ANTHROPIC_BASE_URL`" in change_log
    assert "`ANTHROPIC_MAX_TOKENS`" in change_log
    assert "Optional blank `ANTHROPIC_MODEL`" in change_log
    assert "use defaults" in change_log
    assert "malformed Anthropic env values were previously accepted" in change_log
    assert "4 tests failed before implementation" in change_log
    assert "malformed Anthropic env values were accepted after normalization" in (change_log)
    assert "62 passed" in change_log
    assert "63 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "359 passed" in change_log
    assert "1742 passed" in change_log
    assert "total coverage 93.95%" in change_log
    assert "Anthropic env parsing rejects non-empty" in operator_guide
    assert "leading or trailing whitespace instead of silently trimming" in (operator_guide)


def test_sprint_two_hundred_eighty_six_documents_openai_env_whitespace() -> None:
    change_log = Path("docs/sprints/sprint-286-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "OpenAI Env Whitespace Fail-Closed" in change_log
    assert "rejects non-empty values with leading or trailing whitespace" in (change_log)
    assert "instead of silently trimming them" in change_log
    assert "`OPENAI_API_KEY`" in change_log
    assert "`OPENAI_MODEL`" in change_log
    assert "Blank `OPENAI_API_KEY` and `OPENAI_MODEL` values" in change_log
    assert "same provider setting guards" in change_log
    assert "malformed OpenAI env values were previously accepted" in change_log
    assert "4 tests failed before implementation" in change_log
    assert "malformed OpenAI env values were accepted after normalization" in (change_log)
    assert "4 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "360 passed" in change_log
    assert "1747 passed" in change_log
    assert "total coverage 93.93%" in change_log
    assert "OpenAI env parsing rejects non-empty" in operator_guide
    assert "leading or trailing whitespace instead of silently trimming" in (operator_guide)


def test_sprint_two_hundred_eighty_seven_documents_openai_runtime_config_errors() -> None:
    change_log = Path("docs/sprints/sprint-287-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "OpenAI Runtime Provider Config Errors" in change_log
    assert "wraps direct `OpenAIProviderSettings` validation failures" in (change_log)
    assert "`RuntimeConfigError`" in change_log
    assert "`OPENAI_API_KEY`" in change_log
    assert "`OPENAI_MODEL`" in change_log
    assert "without including provider values" in change_log
    assert "fails before job claim" in change_log
    assert "raw provider validation errors" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "2 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "361 passed" in change_log
    assert "1750 passed" in change_log
    assert "total coverage 93.88%" in change_log
    assert "Worker-side OpenAI provider construction" in operator_guide
    assert "wraps direct provider setting validation failures" in operator_guide
    assert "prevents malformed direct `RuntimeSettings` wiring" in operator_guide


def test_sprint_two_hundred_eighty_eight_documents_model_provider_selector_whitespace() -> None:
    change_log = Path("docs/sprints/sprint-288-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model Provider Selector Whitespace Fail-Closed" in change_log
    assert "`JEDI_MODEL_PROVIDER` env parsing now rejects" in change_log
    assert "leading, trailing, or internal whitespace/control characters" in (change_log)
    assert "Blank `JEDI_MODEL_PROVIDER` values still behave as absent" in (change_log)
    assert "default no-model-calls posture" in change_log
    assert "accidentally activate `openai`" in change_log
    assert "malformed provider selector env values were previously accepted" in (change_log)
    assert "3 tests failed before implementation" in change_log
    assert "3 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "362 passed" in change_log
    assert "1754 passed" in change_log
    assert "total coverage 93.89%" in change_log
    assert "`JEDI_MODEL_PROVIDER` env parsing rejects non-empty values" in (operator_guide)
    assert "silently trimming them into an active provider selector" in (operator_guide)


def test_sprint_two_hundred_eighty_nine_documents_direct_model_provider_diagnostics() -> None:
    change_log = Path("docs/sprints/sprint-289-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Direct Model Provider Selector Diagnostics" in change_log
    assert "direct `RuntimeSettings.model_provider` values" in change_log
    assert "whitespace or control characters" in change_log
    assert "before checking supported providers" in change_log
    assert "Worker handler setup" in change_log
    assert "fixed `JEDI_MODEL_PROVIDER` diagnostic" in change_log
    assert "do not echo untrusted provider selector text" in change_log
    assert "raw selector text in runtime errors" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "2 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 4 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "363 passed" in change_log
    assert "1757 passed" in change_log
    assert "total coverage 93.89%" in change_log
    assert "Direct `RuntimeSettings` wiring follows the same provider-selector" in (operator_guide)
    assert "fixed `JEDI_MODEL_PROVIDER` diagnostic" in operator_guide
    assert "instead of echoing untrusted selector text" in operator_guide


def test_sprint_two_hundred_ninety_documents_model_provider_selector_bounds() -> None:
    change_log = Path("docs/sprints/sprint-290-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model Provider Selector Bounds" in change_log
    assert "`MAX_MODEL_PROVIDER_CHARS` bound of 256 characters" in change_log
    assert "Env parsing, production validation, and worker handler setup" in (change_log)
    assert "reject oversized provider selectors" in change_log
    assert "fixed `Unsupported JEDI_MODEL_PROVIDER` diagnostic" in change_log
    assert "arbitrary selector text" in change_log
    assert "oversized and unsupported provider selectors were previously reflected" in (change_log)
    assert "3 tests failed before implementation" in change_log
    assert "4 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 4 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "364 passed" in change_log
    assert "1762 passed" in change_log
    assert "total coverage 93.91%" in change_log
    assert "Provider selectors are bounded to 256 characters" in operator_guide
    assert "fixed `Unsupported JEDI_MODEL_PROVIDER` diagnostic" in operator_guide


def test_sprint_two_hundred_ninety_one_documents_runtime_enum_auth_mode_diagnostics() -> None:
    change_log = Path("docs/sprints/sprint-291-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime Enum Auth Mode Diagnostics" in change_log
    assert "Runtime enum env parsing now rejects non-empty values" in change_log
    assert "leading, trailing, or internal whitespace/control characters" in (change_log)
    assert "`JEDI_ADMIN_AUTH_MODE`" in change_log
    assert "`JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE`" in change_log
    assert "`JEDI_PUBLIC_WEB_ACCESS`" in change_log
    assert "malformed direct `RuntimeSettings.admin_auth_mode` values" in (change_log)
    assert "fixed diagnostic" in change_log
    assert "does not echo arbitrary mode text" in change_log
    assert "5 tests failed before implementation" in change_log
    assert "5 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 4 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "365 passed" in change_log
    assert "1768 passed" in change_log
    assert "total coverage 93.92%" in change_log
    assert "Non-empty enum values with leading, trailing, or internal" in (operator_guide)
    assert "Direct `RuntimeSettings.admin_auth_mode` wiring is validated" in (operator_guide)
    assert "not echoed into startup errors" in operator_guide


def test_sprint_two_hundred_ninety_two_documents_runtime_environment_switch() -> None:
    change_log = Path("docs/sprints/sprint-292-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime Environment Switch Fail-Closed" in change_log
    assert "`JEDI_ENVIRONMENT` env parsing now rejects non-empty values" in (change_log)
    assert "leading, trailing, or internal whitespace/control characters" in (change_log)
    assert "Case-insensitive `development` and `production`" in change_log
    assert "Direct `RuntimeSettings.runtime_environment` wiring" in change_log
    assert "before `validate_runtime_settings()` decides" in change_log
    assert "silently skipping production validation" in change_log
    assert "4 tests failed before implementation" in change_log
    assert "4 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "366 passed" in change_log
    assert "1773 passed" in change_log
    assert "total coverage 93.91%" in change_log
    assert "Non-empty values with leading, trailing, or internal" in operator_guide
    assert "Direct `RuntimeSettings.runtime_environment` wiring follows" in (operator_guide)
    assert "cannot silently downgrade a production runtime" in operator_guide


def test_sprint_two_hundred_ninety_three_documents_build_claim_state_load_guard() -> None:
    change_log = Path("docs/sprints/sprint-293-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Build Claim State Settings Load Guard" in change_log
    assert "`JEDI_BUILD_CLAIM_FROM_STATE`" in change_log
    assert "`JEDI_BUILD_CLAIM_STATE`" in change_log
    assert "non-empty, unpadded, and free of control characters" in change_log
    assert "Default build claim state values remain" in change_log
    assert "Existing production validation for direct `RuntimeSettings`" in (change_log)
    assert "padded and control-character build claim state env values" in (change_log)
    assert "3 tests failed before implementation" in change_log
    assert "3 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "367 passed" in change_log
    assert "1777 passed" in change_log
    assert "total coverage 93.92%" in change_log
    assert "Runtime settings loading rejects empty, padded, or control-character" in (
        operator_guide
    )
    assert "startup validation also rejects malformed direct build claim state values" in (
        operator_guide
    )


def test_sprint_two_hundred_ninety_four_documents_worker_id_load_guard() -> None:
    change_log = Path("docs/sprints/sprint-294-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Worker ID Settings Load Guard" in change_log
    assert "`JEDI_WORKER_ID`" in change_log
    assert "non-empty, unpadded, and free of control characters" in change_log
    assert "default worker id remains `jedi-devproject-worker`" in change_log
    assert "Existing production validation for direct `RuntimeSettings.worker_id`" in (change_log)
    assert "padded and control-character worker id env values" in change_log
    assert "3 tests failed before implementation" in change_log
    assert "4 passed after implementation" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "368 passed" in change_log
    assert "1781 passed, total coverage 93.92%" in change_log
    assert "Runtime settings loading rejects empty, padded, or control-character worker ids" in (
        operator_guide
    )
    assert "production startup validation applies the same boundary" in operator_guide


def test_sprint_two_hundred_ninety_five_documents_public_web_load_guard() -> None:
    change_log = Path("docs/sprints/sprint-295-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Public Web Settings Load Guard" in change_log
    assert "`JEDI_PUBLIC_WEB_ACCESS=worker`" in change_log
    assert "non-local hostnames" in change_log
    assert "HTTPS, allowlist-matched" in change_log
    assert "do not echo URL credentials or sensitive query values" in change_log
    assert "Existing direct `RuntimeSettings` production validation remains intact" in (change_log)
    assert "3 tests failed before implementation" in change_log
    assert "5 passed after implementation" in change_log
    assert "28 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "369 passed" in change_log
    assert "1785 passed, total coverage 93.89%" in change_log
    assert "Runtime settings loading rejects malformed public documentation retrieval settings" in (
        operator_guide
    )
    assert "fail before runtime settings are returned" in operator_guide
    assert "fail settings loading when" in operator_guide


def test_sprint_two_hundred_ninety_six_documents_admin_console_credential_load_guard() -> None:
    change_log = Path("docs/sprints/sprint-296-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin Console Credential Settings Load Guard" in change_log
    assert "`JEDI_ADMIN_CONSOLE_USERNAME`" in change_log
    assert "`JEDI_ADMIN_CONSOLE_PASSWORD`" in change_log
    assert "unpadded and free of control characters" in change_log
    assert "Blank or absent admin console credential values still behave as unconfigured" in (
        change_log
    )
    assert "do not echo credential fragments" in change_log
    assert "Existing production validation still rejects `JEDI_ADMIN_AUTH_MODE=dev_basic`" in (
        change_log
    )
    assert "3 tests failed before implementation" in change_log
    assert "4 passed after implementation" in change_log
    assert "34 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "370 passed" in change_log
    assert "1789 passed, total coverage 93.90%" in change_log
    assert (
        "Development Basic-auth console credentials are validated during runtime settings loading"
        in operator_guide
    )
    assert "`JEDI_ADMIN_CONSOLE_USERNAME` and `JEDI_ADMIN_CONSOLE_PASSWORD`" in (operator_guide)
    assert "constant-time credential" in operator_guide
    assert "fail-closed" in operator_guide


def test_sprint_two_hundred_ninety_seven_documents_admin_api_token_load_guard() -> None:
    change_log = Path("docs/sprints/sprint-297-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin API Token Settings Load Guard" in change_log
    assert "`JEDI_ADMIN_API_TOKEN`" in change_log
    assert "unpadded and free of control characters" in change_log
    assert "Blank or absent admin API token values still behave as unconfigured" in (change_log)
    assert "do not echo token fragments" in change_log
    assert "minimum 32-character admin API token strength requirement" in change_log
    assert "3 tests failed before implementation" in change_log
    assert "4 passed after implementation" in change_log
    assert "11 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "371 passed" in change_log
    assert "1793 passed, total coverage 93.90%" in change_log
    assert (
        "Runtime settings loading rejects padded or control-character `JEDI_ADMIN_API_TOKEN`"
        in operator_guide
    )
    assert "configured admin bearer secrets cannot be" in operator_guide
    assert "fail-closed" in operator_guide


def test_sprint_two_hundred_ninety_eight_documents_lifecycle_secret_load_guard() -> None:
    change_log = Path("docs/sprints/sprint-298-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Lifecycle Webhook Secret Settings Load Guard" in change_log
    assert "`JEDI_LIFECYCLE_WEBHOOK_SECRET`" in change_log
    assert "unpadded and free of control characters" in change_log
    assert "Blank or absent lifecycle webhook secret values still behave as unconfigured" in (
        change_log
    )
    assert "do not echo secret fragments" in change_log
    assert "minimum 32-character HMAC secret" in change_log
    assert "3 tests failed before implementation" in change_log
    assert "3 passed after implementation" in change_log
    assert "9 passed" in change_log
    assert "10 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 4 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "372 passed" in change_log
    assert "1797 passed, total coverage 93.90%" in change_log
    assert (
        "Runtime settings loading rejects padded or control-character "
        "`JEDI_LIFECYCLE_WEBHOOK_SECRET`" in operator_guide
    )
    assert "lifecycle signing secrets cannot be silently normalized" in operator_guide
    assert "authenticated webhook modes fail-closed" in operator_guide


def test_sprint_two_hundred_ninety_nine_documents_servicenow_oauth_load_guard() -> None:
    change_log = Path("docs/sprints/sprint-299-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow OAuth Credential Settings Load Guard" in change_log
    assert "`SERVICENOW_PM_CLIENT_ID`" in change_log
    assert "`SERVICENOW_PM_CLIENT_SECRET`" in change_log
    assert "`SERVICENOW_DEV_CLIENT_ID`" in change_log
    assert "`SERVICENOW_DEV_CLIENT_SECRET`" in change_log
    assert "unpadded and free of control characters" in change_log
    assert "legacy single-instance fallback still works" in change_log
    assert "do not echo credential fragments" in change_log
    assert "Existing direct `RuntimeSettings` production validation remains intact" in (change_log)
    assert "4 tests failed before implementation" in change_log
    assert "5 passed after implementation" in change_log
    assert "226 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "373 passed" in change_log
    assert "1802 passed, total coverage 93.90%" in change_log
    assert "Runtime settings loading rejects padded or control-character ServiceNow OAuth" in (
        operator_guide
    )
    assert "legacy single-instance fallback is validated after it is resolved" in (operator_guide)
    assert "do not echo" in operator_guide


def test_sprint_three_hundred_documents_servicenow_instance_url_load_guard() -> None:
    change_log = Path("docs/sprints/sprint-300-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow Instance URL Settings Load Guard" in change_log
    assert "`SERVICENOW_PM_INSTANCE_URL`" in change_log
    assert "`SERVICENOW_DEV_INSTANCE_URL`" in change_log
    assert "HTTPS ServiceNow targets" in change_log
    assert "legacy single-instance fallback still works" in change_log
    assert "do not echo URL credentials, fragments, or encoded control values" in (change_log)
    assert "Existing direct `RuntimeSettings` production validation remains intact" in (change_log)
    assert "4 tests failed before implementation" in change_log
    assert "5 passed after implementation" in change_log
    assert "230 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "374 passed" in change_log
    assert "1807 passed, total coverage 93.90%" in change_log
    assert "Runtime settings loading also rejects malformed resolved ServiceNow instance URLs" in (
        operator_guide
    )
    assert "including values resolved from legacy `SERVICENOW_INSTANCE_URL` fallback" in (
        operator_guide
    )
    assert "do not echo URL credentials, fragments, or encoded control values" in (operator_guide)


def test_sprint_three_hundred_one_documents_runtime_numeric_load_guard() -> None:
    change_log = Path("docs/sprints/sprint-301-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime Numeric Settings Load Guard" in change_log
    assert "rejects padded or control-character env values" in change_log
    assert "base-10 integers without padding or control characters" in change_log
    assert "`JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS`" in change_log
    assert "`JEDI_PUBLIC_WEB_TIMEOUT_SECONDS`" in change_log
    assert "finite numbers without padding or control characters" in change_log
    assert "do not echo padded or control-character fragments" in change_log
    assert "Existing malformed numeric and non-finite float validation remains intact" in (
        change_log
    )
    assert "5 tests failed before implementation" in change_log
    assert "22 passed after implementation" in change_log
    assert "235 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "375 passed" in change_log
    assert "1813 passed, total coverage 93.91%" in change_log
    assert "Runtime numeric environment values are strict" in operator_guide
    assert "must parse as ASCII base-10 digits only without signs, underscores" in (operator_guide)
    assert "must parse as finite numbers without padding or control characters" in (operator_guide)
    assert "silently normalizing operator input" in operator_guide


def test_sprint_three_hundred_two_documents_worker_numeric_load_guard() -> None:
    change_log = Path("docs/sprints/sprint-302-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Worker Numeric Settings Load Guard" in change_log
    assert "rejects padded or control-character env values" in change_log
    assert "`JEDI_WORKER_MAX_ITERATIONS`" in change_log
    assert "`JEDI_STALE_JOB_REQUEUE_BATCH_SIZE`" in change_log
    assert "base-10 integers without padding or control characters" in change_log
    assert "`JEDI_WORKER_IDLE_SLEEP_SECONDS`" in change_log
    assert "`JEDI_RETENTION_PRUNE_INTERVAL_SECONDS`" in change_log
    assert "`JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS`" in change_log
    assert "finite numbers without padding or control characters" in change_log
    assert "do not echo padded or control-character fragments" in change_log
    assert "Existing malformed numeric, non-finite float, and non-positive worker validation" in (
        change_log
    )
    assert "1 test failed before implementation" in change_log
    assert "4 passed after implementation" in change_log
    assert "25 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "376 passed" in change_log
    assert "1815 passed, total coverage 93.91%" in change_log
    assert "Worker numeric environment values are strict" in operator_guide
    assert "`JEDI_STALE_JOB_REQUEUE_BATCH_SIZE` must parse as ASCII base-10 digits only" in (
        operator_guide
    )
    assert "must parse as finite numbers without padding or" in operator_guide
    assert "silently normalizing operator input" in operator_guide


def test_sprint_three_hundred_three_documents_retention_numeric_load_guard() -> None:
    change_log = Path("docs/sprints/sprint-303-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retention Numeric Settings Load Guard" in change_log
    assert "reject padded or control-character env values" in change_log
    assert "`JEDI_RETENTION_ARTIFACT_BLOB_DAYS`" in change_log
    assert "`JEDI_RETENTION_JOB_EVENT_DAYS`" in change_log
    assert "`JEDI_RETENTION_PRUNE_BATCH_SIZE`" in change_log
    assert "base-10 integers without padding or control characters" in change_log
    assert "whitespace-only values are rejected as padded operator input" in change_log
    assert "do not echo padded or control-character fragments" in change_log
    assert "Existing disabled-by-default, explicit-window, and non-positive retention" in (
        change_log
    )
    assert "1 test failed before implementation" in change_log
    assert "5 passed after implementation" in change_log
    assert "38 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "377 passed" in change_log
    assert "1817 passed, total coverage 93.90%" in change_log
    assert "Retention numeric values must parse as ASCII base-10 digits only" in (operator_guide)
    assert "empty values remain disabled" in operator_guide
    assert "whitespace-only or padded values fail retention policy loading" in operator_guide


def test_sprint_three_hundred_four_documents_runtime_boolean_load_guard() -> None:
    change_log = Path("docs/sprints/sprint-304-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime Boolean Settings Load Guard" in change_log
    assert "rejects padded or control-character env values" in change_log
    assert "`JEDI_BUILD_CLAIM_APPLY`" in change_log
    assert "`JEDI_STRICT_TRANSPORT_SECURITY_ENABLED`" in change_log
    assert "`JEDI_ALERT_WEBHOOK_ENABLED`" in change_log
    assert "`JEDI_UPDATE_SET_APPLY`" in change_log
    assert "`JEDI_CLASSIFIER_GATE`" in change_log
    assert "accepted boolean literals without padding or control characters" in change_log
    assert "whitespace-only or padded values are rejected as ambiguous operator input" in (
        change_log
    )
    assert "do not echo padded or control-character fragments" in change_log
    assert "Existing accepted boolean literals and malformed-boolean validation" in (change_log)
    assert "5 tests failed before implementation" in change_log
    assert "13 passed after implementation" in change_log
    assert "240 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "378 passed" in change_log
    assert "1823 passed, total coverage 93.90%" in change_log
    assert "Runtime boolean environment values are strict" in operator_guide
    assert "case-insensitively and without padding or control characters" in operator_guide
    assert "silently normalizing operator input" in operator_guide


def test_sprint_three_hundred_five_documents_worker_boolean_load_guard() -> None:
    change_log = Path("docs/sprints/sprint-305-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Worker Boolean Settings Load Guard" in change_log
    assert "rejects padded or control-character env values" in change_log
    assert "`JEDI_WORKER_STOP_ON_FAILURE`" in change_log
    assert "`JEDI_STALE_JOB_REQUEUE_ENABLED`" in change_log
    assert "accepted boolean literals without padding or control characters" in change_log
    assert "whitespace-only or padded values are rejected as ambiguous operator input" in (
        change_log
    )
    assert "do not echo padded or control-character fragments" in change_log
    assert "Existing accepted boolean literals and malformed-boolean validation" in (change_log)
    assert "1 test failed before implementation" in change_log
    assert "3 passed after implementation" in change_log
    assert "26 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "379 passed" in change_log
    assert "1825 passed, total coverage 93.91%" in change_log
    assert "Worker boolean environment values are strict" in operator_guide
    assert "`JEDI_STALE_JOB_REQUEUE_ENABLED` accept only" in operator_guide
    assert "case-insensitively and without padding or control characters" in operator_guide
    assert "silently normalizing operator input" in operator_guide


def test_sprint_three_hundred_six_documents_update_set_username_load_guard() -> None:
    change_log = Path("docs/sprints/sprint-306-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set Username Settings Load Guard" in change_log
    assert "`JEDI_UPDATE_SET_USER_NAME`" in change_log
    assert "non-empty, unpadded, and free of control characters" in change_log
    assert "Empty or absent values still behave as unconfigured" in change_log
    assert "do not echo padded or control-character fragments" in change_log
    assert "Existing direct `RuntimeSettings` production validation remains intact" in (change_log)
    assert "3 tests failed before implementation" in change_log
    assert "5 passed after implementation" in change_log
    assert "243 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "380 passed" in change_log
    assert "1829 passed, total coverage 93.91%" in change_log
    assert "Runtime settings loading rejects empty, padded, or control-character" in (
        operator_guide
    )
    assert "production startup validation rejects malformed direct values" in operator_guide
    assert "audit metadata" in operator_guide


def test_sprint_three_hundred_seven_documents_alert_webhook_url_load_guard() -> None:
    change_log = Path("docs/sprints/sprint-307-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert Webhook URL Settings Load Guard" in change_log
    assert "`JEDI_ALERT_WEBHOOK_URL`" in change_log
    assert "unpadded, free of control characters, HTTPS" in change_log
    assert "even when `JEDI_ALERT_WEBHOOK_ENABLED=false`" in change_log
    assert "Empty or absent `JEDI_ALERT_WEBHOOK_URL` values still behave as unconfigured" in (
        change_log
    )
    assert "do not echo padded, control-character, or credential fragments" in change_log
    assert "Existing delivery-time and production startup validation remains intact" in (change_log)
    assert "5 tests failed before implementation" in change_log
    assert "7 passed after implementation" in change_log
    assert "248 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "381 passed" in change_log
    assert "1835 passed, total coverage 93.88%" in change_log
    assert "Runtime settings loading rejects configured `JEDI_ALERT_WEBHOOK_URL`" in (
        operator_guide
    )
    assert "even when alert delivery is disabled" in operator_guide
    assert "dormant but unsafe alert sink configuration" in change_log


def test_sprint_three_hundred_eight_documents_split_servicenow_blank_override_guard() -> None:
    change_log = Path("docs/sprints/sprint-308-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Split ServiceNow Blank Override Guard" in change_log
    assert "`SERVICENOW_PM_INSTANCE_URL`" in change_log
    assert "`SERVICENOW_DEV_CLIENT_SECRET`" in change_log
    assert "must be real values when present" in change_log
    assert "legacy single-instance fallback by omitting split keys entirely" in change_log
    assert "cannot silently route PM story operations or DEV platform writes" in (change_log)
    assert "do not echo fallback URLs or credential fragments" in change_log
    assert "Existing split ServiceNow URL and OAuth credential validation remains intact" in (
        change_log
    )
    assert "3 tests failed before implementation" in change_log
    assert "13 passed after implementation" in change_log
    assert "252 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "382 passed" in change_log
    assert "1840 passed, total coverage 93.88%" in change_log
    assert "also rejects blank split ServiceNow overrides before fallback" in (operator_guide)
    assert "remove the split key entirely to use the legacy single-instance fallback" in (
        operator_guide
    )
    assert "wrong instance" in operator_guide


def test_sprint_three_hundred_nine_documents_dotenv_key_ambiguity_guard() -> None:
    change_log = Path("docs/sprints/sprint-309-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Dotenv Key Ambiguity Guard" in change_log
    assert "rejects duplicate assignment keys" in change_log
    assert "non-empty, unpadded, and free of whitespace or control characters" in (change_log)
    assert "Comments, blank lines, non-assignment lines" in change_log
    assert "do not echo secret values" in change_log
    assert "fixed `dotenv_invalid_key` error" in change_log
    assert "which ServiceNow target, credential, model provider" in change_log
    assert "5 tests failed before implementation" in change_log
    assert "8 passed after implementation" in change_log
    assert "60 passed" in change_log
    assert "no issues found in 2 source files" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "383 passed" in change_log
    assert "1846 passed, total coverage 93.89%" in change_log
    assert "Local `.env` assignment keys are strict" in operator_guide
    assert "Duplicate assignment keys are rejected with" in operator_guide
    assert "`dotenv_duplicate_key`" in operator_guide
    assert "last-value-wins behavior" in operator_guide


def test_sprint_three_hundred_ten_documents_dotenv_value_quote_guard() -> None:
    change_log = Path("docs/sprints/sprint-310-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Dotenv Value Quote Guard" in change_log
    assert "rejects unmatched or mixed boundary quotes" in change_log
    assert "Matching single-quoted and double-quoted values remain supported" in (change_log)
    assert "Unquoted values still use the existing trimmed value behavior" in change_log
    assert "`dotenv_invalid_value_quotes`" in change_log
    assert "do not echo configured secret values" in change_log
    assert "Duplicate-key, strict-key, comment" in change_log
    assert "silently changing ServiceNow credentials" in change_log
    assert "4 tests failed before implementation" in change_log
    assert "13 passed after implementation" in change_log
    assert "65 passed" in change_log
    assert "no issues found in 2 source files" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "384 passed" in change_log
    assert "1852 passed, total coverage 93.90%" in change_log
    assert "Local `.env` value quote handling is strict" in operator_guide
    assert "`dotenv_invalid_value_quotes`" in operator_guide
    assert "does not echo the configured value" in operator_guide


def test_sprint_three_hundred_eleven_documents_dotenv_key_syntax_guard() -> None:
    change_log = Path("docs/sprints/sprint-311-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Dotenv Key Syntax Guard" in change_log
    assert "shell-compatible uppercase environment variable names" in change_log
    assert "start with a letter or underscore" in change_log
    assert "only uppercase letters, digits, and underscores" in change_log
    assert "fixed `dotenv_invalid_key` diagnostic" in change_log
    assert "Duplicate-key, value-quote, comment" in change_log
    assert "typo-prone or shell-incompatible config keys" in change_log
    assert "4 tests failed before implementation" in change_log
    assert "17 passed after implementation" in change_log
    assert "69 passed" in change_log
    assert "no issues found in 2 source files" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "385 passed" in change_log
    assert "1857 passed, total coverage 93.90%" in change_log
    assert "shell-compatible uppercase" in operator_guide
    assert "start with a letter or underscore" in operator_guide
    assert "only uppercase" in operator_guide


def test_sprint_three_hundred_twelve_documents_project_config_value_hygiene() -> None:
    change_log = Path("docs/sprints/sprint-312-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Project Config Value Hygiene" in change_log
    assert "validates required values before returning `AppConfig`" in change_log
    assert "`servicenow_instance_url` must be an HTTPS ServiceNow URL" in change_log
    assert "`artifact_dir` and `target_boundary` must be unpadded" in change_log
    assert "Internal spaces remain allowed for `target_boundary`" in change_log
    assert "do not echo URL credentials or configured value fragments" in change_log
    assert "Existing required-setting validation and the 1 MiB bounded TOML read" in (change_log)
    assert "8 tests failed before implementation" in change_log
    assert "11 passed after implementation" in change_log
    assert "no issues found in 2 source files" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "386 passed" in change_log
    assert "1866 passed, total coverage 93.91%" in change_log
    assert "Required project config values are validated before `AppConfig`" in (operator_guide)
    assert "`servicenow_instance_url` must be an HTTPS ServiceNow URL" in operator_guide
    assert "Malformed project config diagnostics name the setting" in operator_guide


def test_sprint_three_hundred_thirteen_documents_runtime_store_audit_load_guard() -> None:
    change_log = Path("docs/sprints/sprint-313-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime Store and Audit Load Guard" in change_log
    assert "validates required `DATABASE_URL` and `JEDI_AUDIT_ROOT` values" in change_log
    assert "`DATABASE_URL` must be a PostgreSQL URL" in change_log
    assert "`JEDI_AUDIT_ROOT` must be an absolute path" in change_log
    assert "Production startup validation now reuses the same value-level" in change_log
    assert "do not echo database credentials or path fragments" in change_log
    assert "6 tests failed before implementation" in change_log
    assert "10 passed after implementation" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 2 source files" in change_log
    assert "7 passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "387 passed" in change_log
    assert "1873 passed, total coverage 93.91%" in change_log
    assert "Runtime settings loading validates the required store and audit boundary" in (
        operator_guide
    )
    assert "`DATABASE_URL` must be a PostgreSQL URL" in operator_guide
    assert "`JEDI_AUDIT_ROOT` must be an absolute path" in operator_guide
    assert "do not echo database credentials or path fragments" in operator_guide


def test_sprint_three_hundred_fourteen_documents_dormant_public_web_config_guard() -> None:
    change_log = Path("docs/sprints/sprint-314-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Dormant Public Web Config Guard" in change_log
    assert "validates configured public-web allowlist and documentation URL values" in (change_log)
    assert "`JEDI_PUBLIC_WEB_ACCESS` is disabled" in change_log
    assert "still does not require `JEDI_PUBLIC_WEB_ALLOWED_DOMAINS`" in change_log
    assert "non-local hostnames without padding" in change_log
    assert "credential-free, fragment-free" in change_log
    assert "do not echo URL credentials or sensitive query values" in change_log
    assert "3 tests failed before implementation" in change_log
    assert "8 passed after implementation" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 2 source files" in change_log
    assert "4 passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 179 source files" in change_log
    assert "388 passed" in change_log
    assert "1877 passed, total coverage 93.91%" in change_log
    assert "Runtime settings loading also validates configured public-web allowlist" in (
        operator_guide
    )
    assert "`JEDI_PUBLIC_WEB_ACCESS` is left disabled" in operator_guide
    assert "does not require `JEDI_PUBLIC_WEB_ALLOWED_DOMAINS`" in operator_guide
    assert "single feature-flag change" in operator_guide


def test_sprint_three_hundred_fifteen_documents_base10_integer_token_guard() -> None:
    change_log = Path("docs/sprints/sprint-315-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Base-10 Integer Token Guard" in change_log
    assert "one shared strict parser" in change_log
    assert "base-10 digits only" in change_log
    assert "signed values such as `+60`" in change_log
    assert "underscore-separated values such as `128_000`" in change_log
    assert "do not echo the configured numeric fragment" in change_log
    assert "4 tests failed before implementation" in change_log
    assert "23 passed after implementation" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 7 source files" in change_log
    assert "5 passed" in change_log
    assert "no issues found in 8 source files" in change_log
    assert "389 passed" in change_log
    assert "no issues found in 180 source files" in change_log
    assert "1882 passed, total coverage 93.91%" in change_log
    assert "ASCII base-10 digits only without signs, underscores" in operator_guide
    assert "Retention numeric values must parse as ASCII base-10 digits only" in (operator_guide)
    assert "`JEDI_STALE_JOB_REQUEUE_BATCH_SIZE` must parse as ASCII base-10 digits only" in (
        operator_guide
    )


def test_sprint_three_hundred_sixteen_documents_ascii_integer_token_guard() -> None:
    change_log = Path("docs/sprints/sprint-316-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ASCII Integer Token Guard" in change_log
    assert "requires ASCII base-10 digits only" in change_log
    assert "full-width `１２`" in change_log
    assert "Arabic-Indic `١٢`" in change_log
    assert "do not echo the configured numeric fragment" in change_log
    assert "4 tests failed before implementation" in change_log
    assert "10 passed after implementation" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 5 source files" in change_log
    assert "8 passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "390 passed" in change_log
    assert "no issues found in 181 source files" in change_log
    assert "1889 passed, total coverage 93.91%" in change_log
    assert "ASCII base-10 digits only without signs, underscores" in operator_guide
    assert "Runtime numeric environment values are strict" in operator_guide


def test_sprint_three_hundred_seventeen_documents_fixed_ascii_float_token_guard() -> None:
    change_log = Path("docs/sprints/sprint-317-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Fixed ASCII Float Token Guard" in change_log
    assert "fixed ASCII decimal numbers" in change_log
    assert "signs, underscores, exponent notation" in change_log
    assert "non-ASCII decimal digits are rejected" in change_log
    assert "do not echo the configured numeric fragment" in change_log
    assert "failed before implementation because the shared parser did not exist" in change_log
    assert "JEDI_WORKER_IDLE_SLEEP_SECONDS=1_000.5` was accepted" in change_log
    assert "29 passed after implementation" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 6 source files" in change_log
    assert "20 passed after aligning non-positive coverage to `0`" in change_log
    assert "no issues found in 4 source files" in change_log
    assert "391 passed" in change_log
    assert "no issues found in 181 source files" in change_log
    assert "1907 passed, total coverage 93.86%" in change_log
    assert "fixed ASCII decimal numbers without signs, underscores" in operator_guide
    assert "exponent notation, padding, or control characters" in operator_guide
    assert "`JEDI_WORKER_IDLE_SLEEP_SECONDS`" in operator_guide


def test_sprint_three_hundred_eighteen_documents_public_web_csv_empty_item_guard() -> None:
    change_log = Path("docs/sprints/sprint-318-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Public Web CSV Empty Item Guard" in change_log
    assert "rejects empty items" in change_log
    assert "doubled commas or trailing commas" in change_log
    assert "silently dropping the empty token" in change_log
    assert "diagnostics name the setting and do not echo" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "7 passed after implementation" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 2 source files" in change_log
    assert "8 passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "392 passed" in change_log
    assert "no issues found in 181 source files" in change_log
    assert "1910 passed, total coverage 93.87%" in change_log
    assert "Empty CSV entries are also rejected" in operator_guide
    assert "doubled commas or trailing commas" in operator_guide
    assert "silently dropped" in operator_guide


def test_sprint_three_hundred_nineteen_documents_public_web_validation_redaction() -> None:
    change_log = Path("docs/sprints/sprint-319-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Public Web Validation Diagnostic Redaction" in change_log
    assert "no longer echoes raw invalid public-web" in change_log
    assert "without returning URL userinfo, paths, query keys, or query values" in change_log
    assert "without returning configured host fragments" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "15 passed after implementation" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 2 source files" in change_log
    assert "16 passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "393 passed" in change_log
    assert "no issues found in 181 source files" in change_log
    assert "1913 passed, total coverage 93.87%" in change_log
    assert "does not echo raw invalid" in operator_guide
    assert "without returning the configured URL or host fragment" in operator_guide


def test_sprint_three_hundred_twenty_documents_provider_base_url_host_guard() -> None:
    change_log = Path("docs/sprints/sprint-320-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider Base URL Non-Public Host Guard" in change_log
    assert "rejects non-public host targets" in change_log
    assert "delegated `.localhost`, and legacy numeric local host guard" in change_log
    assert "diagnostics name `base_url` and do not echo" in change_log
    assert "9 tests failed before implementation" in change_log
    assert "22 passed after implementation" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 4 source files" in change_log
    assert "23 passed" in change_log
    assert "no issues found in 5 source files" in change_log
    assert "394 passed" in change_log
    assert "no issues found in 181 source files" in change_log
    assert "1923 passed, total coverage 93.87%" in change_log
    assert "Provider `base_url` values must not target local" in operator_guide
    assert "`2130706433`, `0x7f000001`, or `2852039166`" in operator_guide
    assert "Custom Anthropic gateways remain supported" in operator_guide


def test_sprint_three_hundred_twenty_one_documents_provider_settings_error_redaction() -> None:
    change_log = Path("docs/sprints/sprint-321-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider Settings Validation Input Redaction" in change_log
    assert "OpenAI provider settings now suppress rejected input values" in change_log
    assert "Anthropic provider settings now suppress rejected input values" in change_log
    assert "no longer echo metadata endpoint URLs" in change_log
    assert "embedded credential userinfo" in change_log
    assert "4 tests failed before implementation" in change_log
    assert "14 passed after implementation" in change_log
    assert "5 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 5 source files" in change_log
    assert "no issues found in 181 source files" in change_log
    assert "395 passed" in change_log
    assert "1928 passed, total coverage 93.87%" in change_log
    assert "Direct OpenAI provider settings validation suppresses rejected input values" in (
        operator_guide
    )
    assert "Direct Anthropic provider settings validation follows the same" in operator_guide
    assert "do not echo metadata endpoints" in operator_guide


def test_sprint_three_hundred_twenty_two_documents_runtime_settings_error_redaction() -> None:
    change_log = Path("docs/sprints/sprint-322-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime Settings Validation Input Redaction" in change_log
    assert "Direct `RuntimeSettings` validation now suppresses rejected input values" in (
        change_log
    )
    assert "type, enum, and parsing failures still name the invalid field" in change_log
    assert "database URLs, admin-auth selectors, public-web selectors" in change_log
    assert "4 tests failed before implementation" in change_log
    assert "275 passed after implementation" in change_log
    assert "5 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 181 source files" in change_log
    assert "396 passed" in change_log
    assert "1933 passed, total coverage 93.87%" in change_log
    assert "Direct `RuntimeSettings` construction also suppresses rejected input values" in (
        operator_guide
    )
    assert "do not echo rejected database URL values" in operator_guide
    assert "admin/public-web selector text" in operator_guide


def test_sprint_three_hundred_twenty_three_documents_servicenow_boundary_error_redaction() -> None:
    change_log = Path("docs/sprints/sprint-323-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow Boundary Validation Input Redaction" in change_log
    assert "Direct ServiceNow boundary model validation now suppresses" in change_log
    assert "`ServiceNowSettings`, `HttpRequest`, `HttpResponse`" in change_log
    assert "nested request header values" in change_log
    assert "live instance metadata" in change_log
    assert "4 tests failed before implementation" in change_log
    assert "73 passed after implementation" in change_log
    assert "5 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 3 source files" in change_log
    assert "no issues found in 181 source files" in change_log
    assert "397 passed" in change_log
    assert "1938 passed, total coverage 93.87%" in change_log
    assert "Direct ServiceNow boundary model validation suppresses" in operator_guide
    assert "do not echo rejected instance URLs" in operator_guide
    assert "request body fragments" in operator_guide


def test_sprint_three_hundred_twenty_four_documents_operational_record_error_redaction() -> None:
    change_log = Path("docs/sprints/sprint-324-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Operational Record Validation Input Redaction" in change_log
    assert "Lifecycle ingress and operational-store record validation now suppress" in (change_log)
    assert "`LifecycleStateChangeEvent`, lifecycle event records" in change_log
    assert "artifact payload snippets" in change_log
    assert "retention setting fragments" in change_log
    assert "6 tests failed before implementation" in change_log
    assert "53 passed after implementation" in change_log
    assert "7 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 5 source files" in change_log
    assert "no issues found in 181 source files" in change_log
    assert "398 passed" in change_log
    assert "1945 passed, total coverage 93.87%" in change_log
    assert "Direct lifecycle and operational-store record validation suppresses" in (operator_guide)
    assert "do not echo rejected lifecycle payload fragments" in operator_guide
    assert "ServiceNow sys_ids" in operator_guide


def test_sprint_three_hundred_twenty_five_documents_model_packet_error_redaction() -> None:
    change_log = Path("docs/sprints/sprint-325-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model and Packet Validation Input Redaction" in change_log
    assert "Core model and implementation packet validation now suppress" in change_log
    assert "`Story`, project context, provider policy" in change_log
    assert "generated script content" in change_log
    assert "model-facing contract snippets" in change_log
    assert "5 tests failed before implementation" in change_log
    assert "71 passed after implementation" in change_log
    assert "6 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 5 source files" in change_log
    assert "no issues found in 181 source files" in change_log
    assert "399 passed" in change_log
    assert "1951 passed, total coverage 93.88%" in change_log
    assert "Direct core model and implementation packet validation suppresses" in (operator_guide)
    assert "do not echo rejected story text" in operator_guide
    assert "model-facing contract snippets" in operator_guide


def test_sprint_three_hundred_twenty_six_documents_intent_generation_error_redaction() -> None:
    change_log = Path("docs/sprints/sprint-326-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Intent and Artifact Generation Validation Input Redaction" in change_log
    assert "Normalized automation intent validation now suppresses" in change_log
    assert "Artifact generation validation now suppresses" in change_log
    assert "Business Rule, Client Script, Script Include, UI Policy" in change_log
    assert "Flow Designer evidence, and ATF test plan schemas" in change_log
    assert "story/model payload fragments" in change_log
    assert "1 test failed before implementation because direct automation intent" in change_log
    assert "1 test failed before implementation because direct artifact generation" in (change_log)
    assert "2 passed after implementation" in change_log
    assert "237 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 181 source files" in change_log
    assert "400 passed" in change_log
    assert "1954 passed, total coverage 93.92%" in change_log
    assert "Direct normalized automation intent and artifact generation validation" in (
        operator_guide
    )
    assert "generated script bodies" in operator_guide
    assert "Flow graph evidence" in operator_guide


def test_sprint_three_hundred_twenty_seven_documents_rag_error_redaction() -> None:
    change_log = Path("docs/sprints/sprint-327-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "RAG and public documentation validation input redaction" in change_log
    assert "RAG document and retrieval result validation now suppresses" in change_log
    assert "Public documentation access config and public web response validation" in (change_log)
    assert "public-documentation URLs" in change_log
    assert "1 test failed before implementation" in change_log
    assert "28 passed after implementation" in change_log
    assert "2 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 181 source files" in change_log
    assert "401 passed" in change_log
    assert "1956 passed, total coverage 93.92%" in change_log
    assert "Direct RAG and public-documentation validation suppresses" in operator_guide
    assert "retrieved content" in operator_guide
    assert "citation payloads" in operator_guide


def test_sprint_three_hundred_twenty_eight_documents_operational_dto_error_redaction() -> None:
    change_log = Path("docs/sprints/sprint-328-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "operational DTO validation input redaction" in change_log
    assert "Operational DTO validation now suppresses rejected input values" in change_log
    assert "alert payloads, builder maturity evidence" in change_log
    assert "fulfillment worker results, and stale-job requeue reports" in change_log
    assert "artifact payload snippets" in change_log
    assert "1 test failed before implementation" in change_log
    assert "80 passed after implementation" in change_log
    assert "2 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 182 source files" in change_log
    assert "402 passed" in change_log
    assert "1958 passed, total coverage 93.92%" in change_log
    assert "Direct operational DTO validation suppresses" in operator_guide
    assert "worker error fragments" in operator_guide
    assert "stale requeue timestamps" in operator_guide


def test_sprint_three_hundred_twenty_nine_documents_discovery_flow_error_redaction() -> None:
    change_log = Path("docs/sprints/sprint-329-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "discovery and Flow evidence validation input redaction" in change_log
    assert "Discovery and Flow evidence DTO validation now suppresses" in change_log
    assert "ServiceNow surface records, surface context bundles" in change_log
    assert "Flow XML shape evidence records" in change_log
    assert "graph hashes, snapshot ids" in change_log
    assert "1 test failed before implementation" in change_log
    assert "89 passed after implementation" in change_log
    assert "2 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 183 source files" in change_log
    assert "403 passed" in change_log
    assert "1960 passed, total coverage 93.92%" in change_log
    assert "Direct discovery and Flow evidence validation suppresses" in operator_guide
    assert "script summaries" in operator_guide
    assert "round-trip assertion details" in operator_guide


def test_sprint_three_hundred_thirty_documents_update_writeback_error_redaction() -> None:
    change_log = Path("docs/sprints/sprint-330-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set and writeback DTO validation input redaction" in change_log
    assert "retrieved Update Set handoff, and writeback DTO validation" in change_log
    assert "writeback audit events, build-claim audit events" in change_log
    assert "verification field values" in change_log
    assert "1 test failed before implementation" in change_log
    assert "63 passed after implementation" in change_log
    assert "2 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 184 source files" in change_log
    assert "404 passed" in change_log
    assert "1962 passed, total coverage 93.92%" in change_log
    assert "Direct Update Set and writeback DTO validation suppresses" in operator_guide
    assert "candidate artifacts" in operator_guide
    assert "audit paths, work notes, actor ids" in operator_guide


def test_sprint_three_hundred_thirty_one_documents_capability_planning_error_redaction() -> None:
    change_log = Path("docs/sprints/sprint-331-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "capability, planning, safety, and review DTO validation input redaction" in (change_log)
    assert "Capability, planning, safety, and review DTO validation now suppresses" in (change_log)
    assert "story capability assessments, intake feedback" in change_log
    assert "reviewer ids, review reasons" in change_log
    assert "1 test failed before implementation" in change_log
    assert "49 passed after implementation" in change_log
    assert "2 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 185 source files" in change_log
    assert "405 passed" in change_log
    assert "1964 passed, total coverage 93.94%" in change_log
    assert "Direct capability, planning, safety, and review DTO validation" in (operator_guide)
    assert "placement directives" in operator_guide
    assert "prioritization evidence" in operator_guide


def test_sprint_three_hundred_thirty_two_documents_runtime_control_error_redaction() -> None:
    change_log = Path("docs/sprints/sprint-332-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "runtime and control-plane DTO validation input redaction" in change_log
    assert "Runtime and control-plane DTO validation now suppresses" in change_log
    assert "container smoke plans, external build pipeline results" in change_log
    assert "model fulfillment config, resolved fulfillment flows" in change_log
    assert "1 test failed before implementation" in change_log
    assert "132 passed after implementation" in change_log
    assert "2 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 186 source files" in change_log
    assert "406 passed" in change_log
    assert "1966 passed, total coverage 93.94%" in change_log
    assert "Direct runtime and control-plane DTO validation" in operator_guide
    assert "runtime settings, provider policies" in operator_guide
    assert "delivery handoff evidence" in operator_guide


def test_sprint_three_hundred_thirty_three_documents_bootstrap_legacy_error_redaction() -> None:
    change_log = Path("docs/sprints/sprint-333-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "bootstrap, enrichment, and risk DTO validation input redaction" in change_log
    assert "Bootstrap, enrichment, and risk DTO validation now suppresses" in change_log
    assert "bootstrap field specs, bootstrap field plans" in change_log
    assert "story enrichment results, and risk inputs" in change_log
    assert "project-wide Pydantic DTO audit now reports zero" in change_log
    assert "1 test failed before implementation" in change_log
    assert "31 passed after implementation" in change_log
    assert "missing 0" in change_log
    assert "2 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "407 passed" in change_log
    assert "1968 passed, total coverage 93.95%" in change_log
    assert "Direct bootstrap, enrichment, and risk DTO validation" in operator_guide
    assert "retrieved update-set importer scripts" in operator_guide
    assert "zero `BaseModel` classes without `hide_input_in_errors`" in operator_guide


def test_sprint_three_hundred_thirty_four_documents_worker_failure_diagnostic_redaction() -> None:
    change_log = Path("docs/sprints/sprint-334-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "core fulfillment worker failure diagnostic redaction" in change_log
    assert "Core fulfillment worker failures now redact" in change_log
    assert "before failure notifier delivery" in change_log
    assert "PostgreSQL `last_error` persistence" in change_log
    assert "1 test failed before implementation" in change_log
    assert "svc-password" in change_log
    assert "10 passed after implementation" in change_log
    assert "32 passed" in change_log
    assert "2 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "408 passed" in change_log
    assert "1970 passed, total coverage 93.95%" in change_log
    assert "Worker failure diagnostics are redacted" in operator_guide
    assert "process_one_fulfillment_job()` directly" in operator_guide
    assert "Authorization header values" in operator_guide


def test_sprint_three_hundred_thirty_five_documents_cli_validation_diagnostic_redaction() -> None:
    change_log = Path("docs/sprints/sprint-335-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "CLI validation diagnostic redaction" in change_log
    assert "Bootstrap and delivery CLI commands now redact" in change_log
    assert "invalid_build_result" in change_log
    assert "invalid_lifecycle_webhook_spec" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "external-build-secret" in change_log
    assert "lifecycle-spec-secret" in change_log
    assert "7 passed after implementation" in change_log
    assert "66 passed" in change_log
    assert "3 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "409 passed" in change_log
    assert "1973 passed, total coverage 93.99%" in change_log
    assert "CLI validation error output is redacted" in operator_guide
    assert "operator terminals, CI logs" in operator_guide
    assert "client_secret=..." in operator_guide


def test_sprint_three_hundred_thirty_six_documents_artifact_path_containment() -> None:
    change_log = Path("docs/sprints/sprint-336-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "local artifact path containment" in change_log
    assert "Shared local artifact writers now reject unsafe artifact filenames" in change_log
    assert "candidate run directories, candidate filenames" in change_log
    assert "absolute paths, path separators, and control characters" in change_log
    assert "3 tests failed before implementation" in change_log
    assert "traversal components were accepted" in change_log
    assert "13 passed after implementation" in change_log
    assert "98 passed" in change_log
    assert "4 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "410 passed" in change_log
    assert "1977 passed, total coverage 93.98%" in change_log
    assert "Local artifact filenames and single-directory path components" in (operator_guide)
    assert "cannot escape the configured artifact root" in operator_guide


def test_sprint_three_hundred_thirty_seven_documents_exclusive_artifact_create() -> None:
    change_log = Path("docs/sprints/sprint-337-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "exclusive local artifact creation" in change_log
    assert "exclusive file creation instead of an exists-then-write sequence" in change_log
    assert "existing files, existing symlinks, and broken symlinks" in change_log
    assert "broken symlink redirection" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "15 passed after implementation" in change_log
    assert "3 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "411 passed" in change_log
    assert "1980 passed, total coverage 93.99%" in change_log
    assert "Local write-once artifact creation uses exclusive file creation" in (operator_guide)
    assert "symlink redirection outside the artifact root" in operator_guide


def test_sprint_three_hundred_thirty_eight_documents_artifact_read_safety() -> None:
    change_log = Path("docs/sprints/sprint-338-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "artifact provenance read safety" in change_log
    assert "validates the filesystem entry before streaming" in change_log
    assert "Symlinked artifact paths and non-regular filesystem entries" in change_log
    assert "`ArtifactReadError`" in change_log
    assert "Missing artifact paths continue" in change_log
    assert "1 test failed before implementation" in change_log
    assert "26 passed after implementation" in change_log
    assert "2 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "412 passed" in change_log
    assert "1982 passed, total coverage 93.99%" in change_log
    assert "Local artifact SHA-256 provenance hashing requires a regular file" in (operator_guide)
    assert "do not treat filesystem indirection as authoritative artifact evidence" in (
        operator_guide
    )


def test_sprint_three_hundred_thirty_nine_documents_attachment_read_safety() -> None:
    change_log = Path("docs/sprints/sprint-339-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow attachment artifact read safety" in change_log
    assert "shared regular-file artifact reader instead of `Path.read_bytes()`" in (change_log)
    assert "rejects symlinked paths and non-regular filesystem entries" in change_log
    assert "before OAuth token acquisition or Attachment API upload" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "4 passed after implementation" in change_log
    assert "104 passed" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "413 passed" in change_log
    assert "1985 passed, total coverage 93.96%" in change_log
    assert "Attachment upload uses the same regular-file artifact reader" in (operator_guide)
    assert "normal attachments are streamed in bounded chunks" in operator_guide


def test_sprint_three_hundred_forty_documents_xml_scanner_read_safety() -> None:
    change_log = Path("docs/sprints/sprint-340-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "reviewed XML scanner artifact read safety" in change_log
    assert "shared regular-file artifact reader instead of direct `Path.open()`" in (change_log)
    assert "Placeholder detection and `sys_update_xml` marker scanning" in change_log
    assert "same descriptor-safe file boundary" in change_log
    assert "1 test failed before implementation" in change_log
    assert "18 passed after implementation" in change_log
    assert "1 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "414 passed" in change_log
    assert "1987 passed, total coverage 93.96%" in change_log
    assert "Reviewed Update Set XML marker validation uses the same regular-file" in (
        operator_guide
    )
    assert "review eligibility checks cannot bypass artifact provenance" in (operator_guide)


def test_sprint_three_hundred_forty_one_documents_smoke_xml_exclusive_create() -> None:
    change_log = Path("docs/sprints/sprint-341-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "delivery smoke XML exclusive artifact creation" in change_log
    assert "shared exclusive-create text artifact writer" in change_log
    assert "exists-then-`write_text()` sequence" in change_log
    assert "`run-delivery-artifact-smoke` and `run-reviewed-delivery-smoke`" in (change_log)
    assert "broken-symlink redirection outside the configured artifact root" in (change_log)
    assert "1 test failed before implementation" in change_log
    assert "6 passed after implementation" in change_log
    assert "3 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "415 passed" in change_log
    assert "1990 passed, total coverage 93.99%" in change_log
    assert "Delivery smoke XML exports use the same exclusive-create" in operator_guide
    assert "redirect XML outside the configured artifact root" in operator_guide


def test_sprint_three_hundred_forty_two_documents_cli_json_regular_file_input() -> None:
    change_log = Path("docs/sprints/sprint-342-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "CLI JSON input regular-file enforcement" in change_log
    assert "shared descriptor-safe regular-file reader instead of direct `Path.open()`" in (
        change_log
    )
    assert "json_input_must_be_regular_file" in change_log
    assert "10 MiB JSON input cap and redacted CLI diagnostics are preserved" in (change_log)
    assert "provider responses, lifecycle specs, handoff reports" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "4 passed after implementation" in change_log
    assert "2 passed" in change_log
    assert "7 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "416 passed" in change_log
    assert "1993 passed, total coverage 93.99%" in change_log
    assert "The same loader requires a regular file" in operator_guide
    assert "local orchestration cannot silently follow filesystem indirection" in (operator_guide)


def test_sprint_three_hundred_forty_three_documents_env_toml_regular_file_input() -> None:
    change_log = Path("docs/sprints/sprint-343-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "local env and TOML regular-file enforcement" in change_log
    assert "Local `.env` loading now uses the shared descriptor-safe" in change_log
    assert "Project TOML config loading now uses the same regular-file reader" in (change_log)
    assert "dotenv_must_be_regular_file" in change_log
    assert "project_config_must_be_regular_file" in change_log
    assert "Existing 1 MiB input caps" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "15 passed after implementation" in change_log
    assert "16 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "417 passed" in change_log
    assert "1996 passed, total coverage 93.99%" in change_log
    assert "dotenv_must_be_regular_file" in operator_guide
    assert "project_config_must_be_regular_file" in operator_guide
    assert "local credential loading cannot silently follow filesystem indirection" in (
        operator_guide
    )


def test_sprint_three_hundred_forty_four_documents_public_web_redirect_blocking() -> None:
    change_log = Path("docs/sprints/sprint-344-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "public documentation redirect blocking" in change_log
    assert "explicit urllib opener with a no-redirect handler" in change_log
    assert "blocked before a second outbound request" in change_log
    assert "default `urlopen()` behavior" in change_log
    assert "post-fetch final URL validation remains" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "2 passed after implementation" in change_log
    assert "31 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "418 passed" in change_log
    assert "1999 passed, total coverage 94.04%" in change_log
    assert "30 passed" in change_log
    assert "does not follow redirects" in operator_guide
    assert "blocked before a second outbound request" in operator_guide
    assert "alternate transport reports a different final host" in operator_guide


def test_sprint_three_hundred_forty_five_documents_servicenow_redirect_blocking() -> None:
    change_log = Path("docs/sprints/sprint-345-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport redirect blocking" in change_log
    assert "OAuth, Table API, and Attachment API calls" in change_log
    assert "explicit urllib opener with a no-redirect handler" in change_log
    assert "blocked before a second outbound request" in change_log
    assert "configured ServiceNow instance boundaries remain authoritative" in change_log
    assert "patch the opener factory directly" in change_log
    assert "3 tests failed before implementation" in change_log
    assert "4 passed after implementation" in change_log
    assert "78 passed" in change_log
    assert "79 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "419 passed" in change_log
    assert "2002 passed, total coverage 94.05%" in change_log
    assert "ServiceNow OAuth, Table API, and Attachment API calls do not follow" in (operator_guide)
    assert "prevents an instance, proxy, DNS, or network-control mistake" in operator_guide


def test_sprint_three_hundred_forty_six_documents_inbound_admin_auth_no_trim() -> None:
    change_log = Path("docs/sprints/sprint-346-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "inbound admin Authorization credential normalization" in change_log
    assert "no longer strips inbound credential material" in change_log
    assert "rejected before `secrets.compare_digest()` is called" in change_log
    assert "no longer strips the encoded credential section" in change_log
    assert "rejected before base64 decoding" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "4 passed after implementation" in change_log
    assert "17 passed" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "420 passed" in change_log
    assert "2005 passed, total coverage 94.05%" in change_log
    assert "rejects padded, whitespace-bearing, or control-character-bearing" in (operator_guide)
    assert "before base64 decoding instead of trimming them" in operator_guide
    assert "before comparison instead of trimming them" in operator_guide


def test_sprint_three_hundred_forty_seven_documents_lifecycle_webhook_auth_no_trim() -> None:
    change_log = Path("docs/sprints/sprint-347-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "lifecycle webhook inbound auth header normalization" in change_log
    assert "before integer parsing" in change_log
    assert "can no longer be signed and accepted" in change_log
    assert "rejected before `hmac.compare_digest()`" in change_log
    assert "3 tests failed before implementation" in change_log
    assert "6 passed after implementation" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "421 passed" in change_log
    assert "2009 passed, total coverage 94.04%" in change_log
    assert "Inbound lifecycle webhook credential material is never normalized" in operator_guide
    assert "ASCII base-10 digits without padding" in operator_guide
    assert "before constant-time comparison" in operator_guide


def test_sprint_three_hundred_forty_eight_documents_decoded_basic_auth_no_trim() -> None:
    change_log = Path("docs/sprints/sprint-348-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "decoded Basic-auth credential normalization" in change_log
    assert "rejects malformed decoded credential parts" in change_log
    assert "return the existing unauthorized admin console response" in change_log
    assert "no longer reach `secrets.compare_digest()`" in change_log
    assert "4 tests failed before implementation" in change_log
    assert "9 passed after implementation" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "422 passed" in change_log
    assert "2014 passed, total coverage 94.04%" in change_log
    assert "After decoding, username and password parts are also rejected" in operator_guide
    assert "before constant-time comparison" in operator_guide
    assert "padded, whitespace-bearing, or control-character-bearing" in operator_guide


def test_sprint_three_hundred_forty_nine_documents_runtime_mode_auth_no_trim() -> None:
    change_log = Path("docs/sprints/sprint-349-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "direct runtime environment normalization at auth decisions" in change_log
    assert "no longer strips or lowercases direct runtime environment values" in change_log
    assert "fail closed at both auth decision points" in change_log
    assert "stricter second line of defense" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "5 passed after implementation" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "423 passed" in change_log
    assert "2017 passed, total coverage 94.07%" in change_log
    assert "Security-sensitive runtime auth decisions do not normalize" in operator_guide
    assert "exact normalized value `development`" in operator_guide
    assert "fail closed instead of being treated as development" in operator_guide


def test_sprint_three_hundred_fifty_documents_servicenow_oauth_token_no_trim() -> None:
    change_log = Path("docs/sprints/sprint-350-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow OAuth access-token response normalization" in change_log
    assert "rejects malformed `access_token` response values" in change_log
    assert "before caching or Authorization header construction" in change_log
    assert "no longer trimmed or accepted as a bearer credential" in change_log
    assert "3 tests failed before implementation" in change_log
    assert "7 passed after implementation" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "424 passed" in change_log
    assert "2021 passed, total coverage 94.07%" in change_log
    assert "OAuth token responses are also treated as untrusted input" in operator_guide
    assert "before caching the token or building a `Bearer` Authorization header" in (
        operator_guide
    )
    assert "does not trim token response material into a usable credential" in operator_guide


def test_sprint_three_hundred_fifty_one_documents_anthropic_retry_after_no_trim() -> None:
    change_log = Path("docs/sprints/sprint-351-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Anthropic retry-after response normalization" in change_log
    assert "no longer strips upstream `retry-after` response header values" in change_log
    assert "ignored instead of controlling worker sleep" in change_log
    assert "deterministic exponential backoff" in change_log
    assert "3 tests failed before implementation" in change_log
    assert "6 passed after implementation" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "425 passed" in change_log
    assert "2026 passed, total coverage 94.08%" in change_log
    assert "safe finite `retry-after` values" in operator_guide
    assert "non-finite values such as `nan` and `inf` are ignored" in operator_guide
    assert "fall back to deterministic exponential backoff" in operator_guide


def test_sprint_three_hundred_fifty_two_documents_openai_error_metadata_redaction() -> None:
    change_log = Path("docs/sprints/sprint-352-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "OpenAI structured error metadata normalization" in change_log
    assert "upstream structured `error.type` and `error.code` values" in change_log
    assert "redacted with the configured API key" in change_log
    assert "collapsed before diagnostics" in change_log
    assert "1 test failed before implementation" in change_log
    assert "24 passed after implementation" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "426 passed" in change_log
    assert "2028 passed, total coverage 94.08%" in change_log
    assert "Structured OpenAI `type` and `code` values are also treated" in operator_guide
    assert "whitespace/control-character-normalized before inclusion" in operator_guide
    assert "cannot inject log lines or echo configured API keys" in operator_guide


def test_sprint_three_hundred_fifty_three_documents_servicenow_error_diagnostics() -> None:
    change_log = Path("docs/sprints/sprint-353-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow API error diagnostic metadata normalization" in change_log
    assert "recursively applies the shared sensitive-key vocabulary" in change_log
    assert "normalizes whitespace" in change_log
    assert "control characters before ServiceNow error payloads" in change_log
    assert "1 test failed before implementation" in change_log
    assert "82 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "427 documentation tests passed" in change_log
    assert "2030 total tests passed at 94.05% coverage" in change_log
    assert "ServiceNow API error response diagnostics are also" in operator_guide
    assert "whitespace/control-character-normalized before" in operator_guide
    assert "cannot inject extra diagnostic lines" in operator_guide


def test_sprint_three_hundred_fifty_four_documents_servicenow_error_cap() -> None:
    change_log = Path("docs/sprints/sprint-354-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow API final diagnostic size cap" in change_log
    assert "final post-redaction size cap" in change_log
    assert "cannot create oversized worker failures" in change_log
    assert "truncates it with the existing ServiceNow" in change_log
    assert "1 test failed before implementation" in change_log
    assert "83 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "428 documentation tests passed" in change_log
    assert "2032 total tests passed at 94.05% coverage" in change_log
    assert "ServiceNow API exception diagnostics also apply" in operator_guide
    assert "final post-redaction size cap before formatting" in operator_guide
    assert "cannot create an oversized exception string" in operator_guide


def test_sprint_three_hundred_fifty_five_documents_provider_output_bounds() -> None:
    change_log = Path("docs/sprints/sprint-355-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider successful-output parse bounds" in change_log
    assert "successful `200`" in change_log
    assert "arbitrarily large model output text" in change_log
    assert "oversized output before JSON parsing" in change_log
    assert "do not echo the model output" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "98 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "429 documentation tests passed" in change_log
    assert "2035 total tests passed at 94.05% coverage" in change_log
    assert "OpenAI successful model output text is bounded before JSON parsing" in operator_guide
    assert "Anthropic successful model output text is bounded before JSON parsing" in operator_guide
    assert "1,000,000 characters" in operator_guide


def test_sprint_three_hundred_fifty_six_documents_lifecycle_validation_no_echo() -> None:
    change_log = Path("docs/sprints/sprint-356-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Lifecycle webhook validation error input suppression" in change_log
    assert "cannot reflect" in change_log
    assert "submitted payload values back to callers" in change_log
    assert "include_input=False" in change_log
    assert "structured error type, location, and message metadata" in change_log
    assert "1 test failed before implementation" in change_log
    assert "28 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "430 documentation tests passed" in change_log
    assert "2037 total tests passed at 94.07% coverage" in change_log
    assert "Lifecycle webhook schema validation errors do not echo rejected" in operator_guide
    assert "omit Pydantic `input` fields" in operator_guide
    assert "cannot reflect" in operator_guide
    assert "ServiceNow sys_ids, work notes, credentials" in operator_guide


def test_sprint_three_hundred_fifty_seven_documents_runtime_validation_no_echo() -> None:
    change_log = Path("docs/sprints/sprint-357-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime request validation error input suppression" in change_log
    assert "FastAPI can raise `RequestValidationError`" in change_log
    assert "before route-level code runs" in change_log
    assert "stripping Pydantic/FastAPI `input` fields" in change_log
    assert "1 test failed before implementation" in change_log
    assert "283 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "431 documentation tests passed" in change_log
    assert "2039 total tests passed at 94.07% coverage" in change_log
    assert "Runtime request validation errors do not echo rejected input values" in (operator_guide)
    assert "malformed path or query parameters" in operator_guide
    assert "before route-level admin authentication runs" in operator_guide


def test_sprint_three_hundred_fifty_eight_documents_admin_diagnostic_bounds() -> None:
    change_log = Path("docs/sprints/sprint-358-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Persisted admin diagnostic response bounds" in change_log
    assert "persisted failure text cannot create oversized API or HTML" in change_log
    assert "one shared post-redaction size cap" in change_log
    assert "`...[truncated]`" in change_log
    assert "3 tests failed before implementation" in change_log
    assert "9 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "432 documentation tests passed" in change_log
    assert "2043 total tests passed at 94.07% coverage" in change_log
    assert "Persisted admin diagnostic strings are whitespace/control-character-normalized" in (
        operator_guide
    )
    assert "bounded after" in operator_guide
    assert "fulfillment job `last_error` values" in operator_guide
    assert "`...[truncated]`" in operator_guide


def test_sprint_603_documents_admin_diagnostic_text_normalization() -> None:
    change_log = Path("docs/sprints/sprint-603-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin diagnostic text normalization" in change_log
    assert "`_admin_diagnostic_text()`" in change_log
    assert "2 failing-first admin diagnostic tests" in change_log
    assert "preserved newline and tab characters in persisted `last_error`" in (
        change_log
    )
    assert "whitespace/control-character-normalized and bounded after" in (
        operator_guide
    )
    assert "cannot retain raw multiline diagnostic text" in operator_guide


def test_sprint_three_hundred_fifty_nine_documents_artifact_payload_bounds() -> None:
    change_log = Path("docs/sprints/sprint-359-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Whole artifact diagnostic payload bounds" in change_log
    assert "large structured payload cannot create an oversized admin" in change_log
    assert "`payload_truncated: true`" in change_log
    assert "`original_payload_type`, `diagnostic_preview`, and `truncated: true`" in (change_log)
    assert "2 tests failed before implementation" in change_log
    assert "7 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "433 documentation tests passed" in change_log
    assert "2046 total tests passed at 94.10% coverage" in change_log
    assert "Oversized artifact payload diagnostic views are collapsed as a whole" in (
        operator_guide
    )
    assert "`payload_truncated: true`" in operator_guide
    assert "operator's provenance handle for the full stored payload" in operator_guide


def test_sprint_three_hundred_sixty_documents_artifact_traversal_bounds() -> None:
    change_log = Path("docs/sprints/sprint-360-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Traversal-bounded artifact payload diagnostics" in change_log
    assert "bounded before full recursive" in change_log
    assert "redaction and JSON serialization" in change_log
    assert "`omitted_items`" in change_log
    assert "`omitted_fields`" in change_log
    assert "1 test failed before implementation" in change_log
    assert "5 tests" in change_log
    assert "one diagnostic projection path" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "434 documentation tests passed" in change_log
    assert "2049 total tests passed at 94.11% coverage" in change_log
    assert "Artifact payload diagnostic projection also bounds collection traversal" in (
        operator_guide
    )
    assert "`omitted_items` or `omitted_fields` markers" in operator_guide
    assert "recursively redact or serialize every nested entry" in operator_guide


def test_sprint_three_hundred_sixty_one_documents_iterator_bounded_artifacts() -> None:
    change_log = Path("docs/sprints/sprint-361-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Iterator-bounded artifact diagnostic sampling" in change_log
    assert "`list(value.items())` before sampling" in change_log
    assert "samples dictionaries, lists, and tuples with bounded iterators" in change_log
    assert "1 test failed before implementation" in change_log
    assert "6 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "435 documentation tests passed" in change_log
    assert "2051 total tests passed at 94.02% coverage" in change_log
    assert "samples dictionaries, arrays," in operator_guide
    assert "and tuples through bounded iterators" in operator_guide
    assert "materializing full collection copies" in operator_guide


def test_sprint_three_hundred_sixty_two_documents_alert_response_bounds() -> None:
    change_log = Path("docs/sprints/sprint-362-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert sink response diagnostic bounds" in change_log
    assert "post-redaction size cap" in change_log
    assert "`...[truncated]`" in change_log
    assert "1 test failed before implementation" in change_log
    assert "22 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "436 documentation tests passed" in change_log
    assert "2053 total tests passed at 94.02% coverage" in change_log
    assert "Alert sink response string values are also" in operator_guide
    assert "whitespace/control-character-normalized before `AlertDeliveryError`" in (
        operator_guide
    )
    assert "`AlertDeliveryError` diagnostics" in operator_guide
    assert "large JSON error body" in operator_guide


def test_sprint_three_hundred_sixty_three_documents_alert_response_aggregate_bounds() -> None:
    change_log = Path("docs/sprints/sprint-363-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Whole alert sink response diagnostic bounds" in change_log
    assert "entire structured sink response is bounded after" in change_log
    assert "compact sorted JSON" in change_log
    assert "`...[truncated]`" in change_log
    assert "1 test failed before implementation" in change_log
    assert "23 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "437 documentation tests passed" in change_log
    assert "2055 total tests passed at 94.04% coverage" in change_log
    assert "The full alert sink response diagnostic is also size-capped" in (operator_guide)
    assert "aggregate JSON response shape" in operator_guide
    assert "per-string diagnostic cap" in operator_guide


def test_sprint_three_hundred_sixty_four_documents_alert_response_traversal_bounds() -> None:
    change_log = Path("docs/sprints/sprint-364-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Traversal-bounded alert sink diagnostics" in change_log
    assert "sample dictionaries, lists, and tuples with bounded iterators" in change_log
    assert "`omitted_fields` marker" in change_log
    assert "`omitted_items` marker" in change_log
    assert "1 test failed before implementation" in change_log
    assert "24 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "438 documentation tests passed" in change_log
    assert "2057 total tests passed at 93.99% coverage" in change_log
    assert "Alert sink response diagnostic traversal is bounded before serialization" in (
        operator_guide
    )
    assert "`omitted_fields` or `omitted_items` markers" in operator_guide
    assert "recursively redact every nested entry" in operator_guide


def test_sprint_three_hundred_sixty_five_documents_alert_response_json_safe() -> None:
    change_log = Path("docs/sprints/sprint-365-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "JSON-safe alert sink diagnostics" in change_log
    assert "non-JSON nested values cannot break" in change_log
    assert "`non_json_type` marker" in change_log
    assert "does not call `repr()` or `str()`" in change_log
    assert "1 test failed before implementation" in change_log
    assert "25 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "439 documentation tests passed" in change_log
    assert "2059 total tests passed at 93.99% coverage" in change_log
    assert "Alert sink response diagnostics are JSON-safe" in operator_guide
    assert "`non_json_type` marker" in operator_guide
    assert "object internals out of `AlertDeliveryError` diagnostics" in operator_guide


def test_sprint_604_documents_alert_delivery_text_normalization() -> None:
    change_log = Path("docs/sprints/sprint-604-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert delivery text normalization" in change_log
    assert "`emit_alert_webhook()`" in change_log
    assert "2 failing-first alert delivery tests" in change_log
    assert "outbound webhook body text and alert sink response diagnostics" in change_log
    assert "redacted, whitespace/control-character-normalized, and bounded before compact" in (
        operator_guide
    )
    assert "direct `emit_alert_webhook()` callers cannot bypass generated-alert sanitization" in (
        operator_guide
    )
    assert "Alert sink response string values are also" in operator_guide
    assert "whitespace/control-character-normalized before `AlertDeliveryError`" in (
        operator_guide
    )


def test_sprint_607_documents_alert_sink_response_truncation_marker_collision() -> None:
    change_log = Path("docs/sprints/sprint-607-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert sink response truncation marker collision safety" in change_log
    assert "`_redact_alert_response_node()`" in change_log
    assert "`_unique_alert_response_key()`" in change_log
    assert "1 failing-first alert response diagnostic test" in change_log
    assert "overwrote a user-provided `__jedi_response_truncated__` field" in (
        change_log
    )
    assert "Alert sink response dictionary truncation markers are collision-safe" in (
        operator_guide
    )
    assert "the original response field remains visible" in operator_guide
    assert "deterministic duplicate suffix" in operator_guide


def test_sprint_608_documents_alert_sink_response_exact_string_boundary() -> None:
    change_log = Path("docs/sprints/sprint-608-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert sink response exact-string diagnostic boundary" in change_log
    assert "`_alert_response_key()`" in change_log
    assert "`_redact_alert_response_node()`" in change_log
    assert "2 failing-first alert response diagnostic tests" in change_log
    assert "string subclass key rendered as `client_secret`" in change_log
    assert "Only exact string keys and values enter alert sink response text redaction" in (
        operator_guide
    )
    assert "string subclasses render" in operator_guide
    assert "`[non-json value]` for values" in operator_guide


def test_sprint_931_documents_alert_sink_response_scalar_subclass_boundary() -> None:
    change_log = Path("docs/sprints/sprint-931-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert sink response scalar-subclass diagnostic boundary" in change_log
    assert "`_redact_alert_response_node()`" in change_log
    assert "`[non-json value]`" in change_log
    assert "1 failing-first alert response diagnostic scalar-subclass assertion" in (
        change_log
    )
    assert "Alert sink response boolean and integer values must be exact JSON scalar types" in (
        operator_guide
    )
    assert "`test_alert_response_diagnostic_rejects_scalar_subclass_values`" in change_log


def test_sprint_936_documents_alert_response_exact_container_boundary() -> None:
    change_log = Path("docs/sprints/sprint-936-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert response exact-container diagnostic boundary" in change_log
    assert "`_redact_alert_response_node()`" in change_log
    assert "1 failing-first alert response diagnostic container-subclass assertion" in change_log
    assert "Alert sink response diagnostic traversal is bounded before serialization" in (
        operator_guide
    )
    assert "Dictionary, list, and tuple subclasses render as `[non-json value]`" in (
        operator_guide
    )


def test_sprint_three_hundred_sixty_six_documents_servicenow_diagnostic_traversal_bounds() -> None:
    change_log = Path("docs/sprints/sprint-366-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Traversal-bounded ServiceNow API diagnostics" in change_log
    assert "wide response body cannot force full recursive redaction" in change_log
    assert "`_servicenow_diagnostic_value()`" in change_log
    assert "`omitted_fields` marker" in change_log
    assert "`omitted_items` marker" in change_log
    assert "1 test failed before implementation" in change_log
    assert "84 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "440 documentation tests passed" in change_log
    assert "2061 total tests passed at 93.91% coverage" in change_log
    assert "ServiceNow API response diagnostics are traversal-bounded" in (operator_guide)
    assert "`omitted_fields` or `omitted_items` markers" in operator_guide
    assert "final diagnostic cap" in operator_guide


def test_sprint_three_hundred_sixty_seven_documents_http_error_bounds() -> None:
    change_log = Path("docs/sprints/sprint-367-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Traversal-bounded HTTP error diagnostic shaping" in change_log
    assert "parsed HTTP error JSON cannot force full recursive diagnostic shaping" in (change_log)
    assert "`_bound_http_error_diagnostics()`" in change_log
    assert "`omitted_fields` marker" in change_log
    assert "`omitted_items` marker" in change_log
    assert "1 test failed before implementation" in change_log
    assert "85 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "441 documentation tests passed" in change_log
    assert "2063 total tests passed at 93.83% coverage" in change_log
    assert "Parsed ServiceNow HTTP error JSON diagnostics are traversal-bounded" in (operator_guide)
    assert "`omitted_fields` or `omitted_items` markers" in operator_guide
    assert "every nested entry" in operator_guide


def test_sprint_three_hundred_sixty_eight_documents_secret_redaction_bounds() -> None:
    change_log = Path("docs/sprints/sprint-368-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Traversal-bounded ServiceNow secret redaction" in change_log
    assert "wide request or response diagnostic bodies cannot force full recursive redaction" in (
        change_log
    )
    assert "`redact_secrets()`" in change_log
    assert "`omitted_fields` marker" in change_log
    assert "`omitted_items` marker" in change_log
    assert "1 test failed before implementation" in change_log
    assert "86 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "442 documentation tests passed" in change_log
    assert "2065 total tests passed at 93.77% coverage" in change_log
    assert "ServiceNow diagnostic secret redaction is traversal-bounded" in (operator_guide)
    assert "`omitted_fields` or `omitted_items` markers" in operator_guide
    assert "producing a sanitized diagnostic copy" in operator_guide


def test_sprint_three_hundred_sixty_nine_documents_provider_output_traversal() -> None:
    change_log = Path("docs/sprints/sprint-369-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Bounded provider successful-response traversal" in change_log
    assert "cannot force unbounded collection traversal" in change_log
    assert "OpenAI nested `output[].content[]` scanning" in change_log
    assert "Anthropic `content[]` scanning" in change_log
    assert "3 tests failed before implementation" in change_log
    assert "101 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "443 documentation tests passed" in change_log
    assert "2069 total tests passed at 93.80% coverage" in change_log
    assert "OpenAI successful-response text selection is traversal-bounded" in (operator_guide)
    assert "Anthropic successful-response text selection is traversal-bounded" in (operator_guide)
    assert "arbitrarily wide successful response" in operator_guide


def test_sprint_three_hundred_seventy_documents_anthropic_error_metadata() -> None:
    change_log = Path("docs/sprints/sprint-370-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Anthropic structured error metadata redaction" in change_log
    assert "structured `error.type` metadata cannot inject log lines" in change_log
    assert "configured Anthropic API key" in change_log
    assert "1 test failed before implementation" in change_log
    assert "71 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 187 source files" in change_log
    assert "444 documentation tests passed" in change_log
    assert "2071 total tests passed at 93.80% coverage" in change_log
    assert "Structured Anthropic `type` values are treated as untrusted" in (operator_guide)
    assert "whitespace/control-character-normalized before inclusion" in (operator_guide)


def test_sprint_three_hundred_seventy_one_documents_provider_normalization_bounds() -> None:
    change_log = Path("docs/sprints/sprint-371-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Bounded provider candidate normalization" in change_log
    assert "cannot produce oversized post-parse candidate structures" in change_log
    assert "duplicated unbounded normalization loops" in change_log
    assert "maximum of 100 candidate changes" in change_log
    assert "100 field entries per change" in change_log
    assert "4 tests failed before implementation" in change_log
    assert "106 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 188 source files" in change_log
    assert "445 documentation tests passed" in change_log
    assert "2076 total tests passed at 93.85% coverage" in change_log
    assert "Provider candidate normalization is shared across OpenAI and Anthropic" in (
        operator_guide
    )
    assert "at most 100 candidate changes" in operator_guide
    assert "at most 100 field entries" in operator_guide


def test_sprint_three_hundred_seventy_two_documents_generic_provider_bounds() -> None:
    change_log = Path("docs/sprints/sprint-372-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Generic provider response validation bounds" in change_log
    assert "used by `generate_with_provider()`" in change_log
    assert "accepted more than 100 changes" in change_log
    assert "reflected rejected table, operation, or sys_id values directly" in (change_log)
    assert "2 tests failed before implementation" in change_log
    assert "8 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 188 source files" in change_log
    assert "446 documentation tests passed" in change_log
    assert "2079 total tests passed at 93.84% coverage" in change_log
    assert "The generic provider-policy validator used by `generate_with_provider()`" in (
        operator_guide
    )
    assert "enforces the same 100-change" in operator_guide
    assert "preserving short operator-useful values such as `sys_user`" in (operator_guide)


def test_sprint_three_hundred_seventy_three_documents_provider_block_diagnostics() -> None:
    change_log = Path("docs/sprints/sprint-373-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Sanitized provider-policy block diagnostics" in change_log
    assert "configured provider ids and requested task names" in change_log
    assert "`ProviderBlocked`" in change_log
    assert "reflected `policy.provider_id` and `task` directly" in change_log
    assert "1 test failed before implementation" in change_log
    assert "9 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 188 source files" in change_log
    assert "447 documentation tests passed" in change_log
    assert "2081 total tests passed at 93.84% coverage" in change_log
    assert "Provider-policy block diagnostics are sanitized" in operator_guide
    assert "Configured provider ids and requested task names are redacted" in (operator_guide)
    assert "prompt construction still does not occur" in operator_guide


def test_sprint_three_hundred_seventy_four_documents_packet_validation_diagnostics() -> None:
    change_log = Path("docs/sprints/sprint-374-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Sanitized implementation-packet validation diagnostics" in change_log
    assert "model-provided safety decisions" in change_log
    assert "model-proposed table names" in change_log
    assert "unsupported safety decision values and unexpected table names directly" in (change_log)
    assert "2 tests failed before implementation" in change_log
    assert "2 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 189 source files" in change_log
    assert "448 documentation tests passed" in change_log
    assert "2084 total tests passed at 93.88% coverage" in change_log
    assert "Implementation-packet validation diagnostics are sanitized" in (operator_guide)
    assert "Unsupported safety decisions and model-proposed table names" in (operator_guide)
    assert "Raw XML rejection diagnostics remain fixed strings" in operator_guide


def test_sprint_three_hundred_seventy_five_documents_raw_xml_scan_bounds() -> None:
    change_log = Path("docs/sprints/sprint-375-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Bounded raw XML validation traversal" in change_log
    assert "unbounded recursive traversal" in change_log
    assert "explicit bounded stack" in change_log
    assert "1,000 scanned nodes or 32 nested levels" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "5 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 189 source files" in change_log
    assert "449 documentation tests passed" in change_log
    assert "2088 total tests passed at 93.90% coverage" in change_log
    assert "Raw XML validation in implementation-packet responses is traversal-bounded" in (
        operator_guide
    )
    assert "exceeds 1,000 scanned nodes" in operator_guide
    assert "32 nested levels" in operator_guide
    assert "without echoing the rejected model payload" in operator_guide


def test_sprint_three_hundred_seventy_six_documents_packet_review_bounds() -> None:
    change_log = Path("docs/sprints/sprint-376-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Bounded implementation-packet review contracts" in change_log
    assert "oversized change lists" in change_log
    assert "oversized review-note collections" in change_log
    assert "non-string review items" in change_log
    assert "3 tests failed before implementation" in change_log
    assert "8 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 189 source files" in change_log
    assert "450 documentation tests passed" in change_log
    assert "2092 total tests passed at 93.91% coverage" in change_log
    assert "Implementation-packet response contracts enforce bounded review material" in (
        operator_guide
    )
    assert "at most 100 `test_plan` items" in operator_guide
    assert "Review items must be non-empty exact strings" in operator_guide


def test_sprint_three_hundred_seventy_seven_documents_packet_review_item_bounds() -> None:
    change_log = Path("docs/sprints/sprint-377-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Bounded implementation-packet review note content" in change_log
    assert "oversized text" in change_log
    assert "control-character injection" in change_log
    assert "2,000 characters" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "10 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 189 source files" in change_log
    assert "451 documentation tests passed" in change_log
    assert "2095 total tests passed at 93.91% coverage" in change_log
    assert "no longer than 2,000" in operator_guide
    assert "characters and must not contain control characters" in operator_guide
    assert "must not contain control characters" in operator_guide
    assert "do not echo rejected note content" in operator_guide


def test_sprint_three_hundred_seventy_eight_documents_feedback_note_sanitization() -> None:
    change_log = Path("docs/sprints/sprint-378-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Sanitized manual-review automation feedback" in change_log
    assert "`operator_feedback` entries with `str()`" in change_log
    assert "raw newlines" in change_log
    assert "skips non-string values" in change_log
    assert "2,000 characters including the truncation marker" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "2 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 189 source files" in change_log
    assert "452 documentation tests passed" in change_log
    assert "2098 total tests passed at 93.91% coverage" in change_log
    assert "Manual-review automation feedback is sanitized" in operator_guide
    assert "non-string values are skipped" in operator_guide
    assert "capped at 2,000 characters including the" in operator_guide


def test_sprint_three_hundred_seventy_nine_documents_surface_reason_sanitization() -> None:
    change_log = Path("docs/sprints/sprint-379-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Sanitized surface-operation eligibility reasons" in change_log
    assert "`surface_operation_plan.operations[].kind`" in change_log
    assert "`reason_codes[]` directly with `str()` conversion" in change_log
    assert "non-string values are skipped" in change_log
    assert "stable `unsupported surface operation:`" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "2 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 189 source files" in change_log
    assert "453 documentation tests passed" in change_log
    assert "2101 total tests passed at 93.91% coverage" in change_log
    assert "Unsupported surface-operation eligibility reasons are sanitized" in (operator_guide)
    assert "Surface operation `kind` and `reason_codes` values are treated as" in (operator_guide)
    assert "Non-string reason" in operator_guide
    assert "codes are skipped instead of coerced with `str()`" in operator_guide


def test_sprint_three_hundred_eighty_documents_surface_reason_collection_bounds() -> None:
    change_log = Path("docs/sprints/sprint-380-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Bounded surface-operation reason collections" in change_log
    assert "every unsupported operation and every reason code" in change_log
    assert "string-valued `reason_codes` field as an iterable" in change_log
    assert "at most 50 unsupported operations" in change_log
    assert "fixed omitted-count markers" in change_log
    assert "3 tests failed before implementation" in change_log
    assert "5 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 189 source files" in change_log
    assert "454 documentation tests passed" in change_log
    assert "2105 total tests passed at 93.90% coverage" in change_log
    assert "Surface-operation reason generation is collection-bounded" in operator_guide
    assert "at most" in operator_guide
    assert "50 unsupported surface-operation entries" in operator_guide
    assert "malformed" in operator_guide
    assert "non-list `reason_codes` values are ignored" in operator_guide


def test_sprint_three_hundred_eighty_one_documents_manual_work_note_sanitization() -> None:
    change_log = Path("docs/sprints/sprint-381-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Sanitized manual-review ServiceNow work notes" in change_log
    assert "joined `eligibility_reasons` directly" in change_log
    assert "malformed candidate reasons could crash" in change_log
    assert "each emitted value is capped at 500 characters" in change_log
    assert "omitted-count markers" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "2 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 189 source files" in change_log
    assert "455 documentation tests passed" in change_log
    assert "2108 total tests passed at 93.90% coverage" in change_log
    assert "Manual-review ServiceNow work-note feedback is sanitized again" in (operator_guide)
    assert "each emitted value is capped at 500 characters" in operator_guide
    assert "candidate was assembled outside the normal validated model path" in (operator_guide)


def test_sprint_three_hundred_eighty_two_documents_external_build_work_notes() -> None:
    change_log = Path("docs/sprints/sprint-382-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Sanitized external-build ServiceNow work notes" in change_log
    assert "`ExternalBuildResult.build_reference`" in change_log
    assert "`ExternalBuildResult.message` directly" in change_log
    assert "500-character cap" in change_log
    assert "structured-field allowlist" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "2 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 189 source files" in change_log
    assert "456 documentation tests passed" in change_log
    assert "2111 total tests passed at 93.90% coverage" in change_log
    assert "External build result work notes are sanitized" in operator_guide
    assert "Build references" in operator_guide
    assert "`u_ai_build_reference` continue to carry the original build" in (operator_guide)


def test_sprint_three_hundred_eighty_three_documents_build_claim_work_notes() -> None:
    change_log = Path("docs/sprints/sprint-383-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Sanitized build-claim ServiceNow work notes" in change_log
    assert "`_build_claim_work_notes()`" in change_log
    assert "lifecycle event id directly" in change_log
    assert "500-character cap" in change_log
    assert "Structured build-claim audit events" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "4 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 189 source files" in change_log
    assert "457 documentation tests passed" in change_log
    assert "2114 total tests passed at 93.90% coverage" in change_log
    assert "Build-claim work notes sanitize lifecycle event ids" in operator_guide
    assert "capped at 500 characters including the truncation marker" in operator_guide
    assert "Structured build-claim audit events continue to carry the original" in (operator_guide)


def test_sprint_three_hundred_eighty_four_documents_runtime_failure_work_notes() -> None:
    change_log = Path("docs/sprints/sprint-384-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Sanitized runtime failure ServiceNow work notes" in change_log
    assert "`_servicenow_failure_notifier()`" in change_log
    assert "redacted only configured literal secrets" in change_log
    assert "`safe_work_note_value()`" in change_log
    assert "lifecycle event id, job id, and failure message" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "6 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "458 documentation tests passed" in change_log
    assert "2117 total tests passed at 93.91% coverage" in change_log
    assert "Each interpolated value is treated as untrusted" in operator_guide
    assert "lifecycle event ids, job ids, and failure messages are redacted" in operator_guide
    assert "capped at 500 characters including the truncation marker" in operator_guide


def test_sprint_three_hundred_eighty_five_documents_runtime_completion_work_notes() -> None:
    change_log = Path("docs/sprints/sprint-385-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Sanitized runtime completion ServiceNow work notes" in change_log
    assert "`_servicenow_complete_notifier()`" in change_log
    assert "completion lifecycle event id directly" in change_log
    assert "`safe_work_note_value()`" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "3 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "459 documentation tests passed" in change_log
    assert "2120 total tests passed at 93.91% coverage" in change_log
    assert "Runtime completion closeout also writes a ServiceNow work note" in operator_guide
    assert "The completion lifecycle event id is redacted" in operator_guide
    assert "capped at 500 characters including the truncation marker" in operator_guide


def test_sprint_three_hundred_eighty_six_documents_handoff_work_notes() -> None:
    change_log = Path("docs/sprints/sprint-386-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Sanitized retrieved Update Set handoff work notes" in change_log
    assert "`create_update_set_handoff()`" in change_log
    assert "`_handoff_work_notes()`" in change_log
    assert "`safe_work_note_value()`" in change_log
    assert "`u_ai_artifact_reference` continue to carry the original references" in (change_log)
    assert "2 tests failed before implementation" in change_log
    assert "3 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "460 documentation tests passed" in change_log
    assert "2123 total tests passed at 93.91% coverage" in change_log
    assert "Retrieved Update Set handoff work-note values are sanitized" in operator_guide
    assert "candidate artifact reference are redacted" in operator_guide
    assert "Structured handoff fields continue to carry the original references" in (operator_guide)


def test_sprint_three_hundred_eighty_seven_documents_intake_feedback_work_notes() -> None:
    change_log = Path("docs/sprints/sprint-387-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Sanitized intake feedback work notes" in change_log
    assert "`intake_feedback_work_note()`" in change_log
    assert "reason or guidance collections" in change_log
    assert "`safe_work_note_value()`" in change_log
    assert "capped at 50 entries each" in change_log
    assert "3 tests failed before implementation" in change_log
    assert "12 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "461 documentation tests passed" in change_log
    assert "2127 total tests passed at 93.91% coverage" in change_log
    assert "Intake feedback work notes are sanitized before delivery" in operator_guide
    assert "Story numbers, reason codes, operator guidance, and suggested rewrites" in (
        operator_guide
    )
    assert "at most 50 reason codes and 50 guidance items" in operator_guide


def test_sprint_three_hundred_eighty_eight_documents_artifact_handoff_work_notes() -> None:
    change_log = Path("docs/sprints/sprint-388-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Sanitized artifact handoff summary work notes" in change_log
    assert "`build_artifact_handoff_work_note()`" in change_log
    assert "`safe_work_note_value()`" in change_log
    assert "report paths and summary values" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "3 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "462 documentation tests passed" in change_log
    assert "2130 total tests passed at 93.91% coverage" in change_log
    assert "The artifact handoff work note sanitizes the report path" in operator_guide
    assert "summary values before delivery" in operator_guide
    assert "500 characters including the truncation marker" in operator_guide


def test_sprint_three_hundred_eighty_nine_documents_cli_summary_output() -> None:
    change_log = Path("docs/sprints/sprint-389-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Sanitized CLI summary output" in change_log
    assert "`render_summary()`" in change_log
    assert "`safe_work_note_value()`" in change_log
    assert "summary keys and values" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "6 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "463 documentation tests passed" in change_log
    assert "2133 total tests passed at 93.91% coverage" in change_log
    assert "CLI summary output is sanitized before printing" in operator_guide
    assert "summary keys and values as untrusted report data" in operator_guide
    assert "capped at 500 characters including the truncation marker" in operator_guide


def test_sprint_three_hundred_ninety_documents_admin_artifact_payload_keys() -> None:
    change_log = Path("docs/sprints/sprint-390-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Sanitized admin artifact payload keys" in change_log
    assert "dictionary keys" in change_log
    assert "`safe_work_note_value()`" in change_log
    assert "deterministic duplicate suffixes" in change_log
    assert "3 tests failed before implementation" in change_log
    assert "3 tests" in change_log
    assert "20 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "464 documentation tests passed" in change_log
    assert "2137 total tests passed at 93.90% coverage" in change_log
    assert "Admin artifact payload views sanitize dictionary keys" in operator_guide
    assert "Persisted artifact payload keys are treated as untrusted report data" in (
        operator_guide
    )
    assert "deterministic duplicate suffix" in operator_guide


def test_sprint_934_documents_admin_artifact_payload_key_string_subclass_boundary() -> (
    None
):
    change_log = Path("docs/sprints/sprint-934-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin artifact payload key string-subclass boundary" in change_log
    assert "`_admin_payload_key()`" in change_log
    assert "2 failing-first admin artifact payload key string-subclass assertions" in change_log
    assert "Non-string payload keys and string-subclass payload keys" in operator_guide
    assert "render as `[non-string key]`" in operator_guide


def test_sprint_three_hundred_ninety_one_documents_request_id_reflection() -> None:
    change_log = Path("docs/sprints/sprint-391-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Hardened reflected request IDs" in change_log
    assert "`X-JEDI-Request-ID`" in change_log
    assert "any visible ASCII" in change_log
    assert "letters, digits, hyphen, underscore, or period" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "5 tests" in change_log
    assert "13 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "465 documentation tests passed" in change_log
    assert "2140 total tests passed at 93.90% coverage" in change_log
    assert "Runtime response correlation never reflects arbitrary inbound request IDs" in (
        operator_guide
    )
    assert "`X-Request-ID` is preserved only when it is 1 to 128 ASCII characters" in (
        operator_guide
    )
    assert "secret-like assignment fragments are replaced with a generated UUID" in (operator_guide)


def test_sprint_three_hundred_ninety_two_documents_ascii_request_ids() -> None:
    change_log = Path("docs/sprints/sprint-392-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Enforced ASCII-only request IDs" in change_log
    assert "`X-Request-ID`" in change_log
    assert "Python `str.isalnum()` also accepts non-ASCII letters" in change_log
    assert "`X-JEDI-Request-ID`" in change_log
    assert "1 test failed before implementation" in change_log
    assert "6 tests" in change_log
    assert "14 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "466 documentation tests passed" in change_log
    assert "2142 total tests passed at 93.90% coverage" in change_log
    assert "`X-Request-ID` is preserved only when it is 1 to 128 ASCII characters" in (
        operator_guide
    )
    assert "Values with non-ASCII characters" in operator_guide


def test_sprint_three_hundred_ninety_three_documents_duplicate_payload_keys() -> None:
    change_log = Path("docs/sprints/sprint-393-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Bounded duplicate artifact payload keys" in change_log
    assert "duplicate suffix was appended after that cap" in change_log
    assert "same 500-character key budget" in change_log
    assert "1 test failed before implementation" in change_log
    assert "4 tests" in change_log
    assert "21 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "467 documentation tests passed" in change_log
    assert "2144 total tests passed at 93.90% coverage" in change_log
    assert "the duplicate suffix is included inside the same 500-character bound" in (
        operator_guide
    )


def test_sprint_three_hundred_ninety_four_documents_empty_payload_keys() -> None:
    change_log = Path("docs/sprints/sprint-394-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Non-empty artifact payload key diagnostics" in change_log
    assert "keys that sanitize to an empty label" in change_log
    assert "`[empty key]`" in change_log
    assert "without changing the stored artifact payload" in change_log
    assert "1 test failed before implementation" in change_log
    assert "5 tests" in change_log
    assert "22 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "468 documentation tests passed" in change_log
    assert "2146 total tests passed at 93.92% coverage" in change_log
    assert "If a payload key sanitizes to an empty label" in operator_guide
    assert "the diagnostic view renders it as `[empty key]`" in operator_guide


def test_sprint_three_hundred_ninety_five_documents_truncation_marker_collision() -> None:
    change_log = Path("docs/sprints/sprint-395-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Collision-safe artifact truncation marker" in change_log
    assert "cannot overwrite a user-supplied payload key" in change_log
    assert "`__jedi_payload_truncated__`" in change_log
    assert "`__jedi_payload_truncated__ [duplicate 2]`" in change_log
    assert "1 test failed before implementation" in change_log
    assert "6 tests" in change_log
    assert "23 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "469 documentation tests passed" in change_log
    assert "2148 total tests passed at 93.92% coverage" in change_log
    assert "internal `__jedi_payload_truncated__` diagnostic marker" in operator_guide
    assert "the user value remains visible" in operator_guide
    assert "deterministic duplicate suffix" in operator_guide


def test_sprint_three_hundred_ninety_six_documents_alert_header_bounds() -> None:
    change_log = Path("docs/sprints/sprint-396-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Bounded alert webhook metadata headers" in change_log
    assert "cannot be oversized" in change_log
    assert "`alert_id`, `job_id`, `event_id`, story number, and correlation id" in (change_log)
    assert "longer than 256 characters before sending" in change_log
    assert "5 parameterized cases failed before implementation" in change_log
    assert "12 tests" in change_log
    assert "30 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "470 documentation tests passed" in change_log
    assert "2154 total tests passed at 93.92% coverage" in change_log
    assert "exceeding 256 characters is rejected before transport invocation" in (operator_guide)
    assert "oversized metadata propagation" in operator_guide


def test_sprint_three_hundred_ninety_seven_documents_alert_body_text_bounds() -> None:
    change_log = Path("docs/sprints/sprint-397-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Pre-serialization alert body text bounds" in change_log
    assert "cannot force unbounded JSON serialization" in change_log
    assert "`severity`, `status`, `summary`, `detail`, and `operator_action`" in (change_log)
    assert "longer than 16 KiB before calling the JSON encoder" in change_log
    assert "5 parameterized cases failed before implementation" in change_log
    assert "17 tests" in change_log
    assert "35 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "471 documentation tests passed" in change_log
    assert "2160 total tests passed at 93.93% coverage" in change_log
    assert "Alert body text fields are bounded before JSON serialization" in operator_guide
    assert "longer than 16 KiB before calling the JSON encoder or transport" in (operator_guide)
    assert "not the generated value" in operator_guide


def test_sprint_three_hundred_ninety_eight_documents_alert_routing_taxonomy() -> None:
    change_log = Path("docs/sprints/sprint-398-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert routing taxonomy gate" in change_log
    assert "cannot be arbitrary generated strings" in change_log
    assert "Allowed severities are `critical`, `warning`, and `info`" in change_log
    assert "allowed statuses are `failed`, `rejected`, and `stale_requeued`" in (change_log)
    assert "2 parameterized cases failed before implementation" in change_log
    assert "19 tests" in change_log
    assert "37 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "472 documentation tests passed" in change_log
    assert "2163 total tests passed at 93.93% coverage" in change_log
    assert "Alert routing fields use a fixed taxonomy before delivery" in operator_guide
    assert "`severity` must be one of `critical`, `warning`, or `info`" in (operator_guide)
    assert "`status` must be one of `failed`, `rejected`, or `stale_requeued`" in (operator_guide)
    assert "not the supplied value" in operator_guide


def test_sprint_three_hundred_ninety_nine_documents_alert_metadata_nonblank() -> None:
    change_log = Path("docs/sprints/sprint-399-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Nonblank alert metadata headers" in change_log
    assert "cannot be empty or padded" in change_log
    assert "blank `Idempotency-Key` values" in change_log
    assert "`alert_id`, `job_id`, `event_id`, story number, and correlation id" in (change_log)
    assert "5 parameterized cases failed before implementation" in change_log
    assert "24 tests" in change_log
    assert "42 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "473 documentation tests passed" in change_log
    assert "2169 total tests passed at 93.93% coverage" in change_log
    assert "Empty or padded alert metadata values are also rejected" in operator_guide
    assert "prevent blank idempotency keys" in operator_guide
    assert "ambiguous correlation metadata" in operator_guide


def test_sprint_four_hundred_documents_alert_timestamp_timezone() -> None:
    change_log = Path("docs/sprints/sprint-400-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Timezone-aware alert timestamps" in change_log
    assert "cannot be ambiguous local-time values" in change_log
    assert "naive `created_at` datetimes" in change_log
    assert "before JSON serialization or HTTP transport" in change_log
    assert "1 test failed before implementation" in change_log
    assert "15 tests" in change_log
    assert "44 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "474 documentation tests passed" in change_log
    assert "2172 total tests passed at 93.93% coverage" in change_log
    assert "Alert timestamps must be timezone-aware before delivery" in operator_guide
    assert "rejects naive `created_at` values" in operator_guide
    assert "ambiguous local-time alert records" in operator_guide


def test_sprint_four_hundred_one_documents_stale_requeue_preview_bounds() -> None:
    change_log = Path("docs/sprints/sprint-401-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Bounded stale requeue alert job-id previews" in change_log
    assert "cannot create unbounded alert detail text" in change_log
    assert "joined every requeued job id" in change_log
    assert "preview at most 50 job ids" in change_log
    assert "omitted-count marker" in change_log
    assert "1 test failed before implementation" in change_log
    assert "2 tests" in change_log
    assert "45 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "475 documentation tests passed" in change_log
    assert "2174 total tests passed at 93.93% coverage" in change_log
    assert "previews at most 50 job ids" in operator_guide
    assert "omitted-count marker" in operator_guide
    assert "bounds alert construction before webhook serialization" in operator_guide


def test_sprint_four_hundred_two_documents_generated_alert_diagnostic_bounds() -> None:
    change_log = Path("docs/sprints/sprint-402-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Bounded generated alert diagnostics" in change_log
    assert "large upstream diagnostic strings" in change_log
    assert "preserved the full redacted string" in change_log
    assert "cap it at 16 KiB" in change_log
    assert "standard alert truncation marker" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "4 tests" in change_log
    assert "47 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "476 documentation tests passed" in change_log
    assert "2177 total tests passed at 93.93% coverage" in change_log
    assert "Worker-failure and rejected-job alerts redact diagnostic text" in operator_guide
    assert "cap that detail at 16 KiB" in operator_guide
    assert "keeps oversized upstream exceptions" in operator_guide


def test_sprint_four_hundred_three_documents_generated_alert_timezone_bounds() -> None:
    change_log = Path("docs/sprints/sprint-403-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Timezone-aware generated alert construction" in change_log
    assert "ambiguous local-time datetimes" in change_log
    assert "before an `ExternalAlert` is returned" in change_log
    assert "naive source timestamps" in change_log
    assert "3 tests failed before implementation" in change_log
    assert "4 tests" in change_log
    assert "50 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "477 documentation tests passed" in change_log
    assert "2181 total tests passed at 93.93% coverage" in change_log
    assert "Generated alert constructors also reject naive source timestamps" in (operator_guide)
    assert "timezone-aware job `updated_at` values" in operator_guide
    assert "ambiguous local server time" in operator_guide


def test_sprint_four_hundred_four_documents_stale_requeue_detail_bounds() -> None:
    change_log = Path("docs/sprints/sprint-404-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Bounded stale-requeue alert diagnostics" in change_log
    assert "oversized individual job ids" in change_log
    assert "preview count alone did not bound" in change_log
    assert "shared alert-detail safety path" in change_log
    assert "caps the resulting detail at 16 KiB" in change_log
    assert "1 test failed before implementation" in change_log
    assert "1 test" in change_log
    assert "51 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "478 documentation tests passed" in change_log
    assert "2183 total tests passed at 93.93% coverage" in change_log
    assert "Stale-job recovery alert details are also redacted" in operator_guide
    assert "single upstream job id can still be unexpectedly large" in operator_guide


def test_sprint_four_hundred_five_documents_generated_alert_metadata_bounds() -> None:
    change_log = Path("docs/sprints/sprint-405-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Constructor-safe generated alert metadata" in change_log
    assert "unsafe metadata is rejected before an `ExternalAlert` is returned" in (change_log)
    assert "newline-bearing ids" in change_log
    assert "validate the source job id, event id, story number, and correlation id" in (change_log)
    assert "7 tests failed before implementation" in change_log
    assert "8 tests" in change_log
    assert "58 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "479 documentation tests passed" in change_log
    assert "2191 total tests passed at 93.93% coverage" in change_log
    assert "Generated alert constructors reject unsafe metadata" in operator_guide
    assert "same timestamp, body text, routing, and webhook-header metadata validators" in (
        operator_guide
    )
    assert "header-injection characters" in operator_guide


def test_sprint_four_hundred_six_documents_lifecycle_webhook_credential_bounds() -> None:
    change_log = Path("docs/sprints/sprint-406-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Bounded lifecycle webhook credentials" in change_log
    assert "oversized inbound credential headers" in change_log
    assert "capped at 8 KiB" in change_log
    assert "before integer parsing or replay-window clock checks" in change_log
    assert "before constant-time comparison" in change_log
    assert "3 tests failed before implementation" in change_log
    assert "31 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "480 documentation tests passed" in change_log
    assert "2195 total tests passed at 93.93% coverage" in change_log
    assert "also capped at 8 KiB before integer parsing" in operator_guide
    assert "oversized credential probes" in operator_guide


def test_sprint_four_hundred_seven_documents_lifecycle_webhook_ascii_credentials() -> None:
    change_log = Path("docs/sprints/sprint-407-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ASCII-only lifecycle webhook credentials" in change_log
    assert "non-ASCII inbound credential values" in change_log
    assert "before `hmac.compare_digest()`" in change_log
    assert "measured in bytes rather than Python code points" in change_log
    assert "2 tests failed before implementation" in change_log
    assert "33 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "481 documentation tests passed" in change_log
    assert "2198 total tests passed at 93.93% coverage" in change_log
    assert "rejected before constant-time comparison when they are non-ASCII" in (operator_guide)
    assert "cap measured on ASCII bytes" in operator_guide
    assert "non-ASCII credential probes" in operator_guide


def test_sprint_four_hundred_eight_documents_lifecycle_hmac_signature_shapes() -> None:
    change_log = Path("docs/sprints/sprint-408-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Shaped lifecycle HMAC signatures" in change_log
    assert "malformed signature headers are rejected" in change_log
    assert "before constant-time comparison" in change_log
    assert "exactly 64 hexadecimal characters" in change_log
    assert "Base64 that decodes to a 32-byte SHA-256 MAC" in change_log
    assert "3 tests failed before implementation" in change_log
    assert "36 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "482 documentation tests passed" in change_log
    assert "2202 total tests passed at 93.94% coverage" in change_log
    assert "HMAC signature headers must match one of those two exact shapes" in (operator_guide)
    assert "64 hexadecimal characters" in operator_guide
    assert "Base64 value that decodes to a 32-byte SHA-256 MAC" in operator_guide


def test_sprint_four_hundred_nine_documents_configured_lifecycle_secret_bounds() -> None:
    change_log = Path("docs/sprints/sprint-409-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Configured lifecycle webhook secret validation" in change_log
    assert "malformed configured webhook secrets are rejected" in change_log
    assert "before request authentication runs" in change_log
    assert "ASCII-only, no-padding, no-control-character" in change_log
    assert "4 tests failed before implementation" in change_log
    assert "40 tests" in change_log
    assert "all checks passed" in change_log
    assert "no issues found in 190 source files" in change_log
    assert "483 documentation tests passed" in change_log
    assert "2207 total tests passed at 93.95% coverage" in change_log
    assert "configured lifecycle webhook signing secret is validated" in operator_guide
    assert "fail closed as invalid runtime configuration with `503`" in operator_guide
    assert "future alternate config loaders aligned" in operator_guide


def test_sprint_four_hundred_ten_documents_configured_admin_token_bounds() -> None:
    change_log = Path("docs/sprints/sprint-410-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Configured admin bearer token validation" in change_log
    assert "malformed configured admin API tokens are rejected" in change_log
    assert "before inbound bearer credentials are compared" in change_log
    assert "ASCII-only, no-padding, no-control-character" in change_log
    assert "4 tests" in change_log
    assert "admin artifact API token is invalid" in change_log
    assert "484 documentation tests passed" in change_log
    assert "2212 total tests passed at 93.95% coverage" in change_log
    assert "configured admin bearer token" in operator_guide
    assert "invalid runtime configuration with `503`" in operator_guide
    assert "before any inbound token comparison runs" in operator_guide


def test_sprint_four_hundred_eleven_documents_configured_console_credential_bounds() -> None:
    change_log = Path("docs/sprints/sprint-411-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Configured admin console credential validation" in change_log
    assert "malformed configured console credentials are rejected" in change_log
    assert "before inbound Basic-auth payloads are decoded or compared" in change_log
    assert "non-ASCII, padded, control-character-bearing" in change_log
    assert "8 tests" in change_log
    assert "admin console credentials are invalid" in change_log
    assert "485 documentation tests passed" in change_log
    assert "2221 total tests passed at 93.95% coverage" in change_log
    assert "validates configured console credentials before parsing inbound Basic-auth" in (
        operator_guide
    )
    assert "before inbound Basic auth is decoded or compared" in operator_guide


def test_sprint_four_hundred_twelve_documents_basic_auth_ascii_payloads() -> None:
    change_log = Path("docs/sprints/sprint-412-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ASCII-only Basic-auth encoded payloads" in change_log
    assert "non-ASCII encoded credential sections are rejected" in change_log
    assert "before Base64 decoding" in change_log
    assert "8 KiB limit is measured on encoded ASCII bytes" in change_log
    assert "1 test" in change_log
    assert "25 tests passed" in change_log
    assert "486 documentation tests passed" in change_log
    assert "2223 total tests passed at 93.95% coverage" in change_log
    assert "Basic-auth encoded credential sections are ASCII-only before decoding" in (
        operator_guide
    )
    assert "8192-byte cap is measured on the encoded ASCII bytes" in operator_guide


def test_sprint_four_hundred_thirteen_documents_bounded_rate_limit_keys() -> None:
    change_log = Path("docs/sprints/sprint-413-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Bounded rate-limit bucket keys" in change_log
    assert "caller-provided bucket keys are bounded and sanitized before storage" in change_log
    assert "Safe printable ASCII keys up to 256 bytes are preserved" in change_log
    assert "deterministic `sha256:<digest>` bucket identifiers" in change_log
    assert "3 tests" in change_log
    assert "11 tests passed" in change_log
    assert "487 documentation tests passed" in change_log
    assert "2227 total tests passed at 93.95% coverage" in change_log
    assert "Rate-limit bucket keys are bounded before storage" in operator_guide
    assert "Safe printable ASCII keys up to 256 bytes" in operator_guide
    assert "replaced with deterministic `sha256:<digest>`" in operator_guide


def test_sprint_four_hundred_fourteen_documents_capped_rate_limit_buckets() -> None:
    change_log = Path("docs/sprints/sprint-414-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Capped rate-limit bucket cardinality" in change_log
    assert "live bucket count is bounded" in change_log
    assert "at most 10000 live buckets" in change_log
    assert "shared `rate-limit-overflow` bucket" in change_log
    assert "2 tests" in change_log
    assert "5 tests passed" in change_log
    assert "488 documentation tests passed" in change_log
    assert "2230 total tests passed at 93.95% coverage" in change_log
    assert "Rate-limit state is also bounded by bucket count" in operator_guide
    assert "defaults to at most 10000 live buckets" in operator_guide
    assert "shared `rate-limit-overflow`" in operator_guide


def test_sprint_four_hundred_fifteen_documents_runtime_rate_limit_bucket_caps() -> None:
    change_log = Path("docs/sprints/sprint-415-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime-configurable rate-limit bucket caps" in change_log
    assert "`JEDI_LIFECYCLE_RATE_LIMIT_MAX_BUCKETS`" in change_log
    assert "`JEDI_ADMIN_RATE_LIMIT_MAX_BUCKETS`" in change_log
    assert "strict ASCII base-10 integer parser" in change_log
    assert "21 tests passed" in change_log
    assert "489 documentation tests passed" in change_log
    assert "2236 total tests passed at 93.95% coverage" in change_log
    assert "JEDI_LIFECYCLE_RATE_LIMIT_MAX_BUCKETS" in operator_guide
    assert "JEDI_ADMIN_RATE_LIMIT_MAX_BUCKETS" in operator_guide
    assert "10000 live buckets per process" in operator_guide


def test_sprint_four_hundred_sixteen_documents_rate_limit_bucket_cap_ceiling() -> None:
    change_log = Path("docs/sprints/sprint-416-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Upper-bounded rate-limit bucket caps" in change_log
    assert "hard upper bound" in change_log
    assert "above `100000`" in change_log
    assert "`JEDI_LIFECYCLE_RATE_LIMIT_MAX_BUCKETS`" in change_log
    assert "`JEDI_ADMIN_RATE_LIMIT_MAX_BUCKETS`" in change_log
    assert "2 tests" in change_log
    assert "4 tests passed" in change_log
    assert "490 documentation tests passed" in change_log
    assert "2239 total tests passed at 93.95% coverage" in change_log
    assert "at or below 100000 buckets" in operator_guide
    assert "fail runtime validation before API construction" in operator_guide


def test_sprint_four_hundred_seventeen_documents_rate_limit_request_cap_ceiling() -> None:
    change_log = Path("docs/sprints/sprint-417-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Upper-bounded rate-limit request caps" in change_log
    assert "`max_requests`" in change_log
    assert "above `10000`" in change_log
    assert "`JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS`" in change_log
    assert "`JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS`" in change_log
    assert "2 tests" in change_log
    assert "6 tests passed" in change_log
    assert "491 documentation tests passed" in change_log
    assert "2242 total tests passed at 93.96% coverage" in change_log
    assert "at or below 10000 requests per bucket" in operator_guide
    assert "unbounded number of request timestamps" in operator_guide


def test_sprint_four_hundred_eighteen_documents_rate_limit_window_ceiling() -> None:
    change_log = Path("docs/sprints/sprint-418-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Upper-bounded rate-limit windows" in change_log
    assert "`window_seconds`" in change_log
    assert "above `86400` seconds" in change_log
    assert "`JEDI_LIFECYCLE_RATE_LIMIT_WINDOW_SECONDS`" in change_log
    assert "`JEDI_ADMIN_RATE_LIMIT_WINDOW_SECONDS`" in change_log
    assert "2 tests" in change_log
    assert "8 tests passed" in change_log
    assert "492 documentation tests passed" in change_log
    assert "2245 total tests passed at 93.96% coverage" in change_log
    assert "at or below 86400 seconds" in operator_guide
    assert "longer than one day" in operator_guide


def test_sprint_four_hundred_nineteen_documents_backward_clock_safe_rate_limiting() -> None:
    change_log = Path("docs/sprints/sprint-419-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Backward-clock-safe rate limiting" in change_log
    assert "backward process-clock movement" in change_log
    assert "inflated `Retry-After`" in change_log
    assert "stored older timestamps" in change_log
    assert "2 tests" in change_log
    assert "10 tests passed" in change_log
    assert "19 tests passed" in change_log
    assert "493 documentation tests passed" in change_log
    assert "2248 total tests passed at 93.96% coverage" in change_log
    assert "clamps observed process time" in operator_guide
    assert "inflated `Retry-After` values" in operator_guide


def test_sprint_four_hundred_twenty_documents_concurrent_safe_rate_limiting() -> None:
    change_log = Path("docs/sprints/sprint-420-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Concurrent-safe rate limiting" in change_log
    assert "without a critical section" in change_log
    assert "`max_requests=1`" in change_log
    assert "process-local lock" in change_log
    assert "1 concurrency test" in change_log
    assert "failed before implementation with 2 allowed decisions" in change_log
    assert "11 tests passed" in change_log
    assert "494 documentation tests passed" in change_log
    assert "2250 total tests passed at 93.96% coverage" in change_log
    assert "Limiter checks are serialized inside each process" in operator_guide
    assert "concurrent lifecycle or admin requests" in operator_guide


def test_sprint_four_hundred_twenty_one_documents_unstringifiable_handler_exception_redaction() -> (
    None
):
    change_log = Path("docs/sprints/sprint-421-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Unstringifiable handler exception redaction" in change_log
    assert "`str(exc)` inside `_redacting_handler()`" in change_log
    assert "`handler raised unstringifiable <ExceptionType>`" in change_log
    assert "1 failing-first test" in change_log
    assert "ValueError: client-secret-value" in change_log
    assert "20 tests passed" in change_log
    assert "495 documentation tests passed" in change_log
    assert "2252 total tests passed at 93.97% coverage" in change_log
    assert "Runtime handler redaction also tolerates malformed exception objects" in operator_guide
    assert "bypass redaction or leak credential text" in operator_guide


def test_sprint_four_hundred_twenty_two_documents_safe_unstringifiable_exception_type_labels() -> (
    None
):
    change_log = Path("docs/sprints/sprint-422-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Safe unstringifiable exception type labels" in change_log
    assert "exception class metadata can be mutated" in change_log
    assert "`client-secret-value`" in change_log
    assert "`***REDACTED***`" in change_log
    assert "ASCII Python identifier" in change_log
    assert "128 characters" in change_log
    assert "21 tests passed" in change_log
    assert "496 documentation tests passed" in change_log
    assert "2254 total tests passed at 93.97% coverage" in change_log
    assert "ASCII Python identifier no longer than 128" in operator_guide
    assert "`handler raised unstringifiable exception`" in operator_guide


def test_sprint_four_hundred_twenty_three_documents_core_worker_unstringifiable_exceptions() -> (
    None
):
    change_log = Path("docs/sprints/sprint-423-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Core worker unstringifiable exception handling" in change_log
    assert "`process_one_fulfillment_job()`" in change_log
    assert "`str(exc)` directly" in change_log
    assert "`str(notifier_exc)` directly" in change_log
    assert "2 failing-first tests" in change_log
    assert "ValueError: client-secret-value" in change_log
    assert "12 tests passed" in change_log
    assert "497 documentation tests passed" in change_log
    assert "2257 total tests passed at 93.95% coverage" in change_log
    assert (
        "core worker also tolerates malformed handler and notifier exception objects"
        in operator_guide
    )
    assert "`worker raised unstringifiable exception`" in operator_guide


def test_sprint_four_hundred_twenty_four_documents_runtime_worker_logging_safe_exceptions() -> None:
    change_log = Path("docs/sprints/sprint-424-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime-worker logging-safe exception formatting" in change_log
    assert "called `str(error)` in the logger arguments" in change_log
    assert "4 failing-first tests" in change_log
    assert "ValueError: client-secret-value" in change_log
    assert "32 tests passed" in change_log
    assert "498 documentation tests passed" in change_log
    assert "2262 total tests passed at 93.93% coverage" in change_log
    assert (
        "Runtime-worker maintenance and alert logging also tolerates malformed exception objects"
        in operator_guide
    )
    assert "`runtime worker raised unstringifiable exception`" in operator_guide


def test_sprint_four_hundred_twenty_five_documents_shared_safe_exception_diagnostics() -> None:
    change_log = Path("docs/sprints/sprint-425-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Shared safe exception diagnostics" in change_log
    assert "`jedi_devproject.exception_diagnostics.exception_diagnostic_message()`" in change_log
    assert "CLI error rendering still called `str(exc)` directly" in change_log
    assert "76 tests passed" in change_log
    assert "no issues found in 193 source files" in change_log
    assert "499 documentation tests passed" in change_log
    assert "2268 total tests passed at 93.97% coverage" in change_log
    assert (
        "CLI exception rendering uses the shared safe exception diagnostic helper" in operator_guide
    )
    assert "Exception diagnostic formatting is centralized" in operator_guide
    assert "handler wrappers, core worker failure persistence" in operator_guide


def test_sprint_four_hundred_twenty_six_documents_lifecycle_alert_logging_safe_exceptions() -> None:
    change_log = Path("docs/sprints/sprint-426-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Lifecycle rejected-job alert logging-safe exceptions" in change_log
    assert "called `str(exc)` while preparing the warning log message" in change_log
    assert 'fallback_subject="lifecycle"' in change_log
    assert "1 failing-first lifecycle API test" in change_log
    assert "ValueError: client-secret-value" in change_log
    assert "41 tests passed" in change_log
    assert "500 documentation tests passed" in change_log
    assert "2270 total tests passed at 93.97% coverage" in change_log
    assert (
        "Rejected-job alert delivery failures also use the shared safe exception diagnostic helper"
        in operator_guide
    )
    assert "`lifecycle raised unstringifiable exception`" in operator_guide


def test_sprint_427_documents_runtime_config_numeric_parser_safe_exceptions() -> None:
    change_log = Path("docs/sprints/sprint-427-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime config numeric parser safe exceptions" in change_log
    assert "`str(exc)` while wrapping numeric parser errors" in change_log
    assert 'fallback_subject="runtime config"' in change_log
    assert "2 failing-first runtime config tests" in change_log
    assert "ValueError: client-secret-value" in change_log
    assert "2 tests passed" in change_log
    assert "501 documentation tests passed" in change_log
    assert "2273 total tests passed at 93.97% coverage" in change_log
    assert "Runtime numeric parser error wrapping also uses" in operator_guide
    assert "`runtime config raised unstringifiable exception`" in operator_guide


def test_sprint_428_documents_worker_optional_float_parser_safe_exceptions() -> None:
    change_log = Path("docs/sprints/sprint-428-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Worker optional-float parser safe exceptions" in change_log
    assert "`runtime_worker._optional_float()`" in change_log
    assert 'fallback_subject="runtime worker"' in change_log
    assert "1 failing-first worker settings test" in change_log
    assert "client-secret-value" in change_log
    assert "1 test passed" in change_log
    assert "502 documentation tests passed" in change_log
    assert "2275 total tests passed at 93.97% coverage" in change_log
    assert "Worker decimal parser error wrapping also uses" in operator_guide
    assert "`runtime worker raised unstringifiable exception`" in operator_guide


def test_sprint_429_documents_flow_roundtrip_import_failure_safe_diagnostics() -> None:
    change_log = Path("docs/sprints/sprint-429-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Flow roundtrip import failure safe diagnostics" in change_log
    assert "`run_flow_roundtrip()`" in change_log
    assert "`str(exc)` directly" in change_log
    assert 'fallback_subject="flow roundtrip"' in change_log
    assert "1 failing-first Flow round-trip test" in change_log
    assert "ValueError: client-secret-value" in change_log
    assert "2 tests passed" in change_log
    assert "503 documentation tests passed" in change_log
    assert "2277 total tests passed at 93.97% coverage" in change_log
    assert "Flow round-trip verification report details are also stringification-safe" in (
        operator_guide
    )
    assert "`flow roundtrip raised unstringifiable exception`" in operator_guide


def test_sprint_430_documents_flow_xml_evidence_invalid_shape_safe_diagnostics() -> None:
    change_log = Path("docs/sprints/sprint-430-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Flow XML evidence invalid-shape safe diagnostics" in change_log
    assert "`validate_flow_xml_shape_evidence()`" in change_log
    assert "`FlowXmlShapeEvidenceRecord.reason`" in change_log
    assert 'fallback_subject="flow xml evidence"' in change_log
    assert "1 failing-first Flow XML evidence test" in change_log
    assert "ValueError: client-secret-value" in change_log
    assert "2 tests passed" in change_log
    assert "504 documentation tests passed" in change_log
    assert "2279 total tests passed at 93.97% coverage" in change_log
    assert "Flow XML shape evidence invalid reasons are stringification-safe" in operator_guide
    assert "`flow xml evidence raised unstringifiable exception`" in operator_guide


def test_sprint_1009_documents_flow_xml_evidence_record_collection_guard() -> None:
    change_log = Path("docs/sprints/sprint-1009-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Flow XML evidence record collection guard" in change_log
    assert "`collect_flow_xml_evidence()`" in change_log
    assert "`_flow_evidence_records()`" in change_log
    assert "Flow XML evidence records contain non-JSON value" in change_log
    assert (
        "1 failing-first Flow XML evidence record collection subclass assertion"
        in change_log
    )
    assert (
        "Flow XML evidence collection record sets are exact containers"
        in operator_guide
    )
    assert (
        "`sys_hub_flow`, `sys_hub_action_instance`, "
        "`sys_hub_flow_logic_instance_v2`, `sys_update_xml`, and "
        "`sys_hub_flow_snapshot`"
        in operator_guide
    )
    assert "before flow matching, flow sys_id parsing" in operator_guide
    assert (
        "`test_collect_flow_xml_evidence_rejects_flow_record_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_collect_flow_xml_evidence_rejects_flow_record_subclass_without_leak`"
        in change_log
    )


def test_sprint_431_documents_cli_batch_blocked_reason_safe_diagnostics() -> None:
    change_log = Path("docs/sprints/sprint-431-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "CLI implementation-candidate batch blocked reason safe diagnostics" in change_log
    assert "`run_implementation_candidates_command()`" in change_log
    assert "`str(exc)` directly" in change_log
    assert 'fallback_subject="CLI batch"' in change_log
    assert "1 failing-first CLI batch test" in change_log
    assert "ValueError: client-secret-value" in change_log
    assert "2 tests passed" in change_log
    assert "505 documentation tests passed" in change_log
    assert "2281 total tests passed at 93.97% coverage" in change_log
    assert "CLI implementation-candidate batch blocked reasons are also" in operator_guide
    assert "`CLI batch raised unstringifiable exception`" in operator_guide


def test_sprint_432_documents_flow_graph_diff_structural_validation_error_routing() -> None:
    change_log = Path("docs/sprints/sprint-432-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Flow graph diff structural validation-error routing" in change_log
    assert "`validate_flow_graph_diff_candidate()`" in change_log
    assert "searched `str(exc)`" in change_log
    assert "`ValidationError.errors()[].loc` structurally" in change_log
    assert "1 failing-first Flow graph diff validator test" in change_log
    assert "ValueError: client-secret-value" in change_log
    assert "2 tests passed" in change_log
    assert "506 documentation tests passed" in change_log
    assert "2283 total tests passed at 93.96% coverage" in change_log
    assert "Flow graph diff unsupported-operation routing is based on structured" in (
        operator_guide
    )
    assert "without stringifying the original `ValidationError`" in operator_guide


def test_sprint_433_documents_servicenow_attachment_artifact_read_typed_errors() -> None:
    change_log = Path("docs/sprints/sprint-433-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow attachment artifact read typed errors" in change_log
    assert '`str(exc).startswith("artifact file exceeds ")`' in change_log
    assert "`ArtifactReadError.reason`" in change_log
    assert "`too_large`" in change_log
    assert "`not_regular`" in change_log
    assert "2 failing-first tests" in change_log
    assert "507 documentation tests passed" in change_log
    assert "2286 total tests passed at 93.96% coverage" in change_log
    assert "Attachment upload error classification uses typed artifact read reasons" in (
        operator_guide
    )
    assert "`ArtifactReadError.reason`" in operator_guide


def test_sprint_434_documents_cli_external_build_delivery_typed_success_requirement() -> None:
    change_log = Path("docs/sprints/sprint-434-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "CLI external-build delivery typed success requirement" in change_log
    assert '`str(exc) != "successful_build_required"`' in change_log
    assert "`SuccessfulBuildRequiredError`" in change_log
    assert "2 failing-first tests" in change_log
    assert "508 documentation tests passed" in change_log
    assert "2288 total tests passed at 93.96% coverage" in change_log
    assert "External-build result processing uses a typed" in operator_guide
    assert "`SuccessfulBuildRequiredError`" in operator_guide
    assert "does not compare exception message text" in operator_guide


def test_sprint_435_documents_local_input_loader_non_reflective_path_diagnostics() -> None:
    change_log = Path("docs/sprints/sprint-435-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Local input loader non-reflective path diagnostics" in change_log
    assert "`json_input_too_large`" in change_log
    assert "`json_input_must_be_regular_file`" in change_log
    assert "`project_config_too_large`" in change_log
    assert "`project_config_must_be_regular_file`" in change_log
    assert "4 failing-first tests" in change_log
    assert "509 documentation tests passed" in change_log
    assert "2293 total tests passed at 93.96% coverage" in change_log
    assert "raw config file path" in operator_guide
    assert "without echoing the raw input path" in operator_guide


def test_sprint_436_documents_lifecycle_webhook_invalid_utf8_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-436-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Lifecycle webhook invalid UTF-8 JSON rejection" in change_log
    assert "`UnicodeDecodeError`" in change_log
    assert "`json.loads(body)`" in change_log
    assert "`422 invalid lifecycle webhook JSON`" in change_log
    assert "1 failing-first lifecycle webhook test" in change_log
    assert "510 documentation tests passed" in change_log
    assert "2295 total tests passed at 93.96% coverage" in change_log
    assert "invalid UTF-8 request bodies" in operator_guide
    assert "`invalid lifecycle webhook JSON`" in operator_guide
    assert "exact raw request body before JSON decoding" in operator_guide


def test_sprint_437_documents_local_input_loader_invalid_utf8_diagnostics() -> None:
    change_log = Path("docs/sprints/sprint-437-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Local input loader invalid UTF-8 diagnostics" in change_log
    assert "`UnicodeDecodeError`" in change_log
    assert "`json_input_invalid_utf8`" in change_log
    assert "`project_config_invalid_utf8`" in change_log
    assert "2 failing-first tests" in change_log
    assert "511 documentation tests passed" in change_log
    assert "2298 total tests passed at 93.96% coverage" in change_log
    assert "`project_config_invalid_utf8`" in operator_guide
    assert "`json_input_invalid_utf8`" in operator_guide
    assert "payload fragments" in operator_guide


def test_sprint_438_documents_dotenv_loader_non_reflective_path_and_utf8_diagnostics() -> None:
    change_log = Path("docs/sprints/sprint-438-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Dotenv loader non-reflective path and UTF-8 diagnostics" in change_log
    assert "`dotenv_input_too_large`" in change_log
    assert "`dotenv_must_be_regular_file`" in change_log
    assert "`dotenv_invalid_utf8`" in change_log
    assert "`UnicodeDecodeError`" in change_log
    assert "3 failing-first tests" in change_log
    assert "512 documentation tests passed" in change_log
    assert "2302 total tests passed at 93.97% coverage" in change_log
    assert "`dotenv_invalid_utf8`" in operator_guide
    assert "without echoing raw env file paths" in operator_guide
    assert "credential-like payload fragments" in operator_guide


def test_sprint_439_documents_servicenow_transport_success_parse_hardening() -> None:
    change_log = Path("docs/sprints/sprint-439-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport successful response parse hardening" in change_log
    assert '`body.decode("utf-8")`' in change_log
    assert "`json.loads()`" in change_log
    assert "`_success_response_body_to_json()`" in change_log
    assert "`UnicodeDecodeError`" in change_log
    assert "`JSONDecodeError`" in change_log
    assert "2 failing-first transport tests" in change_log
    assert "513 documentation tests passed" in change_log
    assert "2305 total tests passed at 93.96% coverage" in change_log
    assert "Successful ServiceNow HTTP response parsing is also bounded" in operator_guide
    assert "valid UTF-8 JSON objects" in operator_guide
    assert "without echoing upstream body fragments" in operator_guide


def test_sprint_440_documents_servicenow_successful_result_list_shape_validation() -> None:
    change_log = Path("docs/sprints/sprint-440-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow successful result-list shape validation" in change_log
    assert "`_required_result_record_list()`" in change_log
    assert "`ServiceNow API response result must be a list`" in change_log
    assert "`ServiceNow API response result entries must be objects`" in change_log
    assert "2 failing-first tests" in change_log
    assert "514 documentation tests passed" in change_log
    assert "2308 total tests passed at 93.97% coverage" in change_log
    assert "validates successful `result` shapes" in operator_guide
    assert "list of objects" in operator_guide
    assert "without echoing the malformed `result` value" in operator_guide


def test_sprint_441_documents_servicenow_successful_result_object_shape_validation() -> None:
    change_log = Path("docs/sprints/sprint-441-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow successful result-object shape validation" in change_log
    assert "`_required_result_object()`" in change_log
    assert "`ServiceNow API response result must be an object`" in change_log
    assert "1 failing-first test" in change_log
    assert "515 documentation tests passed" in change_log
    assert "2310 total tests passed at 93.97% coverage" in change_log
    assert "ServiceNow single-record response handling validates" in operator_guide
    assert "create, update, upsert, or attachment metadata" in operator_guide
    assert "without echoing the malformed `result` value" in operator_guide


def test_sprint_442_documents_cicd_capability_malformed_result_classification() -> None:
    change_log = Path("docs/sprints/sprint-442-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "CI/CD capability malformed-result classification" in change_log
    assert "`malformed_result_payload`" in change_log
    assert "ambiguous `status_200` diagnostics" in change_log
    assert "1 failing-first CI/CD capability test" in change_log
    assert "516 documentation tests passed" in change_log
    assert "2312 total tests passed at 93.98% coverage" in change_log
    assert "Malformed successful CI/CD probe responses also fail closed" in operator_guide
    assert "records `malformed_result_payload`" in operator_guide
    assert "does not echo the malformed `result` value" in operator_guide


def test_sprint_443_documents_provider_candidate_field_name_normalization() -> None:
    change_log = Path("docs/sprints/sprint-443-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider candidate field-name normalization" in change_log
    assert "last-value-wins semantics" in change_log
    assert "field entry names must be unique" in change_log
    assert "field entry name must not contain whitespace or control characters" in change_log
    assert "5 provider normalization tests" in change_log
    assert "length-boundary test covers the documented 200-character cap" in change_log
    assert "517 documentation tests passed" in change_log
    assert "2318 total tests passed at 93.98% coverage" in change_log
    assert "Provider field names are also validated" in operator_guide
    assert "no longer than 200 characters" in operator_guide
    assert "do not echo the model-provided field name or value" in operator_guide


def test_sprint_444_documents_anthropic_max_token_ascii_integer_parsing() -> None:
    change_log = Path("docs/sprints/sprint-444-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Anthropic max-token ASCII integer parsing" in change_log
    assert "`ANTHROPIC_MAX_TOKENS`" in change_log
    assert "Python `int(text)`" in change_log
    assert "ASCII base-10 digits only" in change_log
    assert "3 failing-first Anthropic provider config tests" in change_log
    assert "518 documentation tests passed" in change_log
    assert "2322 total tests passed at 93.97% coverage" in change_log
    assert "`ANTHROPIC_MAX_TOKENS` must parse as ASCII base-10 digits only" in (
        operator_guide
    )
    assert "without signs, underscores, padding, non-ASCII digits" in operator_guide
    assert "cannot silently normalize numeric-looking deployment input" in operator_guide


def test_sprint_445_documents_anthropic_retry_after_ascii_decimal_parsing() -> None:
    change_log = Path("docs/sprints/sprint-445-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Anthropic retry-after ASCII decimal parsing" in change_log
    assert "Python `float(retry_after_header)`" in change_log
    assert "`+7`" in change_log
    assert "`7_0`" in change_log
    assert "`1e2`" in change_log
    assert "non-ASCII digit strings" in change_log
    assert "4 failing-first Anthropic provider retry tests" in change_log
    assert "519 documentation tests passed" in change_log
    assert "2327 total tests passed at 93.96% coverage" in change_log
    assert "Anthropic `retry-after` seconds must parse as ASCII decimal numbers" in (
        operator_guide
    )
    assert "without signs, underscores, exponent notation" in operator_guide
    assert "cannot silently normalize numeric-looking response values" in operator_guide


def test_sprint_446_documents_alert_sink_response_key_sanitization() -> None:
    change_log = Path("docs/sprints/sprint-446-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert sink response diagnostic key sanitization" in change_log
    assert "response object keys are treated as untrusted sink output" in change_log
    assert "`client_secret=...`" in change_log
    assert "non-string keys supplied by alternate transports" in change_log
    assert "`[non-string key]`" in change_log
    assert "2 failing-first alert delivery tests" in change_log
    assert "520 documentation tests passed" in change_log
    assert "2330 total tests passed at 93.93% coverage" in change_log
    assert "Alert sink response diagnostic keys are sanitized" in operator_guide
    assert "secret-like key text is redacted" in operator_guide
    assert "non-string keys become `[non-string key]`" in operator_guide


def test_sprint_447_documents_admin_artifact_non_string_payload_key_sanitization() -> None:
    change_log = Path("docs/sprints/sprint-447-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin artifact non-string payload key sanitization" in change_log
    assert "never flow through Python `str(key)`" in change_log
    assert "tuple and object keys" in change_log
    assert "`[non-string key]`" in change_log
    assert "`[non-string key] [duplicate 2]`" in change_log
    assert "1 failing-first admin artifact projection test" in change_log
    assert "521 documentation tests passed" in change_log
    assert "2332 total tests passed at 93.93% coverage" in change_log
    assert "Non-string payload keys render as `[non-string key]`" in operator_guide
    assert "instead of reflecting Python object representations" in operator_guide


def test_sprint_448_documents_admin_artifact_non_json_scalar_value_sanitization() -> None:
    change_log = Path("docs/sprints/sprint-448-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin artifact non-JSON scalar value sanitization" in change_log
    assert "unsupported scalar values cannot crash JSON or HTML diagnostic rendering" in (
        change_log
    )
    assert "bytes and object scalar values" in change_log
    assert "`[non-json value]`" in change_log
    assert "1 failing-first admin artifact view test" in change_log
    assert "522 documentation tests passed" in change_log
    assert "2334 total tests passed at 93.89% coverage" in change_log
    assert "Admin artifact payload scalar values are normalized" in operator_guide
    assert "unsupported scalar types such as bytes or Python objects" in operator_guide
    assert "also render as `[non-json value]`" in operator_guide


def test_sprint_933_documents_admin_artifact_payload_scalar_subclass_boundary() -> (
    None
):
    change_log = Path("docs/sprints/sprint-933-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin artifact payload scalar-subclass diagnostic boundary" in change_log
    assert "`_bounded_redacted_artifact_payload_node()`" in change_log
    assert "1 failing-first admin artifact payload scalar-subclass assertion" in change_log
    assert "Admin artifact payload string, boolean, and integer values" in operator_guide
    assert (
        "string, boolean, and integer subclasses render as `[non-json value]`"
        in operator_guide
    )


def test_sprint_937_documents_admin_artifact_payload_exact_container_boundary() -> (
    None
):
    change_log = Path("docs/sprints/sprint-937-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin artifact payload exact-container diagnostic boundary" in change_log
    assert "`_bounded_redacted_artifact_payload_node()`" in change_log
    assert "1 failing-first admin artifact payload container-subclass assertion" in change_log
    assert "Admin artifact payload views traverse only exact containers" in operator_guide
    assert "dictionary, list, and tuple subclasses render as `[non-json value]`" in (
        operator_guide
    )


def test_sprint_449_documents_admin_artifact_unstringifiable_payload_key_hardening() -> None:
    change_log = Path("docs/sprints/sprint-449-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin artifact unstringifiable payload key hardening" in change_log
    assert "not stringified during sensitive-key classification" in change_log
    assert "hostile or broken `__str__`" in change_log
    assert "1 failing-first admin artifact projection test" in change_log
    assert "523 documentation tests passed" in change_log
    assert "2336 total tests passed at 93.89% coverage" in change_log
    assert "Non-string keys are not stringified for sensitive-key classification" in (
        operator_guide
    )
    assert "malformed key objects cannot crash artifact diagnostics" in operator_guide


def test_sprint_450_documents_admin_artifact_circular_payload_traversal_hardening() -> None:
    change_log = Path("docs/sprints/sprint-450-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin artifact circular payload traversal hardening" in change_log
    assert "cyclic in-memory containers cannot recurse until failure" in change_log
    assert "self-referential dictionary payload" in change_log
    assert "`[circular reference]`" in change_log
    assert "1 failing-first admin artifact projection test" in change_log
    assert "524 documentation tests passed" in change_log
    assert "2338 total tests passed at 93.84% coverage" in change_log
    assert "Admin artifact payload traversal is cycle-safe" in operator_guide
    assert "renders the repeated container as `[circular reference]`" in operator_guide


def test_sprint_451_documents_admin_artifact_payload_depth_bound_hardening() -> None:
    change_log = Path("docs/sprints/sprint-451-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin artifact payload depth-bound hardening" in change_log
    assert "deeply nested but acyclic payloads cannot force unbounded" in change_log
    assert "excessively deep acyclic dictionary payload" in change_log
    assert "`[max depth exceeded]`" in change_log
    assert "1 failing-first admin artifact projection test" in change_log
    assert "525 documentation tests passed" in change_log
    assert "2340 total tests passed at 93.84% coverage" in change_log
    assert "Admin artifact payload traversal is also depth-bounded" in operator_guide
    assert "deeper containers render as `[max depth exceeded]`" in operator_guide


def test_sprint_452_documents_shared_sensitive_key_unstringifiable_input_hardening() -> None:
    change_log = Path("docs/sprints/sprint-452-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Shared sensitive-key unstringifiable input hardening" in change_log
    assert "malformed key objects cannot crash diagnostic redaction paths" in change_log
    assert "fails closed to an empty canonical key" in change_log
    assert "2 failing-first sensitive-key tests" in change_log
    assert "84 adjacent redaction and alert tests passed" in change_log
    assert "526 documentation tests passed" in change_log
    assert "2343 total tests passed at 93.84% coverage" in change_log
    assert "Shared sensitive-key matching fails closed for malformed key objects" in (
        operator_guide
    )
    assert "without invoking object stringification or string-subclass methods" in operator_guide


def test_sprint_453_documents_alert_sink_response_circular_diagnostic_hardening() -> None:
    change_log = Path("docs/sprints/sprint-453-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert sink response circular diagnostic hardening" in change_log
    assert "cyclic response payloads cannot raise a secondary recursion failure" in change_log
    assert "self-referential sink response payload" in change_log
    assert "`[circular reference]`" in change_log
    assert "1 failing-first alert response diagnostic test" in change_log
    assert "527 documentation tests passed" in change_log
    assert "2345 total tests passed at 93.79% coverage" in change_log
    assert "Alert sink response diagnostic traversal is cycle-safe" in operator_guide
    assert "repeated active container renders as `[circular reference]`" in operator_guide


def test_sprint_454_documents_alert_sink_response_depth_bound_diagnostic_hardening() -> None:
    change_log = Path("docs/sprints/sprint-454-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert sink response depth-bound diagnostic hardening" in change_log
    assert "deeply nested but acyclic response payloads cannot force unbounded" in (
        change_log
    )
    assert "excessively deep acyclic sink response payload" in change_log
    assert "`[max depth exceeded]`" in change_log
    assert "1 failing-first alert response diagnostic test" in change_log
    assert "528 documentation tests passed" in change_log
    assert "2347 total tests passed at 93.79% coverage" in change_log
    assert "Alert sink response diagnostic traversal is also depth-bounded" in (
        operator_guide
    )
    assert "deeper containers render as `[max depth exceeded]`" in operator_guide


def test_sprint_455_documents_alert_sink_response_non_json_type_name_suppression() -> None:
    change_log = Path("docs/sprints/sprint-455-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert sink response non-JSON type-name suppression" in change_log
    assert "unsupported scalar values no longer expose Python type names" in change_log
    assert "`non_json_type` and Python type names reached `AlertDeliveryError`" in change_log
    assert "`[non-json value]`" in change_log
    assert "1 failing-first alert response diagnostic test" in change_log
    assert "529 documentation tests passed" in change_log
    assert "2348 total tests passed at 93.79% coverage" in change_log
    assert "represented by `[non-json value]` instead of type names" in operator_guide
    assert "custom transport implementation details" in operator_guide


def test_sprint_456_documents_alert_sink_response_non_finite_float_diagnostic_hardening() -> None:
    change_log = Path("docs/sprints/sprint-456-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert sink response non-finite float diagnostic hardening" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "`[non-json value]`" in change_log
    assert "1 failing-first alert response diagnostic test" in change_log
    assert "530 documentation tests passed" in change_log
    assert "2350 total tests passed at 93.80% coverage" in change_log
    assert (
        "non-finite floats, bytes, and arbitrary Python objects are represented by "
        "`[non-json value]`"
    ) in operator_guide


def test_sprint_457_documents_servicenow_outbound_json_non_finite_number_rejection() -> None:
    change_log = Path("docs/sprints/sprint-457-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow outbound JSON non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "fails closed with a stable" in change_log
    assert "`ServiceNowApiError`" in change_log
    assert "1 failing-first ServiceNow urllib transport test" in change_log
    assert "531 documentation tests passed" in change_log
    assert "2352 total tests passed at 93.81% coverage" in change_log
    assert "Outbound ServiceNow JSON request bodies are strict JSON" in operator_guide
    assert "before opening a" in operator_guide
    assert "network request" in operator_guide
    assert "does not echo request field names, body values" in operator_guide


def test_sprint_458_documents_model_provider_prompt_payload_non_finite_number_rejection() -> None:
    change_log = Path("docs/sprints/sprint-458-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model provider prompt payload non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "shared strict implementation-payload serializer" in change_log
    assert "2 failing-first provider prompt payload tests" in change_log
    assert "532 documentation tests passed" in change_log
    assert "2355 total tests passed at 93.81% coverage" in change_log
    assert "Model provider prompt payloads are strict JSON" in operator_guide
    assert "stays byte-identical" in operator_guide
    assert "does not echo payload field names, values" in operator_guide


def test_sprint_459_documents_model_provider_response_non_finite_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-459-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model provider response non-finite JSON rejection" in change_log
    assert "`NaN`" in change_log
    assert "`Infinity`" in change_log
    assert "`-Infinity`" in change_log
    assert "shared strict JSON object loader" in change_log
    assert "2 failing-first provider response tests" in change_log
    assert "533 documentation tests passed" in change_log
    assert "2358 total tests passed at 93.82% coverage" in change_log
    assert "successful model output JSON parsing is strict" in operator_guide
    assert "same fixed invalid-JSON diagnostic" in operator_guide
    assert "does not echo model-provided field names or values" in operator_guide


def test_sprint_460_documents_lifecycle_webhook_non_finite_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-460-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Lifecycle webhook non-finite JSON rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "before lifecycle schema" in change_log
    assert "validation" in change_log
    assert "1 failing-first lifecycle webhook test" in change_log
    assert "534 documentation tests passed" in change_log
    assert "2360 total tests passed at 93.83% coverage" in change_log
    assert "non-standard JSON numeric constants" in operator_guide
    assert "before lifecycle schema validation" in operator_guide
    assert "exact raw request body before JSON decoding" in operator_guide


def test_sprint_461_documents_servicenow_response_non_finite_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-461-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow response non-finite JSON rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "strict JSON loader" in change_log
    assert "`ServiceNow API response body is not valid JSON`" in change_log
    assert "`ServiceNow API error response body is not valid JSON`" in change_log
    assert "2 failing-first ServiceNow urllib transport tests" in change_log
    assert "535 documentation tests passed" in change_log
    assert "2363 total tests passed at 93.83% coverage" in change_log
    assert "valid UTF-8 strict JSON objects" in operator_guide
    assert "non-standard JSON numeric constants" in operator_guide
    assert "HTTP error response JSON parsing is strict" in operator_guide


def test_sprint_462_documents_cli_json_input_non_finite_number_rejection() -> None:
    change_log = Path("docs/sprints/sprint-462-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "CLI JSON input non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "`load_json_payload()`" in change_log
    assert "`json_input_invalid_json`" in change_log
    assert "1 failing-first CLI JSON input test" in change_log
    assert "536 documentation tests passed" in change_log
    assert "2365 total tests passed at 93.83% coverage" in change_log
    assert "CLI JSON artifact input parsing is strict" in operator_guide
    assert "non-standard JSON numeric constants" in operator_guide
    assert "`json_input_invalid_json`" in operator_guide


def test_sprint_463_documents_artifact_json_output_non_finite_number_rejection() -> None:
    change_log = Path("docs/sprints/sprint-463-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Artifact JSON output non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "`write_json_artifact_once()`" in change_log
    assert "`artifact JSON payload contains non-finite numeric values`" in change_log
    assert "1 failing-first artifact serialization test" in change_log
    assert "537 documentation tests passed" in change_log
    assert "2367 total tests passed at 93.83% coverage" in change_log
    assert "JSON artifact output is strict" in operator_guide
    assert "before opening the target artifact file" in operator_guide
    assert "symlink, and path traversal protections" in operator_guide


def test_sprint_464_documents_operational_artifact_jsonb_non_finite_number_rejection() -> None:
    change_log = Path("docs/sprints/sprint-464-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Operational artifact JSONB non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "`record_json_artifact()`" in change_log
    assert "`operational artifact JSON payload contains non-finite numeric values`" in change_log
    assert "1 failing-first operational-store artifact test" in change_log
    assert "538 documentation tests passed" in change_log
    assert "2369 total tests passed at 93.83% coverage" in change_log
    assert "Operational-store JSON artifact blobs are strict JSONB evidence" in operator_guide
    assert "before hash computation" in operator_guide
    assert "`artifact_blobs` insert" in operator_guide


def test_sprint_465_documents_stable_artifact_hash_non_finite_number_rejection() -> None:
    change_log = Path("docs/sprints/sprint-465-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Stable artifact hash non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "`stable_artifact_hash()`" in change_log
    assert "`artifact hash payload contains non-finite numeric values`" in change_log
    assert "1 failing-first stable artifact hash test" in change_log
    assert "539 documentation tests passed" in change_log
    assert "2371 total tests passed at 93.83% coverage" in change_log
    assert "Shared artifact hash generation is strict JSON" in operator_guide
    assert "before SHA-256 computation" in operator_guide
    assert "cannot be minted over Python-only" in operator_guide


def test_sprint_466_documents_flow_snapshot_evidence_non_finite_number_rejection() -> None:
    change_log = Path("docs/sprints/sprint-466-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Flow snapshot evidence non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "`sys_hub_flow_snapshot:invalid`" in change_log
    assert "`flow_snapshot_evidence_invalid: non-finite snapshot value`" in change_log
    assert "1 failing-first Flow snapshot evidence test" in change_log
    assert "540 documentation tests passed" in change_log
    assert "2373 total tests passed at 93.84% coverage" in change_log
    assert "Flow snapshot evidence hashes are strict JSON" in operator_guide
    assert "does not preserve the malformed row" in operator_guide
    assert "does not echo snapshot field names" in operator_guide


def test_sprint_467_documents_flow_graph_diff_validator_non_finite_number_rejection() -> None:
    change_log = Path("docs/sprints/sprint-467-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Flow graph diff validator non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "non-finite customer update value" in change_log
    assert "non-finite payload value" in change_log
    assert "2 failing-first Flow graph diff validator tests" in change_log
    assert "541 documentation tests passed" in change_log
    assert "2376 total tests passed at 93.84% coverage" in change_log
    assert "Flow graph diff safety scans are strict JSON too" in operator_guide
    assert "before builder planning or handoff" in operator_guide
    assert "does not echo the malformed field names or values" in operator_guide


def test_sprint_468_documents_lifecycle_event_jsonb_non_finite_number_rejection() -> None:
    change_log = Path("docs/sprints/sprint-468-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Operational lifecycle event JSONB non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "`PostgresOperationalStore.record_lifecycle_event()`" in change_log
    assert "`operational lifecycle event payload contains non-finite numeric values`" in (
        change_log
    )
    assert "1 failing-first operational-store lifecycle event test" in change_log
    assert "542 documentation tests passed" in change_log
    assert "2378 total tests passed at 93.84% coverage" in change_log
    assert "Operational-store lifecycle event payloads are strict JSONB evidence too" in (
        operator_guide
    )
    assert "before transaction start" in operator_guide
    assert "or idempotency lookup" in operator_guide
    assert "serializer warnings are suppressed" in operator_guide


def test_sprint_469_documents_flow_graph_state_hash_non_finite_number_rejection() -> None:
    change_log = Path("docs/sprints/sprint-469-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Flow graph round-trip state hash non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "`FlowGraphNodeState.canonical()`" in change_log
    assert "`Flow graph node canonical state contains non-finite numeric values`" in (
        change_log
    )
    assert "1 failing-first Flow round-trip test" in change_log
    assert "543 documentation tests passed" in change_log
    assert "2380 total tests passed at 93.84% coverage" in change_log
    assert "Flow graph round-trip state hashes are strict JSON" in operator_guide
    assert "before `flow_graph_state_hash()` computes the graph" in operator_guide
    assert "cannot be minted over Python-only numeric tokens" in operator_guide


def test_sprint_470_documents_alert_webhook_outbound_json_non_finite_rejection() -> None:
    change_log = Path("docs/sprints/sprint-470-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert webhook outbound JSON non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "`_alert_body_bytes()`" in change_log
    assert "`alert webhook payload contains non-finite numeric values`" in change_log
    assert "1 failing-first alert delivery test" in change_log
    assert "544 documentation tests passed" in change_log
    assert "2382 total tests passed at 93.84% coverage" in change_log
    assert "Alert webhook outbound JSON is strict" in operator_guide
    assert "before compact JSON body generation" in operator_guide
    assert "Pydantic serializer warnings are suppressed" in operator_guide


def test_sprint_471_documents_intake_feedback_hash_non_finite_number_rejection() -> None:
    change_log = Path("docs/sprints/sprint-471-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Intake feedback content hash non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "`_intake_content_hash()`" in change_log
    assert "`intake feedback hash payload contains non-finite numeric values`" in change_log
    assert "2 failing-first capability assessment tests" in change_log
    assert "545 documentation tests passed" in change_log
    assert "2385 total tests passed at 93.84% coverage" in change_log
    assert "Intake feedback content hashes are strict JSON" in operator_guide
    assert "before SHA-256 computation" in operator_guide
    assert "provenance cannot be minted over Python-only numeric tokens" in operator_guide


def test_sprint_472_documents_model_fulfillment_artifact_non_finite_rejection() -> None:
    change_log = Path("docs/sprints/sprint-472-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model fulfillment artifact payload non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "`_model_artifact_payload()`" in change_log
    assert "`model fulfillment artifact payload contains non-finite numeric values`" in (
        change_log
    )
    assert "1 failing-first model fulfillment test" in change_log
    assert "546 documentation tests passed" in change_log
    assert "2387 total tests passed at 93.85% coverage" in change_log
    assert "Model fulfillment artifact payload conversion is strict JSON" in operator_guide
    assert "before returning the" in operator_guide
    assert "DB-ready JSON-mode artifact shape" in operator_guide


def test_sprint_473_documents_implementation_packet_nested_payload_non_finite_rejection() -> None:
    change_log = Path("docs/sprints/sprint-473-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Implementation packet nested payload non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "`_packet_model_payload()`" in change_log
    assert "`implementation packet nested payload contains non-finite numeric values`" in (
        change_log
    )
    assert "1 failing-first implementation packet test" in change_log
    assert "547 documentation tests passed" in change_log
    assert "2389 total tests passed at 93.85% coverage" in change_log
    assert "Implementation packet nested DTO payload conversion is strict JSON" in operator_guide
    assert "before the packet is returned for provider prompting or artifact persistence" in (
        operator_guide
    )
    assert "does not echo assessment fields" in operator_guide


def test_sprint_474_documents_packet_raw_normalized_intent_non_finite_rejection() -> None:
    change_log = Path("docs/sprints/sprint-474-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Implementation packet raw normalized-intent non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "`_packet_raw_payload()`" in change_log
    assert "`implementation packet raw payload contains non-finite numeric values`" in (
        change_log
    )
    assert "1 failing-first implementation packet test" in change_log
    assert "548 documentation tests passed" in change_log
    assert "2391 total tests passed at 93.85% coverage" in change_log
    assert "Implementation packet raw normalized-intent payloads are strict JSON too" in (
        operator_guide
    )
    assert "before they are attached to implementation" in operator_guide
    assert "does not echo normalized-intent field names" in operator_guide


def test_sprint_619_documents_packet_raw_payload_strict_json_boundary() -> None:
    change_log = Path("docs/sprints/sprint-619-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Implementation packet raw payload strict JSON boundary" in change_log
    assert "`_packet_raw_payload()`" in change_log
    assert "`_ensure_packet_raw_payload_json_safe()`" in change_log
    assert "`implementation packet raw payload contains non-JSON values`" in change_log
    assert "2 failing-first implementation packet tests" in change_log
    assert "raw `TypeError`" in change_log
    assert "no `ValueError` was raised" in change_log
    assert "Unsupported non-JSON raw normalized-intent payload values fail" in (
        operator_guide
    )
    assert "Raw normalized-intent payload keys and text values must be exact strings" in (
        operator_guide
    )
    assert "before they are attached to implementation packets" in operator_guide


def test_sprint_930_documents_packet_raw_payload_scalar_subclass_boundary() -> None:
    change_log = Path("docs/sprints/sprint-930-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Implementation packet raw payload scalar-subclass boundary" in change_log
    assert "`_packet_raw_payload()`" in change_log
    assert "`_ensure_packet_raw_payload_json_safe()`" in change_log
    assert "`implementation packet raw payload contains non-JSON values`" in change_log
    assert "1 failing-first implementation packet scalar-subclass assertion" in change_log
    assert (
        "Raw normalized-intent boolean and integer values must also be exact JSON scalar types"
        in operator_guide
    )
    assert "`test_packet_raw_payload_rejects_scalar_subclass_without_payload_leak`" in (
        change_log
    )


def test_sprint_475_documents_context_dossier_dto_payload_non_finite_rejection() -> None:
    change_log = Path("docs/sprints/sprint-475-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Context dossier DTO payload non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "`_context_model_payload()`" in change_log
    assert "`context dossier DTO payload contains non-finite numeric values`" in change_log
    assert "1 failing-first packet context test" in change_log
    assert "549 documentation tests passed" in change_log
    assert "2393 total tests passed at 93.86% coverage" in change_log
    assert "Context dossier DTO payload conversion is strict JSON as well" in operator_guide
    assert "inside the model-facing `context_dossier`" in operator_guide
    assert "does not echo context field names" in operator_guide


def test_sprint_476_documents_legacy_dto_artifact_writer_non_finite_rejection() -> None:
    change_log = Path("docs/sprints/sprint-476-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Legacy DTO artifact writer non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "`_artifact_model_json()`" in change_log
    assert "`artifact DTO payload contains non-finite numeric values`" in change_log
    assert "1 failing-first candidate artifact writer test" in change_log
    assert "550 documentation tests passed" in change_log
    assert "2395 total tests passed at 93.86% coverage" in change_log
    assert "Legacy Pydantic DTO artifact writers are strict JSON too" in operator_guide
    assert "before write-once artifact output" in operator_guide
    assert "does not echo DTO field names" in operator_guide


def test_sprint_477_documents_runtime_worker_report_non_finite_rejection() -> None:
    change_log = Path("docs/sprints/sprint-477-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime worker stdout report non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "`_runtime_report_json()`" in change_log
    assert "`runtime worker report contains non-finite numeric values`" in change_log
    assert "1 failing-first runtime worker report test" in change_log
    assert "551 documentation tests passed" in change_log
    assert "2397 total tests passed at 93.86% coverage" in change_log
    assert "Runtime worker stdout reports are strict JSON" in operator_guide
    assert "before printing them to stdout for log capture" in operator_guide
    assert "does not echo report field names" in operator_guide


def test_sprint_478_documents_admin_artifact_diagnostic_json_non_finite_rejection() -> None:
    change_log = Path("docs/sprints/sprint-478-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin artifact diagnostic JSON non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "`_admin_artifact_payload_json()`" in change_log
    assert "`admin artifact payload diagnostic contains non-finite numeric values`" in (
        change_log
    )
    assert "1 failing-first admin artifact diagnostic test" in change_log
    assert "552 documentation tests passed" in change_log
    assert "2399 total tests passed at 93.87% coverage" in change_log
    assert "Admin artifact payload diagnostic JSON rendering is strict" in operator_guide
    assert "before HTML rendering or truncation-preview generation" in operator_guide
    assert "does not echo payload field names" in operator_guide


def test_sprint_479_documents_capability_assessment_intent_non_finite_rejection() -> None:
    change_log = Path("docs/sprints/sprint-479-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Capability assessment automation-intent non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "`_automation_intent_payload()`" in change_log
    assert "`automation intent payload contains non-finite numeric values`" in change_log
    assert "1 failing-first capability assessment test" in change_log
    assert "553 documentation tests passed" in change_log
    assert "2401 total tests passed at 93.87% coverage" in change_log
    assert "Capability assessment automation-intent payloads are strict JSON too" in (
        operator_guide
    )
    assert "before embedding them into `StoryCapabilityAssessment`" in operator_guide
    assert "does not echo intent field names" in operator_guide


def test_sprint_480_documents_atf_test_plan_artifact_non_finite_rejection() -> None:
    change_log = Path("docs/sprints/sprint-480-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Advisory ATF test plan artifact non-finite number rejection" in change_log
    assert "`NaN`, `Infinity`, or `-Infinity`" in change_log
    assert "`_atf_test_plan_artifact()`" in change_log
    assert "`ATF test plan artifact payload contains non-finite numeric values`" in (
        change_log
    )
    assert "1 failing-first model fulfillment test" in change_log
    assert "554 documentation tests passed" in change_log
    assert "2403 total tests passed at 93.87% coverage" in change_log
    assert "Advisory ATF test plan artifacts use the same strict JSON conversion" in (
        operator_guide
    )
    assert "omits the ATF plan artifact" in operator_guide
    assert "does not echo step fields" in operator_guide


def test_sprint_481_documents_legacy_external_build_field_sanitization() -> None:
    change_log = Path("docs/sprints/sprint-481-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Legacy external-build structured writeback field sanitization" in change_log
    assert "`u_ai_build_reference` and `u_ai_candidate_artifact`" in change_log
    assert "`_base_fields()`" in change_log
    assert "credential-like fragments" in change_log
    assert "1 failing-first writeback test" in change_log
    assert "555 documentation tests passed" in change_log
    assert "2405 total tests passed at 93.87% coverage" in change_log
    assert "Legacy external-build structured writeback fields are diagnostic surfaces too" in (
        operator_guide
    )
    assert "redacts credential-like fragments" in operator_guide
    assert "visible ServiceNow fields" in operator_guide


def test_sprint_482_documents_build_claim_artifact_field_sanitization() -> None:
    change_log = Path("docs/sprints/sprint-482-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Build-claim structured artifact field sanitization" in change_log
    assert "`plan_story_build_claim_writeback()`" in change_log
    assert "`u_ai_candidate_artifact`" in change_log
    assert "credential-like fragments" in change_log
    assert "1 failing-first writeback test" in change_log
    assert "556 documentation tests passed" in change_log
    assert "2407 total tests passed at 93.87% coverage" in change_log
    assert "The build-claim path uses the same structured-field sanitizer" in operator_guide
    assert "raw candidate artifact URL" in operator_guide
    assert "visible ServiceNow field" in operator_guide


def test_sprint_483_documents_writeback_verification_field_normalization() -> None:
    change_log = Path("docs/sprints/sprint-483-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Writeback verification structured-field normalization" in change_log
    assert "`verify_writeback()`" in change_log
    assert "`structured_writeback_field_value()`" in change_log
    assert "`u_ai_build_reference` and `u_ai_candidate_artifact`" in change_log
    assert "1 failing-first writeback orchestration test" in change_log
    assert "557 documentation tests passed" in change_log
    assert "2409 total tests passed at 93.87% coverage" in change_log
    assert "Verification normalizes expected legacy structured fields" in operator_guide
    assert "same sanitizer as writeback planning" in operator_guide
    assert "not reported as a mismatch" in operator_guide


def test_sprint_484_documents_writeback_verification_actual_field_redaction() -> None:
    change_log = Path("docs/sprints/sprint-484-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Writeback verification actual-field diagnostic redaction" in change_log
    assert "`WritebackVerificationResult.actual_fields`" in change_log
    assert "`verify_writeback()`" in change_log
    assert "raw remote values only for mismatch comparison" in change_log
    assert "1 failing-first writeback orchestration test" in change_log
    assert "558 documentation tests passed" in change_log
    assert "2411 total tests passed at 93.87% coverage" in change_log
    assert "returned `actual_fields` are sanitized diagnostics" in operator_guide
    assert "compares against the raw remote ServiceNow values internally" in operator_guide
    assert "before CLI or report rendering" in operator_guide


def test_sprint_485_documents_writeback_batch_report_redaction() -> None:
    change_log = Path("docs/sprints/sprint-485-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Writeback batch report diagnostic redaction" in change_log
    assert "`build_writeback_batch_report()`" in change_log
    assert "recursively sanitizes report strings and dictionary keys" in change_log
    assert "1 failing-first writeback orchestration test" in change_log
    assert "559 documentation tests passed" in change_log
    assert "2413 total tests passed at 93.87% coverage" in change_log
    assert "Batch reports are sanitized diagnostic projections" in operator_guide
    assert "execution ids, actor ids, capability reasons" in operator_guide
    assert "before JSON artifact output" in operator_guide


def test_sprint_486_documents_writeback_batch_report_traversal_hardening() -> None:
    change_log = Path("docs/sprints/sprint-486-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Writeback batch report traversal hardening" in change_log
    assert "`_diagnostic_report_value()`" in change_log
    assert "`[circular reference]`" in change_log
    assert "`[max depth exceeded]`" in change_log
    assert "1 failing-first writeback orchestration test" in change_log
    assert "560 documentation tests passed" in change_log
    assert "2415 total tests passed at 93.81% coverage" in change_log
    assert "Batch report diagnostic traversal is also cycle-safe and depth-bounded" in (
        operator_guide
    )
    assert "repeated containers render as `[circular reference]`" in operator_guide
    assert "beyond the diagnostic depth cap render as `[max depth exceeded]`" in operator_guide


def test_sprint_487_documents_writeback_batch_report_scalar_normalization() -> None:
    change_log = Path("docs/sprints/sprint-487-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Writeback batch report scalar diagnostic normalization" in change_log
    assert "`_diagnostic_report_value()`" in change_log
    assert "`[non-json value]`" in change_log
    assert "Non-finite floats" in change_log
    assert "1 failing-first writeback orchestration test" in change_log
    assert "561 documentation tests passed" in change_log
    assert "2417 total tests passed at 93.82% coverage" in change_log
    assert "Unsupported diagnostic scalar values" in operator_guide
    assert "render as `[non-json value]`" in operator_guide
    assert "finite JSON primitives remain typed" in operator_guide


def test_sprint_605_documents_writeback_batch_report_diagnostic_key_projection() -> None:
    change_log = Path("docs/sprints/sprint-605-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Writeback batch report diagnostic key projection" in change_log
    assert "`_diagnostic_report_key()`" in change_log
    assert "1 failing-first writeback batch report diagnostic-key test" in change_log
    assert "called a hostile key object's `__str__()`" in change_log
    assert "Batch report diagnostic keys are projected before output" in operator_guide
    assert "non-string keys render as `[non-json key]`" in operator_guide
    assert "without calling `str()` or `repr()` on malformed key objects" in (
        operator_guide
    )


def test_sprint_606_documents_writeback_batch_report_key_collision_preservation() -> None:
    change_log = Path("docs/sprints/sprint-606-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Writeback batch report diagnostic key collision preservation" in change_log
    assert "`_deduplicated_diagnostic_report_key()`" in change_log
    assert "`_duplicate_diagnostic_report_key()`" in change_log
    assert "1 failing-first writeback batch report collision-preservation test" in (
        change_log
    )
    assert "duplicate rendered diagnostic keys overwrote earlier evidence" in change_log
    assert "later entries receive deterministic `[duplicate N]` suffixes" in (
        operator_guide
    )
    assert "instead of overwriting earlier evidence" in operator_guide


def test_sprint_488_documents_flow_graph_diff_non_json_payload_rejection() -> None:
    change_log = Path("docs/sprints/sprint-488-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Flow graph diff non-JSON payload rejection" in change_log
    assert "`_strict_validation_json()`" in change_log
    assert "`default=str`" in change_log
    assert "stable non-JSON diagnostics" in change_log
    assert "1 failing-first Flow graph diff validator test" in change_log
    assert "562 documentation tests passed" in change_log
    assert "2419 total tests passed at 93.82% coverage" in change_log
    assert "Flow graph diff safety scans also reject non-JSON Python values" in (
        operator_guide
    )
    assert "not stringified through `str()` or `repr()`" in operator_guide
    assert "object type names, object string output, or values" in operator_guide


def test_sprint_489_documents_flow_snapshot_evidence_non_json_value_rejection() -> None:
    change_log = Path("docs/sprints/sprint-489-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Flow snapshot evidence non-JSON value rejection" in change_log
    assert "`sys_hub_flow_snapshot:invalid`" in change_log
    assert "`flow_snapshot_evidence_invalid: non-JSON snapshot value`" in change_log
    assert "1 failing-first Flow snapshot evidence test" in change_log
    assert "24 tests passed" in change_log
    assert "563 documentation tests passed" in change_log
    assert "2421 total tests passed at 93.82% coverage" in change_log
    assert "Unsupported non-JSON row values are also rejected before hashing" in (
        operator_guide
    )
    assert "`flow_snapshot_evidence_invalid: non-JSON snapshot value`" in (
        operator_guide
    )
    assert "does not call" in operator_guide
    assert "`str()` or `repr()`" in operator_guide


def test_sprint_490_documents_stable_artifact_hash_non_json_value_rejection() -> None:
    change_log = Path("docs/sprints/sprint-490-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Stable artifact hash non-JSON value rejection" in change_log
    assert "`stable_artifact_hash()`" in change_log
    assert "`artifact hash payload contains non-JSON values`" in change_log
    assert "1 failing-first artifact hash test" in change_log
    assert "17 tests passed" in change_log
    assert "564 documentation tests passed" in change_log
    assert "2423 total tests passed at 93.82% coverage" in change_log
    assert "Unsupported non-JSON" in operator_guide
    assert "`artifact hash payload contains non-JSON values`" in operator_guide
    assert "hashing does not call `str()` or `repr()`" in operator_guide


def test_sprint_613_documents_stable_artifact_hash_exact_string_boundary() -> None:
    change_log = Path("docs/sprints/sprint-613-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Stable artifact hash exact-string boundary" in change_log
    assert "`stable_artifact_hash()`" in change_log
    assert "`_ensure_artifact_hash_payload_json_safe()`" in change_log
    assert "`artifact hash payload contains non-JSON values`" in change_log
    assert "1 failing-first artifact hash test" in change_log
    assert "no `ValueError` was raised" in change_log
    assert "Artifact hash payload keys and text values must be exact strings" in (
        operator_guide
    )
    assert "string subclasses fail with the" in operator_guide
    assert "before canonicalization or SHA-256 computation" in operator_guide


def test_sprint_929_documents_stable_artifact_hash_scalar_subclass_boundary() -> None:
    change_log = Path("docs/sprints/sprint-929-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Stable artifact hash scalar-subclass boundary" in change_log
    assert "`stable_artifact_hash()`" in change_log
    assert "`_ensure_artifact_hash_payload_json_safe()`" in change_log
    assert "`artifact hash payload contains non-JSON values`" in change_log
    assert "1 failing-first artifact hash scalar-subclass assertion" in change_log
    assert "Artifact hash boolean and integer values must be exact JSON scalar types" in (
        operator_guide
    )
    assert (
        "`test_stable_artifact_hash_rejects_scalar_subclass_values_without_payload_leak`"
        in change_log
    )


def test_sprint_940_documents_artifact_container_subclass_boundaries() -> None:
    change_log = Path("docs/sprints/sprint-940-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Artifact container-subclass boundaries" in change_log
    assert "`_ensure_artifact_hash_payload_json_safe()`" in change_log
    assert "`_ensure_artifact_dto_payload_json_safe()`" in change_log
    assert "2 failing-first artifact container-subclass assertions" in change_log
    assert "Artifact hash traversal accepts only exact dictionaries and lists" in (
        operator_guide
    )
    assert "DTO payload traversal accepts only" in operator_guide
    assert "exact dictionaries, lists, and tuples" in operator_guide
    assert "dictionary, list, and tuple subclasses fail before `items()`" in (
        operator_guide
    )


def test_sprint_491_documents_operational_lifecycle_event_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-491-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Operational lifecycle event non-JSON payload rejection" in change_log
    assert "`PostgresOperationalStore.record_lifecycle_event()`" in change_log
    assert "`operational lifecycle event payload contains non-JSON values`" in change_log
    assert "1 failing-first operational-store test" in change_log
    assert "47 tests passed" in change_log
    assert "565 documentation tests passed" in change_log
    assert "2425 total tests passed at 93.77% coverage" in change_log
    assert "Pydantic JSON-mode output" in operator_guide
    assert "`operational lifecycle event payload contains non-JSON values`" in (
        operator_guide
    )
    assert "event persistence does not call `str()` or `repr()`" in operator_guide


def test_sprint_610_documents_operational_lifecycle_event_exact_string_boundary() -> None:
    change_log = Path("docs/sprints/sprint-610-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Operational lifecycle event exact-string JSONB boundary" in change_log
    assert "`_ensure_lifecycle_event_payload_json_safe()`" in change_log
    assert "`operational lifecycle event payload contains non-JSON values`" in change_log
    assert "1 failing-first operational-store lifecycle event test" in change_log
    assert "subclassed event id reached database lookup" in change_log
    assert "Lifecycle event payload keys and text values must be exact strings" in (
        operator_guide
    )
    assert "string subclasses fail" in operator_guide
    assert "before transaction start or idempotency lookup" in operator_guide


def test_sprint_492_documents_operational_artifact_jsonb_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-492-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Operational artifact JSONB non-JSON payload rejection" in change_log
    assert "`PostgresOperationalStore.record_json_artifact()`" in change_log
    assert "`operational artifact JSON payload contains non-JSON values`" in change_log
    assert "1 failing-first operational-store artifact test" in change_log
    assert "48 tests passed" in change_log
    assert "566 documentation tests passed" in change_log
    assert "2427 total tests passed at 93.77% coverage" in change_log
    assert "`operational artifact JSON payload contains non-JSON values`" in operator_guide
    assert "DB-backed artifact persistence does not call `str()` or `repr()`" in (
        operator_guide
    )


def test_sprint_611_documents_operational_artifact_exact_string_boundary() -> None:
    change_log = Path("docs/sprints/sprint-611-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Operational artifact exact-string JSONB boundary" in change_log
    assert "`_ensure_operational_artifact_payload_json_safe()`" in change_log
    assert "`operational artifact JSON payload contains non-JSON values`" in change_log
    assert "1 failing-first operational-store artifact test" in change_log
    assert "subclassed value reached `INSERT INTO artifact_blobs`" in change_log
    assert "Operational artifact payload keys and text values must be exact" in (
        operator_guide
    )
    assert "string subclasses fail with the same non-JSON diagnostic" in operator_guide
    assert "before hash computation or" in operator_guide


def test_sprint_941_documents_operational_store_container_subclass_boundaries() -> (
    None
):
    change_log = Path("docs/sprints/sprint-941-change-log.md").read_text(
        encoding="utf-8",
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Operational-store container-subclass JSONB boundaries" in change_log
    assert "`_ensure_lifecycle_event_payload_json_safe()`" in change_log
    assert "`_ensure_operational_artifact_payload_json_safe()`" in change_log
    assert "2 failing-first operational-store container-subclass assertions" in change_log
    assert "Operational artifact payload traversal accepts only exact dictionaries" in (
        operator_guide
    )
    assert "Lifecycle event" in operator_guide
    assert "payload traversal accepts only exact dictionaries, lists, and tuples" in (
        operator_guide
    )
    assert "dictionary, list, and tuple subclasses fail before `items()`" in (
        operator_guide
    )


def test_sprint_493_documents_runtime_worker_report_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-493-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime worker stdout report non-JSON value rejection" in change_log
    assert "`_runtime_report_json()`" in change_log
    assert "`runtime worker report contains non-JSON values`" in change_log
    assert "1 failing-first runtime worker report test" in change_log
    assert "10 tests passed" in change_log
    assert "567 documentation tests passed" in change_log
    assert "2429 total tests passed at 93.76% coverage" in change_log
    assert "`runtime worker report contains" in operator_guide
    assert "non-JSON values`" in operator_guide
    assert "stdout report rendering does not call `str()` or `repr()`" in operator_guide
    assert "compact JSON lines" in operator_guide


def test_sprint_609_documents_runtime_worker_report_exact_string_boundary() -> None:
    change_log = Path("docs/sprints/sprint-609-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime worker report exact-string boundary" in change_log
    assert "`_ensure_runtime_report_json_safe()`" in change_log
    assert "`runtime worker report contains non-JSON values`" in change_log
    assert "2 failing-first runtime worker report tests" in change_log
    assert "neither corrupted report raised `ValueError`" in change_log
    assert "Runtime report keys and text values must be exact strings" in operator_guide
    assert "String subclasses fail with the same non-JSON diagnostic" in operator_guide


def test_sprint_494_documents_legacy_dto_artifact_writer_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-494-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Legacy artifact DTO non-JSON value rejection" in change_log
    assert "`_artifact_model_json()`" in change_log
    assert "`artifact DTO payload contains non-JSON values`" in change_log
    assert "1 failing-first candidate artifact writer test" in change_log
    assert "8 tests passed" in change_log
    assert "568 documentation tests passed" in change_log
    assert "2431 total tests passed at 93.75% coverage" in change_log
    assert "`artifact DTO payload contains non-JSON values`" in operator_guide
    assert "DTO artifact writing does not call `str()` or `repr()`" in operator_guide
    assert "unsupported objects, bytes, or custom" in operator_guide


def test_sprint_612_documents_artifact_dto_exact_string_boundary() -> None:
    change_log = Path("docs/sprints/sprint-612-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Artifact DTO exact-string output boundary" in change_log
    assert "`_ensure_artifact_dto_payload_json_safe()`" in change_log
    assert "`artifact DTO payload contains non-JSON values`" in change_log
    assert "1 failing-first candidate artifact test" in change_log
    assert "no `ArtifactWriteError` was raised" in change_log
    assert "DTO payload keys and text values must be exact strings" in operator_guide
    assert "string subclasses fail with" in operator_guide
    assert "before write-once artifact output" in operator_guide


def test_sprint_495_documents_context_dossier_dto_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-495-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Context dossier DTO non-JSON value rejection" in change_log
    assert "`_context_model_payload()`" in change_log
    assert "`context dossier DTO payload contains non-JSON values`" in change_log
    assert "1 failing-first packet context test" in change_log
    assert "2 tests passed" in change_log
    assert "569 documentation tests passed" in change_log
    assert "2433 total tests passed at 93.75% coverage" in change_log
    assert "`context dossier DTO payload contains non-JSON values`" in operator_guide
    assert "context dossier conversion does not call `str()` or `repr()`" in (
        operator_guide
    )
    assert "object type names, object string output" in operator_guide


def test_sprint_617_documents_context_dossier_dto_exact_string_boundary() -> None:
    change_log = Path("docs/sprints/sprint-617-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Context dossier DTO exact-string boundary" in change_log
    assert "`_context_model_payload()`" in change_log
    assert "`_ensure_context_dto_payload_json_safe()`" in change_log
    assert "`context dossier DTO payload contains non-JSON values`" in change_log
    assert "1 failing-first packet context test" in change_log
    assert "no `ValueError` was raised" in change_log
    assert "Context dossier DTO payload keys and text values must be exact strings" in (
        operator_guide
    )
    assert "string subclasses fail with the same non-JSON diagnostic" in operator_guide
    assert "before compacting or returning the dossier" in operator_guide


def test_sprint_496_documents_automation_intent_payload_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-496-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Automation intent payload non-JSON value rejection" in change_log
    assert "`_automation_intent_payload()`" in change_log
    assert "`automation intent payload contains non-JSON values`" in change_log
    assert "1 failing-first capability assessment test" in change_log
    assert "16 tests passed" in change_log
    assert "570 documentation tests passed" in change_log
    assert "2435 total tests passed at 93.74% coverage" in change_log
    assert "`automation intent payload contains non-JSON values`" in operator_guide
    assert "automation-intent payload conversion does not" in operator_guide
    assert "object type names, object string" in operator_guide


def test_sprint_614_documents_automation_intent_payload_exact_string_boundary() -> None:
    change_log = Path("docs/sprints/sprint-614-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Automation-intent payload exact-string boundary" in change_log
    assert "`_automation_intent_payload()`" in change_log
    assert "`_ensure_capability_payload_json_safe()`" in change_log
    assert "`automation intent payload contains non-JSON values`" in change_log
    assert "1 failing-first capability assessment test" in change_log
    assert "no `ValueError` was raised" in change_log
    assert "Automation-intent payload keys and text values must be exact strings" in (
        operator_guide
    )
    assert "string subclasses fail with the same non-JSON" in operator_guide
    assert "before assessment construction" in operator_guide


def test_sprint_939_documents_model_payload_exact_scalar_container_boundaries() -> (
    None
):
    change_log = Path("docs/sprints/sprint-939-change-log.md").read_text(
        encoding="utf-8",
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model payload exact scalar and container boundaries" in change_log
    assert "`_ensure_context_dto_payload_json_safe()`" in change_log
    assert "`_ensure_capability_payload_json_safe()`" in change_log
    assert "4 failing-first model payload subclass assertions" in change_log
    assert "Context dossier DTO traversal accepts only exact dictionaries" in operator_guide
    assert "Automation-intent payload traversal accepts only exact dictionaries" in (
        operator_guide
    )
    assert "scalar subclasses fail with the same non-JSON diagnostic" in operator_guide
    assert "dictionary, list, and tuple subclasses fail before `items()`" in operator_guide


def test_sprint_497_documents_intake_feedback_hash_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-497-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Intake feedback hash non-JSON value rejection" in change_log
    assert "`_intake_content_hash()`" in change_log
    assert "`intake feedback hash payload contains non-JSON values`" in change_log
    assert "1 failing-first capability assessment test" in change_log
    assert "17 tests passed" in change_log
    assert "571 documentation tests passed" in change_log
    assert "2437 total tests passed at 93.74% coverage" in change_log
    assert "`intake feedback hash payload contains non-JSON values`" in operator_guide
    assert "intake feedback hashing does not call `str()` or `repr()`" in (
        operator_guide
    )
    assert "before canonicalization" in operator_guide


def test_sprint_498_documents_model_fulfillment_artifact_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-498-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model fulfillment artifact non-JSON value rejection" in change_log
    assert "`_model_artifact_payload()`" in change_log
    assert "`model fulfillment artifact payload contains non-JSON values`" in change_log
    assert "1 failing-first model fulfillment test" in change_log
    assert "30 tests passed" in change_log
    assert "572 documentation tests passed" in change_log
    assert "2439 total tests passed at 93.74% coverage" in change_log
    assert "`model fulfillment artifact payload contains non-JSON values`" in operator_guide
    assert "model artifact conversion does not" in operator_guide
    assert "before DB-ready" in operator_guide


def test_sprint_615_documents_model_fulfillment_artifact_exact_string_boundary() -> None:
    change_log = Path("docs/sprints/sprint-615-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model fulfillment artifact exact-string boundary" in change_log
    assert "`_model_artifact_payload()`" in change_log
    assert "`_ensure_model_artifact_payload_json_safe()`" in change_log
    assert "`model fulfillment artifact payload contains non-JSON values`" in change_log
    assert "1 failing-first model fulfillment test" in change_log
    assert "no `ValueError` was raised" in change_log
    assert "Model fulfillment artifact payload keys and text values must be" in (
        operator_guide
    )
    assert "exact strings; string subclasses fail with the same non-JSON" in (
        operator_guide
    )
    assert "before DB-ready artifact" in operator_guide


def test_sprint_499_documents_alert_webhook_payload_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-499-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert webhook outbound JSON non-JSON value rejection" in change_log
    assert "`_alert_body_bytes()`" in change_log
    assert "`alert webhook payload contains non-JSON values`" in change_log
    assert "1 failing-first alert delivery test" in change_log
    assert "65 tests passed" in change_log
    assert "573 documentation tests passed" in change_log
    assert "2441 total tests passed at 93.69% coverage" in change_log
    assert "`alert webhook payload contains non-JSON values`" in operator_guide
    assert "alert webhook body generation" in operator_guide
    assert "before transport" in operator_guide


def test_sprint_618_documents_alert_webhook_payload_exact_string_boundary() -> None:
    change_log = Path("docs/sprints/sprint-618-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert webhook payload exact-string boundary" in change_log
    assert "`_alert_body_bytes()`" in change_log
    assert "`_ensure_alert_payload_json_safe()`" in change_log
    assert "`alert webhook payload contains non-JSON values`" in change_log
    assert "1 failing-first alert delivery test" in change_log
    assert "no `AlertDeliveryError` was raised" in change_log
    assert "Alert webhook payload keys and text values must be exact strings" in (
        operator_guide
    )
    assert "string subclasses fail with the same non-JSON diagnostic" in operator_guide
    assert "before compact JSON body generation or transport" in operator_guide


def test_sprint_942_documents_egress_payload_container_subclass_boundaries() -> None:
    change_log = Path("docs/sprints/sprint-942-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Egress payload container-subclass boundaries" in change_log
    assert "`_ensure_model_artifact_payload_json_safe()`" in change_log
    assert "`_ensure_runtime_report_json_safe()`" in change_log
    assert "`_ensure_alert_payload_json_safe()`" in change_log
    assert "3 failing-first egress payload container-subclass assertions" in change_log
    assert "Runtime report traversal accepts only exact dictionaries" in operator_guide
    assert "Alert payload traversal accepts only exact dictionaries" in operator_guide
    assert "Model artifact payload traversal accepts only exact dictionaries" in (
        operator_guide
    )
    assert "dictionary, list, and tuple subclasses fail before `items()`" in (
        operator_guide
    )


def test_sprint_500_documents_implementation_packet_nested_dto_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-500-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Implementation packet nested DTO non-JSON value rejection" in change_log
    assert "`_packet_model_payload()`" in change_log
    assert "`implementation packet nested payload contains non-JSON values`" in change_log
    assert "1 failing-first implementation packet test" in change_log
    assert "66 tests passed" in change_log
    assert "574 documentation tests passed" in change_log
    assert "2443 total tests passed at 93.64% coverage" in change_log
    assert "`implementation packet nested payload contains non-JSON values`" in operator_guide
    assert "nested packet payload conversion does not call `str()` or `repr()`" in (
        operator_guide
    )
    assert "before provider prompting or artifact persistence" in operator_guide


def test_sprint_616_documents_implementation_packet_nested_dto_exact_string_boundary() -> None:
    change_log = Path("docs/sprints/sprint-616-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Implementation packet nested DTO exact-string boundary" in change_log
    assert "`_packet_model_payload()`" in change_log
    assert "`_ensure_packet_model_payload_json_safe()`" in change_log
    assert "`implementation packet nested payload contains non-JSON values`" in change_log
    assert "1 failing-first implementation packet test" in change_log
    assert "no `ValueError` was raised" in change_log
    assert (
        "Implementation packet nested DTO payload keys and text values must be exact strings"
        in operator_guide
    )
    assert "string subclasses fail with the same non-JSON diagnostic" in operator_guide
    assert "before provider prompting or artifact persistence" in operator_guide


def test_sprint_943_documents_implementation_packet_container_subclass_boundaries() -> None:
    change_log = Path("docs/sprints/sprint-943-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Implementation packet container-subclass boundaries" in change_log
    assert "`_ensure_packet_model_payload_json_safe()`" in change_log
    assert "`_ensure_packet_raw_payload_json_safe()`" in change_log
    assert "2 failing-first implementation packet container-subclass assertions" in (
        change_log
    )
    assert "Nested implementation packet payload traversal accepts only exact" in (
        operator_guide
    )
    assert "Raw normalized-intent payload traversal accepts only exact" in operator_guide
    assert "dictionary, list, tuple, set, and frozenset subclasses fail before" in (
        operator_guide
    )
    assert "dictionary, list, and tuple subclasses fail before `items()`" in (
        operator_guide
    )


def test_sprint_501_documents_generation_field_scalar_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-501-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Generation field scalar non-JSON value rejection" in change_log
    assert "`validation_helpers.py`" in change_log
    assert "`generation field scalar value contains non-JSON value`" in change_log
    assert "4 failing-first validation-helper tests" in change_log
    assert "24 tests passed" in change_log
    assert "131 tests passed" in change_log
    assert "575 documentation tests passed" in change_log
    assert "2449 total tests passed at 93.66% coverage" in change_log
    assert "Shared generation-field scalar coercion is explicit" in operator_guide
    assert "`bool_value()`, `string_list()`, `optional_int()`, and `reference_value()`" in (
        operator_guide
    )
    assert "do not call `str()` or `repr()` on unsupported values" in operator_guide


def test_sprint_889_documents_generation_field_scalar_string_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-889-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Generation field scalar string-subclass guard" in change_log
    assert "2 failing-first validation-helper string-subclass assertions" in change_log
    assert "Shared generation-field scalar text values require exact strings" in operator_guide
    assert (
        "`test_bool_value_rejects_string_subclass_without_string_method_execution`"
        in change_log
    )
    assert (
        "`test_string_list_rejects_string_subclass_items_without_string_method_execution`"
        in change_log
    )


def test_sprint_928_documents_generation_field_scalar_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-928-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Shared generation-field scalar-subclass guard" in change_log
    assert "`validation_helpers.py`" in change_log
    assert "`generation field scalar value contains non-JSON value`" in change_log
    assert "1 failing-first validation-helper scalar-subclass assertion" in change_log
    assert (
        "Shared generation-field boolean and integer values require exact JSON scalar types"
        in operator_guide
    )
    assert (
        "`test_string_list_rejects_scalar_subclass_items_without_string_method_execution`"
        in change_log
    )


def test_sprint_944_documents_generation_helper_container_numeric_subclass_guard() -> (
    None
):
    change_log = Path("docs/sprints/sprint-944-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Shared generation-helper container and numeric subclass boundaries" in (
        change_log
    )
    assert "`string_list()`" in change_log
    assert "`reference_value()`" in change_log
    assert "`_scalar_text()`" in change_log
    assert "3 failing-first shared generation-helper subclass assertions" in change_log
    assert "Shared generation-field list, dictionary, and float values" in (
        operator_guide
    )
    assert "Decimal values are rejected" in operator_guide
    assert "also require exact supported types" in operator_guide
    assert "List subclasses fail before list item iteration" in operator_guide
    assert "dictionary subclasses fail before reference value lookup" in operator_guide
    assert "float subclasses and exact Decimal values fail before string conversion" in (
        operator_guide
    )


def test_sprint_890_documents_project_quality_gate_cleanup() -> None:
    change_log = Path("docs/sprints/sprint-890-change-log.md").read_text(encoding="utf-8")

    assert "Project quality gate cleanup" in change_log
    assert "Ruff long-line cleanup in `tests/test_project_docs.py`" in change_log
    assert "full Ruff gate" in change_log
    assert "full mypy gate" in change_log
    assert "full coverage gate" in change_log


def test_sprint_502_documents_retrieved_update_set_customer_update_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-502-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set customer update scalar non-JSON value rejection" in change_log
    assert "`import_retrieved_update_set()`" in change_log
    assert "`retrieved Update Set customer update contains non-JSON value`" in change_log
    assert "1 failing-first retrieved Update Set handoff test" in change_log
    assert "21 tests passed" in change_log
    assert "576 documentation tests passed" in change_log
    assert "2451 total tests passed at 93.66% coverage" in change_log
    assert "Retrieved Update Set customer update XML serialization is strict" in operator_guide
    assert "`import_retrieved_update_set()` accepts only string values" in operator_guide
    assert "does not call `str()` or `repr()` on unsupported customer-update values" in (
        operator_guide
    )


def test_sprint_503_documents_dictionary_form_handoff_field_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-503-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Dictionary/form handoff field non-JSON value rejection" in change_log
    assert "`create_update_set_handoff()`" in change_log
    assert "`dictionary/form handoff field contains non-JSON value`" in change_log
    assert "1 failing-first retrieved Update Set handoff test" in change_log
    assert "22 tests passed" in change_log
    assert "577 documentation tests passed" in change_log
    assert "2453 total tests passed at 93.67% coverage" in change_log
    assert "Dictionary/form retrieved Update Set intent extraction is strict too" in (
        operator_guide
    )
    assert "`dictionary/form handoff field contains non-JSON value`" in operator_guide
    assert "does not call `str()` or `repr()` on unsupported candidate fields" in (
        operator_guide
    )


def test_sprint_504_documents_form_section_removal_field_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-504-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Form-section removal field non-JSON value rejection" in change_log
    assert "`form_section_customer_updates()`" in change_log
    assert "`form section removal field contains non-JSON value`" in change_log
    assert "1 failing-first form-section customer-update test" in change_log
    assert "75 tests passed" in change_log
    assert "578 documentation tests passed" in change_log
    assert "2455 total tests passed at 93.66% coverage" in change_log
    assert "Form-section removal customer-update generation also treats" in operator_guide
    assert "`form_section_customer_updates()` accepts only primitive" in operator_guide
    assert "does not call `str()` or `repr()` on unsupported values" in operator_guide


def test_sprint_505_documents_record_producer_generation_field_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-505-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Record producer generation field non-JSON value rejection" in change_log
    assert "`record_producer_customer_updates()`" in change_log
    assert "`record producer generation field contains non-JSON value`" in change_log
    assert "1 failing-first record producer generation test" in change_log
    assert "17 tests passed" in change_log
    assert "579 documentation tests passed" in change_log
    assert "2457 total tests passed at 93.66% coverage" in change_log
    assert "Record producer customer-update generation is strict as well" in operator_guide
    assert "`record_producer_customer_updates()` accepts only primitive" in operator_guide
    assert "does not call `str()` or `repr()` on unsupported values" in operator_guide


def test_sprint_893_documents_record_producer_generation_string_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-893-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Record producer generation string-subclass guard" in change_log
    assert "`record_producer_customer_updates()`" in change_log
    assert "`record producer generation field contains non-JSON value`" in change_log
    assert "1 failing-first record producer string-subclass assertion" in change_log
    assert "Record producer generation text values require exact strings" in operator_guide
    assert (
        "`test_record_producer_customer_updates_rejects_string_subclass_field_without_leak`"
        in change_log
    )


def test_sprint_1001_documents_record_producer_metadata_record_collection_guard() -> None:
    change_log = Path("docs/sprints/sprint-1001-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Record Producer metadata record collection guard" in change_log
    assert "`_record_producer_metadata_records()`" in change_log
    assert "record producer generation field contains non-JSON value" in change_log
    assert (
        "1 failing-first Record Producer metadata record collection subclass assertion"
        in change_log
    )
    assert "Record producer ServiceNow metadata record collections are exact containers" in (
        operator_guide
    )
    assert "`fetch_table_records()` must be exact" in operator_guide
    assert "before target-table existence checks" in operator_guide
    assert (
        "`test_record_producer_customer_updates_rejects_metadata_record_collection_subclass`"
        in change_log
    )
    assert (
        "`test_record_producer_customer_updates_rejects_metadata_record_subclass`"
        in change_log
    )


def test_sprint_506_documents_catalog_item_generation_field_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-506-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Catalog item generation field non-JSON value rejection" in change_log
    assert "`catalog_item_customer_updates()`" in change_log
    assert "`catalog item generation field contains non-JSON value`" in change_log
    assert "1 failing-first catalog item generation test" in change_log
    assert "46 tests passed" in change_log
    assert "580 documentation tests passed" in change_log
    assert "2459 total tests passed at 93.67% coverage" in change_log
    assert "Catalog item customer-update generation treats" in operator_guide
    assert "`catalog_item_customer_updates()` accepts only primitive" in operator_guide
    assert "does not call `str()` or `repr()` on unsupported values" in operator_guide


def test_sprint_892_documents_catalog_item_generation_string_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-892-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Catalog item generation string-subclass guard" in change_log
    assert "1 failing-first catalog item string-subclass assertion" in change_log
    assert "Catalog item generation text values require exact strings" in operator_guide
    assert (
        "`test_catalog_item_customer_updates_rejects_string_subclass_item_field_without_leak`"
        in change_log
    )


def test_sprint_507_documents_script_include_generation_field_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-507-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Script Include generation field non-JSON value rejection" in change_log
    assert "`script_include_customer_updates()`" in change_log
    assert "`Script Include generation field contains non-JSON value`" in change_log
    assert "1 failing-first Script Include generation test" in change_log
    assert "53 tests passed" in change_log
    assert "581 documentation tests passed" in change_log
    assert "2461 total tests passed at 93.64% coverage" in change_log
    assert "Script Include customer-update generation also uses" in operator_guide
    assert "`script_include_customer_updates()` accepts only primitive" in operator_guide
    assert "does not call `str()` or `repr()` on unsupported values" in operator_guide


def test_sprint_895_documents_script_include_generation_string_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-895-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Script Include generation string-subclass guard" in change_log
    assert "`script_include_customer_updates()`" in change_log
    assert "`Script Include generation field contains non-JSON value`" in change_log
    assert "1 failing-first Script Include string-subclass assertion" in change_log
    assert "Script Include generation text values require exact strings" in operator_guide
    assert (
        "`test_script_include_customer_updates_rejects_string_subclass_field_without_leak`"
        in change_log
    )


def test_sprint_508_documents_business_rule_generation_field_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-508-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Business Rule generation field non-JSON value rejection" in change_log
    assert "`business_rule_customer_updates()`" in change_log
    assert "`Business Rule generation field contains non-JSON value`" in change_log
    assert "1 failing-first Business Rule generation test" in change_log
    assert "54 tests passed" in change_log
    assert "582 documentation tests passed" in change_log
    assert "2463 total tests passed at 93.61% coverage" in change_log
    assert "Business Rule customer-update generation uses" in operator_guide
    assert "`business_rule_customer_updates()` accepts only primitive" in operator_guide
    assert "does not call `str()` or `repr()` on unsupported values" in operator_guide


def test_sprint_894_documents_business_rule_generation_string_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-894-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Business Rule generation string-subclass guard" in change_log
    assert "`business_rule_customer_updates()`" in change_log
    assert "`Business Rule generation field contains non-JSON value`" in change_log
    assert "1 failing-first Business Rule string-subclass assertion" in change_log
    assert "Business Rule generation text values require exact strings" in operator_guide
    assert (
        "`test_business_rule_customer_updates_rejects_string_subclass_field_without_leak`"
        in change_log
    )


def test_sprint_509_documents_client_script_generation_field_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-509-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Client Script generation field non-JSON value rejection" in change_log
    assert "`client_script_customer_updates()`" in change_log
    assert "`Client Script generation field contains non-JSON value`" in change_log
    assert "1 failing-first Client Script generation test" in change_log
    assert "55 tests passed" in change_log
    assert "583 documentation tests passed" in change_log
    assert "2465 total tests passed at 93.54% coverage" in change_log
    assert "Client Script customer-update generation applies" in operator_guide
    assert "`client_script_customer_updates()` accepts only primitive" in operator_guide
    assert "does not call `str()` or `repr()` on unsupported values" in operator_guide


def test_sprint_896_documents_client_script_generation_string_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-896-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Client Script generation string-subclass guard" in change_log
    assert "`client_script_customer_updates()`" in change_log
    assert "`Client Script generation field contains non-JSON value`" in change_log
    assert "1 failing-first Client Script string-subclass assertion" in change_log
    assert "Client Script generation text values require exact strings" in operator_guide
    assert (
        "`test_client_script_customer_updates_rejects_string_subclass_field_without_leak`"
        in change_log
    )


def test_sprint_510_documents_ui_policy_generation_field_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-510-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "UI Policy generation field non-JSON value rejection" in change_log
    assert "`ui_policy_customer_updates()`" in change_log
    assert "`UI Policy generation field contains non-JSON value`" in change_log
    assert "1 failing-first UI Policy generation test" in change_log
    assert "56 tests passed" in change_log
    assert "584 documentation tests passed" in change_log
    assert "2467 total tests passed at 93.55% coverage" in change_log
    assert "UI Policy customer-update generation now treats" in operator_guide
    assert "`ui_policy_customer_updates()` accepts only primitive" in operator_guide
    assert "does not call `str()` or `repr()` on unsupported values" in operator_guide


def test_sprint_897_documents_ui_policy_generation_string_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-897-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "UI Policy generation string-subclass guard" in change_log
    assert "`ui_policy_customer_updates()`" in change_log
    assert "`UI Policy generation field contains non-JSON value`" in change_log
    assert "1 failing-first UI Policy string-subclass assertion" in change_log
    assert "UI Policy generation text values require exact strings" in operator_guide
    assert (
        "`test_ui_policy_customer_updates_rejects_string_subclass_field_without_leak`"
        in change_log
    )


def test_sprint_511_documents_catalog_ui_policy_generation_field_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-511-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Catalog UI Policy generation field non-JSON value rejection" in change_log
    assert "`catalog_ui_policy_customer_updates()`" in change_log
    assert "`Catalog UI Policy generation field contains non-JSON value`" in change_log
    assert "1 failing-first Catalog UI Policy generation test" in change_log
    assert "57 tests passed" in change_log
    assert "585 documentation tests passed" in change_log
    assert "2469 total tests passed at 93.53% coverage" in change_log
    assert "Catalog UI Policy customer-update generation applies" in operator_guide
    assert "`catalog_ui_policy_customer_updates()` accepts only primitive" in operator_guide
    assert "does not call `str()` or `repr()` on unsupported values" in operator_guide


def test_sprint_898_documents_catalog_ui_policy_generation_string_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-898-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Catalog UI Policy generation string-subclass guard" in change_log
    assert "`catalog_ui_policy_customer_updates()`" in change_log
    assert "`Catalog UI Policy generation field contains non-JSON value`" in change_log
    assert "1 failing-first Catalog UI Policy string-subclass assertion" in change_log
    assert "Catalog UI Policy generation text values require exact strings" in operator_guide
    assert (
        "`test_catalog_ui_policy_customer_updates_rejects_string_subclass_field_without_leak`"
        in change_log
    )


def test_sprint_512_documents_catalog_client_script_generation_field_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-512-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Catalog Client Script generation field non-JSON value rejection" in change_log
    assert "`catalog_client_script_customer_updates()`" in change_log
    assert "`Catalog Client Script generation field contains non-JSON value`" in change_log
    assert "1 failing-first Catalog Client Script generation test" in change_log
    assert "22 tests passed" in change_log
    assert "586 documentation tests passed" in change_log
    assert "2471 total tests passed at 93.52% coverage" in change_log
    assert "Catalog Client Script customer-update generation uses" in operator_guide
    assert "`catalog_client_script_customer_updates()` accepts only primitive" in operator_guide
    assert "does not call `str()` or `repr()` on unsupported values" in operator_guide


def test_sprint_899_documents_catalog_client_script_generation_string_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-899-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Catalog Client Script generation string-subclass guard" in change_log
    assert "`catalog_client_script_customer_updates()`" in change_log
    assert "`Catalog Client Script generation field contains non-JSON value`" in change_log
    assert "1 failing-first Catalog Client Script string-subclass assertion" in change_log
    assert "Catalog Client Script generation text values require exact strings" in operator_guide
    assert (
        "`test_catalog_client_script_rejects_string_subclass_field_without_leak`"
        in change_log
    )


def test_sprint_513_documents_atf_test_plan_generation_field_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-513-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Advisory ATF test plan generation field non-JSON value rejection" in change_log
    assert "`generate_atf_test_plan()`" in change_log
    assert "`ATF test plan generation field contains non-JSON value`" in change_log
    assert "1 failing-first ATF test plan generation test" in change_log
    assert "30 tests passed" in change_log
    assert "587 documentation tests passed" in change_log
    assert "2473 total tests passed at 93.52% coverage" in change_log
    assert "Advisory ATF test plan generation now applies" in operator_guide
    assert "`generate_atf_test_plan()` accepts only primitive" in operator_guide
    assert "does not call `str()` or `repr()` on unsupported candidate fields" in (
        operator_guide
    )


def test_sprint_900_documents_atf_generation_string_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-900-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Advisory ATF test plan generation string-subclass guard" in change_log
    assert "`generate_atf_test_plan()`" in change_log
    assert "`ATF test plan generation field contains non-JSON value`" in change_log
    assert "1 failing-first ATF test plan string-subclass assertion" in change_log
    assert "ATF test plan generation text values require exact strings" in operator_guide
    assert (
        "`test_atf_test_plan_rejects_string_subclass_candidate_field_without_leak`"
        in change_log
    )


def test_sprint_901_documents_form_section_generation_string_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-901-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Form-section generation string-subclass guard" in change_log
    assert "`form_section_customer_updates()`" in change_log
    assert "`form section removal field contains non-JSON value`" in change_log
    assert "1 failing-first form-section string-subclass assertion" in change_log
    assert "Form-section removal text values require exact strings" in operator_guide
    assert (
        "`test_form_section_customer_updates_rejects_string_subclass_field_without_leak`"
        in change_log
    )


def test_sprint_926_documents_form_section_generation_scalar_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-926-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Form-section generation scalar-subclass guard" in change_log
    assert "`form_section_customer_updates()`" in change_log
    assert "`form section removal field contains non-JSON value`" in change_log
    assert "1 failing-first form-section scalar-subclass assertion" in change_log
    assert "Form-section removal scalar values require exact JSON scalar types" in operator_guide
    assert (
        "`test_form_section_customer_updates_rejects_scalar_subclass_field_without_leak`"
        in change_log
    )


def test_sprint_951_documents_form_section_container_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-951-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Form-section container-subclass guard" in change_log
    assert "`_section_names()`" in change_log
    assert "`_reference_display_or_value()`" in change_log
    assert "form section removal field contains non-JSON value" in change_log
    assert (
        "2 failing-first form-section container-subclass execution assertions"
        in change_log
    )
    assert "Form-section removal list and dictionary values are exact containers" in (
        operator_guide
    )
    assert "List and dictionary subclasses fail with" in operator_guide
    assert (
        "`test_form_section_customer_updates_rejects_list_subclass_field_without_leak`"
        in change_log
    )
    assert (
        "`test_form_section_customer_updates_rejects_dict_subclass_metadata_without_leak`"
        in change_log
    )


def test_sprint_1003_documents_form_section_metadata_record_collection_guard() -> None:
    change_log = Path("docs/sprints/sprint-1003-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Form-section metadata record collection guard" in change_log
    assert "`_form_section_metadata_records()`" in change_log
    assert "form section removal field contains non-JSON value" in change_log
    assert (
        "1 failing-first form-section metadata record collection subclass assertion"
        in change_log
    )
    assert (
        "Form-section removal ServiceNow metadata record collections are exact containers"
        in operator_guide
    )
    assert "`fetch_table_records()` responses for `sys_ui_section`" in operator_guide
    assert "before section iteration, view filtering" in operator_guide
    assert (
        "`test_form_section_customer_updates_rejects_metadata_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_form_section_customer_updates_rejects_metadata_record_subclass_without_leak`"
        in change_log
    )


def test_sprint_902_documents_dictionary_form_metadata_string_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-902-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Dictionary/form metadata string-subclass guard" in change_log
    assert "`dictionary_form_customer_updates()`" in change_log
    assert "`dictionary/form metadata field contains non-JSON value`" in change_log
    assert "1 failing-first dictionary/form metadata string-subclass assertion" in change_log
    assert "Dictionary/form metadata text values require exact strings" in operator_guide
    assert (
        "`test_generic_dictionary_form_rejects_string_subclass_metadata_without_leak`"
        in change_log
    )


def test_sprint_927_documents_dictionary_form_metadata_scalar_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-927-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Dictionary/form metadata scalar-subclass guard" in change_log
    assert "`dictionary_form_customer_updates()`" in change_log
    assert "`dictionary/form metadata field contains non-JSON value`" in change_log
    assert "1 failing-first dictionary/form metadata scalar-subclass assertion" in change_log
    assert (
        "Dictionary/form metadata scalar values require exact JSON scalar types"
        in operator_guide
    )
    assert (
        "`test_generic_dictionary_form_rejects_scalar_subclass_metadata_without_leak`"
        in change_log
    )


def test_sprint_903_documents_retrieved_update_set_customer_update_string_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-903-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set customer update string-subclass guard" in change_log
    assert "`import_retrieved_update_set()`" in change_log
    assert "`retrieved Update Set customer update contains non-JSON value`" in change_log
    assert "1 failing-first customer-update string-subclass assertion" in change_log
    assert "Retrieved Update Set customer update text values require exact strings" in (
        operator_guide
    )
    assert (
        "`test_import_retrieved_update_set_rejects_string_subclass_customer_update_without_leak`"
        in change_log
    )


def test_sprint_904_documents_packet_intent_catalog_ui_policy_tristate_guard() -> None:
    change_log = Path("docs/sprints/sprint-904-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Packet-intent catalog UI Policy tristate guard" in change_log
    assert "`_catalog_item_changes_from_normalized_intent()`" in change_log
    assert "catalog variable rule Show schedule action visible must be true, false, or ignore" in (
        change_log
    )
    assert "1 failing-first normalized-intent string-subclass assertion" in change_log
    assert "Normalized-intent catalog UI Policy action tristates are strict" in (
        operator_guide
    )
    assert (
        "`test_catalog_changes_reject_string_subclass_rule_action_without_leak`"
        in change_log
    )


def test_sprint_905_documents_packet_intent_catalog_client_script_action_guard() -> None:
    change_log = Path("docs/sprints/sprint-905-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Packet-intent catalog client script action guard" in change_log
    assert "`_catalog_item_changes_from_normalized_intent()`" in change_log
    assert "catalog client script populate_visitor action kind must be an exact string" in (
        change_log
    )
    assert "1 failing-first catalog client script action string-subclass assertion" in (
        change_log
    )
    assert "Normalized-intent catalog client script action text is exact-string only" in (
        operator_guide
    )
    assert (
        "`test_catalog_changes_reject_string_subclass_client_script_action_without_leak`"
        in change_log
    )


def test_sprint_906_documents_packet_intent_catalog_variable_set_name_guard() -> None:
    change_log = Path("docs/sprints/sprint-906-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Packet-intent catalog variable set name guard" in change_log
    assert "`_catalog_item_changes_from_normalized_intent()`" in change_log
    assert "catalog variable set names must be exact strings" in change_log
    assert "1 failing-first catalog variable set string-subclass assertion" in change_log
    assert "Normalized-intent catalog variable set names are exact-string only" in (
        operator_guide
    )
    assert (
        "`test_catalog_changes_reject_string_subclass_variable_set_without_leak`"
        in change_log
    )


def test_sprint_907_documents_packet_intent_catalog_variable_group_member_guard() -> None:
    change_log = Path("docs/sprints/sprint-907-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Packet-intent catalog variable group member guard" in change_log
    assert "`_catalog_item_changes_from_normalized_intent()`" in change_log
    assert "catalog variable group Schedule members must be exact strings" in change_log
    assert "1 failing-first catalog variable group member string-subclass assertion" in (
        change_log
    )
    assert "Normalized-intent catalog variable group members are exact-string only" in (
        operator_guide
    )
    assert (
        "`test_catalog_changes_reject_string_subclass_variable_group_member_without_leak`"
        in change_log
    )


def test_sprint_908_documents_packet_intent_catalog_ui_policy_cleared_guard() -> None:
    change_log = Path("docs/sprints/sprint-908-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Packet-intent catalog UI Policy cleared boolean guard" in change_log
    assert "`_catalog_item_changes_from_normalized_intent()`" in change_log
    assert "catalog variable rule Show schedule action cleared must be a boolean" in (
        change_log
    )
    assert "1 failing-first catalog UI Policy cleared truthiness assertion" in change_log
    assert "Normalized-intent catalog UI Policy cleared values are exact booleans" in (
        operator_guide
    )
    assert (
        "`test_catalog_changes_reject_hostile_rule_action_cleared_without_leak`"
        in change_log
    )


def test_sprint_909_documents_packet_intent_catalog_ui_policy_reverse_guard() -> None:
    change_log = Path("docs/sprints/sprint-909-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Packet-intent catalog UI Policy reverse_if_false boolean guard" in change_log
    assert "`_catalog_item_changes_from_normalized_intent()`" in change_log
    assert "catalog variable rule Show schedule reverse_if_false must be a boolean" in (
        change_log
    )
    assert "1 failing-first catalog UI Policy reverse_if_false truthiness assertion" in (
        change_log
    )
    assert "Normalized-intent catalog UI Policy reverse_if_false values are exact booleans" in (
        operator_guide
    )
    assert (
        "`test_catalog_changes_reject_hostile_rule_reverse_if_false_without_leak`"
        in change_log
    )


def test_sprint_910_documents_packet_intent_catalog_variable_mandatory_guard() -> None:
    change_log = Path("docs/sprints/sprint-910-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Packet-intent catalog variable mandatory boolean guard" in change_log
    assert "`_catalog_item_changes_from_normalized_intent()`" in change_log
    assert "catalog variable visitor_name mandatory must be a boolean" in change_log
    assert "1 failing-first catalog variable mandatory truthiness assertion" in change_log
    assert "Normalized-intent catalog variable mandatory values are exact booleans" in (
        operator_guide
    )
    assert (
        "`test_catalog_changes_reject_hostile_catalog_variable_mandatory_without_leak`"
        in change_log
    )


def test_sprint_911_documents_packet_intent_record_producer_variable_mandatory_guard() -> None:
    change_log = Path("docs/sprints/sprint-911-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Packet-intent record producer variable mandatory boolean guard" in change_log
    assert "`_record_producer_changes_from_normalized_intent()`" in change_log
    assert "record producer variable summary mandatory must be a boolean" in change_log
    assert "1 failing-first record producer mandatory truthiness assertion" in change_log
    assert "Normalized-intent record producer variable mandatory values are exact booleans" in (
        operator_guide
    )
    assert (
        "`test_record_producer_changes_reject_hostile_variable_mandatory_without_leak`"
        in change_log
    )


def test_sprint_912_documents_packet_intent_fulfillment_flow_attachment_flag_guard() -> None:
    change_log = Path("docs/sprints/sprint-912-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Packet-intent fulfillment flow attachment flag guard" in change_log
    assert "`_catalog_item_changes_from_normalized_intent()`" in change_log
    assert "catalog item fulfillment_flow_attachment_requested must be a boolean" in (
        change_log
    )
    assert "1 failing-first fulfillment flow attachment flag truthiness assertion" in (
        change_log
    )
    assert "Normalized-intent fulfillment flow attachment flags are exact booleans" in (
        operator_guide
    )
    assert (
        "`test_catalog_changes_reject_hostile_fulfillment_flow_attachment_flag_without_leak`"
        in change_log
    )


def test_sprint_913_documents_packet_intent_normalized_text_guard() -> None:
    change_log = Path("docs/sprints/sprint-913-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Packet-intent normalized text exact-string guard" in change_log
    assert "`_optional_intent_text()`" in change_log
    assert "normalized intent text values must be exact strings" in change_log
    assert "1 failing-first normalized text stringification assertion" in change_log
    assert "Normalized-intent text values are exact-string only" in operator_guide
    assert "`test_catalog_changes_reject_hostile_normalized_text_without_leak`" in change_log


def test_sprint_914_documents_packet_intent_normalized_order_guard() -> None:
    change_log = Path("docs/sprints/sprint-914-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Packet-intent normalized order exact-integer guard" in change_log
    assert "`_optional_intent_order()`" in change_log
    assert "normalized intent order values must be positive integers" in change_log
    assert "1 failing-first normalized order integer-coercion assertion" in change_log
    assert "Normalized-intent order values are exact positive integers" in operator_guide
    assert "`test_catalog_changes_reject_hostile_normalized_order_without_leak`" in change_log


def test_sprint_915_documents_packet_intent_ui_policy_render_guard() -> None:
    change_log = Path("docs/sprints/sprint-915-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Packet-intent UI Policy rendering exact-value guard" in change_log
    assert "`_catalog_ui_policy_changes()`" in change_log
    assert "catalog variable rule Show schedule action variable must be an exact string" in (
        change_log
    )
    assert "1 failing-first UI Policy renderer stringification assertion" in change_log
    assert "Catalog UI Policy rendering values are exact normalized values" in operator_guide
    assert (
        "`test_catalog_ui_policy_renderer_rejects_hostile_action_variable_without_leak`"
        in change_log
    )


def test_sprint_916_documents_packet_intent_client_script_render_guard() -> None:
    change_log = Path("docs/sprints/sprint-916-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Packet-intent client script rendering exact-value guard" in change_log
    assert "`_catalog_client_script_changes()`" in change_log
    assert "catalog client script name must be an exact string" in change_log
    assert "1 failing-first client script renderer stringification assertion" in change_log
    assert "Catalog client script rendering values are exact normalized values" in (
        operator_guide
    )
    assert (
        "`test_catalog_client_script_renderer_rejects_hostile_name_without_leak`"
        in change_log
    )


def test_sprint_917_documents_catalog_metadata_scalar_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-917-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Catalog metadata scalar-subclass guard" in change_log
    assert "`_catalog_field_text()`" in change_log
    assert "catalog item generation field contains non-JSON value" in change_log
    assert "1 failing-first catalog metadata scalar-subclass stringification assertion" in (
        change_log
    )
    assert "Catalog item customer-update metadata text accepts only exact JSON scalar values" in (
        operator_guide
    )
    assert (
        "`test_catalog_item_customer_updates_rejects_hostile_scalar_subclass_metadata`"
        in change_log
    )


def test_sprint_918_documents_catalog_client_script_scalar_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-918-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Catalog client script scalar-subclass guard" in change_log
    assert "`_catalog_client_script_field_text()`" in change_log
    assert "Catalog Client Script generation field contains non-JSON value" in change_log
    assert "1 failing-first catalog client script scalar-subclass stringification assertion" in (
        change_log
    )
    expected_operator_text = (
        "Catalog client script customer-update generation also accepts only exact JSON scalar"
    )
    assert expected_operator_text in operator_guide
    assert (
        "`test_catalog_client_script_rejects_scalar_subclass_field_without_leak`"
        in change_log
    )


def test_sprint_946_documents_catalog_client_script_list_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-946-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Catalog Client Script list-subclass guard" in change_log
    assert "`_catalog_client_script_string_list()`" in change_log
    assert "Catalog Client Script generation field contains non-JSON value" in change_log
    assert (
        "1 failing-first Catalog Client Script list-subclass iteration assertion"
        in change_log
    )
    assert "Catalog Client Script generation list values are exact containers" in (
        operator_guide
    )
    assert "list subclasses fail with" in operator_guide
    assert (
        "`test_catalog_client_script_rejects_list_subclass_field_without_leak`"
        in change_log
    )


def test_sprint_947_documents_catalog_item_container_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-947-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Catalog item container-subclass guard" in change_log
    assert "`_variable_set_names()`" in change_log
    assert "`_variable_group_intents()`" in change_log
    assert "`_reference_value()`" in change_log
    assert "catalog item generation field contains non-JSON value" in change_log
    assert (
        "2 failing-first catalog item container-subclass execution assertions"
        in change_log
    )
    assert "Catalog item generation list and dictionary values are exact containers" in (
        operator_guide
    )
    assert "List and dictionary subclasses fail with" in operator_guide
    assert (
        "`test_catalog_item_customer_updates_rejects_list_subclass_item_field_without_leak`"
        in change_log
    )
    assert (
        "`test_catalog_item_customer_updates_rejects_dict_subclass_metadata_without_leak`"
        in change_log
    )


def test_sprint_1000_documents_catalog_metadata_record_collection_guard() -> None:
    change_log = Path("docs/sprints/sprint-1000-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Catalog metadata record collection guard" in change_log
    assert "`_catalog_metadata_records()`" in change_log
    assert "catalog item generation field contains non-JSON value" in change_log
    assert "1 failing-first catalog metadata record collection subclass assertion" in (
        change_log
    )
    assert "Catalog item ServiceNow metadata record collections are exact containers" in (
        operator_guide
    )
    assert "`fetch_table_records()` must be exact lists containing exact dictionaries" in (
        operator_guide
    )
    assert "before active record filtering, display matching" in operator_guide
    assert (
        "`test_catalog_item_customer_updates_rejects_metadata_record_collection_subclass`"
        in change_log
    )
    assert (
        "`test_catalog_item_customer_updates_rejects_metadata_record_subclass`"
        in change_log
    )


def test_sprint_1002_documents_dictionary_form_metadata_record_collection_guard() -> None:
    change_log = Path("docs/sprints/sprint-1002-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Dictionary/form metadata record collection guard" in change_log
    assert "`_dictionary_form_metadata_records()`" in change_log
    assert "dictionary/form metadata field contains non-JSON value" in change_log
    assert (
        "1 failing-first dictionary/form metadata record collection subclass assertion"
        in change_log
    )
    assert (
        "Dictionary/form ServiceNow metadata record collections are exact containers"
        in operator_guide
    )
    assert "`fetch_table_records()` responses for `sys_ui_section` and `sys_ui_element`" in (
        operator_guide
    )
    assert "before section iteration, default-view filtering" in operator_guide
    assert (
        "`test_generic_dictionary_form_rejects_metadata_record_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_generic_dictionary_form_rejects_metadata_record_subclass_without_leak`"
        in change_log
    )


def test_sprint_919_documents_business_rule_scalar_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-919-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Business Rule scalar-subclass guard" in change_log
    assert "`_business_rule_field_text()`" in change_log
    assert "Business Rule generation field contains non-JSON value" in change_log
    assert "1 failing-first Business Rule scalar-subclass stringification assertion" in change_log
    assert "Business Rule generation scalar values are exact JSON scalars" in operator_guide
    assert (
        "`test_business_rule_customer_updates_rejects_scalar_subclass_field_without_leak`"
        in change_log
    )


def test_sprint_950_documents_business_rule_list_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-950-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Business Rule list-subclass guard" in change_log
    assert "`_business_rule_string_list()`" in change_log
    assert "Business Rule generation field contains non-JSON value" in change_log
    assert (
        "1 failing-first Business Rule list-subclass iteration assertion"
        in change_log
    )
    assert "Business Rule generation list values are exact containers" in operator_guide
    assert "List subclasses fail with" in operator_guide
    assert (
        "`test_business_rule_customer_updates_rejects_list_subclass_field_without_leak`"
        in change_log
    )


def test_sprint_920_documents_client_script_scalar_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-920-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Client Script scalar-subclass guard" in change_log
    assert "`_client_script_field_text()`" in change_log
    assert "Client Script generation field contains non-JSON value" in change_log
    assert "1 failing-first Client Script scalar-subclass stringification assertion" in change_log
    assert "Client Script generation scalar values are exact JSON scalars" in operator_guide
    assert (
        "`test_client_script_customer_updates_rejects_scalar_subclass_field_without_leak`"
        in change_log
    )


def test_sprint_948_documents_client_script_list_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-948-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Client Script list-subclass guard" in change_log
    assert "`_client_script_string_list()`" in change_log
    assert "Client Script generation field contains non-JSON value" in change_log
    assert (
        "1 failing-first Client Script list-subclass iteration assertion"
        in change_log
    )
    assert "Client Script generation list values are exact containers" in operator_guide
    assert "List subclasses fail with" in operator_guide
    assert (
        "`test_client_script_customer_updates_rejects_list_subclass_field_without_leak`"
        in change_log
    )


def test_sprint_921_documents_script_include_scalar_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-921-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Script Include scalar-subclass guard" in change_log
    assert "`_script_include_field_text()`" in change_log
    assert "Script Include generation field contains non-JSON value" in change_log
    assert "1 failing-first Script Include scalar-subclass stringification assertion" in change_log
    assert "Script Include generation scalar values are exact JSON scalars" in operator_guide
    assert (
        "`test_script_include_customer_updates_rejects_scalar_subclass_field_without_leak`"
        in change_log
    )


def test_sprint_949_documents_script_include_list_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-949-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Script Include list-subclass guard" in change_log
    assert "`_script_include_string_list()`" in change_log
    assert "Script Include generation field contains non-JSON value" in change_log
    assert (
        "1 failing-first Script Include list-subclass iteration assertion"
        in change_log
    )
    assert "Script Include generation list values are exact containers" in operator_guide
    assert "List subclasses fail with" in operator_guide
    assert (
        "`test_script_include_customer_updates_rejects_list_subclass_field_without_leak`"
        in change_log
    )


def test_sprint_922_documents_ui_policy_scalar_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-922-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "UI Policy scalar-subclass guard" in change_log
    assert "`_ui_policy_field_text()`" in change_log
    assert "UI Policy generation field contains non-JSON value" in change_log
    assert "1 failing-first UI Policy scalar-subclass stringification assertion" in change_log
    assert "UI Policy generation scalar values are exact JSON scalars" in operator_guide
    assert (
        "`test_ui_policy_customer_updates_rejects_scalar_subclass_field_without_leak`"
        in change_log
    )


def test_sprint_923_documents_catalog_ui_policy_scalar_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-923-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Catalog UI Policy scalar-subclass guard" in change_log
    assert "`_catalog_ui_policy_field_text()`" in change_log
    assert "Catalog UI Policy generation field contains non-JSON value" in change_log
    assert (
        "1 failing-first Catalog UI Policy scalar-subclass stringification assertion"
        in change_log
    )
    assert "Catalog UI Policy generation scalar values are exact JSON scalars" in operator_guide
    assert (
        "`test_catalog_ui_policy_customer_updates_rejects_scalar_subclass_field_without_leak`"
        in change_log
    )


def test_sprint_924_documents_record_producer_scalar_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-924-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Record producer scalar-subclass guard" in change_log
    assert "`_record_producer_field_text()`" in change_log
    assert "record producer generation field contains non-JSON value" in change_log
    assert "1 failing-first Record Producer scalar-subclass stringification assertion" in change_log
    assert "Record producer generation scalar values are exact JSON scalars" in operator_guide
    assert (
        "`test_record_producer_customer_updates_rejects_scalar_subclass_field_without_leak`"
        in change_log
    )


def test_sprint_925_documents_atf_generation_scalar_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-925-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ATF generation scalar-subclass guard" in change_log
    assert "`_atf_field_text()`" in change_log
    assert "ATF test plan generation field contains non-JSON value" in change_log
    assert "1 failing-first ATF scalar-subclass stringification assertion" in change_log
    assert "ATF test plan generation scalar values are exact JSON scalars" in operator_guide
    assert (
        "`test_atf_test_plan_rejects_scalar_subclass_candidate_field_without_leak`"
        in change_log
    )


def test_sprint_945_documents_atf_generation_list_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-945-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ATF generation list-subclass guard" in change_log
    assert "`_atf_string_list()`" in change_log
    assert "ATF test plan generation field contains non-JSON value" in change_log
    assert "1 failing-first ATF list-subclass iteration assertion" in change_log
    assert "ATF test plan generation list values are exact containers" in operator_guide
    assert "list subclasses fail with" in operator_guide
    assert (
        "`test_atf_test_plan_rejects_list_subclass_candidate_field_without_leak`"
        in change_log
    )


def test_sprint_514_documents_dictionary_form_metadata_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-514-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Dictionary/form metadata non-JSON value rejection" in change_log
    assert "`dictionary_form_customer_updates()`" in change_log
    assert "`dictionary/form metadata field contains non-JSON value`" in change_log
    assert "1 failing-first dictionary/form metadata test" in change_log
    assert "6 tests passed" in change_log
    assert "588 documentation tests passed" in change_log
    assert "2475 total tests passed at 93.49% coverage" in change_log
    assert "Dictionary/form live metadata consumption is strict as well" in operator_guide
    assert "`dictionary_form_customer_updates()` accepts only primitive" in operator_guide
    assert "does not call `str()` or `repr()` on unsupported fetched ServiceNow metadata" in (
        operator_guide
    )


def test_sprint_515_documents_retrieved_update_set_lookup_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-515-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set lookup non-JSON value rejection" in change_log
    assert "`import_retrieved_update_set()`" in change_log
    assert "`retrieved Update Set lookup contains non-JSON value`" in change_log
    assert "1 failing-first retrieved Update Set lookup test" in change_log
    assert "24 tests passed" in change_log
    assert "589 documentation tests passed" in change_log
    assert "2477 total tests passed at 93.48% coverage" in change_log
    assert "Retrieved Update Set post-import lookup handling is strict as well" in (
        operator_guide
    )
    assert "accepts only primitive string, boolean, and integer scalar values" in (
        operator_guide
    )
    assert "does not call `str()` or `repr()` on unsupported ServiceNow response values" in (
        operator_guide
    )


def test_sprint_516_documents_legacy_update_set_apply_lookup_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-516-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Legacy Update Set apply lookup non-JSON value rejection" in change_log
    assert "`apply_candidate_to_update_set()`" in change_log
    assert "`Update Set apply lookup contains non-JSON value`" in change_log
    assert "1 failing-first legacy Update Set apply lookup test" in change_log
    assert "12 tests passed" in change_log
    assert "590 documentation tests passed" in change_log
    assert "2479 total tests passed at 93.46% coverage" in change_log
    assert "Legacy local Update Set apply lookup handling is strict" in operator_guide
    assert "`apply_candidate_to_update_set()` accepts only primitive" in operator_guide
    assert "does not call `str()` or `repr()` on unsupported ServiceNow response values" in (
        operator_guide
    )


def test_sprint_517_documents_update_set_importer_lookup_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-517-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set importer bootstrap lookup non-JSON value rejection" in change_log
    assert "`apply_update_set_importer_records()`" in change_log
    assert "`verify_update_set_importer_records()`" in change_log
    assert "`Update Set importer lookup contains non-JSON value`" in change_log
    assert "1 failing-first Update Set importer bootstrap lookup test" in change_log
    assert "20 tests passed" in change_log
    assert "Update Set importer bootstrap lookup handling is strict" in operator_guide
    assert "`apply_update_set_importer_records()` and `verify_update_set_importer_records()`" in (
        operator_guide
    )
    assert "does not call `str()` or `repr()` on unsupported ServiceNow response values" in (
        operator_guide
    )


def test_sprint_518_documents_update_set_importer_apply_result_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-518-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set importer apply-result sys_id non-JSON value rejection" in change_log
    assert "`UpdateSetImporterApplyResult.upserted_records`" in change_log
    assert "`apply_update_set_importer_records()`" in change_log
    assert "`Update Set importer lookup contains non-JSON value`" in change_log
    assert "1 failing-first Update Set importer apply-result test" in change_log
    assert "21 tests passed" in change_log
    assert "Update Set importer bootstrap apply results are strict too" in operator_guide
    assert "before adding it to `upserted_records`" in operator_guide
    assert "before an apply result can expose object representations" in operator_guide


def test_sprint_998_documents_update_set_importer_apply_response_guard() -> None:
    change_log = Path("docs/sprints/sprint-998-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set importer apply response guard" in change_log
    assert "`_update_set_importer_upsert_result()`" in change_log
    assert "Update Set importer lookup contains non-JSON value" in change_log
    assert (
        "1 failing-first Update Set importer definition response subclass assertion"
        in change_log
    )
    assert "Update Set importer bootstrap apply results are strict too" in (
        operator_guide
    )
    assert "`apply_update_set_importer_records()` accepts only exact Python dictionaries" in (
        operator_guide
    )
    assert "before response-field access" in operator_guide
    assert "dependent operation upserts" in operator_guide
    assert (
        "`test_apply_update_set_importer_records_rejects_definition_response_subclass`"
        in change_log
    )
    assert (
        "`test_apply_update_set_importer_records_rejects_operation_response_subclass`"
        in change_log
    )


def test_sprint_887_documents_update_set_importer_lookup_string_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-887-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set importer lookup string-subclass guard" in change_log
    assert "2 failing-first Update Set importer lookup string-subclass assertions" in change_log
    assert "Update Set importer lookup text values require exact strings" in operator_guide
    assert (
        "`test_apply_update_set_importer_records_rejects_string_subclass_definition_lookup`"
        in change_log
    )
    assert (
        "`test_verify_update_set_importer_records_rejects_string_subclass_definition_lookup`"
        in change_log
    )


def test_sprint_519_documents_lifecycle_webhook_lookup_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-519-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Lifecycle webhook bootstrap lookup non-JSON value rejection" in change_log
    assert "`apply_lifecycle_webhook_records()`" in change_log
    assert "`verify_lifecycle_webhook_records()`" in change_log
    assert "`Lifecycle webhook lookup contains non-JSON value`" in change_log
    assert "1 failing-first lifecycle webhook bootstrap lookup test" in change_log
    assert "22 tests passed" in change_log
    assert "Lifecycle webhook bootstrap lookup handling is strict" in operator_guide
    assert "`apply_lifecycle_webhook_records()` and `verify_lifecycle_webhook_records()`" in (
        operator_guide
    )
    assert "does not call `str()` or `repr()` on unsupported ServiceNow response values" in (
        operator_guide
    )


def test_sprint_520_documents_lifecycle_webhook_apply_result_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-520-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Lifecycle webhook apply-result sys_id non-JSON value rejection" in change_log
    assert "`LifecycleWebhookApplyResult.upserted_records`" in change_log
    assert "`apply_lifecycle_webhook_records()`" in change_log
    assert "`Lifecycle webhook lookup contains non-JSON value`" in change_log
    assert "1 failing-first lifecycle webhook apply-result test" in change_log
    assert "23 tests passed" in change_log
    assert "Lifecycle webhook bootstrap apply results are strict too" in operator_guide
    assert "before adding it to `upserted_records`" in operator_guide
    assert "before an apply result can expose object representations" in operator_guide


def test_sprint_888_documents_lifecycle_webhook_lookup_string_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-888-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Lifecycle webhook lookup string-subclass guard" in change_log
    assert "2 failing-first lifecycle webhook lookup string-subclass assertions" in change_log
    assert "Lifecycle webhook lookup text values require exact strings" in operator_guide
    assert (
        "`test_apply_lifecycle_webhook_records_rejects_string_subclass_rest_message_lookup`"
        in change_log
    )
    assert (
        "`test_verify_lifecycle_webhook_records_rejects_string_subclass_rest_message_lookup`"
        in change_log
    )


def test_sprint_999_documents_bootstrap_verification_record_guard() -> None:
    change_log = Path("docs/sprints/sprint-999-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Bootstrap verification record guard" in change_log
    assert "`_lifecycle_webhook_fetch_result()`" in change_log
    assert "`_update_set_importer_fetch_result()`" in change_log
    assert "Lifecycle webhook lookup contains non-JSON value" in change_log
    assert "Update Set importer lookup contains non-JSON value" in change_log
    assert "1 failing-first lifecycle webhook verification record subclass assertion" in (
        change_log
    )
    assert "Lifecycle webhook bootstrap verification records require exact dictionaries" in (
        operator_guide
    )
    assert "Update Set importer bootstrap verification records require exact dictionaries" in (
        operator_guide
    )
    assert "before field mismatch checks" in operator_guide
    assert "verification-result recording" in operator_guide
    assert (
        "`test_verify_lifecycle_webhook_records_rejects_rest_message_record_subclass`"
        in change_log
    )
    assert (
        "`test_verify_update_set_importer_records_rejects_definition_record_subclass`"
        in change_log
    )


def test_sprint_891_documents_lifecycle_webhook_verification_metadata_guard() -> None:
    change_log = Path("docs/sprints/sprint-891-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Lifecycle webhook verification metadata guard" in change_log
    assert "2 failing-first lifecycle verification metadata assertions" in change_log
    assert "Lifecycle webhook verification metadata normalization is safe" in operator_guide
    assert (
        "`test_verify_lifecycle_webhook_records_rejects_string_subclass_boolean_metadata`"
        in change_log
    )
    assert (
        "`test_verify_lifecycle_webhook_records_rejects_string_subclass_reference_metadata`"
        in change_log
    )


def test_sprint_521_documents_servicenow_upsert_lookup_non_json_rejection() -> None:
    change_log = Path("docs/sprints/sprint-521-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow client upsert lookup sys_id non-JSON value rejection" in change_log
    assert "`ServiceNowClient.upsert_table_record()`" in change_log
    assert "`ServiceNow API lookup contains non-JSON value`" in change_log
    assert "1 failing-first ServiceNow client upsert lookup test" in change_log
    assert "99 tests passed" in change_log
    assert "ServiceNow upsert lookup handling is strict as well" in operator_guide
    assert "before building the PATCH URL" in operator_guide
    assert "does not call `str()` or `repr()` on unsupported lookup response values" in (
        operator_guide
    )


def test_sprint_522_documents_servicenow_lookup_query_delimiter_rejection() -> None:
    change_log = Path("docs/sprints/sprint-522-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow Table API lookup query delimiter rejection" in change_log
    assert "`ServiceNowClient.fetch_table_record()`" in change_log
    assert "`ServiceNowClient.fetch_table_records()`" in change_log
    assert "`ServiceNow API lookup query is unsafe`" in change_log
    assert "1 failing-first ServiceNow client lookup query test" in change_log
    assert "100 tests passed" in change_log
    assert "ServiceNow Table API lookup query construction is delimiter-safe" in (
        operator_guide
    )
    assert "before OAuth token acquisition" in operator_guide
    assert "does not echo lookup values" in operator_guide


def test_sprint_523_documents_servicenow_table_name_path_rejection() -> None:
    change_log = Path("docs/sprints/sprint-523-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow Table API table-name path rejection" in change_log
    assert "`ServiceNowClient.upsert_table_record()`" in change_log
    assert "`ServiceNowClient.fetch_table_record()`" in change_log
    assert "`ServiceNowClient.fetch_table_records()`" in change_log
    assert "`ServiceNow API table name is unsafe`" in change_log
    assert "1 failing-first ServiceNow client table-name test" in change_log
    assert "101 tests passed" in change_log
    assert "Generic ServiceNow Table API table names are path-safe" in operator_guide
    assert "before OAuth token acquisition or request construction" in operator_guide
    assert "does not echo table values" in operator_guide


def test_sprint_524_documents_servicenow_record_id_path_rejection() -> None:
    change_log = Path("docs/sprints/sprint-524-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow Table API record-id path rejection" in change_log
    assert "`ServiceNowClient.update_story_fields()`" in change_log
    assert "`ServiceNowClient.upsert_table_record()`" in change_log
    assert "`ServiceNow API record id is unsafe`" in change_log
    assert "1 failing-first ServiceNow client record-id test" in change_log
    assert "102 tests passed" in change_log
    assert "ServiceNow Table API record ids used in URL paths are path-safe" in (
        operator_guide
    )
    assert "before OAuth token acquisition or request construction" in operator_guide
    assert "does not echo record id values" in operator_guide


def test_sprint_525_documents_servicenow_cicd_path_id_rejection() -> None:
    change_log = Path("docs/sprints/sprint-525-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow CI/CD path-id rejection" in change_log
    assert "`ServiceNowClient.preview_cicd_update_set()`" in change_log
    assert "`ServiceNowClient.commit_cicd_update_set()`" in change_log
    assert "`ServiceNowClient.fetch_cicd_progress()`" in change_log
    assert "`ServiceNow API record id is unsafe`" in change_log
    assert "1 failing-first ServiceNow CI/CD progress-id test" in change_log
    assert "103 tests passed" in change_log
    assert "ServiceNow CI/CD Update Set path ids use the same record-id safety rule" in (
        operator_guide
    )
    assert "before OAuth token acquisition or request construction" in operator_guide
    assert "does not echo CI/CD ids" in operator_guide


def test_sprint_526_documents_servicenow_importer_operation_uri_rejection() -> None:
    change_log = Path("docs/sprints/sprint-526-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow importer operation URI path rejection" in change_log
    assert "`ServiceNowClient.import_update_set_xml()`" in change_log
    assert "`sys_ws_operation.operation_uri`" in change_log
    assert "`ServiceNow API operation URI is unsafe`" in change_log
    assert "1 failing-first ServiceNow importer operation URI test" in change_log
    assert "104 tests passed" in change_log
    assert "Discovered ServiceNow Scripted REST operation URIs are path-safe before use" in (
        operator_guide
    )
    assert "before the import POST is constructed" in operator_guide
    assert "does not echo operation URI values" in operator_guide


def test_sprint_558_documents_servicenow_operation_uri_length_guard() -> None:
    change_log = Path("docs/sprints/sprint-558-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow operation URI length guard" in change_log
    assert "`ServiceNowClient.import_update_set_xml()`" in change_log
    assert "`_servicenow_operation_uri()`" in change_log
    assert "`sys_ws_operation.operation_uri`" in change_log
    assert "`ServiceNow API operation URI is unsafe`" in change_log
    assert "1 failing-first ServiceNow importer operation URI length test" in change_log
    assert "did not raise `ServiceNowApiError`" in change_log
    assert "operation URIs are path-safe before use and bounded" in operator_guide
    assert "no longer than 256 characters" in operator_guide
    assert "before the import POST is constructed" in operator_guide
    assert "does not echo operation URI values" in operator_guide


def test_sprint_527_documents_servicenow_attachment_story_id_before_file_read() -> None:
    change_log = Path("docs/sprints/sprint-527-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow attachment story-id validation before file read" in change_log
    assert "`ServiceNowClient.attach_story_file()`" in change_log
    assert "`read_regular_artifact_bytes()`" in change_log
    assert "`ServiceNow API record id is unsafe`" in change_log
    assert "1 failing-first ServiceNow attachment story-id test" in change_log
    assert "105 tests passed" in change_log
    assert "Attachment target story ids are validated before local file reads" in operator_guide
    assert "before reading the attachment artifact" in operator_guide
    assert "does not echo record id values" in operator_guide


def test_sprint_528_documents_servicenow_attachment_metadata_before_file_read() -> None:
    change_log = Path("docs/sprints/sprint-528-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow attachment metadata validation before file read" in change_log
    assert "`ServiceNowClient.attach_story_file()`" in change_log
    assert "`file_name`" in change_log
    assert "`content_type`" in change_log
    assert "`read_regular_artifact_bytes()`" in change_log
    assert "`ServiceNow attachment file name is unsafe`" in change_log
    assert "`ServiceNow attachment content type is unsafe`" in change_log
    assert "2 failing-first ServiceNow attachment metadata tests" in change_log
    assert "Attachment upload metadata is validated before local file reads" in operator_guide
    assert "ordinary internal spaces" in operator_guide
    assert "simple MIME type/subtype tokens" in operator_guide
    assert "without echoing submitted metadata values" in operator_guide


def test_sprint_529_documents_servicenow_attachment_read_error_path_redaction() -> None:
    change_log = Path("docs/sprints/sprint-529-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow attachment read-error path redaction" in change_log
    assert "`ServiceNowClient.attach_story_file()`" in change_log
    assert "`file_path`" in change_log
    assert "`ServiceNow attachment file must be a regular file`" in change_log
    assert "`ArtifactReadError.reason`" in change_log
    assert "1 failing-first ServiceNow attachment read-error test" in change_log
    assert "absolute attachment path" in change_log
    assert "Symlinked or non-regular attachment paths fail with the fixed diagnostic" in (
        operator_guide
    )
    assert "without echoing local path values" in operator_guide
    assert "credential-like payloads" in operator_guide


def test_sprint_547_documents_servicenow_attachment_metadata_type_guards() -> None:
    change_log = Path("docs/sprints/sprint-547-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow attachment metadata type guards" in change_log
    assert "`_servicenow_attachment_file_name()`" in change_log
    assert "`_servicenow_attachment_content_type()`" in change_log
    assert "`AttributeError` with hostile object representations" in change_log
    assert "`ServiceNow attachment file name is unsafe`" in change_log
    assert "`ServiceNow attachment content type is unsafe`" in change_log
    assert "2 failing-first ServiceNow attachment metadata type tests" in change_log
    assert "without calling `str()` or `repr()` for diagnostics" in change_log
    assert "Non-string and unsafe metadata fails with fixed diagnostics" in operator_guide
    assert "before string-method calls" in operator_guide
    assert "without echoing object type names" in operator_guide


def test_sprint_560_documents_servicenow_attachment_content_type_length_guard() -> None:
    change_log = Path("docs/sprints/sprint-560-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow attachment content-type length guard" in change_log
    assert "`_servicenow_attachment_content_type()`" in change_log
    assert "`ServiceNowClient.attach_story_file()`" in change_log
    assert "`ServiceNow attachment content type is unsafe`" in change_log
    assert "1 failing-first ServiceNow attachment content-type length test" in change_log
    assert "reached `read_regular_artifact_bytes()`" in change_log
    assert "Attachment upload metadata is validated before local file reads" in operator_guide
    assert "Attachment content types must be string, no longer than 255 characters" in (
        operator_guide
    )
    assert "oversized metadata uses the same fixed diagnostics" in operator_guide
    assert "without echoing submitted metadata values" in operator_guide


def test_sprint_579_documents_servicenow_attachment_file_name_str_subclass_guard() -> (
    None
):
    change_log = Path("docs/sprints/sprint-579-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow attachment file-name string-subclass guard" in change_log
    assert "`_servicenow_attachment_file_name()`" in change_log
    assert "`ServiceNowClient.attach_story_file()`" in change_log
    assert "`ServiceNow attachment file name is unsafe`" in change_log
    assert (
        "1 failing-first ServiceNow attachment file-name string-subclass test"
        in change_log
    )
    assert "raised `RuntimeError` from overridden `strip()`" in change_log
    assert (
        "ServiceNow attachment file-name validation is type-safe before string handling"
        in operator_guide
    )
    assert "Attachment file names must be exact `str` instances" in operator_guide
    assert "string subclasses" in operator_guide
    assert "before local file reads" in operator_guide


def test_sprint_580_documents_servicenow_attachment_content_type_str_subclass_guard() -> (
    None
):
    change_log = Path("docs/sprints/sprint-580-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow attachment content-type string-subclass guard" in change_log
    assert "`_servicenow_attachment_content_type()`" in change_log
    assert "`ServiceNowClient.attach_story_file()`" in change_log
    assert "`ServiceNow attachment content type is unsafe`" in change_log
    assert (
        "1 failing-first ServiceNow attachment content-type string-subclass test"
        in change_log
    )
    assert "raised `RuntimeError` from overridden `strip()`" in change_log
    assert (
        "ServiceNow attachment content-type validation is type-safe before string handling"
        in operator_guide
    )
    assert "Attachment content types must be exact `str` instances" in operator_guide
    assert "string subclasses" in operator_guide
    assert "before local file reads" in operator_guide


def test_sprint_581_documents_servicenow_oauth_access_token_str_subclass_guard() -> (
    None
):
    change_log = Path("docs/sprints/sprint-581-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow OAuth access-token string-subclass guard" in change_log
    assert "`OAuthClientCredentials._fetch_token()`" in change_log
    assert "`ServiceNow OAuth response did not include access_token`" in change_log
    assert "1 failing-first ServiceNow OAuth access-token string-subclass test" in (
        change_log
    )
    assert "raised `RuntimeError` from overridden `strip()`" in change_log
    assert (
        "ServiceNow OAuth access-token validation is type-safe before string handling"
        in operator_guide
    )
    assert "Access-token values must be exact `str` instances" in operator_guide
    assert "string subclasses" in operator_guide
    assert "before caching the token" in operator_guide


def test_sprint_582_documents_servicenow_lookup_part_str_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-582-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow lookup part string-subclass guard" in change_log
    assert "`_is_unsafe_servicenow_lookup_part()`" in change_log
    assert "`_servicenow_lookup_query()`" in change_log
    assert "`ServiceNow API lookup query is unsafe`" in change_log
    assert "2 failing-first ServiceNow lookup part string-subclass tests" in (
        change_log
    )
    assert "raised `RuntimeError` from overridden `__iter__()`" in change_log
    assert "lookup keys and values must be exact `str` instances" in operator_guide
    assert "string subclasses" in operator_guide
    assert "before delimiter checks" in operator_guide


def test_sprint_583_documents_servicenow_story_response_text_str_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-583-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow story response text string-subclass guard" in change_log
    assert "`_servicenow_story_response_text()`" in change_log
    assert "`_optional_servicenow_story_response_text()`" in change_log
    assert "`ServiceNow API story response field is unsafe`" in change_log
    assert "1 failing-first ServiceNow story response text string-subclass test" in (
        change_log
    )
    assert "raised `RuntimeError` from overridden `strip()`" in change_log
    assert "Story response text values must be exact `str` instances" in operator_guide
    assert "string subclasses" in operator_guide
    assert "before optional acceptance-criteria trimming" in operator_guide


def test_sprint_584_documents_servicenow_lookup_response_text_str_subclass_guard() -> (
    None
):
    change_log = Path("docs/sprints/sprint-584-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow lookup response text string-subclass guard" in change_log
    assert "`_servicenow_lookup_text()`" in change_log
    assert "`ServiceNowClient.upsert_table_record()`" in change_log
    assert "`ServiceNow API lookup contains non-JSON value`" in change_log
    assert "1 failing-first ServiceNow lookup response text string-subclass test" in (
        change_log
    )
    assert "`ServiceNow API record id is unsafe`" in change_log
    assert "lookup response text values must be exact `str` instances" in operator_guide
    assert "string subclasses" in operator_guide
    assert "before building the PATCH URL" in operator_guide


def test_sprint_585_documents_servicenow_api_diagnostic_text_str_subclass_guard() -> (
    None
):
    change_log = Path("docs/sprints/sprint-585-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow API diagnostic text string-subclass guard" in change_log
    assert "`_servicenow_diagnostic_value()`" in change_log
    assert "`[non-json value]`" in change_log
    assert "1 failing-first ServiceNow API diagnostic text string-subclass test" in (
        change_log
    )
    assert "accepted as redacted diagnostic text before implementation" in change_log
    assert "ServiceNow API exception diagnostic text values must be exact `str`" in (
        operator_guide
    )
    assert "string subclasses and unsupported scalar values render as `[non-json value]`" in (
        operator_guide
    )
    assert "before redaction, whitespace normalization, or `repr()` formatting" in (
        operator_guide
    )


def test_sprint_586_documents_servicenow_secret_redaction_str_subclass_guard() -> (
    None
):
    change_log = Path("docs/sprints/sprint-586-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow secret redaction string-subclass guard" in change_log
    assert "`redact_secrets()`" in change_log
    assert "`isinstance(value, str)`" in change_log
    assert "`[non-json value]`" in change_log
    assert "1 failing-first ServiceNow secret redaction string-subclass test" in (
        change_log
    )
    assert "accepted and redacted as ordinary text before implementation" in change_log
    assert "ServiceNow diagnostic secret redaction treats text values as untrusted" in (
        operator_guide
    )
    assert "accepts only exact `str` instances for diagnostic text redaction" in (
        operator_guide
    )
    assert "String subclasses render as" in operator_guide
    assert "`[non-json value]` before URL" in operator_guide


def test_sprint_587_documents_servicenow_http_error_diagnostic_str_subclass_guard() -> (
    None
):
    change_log = Path("docs/sprints/sprint-587-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow HTTP error diagnostic string-subclass guard" in change_log
    assert "`_bound_http_error_diagnostics()`" in change_log
    assert "`[non-json value]`" in change_log
    assert "1 failing-first ServiceNow HTTP error diagnostic string-subclass test" in (
        change_log
    )
    assert "was reflected before implementation" in change_log
    assert "Parsed HTTP error diagnostic text values must be exact `str`" in (
        operator_guide
    )
    assert "string subclasses render as `[non-json value]`" in operator_guide
    assert "before truncation" in operator_guide


def test_sprint_588_documents_servicenow_api_diagnostic_key_projection() -> None:
    change_log = Path("docs/sprints/sprint-588-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow API diagnostic key projection" in change_log
    assert "`_servicenow_diagnostic_value()`" in change_log
    assert "`[non-json key]`" in change_log
    assert "1 failing-first ServiceNow API diagnostic key projection test" in (
        change_log
    )
    assert "hostile dictionary key `repr()` was reflected before implementation" in (
        change_log
    )
    assert "Diagnostic object keys are also projected before exception formatting" in (
        operator_guide
    )
    assert "duplicate rendered keys receive deterministic suffixes" in operator_guide
    assert "non-string keys render as `[non-json key]`" in operator_guide
    assert "without calling `str()` or `repr()` on the original key" in operator_guide


def test_sprint_589_documents_servicenow_http_error_diagnostic_key_projection() -> None:
    change_log = Path("docs/sprints/sprint-589-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow HTTP error diagnostic key projection" in change_log
    assert "`_bound_http_error_diagnostics()`" in change_log
    assert "`[non-json key]`" in change_log
    assert "1 failing-first ServiceNow HTTP error diagnostic key projection test" in (
        change_log
    )
    assert "hostile dictionary key `repr()` was reflected before implementation" in (
        change_log
    )
    assert "Parsed HTTP error diagnostic object keys are projected before response propagation" in (
        operator_guide
    )
    assert "duplicate rendered keys receive deterministic suffixes" in operator_guide
    assert "non-string keys render as `[non-json key]`" in operator_guide
    assert "without calling `str()` or `repr()` on the original key" in operator_guide


def test_sprint_935_documents_servicenow_diagnostic_exact_container_boundary() -> (
    None
):
    change_log = Path("docs/sprints/sprint-935-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow diagnostic exact-container boundary" in change_log
    assert "`_bound_http_error_diagnostics()`" in change_log
    assert "`_servicenow_diagnostic_value()`" in change_log
    assert "`redact_secrets()`" in change_log
    assert "3 failing-first ServiceNow diagnostic container-subclass assertions" in change_log
    assert "Parsed ServiceNow HTTP error JSON diagnostics" in operator_guide
    assert "Dictionary, list, and tuple subclasses render as `[non-json value]`" in (
        operator_guide
    )
    assert "ServiceNow diagnostic secret redaction is traversal-bounded for exact" in (
        operator_guide
    )


def test_sprint_590_documents_servicenow_http_error_diagnostic_scalar_normalization() -> (
    None
):
    change_log = Path("docs/sprints/sprint-590-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow HTTP error diagnostic scalar normalization" in change_log
    assert "`_bound_http_error_diagnostics()`" in change_log
    assert "`[non-json value]`" in change_log
    assert "1 failing-first ServiceNow HTTP error diagnostic scalar normalization test" in (
        change_log
    )
    assert "unsupported object `repr()` and `nan` were reflected before implementation" in (
        change_log
    )
    assert "Parsed HTTP error diagnostic scalar values are JSON-safe" in operator_guide
    assert "non-finite floats and unsupported Python objects render as `[non-json value]`" in (
        operator_guide
    )
    assert "without calling `str()` or `repr()` on the original value" in change_log


def test_sprint_591_documents_servicenow_secret_redaction_key_projection() -> None:
    change_log = Path("docs/sprints/sprint-591-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow secret redaction key projection" in change_log
    assert "`redact_secrets()`" in change_log
    assert "`[non-json key]`" in change_log
    assert "1 failing-first ServiceNow secret redaction key projection test" in (
        change_log
    )
    assert "hostile dictionary key `repr()` was reflected before implementation" in (
        change_log
    )
    assert "ServiceNow diagnostic secret redaction also projects object keys" in (
        operator_guide
    )
    assert "duplicate rendered keys" in operator_guide
    assert "non-string keys render as `[non-json key]`" in operator_guide
    assert "without calling" in operator_guide


def test_sprint_592_documents_servicenow_secret_redaction_scalar_normalization() -> (
    None
):
    change_log = Path("docs/sprints/sprint-592-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow secret redaction scalar normalization" in change_log
    assert "`redact_secrets()`" in change_log
    assert "`[non-json value]`" in change_log
    assert "1 failing-first ServiceNow secret redaction scalar normalization test" in (
        change_log
    )
    assert "unsupported object `repr()` and `nan` were reflected before implementation" in (
        change_log
    )
    assert "ServiceNow diagnostic secret redaction scalar values are JSON-safe" in (
        operator_guide
    )
    assert "Non-finite floats and unsupported Python objects render" in operator_guide
    assert "without calling `str()` or `repr()` on the original value" in operator_guide


def test_sprint_593_documents_servicenow_api_diagnostic_cycle_safety() -> None:
    change_log = Path("docs/sprints/sprint-593-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow API diagnostic cycle safety" in change_log
    assert "`_servicenow_diagnostic_value()`" in change_log
    assert "`[circular reference]`" in change_log
    assert "1 failing-first ServiceNow API diagnostic cycle-safety test" in change_log
    assert "raised `RecursionError` before implementation" in change_log
    assert "ServiceNow API exception diagnostic traversal is cycle-safe" in operator_guide
    assert "repeated active container renders as `[circular reference]`" in operator_guide
    assert "instead of raising a secondary recursion failure" in operator_guide


def test_sprint_594_documents_servicenow_http_error_diagnostic_cycle_safety() -> None:
    change_log = Path("docs/sprints/sprint-594-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow HTTP error diagnostic cycle safety" in change_log
    assert "`_bound_http_error_diagnostics()`" in change_log
    assert "`[circular reference]`" in change_log
    assert (
        "1 failing-first ServiceNow HTTP error diagnostic cycle-safety test"
        in change_log
    )
    assert "raised `RecursionError` before implementation" in change_log
    assert "Parsed HTTP error diagnostic traversal is also cycle-safe" in operator_guide
    assert "repeated active containers render as `[circular reference]`" in (
        operator_guide
    )
    assert "instead of raising secondary recursion failures" in operator_guide


def test_sprint_595_documents_servicenow_http_diagnostic_exact_truncation_cap() -> (
    None
):
    change_log = Path("docs/sprints/sprint-595-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow HTTP diagnostic exact truncation cap" in change_log
    assert "`_truncate_http_error_diagnostic()`" in change_log
    assert "`...[truncated]`" in change_log
    assert "1 failing-first ServiceNow HTTP diagnostic exact-cap test" in change_log
    assert "returned 4110 characters for a 4096-character cap" in change_log
    assert "The ServiceNow HTTP diagnostic cap includes the `...[truncated]` marker" in (
        operator_guide
    )
    assert "cannot push transport or API diagnostics beyond the configured maximum" in (
        operator_guide
    )


def test_sprint_596_documents_servicenow_api_diagnostic_per_string_cap() -> None:
    change_log = Path("docs/sprints/sprint-596-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow API diagnostic per-string cap" in change_log
    assert "`_servicenow_diagnostic_value()`" in change_log
    assert "`...[truncated]`" in change_log
    assert "1 failing-first ServiceNow API diagnostic per-string cap test" in change_log
    assert "preserved an oversized message without `...[truncated]`" in change_log
    assert "Exact string diagnostic values are capped after redaction" in operator_guide
    assert "before they enter the structured diagnostic object" in operator_guide
    assert "exact string keys are redacted, normalized, and bounded" in operator_guide


def test_sprint_602_documents_servicenow_http_error_diagnostic_text_normalization() -> None:
    change_log = Path("docs/sprints/sprint-602-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow HTTP error diagnostic text normalization" in change_log
    assert "`_bound_http_error_diagnostics()`" in change_log
    assert "2 failing-first ServiceNow HTTP error diagnostic text-normalization tests" in (
        change_log
    )
    assert "preserved newline and tab characters in exact string values and keys" in (
        change_log
    )
    assert "before normalization and truncation" in operator_guide
    assert "collapse whitespace/control-character runs before the shared cap" in (
        operator_guide
    )
    assert "lower-level transport diagnostics cannot retain raw multiline text" in (
        operator_guide
    )
    assert "exact string keys are whitespace/control-character-normalized" in (
        operator_guide
    )


def test_sprint_597_documents_servicenow_diagnostic_duplicate_key_exact_cap() -> None:
    change_log = Path("docs/sprints/sprint-597-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow diagnostic duplicate key exact cap" in change_log
    assert "`_unique_servicenow_diagnostic_key()`" in change_log
    assert "`MAX_HTTP_ERROR_DIAGNOSTIC_CHARS`" in change_log
    assert "2 failing-first duplicate-key cap tests" in change_log
    assert "duplicate keys exceeded `MAX_HTTP_ERROR_DIAGNOSTIC_CHARS`" in change_log
    assert "duplicate rendered keys receive deterministic suffixes inside the same" in (
        operator_guide
    )
    assert "diagnostic key cap" in operator_guide


def test_sprint_598_documents_servicenow_secret_redaction_cycle_safety() -> None:
    change_log = Path("docs/sprints/sprint-598-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow secret redaction cycle safety" in change_log
    assert "`redact_secrets()`" in change_log
    assert "`[circular reference]`" in change_log
    assert "1 failing-first ServiceNow secret redaction cycle-safety test" in (
        change_log
    )
    assert "raised `RecursionError` before implementation" in change_log
    assert "Secret-redaction traversal is also" in operator_guide
    assert "repeated active containers render as `[circular reference]`" in (
        operator_guide
    )
    assert "instead of raising a secondary recursion failure" in operator_guide


def test_sprint_599_documents_servicenow_secret_redaction_text_value_cap() -> None:
    change_log = Path("docs/sprints/sprint-599-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow secret redaction text value cap" in change_log
    assert "`redact_secrets()`" in change_log
    assert "`MAX_HTTP_ERROR_DIAGNOSTIC_CHARS`" in change_log
    assert "1 failing-first ServiceNow secret redaction text-value cap test" in (
        change_log
    )
    assert "preserved an oversized string without `...[truncated]`" in change_log
    assert "Exact string values are" in operator_guide
    assert "capped after diagnostic redaction" in operator_guide
    assert "cannot retain an" in operator_guide
    assert "oversized text value" in operator_guide


def test_sprint_600_documents_servicenow_diagnostic_truncation_marker_collision_safety() -> (
    None
):
    change_log = Path("docs/sprints/sprint-600-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow diagnostic truncation marker collision safety" in change_log
    assert "`_add_servicenow_truncation_marker()`" in change_log
    assert "`__jedi_response_truncated__ (2)`" in change_log
    assert "3 failing-first ServiceNow truncation marker collision tests" in (
        change_log
    )
    assert "overwrote `user marker`" in change_log
    assert "Internal dictionary truncation markers are inserted through" in (
        operator_guide
    )
    assert "Internal dictionary truncation markers use collision-safe key rendering" in (
        operator_guide
    )
    assert "Secret-redaction dictionary truncation markers are also collision-safe" in (
        operator_guide
    )


def test_sprint_601_documents_servicenow_secret_redaction_text_normalization() -> None:
    change_log = Path("docs/sprints/sprint-601-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow secret redaction text normalization" in change_log
    assert "`redact_secrets()`" in change_log
    assert "1 failing-first ServiceNow secret redaction text-normalization test" in (
        change_log
    )
    assert "preserved newline and tab characters" in change_log
    assert "whitespace/control-character-normalized and capped after" in (
        operator_guide
    )
    assert "cannot retain an" in operator_guide
    assert "oversized text value or raw line-breaking control text" in operator_guide


def test_sprint_548_documents_servicenow_story_response_text_type_guard() -> None:
    change_log = Path("docs/sprints/sprint-548-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow story response text type guard" in change_log
    assert "`_story_from_record()`" in change_log
    assert "`ServiceNow API story response field is unsafe`" in change_log
    assert "1 failing-first ServiceNow story response text test" in change_log
    assert "accepted the hostile object by calling `str()`" in change_log
    assert "ServiceNow story response text is type-safe before model construction" in (
        operator_guide
    )
    assert "accepts only string values for required story text fields" in operator_guide
    assert "before a `Story` is constructed" in operator_guide
    assert "does not echo object type names" in operator_guide


def test_sprint_562_documents_servicenow_story_additional_context_length_guard() -> None:
    change_log = Path("docs/sprints/sprint-562-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow story additional-context length guard" in change_log
    assert "`_story_from_record()`" in change_log
    assert "`Story.additional_context`" in change_log
    assert "`ServiceNow API story response field is unsafe`" in change_log
    assert "1 failing-first ServiceNow story additional-context length test" in change_log
    assert "did not raise `ServiceNowApiError`" in change_log
    assert "story response text is type-safe before model construction" in operator_guide
    assert "bounded to 1024 characters" in operator_guide
    assert "oversized additional-context values use the same fixed diagnostic" in operator_guide
    assert "without echoing submitted context values" in operator_guide


def test_sprint_549_documents_servicenow_metadata_response_text_type_guard() -> None:
    change_log = Path("docs/sprints/sprint-549-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow metadata response text type guard" in change_log
    assert "`_state_choice_from_record()`" in change_log
    assert "`_dictionary_field_from_record()`" in change_log
    assert "`ServiceNow API metadata response field is unsafe`" in change_log
    assert "2 failing-first ServiceNow metadata response text tests" in change_log
    assert "accepted hostile objects by calling `str()`" in change_log
    assert "ServiceNow metadata response text is type-safe before model construction" in (
        operator_guide
    )
    assert "accept only string values for state-choice labels/values" in operator_guide
    assert "before `StoryStateChoice` or `StoryDictionaryField` models are constructed" in (
        operator_guide
    )
    assert "does not echo object type names" in operator_guide


def test_sprint_563_documents_servicenow_metadata_response_text_length_guard() -> None:
    change_log = Path("docs/sprints/sprint-563-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow metadata response text length guard" in change_log
    assert "`_servicenow_metadata_response_text()`" in change_log
    assert "`StoryStateChoice`" in change_log
    assert "`StoryDictionaryField`" in change_log
    assert "`ServiceNow API metadata response field is unsafe`" in change_log
    assert "1 failing-first ServiceNow metadata response text length test" in change_log
    assert "did not raise `ServiceNowApiError`" in change_log
    assert "ServiceNow metadata response text is type-safe before model construction" in (
        operator_guide
    )
    assert "no longer than 1024 characters" in operator_guide
    assert "Non-string or oversized metadata response text fails" in operator_guide
    assert "does not echo object type names" in operator_guide


def test_sprint_565_documents_servicenow_metadata_response_text_control_guard() -> None:
    change_log = Path("docs/sprints/sprint-565-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow metadata response text control-character guard" in change_log
    assert "`_servicenow_metadata_response_text()`" in change_log
    assert "`StoryStateChoice`" in change_log
    assert "`StoryDictionaryField`" in change_log
    assert "`ServiceNow API metadata response field is unsafe`" in change_log
    assert "1 failing-first ServiceNow metadata response text control-character test" in (
        change_log
    )
    assert "did not raise `ServiceNowApiError`" in change_log
    assert "ServiceNow metadata response text is type-safe before model construction" in (
        operator_guide
    )
    assert "must not contain ASCII control characters" in operator_guide
    assert "control-character metadata response text fails" in operator_guide
    assert "does not echo object type names" in operator_guide


def test_sprint_568_documents_servicenow_metadata_text_str_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-568-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow metadata text string-subclass guard" in change_log
    assert "`_servicenow_metadata_response_text()`" in change_log
    assert "`StoryStateChoice`" in change_log
    assert "`StoryDictionaryField`" in change_log
    assert "`ServiceNow API metadata response field is unsafe`" in change_log
    assert "1 failing-first ServiceNow metadata response text string-subclass test" in (
        change_log
    )
    assert "did not raise `ServiceNowApiError`" in change_log
    assert "ServiceNow metadata response text is type-safe before model construction" in (
        operator_guide
    )
    assert "must be exact `str` instances" in operator_guide
    assert "string subclasses" in operator_guide
    assert "does not echo object type names" in operator_guide


def test_sprint_550_documents_servicenow_metadata_response_boolean_type_guard() -> None:
    change_log = Path("docs/sprints/sprint-550-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow metadata response boolean type guard" in change_log
    assert "`_truthy()`" in change_log
    assert "`ServiceNow API metadata response field is unsafe`" in change_log
    assert "2 failing-first ServiceNow metadata response boolean tests" in change_log
    assert "accepted hostile objects by calling `str()`" in change_log
    assert "ServiceNow metadata response booleans are strict before model construction" in (
        operator_guide
    )
    assert "accept only actual booleans and explicit string boolean values" in (
        operator_guide
    )
    assert "Non-string objects and malformed boolean strings fail" in operator_guide
    assert "does not echo object type names" in operator_guide


def test_sprint_564_documents_servicenow_metadata_response_boolean_padding_guard() -> None:
    change_log = Path("docs/sprints/sprint-564-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow metadata response boolean padding guard" in change_log
    assert "`_servicenow_metadata_response_bool()`" in change_log
    assert "`StoryStateChoice`" in change_log
    assert "`StoryDictionaryField`" in change_log
    assert "`ServiceNow API metadata response field is unsafe`" in change_log
    assert "1 failing-first ServiceNow metadata response boolean padding test" in (
        change_log
    )
    assert "did not raise `ServiceNowApiError`" in change_log
    assert "ServiceNow metadata response booleans are strict before model construction" in (
        operator_guide
    )
    assert "string boolean values must be unpadded" in operator_guide
    assert "padded boolean strings fail" in operator_guide
    assert "does not echo object type names" in operator_guide


def test_sprint_567_documents_servicenow_metadata_boolean_str_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-567-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow metadata boolean string-subclass guard" in change_log
    assert "`_servicenow_metadata_response_bool()`" in change_log
    assert "`StoryStateChoice`" in change_log
    assert "`StoryDictionaryField`" in change_log
    assert "`ServiceNow API metadata response field is unsafe`" in change_log
    assert "1 failing-first ServiceNow metadata response boolean string-subclass test" in (
        change_log
    )
    assert "raised `RuntimeError` from `.lower()`" in change_log
    assert "ServiceNow metadata response booleans are strict before model construction" in (
        operator_guide
    )
    assert "must be exact `str` instances" in operator_guide
    assert "string subclasses" in operator_guide
    assert "does not echo object type names" in operator_guide


def test_sprint_551_documents_servicenow_metadata_response_sequence_type_guard() -> None:
    change_log = Path("docs/sprints/sprint-551-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow metadata response sequence type guard" in change_log
    assert "`sys_choice.sequence`" in change_log
    assert "`ServiceNow API metadata response field is unsafe`" in change_log
    assert "1 failing-first ServiceNow metadata response sequence test" in change_log
    assert "called `int()` on the hostile object" in change_log
    assert (
        "ServiceNow metadata response sequence values are strict before state-choice sorting"
        in operator_guide
    )
    assert "accepts only actual non-boolean integers and simple ASCII decimal strings" in (
        operator_guide
    )
    assert "Missing or blank sequence values map to `0`" in operator_guide
    assert "does not echo object type names" in operator_guide


def test_sprint_566_documents_servicenow_metadata_response_sequence_range_guard() -> None:
    change_log = Path("docs/sprints/sprint-566-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow metadata response sequence range guard" in change_log
    assert "`_servicenow_metadata_response_int()`" in change_log
    assert "`sys_choice.sequence`" in change_log
    assert "`StoryStateChoice`" in change_log
    assert "`ServiceNow API metadata response field is unsafe`" in change_log
    assert "1 failing-first ServiceNow metadata response sequence range test" in (
        change_log
    )
    assert "did not raise `ServiceNowApiError`" in change_log
    assert (
        "ServiceNow metadata response sequence values are strict before state-choice sorting"
        in operator_guide
    )
    assert "must fit `0..2147483647`" in operator_guide
    assert "oversized decimal strings" in operator_guide
    assert "does not echo object type names" in operator_guide


def test_sprint_569_documents_servicenow_metadata_sequence_str_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-569-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow metadata sequence string-subclass guard" in change_log
    assert "`_servicenow_metadata_response_int()`" in change_log
    assert "`sys_choice.sequence`" in change_log
    assert "`StoryStateChoice`" in change_log
    assert "`ServiceNow API metadata response field is unsafe`" in change_log
    assert "1 failing-first ServiceNow metadata response sequence string-subclass test" in (
        change_log
    )
    assert "raised `RuntimeError` from `.isascii()`" in change_log
    assert (
        "ServiceNow metadata response sequence values are strict before state-choice sorting"
        in operator_guide
    )
    assert "Sequence string values must be exact `str` instances" in operator_guide
    assert "string subclasses" in operator_guide
    assert "does not echo object type names" in operator_guide


def test_sprint_570_documents_servicenow_metadata_sequence_int_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-570-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow metadata sequence integer-subclass guard" in change_log
    assert "`_servicenow_metadata_response_int()`" in change_log
    assert "`sys_choice.sequence`" in change_log
    assert "`StoryStateChoice`" in change_log
    assert "`ServiceNow API metadata response field is unsafe`" in change_log
    assert "1 failing-first ServiceNow metadata response sequence integer-subclass test" in (
        change_log
    )
    assert "raised `RuntimeError` during range comparison" in change_log
    assert (
        "ServiceNow metadata response sequence values are strict before state-choice sorting"
        in operator_guide
    )
    assert "Numeric sequence values must be exact `int` instances" in operator_guide
    assert "integer subclasses" in operator_guide
    assert "does not echo object type names" in operator_guide


def test_sprint_571_documents_servicenow_story_priority_int_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-571-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow story response priority integer-subclass guard" in change_log
    assert "`_servicenow_story_response_int()`" in change_log
    assert "`priority`" in change_log
    assert "`Story`" in change_log
    assert "`ServiceNow API story response field is unsafe`" in change_log
    assert "1 failing-first ServiceNow story response priority integer-subclass test" in (
        change_log
    )
    assert "accepted the hostile integer subclass" in change_log
    assert (
        "ServiceNow story response priority values are strict before model construction"
        in operator_guide
    )
    assert "Priority numeric values must be exact `int` instances" in operator_guide
    assert "integer subclasses" in operator_guide
    assert "does not echo object type names" in operator_guide


def test_sprint_572_documents_servicenow_story_points_float_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-572-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow story response story-points numeric-subclass guard" in change_log
    assert "`_servicenow_story_response_float()`" in change_log
    assert "`story_points`" in change_log
    assert "`Story`" in change_log
    assert "`ServiceNow API story response field is unsafe`" in change_log
    assert "1 failing-first ServiceNow story response story-points float-subclass test" in (
        change_log
    )
    assert "raised `RuntimeError` during comparison" in change_log
    assert (
        "ServiceNow story response story-point values are strict before model construction"
        in operator_guide
    )
    assert "Story-point numeric values must be exact `int` or exact `float` instances" in (
        operator_guide
    )
    assert "numeric subclasses" in operator_guide
    assert "does not echo object type names" in operator_guide


def test_sprint_573_documents_servicenow_table_name_str_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-573-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow table-name string-subclass guard" in change_log
    assert "`_servicenow_table_name()`" in change_log
    assert "`ServiceNowClient.fetch_table_record()`" in change_log
    assert "`ServiceNow API table name is unsafe`" in change_log
    assert "1 failing-first ServiceNow table-name string-subclass test" in change_log
    assert "raised `RuntimeError` from overridden `strip()`" in change_log
    assert (
        "ServiceNow table-name validation is type-safe before string handling"
        in operator_guide
    )
    assert "Table-name values must be exact `str` instances" in operator_guide
    assert "string subclasses" in operator_guide
    assert "does not echo object type names" in operator_guide


def test_sprint_574_documents_servicenow_record_id_str_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-574-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow record-id string-subclass guard" in change_log
    assert "`_servicenow_record_id()`" in change_log
    assert "`ServiceNowClient.update_story_fields()`" in change_log
    assert "`ServiceNow API record id is unsafe`" in change_log
    assert "1 failing-first ServiceNow record-id string-subclass test" in change_log
    assert "raised `RuntimeError` from overridden `strip()`" in change_log
    assert (
        "ServiceNow record-id validation is type-safe before string handling"
        in operator_guide
    )
    assert "Record-id values must be exact `str` instances" in operator_guide
    assert "string subclasses" in operator_guide
    assert "does not echo object type names" in operator_guide


def test_sprint_575_documents_servicenow_field_name_str_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-575-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow field-name string-subclass guard" in change_log
    assert "`_servicenow_field_name()`" in change_log
    assert "`ServiceNowClient.update_story_fields()`" in change_log
    assert "`ServiceNow API field name is unsafe`" in change_log
    assert "1 failing-first ServiceNow field-name string-subclass test" in change_log
    assert "raised `RuntimeError` from overridden `strip()`" in change_log
    assert (
        "ServiceNow field-name validation is type-safe before string handling"
        in operator_guide
    )
    assert "Field-name values must be exact `str` instances" in operator_guide
    assert "string subclasses" in operator_guide
    assert "does not echo object type names" in operator_guide


def test_sprint_576_documents_servicenow_operation_uri_str_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-576-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow operation URI string-subclass guard" in change_log
    assert "`_servicenow_operation_uri()`" in change_log
    assert "`ServiceNowClient.import_update_set_xml()`" in change_log
    assert "`ServiceNow API operation URI is unsafe`" in change_log
    assert "1 failing-first ServiceNow operation URI string-subclass test" in change_log
    assert "raised `RuntimeError` from overridden `strip()`" in change_log
    assert (
        "Discovered ServiceNow Scripted REST operation URI validation is type-safe"
        in operator_guide
    )
    assert "Operation URI values must be exact `str` instances" in operator_guide
    assert "string subclasses" in operator_guide
    assert "does not echo object type names" in operator_guide


def test_sprint_577_documents_servicenow_dictionary_internal_type_str_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-577-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow dictionary internal-type string-subclass guard" in change_log
    assert "`_servicenow_dictionary_internal_type()`" in change_log
    assert "`ServiceNowClient.create_story_dictionary_field()`" in change_log
    assert "`ServiceNow dictionary internal type is unsafe`" in change_log
    assert (
        "1 failing-first ServiceNow dictionary internal-type string-subclass test"
        in change_log
    )
    assert "raised `RuntimeError` from overridden `strip()`" in change_log
    assert (
        "ServiceNow dictionary internal-type validation is type-safe before string handling"
        in operator_guide
    )
    assert "Internal-type values must be exact `str` instances" in operator_guide
    assert "string subclasses" in operator_guide
    assert "does not echo object type names" in operator_guide


def test_sprint_578_documents_servicenow_dictionary_column_label_str_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-578-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow dictionary column-label string-subclass guard" in change_log
    assert "`_servicenow_dictionary_column_label()`" in change_log
    assert "`ServiceNowClient.create_story_dictionary_field()`" in change_log
    assert "`ServiceNow dictionary column label is unsafe`" in change_log
    assert (
        "1 failing-first ServiceNow dictionary column-label string-subclass test"
        in change_log
    )
    assert "raised `RuntimeError` from overridden `strip()`" in change_log
    assert (
        "ServiceNow dictionary column-label validation is type-safe before string handling"
        in operator_guide
    )
    assert "Column-label values must be exact `str` instances" in operator_guide
    assert "string subclasses" in operator_guide
    assert "does not echo object type names" in operator_guide


def test_sprint_552_documents_servicenow_story_response_priority_type_guard() -> None:
    change_log = Path("docs/sprints/sprint-552-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow story response priority type guard" in change_log
    assert "`_story_from_record()`" in change_log
    assert "`ServiceNow API story response field is unsafe`" in change_log
    assert "1 failing-first ServiceNow story response priority test" in change_log
    assert "called `int()` on the hostile object" in change_log
    assert (
        "ServiceNow story response priority values are strict before model construction"
        in operator_guide
    )
    assert "accepts only actual non-boolean integers and simple ASCII decimal strings" in (
        operator_guide
    )
    assert "Missing, null, or blank priority values still map to the operational default `5`" in (
        operator_guide
    )
    assert "does not echo object type names" in operator_guide


def test_sprint_553_documents_servicenow_story_response_story_points_type_guard() -> None:
    change_log = Path("docs/sprints/sprint-553-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow story response story-points type guard" in change_log
    assert "`_story_from_record()`" in change_log
    assert "`ServiceNow API story response field is unsafe`" in change_log
    assert "1 failing-first ServiceNow story response story-points test" in change_log
    assert "called `float()` on the hostile object" in change_log
    assert (
        "ServiceNow story response story-point values are strict before model construction"
        in operator_guide
    )
    assert (
        "accepts only actual non-boolean finite non-negative integers or floats"
        in operator_guide
    )
    assert (
        "Missing, null, or blank story-point values still map to the operational default `0.0`"
        in operator_guide
    )
    assert "does not echo object type names" in operator_guide


def test_sprint_554_documents_servicenow_oauth_access_token_size_and_ascii_guard() -> None:
    change_log = Path("docs/sprints/sprint-554-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow OAuth access-token size and ASCII guard" in change_log
    assert "`OAuthClientCredentials._fetch_token()`" in change_log
    assert "`ServiceNow OAuth response did not include access_token`" in change_log
    assert "1 failing-first ServiceNow OAuth oversized access-token test" in change_log
    assert "the oversized token was accepted" in change_log
    assert "ServiceNow OAuth token responses are also treated as untrusted input" in (
        operator_guide
    )
    assert "rejects missing, empty, non-ASCII, oversized, padded" in operator_guide
    assert "capped at 8192 ASCII bytes" in operator_guide
    assert "does not echo token values" in operator_guide


def test_sprint_555_documents_servicenow_record_id_length_guard() -> None:
    change_log = Path("docs/sprints/sprint-555-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow record-id length guard" in change_log
    assert "`_servicenow_record_id()`" in change_log
    assert "`ServiceNow API record id is unsafe`" in change_log
    assert "1 failing-first ServiceNow record-id length test" in change_log
    assert "reached OAuth token acquisition" in change_log
    assert "record ids used in URL paths are path-safe" in operator_guide
    assert "no longer than 128 characters" in operator_guide
    assert "record-id validation is type-safe before string handling and bounded" in (
        operator_guide
    )
    assert "does not echo record id values" in operator_guide


def test_sprint_530_documents_ready_story_project_id_query_guard() -> None:
    change_log = Path("docs/sprints/sprint-530-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow ready-story project-id query injection guard" in change_log
    assert "`ServiceNowClient.fetch_ready_stories(project_sys_id=...)`" in change_log
    assert "`state=Ready^project=<id>`" in change_log
    assert "`ServiceNow API record id is unsafe`" in change_log
    assert "1 failing-first ServiceNow ready-story project-id test" in change_log
    assert "OAuth token acquisition was attempted before project id validation" in change_log
    assert "Ready-story project filters are delimiter-safe before encoded-query construction" in (
        operator_guide
    )
    assert "`ServiceNowClient.fetch_ready_stories(project_sys_id=...)`" in operator_guide
    assert "before OAuth token acquisition, GET construction, or Table API transport" in (
        operator_guide
    )
    assert "does not echo project id values" in operator_guide


def test_sprint_531_documents_servicenow_sysparm_fields_projection_guard() -> None:
    change_log = Path("docs/sprints/sprint-531-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow sysparm_fields projection guard" in change_log
    assert "`ServiceNowClient.fetch_table_records(fields=...)`" in change_log
    assert "`sysparm_fields`" in change_log
    assert "`ServiceNow API field name is unsafe`" in change_log
    assert "1 failing-first ServiceNow `sysparm_fields` projection test" in change_log
    assert "OAuth token acquisition was attempted before field-name validation" in change_log
    assert "ServiceNow Table API field projection construction is delimiter-safe" in (
        operator_guide
    )
    assert "`ServiceNowClient.fetch_table_records(fields=...)`" in operator_guide
    assert "dotted reference paths made of identifier parts" in operator_guide
    assert "does not echo field values" in operator_guide


def test_sprint_532_documents_servicenow_sysparm_limit_range_guard() -> None:
    change_log = Path("docs/sprints/sprint-532-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow sysparm_limit range guard" in change_log
    assert "`ServiceNowClient.fetch_stories()`" in change_log
    assert "`ServiceNowClient.fetch_table_records()`" in change_log
    assert "`sysparm_limit`" in change_log
    assert "`ServiceNow API result limit is unsafe`" in change_log
    assert "2 failing-first ServiceNow result-limit tests" in change_log
    assert "fixed result-limit diagnostic did not exist" in change_log
    assert "ServiceNow Table API result limits are bounded before request construction" in (
        operator_guide
    )
    assert "from 1 through 500" in operator_guide
    assert "does not echo query values" in operator_guide


def test_sprint_533_documents_servicenow_cicd_retrieve_id_validation() -> None:
    change_log = Path("docs/sprints/sprint-533-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow CI/CD retrieve id validation" in change_log
    assert "`ServiceNowClient.retrieve_cicd_update_set()`" in change_log
    assert "`update_set_id`" in change_log
    assert "`update_source_id`" in change_log
    assert "`update_source_instance_id`" in change_log
    assert "`ServiceNow API record id is unsafe`" in change_log
    assert "1 failing-first ServiceNow CI/CD retrieve id test" in change_log
    assert "OAuth token acquisition was attempted before retrieve id validation" in change_log
    assert "ServiceNow CI/CD Update Set path ids use the same record-id safety rule" in (
        operator_guide
    )
    assert "`ServiceNowClient.retrieve_cicd_update_set()` validates" in operator_guide
    assert "query fragments" in operator_guide


def test_sprint_534_documents_servicenow_boolean_flag_serialization_guard() -> None:
    change_log = Path("docs/sprints/sprint-534-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow boolean flag serialization guard" in change_log
    assert "`_bool_query_value()`" in change_log
    assert "`ServiceNow API boolean value is unsafe`" in change_log
    assert "1 failing-first ServiceNow boolean flag test" in change_log
    assert "string flag was treated as truthy" in change_log
    assert "dictionary `read_only`" in change_log
    assert "CI/CD retrieve `auto_preview` and `cleanup_retrieved`" in change_log
    assert "CI/CD commit `force_commit`" in change_log
    assert "ServiceNow boolean query/body flags are strict before serialization" in (
        operator_guide
    )
    assert "accepts only actual Python `bool` values" in operator_guide
    assert "does not echo flag values" in operator_guide


def test_sprint_535_documents_servicenow_dictionary_element_write_guard() -> None:
    change_log = Path("docs/sprints/sprint-535-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow dictionary element write guard" in change_log
    assert "`ServiceNowClient.create_story_dictionary_field()`" in change_log
    assert "`sys_dictionary` JSON body" in change_log
    assert "`ServiceNow API field name is unsafe`" in change_log
    assert "1 failing-first ServiceNow dictionary element test" in change_log
    assert "OAuth token acquisition was attempted before dictionary element validation" in (
        change_log
    )
    assert "ServiceNow dictionary field creation validates element names before writing" in (
        operator_guide
    )
    assert "`element` body field" in operator_guide
    assert "does not echo element values" in operator_guide


def test_sprint_536_documents_servicenow_dictionary_internal_type_write_guard() -> None:
    change_log = Path("docs/sprints/sprint-536-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow dictionary internal type write guard" in change_log
    assert "`ServiceNowClient.create_story_dictionary_field()`" in change_log
    assert "`internal_type` directly into the `sys_dictionary` JSON body" in change_log
    assert "`ServiceNow dictionary internal type is unsafe`" in change_log
    assert "1 failing-first ServiceNow dictionary internal type test" in change_log
    assert "OAuth token acquisition was attempted before dictionary internal type validation" in (
        change_log
    )
    assert "ServiceNow dictionary field creation validates internal types" in (
        operator_guide
    )
    assert "`internal_type` body field" in operator_guide
    assert "does not echo internal type values" in operator_guide


def test_sprint_537_documents_servicenow_dictionary_max_length_write_guard() -> None:
    change_log = Path("docs/sprints/sprint-537-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow dictionary max length write guard" in change_log
    assert "`ServiceNowClient.create_story_dictionary_field()`" in change_log
    assert "`str(max_length)`" in change_log
    assert "`ServiceNow dictionary max length is unsafe`" in change_log
    assert "1 failing-first ServiceNow dictionary max-length test" in change_log
    assert "OAuth token acquisition was attempted before dictionary max-length validation" in (
        change_log
    )
    assert "ServiceNow dictionary field creation validates max lengths" in operator_guide
    assert "from 1 through 65535" in operator_guide
    assert "`max_length` body field" in operator_guide
    assert "does not echo max-length values" in operator_guide


def test_sprint_538_documents_servicenow_dictionary_column_label_write_guard() -> None:
    change_log = Path("docs/sprints/sprint-538-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow dictionary column label write guard" in change_log
    assert "`ServiceNowClient.create_story_dictionary_field()`" in change_log
    assert "`column_label` directly into the `sys_dictionary` JSON body" in change_log
    assert "`ServiceNow dictionary column label is unsafe`" in change_log
    assert "1 failing-first ServiceNow dictionary column-label test" in change_log
    assert "OAuth token acquisition was attempted before dictionary column-label validation" in (
        change_log
    )
    assert "ServiceNow dictionary field creation validates column labels" in operator_guide
    assert "normal human labels with spaces" in operator_guide
    assert "`column_label` body field" in operator_guide
    assert "does not echo column-label values" in operator_guide


def test_sprint_539_documents_servicenow_story_patch_field_name_guard() -> None:
    change_log = Path("docs/sprints/sprint-539-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow story PATCH field-name guard" in change_log
    assert "`ServiceNowClient.update_story_fields()`" in change_log
    assert "`rm_story` JSON body" in change_log
    assert "`ServiceNow API field name is unsafe`" in change_log
    assert "1 failing-first ServiceNow story PATCH field-name test" in change_log
    assert "OAuth token acquisition was attempted before PATCH body field-name validation" in (
        change_log
    )
    assert "ServiceNow story PATCH body field names are delimiter-safe" in operator_guide
    assert "validates every PATCH body field name" in operator_guide
    assert "does not echo field names" in operator_guide


def test_sprint_540_documents_servicenow_generic_upsert_field_name_guard() -> None:
    change_log = Path("docs/sprints/sprint-540-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow generic upsert field-name guard" in change_log
    assert "`ServiceNowClient.upsert_table_record()`" in change_log
    assert "POST and PATCH bodies" in change_log
    assert "`ServiceNow API field name is unsafe`" in change_log
    assert "1 failing-first ServiceNow generic upsert field-name test" in change_log
    assert "OAuth token acquisition was attempted before upsert body field-name validation" in (
        change_log
    )
    assert "Generic ServiceNow Table API upsert body field names are delimiter-safe" in (
        operator_guide
    )
    assert "validates every create/update body field name" in operator_guide
    assert "does not echo field names" in operator_guide


def test_sprint_541_documents_servicenow_field_name_type_guard() -> None:
    change_log = Path("docs/sprints/sprint-541-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow field-name type guard" in change_log
    assert "`_servicenow_field_name()`" in change_log
    assert "`AttributeError` with the hostile object representation" in change_log
    assert "`ServiceNow API field name is unsafe`" in change_log
    assert "1 failing-first ServiceNow non-string field-name test" in change_log
    assert "without calling `str()` or `repr()` for diagnostics" in change_log
    assert "ServiceNow field-name validation is type-safe before string handling" in (
        operator_guide
    )
    assert "rejects non-string values before calling string methods" in operator_guide
    assert "cannot leak object type names" in operator_guide


def test_sprint_542_documents_servicenow_record_id_type_guard() -> None:
    change_log = Path("docs/sprints/sprint-542-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow record-id type guard" in change_log
    assert "`_servicenow_record_id()`" in change_log
    assert "`AttributeError` with the hostile object representation" in change_log
    assert "`ServiceNow API record id is unsafe`" in change_log
    assert "1 failing-first ServiceNow non-string record-id test" in change_log
    assert "without calling `str()` or `repr()` for diagnostics" in change_log
    assert "ServiceNow record-id validation is type-safe before string handling" in (
        operator_guide
    )
    assert "shared record-id guard rejects non-string values" in operator_guide
    assert "cannot leak object type names" in operator_guide


def test_sprint_543_documents_servicenow_table_name_type_guard() -> None:
    change_log = Path("docs/sprints/sprint-543-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow table-name type guard" in change_log
    assert "`_servicenow_table_name()`" in change_log
    assert "`AttributeError` with the hostile object representation" in change_log
    assert "`ServiceNow API table name is unsafe`" in change_log
    assert "1 failing-first ServiceNow non-string table-name test" in change_log
    assert "without calling `str()` or `repr()` for diagnostics" in change_log
    assert "ServiceNow table-name validation is type-safe before string handling" in (
        operator_guide
    )
    assert "shared table-name guard rejects non-string values" in operator_guide
    assert "cannot leak object type names" in operator_guide


def test_sprint_556_documents_servicenow_table_name_length_guard() -> None:
    change_log = Path("docs/sprints/sprint-556-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow table-name length guard" in change_log
    assert "`_servicenow_table_name()`" in change_log
    assert "`ServiceNow API table name is unsafe`" in change_log
    assert "1 failing-first ServiceNow table-name length test" in change_log
    assert "reached OAuth token acquisition" in change_log
    assert "Generic ServiceNow Table API table names are path-safe" in operator_guide
    assert "no longer than 128 characters" in operator_guide
    assert "table-name validation is type-safe before string handling and bounded" in (
        operator_guide
    )
    assert "does not echo table values" in operator_guide


def test_sprint_557_documents_servicenow_field_name_length_guard() -> None:
    change_log = Path("docs/sprints/sprint-557-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow field-name length guard" in change_log
    assert "`_servicenow_field_name()`" in change_log
    assert "`ServiceNow API field name is unsafe`" in change_log
    assert "1 failing-first ServiceNow field-name length test" in change_log
    assert "reached OAuth token acquisition" in change_log
    assert "field projection construction is delimiter-safe" in operator_guide
    assert "no longer than 256 characters" in operator_guide
    assert "field-name validation is type-safe before string handling and bounded" in (
        operator_guide
    )
    assert "does not echo field names" in operator_guide


def test_sprint_544_documents_servicenow_lookup_query_type_guard() -> None:
    change_log = Path("docs/sprints/sprint-544-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow lookup query type guard" in change_log
    assert "`_servicenow_lookup_query()`" in change_log
    assert "`_is_unsafe_servicenow_lookup_part()` raised `TypeError`" in change_log
    assert "`ServiceNow API lookup query is unsafe`" in change_log
    assert "2 failing-first ServiceNow lookup type tests" in change_log
    assert "without calling `str()` or `repr()` for diagnostics" in change_log
    assert "ServiceNow lookup query construction is type-safe before delimiter checks" in (
        operator_guide
    )
    assert "rejects non-string lookup keys and values" in operator_guide
    assert "cannot leak object type names" in operator_guide


def test_sprint_559_documents_servicenow_lookup_part_length_guard() -> None:
    change_log = Path("docs/sprints/sprint-559-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow lookup part length guard" in change_log
    assert "`_servicenow_lookup_query()`" in change_log
    assert "`ServiceNow API lookup query is unsafe`" in change_log
    assert "1 failing-first ServiceNow lookup part length test" in change_log
    assert "reached OAuth token acquisition" in change_log
    assert "lookup query construction is delimiter-safe and bounded" in operator_guide
    assert "more than 1024 characters" in operator_guide
    assert "lookup query construction is type-safe before delimiter checks and bounded" in (
        operator_guide
    )
    assert "does not echo lookup values" in operator_guide


def test_sprint_545_documents_servicenow_result_limit_type_guard() -> None:
    change_log = Path("docs/sprints/sprint-545-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow sysparm_limit type guard" in change_log
    assert "`_servicenow_result_limit()`" in change_log
    assert "`TypeError` with a hostile object representation" in change_log
    assert "`ServiceNow API result limit is unsafe`" in change_log
    assert "1 failing-first ServiceNow result-limit type test" in change_log
    assert "without calling `str()` or `repr()` for diagnostics" in change_log
    assert "Non-integer, non-positive, boolean, or oversized limits fail" in operator_guide
    assert "before OAuth token acquisition, GET construction, numeric comparison" in (
        operator_guide
    )
    assert "does not echo object type names" in operator_guide


def test_sprint_546_documents_servicenow_dictionary_internal_type_type_guard() -> None:
    change_log = Path("docs/sprints/sprint-546-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow dictionary internal type type guard" in change_log
    assert "`_servicenow_dictionary_internal_type()`" in change_log
    assert "`AttributeError` with a hostile object representation" in change_log
    assert "`ServiceNow dictionary internal type is unsafe`" in change_log
    assert "1 failing-first ServiceNow dictionary internal type test" in change_log
    assert "without calling `str()` or `repr()` for diagnostics" in change_log
    assert "accepts only string, unpadded ServiceNow identifier-style type names" in (
        operator_guide
    )
    assert "Non-string and unsafe internal types fail" in operator_guide
    assert "before OAuth token acquisition, POST construction, string-method calls" in (
        operator_guide
    )


def test_sprint_561_documents_servicenow_dictionary_internal_type_length_guard() -> None:
    change_log = Path("docs/sprints/sprint-561-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow dictionary internal-type length guard" in change_log
    assert "`_servicenow_dictionary_internal_type()`" in change_log
    assert "`ServiceNowClient.create_story_dictionary_field()`" in change_log
    assert "`ServiceNow dictionary internal type is unsafe`" in change_log
    assert "1 failing-first ServiceNow dictionary internal-type length test" in change_log
    assert "reached OAuth token acquisition" in change_log
    assert "ServiceNow dictionary field creation validates internal types" in operator_guide
    assert "no longer than 128 characters" in operator_guide
    assert "oversized internal types use the same fixed diagnostic" in operator_guide
    assert "does not echo internal type values" in operator_guide


def test_sprint_620_documents_exact_string_work_note_boundary() -> None:
    change_log = Path("docs/sprints/sprint-620-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Exact-string ServiceNow work-note boundary" in change_log
    assert "`safe_work_note_value()` now accepts exact `str` values only" in change_log
    assert "`render_summary()` now formats only explicit safe scalar types" in change_log
    assert "4 failing-first tests" in change_log
    assert "15 tests passed" in change_log
    assert "The shared ServiceNow work-note value sanitizer accepts exact strings only" in (
        operator_guide
    )
    assert "String subclasses and" in operator_guide
    assert "non-string objects are replaced" in operator_guide
    assert "CLI summary rendering uses an explicit safe scalar formatter" in operator_guide


def test_sprint_621_documents_artifact_handoff_summary_exact_scalar_boundary() -> None:
    change_log = Path("docs/sprints/sprint-621-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Artifact handoff summary exact-scalar boundary" in change_log
    assert "`build_artifact_handoff_work_note()` summary rendering" in change_log
    assert "`_handoff_summary_value()`" in change_log
    assert "[unsupported handoff summary value]" in change_log
    assert "1 failing-first artifact handoff test" in change_log
    assert "19 tests passed" in change_log
    assert "Artifact handoff work-note summaries are also stringification-safe" in (
        operator_guide
    )
    assert "formats only exact strings, booleans, integers, finite floats, and null" in (
        operator_guide
    )
    assert "custom `__str__` methods" in operator_guide


def test_sprint_622_documents_artifact_handoff_delivery_job_validation() -> None:
    change_log = Path("docs/sprints/sprint-622-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Artifact handoff delivery job fail-closed validation" in change_log
    assert "`delivery_attachment_jobs_from_report()`" in change_log
    assert "`artifact_handoff_report_invalid`" in change_log
    assert "2 failing-first artifact handoff tests" in change_log
    assert "21 tests passed" in change_log
    assert "Artifact handoff delivery job extraction is fail-closed" in operator_guide
    assert "requires `attach_to_servicenow` to be an actual boolean" in operator_guide
    assert "without calling custom `__str__` or" in operator_guide
    assert "`__bool__` methods" in operator_guide


def test_sprint_623_documents_artifact_handoff_report_creation_validation() -> None:
    change_log = Path("docs/sprints/sprint-623-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Artifact handoff report creation fail-closed validation" in change_log
    assert "`build_artifact_handoff_report()`" in change_log
    assert "`approved_for_delivery` to be an exact boolean" in change_log
    assert "`artifact_handoff_report_invalid`" in change_log
    assert "2 failing-first artifact handoff tests" in change_log
    assert "23 tests passed" in change_log
    assert "Artifact handoff report creation uses the same malformed-report boundary" in (
        operator_guide
    )
    assert "requires artifact inputs to be dictionaries" in operator_guide
    assert "`approved_for_delivery` to be an" in operator_guide
    assert "actual boolean before artifact planning" in operator_guide
    assert "before path construction, enum parsing, or approval checks" in operator_guide


def test_sprint_624_documents_writeback_state_choice_exact_string_mapping() -> None:
    change_log = Path("docs/sprints/sprint-624-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Writeback state choice exact-string mapping" in change_log
    assert "`build_state_mapping_from_choices()`" in change_log
    assert "2 failing-first writeback tests" in change_log
    assert "16 tests passed" in change_log
    assert "Writeback state-choice mapping is exact-string only" in operator_guide
    assert "string subclasses," in operator_guide
    assert "objects, numbers, and other malformed choice values" in operator_guide
    assert "the mapper returns no state mapping" in operator_guide


def test_sprint_625_documents_writeback_batch_report_exact_string_values() -> None:
    change_log = Path("docs/sprints/sprint-625-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Writeback batch report exact-string diagnostic values" in change_log
    assert "`_diagnostic_report_value()`" in change_log
    assert "String subclasses render as `[non-json value]`" in change_log
    assert "1 failing-first writeback orchestration test" in change_log
    assert "27 tests passed" in change_log
    assert "nested exact string values are redacted" in operator_guide
    assert "Unsupported diagnostic scalar values, string subclasses" in operator_guide
    assert "finite JSON primitives remain typed" in operator_guide


def test_sprint_932_documents_writeback_batch_report_scalar_subclass_boundary() -> (
    None
):
    change_log = Path("docs/sprints/sprint-932-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Writeback batch report scalar-subclass diagnostic boundary" in change_log
    assert "`_diagnostic_report_value()`" in change_log
    assert "1 failing-first writeback batch report scalar-subclass assertion" in change_log
    assert "Batch report boolean and integer diagnostic values" in operator_guide
    assert "boolean and integer subclasses render as `[non-json value]`" in operator_guide


def test_sprint_938_documents_writeback_batch_report_exact_container_boundary() -> (
    None
):
    change_log = Path("docs/sprints/sprint-938-change-log.md").read_text(
        encoding="utf-8",
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Writeback batch report exact-container diagnostic boundary" in change_log
    assert "`_diagnostic_report_node()`" in change_log
    assert "1 failing-first writeback batch report container-subclass assertion" in (
        change_log
    )
    assert "Batch reports traverse only exact dictionaries, lists, and tuples" in (
        operator_guide
    )
    assert "dictionary, list, and tuple subclasses render as `[non-json value]`" in (
        operator_guide
    )


def test_sprint_626_documents_manual_review_feedback_exact_string_boundary() -> None:
    change_log = Path("docs/sprints/sprint-626-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Manual-review feedback exact-string metadata boundary" in change_log
    assert "`eligibility_reasons` and `reviewer_notes`" in change_log
    assert "String subclasses and non-string values are skipped" in change_log
    assert "1 failing-first model fulfillment test" in change_log
    assert "32 tests passed" in change_log
    assert "only exact string values are accepted" in operator_guide
    assert "string subclasses and non-string values are skipped" in operator_guide
    assert "Manual-review ServiceNow work-note feedback" in operator_guide


def test_sprint_627_documents_context_escalation_exact_string_boundary() -> None:
    change_log = Path("docs/sprints/sprint-627-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Context escalation exact-string routing boundary" in change_log
    assert "`plan_context_escalation()`" in change_log
    assert "2 failing-first context escalation tests" in change_log
    assert "5 tests passed" in change_log
    assert "Context escalation routing is exact-string only" in operator_guide
    assert "Unsafe `status` values fail closed to manual review" in operator_guide
    assert "cannot execute custom string conversion hooks" in operator_guide


def test_sprint_628_documents_openai_provider_validation_exact_location_diagnostics() -> None:
    change_log = Path("docs/sprints/sprint-628-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "OpenAI provider validation exact-location diagnostics" in change_log
    assert "`_openai_runtime_error_fields()`" in change_log
    assert "1 failing-first runtime test" in change_log
    assert "3 tests passed" in change_log
    assert "OpenAI provider runtime validation diagnostics are exact-field only" in operator_guide
    assert "Unknown," in operator_guide
    assert "non-string, string-subclass, or unstringifiable validation locations" in operator_guide
    assert "`OPENAI_PROVIDER_SETTINGS`" in operator_guide
    assert "cannot execute custom `__str__` hooks" in operator_guide


def test_sprint_629_documents_admin_alert_row_exact_string_rendering() -> None:
    change_log = Path("docs/sprints/sprint-629-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin alert row exact-string rendering" in change_log
    assert "`_admin_alert_row()`" in change_log
    assert "1 failing-first runtime test" in change_log
    assert "3 tests passed" in change_log
    assert "HTML admin console treats alert response fields as untrusted" in operator_guide
    assert "only when those projected fields are exact strings" in operator_guide
    assert "cannot execute custom `__str__` hooks" in operator_guide


def test_sprint_630_documents_artifact_handoff_cli_exact_story_number_boundary() -> None:
    change_log = Path("docs/sprints/sprint-630-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Artifact handoff CLI exact story-number boundary" in change_log
    assert "`_handoff_report_story_number()`" in change_log
    assert "2 failing-first CLI tests" in change_log
    assert "4 tests passed" in change_log
    assert "Artifact handoff report story numbers are exact-string only" in operator_guide
    assert "`write-artifact-handoff-summary` and `attach-delivery-artifacts`" in operator_guide
    assert "`reason=artifact_handoff_report_invalid`" in operator_guide
    assert "do not coerce malformed report identifiers with" in operator_guide


def test_sprint_631_documents_delivery_attachment_audit_exact_response_metadata() -> None:
    change_log = Path("docs/sprints/sprint-631-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Delivery attachment audit exact-string response metadata" in change_log
    assert "1 failing-first CLI test" in change_log
    assert "`attachment-sys-id-secret`" in change_log
    assert "4 tests passed" in change_log
    assert "Attachment audit values are exact-string only" in operator_guide
    assert "`[attachment sys_id unavailable]`" in operator_guide
    assert "instead of coercing it with" in operator_guide


def test_sprint_632_documents_model_fulfillment_story_text_exact_context_boundary() -> None:
    change_log = Path("docs/sprints/sprint-632-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model fulfillment story text exact-string context boundary" in change_log
    assert "`_surface_context_and_rags_for_story()`" in change_log
    assert "`_story_text_for_surface_context()`" in change_log
    assert "1 failing-first model fulfillment test" in change_log
    assert "3 tests passed" in change_log
    assert "Model fulfillment story text for surface context is exact-string only" in operator_guide
    assert "`short_description`, `description`, and" in operator_guide
    assert "cannot execute custom `__str__` hooks" in operator_guide


def test_sprint_633_documents_model_fulfillment_required_surface_exact_boundary() -> None:
    change_log = Path("docs/sprints/sprint-633-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model fulfillment required-surface exact-string boundary" in change_log
    assert "`_required_surfaces_for_assessment()`" in change_log
    assert "1 failing-first model fulfillment test" in change_log
    assert "`required-surface-secret`" in change_log
    assert "3 tests passed" in change_log
    assert "Model fulfillment required-surface overrides are exact-string only" in operator_guide
    assert "keeps only exact string surface names" in operator_guide
    assert "cannot execute custom" in operator_guide


def test_sprint_634_documents_public_doc_citation_version_exact_boundary() -> None:
    change_log = Path("docs/sprints/sprint-634-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Public documentation citation version exact-string boundary" in change_log
    assert "`_public_doc_citation_version()`" in change_log
    assert "1 failing-first model fulfillment test" in change_log
    assert "`public-doc-version-secret`" in change_log
    assert "3 tests passed" in change_log
    assert "Public-documentation citation versions are exact-string only" in operator_guide
    assert "records an empty" in operator_guide
    assert "instead of coercing it with" in operator_guide


def test_sprint_635_documents_retrieved_update_set_handoff_exact_scalar_boundary() -> None:
    change_log = Path("docs/sprints/sprint-635-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set handoff exact primitive scalar boundary" in change_log
    assert "`_candidate_field_text()`" in change_log
    assert "`_imported_update_set_lookup_text()`" in change_log
    assert "1 failing-first retrieved Update Set handoff test" in change_log
    assert "3 tests passed" in change_log
    assert "accepts only exact primitive `str`, `bool`, and `int`" in operator_guide
    assert "integer subclasses" in operator_guide
    assert "`dictionary/form handoff field contains non-JSON value`" in operator_guide


def test_sprint_636_documents_artifact_manifest_concrete_path_boundary() -> None:
    change_log = Path("docs/sprints/sprint-636-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Artifact manifest concrete Path boundary" in change_log
    assert "2 failing-first artifact manifest tests" in change_log
    assert "hostile `Path` subclasses" in change_log
    assert "5 tests passed" in change_log
    assert "Artifact manifest path serialization is strict" in operator_guide
    assert "concrete platform `pathlib.Path` values" in operator_guide
    assert "`artifact path must be a concrete pathlib Path`" in operator_guide


def test_sprint_637_documents_model_fulfillment_persisted_artifact_boundary() -> None:
    change_log = Path("docs/sprints/sprint-637-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model fulfillment persisted artifact exact-string boundary" in change_log
    assert "`str(artifact.path)`" in change_log
    assert "1 failing-first model fulfillment test" in change_log
    assert "4 tests passed" in change_log
    assert "Persisted fulfillment artifact paths are exact-string only" in operator_guide
    assert "`db://artifact_blobs/<id>`" in operator_guide
    assert "`persisted artifact path contains non-JSON value`" in operator_guide


def test_sprint_638_documents_public_doc_context_bundle_citation_boundary() -> None:
    change_log = Path("docs/sprints/sprint-638-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Public documentation context-bundle citation version boundary" in change_log
    assert "`str(result.citation.version or \"\")`" in change_log
    assert "1 failing-first instance-discovery test" in change_log
    assert "4 tests passed" in change_log
    assert (
        "Public-documentation citation versions are exact-string only in ServiceNow "
        "surface context bundles"
    ) in operator_guide
    assert "`public_docs` surface" in operator_guide
    assert "does not call `str()` on" in operator_guide


def test_sprint_639_documents_public_doc_required_citation_boundary() -> None:
    change_log = Path("docs/sprints/sprint-639-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Public documentation required citation metadata boundary" in change_log
    assert "`source` and `content_hash`" in change_log
    assert "1 failing-first instance-discovery test" in change_log
    assert "4 tests passed" in change_log
    assert "Public-documentation citation `source` and `content_hash` metadata" in operator_guide
    assert "`public_web:<hash>` evidence entries" in operator_guide
    assert "`public documentation citation contains non-JSON value`" in operator_guide


def test_sprint_640_documents_public_doc_content_excerpt_boundary() -> None:
    change_log = Path("docs/sprints/sprint-640-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Public documentation content excerpt boundary" in change_log
    assert "hostile public-doc content string subclass" in change_log
    assert "1 failing-first instance-discovery test" in change_log
    assert "5 tests passed" in change_log
    assert "Public-documentation content excerpts are exact-string only" in operator_guide
    assert "`public documentation content contains non-JSON value`" in operator_guide
    assert "before record summaries" in operator_guide
    assert "or excerpt-length metadata are created" in operator_guide


def test_sprint_641_documents_public_doc_query_evidence_boundary() -> None:
    change_log = Path("docs/sprints/sprint-641-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Public documentation query evidence boundary" in change_log
    assert "`instance_context_bundle.public_doc_queries`" in change_log
    assert "1 failing-first instance-discovery test" in change_log
    assert "4 tests passed" in change_log
    assert "Public-documentation query evidence is exact-string only" in operator_guide
    assert "`public_docs:<query>` evidence strings" in operator_guide
    assert "`public documentation query contains non-JSON value`" in operator_guide


def test_sprint_642_documents_public_doc_confidence_format_boundary() -> None:
    change_log = Path("docs/sprints/sprint-642-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Public documentation citation confidence formatting boundary" in change_log
    assert "custom `__format__` behavior" in change_log
    assert "1 failing-first instance-discovery test" in change_log
    assert "4 tests passed" in change_log
    assert "Public-documentation citation confidence is validated" in operator_guide
    assert "`0..1` range" in operator_guide
    assert "`public documentation citation confidence is unsafe`" in operator_guide


def test_sprint_643_documents_dictionary_form_discovery_metadata_boundary() -> None:
    change_log = Path("docs/sprints/sprint-643-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Dictionary/form discovery metadata exact-string boundary" in change_log
    assert "`discover_dictionary_form_context()`" in change_log
    assert "1 failing-first instance-discovery test" in change_log
    assert "3 tests passed" in change_log
    assert "Dictionary/form discovery metadata is exact-string only" in operator_guide
    assert "`sys_db_object`, `sys_dictionary`, `sys_ui_section`" in operator_guide
    assert "`dictionary/form discovery metadata contains non-JSON value`" in operator_guide


def test_sprint_644_documents_dictionary_form_discovery_numeric_boundary() -> None:
    change_log = Path("docs/sprints/sprint-644-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Dictionary/form discovery numeric metadata boundary" in change_log
    assert "hostile form element position object" in change_log
    assert "1 failing-first instance-discovery test" in change_log
    assert "4 tests passed" in change_log
    assert "Dictionary/form discovery numeric metadata is strict" in operator_guide
    assert "exact integers or digit-only exact strings" in operator_guide
    assert "`dictionary/form discovery numeric metadata is unsafe`" in operator_guide


def test_sprint_1004_documents_dictionary_form_discovery_record_collection_guard() -> None:
    change_log = Path("docs/sprints/sprint-1004-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Dictionary/form discovery record collection guard" in change_log
    assert "`discover_dictionary_form_context()`" in change_log
    assert "`_metadata_records()`" in change_log
    assert "dictionary/form discovery metadata contains non-JSON value" in change_log
    assert (
        "1 failing-first dictionary/form discovery record collection subclass assertion"
        in change_log
    )
    assert (
        "Dictionary/form discovery record collections are exact containers"
        in operator_guide
    )
    assert "`fetch_table_records()` responses for `sys_db_object`" in operator_guide
    assert "before truthiness checks, indexing" in operator_guide
    assert (
        "`test_discover_dictionary_form_context_rejects_record_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_discover_dictionary_form_context_rejects_record_subclass_without_leak`"
        in change_log
    )


def test_sprint_645_documents_discovery_active_metadata_boundary() -> None:
    change_log = Path("docs/sprints/sprint-645-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Discovery active metadata exact bool/string boundary" in change_log
    assert "hostile active-state object" in change_log
    assert "1 failing-first instance-discovery test" in change_log
    assert "6 tests passed" in change_log
    assert "Discovery active-state metadata is strict" in operator_guide
    assert "accepted only as exact booleans or exact strings" in operator_guide
    assert "`discovery active metadata is unsafe`" in operator_guide


def test_sprint_646_documents_discovery_text_metadata_boundary() -> None:
    change_log = Path("docs/sprints/sprint-646-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Discovery surface text metadata exact-string boundary" in change_log
    assert "hostile business-rule name object" in change_log
    assert "1 failing-first instance-discovery test" in change_log
    assert "7 tests passed" in change_log
    assert "Shared ServiceNow surface discovery text metadata is exact-string only" in (
        operator_guide
    )
    assert "exact reference dictionaries" in operator_guide
    assert "`discovery text metadata contains non-JSON value`" in operator_guide


def test_sprint_1005_documents_shared_surface_discovery_record_collection_guard() -> None:
    change_log = Path("docs/sprints/sprint-1005-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Shared surface discovery record collection guard" in change_log
    assert "`_table_surface()`" in change_log
    assert "`_records_surface()`" in change_log
    assert "`_surface_records()`" in change_log
    assert "discovery text metadata contains non-JSON value" in change_log
    assert (
        "1 failing-first shared surface discovery record collection subclass assertion"
        in change_log
    )
    assert (
        "Shared ServiceNow surface discovery record collections are exact containers"
        in operator_guide
    )
    assert "before record iteration, `.get()` access" in operator_guide
    assert (
        "`test_discover_surface_context_rejects_record_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_discover_surface_context_rejects_record_subclass_without_leak`"
        in change_log
    )


def test_sprint_1008_documents_cmdb_ire_discovery_record_collection_guard() -> None:
    change_log = Path("docs/sprints/sprint-1008-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "CMDB IRE discovery record collection guard" in change_log
    assert "`_cmdb_ire_identification_rules_surface()`" in change_log
    assert "`_cmdb_class_hierarchy_surface()`" in change_log
    assert "`_surface_records()`" in change_log
    assert "discovery text metadata contains non-JSON value" in change_log
    assert (
        "1 failing-first CMDB IRE record collection subclass assertion"
        in change_log
    )
    assert (
        "CMDB IRE discovery record collections are exact containers"
        in operator_guide
    )
    assert "`cmdb_identifier`, `cmdb_identifier_entry`, and `sys_db_object`" in (
        operator_guide
    )
    assert "before IRE rule iteration, active-state parsing" in operator_guide
    assert (
        "`test_cmdb_ire_identification_rejects_record_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_cmdb_ire_identification_rejects_record_subclass_without_leak`"
        in change_log
    )


def test_sprint_647_documents_implementation_packet_review_item_boundary() -> None:
    change_log = Path("docs/sprints/sprint-647-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Implementation-packet review item exact-string boundary" in change_log
    assert "hostile review item string subclass" in change_log
    assert "1 failing-first implementation-packet test" in change_log
    assert "6 tests passed" in change_log
    assert "Review items must be non-empty exact strings" in operator_guide
    assert "String subclasses and non-string values" in operator_guide
    assert "`test_plan items must be non-empty exact strings`" in operator_guide


def test_sprint_648_documents_raw_xml_scanner_exact_key_boundary() -> None:
    change_log = Path("docs/sprints/sprint-648-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Implementation-packet raw XML scanner exact-key boundary" in change_log
    assert "hostile provider-response key" in change_log
    assert "1 failing-first packet-validation test" in change_log
    assert "6 tests passed" in change_log
    assert "Provider response object keys encountered during the raw XML scan" in (
        operator_guide
    )
    assert "`model response object keys must be exact strings`" in operator_guide
    assert "string subclasses cannot execute custom string methods" in operator_guide


def test_sprint_649_documents_response_table_exact_string_boundary() -> None:
    change_log = Path("docs/sprints/sprint-649-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Implementation-packet response table exact-string boundary" in change_log
    assert "hostile provider-response table object" in change_log
    assert "1 failing-first packet-validation test" in change_log
    assert "4 tests passed" in change_log
    assert "Model-proposed table names must be exact strings" in operator_guide
    assert "`model response table names must be exact strings`" in operator_guide
    assert "before trimming, table comparison, or diagnostic rendering" in operator_guide


def test_sprint_650_documents_generic_provider_response_identifier_boundary() -> None:
    change_log = Path("docs/sprints/sprint-650-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Generic provider response exact identifier boundary" in change_log
    assert "hostile operation object" in change_log
    assert "hostile table and sys_id objects" in change_log
    assert "8 tests passed" in change_log
    assert "Change `table`," in operator_guide
    assert "`operation must be an exact string`" in operator_guide
    assert "`sys_id must be an exact string`" in operator_guide


def test_sprint_651_documents_provider_field_name_exact_string_boundary() -> None:
    change_log = Path("docs/sprints/sprint-651-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider field-name exact-string normalization boundary" in change_log
    assert "hostile field-name string subclass" in change_log
    assert "1 failing-first provider-response-normalization test" in change_log
    assert "6 tests passed" in change_log
    assert "Field entry names must be non-empty exact strings" in operator_guide
    assert "before emptiness checks, length checks" in operator_guide
    assert "response field entry must include a non-empty exact name" in operator_guide


def test_sprint_652_documents_provider_candidate_exact_container_boundary() -> None:
    change_log = Path("docs/sprints/sprint-652-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider candidate exact-container normalization boundary" in change_log
    assert "hostile `list` and `dict` subclasses" in change_log
    assert "4 failing-first provider-response-normalization tests" in change_log
    assert "127 tests passed" in change_log
    assert "must use exact JSON-native `list` or `dict` containers" in operator_guide
    assert "before length checks, mapping lookups, iteration, copying" in operator_guide
    assert "response changes must be an exact list" in operator_guide
    assert "response field entry must be an exact object" in operator_guide


def test_sprint_653_documents_provider_candidate_root_exact_object_boundary() -> None:
    change_log = Path("docs/sprints/sprint-653-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider candidate root exact-object normalization boundary" in change_log
    assert "hostile root candidate dictionary subclass" in change_log
    assert "1 failing-first provider-response-normalization test" in change_log
    assert "128 tests passed" in change_log
    assert "The root candidate check runs before the normalizer reads `changes`" in (
        operator_guide
    )
    assert "response candidate must be an exact object" in operator_guide
    assert "dictionary subclasses cannot" in operator_guide
    assert "execute custom lookup hooks" in operator_guide


def test_sprint_654_documents_provider_candidate_exact_object_key_boundary() -> None:
    change_log = Path("docs/sprints/sprint-654-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider candidate exact-object-key normalization boundary" in change_log
    assert "unsafe root, change, and field-entry string-subclass keys" in change_log
    assert "3 failing-first provider-response-normalization tests" in change_log
    assert "131 tests passed" in change_log
    assert "Object keys on the root candidate, each change object" in operator_guide
    assert "must be exact strings" in operator_guide
    assert "response candidate keys must be exact strings" in operator_guide
    assert "response change keys must be exact strings" in operator_guide
    assert "response field entry keys must be exact strings" in operator_guide


def test_sprint_655_documents_provider_field_value_json_scalar_boundary() -> None:
    change_log = Path("docs/sprints/sprint-655-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider field-value JSON-scalar normalization boundary" in change_log
    assert "4 failing-first provider-response-normalization tests" in change_log
    assert "missing values, object values, string-subclass values" in change_log
    assert "135 tests passed" in change_log
    assert "Field entries must include an explicit `value` key" in operator_guide
    assert "values must be exact JSON scalar values" in operator_guide
    assert "response field entry must include value" in operator_guide
    assert "response field value must be a JSON scalar" in operator_guide
    assert "before insertion into normalized fields" in operator_guide


def test_sprint_656_documents_provider_root_text_list_boundary() -> None:
    change_log = Path("docs/sprints/sprint-656-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider root text-list normalization boundary" in change_log
    assert "3 failing-first provider-response-normalization tests" in change_log
    assert "unsafe `test_plan` and `rollback_notes` shapes" in change_log
    assert "138 tests passed" in change_log
    assert "Root-level provider `test_plan` and `rollback_notes` values" in operator_guide
    assert "validated after change normalization" in operator_guide
    assert "specific change diagnostics retain priority" in operator_guide
    assert "response test_plan must be an exact list" in operator_guide
    assert "response rollback_notes items must be exact strings" in operator_guide


def test_sprint_657_documents_provider_allowed_property_boundary() -> None:
    change_log = Path("docs/sprints/sprint-657-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider candidate allowed-property normalization boundary" in change_log
    assert "additionalProperties: false" in change_log
    assert "3 failing-first provider-response-normalization tests" in change_log
    assert "141 tests passed" in change_log
    assert "additionalProperties: false" in operator_guide
    assert "The root candidate may only include `changes`, `test_plan`, and `rollback_notes`" in (
        operator_guide
    )
    assert "response candidate includes unsupported properties" in operator_guide
    assert "response change includes unsupported properties" in operator_guide
    assert "response field entry includes unsupported properties" in operator_guide


def test_sprint_658_documents_provider_change_metadata_boundary() -> None:
    change_log = Path("docs/sprints/sprint-658-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider change metadata schema normalization boundary" in change_log
    assert "5 failing-first provider-response-normalization tests" in change_log
    assert "unsafe change metadata was accepted" in change_log
    assert "146 tests passed" in change_log
    assert "Change metadata is validated after field normalization" in operator_guide
    assert "field-specific diagnostics retain priority" in operator_guide
    assert "response change table must be an exact string" in operator_guide
    assert "response change operation is unsupported" in operator_guide
    assert "response change sys_id must be null" in operator_guide
    assert "response change rationale must be an exact string or null" in operator_guide


def test_sprint_659_documents_provider_root_text_list_bounds() -> None:
    change_log = Path("docs/sprints/sprint-659-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider root text-list bound normalization boundary" in change_log
    assert "2 failing-first provider-response-normalization tests" in change_log
    assert "oversized root text-list counts and oversized note items" in change_log
    assert "148 tests passed" in change_log
    assert "Each list may contain at most 100" in operator_guide
    assert "each item may contain at most 2000 characters" in operator_guide
    assert "response test_plan includes too many items (max 100)" in operator_guide
    assert "response rollback_notes item exceeds 2000 characters" in operator_guide


def test_sprint_660_documents_provider_change_metadata_text_bounds() -> None:
    change_log = Path("docs/sprints/sprint-660-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider change metadata text-bound normalization boundary" in change_log
    assert "5 failing-first provider-response-normalization tests" in change_log
    assert "unsafe table identifiers and oversized rationale text" in change_log
    assert "Provider change table identifiers must be non-empty" in operator_guide
    assert "at most 200 characters" in operator_guide
    assert "response change table must be a non-empty identifier" in operator_guide
    assert "response change rationale exceeds 2000 characters" in operator_guide


def test_sprint_661_documents_provider_string_field_value_bounds() -> None:
    change_log = Path("docs/sprints/sprint-661-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider string field-value bound normalization boundary" in change_log
    assert "2 failing-first provider-response-normalization tests" in change_log
    assert "oversized string field values" in change_log
    assert "Exact string field values may contain at most 100000 characters" in (
        operator_guide
    )
    assert "response field value exceeds 100000 characters" in operator_guide


def test_sprint_662_documents_provider_numeric_field_value_bounds() -> None:
    change_log = Path("docs/sprints/sprint-662-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider numeric field-value safe JSON boundary" in change_log
    assert "4 failing-first provider-response-normalization assertions" in change_log
    assert "unsafe numeric field values" in change_log
    assert "Numeric field values must stay within the interoperable safe JSON range" in (
        operator_guide
    )
    assert "response field numeric value is outside safe JSON range" in operator_guide


def test_sprint_663_documents_provider_minimum_change_count() -> None:
    change_log = Path("docs/sprints/sprint-663-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider minimum-change normalization boundary" in change_log
    assert "1 failing-first provider-response-normalization test" in change_log
    assert "empty provider change lists" in change_log
    assert "Provider candidates must include at least one change" in operator_guide
    assert "response must include at least one change" in operator_guide


def test_sprint_664_documents_provider_schema_bound_alignment() -> None:
    change_log = Path("docs/sprints/sprint-664-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider schema bound alignment" in change_log
    assert "1 failing-first OpenAI provider schema test" in change_log
    assert "schema drift" in change_log
    assert "OpenAI structured-output schema advertises the same provider bounds" in (
        operator_guide
    )
    assert "Anthropic still strips unsupported schema constraints" in operator_guide


def test_sprint_665_documents_provider_schema_numeric_bound_alignment() -> None:
    change_log = Path("docs/sprints/sprint-665-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider schema numeric-bound alignment" in change_log
    assert "1 failing-first OpenAI provider schema assertion" in change_log
    assert "numeric safe range" in change_log
    assert "OpenAI structured-output schema also advertises the numeric safe range" in (
        operator_guide
    )
    assert "`-9007199254740991..9007199254740991`" in operator_guide


def test_sprint_666_documents_provider_review_item_non_empty_boundary() -> None:
    change_log = Path("docs/sprints/sprint-666-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider review-list item non-empty boundary" in change_log
    assert "2 failing-first provider-response-normalization assertions" in change_log
    assert "blank provider review-list items" in change_log
    assert "Root-level provider review-list items must be non-empty exact strings" in (
        operator_guide
    )
    assert "response test_plan items must be non-empty exact strings" in operator_guide


def test_sprint_667_documents_provider_table_identifier_shape_boundary() -> None:
    change_log = Path("docs/sprints/sprint-667-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider table identifier shape boundary" in change_log
    assert "4 failing-first provider-response-normalization assertions" in change_log
    assert "unsafe table identifier shapes" in change_log
    assert "Provider change table identifiers must use ServiceNow-safe identifier syntax" in (
        operator_guide
    )
    assert "response change table must be a safe identifier" in operator_guide


def test_sprint_668_documents_provider_field_identifier_shape_boundary() -> None:
    change_log = Path("docs/sprints/sprint-668-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider field identifier shape boundary" in change_log
    assert "4 failing-first provider-response-normalization assertions" in change_log
    assert "unsafe field identifier shapes" in change_log
    assert "Provider change field identifiers must use ServiceNow-safe identifier syntax" in (
        operator_guide
    )
    assert "response field entry name must be a safe identifier" in operator_guide


def test_sprint_669_documents_provider_schema_identifier_pattern_alignment() -> None:
    change_log = Path("docs/sprints/sprint-669-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider schema identifier-pattern alignment" in change_log
    assert "1 failing-first OpenAI provider schema assertion" in change_log
    assert "safe identifier pattern" in change_log
    assert "OpenAI structured-output schema advertises the safe identifier pattern" in (
        operator_guide
    )
    assert "`^[A-Za-z_][A-Za-z0-9_]*$`" in operator_guide
    assert "Anthropic strips the `pattern` constraint" in operator_guide


def test_sprint_670_documents_provider_identifier_pattern_single_source() -> None:
    change_log = Path("docs/sprints/sprint-670-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider identifier pattern single-source enforcement" in change_log
    assert "2 failing-first provider-response-normalization assertions" in change_log
    assert "runtime validation ignored the exported pattern" in change_log
    assert "Provider safe identifier enforcement uses the exported pattern constant" in (
        operator_guide
    )
    assert "`PROVIDER_SAFE_IDENTIFIER_PATTERN`" in operator_guide


def test_sprint_671_documents_provider_rationale_control_character_boundary() -> None:
    change_log = Path("docs/sprints/sprint-671-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider rationale control-character boundary" in change_log
    assert "2 failing-first provider-response-normalization assertions" in change_log
    assert "newline/control-bearing rationale text" in change_log
    assert "Provider change rationale text must not contain ASCII control characters" in (
        operator_guide
    )
    assert "response change rationale must not contain control characters" in operator_guide


def test_sprint_672_documents_provider_review_list_control_character_boundary() -> None:
    change_log = Path("docs/sprints/sprint-672-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider review-list control-character boundary" in change_log
    assert "2 failing-first provider-response-normalization assertions" in change_log
    assert "newline/control-bearing review-list text" in change_log
    assert "Root-level provider review-list items must not contain ASCII control characters" in (
        operator_guide
    )
    assert "response test_plan items must not contain control characters" in operator_guide


def test_sprint_673_documents_provider_schema_no_control_text_pattern_alignment() -> None:
    change_log = Path("docs/sprints/sprint-673-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider schema no-control text-pattern alignment" in change_log
    assert "1 failing-first OpenAI provider schema assertion" in change_log
    assert "no-control text pattern" in change_log
    assert "OpenAI structured-output schema advertises the no-control text pattern" in (
        operator_guide
    )
    assert "`^[^\\u0000-\\u001F\\u007F]*$`" in operator_guide
    assert "Anthropic strips text `pattern` constraints" in operator_guide


def test_sprint_674_documents_provider_text_pattern_single_source() -> None:
    change_log = Path("docs/sprints/sprint-674-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider text pattern single-source enforcement" in change_log
    assert "2 failing-first provider-response-normalization assertions" in change_log
    assert "runtime text validation ignored the exported pattern" in change_log
    assert "Provider text policy enforcement uses the exported pattern constant" in (
        operator_guide
    )
    assert "`PROVIDER_NO_CONTROL_TEXT_PATTERN`" in operator_guide


def test_sprint_675_documents_provider_meaningful_text_policy() -> None:
    change_log = Path("docs/sprints/sprint-675-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider meaningful text-policy boundary" in change_log
    assert "2 failing-first provider-response-normalization assertions" in change_log
    assert "blank rationale text" in change_log
    assert "Provider text policy requires at least one non-whitespace" in operator_guide
    assert "use `null` rather than an empty string" in operator_guide


def test_sprint_676_documents_provider_prompt_sentence_boundary() -> None:
    change_log = Path("docs/sprints/sprint-676-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider prompt sentence-boundary hardening" in change_log
    assert "1 failing-first provider-contract assertion" in change_log
    assert "script.For standard Catalog" in change_log
    assert "Shared provider system prompt sentence boundaries are regression-tested" in (
        operator_guide
    )
    assert "script. For standard Catalog Item builds" in operator_guide


def test_sprint_677_documents_anthropic_metadata_stringification_boundary() -> None:
    change_log = Path("docs/sprints/sprint-677-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Anthropic metadata stringification boundary" in change_log
    assert "1 failing-first Anthropic provider assertion" in change_log
    assert "client_secret=stop-reason-secret" in change_log
    assert "Anthropic successful-response metadata only reflects exact strings" in (
        operator_guide
    )
    assert "[unsupported provider metadata value]" in operator_guide


def test_sprint_678_documents_provider_response_text_exact_string_boundary() -> None:
    change_log = Path("docs/sprints/sprint-678-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider response text exact-string boundary" in change_log
    assert "3 failing-first provider response-text assertions" in change_log
    assert "client_secret=output-text-secret" in change_log
    assert "Provider response JSON text must be exact strings" in operator_guide
    assert "string subclasses are ignored as missing provider output" in operator_guide


def test_sprint_679_documents_provider_response_list_exact_container_boundary() -> None:
    change_log = Path("docs/sprints/sprint-679-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider response list exact-container boundary" in change_log
    assert "3 failing-first provider response-list assertions" in change_log
    assert "client_secret=output-list-secret" in change_log
    assert "Provider response JSON container lists must be exact lists" in operator_guide
    assert "list subclasses are ignored as missing provider output" in operator_guide


def test_sprint_680_documents_provider_response_dict_exact_item_boundary() -> None:
    change_log = Path("docs/sprints/sprint-680-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider response dict exact-item boundary" in change_log
    assert "3 failing-first provider response-dict assertions" in change_log
    assert "client_secret=output-item-secret" in change_log
    assert "Provider response JSON item objects must be exact dictionaries" in operator_guide
    assert "dict subclasses are ignored as missing provider output" in operator_guide


def test_sprint_681_documents_provider_error_envelope_exact_dict_boundary() -> None:
    change_log = Path("docs/sprints/sprint-681-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider error envelope exact-dict boundary" in change_log
    assert "2 failing-first provider error-envelope assertions" in change_log
    assert "client_secret=error-envelope-secret" in change_log
    assert "Provider API error envelopes must be exact dictionaries" in operator_guide
    assert "dict subclasses fall back to status-only diagnostics" in operator_guide


def test_sprint_682_documents_provider_top_level_response_body_exact_dict_boundary() -> None:
    change_log = Path("docs/sprints/sprint-682-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider top-level response body exact-dict boundary" in change_log
    assert "4 failing-first provider top-level body assertions" in change_log
    assert "client_secret=response-body-secret" in change_log
    assert "Provider top-level response JSON bodies must be exact dictionaries" in (
        operator_guide
    )
    assert "response-body subclasses are rejected before provider parsing" in operator_guide


def test_sprint_683_documents_anthropic_response_header_exact_container_boundary() -> None:
    change_log = Path("docs/sprints/sprint-683-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Anthropic response header exact-container boundary" in change_log
    assert "3 failing-first Anthropic response-header assertions" in change_log
    assert "client_secret=header-mapping-secret" in change_log
    assert "client_secret=header-key-secret" in change_log
    assert "Anthropic response headers must use exact dictionaries" in operator_guide
    assert "header subclasses and non-exact header keys or values are ignored" in (
        operator_guide
    )


def test_sprint_684_documents_provider_prompt_payload_exact_json_boundary() -> None:
    change_log = Path("docs/sprints/sprint-684-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider prompt payload exact-JSON boundary" in change_log
    assert "4 failing-first provider prompt-payload assertions" in change_log
    assert "client_secret=prompt-mapping-secret" in change_log
    assert "client_secret=prompt-list-secret" in change_log
    assert "Provider prompt payloads are copied through an exact JSON boundary" in (
        operator_guide
    )
    assert "dict subclasses, list subclasses, key subclasses, and scalar subclasses" in (
        operator_guide
    )


def test_sprint_685_documents_openai_error_scalar_exact_string_boundary() -> None:
    change_log = Path("docs/sprints/sprint-685-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "OpenAI error scalar exact-string boundary" in change_log
    assert "3 failing-first OpenAI error-scalar assertions" in change_log
    assert "client_secret=message-secret" in change_log
    assert "OpenAI error diagnostic scalar fields must be exact strings" in operator_guide
    assert "message, type, and code string subclasses are ignored" in operator_guide


def test_sprint_686_documents_anthropic_error_scalar_exact_string_boundary() -> None:
    change_log = Path("docs/sprints/sprint-686-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Anthropic error scalar exact-string boundary" in change_log
    assert "2 failing-first Anthropic error-scalar assertions" in change_log
    assert "client_secret=message-secret" in change_log
    assert "Anthropic error diagnostic scalar fields must be exact strings" in (
        operator_guide
    )
    assert "message and type string subclasses are ignored" in operator_guide


def test_sprint_687_documents_provider_content_type_marker_boundary() -> None:
    change_log = Path("docs/sprints/sprint-687-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider content type-marker exact-string boundary" in change_log
    assert "2 failing-first provider content type-marker assertions" in change_log
    assert "client_secret=type-marker-secret" in change_log
    assert "Provider response content type markers must be exact strings" in operator_guide
    assert "non-string marker objects cannot execute equality hooks" in operator_guide


def test_sprint_688_documents_provider_status_code_exact_integer_boundary() -> None:
    change_log = Path("docs/sprints/sprint-688-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider response status-code exact-integer boundary" in change_log
    assert "2 failing-first provider status-code assertions" in change_log
    assert "client_secret=status-code-secret" in change_log
    assert "Provider response status codes must be exact integers" in operator_guide
    assert "status-code objects cannot execute comparison hooks" in operator_guide


def test_sprint_689_documents_provider_status_code_http_range_boundary() -> None:
    change_log = Path("docs/sprints/sprint-689-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider response status-code HTTP-range boundary" in change_log
    assert "4 failing-first provider status-code range assertions" in change_log
    assert "`99`" in change_log
    assert "`600`" in change_log
    assert "Provider response status codes must also be valid HTTP status values" in (
        operator_guide
    )
    assert "`100..599`" in operator_guide


def test_sprint_690_documents_provider_response_object_exact_type_boundary() -> None:
    change_log = Path("docs/sprints/sprint-690-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider transport response object exact-type boundary" in change_log
    assert "2 failing-first provider response-object assertions" in change_log
    assert "client_secret=response-object-secret" in change_log
    assert "Provider transport responses must be exact response DTOs" in operator_guide
    assert "arbitrary response objects cannot execute attribute hooks" in operator_guide


def test_sprint_691_documents_servicenow_oauth_response_status_boundary() -> None:
    change_log = Path("docs/sprints/sprint-691-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow OAuth response status boundary" in change_log
    assert "4 failing-first ServiceNow OAuth response assertions" in change_log
    assert "client_secret=oauth-response-object-secret" in change_log
    assert "client_secret=oauth-status-code-secret" in change_log
    assert "ServiceNow OAuth token responses must be exact `HttpResponse` objects" in (
        operator_guide
    )
    assert "OAuth status codes must be exact integers in the `100..599` range" in (
        operator_guide
    )


def test_sprint_692_documents_servicenow_oauth_body_boundary() -> None:
    change_log = Path("docs/sprints/sprint-692-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow OAuth response body exact-dictionary boundary" in change_log
    assert "2 failing-first ServiceNow OAuth body assertions" in change_log
    assert "client_secret=oauth-json-body-secret" in change_log
    assert "client_secret=oauth-json-dict-secret" in change_log
    assert "ServiceNow OAuth response bodies must be exact dictionaries" in operator_guide
    assert "dict subclasses cannot override token lookup" in operator_guide


def test_sprint_693_documents_servicenow_api_body_boundary() -> None:
    change_log = Path("docs/sprints/sprint-693-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow API response body exact-dictionary boundary" in change_log
    assert "2 failing-first ServiceNow API response-body assertions" in change_log
    assert "client_secret=servicenow-response-body-secret" in change_log
    assert "client_secret=servicenow-response-dict-secret" in change_log
    assert "Successful ServiceNow API response bodies must be exact dictionaries" in (
        operator_guide
    )
    assert "shared response-body helper rejects mapping objects and dict subclasses" in (
        operator_guide
    )


def test_sprint_694_documents_servicenow_api_response_status_boundary() -> None:
    change_log = Path("docs/sprints/sprint-694-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow API response status boundary" in change_log
    assert "4 failing-first ServiceNow API response-status assertions" in change_log
    assert "client_secret=servicenow-api-response-object-secret" in change_log
    assert "client_secret=servicenow-api-status-code-secret" in change_log
    assert "Successful ServiceNow API responses must be exact `HttpResponse` objects" in (
        operator_guide
    )
    assert "ServiceNow API status codes must be exact integers in the `100..599` range" in (
        operator_guide
    )


def test_sprint_695_documents_servicenow_api_error_body_top_level_boundary() -> None:
    change_log = Path("docs/sprints/sprint-695-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow API error body top-level exact-dictionary boundary" in change_log
    assert "1 failing-first ServiceNow API error-body assertion" in change_log
    assert "client_secret=servicenow-error-body-items-secret" in change_log
    assert "ServiceNow API error diagnostic bodies must be exact dictionaries" in (
        operator_guide
    )
    assert "top-level dict subclasses collapse to `[non-json value]`" in operator_guide


def test_sprint_696_documents_servicenow_result_body_boundary() -> None:
    change_log = Path("docs/sprints/sprint-696-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow Table API result body exact-dictionary boundary" in change_log
    assert "3 failing-first ServiceNow result-body assertions" in change_log
    assert "client_secret=servicenow-result-body-secret" in change_log
    assert "client_secret=servicenow-result-dict-secret" in change_log
    assert "client_secret=servicenow-result-object-dict-secret" in change_log
    assert "ServiceNow Table API result bodies must be exact dictionaries" in operator_guide
    assert "result extraction rejects mapping objects and dict subclasses" in operator_guide


def test_sprint_697_documents_servicenow_table_api_status_boundary() -> None:
    change_log = Path("docs/sprints/sprint-697-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow Table API response status boundary" in change_log
    assert "4 failing-first ServiceNow Table API response-status assertions" in change_log
    assert "client_secret=servicenow-table-response-object-secret" in change_log
    assert "client_secret=servicenow-table-status-code-secret" in change_log
    assert "ServiceNow Table API responses must pass the shared exact response/status boundary" in (
        operator_guide
    )
    assert "regular Table API methods no longer branch directly on `response.status_code`" in (
        operator_guide
    )


def test_sprint_698_documents_servicenow_cicd_probe_response_boundary() -> None:
    change_log = Path("docs/sprints/sprint-698-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow CICD probe response boundary" in change_log
    assert "6 failing-first ServiceNow CICD probe response assertions" in change_log
    assert "client_secret=servicenow-probe-response-object-secret" in change_log
    assert "client_secret=servicenow-probe-status-code-secret" in change_log
    assert "client_secret=servicenow-probe-body-secret" in change_log
    assert "client_secret=servicenow-probe-dict-secret" in change_log
    assert "ServiceNow CICD probe responses are observational but still boundary-checked" in (
        operator_guide
    )
    assert "valid HTTP error statuses remain returned as probe data" in operator_guide


def test_sprint_699_documents_servicenow_api_error_status_prevalidation() -> None:
    change_log = Path("docs/sprints/sprint-699-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow API error formatter prevalidated-status boundary" in change_log
    assert "2 failing-first ServiceNow API error-formatter assertions" in change_log
    assert "client_secret=servicenow-error-status-secret" in change_log
    assert "ServiceNow API error formatting requires a prevalidated integer status code" in (
        operator_guide
    )
    assert "the formatter no longer falls back to `response.status_code`" in operator_guide


def test_sprint_700_documents_servicenow_result_payload_exact_container_boundary() -> None:
    change_log = Path("docs/sprints/sprint-700-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow result payload exact-container boundary" in change_log
    assert "3 failing-first ServiceNow result-container assertions" in change_log
    assert "client_secret=servicenow-result-list-secret" in change_log
    assert "client_secret=servicenow-result-record-secret" in change_log
    assert "client_secret=servicenow-result-object-secret" in change_log
    assert "ServiceNow Table API `result` payloads are validated at the container boundary" in (
        operator_guide
    )
    assert "Result lists must be exact `list` instances" in operator_guide


def test_sprint_701_documents_servicenow_mutation_field_body_exact_dict_boundary() -> None:
    change_log = Path("docs/sprints/sprint-701-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow mutation field-body exact-dict boundary" in change_log
    assert "2 failing-first ServiceNow field-body assertions" in change_log
    assert "client_secret=servicenow-field-body-secret" in change_log
    assert "client_secret=servicenow-upsert-field-body-secret" in change_log
    assert (
        "ServiceNow Table API mutation field bodies are validated before request construction"
        in operator_guide
    )
    assert "before field-name sanitization, OAuth token acquisition, lookup queries" in (
        operator_guide
    )


def test_sprint_702_documents_servicenow_lookup_body_exact_dict_boundary() -> None:
    change_log = Path("docs/sprints/sprint-702-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow lookup body exact-dict boundary" in change_log
    assert "2 failing-first ServiceNow lookup-body assertions" in change_log
    assert "client_secret=servicenow-lookup-body-secret" in change_log
    assert "client_secret=servicenow-upsert-lookup-body-secret" in change_log
    assert "ServiceNow Table API lookup bodies are also validated before query construction" in (
        operator_guide
    )
    assert "before lookup key/value sanitization, OAuth token acquisition, GET requests" in (
        operator_guide
    )


def test_sprint_703_documents_servicenow_field_list_exact_list_boundary() -> None:
    change_log = Path("docs/sprints/sprint-703-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow field-list exact-list boundary" in change_log
    assert "1 failing-first ServiceNow field-list assertion" in change_log
    assert "client_secret=servicenow-field-list-secret" in change_log
    assert "ServiceNow Table API `sysparm_fields` lists are validated" in operator_guide
    assert (
        "before field-name sanitization, OAuth token acquisition, or GET request construction"
        in operator_guide
    )


def test_sprint_704_documents_servicenow_result_limit_exact_int_boundary() -> None:
    change_log = Path("docs/sprints/sprint-704-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow result-limit exact-int boundary" in change_log
    assert "1 failing-first ServiceNow result-limit assertion" in change_log
    assert "client_secret=servicenow-result-limit-lt-secret" in change_log
    assert "client_secret=servicenow-result-limit-str-secret" in change_log
    assert "ServiceNow Table API result limits are validated before query construction" in (
        operator_guide
    )
    assert "require `limit` to be an exact integer in the supported range" in operator_guide


def test_sprint_705_documents_servicenow_dictionary_max_length_exact_int_boundary() -> None:
    change_log = Path("docs/sprints/sprint-705-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow dictionary max-length exact-int boundary" in change_log
    assert "1 failing-first ServiceNow dictionary max-length assertion" in change_log
    assert "client_secret=servicenow-max-length-lt-secret" in change_log
    assert "client_secret=servicenow-max-length-str-secret" in change_log
    assert "ServiceNow dictionary field max lengths are validated" in operator_guide
    assert "requires `max_length`, when supplied, to be an exact integer" in operator_guide


def test_sprint_706_documents_servicenow_lookup_response_scalar_exact_type_boundary() -> None:
    change_log = Path("docs/sprints/sprint-706-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow lookup response scalar exact-type boundary" in change_log
    assert "1 failing-first ServiceNow lookup-response assertion" in change_log
    assert "client_secret=servicenow-lookup-response-int-secret" in change_log
    assert "ServiceNow lookup response text is validated before reuse" in operator_guide
    assert "accepts only null, exact strings, exact booleans, and exact integers" in operator_guide


def test_sprint_707_documents_servicenow_transport_query_params_exact_dict_boundary() -> None:
    change_log = Path("docs/sprints/sprint-707-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport query-params exact-dict boundary" in change_log
    assert "1 failing-first ServiceNow transport query-param assertion" in change_log
    assert "client_secret=servicenow-query-params-len-secret" in change_log
    assert "client_secret=servicenow-query-params-items-secret" in change_log
    assert "ServiceNow transport query parameters are validated before URL construction" in (
        operator_guide
    )
    assert "requires `HttpRequest.params` to be an exact dictionary" in operator_guide


def test_sprint_708_documents_servicenow_transport_body_exact_dict_boundary() -> None:
    change_log = Path("docs/sprints/sprint-708-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport request-body exact-dict boundary" in change_log
    assert "1 failing-first ServiceNow transport body assertion" in change_log
    assert "client_secret=servicenow-body-len-secret" in change_log
    assert "client_secret=servicenow-body-items-secret" in change_log
    assert "ServiceNow transport request bodies are validated before body encoding" in (
        operator_guide
    )
    assert "requires `HttpRequest.body` to be an exact dictionary" in operator_guide


def test_sprint_709_documents_servicenow_transport_headers_exact_dict_boundary() -> None:
    change_log = Path("docs/sprints/sprint-709-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport headers exact-dict boundary" in change_log
    assert "1 failing-first ServiceNow transport headers assertion" in change_log
    assert "client_secret=servicenow-headers-items-secret" in change_log
    assert "client_secret=servicenow-headers-get-secret" in change_log
    assert "ServiceNow transport headers are validated before request construction" in (
        operator_guide
    )
    assert "requires `HttpRequest.headers` to be an exact dictionary" in operator_guide


def test_sprint_710_documents_servicenow_transport_body_bytes_exact_bytes_boundary() -> None:
    change_log = Path("docs/sprints/sprint-710-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport body-bytes exact-bytes boundary" in change_log
    assert "1 failing-first ServiceNow transport body-bytes assertion" in change_log
    assert "client_secret=servicenow-body-bytes-secret" in change_log
    assert "ServiceNow transport raw body bytes are validated before request construction" in (
        operator_guide
    )
    assert "requires `HttpRequest.body_bytes` to be exact bytes" in operator_guide


def test_sprint_711_documents_servicenow_transport_form_body_scalar_boundary() -> None:
    change_log = Path("docs/sprints/sprint-711-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport form body scalar boundary" in change_log
    assert "2 failing-first ServiceNow transport form body assertions" in change_log
    assert "client_secret=servicenow-form-key-secret" in change_log
    assert "client_secret=servicenow-form-value-secret" in change_log
    assert "ServiceNow transport form request bodies are validated before URL encoding" in (
        operator_guide
    )
    assert "exact string keys and exact string values" in operator_guide


def test_sprint_712_documents_servicenow_transport_json_body_exact_json_boundary() -> None:
    change_log = Path("docs/sprints/sprint-712-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport JSON body exact-JSON boundary" in change_log
    assert "2 failing-first ServiceNow transport JSON body assertions" in change_log
    assert "client_secret=servicenow-json-key-secret" in change_log
    assert "client_secret=servicenow-json-value-secret" in change_log
    assert "ServiceNow transport JSON request bodies are validated before serialization" in (
        operator_guide
    )
    assert "`ServiceNow JSON request body contains non-JSON values`" in operator_guide


def test_sprint_713_documents_servicenow_transport_json_body_recursion_boundary() -> None:
    change_log = Path("docs/sprints/sprint-713-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport JSON body recursion boundary" in change_log
    assert "2 failing-first ServiceNow transport JSON recursion assertions" in change_log
    assert "contains circular references" in change_log
    assert "too deeply nested" in change_log
    assert "ServiceNow transport JSON request bodies are cycle-safe and depth-bounded" in (
        operator_guide
    )
    assert "`ServiceNow JSON request body contains circular references`" in operator_guide
    assert "`ServiceNow JSON request body is too deeply nested`" in operator_guide


def test_sprint_714_documents_servicenow_transport_method_url_boundary() -> None:
    change_log = Path("docs/sprints/sprint-714-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport method and URL boundary" in change_log
    assert "2 failing-first ServiceNow transport method/URL assertions" in change_log
    assert "client_secret=servicenow-method-upper-secret" in change_log
    assert "client_secret=servicenow-url-encode-secret" in change_log
    assert "ServiceNow transport methods and URLs are validated before request construction" in (
        operator_guide
    )
    assert "`ServiceNow request method is unsafe`" in operator_guide
    assert "`ServiceNow request URL is unsafe`" in operator_guide


def test_sprint_715_documents_servicenow_transport_header_scalar_boundary() -> None:
    change_log = Path("docs/sprints/sprint-715-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport header scalar boundary" in change_log
    assert "2 failing-first ServiceNow transport header scalar assertions" in change_log
    assert "client_secret=servicenow-header-key-title-secret" in change_log
    assert "client_secret=servicenow-header-value-title-secret" in change_log
    assert (
        "ServiceNow transport header keys and values are validated before request construction"
        in operator_guide
    )
    assert (
        "`ServiceNow request headers must contain exact string keys and values`"
        in operator_guide
    )


def test_sprint_716_documents_servicenow_transport_query_scalar_boundary() -> None:
    change_log = Path("docs/sprints/sprint-716-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport query scalar boundary" in change_log
    assert "2 failing-first ServiceNow transport query scalar assertions" in change_log
    assert "client_secret=servicenow-query-key-secret" in change_log
    assert "client_secret=servicenow-query-value-secret" in change_log
    assert (
        "ServiceNow transport query parameter keys and values are validated before URL encoding"
        in operator_guide
    )
    assert (
        "`ServiceNow query params must contain exact string keys and values`"
        in operator_guide
    )


def test_sprint_717_documents_servicenow_transport_response_status_boundary() -> None:
    change_log = Path("docs/sprints/sprint-717-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport response status boundary" in change_log
    assert "2 failing-first ServiceNow transport response status assertions" in change_log
    assert "client_secret=servicenow-success-status-lt-secret" in change_log
    assert "client_secret=servicenow-http-error-code-gt-secret" in change_log
    assert (
        "ServiceNow transport response status values are validated before HttpResponse construction"
        in operator_guide
    )
    assert (
        "`ServiceNow transport response status must be an exact HTTP status code`"
        in operator_guide
    )


def test_sprint_718_documents_servicenow_transport_timeout_boundary() -> None:
    change_log = Path("docs/sprints/sprint-718-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport timeout boundary" in change_log
    assert "2 failing-first ServiceNow transport timeout assertions" in change_log
    assert "client_secret=servicenow-timeout-float-secret" in change_log
    assert "ServiceNow transport timeout values are validated before opener execution" in (
        operator_guide
    )
    assert (
        "`ServiceNow transport timeout must be a finite positive number`"
        in operator_guide
    )


def test_sprint_719_documents_servicenow_transport_response_body_bytes_boundary() -> None:
    change_log = Path("docs/sprints/sprint-719-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport response body bytes boundary" in change_log
    assert "2 failing-first ServiceNow transport response body bytes assertions" in change_log
    assert "client_secret=servicenow-success-body-decode-secret" in change_log
    assert "client_secret=servicenow-error-body-decode-secret" in change_log
    assert "ServiceNow transport response body reads are validated before decoding" in (
        operator_guide
    )
    assert "`ServiceNow transport response body must be exact bytes`" in operator_guide


def test_sprint_720_documents_servicenow_transport_network_error_boundary() -> None:
    change_log = Path("docs/sprints/sprint-720-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport network error boundary" in change_log
    assert "2 failing-first ServiceNow transport network error assertions" in change_log
    assert "client_secret=servicenow-url-error-reason-secret" in change_log
    assert "client_secret=servicenow-os-error-secret" in change_log
    assert "ServiceNow transport network failures are wrapped before leaving the transport" in (
        operator_guide
    )
    assert "`ServiceNow transport request failed`" in operator_guide


def test_sprint_721_documents_servicenow_transport_status_before_body_boundary() -> None:
    change_log = Path("docs/sprints/sprint-721-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport status-before-body boundary" in change_log
    assert "2 failing-first ServiceNow transport status-before-body assertions" in change_log
    assert "client_secret=servicenow-success-body-read-secret" in change_log
    assert "client_secret=servicenow-error-body-read-secret" in change_log
    assert "ServiceNow transport response status is validated before body reads" in operator_guide
    assert (
        "`ServiceNow transport response status must be an exact HTTP status code`"
        in operator_guide
    )


def test_sprint_722_documents_servicenow_transport_status_attribute_boundary() -> None:
    change_log = Path("docs/sprints/sprint-722-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport status attribute boundary" in change_log
    assert "2 failing-first ServiceNow transport status attribute assertions" in change_log
    assert "client_secret=servicenow-success-status-attr-secret" in change_log
    assert "client_secret=servicenow-http-error-code-attr-secret" in change_log
    assert "ServiceNow transport response status attributes are read through a safe boundary" in (
        operator_guide
    )
    assert (
        "`ServiceNow transport response status must be an exact HTTP status code`"
        in operator_guide
    )


def test_sprint_723_documents_servicenow_transport_body_read_boundary() -> None:
    change_log = Path("docs/sprints/sprint-723-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport response body read boundary" in change_log
    assert "2 failing-first ServiceNow transport response body read assertions" in change_log
    assert "client_secret=servicenow-success-body-read-error-secret" in change_log
    assert "client_secret=servicenow-error-body-read-error-secret" in change_log
    assert "ServiceNow transport response body reads execute through a safe boundary" in (
        operator_guide
    )
    assert "`ServiceNow transport response body read failed`" in operator_guide


def test_sprint_724_documents_servicenow_transport_response_context_boundary() -> None:
    change_log = Path("docs/sprints/sprint-724-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport response context boundary" in change_log
    assert "2 failing-first ServiceNow transport response context assertions" in change_log
    assert "client_secret=servicenow-success-enter-secret" in change_log
    assert "client_secret=servicenow-success-exit-secret" in change_log
    assert "ServiceNow transport response context managers execute through a safe boundary" in (
        operator_guide
    )
    assert "`ServiceNow transport response context failed`" in operator_guide


def test_sprint_725_documents_servicenow_transport_opener_boundary() -> None:
    change_log = Path("docs/sprints/sprint-725-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport opener boundary" in change_log
    assert "2 failing-first ServiceNow transport opener assertions" in change_log
    assert "client_secret=servicenow-open-runtime-secret" in change_log
    assert "client_secret=servicenow-open-attr-secret" in change_log
    assert "ServiceNow transport opener execution runs through a safe boundary" in (
        operator_guide
    )
    assert "`ServiceNow transport request failed`" in operator_guide


def test_sprint_726_documents_servicenow_transport_opener_construction_boundary() -> None:
    change_log = Path("docs/sprints/sprint-726-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport opener construction boundary" in change_log
    assert "1 failing-first ServiceNow transport opener construction assertion" in change_log
    assert "client_secret=servicenow-build-opener-secret" in change_log
    assert "ServiceNow transport opener construction runs through a safe boundary" in (
        operator_guide
    )
    assert "`ServiceNow transport request failed`" in operator_guide


def test_sprint_727_documents_servicenow_transport_request_construction_boundary() -> None:
    change_log = Path("docs/sprints/sprint-727-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport request construction boundary" in change_log
    assert "1 failing-first ServiceNow transport request construction assertion" in change_log
    assert "client_secret=servicenow-request-construction-secret" in change_log
    assert "ServiceNow transport request construction runs through a safe boundary" in (
        operator_guide
    )
    assert "`ServiceNow transport request failed`" in operator_guide


def test_sprint_728_documents_servicenow_transport_url_encoding_boundary() -> None:
    change_log = Path("docs/sprints/sprint-728-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport URL encoding boundary" in change_log
    assert "2 failing-first ServiceNow transport URL encoding assertions" in change_log
    assert "client_secret=servicenow-query-urlencode-secret" in change_log
    assert "client_secret=servicenow-form-urlencode-secret" in change_log
    assert "ServiceNow transport URL encoding runs through a safe boundary" in operator_guide
    assert "`ServiceNow transport URL encoding failed`" in operator_guide


def test_sprint_729_documents_servicenow_transport_json_encoding_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-729-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport JSON encoding cause boundary" in change_log
    assert "3 failing-first ServiceNow transport JSON encoding cause assertions" in change_log
    assert "bad_score" in change_log
    assert "HostileJsonBodyKey" in change_log
    assert "HostileJsonBodyValue" in change_log
    assert "ServiceNow transport JSON encoding diagnostics do not retain unsafe causes" in (
        operator_guide
    )
    assert "`ServiceNow JSON request body contains non-JSON values`" in operator_guide


def test_sprint_730_documents_servicenow_transport_success_json_parse_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-730-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow transport successful-response JSON parse cause boundary" in change_log
    assert "3 failing-first ServiceNow successful-response JSON parse cause assertions" in (
        change_log
    )
    assert "access_token" in change_log
    assert "client_secret" in change_log
    assert "score" in change_log
    assert "ServiceNow transport successful-response JSON parse diagnostics do not retain" in (
        operator_guide
    )
    assert "`ServiceNow API response body is not valid JSON`" in operator_guide


def test_sprint_731_documents_servicenow_attachment_read_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-731-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow attachment read cause boundary" in change_log
    assert "3 failing-first ServiceNow attachment read cause assertions" in change_log
    assert "oversized.xml" in change_log
    assert "attachment-client_secret=path-secret.xml" in change_log
    assert "spoofed-message" in change_log
    assert "ServiceNow attachment read diagnostics do not retain unsafe causes" in operator_guide
    assert "`ServiceNow attachment file must be a regular file`" in operator_guide


def test_sprint_732_documents_dotenv_read_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-732-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow dotenv read cause boundary" in change_log
    assert "2 failing-first ServiceNow dotenv read cause assertions" in change_log
    assert "client_secret=dotenv-link-secret.env" in change_log
    assert "client_secret=dotenv-utf8-secret.env" in change_log
    assert "ServiceNow dotenv read diagnostics do not retain unsafe causes" in operator_guide
    assert "`dotenv_invalid_utf8`" in operator_guide


def test_sprint_733_documents_project_config_read_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-733-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Project config read cause boundary" in change_log
    assert "2 failing-first project config read cause assertions" in change_log
    assert "client_secret=config-link-secret.toml" in change_log
    assert "client_secret=config-utf8-secret.toml" in change_log
    assert "Project config read diagnostics do not retain unsafe causes" in operator_guide
    assert "`project_config_invalid_utf8`" in operator_guide


def test_sprint_734_documents_cli_json_input_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-734-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "CLI JSON input cause boundary" in change_log
    assert "3 failing-first CLI JSON input cause assertions" in change_log
    assert "client_secret=json-link-secret.json" in change_log
    assert "client_secret=json-utf8-secret.json" in change_log
    assert "client_secret=json-nan-secret.json" in change_log
    assert "CLI JSON input diagnostics do not retain unsafe causes" in operator_guide
    assert "`json_input_invalid_json`" in operator_guide


def test_sprint_735_documents_stable_artifact_hash_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-735-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Stable artifact hash cause boundary" in change_log
    assert "3 failing-first stable artifact hash cause assertions" in change_log
    assert "bad_score" in change_log
    assert "StringifiesSecret" in change_log
    assert "HostileHashText" in change_log
    assert "Stable artifact hash diagnostics do not retain unsafe causes" in operator_guide
    assert "`artifact hash payload contains non-JSON values`" in operator_guide


def test_sprint_736_documents_context_dossier_dto_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-736-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Context dossier DTO cause boundary" in change_log
    assert "3 failing-first context dossier DTO cause assertions" in change_log
    assert "confidence" in change_log
    assert "SecretBearingObject" in change_log
    assert "HostileContextText" in change_log
    assert "Context dossier DTO diagnostics do not retain unsafe causes" in operator_guide
    assert "`context dossier DTO payload contains non-JSON values`" in operator_guide


def test_sprint_737_documents_model_fulfillment_artifact_payload_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-737-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model fulfillment artifact payload cause boundary" in change_log
    assert "3 failing-first model fulfillment artifact payload cause assertions" in change_log
    assert "weight" in change_log
    assert "SecretBearingObject" in change_log
    assert "HostileModelArtifactText" in change_log
    assert "Model fulfillment artifact payload diagnostics do not retain unsafe causes" in (
        operator_guide
    )
    assert "`model fulfillment artifact payload contains non-JSON values`" in operator_guide


def test_sprint_738_documents_provider_contract_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-738-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider contract cause boundary" in change_log
    assert "7 failing-first provider contract cause assertions" in change_log
    assert "HostilePayload" in change_log
    assert "SneakyKey" in change_log
    assert "provider-response-secret" in change_log
    assert "Provider contract diagnostics do not retain unsafe causes" in operator_guide
    assert "`Model provider prompt payload contains unsupported JSON value types`" in (
        operator_guide
    )


def test_sprint_739_documents_capability_assessment_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-739-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Capability assessment cause boundary" in change_log
    assert "6 failing-first capability assessment cause assertions" in change_log
    assert "guidance" in change_log
    assert "SecretBearingObject" in change_log
    assert "HostileIntentText" in change_log
    assert "Capability assessment diagnostics do not retain unsafe causes" in operator_guide
    assert "`automation intent payload contains non-JSON values`" in operator_guide


def test_sprint_740_documents_operational_store_jsonb_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-740-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Operational store JSONB cause boundary" in change_log
    assert "6 failing-first operational store cause assertions" in change_log
    assert "bad_score" in change_log
    assert "StringifiesSecret" in change_log
    assert "HostileArtifactText" in change_log
    assert "HostileLifecycleText" in change_log
    assert "Operational store JSONB diagnostics do not retain unsafe causes" in operator_guide
    assert "`operational lifecycle event payload contains non-JSON values`" in operator_guide


def test_sprint_741_documents_runtime_worker_report_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-741-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime worker report cause boundary" in change_log
    assert "4 failing-first runtime worker report cause assertions" in change_log
    assert "idle" in change_log
    assert "StringifiesSecret" in change_log
    assert "HostileRuntimeReportText" in change_log
    assert "Runtime worker report diagnostics do not retain unsafe causes" in operator_guide
    assert "`runtime worker report contains non-JSON values`" in operator_guide


def test_sprint_742_documents_alert_webhook_payload_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-742-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert webhook payload cause boundary" in change_log
    assert "3 failing-first alert webhook payload cause assertions" in change_log
    assert "detail" in change_log
    assert "SecretBearingObject" in change_log
    assert "HostileAlertText" in change_log
    assert "Alert webhook payload diagnostics do not retain unsafe causes" in operator_guide
    assert "`alert webhook payload contains non-JSON values`" in operator_guide


def test_sprint_743_documents_implementation_packet_payload_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-743-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Implementation packet payload cause boundary" in change_log
    assert "6 failing-first implementation packet payload cause assertions" in change_log
    assert "risk_score" in change_log
    assert "SecretBearingObject" in change_log
    assert "HostilePacketText" in change_log
    assert "HostileRawPacketText" in change_log
    assert "Implementation packet payload diagnostics do not retain unsafe causes" in operator_guide
    assert "`implementation packet raw payload contains non-JSON values`" in operator_guide


def test_sprint_744_documents_artifact_dto_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-744-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Artifact DTO cause boundary" in change_log
    assert "3 failing-first artifact DTO cause assertions" in change_log
    assert "confidence" in change_log
    assert "SecretBearingObject" in change_log
    assert "HostileCandidateText" in change_log
    assert "Artifact DTO diagnostics do not retain unsafe causes" in operator_guide
    assert "`artifact DTO payload contains non-JSON values`" in operator_guide


def test_sprint_745_documents_artifact_json_output_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-745-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Artifact JSON output cause boundary" in change_log
    assert "1 failing-first artifact JSON output cause assertion" in change_log
    assert "bad_score" in change_log
    assert "artifact-secret" in change_log
    assert "Artifact JSON output diagnostics do not retain unsafe causes" in operator_guide
    assert "`artifact JSON payload contains non-finite numeric values`" in operator_guide


def test_sprint_746_documents_admin_artifact_payload_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-746-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin artifact payload cause boundary" in change_log
    assert "1 failing-first admin artifact payload cause assertion" in change_log
    assert "risk_score" in change_log
    assert "do-not-echo-this" in change_log
    assert "Admin artifact payload diagnostics do not retain unsafe causes" in operator_guide
    assert (
        "`admin artifact payload diagnostic contains non-finite numeric values`"
        in operator_guide
    )


def test_sprint_747_documents_flow_graph_hash_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-747-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Flow graph hash cause boundary" in change_log
    assert "1 failing-first Flow graph hash cause assertion" in change_log
    assert "private_value_marker" in change_log
    assert "do-not-echo-this" in change_log
    assert "Flow graph hash diagnostics do not retain unsafe causes" in operator_guide
    assert "`Flow graph node canonical state contains non-finite numeric values`" in (
        operator_guide
    )


def test_sprint_748_documents_flow_xml_shape_evidence_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-748-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Flow XML shape evidence cause boundary" in change_log
    assert "1 failing-first Flow XML shape evidence cause assertion" in change_log
    assert "Flow XML shape evidence is not valid XML" in change_log
    assert "Flow XML shape evidence diagnostics do not retain unsafe causes" in operator_guide
    assert "`Flow XML shape evidence is not valid XML`" in operator_guide


def test_sprint_749_documents_flow_graph_diff_operation_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-749-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Flow graph diff operation cause boundary" in change_log
    assert "1 failing-first Flow graph diff operation cause assertion" in change_log
    assert "client-secret-value" in change_log
    assert "Flow graph diff operation diagnostics do not retain unsafe causes" in operator_guide
    assert "`unsupported Flow graph diff operation`" in operator_guide


def test_sprint_750_documents_runtime_config_numeric_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-750-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime config numeric cause boundary" in change_log
    assert "2 failing-first runtime config numeric cause assertions" in change_log
    assert "client-secret-value" in change_log
    assert "Runtime config numeric diagnostics do not retain unsafe causes" in operator_guide
    assert "`runtime config raised unstringifiable UnstringifiableNumericRuntimeConfigError`" in (
        operator_guide
    )


def test_sprint_751_documents_runtime_openai_provider_setting_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-751-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime OpenAI provider setting cause boundary" in change_log
    assert "2 failing-first runtime OpenAI provider setting cause assertions" in change_log
    assert "openai-client-secret-value" in change_log
    assert "Runtime OpenAI provider setting diagnostics do not retain unsafe causes" in (
        operator_guide
    )
    assert "`OPENAI_API_KEY provider setting raised unstringifiable" in operator_guide


def test_sprint_752_documents_flow_graph_diff_payload_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-752-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Flow graph diff payload cause boundary" in change_log
    assert "2 failing-first Flow graph diff payload cause assertions" in change_log
    assert "StringifiesSecret" in change_log
    assert "do-not-echo-this" in change_log
    assert "Flow graph diff payload diagnostics do not retain unsafe causes" in operator_guide
    assert "`Flow graph diff contains a non-JSON payload value`" in operator_guide


def test_sprint_753_documents_public_web_transport_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-753-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Public web transport cause boundary" in change_log
    assert "2 failing-first public web transport cause assertions" in change_log
    assert "doc-secret" in change_log
    assert "Public web transport diagnostics do not retain unsafe causes" in operator_guide
    assert "`public documentation fetch failed`" in operator_guide


def test_sprint_754_documents_lifecycle_hmac_timestamp_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-754-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Lifecycle HMAC timestamp cause boundary" in change_log
    assert "1 failing-first lifecycle HMAC timestamp cause assertion" in change_log
    assert "5000-digit timestamp" in change_log
    assert "Lifecycle HMAC timestamp diagnostics do not retain unsafe causes" in operator_guide
    assert "`lifecycle webhook timestamp invalid`" in operator_guide


def test_sprint_755_documents_runtime_handler_redaction_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-755-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime handler redaction cause boundary" in change_log
    assert "1 failing-first runtime handler redaction cause assertion" in change_log
    assert "client-secret-value" in change_log
    assert "Runtime handler redaction diagnostics do not retain unsafe causes" in operator_guide
    assert "`handler raised unstringifiable _UnstringifiableRuntimeError`" in operator_guide


def test_sprint_756_documents_runtime_openai_provider_runtime_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-756-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime OpenAI provider runtime cause boundary" in change_log
    assert "2 failing-first runtime OpenAI provider runtime cause assertions" in change_log
    assert "openai-key" in change_log
    assert "Runtime OpenAI provider runtime diagnostics do not retain unsafe causes" in (
        operator_guide
    )
    assert "`Invalid OpenAI provider runtime settings:`" in operator_guide


def test_sprint_757_documents_artifact_filesystem_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-757-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Artifact filesystem cause boundary" in change_log
    assert "2 failing-first artifact filesystem cause assertions" in change_log
    assert "artifact already exists" in change_log
    assert "artifact path must be a regular file" in change_log
    assert "Artifact filesystem diagnostics do not retain unsafe causes" in operator_guide
    assert "`artifact already exists:`" in operator_guide


def test_sprint_758_documents_lifecycle_payload_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-758-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Lifecycle payload cause boundary" in change_log
    assert "2 failing-first lifecycle payload cause assertions" in change_log
    assert "invalid lifecycle webhook JSON" in change_log
    assert "extra_forbidden" in change_log
    assert "Lifecycle webhook payload diagnostics do not retain unsafe causes" in (
        operator_guide
    )
    assert "`invalid lifecycle webhook JSON`" in operator_guide


def test_sprint_759_documents_admin_not_found_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-759-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin not-found cause boundary" in change_log
    assert "3 failing-first admin not-found cause assertions" in change_log
    assert "artifact not found" in change_log
    assert "job not found" in change_log
    assert "Admin not-found diagnostics do not retain unsafe causes" in operator_guide
    assert "`artifact not found`" in operator_guide


def test_sprint_760_documents_anthropic_max_tokens_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-760-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Anthropic max-tokens cause boundary" in change_log
    assert "1 failing-first Anthropic provider config cause assertion" in change_log
    assert "ANTHROPIC_MAX_TOKENS" in change_log
    assert "ASCII base-10 digits" in change_log
    assert "Anthropic max-token diagnostics do not retain unsafe causes" in operator_guide
    assert "`ANTHROPIC_MAX_TOKENS` must parse as ASCII base-10 digits only" in (
        operator_guide
    )


def test_sprint_761_documents_runtime_worker_float_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-761-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime worker float cause boundary" in change_log
    assert "1 failing-first runtime worker float cause assertion" in change_log
    assert "JEDI_WORKER_IDLE_SLEEP_SECONDS" in change_log
    assert "runtime worker raised unstringifiable" in change_log
    assert "Runtime worker float diagnostics do not retain unsafe causes" in operator_guide
    assert "`runtime worker raised unstringifiable UnstringifiableWorkerFloatError`" in (
        operator_guide
    )


def test_sprint_762_documents_model_intent_validator_cause_boundary() -> None:
    change_log = Path("docs/sprints/sprint-762-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model intent validator cause boundary" in change_log
    assert "6 failing-first model intent validator cause assertions" in change_log
    assert "reference qualifier rejected" in change_log
    assert "condition rejected" in change_log
    assert "action rejected" in change_log
    assert "Model intent validator diagnostics do not retain unsafe causes" in operator_guide
    assert "`reference qualifier rejected`" in operator_guide


def test_sprint_763_documents_explicit_exception_cause_regression_gate() -> None:
    change_log = Path("docs/sprints/sprint-763-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Explicit exception cause regression gate" in change_log
    assert "1 source-wide AST regression assertion" in change_log
    assert "`from None`" in change_log
    assert "no named exception causes" in change_log
    assert "Explicit exception cause regression gate" in operator_guide
    assert "Every explicit source exception cause must be `from None`" in operator_guide


def test_sprint_764_documents_ci_verification_gate() -> None:
    change_log = Path("docs/sprints/sprint-764-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "CI verification gate" in change_log
    assert "2 failing-first CI workflow assertions" in change_log
    assert "pull_request" in change_log
    assert "branches: [master]" in change_log
    assert "CI verification gate" in operator_guide
    assert "`python3 -m pytest --cov=jedi_devproject" in operator_guide


def test_sprint_765_documents_hosted_container_port_and_healthcheck_contract() -> None:
    change_log = Path("docs/sprints/sprint-765-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Hosted container port and healthcheck contract" in change_log
    assert "3 failing-first container deployment assertions" in change_log
    assert "`${PORT:-8000}`" in change_log
    assert "`GET /health`" in change_log
    assert "The hosted API image binds to `${PORT:-8000}`" in operator_guide
    assert "container healthcheck calls `GET /health`" in operator_guide


def test_sprint_766_documents_docker_context_secret_exclusion_contract() -> None:
    change_log = Path("docs/sprints/sprint-766-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Docker context secret exclusion contract" in change_log
    assert "2 failing-first Docker context assertions" in change_log
    assert "`.env*`" in change_log
    assert "`!.env.example`" in change_log
    assert "Docker build context excludes `.env*`" in operator_guide
    assert "keeps `!.env.example`" in operator_guide


def test_sprint_767_documents_hosted_process_separation_contract() -> None:
    change_log = Path("docs/sprints/sprint-767-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Hosted process separation contract" in change_log
    assert "3 failing-first hosted deployment assertions" in change_log
    assert "`railway.json`" in change_log
    assert "`deploy/railway/worker-service.json`" in change_log
    assert "Hosted Railway Process Split" in operator_guide
    assert "The worker service must not expose a public HTTP process" in operator_guide


def test_sprint_768_documents_runtime_role_startup_boundary() -> None:
    change_log = Path("docs/sprints/sprint-768-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime role startup boundary" in change_log
    assert "7 failing-first runtime role assertions" in change_log
    assert "`JEDI_RUNTIME_ROLE=api`" in change_log
    assert "`JEDI_RUNTIME_ROLE=worker`" in change_log
    assert "Runtime Role Boundary" in operator_guide
    assert "`JEDI_RUNTIME_ROLE=api`" in operator_guide
    assert "`JEDI_RUNTIME_ROLE=worker`" in operator_guide


def test_sprint_769_documents_operational_store_schema_readiness() -> None:
    change_log = Path("docs/sprints/sprint-769-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Operational store schema readiness" in change_log
    assert "5 failing-first schema readiness assertions" in change_log
    assert "`verify_schema_ready()`" in change_log
    assert "`operational_store_schema`" in change_log
    assert "Operational store schema readiness" in operator_guide
    assert "`GET /ready` checks packaged migration tables" in operator_guide


def test_sprint_1010_documents_operational_store_schema_readiness_row_guard() -> None:
    change_log = Path("docs/sprints/sprint-1010-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Operational store schema readiness row guard" in change_log
    assert "`verify_schema_ready()`" in change_log
    assert "`_schema_readiness_table_name()`" in change_log
    assert "operational store schema readiness row contains non-JSON value" in change_log
    assert (
        "1 failing-first operational-store schema readiness row subclass assertion"
        in change_log
    )
    assert "Operational store schema readiness rows are exact-shape guarded" in (
        operator_guide
    )
    assert "`information_schema.tables`" in operator_guide
    assert "before readiness-table matching, API readiness responses" in operator_guide
    assert (
        "`test_verify_schema_ready_rejects_schema_row_subclass_without_leak`"
        in change_log
    )


def test_sprint_1011_documents_operational_store_surface_maturity_row_guard() -> None:
    change_log = Path("docs/sprints/sprint-1011-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Operational store surface maturity row guard" in change_log
    assert "`builder_maturity_evidence_for_surface()`" in change_log
    assert "`_surface_maturity_count()`" in change_log
    assert "operational store surface maturity row contains non-JSON value" in change_log
    assert (
        "1 failing-first operational-store surface maturity row subclass assertion"
        in change_log
    )
    assert "Operational store surface maturity evidence rows are exact-shape guarded" in (
        operator_guide
    )
    assert "`samples`, `successes`, and `failures` must be exact integers" in (
        operator_guide
    )
    assert "before maturity scoring, automation-threshold checks" in operator_guide
    assert (
        "`test_surface_maturity_evidence_rejects_row_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_surface_maturity_evidence_rejects_count_object_without_leak`"
        in change_log
    )


def test_sprint_1012_documents_operational_store_read_row_collection_guard() -> None:
    change_log = Path("docs/sprints/sprint-1012-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Operational store read-row collection guard" in change_log
    assert "`_operational_read_rows()`" in change_log
    assert "`recent_lifecycle_events()`" in change_log
    assert "operational store read rows contain non-JSON value" in change_log
    assert (
        "1 failing-first operational-store read-row collection subclass assertion"
        in change_log
    )
    assert "Operational store list read rows are exact containers" in operator_guide
    assert "`recent_fulfillment_jobs()`" in operator_guide
    assert "before row iteration, Pydantic model validation" in operator_guide
    assert (
        "`test_recent_lifecycle_events_rejects_row_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_recent_lifecycle_events_rejects_row_subclass_without_leak`"
        in change_log
    )


def test_sprint_1013_documents_operational_store_single_read_row_guard() -> None:
    change_log = Path("docs/sprints/sprint-1013-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Operational store single-row read guard" in change_log
    assert "`_operational_read_row()`" in change_log
    assert "`enqueue_fulfillment_job()`" in change_log
    assert "operational store read row contains non-JSON value" in change_log
    assert (
        "1 failing-first operational-store single-row subclass assertion" in change_log
    )
    assert "Operational store single read rows are exact dictionaries" in operator_guide
    assert "returned `fetch_one()` rows through `_operational_read_row()`" in operator_guide
    assert "before row indexing, Pydantic model validation" in operator_guide
    assert (
        "`test_enqueue_fulfillment_job_rejects_row_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_record_json_artifact_rejects_blob_row_subclass_before_indexing_without_leak`"
        in change_log
    )


def test_sprint_1014_documents_operational_store_scalar_read_guard() -> None:
    change_log = Path("docs/sprints/sprint-1014-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Operational store scalar read guard" in change_log
    assert "`_operational_read_int()`" in change_log
    assert "operational store read scalar is unsafe" in change_log
    assert "1 failing-first artifact blob id object assertion" in change_log
    assert "1 failing-first retention deleted-count object assertion" in change_log
    assert "Operational store scalar reads are exact integer guarded" in operator_guide
    assert "Artifact blob id extraction requires an exact positive integer" in (
        operator_guide
    )
    assert "retention prune count reads require exact non-negative integers" in (
        operator_guide
    )
    assert "before `int()` coercion, artifact reference insertion" in operator_guide
    assert (
        "`test_record_json_artifact_rejects_blob_id_object_before_int_conversion`"
        in change_log
    )
    assert (
        "`test_prune_expired_records_rejects_count_object_without_leak`"
        in change_log
    )


def test_sprint_1015_documents_operational_store_record_hydration_guard() -> None:
    change_log = Path("docs/sprints/sprint-1015-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Operational store record hydration guard" in change_log
    assert "`LifecycleEventRecord`" in change_log
    assert "`FulfillmentJobRecord`" in change_log
    assert "operational store record scalar is unsafe" in change_log
    assert "operational store record payload is unsafe" in change_log
    assert "1 failing-first operational-store record text subclass assertion" in (
        change_log
    )
    assert "Operational store record hydration is exact-scalar guarded" in (
        operator_guide
    )
    assert "exact JSON dictionaries/lists/scalars" in operator_guide
    assert "before Pydantic coercion, model serialization" in operator_guide
    assert (
        "`test_fulfillment_job_record_rejects_string_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_lifecycle_event_record_rejects_payload_subclass_without_leak`"
        in change_log
    )


def test_sprint_1016_documents_operational_store_payload_traversal_guard() -> None:
    change_log = Path("docs/sprints/sprint-1016-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Operational store payload traversal guard" in change_log
    assert "`_ensure_operational_record_payload_json_safe()`" in change_log
    assert "`MAX_OPERATIONAL_RECORD_PAYLOAD_DEPTH`" in change_log
    assert "operational store record payload is unsafe" in change_log
    assert "1 failing-first cyclic operational-store payload assertion" in change_log
    assert "1 failing-first over-depth operational-store payload assertion" in (
        change_log
    )
    assert "Operational store record payload traversal is cycle-safe" in operator_guide
    assert "caps traversal at 32 levels" in operator_guide
    assert "before recursive validation, Pydantic model hydration" in operator_guide
    assert (
        "`test_lifecycle_event_record_rejects_cyclic_payload_without_leak`"
        in change_log
    )
    assert (
        "`test_lifecycle_event_record_rejects_excessively_nested_payload_without_leak`"
        in change_log
    )


def test_sprint_1017_documents_retention_prune_report_hydration_guard() -> None:
    change_log = Path("docs/sprints/sprint-1017-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retention prune report hydration guard" in change_log
    assert "`RetentionClassPruneResult`" in change_log
    assert "`RetentionPruneReport`" in change_log
    assert "operational store retention report scalar is unsafe" in change_log
    assert "operational store retention report results are unsafe" in change_log
    assert "1 failing-first retention report text subclass assertion" in change_log
    assert "Retention prune report hydration is exact-shape guarded" in operator_guide
    assert "exact lists of already-validated `RetentionClassPruneResult` objects" in (
        operator_guide
    )
    assert "before Pydantic coercion, audit JSON rendering" in operator_guide
    assert (
        "`test_retention_prune_result_rejects_record_class_string_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_retention_prune_report_rejects_results_collection_subclass_without_leak`"
        in change_log
    )


def test_sprint_1018_documents_surface_maturity_evidence_record_guard() -> None:
    change_log = Path("docs/sprints/sprint-1018-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Surface maturity evidence record guard" in change_log
    assert "`SurfaceMaturityEvidenceRecord`" in change_log
    assert "operational store surface maturity record scalar is unsafe" in change_log
    assert (
        "1 failing-first surface maturity evidence text subclass assertion"
        in change_log
    )
    assert "Operational store surface maturity evidence records are exact-scalar guarded" in (
        operator_guide
    )
    assert "exact non-negative integer `samples`, `successes`, and `failures`" in (
        operator_guide
    )
    assert "before Pydantic coercion, maturity scoring" in operator_guide
    assert (
        "`test_surface_maturity_evidence_record_rejects_surface_string_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_surface_maturity_evidence_record_rejects_invalid_count_scalars`"
        in change_log
    )


def test_sprint_770_documents_operational_store_initialization_command() -> None:
    change_log = Path("docs/sprints/sprint-770-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Operational store initialization command" in change_log
    assert "3 failing-first initialization command assertions" in change_log
    assert "`init-operational-store`" in change_log
    assert "operational_store_schema_ready=true" in change_log
    assert "`init-operational-store`" in operator_guide
    assert "operational_store_schema_ready=true" in operator_guide


def test_sprint_771_documents_non_root_container_runtime() -> None:
    change_log = Path("docs/sprints/sprint-771-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Non-root container runtime" in change_log
    assert "3 failing-first non-root container assertions" in change_log
    assert "`USER jedi`" in change_log
    assert "`/app/artifacts`" in change_log
    assert "Container images run as `jedi`" in operator_guide
    assert "`USER jedi`" in operator_guide


def test_sprint_772_documents_container_audit_root_default() -> None:
    change_log = Path("docs/sprints/sprint-772-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Container audit-root default" in change_log
    assert "3 failing-first audit-root container assertions" in change_log
    assert "`JEDI_AUDIT_ROOT=/app/artifacts/audit`" in change_log
    assert "`/app/artifacts/audit`" in change_log
    assert "Container images default `JEDI_AUDIT_ROOT`" in operator_guide
    assert "`/app/artifacts/audit`" in operator_guide


def test_sprint_774_documents_compose_runtime_restart_policies() -> None:
    change_log = Path("docs/sprints/sprint-774-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Compose runtime restart policies" in change_log
    assert "3 failing-first compose restart assertions" in change_log
    assert "`restart: unless-stopped`" in change_log
    assert "`restart: on-failure`" in change_log
    assert "Local compose restart policies" in operator_guide
    assert "`postgres` uses `restart: unless-stopped`" in operator_guide


def test_sprint_775_documents_compose_role_specific_images() -> None:
    change_log = Path("docs/sprints/sprint-775-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Compose role-specific runtime images" in change_log
    assert "2 failing-first compose Dockerfile assertions" in change_log
    assert "`Dockerfile.worker`" in change_log
    assert "`JEDI_RUNTIME_ROLE=worker`" in change_log
    assert "Compose uses role-specific images" in operator_guide
    assert "`worker` builds from `Dockerfile.worker`" in operator_guide


def test_sprint_776_documents_compose_explicit_runtime_roles() -> None:
    change_log = Path("docs/sprints/sprint-776-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Compose explicit runtime roles" in change_log
    assert "2 failing-first compose runtime role assertions" in change_log
    assert "`JEDI_RUNTIME_ROLE=api`" in change_log
    assert "`JEDI_RUNTIME_ROLE=worker`" in change_log
    assert "Compose also declares service-level runtime roles" in operator_guide
    assert "`api` sets `JEDI_RUNTIME_ROLE=api`" in operator_guide


def test_sprint_777_documents_compose_postgres_password_externalization() -> None:
    change_log = Path("docs/sprints/sprint-777-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Compose Postgres password externalization" in change_log
    assert "4 failing-first compose credential assertions" in change_log
    assert "`JEDI_POSTGRES_PASSWORD`" in change_log
    assert "`postgresql://jedi:jedi@postgres:5432/jedi`" in change_log
    assert "Local compose requires `JEDI_POSTGRES_PASSWORD`" in operator_guide
    assert "`POSTGRES_PASSWORD` and `DATABASE_URL`" in operator_guide


def test_sprint_778_documents_compose_password_example_config() -> None:
    change_log = Path("docs/sprints/sprint-778-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Compose password example config" in change_log
    assert "3 failing-first env example assertions" in change_log
    assert "`.env.example`" in change_log
    assert "`JEDI_POSTGRES_PASSWORD=`" in change_log
    assert "The example env file includes `JEDI_POSTGRES_PASSWORD=`" in operator_guide


def test_sprint_779_documents_neutral_servicenow_example_targets() -> None:
    change_log = Path("docs/sprints/sprint-779-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Neutral ServiceNow example targets" in change_log
    assert "4 failing-first ServiceNow example target assertions" in change_log
    assert "`dev205693.service-now.com`" in change_log
    assert "`https://<instance>.service-now.com`" in change_log
    assert "Local configuration examples use neutral ServiceNow placeholders" in operator_guide


def test_sprint_780_documents_compose_split_servicenow_runtime_values() -> None:
    change_log = Path("docs/sprints/sprint-780-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Compose split ServiceNow runtime values" in change_log
    assert "6 failing-first split ServiceNow compose assertions" in change_log
    assert "`SERVICENOW_PM_INSTANCE_URL`" in change_log
    assert "`SERVICENOW_DEV_CLIENT_SECRET`" in change_log
    assert "Compose requires split ServiceNow PM/DEV values" in operator_guide
    assert "`SERVICENOW_INSTANCE_URL` remains a direct-runtime fallback" in operator_guide


def test_sprint_781_documents_compose_api_readiness_healthcheck() -> None:
    change_log = Path("docs/sprints/sprint-781-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Compose API readiness healthcheck" in change_log
    assert "8 failing-first compose readiness assertions" in change_log
    assert "`/ready`" in change_log
    assert "`docker compose ps`" in change_log
    assert "Compose API readiness healthcheck calls `GET /ready`" in operator_guide


def test_sprint_782_documents_docker_context_runtime_evidence_exclusion() -> None:
    change_log = Path("docs/sprints/sprint-782-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Docker context runtime evidence exclusion" in change_log
    assert "6 failing-first Docker context artifact assertions" in change_log
    assert "`.eventloom/`" in change_log
    assert "`coverage.xml`" in change_log
    assert "Docker build context also excludes local runtime evidence" in operator_guide


def test_sprint_783_documents_compose_runtime_privilege_reduction() -> None:
    change_log = Path("docs/sprints/sprint-783-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Compose runtime privilege reduction" in change_log
    assert "8 failing-first compose privilege assertions" in change_log
    assert "`no-new-privileges:true`" in change_log
    assert "`cap_drop: [ALL]`" in change_log
    assert "Compose reduces API and worker container privileges" in operator_guide


def test_sprint_784_documents_compose_read_only_app_roots() -> None:
    change_log = Path("docs/sprints/sprint-784-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Compose read-only app roots" in change_log
    assert "8 failing-first compose read-only root assertions" in change_log
    assert "`read_only: true`" in change_log
    assert "`/app/artifacts`" in change_log
    assert "Compose app containers use read-only root filesystems" in operator_guide


def test_sprint_785_documents_compose_worker_api_readiness_dependency() -> None:
    change_log = Path("docs/sprints/sprint-785-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Compose worker API readiness dependency" in change_log
    assert "5 failing-first compose dependency assertions" in change_log
    assert "`condition: service_healthy`" in change_log
    assert "`api` readiness" in change_log
    assert "Compose worker startup waits for API readiness" in operator_guide


def test_sprint_786_documents_compose_bounded_service_logs() -> None:
    change_log = Path("docs/sprints/sprint-786-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Compose bounded service logs" in change_log
    assert "7 failing-first compose logging assertions" in change_log
    assert "`max-size: \"10m\"`" in change_log
    assert "`max-file: \"5\"`" in change_log
    assert "Compose service logs are bounded" in operator_guide


def test_sprint_787_documents_compose_app_init_shim() -> None:
    change_log = Path("docs/sprints/sprint-787-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Compose app init shim" in change_log
    assert "5 failing-first compose init assertions" in change_log
    assert "`init: true`" in change_log
    assert "signal forwarding" in change_log
    assert "Compose app services use Docker's init shim" in operator_guide


def test_sprint_788_documents_compose_app_pid_limits() -> None:
    change_log = Path("docs/sprints/sprint-788-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Compose app PID limits" in change_log
    assert "5 failing-first compose PID assertions" in change_log
    assert "`pids_limit: 256`" in change_log
    assert "process-count exhaustion" in change_log
    assert "Compose app services limit process counts" in operator_guide


def test_sprint_789_documents_compose_app_graceful_shutdown() -> None:
    change_log = Path("docs/sprints/sprint-789-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Compose app graceful shutdown" in change_log
    assert "6 failing-first compose graceful shutdown assertions" in change_log
    assert "`stop_signal: SIGTERM`" in change_log
    assert "`stop_grace_period: 30s`" in change_log
    assert "Compose app services define graceful shutdown windows" in operator_guide


def test_sprint_790_documents_compose_loopback_api_binding() -> None:
    change_log = Path("docs/sprints/sprint-790-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Compose loopback API binding" in change_log
    assert "4 failing-first compose port binding assertions" in change_log
    assert "`127.0.0.1:8000:8000`" in change_log
    assert "`8000:8000`" in change_log
    assert "Compose binds the local API port to loopback only" in operator_guide


def test_sprint_791_documents_ci_read_only_token_permissions() -> None:
    change_log = Path("docs/sprints/sprint-791-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "CI read-only token permissions" in change_log
    assert "4 failing-first CI permission assertions" in change_log
    assert "`permissions: contents: read`" in change_log
    assert "`contents: write`" in change_log
    assert "CI workflow token permissions are read-only" in operator_guide


def test_sprint_792_documents_ci_concurrency_cancellation() -> None:
    change_log = Path("docs/sprints/sprint-792-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "CI concurrency cancellation" in change_log
    assert "4 failing-first CI concurrency assertions" in change_log
    assert "`cancel-in-progress: true`" in change_log
    assert "`github.workflow`" in change_log
    assert "CI verification cancels stale runs" in operator_guide


def test_sprint_793_documents_ci_checkout_credential_persistence() -> None:
    change_log = Path("docs/sprints/sprint-793-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "CI checkout credential persistence" in change_log
    assert "3 failing-first CI checkout credential assertions" in change_log
    assert "`persist-credentials: false`" in change_log
    assert "`actions/checkout@v4`" in change_log
    assert "CI checkout does not persist credentials" in operator_guide


def test_sprint_794_documents_ci_action_sha_pinning() -> None:
    change_log = Path("docs/sprints/sprint-794-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "CI third-party action SHA pinning" in change_log
    assert "3 failing-first CI action pinning assertions" in change_log
    assert "`actions/checkout@11d5960a326750d5838078e36cf38b85af677262`" in change_log
    assert "`actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065`" in change_log
    assert "CI third-party actions are pinned to commit SHAs" in operator_guide


def test_sprint_795_documents_runtime_base_image_digest_pinning() -> None:
    change_log = Path("docs/sprints/sprint-795-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime base image digest pinning" in change_log
    assert "4 failing-first runtime base image digest assertions" in change_log
    assert (
        "`python:3.13-slim@"
        "sha256:9662417aace5ae7b8e2609cce472b72a8958e134ba372808abe9cc1a0c0125e6`"
        in change_log
    )
    assert "Runtime Dockerfiles pin the Python base image digest" in operator_guide


def test_sprint_796_documents_compose_postgres_digest_pinning() -> None:
    change_log = Path("docs/sprints/sprint-796-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Compose Postgres image digest pinning" in change_log
    assert "3 failing-first compose Postgres digest assertions" in change_log
    assert (
        "`postgres:16@"
        "sha256:95206741a5b214807675e14165369d05b93a9cf692223b616d07cca227e74b0b`"
        in change_log
    )
    assert "Compose pins the PostgreSQL image digest" in operator_guide


def test_sprint_797_documents_compose_postgres_privilege_reduction() -> None:
    change_log = Path("docs/sprints/sprint-797-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Compose Postgres privilege reduction" in change_log
    assert "5 failing-first compose Postgres privilege assertions" in change_log
    assert "`no-new-privileges:true`" in change_log
    assert "`pids_limit: 512`" in change_log
    assert (
        "Compose reduces PostgreSQL container privileges without read-only root"
        in operator_guide
    )


def test_sprint_798_documents_compose_postgres_graceful_shutdown() -> None:
    change_log = Path("docs/sprints/sprint-798-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Compose Postgres graceful shutdown" in change_log
    assert "3 failing-first compose Postgres graceful shutdown assertions" in change_log
    assert "`stop_signal: SIGTERM`" in change_log
    assert "`stop_grace_period: 60s`" in change_log
    assert "Compose gives PostgreSQL an explicit graceful shutdown window" in operator_guide


def test_sprint_799_documents_docker_context_control_plane_exclusion() -> None:
    change_log = Path("docs/sprints/sprint-799-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Docker context control-plane exclusion" in change_log
    assert "8 failing-first Docker context control-plane exclusion assertions" in change_log
    assert "`.mcp.json`" in change_log
    assert "`zaxy-mcp.json`" in change_log
    assert "`.claude/`" in change_log
    assert "Docker build context excludes local control-plane configuration" in operator_guide


def test_sprint_800_documents_dockerfile_pip_upgrade_removal() -> None:
    change_log = Path("docs/sprints/sprint-800-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Dockerfile pip upgrade removal" in change_log
    assert "3 failing-first Dockerfile pip upgrade assertions" in change_log
    assert "`--upgrade pip`" in change_log
    assert "`pip install --no-cache-dir .`" in change_log
    assert "Runtime Dockerfiles do not upgrade pip during image builds" in operator_guide


def test_sprint_801_documents_dockerfile_pip_environment_defaults() -> None:
    change_log = Path("docs/sprints/sprint-801-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Dockerfile pip environment defaults" in change_log
    assert "4 failing-first Dockerfile pip environment assertions" in change_log
    assert "`PIP_DISABLE_PIP_VERSION_CHECK=1`" in change_log
    assert "`PIP_NO_CACHE_DIR=1`" in change_log
    assert "`PIP_ROOT_USER_ACTION=ignore`" in change_log
    assert "Runtime Dockerfiles define pip build environment defaults" in operator_guide


def test_sprint_802_documents_public_runtime_hsts_requirement() -> None:
    change_log = Path("docs/sprints/sprint-802-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Public runtime HSTS production gate" in change_log
    assert "2 failing-first public runtime HSTS assertions" in change_log
    assert "`JEDI_STRICT_TRANSPORT_SECURITY_ENABLED=true`" in change_log
    assert "`JEDI_RUNTIME_ROLE=api`" in change_log
    assert "`JEDI_RUNTIME_ROLE=combined`" in change_log
    assert "fail startup unless `JEDI_STRICT_TRANSPORT_SECURITY_ENABLED=true`" in operator_guide


def test_sprint_803_documents_executable_runtime_role_boundaries() -> None:
    change_log = Path("docs/sprints/sprint-803-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Executable runtime role boundaries" in change_log
    assert "2 failing-first runtime role entrypoint assertions" in change_log
    assert "`JEDI_RUNTIME_ROLE=worker`" in change_log
    assert "`JEDI_RUNTIME_ROLE=api`" in change_log
    assert "runtime API factory also" in operator_guide
    assert "rejects `JEDI_RUNTIME_ROLE=worker` before opening" in operator_guide
    assert "Worker entrypoints also reject" in operator_guide
    assert "`JEDI_RUNTIME_ROLE=api` before invoking" in operator_guide


def test_sprint_804_documents_env_example_role_and_hsts_controls() -> None:
    change_log = Path("docs/sprints/sprint-804-change-log.md").read_text(encoding="utf-8")
    env_example = Path(".env.example").read_text(encoding="utf-8")

    assert "Env example role and HSTS controls" in change_log
    assert "4 failing-first env example runtime control assertions" in change_log
    assert "`JEDI_RUNTIME_ROLE=combined`" in change_log
    assert "`JEDI_STRICT_TRANSPORT_SECURITY_ENABLED=false`" in change_log
    assert "JEDI_RUNTIME_ROLE=combined" in env_example
    assert "JEDI_STRICT_TRANSPORT_SECURITY_ENABLED=false" in env_example


def test_sprint_805_documents_production_admin_disabled_with_bearer_posture() -> None:
    change_log = Path("docs/sprints/sprint-805-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")
    admin_auth_config = Path("docs/admin-auth-config.md").read_text(encoding="utf-8")

    assert "Production admin disabled-with-bearer posture" in change_log
    assert "3 failing-first production admin posture assertions" in change_log
    assert "`JEDI_ADMIN_AUTH_MODE=disabled`" in change_log
    assert "`JEDI_ADMIN_API_TOKEN`" in change_log
    assert "`JEDI_ADMIN_AUTH_MODE=disabled` is the supported interim production posture" in (
        operator_guide
    )
    assert "Browser admin console is unavailable" in admin_auth_config
    assert "Authorization: Bearer <JEDI_ADMIN_API_TOKEN>" in admin_auth_config


def test_sprint_806_documents_api_build_claim_role_boundary() -> None:
    change_log = Path("docs/sprints/sprint-806-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "API build-claim role boundary" in change_log
    assert "1 failing-first API build-claim role assertion" in change_log
    assert "`JEDI_BUILD_CLAIM_APPLY=true`" in change_log
    assert "`JEDI_RUNTIME_ROLE=api`" in change_log
    assert "`JEDI_BUILD_CLAIM_APPLY=true` or `JEDI_UPDATE_SET_APPLY=true`" in operator_guide


def test_sprint_807_documents_direct_fulfillment_role_boundary() -> None:
    change_log = Path("docs/sprints/sprint-807-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Direct fulfillment API-role boundary" in change_log
    assert "1 failing-first direct fulfillment role assertion" in change_log
    assert "`JEDI_RUNTIME_ROLE=api`" in change_log
    assert "direct fulfillment processor also rejects" in operator_guide
    assert "before creating ServiceNow clients" in operator_guide


def test_sprint_808_documents_combined_production_explicit_opt_in() -> None:
    change_log = Path("docs/sprints/sprint-808-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")
    env_example = Path(".env.example").read_text(encoding="utf-8")

    assert "Combined production explicit opt-in" in change_log
    assert "2 failing-first combined production assertions" in change_log
    assert "`JEDI_ALLOW_COMBINED_PRODUCTION=true`" in change_log
    assert "Hosted production validation rejects the combined role" in operator_guide
    assert "JEDI_ALLOW_COMBINED_PRODUCTION=false" in env_example


def test_sprint_809_documents_scoped_combined_production_exception_flag() -> None:
    change_log = Path("docs/sprints/sprint-809-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Scoped combined production exception flag" in change_log
    assert "2 failing-first split-role exception flag assertions" in change_log
    assert "`JEDI_ALLOW_COMBINED_PRODUCTION=true`" in change_log
    assert "Split production roles reject `JEDI_ALLOW_COMBINED_PRODUCTION=true`" in operator_guide
    assert "config audits stay unambiguous" in operator_guide


def test_sprint_810_documents_production_admin_console_credential_rejection() -> None:
    change_log = Path("docs/sprints/sprint-810-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Production admin console credential rejection" in change_log
    assert "2 failing-first public production credential assertions" in change_log
    assert "`JEDI_ADMIN_CONSOLE_USERNAME`" in change_log
    assert "`JEDI_ADMIN_CONSOLE_PASSWORD`" in change_log
    assert "Public production roles also reject" in operator_guide
    assert "development-only and must not be deployed" in operator_guide


def test_sprint_811_documents_public_production_hsts_max_age_floor() -> None:
    change_log = Path("docs/sprints/sprint-811-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Public production HSTS max-age floor" in change_log
    assert "2 failing-first public production HSTS max-age assertions" in change_log
    assert "`JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS`" in change_log
    assert "Public production roles require at least `31536000` seconds" in operator_guide
    assert "`JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS>=31536000`" in operator_guide


def test_sprint_812_documents_public_production_replay_window_ceiling() -> None:
    change_log = Path("docs/sprints/sprint-812-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Public production lifecycle replay window ceiling" in change_log
    assert "2 failing-first public production replay-window assertions" in change_log
    assert "`JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS`" in change_log
    assert "reject `JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS` values above `900`" in (
        operator_guide
    )
    assert "`JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS<=900`" in operator_guide


def test_sprint_813_documents_production_body_size_ceilings() -> None:
    change_log = Path("docs/sprints/sprint-813-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Production body-size ceiling validation" in change_log
    assert "1 failing-first production body-size assertion" in change_log
    assert "`JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES`" in change_log
    assert "`JEDI_ADMIN_MAX_BODY_BYTES`" in change_log
    assert "`JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES`" in change_log
    assert "`JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES<=1048576`" in operator_guide
    assert "`JEDI_ADMIN_MAX_BODY_BYTES<=65536`" in operator_guide
    assert "`JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES<=65536`" in operator_guide


def test_sprint_814_documents_production_public_web_resource_ceilings() -> None:
    change_log = Path("docs/sprints/sprint-814-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Production public-web resource ceiling validation" in change_log
    assert "1 failing-first public-web resource assertion" in change_log
    assert "`JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES`" in change_log
    assert "`JEDI_PUBLIC_WEB_MAX_EXCERPT_CHARS`" in change_log
    assert "`JEDI_PUBLIC_WEB_MAX_RESULTS`" in change_log
    assert "`JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES<=1048576`" in operator_guide
    assert "`JEDI_PUBLIC_WEB_MAX_EXCERPT_CHARS<=16000`" in operator_guide
    assert "`JEDI_PUBLIC_WEB_MAX_RESULTS<=10`" in operator_guide


def test_sprint_815_documents_production_stale_job_threshold_ceiling() -> None:
    change_log = Path("docs/sprints/sprint-815-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Production stale-job threshold ceiling validation" in change_log
    assert "1 failing-first stale-job threshold assertion" in change_log
    assert "`JEDI_RUNNING_JOB_STALE_AFTER_SECONDS`" in change_log
    assert "`JEDI_RUNNING_JOB_STALE_AFTER_SECONDS<=86400`" in operator_guide
    assert "stale-job visibility cannot be disabled for days" in operator_guide


def test_sprint_816_documents_production_outbound_timeout_ceilings() -> None:
    change_log = Path("docs/sprints/sprint-816-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Production outbound timeout ceiling validation" in change_log
    assert "1 failing-first outbound timeout assertion" in change_log
    assert "`JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS`" in change_log
    assert "`JEDI_PUBLIC_WEB_TIMEOUT_SECONDS`" in change_log
    assert "`JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS<=30`" in operator_guide
    assert "`JEDI_PUBLIC_WEB_TIMEOUT_SECONDS<=30`" in operator_guide
    assert "worker loops cannot be stalled by multi-minute outbound waits" in operator_guide


def test_sprint_817_documents_worker_maintenance_batch_ceilings() -> None:
    change_log = Path("docs/sprints/sprint-817-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Worker maintenance batch ceiling validation" in change_log
    assert "2 failing-first worker maintenance batch assertions" in change_log
    assert "`JEDI_RETENTION_PRUNE_BATCH_SIZE`" in change_log
    assert "`JEDI_STALE_JOB_REQUEUE_BATCH_SIZE`" in change_log
    assert "`JEDI_RETENTION_PRUNE_BATCH_SIZE<=5000`" in operator_guide
    assert "`JEDI_STALE_JOB_REQUEUE_BATCH_SIZE<=100`" in operator_guide
    assert "maintenance cannot create unbounded lock or write bursts" in operator_guide


def test_sprint_818_documents_worker_scheduler_interval_ceilings() -> None:
    change_log = Path("docs/sprints/sprint-818-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Worker scheduler interval ceiling validation" in change_log
    assert "1 failing-first worker scheduler interval assertion" in change_log
    assert "`JEDI_WORKER_IDLE_SLEEP_SECONDS`" in change_log
    assert "`JEDI_RETENTION_PRUNE_INTERVAL_SECONDS`" in change_log
    assert "`JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS`" in change_log
    assert "`JEDI_WORKER_IDLE_SLEEP_SECONDS<=300`" in operator_guide
    assert "`JEDI_RETENTION_PRUNE_INTERVAL_SECONDS<=86400`" in operator_guide
    assert "`JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS<=86400`" in operator_guide
    assert "workers cannot appear healthy while sleeping or delaying maintenance for days" in (
        operator_guide
    )


def test_sprint_819_documents_worker_max_iteration_ceiling() -> None:
    change_log = Path("docs/sprints/sprint-819-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Worker max-iteration ceiling validation" in change_log
    assert "1 failing-first worker max-iteration assertion" in change_log
    assert "`JEDI_WORKER_MAX_ITERATIONS`" in change_log
    assert "`JEDI_WORKER_MAX_ITERATIONS<=10000`" in operator_guide
    assert "unset remains the deliberate long-running worker mode" in operator_guide


def test_sprint_820_documents_production_stop_on_failure_rejection() -> None:
    change_log = Path("docs/sprints/sprint-820-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Production worker stop-on-failure rejection" in change_log
    assert "1 failing-first production stop-on-failure assertion" in change_log
    assert "`JEDI_WORKER_STOP_ON_FAILURE`" in change_log
    assert "`JEDI_WORKER_STOP_ON_FAILURE=false` in production" in operator_guide
    assert "a single failed fulfillment job cannot intentionally stop the hosted worker" in (
        operator_guide
    )


def test_sprint_821_documents_production_admin_api_token_ceiling() -> None:
    change_log = Path("docs/sprints/sprint-821-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Production admin API token ceiling validation" in change_log
    assert "1 failing-first production admin API token ceiling assertion" in change_log
    assert "`JEDI_ADMIN_API_TOKEN`" in change_log
    assert "`JEDI_ADMIN_API_TOKEN` must be at most 8192 bytes" in operator_guide
    assert "oversized configured bearer secrets fail before the API starts" in operator_guide


def test_sprint_822_documents_production_admin_api_token_ascii_validation() -> None:
    change_log = Path("docs/sprints/sprint-822-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Production admin API token ASCII validation" in change_log
    assert "1 failing-first production admin API token ASCII assertion" in change_log
    assert "`JEDI_ADMIN_API_TOKEN`" in change_log
    assert "`JEDI_ADMIN_API_TOKEN` must contain only ASCII characters" in operator_guide
    assert "non-ASCII configured bearer secrets fail before the API starts" in operator_guide


def test_sprint_823_documents_admin_bearer_token_policy_parity() -> None:
    change_log = Path("docs/sprints/sprint-823-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin bearer token policy parity" in change_log
    assert "1 failing-first shared admin bearer token policy assertion" in change_log
    assert "startup validation and request-time auth share one bearer token ceiling" in (
        operator_guide
    )
    assert "`MAX_ADMIN_BEARER_TOKEN_BYTES`" in change_log


def test_sprint_824_documents_admin_basic_auth_policy_parity() -> None:
    change_log = Path("docs/sprints/sprint-824-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin Basic-auth policy parity" in change_log
    assert "1 failing-first admin console credential ceiling assertion" in change_log
    assert (
        "settings loading and request-time Basic-auth parsing share bounded credential policy"
        in operator_guide
    )
    assert "`MAX_BASIC_AUTH_CREDENTIAL_BYTES`" in change_log


def test_sprint_825_documents_admin_basic_auth_encoded_policy_parity() -> None:
    change_log = Path("docs/sprints/sprint-825-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin Basic-auth encoded policy parity" in change_log
    assert "1 failing-first Basic-auth encoded section policy assertion" in change_log
    assert "encoded Basic-auth section validation also lives in shared policy" in operator_guide
    assert "`MAX_BASIC_AUTH_ENCODED_BYTES`" in change_log


def test_sprint_826_documents_lifecycle_webhook_credential_policy_parity() -> None:
    change_log = Path("docs/sprints/sprint-826-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Lifecycle webhook credential policy parity" in change_log
    assert "1 failing-first lifecycle webhook secret ceiling assertion" in change_log
    assert "startup validation and request-time lifecycle auth share one credential ceiling" in (
        operator_guide
    )
    assert "`MAX_LIFECYCLE_WEBHOOK_CREDENTIAL_BYTES`" in change_log


def test_sprint_827_documents_runtime_rate_limiter_fail_closed_construction() -> None:
    change_log = Path("docs/sprints/sprint-827-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime rate-limiter fail-closed construction" in change_log
    assert "1 failing-first runtime API rate-limit construction assertion" in change_log
    assert "runtime API construction rejects non-positive rate-limit settings" in operator_guide
    assert "`JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS`" in change_log


def test_sprint_828_documents_alert_webhook_runtime_construction_guard() -> None:
    change_log = Path("docs/sprints/sprint-828-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert webhook runtime construction guard" in change_log
    assert "1 failing-first alert webhook runtime construction assertion" in change_log
    assert "runtime API construction rejects invalid alert webhook settings" in operator_guide
    assert "`JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS`" in change_log
    assert "`JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES`" in change_log


def test_sprint_829_documents_runtime_request_body_limit_construction_guard() -> None:
    change_log = Path("docs/sprints/sprint-829-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime request body limit construction guard" in change_log
    assert "1 failing-first runtime request body limit construction assertion" in change_log
    assert "runtime API construction rejects invalid request body limits" in operator_guide
    assert "`JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES`" in change_log
    assert "`JEDI_ADMIN_MAX_BODY_BYTES`" in change_log


def test_sprint_830_documents_lifecycle_api_body_limit_factory_guard() -> None:
    change_log = Path("docs/sprints/sprint-830-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Lifecycle API body limit factory guard" in change_log
    assert "1 failing-first lifecycle API body limit construction assertion" in change_log
    assert "`create_lifecycle_api()` rejects invalid `max_request_body_bytes`" in operator_guide
    assert "`max_request_body_bytes must be a positive integer`" in change_log


def test_sprint_831_documents_worker_loop_control_guard() -> None:
    change_log = Path("docs/sprints/sprint-831-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Worker loop direct-control guard" in change_log
    assert "1 failing-first worker loop control assertion" in change_log
    assert "`run_loop()` rejects invalid direct worker controls" in operator_guide
    assert "`JEDI_WORKER_IDLE_SLEEP_SECONDS`" in change_log
    assert "`JEDI_WORKER_STOP_ON_FAILURE`" in change_log


def test_sprint_832_documents_stale_requeue_direct_control_guard() -> None:
    change_log = Path("docs/sprints/sprint-832-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Stale requeue direct-control guard" in change_log
    assert "1 failing-first stale requeue control assertion" in change_log
    assert "`requeue_stale_running_jobs()` rejects invalid direct controls" in operator_guide
    assert "`JEDI_RUNNING_JOB_STALE_AFTER_SECONDS`" in change_log
    assert "`JEDI_STALE_JOB_REQUEUE_BATCH_SIZE`" in change_log


def test_sprint_833_documents_retention_prune_direct_policy_guard() -> None:
    change_log = Path("docs/sprints/sprint-833-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retention prune direct-policy guard" in change_log
    assert "1 failing-first retention prune policy assertion" in change_log
    assert "`prune_operational_store()` rejects invalid direct retention policies" in operator_guide
    assert "`JEDI_RETENTION_ARTIFACT_BLOB_DAYS`" in change_log
    assert "`JEDI_RETENTION_JOB_EVENT_DAYS`" in change_log
    assert "`JEDI_RETENTION_PRUNE_BATCH_SIZE`" in change_log


def test_sprint_834_documents_alert_webhook_direct_body_limit_guard() -> None:
    change_log = Path("docs/sprints/sprint-834-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert webhook direct body-limit guard" in change_log
    assert "1 failing-first alert webhook body-limit assertion" in change_log
    assert "`emit_alert_webhook()` rejects invalid direct body limits" in operator_guide
    assert "`JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES`" in change_log
    assert "`alert webhook max body bytes must be a positive integer`" in change_log


def test_sprint_835_documents_admin_result_limit_guard() -> None:
    change_log = Path("docs/sprints/sprint-835-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin result limit guard" in change_log
    assert "1 failing-first admin result limit assertion" in change_log
    assert "Admin list endpoints reject non-positive `limit` values" in operator_guide
    assert "`GET /admin/lifecycle-events`" in change_log
    assert "`GET /admin/jobs`" in change_log
    assert "`GET /admin/alerts`" in change_log


def test_sprint_836_documents_rate_limiter_direct_numeric_guard() -> None:
    change_log = Path("docs/sprints/sprint-836-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Rate limiter direct numeric guard" in change_log
    assert "1 failing-first rate limiter numeric assertion" in change_log
    assert "`InMemoryRateLimiter` rejects boolean and non-integer direct controls" in operator_guide
    assert "`max_requests must be an integer`" in change_log
    assert "`window_seconds must be an integer`" in change_log
    assert "`max_buckets must be an integer`" in change_log


def test_sprint_837_documents_rate_limiter_direct_key_guard() -> None:
    change_log = Path("docs/sprints/sprint-837-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Rate limiter direct key guard" in change_log
    assert "1 failing-first rate limiter key assertion" in change_log
    assert "`InMemoryRateLimiter.check()` rejects non-exact-string keys" in operator_guide
    assert "`rate limit key must be an exact string`" in change_log
    assert "before clock reads or bucket state access" in change_log


def test_sprint_838_documents_rate_limiter_clock_value_guard() -> None:
    change_log = Path("docs/sprints/sprint-838-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Rate limiter clock value guard" in change_log
    assert "1 failing-first rate limiter clock assertion" in change_log
    assert "`InMemoryRateLimiter` rejects invalid clock values" in operator_guide
    assert "`rate limit clock must return a finite non-negative number`" in change_log
    assert "before bucket storage" in change_log


def test_sprint_839_documents_rate_limiter_clock_callable_guard() -> None:
    change_log = Path("docs/sprints/sprint-839-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Rate limiter clock callable guard" in change_log
    assert "1 failing-first rate limiter clock callable assertion" in change_log
    assert "`InMemoryRateLimiter` rejects non-callable clock dependencies" in operator_guide
    assert "`rate limit clock must be callable`" in change_log
    assert "before limiter state initialization" in change_log


def test_sprint_840_documents_admin_rate_limiter_decision_guard() -> None:
    change_log = Path("docs/sprints/sprint-840-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin rate limiter decision guard" in change_log
    assert "1 failing-first malformed admin limiter decision assertion" in change_log
    assert "`_require_admin_rate_limit` validates limiter decision objects" in operator_guide
    assert "`admin rate limiter is invalid`" in change_log
    assert "before `Retry-After` header construction" in change_log


def test_sprint_841_documents_lifecycle_rate_limiter_decision_guard() -> None:
    change_log = Path("docs/sprints/sprint-841-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Lifecycle rate limiter decision guard" in change_log
    assert "1 failing-first malformed lifecycle limiter decision assertion" in change_log
    assert "`_require_rate_limit` validates lifecycle limiter decision objects" in operator_guide
    assert "`lifecycle rate limiter is invalid`" in change_log
    assert "before lifecycle `Retry-After` header construction" in change_log


def test_sprint_842_documents_alert_webhook_response_dto_guard() -> None:
    change_log = Path("docs/sprints/sprint-842-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert webhook response DTO guard" in change_log
    assert "1 failing-first alert webhook response DTO assertion" in change_log
    assert (
        "`emit_alert_webhook()` requires exact `HttpResponse` transport results"
        in operator_guide
    )
    assert "`alert webhook transport returned invalid response`" in change_log
    assert "before response status or body inspection" in change_log


def test_sprint_843_documents_alert_webhook_transport_exception_guard() -> None:
    change_log = Path("docs/sprints/sprint-843-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert webhook transport exception guard" in change_log
    assert "1 failing-first alert webhook transport exception assertion" in change_log
    assert "`emit_alert_webhook()` wraps transport execution failures" in operator_guide
    assert "`alert webhook transport request failed`" in change_log
    assert "without stringifying or chaining the original exception" in change_log


def test_sprint_844_documents_provider_base_url_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-844-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider base URL exact-string guard" in change_log
    assert "1 failing-first provider base URL exact-string assertion" in change_log
    assert "`validate_provider_base_url()` rejects non-exact strings" in operator_guide
    assert "`base_url must be an exact string`" in change_log
    assert "before URL parsing or endpoint safety checks" in change_log


def test_sprint_845_documents_provider_token_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-845-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Provider token exact-string guard" in change_log
    assert "1 failing-first provider token exact-string assertion" in change_log
    assert (
        "`validate_provider_api_key()` and `validate_provider_model()` reject non-exact strings"
        in operator_guide
    )
    assert "`api_key must be an exact string`" in change_log
    assert "`model must be an exact string`" in change_log


def test_sprint_846_documents_url_query_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-846-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "URL query helper exact-string guard" in change_log
    assert "1 failing-first URL query helper exact-string assertion" in change_log
    assert "URL query safety helpers reject non-exact strings" in operator_guide
    assert "`value must be an exact string`" in change_log
    assert "`query must be an exact string`" in change_log


def test_sprint_847_documents_unicode_control_character_guard() -> None:
    change_log = Path("docs/sprints/sprint-847-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Unicode control character guard" in change_log
    assert "1 failing-first Unicode control character assertion" in change_log
    assert "`is_control_character()` rejects malformed direct calls" in operator_guide
    assert "`character must be an exact string`" in change_log
    assert "`character must be a single character`" in change_log


def test_sprint_848_documents_sensitive_key_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-848-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Sensitive key exact-string guard" in change_log
    assert "1 failing-first sensitive key exact-string assertion" in change_log
    assert "`normalize_sensitive_key()` only normalizes exact strings" in operator_guide
    assert "`StringifiableSensitiveKey`" in change_log
    assert "`SensitiveKeySubclass`" in change_log


def test_sprint_849_documents_work_note_secret_values_guard() -> None:
    change_log = Path("docs/sprints/sprint-849-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Work-note literal secret-values guard" in change_log
    assert "2 failing-first work-note secret-values assertions" in change_log
    assert "`safe_work_note_value()` treats literal `secret_values` as untrusted" in operator_guide
    assert "`_HostileSecretValues`" in change_log
    assert "`_SecretValueSubclass`" in change_log


def test_sprint_850_documents_diagnostic_redaction_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-850-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Diagnostic redaction exact-string guard" in change_log
    assert "1 failing-first diagnostic redaction exact-string assertion" in change_log
    assert "`_redact_diagnostic_text()` accepts only exact strings or `None`" in operator_guide
    assert "`[non-string diagnostic text]`" in change_log
    assert "`_HostileDiagnosticText`" in change_log


def test_sprint_851_documents_runtime_redaction_secret_values_guard() -> None:
    change_log = Path("docs/sprints/sprint-851-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime redaction literal secret-values guard" in change_log
    assert "2 failing-first runtime redaction secret-values assertions" in change_log
    assert "`_redacting_handler()` treats literal `secret_values` as untrusted" in operator_guide
    assert "`_HostileSecretValues`" in change_log
    assert "`_SecretValueSubclass`" in change_log


def test_sprint_852_documents_servicenow_failure_notifier_secret_values_guard() -> None:
    change_log = Path("docs/sprints/sprint-852-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow failure notifier secret-values guard" in change_log
    assert "1 failing-first ServiceNow failure notifier secret-values assertion" in change_log
    assert (
        "`_servicenow_failure_notifier()` passes untrusted `secret_values` directly into "
        "hardened sanitizers"
        in operator_guide
    )
    assert "`HostileFailureNotifierSecretValues`" in change_log


def test_sprint_853_documents_completion_missing_sys_id_diagnostic_redaction() -> None:
    change_log = Path("docs/sprints/sprint-853-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Completion missing-sys-id diagnostic redaction" in change_log
    assert "1 failing-first completion missing-sys-id diagnostic assertion" in change_log
    assert (
        "`_servicenow_complete_notifier()` sanitizes the story number before raising the "
        "missing `story_sys_id` diagnostic"
        in operator_guide
    )
    assert "`test_servicenow_complete_notifier_sanitizes_missing_sys_id_story_number`" in change_log


def test_sprint_854_documents_failure_notifier_story_not_found_redaction() -> None:
    change_log = Path("docs/sprints/sprint-854-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Failure notifier story-not-found diagnostic redaction" in change_log
    assert "1 failing-first failure notifier story-not-found diagnostic assertion" in change_log
    assert (
        "`_servicenow_failure_notifier()` sanitizes the story number before raising the "
        "`story not found` diagnostic"
        in operator_guide
    )
    assert "`test_servicenow_failure_notifier_sanitizes_story_not_found_diagnostic`" in change_log


def test_sprint_855_documents_failure_notifier_lookup_query_guard() -> None:
    change_log = Path("docs/sprints/sprint-855-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Failure notifier story lookup query guard" in change_log
    assert "1 failing-first failure notifier lookup query assertion" in change_log
    assert (
        "`_servicenow_failure_notifier()` validates story lookup query parts before calling "
        "`fetch_stories()`"
        in operator_guide
    )
    assert "`test_servicenow_failure_notifier_rejects_unsafe_story_number_lookup`" in change_log


def test_sprint_856_documents_failure_notifier_story_sys_id_record_guard() -> None:
    change_log = Path("docs/sprints/sprint-856-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Failure notifier story sys-id record guard" in change_log
    assert "1 failing-first failure notifier story sys-id assertion" in change_log
    assert (
        "`_servicenow_failure_notifier()` applies record-id syntax validation to "
        "`story_sys_id` lookup values"
        in operator_guide
    )
    assert "`test_servicenow_failure_notifier_rejects_unsafe_story_sys_id_lookup`" in change_log


def test_sprint_857_documents_failure_notifier_state_choice_guard() -> None:
    change_log = Path("docs/sprints/sprint-857-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Failure notifier state-choice guard" in change_log
    assert "1 failing-first failure notifier state-choice assertion" in change_log
    assert (
        "`_story_state_choice_value()` skips malformed state-choice records before comparing labels"
        in operator_guide
    )
    assert "`test_servicenow_failure_notifier_skips_malformed_state_choices`" in change_log


def test_sprint_858_documents_failure_notifier_state_choice_value_guard() -> None:
    change_log = Path("docs/sprints/sprint-858-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Failure notifier state-choice value guard" in change_log
    assert "1 failing-first failure notifier state-choice value assertion" in change_log
    assert (
        "`_story_state_choice_value()` rejects unsafe exact-string state-choice values before "
        "returning the state"
        in operator_guide
    )
    assert "`test_servicenow_failure_notifier_skips_unsafe_state_choice_values`" in change_log


def test_sprint_859_documents_failure_notifier_lookup_result_guard() -> None:
    change_log = Path("docs/sprints/sprint-859-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Failure notifier lookup-result sys-id guard" in change_log
    assert "1 failing-first failure notifier lookup-result assertion" in change_log
    assert (
        "`_servicenow_failure_notifier()` validates found story `sys_id` values before "
        "failed-story update"
        in operator_guide
    )
    assert "`test_servicenow_failure_notifier_rejects_unsafe_found_story_sys_id`" in change_log


def test_sprint_860_documents_completion_story_sys_id_guard() -> None:
    change_log = Path("docs/sprints/sprint-860-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Completion notifier story-sys-id guard" in change_log
    assert "1 failing-first completion story-sys-id assertion" in change_log
    assert (
        "`_servicenow_complete_notifier()` validates completion `story_sys_id` values before "
        "closeout update"
        in operator_guide
    )
    assert "`test_servicenow_complete_notifier_rejects_unsafe_story_sys_id`" in change_log


def test_sprint_861_documents_servicenow_story_query_guard() -> None:
    change_log = Path("docs/sprints/sprint-861-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow story query guard" in change_log
    assert "1 failing-first ServiceNow story-query assertion" in change_log
    assert "`ServiceNowClient.fetch_stories()` validates raw story `sysparm_query` values" in (
        operator_guide
    )
    assert "`test_servicenow_client_rejects_unsafe_story_query_before_request`" in change_log


def test_sprint_862_documents_ready_story_project_id_truthiness_guard() -> None:
    change_log = Path("docs/sprints/sprint-862-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Ready-story project-id truthiness guard" in change_log
    assert "1 failing-first ready-story project-id truthiness assertion" in change_log
    assert (
        "`ServiceNowClient.fetch_ready_stories(project_sys_id=...)` validates provided "
        "project ids before truthiness branching"
        in operator_guide
    )
    assert (
        "`test_servicenow_client_rejects_hostile_ready_story_project_id_before_truthiness`"
        in change_log
    )


def test_sprint_863_documents_servicenow_field_list_truthiness_guard() -> None:
    change_log = Path("docs/sprints/sprint-863-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow field-list truthiness guard" in change_log
    assert "1 failing-first ServiceNow field-list truthiness assertion" in change_log
    assert (
        "`ServiceNowClient.fetch_table_records(fields=...)` validates provided field lists "
        "before truthiness branching"
        in operator_guide
    )
    assert "`test_servicenow_client_rejects_table_record_fields_before_truthiness`" in change_log


def test_sprint_864_documents_cicd_source_id_truthiness_guard() -> None:
    change_log = Path("docs/sprints/sprint-864-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow CI/CD source-id truthiness guard" in change_log
    assert "2 failing-first ServiceNow CI/CD source-id truthiness assertions" in change_log
    assert (
        "`ServiceNowClient.retrieve_cicd_update_set()` validates optional source ids before "
        "truthiness branching"
        in operator_guide
    )
    assert (
        "`test_servicenow_client_rejects_cicd_retrieve_source_ids_before_truthiness`"
        in change_log
    )


def test_sprint_865_documents_cicd_probe_action_guard() -> None:
    change_log = Path("docs/sprints/sprint-865-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow CI/CD probe action guard" in change_log
    assert "1 failing-first ServiceNow CI/CD probe-action assertion" in change_log
    assert (
        "`ServiceNowClient.probe_cicd_update_set_endpoint()` validates probe actions before "
        "membership checks"
        in operator_guide
    )
    assert "`test_servicenow_cicd_probe_rejects_unsafe_action_before_membership`" in change_log


def test_sprint_866_documents_servicenow_empty_field_list_guard() -> None:
    change_log = Path("docs/sprints/sprint-866-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow empty field-list guard" in change_log
    assert "1 failing-first ServiceNow empty field-list assertion" in change_log
    assert (
        "`ServiceNowClient.fetch_table_records(fields=...)` rejects empty provided field lists"
        in operator_guide
    )
    assert "`test_servicenow_client_rejects_empty_table_record_fields_before_request`" in change_log


def test_sprint_867_documents_cicd_request_container_truthiness_guard() -> None:
    change_log = Path("docs/sprints/sprint-867-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow CI/CD request-container truthiness guard" in change_log
    assert "2 failing-first ServiceNow CI/CD request-container truthiness assertions" in (
        change_log
    )
    assert (
        "`ServiceNowClient._send_cicd_update_set_request()` validates optional params and "
        "body containers before truthiness branching"
        in operator_guide
    )
    assert (
        "`test_servicenow_client_rejects_cicd_request_params_before_truthiness`"
        in change_log
    )
    assert (
        "`test_servicenow_client_rejects_cicd_request_body_before_truthiness`"
        in change_log
    )


def test_sprint_868_documents_cicd_request_method_action_guard() -> None:
    change_log = Path("docs/sprints/sprint-868-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow CI/CD request method/action guard" in change_log
    assert "2 failing-first ServiceNow CI/CD request method/action assertions" in change_log
    assert (
        "`ServiceNowClient._send_cicd_update_set_request()` validates CI/CD request methods "
        "and actions before URL construction"
        in operator_guide
    )
    assert "`test_servicenow_client_rejects_cicd_request_method_before_auth`" in change_log
    assert (
        "`test_servicenow_client_rejects_cicd_request_action_before_url_construction`"
        in change_log
    )


def test_sprint_869_documents_empty_lookup_body_guard() -> None:
    change_log = Path("docs/sprints/sprint-869-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow empty lookup body guard" in change_log
    assert "2 failing-first ServiceNow empty lookup assertions" in change_log
    assert (
        "`ServiceNowClient.fetch_table_record()` and "
        "`ServiceNowClient.upsert_table_record()` reject empty lookup bodies"
        in operator_guide
    )
    assert "`test_servicenow_client_rejects_empty_lookup_before_request`" in change_log
    assert "`test_servicenow_client_rejects_empty_upsert_lookup_before_lookup`" in change_log


def test_sprint_870_documents_missing_response_result_guard() -> None:
    change_log = Path("docs/sprints/sprint-870-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow missing response result guard" in change_log
    assert "2 failing-first ServiceNow missing result assertions" in change_log
    assert (
        "ServiceNow table/list response handling requires successful responses to include "
        "`result`"
        in operator_guide
    )
    assert (
        "ServiceNow single-record response handling requires successful responses to include "
        "`result`"
        in operator_guide
    )
    assert (
        "`test_servicenow_result_record_list_rejects_missing_result_without_silent_empty`"
        in change_log
    )
    assert (
        "`test_servicenow_result_object_rejects_missing_result_without_silent_empty`"
        in change_log
    )


def test_sprint_871_documents_dictionary_form_existing_element_sys_id_guard() -> None:
    change_log = Path("docs/sprints/sprint-871-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Dictionary/form existing element sys_id guard" in change_log
    assert "1 failing-first dictionary/form missing element sys_id assertion" in change_log
    assert (
        "Dictionary/form form-layout XML requires fetched existing `sys_ui_element` rows to "
        "include `sys_id`"
        in operator_guide
    )
    assert (
        "`test_generic_dictionary_form_rejects_existing_form_element_missing_sys_id`"
        in change_log
    )


def test_sprint_872_documents_form_section_missing_sys_id_guard() -> None:
    change_log = Path("docs/sprints/sprint-872-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Form-section missing sys_id guard" in change_log
    assert "1 failing-first form-section missing sys_id assertion" in change_log
    assert (
        "Form-section removal customer-update generation requires matched `sys_ui_section` "
        "records to include `sys_id`"
        in operator_guide
    )
    assert (
        "`test_form_section_customer_updates_rejects_missing_section_sys_id`"
        in change_log
    )


def test_sprint_873_documents_catalog_metadata_missing_sys_id_guard() -> None:
    change_log = Path("docs/sprints/sprint-873-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Catalog metadata missing sys_id guard" in change_log
    assert "1 failing-first catalog metadata missing sys_id assertion" in change_log
    assert (
        "Catalog item customer-update generation requires matched catalog metadata records "
        "to include `sys_id`"
        in operator_guide
    )
    assert (
        "`test_catalog_item_customer_updates_rejects_matched_topic_missing_sys_id`"
        in change_log
    )


def test_sprint_874_documents_update_set_apply_form_section_sys_id_guard() -> None:
    change_log = Path("docs/sprints/sprint-874-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply form-section sys_id guard" in change_log
    assert "1 failing-first Update Set apply missing section sys_id assertion" in change_log
    assert (
        "Direct Update Set apply form layout planning requires matched `sys_ui_section` "
        "records to include `sys_id`"
        in operator_guide
    )
    assert (
        "`test_apply_candidate_rejects_named_form_section_missing_sys_id`"
        in change_log
    )


def test_sprint_875_documents_update_set_apply_metadata_non_json_guard() -> None:
    change_log = Path("docs/sprints/sprint-875-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply metadata non-JSON guard" in change_log
    assert "1 failing-first Update Set apply metadata non-JSON assertion" in change_log
    assert (
        "Direct Update Set apply form metadata conversion accepts only primitive string, "
        "boolean, and integer scalar values"
        in operator_guide
    )
    assert (
        "`test_apply_candidate_rejects_named_form_section_non_json_sys_id_without_leak`"
        in change_log
    )


def test_sprint_876_documents_update_set_apply_position_metadata_guard() -> None:
    change_log = Path("docs/sprints/sprint-876-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply position metadata guard" in change_log
    assert "1 failing-first Update Set apply position metadata assertion" in change_log
    assert (
        "Direct Update Set apply form element position parsing uses the same primitive-only "
        "metadata boundary"
        in operator_guide
    )
    assert (
        "`test_apply_candidate_rejects_form_element_non_json_position_without_leak`"
        in change_log
    )


def test_sprint_877_documents_update_set_apply_invalid_position_guard() -> None:
    change_log = Path("docs/sprints/sprint-877-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply invalid position guard" in change_log
    assert "1 failing-first Update Set apply invalid position assertion" in change_log
    assert (
        "Direct Update Set apply form element position parsing also fails closed on "
        "malformed primitive position values"
        in operator_guide
    )
    assert (
        "`test_apply_candidate_rejects_form_element_invalid_position_without_leak`"
        in change_log
    )


def test_sprint_878_documents_update_set_apply_view_metadata_guard() -> None:
    change_log = Path("docs/sprints/sprint-878-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply section view metadata guard" in change_log
    assert "1 failing-first Update Set apply section view metadata assertion" in change_log
    assert (
        "Direct Update Set apply section view filtering uses the primitive-only metadata "
        "boundary"
        in operator_guide
    )
    assert (
        "`test_apply_candidate_rejects_section_view_non_json_value_without_leak`"
        in change_log
    )


def test_sprint_952_documents_update_set_apply_reference_dict_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-952-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply reference dict-subclass guard" in change_log
    assert "`_is_global_main_story_view_section()`" in change_log
    assert "`_reference_value()`" in change_log
    assert "Update Set apply metadata contains non-JSON value" in change_log
    assert (
        "1 failing-first Update Set apply reference dict-subclass assertion"
        in change_log
    )
    assert "Direct Update Set apply reference metadata dictionaries are exact containers" in (
        operator_guide
    )
    assert "Dictionary subclasses fail with" in operator_guide
    assert (
        "`test_apply_candidate_rejects_section_view_dict_subclass_without_leak`"
        in change_log
    )


def test_sprint_953_documents_dictionary_form_reference_dict_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-953-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Dictionary/form reference dict-subclass guard" in change_log
    assert "`_is_global_main_view_section()`" in change_log
    assert "`_view_payload_value()`" in change_log
    assert "`reference_value()`" in change_log
    assert "dictionary/form metadata field contains non-JSON value" in change_log
    assert (
        "1 failing-first dictionary/form reference dict-subclass assertion"
        in change_log
    )
    assert "Dictionary/form reference metadata dictionaries are exact containers" in (
        operator_guide
    )
    assert "Dictionary subclasses fail with" in operator_guide
    assert (
        "`test_generic_dictionary_form_rejects_view_dict_subclass_metadata_without_leak`"
        in change_log
    )


def test_sprint_954_documents_handoff_reference_dict_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-954-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set handoff reference dict-subclass guard" in change_log
    assert "`_reference_table()`" in change_log
    assert "dictionary/form handoff field contains non-JSON value" in change_log
    assert (
        "1 failing-first retrieved Update Set handoff reference dict-subclass assertion"
        in change_log
    )
    assert (
        "Dictionary/form handoff reference table metadata accepts only exact dictionaries"
        in operator_guide
    )
    assert "Dictionary subclasses fail with" in operator_guide
    assert (
        "`test_create_update_set_handoff_rejects_reference_dict_subclass_without_leak`"
        in change_log
    )


def test_sprint_955_documents_handoff_candidate_truthiness_guard() -> None:
    change_log = Path("docs/sprints/sprint-955-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set handoff candidate truthiness guard" in change_log
    assert "`_first_present()`" in change_log
    assert "`_candidate_field_present()`" in change_log
    assert "dictionary/form handoff field contains non-JSON value" in change_log
    assert (
        "1 failing-first retrieved Update Set handoff candidate truthiness assertion"
        in change_log
    )
    assert "Dictionary/form handoff candidate field selection is truthiness-safe" in (
        operator_guide
    )
    assert "before `__bool__`, `str()`, or `repr()` can execute" in operator_guide
    assert (
        "`test_create_update_set_handoff_rejects_truthy_object_field_without_leak`"
        in change_log
    )


def test_sprint_956_documents_handoff_description_summary_guard() -> None:
    change_log = Path("docs/sprints/sprint-956-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set handoff description summary guard" in change_log
    assert "`_field_summary()`" in change_log
    assert "`_summary_value()`" in change_log
    assert "[non-json summary value]" in change_log
    assert (
        "1 failing-first retrieved Update Set handoff description summary assertion"
        in change_log
    )
    assert "Retrieved Update Set descriptions summarize proposed candidate changes" in (
        operator_guide
    )
    assert "Unsupported summary values render as `[non-json summary value]`" in (
        operator_guide
    )
    assert (
        "`test_create_update_set_handoff_sanitizes_description_summary_without_stringifying`"
        in change_log
    )


def test_sprint_957_documents_handoff_reviewer_note_guard() -> None:
    change_log = Path("docs/sprints/sprint-957-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set handoff reviewer-note guard" in change_log
    assert "`_reviewer_note_lines()`" in change_log
    assert "`safe_work_note_value()`" in change_log
    assert "[non-string work note value]" in change_log
    assert (
        "1 failing-first retrieved Update Set handoff reviewer-note assertion"
        in change_log
    )
    assert "Retrieved Update Set reviewer notes are sanitized before description" in (
        operator_guide
    )
    assert "Non-string notes and string subclasses render as `[non-string work note value]`" in (
        operator_guide
    )
    assert (
        "`test_create_update_set_handoff_sanitizes_reviewer_note_without_stringifying`"
        in change_log
    )


def test_sprint_958_documents_handoff_description_header_guard() -> None:
    change_log = Path("docs/sprints/sprint-958-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set handoff description header guard" in change_log
    assert "`_update_set_description()`" in change_log
    assert "`_description_optional_text()`" in change_log
    assert "[non-string work note value]" in change_log
    assert (
        "1 failing-first retrieved Update Set handoff description header assertion"
        in change_log
    )
    assert "Retrieved Update Set description headers are sanitized before XML" in (
        operator_guide
    )
    assert (
        "Story numbers, candidate artifact references, and optional candidate hashes"
        in operator_guide
    )
    assert (
        "`test_create_update_set_handoff_sanitizes_description_header_without_stringifying`"
        in change_log
    )


def test_sprint_959_documents_handoff_remote_sys_id_source_guard() -> None:
    change_log = Path("docs/sprints/sprint-959-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set handoff remote_sys_id source guard" in change_log
    assert "`_remote_sys_id()`" in change_log
    assert "`_remote_sys_id_source()`" in change_log
    assert "1 failing-first retrieved Update Set handoff remote_sys_id source assertion" in (
        change_log
    )
    assert "Retrieved Update Set `remote_sys_id` generation uses only exact string" in (
        operator_guide
    )
    assert "before truthiness checks, lowercase conversion, hex filtering" in operator_guide
    assert (
        "`test_create_update_set_handoff_remote_sys_id_ignores_malformed_hash`"
        in change_log
    )


def test_sprint_960_documents_handoff_description_metric_guard() -> None:
    change_log = Path("docs/sprints/sprint-960-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set handoff description metric guard" in change_log
    assert "`_description_metric_text()`" in change_log
    assert "[non-json summary value]" in change_log
    assert (
        "1 failing-first retrieved Update Set handoff description metric assertion"
        in change_log
    )
    assert "Retrieved Update Set description metrics are serialized" in operator_guide
    assert "exact integers or finite exact floats" in operator_guide
    assert (
        "`test_create_update_set_handoff_sanitizes_description_metrics_without_stringifying`"
        in change_log
    )


def test_sprint_961_documents_handoff_changes_collection_guard() -> None:
    change_log = Path("docs/sprints/sprint-961-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set handoff changes collection guard" in change_log
    assert "`_candidate_changes()`" in change_log
    assert "retrieved Update Set handoff changes contain non-JSON value" in change_log
    assert (
        "1 failing-first retrieved Update Set handoff changes collection assertion"
        in change_log
    )
    assert "Retrieved Update Set handoff change collections are exact-list guarded" in (
        operator_guide
    )
    assert "before truthiness checks, iteration, table routing" in operator_guide
    assert (
        "`test_create_update_set_handoff_rejects_changes_collection_subclass_without_leak`"
        in change_log
    )


def test_sprint_962_documents_handoff_reviewer_note_collection_guard() -> None:
    change_log = Path("docs/sprints/sprint-962-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set handoff reviewer-note collection guard" in change_log
    assert "`_reviewer_notes()`" in change_log
    assert "retrieved Update Set handoff reviewer notes contain non-JSON value" in (
        change_log
    )
    assert (
        "1 failing-first retrieved Update Set handoff reviewer-note collection assertion"
        in change_log
    )
    assert "Retrieved Update Set reviewer-note collections are exact-list guarded" in (
        operator_guide
    )
    assert "before truthiness checks or iteration" in operator_guide
    assert (
        "`test_create_update_set_handoff_rejects_reviewer_note_collection_subclass_without_leak`"
        in change_log
    )


def test_sprint_963_documents_handoff_story_number_name_guard() -> None:
    change_log = Path("docs/sprints/sprint-963-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set handoff story-number name guard" in change_log
    assert "`_update_set_name()`" in change_log
    assert "retrieved Update Set handoff story number contains non-JSON value" in (
        change_log
    )
    assert (
        "1 failing-first retrieved Update Set handoff story-number assertion"
        in change_log
    )
    assert "Retrieved Update Set names require an exact string story number" in (
        operator_guide
    )
    assert "before Update Set name construction, XML serialization" in operator_guide
    assert (
        "`test_create_update_set_handoff_rejects_story_number_object_without_leak`"
        in change_log
    )


def test_sprint_964_documents_handoff_instance_url_guard() -> None:
    change_log = Path("docs/sprints/sprint-964-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set handoff instance URL guard" in change_log
    assert "`_update_set_url()`" in change_log
    assert "retrieved Update Set handoff instance URL contains non-JSON value" in (
        change_log
    )
    assert (
        "1 failing-first retrieved Update Set handoff instance URL assertion"
        in change_log
    )
    assert "Retrieved Update Set handoff URLs require an exact string instance URL" in (
        operator_guide
    )
    assert "before `rstrip()`, story work-note formatting" in operator_guide
    assert "post-import handoff metadata failure" in operator_guide
    assert (
        "`test_create_update_set_handoff_rejects_instance_url_object_without_leak`"
        in change_log
    )


def test_sprint_965_documents_handoff_lookup_collection_guard() -> None:
    change_log = Path("docs/sprints/sprint-965-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set handoff lookup collection guard" in change_log
    assert "`_imported_update_set_sys_id()`" in change_log
    assert "retrieved Update Set lookup contains non-JSON value" in change_log
    assert (
        "1 failing-first retrieved Update Set handoff lookup collection assertion"
        in change_log
    )
    assert "Retrieved Update Set post-import lookup record collections are exact-shape" in (
        operator_guide
    )
    assert "before truthiness checks, indexing hooks, `.get()` hooks" in operator_guide
    assert (
        "`test_import_retrieved_update_set_rejects_lookup_collection_subclass_without_leak`"
        in change_log
    )


def test_sprint_966_documents_customer_update_collection_guard() -> None:
    change_log = Path("docs/sprints/sprint-966-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set customer update collection guard" in change_log
    assert "`_customer_updates()`" in change_log
    assert "retrieved Update Set customer update contains non-JSON value" in change_log
    assert (
        "1 failing-first retrieved Update Set customer update collection assertion"
        in change_log
    )
    assert (
        "Retrieved Update Set generated customer update collections are "
        "exact-shape guarded"
        in operator_guide
    )
    assert "before truthiness checks, customer update iteration" in operator_guide
    assert (
        "`test_import_retrieved_update_set_rejects_customer_update_collection_subclass`"
        in change_log
    )


def test_sprint_977_documents_handoff_generated_customer_update_guard() -> None:
    change_log = Path("docs/sprints/sprint-977-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set generated customer update guard" in change_log
    assert "`_customer_updates_for_candidate()`" in change_log
    assert "`_customer_updates()`" in change_log
    assert "retrieved Update Set customer update contains non-JSON value" in change_log
    assert (
        "1 failing-first retrieved Update Set generated customer-update assertion"
        in change_log
    )
    assert (
        "Retrieved Update Set generated customer update collections are "
        "exact-shape guarded"
        in operator_guide
    )
    assert "before truthiness checks, customer update iteration" in operator_guide
    assert (
        "`test_create_update_set_handoff_rejects_generated_customer_update_collection_subclass`"
        in change_log
    )


def test_sprint_978_documents_handoff_change_identifier_guard() -> None:
    change_log = Path("docs/sprints/sprint-978-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set handoff change identifier guard" in change_log
    assert "`_handoff_change_identifier_text()`" in change_log
    assert "retrieved Update Set handoff changes contain non-JSON value" in change_log
    assert (
        "1 failing-first retrieved Update Set change table identifier assertion"
        in change_log
    )
    assert (
        "Retrieved Update Set handoff change identifiers are exact-string guarded"
        in operator_guide
    )
    assert "before proposed-change description rendering" in operator_guide
    assert "deterministic builder selection" in operator_guide
    assert (
        "`test_create_update_set_handoff_rejects_change_table_string_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_create_update_set_handoff_rejects_change_operation_string_subclass_without_leak`"
        in change_log
    )


def test_sprint_979_documents_handoff_change_fields_guard() -> None:
    change_log = Path("docs/sprints/sprint-979-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set handoff change fields guard" in change_log
    assert "`_handoff_change_fields()`" in change_log
    assert (
        "retrieved Update Set handoff change fields contain non-JSON value"
        in change_log
    )
    assert (
        "1 failing-first retrieved Update Set change fields container assertion"
        in change_log
    )
    assert (
        "Retrieved Update Set handoff change field containers are "
        "exact-dictionary guarded"
        in operator_guide
    )
    assert "before truthiness checks, field iteration" in operator_guide
    assert "dictionary/form intent extraction" in operator_guide
    assert (
        "`test_create_update_set_handoff_rejects_change_fields_dict_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_create_update_set_handoff_rejects_change_field_key_string_subclass_without_leak`"
        in change_log
    )


def test_sprint_980_documents_dictionary_form_alias_truthiness_guard() -> None:
    change_log = Path("docs/sprints/sprint-980-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Dictionary/form handoff alias truthiness guard" in change_log
    assert "`_form_table_name()`" in change_log
    assert "`_reference_table()`" in change_log
    assert "`_placement_anchor()`" in change_log
    assert "dictionary/form handoff field contains non-JSON value" in change_log
    assert (
        "Dictionary/form handoff alias selection is truthiness-safe"
        in operator_guide
    )
    assert "before boolean chaining, `if` checks, `__bool__`" in operator_guide
    assert "reference resolution, placement planning" in operator_guide
    assert (
        "`test_create_update_set_handoff_rejects_truthy_form_table_alias_without_leak`"
        in change_log
    )
    assert (
        "`test_create_update_set_handoff_rejects_truthy_placement_anchor_without_leak`"
        in change_log
    )
    assert (
        "`test_create_update_set_handoff_rejects_truthy_reference_alias_without_leak`"
        in change_log
    )


def test_sprint_981_documents_handoff_state_choice_guard() -> None:
    change_log = Path("docs/sprints/sprint-981-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set handoff state choice guard" in change_log
    assert "`_ready_for_testing_state()`" in change_log
    assert "`_handoff_state_choices()`" in change_log
    assert (
        "retrieved Update Set handoff state choices contain non-JSON value"
        in change_log
    )
    assert "1 failing-first state-choice collection assertion" in change_log
    assert (
        "Retrieved Update Set handoff state-choice lookup is exact-shape guarded"
        in operator_guide
    )
    assert "before iteration hooks, `model_dump()` hooks" in operator_guide
    assert "after the retrieved Update Set import" in operator_guide
    assert (
        "`test_create_update_set_handoff_rejects_state_choice_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_create_update_set_handoff_rejects_state_choice_item_subclass_without_leak`"
        in change_log
    )


def test_sprint_982_documents_writeback_orchestration_state_choice_guard() -> None:
    change_log = Path("docs/sprints/sprint-982-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Writeback orchestration state choice guard" in change_log
    assert "`_writeback_state_choices()`" in change_log
    assert "writeback state choices contain non-JSON value" in change_log
    assert (
        "1 failing-first writeback capability state-choice collection assertion"
        in change_log
    )
    assert (
        "Writeback orchestration state-choice lookup is exact-shape guarded"
        in operator_guide
    )
    assert "before iteration hooks, `model_dump()` hooks" in operator_guide
    assert "story mutation, audit writing" in operator_guide
    assert (
        "`test_evaluate_writeback_capability_rejects_state_choice_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_execute_writeback_rejects_state_choice_collection_subclass_before_mutation`"
        in change_log
    )


def test_sprint_983_documents_writeback_orchestration_dictionary_field_guard() -> None:
    change_log = Path("docs/sprints/sprint-983-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Writeback orchestration dictionary field guard" in change_log
    assert "`_writeback_dictionary_fields()`" in change_log
    assert "writeback dictionary fields contain non-JSON value" in change_log
    assert (
        "1 failing-first writeback capability dictionary-field collection assertion"
        in change_log
    )
    assert (
        "Writeback orchestration dictionary-field lookup is exact-shape guarded"
        in operator_guide
    )
    assert "before iteration hooks, model hooks" in operator_guide
    assert "story mutation, audit writing" in operator_guide
    assert (
        "`test_evaluate_writeback_capability_rejects_dictionary_field_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_execute_writeback_rejects_dictionary_field_collection_subclass_before_mutation`"
        in change_log
    )


def test_sprint_984_documents_writeback_orchestration_story_fetch_guard() -> None:
    change_log = Path("docs/sprints/sprint-984-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Writeback orchestration story fetch guard" in change_log
    assert "`_writeback_stories()`" in change_log
    assert "writeback stories contain non-JSON value" in change_log
    assert (
        "1 failing-first writeback verification story collection assertion"
        in change_log
    )
    assert (
        "Writeback orchestration story lookup is exact-shape guarded"
        in operator_guide
    )
    assert "before truthiness hooks, indexing hooks" in operator_guide
    assert "`model_copy()` hooks" in operator_guide
    assert "story mutation, audit writing" in operator_guide
    assert (
        "`test_verify_writeback_rejects_story_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_execute_build_claim_rejects_story_collection_subclass_before_mutation`"
        in change_log
    )


def test_sprint_985_documents_intake_feedback_story_fetch_guard() -> None:
    change_log = Path("docs/sprints/sprint-985-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Intake feedback story fetch guard" in change_log
    assert "`_intake_stories()`" in change_log
    assert "intake story fetch contains non-JSON value" in change_log
    assert "1 failing-first intake feedback story collection assertion" in change_log
    assert (
        "Intake feedback story lookup is exact-shape guarded inside the "
        "fulfillment handler's fail-open feedback path"
        in operator_guide
    )
    assert "before truthiness hooks, indexing hooks" in operator_guide
    assert "enrichment `model_copy()` hooks" in operator_guide
    assert "ServiceNow mutation, or feedback artifact writing" in operator_guide
    assert (
        "`test_intake_feedback_rejects_story_collection_subclass_without_log_leak`"
        in change_log
    )
    assert (
        "`test_intake_feedback_rejects_story_item_subclass_without_log_leak`"
        in change_log
    )


def test_sprint_986_documents_model_fulfillment_story_fetch_guard() -> None:
    change_log = Path("docs/sprints/sprint-986-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Model fulfillment story fetch guard" in change_log
    assert "`_model_fulfillment_stories()`" in change_log
    assert "model fulfillment stories contain non-JSON value" in change_log
    assert "1 failing-first model fulfillment story collection assertion" in change_log
    assert (
        "Model fulfillment story lookup is exact-shape guarded before enrichment"
        in operator_guide
    )
    assert "before truthiness hooks, indexing hooks" in operator_guide
    assert "enrichment `model_copy()` hooks" in operator_guide
    assert "ServiceNow context fetches, provider calls" in operator_guide
    assert "story mutation, or artifact-return construction" in operator_guide
    assert (
        "`test_model_candidate_handler_rejects_story_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_model_candidate_handler_rejects_story_item_subclass_without_leak`"
        in change_log
    )


def test_sprint_987_documents_runtime_failure_notifier_story_collection_guard() -> None:
    change_log = Path("docs/sprints/sprint-987-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime failure notifier story collection guard" in change_log
    assert "`_failure_notifier_stories()`" in change_log
    assert "story lookup result is unsafe" in change_log
    assert (
        "1 failing-first failure-notifier story collection subclass assertion"
        in change_log
    )
    assert (
        "`_servicenow_failure_notifier()` validates story lookup collection shape"
        in operator_guide
    )
    assert "before truthiness hooks, indexing hooks" in operator_guide
    assert "ServiceNow mutation, or failure work-note construction" in operator_guide
    assert (
        "`test_servicenow_failure_notifier_rejects_story_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_servicenow_failure_notifier_rejects_alternate_story_iterable`"
        in change_log
    )


def test_sprint_988_documents_artifact_handoff_cli_story_lookup_guard() -> None:
    change_log = Path("docs/sprints/sprint-988-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Artifact handoff CLI story lookup guard" in change_log
    assert "`_cli_story_lookup_results()`" in change_log
    assert "story_lookup_result_unsafe" in change_log
    assert "1 failing-first handoff summary story collection assertion" in change_log
    assert "Artifact handoff CLI story lookup results are exact-shape guarded" in (
        operator_guide
    )
    assert "before truthiness hooks, indexing hooks" in operator_guide
    assert "attachment upload, attachment audit writing" in operator_guide
    assert (
        "`test_cli_write_artifact_handoff_summary_rejects_story_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_cli_attach_delivery_artifacts_rejects_story_collection_subclass_without_leak`"
        in change_log
    )


def test_sprint_989_documents_pipeline_cli_story_lookup_guard() -> None:
    change_log = Path("docs/sprints/sprint-989-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Pipeline CLI story lookup guard" in change_log
    assert "`_pipeline_story_lookup_results()`" in change_log
    assert "story_lookup_result_unsafe" in change_log
    assert "1 failing-first implementation packet story collection assertion" in (
        change_log
    )
    assert "Pipeline and implementation CLI story lookup results are exact-shape guarded" in (
        operator_guide
    )
    assert "before truthiness hooks, indexing hooks" in operator_guide
    assert "pipeline execution, packet generation" in operator_guide
    assert "lifecycle manifest writing, or dry-run writeback planning" in operator_guide
    assert (
        "`test_cli_build_implementation_packet_rejects_story_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_cli_run_lifecycle_smoke_rejects_story_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_cli_run_pdi_rejects_story_collection_subclass_without_leak`"
        in change_log
    )


def test_sprint_990_documents_runtime_split_client_story_lookup_guard() -> None:
    change_log = Path("docs/sprints/sprint-990-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime split-client story lookup guard" in change_log
    assert "`_split_story_lookup_results()`" in change_log
    assert "story lookup result is unsafe" in change_log
    assert "1 failing-first ready-story collection assertion" in change_log
    assert "`SplitServiceNowClient` validates PM/story lookup collection shape" in (
        operator_guide
    )
    assert "`fetch_ready_stories()` and `fetch_stories()`" in operator_guide
    assert "before downstream truthiness hooks, length hooks" in operator_guide
    assert "worker scheduling, pipeline execution" in operator_guide
    assert (
        "`test_split_servicenow_client_rejects_ready_story_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_split_servicenow_client_rejects_story_lookup_collection_subclass_without_leak`"
        in change_log
    )


def test_sprint_991_documents_runtime_split_client_table_record_collection_guard() -> None:
    change_log = Path("docs/sprints/sprint-991-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime split-client table-record collection guard" in change_log
    assert "`_split_table_record_lookup_results()`" in change_log
    assert "table record lookup result is unsafe" in change_log
    assert "1 failing-first table-record collection subclass assertion" in change_log
    assert (
        "`SplitServiceNowClient` also validates development table-record collection shape"
        in operator_guide
    )
    assert "`fetch_table_records()` must return an exact Python list" in operator_guide
    assert "before downstream truthiness hooks, length hooks" in operator_guide
    assert "builder routing, update-set XML generation" in operator_guide
    assert (
        "`test_split_servicenow_client_rejects_table_record_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_split_servicenow_client_rejects_alternate_table_record_collection`"
        in change_log
    )


def test_sprint_992_documents_runtime_split_client_story_metadata_collection_guard() -> None:
    change_log = Path("docs/sprints/sprint-992-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime split-client story metadata collection guard" in change_log
    assert "`_split_story_state_choice_results()`" in change_log
    assert "`_split_story_dictionary_field_results()`" in change_log
    assert "story state choices result is unsafe" in change_log
    assert "story dictionary fields result is unsafe" in change_log
    assert "1 failing-first state-choice collection subclass assertion" in change_log
    assert "`SplitServiceNowClient` validates PM story metadata collection shape too" in (
        operator_guide
    )
    assert "`fetch_story_state_choices()` must return an exact Python list" in (
        operator_guide
    )
    assert "`fetch_story_dictionary_fields()` must return an exact Python list" in (
        operator_guide
    )
    assert "before downstream truthiness hooks, length hooks" in operator_guide
    assert "writeback state mapping, bootstrap checks" in operator_guide
    assert (
        "`test_split_servicenow_client_rejects_state_choice_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_split_servicenow_client_rejects_dictionary_field_collection_subclass`"
        in change_log
    )


def test_sprint_993_documents_runtime_split_client_single_record_response_guard() -> None:
    change_log = Path("docs/sprints/sprint-993-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime split-client single-record response guard" in change_log
    assert "`_split_optional_table_record_result()`" in change_log
    assert "`_split_table_mutation_result()`" in change_log
    assert "`_split_update_set_import_result()`" in change_log
    assert "table record lookup result is unsafe" in change_log
    assert "table mutation result is unsafe" in change_log
    assert "update set import result is unsafe" in change_log
    assert "`SplitServiceNowClient` validates development single-record" in (
        operator_guide
    )
    assert "`fetch_table_record()` returns only `None` or an exact Python dictionary" in (
        operator_guide
    )
    assert "`upsert_table_record()` returns only an exact Python dictionary" in (
        operator_guide
    )
    assert "`import_update_set_xml()` returns only an exact Python dictionary" in (
        operator_guide
    )
    assert "before downstream truthiness hooks, length hooks" in operator_guide
    assert "handoff decisions, or import-status decisions" in operator_guide
    assert (
        "`test_split_servicenow_client_rejects_table_record_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_split_servicenow_client_rejects_upsert_response_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_split_servicenow_client_rejects_update_set_import_response_subclass`"
        in change_log
    )


def test_sprint_994_documents_runtime_split_client_story_mutation_response_guard() -> None:
    change_log = Path("docs/sprints/sprint-994-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime split-client story mutation response guard" in change_log
    assert "`_split_story_mutation_result()`" in change_log
    assert "story mutation result is unsafe" in change_log
    assert "1 failing-first story update response subclass assertion" in change_log
    assert "`SplitServiceNowClient` validates PM story mutation response shape" in (
        operator_guide
    )
    assert "`update_story_fields()` returns only an exact Python dictionary" in (
        operator_guide
    )
    assert "before downstream truthiness hooks, length hooks" in operator_guide
    assert "audit decisions, or notifier completion logic" in operator_guide
    assert (
        "`test_split_servicenow_client_rejects_story_update_response_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_split_servicenow_client_rejects_alternate_story_update_response`"
        in change_log
    )


def test_sprint_995_documents_bootstrap_dictionary_field_planning_guard() -> None:
    change_log = Path("docs/sprints/sprint-995-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Bootstrap dictionary-field planning guard" in change_log
    assert "`_bootstrap_dictionary_fields()`" in change_log
    assert "bootstrap dictionary fields contain non-JSON value" in change_log
    assert "1 failing-first bootstrap dictionary-field collection subclass assertion" in (
        change_log
    )
    assert (
        "Bootstrap story metadata planning validates dictionary-field collection shape"
        in operator_guide
    )
    assert "`plan_bootstrap_fields()` accepts only exact Python lists" in operator_guide
    assert "before iteration hooks, model hooks" in operator_guide
    assert "missing-field decisions, writable-field decisions" in operator_guide
    assert (
        "`test_bootstrap_plan_rejects_dictionary_field_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_bootstrap_plan_rejects_dictionary_field_item_subclass_without_leak`"
        in change_log
    )


def test_sprint_996_documents_bootstrap_apply_response_guard() -> None:
    change_log = Path("docs/sprints/sprint-996-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Bootstrap apply response guard" in change_log
    assert "`_bootstrap_create_field_result()`" in change_log
    assert "`_bootstrap_table_upsert_result()`" in change_log
    assert "bootstrap create field result is unsafe" in change_log
    assert "bootstrap table upsert result is unsafe" in change_log
    assert "1 failing-first bootstrap create-field response subclass assertion" in (
        change_log
    )
    assert "Bootstrap apply validates ServiceNow mutation response shape" in (
        operator_guide
    )
    assert "`apply_bootstrap_fields()` accepts only exact Python dictionaries" in (
        operator_guide
    )
    assert "including dictionary writable-field remediation" in operator_guide
    assert "before truthiness hooks, length hooks" in operator_guide
    assert "platform-read-only result recording" in operator_guide
    assert (
        "`test_apply_bootstrap_fields_rejects_create_field_response_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_apply_bootstrap_fields_rejects_dictionary_upsert_response_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_apply_bootstrap_fields_rejects_platform_policy_response_subclass_without_leak`"
        in change_log
    )


def test_sprint_997_documents_lifecycle_apply_response_guard() -> None:
    change_log = Path("docs/sprints/sprint-997-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Lifecycle webhook apply response guard" in change_log
    assert "`_lifecycle_webhook_upsert_result()`" in change_log
    assert "Lifecycle webhook lookup contains non-JSON value" in change_log
    assert "1 failing-first lifecycle REST message response subclass assertion" in (
        change_log
    )
    assert "Lifecycle webhook bootstrap apply results are strict too" in (
        operator_guide
    )
    assert "`apply_lifecycle_webhook_records()` accepts only exact Python dictionaries" in (
        operator_guide
    )
    assert "before response-field access" in operator_guide
    assert "dependent REST method upserts" in operator_guide
    assert (
        "`test_apply_lifecycle_webhook_records_rejects_rest_message_response_subclass`"
        in change_log
    )
    assert (
        "`test_apply_lifecycle_webhook_records_rejects_method_response_subclass_without_leak`"
        in change_log
    )


def test_sprint_967_documents_update_set_import_metadata_guard() -> None:
    change_log = Path("docs/sprints/sprint-967-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set import metadata guard" in change_log
    assert "`_import_metadata_text()`" in change_log
    assert "retrieved Update Set metadata contains non-JSON value" in change_log
    assert (
        "1 failing-first retrieved Update Set import metadata assertion"
        in change_log
    )
    assert "Retrieved Update Set import metadata also requires exact strings" in (
        operator_guide
    )
    assert "before customer update XML generation, XML escaping" in operator_guide
    assert (
        "`test_import_retrieved_update_set_rejects_metadata_string_subclass_without_leak`"
        in change_log
    )


def test_sprint_968_documents_handoff_story_sys_id_guard() -> None:
    change_log = Path("docs/sprints/sprint-968-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set handoff story sys_id guard" in change_log
    assert "`_handoff_story_sys_id()`" in change_log
    assert "retrieved Update Set handoff story sys_id contains non-JSON value" in (
        change_log
    )
    assert (
        "1 failing-first retrieved Update Set handoff story sys_id assertion"
        in change_log
    )
    assert "Retrieved Update Set story writeback identifiers require exact string" in (
        operator_guide
    )
    assert "before candidate routing, customer-update generation" in operator_guide
    assert (
        "`test_create_update_set_handoff_rejects_story_sys_id_object_without_leak`"
        in change_log
    )


def test_sprint_969_documents_handoff_artifact_ref_guard() -> None:
    change_log = Path("docs/sprints/sprint-969-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Retrieved Update Set handoff artifact reference guard" in change_log
    assert "`_handoff_artifact_ref()`" in change_log
    assert "retrieved Update Set handoff artifact reference contains non-JSON value" in (
        change_log
    )
    assert (
        "1 failing-first retrieved Update Set handoff artifact reference assertion"
        in change_log
    )
    assert "Retrieved Update Set artifact references require exact strings" in (
        operator_guide
    )
    assert "before candidate routing, customer-update generation" in operator_guide
    assert (
        "`test_create_update_set_handoff_rejects_artifact_ref_object_without_leak`"
        in change_log
    )


def test_sprint_879_documents_update_set_apply_element_metadata_guard() -> None:
    change_log = Path("docs/sprints/sprint-879-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply form element metadata guard" in change_log
    assert "1 failing-first Update Set apply form element metadata assertion" in change_log
    assert (
        "Direct Update Set apply form element name comparisons use the primitive-only "
        "metadata boundary"
        in operator_guide
    )
    assert (
        "`test_apply_candidate_rejects_form_element_non_json_element_without_leak`"
        in change_log
    )


def test_sprint_880_documents_update_set_apply_form_candidate_field_guard() -> None:
    change_log = Path("docs/sprints/sprint-880-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply form candidate field guard" in change_log
    assert "1 failing-first Update Set apply form candidate field assertion" in change_log
    assert (
        "Direct Update Set apply form layout candidate fields use a primitive-only input "
        "boundary"
        in operator_guide
    )
    assert (
        "`test_apply_candidate_rejects_form_section_candidate_field_without_leak`"
        in change_log
    )


def test_sprint_881_documents_update_set_apply_dictionary_candidate_field_guard() -> None:
    change_log = Path("docs/sprints/sprint-881-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply dictionary candidate field guard" in change_log
    assert "2 failing-first Update Set apply dictionary candidate field assertions" in change_log
    assert (
        "Direct Update Set apply dictionary candidate fields use a primitive-only input "
        "boundary"
        in operator_guide
    )
    assert (
        "`test_apply_candidate_rejects_dictionary_element_candidate_field_without_leak`"
        in change_log
    )
    assert (
        "`test_apply_candidate_rejects_dictionary_payload_candidate_field_without_leak`"
        in change_log
    )


def test_sprint_882_documents_update_set_apply_candidate_string_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-882-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply candidate string-subclass guard" in change_log
    assert "2 failing-first Update Set apply candidate string-subclass assertions" in change_log
    assert "String subclasses fail with the same candidate non-JSON diagnostic" in operator_guide
    assert (
        "`test_apply_candidate_rejects_dictionary_string_subclass_candidate_field`"
        in change_log
    )
    assert "`test_apply_candidate_rejects_form_string_subclass_candidate_field`" in change_log


def test_sprint_883_documents_update_set_apply_response_string_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-883-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply response string-subclass guard" in change_log
    assert "2 failing-first Update Set apply response string-subclass assertions" in change_log
    assert "Direct Update Set apply ServiceNow response text values require exact strings" in (
        operator_guide
    )
    assert "`test_apply_candidate_rejects_form_element_string_subclass_metadata`" in change_log
    assert "`test_apply_candidate_rejects_string_subclass_integration_user_sys_id`" in change_log


def test_sprint_884_documents_update_set_apply_form_xml_string_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-884-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply form XML string-subclass guard" in change_log
    assert "1 failing-first Update Set apply form XML string-subclass assertion" in change_log
    assert "Direct Update Set apply XML-backed form candidate parsing requires exact strings" in (
        operator_guide
    )
    assert "`test_apply_candidate_rejects_form_xml_string_subclass_candidate_field`" in change_log


def test_sprint_885_documents_update_set_apply_form_placement_candidate_guard() -> None:
    change_log = Path("docs/sprints/sprint-885-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply form placement candidate guard" in change_log
    assert "1 failing-first Update Set apply form placement candidate assertion" in change_log
    assert (
        "Direct Update Set apply form placement candidate fields use the candidate "
        "primitive boundary"
        in operator_guide
    )
    assert "`test_apply_candidate_rejects_form_placement_candidate_field_without_leak`" in (
        change_log
    )


def test_sprint_886_documents_update_set_apply_request_identifier_guard() -> None:
    change_log = Path("docs/sprints/sprint-886-change-log.md").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply request identifier guard" in change_log
    assert "2 failing-first Update Set apply request identifier assertions" in change_log
    assert "Direct Update Set apply request identifiers require exact strings" in operator_guide
    assert "`test_apply_candidate_rejects_request_update_set_sys_id_string_subclass`" in (
        change_log
    )
    assert "`test_apply_candidate_rejects_request_integration_user_string_subclass`" in (
        change_log
    )


def test_sprint_970_documents_update_set_apply_change_identifier_guard() -> None:
    change_log = Path("docs/sprints/sprint-970-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply change identifier guard" in change_log
    assert "`_apply_change_identifier_text()`" in change_log
    assert "Update Set apply change identifier contains non-JSON value" in change_log
    assert "2 failing-first direct Update Set apply change identifier assertions" in (
        change_log
    )
    assert "Direct Update Set apply change identifiers require exact strings" in (
        operator_guide
    )
    assert "before custom dictionary discovery, table routing" in operator_guide
    assert "`test_apply_candidate_rejects_change_table_string_subclass`" in change_log
    assert "`test_apply_candidate_rejects_change_operation_string_subclass`" in (
        change_log
    )


def test_sprint_971_documents_update_set_apply_records_collection_guard() -> None:
    change_log = Path("docs/sprints/sprint-971-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply records collection guard" in change_log
    assert "`_apply_records()`" in change_log
    assert "Update Set apply records contain non-JSON value" in change_log
    assert "2 failing-first direct Update Set apply record collection assertions" in (
        change_log
    )
    assert "Direct Update Set apply ServiceNow record collections require exact lists" in (
        operator_guide
    )
    assert "before section-count checks, form-element iteration" in operator_guide
    assert (
        "`test_apply_candidate_rejects_section_records_collection_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_apply_candidate_rejects_customer_updates_collection_subclass_without_leak`"
        in change_log
    )


def test_sprint_972_documents_update_set_apply_single_record_guard() -> None:
    change_log = Path("docs/sprints/sprint-972-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply single-record lookup guard" in change_log
    assert "`_apply_optional_record()`" in change_log
    assert "Update Set apply record contains non-JSON value" in change_log
    assert "1 failing-first direct Update Set apply single-record assertion" in (
        change_log
    )
    assert (
        "Direct Update Set apply ServiceNow single-record lookups require exact "
        "dictionaries"
        in operator_guide
    )
    assert "before integration-user `sys_id` lookup" in operator_guide
    assert (
        "`test_apply_candidate_rejects_integration_user_record_subclass_without_leak`"
        in change_log
    )


def test_sprint_973_documents_update_set_apply_changes_collection_guard() -> None:
    change_log = Path("docs/sprints/sprint-973-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply changes collection guard" in change_log
    assert "`_apply_changes()`" in change_log
    assert "Update Set apply changes contain non-JSON value" in change_log
    assert "2 failing-first direct Update Set apply changes collection assertions" in (
        change_log
    )
    assert "Direct Update Set apply change collections are exact-list guarded" in (
        operator_guide
    )
    assert "before routing or dictionary discovery" in operator_guide
    assert (
        "`test_apply_candidate_rejects_changes_collection_subclass_without_leak`"
        in change_log
    )
    assert "`test_apply_candidate_rejects_non_candidate_change_without_leak`" in (
        change_log
    )


def test_sprint_974_documents_update_set_apply_change_fields_guard() -> None:
    change_log = Path("docs/sprints/sprint-974-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply change fields container guard" in change_log
    assert "`_apply_change_fields()`" in change_log
    assert "Update Set apply change fields contain non-JSON value" in change_log
    assert "2 failing-first direct Update Set apply change field container assertions" in (
        change_log
    )
    assert "Direct Update Set apply change field containers require exact dictionaries" in (
        operator_guide
    )
    assert "before dictionary normalization, form planning" in operator_guide
    assert (
        "`test_apply_candidate_rejects_dictionary_change_fields_subclass_without_leak`"
        in change_log
    )
    assert (
        "`test_apply_candidate_rejects_form_change_fields_subclass_without_leak`"
        in change_log
    )


def test_sprint_975_documents_update_set_apply_change_field_key_guard() -> None:
    change_log = Path("docs/sprints/sprint-975-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply change field key guard" in change_log
    assert "`_apply_change_fields()`" in change_log
    assert "Update Set apply change fields contain non-JSON value" in change_log
    assert "2 failing-first direct Update Set apply field-key assertions" in change_log
    assert (
        "Direct Update Set apply change field containers require exact dictionaries "
        "with exact string keys"
        in operator_guide
    )
    assert "malformed field keys, string-subclass field keys" in operator_guide
    assert (
        "`test_apply_candidate_rejects_dictionary_change_field_key_object_without_leak`"
        in change_log
    )
    assert (
        "`test_apply_candidate_rejects_form_change_field_key_string_subclass`"
        in change_log
    )


def test_sprint_976_documents_update_set_apply_dictionary_discovery_identifier_guard() -> None:
    change_log = Path("docs/sprints/sprint-976-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Update Set apply dictionary discovery identifier guard" in change_log
    assert "`_custom_dictionary_elements()`" in change_log
    assert "`_apply_change_identifier_text()`" in change_log
    assert "Update Set apply change identifier contains non-JSON value" in change_log
    assert (
        "1 failing-first direct Update Set apply dictionary discovery assertion"
        in change_log
    )
    assert "before custom dictionary discovery, table routing" in operator_guide
    assert (
        "`test_apply_candidate_rejects_change_table_object_before_dictionary_discovery`"
        in change_log
    )


def test_sprint_1019_documents_validation_helper_decimal_input_guard() -> None:
    change_log = Path("docs/sprints/sprint-1019-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Validation helper Decimal input guard" in change_log
    assert "`_scalar_text()`" in change_log
    assert "generation field scalar value contains non-JSON value" in change_log
    assert "1 failing-first optional-int Decimal assertion" in change_log
    assert "1 failing-first bool-value Decimal assertion" in change_log
    assert "Shared generation field scalar normalization rejects Decimal values" in (
        operator_guide
    )
    assert (
        "`test_optional_int_rejects_decimal_without_value_leak`" in change_log
    )
    assert "`test_bool_value_rejects_decimal_without_value_leak`" in change_log


def test_sprint_1020_documents_validation_helper_slug_string_subclass_guard() -> None:
    change_log = Path("docs/sprints/sprint-1020-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Validation helper slug string-subclass guard" in change_log
    assert "`slug()`" in change_log
    assert "generation field scalar value contains non-JSON value" in change_log
    assert "1 failing-first slug value string-subclass assertion" in change_log
    assert "1 failing-first slug default string-subclass assertion" in change_log
    assert "Shared generation-field slug creation requires exact strings" in (
        operator_guide
    )
    assert "before calling `.strip()`, `.lower()`, regex normalization" in (
        operator_guide
    )
    assert (
        "`test_slug_rejects_string_subclass_without_string_method_execution`"
        in change_log
    )
    assert (
        "`test_slug_rejects_default_string_subclass_without_value_leak`"
        in change_log
    )


def test_sprint_1021_documents_stable_record_sys_id_part_guard() -> None:
    change_log = Path("docs/sprints/sprint-1021-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Stable record sys_id part guard" in change_log
    assert "`stable_record_sys_id()`" in change_log
    assert "generation field scalar value contains non-JSON value" in change_log
    assert "1 failing-first stable sys_id string-subclass assertion" in change_log
    assert "1 failing-first stable sys_id non-string assertion" in change_log
    assert "Stable generated record sys_id derivation requires exact string name parts" in (
        operator_guide
    )
    assert "before joining parts, UTF-8 encoding, or SHA-256 hashing" in (
        operator_guide
    )
    assert (
        "`test_stable_record_sys_id_rejects_string_subclass_without_value_leak`"
        in change_log
    )
    assert (
        "`test_stable_record_sys_id_rejects_non_string_without_type_leak`"
        in change_log
    )


def test_sprint_1022_documents_runtime_config_scalar_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-1022-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime config scalar exact-string guard" in change_log
    assert "`_bool_value()`" in change_log
    assert "`_enum_value()`" in change_log
    assert "`_runtime_environment_value()`" in change_log
    assert "<SETTING> must be a string runtime" in change_log
    assert "setting`." in change_log
    assert "1 failing-first runtime boolean scalar assertion" in change_log
    assert "1 failing-first runtime enum scalar assertion" in change_log
    assert "1 failing-first runtime environment scalar assertion" in change_log
    assert (
        "Runtime boolean, enum, and environment-mode settings require exact strings"
        in operator_guide
    )
    assert "before truthiness checks, `str()` conversion" in operator_guide
    assert (
        "`test_runtime_config_bool_value_rejects_non_string_without_truthiness_leak`"
        in change_log
    )
    assert (
        "`test_runtime_config_enum_value_rejects_string_subclass_without_string_leak`"
        in change_log
    )
    assert (
        "`test_runtime_environment_value_rejects_non_string_without_value_leak`"
        in change_log
    )


def test_sprint_1023_documents_split_servicenow_env_fallback_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-1023-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Split ServiceNow env fallback exact-string guard" in change_log
    assert "`_env_value()`" in change_log
    assert "`_blank_split_servicenow_override_errors()`" in change_log
    assert "<SETTING> must be a string runtime" in change_log
    assert "setting`." in change_log
    assert "1 failing-first split ServiceNow fallback assertion" in change_log
    assert "1 failing-first blank split ServiceNow override assertion" in change_log
    assert "Split ServiceNow fallback resolution is exact-string guarded" in (
        operator_guide
    )
    assert "before truthiness checks, fallback selection" in operator_guide
    assert (
        "`test_runtime_env_value_rejects_non_string_primary_without_truthiness_leak`"
        in change_log
    )
    assert (
        "`test_blank_split_servicenow_overrides_reject_non_string_without_value_leak`"
        in change_log
    )


def test_sprint_1024_documents_runtime_store_and_audit_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-1024-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime store and audit exact-string guard" in change_log
    assert "`DATABASE_URL`" in change_log
    assert "`JEDI_AUDIT_ROOT`" in change_log
    assert "<SETTING> must be a string runtime setting" in change_log
    assert "1 failing-first database URL scalar assertion" in change_log
    assert "1 failing-first audit root scalar assertion" in change_log
    assert "Required store and audit values are exact-string guarded" in (
        operator_guide
    )
    assert "before URL parsing" in operator_guide
    assert "`Path(...)` construction" in operator_guide
    assert (
        "`test_load_runtime_settings_rejects_non_string_database_url_without_value_leak`"
        in change_log
    )
    assert (
        "`test_load_runtime_settings_rejects_non_string_audit_root_without_value_leak`"
        in change_log
    )


def test_sprint_1025_documents_runtime_csv_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-1025-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime CSV exact-string guard" in change_log
    assert "`_csv_values()`" in change_log
    assert "<SETTING> must be a string runtime setting" in change_log
    assert "`JEDI_PUBLIC_WEB_ALLOWED_DOMAINS`" in change_log
    assert "`JEDI_PUBLIC_WEB_DOC_URLS`" in change_log
    assert "1 failing-first runtime CSV non-string assertion" in change_log
    assert "1 failing-first runtime CSV string-subclass assertion" in change_log
    assert "Runtime CSV parsing is exact-string guarded before splitting" in (
        operator_guide
    )
    assert "before `.split()`" in operator_guide
    assert (
        "`test_runtime_csv_values_rejects_non_string_without_truthiness_leak`"
        in change_log
    )
    assert (
        "`test_runtime_csv_values_rejects_string_subclass_without_method_leak`"
        in change_log
    )


def test_sprint_1026_documents_runtime_optional_setting_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-1026-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime optional setting exact-string guard" in change_log
    assert "`_optional_model_provider()`" in change_log
    assert "`_optional_alert_webhook_url()`" in change_log
    assert "`_optional_admin_console_credential()`" in change_log
    assert "`_optional_openai_provider_value()`" in change_log
    assert "<SETTING> must be a string runtime setting" in change_log
    assert "`JEDI_MODEL_PROVIDER`" in change_log
    assert "`JEDI_ALERT_WEBHOOK_URL`" in change_log
    assert "`JEDI_ADMIN_USERNAME`" in change_log
    assert "`OPENAI_MODEL`" in change_log
    assert "1 failing-first optional model provider string-subclass assertion" in (
        change_log
    )
    assert "1 failing-first optional alert webhook non-string assertion" in change_log
    assert "1 failing-first optional admin credential string-subclass assertion" in (
        change_log
    )
    assert "1 failing-first optional OpenAI setting string-subclass assertion" in (
        change_log
    )
    assert "Optional runtime settings are exact-string guarded" in operator_guide
    assert "before `.strip()`" in operator_guide
    assert "admin credential" in operator_guide
    assert "byte-length checks" in operator_guide
    assert (
        "`test_optional_model_provider_rejects_string_subclass_without_method_leak`"
        in change_log
    )
    assert (
        "`test_optional_alert_webhook_url_rejects_non_string_without_equality_leak`"
        in change_log
    )
    assert (
        "`test_optional_admin_console_credential_rejects_string_subclass_without_method_leak`"
        in change_log
    )
    assert (
        "`test_optional_openai_provider_value_rejects_string_subclass_without_method_leak`"
        in change_log
    )


def test_sprint_1027_documents_direct_runtime_mode_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-1027-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Direct runtime mode exact-string guard" in change_log
    assert "`_runtime_environment()`" in change_log
    assert "`_runtime_role()`" in change_log
    assert "`RuntimeSettings.runtime_environment`" in change_log
    assert "`RuntimeSettings.runtime_role`" in change_log
    assert "`JEDI_ENVIRONMENT`" in change_log
    assert "`JEDI_RUNTIME_ROLE`" in change_log
    assert "<SETTING> must be a string runtime" in change_log
    assert "setting`." in change_log
    assert (
        "1 failing-first direct runtime environment string-subclass assertion"
        in change_log
    )
    assert "1 failing-first direct runtime role non-string assertion" in change_log
    assert "Direct runtime mode and role validation is exact-string guarded" in (
        operator_guide
    )
    assert "before `.strip()`" in operator_guide
    assert "`str()` conversion" in operator_guide
    assert "production/development branching" in operator_guide
    assert (
        "`test_validate_runtime_settings_rejects_runtime_environment_string_subclass_without_method_leak`"
        in change_log
    )
    assert (
        "`test_validate_runtime_settings_rejects_runtime_role_non_string_without_str_leak`"
        in change_log
    )


def test_sprint_1028_documents_direct_production_credential_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-1028-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Direct production credential exact-string guard" in change_log
    assert "`_direct_optional_runtime_setting_text()`" in change_log
    assert "`RuntimeSettings.lifecycle_webhook_secret`" in change_log
    assert "`RuntimeSettings.admin_api_token`" in change_log
    assert "`JEDI_LIFECYCLE_WEBHOOK_SECRET`" in change_log
    assert "`JEDI_ADMIN_API_TOKEN`" in change_log
    assert "<SETTING> must be a string runtime" in change_log
    assert "setting`." in change_log
    assert (
        "1 failing-first direct lifecycle webhook secret string-subclass assertion"
        in change_log
    )
    assert "1 failing-first direct admin API token string-subclass assertion" in (
        change_log
    )
    assert "Direct production credential validation follows the same exact-string boundary" in (
        operator_guide
    )
    assert "before truthiness checks" in operator_guide
    assert "`len()`" in operator_guide
    assert "admin-auth requirement checks" in operator_guide
    assert (
        "`test_validate_runtime_settings_rejects_webhook_secret_string_subclass_without_len_leak`"
        in change_log
    )
    assert (
        "`test_validate_runtime_settings_rejects_admin_api_token_string_subclass_without_len_leak`"
        in change_log
    )


def test_sprint_1029_documents_direct_auth_mode_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-1029-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Direct auth mode exact-string guard" in change_log
    assert "`RuntimeSettings.lifecycle_webhook_auth_mode`" in change_log
    assert "`RuntimeSettings.admin_auth_mode`" in change_log
    assert "`JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE`" in change_log
    assert "`JEDI_ADMIN_AUTH_MODE`" in change_log
    assert "<SETTING> must be a string runtime" in change_log
    assert "setting`." in change_log
    assert (
        "1 failing-first direct lifecycle webhook auth mode string-subclass assertion"
        in change_log
    )
    assert "1 failing-first direct admin auth mode non-string assertion" in change_log
    assert "Direct auth-mode validation is exact-string guarded" in operator_guide
    assert "before equality checks" in operator_guide
    assert "`str()` conversion" in operator_guide
    assert "unimplemented-auth diagnostics" in operator_guide
    assert (
        "`test_validate_runtime_settings_rejects_lifecycle_auth_mode_string_subclass_without_eq_leak`"
        in change_log
    )
    assert (
        "`test_validate_runtime_settings_rejects_admin_auth_mode_non_string_without_str_leak`"
        in change_log
    )


def test_sprint_1030_documents_direct_model_setting_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-1030-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Direct model setting exact-string guard" in change_log
    assert "`RuntimeSettings.model_provider`" in change_log
    assert "`RuntimeSettings.openai_api_key`" in change_log
    assert "`RuntimeSettings.openai_model`" in change_log
    assert "`JEDI_MODEL_PROVIDER`" in change_log
    assert "`OPENAI_API_KEY`" in change_log
    assert "`OPENAI_MODEL`" in change_log
    assert "<SETTING> must be a string runtime" in change_log
    assert "setting`." in change_log
    assert "1 failing-first direct model provider string-subclass assertion" in (
        change_log
    )
    assert "1 failing-first direct OpenAI API key string-subclass assertion" in (
        change_log
    )
    assert "Direct model-provider validation is exact-string guarded" in operator_guide
    assert "before truthiness checks" in operator_guide
    assert "model-provider length checks" in operator_guide
    assert "OpenAI-required-field checks" in operator_guide
    assert (
        "`test_validate_runtime_settings_rejects_model_provider_string_subclass_without_len_leak`"
        in change_log
    )
    assert (
        "`test_validate_runtime_settings_rejects_openai_api_key_string_subclass_without_truthiness_leak`"
        in change_log
    )


def test_sprint_1031_documents_direct_public_web_access_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-1031-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Direct public web access exact-string guard" in change_log
    assert "`RuntimeSettings.public_web_access`" in change_log
    assert "`JEDI_PUBLIC_WEB_ACCESS`" in change_log
    assert "JEDI_PUBLIC_WEB_ACCESS must be a string runtime setting" in change_log
    assert "1 failing-first direct public-web access string-subclass assertion" in (
        change_log
    )
    assert "Direct public-web access validation is exact-string guarded" in (
        operator_guide
    )
    assert "before equality checks" in operator_guide
    assert "API-role worker-only checks" in operator_guide
    assert "required allowlist checks" in operator_guide
    assert (
        "`test_validate_runtime_settings_rejects_public_web_access_string_subclass_without_eq_leak`"
        in change_log
    )


def test_sprint_1032_documents_direct_worker_id_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-1032-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Direct worker id exact-string guard" in change_log
    assert "`RuntimeSettings.worker_id`" in change_log
    assert "`JEDI_WORKER_ID`" in change_log
    assert "JEDI_WORKER_ID must be a string runtime setting" in change_log
    assert "1 failing-first direct worker id string-subclass assertion" in change_log
    assert "Direct `RuntimeSettings.worker_id` validation is exact-string guarded" in (
        operator_guide
    )
    assert "before truthiness checks" in operator_guide
    assert "control-character scans" in operator_guide
    assert "job-event audit metadata" in operator_guide
    assert (
        "`test_validate_runtime_settings_rejects_worker_id_string_subclass_without_truthiness_leak`"
        in change_log
    )


def test_sprint_1033_documents_direct_update_set_user_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-1033-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Direct Update Set user exact-string guard" in change_log
    assert "`RuntimeSettings.update_set_user_name`" in change_log
    assert "`JEDI_UPDATE_SET_USER_NAME`" in change_log
    assert "JEDI_UPDATE_SET_USER_NAME must be a string runtime setting" in (
        change_log
    )
    assert (
        "1 failing-first direct update-set user name string-subclass assertion"
        in change_log
    )
    assert (
        "Direct `RuntimeSettings.update_set_user_name` validation is exact-string guarded"
        in operator_guide
    )
    assert "before truthiness checks" in operator_guide
    assert "control-character scans" in operator_guide
    assert "local Update Set apply audit metadata" in operator_guide
    assert (
        "`test_validate_runtime_settings_rejects_update_set_apply_operator_string_subclass_without_leak`"
        in change_log
    )


def test_sprint_1034_documents_direct_public_web_list_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-1034-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Direct public-web list exact-string guard" in change_log
    assert "`RuntimeSettings.public_web_allowed_domains`" in change_log
    assert "`RuntimeSettings.public_web_doc_urls`" in change_log
    assert "JEDI_PUBLIC_WEB_ALLOWED_DOMAINS must be a string list setting" in (
        change_log
    )
    assert "JEDI_PUBLIC_WEB_DOC_URLS must be a string list setting" in change_log
    assert (
        "1 failing-first direct public-web allowed-domain string-subclass assertion"
        in change_log
    )
    assert (
        "Direct public-web allowlist and documentation URL collections are exact-list guarded"
        in operator_guide
    )
    assert "before truthiness checks" in operator_guide
    assert "hostname normalization" in operator_guide
    assert "public-documentation egress controls" in operator_guide
    assert (
        "`test_validate_runtime_settings_rejects_public_web_allowed_domains_string_subclass_without_leak`"
        in change_log
    )


def test_sprint_1035_documents_direct_integer_runtime_exact_type_guard() -> None:
    change_log = Path("docs/sprints/sprint-1035-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Direct integer runtime exact-type guard" in change_log
    assert "direct integer runtime setting validation" in change_log
    assert "<SETTING> must be an integer runtime setting" in change_log
    assert "1 failing-first direct positive integer setting subclass assertion" in (
        change_log
    )
    assert "Direct integer runtime settings are exact-integer guarded" in (
        operator_guide
    )
    assert "before comparison operators" in operator_guide
    assert "positive-value checks" in operator_guide
    assert "public-web size and result limits" in operator_guide
    assert (
        "`test_validate_runtime_settings_rejects_positive_int_setting_subclass_without_leak`"
        in change_log
    )


def test_sprint_1036_documents_direct_timeout_finite_number_guard() -> None:
    change_log = Path("docs/sprints/sprint-1036-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Direct timeout finite-number guard" in change_log
    assert "direct outbound timeout validation" in change_log
    assert "<SETTING> must be a finite number runtime setting" in change_log
    assert "1 failing-first direct timeout setting subclass assertion" in change_log
    assert "Direct outbound timeout runtime settings are exact finite-number guarded" in (
        operator_guide
    )
    assert "before comparison operators" in operator_guide
    assert "positive-value checks" in operator_guide
    assert "`JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS`" in operator_guide
    assert "`JEDI_PUBLIC_WEB_TIMEOUT_SECONDS`" in operator_guide
    assert (
        "`test_validate_runtime_settings_rejects_timeout_setting_subclass_without_leak`"
        in change_log
    )


def test_sprint_1037_documents_direct_boolean_runtime_exact_type_guard() -> None:
    change_log = Path("docs/sprints/sprint-1037-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Direct boolean runtime exact-type guard" in change_log
    assert "direct boolean runtime setting validation" in change_log
    assert "<SETTING> must be a boolean runtime setting" in change_log
    assert "1 failing-first direct boolean setting object assertion" in change_log
    assert "Direct boolean runtime settings are exact-boolean guarded" in (
        operator_guide
    )
    assert "before `__bool__` execution" in operator_guide
    assert "fail-closed classifier validation" in operator_guide
    assert "`JEDI_ALLOW_COMBINED_PRODUCTION`" in operator_guide
    assert "`JEDI_CLASSIFIER_GATE`" in operator_guide
    assert (
        "`test_validate_runtime_settings_rejects_boolean_setting_object_without_leak`"
        in change_log
    )


def test_sprint_1038_documents_direct_build_claim_state_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-1038-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Direct build-claim state exact-string guard" in change_log
    assert "`JEDI_BUILD_CLAIM_FROM_STATE`" in change_log
    assert "`JEDI_BUILD_CLAIM_STATE`" in change_log
    assert "JEDI_BUILD_CLAIM_FROM_STATE must be a string runtime setting" in (
        change_log
    )
    assert "1 failing-first direct build-claim state string-subclass assertion" in (
        change_log
    )
    assert (
        "Direct `RuntimeSettings.build_claim_from_state` and "
        "`RuntimeSettings.build_claim_state` validation is exact-string guarded"
        in operator_guide
    )
    assert "before truthiness checks" in operator_guide
    assert "ServiceNow claim transition metadata" in operator_guide
    assert (
        "`test_validate_runtime_settings_rejects_build_claim_state_string_subclass_without_leak`"
        in change_log
    )


def test_sprint_1039_documents_direct_alert_webhook_url_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-1039-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Direct alert webhook URL exact-string guard" in change_log
    assert "`RuntimeSettings.alert_webhook_url`" in change_log
    assert "`JEDI_ALERT_WEBHOOK_URL`" in change_log
    assert "JEDI_ALERT_WEBHOOK_URL must be a string runtime setting" in change_log
    assert "1 failing-first direct alert webhook URL string-subclass assertion" in (
        change_log
    )
    assert (
        "Direct `RuntimeSettings.alert_webhook_url` validation is exact-string guarded"
        in operator_guide
    )
    assert "before truthiness checks" in operator_guide
    assert "SSRF validation" in operator_guide
    assert "outbound alert delivery configuration" in operator_guide
    assert (
        "`test_validate_runtime_settings_rejects_alert_webhook_url_string_subclass_without_leak`"
        in change_log
    )


def test_sprint_1040_documents_direct_audit_root_exact_path_guard() -> None:
    change_log = Path("docs/sprints/sprint-1040-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Direct audit root exact-path guard" in change_log
    assert "`RuntimeSettings.audit_root`" in change_log
    assert "`JEDI_AUDIT_ROOT`" in change_log
    assert "JEDI_AUDIT_ROOT must be a path runtime setting" in change_log
    assert "1 failing-first direct audit-root object assertion" in change_log
    assert (
        "Direct `RuntimeSettings.audit_root` validation is exact concrete-path guarded"
        in operator_guide
    )
    assert "before `str()`" in operator_guide
    assert "`is_absolute()`" in operator_guide
    assert "local audit evidence storage" in operator_guide
    assert (
        "`test_validate_runtime_settings_rejects_direct_audit_root_object_without_leak`"
        in change_log
    )


def test_sprint_1041_documents_direct_database_url_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-1041-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Direct database URL exact-string guard" in change_log
    assert "`RuntimeSettings.database_url`" in change_log
    assert "`DATABASE_URL`" in change_log
    assert "DATABASE_URL must be a string runtime setting" in change_log
    assert "1 failing-first direct database URL string-subclass assertion" in (
        change_log
    )
    assert (
        "Direct `RuntimeSettings.database_url` validation is exact-string guarded"
        in operator_guide
    )
    assert "before URL parsing" in operator_guide
    assert "PostgreSQL operational store boundary" in operator_guide
    assert (
        "`test_validate_runtime_settings_rejects_database_url_string_subclass_without_leak`"
        in change_log
    )


def test_sprint_1042_documents_direct_servicenow_url_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-1042-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Direct ServiceNow instance URL exact-string guard" in change_log
    assert "`SERVICENOW_INSTANCE_URL`" in change_log
    assert "`SERVICENOW_PM_INSTANCE_URL`" in change_log
    assert "`SERVICENOW_DEV_INSTANCE_URL`" in change_log
    assert "<SETTING> must be a string runtime setting" in change_log
    assert "1 failing-first direct ServiceNow instance URL string-subclass assertion" in (
        change_log
    )
    assert (
        "Direct `RuntimeSettings.servicenow_instance_url`, "
        "`RuntimeSettings.servicenow_pm_instance_url`, and "
        "`RuntimeSettings.servicenow_dev_instance_url` validation is exact-string guarded"
        in operator_guide
    )
    assert "before URL parsing" in operator_guide
    assert "source and target ServiceNow instance boundaries" in operator_guide
    assert (
        "`test_validate_runtime_settings_rejects_servicenow_instance_url_string_subclass_without_leak`"
        in change_log
    )


def test_sprint_1043_documents_direct_servicenow_oauth_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-1043-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Direct ServiceNow OAuth credential exact-string guard" in change_log
    assert "`SERVICENOW_CLIENT_ID`" in change_log
    assert "`SERVICENOW_CLIENT_SECRET`" in change_log
    assert "`SERVICENOW_PM_CLIENT_ID`" in change_log
    assert "`SERVICENOW_PM_CLIENT_SECRET`" in change_log
    assert "`SERVICENOW_DEV_CLIENT_ID`" in change_log
    assert "`SERVICENOW_DEV_CLIENT_SECRET`" in change_log
    assert "<SETTING> must be a string runtime setting" in change_log
    assert "1 failing-first direct ServiceNow OAuth credential string-subclass assertion" in (
        change_log
    )
    assert (
        "Direct `RuntimeSettings.servicenow_client_id`, "
        "`RuntimeSettings.servicenow_client_secret`, "
        "`RuntimeSettings.servicenow_pm_client_id`, "
        "`RuntimeSettings.servicenow_pm_client_secret`, "
        "`RuntimeSettings.servicenow_dev_client_id`, and "
        "`RuntimeSettings.servicenow_dev_client_secret` validation is exact-string guarded"
        in operator_guide
    )
    assert "before truthiness checks" in operator_guide
    assert "ServiceNow OAuth boundaries" in operator_guide
    assert (
        "`test_validate_runtime_settings_rejects_servicenow_oauth_secret_string_subclass_without_leak`"
        in change_log
    )


def test_sprint_1044_documents_direct_admin_console_credential_exact_string_guard() -> None:
    change_log = Path("docs/sprints/sprint-1044-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Direct admin console credential exact-string guard" in change_log
    assert "`JEDI_ADMIN_CONSOLE_USERNAME`" in change_log
    assert "`JEDI_ADMIN_CONSOLE_PASSWORD`" in change_log
    assert "<SETTING> must be a string runtime setting" in change_log
    assert "1 failing-first direct admin console credential string-subclass assertion" in (
        change_log
    )
    assert (
        "Direct `RuntimeSettings.admin_console_username` and "
        "`RuntimeSettings.admin_console_password` validation is exact-string guarded"
        in operator_guide
    )
    assert "before production role-policy checks" in operator_guide
    assert "local development Basic-auth credentials" in operator_guide
    assert (
        "`test_validate_runtime_settings_rejects_admin_console_password_string_subclass_without_leak`"
        in change_log
    )


def test_sprint_1045_documents_runtime_role_helper_normalized_input_boundary() -> None:
    change_log = Path("docs/sprints/sprint-1045-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime role helper normalized-input boundary" in change_log
    assert "`_api_runtime_role_errors()`" in change_log
    assert "`_worker_runtime_role_errors()`" in change_log
    assert "`settings.model_provider`" in change_log
    assert "`settings.lifecycle_webhook_auth_mode`" in change_log
    assert "shared exact-string, exact-boolean, and exact-integer runtime setting boundaries" in (
        change_log
    )
    assert "1 failing-first structural role-helper assertion" in change_log
    assert (
        "Production runtime role-policy helpers consume normalized values only"
        in operator_guide
    )
    assert "no longer read raw `RuntimeSettings` attributes" in operator_guide
    assert "worker-only provider settings" in operator_guide
    assert "API-only webhook/admin settings" in operator_guide
    assert (
        "`test_runtime_role_helpers_do_not_read_raw_settings_for_normalized_fields`"
        in change_log
    )


def test_sprint_1046_documents_worker_fulfillment_runtime_role_validation_order() -> None:
    change_log = Path("docs/sprints/sprint-1046-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Worker fulfillment runtime-role validation order" in change_log
    assert "`process_one_runtime_fulfillment()`" in change_log
    assert "`validate_runtime_settings()`" in change_log
    assert "`RuntimeSettings.runtime_role`" in change_log
    assert "JEDI_RUNTIME_ROLE must be a string runtime setting" in change_log
    assert "1 failing-first worker fulfillment startup-order assertion" in change_log
    assert (
        "Runtime role validation runs before development-mode startup exits"
        in operator_guide
    )
    assert "before worker fulfillment rejects API-only runtime roles" in operator_guide
    assert "before checking whether the role is `api`" in operator_guide
    assert (
        "`test_process_one_runtime_fulfillment_validates_runtime_role_before_api_role_branch`"
        in change_log
    )


def test_sprint_1047_documents_embedded_worker_runtime_mode_exact_string_boundary() -> None:
    change_log = Path("docs/sprints/sprint-1047-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Embedded worker runtime mode exact-string boundary" in change_log
    assert "`run_once()`" in change_log
    assert "`run_loop()`" in change_log
    assert "`RuntimeSettings.runtime_role`" in change_log
    assert "`RuntimeSettings.runtime_environment`" in change_log
    assert "2 failing-first embedded worker direct-object assertions" in change_log
    assert (
        "Embedded worker runtime mode checks use the same exact-string boundary"
        in operator_guide
    )
    assert "before worker role branching" in operator_guide
    assert "production stop-on-failure checks" in operator_guide
    assert (
        "`test_run_once_validates_runtime_role_before_api_role_branch`" in change_log
    )
    assert (
        "`test_run_loop_validates_runtime_environment_before_stop_on_failure_branch`"
        in change_log
    )


def test_sprint_1048_documents_maintenance_database_url_boundary() -> None:
    change_log = Path("docs/sprints/sprint-1048-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Maintenance database URL boundary" in change_log
    assert "`prune_operational_store()`" in change_log
    assert "`requeue_stale_running_jobs()`" in change_log
    assert "`RuntimeSettings.database_url`" in change_log
    assert "same exact-string and PostgreSQL URL hygiene checks" in change_log
    assert "4 failing-first maintenance database URL assertions" in change_log
    assert (
        "Direct retention pruning also validates the runtime database URL before opening"
        in operator_guide
    )
    assert (
        "Direct stale-job recovery also validates the runtime database URL before opening"
        in operator_guide
    )
    assert "same exact-string and PostgreSQL URL hygiene boundary" in operator_guide
    assert (
        "`test_prune_operational_store_rejects_database_url_string_subclass_before_store_open`"
        in change_log
    )
    assert (
        "`test_requeue_stale_running_jobs_rejects_malformed_database_url_before_store_open`"
        in change_log
    )


def test_sprint_1049_documents_alert_emission_direct_settings_boundary() -> None:
    change_log = Path("docs/sprints/sprint-1049-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Alert emission direct settings boundary" in change_log
    assert "`_emit_worker_failure_alert()`" in change_log
    assert "`_emit_stale_requeue_alert()`" in change_log
    assert "`RuntimeSettings.alert_webhook_url`" in change_log
    assert "`RuntimeSettings.alert_webhook_max_body_bytes`" in change_log
    assert "before constructing alert payloads or invoking transport" in change_log
    assert "2 failing-first direct alert settings assertions" in change_log
    assert (
        "Direct worker alert emitters validate `RuntimeSettings.alert_webhook_url`"
        in operator_guide
    )
    assert "before alert payload construction or transport use" in operator_guide
    assert "RuntimeConfigError diagnostics that name the runtime setting" in operator_guide
    assert (
        "`test_emit_worker_failure_alert_rejects_alert_url_subclass_before_transport`"
        in change_log
    )
    assert (
        "`test_emit_stale_requeue_alert_rejects_invalid_body_limit_before_transport`"
        in change_log
    )


def test_sprint_1050_documents_runtime_handler_model_routing_boundary() -> None:
    change_log = Path("docs/sprints/sprint-1050-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime handler model-routing direct settings boundary" in change_log
    assert "`_runtime_handler()`" in change_log
    assert "`RuntimeSettings.model_provider`" in change_log
    assert "`RuntimeSettings.openai_api_key`" in change_log
    assert "`RuntimeSettings.openai_model`" in change_log
    assert "`RuntimeSettings.public_web_access`" in change_log
    assert "before provider construction" in change_log
    assert "2 failing-first runtime handler boundary assertions" in change_log
    assert (
        "Runtime fulfillment handler assembly uses the same exact-string boundary"
        in operator_guide
    )
    assert "before constructing model providers" in operator_guide
    assert "public documentation retrievers" in operator_guide
    assert "claim-handler execution" in operator_guide
    assert (
        "`test_runtime_handler_rejects_model_provider_subclass_before_len`"
        in change_log
    )
    assert (
        "`test_runtime_handler_rejects_public_web_access_subclass_before_eq`"
        in change_log
    )


def test_sprint_1051_documents_servicenow_runtime_client_boundary() -> None:
    change_log = Path("docs/sprints/sprint-1051-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "ServiceNow runtime client direct settings boundary" in change_log
    assert "`_servicenow_runtime_connection_settings()`" in change_log
    assert "`_servicenow_story_client_from_settings()`" in change_log
    assert "`_servicenow_development_client_from_settings()`" in change_log
    assert "`_servicenow_pm_and_dev_settings_match()`" in change_log
    assert "before fallback selection" in change_log
    assert "2 failing-first ServiceNow runtime construction assertions" in change_log
    assert (
        "Runtime ServiceNow client construction uses the same exact-string"
        in operator_guide
    )
    assert "before resolving PM/story and development-instance fallbacks" in operator_guide
    assert "before truthiness fallback" in operator_guide
    assert "equality checks" in operator_guide
    assert (
        "`test_servicenow_story_client_rejects_pm_url_subclass_before_fallback_truthiness`"
        in change_log
    )
    assert (
        "`test_servicenow_pm_dev_match_rejects_secret_subclass_before_equality`"
        in change_log
    )


def test_sprint_1052_documents_runtime_auth_configured_settings_boundary() -> None:
    change_log = Path("docs/sprints/sprint-1052-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime auth configured settings boundary" in change_log
    assert "`_require_admin_token()`" in change_log
    assert "`_require_admin_console_credentials()`" in change_log
    assert "`RuntimeSettings.admin_api_token`" in change_log
    assert "`RuntimeSettings.admin_auth_mode`" in change_log
    assert "`RuntimeSettings.runtime_environment`" in change_log
    assert "`RuntimeSettings.admin_console_password`" in change_log
    assert "before bearer-token comparison" in change_log
    assert "3 failing-first request-time admin auth boundary assertions" in change_log
    assert "Request-time admin authentication also exact-string validates" in operator_guide
    assert "before credential parsing or constant-time comparison" in operator_guide
    assert "Basic-auth decoding" in operator_guide
    assert "bearer-token comparison" in operator_guide
    assert (
        "`test_admin_console_rejects_auth_mode_subclass_before_equality`"
        in change_log
    )
    assert (
        "`test_admin_console_rejects_password_subclass_before_compare`"
        in change_log
    )
    assert (
        "`test_admin_bearer_token_rejects_configured_token_subclass_before_compare`"
        in change_log
    )


def test_sprint_1053_documents_runtime_env_template_coverage() -> None:
    change_log = Path("docs/sprints/sprint-1053-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Runtime Env Template Coverage" in change_log
    assert "every `JEDI_*` and `OPENAI_*`" in change_log
    assert "`load_runtime_settings()`" in change_log
    assert "role selection" in change_log
    assert "public-document retrieval" in change_log
    assert "`docs/operator-guide.md`" in change_log
    assert "synchronized production operator template" in operator_guide
    assert "fill required secrets in the deployment" in operator_guide
    assert (
        "`test_env_example_documents_all_runtime_environment_controls`"
        in change_log
    )


def test_sprint_1054_documents_admin_operations_summary() -> None:
    change_log = Path("docs/sprints/sprint-1054-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Admin Operations Summary" in change_log
    assert "`fulfillment_job_status_summary()`" in change_log
    assert "`FulfillmentJobStatusSummaryRecord`" in change_log
    assert "`GET /admin/operations`" in change_log
    assert "existing admin bearer token and rate limiter" in change_log
    assert "`stale_running`" in change_log
    assert "does not infer state from `/admin/jobs`" in change_log
    assert "GET /admin/operations" in operator_guide
    assert "Authorization: Bearer <JEDI_ADMIN_API_TOKEN>" in operator_guide
    assert "DB-backed" in operator_guide
    assert "aggregate SQL against" in operator_guide
    assert "`fulfillment_jobs`" in operator_guide
    assert "does not infer backlog or stale-running status from the paginated" in (
        operator_guide
    )
    assert (
        "`test_fulfillment_job_status_summary_uses_postgres_aggregate_counts`"
        in change_log
    )
    assert (
        "`test_admin_operations_returns_db_backed_fulfillment_summary`"
        in change_log
    )


def test_sprint_1055_documents_backup_restore_runbook() -> None:
    change_log = Path("docs/sprints/sprint-1055-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Backup and Restore Runbook" in change_log
    assert "PostgreSQL is the authoritative operational store" in change_log
    assert "retention pruning is not backup" in change_log
    assert "RPO" in change_log
    assert "RTO" in change_log
    assert "restore drill" in change_log
    assert "Backup and Restore Runbook" in operator_guide
    assert "PostgreSQL is the authoritative operational store" in operator_guide
    assert "retention pruning is not a backup control" in operator_guide
    assert "point-in-time recovery" in operator_guide
    assert "restore drill" in operator_guide
    assert "Do not delete `artifact_refs`" in operator_guide
    assert "No production deployment is ready until" in operator_guide
    assert "`test_sprint_1055_documents_backup_restore_runbook`" in change_log


def test_sprint_1056_documents_lifecycle_webhook_secret_rotation() -> None:
    change_log = Path("docs/sprints/sprint-1056-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")
    env_example = Path(".env.example").read_text(encoding="utf-8")

    assert "Lifecycle Webhook Secret Rotation" in change_log
    assert "`JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET`" in change_log
    assert "overlap window" in change_log
    assert "constant-time comparison" in change_log
    assert "API-only" in change_log
    assert "lifecycle webhook secret rotation runbook" in operator_guide
    assert "`JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET`" in operator_guide
    assert "must differ from the active secret" in operator_guide
    assert "old-secret retirement time" in operator_guide
    assert "Other runtime secrets still require a coordinated" in operator_guide
    assert "JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET=" in env_example
    assert (
        "`test_lifecycle_webhook_hmac_auth_accepts_previous_secret_during_rotation`"
        in change_log
    )


def test_sprint_1057_documents_runtime_trusted_host_enforcement() -> None:
    change_log = Path("docs/sprints/sprint-1057-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")
    env_example = Path(".env.example").read_text(encoding="utf-8")

    assert "Runtime Trusted Host Enforcement" in change_log
    assert "`JEDI_TRUSTED_HOSTS`" in change_log
    assert "TrustedHostMiddleware" in change_log
    assert "public `api` and `combined`" in change_log
    assert "Host header" in change_log
    assert "JEDI_TRUSTED_HOSTS=" in env_example
    assert "`JEDI_TRUSTED_HOSTS`" in operator_guide
    assert "unexpected Host headers" in operator_guide
    assert "wildcard-all entries" in operator_guide
    assert "`test_runtime_api_trusted_hosts_rejects_unlisted_host`" in change_log
    assert "`test_load_runtime_settings_reads_trusted_hosts`" in change_log


def test_sprint_1058_documents_trusted_host_worker_boundary() -> None:
    change_log = Path("docs/sprints/sprint-1058-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Trusted Host Worker Role Boundary" in change_log
    assert "`JEDI_TRUSTED_HOSTS`" in change_log
    assert "public API Host header control" in change_log
    assert "worker-only services" in change_log
    assert "JEDI_TRUSTED_HOSTS` is also API-only" in operator_guide
    assert "workers do not serve public HTTP requests" in operator_guide
    assert "`test_validate_runtime_settings_rejects_api_secrets_on_worker_role`" in (
        change_log
    )


def test_sprint_1059_documents_security_verification_gate() -> None:
    change_log = Path("docs/sprints/sprint-1059-change-log.md").read_text(
        encoding="utf-8"
    )
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")
    development_guide = Path("docs/development.md").read_text(encoding="utf-8")
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "Security Verification Gate" in change_log
    assert "`defusedxml`" in change_log
    assert "runtime dependency" in change_log
    assert "python3 -m bandit -q -r src" in change_log
    assert "python3 -m pip_audit . --progress-spinner off" in change_log
    assert "python3 -m bandit -q -r src" in operator_guide
    assert "python3 -m pip_audit . --progress-spinner off" in operator_guide
    assert "python3 -m bandit -q -r src" in development_guide
    assert "python3 -m pip_audit . --progress-spinner off" in development_guide
    assert "python3 -m bandit -q -r src" in workflow
    assert "python3 -m pip_audit . --progress-spinner off" in workflow
    assert '"bandit[toml]"' in pyproject
    assert '"pip-audit"' in pyproject
    assert '"defusedxml>=0.7.1"' in pyproject
    assert '"types-defusedxml"' in pyproject
    assert "`test_ci_workflow_runs_security_gates_before_typecheck_and_tests`" in (
        change_log
    )


def test_production_hardening_completion_audit_documents_current_evidence() -> None:
    audit = Path("docs/production-hardening-completion-audit.md").read_text(
        encoding="utf-8"
    )

    assert "Production Hardening Completion Audit" in audit
    assert "security, reliability, operational readiness, auditability" in audit
    assert "Evidence Matrix" in audit
    assert "Lifecycle webhook authentication" in audit
    assert "`JEDI_TRUSTED_HOSTS`" in audit
    assert "Worker/API responsibility split" in audit
    assert "`defusedxml`" in audit
    assert "Ruff, Bandit, project-scoped `pip-audit`, strict mypy" in audit
    assert "PostgreSQL operational store" in audit
    assert "Write-once local artifacts" in audit
    assert "3,946 tests and 93.32% coverage" in audit
    assert "Required External Controls" in audit
    assert "Customer ATO/control inheritance mapping" in audit
