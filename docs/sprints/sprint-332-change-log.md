# Sprint 332 Change Log

Scope: Production hardening - runtime and control-plane DTO validation input redaction.

## Summary

- Runtime and control-plane DTO validation now suppresses rejected input values in Pydantic validation errors.
- The covered boundary includes container smoke plans, external build pipeline results, rate-limit decisions, lifecycle webhook responses, runtime worker summaries, runtime worker settings, build-claim fulfillment config, model fulfillment config, resolved fulfillment flows, dictionary/form intents, Anthropic HTTP responses, CI/CD Update Set probes, pipeline inputs, pipeline results, and artifact handoff plans.
- Existing validation remains in place. Diagnostics still name invalid fields and stable reasons, but type, enum, parser, extra-field, and nested-model failures do not echo rejected event payloads, build references, retry decisions, webhook actions, runtime settings, provider policies, flow identifiers, dictionary placement values, provider response details, CI/CD probe output, pipeline artifacts, or delivery handoff evidence into logs, artifacts, or ServiceNow work notes.

## Verification

- `python3 -m pytest tests/test_runtime_control_dto_redaction.py::test_runtime_control_dto_validation_errors_do_not_echo_rejected_inputs -q` - 1 test failed before implementation because direct container smoke plan validation echoed `input_value='sprint-332-secret-ContainerLifecycleSmokePlan'`.
- `python3 -m pytest tests/test_runtime_control_dto_redaction.py tests/test_container_runtime.py tests/test_external_build_contract.py tests/test_lifecycle_api.py tests/test_runtime_entrypoints.py tests/test_runtime_worker_retention.py tests/test_fulfillment_handler.py tests/test_model_fulfillment.py tests/test_cicd_update_sets.py tests/test_pipeline.py tests/test_artifact_handoff.py -q` - 132 passed after implementation.
- `python3 -m pytest tests/test_runtime_control_dto_redaction.py::test_runtime_control_dto_validation_errors_do_not_echo_rejected_inputs tests/test_project_docs.py::test_sprint_three_hundred_thirty_two_documents_runtime_control_error_redaction -q` - 2 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 186 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 406 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1966 passed, total coverage 93.94%.
