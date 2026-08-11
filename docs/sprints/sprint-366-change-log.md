# Sprint 366 Change Log

## Traversal-bounded ServiceNow API diagnostics

Hardened ServiceNow API error diagnostics so a wide response body cannot force full recursive redaction before the final diagnostic cap. Previous controls normalized and redacted diagnostic strings and capped the final error text, but `_servicenow_diagnostic_value()` still walked entire dictionary, list, and tuple structures before `repr()` and truncation.

The ServiceNow diagnostic projection now samples dictionaries, lists, and tuples with bounded iterators. Wide dictionaries include an `omitted_fields` marker; wide arrays and tuples include an `omitted_items` marker. Sensitive keys still redact before recursion, string values still use ServiceNow diagnostic normalization and redaction, and `_servicenow_api_error_message()` still applies the final cap.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving a wide ServiceNow API diagnostic mapping was fully consumed before final error formatting.
- Focused verification: `python3 -m pytest tests/test_servicenow.py -q -k "does_not_consume_all_fields or api_failure_normalizes_untrusted_error_diagnostics or api_failure_bounds_final_error_diagnostic or redact_secrets_masks_sensitive"` passed with 14 tests.
- ServiceNow regression verification: `python3 -m pytest tests/test_servicenow.py -q` passed with 84 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 187 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 187 source files, 440 documentation tests passed, and 2061 total tests passed at 93.91% coverage.
