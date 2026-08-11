# Sprint 598 Change Log

## ServiceNow secret redaction cycle safety

Sprint 598 continued production hardening by making shared ServiceNow diagnostic secret redaction cycle-safe. `redact_secrets()` already bounded wide dictionaries, lists, and tuples, projected unsafe keys, normalized unsafe scalar values, guarded string subclasses, and redacted credential-like fragments inside exact strings, but a cyclic diagnostic payload could still raise `RecursionError` before returning a sanitized request or response copy.

Secret redaction now keeps the public `redact_secrets()` signature and delegates to an internal traversal helper that tracks active container ids. Repeated active dictionaries, lists, or tuples render as `[circular reference]` and traversal continues instead of recursing indefinitely.

This prevents malformed in-process diagnostic payloads from creating secondary sanitizer failures before request/response diagnostics, operator logs, worker failures, or test assertions can receive a safe redacted view.

Verification:

- Added 1 failing-first ServiceNow secret redaction cycle-safety test proving a self-referential diagnostic payload raised `RecursionError` before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_redact_secrets_handles_circular_diagnostic_payload -q`: failed before implementation with `RecursionError`.
- `python3 -m pytest tests/test_servicenow.py::test_redact_secrets_handles_circular_diagnostic_payload tests/test_servicenow.py::test_redact_secrets_does_not_consume_all_fields_for_wide_diagnostic tests/test_servicenow.py::test_redact_secrets_rejects_non_json_diagnostic_keys tests/test_servicenow.py::test_redact_secrets_normalizes_non_json_scalar_values tests/test_servicenow.py::test_redact_secrets_masks_sensitive_strings_under_non_sensitive_keys -q`: 5 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_598_documents_servicenow_secret_redaction_cycle_safety -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 202 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 672 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2669 passed, 93.16% coverage.
