# Sprint 514 Change Log

## Dictionary/form metadata non-JSON value rejection

Sprint 514 continued production hardening by tightening the live ServiceNow metadata consumed during dictionary/form Update Set generation. Candidate intent extraction was already strict, but fetched `sys_ui_section` and `sys_ui_element` records still used raw string coercion while filtering default views, matching placement anchors, computing positions, and rendering form layout XML.

`dictionary_form_customer_updates()` now rejects unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values from fetched section and element metadata with the fixed `dictionary/form metadata field contains non-JSON value` diagnostic. The diagnostic does not echo object type names, object string output, credential-like keys, section values, view values, element names, element sys_ids, or position values.

This keeps dictionary/form layout generation fail-closed for corrupted or hostile instance context: unsupported metadata fails before anchor matching, view filtering, form layout planning, XML generation, ServiceNow import, or story writeback.

Verification:

- Added 1 failing-first dictionary/form metadata test covering a secret-bearing object with a hostile `__str__`.
- `python3 -m pytest tests/test_generic_dictionary_form.py::test_generic_dictionary_form_rejects_non_json_metadata_without_leak -q`: failed before implementation because the strict diagnostic did not exist.
- `python3 -m pytest tests/test_generic_dictionary_form.py::test_generic_dictionary_form_rejects_non_json_metadata_without_leak -q`: 1 test passed.
- `python3 -m pytest tests/test_generic_dictionary_form.py -q`: 6 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 588 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2475 total tests passed at 93.49% coverage.
