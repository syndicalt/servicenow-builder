# Sprint 903 Change Log

## Retrieved Update Set customer update string-subclass guard

Hardened retrieved Update Set customer-update XML serialization so generated customer-update metadata and payload fields must use exact strings instead of string subclasses.

`import_retrieved_update_set()` now rejects string subclasses with the fixed `retrieved Update Set customer update contains non-JSON value` diagnostic. The diagnostic does not echo subclass names, overridden string method output, credential-like fragments, update names, target names, payload text, or generated unload XML.

This keeps the boundary closed before CDATA escaping, XML attribute escaping, unload document assembly, ServiceNow import, post-import lookup, story field update, or handoff work-note formatting can execute caller-controlled string methods from model-derived or builder-derived customer update fields.

## Tests

- Added 1 failing-first customer-update string-subclass assertion: `test_import_retrieved_update_set_rejects_string_subclass_customer_update_without_leak`.
- Focused red: `pytest tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_string_subclass_customer_update_without_leak tests/test_project_docs.py::test_sprint_903_documents_retrieved_update_set_customer_update_string_subclass_guard -q` failed because the string subclass executed its overridden `replace()` method during CDATA handling.
- Focused green: `pytest tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_string_subclass_customer_update_without_leak tests/test_project_docs.py::test_sprint_903_documents_retrieved_update_set_customer_update_string_subclass_guard -q` passed with 2 tests.
- Update Set handoff suite: `pytest tests/test_update_set_handoff.py -q` passed with 28 tests.
- Documentation suite: `pytest tests/test_project_docs.py -q` passed with 976 tests.
- Static gates: `python3 -m ruff check src tests` and `python3 -m mypy src tests` passed.
- Full coverage gate: `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` passed with 3516 tests at 93.52% coverage.
