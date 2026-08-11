# Sprint 375 Change Log

## Bounded raw XML validation traversal

Hardened raw XML validation for implementation-packet model responses so malformed or adversarial nested model output cannot force unbounded recursive traversal. The previous validator recursively walked every dict/list node while looking for raw Update Set XML fields or content, which created an avoidable stack-depth and unbounded-work risk.

Raw XML validation now uses an explicit bounded stack. It fails closed when a response exceeds 1,000 scanned nodes or 32 nested levels, preserves fixed diagnostics for raw XML field and content rejection, and does not echo rejected model payload text. This keeps the no-raw-XML policy intact while giving the worker a predictable upper bound for validation work.

## Tests

- Failing-first coverage: 2 tests failed before implementation, proving excessive nesting and oversized model response graphs were accepted by the raw XML scanner.
- Focused verification: `python3 -m pytest tests/test_packet_validation.py -q` passed with 5 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 189 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 189 source files, 449 documentation tests passed, and 2088 total tests passed at 93.90% coverage.
