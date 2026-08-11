# Sprint 402 Change Log

## Bounded generated alert diagnostics

Hardened worker-failure and rejected-job alert construction so large upstream diagnostic strings cannot create oversized alert details before webhook delivery validation. The prior constructors redacted diagnostic text, but preserved the full redacted string in `ExternalAlert.detail`.

Worker-failure and rejected-job alerts now redact detail text and cap it at 16 KiB with the standard alert truncation marker during alert construction. This keeps generated alerts deliverable while preserving the existing webhook body-size gate as the final outbound payload control.

## Tests

- Failing-first coverage: 2 tests failed before implementation, proving worker failure and rejected-job alert constructors produced details larger than the alert body text limit after redaction.
- Focused verification: `python3 -m pytest tests/test_alert_delivery.py -q -k "bounds_generated_detail or worker_failure_alert or rejected_job_alert"` passed with 4 tests.
- Broader alert verification: `python3 -m pytest tests/test_alert_delivery.py -q` passed with 47 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 476 documentation tests passed, and 2177 total tests passed at 93.93% coverage.
