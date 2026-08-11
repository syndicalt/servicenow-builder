# Sprint 319 Change Log - Public Web Validation Diagnostic Redaction

## Summary

- Direct `RuntimeSettings` production validation no longer echoes raw invalid public-web allowlist entries or documentation URLs.
- Public documentation URL diagnostics now name `JEDI_PUBLIC_WEB_DOC_URLS` and describe the violated rule without returning URL userinfo, paths, query keys, or query values.
- Public documentation allowlist diagnostics now name `JEDI_PUBLIC_WEB_ALLOWED_DOMAINS` without returning configured host fragments.
- Existing public-web credential, sensitive-query, fragment, encoded-control, private-host, and allowlist-match validation remains intact.
- Documented the direct-settings diagnostic boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_validate_runtime_settings_redacts_public_web_doc_url_credentials tests/test_runtime.py::test_validate_runtime_settings_redacts_public_web_doc_url_query_secrets -q` - 2 tests failed before implementation because direct validation echoed raw invalid URLs.
- `python3 -m pytest tests/test_runtime.py::test_validate_runtime_settings_rejects_public_web_doc_url_credentials tests/test_runtime.py::test_validate_runtime_settings_redacts_public_web_doc_url_credentials tests/test_runtime.py::test_validate_runtime_settings_redacts_public_web_doc_url_query_secrets tests/test_runtime.py::test_validate_runtime_settings_rejects_unsafe_public_web_doc_url_content tests/test_runtime.py::test_validate_runtime_settings_rejects_private_public_web_doc_hosts tests/test_runtime.py::test_validate_runtime_settings_rejects_malformed_public_web_allowed_domains -q` - 15 passed after implementation.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py` - no issues found in 2 source files.
- `python3 -m pytest tests/test_runtime.py::test_validate_runtime_settings_rejects_public_web_doc_url_credentials tests/test_runtime.py::test_validate_runtime_settings_redacts_public_web_doc_url_credentials tests/test_runtime.py::test_validate_runtime_settings_redacts_public_web_doc_url_query_secrets tests/test_runtime.py::test_validate_runtime_settings_rejects_unsafe_public_web_doc_url_content tests/test_runtime.py::test_validate_runtime_settings_rejects_private_public_web_doc_hosts tests/test_runtime.py::test_validate_runtime_settings_rejects_malformed_public_web_allowed_domains tests/test_project_docs.py::test_sprint_three_hundred_nineteen_documents_public_web_validation_redaction -q` - 16 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 393 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 181 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1913 passed, total coverage 93.87%.
