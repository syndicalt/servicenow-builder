# Sprint 754 Change Log - Lifecycle HMAC timestamp cause boundary

## Scope

Hardened lifecycle webhook HMAC timestamp parsing so invalid timestamp diagnostics do not retain unsafe integer parser exceptions as public `HTTPException` causes.

## Tests First

- Added 1 failing-first lifecycle HMAC timestamp cause assertion:
  `tests/test_lifecycle_api.py::test_lifecycle_webhook_hmac_auth_invalid_timestamp_does_not_retain_cause`
- Initial failure proved a 5000-digit timestamp could pass the digit-only shape guard, fail Python integer parsing, and remain attached to the public `lifecycle webhook timestamp invalid` exception through `__cause__`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_754_documents_lifecycle_hmac_timestamp_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed the original integer parser cause in `_require_hmac_webhook_auth()` when HMAC timestamp parsing fails.
- Preserved the existing fixed diagnostic:
  - `lifecycle webhook timestamp invalid`
- Documented the lifecycle HMAC timestamp cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_lifecycle_api.py -q -k lifecycle_webhook_hmac_auth_invalid_timestamp_does_not_retain_cause` failed first, then passed.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_754` failed first, then passed.
- `ruff check src tests` passed.
- `mypy src tests` passed.
- `python3 -m pytest tests/test_lifecycle_api.py -q` passed: 44 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed: 3092 passed, 93.38% coverage.
