# Local Regulated Data Policy

## Purpose

Local development should prove behavior without exposing regulated customer data, credentials, secrets, or unnecessary personally identifiable information.

## Rules

- Use synthetic or sanitized fixtures by default.
- Do not commit real ServiceNow credentials, OAuth tokens, cookies, API keys, or session data.
- Do not commit raw customer exports unless a written project decision approves the dataset and its handling controls.
- Redact secrets before writing logs, artifacts, prompts, embeddings, or test fixtures.
- Store generated candidates separately from raw inputs.
- Treat missing data-classification metadata as a blocking validation error.

## Approved Local Data

- Synthetic `rm_story` records.
- Sanitized table metadata with no customer secrets.
- Mock retrieval documents created for tests.
- Redacted run manifests and candidate artifacts.

## Prohibited Local Data

- Production ServiceNow exports.
- Authentication material.
- Sensitive user records.
- Unredacted agency policy documents unless approved for the local workspace.
- Model prompts or responses containing regulated data from a real customer environment.
