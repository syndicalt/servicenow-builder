# Sprint 443 Change Log

## Provider candidate field-name normalization

Hardened shared provider candidate normalization so model-provided `name/value` field entries cannot silently overwrite each other or carry unsafe field-name text into internal implementation intent. Prior behavior collapsed duplicate field names with last-value-wins semantics and accepted field names containing whitespace or control characters.

Provider candidate normalization now rejects:

- duplicate field names within a single change
- field names longer than 200 characters
- field names containing whitespace or control characters

Failures use fixed diagnostics such as:

- `TestProvider response field entry names must be unique`
- `TestProvider response field entry name must not contain whitespace or control characters`

The diagnostics do not echo the model-provided field name, field value, credential-like keys, or upstream response fragments.

## Verification

- Added 5 provider normalization tests covering duplicate field names, oversized field names, and unsafe whitespace/control-character field names. The duplicate and unsafe-name tests were added failing-first before implementation; the length-boundary test covers the documented 200-character cap.
- `python3 -m pytest tests/test_provider_response_normalization.py -q`: failed before implementation because duplicate and unsafe field names were silently accepted.
- `python3 -m pytest tests/test_provider_response_normalization.py -q`: 5 tests passed after implementation.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 194 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 517 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2318 total tests passed at 93.98% coverage.
