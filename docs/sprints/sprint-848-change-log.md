# Sprint 848 Change Log - Sensitive key exact-string guard

## Intent

Harden shared sensitive-key normalization so redaction and query-key checks do
not invoke arbitrary object stringification or string-subclass methods while
classifying credential-like field names.

## Changes

- Added 1 failing-first sensitive key exact-string assertion: `tests/test_sensitive_keys.py::test_sensitive_key_classifier_rejects_non_exact_strings`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_848_documents_sensitive_key_exact_string_guard`.
- `normalize_sensitive_key()` now returns an empty comparison key for non-exact strings such as `StringifiableSensitiveKey`.
- `is_sensitive_key()` now refuses string-subclass keys such as `SensitiveKeySubclass` before sensitive-key matching.

## Verification

- `pytest tests/test_sensitive_keys.py::test_sensitive_key_classifier_rejects_non_exact_strings tests/test_project_docs.py::test_sprint_848_documents_sensitive_key_exact_string_guard -q` - 2 passed.
- `pytest tests/test_project_docs.py -q` - 921 passed.
- `pytest tests/test_sensitive_keys.py tests/test_runtime_redaction.py tests/test_alert_delivery.py tests/test_url_query_safety.py tests/test_alert_webhook_url.py tests/test_servicenow.py tests/test_runtime.py tests/test_writeback.py -q` - 874 passed.
- `pytest tests/test_sensitive_keys.py tests/test_runtime_redaction.py tests/test_alert_delivery.py tests/test_url_query_safety.py tests/test_alert_webhook_url.py tests/test_servicenow.py tests/test_runtime.py tests/test_writeback.py tests/test_project_docs.py -q` - 1795 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3387 passed, 93.44% coverage.
