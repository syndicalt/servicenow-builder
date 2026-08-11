# Sprint 399 Change Log

## Nonblank alert metadata headers

Hardened external alert webhook delivery so metadata header values cannot be empty or padded. The prior delivery path rejected ASCII control characters and oversized header values, but it still allowed blank `Idempotency-Key` values and ambiguous padded correlation metadata.

Alert delivery now rejects empty or padded `alert_id`, `job_id`, `event_id`, story number, and correlation id values before HTTP transport. Existing controls still reject ASCII control characters and values longer than 256 characters. The rejection diagnostic names only the unsafe field, not the supplied value.

## Tests

- Failing-first coverage: 5 parameterized cases failed before implementation, proving blank or padded alert metadata values were accepted for `alert_id`, `job_id`, `event_id`, story number, and correlation id.
- Focused verification: `python3 -m pytest tests/test_alert_delivery.py -q -k "blank_or_padded_header_values or unknown_routing_values or oversized_body_text or oversized_payload or header_values or sends_bounded_json_payload"` passed with 24 tests.
- Broader alert verification: `python3 -m pytest tests/test_alert_delivery.py -q` passed with 42 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 473 documentation tests passed, and 2169 total tests passed at 93.93% coverage.
