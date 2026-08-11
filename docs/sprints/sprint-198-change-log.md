# Sprint 198 Change Log

Scope: Production hardening - quote-aware sensitive assignment redaction.

## Changes

- Added regression coverage for sensitive assignment values quoted with embedded spaces.
- Updated diagnostic assignment redaction to consume complete single-quoted and double-quoted values before replacing them with `***REDACTED***`.
- Preserved existing unquoted assignment, authorization scheme, URL userinfo, encoded query-key, semicolon query, and hyphenated key redaction behavior.
- Documented quote-aware sensitive assignment redaction in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime_redaction.py -q` - 10 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 272 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1422 passed, 93.92% coverage.
