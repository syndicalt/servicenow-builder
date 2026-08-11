# Sprint 592 Change Log

## ServiceNow secret redaction scalar normalization

Sprint 592 continued production hardening by preventing shared ServiceNow diagnostic secret redaction from reflecting unsupported scalar values in sanitized request or response copies. `redact_secrets()` already masked sensitive structured values, bounded traversal, projected unsafe keys, guarded string subclasses, and redacted credential-like fragments inside exact strings, but arbitrary non-string objects and non-finite floats were still returned directly.

ServiceNow diagnostic secret redaction now normalizes scalar values through a JSON-safe boundary. `None`, booleans, integers, finite floats, and exact strings remain available for diagnostics after redaction. Non-finite floats, arbitrary Python objects, bytes, and other unsupported scalar values render as `[non-json value]` without calling `str()` or `repr()` on the original value.

This keeps sanitized ServiceNow request and response diagnostics useful while ensuring alternate transports cannot inject object type names, object string output, non-finite numeric tokens, upstream value fragments, or credential-like payloads into redacted diagnostics.

Verification:

- Added 1 failing-first ServiceNow secret redaction scalar normalization test proving an unsupported object `repr()` and `nan` were reflected before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_redact_secrets_normalizes_non_json_scalar_values -q`: failed before implementation because the hostile object representation and `nan` value appeared in the sanitized diagnostic copy instead of `[non-json value]`.
- `python3 -m pytest tests/test_servicenow.py::test_redact_secrets_normalizes_non_json_scalar_values tests/test_servicenow.py::test_redact_secrets_rejects_non_json_diagnostic_keys tests/test_servicenow.py::test_redact_secrets_rejects_string_subclass_diagnostic_text tests/test_servicenow.py::test_redact_secrets_masks_sensitive_values tests/test_servicenow.py::test_redact_secrets_does_not_consume_all_fields_for_wide_diagnostic -q`: 13 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_592_documents_servicenow_secret_redaction_scalar_normalization -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 195 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 666 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2656 passed, 93.36% coverage.
