# Sprint 202 Change Log

Scope: Production hardening - PEM and private-key redaction.

## Changes

- Added regression coverage for multiline PEM private-key blocks in diagnostic strings.
- Added multiline diagnostic redaction for `-----BEGIN ... PRIVATE KEY-----` through `-----END ... PRIVATE KEY-----`.
- Added alert webhook URL validation coverage for `private_key` query parameters.
- Added alert sink response and ServiceNow API diagnostic redaction coverage for structured `private_key`, `privateKey`, and `ssh_private_key` keys.
- Extended the shared sensitive-key vocabulary with private-key aliases.
- Documented PEM private-key block redaction in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime_redaction.py tests/test_alert_webhook_url.py tests/test_alert_delivery.py::test_emit_alert_webhook_failure_redacts_sensitive_response_values tests/test_servicenow.py::test_redact_secrets_masks_sensitive_values -q` - 38 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 276 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1441 passed, 93.92% coverage.
