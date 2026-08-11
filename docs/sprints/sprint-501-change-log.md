# Sprint 501 Change Log

## Generation field scalar non-JSON value rejection

Hardened shared generation-field coercion in `validation_helpers.py` so supported ServiceNow customer-update builders no longer implicitly stringify arbitrary Python values while deriving booleans, comma-delimited lists, optional integer order values, or ServiceNow reference values.

The affected helpers are `bool_value()`, `string_list()`, `optional_int()`, and `reference_value()`. They now accept only primitive JSON-like scalar values used by the supported generation paths and reject unsupported objects, bytes, scalar-position containers, and non-finite numeric values with the fixed `generation field scalar value contains non-JSON value` diagnostic. The diagnostic does not echo helper inputs, object type names, object string output, credential-like keys, or payload values.

This preserves existing valid builder behavior, including list item coercion for primitive numeric values and treating a whole `0` string-list input as blank, while removing arbitrary `str()`/`repr()` conversion from Business Rule, Client Script, Script Include, UI Policy, catalog, ATF, dictionary/form, and form-section customer update generation.

## Verification

- Added 4 failing-first validation-helper tests proving secret-bearing objects were previously stringified by shared generation-field coercion helpers.
- `python3 -m pytest tests/test_validation_helpers.py -q`: failed before implementation because the helpers did not raise for secret-bearing objects.
- `python3 -m pytest tests/test_validation_helpers.py -q`: 24 tests passed.
- `python3 -m pytest tests/test_generation_validators.py tests/test_catalog_item_generation.py tests/test_atf_test_generation.py tests/test_generic_dictionary_form.py -q`: 131 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 575 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2449 total tests passed at 93.66% coverage.
