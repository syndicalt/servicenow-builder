# Sprint 407 Change Log

## ASCII-only lifecycle webhook credentials

Hardened lifecycle webhook authentication so non-ASCII inbound credential values are rejected before parsing or comparison. Sprint 406 added an 8 KiB cap for lifecycle credential headers, but the shared credential validator still treated character length and whitespace/control checks as sufficient for HMAC signatures and interim shared-secret values.

Lifecycle webhook credential validation now encodes inbound credential values as ASCII before applying the 8 KiB cap. Non-ASCII HMAC signature and shared-secret values fail closed before `hmac.compare_digest()`, and the size cap is measured in bytes rather than Python code points.

## Tests

- Failing-first coverage: 2 tests failed before implementation, proving non-ASCII HMAC signature and shared-secret values reached constant-time comparison.
- Focused verification: `python3 -m pytest tests/test_lifecycle_api.py -q -k "non_ascii_signature_before_compare or non_ascii_secret_before_compare"` passed with 2 tests.
- Broader lifecycle verification: `python3 -m pytest tests/test_lifecycle_api.py -q` passed with 33 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff format src/jedi_devproject/lifecycle_api.py tests/test_lifecycle_api.py tests/test_project_docs.py && python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 481 documentation tests passed, and 2198 total tests passed at 93.93% coverage.
