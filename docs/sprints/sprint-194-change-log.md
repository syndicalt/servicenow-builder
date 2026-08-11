# Sprint 194 Change Log

Scope: Production hardening - all-userinfo diagnostic URL redaction.

## Changes

- Updated shared diagnostic URL redaction to mask the entire URL userinfo component whenever username or password userinfo is present.
- Added regression coverage for username-only userinfo such as `https://api-token@example.service-now.com/api`.
- Updated runtime admin diagnostics expectations so job events and operational alerts no longer expose URL usernames.
- Preserved host, path, and non-sensitive query detail for operator troubleshooting.
- Documented all-userinfo diagnostic URL redaction in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime_redaction.py tests/test_runtime.py::test_job_events_returns_correlation_metadata_and_redacted_messages tests/test_runtime.py::test_admin_alerts_lists_attention_jobs_with_correlation_and_redacted_details tests/test_alert_delivery.py::test_worker_failure_alert_preserves_job_story_and_redacted_message tests/test_alert_delivery.py::test_rejected_job_alert_preserves_job_context_and_redacts_reason tests/test_servicenow.py::test_http_request_sanitized_redacts_url_credentials_and_sensitive_query -q` - 10 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 268 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1411 passed, 93.92% coverage.
