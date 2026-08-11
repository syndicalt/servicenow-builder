# Sprint 456 Change Log

## Alert sink response non-finite float diagnostic hardening

Hardened alert sink response diagnostics so non-finite float values cannot be emitted
as `NaN`, `Infinity`, or `-Infinity` in `AlertDeliveryError` JSON diagnostics. Python
`json.dumps()` permits those tokens by default even though they are not strict JSON,
so malformed alternate transport payloads could produce non-portable operator evidence.

Alert response redaction now preserves finite floats and ordinary JSON scalars, but maps
non-finite floats to `[non-json value]`. Existing string redaction, key sanitization,
non-JSON scalar handling, cycle handling, depth cap, width bounds, and whole-diagnostic
cap remain intact.

## Verification

- Added 1 failing-first alert response diagnostic test covering NaN, positive infinity,
  negative infinity, and a finite float.
- `python3 -m pytest tests/test_alert_delivery.py -q -k "non_finite_floats"`: failed
  before implementation because `NaN`, `Infinity`, and `-Infinity` reached the diagnostic
  JSON.
- `python3 -m pytest tests/test_alert_delivery.py -q -k "non_finite_floats or non_json_response_values or excessive_response_depth or circular_response_payloads or sensitive_response_keys or non_string_response_keys or alert_response_diagnostic_does_not_consume_all_fields"`:
  7 tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 530 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2350 total tests passed at 93.80% coverage.
