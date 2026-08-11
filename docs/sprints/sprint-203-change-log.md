# Sprint 203 Change Log

Scope: Production hardening - cloud credential redaction aliases.

## Changes

- Added regression coverage for cloud credential assignment names such as `aws_secret_access_key`, `awsSessionToken`, and `azureClientSecret`.
- Added diagnostic URL query redaction coverage for cloud credential query keys.
- Added alert webhook URL validation coverage for `awsSecretAccessKey` query parameters.
- Added alert sink response and ServiceNow API diagnostic redaction coverage for structured cloud credential keys.
- Extended the shared sensitive-key vocabulary with AWS and Azure credential aliases.
- Documented cloud credential redaction aliases in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime_redaction.py tests/test_alert_webhook_url.py tests/test_alert_delivery.py::test_emit_alert_webhook_failure_redacts_sensitive_response_values tests/test_servicenow.py::test_redact_secrets_masks_sensitive_values -q` - 42 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 277 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1446 passed, 93.92% coverage.
