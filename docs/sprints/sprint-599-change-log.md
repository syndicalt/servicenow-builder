# Sprint 599 Change Log

## ServiceNow secret redaction text value cap

Sprint 599 continued production hardening by bounding exact string values returned from shared ServiceNow diagnostic secret redaction. `redact_secrets()` already redacted credential-like text, rejected string subclasses, projected unsafe keys, normalized unsupported scalar values, bounded collection traversal, and handled cycles, but exact string values could still remain oversized in the sanitized diagnostic copy.

Secret redaction now applies the shared exact-length truncation helper after `_redact_diagnostic_text()` returns the sanitized text. This preserves existing secret masking semantics while ensuring exact string diagnostic values fit within `MAX_HTTP_ERROR_DIAGNOSTIC_CHARS`, including the `...[truncated]` marker.

This prevents large upstream request or response diagnostic strings from surviving inside sanitized copies before logs, tests, artifacts, work notes, or downstream exception formatting render them.

Verification:

- Added 1 failing-first ServiceNow secret redaction text-value cap test proving `redact_secrets()` preserved an oversized string without `...[truncated]` before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_redact_secrets_caps_exact_string_values_after_redaction -q`: failed before implementation because the sanitized diagnostic string was oversized and did not end with `...[truncated]`.
- `python3 -m pytest tests/test_servicenow.py::test_redact_secrets_caps_exact_string_values_after_redaction tests/test_servicenow.py::test_redact_secrets_masks_sensitive_strings_under_non_sensitive_keys tests/test_servicenow.py::test_redact_secrets_handles_circular_diagnostic_payload tests/test_servicenow.py::test_redact_secrets_rejects_non_json_diagnostic_keys tests/test_servicenow.py::test_redact_secrets_normalizes_non_json_scalar_values -q`: 5 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_599_documents_servicenow_secret_redaction_text_value_cap -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 203 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 673 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2671 passed, 93.15% coverage.
