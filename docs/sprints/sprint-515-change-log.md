# Sprint 515 Change Log

## Retrieved Update Set lookup non-JSON value rejection

Sprint 515 continued production hardening by tightening the ServiceNow response handling after retrieved Update Set XML import. Customer-update XML serialization was already strict, but the post-import lookup still stringified the returned `sys_remote_update_set.sys_id` before building handoff URLs and story fields.

`import_retrieved_update_set()` now rejects unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values from the returned retrieved Update Set lookup with the fixed `retrieved Update Set lookup contains non-JSON value` diagnostic. The diagnostic does not echo object type names, object string output, credential-like keys, returned sys_ids, or ServiceNow response internals.

This keeps the retrieved Update Set handoff fail-closed for corrupted or hostile ServiceNow lookup responses: unsupported lookup metadata fails before URL construction, story field updates, work-note formatting, or downstream handoff reporting.

Verification:

- Added 1 failing-first retrieved Update Set lookup test covering a secret-bearing object with a hostile `__str__`.
- `python3 -m pytest tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_non_json_lookup_sys_id_without_leak -q`: failed before implementation because the strict diagnostic did not exist.
- `python3 -m pytest tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_non_json_lookup_sys_id_without_leak -q`: 1 test passed.
- `python3 -m pytest tests/test_update_set_handoff.py -q`: 24 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 589 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2477 total tests passed at 93.48% coverage.
