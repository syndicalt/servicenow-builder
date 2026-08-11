# Sprint 369 Change Log

## Bounded provider successful-response traversal

Hardened successful-response parsing for OpenAI and Anthropic provider adapters so model responses cannot force unbounded collection traversal before output text is selected for JSON parsing. Previous controls bounded selected output text before JSON parsing, but OpenAI nested `output[].content[]` scanning and Anthropic `content[]` scanning still walked full provider-supplied lists.

OpenAI response parsing now scans only the bounded provider response collection-item window for both `output` items and nested `content` items. Anthropic response parsing now scans only the bounded provider response collection-item window for content blocks. If no valid output text is found inside the bounded window, each adapter fails closed with the existing fixed missing-output diagnostic.

## Tests

- Failing-first coverage: 3 tests failed before implementation, proving OpenAI output scanning, OpenAI content scanning, and Anthropic content scanning each consumed more than the bounded item window.
- Focused verification: `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q -k "does_not_scan_unbounded or parses_output_item_text or fails_closed_when_no_text_block_is_present or rejects_oversized_output_before_json_parse"` passed with 7 tests.
- Provider regression verification: `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` passed with 101 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 187 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 187 source files, 443 documentation tests passed, and 2069 total tests passed at 93.80% coverage.
