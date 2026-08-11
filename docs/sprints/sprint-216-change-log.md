# Sprint 216 Change Log

Scope: Production hardening - public documentation private-host startup guard.

## Changes

- Added production runtime regression coverage for public documentation URLs targeting `127.0.0.1`.
- Added production runtime regression coverage for `localhost` and delegated `.localhost` public documentation hosts.
- Added production runtime regression coverage for private RFC1918 hosts such as `10.0.0.1`.
- Added production runtime regression coverage for link-local metadata hosts such as `169.254.169.254`.
- Added production runtime regression coverage for legacy numeric local targets such as `2130706433` and `2852039166`.
- Added shared `is_non_public_hostname()` host classification in `url_host_safety.py` and reused it from the public documentation retriever and production runtime config.
- Documented that production startup rejects public documentation URLs whose normalized host is localhost, private, link-local, reserved, multicast, unspecified, or legacy numeric local.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_validate_runtime_settings_rejects_private_public_web_doc_hosts tests/test_rag.py::test_public_web_retriever_blocks_private_hosts_and_non_https tests/test_rag.py::test_public_web_retriever_blocks_legacy_numeric_private_hosts tests/test_alert_webhook_url.py --cov=jedi_devproject.url_host_safety --cov-report=term --cov-fail-under=90 -q` - 52 passed, 94.55% focused coverage.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 290 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1521 passed, 93.96% coverage.
