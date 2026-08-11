# Sprint 176 Change Log

## Scope

Production hardening: opt-in lifecycle rejected-job alert routing and broader diagnostic redaction.

## Changes

- Added `rejected_job_alert()` to convert terminal rejected `FulfillmentJobRecord` rows into strict `ExternalAlert` payloads.
- Added `rejected_job_notifier` support to `create_lifecycle_api()`.
- Rejected-job notifier failures are best-effort. They log a redacted warning and do not block lifecycle webhook acceptance after PostgreSQL records the rejected terminal job.
- Wired `create_runtime_api()` to emit rejected-job alerts through `emit_alert_webhook()` when `JEDI_ALERT_WEBHOOK_ENABLED=true`.
- Added injectable `alert_transport` support to `create_runtime_api()` so alert webhook tests and host wiring do not reuse the ServiceNow API transport.
- Hardened diagnostic redaction to mask plain sensitive key/value assignments such as `client_secret=value` and `access_token: value`, not only URL query values.
- Documented rejected-job alert routing in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime_redaction.py -q` - 1 passed.
- `python3 -m pytest tests/test_alert_delivery.py::test_rejected_job_alert_preserves_job_context_and_redacts_reason -q` - 1 passed.
- `python3 -m pytest tests/test_lifecycle_api.py::test_lifecycle_webhook_emits_rejected_job_notification_after_rejecting_story tests/test_lifecycle_api.py::test_lifecycle_webhook_rejected_job_notification_failure_does_not_block_acceptance -q` - 2 passed.
- `python3 -m pytest tests/test_runtime.py::test_runtime_rejected_event_emits_external_alert_without_enqueueing_worker -q` - 1 passed.
- `python3 -m pytest tests/test_runtime_redaction.py tests/test_alert_delivery.py -q` - 8 passed.
- `python3 -m pytest tests/test_lifecycle_api.py::test_lifecycle_webhook_records_story_rejected_reset_without_enqueueing_build tests/test_lifecycle_api.py::test_lifecycle_webhook_emits_rejected_job_notification_after_rejecting_story tests/test_lifecycle_api.py::test_lifecycle_webhook_rejected_job_notification_failure_does_not_block_acceptance -q` - 3 passed.
- `python3 -m pytest tests/test_runtime.py::test_runtime_complete_event_updates_ai_status_without_enqueueing_worker tests/test_runtime.py::test_runtime_rejected_event_emits_external_alert_without_enqueueing_worker -q` - 2 passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 250 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1366 passed, 93.88% coverage.

## Residual Risk

- Retention-prune alerts and a formal alert severity taxonomy still need explicit routing policy before external emission.
