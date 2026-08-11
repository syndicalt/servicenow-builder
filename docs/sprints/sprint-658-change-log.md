# Sprint 658 Change Log

## Provider change metadata schema normalization boundary

Sprint 658 continued production hardening by aligning shared provider candidate normalization with the schema-required change metadata contract. Provider change objects must include `table`, `operation`, `fields`, `sys_id`, and `rationale`, but the normalizer previously validated only the `fields` collection and could return missing, subclassed, or semantically invalid metadata to later validators.

Provider change metadata is now validated after field normalization, preserving existing field-specific diagnostic priority. Each change must include an exact-string `table`, an exact-string `operation` in `insert`, `update`, or `delete`, a null `sys_id`, and a `rationale` that is either an exact string or null. Missing or unsafe metadata fails closed with fixed diagnostics such as `<Provider> response change table must be an exact string`, `<Provider> response change operation is unsupported`, `<Provider> response change sys_id must be null`, or `<Provider> response change rationale must be an exact string or null`. Diagnostics do not echo model-provided metadata or exception text.

Verification:

- Added 5 failing-first provider-response-normalization tests proving missing table metadata, string-subclass table metadata, unsupported operations, non-null `sys_id`, and string-subclass rationale metadata were accepted before implementation.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_requires_change_table tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_change_table_subclass_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_invalid_change_operation_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_non_null_sys_id_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_rationale_subclass_without_leak -q`: failed before implementation because unsafe change metadata was accepted.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py -q`: 146 tests passed.
- `ruff check src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py`: all checks passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 732 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2824 tests passed with 93.01% total coverage.
