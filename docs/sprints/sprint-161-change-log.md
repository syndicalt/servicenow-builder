# Sprint 161 Change Log

## Scope

Implemented the next production-hardening slice for roadmap items 4, 5, and 6.

## Changes

- Made capability status semantics stricter: `enabled` now means the deterministic builder can create retrieved Update Set handoff artifacts now.
- Moved lower maturity builders to `candidate_generation` while preserving their structured model-reasoning path.
- Enabled retrieved Update Set handoff for the narrow declarative `ui_policy_generate` subset using deterministic `sys_ui_policy` and `sys_ui_policy_action` customer update builders.
- Added `cmdb_ire_generate` for structured CMDB IRE candidate generation covering `cmdb_identifier`, `cmdb_identifier_entry`, and `cmdb_reconciliation_definition`, including reconciliation-rule intent.
- Kept CMDB IRE retrieved Update Set handoff disabled until real XML shape evidence and validators are captured.
- Added worker-only public web documentation retrieval with HTTPS allowlists, private-host blocking, redirect checks, bounded excerpts, script/style stripping, citation hashes, and fail-closed missing-context behavior.
- Added runtime settings for `JEDI_PUBLIC_WEB_ACCESS=worker`, `JEDI_PUBLIC_WEB_ALLOWED_DOMAINS`, `JEDI_PUBLIC_WEB_DOC_URLS`, and public web bounds.

## Verification

- Added targeted tests for UI Policy handoff, public web retrieval controls, public-doc context sufficiency, runtime settings, and CMDB IRE capability semantics.
- Targeted regression command passed:
  `python3 -m pytest tests/test_capabilities.py tests/test_update_set_handoff.py::test_create_update_set_handoff_blocks_non_dictionary_candidates_until_builder_matures tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_ui_policy_customer_updates tests/test_rag.py tests/test_instance_discovery.py::test_discover_servicenow_surface_context_collects_related_platform_surfaces tests/test_instance_discovery.py::test_required_public_docs_without_results_are_insufficient tests/test_model_fulfillment.py::test_model_candidate_handler_generates_ui_policy_update_set_handoff tests/test_model_fulfillment.py::test_model_candidate_handler_adds_live_public_docs_to_packet tests/test_model_fulfillment.py::test_model_candidate_handler_skips_provider_when_required_public_docs_missing tests/test_runtime.py::test_load_runtime_settings_reads_public_web_worker_controls tests/test_runtime.py::test_validate_runtime_settings_rejects_production_public_web_without_allowlist -q`
