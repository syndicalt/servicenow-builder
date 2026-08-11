# Sprint 620 Change Log

## Exact-string ServiceNow work-note boundary

Sprint 620 continued production hardening by tightening the shared ServiceNow work-note sanitizer and CLI summary rendering boundary. `safe_work_note_value()` previously accepted `str` subclasses and several CLI summary call sites coerced arbitrary keys and values with `str()` before sanitization, which meant hostile object conversion hooks could execute before redaction or fixed diagnostics.

`safe_work_note_value()` now accepts exact `str` values only. String subclasses and non-string objects return the fixed `[non-string work note value]` marker before literal-secret iteration, diagnostic redaction, whitespace normalization, or truncation can execute. `render_summary()` now formats only explicit safe scalar types and emits `[unsupported summary value]` for unsupported summary values instead of calling arbitrary `__str__` methods.

Verification:

- Added 4 failing-first tests proving hostile string subclasses, non-string work-note values, hostile secret iterators, and hostile CLI summary values could reach unsafe coercion paths before implementation.
- `python3 -m pytest tests/test_work_note_safety.py tests/test_cli_io.py -q`: 15 tests passed.
- `python3 -m pytest tests/test_work_note_safety.py tests/test_cli_io.py tests/test_project_docs.py::test_sprint_620_documents_exact_string_work_note_boundary -q`: 16 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 694 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2724 tests passed at 93.09% coverage.
