# Sprint 603 Change Log

## Admin diagnostic text normalization

Sprint 603 continued production hardening by normalizing persisted admin diagnostic strings after redaction and before the shared admin diagnostic cap. Admin JSON endpoints and the HTML console already redacted credential-bearing diagnostics and capped long values, but short persisted `last_error` text could still retain raw newline or tab characters after redaction.

`_admin_diagnostic_text()` now collapses whitespace/control-character runs after `_redact_diagnostic_text()` returns sanitized text and before applying `MAX_ADMIN_DIAGNOSTIC_CHARS`. This centralizes the behavior for fulfillment job `last_error` values, job event messages, artifact reference paths, operational alert details, and artifact payload diagnostic strings without changing provenance for the stored original artifacts.

Verification:

- Added 2 failing-first admin diagnostic tests proving `/admin/jobs` JSON responses and the HTML admin console preserved newline and tab characters in persisted `last_error` diagnostics before implementation.
- `python3 -m pytest tests/test_runtime.py::test_admin_jobs_normalizes_persisted_last_error_diagnostics tests/test_runtime.py::test_admin_console_normalizes_persisted_last_error_diagnostics -q`: failed before implementation because admin diagnostics retained raw newline and tab characters.
- `python3 -m pytest tests/test_runtime.py::test_admin_jobs_normalizes_persisted_last_error_diagnostics tests/test_runtime.py::test_admin_console_normalizes_persisted_last_error_diagnostics tests/test_runtime.py::test_admin_jobs_redacts_sensitive_diagnostics tests/test_runtime.py::test_admin_jobs_bounds_persisted_last_error_diagnostics tests/test_runtime.py::test_admin_console_redacts_sensitive_diagnostics -q`: 5 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_603_documents_admin_diagnostic_text_normalization tests/test_project_docs.py::test_sprint_three_hundred_fifty_eight_documents_admin_diagnostic_bounds -q`: 2 passed.
- `python3 -m pytest tests/test_runtime.py -q`: 335 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 677 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2683 passed, total coverage 93.16%, required 90% coverage reached.
