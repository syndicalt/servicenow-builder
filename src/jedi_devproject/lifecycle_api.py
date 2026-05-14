from __future__ import annotations

from typing import Protocol

from fastapi import FastAPI, status
from pydantic import BaseModel, ConfigDict

from jedi_devproject.lifecycle_events import (
    LifecycleStateChangeEvent,
    plan_story_ready_lifecycle_event,
)
from jedi_devproject.operational_store import FulfillmentJobRecord, LifecycleEventRecord


class LifecycleEventStore(Protocol):
    def record_lifecycle_event(
        self,
        event: LifecycleStateChangeEvent,
        *,
        validation_status: str = "accepted",
    ) -> LifecycleEventRecord: ...

    def enqueue_fulfillment_job(
        self,
        *,
        event_id: str,
        story_number: str,
    ) -> FulfillmentJobRecord: ...


class LifecycleWebhookResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepted: bool
    event_id: str
    story_number: str
    should_evaluate: bool
    lifecycle_action: str | None
    job_id: str | None
    reasons: list[str]


def create_lifecycle_api(*, store: LifecycleEventStore) -> FastAPI:
    app = FastAPI(
        title="Jedi DevProject Lifecycle API",
        version="0.2.0",
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post(
        "/lifecycle/events",
        response_model=LifecycleWebhookResponse,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def receive_lifecycle_event(
        event: LifecycleStateChangeEvent,
    ) -> LifecycleWebhookResponse:
        store.record_lifecycle_event(event)
        plan = plan_story_ready_lifecycle_event(event)

        job_id: str | None = None
        if plan.should_evaluate:
            job = store.enqueue_fulfillment_job(
                event_id=event.event_id,
                story_number=event.story_number,
            )
            job_id = job.job_id

        return LifecycleWebhookResponse(
            accepted=True,
            event_id=event.event_id,
            story_number=event.story_number,
            should_evaluate=plan.should_evaluate,
            lifecycle_action=plan.lifecycle_action,
            job_id=job_id,
            reasons=plan.reasons,
        )

    return app
