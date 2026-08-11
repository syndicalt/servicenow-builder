# Sprint 450 Change Log

## Admin artifact circular payload traversal hardening

Hardened admin artifact payload projection so cyclic in-memory containers cannot recurse until failure. JSONB-backed production artifacts should not contain cycles, but admin diagnostics also run against alternate store implementations, tests, and operational recovery paths. Prior behavior recursively walked dictionaries, lists, and tuples without tracking container identity, so a cyclic payload raised `RecursionError` instead of returning a bounded diagnostic view.

Admin artifact payload traversal now tracks active container identities while projecting dictionaries, lists, and tuples. Repeated active containers render as `[circular reference]`, mark the diagnostic as truncated, and preserve the existing redaction, collection bounds, non-string key handling, non-JSON scalar handling, and duplicate key behavior.

## Verification

- Added 1 failing-first admin artifact projection test covering a self-referential dictionary payload.
- `python3 -m pytest tests/test_runtime.py -q -k "circular_references"`: failed before implementation with `RecursionError`.
- `python3 -m pytest tests/test_runtime.py -q -k "circular_references or unstringifiable_payload_keys or non_string_payload_keys or non_json_scalar_values or payload_key or payload_projection_preserves_user_truncation_marker_key"`: 10 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 194 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 524 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2338 total tests passed at 93.84% coverage.
