# Sprint 361 Change Log

## Iterator-bounded artifact diagnostic sampling

Closed a root-cause gap in the artifact diagnostic projection introduced by Sprint 360. The
projection returned bounded diagnostic previews, but the dictionary branch still materialized
`list(value.items())` before sampling. That meant a very wide artifact object could still force the
admin route to allocate and consume the full field set before emitting an `omitted_fields` marker.

The projection now samples dictionaries, lists, and tuples with bounded iterators. It uses collection
length only to compute deterministic `omitted_fields` and `omitted_items` counts, and it no longer
copies the full collection before applying the admin collection-item cap. This preserves the Sprint
360 diagnostic-preview contract while reducing server-side CPU and memory exposure for very wide
artifact payloads.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving a wide mapping was fully consumed by `list(value.items())` before projection sampling.
- Focused verification: `python3 -m pytest tests/test_runtime.py -q -k "does_not_consume_all_fields or bounds_large_payload_traversal or bounds_large_payload_object_fields or bounds_large_persisted_payload or artifact_read_returns_metadata_and_payload"` passed with 6 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 187 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 187 source files, 435 documentation tests passed, and 2051 total tests passed at 94.02% coverage.
