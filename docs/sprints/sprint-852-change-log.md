# Sprint 852 Change Log - ServiceNow failure notifier secret-values guard

## Intent

Harden ServiceNow failure work-note notification so malformed literal
`secret_values` cannot crash notifier construction or replace failed-job
writeback with a hostile iterator diagnostic.

## Changes

- Added 1 failing-first ServiceNow failure notifier secret-values assertion: `tests/test_runtime.py::test_servicenow_failure_notifier_ignores_hostile_secret_iterator`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_852_documents_servicenow_failure_notifier_secret_values_guard`.
- Added shared `safe_literal_secret_values()` projection for runtime diagnostics and work-note literal secret redaction.
- Added direct `safe_literal_secret_values()` coverage for partially hostile iterators that yield safe values before failing.
- `HostileFailureNotifierSecretValues` verifies notifier construction and failure writeback do not surface iterator exception text.
- `_servicenow_failure_notifier()` projects literal secret values once through the hardened bounded exact-string policy before failed-job work-note construction.

## Verification

- `pytest tests/test_runtime.py::test_servicenow_failure_notifier_ignores_hostile_secret_iterator tests/test_project_docs.py::test_sprint_852_documents_servicenow_failure_notifier_secret_values_guard -q` - 2 passed.
- `pytest tests/test_runtime.py::test_servicenow_failure_notifier_sanitizes_work_note_values tests/test_runtime.py::test_servicenow_failure_notifier_ignores_hostile_secret_iterator tests/test_runtime.py::test_servicenow_failure_notifier_bounds_work_note_values tests/test_runtime_redaction.py tests/test_work_note_safety.py tests/test_project_docs.py -q` - 961 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3401 passed, 93.46% coverage.
