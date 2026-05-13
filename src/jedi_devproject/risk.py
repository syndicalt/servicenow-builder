from __future__ import annotations

from pydantic import BaseModel, Field


class RiskInput(BaseModel):
    story_type: str
    affected_tables: list[str] = Field(default_factory=list)
    target_table: str | None = None
    field_name: str | None = None
    mandatory: bool = False
    has_default: bool = False
    changes_access_control: bool = False
    changes_workflow: bool = False
    changes_integration: bool = False
    migrates_data: bool = False


def calculate_risk_score(risk_input: RiskInput) -> float:
    score = 0.10

    if risk_input.story_type == "dictionary_form":
        score += 0.02

    if risk_input.mandatory:
        score += 0.15

    if risk_input.has_default:
        score += 0.05

    if risk_input.target_table not in {None, "rm_story"}:
        score += 0.15

    if risk_input.field_name and not risk_input.field_name.startswith("u_"):
        score += 0.10

    if risk_input.changes_access_control:
        score += 0.35

    if risk_input.changes_workflow:
        score += 0.25

    if risk_input.changes_integration:
        score += 0.35

    if risk_input.migrates_data:
        score += 0.35

    return min(round(score, 2), 1.0)
