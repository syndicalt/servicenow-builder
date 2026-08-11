# Sprint 214 Change Log

Scope: Production hardening - public documentation outbound URL guard.

## Changes

- Added regression coverage for public documentation URLs with embedded credentials such as `https://doc-user:doc-secret@docs.servicenow.com/docs`.
- Added regression coverage for legacy numeric local targets such as `2130706433` and `2852039166` in the public documentation retriever.
- Added production runtime validation so credentialed `JEDI_PUBLIC_WEB_DOC_URLS` fail startup.
- Extracted shared hostname normalization and legacy IPv4 parsing into `url_host_safety.py` so alert webhooks and public documentation retrieval use the same hardened host interpretation.
- Documented that public documentation retrieval rejects credentialed URLs and legacy numeric local targets before transport.

## Verification

- `python3 -m pytest tests/test_rag.py::test_public_web_retriever_blocks_embedded_credentials_before_transport tests/test_rag.py::test_public_web_retriever_blocks_legacy_numeric_private_hosts tests/test_runtime.py::test_validate_runtime_settings_rejects_public_web_doc_url_credentials tests/test_alert_webhook_url.py --cov=jedi_devproject.url_host_safety --cov-report=term --cov-fail-under=90 -q` - 46 passed, 95.74% focused coverage.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 173 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 288 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1504 passed, 93.94% coverage.
