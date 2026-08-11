# Sprint 348 Change Log

Scope: Production hardening - decoded Basic-auth credential normalization.

## Summary

- Development Basic-auth decoding now rejects malformed decoded credential parts before configured credential comparison.
- Decoded usernames and passwords with leading whitespace, trailing whitespace, or control characters return the existing unauthorized admin console response.
- Padded decoded Basic-auth credential parts no longer reach `secrets.compare_digest()`.
- Existing encoded Basic-auth payload bounds and no-trim validation remain unchanged.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_admin_basic_auth_rejects_padded_decoded_credentials_before_compare -q` - 4 tests failed before implementation because decoded Basic-auth credential parts reached comparison.
- `python3 -m pytest tests/test_runtime.py -q -k "admin_basic_auth_rejects_padded_decoded_credentials or basic_auth_decoder or admin_console_requires_basic_auth or admin_console_rejects_wrong_basic_auth or admin_console_renders_jobs_events"` - 9 passed after implementation.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_forty_eight_documents_decoded_basic_auth_no_trim -q` - 1 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 187 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 422 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 2014 passed, total coverage 94.04%.
