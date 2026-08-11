# Sprint 519 Change Log

## Lifecycle webhook bootstrap lookup non-JSON value rejection

Sprint 519 continued production hardening by tightening the bootstrap path that installs the ServiceNow REST Message, REST Method, and Business Rule used for lifecycle event emission. The apply flow creates or updates `sys_rest_message`, then uses the returned REST Message `sys_id` to create or update `sys_rest_message_fn`. The verify flow uses the same REST Message `sys_id` to locate and validate the REST Method.

`apply_lifecycle_webhook_records()` and `verify_lifecycle_webhook_records()` now reject unsupported objects, bytes, containers, floats, and non-scalar values from the ServiceNow REST Message lookup with the fixed `Lifecycle webhook lookup contains non-JSON value` diagnostic. The diagnostic does not echo object type names, object string output, credential-like keys, returned sys_ids, endpoint values, or ServiceNow response internals.

This keeps lifecycle webhook bootstrap fail-closed for corrupted or hostile ServiceNow lookup responses: unsupported lookup metadata fails before creating the REST Method record, verifying against a fabricated parent reference, or writing leaked response details into diagnostics.

Verification:

- Added 1 failing-first lifecycle webhook bootstrap lookup test covering a secret-bearing object with a hostile `__str__`.
- `python3 -m pytest tests/test_bootstrap.py::test_apply_lifecycle_webhook_records_rejects_non_json_rest_message_lookup -q`: failed before implementation because the strict diagnostic did not exist.
- `python3 -m pytest tests/test_bootstrap.py::test_apply_lifecycle_webhook_records_rejects_non_json_rest_message_lookup -q`: 1 test passed.
- `python3 -m pytest tests/test_bootstrap.py -q`: 22 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 593 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2485 total tests passed at 93.42% coverage.
