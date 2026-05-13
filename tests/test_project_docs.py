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


def test_sprint_twenty_nine_change_log_documents_packet_cli() -> None:
    change_log = Path("docs/sprints/sprint-29-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "build-implementation-packet" in change_log
    assert "reviewable implementation packet artifact" in change_log
    assert "read-only PDI story fetch" in change_log
    assert "no_stories_found" in change_log
    assert "Now Assist" in change_log
    assert "no model call" in change_log


def test_sprint_thirty_change_log_documents_model_contract_hardening() -> None:
    change_log = Path("docs/sprints/sprint-30-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "implementation output contract" in change_log
    assert "test_plan" in change_log
    assert "rollback_notes" in change_log
    assert "ModelResponseError" in change_log


def test_sprint_thirty_one_change_log_documents_candidate_handoff() -> None:
    change_log = Path("docs/sprints/sprint-31-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "UpdateSetCandidate" in change_log
    assert "generate_implementation_update_set_candidate" in change_log
    assert "artifact_hash" in change_log
    assert "reviewable handoff" in change_log
    assert "manual-review" in change_log


def test_sprint_thirty_two_change_log_documents_candidate_cli() -> None:
    change_log = Path("docs/sprints/sprint-32-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "build-implementation-candidate" in change_log
    assert "provider response file" in change_log
    assert "PDI story source" in change_log
    assert "write-once candidate artifact" in change_log
    assert "unsafe provider response" in change_log


def test_sprint_thirty_three_change_log_documents_candidate_batch_runner() -> None:
    change_log = Path("docs/sprints/sprint-33-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "run-implementation-candidates" in change_log
    assert "implementation candidate jobs file" in change_log
    assert "no_jobs" in change_log
    assert "safe summary" in change_log


def test_sprint_thirty_four_change_log_documents_candidate_batch_reports() -> None:
    change_log = Path("docs/sprints/sprint-34-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "candidate batch report" in change_log
    assert "--batch-report-root" in change_log
    assert "per-story outcome" in change_log
    assert "ServiceNow sys_id" in change_log


def test_sprint_thirty_five_change_log_documents_failure_isolation() -> None:
    change_log = Path("docs/sprints/sprint-35-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "failure isolation" in change_log
    assert "blocked outcome" in change_log
    assert "continues processing" in change_log
    assert "nonzero" in change_log


def test_sprint_thirty_six_change_log_documents_lifecycle_smoke_runner() -> None:
    change_log = Path("docs/sprints/sprint-36-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "run-lifecycle-smoke" in change_log
    assert "dry-run lifecycle" in change_log
    assert "writeback plan" in change_log
    assert "does not mutate ServiceNow" in change_log


def test_sprint_thirty_seven_change_log_documents_bootstrap_planning() -> None:
    change_log = Path("docs/sprints/sprint-37-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "plan-bootstrap-fields" in change_log
    assert "u_ai_status" in change_log
    assert "does not create state" in change_log
    assert "no form layout" in change_log


def test_sprint_thirty_eight_change_log_documents_bootstrap_apply() -> None:
    change_log = Path("docs/sprints/sprint-38-change-log.md").read_text(
        encoding="utf-8"
    )

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
    change_log = Path("docs/sprints/sprint-14-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "SPM/PPM workflow research" in change_log
    assert "ServiceNow work surface" in change_log
    assert "structured writeback" in change_log
    assert "Ready for Testing" in change_log


def test_sprint_fifteen_change_log_documents_writeback_boundary() -> None:
    change_log = Path("docs/sprints/sprint-15-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "writeback planner" in change_log
    assert "external build result" in change_log
    assert "Ready for Testing" in change_log
    assert "PATCH primitive" in change_log
    assert "policy-gated" in change_log


def test_sprint_sixteen_change_log_documents_state_discovery() -> None:
    change_log = Path("docs/sprints/sprint-16-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "sys_choice" in change_log
    assert "Ready for Testing" in change_log
    assert "instance state mapping" in change_log
    assert "fails closed" in change_log


def test_sprint_seventeen_change_log_documents_dry_run_writeback_cli() -> None:
    change_log = Path("docs/sprints/sprint-17-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "plan-writeback" in change_log
    assert "dry-run" in change_log
    assert "no ServiceNow mutation" in change_log
    assert "Ready for Testing" in change_log


def test_sprint_eighteen_change_log_documents_writeback_field_discovery() -> None:
    change_log = Path("docs/sprints/sprint-18-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "sys_dictionary" in change_log
    assert "structured writeback fields" in change_log
    assert "fails closed" in change_log
    assert "plan-writeback" in change_log


def test_sprint_nineteen_change_log_documents_confirmed_apply_gate() -> None:
    change_log = Path("docs/sprints/sprint-19-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "confirmed apply" in change_log
    assert "--apply" in change_log
    assert "--confirm-story-number" in change_log
    assert "dry-run default" in change_log


def test_sprint_twenty_change_log_documents_writeback_audit_artifact() -> None:
    change_log = Path("docs/sprints/sprint-20-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "writeback audit artifact" in change_log
    assert "--actor-id" in change_log
    assert "service principal" in change_log
    assert "--audit-root" in change_log
    assert "write-once" in change_log


def test_sprint_twenty_one_change_log_documents_writeback_orchestration_boundary() -> None:
    change_log = Path("docs/sprints/sprint-21-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "execute_writeback" in change_log
    assert "service actor" in change_log
    assert "CLI adapter" in change_log
    assert "orchestration boundary" in change_log


def test_sprint_twenty_two_change_log_documents_writeback_idempotency() -> None:
    change_log = Path("docs/sprints/sprint-22-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "idempotency" in change_log
    assert "writeback audit artifact" in change_log
    assert "retry" in change_log
    assert "no-op" in change_log
    assert "remote writeback" in change_log


def test_sprint_twenty_three_change_log_documents_writeback_capability_preflight() -> None:
    change_log = Path("docs/sprints/sprint-23-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "writeback capability preflight" in change_log
    assert "check-writeback-capability" in change_log
    assert "Ready for Testing" in change_log
    assert "required structured fields" in change_log


def test_sprint_twenty_four_change_log_documents_batch_writeback_orchestration() -> None:
    change_log = Path("docs/sprints/sprint-24-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "batch writeback orchestration" in change_log
    assert "capability preflight once" in change_log
    assert "fail closed" in change_log
    assert "summary" in change_log


def test_sprint_twenty_five_change_log_documents_writeback_job_file_ingestion() -> None:
    change_log = Path("docs/sprints/sprint-25-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "writeback job file" in change_log
    assert "run-writeback-batch" in change_log
    assert "typed job records" in change_log
    assert "empty job file" in change_log


def test_sprint_twenty_six_change_log_documents_batch_report_artifact() -> None:
    change_log = Path("docs/sprints/sprint-26-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "batch report artifact" in change_log
    assert "no ServiceNow sys_ids" in change_log
    assert "write-once" in change_log
    assert "run-writeback-batch" in change_log


def test_sprint_twenty_seven_change_log_documents_manifest_alignment() -> None:
    change_log = Path("docs/sprints/sprint-27-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "manifest alignment" in change_log
    assert "Controlled ServiceNow story writeback" in change_log
    assert "Direct Update Set imports" in change_log
    assert "execute_writeback" in change_log


def test_sprint_twenty_eight_change_log_documents_implementation_packet() -> None:
    change_log = Path("docs/sprints/sprint-28-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "LLM implementation packet" in change_log
    assert "Now Assist" in change_log
    assert "deterministic gates" in change_log
    assert "generate_implementation_candidate" in change_log


def test_sprint_thirty_nine_change_log_documents_live_writeback_verification() -> None:
    change_log = Path("docs/sprints/sprint-39-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "verify-writeback" in change_log
    assert "STRY0010013" in change_log
    assert "remote_writeback_already_applied" in change_log
    assert "build-writeback-apply-20260513-001" in change_log


def test_sprint_forty_change_log_documents_lifecycle_manifest() -> None:
    change_log = Path("docs/sprints/sprint-40-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "lifecycle manifest" in change_log
    assert "record-lifecycle-manifest" in change_log
    assert "implementation_packet" in change_log
    assert "implementation_candidate" in change_log
    assert "writeback" in change_log


def test_sprint_forty_one_change_log_documents_apply_manifest() -> None:
    change_log = Path("docs/sprints/sprint-41-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "plan-writeback --apply" in change_log
    assert "--manifest-root" in change_log
    assert "verify_writeback" in change_log
    assert "writeback_audit" in change_log


def test_sprint_forty_two_change_log_documents_artifact_handoff_contract() -> None:
    change_log = Path("docs/sprints/sprint-42-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "artifact handoff" in change_log
    assert "Approved Update Set XML" in change_log
    assert "Test Evidence Bundle" in change_log
    assert "internal audit evidence" in change_log


def test_sprint_forty_three_change_log_documents_handoff_report() -> None:
    change_log = Path("docs/sprints/sprint-43-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "plan-artifact-handoff" in change_log
    assert "handoff report" in change_log
    assert "attach_to_servicenow" in change_log
    assert "delivery_evidence" in change_log


def test_sprint_forty_four_change_log_documents_handoff_hashing() -> None:
    change_log = Path("docs/sprints/sprint-44-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "SHA-256" in change_log
    assert "missing" in change_log
    assert "fail closed" in change_log
    assert "handoff report" in change_log


def test_sprint_forty_five_change_log_documents_handoff_summary_writeback() -> None:
    change_log = Path("docs/sprints/sprint-45-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "write-artifact-handoff-summary" in change_log
    assert "work_notes" in change_log
    assert "dry-run" in change_log
    assert "does not attach" in change_log
