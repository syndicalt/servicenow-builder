from __future__ import annotations

import base64
import binascii
import html
import json
import os
import secrets
from collections.abc import Callable, Iterable
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Protocol, cast
from urllib.parse import urlsplit

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict

from jedi_devproject.fulfillment_handler import (
    BuildClaimFulfillmentConfig,
    build_claim_fulfillment_handler,
)
from jedi_devproject.fulfillment_worker import (
    FulfillmentExecutionResult,
    FulfillmentFailureNotifier,
    FulfillmentHandler,
    FulfillmentWorkerResult,
    FulfillmentWorkerStore,
    process_one_fulfillment_job,
)
from jedi_devproject.implementation_packet import IMPLEMENTATION_PACKET_TASK
from jedi_devproject.lifecycle_api import (
    LifecycleEventStore,
    LifecycleWebhookAuthMode,
    create_lifecycle_api,
)
from jedi_devproject.model_fulfillment import (
    ModelCandidateFulfillmentConfig,
    model_candidate_fulfillment_handler,
)
from jedi_devproject.models import DataClassification, ProviderPolicy, ProviderStatus
from jedi_devproject.openai_provider import OpenAIProviderSettings, OpenAIResponsesProvider
from jedi_devproject.operational_store import (
    ArtifactBlobRecord,
    ArtifactRefRecord,
    FulfillmentJobRecord,
    LifecycleEventRecord,
    connect_operational_store,
)
from jedi_devproject.rag import Document, RagDomain, SpecializedRags
from jedi_devproject.safety import AllowlistPolicy, StoryType
from jedi_devproject.servicenow import (
    HttpTransport,
    OAuthClientCredentials,
    ServiceNowClient,
    ServiceNowSettings,
    UrllibTransport,
    load_dotenv_values,
)


class RuntimeConfigError(ValueError):
    """Raised when runtime environment configuration is incomplete."""


