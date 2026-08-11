# Sprint 195 Change Log

Scope: Production hardening - encoded sensitive query-key diagnostic redaction.

## Changes

- Updated shared diagnostic URL redaction to decode query key names before checking the sensitive-key vocabulary.
- Added regression coverage for encoded sensitive keys such as `client%5Fsecret=encoded-secret`.
- Preserved original query key spelling in diagnostics while masking the sensitive value.
- Preserved non-sensitive query parameters for operator troubleshooting.
- Documented encoded sensitive query-key redaction in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime_redaction.py tests/test_servicenow.py::test_redact_secrets_masks_sensitive_strings_under_non_sensitive_keys tests/test_alert_delivery.py::test_worker_failure_alert_preserves_job_story_and_redacted_message -q` - 8 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 269 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1413 passed, 93.92% coverage.
