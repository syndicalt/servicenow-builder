# Sprint 423 Change Log

## Core worker unstringifiable exception handling

Hardened `process_one_fulfillment_job()` so the core worker failure boundary does not depend on handler or failure-notifier exceptions being stringifiable. Prior behavior called `str(exc)` directly when a handler failed and `str(notifier_exc)` directly when failure writeback notification failed. A malformed exception could therefore bypass failed-job persistence or hide the original worker failure behind a secondary stringification exception.

The worker now formats exceptions through a safe helper before diagnostic redaction. Normal exception messages are preserved and redacted as before. If stringification fails, the worker records `worker raised unstringifiable <ExceptionType>` when the type label is safe, or `worker raised unstringifiable exception` when the label is unsafe, non-ASCII, oversized, or mutated.

This keeps PostgreSQL `last_error` persistence, failure notifier delivery, and `FulfillmentWorkerResult` returns deterministic even when provider SDKs or future integrations raise malformed exception objects.

## Verification

- Added 2 failing-first tests covering unstringifiable handler exceptions and unstringifiable failure-notifier exceptions.
- `python3 -m pytest tests/test_fulfillment_worker.py -q -k "stringified"`: failed before implementation because `ValueError: client-secret-value` escaped both paths.
- `python3 -m pytest tests/test_fulfillment_worker.py -q`: 12 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 191 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 497 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2257 total tests passed at 93.95% coverage.