class RuntimeSettings(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    runtime_environment: str = "development"
    database_url: str
    servicenow_instance_url: str
    servicenow_client_id: str
    servicenow_client_secret: str
    worker_id: str = "jedi-devproject-worker"
    audit_root: Path
    build_claim_apply: bool = False
    build_claim_from_state: str = "Ready"
    build_claim_state: str = "Work in Progress"
    model_provider: str | None = None
    openai_api_key: str | None = None
    openai_model: str | None = None
    admin_api_token: str | None = None
    admin_auth_mode: Literal["disabled", "dev_basic", "oidc", "servicenow_oauth"] = "disabled"
    admin_console_username: str | None = None
    admin_console_password: str | None = None
    lifecycle_webhook_auth_mode: LifecycleWebhookAuthMode = "disabled"
    lifecycle_webhook_secret: str | None = None
    lifecycle_webhook_max_skew_seconds: int = 300
    update_set_apply: bool = False
    update_set_user_name: str | None = None


class RuntimeStore(LifecycleEventStore, FulfillmentWorkerStore, Protocol):
    def __enter__(self) -> RuntimeStore: ...

    def __exit__(self, *_args: object) -> None: ...

    def get_artifact_blob(self, artifact_id: int) -> ArtifactBlobRecord: ...

    def artifact_refs_for_job(self, job_id: str) -> list[ArtifactRefRecord]: ...

    def recent_lifecycle_events(self, *, limit: int = 50) -> list[LifecycleEventRecord]: ...

    def recent_fulfillment_jobs(self, *, limit: int = 50) -> list[FulfillmentJobRecord]: ...


StoreFactory = Callable[[str], RuntimeStore]
DEFAULT_STORE_FACTORY = cast(StoreFactory, connect_operational_store)


def load_runtime_settings(env_path: Path | None = None) -> RuntimeSettings:
    values = dict(os.environ)
    if env_path is not None and env_path.exists():
        values.update(load_dotenv_values(env_path))
    required = [
        "DATABASE_URL",
        "SERVICENOW_INSTANCE_URL",
        "SERVICENOW_CLIENT_ID",
        "SERVICENOW_CLIENT_SECRET",
        "JEDI_AUDIT_ROOT",
    ]
    missing = [key for key in required if not values.get(key)]
    if missing:
        raise RuntimeConfigError(f"Missing required runtime settings: {', '.join(missing)}")

    return RuntimeSettings(
        runtime_environment=str(values.get("JEDI_ENVIRONMENT") or "development"),
        database_url=str(values["DATABASE_URL"]),
        servicenow_instance_url=str(values["SERVICENOW_INSTANCE_URL"]),
        servicenow_client_id=str(values["SERVICENOW_CLIENT_ID"]),
        servicenow_client_secret=str(values["SERVICENOW_CLIENT_SECRET"]),
        worker_id=str(values.get("JEDI_WORKER_ID") or "jedi-devproject-worker"),
        audit_root=Path(str(values["JEDI_AUDIT_ROOT"])),
        build_claim_apply=_truthy(values.get("JEDI_BUILD_CLAIM_APPLY")),
        build_claim_from_state=str(values.get("JEDI_BUILD_CLAIM_FROM_STATE") or "Ready"),
        build_claim_state=str(values.get("JEDI_BUILD_CLAIM_STATE") or "Work in Progress"),
        model_provider=_optional_str(values.get("JEDI_MODEL_PROVIDER")),
        openai_api_key=_optional_str(values.get("OPENAI_API_KEY")),
        openai_model=_optional_str(values.get("OPENAI_MODEL")),
        admin_api_token=_optional_str(values.get("JEDI_ADMIN_API_TOKEN")),
        admin_auth_mode=cast(
            Literal["disabled", "dev_basic", "oidc", "servicenow_oauth"],
            str(values.get("JEDI_ADMIN_AUTH_MODE") or "disabled"),
        ),
        admin_console_username=_optional_str(values.get("JEDI_ADMIN_CONSOLE_USERNAME")),
        admin_console_password=_optional_str(values.get("JEDI_ADMIN_CONSOLE_PASSWORD")),
        lifecycle_webhook_auth_mode=cast(
            LifecycleWebhookAuthMode,
            str(values.get("JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE") or "disabled"),
        ),
        lifecycle_webhook_secret=_optional_str(values.get("JEDI_LIFECYCLE_WEBHOOK_SECRET")),
        lifecycle_webhook_max_skew_seconds=_int_value(
            values.get("JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS"),
            default=300,
        ),
        update_set_apply=_truthy(values.get("JEDI_UPDATE_SET_APPLY")),
        update_set_user_name=_optional_str(values.get("JEDI_UPDATE_SET_USER_NAME")),
    )


def create_runtime_api(
    *,
    settings: RuntimeSettings,
    store_factory: StoreFactory = DEFAULT_STORE_FACTORY,
) -> FastAPI:
    store = store_factory(settings.database_url)
    app = create_lifecycle_api(
        store=store,
        webhook_auth_mode=settings.lifecycle_webhook_auth_mode,
        webhook_secret=settings.lifecycle_webhook_secret,
        runtime_environment=settings.runtime_environment,
        webhook_max_skew_seconds=settings.lifecycle_webhook_max_skew_seconds,
    )

    @app.get("/artifacts/{artifact_id}")
    def get_artifact(
        artifact_id: int,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _require_admin_token(settings=settings, authorization=authorization)
        try:
            artifact = store.get_artifact_blob(artifact_id)
        except KeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="artifact not found",
            ) from exc
        return _artifact_blob_response(artifact)

    @app.get("/jobs/{job_id}/artifacts")
    def list_job_artifacts(
        job_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _require_admin_token(settings=settings, authorization=authorization)
        return {
            "job_id": job_id,
            "artifacts": [
                _artifact_ref_response(ref) for ref in store.artifact_refs_for_job(job_id)
            ],
        }

    @app.get("/admin/lifecycle-events")
    def list_lifecycle_events(
        authorization: str | None = Header(default=None),
        limit: int = 50,
    ) -> dict[str, Any]:
        _require_admin_token(settings=settings, authorization=authorization)
        safe_limit = _bounded_limit(limit)
        return {
            "events": [
                _lifecycle_event_response(event)
                for event in store.recent_lifecycle_events(limit=safe_limit)
            ]
        }

    @app.get("/admin/jobs")
    def list_jobs(
        authorization: str | None = Header(default=None),
        limit: int = 50,
    ) -> dict[str, Any]:
        _require_admin_token(settings=settings, authorization=authorization)
        safe_limit = _bounded_limit(limit)
        return {
            "jobs": [
                _fulfillment_job_response(job)
                for job in store.recent_fulfillment_jobs(limit=safe_limit)
            ]
        }

    @app.get("/admin", response_class=HTMLResponse)
    def admin_console(authorization: str | None = Header(default=None)) -> HTMLResponse:
        _require_admin_console_credentials(settings=settings, authorization=authorization)
        jobs = store.recent_fulfillment_jobs(limit=25)
        events = store.recent_lifecycle_events(limit=25)
        artifact_refs_by_job = {job.job_id: store.artifact_refs_for_job(job.job_id) for job in jobs}
        return HTMLResponse(
            _admin_console_html(
                jobs=jobs,
                events=events,
                artifact_refs_by_job=artifact_refs_by_job,
            )
        )

    @app.get("/admin/artifacts/{artifact_id}", response_class=HTMLResponse)
    def admin_console_artifact(
        artifact_id: int,
        authorization: str | None = Header(default=None),
    ) -> HTMLResponse:
        _require_admin_console_credentials(settings=settings, authorization=authorization)
        try:
            artifact = store.get_artifact_blob(artifact_id)
        except KeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="artifact not found",
            ) from exc
        return HTMLResponse(_admin_artifact_html(artifact))

    return app


def _require_admin_token(
    *,
    settings: RuntimeSettings,
    authorization: str | None,
) -> None:
    if not settings.admin_api_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin artifact API is not configured",
        )
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="admin bearer token required",
        )
    token = authorization.removeprefix("Bearer ").strip()
    if not secrets.compare_digest(token, settings.admin_api_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin bearer token rejected",
        )


