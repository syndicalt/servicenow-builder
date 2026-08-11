# Sprint 601 Change Log

## ServiceNow secret redaction text normalization

Sprint 601 continued production hardening by normalizing exact string values returned from shared ServiceNow diagnostic secret redaction. `redact_secrets()` already redacted credential-like text, rejected string subclasses, bounded exact string values, projected unsafe keys, normalized unsupported scalar values, bounded collection traversal, and handled cycles, but exact string values could still retain raw newline or tab characters in the sanitized diagnostic copy.

Secret redaction now collapses whitespace/control-character runs after `_redact_diagnostic_text()` returns sanitized text and before the shared exact-length truncation helper applies the cap. This preserves existing secret masking while preventing line-breaking diagnostic text from surviving in sanitized request or response copies.

This reduces log, work-note, artifact, and test-output injection risk for malformed upstream diagnostics while keeping the redacted content useful to operators.

Verification:

- Added 1 failing-first ServiceNow secret redaction text-normalization test proving `redact_secrets()` preserved newline and tab characters after masking a sensitive assignment before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_redact_secrets_normalizes_exact_string_values_after_redaction -q`: failed before implementation because the sanitized diagnostic string still contained raw newline and tab characters.
- `python3 -m pytest tests/test_servicenow.py::test_redact_secrets_normalizes_exact_string_values_after_redaction tests/test_servicenow.py::test_redact_secrets_caps_exact_string_values_after_redaction tests/test_servicenow.py::test_redact_secrets_masks_sensitive_strings_under_non_sensitive_keys tests/test_servicenow.py::test_redact_secrets_rejects_string_subclass_diagnostic_text tests/test_servicenow.py::test_redact_secrets_normalizes_non_json_scalar_values -q`: 5 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_601_documents_servicenow_secret_redaction_text_normalization -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 207 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 675 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2677 passed, total coverage 93.16%, required 90% coverage reached.
