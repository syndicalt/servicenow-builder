from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ContainerLifecycleSmokePlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    story_number: str
    event_id: str
    apply_enabled: bool
    event_payload: dict[str, str]
    commands: list[str]

    def safe_summary(self) -> str:
        return (
            f"Container lifecycle smoke for {self.story_number} using event "
            f"{self.event_id}; apply_enabled={self.apply_enabled}; "
            f"steps={len(self.commands)}"
        )


def plan_container_lifecycle_smoke(
    *,
    story_number: str,
    event_id: str,
    apply_enabled: bool = False,
) -> ContainerLifecycleSmokePlan:
    if apply_enabled:
        raise ValueError("apply_enabled must remain false for container lifecycle smoke")

    event_payload = {
        "event_id": event_id,
        "event_type": "story_state_changed",
        "source": "container-smoke",
        "table": "rm_story",
        "story_number": story_number,
        "previous_state": "Draft",
        "current_state": "Ready",
        "occurred_at": "2026-05-14T00:00:00Z",
        "correlation_id": f"{story_number}-Draft-Ready-{event_id}",
        "emitted_by": "jedi-devproject-container-smoke",
    }
    return ContainerLifecycleSmokePlan(
        story_number=story_number,
        event_id=event_id,
        apply_enabled=False,
        event_payload=event_payload,
        commands=[
            "docker compose up -d postgres api",
            "POST http://localhost:8000/lifecycle/events",
            "docker compose run --rm worker",
            "docker compose down",
        ],
    )