def _require_admin_console_credentials(
    *,
    settings: RuntimeSettings,
    authorization: str | None,
) -> None:
    if settings.admin_auth_mode == "disabled":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin console authentication is disabled",
        )
    if settings.admin_auth_mode in {"oidc", "servicenow_oauth"}:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"admin auth mode is not implemented: {settings.admin_auth_mode}",
        )
    if settings.admin_auth_mode != "dev_basic":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"admin auth mode is not supported: {settings.admin_auth_mode}",
        )
    if settings.runtime_environment.strip().lower() != "development":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="dev_basic admin auth is development-only",
        )
    if not settings.admin_console_username or not settings.admin_console_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin console is not configured",
        )
    credentials = _basic_auth_credentials(authorization)
    if credentials is None:
        raise _admin_console_unauthorized()
    username, password = credentials
    username_ok = secrets.compare_digest(username, settings.admin_console_username)
    password_ok = secrets.compare_digest(password, settings.admin_console_password)
    if not (username_ok and password_ok):
        raise _admin_console_unauthorized()


def _basic_auth_credentials(authorization: str | None) -> tuple[str, str] | None:
    if authorization is None or not authorization.startswith("Basic "):
        return None
    encoded = authorization.removeprefix("Basic ").strip()
    try:
        decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return None
    username, separator, password = decoded.partition(":")
    if separator != ":":
        return None
    return username, password


def _admin_console_unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="admin console credentials required",
        headers={"WWW-Authenticate": 'Basic realm="jedi-admin"'},
    )


def _artifact_blob_response(artifact: ArtifactBlobRecord) -> dict[str, Any]:
    return {
        "id": artifact.id,
        "job_id": artifact.job_id,
        "story_number": artifact.story_number,
        "artifact_kind": artifact.artifact_kind,
        "schema_version": artifact.schema_version,
        "sha256": artifact.sha256,
        "created_at": _json_timestamp(artifact.created_at),
        "payload": artifact.payload_json,
    }


