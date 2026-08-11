# Sprint 421 Change Log

## Unstringifiable handler exception redaction

Hardened the runtime fulfillment redaction wrapper against malformed exception objects. Prior behavior called `str(exc)` inside `_redacting_handler()`, so an exception whose `__str__` method raised could bypass the intended redacted `RuntimeError` path and surface the secondary stringification failure instead.

The wrapper now formats handler exceptions through a safe helper. Normal exception messages are still redacted as before. If stringification itself fails, the wrapper reports `handler raised unstringifiable <ExceptionType>` and then redacts that fallback before persistence, notifier delivery, work-note writeback, or runtime return paths can consume it.

This keeps fulfillment failure handling deterministic even when provider SDKs, mocks, or future integration adapters raise malformed exception objects.

## Verification

- Added 1 failing-first test proving a handler exception with a secret-bearing failing `__str__` no longer leaks the secondary error or bypasses the runtime wrapper.
- `python3 -m pytest tests/test_runtime_redaction.py -q -k "unstringifiable"`: failed before implementation because `ValueError: client-secret-value` escaped.
- `python3 -m pytest tests/test_runtime_redaction.py -q`: 20 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 191 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 495 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2252 total tests passed at 93.97% coverage.
