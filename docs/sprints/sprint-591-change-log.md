# Sprint 591 Change Log

## ServiceNow secret redaction key projection

Sprint 591 continued production hardening by preventing shared ServiceNow diagnostic secret redaction from reflecting Python-specific dictionary keys in sanitized request or response copies. `redact_secrets()` already masked sensitive structured values, bounded traversal, guarded string subclasses, and redacted credential-like fragments inside exact strings, but it still preserved raw dictionary keys.

ServiceNow diagnostic secret redaction now projects keys through the same safe diagnostic key path used by ServiceNow API exception diagnostics. Exact string keys are redacted and whitespace-normalized, duplicate rendered keys receive deterministic suffixes, and non-string keys render as `[non-json key]` without calling `str()` or `repr()` on the original key. Sensitive-key value masking still uses the original exact string key, so ordinary ServiceNow JSON diagnostics preserve structured secret redaction while Python-only keys fail closed.

This keeps sanitized ServiceNow request and response diagnostics useful while ensuring alternate transports cannot inject object type names, object string output, upstream key fragments, or credential-like payloads into redacted diagnostics.

Verification:

- Added 1 failing-first ServiceNow secret redaction key projection test proving a hostile dictionary key `repr()` was reflected before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_redact_secrets_rejects_non_json_diagnostic_keys -q`: failed before implementation because the hostile key representation appeared in the sanitized diagnostic copy instead of `[non-json key]`.
- `python3 -m pytest tests/test_servicenow.py::test_redact_secrets_rejects_non_json_diagnostic_keys tests/test_servicenow.py::test_redact_secrets_rejects_string_subclass_diagnostic_text tests/test_servicenow.py::test_redact_secrets_masks_sensitive_values tests/test_servicenow.py::test_redact_secrets_does_not_consume_all_fields_for_wide_diagnostic -q`: 12 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_591_documents_servicenow_secret_redaction_key_projection -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 194 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 665 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2654 passed, 93.34% coverage.
