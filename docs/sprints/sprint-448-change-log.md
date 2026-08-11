# Sprint 448 Change Log

## Admin artifact non-JSON scalar value sanitization

Hardened admin artifact payload projections so unsupported scalar values cannot crash JSON or HTML diagnostic rendering. Prior behavior recursively redacted strings and collections but returned arbitrary scalar objects unchanged. A corrupted artifact payload, alternate store implementation, or test transport could therefore pass bytes or Python objects into `json.dumps(...)` and produce an admin API failure instead of a bounded diagnostic view.

Admin artifact payload projection now preserves ordinary JSON primitives, redacts and bounds strings, maps non-finite floats to `[non-json value]`, and maps unsupported scalar types such as bytes or Python objects to `[non-json value]` without reflecting raw bytes, object representations, or custom type details.

## Verification

- Added 1 failing-first admin artifact view test covering bytes and object scalar values.
- `python3 -m pytest tests/test_runtime.py -q -k "non_json_scalar_values"`: failed before implementation because bytes reached `json.dumps(...)` and raised `TypeError`.
- `python3 -m pytest tests/test_runtime.py -q -k "non_json_scalar_values or payload_key or payload_projection_preserves_user_truncation_marker_key"`: 8 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 194 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 522 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2334 total tests passed at 93.89% coverage.
