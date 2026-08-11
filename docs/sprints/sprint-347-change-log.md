# Sprint 347 Change Log

Scope: Production hardening - lifecycle webhook inbound auth header normalization.

## Summary

- HMAC lifecycle webhook timestamps now reject padded, whitespace-bearing, control-character-bearing, empty, or non-ASCII-digit header values before integer parsing.
- Padded HMAC timestamp headers can no longer be signed and accepted as valid lifecycle events.
- HMAC signature header values are rejected before `hmac.compare_digest()` when padded, whitespace-bearing, or control-character-bearing.
- Interim shared-secret webhook header values are rejected before `hmac.compare_digest()` when padded, whitespace-bearing, or control-character-bearing.

## Verification

- `python3 -m pytest tests/test_lifecycle_api.py -q -k "padded_timestamp or padded_signature or padded_secret"` - 3 tests failed before implementation because padded lifecycle webhook credential material was accepted or compared.
- `python3 -m pytest tests/test_lifecycle_api.py -q -k "padded_timestamp or padded_signature or padded_secret or accepts_valid_signature or accepts_valid_servicenow_base64_signature or accepts_valid_secret"` - 6 passed after implementation.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_forty_seven_documents_lifecycle_webhook_auth_no_trim -q` - 1 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 187 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 421 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 2009 passed, total coverage 94.04%.
