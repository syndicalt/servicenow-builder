# Sprint 344 Change Log

Scope: Production hardening - public documentation redirect blocking.

## Summary

- Public documentation retrieval now builds an explicit urllib opener with a no-redirect handler instead of using default `urlopen()` behavior.
- Any 3xx redirect is blocked before a second outbound request can be made, so the allowlist and private-host controls cannot be bypassed by an allowlisted URL that redirects to another destination.
- Existing post-fetch final URL validation remains in place for alternate transports and still fails closed if a response reports a different final host.
- Existing HTTPS, allowlist, sensitive-query, timeout, byte-limit, and excerpt-bound controls are preserved.

## Verification

- `python3 -m pytest tests/test_rag.py::test_urllib_public_web_transport_installs_no_redirect_handler tests/test_rag.py::test_urllib_public_web_transport_blocks_redirect_before_following -q` - 2 tests failed before implementation because the transport used default `urlopen()` behavior and exposed no redirect handler.
- `python3 -m pytest tests/test_rag.py::test_urllib_public_web_transport_installs_no_redirect_handler tests/test_rag.py::test_urllib_public_web_transport_blocks_redirect_before_following -q` - 2 passed after implementation.
- `python3 -m pytest tests/test_rag.py -q` - 30 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_forty_four_documents_public_web_redirect_blocking tests/test_rag.py -q` - 31 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 187 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 418 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1999 passed, total coverage 94.04%.
