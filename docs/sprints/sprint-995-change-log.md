# Sprint 995 Change Log - Bootstrap dictionary-field planning guard

## Summary

Hardened bootstrap field planning so story dictionary metadata is validated before initialization decisions are made.

## Security

`plan_bootstrap_fields()` now routes provided dictionary fields through `_bootstrap_dictionary_fields()`. The helper accepts only exact Python lists containing exact `StoryDictionaryField` records and fails closed with `bootstrap dictionary fields contain non-JSON value`.

Malformed dictionary-field collections or entries fail before iteration hooks, model hooks, active-field filtering, missing-field decisions, writable-field decisions, or bootstrap apply planning can consume caller-controlled behavior.

## Tests

- Added 1 failing-first bootstrap dictionary-field collection subclass assertion: `test_bootstrap_plan_rejects_dictionary_field_collection_subclass_without_leak`.
- Added 1 failing-first bootstrap dictionary-field item subclass assertion: `test_bootstrap_plan_rejects_dictionary_field_item_subclass_without_leak`.
- Added 1 documentation assertion: `test_sprint_995_documents_bootstrap_dictionary_field_planning_guard`.

## Verification

- `pytest tests/test_bootstrap.py::test_bootstrap_plan_rejects_dictionary_field_collection_subclass_without_leak tests/test_bootstrap.py::test_bootstrap_plan_rejects_dictionary_field_item_subclass_without_leak -q` failed before implementation because a collection hook diagnostic leaked and a model subclass was accepted.
- `pytest tests/test_bootstrap.py::test_bootstrap_plan_rejects_dictionary_field_collection_subclass_without_leak tests/test_bootstrap.py::test_bootstrap_plan_rejects_dictionary_field_item_subclass_without_leak tests/test_bootstrap.py::test_bootstrap_plan_only_includes_missing_custom_writeback_fields tests/test_bootstrap.py::test_bootstrap_plan_is_noop_when_custom_fields_exist tests/test_bootstrap.py::test_apply_bootstrap_fields_creates_only_missing_custom_fields -q` - 5 passed.
- `python3 -m ruff check src/jedi_devproject/bootstrap_fields.py tests/test_bootstrap.py` - passed.
- `python3 -m mypy src/jedi_devproject/bootstrap_fields.py tests/test_bootstrap.py` - passed.
