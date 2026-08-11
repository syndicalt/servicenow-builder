# Sprint 521 Change Log

## ServiceNow client upsert lookup sys_id non-JSON value rejection

Sprint 521 moved the same fail-closed lookup posture down into the shared ServiceNow client. Bootstrap callers now defend their own apply and verify paths, but the root `ServiceNowClient.upsert_table_record()` path also fetched an existing Table API record, called `str(existing_record["sys_id"])`, and placed that value into the PATCH URL.

`ServiceNowClient.upsert_table_record()` now validates an existing record `sys_id` before building the PATCH URL. Unsupported objects, bytes, containers, floats, and non-scalar values fail with the fixed `ServiceNow API lookup contains non-JSON value` diagnostic. The diagnostic does not echo object type names, object string output, credential-like keys, returned sys_ids, endpoint values, or ServiceNow response internals.

This keeps generic Table API upsert behavior fail-closed for corrupted or hostile ServiceNow lookup responses: unsupported lookup metadata fails before a PATCH request is created, before an untrusted object can enter a URL, and before leaked response details can enter diagnostics.

Verification:

- Added 1 failing-first ServiceNow client upsert lookup test covering a secret-bearing existing-record `sys_id` with a hostile `__str__`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_upsert_rejects_non_json_existing_record_sys_id -q`: failed before implementation because the strict diagnostic did not exist.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_upsert_rejects_non_json_existing_record_sys_id -q`: 1 test passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 99 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 595 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2489 total tests passed at 93.41% coverage.
