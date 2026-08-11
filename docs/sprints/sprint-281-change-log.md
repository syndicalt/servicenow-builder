# Sprint 281 Change Log - Model Provider Double-Encoded URL Control Guard

## Summary

- Shared encoded whitespace/control-character detection now performs bounded multi-pass decoding using the existing three-pass limit.
- OpenAI and Anthropic provider `base_url` settings now reject double-encoded newline and tab sequences such as `%250a` and `%2509`.
- Added direct helper coverage proving benign encoded values remain allowed while double-encoded control values are rejected.
- Existing provider empty-value, raw whitespace/control-character, single-encoded control-character, HTTPS, hostname, credential, query, and fragment guards remain intact.
- Added failing regressions proving both adapters previously accepted double-encoded provider base URL controls.
- Documented the bounded multi-pass provider encoded-control boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_openai_provider.py::test_openai_provider_settings_reject_encoded_control_character_base_url tests/test_anthropic_provider.py::test_anthropic_provider_settings_reject_encoded_control_character_base_url -q` - 4 tests failed and 4 passed before implementation because both adapters accepted double-encoded provider base URL controls while rejecting single-encoded controls.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` - 75 passed.
- `python3 -m pytest tests/test_url_query_safety.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_alert_webhook_url.py tests/test_rag.py::test_public_web_retriever_blocks_unsafe_url_content_before_transport tests/test_runtime.py::test_validate_runtime_settings_rejects_alert_webhook_url_encoded_control_characters -q` - 126 passed.
- `python3 -m pytest tests/test_url_query_safety.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_alert_webhook_url.py tests/test_rag.py::test_public_web_retriever_blocks_unsafe_url_content_before_transport tests/test_runtime.py::test_validate_runtime_settings_rejects_alert_webhook_url_encoded_control_characters tests/test_project_docs.py::test_sprint_two_hundred_eighty_one_documents_provider_double_encoded_guard -q` - 127 passed.
- `python3 -m ruff check src/jedi_devproject/url_query_safety.py src/jedi_devproject/provider_url_safety.py src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_url_query_safety.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_alert_webhook_url.py tests/test_rag.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/url_query_safety.py src/jedi_devproject/provider_url_safety.py src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_url_query_safety.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_alert_webhook_url.py tests/test_rag.py tests/test_runtime.py tests/test_project_docs.py` - success: no issues found in 11 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 177 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 355 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1723 passed; total coverage 93.97%.
