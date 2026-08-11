# Sprint 750 Change Log - Runtime config numeric cause boundary

## Scope

Hardened runtime configuration numeric parser diagnostics so integer and floating-point setting failures do not retain unsafe parser exceptions as public `RuntimeConfigError` causes.

## Tests First

- Added 2 failing-first runtime config numeric cause assertions:
  - `tests/test_runtime.py::test_runtime_config_int_value_wraps_unstringifiable_parser_errors`
  - `tests/test_runtime.py::test_runtime_config_float_value_wraps_unstringifiable_parser_errors`
- Initial failures proved the public `RuntimeConfigError` retained the original hostile numeric parser cause.
- The hostile parser exception included `client-secret-value` to prove cause retention could preserve sensitive exception text even though the diagnostic message was redacted.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_750_documents_runtime_config_numeric_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original numeric parser causes in `_int_value()` and `_float_value()`.
- Preserved existing safe exception diagnostics from `exception_diagnostic_message()`.
- Documented the runtime config numeric cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "runtime_config_int_value_wraps_unstringifiable_parser_errors or runtime_config_float_value_wraps_unstringifiable_parser_errors"` failed first, then passed.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_750` failed first, then passed.
- `ruff check src tests` passed.
- `mypy src tests` passed.
- `python3 -m pytest tests/test_runtime.py -q -k "runtime_config"` passed: 2 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed: 3081 passed, 93.33% coverage.
