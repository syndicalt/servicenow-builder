# Sprint 196 Change Log

Scope: Production hardening - semicolon-separated sensitive query redaction.

## Changes

- Updated shared diagnostic URL query redaction to process both `&` and `;` query separators.
- Preserved original query separators and original query key spelling in diagnostic output.
- Added regression coverage for `sysparm_limit=1;client%5Fsecret=encoded-secret`.
- Kept non-sensitive query parameters visible for operator troubleshooting while masking sensitive values.
- Documented semicolon-separated sensitive query redaction in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime_redaction.py tests/test_servicenow.py::test_redact_secrets_masks_sensitive_strings_under_non_sensitive_keys tests/test_alert_delivery.py::test_worker_failure_alert_preserves_job_story_and_redacted_message -q` - 9 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 270 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1415 passed, 93.92% coverage.
