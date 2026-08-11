# Sprint 960 Change Log - Retrieved Update Set handoff description metric guard

## Summary

Hardened retrieved Update Set description metric rendering so corrupted in-process candidate confidence or risk-score values cannot execute custom scalar methods while the ServiceNow review handoff XML is created.

`_update_set_description()` now routes candidate confidence and risk score through `_description_metric_text()`. Exact integers and finite exact floats render normally. Non-finite floats, numeric subclasses, arbitrary objects, bytes, and unsupported metric values render as `[non-json summary value]` before XML serialization.

## Security impact

- Retrieved Update Set description generation no longer directly interpolates candidate confidence or risk-score objects.
- Corrupted candidate metrics cannot execute `str()`, `repr()`, comparison hooks, or custom scalar methods during handoff XML generation.
- The metric boundary follows the same diagnostic convention used by retrieved Update Set candidate field summaries.

## Tests

- Added 1 failing-first retrieved Update Set handoff description metric assertion: `test_create_update_set_handoff_sanitizes_description_metrics_without_stringifying`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_960_documents_handoff_description_metric_guard`.

## Verification

- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_sanitizes_description_metrics_without_stringifying -q` failed before implementation because direct f-string interpolation executed the hostile metric `__str__`.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_sanitizes_description_metrics_without_stringifying tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story -q` - 2 passed.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_sanitizes_description_metrics_without_stringifying tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story tests/test_project_docs.py::test_sprint_960_documents_handoff_description_metric_guard -q` - 3 passed.
- `pytest tests/test_update_set_handoff.py -q` - 38 passed.
- `pytest tests/test_project_docs.py -q` - 1033 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed with no issues in 203 source files.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3645 passed, total coverage 93.25%.
