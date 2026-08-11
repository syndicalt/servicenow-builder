# Sprint 755 Change Log - Runtime handler redaction cause boundary

## Scope

Hardened runtime handler redaction so handler failures wrapped by `_redacting_handler()` do not retain unsafe handler exceptions as public `RuntimeError` causes.

## Tests First

- Added 1 failing-first runtime handler redaction cause assertion:
  `tests/test_runtime_redaction.py::test_redacting_handler_handles_unstringifiable_exceptions_without_leaking_secret`
- Initial failure proved the public redacted `RuntimeError` retained the original `_UnstringifiableRuntimeError` as `__cause__`.
- The hostile exception included `client-secret-value` to prove cause retention could preserve sensitive exception text even though the visible diagnostic was redacted.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_755_documents_runtime_handler_redaction_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original handler exception causes in `_redacting_handler()`.
- Preserved existing redacted diagnostics, including:
  - `handler raised unstringifiable _UnstringifiableRuntimeError`
- Documented the runtime handler redaction cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime_redaction.py -q -k redacting_handler_handles_unstringifiable_exceptions_without_leaking_secret` failed first, then passed.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_755` failed first, then passed.
- `ruff check src tests` passed.
- `mypy src tests` passed.
- `python3 -m pytest tests/test_runtime_redaction.py -q` passed: 21 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed: 3093 passed, 93.38% coverage.
