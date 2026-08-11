# Sprint 517 Change Log

## Update Set importer bootstrap lookup non-JSON value rejection

Sprint 517 continued production hardening by tightening the bootstrap path that installs the ServiceNow Scripted REST API used for retrieved Update Set import. The apply flow creates or updates `sys_ws_definition`, then uses the returned definition `sys_id` to create or update `sys_ws_operation`. The verify flow uses the same definition `sys_id` to locate and validate the operation.

`apply_update_set_importer_records()` and `verify_update_set_importer_records()` now reject unsupported objects, bytes, containers, floats, and non-scalar values from the ServiceNow definition lookup with the fixed `Update Set importer lookup contains non-JSON value` diagnostic. The diagnostic does not echo object type names, object string output, credential-like keys, returned sys_ids, or ServiceNow response internals.

This keeps the importer bootstrap fail-closed for corrupted or hostile ServiceNow lookup responses: unsupported lookup metadata fails before creating the operation record, verifying against a fabricated parent reference, or writing leaked response details into diagnostics.

Verification:

- Added 1 failing-first Update Set importer bootstrap lookup test covering a secret-bearing object with a hostile `__str__`.
- `python3 -m pytest tests/test_bootstrap.py::test_apply_update_set_importer_records_rejects_non_json_definition_lookup -q`: failed before implementation because the strict diagnostic did not exist.
- `python3 -m pytest tests/test_bootstrap.py::test_apply_update_set_importer_records_rejects_non_json_definition_lookup -q`: 1 test passed.
- `python3 -m pytest tests/test_bootstrap.py -q`: 20 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 591 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2481 total tests passed at 93.44% coverage.
