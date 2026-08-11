# Sprint 398 Change Log

## Alert routing taxonomy gate

Hardened external alert webhook delivery so alert routing fields cannot be arbitrary generated strings. The prior delivery path bounded header metadata and body text length, but `severity` and `status` were still free-form values in the outbound payload.

Alert delivery now rejects unknown routing values before JSON serialization or HTTP transport. Allowed severities are `critical`, `warning`, and `info`; allowed statuses are `failed`, `rejected`, and `stale_requeued`. Rejection diagnostics name only the unsupported field, not the supplied value.

## Tests

- Failing-first coverage: 2 parameterized cases failed before implementation, proving unsupported `severity` and `status` values were accepted and sent.
- Focused verification: `python3 -m pytest tests/test_alert_delivery.py -q -k "unknown_routing_values or oversized_body_text or oversized_payload or header_values or sends_bounded_json_payload"` passed with 19 tests.
- Broader alert verification: `python3 -m pytest tests/test_alert_delivery.py -q` passed with 37 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 472 documentation tests passed, and 2163 total tests passed at 93.93% coverage.
