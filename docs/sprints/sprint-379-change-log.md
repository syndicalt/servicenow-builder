# Sprint 379 Change Log

## Sanitized surface-operation eligibility reasons

Hardened unsupported surface-operation eligibility reasons before they are stored in candidates, artifacts, worker diagnostics, or ServiceNow work notes. The manual-review path previously reflected `surface_operation_plan.operations[].kind` and `reason_codes[]` directly with `str()` conversion, which meant packet metadata could inject newlines, secret-like fragments, oversized text, or object internals into eligibility reasons.

Surface-operation `kind` values now pass through the shared safe feedback-note normalizer before inclusion. Reason codes are accepted only when they are strings; non-string values are skipped instead of stringified. String values are redacted, whitespace/control characters are collapsed, and capped at 2,000 characters including the truncation marker while preserving the stable `unsupported surface operation:` and `surface operation reason:` prefixes.

## Tests

- Failing-first coverage: 2 tests failed before implementation, proving unsupported surface-operation kind and reason-code metadata could leak secret-like fragments, newlines, object internals, and unbounded text into eligibility reasons.
- Focused verification: `python3 -m pytest tests/test_implementation_packet.py -q -k "surface_operation_reasons"` passed with 2 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 189 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 189 source files, 453 documentation tests passed, and 2101 total tests passed at 93.91% coverage.
