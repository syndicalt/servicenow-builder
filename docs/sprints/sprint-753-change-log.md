# Sprint 753 Change Log - Public web transport cause boundary

## Scope

Hardened public web retrieval transport diagnostics so HTTP and URL/timeout failures do not retain unsafe transport exceptions as public `PublicWebRetrievalBlocked` causes.

## Tests First

- Added 2 failing-first public web transport cause assertions:
  - `tests/test_rag.py::test_urllib_public_web_transport_http_errors_do_not_retain_cause`
  - `tests/test_rag.py::test_urllib_public_web_transport_url_errors_do_not_retain_cause`
- Initial failures proved HTTP and URL retrieval failures retained lower-level transport exceptions as `__cause__`.
- The hostile transport exceptions included `doc-secret` to prove cause retention could preserve sensitive URL, message, or timeout fragments even though the public diagnostic was fixed.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_753_documents_public_web_transport_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original `HTTPError` causes for public documentation HTTP failures.
- Suppressed original `URLError` and `TimeoutError` causes for public documentation transport failures.
- Preserved existing fixed diagnostics:
  - `public documentation fetch failed with HTTP <status>`
  - `public documentation fetch failed`
- Documented the public web transport cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_rag.py -q -k "urllib_public_web_transport_http_errors_do_not_retain_cause or urllib_public_web_transport_url_errors_do_not_retain_cause"` failed first, then passed.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_753` failed first, then passed.
- `ruff check src tests` passed.
- `mypy src tests` passed.
- `python3 -m pytest tests/test_rag.py -q` passed: 32 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed: 3090 passed, 93.37% coverage.
