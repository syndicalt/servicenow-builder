# Sprint 934 Change Log - Admin artifact payload key string-subclass boundary

## Scope
- Hardened `_admin_payload_key()` for admin artifact payload diagnostic keys.
- Hardened the admin artifact traversal sensitive-key branch to classify only exact string keys.
- Added a failing-first regression for hostile string-subclass artifact payload keys.
- Documented the exact-string key boundary for admin artifact diagnostic payloads.

## Production Hardening
- Admin artifact payload keys are sanitized only when they are exact strings.
- String-subclass keys render as `[non-string key]` instead of entering work-note redaction or sensitive-key classification.
- String-subclass keys do not reach sensitive-key classification before value traversal.
- The key projector does not call `str()`, `repr()`, or string subclass methods on malformed payload keys before artifact API serialization or HTML rendering.

## Tests
- Added `test_artifact_payload_projection_rejects_string_subclass_payload_keys`.
- Added `test_artifact_payload_projection_skips_sensitive_check_for_key_subclasses`.
- Added `test_sprint_934_documents_admin_artifact_payload_key_string_subclass_boundary`.
- Captured 2 failing-first admin artifact payload key string-subclass assertions.
- Focused verification: `3 passed`.
- Scoped verification: `tests/test_runtime.py` passed with 423 tests and `tests/test_project_docs.py` passed with 1007 tests.
- Static verification: `python3 -m ruff check src tests` and `python3 -m mypy src tests` passed.
- Full coverage verification: `3579 passed`; total coverage remained 93.53%.
