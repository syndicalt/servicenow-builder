# Sprint 518 Change Log

## Update Set importer apply-result sys_id non-JSON value rejection

Sprint 518 continued production hardening by tightening the payload returned by the bootstrap path that installs the ServiceNow Scripted REST API used for retrieved Update Set import. Sprint 517 made the `sys_ws_definition.sys_id` lookup safe before using it as the `sys_ws_operation` parent reference. Sprint 518 extends the same strictness to every `sys_id` stored in the `UpdateSetImporterApplyResult.upserted_records` evidence payload.

`apply_update_set_importer_records()` now validates the `sys_id` returned from each `sys_ws_definition` and `sys_ws_operation` upsert before adding it to the apply result. Unsupported objects, bytes, containers, floats, and non-scalar values fail with the fixed `Update Set importer lookup contains non-JSON value` diagnostic. The diagnostic does not echo object type names, object string output, credential-like keys, returned sys_ids, or ServiceNow response internals.

This keeps importer bootstrap evidence JSON-safe at the source: corrupted or hostile ServiceNow upsert responses cannot be returned as apply-result payloads for later CLI rendering, audit serialization, or operator inspection.

Verification:

- Added 1 failing-first Update Set importer apply-result test covering a secret-bearing operation upsert result with a hostile `__str__`.
- `python3 -m pytest tests/test_bootstrap.py::test_apply_update_set_importer_records_rejects_non_json_operation_result -q`: failed before implementation because the operation result was accepted.
- `python3 -m pytest tests/test_bootstrap.py::test_apply_update_set_importer_records_rejects_non_json_definition_lookup tests/test_bootstrap.py::test_apply_update_set_importer_records_rejects_non_json_operation_result -q`: 2 tests passed.
- `python3 -m pytest tests/test_bootstrap.py -q`: 21 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 592 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2483 total tests passed at 93.44% coverage.
