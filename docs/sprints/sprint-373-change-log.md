# Sprint 373 Change Log

## Sanitized provider-policy block diagnostics

Hardened provider-policy block diagnostics so configured provider ids and requested task names cannot inject log lines or echo secret-like fragments when `generate_with_provider()` raises `ProviderBlocked`. Previous generic provider hardening sanitized rejected model response values, but the policy-block path still reflected `policy.provider_id` and `task` directly.

`ProviderBlocked` messages now reuse the generic model-response diagnostic sanitizer. Provider ids and task names are passed through diagnostic redaction, whitespace/control-character normalization, and the fixed model-response diagnostic cap before inclusion. The policy check still happens before provider prompt construction, so blocked tasks do not call the provider.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving a blocked provider task could echo secret-like values and newline injection in the block diagnostic.
- Focused verification: `python3 -m pytest tests/test_providers.py -q` passed with 9 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 188 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 188 source files, 447 documentation tests passed, and 2081 total tests passed at 93.84% coverage.
