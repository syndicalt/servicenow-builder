# Sprint 327 Change Log

Scope: Production hardening - RAG and public documentation validation input redaction.

## Summary

- RAG document and retrieval result validation now suppresses rejected input values in Pydantic validation errors.
- Public documentation access config and public web response validation now suppress rejected input values in Pydantic validation errors.
- Validation diagnostics still name invalid fields and stable reasons, but enum, type, parser, and bounds failures do not echo rejected documentation domains, retrieved content, public-documentation URLs, response snippets, timeout fragments, or citation payloads into logs, artifacts, or ServiceNow work notes.

## Verification

- `python3 -m pytest tests/test_rag.py::test_rag_validation_errors_do_not_echo_rejected_inputs -q` - 1 test failed before implementation because direct RAG validation echoed `input_value='secret-domain'`.
- `python3 -m pytest tests/test_rag.py::test_rag_validation_errors_do_not_echo_rejected_inputs tests/test_rag.py -q` - 28 passed after implementation.
- `python3 -m pytest tests/test_rag.py::test_rag_validation_errors_do_not_echo_rejected_inputs tests/test_project_docs.py::test_sprint_three_hundred_twenty_seven_documents_rag_error_redaction -q` - 2 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 181 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 401 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1956 passed, total coverage 93.92%.
