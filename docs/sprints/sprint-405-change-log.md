# Sprint 405 Change Log

## Constructor-safe generated alert metadata

Hardened generated operational alert constructors so unsafe metadata is rejected before an `ExternalAlert` is returned. Delivery already rejected unsafe webhook headers, but generated alert constructors could still return queueable alert objects with newline-bearing ids, padded story numbers, unsafe correlation ids, or oversized metadata that would only fail later at send time.

Worker-failure alerts now validate the source job id and story number before deriving the alert id. Rejected-job alerts validate the source job id, event id, story number, and correlation id before deriving the alert id. Stale-requeue alerts validate their generated single-job or multi-job metadata before returning the alert. Every generated alert is also passed through the shared timestamp, body text, routing, and webhook-header metadata validators before construction completes.

## Tests

- Failing-first coverage: 7 tests failed before implementation, proving worker-failure, rejected-job, and stale-requeue constructors accepted unsafe generated alert metadata.
- Focused verification: `python3 -m pytest tests/test_alert_delivery.py -q -k "unsafe_generated_metadata or unsafe_single_job_metadata or stale_requeue_alert_bounds_generated_detail_after_redaction"` passed with 8 tests.
- Broader alert verification: `python3 -m pytest tests/test_alert_delivery.py -q` passed with 58 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 479 documentation tests passed, and 2191 total tests passed at 93.93% coverage.
