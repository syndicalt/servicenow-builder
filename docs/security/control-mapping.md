# Security Control Mapping

This draft maps MVP controls to practical engineering evidence. It is not an ATO package.

| Control Area | MVP Evidence |
|---|---|
| Least privilege | Read-only ServiceNow Table API client for ingestion |
| Secret protection | `.env` ignored, redaction tests, no secrets in fixtures |
| Auditability | Candidate hashes, reviewer events, sprint change logs |
| Boundary control | Provider policy model and default rules-only provider |
| Data minimization | Minimized provider payload tests |
| Change control | Review workflow and export preflight |
| Fail-closed behavior | Safety gates, provider blocking, API error handling |
| Test evidence | Ruff, mypy, pytest, coverage gate over 90% |

Open control work remains before production use: customer ATO mapping, approved storage, approved vector store, retention policy, identity controls, and incident response process.
