# Sprint 853 Change Log - Completion missing-sys-id diagnostic redaction

## Intent

Harden the runtime completion closeout error path so a malformed completed-story
payload cannot leak secret-like fragments, control characters, or oversized text
through the missing `story_sys_id` diagnostic.

## Changes

- Added 1 failing-first completion missing-sys-id diagnostic assertion: `tests/test_runtime.py::test_servicenow_complete_notifier_sanitizes_missing_sys_id_story_number`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_853_documents_completion_missing_sys_id_diagnostic_redaction`.
- `_servicenow_complete_notifier()` now sanitizes story numbers before raising missing `story_sys_id` diagnostics.
- `test_servicenow_complete_notifier_sanitizes_missing_sys_id_story_number` verifies secret-like story-number fragments and control characters are not exposed.

## Verification

- `pytest tests/test_runtime.py::test_servicenow_complete_notifier_sanitizes_missing_sys_id_story_number tests/test_project_docs.py::test_sprint_853_documents_completion_missing_sys_id_diagnostic_redaction -q` - 2 passed.
- `pytest tests/test_runtime.py -q -k "servicenow_complete_notifier or runtime_complete_event_updates_ai_status"` - 4 passed, 409 deselected.
- `pytest tests/test_project_docs.py -q` - 926 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3403 passed, 93.47% coverage.
