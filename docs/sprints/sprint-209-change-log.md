# Sprint 209 Change Log

Scope: Production hardening - alert webhook legacy numeric IPv4 SSRF guard.

## Changes

- Added regression coverage for short-form loopback IPv4 targets such as `127.1`.
- Added regression coverage for integer, octal, and hexadecimal loopback IPv4 targets such as `2130706433`, `0177.0.0.1`, and `0x7f000001`.
- Added regression coverage for integer link-local metadata targets such as `2852039166`.
- Extended shared alert webhook URL validation with deterministic legacy numeric IPv4 parsing, without DNS resolution and without blocking ordinary private-network alert sinks.
- Documented legacy numeric local-target rejection in the operator guide.

## Verification

- `python3 -m pytest tests/test_alert_webhook_url.py -q` - 33 passed.
- `python3 -m pytest tests/test_alert_delivery.py::test_emit_alert_webhook_rejects_integer_loopback_ipv4_url tests/test_runtime.py::test_validate_runtime_settings_rejects_alert_webhook_url_legacy_ipv4_loopback -q` - 2 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 283 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1478 passed, 93.94% coverage.
