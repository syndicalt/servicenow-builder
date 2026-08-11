# Sprint 826 Change Log - Lifecycle webhook credential policy parity

## Scope

Centralized lifecycle webhook credential policy so production startup validation and request-time lifecycle authentication share one credential byte ceiling.

## Tests First

- Added 1 failing-first lifecycle webhook secret ceiling assertion: `tests/test_runtime.py::test_validate_runtime_settings_rejects_oversized_lifecycle_webhook_secret`.
- Added 1 failing-first shared lifecycle webhook credential policy assertion: `tests/test_runtime.py::test_lifecycle_webhook_credential_policy_is_shared_by_startup_and_request_time`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_826_documents_lifecycle_webhook_credential_policy_parity`.
- Initial failure proved production startup validation accepted a 8193-byte configured `JEDI_LIFECYCLE_WEBHOOK_SECRET`, while request-time lifecycle auth rejected the same credential shape.

## Changes

- Added `jedi_devproject.lifecycle_webhook_policy` as the shared source for `MAX_LIFECYCLE_WEBHOOK_CREDENTIAL_BYTES` and lifecycle credential malformed checks.
- Runtime startup validation now rejects configured HMAC lifecycle webhook secrets larger than 8192 bytes.
- Lifecycle request-time auth delegates configured secret, shared-secret header, timestamp, and signature credential shape checks to the shared policy.
- Updated the operator guide to document that startup validation and request-time lifecycle auth share one credential ceiling.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "oversized_lifecycle_webhook_secret or lifecycle_webhook_credential_policy_is_shared"` - 2 passed, 379 deselected.
- `python3 -m pytest tests/test_lifecycle_api.py -q -k "malformed_configured_secret or timestamp_invalid or signature_rejected or oversized"` - 8 passed, 38 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k "sprint_826 or two_hundred_thirty_three_documents_webhook_secret_hygiene"` - 2 passed, 897 deselected.
- `python3 -m ruff check src tests` - All checks passed.
- `python3 -m mypy src tests` - Success: no issues found in 202 source files.
- `python3 -m pytest tests/test_runtime.py -q` - 381 passed.
- `python3 -m pytest tests/test_lifecycle_api.py -q` - 46 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3259 passed, 93.42% coverage.
