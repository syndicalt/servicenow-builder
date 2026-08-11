# Sprint 364 Change Log

## Traversal-bounded alert sink diagnostics

Closed the root-cause counterpart to Sprint 363. Failed alert sink responses were capped after
recursive redaction and deterministic serialization, but the diagnostic formatter still walked the
entire response object before applying the final cap. A malicious or broken alert sink could
therefore return a very wide object or array and force unnecessary CPU and memory work even though
the final error string was bounded.

Alert sink diagnostics now sample dictionaries, lists, and tuples with bounded iterators before
serialization. Wide objects include an `omitted_fields` marker, and wide arrays or tuples include an
`omitted_items` marker. This preserves secret redaction and final diagnostic size caps while also
bounding the work needed to produce the diagnostic.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving a wide alert sink response mapping was fully consumed before diagnostic formatting.
- Focused verification: `python3 -m pytest tests/test_alert_delivery.py -q -k "does_not_consume_all_fields or whole_structured_response or bounds_redacted_response"` passed with 3 tests.
- Alert regression verification: `python3 -m pytest tests/test_alert_delivery.py -q` passed with 24 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 187 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 187 source files, 438 documentation tests passed, and 2057 total tests passed at 93.99% coverage.
