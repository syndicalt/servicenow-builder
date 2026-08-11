# Sprint 422 Change Log

## Safe unstringifiable exception type labels

Hardened the fallback message introduced for unstringifiable handler exceptions. Python exception class metadata can be mutated, so a malformed exception type name could place unsafe or secret-like text into the generic fallback before redaction.

The runtime redaction wrapper now includes the exception type label only when it is an ASCII Python identifier and no longer than 128 characters. Unsafe, non-ASCII, oversized, or mutated labels collapse to `handler raised unstringifiable exception`.

This keeps the fallback useful for normal code-owned exception classes while preventing attacker-controlled or malformed exception metadata from becoming diagnostic content.

## Verification

- Added 1 failing-first test mutating an unstringifiable exception class name to `client-secret-value`.
- `python3 -m pytest tests/test_runtime_redaction.py -q -k "type_label"`: failed before implementation because the unsafe label was included and redacted as `***REDACTED***`.
- `python3 -m pytest tests/test_runtime_redaction.py -q`: 21 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 191 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 496 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2254 total tests passed at 93.97% coverage.
