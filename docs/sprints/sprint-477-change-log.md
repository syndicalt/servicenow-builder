# Sprint 477 Change Log

## Runtime worker stdout report non-finite number rejection

Hardened runtime worker stdout report rendering so worker loop summaries, retention prune reports,
and stale-job requeue reports cannot emit non-standard JSON when corrupted in-process DTOs contain
`NaN`, `Infinity`, or `-Infinity`. These reports are operational evidence captured by logs, so they
must fail closed before log ingestion receives Python-only numeric tokens.

`_runtime_report_json()` now preflights Python-mode Pydantic report payloads with strict JSON
numeric handling before returning the established compact JSON report body. Non-finite worker report
payloads fail with `runtime worker report contains non-finite numeric values`. The diagnostic is
stable and does not echo report field names, worker stop reasons, job ids, or payload values.

## Verification

- Added 1 failing-first runtime worker report test covering a non-finite worker loop summary value
  without field-name, stop-reason, or value reflection.
- `python3 -m pytest tests/test_runtime_entrypoints.py::test_runtime_report_json_rejects_non_finite_summary_without_payload_leak -q`:
  failed before implementation because `_runtime_report_json()` did not exist and runtime reports
  were printed with direct `model_dump_json()` output.
- `python3 -m pytest tests/test_runtime_entrypoints.py::test_runtime_report_json_rejects_non_finite_summary_without_payload_leak tests/test_runtime_worker_retention.py::test_prune_operational_store_uses_store_factory_and_prints_report tests/test_runtime_worker_retention.py::test_requeue_stale_running_jobs_uses_store_factory_and_prints_report -q`:
  3 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 551 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2397 total tests passed at 93.86% coverage.
