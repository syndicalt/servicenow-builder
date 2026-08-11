# Sprint 328 Change Log

Scope: Production hardening - operational DTO validation input redaction.

## Summary

- Operational DTO validation now suppresses rejected input values in Pydantic validation errors.
- The covered boundary includes alert payloads, builder maturity evidence, context escalation plans, fulfillment artifact references, persisted artifact references, fulfillment execution results, fulfillment worker results, and stale-job requeue reports.
- Existing fail-closed validation remains in place. Diagnostics still name invalid fields and stable reasons, but type, enum, parser, extra-field, and bounds failures do not echo rejected alert details, job ids, artifact refs, artifact payload snippets, worker error fragments, routing reasons, or stale requeue timestamps into logs, artifacts, or ServiceNow work notes.

## Verification

- `python3 -m pytest tests/test_operational_dto_redaction.py::test_operational_dto_validation_errors_do_not_echo_rejected_inputs -q` - 1 test failed before implementation because direct operational DTO validation echoed `input_value='secret-created-at'`.
- `python3 -m pytest tests/test_operational_dto_redaction.py::test_operational_dto_validation_errors_do_not_echo_rejected_inputs tests/test_alert_delivery.py tests/test_builder_maturity.py tests/test_context_escalation.py tests/test_fulfillment_worker.py tests/test_runtime_worker_retention.py -q` - 80 passed after implementation.
- `python3 -m pytest tests/test_operational_dto_redaction.py::test_operational_dto_validation_errors_do_not_echo_rejected_inputs tests/test_project_docs.py::test_sprint_three_hundred_twenty_eight_documents_operational_dto_error_redaction -q` - 2 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 182 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 402 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1958 passed, total coverage 93.92%.
