# Sprint 758 Change Log - Lifecycle payload cause boundary

## Scope

Hardened lifecycle webhook payload diagnostics so malformed JSON and schema-validation failures do not retain unsafe parser or validation exceptions as public `HTTPException` causes.

## Tests First

- Added 2 failing-first lifecycle payload cause assertions:
  - `tests/test_lifecycle_api.py::test_lifecycle_webhook_invalid_json_does_not_retain_cause`
  - `tests/test_lifecycle_api.py::test_lifecycle_webhook_validation_error_does_not_retain_cause`
- Initial failures proved malformed JSON retained `JSONDecodeError` and schema validation retained Pydantic `ValidationError` on the public `HTTPException.__cause__`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_758_documents_lifecycle_payload_cause_boundary`
- The documentation assertion was added before the sprint log and operator guide update, so the docs gate covers the new operator-facing contract.

## Changes

- Suppressed original JSON parser causes for `invalid lifecycle webhook JSON` responses.
- Suppressed original Pydantic validation causes for sanitized lifecycle payload validation responses.
- Preserved fixed diagnostics:
  - `invalid lifecycle webhook JSON`
  - sanitized Pydantic details such as `extra_forbidden`
- Documented the lifecycle webhook payload cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_lifecycle_api.py -q -k "does_not_retain_cause and lifecycle_webhook"` - 3 passed, 43 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_758` - 1 passed, 831 deselected.
- `python3 -m pytest tests/test_lifecycle_api.py -q` - 46 passed.
- `ruff check src tests` - passed.
- `mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3098 passed, 93.38% coverage.
