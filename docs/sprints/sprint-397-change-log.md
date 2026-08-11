# Sprint 397 Change Log

## Pre-serialization alert body text bounds

Hardened external alert webhook delivery so generated alert body text cannot force unbounded JSON serialization before the existing payload-size gate runs. The prior delivery path bounded the final compact JSON body with `max_body_bytes`, but it still serialized the full `ExternalAlert` first.

Alert delivery now rejects generated `severity`, `status`, `summary`, `detail`, and `operator_action` values longer than 16 KiB before calling the JSON encoder or HTTP transport. The existing `JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES` limit still governs the final compact JSON payload. The new rejection diagnostic names only the field and configured limit, not the generated value.

## Tests

- Failing-first coverage: 5 parameterized cases failed before implementation, proving oversized alert body text reached `json.dumps()` for `severity`, `status`, `summary`, `detail`, and `operator_action`.
- Focused verification: `python3 -m pytest tests/test_alert_delivery.py -q -k "oversized_body_text or oversized_payload or header_values or sends_bounded_json_payload"` passed with 17 tests.
- Broader alert verification: `python3 -m pytest tests/test_alert_delivery.py -q` passed with 35 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 471 documentation tests passed, and 2160 total tests passed at 93.93% coverage.
