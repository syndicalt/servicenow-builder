# Sprint 586 Change Log

## ServiceNow secret redaction string-subclass guard

Sprint 586 continued production hardening by preventing shared ServiceNow diagnostic secret redaction from accepting string subclasses as primitive diagnostic text. `redact_secrets()` already masked sensitive structured keys, redacted credential-like fragments inside ordinary strings, and bounded traversal across dictionaries, lists, and tuples, but it still used `isinstance(value, str)` for string handling.

ServiceNow diagnostic secret redaction now accepts exact `str` values only for text redaction. String subclasses render as `[non-json value]` before URL password masking, sensitive query redaction, cookie redaction, Authorization redaction, private-key redaction, sensitive assignment redaction, request sanitization, exception formatting, work-note failure reporting, artifact references, or operator-log output.

This keeps sanitized ServiceNow request and response diagnostics useful while ensuring alternate transports cannot inject subclass behavior, object type names, object string output, or credential-like payloads into redacted diagnostics.

Verification:

- Added 1 failing-first ServiceNow secret redaction string-subclass test proving a subclassed diagnostic string was accepted and redacted as ordinary text before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_redact_secrets_rejects_string_subclass_diagnostic_text -q`: failed before implementation because the subclassed diagnostic string appeared as redacted text instead of `[non-json value]`.
- `python3 -m pytest tests/test_servicenow.py::test_redact_secrets_rejects_string_subclass_diagnostic_text tests/test_servicenow.py::test_redact_secrets_masks_sensitive_strings_under_non_sensitive_keys tests/test_servicenow.py::test_redact_secrets_masks_sensitive_values tests/test_servicenow.py::test_redact_secrets_does_not_consume_all_fields_for_wide_diagnostic -q`: 12 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_586_documents_servicenow_secret_redaction_str_subclass_guard -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 189 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 660 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2644 passed, 93.35% coverage.
