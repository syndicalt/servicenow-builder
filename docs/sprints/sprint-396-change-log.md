# Sprint 396 Change Log

## Bounded alert webhook metadata headers

Hardened external alert webhook delivery so generated metadata header values cannot be oversized. Alert delivery already rejected ASCII control characters before transport invocation, but it still allowed unbounded `alert_id`, `job_id`, `event_id`, story number, and correlation id values in outbound headers.

Alert metadata header validation now rejects values longer than 256 characters before sending. The compact JSON alert body remains governed by the existing `max_body_bytes` control; this sprint only closes the outbound metadata header boundary.

## Tests

- Failing-first coverage: 5 parameterized cases failed before implementation, proving oversized alert metadata values were sent for `alert_id`, `job_id`, `event_id`, story number, and correlation id.
- Focused verification: `python3 -m pytest tests/test_alert_delivery.py -q -k "header_values or sends_bounded_json_payload or omits_empty_correlation_header"` passed with 12 tests.
- Broader alert verification: `python3 -m pytest tests/test_alert_delivery.py -q` passed with 30 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 470 documentation tests passed, and 2154 total tests passed at 93.92% coverage.
