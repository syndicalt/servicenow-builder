# Local Regulated Data Policy

## Purpose

Local development should prove behavior without exposing regulated customer data, credentials,
secrets, or unnecessary personally identifiable information. The same rules protect the hosted
runtime: the controls below are policy for developers and operators, enforced where possible by
the code referenced in `docs/security/control-mapping.md`.

## Rules

- Use synthetic or sanitized fixtures by default. Tests must use fake transports and synthetic
  records; live PDI calls are manual smoke tests only.
- Do not commit real ServiceNow credentials, OAuth tokens, cookies, API keys, webhook signing
  secrets, admin tokens, database URLs with passwords, or session data.
- Keep secrets in the local `.env` or the hosting environment's secret store. `.env` is
  git-ignored; `.env.example` must contain key names with empty or placeholder values only.
- Do not commit raw customer exports unless a written project decision approves the dataset and
  its handling controls.
- Redact secrets before writing logs, artifacts, prompts, embeddings, work notes, or test
  fixtures. Runtime redaction helpers (`runtime_redaction.py`, `diagnostic_redaction.py`,
  `work_note_safety.py`) are the reference behavior for any new output surface.
- Store generated candidates separately from raw inputs. Runtime artifacts belong in the
  PostgreSQL operational store; local audit output belongs under `JEDI_AUDIT_ROOT` (git-ignored
  `artifacts/`), never beside source fixtures.
- Treat missing data-classification metadata as a blocking validation error before any model call.
- Keep dry-run defaults intact locally: `JEDI_BUILD_CLAIM_APPLY=false`,
  `JEDI_UPDATE_SET_APPLY=false`, `JEDI_ALERT_WEBHOOK_ENABLED=false`, and
  `JEDI_PUBLIC_WEB_ACCESS=disabled` unless a specific, reviewed test requires otherwise.

## Approved Local Data

- Synthetic `rm_story` records.
- Sanitized table metadata with no customer secrets.
- Mock retrieval documents created for tests.
- Redacted run manifests and candidate artifacts.
- PDI (Personal Developer Instance) data created by the developer for evaluation, accessed with a
  developer-owned least-privilege OAuth client.

## Prohibited Local Data

- Production ServiceNow exports.
- Authentication material of any kind (client secrets, tokens, cookies, signing secrets, admin
  tokens, provider API keys) outside the local `.env` or approved secret store.
- Sensitive user records.
- Unredacted agency policy documents unless approved for the local workspace.
- Model prompts or responses containing regulated data from a real customer environment.

## Known Local-File Gap

`.gitignore` covers `.env` only. Other local env files — for example `.env.local` — are not
ignored and will show up as untracked files. Never `git add` any file carrying secret values;
prefer the single ignored `.env`, and delete stray env copies after use. Run
`git check-ignore -v <path>` when in doubt.

## Incident Handling

If regulated data or a secret is committed or sent to an unapproved endpoint:

1. Treat the secret as compromised; rotate it through the customer-approved secret manager.
2. Remove the data from the working tree and rewrite or purge history as required by the
   customer's incident process.
3. Record the exposure, scope, rotation evidence, and remediation in the customer operations log.
