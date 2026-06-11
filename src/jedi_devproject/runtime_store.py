"""Operational store contract shared by the runtime API and fulfillment worker wiring."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, cast

from jedi_devproject.fulfillment_worker import FulfillmentWorkerStore
from jedi_devproject.lifecycle_api import LifecycleEventStore
from jedi_devproject.operational_store import (
    ArtifactBlobRecord,
    ArtifactRefRecord,
    FulfillmentJobRecord,
    LifecycleEventRecord,
    connect_operational_store,
)


class RuntimeStore(LifecycleEventStore, FulfillmentWorkerStore, Protocol):
    def __enter__(self) -> RuntimeStore: ...

    def __exit__(self, *_args: object) -> None: ...

    def get_artifact_blob(self, artifact_id: int) -> ArtifactBlobRecord: ...

    def artifact_refs_for_job(self, job_id: str) -> list[ArtifactRefRecord]: ...

    def recent_lifecycle_events(self, *, limit: int = 50) -> list[LifecycleEventRecord]: ...

    def recent_fulfillment_jobs(self, *, limit: int = 50) -> list[FulfillmentJobRecord]: ...


StoreFactory = Callable[[str], RuntimeStore]
DEFAULT_STORE_FACTORY = cast(StoreFactory, connect_operational_store)
