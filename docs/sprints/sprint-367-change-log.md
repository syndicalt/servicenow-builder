# Sprint 367 Change Log

## Traversal-bounded HTTP error diagnostic shaping

Hardened ServiceNow transport error diagnostics so parsed HTTP error JSON cannot force full recursive diagnostic shaping before response handling continues. Previous controls bounded the raw response read, capped large strings, and capped the later ServiceNow API exception text, but `_bound_http_error_diagnostics()` still used whole-structure comprehensions for dictionaries and lists.

The HTTP error diagnostic projector now samples dictionaries, lists, and tuples with bounded iterators. Wide dictionaries include an `omitted_fields` marker; wide arrays and tuples include an `omitted_items` marker. String values still use the existing HTTP diagnostic truncation path, and oversized raw response bodies remain rejected before JSON parsing.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving a wide parsed HTTP error diagnostic mapping was fully consumed before bounded response shaping completed.
- Focused verification: `python3 -m pytest tests/test_servicenow.py -q -k "bound_http_error_diagnostics_does_not_consume_all_fields or truncates_large_json_http_error_strings or truncates_large_non_json_http_error_body or returns_json_body_for_http_error_response or preserves_non_json_http_error_body or bounds_oversized_http_error_response_body or does_not_consume_all_fields"` passed with 7 tests.
- ServiceNow regression verification: `python3 -m pytest tests/test_servicenow.py -q` passed with 85 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 187 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 187 source files, 441 documentation tests passed, and 2063 total tests passed at 93.83% coverage.
