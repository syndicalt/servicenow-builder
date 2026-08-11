# Sprint 856 Change Log - Failure notifier story sys-id record guard

## Intent

Harden the authoritative ServiceNow failure notifier lookup path so malformed
`story_sys_id` values cannot reach encoded-query construction with characters
outside the ServiceNow record-id policy.

## Changes

- Added 1 failing-first failure notifier story sys-id assertion: `tests/test_runtime.py::test_servicenow_failure_notifier_rejects_unsafe_story_sys_id_lookup`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_856_documents_failure_notifier_story_sys_id_record_guard`.
- `test_servicenow_failure_notifier_rejects_unsafe_story_sys_id_lookup` verifies unsafe `story_sys_id` values fail before `fetch_stories()`.
- `_servicenow_failure_notifier()` now applies record-id syntax validation to authoritative `story_sys_id` lookup values.

## Verification

- `pytest tests/test_runtime.py::test_servicenow_failure_notifier_rejects_unsafe_story_sys_id_lookup tests/test_project_docs.py::test_sprint_856_documents_failure_notifier_story_sys_id_record_guard -q` - 2 passed.
- `pytest tests/test_runtime.py -q -k "servicenow_failure_notifier"` - 6 passed, 410 deselected.
- `pytest tests/test_project_docs.py -q` - 929 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3409 passed, 93.49% coverage.
