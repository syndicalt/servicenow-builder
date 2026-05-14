from __future__ import annotations

from jedi_devproject.container_smoke import plan_container_lifecycle_smoke


def test_container_lifecycle_smoke_plan_sequences_api_then_worker() -> None:
    plan = plan_container_lifecycle_smoke(
        story_number="STRY0010013",
        event_id="evt-smoke-001",
    )

    assert plan.apply_enabled is False
    assert plan.event_payload == {
        "event_id": "evt-smoke-001",
        "event_type": "story_state_changed",
        "source": "container-smoke",
        "table": "rm_story",
        "story_number": "STRY0010013",
        "previous_state": "Draft",
        "current_state": "Ready",
        "occurred_at": "2026-05-14T00:00:00Z",
        "correlation_id": "STRY0010013-Draft-Ready-evt-smoke-001",
        "emitted_by": "jedi-devproject-container-smoke",
    }
    assert plan.commands == [
        "docker compose up -d postgres api",
        "POST http://localhost:8000/lifecycle/events",
        "docker compose run --rm worker",
        "docker compose down",
    ]


def test_container_lifecycle_smoke_summary_is_secret_safe() -> None:
    plan = plan_container_lifecycle_smoke(
        story_number="STRY0010013",
        event_id="evt-smoke-001",
    )

    summary = plan.safe_summary()

    assert "STRY0010013" in summary
    assert "evt-smoke-001" in summary
    assert "SERVICENOW_CLIENT_SECRET" not in summary
    assert "client-secret" not in summary
    assert "token" not in summary.lower()


def test_container_lifecycle_smoke_plan_rejects_apply_enabled() -> None:
    try:
        plan_container_lifecycle_smoke(
            story_number="STRY0010013",
            event_id="evt-smoke-001",
            apply_enabled=True,
        )
    except ValueError as exc:
        assert "apply_enabled must remain false" in str(exc)
    else:
        raise AssertionError("apply-enabled container smoke should fail closed")
