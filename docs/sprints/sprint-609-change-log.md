# Sprint 609 Change Log

## Runtime worker report exact-string boundary

Sprint 609 continued production hardening by requiring exact string keys and values before runtime worker stdout reports are accepted for compact JSON output. Runtime reports already rejected non-finite numbers and unsupported non-JSON values before printing to stdout, but string subclasses still passed the preflight guard. A corrupted in-process report could therefore carry subclassed text through the operational log boundary.

`_ensure_runtime_report_json_safe()` now accepts exact `str` values and exact `str` mapping keys only. String subclasses fail through the same `runtime worker report contains non-JSON values` diagnostic as other unsupported values, without echoing report fields, stop reasons, job ids, object output, or credential-like fragments.

Verification:

- Added 2 failing-first runtime worker report tests proving string subclass keys and values passed the JSON-safety preflight before implementation.
- `python3 -m pytest tests/test_runtime_worker_retention.py::test_runtime_report_json_rejects_string_subclass_values_without_stringifying tests/test_runtime_worker_retention.py::test_runtime_report_json_rejects_string_subclass_keys_without_stringifying -q`: failed before implementation because neither corrupted report raised `ValueError`.
- `python3 -m pytest tests/test_runtime_worker_retention.py::test_runtime_report_json_rejects_string_subclass_values_without_stringifying tests/test_runtime_worker_retention.py::test_runtime_report_json_rejects_string_subclass_keys_without_stringifying tests/test_runtime_worker_retention.py::test_requeue_stale_running_jobs_uses_store_factory_and_prints_report tests/test_runtime_worker_retention.py::test_main_wires_interval_gated_stale_job_recovery_when_enabled -q`: 4 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_609_documents_runtime_worker_report_exact_string_boundary tests/test_project_docs.py::test_sprint_493_documents_runtime_worker_report_non_json_rejection -q`: 2 passed.
- `python3 -m pytest tests/test_runtime_worker_retention.py -q`: 35 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 683 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2698 passed, total coverage 93.16%, required 90% coverage reached.
