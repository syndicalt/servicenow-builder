# Sprint 371 Change Log

## Bounded provider candidate normalization

Hardened model provider candidate normalization so successful OpenAI and Anthropic responses cannot produce oversized post-parse candidate structures before deterministic validators run. Previous controls bounded selected output text before JSON parsing, but both adapters duplicated unbounded normalization loops over candidate `changes` and per-change `fields`.

The duplicated normalizers were replaced with a shared provider response normalization boundary. It preserves the existing provider-specific fixed diagnostics while enforcing a maximum of 100 candidate changes and 100 field entries per change. Oversized candidates fail closed before normalization into the internal implementation-candidate shape.

## Tests

- Failing-first coverage: 4 tests failed before implementation, proving OpenAI and Anthropic accepted too many candidate changes and too many candidate fields.
- Focused verification: `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q -k "too_many_candidate or rejects_arbitrary_field_object or rejects_non_list_changes or rejects_non_object_change or rejects_non_object_field_entry or rejects_field_entries_without_names or posts_structured_output_request"` passed with 12 tests.
- Provider regression verification: `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` passed with 106 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 188 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 188 source files, 445 documentation tests passed, and 2076 total tests passed at 93.85% coverage.
