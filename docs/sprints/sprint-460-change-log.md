# Sprint 460 Change Log

## Lifecycle webhook non-finite JSON rejection

Hardened lifecycle webhook JSON ingestion so authenticated request bodies containing non-standard
JSON numeric constants such as `NaN`, `Infinity`, or `-Infinity` fail before lifecycle schema
validation, event recording, or fulfillment-job enqueue. Python `json.loads()` accepts those
constants by default, so a malformed ServiceNow emitter or proxy could previously push non-strict
JSON into validation as ordinary floats.

Lifecycle webhook parsing now rejects those constants with the same fixed
`invalid lifecycle webhook JSON` diagnostic used for malformed JSON and invalid UTF-8 bodies. The
diagnostic does not echo submitted field names, submitted values, or credential-like payload
fragments, and schema validation errors still preserve structured non-reflective Pydantic error
metadata.

## Verification

- Added 1 failing-first lifecycle webhook test covering authenticated non-finite JSON rejection
  before event recording or job enqueue.
- `python3 -m pytest tests/test_lifecycle_api.py::test_lifecycle_webhook_hmac_auth_rejects_non_finite_json_before_recording -q`:
  failed before implementation because `NaN` reached schema validation instead of the invalid-JSON
  path.
- `python3 -m pytest tests/test_lifecycle_api.py::test_lifecycle_webhook_hmac_auth_rejects_non_finite_json_before_recording tests/test_lifecycle_api.py::test_lifecycle_webhook_hmac_auth_rejects_invalid_utf8_json_before_recording tests/test_lifecycle_api.py::test_lifecycle_webhook_validation_error_does_not_echo_rejected_input tests/test_lifecycle_api.py::test_lifecycle_webhook_records_ready_event_and_enqueues_fulfillment -q`:
  4 tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 534 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2360 total tests passed at 93.83% coverage.
