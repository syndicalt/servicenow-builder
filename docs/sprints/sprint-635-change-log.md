# Sprint 635 Change Log

## Retrieved Update Set handoff exact primitive scalar boundary

Sprint 635 continued production hardening by tightening `_candidate_field_text()` and `_imported_update_set_lookup_text()`, the scalar normalization helpers used by retrieved Update Set handoff generation and imported update-set lookup handling. The previous helpers used `isinstance(value, bool | int)` and `isinstance(value, str)`, so integer or string subclasses could be accepted and later converted with custom `__str__` behavior while customer update XML or lookup values were being built.

The helpers now accept only exact `str`, exact `bool`, and exact `int` values, with `None` still mapping to an empty string where optional fields allow it. String subclasses, integer subclasses, objects, containers, floats, bytes, and other unsupported values fail closed with the existing stable diagnostics before XML generation, ServiceNow import, or story writeback.

Verification:

- Added 1 failing-first retrieved Update Set handoff test proving a hostile integer subclass was accepted before implementation.
- `python3 -m pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_integer_subclass_field_without_leak -q`: failed before implementation because no `ValueError` was raised.
- `python3 -m pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_integer_subclass_field_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_non_json_dictionary_form_field_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_preserves_reference_field_metadata -q`: 3 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 709 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2759 tests passed at 93.08% coverage.
