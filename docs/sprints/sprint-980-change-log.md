# Sprint 980 Change Log - Dictionary/form handoff alias truthiness guard

## Summary

Hardened dictionary/form retrieved Update Set handoff alias selection so malformed candidate field values cannot execute truthiness hooks while table, reference, qualifier, or placement metadata is resolved.

`_form_table_name()`, `_reference_table()`, `_reference_qualifier()`, `_placement_anchor()`, and `_story_table_name()` now use `_first_present()` and `_candidate_field_present()` instead of raw `or` chains or direct `if value` checks. Unsupported values flow into `_candidate_field_text()` and fail closed with `dictionary/form handoff field contains non-JSON value`.

## Security impact

- Malformed table aliases fail before boolean chaining, table normalization, dictionary/form intent comparison, customer-update generation, ServiceNow import, story writeback, or returned handoff metadata.
- Malformed placement anchors fail before direct `if` checks, placement planning, customer-update generation, ServiceNow import, or story writeback.
- Malformed reference and reference-qualifier aliases fail before boolean chaining, reference resolution, XML generation, ServiceNow import, or story writeback.
- Diagnostics do not include object type names, custom truthiness output, custom string output, or credential-like fragments.

## Tests

- Added 1 failing-first form table alias assertion: `test_create_update_set_handoff_rejects_truthy_form_table_alias_without_leak`.
- Added 1 failing-first placement anchor assertion: `test_create_update_set_handoff_rejects_truthy_placement_anchor_without_leak`.
- Added 1 reference alias assertion: `test_create_update_set_handoff_rejects_truthy_reference_alias_without_leak`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_980_documents_dictionary_form_alias_truthiness_guard`.

## Verification

- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_truthy_form_table_alias_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_truthy_placement_anchor_without_leak -q` failed before implementation because malformed alias values executed `__bool__`.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_truthy_form_table_alias_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_truthy_placement_anchor_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_accepts_table_aliases_and_position_hints -q` - 3 passed.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_truthy_form_table_alias_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_truthy_placement_anchor_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_truthy_reference_alias_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_accepts_table_aliases_and_position_hints -q` - 4 passed.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_truthy_form_table_alias_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_truthy_placement_anchor_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_truthy_reference_alias_without_leak tests/test_project_docs.py::test_sprint_980_documents_dictionary_form_alias_truthiness_guard -q` - 4 passed.
- `pytest tests/test_update_set_handoff.py -q` - 55 passed.
- `pytest tests/test_project_docs.py -q` - 1053 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3694 passed, 93.25% coverage.
