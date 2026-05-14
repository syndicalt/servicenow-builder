from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from time import sleep as sleep_seconds

from pydantic import BaseModel, ConfigDict

from jedi_devproject.fulfillment_worker import FulfillmentWorkerResult
from jedi_devproject.runtime import (
    RuntimeSettings,
    load_runtime_settings,
    process_one_runtime_fulfillment,
)

DEFAULT_ENV_PATH = Path("/app/.env")
RuntimeProcessor = Callable[[RuntimeSettings], FulfillmentWorkerResult]
Sleeper = Callable[[float], None]


class RuntimeWorkerLoopSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    iterations: int
    completed: int
    idle: int
    failed: int
    stopped_reason: str


def process_runtime_settings(settings: RuntimeSettings) -> FulfillmentWorkerResult:
    return process_one_runtime_fulfillment(settings=settings)


def run_once(
    *,
    settings: RuntimeSettings,
    processor: RuntimeProcessor = process_runtime_settings,
) -> FulfillmentWorkerResult:
    return processor(settings)


def run_loop(
    *,
    settings: RuntimeSettings,
    processor: RuntimeProcessor = process_runtime_settings,
    max_iterations: int | None = None,
    idle_sleep_seconds: float = 5.0,
    sleep: Sleeper = sleep_seconds,
    stop_on_failure: bool = True,
) -> RuntimeWorkerLoopSummary:
    iterations = 0
    completed = 0
    idle = 0
    failed = 0
    stopped_reason = "max_iterations"

    while max_iterations is None or iterations < max_iterations:
        result = run_once(settings=settings, processor=processor)
        iterations += 1
        if result.status == "completed":
            completed += 1
            continue
        if result.status == "idle":
            idle += 1
            sleep(idle_sleep_seconds)
            continue
        if result.status == "failed":
            failed += 1
            if stop_on_failure:
                stopped_reason = "failed_job"
                break
            continue

    return RuntimeWorkerLoopSummary(
        iterations=iterations,
        completed=completed,
        idle=idle,
        failed=failed,
        stopped_reason=stopped_reason,
    )


def main() -> int:
    result = run_once(settings=load_runtime_settings(DEFAULT_ENV_PATH))
    print(result.model_dump_json())
    return 0 if result.status in {"idle", "completed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
