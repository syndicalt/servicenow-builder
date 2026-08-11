# Sprint 610 Change Log

## Operational lifecycle event exact-string JSONB boundary

Sprint 610 continued production hardening by requiring exact string values before lifecycle event payloads are accepted for operational-store JSONB persistence. Lifecycle event payloads already rejected non-finite numeric values and unsupported non-JSON values before transaction start, but string subclasses still passed the JSON-safety preflight and could reach the database boundary as if they were ordinary strings.

`_ensure_lifecycle_event_payload_json_safe()` now accepts exact `str` values and exact `str` mapping keys only. String subclasses fail through the same `operational lifecycle event payload contains non-JSON values` diagnostic as other unsupported values, without echoing event field names, ServiceNow sys_ids, correlation ids, object output, or credential-like fragments.

Verification:

- Added 1 failing-first operational-store lifecycle event test proving a string subclass event id passed the JSON-safety preflight before implementation.
- `python3 -m pytest tests/test_operational_store.py::test_record_lifecycle_event_rejects_string_subclass_payload_before_transaction -q`: failed before implementation because the subclassed event id reached database lookup instead of raising `ValueError` before transaction start.
- `python3 -m pytest tests/test_operational_store.py::test_record_lifecycle_event_rejects_string_subclass_payload_before_transaction tests/test_operational_store.py::test_record_lifecycle_event_rejects_non_finite_payload_before_transaction tests/test_operational_store.py::test_record_lifecycle_event_rejects_non_json_payload_before_transaction -q`: 3 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_610_documents_operational_lifecycle_event_exact_string_boundary tests/test_project_docs.py::test_sprint_491_documents_operational_lifecycle_event_non_json_rejection -q`: 2 passed.
- `python3 -m pytest tests/test_operational_store.py -q`: 49 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 684 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2700 passed, total coverage 93.16%, required 90% coverage reached.
