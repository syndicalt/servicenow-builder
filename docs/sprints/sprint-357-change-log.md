# Sprint 357 Change Log

## Runtime request validation error input suppression

Hardened framework-generated runtime request validation errors so malformed path and query
parameters cannot reflect submitted values back to callers. Sprint 356 fixed lifecycle DTO
validation responses inside the webhook handler, but FastAPI can raise `RequestValidationError`
before route-level code runs. For admin diagnostic endpoints, a malformed query value such as
`limit=client_secret=...` could therefore produce an HTTP 422 response containing the rejected
`input` value before admin token validation.

The runtime app now installs a `RequestValidationError` handler that returns structured validation
type, location, and message metadata while stripping Pydantic/FastAPI `input` fields from the
response body. This keeps operator diagnostics useful without reflecting credentials, ServiceNow
sys_ids, or other caller-controlled fragments from malformed requests.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving `/admin/jobs?limit=client_secret=...` echoed the rejected query value in the HTTP 422 response before store access.
- Focused verification: `python3 -m pytest tests/test_runtime.py -q -k "admin_query_validation_error_does_not_echo_rejected_input"` passed after implementation.
- Runtime regression verification: `python3 -m pytest tests/test_runtime.py -q` passed with 283 tests.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 187 source files, 431 documentation tests passed, and 2039 total tests passed at 94.07% coverage.
