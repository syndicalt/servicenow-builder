# Sprint 314 Change Log - Dormant Public Web Config Guard

## Summary

- Runtime settings loading now validates configured public-web allowlist and documentation URL values even when `JEDI_PUBLIC_WEB_ACCESS` is disabled.
- Disabled public-web mode still does not require `JEDI_PUBLIC_WEB_ALLOWED_DOMAINS` or `JEDI_PUBLIC_WEB_DOC_URLS`.
- If dormant public-web values are present, allowed domains must be non-local hostnames without padding, whitespace, or control characters.
- If dormant public-web documentation URLs are present, they must be HTTPS, credential-free, fragment-free, whitespace/control-character-free, encoded-control-free, sensitive-query-free, and host-matched to the allowlist.
- Malformed dormant public-web diagnostics name only `JEDI_PUBLIC_WEB_ALLOWED_DOMAINS` or `JEDI_PUBLIC_WEB_DOC_URLS` and do not echo URL credentials or sensitive query values.
- Added failing regressions proving local allowlist entries, credentialed dormant documentation URLs, sensitive dormant documentation URL queries, and dormant documentation URLs outside the allowlist were previously accepted when public web access was disabled.
- Existing enabled worker-mode public-web validation remains intact.
- Documented the dormant public-web configuration guard in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_load_runtime_settings_rejects_dormant_unsafe_public_web_config -q` - 3 tests failed before implementation because dormant unsafe public-web values were accepted while public web access was disabled.
- `python3 -m pytest tests/test_runtime.py::test_load_runtime_settings_rejects_dormant_unsafe_public_web_config tests/test_runtime.py::test_load_runtime_settings_reads_public_web_worker_controls tests/test_runtime.py::test_load_runtime_settings_rejects_malformed_public_web_worker_allowlist tests/test_runtime.py::test_load_runtime_settings_rejects_public_web_worker_docs_outside_allowlist tests/test_runtime.py::test_load_runtime_settings_rejects_public_web_worker_doc_url_secrets_without_echo tests/test_runtime.py::test_load_runtime_settings_rejects_non_positive_public_web_worker_limits -q` - 8 passed after implementation.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py` - no issues found in 2 source files.
- `python3 -m pytest tests/test_runtime.py::test_load_runtime_settings_rejects_dormant_unsafe_public_web_config tests/test_project_docs.py::test_sprint_three_hundred_fourteen_documents_dormant_public_web_config_guard -q` - 4 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 388 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1877 passed, total coverage 93.91%.
