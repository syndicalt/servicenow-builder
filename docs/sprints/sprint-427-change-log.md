# Sprint 427 Change Log

## Runtime config numeric parser safe exceptions

Hardened runtime config numeric setting wrappers so malformed parser exceptions cannot replace controlled startup diagnostics. Prior behavior caught numeric parser `ValueError`s from integer and decimal settings, then called `str(exc)` while wrapping numeric parser errors into `RuntimeConfigError`.

The runtime config loader now formats numeric parser failures through `exception_diagnostic_message(..., fallback_subject="runtime config")`. Normal parser diagnostics are preserved as before. If a parser dependency or future validator raises an exception that cannot be stringified, settings loading fails with `runtime config raised unstringifiable <ExceptionType>` or the generic `runtime config raised unstringifiable exception` instead of surfacing a secondary stringification failure.

This keeps startup, worker, and API configuration failures on the same redaction-safe diagnostic path used by runtime handlers, fulfillment workers, lifecycle alert logging, and CLI rendering.

## Verification

- Added 2 failing-first runtime config tests covering unstringifiable integer and decimal parser failures.
- `python3 -m pytest tests/test_runtime.py -q -k "runtime_config_int_value_wraps_unstringifiable_parser_errors or runtime_config_float_value_wraps_unstringifiable_parser_errors"`: failed before implementation because `ValueError: client-secret-value` escaped during numeric parser error wrapping.
- `python3 -m pytest tests/test_runtime.py -q -k "runtime_config_int_value_wraps_unstringifiable_parser_errors or runtime_config_float_value_wraps_unstringifiable_parser_errors"`: 2 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 193 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 501 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2273 total tests passed at 93.97% coverage.
