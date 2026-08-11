# Sprint 588 Change Log

## ServiceNow API diagnostic key projection

Sprint 588 continued production hardening by preventing ServiceNow API exception diagnostics from reflecting Python-specific dictionary keys. `_servicenow_diagnostic_value()` already redacted sensitive keys, bounded traversal, guarded diagnostic text values, and capped the final exception diagnostic, but it still preserved raw dictionary keys before `repr()` formatting.

ServiceNow API diagnostic projection now renders diagnostic keys through a safe key path. Exact string keys are redacted and whitespace-normalized before formatting, duplicate rendered keys receive deterministic suffixes, and non-string keys render as `[non-json key]` without calling `str()` or `repr()` on the original key. Sensitive-key value masking still uses the original exact string key, so ordinary ServiceNow JSON diagnostics preserve structured secret redaction while Python-only keys fail closed.

This keeps ServiceNow API failure diagnostics useful while ensuring alternate transports cannot inject object type names, object string output, upstream key fragments, or credential-like payloads into operator-facing exception text.

Verification:

- Added 1 failing-first ServiceNow API diagnostic key projection test proving a hostile dictionary key `repr()` was reflected before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_api_failure_rejects_non_json_diagnostic_keys -q`: failed before implementation because the hostile key representation appeared in the ServiceNow API diagnostic instead of `[non-json key]`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_api_failure_rejects_non_json_diagnostic_keys tests/test_servicenow.py::test_servicenow_api_failure_rejects_string_subclass_diagnostic_text tests/test_servicenow.py::test_servicenow_api_failure_raises_without_secret_leakage tests/test_servicenow.py::test_servicenow_diagnostic_value_does_not_consume_all_fields_for_wide_response -q`: 4 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_588_documents_servicenow_api_diagnostic_key_projection -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 191 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 662 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2648 passed, 93.32% coverage.