def _artifact_ref_response(ref: ArtifactRefRecord) -> dict[str, Any]:
    return {
        "id": ref.id,
        "job_id": ref.job_id,
        "artifact_kind": ref.artifact_kind,
        "path": ref.path,
        "sha256": ref.sha256,
        "artifact_id": ref.artifact_id,
        "created_at": _json_timestamp(ref.created_at),
    }


def _lifecycle_event_response(event: LifecycleEventRecord) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "story_number": event.story_number,
        "received_at": _json_timestamp(event.received_at),
        "validation_status": event.validation_status,
    }


def _fulfillment_job_response(job: FulfillmentJobRecord) -> dict[str, Any]:
    return {
        "job_id": job.job_id,
        "event_id": job.event_id,
        "story_number": job.story_number,
        "status": job.status,
        "attempt_count": job.attempt_count,
        "created_at": _json_timestamp(job.created_at),
        "updated_at": _json_timestamp(job.updated_at),
        "locked_by": job.locked_by,
        "locked_at": _json_timestamp(job.locked_at) if job.locked_at is not None else None,
        "last_error": job.last_error,
    }


def _admin_console_html(
    *,
    jobs: list[FulfillmentJobRecord],
    events: list[LifecycleEventRecord],
    artifact_refs_by_job: dict[str, list[ArtifactRefRecord]],
) -> str:
    job_rows = "\n".join(
        _admin_job_row(job, artifact_refs_by_job.get(job.job_id, [])) for job in jobs
    )
    event_rows = "\n".join(_admin_event_row(event) for event in events)
    if not job_rows:
        job_rows = '<tr><td colspan="8" class="empty">No fulfillment jobs found.</td></tr>'
    if not event_rows:
        event_rows = '<tr><td colspan="5" class="empty">No lifecycle events found.</td></tr>'
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>JEDI Admin Console</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f8fa;
      --panel: #ffffff;
      --border: #d8dee4;
      --text: #24292f;
      --muted: #57606a;
      --accent: #0969da;
      --error: #b42318;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, Helvetica, sans-serif;
      font-size: 14px;
    }}
    header {{
      background: var(--panel);
      border-bottom: 1px solid var(--border);
      padding: 18px 24px;
    }}
    h1 {{
      margin: 0 0 4px;
      font-size: 22px;
      font-weight: 700;
    }}
    header p {{
      margin: 0;
      color: var(--muted);
    }}
    main {{
      padding: 24px;
      display: grid;
      gap: 24px;
    }}
    section {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
    }}
    h2 {{
      margin: 0;
      padding: 14px 16px;
      border-bottom: 1px solid var(--border);
      font-size: 16px;
    }}
    .table-wrap {{ overflow-x: auto; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 920px;
    }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
      font-size: 12px;
    }}
    a {{ color: var(--accent); }}
    .muted {{ color: var(--muted); }}
    .error {{ color: var(--error); }}
    .empty {{
      color: var(--muted);
      text-align: center;
      padding: 22px;
    }}
  </style>
</head>
<body>
  <header>
    <h1>JEDI Admin Console</h1>
    <p>Read-only operational view. ServiceNow remains the user work surface.</p>
  </header>
  <main>
    <section>
      <h2>Fulfillment Jobs</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Job</th>
              <th>Story</th>
              <th>Status</th>
              <th>Attempts</th>
              <th>Updated</th>
              <th>Locked By</th>
              <th>Last Error</th>
              <th>Artifacts</th>
            </tr>
          </thead>
          <tbody>{job_rows}</tbody>
        </table>
      </div>
    </section>
    <section>
      <h2>Lifecycle Events</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Event</th>
              <th>Type</th>
              <th>Story</th>
              <th>Received</th>
              <th>Validation</th>
            </tr>
          </thead>
          <tbody>{event_rows}</tbody>
        </table>
      </div>
    </section>
  </main>
