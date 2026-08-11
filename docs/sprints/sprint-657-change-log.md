# Sprint 657 Change Log

## Provider candidate allowed-property normalization boundary

Sprint 657 continued production hardening by aligning shared provider candidate normalization with the provider schema's `additionalProperties: false` contract. The normalizer already required exact containers and exact string keys, but it still accepted unknown root, change, and field-entry properties and copied them into the normalized candidate.

Provider candidate root objects now may include only `changes`, `test_plan`, and `rollback_notes`. Change objects may include only `table`, `operation`, `fields`, `sys_id`, and `rationale`. Field-entry objects may include only `name` and `value`. Unknown properties fail closed with fixed diagnostics such as `<Provider> response candidate includes unsupported properties`, `<Provider> response change includes unsupported properties`, or `<Provider> response field entry includes unsupported properties`. Diagnostics do not echo unsupported property names, model-provided values, or exception text.

Verification:

- Added 3 failing-first provider-response-normalization tests proving unknown root, change, and field-entry properties were accepted before implementation.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_unknown_root_property tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_unknown_change_property tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_unknown_field_property -q`: failed before implementation because unsupported properties were accepted.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py -q`: 141 tests passed.
- `ruff check src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py`: all checks passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 731 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2818 tests passed with 93.01% total coverage.
