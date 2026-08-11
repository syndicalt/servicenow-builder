# Sprint 493 Change Log

## Runtime worker stdout report non-JSON value rejection

Hardened `_runtime_report_json()` so worker stdout audit reports cannot fail through raw Pydantic serializer diagnostics when a corrupted in-process report contains unsupported Python values.

Sprint 477 rejected non-finite numeric runtime report values. This sprint closes the adjacent structural JSON gap: unsupported objects, bytes, and other non-JSON values now fail before stdout rendering with the fixed `runtime worker report contains non-JSON values` diagnostic. The diagnostic does not echo report field names, object type names, object string output, worker stop reasons, job ids, credential-like keys, or values.

The implementation preserves valid Pydantic-native report values such as datetimes by preflighting Python-mode report payloads, then rendering Pydantic JSON-mode payloads as compact JSON lines.

## Verification

- Added 1 failing-first runtime worker report test proving an object with secret-bearing `__str__` output previously surfaced a raw Pydantic serializer diagnostic.
- `python3 -m pytest tests/test_runtime_entrypoints.py::test_runtime_report_json_rejects_non_json_summary_without_payload_leak -q`: failed before implementation because the diagnostic reflected the local object type name.
- `python3 -m pytest tests/test_runtime_entrypoints.py::test_runtime_report_json_rejects_non_json_summary_without_payload_leak tests/test_runtime_entrypoints.py::test_runtime_report_json_rejects_non_finite_summary_without_payload_leak tests/test_runtime_worker_retention.py::test_prune_operational_store_uses_store_factory_and_prints_report tests/test_runtime_worker_retention.py::test_requeue_stale_running_jobs_uses_store_factory_and_prints_report -q`: 4 tests passed.
- `python3 -m pytest tests/test_runtime_entrypoints.py -q`: 10 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 567 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2429 total tests passed at 93.76% coverage.
