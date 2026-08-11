# Sprint 304 Change Log - Runtime Boolean Settings Load Guard

## Summary

- Runtime boolean settings loading now rejects padded or control-character env values before boolean normalization.
- `JEDI_BUILD_CLAIM_APPLY`, `JEDI_STRICT_TRANSPORT_SECURITY_ENABLED`, `JEDI_ALERT_WEBHOOK_ENABLED`, `JEDI_UPDATE_SET_APPLY`, and `JEDI_CLASSIFIER_GATE` must use accepted boolean literals without padding or control characters.
- Empty values still use each setting's default, but whitespace-only or padded values are rejected as ambiguous operator input.
- Malformed runtime boolean diagnostics name only the setting and do not echo padded or control-character fragments.
- Existing accepted boolean literals and malformed-boolean validation remain intact.
- Added failing regressions proving padded runtime boolean env values were previously accepted or downgraded to generic parser errors during settings loading.
- Documented the stricter runtime boolean settings-load boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "runtime_boolean_values or defaults_classifier_gate_enabled or reads_strict_transport_security_config or reads_alert_webhook_config"` - 5 tests failed before implementation because padded runtime boolean values were accepted or produced generic diagnostics.
- `python3 -m pytest tests/test_runtime.py -q -k "runtime_boolean_values or defaults_classifier_gate_enabled or reads_strict_transport_security_config or reads_alert_webhook_config"` - 13 passed after implementation.
- `python3 -m pytest tests/test_runtime.py -q` - 240 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_four_documents_runtime_boolean_load_guard -q` - 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 378 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1823 passed, total coverage 93.90%.
