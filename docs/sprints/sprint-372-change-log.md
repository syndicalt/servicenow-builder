# Sprint 372 Change Log

## Generic provider response validation bounds

Hardened the generic provider-policy validation path used by `generate_with_provider()` so older or test-only model providers cannot bypass bounded model-response validation. Previous hardening bounded OpenAI and Anthropic adapter normalization, but the generic validator still accepted more than 100 changes and reflected rejected table, operation, or sys_id values directly in `ModelResponseError` diagnostics.

The generic validator now rejects responses with more than 100 candidate changes before allowlist evaluation. Rejected table, operation, and sys_id values are passed through diagnostic redaction, whitespace/control-character normalization, and a fixed diagnostic cap before being included in `ModelResponseError`. Short ordinary operator diagnostics such as `table not allowed: sys_user` remain available.

## Tests

- Failing-first coverage: 2 tests failed before implementation, proving oversized generic provider responses were accepted and rejected table diagnostics could echo secret-like values plus newline injection.
- Focused verification: `python3 -m pytest tests/test_providers.py -q` passed with 8 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 188 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 188 source files, 446 documentation tests passed, and 2079 total tests passed at 93.84% coverage.
