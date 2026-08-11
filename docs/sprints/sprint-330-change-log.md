# Sprint 330 Change Log

Scope: Production hardening - Update Set and writeback DTO validation input redaction.

## Summary

- Update Set apply, retrieved Update Set handoff, and writeback DTO validation now suppresses rejected input values in Pydantic validation errors.
- The covered boundary includes Update Set apply requests, apply results, planned form layout changes, retrieved Update Set handoff requests and results, external build results, story state mappings, writeback policies, writeback plans, writeback audit events, build-claim audit events, writeback execution requests and results, writeback job records, batch results, capability results, and verification results.
- Existing validation remains in place. Diagnostics still name invalid fields and stable reasons, but type, enum, parser, extra-field, and bounds failures do not echo rejected story sys_ids, build references, candidate artifacts, retrieved Update Set ids, instance URLs, audit paths, work notes, actor ids, state values, or verification field values into logs, artifacts, or ServiceNow work notes.

## Verification

- `python3 -m pytest tests/test_update_writeback_dto_redaction.py::test_update_set_and_writeback_dto_validation_errors_do_not_echo_rejected_inputs -q` - 1 test failed before implementation because direct Update Set apply validation echoed `input_value='secret-candidate'`.
- `python3 -m pytest tests/test_update_writeback_dto_redaction.py::test_update_set_and_writeback_dto_validation_errors_do_not_echo_rejected_inputs tests/test_update_set_apply.py tests/test_update_set_handoff.py tests/test_writeback.py tests/test_writeback_audit.py tests/test_writeback_orchestration.py -q` - 63 passed after implementation.
- `python3 -m pytest tests/test_update_writeback_dto_redaction.py::test_update_set_and_writeback_dto_validation_errors_do_not_echo_rejected_inputs tests/test_project_docs.py::test_sprint_three_hundred_thirty_documents_update_writeback_error_redaction -q` - 2 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 184 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 404 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1962 passed, total coverage 93.92%.
