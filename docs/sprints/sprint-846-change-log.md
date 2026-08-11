# Sprint 846 Change Log - URL query helper exact-string guard

## Intent

Harden shared URL query and content safety helpers so direct callers cannot pass
non-string values, bytes, or string subclasses into parsing, decoding,
sensitive-key matching, or whitespace/control-character checks.

## Changes

- Added 1 failing-first URL query helper exact-string assertion: `tests/test_url_query_safety.py::test_url_query_helpers_reject_non_exact_strings`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_846_documents_url_query_exact_string_guard`.
- `has_whitespace_or_control_character()` and `has_encoded_whitespace_or_control_character()` now reject non-exact strings with `value must be an exact string`.
- `sensitive_query_keys()`, `query_pairs()`, and `query_pair_candidates()` now reject non-exact strings with `query must be an exact string`.

## Verification

- `pytest tests/test_url_query_safety.py::test_url_query_helpers_reject_non_exact_strings tests/test_project_docs.py::test_sprint_846_documents_url_query_exact_string_guard -q` - 6 passed.
- `pytest tests/test_url_query_safety.py tests/test_alert_webhook_url.py tests/test_provider_settings_safety.py tests/test_provider_contract.py tests/test_config.py tests/test_runtime.py -q` - 513 passed.
- `pytest tests/test_project_docs.py -q` - 919 passed.
- `pytest tests/test_url_query_safety.py tests/test_alert_webhook_url.py tests/test_provider_settings_safety.py tests/test_provider_contract.py tests/test_config.py tests/test_runtime.py tests/test_rag.py tests/test_servicenow.py tests/test_numeric_settings.py tests/test_runtime_worker_retention.py -q` - 922 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3378 passed, 93.44% coverage.
