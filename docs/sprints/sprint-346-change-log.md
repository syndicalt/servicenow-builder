# Sprint 346 Change Log

Scope: Production hardening - inbound admin Authorization credential normalization.

## Summary

- Admin Bearer token validation no longer strips inbound credential material before comparison.
- Padded, whitespace-bearing, or control-character-bearing Bearer token values are rejected before `secrets.compare_digest()` is called, preserving the existing `admin bearer token rejected` response.
- Development Basic-auth credential decoding no longer strips the encoded credential section.
- Padded, whitespace-bearing, or control-character-bearing Basic credential sections are rejected before base64 decoding, preserving the existing unauthorized Basic-auth response path.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_basic_auth_decoder_rejects_padded_payload_before_decode tests/test_runtime.py::test_admin_bearer_token_rejects_padded_token_before_compare -q` - 2 tests failed before implementation because inbound Authorization credential material was stripped before decode or comparison.
- `python3 -m pytest tests/test_runtime.py::test_basic_auth_decoder_rejects_oversized_payload_before_decode tests/test_runtime.py::test_basic_auth_decoder_rejects_padded_payload_before_decode tests/test_runtime.py::test_admin_bearer_token_rejects_oversized_token_before_compare tests/test_runtime.py::test_admin_bearer_token_rejects_padded_token_before_compare -q` - 4 passed after implementation.
- `python3 -m pytest tests/test_runtime.py -q -k "admin_bearer or basic_auth or admin_console_requires or artifact_read"` - 17 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_forty_six_documents_inbound_admin_auth_no_trim tests/test_runtime.py -q -k "admin_bearer or basic_auth or admin_console_requires or artifact_read"` - 17 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 187 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 420 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 2005 passed, total coverage 94.05%.
