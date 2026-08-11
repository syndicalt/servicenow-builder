# Sprint 499 Change Log

## Alert webhook outbound JSON non-JSON value rejection

Hardened `_alert_body_bytes()` so external alert webhook bodies cannot fail through raw Pydantic serializer diagnostics when corrupted in-process alert DTOs contain unsupported Python values.

Sprint 470 rejected non-finite numeric alert payload values. This sprint closes the adjacent structural JSON gap: unsupported objects, bytes, and other non-JSON values now fail before compact JSON body generation or transport with the fixed `alert webhook payload contains non-JSON values` diagnostic. The diagnostic does not echo alert field names, story or correlation identifiers, object type names, object string output, credential-like keys, or payload values.

The implementation preserves valid Pydantic-native alert values such as timezone-aware datetimes by preflighting Python-mode payloads, then rendering the established compact JSON-mode webhook body.

## Verification

- Added 1 failing-first alert delivery test proving an object with secret-bearing `__str__` output previously surfaced a raw Pydantic serializer diagnostic.
- `python3 -m pytest tests/test_alert_delivery.py::test_alert_body_bytes_rejects_non_json_payload_without_warning_or_leak -q`: failed before implementation because the diagnostic reflected the local object type name.
- `python3 -m pytest tests/test_alert_delivery.py::test_alert_body_bytes_rejects_non_json_payload_without_warning_or_leak tests/test_alert_delivery.py::test_alert_body_bytes_rejects_non_finite_payload_without_warning_or_leak tests/test_alert_delivery.py::test_emit_alert_webhook_sends_bounded_json_payload -q`: 3 tests passed.
- `python3 -m pytest tests/test_alert_delivery.py -q`: 65 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 573 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2441 total tests passed at 93.69% coverage.
