# Sprint 742 Change Log - Alert webhook payload cause boundary

## Scope

Hardened alert webhook payload diagnostics so alert body generation failures do not retain unsafe
low-level exception instances as public `AlertDeliveryError` causes.

## Tests First

- Added 3 failing-first alert webhook payload cause assertions:
  - `tests/test_alert_delivery.py::test_alert_body_bytes_rejects_non_finite_payload_without_warning_or_leak`
  - `tests/test_alert_delivery.py::test_alert_body_bytes_rejects_non_json_payload_without_warning_or_leak`
  - `tests/test_alert_delivery.py::test_alert_body_bytes_rejects_string_subclass_payload_without_warning_or_leak`
- Initial failures proved the public `AlertDeliveryError` retained unsafe causes for:
  - Alert `detail` non-finite numeric payload rejection.
  - Alert `SecretBearingObject` unsupported object rejection.
  - Alert `HostileAlertText` string subclass payload rejection.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_742_documents_alert_webhook_payload_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original Pydantic serializer causes in `_alert_body_bytes()`.
- Suppressed original non-finite numeric validation causes in `_alert_body_bytes()`.
- Suppressed original non-JSON structure validation causes in `_alert_body_bytes()`.
- Preserved the existing fixed diagnostics:
  - `alert webhook payload contains non-finite numeric values`
  - `alert webhook payload contains non-JSON values`
- Documented the alert webhook payload cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_alert_delivery.py -q -k "alert_body_bytes_rejects"` failed first with
  3 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_742` failed first with 1 failure.
- `python3 -m pytest tests/test_alert_delivery.py -q -k "alert_body_bytes_rejects"` passed with 3 tests
  and 68 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_742` passed with 1 test and 815
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_alert_delivery.py -q` passed with 71 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3072 tests and 93.33% total coverage.
