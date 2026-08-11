# Sprint 512 Change Log

## Catalog Client Script generation field non-JSON value rejection

Sprint 512 continued the production-hardening pass across catalog generation by tightening Catalog Client Script handoff. Catalog Client Script candidate fields include executable browser-side script behavior and declared read/write metadata, so arbitrary objects must never be coerced into XML payloads, validator inputs, or diagnostics.

`catalog_client_script_customer_updates()` now rejects unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values in catalog item names, script names, script types, watched variables, script bodies, declared fields read, and declared fields written with the fixed `Catalog Client Script generation field contains non-JSON value` diagnostic. The diagnostic does not echo object type names, object string output, credential-like keys, script bodies, variable names, or field metadata.

This keeps Catalog Client Script handoff aligned with the hardened Dictionary, form layout, catalog item, record producer, Script Include, Business Rule, Client Script, UI Policy, and Catalog UI Policy paths: unsupported scalar input fails before script type validation, script safety scanning, field-write validation, catalog variable ownership checks, XML generation, ServiceNow import, or story writeback.

Verification:

- Added 1 failing-first Catalog Client Script generation test covering a secret-bearing object with a hostile `__str__`.
- `python3 -m pytest tests/test_catalog_client_script_generation.py::test_catalog_client_script_rejects_non_json_field_without_leak -q`: failed before implementation because the strict diagnostic did not exist.
- `python3 -m pytest tests/test_catalog_client_script_generation.py::test_catalog_client_script_rejects_non_json_field_without_leak -q`: 1 test passed.
- `python3 -m pytest tests/test_catalog_client_script_generation.py -q`: 22 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 586 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2471 total tests passed at 93.52% coverage.
