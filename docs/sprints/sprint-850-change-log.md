# Sprint 850 Change Log - Diagnostic redaction exact-string guard

## Intent

Harden shared diagnostic redaction so malformed direct callers cannot pass
booleans, numbers, bytes, or string subclasses into URL parsing, regex
replacement, query-key decoding, or assignment redaction.

## Changes

- Added 1 failing-first diagnostic redaction exact-string assertion: `tests/test_runtime_redaction.py::test_redact_diagnostic_text_rejects_non_exact_strings`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_850_documents_diagnostic_redaction_exact_string_guard`.
- `_redact_diagnostic_text()` now accepts only exact strings or `None`.
- Non-exact inputs such as `_HostileDiagnosticText` now render as `[non-string diagnostic text]`.

## Verification

- `pytest tests/test_runtime_redaction.py::test_redact_diagnostic_text_rejects_non_exact_strings tests/test_project_docs.py::test_sprint_850_documents_diagnostic_redaction_exact_string_guard -q` - 5 passed.
- `pytest tests/test_runtime_redaction.py tests/test_alert_delivery.py tests/test_work_note_safety.py tests/test_servicenow.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_providers.py tests/test_cli_io.py tests/test_fulfillment_worker.py tests/test_runtime.py -q` - 994 passed.
- `pytest tests/test_project_docs.py -q` - 923 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3395 passed, 93.44% coverage.