</body>
</html>"""


def _admin_job_row(job: FulfillmentJobRecord, refs: list[ArtifactRefRecord]) -> str:
    artifact_links = ", ".join(_admin_artifact_link(ref) for ref in refs)
    if not artifact_links:
        artifact_links = '<span class="muted">None</span>'
    last_error = _html(job.last_error or "")
    if last_error:
        last_error = f'<span class="error">{last_error}</span>'
    else:
        last_error = '<span class="muted">None</span>'
    return (
        "<tr>"
        f"<td><code>{_html(job.job_id)}</code></td>"
        f"<td>{_html(job.story_number)}</td>"
        f"<td>{_html(job.status)}</td>"
        f"<td>{job.attempt_count}</td>"
        f"<td>{_html(_json_timestamp(job.updated_at))}</td>"
        f"<td>{_html(job.locked_by or '')}</td>"
        f"<td>{last_error}</td>"
        f"<td>{artifact_links}</td>"
        "</tr>"
    )


def _admin_event_row(event: LifecycleEventRecord) -> str:
    return (
        "<tr>"
        f"<td><code>{_html(event.event_id)}</code></td>"
        f"<td>{_html(event.event_type)}</td>"
        f"<td>{_html(event.story_number)}</td>"
        f"<td>{_html(_json_timestamp(event.received_at))}</td>"
        f"<td>{_html(event.validation_status)}</td>"
        "</tr>"
    )


def _admin_artifact_link(ref: ArtifactRefRecord) -> str:
    label = _html(ref.artifact_kind)
    if ref.artifact_id is None:
        return f"<span>{label}</span>"
    return f'<a href="/admin/artifacts/{ref.artifact_id}">{label}</a>'


def _admin_artifact_html(artifact: ArtifactBlobRecord) -> str:
    payload_json = json.dumps(artifact.payload_json, indent=2, sort_keys=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Artifact {artifact.id} - JEDI Admin Console</title>
  <style>
    body {{
      margin: 0;
      background: #f6f8fa;
      color: #24292f;
      font-family: Arial, Helvetica, sans-serif;
      font-size: 14px;
    }}
    header {{
      background: #ffffff;
      border-bottom: 1px solid #d8dee4;
      padding: 18px 24px;
    }}
    main {{ padding: 24px; }}
    h1 {{ margin: 0 0 4px; font-size: 22px; }}
    dl {{
      display: grid;
      grid-template-columns: max-content 1fr;
      gap: 8px 14px;
      margin: 0 0 20px;
    }}
    dt {{ color: #57606a; font-weight: 700; }}
    dd {{ margin: 0; }}
    pre {{
      background: #ffffff;
      border: 1px solid #d8dee4;
      border-radius: 8px;
      padding: 16px;
      overflow: auto;
      white-space: pre-wrap;
    }}
    a {{ color: #0969da; }}
  </style>
</head>
<body>
  <header>
    <h1>Artifact {artifact.id}</h1>
    <a href="/admin">Back to Admin Console</a>
  </header>
  <main>
    <dl>
      <dt>Kind</dt><dd>{_html(artifact.artifact_kind)}</dd>
      <dt>Story</dt><dd>{_html(artifact.story_number)}</dd>
      <dt>Job</dt><dd>{_html(artifact.job_id)}</dd>
      <dt>Schema</dt><dd>{_html(artifact.schema_version)}</dd>
      <dt>Created</dt><dd>{_html(_json_timestamp(artifact.created_at))}</dd>
      <dt>SHA-256</dt><dd><code>{_html(artifact.sha256)}</code></dd>
    </dl>
    <pre>{_html(payload_json)}</pre>
  </main>
</body>
</html>"""


def _html(value: str) -> str:
    return html.escape(value, quote=True)


def _bounded_limit(limit: int) -> int:
    return min(max(limit, 1), 100)


