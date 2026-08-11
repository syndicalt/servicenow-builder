# Sprint 201 Change Log

Scope: Production hardening - cookie and Set-Cookie redaction.

## Changes

- Added regression coverage for `Cookie:` and `Set-Cookie:` diagnostic header values.
- Added line-bounded diagnostic header redaction so cookie material is masked without consuming following diagnostic lines.
- Added alert webhook URL validation coverage for `cookie` query parameters.
- Added alert sink response and ServiceNow API diagnostic redaction coverage for structured `Cookie` and `Set-Cookie` keys.
- Extended the shared sensitive-key vocabulary with `cookie` and `set_cookie`.
- Documented cookie-bearing diagnostic redaction in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime_redaction.py tests/test_alert_webhook_url.py tests/test_alert_delivery.py::test_emit_alert_webhook_failure_redacts_sensitive_response_values tests/test_servicenow.py::test_redact_secrets_masks_sensitive_values -q` - 35 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 275 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1437 passed, 93.92% coverage.
