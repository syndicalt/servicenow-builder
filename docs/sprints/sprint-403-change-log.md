# Sprint 403 Change Log

## Timezone-aware generated alert construction

Hardened generated operational alert constructors so ambiguous local-time datetimes are rejected before an `ExternalAlert` is returned. Delivery-time validation already rejected naive `created_at` values, but generated alerts could still be built with naive source timestamps and only fail later during webhook delivery.

Worker-failure alerts now require timezone-aware `created_at` values, rejected-job alerts require timezone-aware job `updated_at` values, and stale-requeue alerts require timezone-aware `requeued_at` values. This keeps generated alert ids, incident timelines, and replay metadata from being derived from ambiguous local server time.

## Tests

- Failing-first coverage: 3 tests failed before implementation, proving worker-failure, rejected-job, and stale-requeue alert constructors accepted naive source timestamps.
- Focused verification: `python3 -m pytest tests/test_alert_delivery.py -q -k "rejects_naive_created_at or rejects_naive_updated_at or rejects_naive_requeued_at"` passed with 4 tests.
- Broader alert verification: `python3 -m pytest tests/test_alert_delivery.py -q` passed with 50 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 477 documentation tests passed, and 2181 total tests passed at 93.93% coverage.
