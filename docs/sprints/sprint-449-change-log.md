# Sprint 449 Change Log

## Admin artifact unstringifiable payload key hardening

Hardened admin artifact payload projection so non-string dictionary keys are not stringified during sensitive-key classification. Prior behavior rendered non-string keys as `[non-string key]`, but the adjacent `is_sensitive_key(key)` check still called `str(key)`. A malformed key object with a hostile or broken `__str__` method could therefore crash admin artifact diagnostics and raise secret-looking exception text before the safe key renderer returned a bounded view.

Admin artifact dictionary traversal now performs sensitive-key classification only for string keys. Non-string keys continue to render as `[non-string key]`, duplicate labels continue to receive deterministic suffixes, and nested values are still recursively redacted and bounded.

## Verification

- Added 1 failing-first admin artifact projection test covering an unstringifiable non-string payload key.
- `python3 -m pytest tests/test_runtime.py -q -k "unstringifiable_payload_keys"`: failed before implementation because `is_sensitive_key(key)` called the key object's `__str__`.
- `python3 -m pytest tests/test_runtime.py -q -k "unstringifiable_payload_keys or non_string_payload_keys or non_json_scalar_values or payload_key or payload_projection_preserves_user_truncation_marker_key"`: 9 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 194 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 523 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2336 total tests passed at 93.89% coverage.
