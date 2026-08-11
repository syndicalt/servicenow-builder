# Sprint 973 Change Log - Update Set apply changes collection guard

## Summary

Hardened direct Update Set apply candidate change collection handling so corrupted in-process `UpdateSetCandidate.changes` values cannot execute container or entry hooks before dictionary discovery, routing, or ServiceNow side effects.

`apply_candidate_to_update_set()` now normalizes candidate changes through `_apply_changes()` before `_custom_dictionary_elements()` or the main apply loop. The helper accepts only exact Python lists containing exact `CandidateChange` records. List subclasses, alternate iterables, malformed entries, and model subclasses fail closed with `Update Set apply changes contain non-JSON value`.

## Security impact

- Malformed change collections fail before truthiness checks, iteration, custom dictionary element discovery, table routing, integration-user lookup, current Update Set preference writes, dictionary/form upserts, customer-update fetch, or apply result reporting.
- Malformed change entries fail before attribute access such as `.table`, `.operation`, `.fields`, or `.rationale` can execute caller-controlled hooks.
- Valid exact-list candidate changes continue to use the existing change identifier, candidate field, and response metadata guards.

## Tests

- Added 2 failing-first direct Update Set apply changes collection assertions: `test_apply_candidate_rejects_changes_collection_subclass_without_leak` and `test_apply_candidate_rejects_non_candidate_change_without_leak`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_973_documents_update_set_apply_changes_collection_guard`.

## Verification

- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_changes_collection_subclass_without_leak tests/test_update_set_apply.py::test_apply_candidate_rejects_non_candidate_change_without_leak -q` failed before implementation because the changes diagnostic did not exist.
- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_changes_collection_subclass_without_leak tests/test_update_set_apply.py::test_apply_candidate_rejects_non_candidate_change_without_leak tests/test_update_set_apply.py::test_apply_candidate_sets_current_update_set_then_applies_dictionary_change -q` - 3 passed.
- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_changes_collection_subclass_without_leak tests/test_update_set_apply.py::test_apply_candidate_rejects_non_candidate_change_without_leak tests/test_update_set_apply.py::test_apply_candidate_sets_current_update_set_then_applies_dictionary_change tests/test_project_docs.py::test_sprint_973_documents_update_set_apply_changes_collection_guard -q` - 4 passed.
- `pytest tests/test_update_set_apply.py -q` - 37 passed.
- `pytest tests/test_project_docs.py -q` - 1046 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3674 passed, total coverage 93.24%.
