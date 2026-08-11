# Sprint 404 Change Log

## Bounded stale-requeue alert diagnostics

Hardened stale-requeue alert construction so oversized individual job ids cannot create oversized alert details before webhook delivery validation. The previous sprint capped stale-requeue previews at 50 job ids, but preview count alone did not bound the generated string size.

Stale-requeue alerts now route their generated detail through the shared alert-detail safety path. That redacts diagnostic text and caps the resulting detail at 16 KiB with the standard alert truncation marker before returning the `ExternalAlert`.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving a single oversized stale job id could produce an alert detail larger than the alert body text limit.
- Focused verification: `python3 -m pytest tests/test_alert_delivery.py -q -k "stale_requeue_alert_bounds_generated_detail_after_redaction"` passed with 1 test.
- Broader alert verification: `python3 -m pytest tests/test_alert_delivery.py -q` passed with 51 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 478 documentation tests passed, and 2183 total tests passed at 93.93% coverage.
