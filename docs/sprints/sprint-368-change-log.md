# Sprint 368 Change Log

## Traversal-bounded ServiceNow secret redaction

Hardened ServiceNow diagnostic secret redaction so wide request or response diagnostic bodies cannot force full recursive redaction before a sanitized diagnostic copy is produced. Previous controls shared a broad sensitive-key vocabulary and redacted unsafe diagnostic strings, but `redact_secrets()` still used whole-structure comprehensions for dictionaries and lists.

The ServiceNow redactor now samples dictionaries, lists, and tuples with bounded iterators. Wide dictionaries include an `omitted_fields` marker; wide arrays and tuples include an `omitted_items` marker. Sensitive keys still mask their values before recursion, and non-sensitive strings still use the shared diagnostic text redactor.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving a wide diagnostic mapping was fully consumed during secret redaction.
- Focused verification: `python3 -m pytest tests/test_servicenow.py -q -k "redact_secrets_does_not_consume_all_fields or redact_secrets_masks_sensitive or http_request_sanitized"` passed with 14 tests.
- ServiceNow regression verification: `python3 -m pytest tests/test_servicenow.py -q` passed with 86 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 187 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 187 source files, 442 documentation tests passed, and 2065 total tests passed at 93.77% coverage.