def _json_timestamp(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _runtime_handler(
    *,
    settings: RuntimeSettings,
    client: ServiceNowClient,
    claim_handler: FulfillmentHandler,
    transport: HttpTransport,
) -> FulfillmentHandler:
    if settings.model_provider is None:
        return claim_handler
    if settings.model_provider != "openai":
        raise RuntimeConfigError(f"Unsupported model provider: {settings.model_provider}")
    if not settings.openai_api_key:
        raise RuntimeConfigError("OPENAI_API_KEY is required when JEDI_MODEL_PROVIDER=openai")
    if not settings.openai_model:
        raise RuntimeConfigError("OPENAI_MODEL is required when JEDI_MODEL_PROVIDER=openai")

    model_handler = model_candidate_fulfillment_handler(
        client=client,
        config=ModelCandidateFulfillmentConfig(
            policy=_default_model_allowlist_policy(),
            provider_policy=_default_openai_provider_policy(),
            rags=_default_runtime_rags(),
            provider=OpenAIResponsesProvider(
                settings=OpenAIProviderSettings(
                    api_key=settings.openai_api_key,
                    model=settings.openai_model,
                ),
                transport=transport,
            ),
            instance_url=settings.servicenow_instance_url,
            apply_update_set_changes=settings.update_set_apply,
            update_set_user_name=settings.update_set_user_name,
        ),
    )

    def handle(job: FulfillmentJobRecord) -> FulfillmentExecutionResult:
        claim_handler(job)
        return model_handler(job)

    return handle


def process_one_runtime_fulfillment(
    *,
    settings: RuntimeSettings,
    store_factory: StoreFactory = DEFAULT_STORE_FACTORY,
    transport: HttpTransport | None = None,
) -> FulfillmentWorkerResult:
    request_transport = transport or UrllibTransport()
    servicenow_client = _servicenow_client_from_settings(
        settings=settings,
        transport=request_transport,
    )
    with store_factory(settings.database_url) as store:
        claim_handler = build_claim_fulfillment_handler(
            client=servicenow_client,
            config=BuildClaimFulfillmentConfig(
                actor_id=settings.worker_id,
                audit_root=settings.audit_root,
                apply=settings.build_claim_apply,
                from_state=settings.build_claim_from_state,
                claim_state=settings.build_claim_state,
            ),
        )
        handler = _runtime_handler(
            settings=settings,
            client=servicenow_client,
            claim_handler=claim_handler,
            transport=request_transport,
        )
        return process_one_fulfillment_job(
            store=store,
            worker_id=settings.worker_id,
            handler=_redacting_handler(
                handler=handler,
                secret_values=_runtime_secret_values(settings),
            ),
            failure_notifier=_servicenow_failure_notifier(
                client=servicenow_client,
                secret_values=_runtime_secret_values(settings),
            ),
        )


def _servicenow_client_from_settings(
    *,
    settings: RuntimeSettings,
    transport: HttpTransport,
) -> ServiceNowClient:
    auth = OAuthClientCredentials(
        instance_url=settings.servicenow_instance_url,
        client_id=settings.servicenow_client_id,
        client_secret=settings.servicenow_client_secret,
        transport=transport,
    )
    return ServiceNowClient(
        settings=ServiceNowSettings(instance_url=settings.servicenow_instance_url),
        auth=auth,
        transport=transport,
    )


def _servicenow_failure_notifier(
    *,
    client: ServiceNowClient,
    secret_values: Iterable[str] = (),
) -> FulfillmentFailureNotifier:
    def notify(job: FulfillmentJobRecord, error_message: str) -> None:
        fulfillment_job = FulfillmentJobRecord.model_validate(job)
        stories = client.fetch_stories(
            sysparm_query=f"number={fulfillment_job.story_number}",
            limit=1,
        )
        if not stories:
            raise RuntimeError(f"story not found: {fulfillment_job.story_number}")
        fields: dict[str, object] = {
            "u_ai_status": "Automation Failed",
            "work_notes": (
                "Automated fulfillment failed for lifecycle event "
                f"{fulfillment_job.event_id}. Job: {fulfillment_job.job_id}. "
                f"Error: {_redact_text(error_message, secret_values)}"
            ),
        }
        draft_state = _story_state_choice_value(client=client, label="Draft")
        if draft_state is not None:
            fields["state"] = draft_state
        client.update_story_fields(
            stories[0].sys_id,
            fields,
        )

    return notify


def _story_state_choice_value(*, client: ServiceNowClient, label: str) -> str | None:
    normalized_label = label.strip().lower()
    for choice in client.fetch_story_state_choices():
        if choice.label.strip().lower() == normalized_label:
            return choice.value
    return None


def _default_model_allowlist_policy() -> AllowlistPolicy:
    return AllowlistPolicy(
        story_types={StoryType.DICTIONARY_FORM},
        tables={"sys_dictionary", "sys_ui_form"},
        operations={"insert", "update"},
        max_points=3,
    )


def _default_openai_provider_policy() -> ProviderPolicy:
    return ProviderPolicy(
        provider_id="openai-chatgpt",
        deployment_boundary="railway-dev-pdi",
        authorization_level="explicit-dev-evaluation",
        allowed_data_classes={DataClassification.PUBLIC},
        allowed_tasks={IMPLEMENTATION_PACKET_TASK},
        max_context_policy="implementation-packet-v1",
        retention_policy="dev-evaluation-no-training",
        status=ProviderStatus.APPROVED,
    )


def _default_runtime_rags() -> SpecializedRags:
    return SpecializedRags.from_documents(
        [
            Document(
                domain=RagDomain.SERVICENOW_PLATFORM,
                source="runtime/default-servicenow-dictionary-form",
                content=(
                    "rm_story dictionary field work uses sys_dictionary. "
                    "Story form placement uses sys_ui_form."
                ),
                version="runtime-v1",
            ),
            Document(
                domain=RagDomain.INSTANCE_METADATA,
                source="runtime/default-rm-story-metadata",
                content=(
                    "rm_story supports customer-owned custom fields prefixed with u_. "
                    "u_ai_review_notes is the AI Review Notes field."
                ),
                version="runtime-v1",
            ),
            Document(
                domain=RagDomain.PROJECT_CONTEXT,
                source="runtime/default-project-context",
                content=(
                    "AI Review Notes supports implementation review and automated "
                    "fulfillment auditability."
                ),
                version="runtime-v1",
            ),
            Document(
                domain=RagDomain.COMPLIANCE,
                source="runtime/default-compliance-boundary",
                content=(
                    "Only public PDI story context may be sent to the configured "
                    "OpenAI provider during dev evaluation."
                ),
                version="runtime-v1",
            ),
        ]
    )


def _redacting_handler(
    *,
    handler: FulfillmentHandler,
    secret_values: Iterable[str],
) -> FulfillmentHandler:
    def handle(job: FulfillmentJobRecord) -> FulfillmentExecutionResult:
        try:
            return handler(job)
        except Exception as exc:
            raise RuntimeError(_redact_text(str(exc), secret_values)) from exc

    return handle


def _runtime_secret_values(settings: RuntimeSettings) -> tuple[str, ...]:
    values = [
        settings.database_url,
        _url_password(settings.database_url),
        settings.servicenow_client_secret,
        settings.lifecycle_webhook_secret or "",
    ]
    return tuple(value for value in values if value)


def _url_password(url: str) -> str:
    try:
        return urlsplit(url).password or ""
    except ValueError:
        return ""


def _redact_text(text: str, secret_values: Iterable[str]) -> str:
    redacted = text
    for secret in sorted(set(secret_values), key=len, reverse=True):
        if secret:
            redacted = redacted.replace(secret, "***REDACTED***")
    return redacted


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _int_value(value: str | None, *, default: int) -> int:
    if value is None or value.strip() == "":
        return default
    return int(value.strip())


def _optional_str(value: str | None) -> str | None:
    if value is None or value.strip() == "":
        return None
    return value.strip()
