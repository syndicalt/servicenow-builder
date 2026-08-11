# Sprint 667 Change Log

## Provider table identifier shape boundary

Sprint 667 continued production hardening by narrowing provider change table names from generic bounded strings to ServiceNow-safe identifiers. Earlier sprints rejected blank, whitespace/control-bearing, and oversized table strings, but punctuation-bearing names such as `sys-dictionary`, dotted names such as `sys.dictionary`, digit-leading names, or secret-bearing punctuation strings could still enter normalized candidate changes.

Provider change `table` values now must use ASCII identifier syntax: start with a letter or underscore and contain only letters, digits, and underscores. Safe ServiceNow table names such as `sys_dictionary`, `cmdb_ci`, and scoped app table names like `x_jedi_app_table` remain accepted. Unsafe shapes fail closed with `<Provider> response change table must be a safe identifier` without echoing the submitted table value.

Verification:

- Added 4 failing-first provider-response-normalization assertions proving unsafe table identifier shapes were accepted before implementation.
- Added 3 positive provider-response-normalization assertions proving standard and scoped ServiceNow table identifiers remain accepted.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_unsafe_table_identifier_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_accepts_safe_table_identifier -q`: failed before implementation because unsafe table identifier shapes were accepted.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_unsafe_table_identifier_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_accepts_safe_table_identifier -q`: 7 tests passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_667_documents_provider_table_identifier_shape_boundary -q`: failed before documentation because the Sprint 667 change log did not exist.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_667_documents_provider_table_identifier_shape_boundary -q`: 1 test passed.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py -q`: 169 tests passed.
- `ruff check src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py tests/test_project_docs.py`: failed once on a long helper expression, then passed after wrapping.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 741 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2856 tests passed with 93.04% total coverage.
