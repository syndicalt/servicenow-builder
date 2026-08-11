# Sprint 400 Change Log

## Timezone-aware alert timestamps

Hardened external alert webhook delivery so alert timestamps cannot be ambiguous local-time values. The prior delivery path accepted naive `created_at` datetimes and serialized them into outbound JSON without timezone information.

Alert delivery now rejects naive `created_at` values before JSON serialization or HTTP transport. Timezone-aware alert timestamps continue to serialize through the compact JSON payload path. This keeps downstream incident timelines, audit storage, and replay diagnostics tied to explicit time offsets.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving a naive `created_at` reached `json.dumps()` before rejection.
- Focused verification: `python3 -m pytest tests/test_alert_delivery.py -q -k "created_at or blank_or_padded_header_values or unknown_routing_values or oversized_body_text or sends_bounded_json_payload"` passed with 15 tests.
- Broader alert verification: `python3 -m pytest tests/test_alert_delivery.py -q` passed with 44 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 474 documentation tests passed, and 2172 total tests passed at 93.93% coverage.
