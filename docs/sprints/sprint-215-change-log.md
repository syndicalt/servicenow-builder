# Sprint 215 Change Log

Scope: Production hardening - public documentation URL content guard.

## Changes

- Added regression coverage for public documentation URLs carrying sensitive query parameters such as `token=doc-secret`.
- Added regression coverage for public documentation URLs with fragments such as `#section`.
- Added regression coverage for raw whitespace and percent-encoded control characters in public documentation URLs.
- Added production runtime validation so unsafe `JEDI_PUBLIC_WEB_DOC_URLS` fail startup before worker execution.
- Extracted shared URL content and sensitive-query validation into `url_query_safety.py` so alert webhooks and public documentation retrieval use the same bounded query parsing behavior.
- Documented public documentation URL rejection for fragments, whitespace/control characters, encoded whitespace/control characters, and sensitive query parameters.

## Verification

- `python3 -m pytest tests/test_rag.py::test_public_web_retriever_blocks_unsafe_url_content_before_transport tests/test_runtime.py::test_validate_runtime_settings_rejects_unsafe_public_web_doc_url_content tests/test_alert_webhook_url.py --cov=jedi_devproject.url_query_safety --cov=jedi_devproject.url_host_safety --cov-report=term --cov-fail-under=90 -q` - 51 passed, 95.14% focused coverage.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 289 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1513 passed, 93.95% coverage.
