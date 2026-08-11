# Sprint 360 Change Log

## Traversal-bounded artifact payload diagnostics

Hardened artifact diagnostic projection so oversized payloads are bounded before full recursive
redaction and JSON serialization. Sprint 359 collapsed large artifact views after recursive
redaction, but the implementation still walked and serialized the full redacted structure before
deciding to return a compact diagnostic preview. That protected the response size, but not the
server-side traversal work for very large artifact rows.

Artifact payload diagnostic projection now samples large lists and objects up to a fixed collection
item cap. Omitted list entries are represented with `omitted_items`, and omitted object fields are
represented with `omitted_fields`. If traversal was truncated, the admin response still returns the
same `payload_truncated: true` diagnostic-preview contract introduced in Sprint 359, but the preview
is generated from the bounded projection rather than the full payload. Small artifact payloads keep
their existing response shape. The obsolete unbounded artifact redaction helper was removed so the
admin route has one diagnostic projection path.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving oversized artifact payload previews were generated from the full structure and had no deterministic omitted-items marker.
- Focused verification: `python3 -m pytest tests/test_runtime.py -q -k "bounds_large_payload_traversal"` passed after implementation.
- Artifact regression verification: `python3 -m pytest tests/test_runtime.py -q -k "bounds_large_payload_traversal or bounds_large_payload_object_fields or bounds_large_persisted_payload or artifact_read_returns_metadata_and_payload"` passed with 5 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 187 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 187 source files, 434 documentation tests passed, and 2049 total tests passed at 94.11% coverage.
