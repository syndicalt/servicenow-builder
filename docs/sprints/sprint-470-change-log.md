# Sprint 470 Change Log

## Alert webhook outbound JSON non-finite number rejection

Hardened alert webhook body generation so outbound alert JSON cannot silently normalize corrupted
in-process alert payloads containing `NaN`, `Infinity`, or `-Infinity`. Alert delivery is an
operational incident path, so it must fail closed before transport instead of sending non-strict or
shape-masked JSON to an external sink.

`_alert_body_bytes()` now preflights the Python-mode `ExternalAlert` payload with strict JSON
numeric handling before generating the compact webhook body. Non-finite alert payload values fail
with `alert webhook payload contains non-finite numeric values`. The diagnostic is stable, does not
echo alert field names, story or correlation identifiers, or values, and suppresses Pydantic
serializer warnings for malformed constructed alert objects.

## Verification

- Added 1 failing-first alert delivery test covering non-finite outbound alert payload rejection
  before transport, without warning, field-name, or value reflection.
- `python3 -m pytest tests/test_alert_delivery.py::test_alert_body_bytes_rejects_non_finite_payload_without_warning_or_leak -q`:
  failed before implementation because body generation accepted the corrupted alert payload.
- `python3 -m pytest tests/test_alert_delivery.py::test_emit_alert_webhook_sends_bounded_json_payload tests/test_alert_delivery.py::test_alert_body_bytes_rejects_non_finite_payload_without_warning_or_leak tests/test_alert_delivery.py::test_emit_alert_webhook_omits_empty_correlation_header -q`:
  3 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 544 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2382 total tests passed at 93.84% coverage.
