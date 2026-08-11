# Sprint 356 Change Log

## Lifecycle webhook validation error input suppression

Hardened public lifecycle webhook validation errors so malformed JSON objects cannot reflect
submitted payload values back to callers. The lifecycle DTOs already hide input in Pydantic
exception text, but the FastAPI route returned `ValidationError.errors(include_url=False)` directly;
Pydantic includes an `input` field in that structured error output by default. Extra fields or
invalid values could therefore echo ServiceNow sys_ids, work notes, credentials, or other submitted
payload fragments in the HTTP 422 response.

The lifecycle route now returns validation errors with `include_input=False`. Operators still get
structured error type, location, and message metadata for debugging, while rejected payload values
are omitted from the response body. Invalid JSON remains a fixed `invalid lifecycle webhook JSON`
diagnostic.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving an extra lifecycle webhook
  field containing `client_secret=...` was echoed in the HTTP 422 response body.
- Focused verification: `python3 -m pytest tests/test_lifecycle_api.py -q -k "validation_error_does_not_echo_rejected_input"` passed after implementation.
- Lifecycle API regression verification: `python3 -m pytest tests/test_lifecycle_api.py -q` passed with 28 tests.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 187 source files, 430 documentation tests passed, and 2037 total tests passed at 94.07% coverage.
