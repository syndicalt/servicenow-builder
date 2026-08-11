# Sprint 401 Change Log

## Bounded stale requeue alert job-id previews

Hardened stale-job recovery alert construction so large recovery batches cannot create unbounded alert detail text before webhook delivery validation runs. The prior `stale_requeue_alert()` implementation joined every requeued job id into the alert detail string.

Stale requeue alerts now preserve the total requeued count, preview at most 50 job ids, and append an omitted-count marker for the rest. This bounds alert construction before JSON serialization, transport, and the final webhook body-size gate.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving the stale requeue alert detail included job ids beyond the 50-item preview boundary.
- Focused verification: `python3 -m pytest tests/test_alert_delivery.py -q -k "stale_requeue_alert"` passed with 2 tests.
- Broader alert verification: `python3 -m pytest tests/test_alert_delivery.py -q` passed with 45 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 475 documentation tests passed, and 2174 total tests passed at 93.93% coverage.
