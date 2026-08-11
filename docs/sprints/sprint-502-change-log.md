# Sprint 502 Change Log

## Retrieved Update Set customer update scalar non-JSON value rejection

Hardened retrieved Update Set XML handoff serialization so generated customer-update metadata and payload fields are not implicitly stringified while building the `sys_update_xml` unload document.

`import_retrieved_update_set()` now requires string values for the customer-update `action`, `name`, `payload`, `target_name`, and `type` fields before any ServiceNow import request is made. Unsupported Python objects, bytes, containers, numbers, and missing scalar values fail with the fixed `retrieved Update Set customer update contains non-JSON value` diagnostic. The diagnostic does not echo customer-update field names, object type names, object string output, credential-like keys, or payload values.

This preserves existing deterministic customer-update builders while closing the retrieved Update Set handoff boundary against arbitrary `str()`/`repr()` conversion inside XML metadata or payload CDATA assembly.

## Verification

- Added 1 failing-first retrieved Update Set handoff test proving a secret-bearing object was previously stringified into handoff XML.
- `python3 -m pytest tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_non_json_customer_update_scalar_without_leak -q`: failed before implementation because the import path did not reject the object.
- `python3 -m pytest tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_non_json_customer_update_scalar_without_leak -q`: 1 test passed.
- `python3 -m pytest tests/test_update_set_handoff.py -q`: 21 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 576 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2451 total tests passed at 93.66% coverage.
