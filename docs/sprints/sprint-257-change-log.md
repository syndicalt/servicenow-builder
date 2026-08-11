# Sprint 257 Change Log - Public Web CSV Padding Guard

## Summary

- Public web CSV padding guarding prevents comma-separated allowlist domains and documentation URLs from being silently normalized before production validation.
- Added an env-level regression proving padded `JEDI_PUBLIC_WEB_ALLOWED_DOMAINS` and `JEDI_PUBLIC_WEB_DOC_URLS` entries are rejected after settings load.
- Updated CSV parsing to preserve non-empty entries verbatim so validation can enforce the documented no-padding contract.
- Verified normal public-web worker controls and existing unsafe public-web validation paths still pass.
- Documented that comma-separated public-web entries preserve interior padding for validation.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_validate_runtime_settings_rejects_padded_public_web_csv_values_from_env tests/test_runtime.py::test_load_runtime_settings_reads_public_web_worker_controls tests/test_runtime.py::test_validate_runtime_settings_rejects_malformed_public_web_allowed_domains tests/test_runtime.py::test_validate_runtime_settings_rejects_public_web_docs_outside_allowlist tests/test_runtime.py::test_validate_runtime_settings_rejects_unsafe_public_web_doc_url_content -q` - 8 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py` - all checks passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success with 174 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 331 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1645 passed with 93.97% total coverage.
