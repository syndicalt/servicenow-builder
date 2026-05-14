from __future__ import annotations

from typing import Any

from jedi_devproject.cicd_update_sets import evaluate_cicd_update_set_capability


class FakeCicdClient:
    def __init__(self, responses: dict[str, dict[str, Any]]) -> None:
        self.responses = responses
        self.actions: list[str] = []

    def probe_cicd_update_set_endpoint(self, *, action: str) -> dict[str, Any]:
        self.actions.append(action)
        return self.responses[action]


def test_evaluate_cicd_update_set_capability_allows_missing_parameter_probes() -> None:
    client = FakeCicdClient(
        {
            "create": {
                "status_code": 400,
                "result": {
                    "status": "3",
                    "status_label": "Failed",
                    "status_message": "Missing required parameter: update_set_name",
                    "status_detail": "",
                    "error": "",
                },
            },
            "retrieve": {
                "status_code": 400,
                "result": {
                    "status": "3",
                    "status_label": "Failed",
                    "status_message": "Missing required parameter: update_set_id",
                    "status_detail": "",
                    "error": "",
                },
            },
        }
    )

    result = evaluate_cicd_update_set_capability(client)

    assert result.available is True
    assert client.actions == ["create", "retrieve"]
    assert [probe.accessible for probe in result.probes] == [True, True]
    assert result.reasons == []


def test_evaluate_cicd_update_set_capability_blocks_forbidden_probe() -> None:
    client = FakeCicdClient(
        {
            "create": {
                "status_code": 403,
                "error": {
                    "message": "Forbidden",
                    "detail": "User missing sn_cicd.sys_ci_automation",
                },
            },
            "retrieve": {
                "status_code": 400,
                "result": {
                    "status": "3",
                    "status_label": "Failed",
                    "status_message": "Missing required parameter: update_set_id",
                },
            },
        }
    )

    result = evaluate_cicd_update_set_capability(client)

    assert result.available is False
    assert result.probes[0].accessible is False
    assert result.reasons == ["create:status_403:Forbidden"]
