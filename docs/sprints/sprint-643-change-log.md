# Sprint 643 Change Log

## Dictionary/form discovery metadata exact-string boundary

Sprint 643 continued production hardening by tightening live dictionary/form discovery metadata before it enters `instance_context_bundle`. `discover_dictionary_form_context()` previously used direct `str()` conversions for values returned by ServiceNow table, dictionary, section, element, and ACL records. A corrupted in-process client or malformed response object could execute custom conversion while table schema or form layout context was being assembled for model use.

Dictionary/form discovery now accepts direct text metadata only when it is an exact string or missing. Unsupported objects, bytes, containers, string subclasses, and unstringifiable values fail closed with `dictionary/form discovery metadata contains non-JSON value` before table labels, fields, form sections, elements, or ACL indicators are persisted into discovery context.

Verification:

- Added 1 failing-first instance-discovery test proving a hostile table label object was accepted before implementation.
- `python3 -m pytest tests/test_instance_discovery.py::test_discover_dictionary_form_context_rejects_table_label_object_without_leak -q`: failed before implementation because no `ValueError` was raised.
- `python3 -m pytest tests/test_instance_discovery.py::test_discover_dictionary_form_context_rejects_table_label_object_without_leak tests/test_instance_discovery.py::test_discover_dictionary_form_context_fetches_target_instance_state tests/test_instance_discovery.py::test_discover_servicenow_surface_context_collects_related_platform_surfaces -q`: 3 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 717 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2776 tests passed at 93.05% coverage.
