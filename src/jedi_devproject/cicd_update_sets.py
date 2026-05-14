from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field


class CicdUpdateSetProbe(BaseModel):
    action: str
    status_code: int
    status: str | None = None
    status_label: str | None = None
    status_message: str | None = None
    status_detail: str | None = None
    error: str | None = None
    accessible: bool = False
    reason: str | None = None


class CicdUpdateSetCapabilityResult(BaseModel):
    available: bool
    probes: list[CicdUpdateSetProbe] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class CicdUpdateSetCapabilityClient(Protocol):
    def probe_cicd_update_set_endpoint(self, *, action: str) -> dict[str, Any]:
        """Probe a CI/CD Update Set API endpoint without creating platform state."""


def evaluate_cicd_update_set_capability(
    client: CicdUpdateSetCapabilityClient,
) -> CicdUpdateSetCapabilityResult:
    probes = [
        _probe_action(client, action="create"),
        _probe_action(client, action="retrieve"),
    ]
    reasons = [
        f"{probe.action}:{probe.reason}"
        for probe in probes
        if not probe.accessible and probe.reason
    ]
    return CicdUpdateSetCapabilityResult(
        available=all(probe.accessible for probe in probes),
        probes=probes,
        reasons=reasons,
    )


def _probe_action(
    client: CicdUpdateSetCapabilityClient,
    *,
    action: str,
) -> CicdUpdateSetProbe:
    response = client.probe_cicd_update_set_endpoint(action=action)
    result = _result_payload(response)
    status_code = int(response.get("status_code") or 0)
    status_message = _string_or_none(result.get("status_message"))
    error = _string_or_none(result.get("error"))
    accessible = _is_accessible_probe_response(
        action=action,
        status_code=status_code,
        status_message=status_message,
        error=error,
    )
    return CicdUpdateSetProbe(
        action=action,
        status_code=status_code,
        status=_string_or_none(result.get("status")),
        status_label=_string_or_none(result.get("status_label")),
        status_message=status_message,
        status_detail=_string_or_none(result.get("status_detail")),
        error=error,
        accessible=accessible,
        reason=None if accessible else _blocked_reason(status_code=status_code, result=result),
    )


def _result_payload(response: dict[str, Any]) -> dict[str, Any]:
    result = response.get("result")
    if isinstance(result, dict):
        return result
    error = response.get("error")
    if isinstance(error, dict):
        return {
            "status_label": "Failed",
            "status_message": error.get("message"),
            "status_detail": error.get("detail"),
            "error": error.get("message"),
        }
    return {}


def _is_accessible_probe_response(
    *,
    action: str,
    status_code: int,
    status_message: str | None,
    error: str | None,
) -> bool:
    if status_code in {401, 403, 404}:
        return False
    message = f"{status_message or ''} {error or ''}".lower()
    expected_missing_parameter = {
        "create": "update_set_name",
        "retrieve": "update_set_id",
    }[action]
    return status_code == 400 and expected_missing_parameter in message


def _blocked_reason(*, status_code: int, result: dict[str, Any]) -> str:
    message = _string_or_none(result.get("status_message")) or _string_or_none(result.get("error"))
    if message:
        return f"status_{status_code}:{message}"
    return f"status_{status_code}"


def _string_or_none(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None
