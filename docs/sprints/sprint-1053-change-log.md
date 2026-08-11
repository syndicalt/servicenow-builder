# Sprint 1053 Change Log

## Runtime Env Template Coverage

- Added a failing-first deployment test that compares every `JEDI_*` and `OPENAI_*`
  setting parsed by `load_runtime_settings()` against `.env.example`.
- Expanded `.env.example` so operators can see every runtime control for runtime
  role selection, worker identity, build claiming, update-set apply, classifier
  gating, model-provider configuration, admin authentication, lifecycle webhook
  authentication, rate limits, request ceilings, HSTS, stale-job recovery, alert
  delivery, and public-document retrieval.
- Documented `.env.example` as the synchronized production operator template in
  `docs/operator-guide.md` so hidden runtime defaults do not become deployment
  behavior.

## Verification

- `pytest tests/test_container_runtime.py::test_env_example_documents_all_runtime_environment_controls -q`
- `test_env_example_documents_all_runtime_environment_controls`
