from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, cast

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

from jedi_devproject.fulfillment_handler import (
    BuildClaimFulfillmentConfig,
    build_claim_fulfillment_handler,
)
from jedi_devproject.fulfillment_worker import (
    FulfillmentWorkerResult,
    FulfillmentWorkerStore,
    process_one_fulfillment_job,
)
from jedi_devproject.lifecycle_api import LifecycleEventStore, create_lifecycle_api
from jedi_devproject.operational_store import connect_operational_store
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

    database_url: str
    servicenow_instance_url: str
    servicenow_client_id: str
    servicenow_client_secret: str
    worker_id: str = "jedi-devproject-worker"
    audit_root: Path
    build_claim_apply: bool = False


class RuntimeStore(LifecycleEventStore, FulfillmentWorkerStore, Protocol):
    def __enter__(self) -> RuntimeStore: ...

    def __exit__(self, *_args: object) -> None: ...


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
        raise RuntimeConfigError(
            f"Missing required runtime settings: {', '.join(missing)}"
        )

    return RuntimeSettings(
        database_url=str(values["DATABASE_URL"]),
        servicenow_instance_url=str(values["SERVICENOW_INSTANCE_URL"]),
        servicenow_client_id=str(values["SERVICENOW_CLIENT_ID"]),
        servicenow_client_secret=str(values["SERVICENOW_CLIENT_SECRET"]),
        worker_id=str(values.get("JEDI_WORKER_ID") or "jedi-devproject-worker"),
        audit_root=Path(str(values["JEDI_AUDIT_ROOT"])),
        build_claim_apply=_truthy(values.get("JEDI_BUILD_CLAIM_APPLY")),
    )


def create_runtime_api(
    *,
    settings: RuntimeSettings,
    store_factory: StoreFactory = DEFAULT_STORE_FACTORY,
) -> FastAPI:
    store = store_factory(settings.database_url)
    return create_lifecycle_api(store=store)


def process_one_runtime_fulfillment(
    *,
    settings: RuntimeSettings,
    store_factory: StoreFactory = DEFAULT_STORE_FACTORY,
    transport: HttpTransport | None = None,
) -> FulfillmentWorkerResult:
    with store_factory(settings.database_url) as store:
        return process_one_fulfillment_job(
            store=store,
            worker_id=settings.worker_id,
            handler=build_claim_fulfillment_handler(
                client=_servicenow_client_from_settings(
                    settings=settings,
                    transport=transport or UrllibTransport(),
                ),
                config=BuildClaimFulfillmentConfig(
                    actor_id=settings.worker_id,
                    audit_root=settings.audit_root,
                    apply=settings.build_claim_apply,
                ),
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


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}
