# Sprint 854 Change Log - Failure notifier story-not-found diagnostic redaction

## Intent

Harden the ServiceNow failure notifier lookup-miss error path so a malformed
fulfillment job cannot leak secret-like fragments, control characters, or
oversized text through the `story not found` diagnostic.

## Changes

- Added 1 failing-first failure notifier story-not-found diagnostic assertion: `tests/test_runtime.py::test_servicenow_failure_notifier_sanitizes_story_not_found_diagnostic`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_854_documents_failure_notifier_story_not_found_redaction`.
- `_servicenow_failure_notifier()` now sanitizes story numbers before raising `story not found` diagnostics.
- `test_servicenow_failure_notifier_sanitizes_story_not_found_diagnostic` verifies story-number fragments and control characters are not exposed on lookup misses.

## Verification

- `pytest tests/test_runtime.py::test_servicenow_failure_notifier_sanitizes_story_not_found_diagnostic tests/test_project_docs.py::test_sprint_854_documents_failure_notifier_story_not_found_redaction -q` - 2 passed.
- `pytest tests/test_runtime.py -q -k "servicenow_failure_notifier"` - 4 passed, 410 deselected.
- `pytest tests/test_project_docs.py -q` - 927 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3405 passed, 93.48% coverage.
