# Sprint 855 Change Log - Failure notifier story lookup query guard

## Intent

Harden ServiceNow failure notifier lookup construction so malformed fulfillment
job story identifiers cannot inject ServiceNow encoded-query delimiters before
failed-job work-note writeback.

## Changes

- Added 1 failing-first failure notifier lookup query assertion: `tests/test_runtime.py::test_servicenow_failure_notifier_rejects_unsafe_story_number_lookup`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_855_documents_failure_notifier_lookup_query_guard`.
- `test_servicenow_failure_notifier_rejects_unsafe_story_number_lookup` verifies unsafe story-number lookup parts fail before `fetch_stories()`.
- `_servicenow_failure_notifier()` now validates story lookup parts before explicit encoded-query construction.
- The lookup-miss diagnostic test now covers safe query values with configured literal-secret redaction; delimiter-bearing values fail earlier at the query guard.

## Verification

- `pytest tests/test_runtime.py::test_servicenow_failure_notifier_rejects_unsafe_story_number_lookup tests/test_runtime.py::test_servicenow_failure_notifier_sanitizes_story_not_found_diagnostic tests/test_project_docs.py::test_sprint_855_documents_failure_notifier_lookup_query_guard -q` - 3 passed.
- `pytest tests/test_runtime.py -q -k "servicenow_failure_notifier"` - 5 passed, 410 deselected.
- `pytest tests/test_project_docs.py -q` - 928 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3407 passed, 93.49% coverage.
