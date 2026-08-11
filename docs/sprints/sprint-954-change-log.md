# Sprint 954 Change Log - Retrieved Update Set handoff reference dict-subclass guard

## Scope

- Hardened `_reference_table()` so dictionary/form retrieved Update Set handoff accepts only exact dictionaries before candidate reference `value` or `display_value` lookup.
- Preserved exact JSON dictionary support for normalized provider/model reference metadata.
- Documented the handoff reference-dictionary subclass boundary in the operator guide.

## Production Hardening

- Dictionary subclasses now fail with `dictionary/form handoff field contains non-JSON value` before retrieved Update Set customer updates are generated.
- Retrieved Update Set handoff no longer allows caller-controlled mapping accessors to run while extracting candidate-derived dictionary reference metadata.
- The normal reference-field handoff path still emits reviewed `sys_dictionary` reference metadata into the retrieved Update Set XML.

## Tests

- Added `test_create_update_set_handoff_rejects_reference_dict_subclass_without_leak`.
- Captured 1 failing-first retrieved Update Set handoff reference dict-subclass assertion.
- Focused verification passed: 3 tests.
- Scoped verification passed: `tests/test_update_set_handoff.py` 32 tests and `tests/test_project_docs.py` 1027 tests.
- Static verification passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage verification passed: 3633 tests at 93.30% coverage.
