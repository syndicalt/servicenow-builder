# Sprint 425 Change Log

## Shared safe exception diagnostics

Re-engineered the unstringifiable-exception hardening from Sprints 421 through 424 into a shared diagnostic utility. Prior behavior had separate local helper implementations in runtime handler redaction, the core fulfillment worker, and runtime-worker logging, while CLI error rendering still called `str(exc)` directly.

Added `jedi_devproject.exception_diagnostics.exception_diagnostic_message()` as the single implementation for safe exception stringification. It preserves normal exception strings. If stringification fails, it emits `<subject> raised unstringifiable <ExceptionType>` only when the subject and exception type label are safe, otherwise it emits `<subject> raised unstringifiable exception` or falls back to the neutral `error` subject.

Refactored runtime handler redaction, core worker failure persistence, runtime-worker maintenance and alert logging, and CLI error rendering to use the shared helper before their existing redaction layers. This removes duplicated safety logic and extends the same protection to operator CLI output.

## Verification

- Added shared exception diagnostic tests for normal errors, unstringifiable errors, unsafe type labels, and unsafe fallback subjects.
- Added a CLI rendering test proving unstringifiable CLI exceptions produce a bounded diagnostic without leaking the secondary stringification error.
- `python3 -m pytest tests/test_exception_diagnostics.py tests/test_cli_io.py tests/test_runtime_redaction.py tests/test_fulfillment_worker.py tests/test_runtime_worker_retention.py -q`: 76 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 193 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 499 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2268 total tests passed at 93.97% coverage.
