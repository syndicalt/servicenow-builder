from __future__ import annotations

import os
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
from jedi_devproject.servicenow import load_dotenv_values

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


class RuntimeWorkerSettings(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    runtime: RuntimeSettings
    max_iterations: int | None = None
    idle_sleep_seconds: float = 5.0
    stop_on_failure: bool = False


def load_worker_settings(env_path: Path | None = DEFAULT_ENV_PATH) -> RuntimeWorkerSettings:
    values = dict(os.environ)
    if env_path is not None and env_path.exists():
        values.update(load_dotenv_values(env_path))
    return RuntimeWorkerSettings(
        runtime=load_runtime_settings(env_path),
        max_iterations=_optional_int(values.get("JEDI_WORKER_MAX_ITERATIONS")),
        idle_sleep_seconds=_optional_float(
            values.get("JEDI_WORKER_IDLE_SLEEP_SECONDS"),
            default=5.0,
        ),
        stop_on_failure=_truthy(values.get("JEDI_WORKER_STOP_ON_FAILURE")),
    )


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


def main(
    *,
    env_path: Path | None = DEFAULT_ENV_PATH,
    processor: RuntimeProcessor = process_runtime_settings,
    sleep: Sleeper = sleep_seconds,
) -> int:
    settings = load_worker_settings(env_path)
    summary = run_loop(
        settings=settings.runtime,
        processor=processor,
        max_iterations=settings.max_iterations,
        idle_sleep_seconds=settings.idle_sleep_seconds,
        sleep=sleep,
        stop_on_failure=settings.stop_on_failure,
    )
    print(summary.model_dump_json())
    return 1 if summary.failed and settings.stop_on_failure else 0


def _optional_int(value: str | None) -> int | None:
    if value is None or value.strip() == "":
        return None
    return int(value)


def _optional_float(value: str | None, *, default: float) -> float:
    if value is None or value.strip() == "":
        return default
    return float(value)


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    raise SystemExit(main())
