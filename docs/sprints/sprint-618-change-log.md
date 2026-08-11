# Sprint 618 Change Log

## Alert webhook payload exact-string boundary

Sprint 618 continued production hardening by requiring exact string values before outbound alert webhook payloads are serialized into compact JSON bodies. `_alert_body_bytes()` already rejected non-finite numeric values and unsupported non-JSON values, but string subclasses still passed the alert payload preflight and could be serialized as ordinary strings before transport.

`_ensure_alert_payload_json_safe()` now accepts exact `str` values and exact `str` mapping keys only. String subclasses fail through the same `alert webhook payload contains non-JSON values` diagnostic as other unsupported values, without echoing alert field names, story or correlation identifiers, object output, credential-like keys, or payload values.

Verification:

- Added 1 failing-first alert delivery test proving a string subclass alert payload value was accepted before implementation.
- `python3 -m pytest tests/test_alert_delivery.py::test_alert_body_bytes_rejects_string_subclass_payload_without_warning_or_leak -q`: failed before implementation because no `AlertDeliveryError` was raised.
- `python3 -m pytest tests/test_alert_delivery.py -q`: 71 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 692 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2716 tests passed at 93.11% coverage.
