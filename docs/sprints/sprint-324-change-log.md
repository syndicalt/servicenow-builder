# Sprint 324 Change Log - Operational Record Validation Input Redaction

## Summary

- Lifecycle ingress and operational-store record validation now suppress rejected input values in Pydantic validation errors.
- `LifecycleStateChangeEvent`, lifecycle event records, fulfillment job records, job event records, artifact refs, artifact blobs, retention records, and surface maturity records still name invalid fields without echoing raw rejected values.
- The redaction boundary covers lifecycle payload fragments, ServiceNow sys_ids, job error text, artifact paths, artifact payload snippets, and retention setting fragments before diagnostics can reach logs, artifacts, or ServiceNow work notes.
- Existing lifecycle planning, operational persistence, retention, and store projection behavior remains intact.
- Documented the operational record diagnostic boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_lifecycle_events.py::test_lifecycle_event_validation_errors_do_not_echo_rejected_inputs tests/test_operational_store.py::test_operational_record_validation_errors_do_not_echo_rejected_inputs -q` - 6 tests failed before implementation because lifecycle and operational record validation errors included `input_value`.
- `python3 -m pytest tests/test_lifecycle_events.py::test_lifecycle_event_validation_errors_do_not_echo_rejected_inputs tests/test_operational_store.py::test_operational_record_validation_errors_do_not_echo_rejected_inputs tests/test_lifecycle_events.py tests/test_operational_store.py -q` - 53 passed after implementation.
- `python3 -m pytest tests/test_lifecycle_events.py::test_lifecycle_event_validation_errors_do_not_echo_rejected_inputs tests/test_operational_store.py::test_operational_record_validation_errors_do_not_echo_rejected_inputs tests/test_project_docs.py::test_sprint_three_hundred_twenty_four_documents_operational_record_error_redaction -q` - 7 passed.
- `python3 -m ruff check src/jedi_devproject/lifecycle_events.py src/jedi_devproject/operational_store.py tests/test_lifecycle_events.py tests/test_operational_store.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/lifecycle_events.py src/jedi_devproject/operational_store.py tests/test_lifecycle_events.py tests/test_operational_store.py tests/test_project_docs.py` - no issues found in 5 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 181 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 398 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1945 passed, total coverage 93.87%.
