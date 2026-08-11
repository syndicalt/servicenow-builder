# Sprint 585 Change Log

## ServiceNow API diagnostic text string-subclass guard

Sprint 585 continued production hardening by preventing ServiceNow API exception diagnostics from accepting string subclasses as trusted response text. `_servicenow_diagnostic_value()` already redacted sensitive keys, bounded traversal, normalized exact strings, and capped the final exception diagnostic, but a Python transport or future client path could still provide a `str` subclass inside `HttpResponse.json_body` and have that value processed as normal diagnostic text.

ServiceNow API diagnostic projection now accepts exact `str` values only for redacted text handling. String subclasses render as `[non-json value]` before redaction, whitespace normalization, `repr()` formatting, final diagnostic truncation, work-note failure reporting, artifact references, or operator-log output. Ordinary JSON scalars remain typed, finite floats remain available for diagnostics, and unsupported Python-only scalar values use the same stable marker instead of reflecting object representations.

This keeps ServiceNow API failure diagnostics useful while ensuring alternate transports cannot inject subclass behavior, object type names, object string output, upstream body fragments, or credential-like payloads into operator-facing exception text.

Verification:

- Added 1 failing-first ServiceNow API diagnostic text string-subclass test proving a subclassed error `message` was accepted as redacted diagnostic text before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_api_failure_rejects_string_subclass_diagnostic_text -q`: failed before implementation because the subclassed ServiceNow error message appeared as normal redacted diagnostic text instead of `[non-json value]`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_api_failure_rejects_string_subclass_diagnostic_text tests/test_servicenow.py::test_servicenow_api_failure_bounds_final_error_diagnostic tests/test_servicenow.py::test_servicenow_diagnostic_value_does_not_consume_all_fields_for_wide_response -q`: 3 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_585_documents_servicenow_api_diagnostic_text_str_subclass_guard -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 188 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 659 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2642 passed, 93.35% coverage.
