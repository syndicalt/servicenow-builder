from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class ContextEscalationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    action: Literal["retrieve_live_instance_context", "manual_review", "proceed_to_model"]
    should_retrieve: bool
    should_call_model: bool
    reasons: list[str]


def plan_context_escalation(context_sufficiency: dict[str, Any]) -> ContextEscalationPlan:
    status = _context_text(context_sufficiency.get("status")).strip()
    missing_context = [
        text
        for item in context_sufficiency.get("missing_context", [])
        for text in [_context_text(item).strip()]
        if text
    ]

    if status == "sufficient":
        return ContextEscalationPlan(
            action="proceed_to_model",
            should_retrieve=False,
            should_call_model=True,
            reasons=[],
        )

    if status == "needs_retrieval":
        return ContextEscalationPlan(
            action="retrieve_live_instance_context",
            should_retrieve=True,
            should_call_model=False,
            reasons=["live_instance_context_missing"],
        )

    return ContextEscalationPlan(
        action="manual_review",
        should_retrieve=False,
        should_call_model=False,
        reasons=[f"context_insufficient:{item}" for item in missing_context]
        or ["context_insufficient"],
    )


def _context_text(value: Any) -> str:
    if type(value) is not str:
        return ""
    return value
