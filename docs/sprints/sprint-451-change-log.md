# Sprint 451 Change Log

## Admin artifact payload depth-bound hardening

Hardened admin artifact payload projection so deeply nested but acyclic payloads cannot force unbounded recursive diagnostic work. Prior behavior bounded collection width and handled cycles, but it still traversed arbitrary nesting depth. A malformed artifact payload could therefore consume excessive stack and CPU before the admin JSON or HTML diagnostic view was rendered.

Admin artifact payload traversal now caps nested dictionary, list, and tuple projection at a fixed diagnostic depth. Containers beyond the cap render as `[max depth exceeded]`, mark the diagnostic as truncated, and preserve the existing key sanitization, sensitive-key redaction, cycle handling, collection-width bounds, and non-JSON scalar handling.

## Verification

- Added 1 failing-first admin artifact projection test covering an excessively deep acyclic dictionary payload.
- `python3 -m pytest tests/test_runtime.py -q -k "excessive_depth"`: failed before implementation because the payload rendered all 40 levels and did not mark truncation.
- `python3 -m pytest tests/test_runtime.py -q -k "excessive_depth or circular_references or unstringifiable_payload_keys or non_string_payload_keys or non_json_scalar_values or payload_key or payload_projection_preserves_user_truncation_marker_key"`: 11 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 194 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 525 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2340 total tests passed at 93.84% coverage.
