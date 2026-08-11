# Sprint 426 Change Log

## Lifecycle rejected-job alert logging-safe exceptions

Hardened lifecycle webhook rejected-job alert logging so best-effort alert delivery cannot disrupt webhook acceptance when the alert failure exception cannot be stringified. Prior behavior caught rejected-job alert notifier failures but then called `str(exc)` while preparing the warning log message.

The lifecycle API now formats rejected-job notifier exceptions through `exception_diagnostic_message(..., fallback_subject="lifecycle")` before lifecycle diagnostic redaction. Normal notifier error messages are preserved and redacted as before. If stringification fails, the lifecycle path logs `lifecycle raised unstringifiable <ExceptionType>` or the generic `lifecycle raised unstringifiable exception`.

This keeps story rejection lifecycle events best-effort after PostgreSQL records the rejected terminal job: alert logging failures cannot turn an accepted lifecycle webhook into an API exception.

## Verification

- Added 1 failing-first lifecycle API test covering an unstringifiable rejected-job alert notifier exception.
- `python3 -m pytest tests/test_lifecycle_api.py -q -k "unstringifiable"`: failed before implementation because `ValueError: client-secret-value` escaped during rejected-job alert logging.
- `python3 -m pytest tests/test_lifecycle_api.py -q`: 41 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 193 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 500 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2270 total tests passed at 93.97% coverage.
