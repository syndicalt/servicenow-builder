# Sprint 298 Change Log - Lifecycle Webhook Secret Settings Load Guard

## Summary

- Runtime settings loading now rejects malformed lifecycle webhook secret configuration.
- `JEDI_LIFECYCLE_WEBHOOK_SECRET` must be unpadded and free of control characters before runtime settings are returned.
- Blank or absent lifecycle webhook secret values still behave as unconfigured, preserving the fail-closed webhook auth path when an authenticated mode requires a secret.
- Malformed lifecycle webhook secret diagnostics name only the setting and do not echo secret fragments.
- Existing production validation still requires `JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE=hmac_sha256` and a minimum 32-character HMAC secret.
- Added failing regressions proving padded and control-character lifecycle webhook secret env values were previously accepted during settings loading.
- Documented the lifecycle webhook secret settings-load boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "lifecycle_webhook_secret and load_runtime_settings"` - 3 tests failed before implementation because malformed lifecycle webhook secret values were accepted during settings loading.
- `python3 -m pytest tests/test_runtime.py -q -k "lifecycle_webhook_secret and load_runtime_settings"` - 3 passed after implementation.
- `python3 -m pytest tests/test_runtime.py -q -k "lifecycle_webhook"` - 9 passed.
- `python3 -m pytest tests/test_lifecycle_api.py -q -k "webhook_auth or shared_secret or hmac"` - 10 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_two_hundred_ninety_eight_documents_lifecycle_secret_load_guard -q` - 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_lifecycle_api.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_lifecycle_api.py tests/test_project_docs.py` - no issues found in 4 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 372 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1797 passed, total coverage 93.90%.
