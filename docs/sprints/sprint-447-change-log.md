# Sprint 447 Change Log

## Admin artifact non-string payload key sanitization

Hardened admin artifact payload projections so dictionary keys that are not strings never flow through Python `str(key)` before rendering JSON or HTML diagnostics. Prior behavior sanitized stringified keys, which redacted some secret-like text but could still expose tuple structure, object memory representations, or other implementation details in operator-facing artifact views.

Admin artifact payload key rendering now preserves the existing string-key behavior and treats all non-string keys as a deterministic `[non-string key]` diagnostic label. Duplicate labels continue to receive collision-safe suffixes such as `[non-string key] [duplicate 2]`, so diagnostic content remains visible without reflecting untrusted key structure.

## Verification

- Added 1 failing-first admin artifact projection test covering tuple and object keys.
- `python3 -m pytest tests/test_runtime.py -q -k "non_string_payload_keys"`: failed before implementation because tuple key contents and object representations reached the rendered payload.
- `python3 -m pytest tests/test_runtime.py -q -k "payload_key or payload_projection_preserves_user_truncation_marker_key"`: 7 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 194 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 521 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2332 total tests passed at 93.93% coverage.
