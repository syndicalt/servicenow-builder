# Sprint 261 Change Log - Lifecycle Webhook Streaming Body Bound

## Summary

- Lifecycle webhook request bodies are now read through a bounded streaming helper instead of `request.body()`.
- Added a failing regression proving an oversized lifecycle stream is rejected with `413` once accumulated bytes exceed the configured cap.
- Updated the lifecycle receiver to parse JSON from the already-bounded byte buffer, preserving HMAC signing against the raw request body.
- Removed the stale post-read size helper so lifecycle request-size enforcement has one authoritative path.
- Documented that lifecycle webhook body limits are enforced before JSON parsing, HMAC validation, lifecycle planning, or operational-store writes.

## Verification

- `python3 -m pytest tests/test_lifecycle_api.py::test_lifecycle_webhook_records_ready_event_and_enqueues_fulfillment tests/test_lifecycle_api.py::test_lifecycle_webhook_rejects_oversized_payload_before_recording tests/test_lifecycle_api.py::test_lifecycle_bounded_body_reader_rejects_stream_before_unbounded_read tests/test_lifecycle_api.py::test_lifecycle_webhook_hmac_auth_accepts_valid_signature -q` - 4 passed.
- `python3 -m ruff check src/jedi_devproject/lifecycle_api.py tests/test_lifecycle_api.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/lifecycle_api.py tests/test_lifecycle_api.py` - success: no issues found in 2 source files.
- `python3 -m pytest tests/test_lifecycle_api.py::test_lifecycle_webhook_records_ready_event_and_enqueues_fulfillment tests/test_lifecycle_api.py::test_lifecycle_webhook_rejects_oversized_payload_before_recording tests/test_lifecycle_api.py::test_lifecycle_bounded_body_reader_rejects_stream_before_unbounded_read tests/test_lifecycle_api.py::test_lifecycle_webhook_hmac_auth_accepts_valid_signature tests/test_project_docs.py::test_sprint_two_hundred_sixty_one_documents_lifecycle_streaming_body_bound -q` - 5 passed.
- `python3 -m ruff check src/jedi_devproject/lifecycle_api.py tests/test_lifecycle_api.py tests/test_project_docs.py` - all checks passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 174 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 335 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1654 passed, total coverage 93.96%.
