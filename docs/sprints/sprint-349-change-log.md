# Sprint 349 Change Log

Scope: Production hardening - direct runtime environment normalization at auth decisions.

## Summary

- Lifecycle webhook disabled-auth handling no longer strips or lowercases direct runtime environment values before deciding whether the development-only exception applies.
- Development Basic-auth admin console handling no longer strips or lowercases direct runtime environment values before enforcing the development-only boundary.
- Padded direct runtime environment values now fail closed at both auth decision points instead of being treated as development.
- Runtime settings validation remains the primary startup boundary, and these lower-level checks now provide a stricter second line of defense.

## Verification

- `python3 -m pytest tests/test_lifecycle_api.py::test_lifecycle_webhook_disabled_auth_rejects_padded_development_environment tests/test_runtime.py::test_admin_console_rejects_padded_development_environment_before_auth -q` - 2 tests failed before implementation because padded direct runtime environment values were normalized into development.
- `python3 -m pytest tests/test_lifecycle_api.py::test_lifecycle_webhook_disabled_auth_rejects_padded_development_environment tests/test_lifecycle_api.py::test_lifecycle_webhook_records_ready_event_and_enqueues_fulfillment tests/test_runtime.py::test_admin_console_rejects_padded_development_environment_before_auth tests/test_runtime.py::test_admin_console_requires_basic_auth tests/test_runtime.py::test_admin_console_renders_jobs_events_and_artifact_links -q` - 5 passed after implementation.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_forty_nine_documents_runtime_mode_auth_no_trim -q` - 1 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 187 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 423 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 2017 passed, total coverage 94.07%.
